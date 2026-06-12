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


def last_turn_blocks(path):
    """Content blocks of assistant messages since the last real user message."""
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
            content = (evt.get("message") or {}).get("content") or []
            is_tool_result = any(isinstance(b, dict) and b.get("type") == "tool_result"
                                 for b in content)
            if not is_tool_result:
                break
    blocks = []
    for evt in reversed(turn):
        blocks.extend((evt.get("message") or {}).get("content") or [])
    return blocks


def audit(blocks):
    problems = []
    text = " ".join(b.get("text", "") for b in blocks
                    if isinstance(b, dict) and b.get("type") == "text")
    m = list(VERIFY_RE.finditer(text))
    if not m:
        problems.append("missing ⟦verify⟧ marker - emit it (verification.md)")
    else:
        claims, cited, pw = (int(x) for x in m[-1].groups())
        prose_len = len(re.sub(r"```.*?```", "", VERIFY_RE.sub("", text), flags=re.DOTALL).strip())
        if cited != claims - pw:
            problems.append(
                f"verify arithmetic broken: cited={cited} != claims={claims} - pw={pw}")
        if claims == 0 and prose_len > PROSE_THRESHOLD:
            problems.append(
                "claims=0 on a substantive reply - recount per verification.md zero-count recheck")
    gate_seen = False
    for b in blocks:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text" and GATE_RE.search(b.get("text", "")):
            gate_seen = True
        elif b.get("type") == "tool_use" and b.get("name") in STATE_TOOLS:
            if not gate_seen:
                problems.append(
                    f"state-changing tool {b.get('name')} with no preceding ⟦gate⟧ (authorization.md)")
                continue
    return problems


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
    problems = audit(blocks)
    if problems:
        print(json.dumps({"decision": "block", "reason": "; ".join(problems)}))


if __name__ == "__main__":
    main()
