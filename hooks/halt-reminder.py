#!/usr/bin/env python3
"""PostToolUse hook: inject errors.md halt reminder when a tool result is an error.

Conservative predicate (explicit error flags only) — benign-vs-real classification
stays with the model, per errors.md. Tune per-tool here if injections over/under-fire.
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
    if is_error(data.get("tool_response")):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "Tool result was an error. errors.md applies - classify it; if it "
                    "counts, emit ⟦halt tool=... err=\"...\"⟧ and stop. "
                    "No retry, no fallback."
                ),
            }
        }))


if __name__ == "__main__":
    main()
