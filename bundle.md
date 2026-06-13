# bundle

## Behavior

`gordon-christensen.txt` is a flattened, single-file copy of the operating rules,
built for delivery to Claude chat (claude.ai project / custom instructions) where
the per-file auto-loading of `~/.claude/rules/` is not available.

It is a generated artifact, not a source of truth. `combine.sh` produces it by
prepending a chat-adaptation preamble, then concatenating `README.md` and the rule
files verbatim in the canonical order of the README "Rule index". The preamble
reframes the CLI-only machinery for the chat audience: it marks the Measurement
sections and Hooks as inert, keeps the `⟦…⟧` markers as self-administered checklists
rather than grep targets, and translates CLI tool references to the chat tools
(code-execution container, web search, Project knowledge). The bundle-maintenance
rule (`bundle.md`, this file) is deliberately left out of the bundle — it documents
the build, not chat behavior.

### Keep it in sync

`gordon-christensen.txt` goes stale the moment any rule changes. Whenever you add,
remove, or edit a rule `.md` in this tree (or edit `README.md`):

- Re-run `./combine.sh` and commit the regenerated `gordon-christensen.txt` in the
  same change as the rule edit.
- If you add or remove a rule file, update the `FILES` array in `combine.sh` to
  match, then re-run it.
- The chat-adaptation preamble is authored inline in `combine.sh`; revise it there
  (not in the generated `.txt`) when chat capabilities or the marker reframing change.
- Never hand-edit `gordon-christensen.txt` — edits there are overwritten on the next
  run and never reach the source rules.

`combine.sh` and `gordon-christensen.txt` are not `.md` files, so they are not
auto-loaded into sessions; only the source rules are.

## Marker

None — there is no per-turn behavior to instrument. The sync obligation is enforced
at review time: a rule change with no corresponding `gordon-christensen.txt` update
in the same commit is the violation signal.

## Measurement

- Staleness: `gordon-christensen.txt` older than any tracked rule `.md` —
  `find . -name '*.md' -newer gordon-christensen.txt`; non-empty output = stale bundle.
- Drift: re-run `./combine.sh`, then `git diff --exit-code gordon-christensen.txt`;
  a non-empty diff means the committed bundle does not match its sources.

## Recovery

When the bundle is found stale or drifted: re-run `./combine.sh`, review the diff,
and commit the regenerated `gordon-christensen.txt`, naming the rule change it was
missing.
