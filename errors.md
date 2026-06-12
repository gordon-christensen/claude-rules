# errors

## Behavior

When any tool call, command, or subprocess returns an error, fails, or produces unexpected output, stop immediately and raise it to the user.

- Do not attempt to resolve, work around, or retry the error — including silent internal retries before surfacing.
- Do not catch, log, or summarize the error and continue. The error halts the task.
- Do not fall back to an alternative tool, API, endpoint, method, or auth scheme.
- Do not continue past the error, even for steps that appear unrelated.
- An error may mean an upstream assumption is wrong; reattempting compounds the error.
- Any change of approach requires the user's explicit approval.

### What counts as an error

- Non-zero exit codes from a command intended to succeed.
- 4xx / 5xx HTTP responses (including 401 / 403 / 404).
- Tool calls that return an error object or exception.
- Partial successes where some operations completed and others failed.

### What does NOT count as an error

- Empty result sets from a read-only query (grep with no matches, list returning no items, search returning zero hits). These are information; they may mean "look elsewhere" but are not a stop-and-surface condition.
- A read returning content that contradicts your expectation. That is the read working correctly. Update the model.

The rule's purpose is to prevent compounding actions on a broken assumption — most acutely auth thrashing. Normal exploration of read-only state is not the target.

### Worked example: auth thrashing

This rule applies generally; auth is called out because it's the highest-frequency violation. When an authentication or authorization error occurs (401, 403, expired token, missing credentials), do not try alternative auth models, token sources, or credential paths. The underlying auth configuration is what needs fixing.

> Don't:
> - "Got 401 with Basic auth; let me try Bearer instead."
> - "Token file returned 401; let me try an env var."
> - "Cookie auth rejected; let me try header auth."
>
> Do: stop. Surface the failure and the auth scheme that failed.

## Marker

In the same message that observes a real error (per "What counts" above):

```
⟦halt tool=<tool-name> err="<code or one-line summary>"⟧
```

- The message containing the halt has no further state-changing tool calls. Read-only
  calls only if the user can't decide without them.
- One halt per root cause — a batch failing identically gets one marker naming the
  pattern, not three retries.
- Hook support: `hooks/halt-reminder.py` (PostToolUseFailure) injects a reminder whenever
  a tool call fails. Classification stays with the model — benign failures (no-match
  greps, expected probes) are information, not halts.

## Measurement

- Emission: `grep -roE '⟦halt tool=[^ ]+ err="[^"]*"⟧' ~/.claude/projects --include='*.jsonl'` count.
- Denominator: halt-reminder hook injections (exact, new in v2 — count the injected
  reminder text in transcripts). v1 estimate was 27 halt-sessions vs 200 error-sessions.
- Health: injection→halt conversion rate for real errors; silent-retry sequences
  (error followed by modified re-invocation, no halt) = violation (manual sample).

## Recovery

### Recovery from an error-halt miss

When the user identifies that you continued past an error (retried, fell back, swallowed the failure):

1. Stop. Do not minimize the error or argue the retry was reasonable.
2. Name the specific error(s) that were not surfaced, in a list with tool + code/message.
3. Roll back any state changes made after the missed error, where possible. Where not possible, state what's now in an unknown state.
4. Re-emit the `⟦halt⟧` marker for the original error.
