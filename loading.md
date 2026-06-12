# loading

## Behavior

When this configuration or any reference doc says "read on demand," "load when X," or "not auto-loaded" — **load aggressively**. If there is even a 1% chance a topic might apply to the task, Read it. The cost of re-researching what these docs cover — hours or days — dwarfs the cost of a few thousand extra tokens. Context overflow is the acceptable risk; missing knowledge is not.

Per-topic trigger lists are the surface for that rule. Any signal matching any item = load. Lists are not exhaustive — if something seems adjacent, load anyway. There is no "Skip when" escape hatch; if you're debating, load.

## Marker

None — transcript-native instrumentation; see Measurement.

## Measurement

- Reads under on-demand trees:
  `grep -rl 'file_path":"[^"]*\.claude/on-demand/' ~/.claude/projects --include='*.jsonl' | wc -l`
- Read count: `grep -rh 'file_path\":\"[^\"]*\.claude/on-demand/' ~/.claude/projects --include='*.jsonl' | wc -l` — reproduces the reads half of the baseline.
- v1 baseline: 81 sessions / 439 reads.
- Under-loading is the failure mode and is not mechanically detectable; sample sessions
  touching institution topics for missing loads.

## Recovery

When a session is found to have worked an institution topic without loading its area:
name the area, Read it now, and re-verify any answers given from inference.
