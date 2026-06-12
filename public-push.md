# public-push

## Behavior

Claude never pushes to or opens PRs against a public-facing remote. The user runs the push and opens the PR.

### Scope

A "public-facing remote" is any git remote where pushed commits become accessible outside the user's organization. Classify in this priority order:

1. **Internal host** — institution-controlled DNS hosting a private forge (self-managed Bitbucket Data Center / Stash, GitHub Enterprise, GitLab self-managed, etc.). Not public-facing; normal authorization rules apply.
2. **Public-tenancy host, institution-owned workspace** — `github.com`, `gitlab.com`, `bitbucket.org`. If the *workspace/owner* is identified as institution-owned in the loaded institution's on-demand tree (via that institution's source-map, services documentation, or equivalent), the workspace is not public-facing. The rule itself names no institution and no specific workspace — classification is delegated to the on-demand tree. Note: the workspace, not just the host — other owners on the same host remain public. If the on-demand tree is not loaded, skip this tier and apply tier 3.
3. **Public-tenancy host, no institution exception** — any `github.com/*`, `gitlab.com/*`, `bitbucket.org/<unknown-owner>/*`. Public-facing.
4. **Unclassifiable** — treat as public-facing.

### Why this rule is absolute

GitHub does not auto-garbage-collect dangling commits. After a push, the commit SHA remains accessible via `https://<host>/<owner>/<repo>/commit/<sha>` even after:

- Branch deletion
- PR closure (declined or merged-then-reverted)
- History rewriting on the public-facing branch

Remediation requires platform-support intervention plus credential rotation for any sensitive value exposed. Forks are independent and outside the original owner's reach. **The cost of an accidental public push is permanent and outside Claude's ability to fix.** This is exactly the class of action where Claude's judgment about "safety to push" is the failure mode the rule guards against. The human gate is not a redundancy — it is the only protection.

### What Claude does instead

For any change destined for a public-facing remote:

1. Make the branch locally.
2. Stage and commit per [pr-and-commits.md](pr-and-commits.md).
3. Prepare the PR description.
4. Report to the user: remote URL, branch name, commit SHA, summary of the diff, and the exact commands the user should run, e.g.
   ```
   git -C <repo path> push -u origin <branch>
   gh pr create --title "..." --body "..."
   ```
5. Stop. The user pushes and opens the PR.

Claude may continue with unrelated tasks after reporting.

### What does not override this rule

- **Explicit user instruction to push.** "Push and PR" is the user's general direction. It does NOT authorize Claude to perform the push or open the PR on a public-facing remote. The user runs both.
- **"It looks safe" / "I've reviewed it."** Claude's classification of "safe to push to public" is the failure mode this rule guards against.
- **Auto mode.** Auto mode broadens autonomy for reversible local work; it never broadens it for irreversible public-disclosure actions.
- **Time pressure or convenience.** Public push is permanent. Convenience is not.
- **Delegated execution.** Dispatching a subagent, triggering a CI job, or invoking any tool that would perform the push on Claude's behalf is the same as pushing directly. The prohibition applies to the outcome, not the mechanism.

## Marker

Before any tool call that would push to or open a PR against a public-facing remote —
then stop unconditionally; the user runs the commands:

```
⟦push-halt remote="<remote url>" branch=<branch> act=<push|pr|branch>⟧
```

The same message reports: commit SHA(s), diff summary, and the exact `git push` /
`gh pr create` commands for the user, per "What Claude does instead" above. Do not
execute, and do not poll for confirmation — the rule is unconditional.

## Measurement

- Emission: `grep -roE '⟦push-halt remote="[^"]*" branch=[^ ]+ act=(push|pr|branch)⟧' ~/.claude/projects --include='*.jsonl'`.
- Violation query: Bash tool_input containing `git push` or `gh pr create` against
  public-tenancy hosts with no prior push-halt in the session — any hit is a violation.
- v1 baseline: 5 halts / 4 sessions; expected rare.

## Recovery

### Recovery from a public-push miss

If Claude pushed to or opened a PR on a public-facing remote without the halt declaration. Note: the general rollback step from errors.md does not apply here — deletion does not reverse public disclosure and may complicate remediation.

1. Stop. Do not push further commits. Do not force-push or amend to "fix" the public branch — those compound the issue and do not remove the original commits from cache.
2. Name the action: full remote URL, branch name, full commit SHA(s) pushed, PR number if opened.
3. Surface to the user immediately. The user decides remediation: history rewrite, platform-support contact, credential rotation if anything sensitive was exposed.
4. Do not delete the branch as cleanup. Deletion does not remove the commits from cache and may complicate support's remediation.
