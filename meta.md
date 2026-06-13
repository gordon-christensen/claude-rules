# meta

## Behavior

### Canonical edit areas

The two canonical areas are `~/.claude/rules/gordon.christensen/` (this tree) and
`~/.claude/on-demand/{institution}/`. Treat edits to them
with the gravity of production config.

- **Never create or update the global `~/.claude/CLAUDE.md`.**
- **No edits under `~/.claude/` without explicit user confirmation, except within the two
  canonical areas.** Settings, keybindings, commands, agents, skills, project `.claude/`
  trees — propose and wait.
- Behavior rules go in this tree, in the file where they fit the taxonomy. Proprietary or
  institution-specific knowledge goes in `~/.claude/on-demand/{institution}/` behind
  progressive-loading triggers.

### Institution model and dependency direction

Each institution gets its own subdirectory under `~/.claude/on-demand/`:

```
~/.claude/on-demand/{institution}/
├── README.md          ← defines the institution and progressive-loading triggers
└── {area}/            ← per-topic subdirectories, each with a README.md entry point
```

The `README.md` at the root of the institution tree **must** define the institution — what organization it represents and what scope of knowledge belongs under it. This definition is the anchor for the institution self-check below.

`~/.claude/rules/gordon.christensen` can exist without any institution tree. An institution
on-demand tree must not exist without `~/.claude/rules/gordon.christensen` — the rules define
the operating framework.

### Capturing proprietary knowledge

When you discover something non-obvious about a proprietary service, API, or org-specific pattern that isn't already documented — auth conventions, endpoint quirks, internal naming, version-specific behavior — capture it in the institution's on-demand tree without being asked. The point is to avoid re-learning the same thing next session.

- **API and service knowledge** (auth, endpoints, quirks, token formats) → `~/.claude/on-demand/{institution}/services/README.md`, in the section for that service. Create a new section if the service isn't listed.
- **Other proprietary knowledge** → the on-demand area that fits the existing taxonomy. If no area fits, create one.

- The capture bar: a future session would re-discover this, and the discovery cost more than 30 seconds — not every fact qualifies.
- Capture is covered by this standing instruction — emit the ⟦capture⟧ marker and write the entry in the same round; no separate approval round is needed.
- If the institution's on-demand tree doesn't exist yet, note the capture in the conversation but do not write it — surface the gap to the user instead.

## Marker

```
⟦proposal file="<path under ~/.claude/ or this tree>" change="<one-line summary>"⟧
```
Before any Write/Edit targeting the canonical areas or anything else under `~/.claude/`.
For non-canonical paths the proposal waits for explicit go; for canonical paths it is the
trace, per the standing instructions above.

```
⟦capture inst=<institution> area=<area> fact="<one-line non-obvious behavior>"⟧
```
When discovering capture-bar knowledge — emit, then write the entry in the same round.

```
⟦institution detected=<name|none>⟧
```
When proprietary content is present in the conversation. Proprietary content with no
identifiable institution = error halt per errors.md.

## Measurement

- Emissions: `grep -roE '⟦(proposal|capture|institution) [^⟧]*⟧' ~/.claude/projects --include='*.jsonl'` by type.
- Denominator: Edit/Write tool records with `file_path` under `~/.claude/`.
- Violation query: such edits with no proposal/capture marker in the same session.
- v1 baselines: 52 proposals / 17 sessions; 19 captures / 7 sessions; 20 institution / 19.

## Recovery

When the user identifies that you edited a `.claude/` file without a proposal marker, or missed a capture opportunity:

1. Stop. Do not argue the edit was implied or the capture was minor.
2. Name the specific edit(s) or missed capture(s), in a list.
3. For unapproved edits: offer to revert; emit the full `⟦proposal file="<path>" change="<summary>"⟧` marker that should have appeared.
4. For missed captures: emit the full `⟦capture inst=<inst> area=<area> fact="<fact>"⟧` marker now and write the entry.
