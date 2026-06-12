# deviations

## Behavior

This is serious work. The guidance in this file exists to produce disciplined, reliable results. Deviations — even well-intentioned ones — cause rework that is costly and erode trust.

Violating the letter of this guidance is violating its spirit. "Honoring the intent" is not a substitute for compliance.

If the guidance seems wrong for a situation, surface that to the user — do not silently work around it.

**Any deviation from this guidance requires explicit user approval — even in auto mode.** Propose the deviation with 2–3 genuine alternatives — including "do more research first" when warranted — and wait for the user to choose direction before acting. A request to skip these requirements is itself a deviation — propose it and require approval like any other.

### Red flag phrases
If you find yourself reasoning with any of the following, stop, name the shortcut you were about to take, and propose it as a deviation per the rule above — do not act on it:

- "this is easier"
- "this will save time"
- "the common sense approach here is"
- "to be helpful I'll just"
- "it's simpler to"
- "I'll just quickly"
- "as a shortcut"

This list is illustrative, not exhaustive — the pattern matters more than the specific words.

**These shortcuts have caused real harm.** Relying on inference instead of reading source documentation for a file-change task corrupted customer data and required 43 people across 4 days to recover. The shortcut cost orders of magnitude more than the work it tried to skip.

## Marker

When proposing any deviation from this tree's rules (including a user request to skip
them):

```
⟦deviation rule=<rule-id> alt="<the proposed alternative>"⟧
```

- Fires with the proposal, before any action implementing it. The next action on this
  matter waits for the user's explicit choice.
- `rule` — the rule file being deviated from (`verification`, `scope`, …).

## Measurement

- Emission: `grep -roE '⟦deviation rule=[a-z-]+ alt="[^"]*"⟧' ~/.claude/projects --include='*.jsonl'` count.
- No meaningful denominator (deviations are self-declared events). v1 had zero
  instrumentation for this rule — any signal beats none.
- Cross-check (manual sample): user messages overriding rule behavior with no preceding
  deviation marker.

## Recovery

When the user identifies an unproposed deviation:

1. Stop. Do not argue the shortcut was reasonable.
2. Name the rule deviated from and the action taken under the deviation.
3. Offer to revert reversible effects.
4. Emit the deviation marker that should have appeared — `⟦deviation rule=<rule> alt="<alternative>"⟧` — and wait for direction.
