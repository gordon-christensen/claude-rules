# behavior

Operating rules for Claude Code. Successor to rutabaga-yoga, redesigned around
measurability: every rule defines its instrument (marker or transcript-native query)
and its decay signal. Design: arpa `projects/behavior-rules/design.md`.

## Install

```
git clone <remote> ~/rules/behavior
ln -s ~/rules/behavior ~/.claude/rules/behavior
```

Claude Code auto-loads every `.md` under `~/.claude/rules/`. Keep non-rule material
(designs, notes) out of this tree — it all lands in every session's context.

## Marker grammar

One format: `⟦<marker-id> <field>=<value> ...⟧` — always one line, in reply text.
One grep (`⟦`) finds every marker. Three value types, no free-text compliance fields:

| Type | Form | Decay query |
|---|---|---|
| enum | `risk=routine` | one value at ~100% over time |
| int | `claims=4` | distribution collapse |
| content | `scope="fix date fmt"`; bare `none` if empty | `none`-rate → 100% |

Values may not contain `⟧` or double quotes — paraphrase.
Unquoted values may not contain spaces; comma-separate list members (e.g., `tools=edit,write`). Quoted (content) values may contain spaces and commas.
For `⟦verify⟧`, `cited = claims − pw` is a parseable invariant — hooks assert it.

### Recurring (the entire per-turn load)

| Marker | When | Owner |
|---|---|---|
| `⟦intent goal="..."⟧` | before each tool batch | intent.md |
| `⟦gate tools=... scope="..." excluded="item, item"\|none risk=routine\|irreversible\|external⟧` | before state-changing actions, one per scope-unit | authorization.md (tools, risk) + scope.md (scope, excluded) |
| `⟦verify claims=N cited=N pw=N⟧` | end of every reply; `cited = claims − pw` | verification.md |

Example: `⟦gate tools=edit scope="fix null guard in parser.py" excluded=none risk=routine⟧`

### Event markers

| Marker | Event | Owner |
|---|---|---|
| `⟦halt tool=... err="..."⟧` | real tool error | errors.md |
| `⟦uncertain type=intent\|factual plan=ask\|lookup⟧` | ambiguous request | authorization.md |
| `⟦deviation rule=<rule-id> alt="..."⟧` | proposing a deviation | deviations.md |
| `⟦push-halt remote="..." branch=... act=push\|pr\|branch⟧` | public-remote push intent | public-push.md |
| `⟦counts kind=initial\|followup ctx=N det=N test=N⟧` | PR/commit body drafted | pr-commits.md |
| `⟦proposal file="..." change="..."⟧` | edit under ~/.claude/ proposed | meta.md |
| `⟦capture inst=... area=... fact="..."⟧` | knowledge capture | meta.md |
| `⟦institution detected=<name>\|none⟧` | proprietary content present | meta.md |

## Hooks

Two scripts in `hooks/` (see each rule file for rationale). Wire in `settings.json`
(user-approved step, outside this tree):

```json
{
  "hooks": {
    "PostToolUse": [
      {"matcher": "*",
       "hooks": [{"type": "command", "command": "python3 ~/rules/behavior/hooks/halt-reminder.py"}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "python3 ~/rules/behavior/hooks/turn-audit.py"}]}
    ]
  }
}
```

Tests: `python3 -m unittest discover -s tests -v` (from repo root).

## Measurement

Each rule file's Measurement section documents its queries (no script — run ad hoc
against `~/.claude/projects/**/*.jsonl`). v1 baselines live in the design doc.

## Rule index

verification · intent · scope · authorization · errors · deviations · public-push ·
pr-commits · meta · output · loading
