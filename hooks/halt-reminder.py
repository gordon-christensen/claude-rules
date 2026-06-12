#!/usr/bin/env python3
"""PostToolUseFailure hook: inject errors.md halt reminder when a tool call fails.

PostToolUse fires only on success; tool failures fire PostToolUseFailure — every
invocation of this hook IS a failed call, so no error predicate is needed on that
event. The is_error fallback covers accidental wiring to PostToolUse. Benign-vs-real
classification stays with the model, per errors.md.
"""
import json
import sys


def is_error(resp) -> bool:
    if not isinstance(resp, dict):
        return False
    return resp.get("is_error") is True or resp.get("isError") is True \
        or resp.get("type") == "error"


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    if data.get("hook_event_name") == "PostToolUseFailure" \
            or is_error(data.get("tool_response")):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": (
                    "Tool result was an error. errors.md applies - classify it; if it "
                    "counts, emit ⟦halt tool=... err=\"...\"⟧ and stop. "
                    "No retry, no fallback."
                ),
            }
        }))


if __name__ == "__main__":
    main()
