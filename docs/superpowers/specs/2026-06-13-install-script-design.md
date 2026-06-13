# Install Script Design

**Date:** 2026-06-13  
**Repo:** `github.com/gordon-christensen/claude-rules`  
**Branch:** `main`

## Goal

Add two files to `main` so anyone (or any new machine) can install the gordon-christensen Claude Code rules with a single command and have the hooks automatically wired into `~/.claude/settings.json`.

## Files

### `install.sh`

A `curl -fsSL .../install.sh | bash`-compatible script. Idempotent: safe to re-run for upgrades.

**Steps:**

1. `set -euo pipefail` — fail fast on any error.
2. **Clone or update:**
   - If `~/.claude/rules/gordon-christensen/.git` exists: `git -C <dir> pull --ff-only`
   - Otherwise: `git clone --depth=1 https://github.com/gordon-christensen/claude-rules.git ~/.claude/rules/gordon-christensen`
3. `chmod +x hooks/*.py` — ensure the two hook scripts are executable.
4. **Wire `~/.claude/settings.json`** via an inline `python3` heredoc (stdlib only — `json`, `pathlib`):
   - Read `~/.claude/settings.json`; treat missing file as `{}`.
   - Overwrite `hooks.PostToolUseFailure` with the `halt-reminder.py` entry.
   - Overwrite `hooks.Stop` with the `turn-audit.py` entry.
   - Leave all other top-level keys untouched.
   - Write back with 2-space indent + trailing newline.
5. Print a "done — restart Claude Code" message.

**Hook entries written:**

```json
"PostToolUseFailure": [
  {"hooks": [{"type": "command", "command": "python3 ~/.claude/rules/gordon-christensen/hooks/halt-reminder.py"}]}
],
"Stop": [
  {"hooks": [{"type": "command", "command": "python3 ~/.claude/rules/gordon-christensen/hooks/turn-audit.py"}]}
]
```

**Requirements:** `git`, `python3`, `curl` (for the caller).

### `INSTALL.txt`

Plain-text installation guide. Contains:

- The one-liner install command
- What gets installed and where
- Upgrade instructions (re-run the one-liner, or `git pull` directly)
- Requirements

## Upgrade Story

Re-running `install.sh` pulls the latest `main` via `git pull --ff-only`. The settings wiring is also re-applied (idempotent overwrite), so any hook path changes are picked up automatically.

## What Is Not In Scope

- Uninstall
- Wiring anything in `settings.json` beyond the two hooks
- Supporting non-`~/.claude` install targets
