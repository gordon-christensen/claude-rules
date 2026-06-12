# pr-commits

## Behavior

Apply this shape when the change has a "why" worth explaining — anything an engineer would want to defend in review, or that another engineer would benefit from understanding later. Bot PRs (Renovate, Dependabot), trivial typo or lint-only fixes, mechanical reverts, and cherry-picks need only a clear subject line.

### Two documents

- **Long-form** — a narrative write-up stored somewhere linkable (wiki, repo, etc.). Write and publish this **before** opening the PR so the link in the terse PR description is live at PR-open time.
- **Terse PR description and commit body** — same text in both places. Length-capped, scannable.

### Terse structure

Three sections, in order:

1. **Context** — at most **5 sentences**. The why: what was wrong, what changed, what it is now.
2. **Details** — at most **5 single-sentence bullets**. The what: each bullet one self-contained statement. The last bullet links the long-form: `For more details, see <long-form url>.`
3. **Testing** — at most **5 single-sentence bullets**. Each bullet one verification step or piece of evidence.

Each bullet is one sentence — no semicolons connecting independent clauses, no multi-paragraph bullets. Before posting, emit the ⟦counts⟧ marker (see Marker section) and redraft until every count is within limit.

Reading level target: grade 11–12 (technical but skimmable). Avoid stacked subordinate clauses and abstract chain verbs ("exposed a latent bug" → "has a bug that strips the URL"). Active voice, concrete subjects.

### Open tasks — native, not markdown

The terse description **must not** include a markdown checklist of open tasks. Native task UIs are the source of truth.

- **PR-gating tasks** (verify before apply/merge): create as native PR tasks in your code-review platform. At most **5 tasks**, single-sentence each, **issue-specific only**.
- **Ticket-gating tasks** (post-merge verification): add to the ticket tracker. At most **5 tasks**, single-sentence each, **issue-specific only**.

### Follow-up commits on an open PR

When a PR receives a follow-up commit (fix, refactor, scope extension), do **not** rewrite the existing terse description or long-form. Append a new section to both, separated from the previous content by a horizontal rule (`---` in markdown).

- **Long-form** — append `---` then `## Commit <SHA>` (10-char short SHA) at the bottom, before any "Related" section. Small Context / Fix / Testing skeleton — 2–3 short paragraphs is typical.
- **Terse PR description + commit body** — append `---` then `## Commit <SHA>` section after the existing Testing block, with:
  - **Context** — at most **3 sentences**
  - **Details** — at most **2 single-sentence bullets**
  - **Testing** — at most **2 single-sentence bullets**

Emit the ⟦counts⟧ marker for the follow-up section's limits.

Rationale: preserves the PR's narrative arc — what was originally proposed vs. what showed up later — instead of overwriting the original each iteration. The HR makes the evolution scan cleanly top-to-bottom.

### Scope discipline

**Issue-specific** means in scope of the ticket title and description (or, for no-ticket PRs, what was explicitly agreed with the user as this PR's scope). Anything outside that — even if it shares a root cause, is the same one-line fix, or "while you're in there" — is **Related**, not issue-specific.

Across the PR and the PR tasks: **issue-specific only**. Collateral and related follow-ups (same root cause, different ticket; hardening ideas; related-but-deferred) live in a **"Related" subsection of the long-form**, never in the visible-to-others artifacts.

## Marker

After drafting any terse PR description / commit body governed by this rule (initial or
follow-up section):

```
⟦counts kind=<initial|followup> ctx=<sentences> det=<bullets> test=<bullets>⟧
```

Limits: `kind=initial` → `ctx≤5 det≤5 test≤5`; `kind=followup` → `ctx≤3 det≤2 test≤2`. A marker
showing an over-limit count means redraft before posting — the marker states reality, the
limit gates the post.

## Measurement

- Emission: `grep -roE '⟦counts kind=(initial|followup) ctx=[0-9]+ det=[0-9]+ test=[0-9]+⟧' ~/.claude/projects --include='*.jsonl'`.
- Denominator: PR-creation / commit events in Bash tool_input (approximate).
- Violation: any emission exceeding its kind's limits that was followed by posting anyway — regex-detectable per kind.
- v1 baseline: 21 emissions / 12 sessions.

## Recovery

### Recovery from a count or scope miss

When the user identifies a section over its limit, or content that's Related rather than issue-specific:

1. Stop. Do not argue the extra sentence/bullet was necessary or the extra scope was harmless.
2. Name the specific overage or scope creep, by section.
3. Redraft to fixed state — counts within limit, scope items moved to the Related subsection of the long-form.
4. Re-emit the full `⟦counts kind=<initial|followup> ctx=N det=N test=N⟧` marker with the redrafted counts.
