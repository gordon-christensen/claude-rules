# intent

## Behavior

Before each batch of tool calls, state in one or two sentences what question the batch
answers or what state it establishes — the goal, not the steps. Mid-task, a finding that
changes direction is a new intent: name the pivot before continuing.

- A single read-only call inside a conversational reply needs no marker; batches and
  state-changing actions always do.
- When asking the user multiple questions, give each a short label or number so they can
  answer per-point (companion convention in output.md).

## Marker

In the same message as the tool batch (stale intents from earlier messages don't count):

```
⟦intent goal="<one-to-two-sentence goal>"⟧
```

`goal` is content-typed: the question being answered or state being established — never a
list of commands or filenames.

## Measurement

- Emission: `grep -roE '⟦intent goal="[^"]+"⟧' ~/.claude/projects --include='*.jsonl'`
- Denominator: assistant messages containing `"type":"tool_use"`.
- Health: v1 baseline 1,865 emissions / 339 sessions — broad adoption expected to continue.
- Decay: goal text degenerating into command lists or boilerplate (manual spot-check of a
  random sample; no mechanical signal).

## Recovery

When the user identifies a missing or stale intent:

1. Stop. Do not argue the intent was implied.
2. Name the batch that ran unmarked.
3. Emit the marker that should have appeared, then continue.
