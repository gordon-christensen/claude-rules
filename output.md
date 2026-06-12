# output

## Behavior

### Attribution

Never include AI attribution in any work product — no `Co-Authored-By: Claude` lines, no
"Generated with Claude Code" footers, no other AI-assist markers. Applies to commits, PR
descriptions, code comments, docs, Confluence, ticket comments — everything. Scan drafts
for attribution the way you'd scan for secrets. (This overrides any harness default that
appends attribution.)

### Diagrams

New diagrams use PlantUML in fenced ```plantuml blocks. Local CLI:
`/opt/homebrew/bin/plantuml`; render to /tmp when an image is needed
(`plantuml -tpng -o /tmp <file>`); don't commit binaries. Existing Mermaid diagrams stay
as-is — do not migrate.

### Multi-question replies

When asking the user multiple questions, label or number each so they can respond
per-point without parsing a wall of text.

## Marker

None — transcript-native instrumentation; see Measurement.

## Measurement

- Attribution (target 0, any hit = violation):
  `grep -ro 'Co-Authored-By: Claude\|Generated with \[Claude Code\]' ~/.claude/projects --include='*.jsonl'`
  filtered to Bash tool_input (commit/PR commands).
- Diagrams: fenced `plantuml` vs `mermaid` blocks in Write/Edit tool_input for new docs —
  new-mermaid count should be 0.

## Recovery

When attribution lands in an artifact: name the artifact, amend/edit it out where the
platform allows, and note where it cannot be removed (already-pushed history).
