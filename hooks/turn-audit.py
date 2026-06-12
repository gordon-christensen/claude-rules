#!/usr/bin/env python3
"""Stop hook: audit the finished turn for behavior markers.

Blocks on: missing verify marker; claims=0 on substantive prose; broken
cited = claims - pw arithmetic; state-changing tool_use with no preceding gate.
One correction round per turn (stop_hook_active guard).
"""
import json
import re
import sys

PROSE_THRESHOLD = 600
STATE_TOOLS = {"Edit", "Write", "NotebookEdit"}
VERIFY_RE = re.compile(r"⟦verify claims=(\d+) cited=(\d+) pw=(\d+)⟧")
GATE_RE = re.compile(r"⟦gate [^⟧]*⟧")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def strip_fences(s):
    return FENCE_RE.sub("", s)


def content_blocks(evt):
    """Message content normalized to a block list (real transcripts may store
    user message content as a plain string)."""
    content = (evt.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return content or []


def last_turn_blocks(path):
    """Content blocks of assistant messages since the last real user message.

    Injected meta events (hook feedback, harness reminders) appear as user-type
    events with isMeta set — they are noise inside a logical turn, not turn
    boundaries, and must not fragment the audited span.
    """
    events = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    turn = []
    for evt in reversed(events):
        etype = evt.get("type")
        if etype == "assistant":
            turn.append(evt)
        elif etype == "user":
            if evt.get("isMeta"):
                continue
            content = content_blocks(evt)
            is_tool_result = any(isinstance(b, dict) and b.get("type") == "tool_result"
                                 for b in content)
            if not is_tool_result:
                break
    blocks = []
    for evt in reversed(turn):
        blocks.extend(content_blocks(evt))
    return blocks


def audit(blocks):
    """Returns (blocking, advisory) problem lists.

    Real transcripts are unreliable for prose: an interrupted turn's text
    blocks may be absent from the main line while its tool_use events are
    present (observed 2026-06-12). Therefore gate-ordering findings are
    advisory only, and verify findings block only when the turn's final
    text block actually landed (last block is text).
    """
    blocking = []
    advisory = []
    texts = [b for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    if not texts:
        return blocking, advisory  # nothing auditable landed in the transcript
    last_is_text = isinstance(blocks[-1], dict) and blocks[-1].get("type") == "text"
    text = strip_fences(" ".join(b.get("text", "") for b in texts))
    m = list(VERIFY_RE.finditer(text))
    if not m:
        if last_is_text:
            blocking.append("missing ⟦verify⟧ marker - emit it (verification.md)")
    else:
        claims, cited, pw = (int(x) for x in m[-1].groups())
        prose_len = len(VERIFY_RE.sub("", text).strip())
        if cited != claims - pw:
            blocking.append(
                f"verify arithmetic broken: cited={cited} != claims={claims} - pw={pw}")
        if claims == 0 and prose_len > PROSE_THRESHOLD:
            blocking.append(
                "claims=0 on a substantive reply - recount per verification.md zero-count recheck")
    gate_seen = False
    for b in blocks:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text" and GATE_RE.search(strip_fences(b.get("text", ""))):
            gate_seen = True
        elif b.get("type") == "tool_use" and b.get("name") in STATE_TOOLS:
            if not gate_seen:
                advisory.append(
                    f"state-changing tool {b.get('name')} with no preceding ⟦gate⟧ (authorization.md)")
                continue
    return blocking, advisory


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    if data.get("stop_hook_active"):
        return
    path = data.get("transcript_path")
    if not path:
        return
    try:
        blocks = last_turn_blocks(path)
    except OSError:
        return
    blocking, advisory = audit(blocks)
    if blocking:
        reason = "; ".join(blocking)
        if advisory:
            reason += " | advisory: " + "; ".join(advisory)
        print(json.dumps({"decision": "block", "reason": reason}))
    elif advisory:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": (
                    "Advisory (transcript prose can lag/branch; not blocking): "
                    + "; ".join(advisory)
                ),
            }
        }))


if __name__ == "__main__":
    main()
