# scope

## Behavior

Keep changes small and focused on what was asked. Do not expand scope without explicit instruction.

- Do only what was requested — do not refactor surrounding code, reorganize files, or add unrequested features.
- If an improvement or refactoring opportunity is noticed, surface it to the user without acting on it.
- Unrequested additions — even helpful ones — are scope creep.

> Don't: "while I'm in here, let me also rename this variable." Do: note the opportunity in your reply; finish the actual task.

### Scope-creep red flags

If you find yourself reasoning with any of the following, stop. You are about to expand scope:

- "while I'm at it…"
- "this is a quick win…"
- "it's right there, just one more line…"
- "to be thorough, I'll also…"
- "this would clean up nicely…"

This list is illustrative, not exhaustive — the pattern matters more than the specific words.

**Scope creep has caused real harm.** A "while I'm in here" rework bundled with a bug fix obscured the actual change. The PR was sent back, the rework stripped as inconsequential, and the fix reapplied alone. The unrequested "help" shipped nothing and cost a review cycle.

## Marker

Scope owns two fields of the shared `⟦gate⟧` marker (see authorization.md for the
marker's firing rules and its other fields):

```
⟦gate ... scope="<exactly what this action does>" excluded=<"item, item"|none> ...⟧
```

- `scope` — one phrase, the declared boundary of the action.
- `excluded` — tempting-but-unrequested items noticed and not done; bare `none` if none.
  A non-empty list means: "I see these, I'm not doing them, pick them up if you want."
- Wanting to act beyond the declared `scope` mid-action means stop and re-emit the gate —
  never silently widen.
- One gate may cover a batch of actions sharing a single scope declaration.
- The `...` in the template stand for the authorization-owned fields (`tools=`, `risk=`) — never emit literal `...`; see authorization.md for the full field list.

## Measurement

- Field extraction: `grep -roE '⟦gate [^⟧]*⟧' ~/.claude/projects --include='*.jsonl'`,
  then parse `excluded=`.
- Health: `excluded` carries real items at a healthy rate (v1 out-of-scope baseline:
  44.4% real / 55.6% none).
- Decay: `excluded=none` rate trending toward 100% — the field going ritual.

## Recovery

When the user identifies that you exceeded the declared (or implied) scope:

1. Stop. Do not justify the extra work or claim it was harmless.
2. Name the specific items that were out of scope, in a list.
3. Propose a revert or hand them back as a deviation to approve separately.
4. Re-emit the `⟦gate⟧` with the original scope for the next action.
