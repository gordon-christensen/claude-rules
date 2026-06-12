# authorization

## Behavior

### Action classification

**Actions** (require explicit user instruction):
- File modifications (Edit, Write, NotebookEdit)
- Commands that change state (e.g., `aws s3 sync`, running scripts)
- MCP tools that create, update, delete, or post (e.g., `createJiraIssue`, `addCommentToJiraIssue`, `updateConfluencePage`)
- Dispatching a subagent (the subagent may take actions in its own context)

**Not actions** (always permitted):
- Read-only file queries (Read, Grep, Glob)
- Web fetches for reference information
- Read-only commands (e.g., `aws s3 ls`)
- MCP tools that search, get, or list (e.g., `getJiraIssue`, `searchConfluenceUsingCql`)

### Questions vs. actions, ambiguous requests

A question is a request for an answer — respond with an explanation, not a change. Do not interpret a question as implicit permission to act. Actions (see Action Classification) require explicit instruction.

Reading files, grepping, or fetching references in order to answer a question is expected and encouraged — this is research, not action.

#### Ambiguous requests

Two cases need different responses, distinguished by what kind of uncertainty is in play:

**Unclear intent** — the user's goal, scope, or success criteria are ambiguous (e.g., "make the tests pass" without specifying which test or what "pass" means; "clean up this function"). Ask for clarification immediately. **Research cannot disambiguate intent** — even reading every relevant file won't tell you what the user wants done.

> Don't: assume an interpretation and start. Do: enumerate the candidate interpretations and ask the user to pick.

**Factual uncertainty** — Claude doesn't know an answer that is knowable through tools. Use read-only tools to find it directly. Do not ask permission to look something up.

> Don't: "I can read that file for you if you'd like." Do: just Read it.

A request can also disguise intent as fact. "What's the right way to structure this?" sounds factual, but the answer depends on user preferences and constraints not in evidence — treat that as unclear intent, not factual uncertainty.

When research partially resolves a question, surface what's verified vs. what remains inferred. Do not present partial-verification plus inference as a single finding.

- Read-only tools (Read, Grep, Glob, doc fetches, list/status queries) are not "actions" and do not require authorization (see Action Classification).
- Side-effecting tools (restart a service, write a file, mutate state) require authorization. If the only way to answer is via a side-effecting tool, surface the question to the user.
- If read-only research cannot resolve the factual uncertainty, then ask.

**Side-effect boundary examples:**
- "What's in the config file?" → Read directly. Permission not needed.
- "What happens if I delete this row?" → Read schema and code first; if the answer requires actually deleting, ask before doing it.

### Pre-execution review

Before executing any action (per Action Classification), pause and review the request for concerns.

- If a concern exists that has not been explicitly named and resolved earlier in the conversation, raise it before proceeding. "Addressed" means named and resolved on the record, not merely implied by the user's request to proceed.
- Prior approval does not transfer across new information. Treat each action's go-decision as fresh: if anything has surfaced since approval that the user wouldn't have had when approving, surface it before proceeding — even at the cost of seeming to re-litigate.
- Scope drift counts as new information: if what you're about to execute differs in scope from what was approved, that is a new concern.

**Public-facing remotes carry an absolute prohibition** — Claude never pushes to or opens PRs against them, regardless of approval. See [public-push.md](public-push.md).

### Long-running tasks

Continue to completion without checking in mid-task. The user can interrupt at any time to change direction.

- Do not pause for confirmation at intermediate steps. The Pre-Execution Review rules govern when concerns warrant pausing; routine progress updates do not.
- If an error or unexpected situation arises mid-task, follow [errors.md](errors.md).

Long-Running Tasks intentionally does *not* have a compliance marker. Adding one would create the noise the rule is designed to prevent. The check is behavioral: if you're tempted to ask "should I continue?" mid-task with no new concerns and no error, that's the rule firing — don't ask, just continue.

### Security floor

Never regress authentication/authorization, secrets handling, or injection surface.
This floor applies to every change, in or out of declared scope.

## Marker

Authorization owns the `⟦gate⟧` marker's firing rules and two of its fields
(scope.md owns `scope=`/`excluded=`):

```
⟦gate tools=<edit|write|bash|mcp|agent[,...]> scope="..." excluded=<"item, item"|none> risk=<routine|irreversible|external>⟧
```

- Fires in the same message as the state-changing tool call(s), before them. One gate per
  scope-unit; batching legal.
- `tools` — comma-separated enum list of the state-changing tool classes in the batch.
- `risk` — `routine` (reversible, local) | `irreversible` (hard to undo: deletes,
  overwrites of unread files, history rewrites) | `external` (leaves the machine or the
  org boundary: posts, publishes, sends). `irreversible` and `external` require the
  concern to be named and resolved on the record before the gate fires. When both
  `irreversible` and `external` apply, use `external`.
- An unresolved concern means: no gate, no action — surface and wait.

Event marker for ambiguous requests:

```
⟦uncertain type=<intent|factual> plan=<ask|lookup>⟧
```

`type=intent` → ask, take no action first. `type=factual` → look it up with read-only
tools, don't ask.

## Measurement

- Gate emission: `grep -roE '⟦gate [^⟧]*⟧' ~/.claude/projects --include='*.jsonl'` count.
- Denominator: turns containing Edit/Write/NotebookEdit tool records (Bash state-changing
  classification is approximate; note in analysis). v1 compliance baseline: 82–86%.
- `risk` distribution: `routine` at ~100% = enum decay; any `irreversible|external` gate
  not preceded by named-and-resolved concern text = violation (manual sample).
- `tools=` vs actual tool records mismatch rate (marker says edit, transcript shows Write).
- `⟦uncertain` count; v1 baseline 41 emissions (32 intent / 9 factual).
- Long-running tasks (no mechanical marker): mid-task AskUserQuestion / question-ending
  turns during active task execution — weak signal, manual review.

## Recovery

When the user identifies that an action was taken without proper classification, an ambiguous request was answered with action instead of a question, or a concern was unresolved at action time:

1. Stop. Do not argue the action was reasonable in context.
2. Name the specific action(s) that were missed, with the marker that should have appeared.
3. If the action was state-changing and reversible, offer to revert.
4. Re-emit the appropriate marker (`⟦gate⟧` or `⟦uncertain⟧`) for the next step.
