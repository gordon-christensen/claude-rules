# Install Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `install.sh` and `INSTALL.txt` to the `main` branch so the gordon-christensen Claude Code rules can be installed (and upgraded) with a single `curl … | bash` command that also wires the two hooks into `~/.claude/settings.json`.

**Architecture:** `install.sh` is an idempotent bash script: clone-or-pull the repo into `~/.claude/rules/gordon-christensen`, `chmod +x` the hook scripts, then merge two hook entries into `~/.claude/settings.json` via an inline `python3` heredoc (stdlib only). The install dir, repo URL, and settings path are read from environment variables that default to the production values, which lets the test suite run the real script against temp directories and a local git remote without touching the user's environment.

**Tech Stack:** bash, git, `python3` (stdlib `json`/`pathlib`), Python `unittest` + `subprocess` for tests (matching the existing `tests/test_hooks.py` style).

---

## File Structure

| File | Responsibility |
|---|---|
| `install.sh` (create) | The installer. Clone-or-pull, chmod, settings wiring. Env-var overridable. |
| `INSTALL.txt` (create) | Plain-text install/upgrade instructions. |
| `tests/test_install.py` (create) | End-to-end tests: run `install.sh` against temp dirs + a local bare-repo remote; assert files land and settings.json is wired/merged correctly. |

The settings-wiring Python is inline in `install.sh` (per the approved spec). It is exercised end-to-end through the install script rather than as a separate unit — `tests/test_install.py` covers every wiring branch (no file, empty file, existing unrelated keys, existing hooks overwritten).

---

## Conventions used in every task

- All commands run from the worktree root: `~/.claude/rules/gordon.christensen/.claude/worktrees/expressive-jumping-mitten`
- Run tests with: `python3 -m unittest tests.test_install -v`
- `install.sh` honors these env vars (defaults in parentheses):
  - `REPO_URL` (`https://github.com/gordon-christensen/claude-rules.git`)
  - `INSTALL_DIR` (`$HOME/.claude/rules/gordon-christensen`)
  - `SETTINGS_FILE` (`$HOME/.claude/settings.json`)

---

## Task 1: Test harness + first failing test (fresh clone copies files)

**Files:**
- Create: `tests/test_install.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_install.py` with a base class that builds a local bare git remote to clone from, plus the first test:

```python
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO / "install.sh"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


class InstallTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # A fake "published repo" with the files install.sh expects to deliver.
        self.src = self.root / "src"
        self.src.mkdir()
        (self.src / "verification.md").write_text("# verification\n")
        hooks = self.src / "hooks"
        hooks.mkdir()
        (hooks / "halt-reminder.py").write_text("#!/usr/bin/env python3\n")
        (hooks / "turn-audit.py").write_text("#!/usr/bin/env python3\n")
        run(["git", "-C", str(self.src), "init", "-q", "-b", "main"])
        run(["git", "-C", str(self.src), "add", "-A"])
        run(["git", "-C", str(self.src), "-c", "user.email=t@t", "-c",
             "user.name=t", "commit", "-q", "-m", "init"])
        # A bare clone to serve as the cl, the REPO_URL install.sh clones from.
        self.remote = self.root / "remote.git"
        run(["git", "clone", "-q", "--bare", str(self.src), str(self.remote)])

        self.install_dir = self.root / "rules" / "gordon-christensen"
        self.settings = self.root / "settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def run_install(self):
        env = {
            **os.environ,
            "REPO_URL": str(self.remote),
            "INSTALL_DIR": str(self.install_dir),
            "SETTINGS_FILE": str(self.settings),
        }
        return run(["bash", str(INSTALL_SH)], env=env)


class TestFreshClone(InstallTestBase):
    def test_clone_copies_rule_files(self):
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.install_dir / "verification.md").is_file())
        self.assertTrue((self.install_dir / "hooks" / "halt-reminder.py").is_file())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests.test_install.TestFreshClone -v`
Expected: FAIL — `install.sh` does not exist yet, so `bash` exits non-zero (`returncode != 0`).

- [ ] **Step 3: Create the minimal `install.sh` to pass**

Create `install.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/gordon-christensen/claude-rules.git}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.claude/rules/gordon-christensen}"
SETTINGS_FILE="${SETTINGS_FILE:-$HOME/.claude/settings.json}"

if [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" pull --ff-only
else
  git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
fi
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m unittest tests.test_install.TestFreshClone -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add install.sh tests/test_install.py
git commit -m "Add install.sh skeleton: clone repo into INSTALL_DIR"
```

---

## Task 2: Idempotent re-run (pull instead of re-clone)

**Files:**
- Modify: `tests/test_install.py` (add a test class)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_install.py`:

```python
class TestIdempotentRerun(InstallTestBase):
    def test_second_run_succeeds_and_keeps_files(self):
        first = self.run_install()
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_install()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue((self.install_dir / "verification.md").is_file())
```

- [ ] **Step 2: Run the test to verify it passes (or fails)**

Run: `python3 -m unittest tests.test_install.TestIdempotentRerun -v`
Expected: PASS already — the `if [ -d "$INSTALL_DIR/.git" ]` branch from Task 1 handles the re-run via `git pull --ff-only`. (A `--depth=1` clone can pull from the same remote with no new commits and exit 0.)

If it FAILS (e.g. `pull --ff-only` errors on the shallow clone with no upstream tracking), fix `install.sh` by setting an explicit upstream in the clone branch, then re-run:

```bash
# inside install.sh, replace the clone line's effect by ensuring tracking exists
git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
git -C "$INSTALL_DIR" branch --set-upstream-to=origin/main main 2>/dev/null || true
```

- [ ] **Step 3: Commit**

```bash
git add install.sh tests/test_install.py
git commit -m "Verify install.sh is idempotent on re-run"
```

---

## Task 3: chmod +x the hook scripts

**Files:**
- Modify: `install.sh`
- Modify: `tests/test_install.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_install.py`:

```python
class TestHooksExecutable(InstallTestBase):
    def test_hook_scripts_are_executable(self):
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ("halt-reminder.py", "turn-audit.py"):
            p = self.install_dir / "hooks" / name
            self.assertTrue(os.access(p, os.X_OK), f"{name} not executable")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests.test_install.TestHooksExecutable -v`
Expected: FAIL — the cloned files are not marked executable (committed without the +x bit in the fixture).

- [ ] **Step 3: Add the chmod to `install.sh`**

Append after the clone/pull block:

```bash
chmod +x "$INSTALL_DIR"/hooks/*.py
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m unittest tests.test_install.TestHooksExecutable -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add install.sh tests/test_install.py
git commit -m "install.sh: mark hook scripts executable"
```

---

## Task 4: Wire settings.json — create when absent

**Files:**
- Modify: `install.sh`
- Modify: `tests/test_install.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_install.py`:

```python
class TestSettingsCreated(InstallTestBase):
    def test_creates_settings_with_both_hooks(self):
        self.assertFalse(self.settings.exists())
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(self.settings.read_text())
        halt = data["hooks"]["PostToolUseFailure"][0]["hooks"][0]["command"]
        stop = data["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertEqual(
            halt, f"python3 {self.install_dir}/hooks/halt-reminder.py")
        self.assertEqual(
            stop, f"python3 {self.install_dir}/hooks/turn-audit.py")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests.test_install.TestSettingsCreated -v`
Expected: FAIL — `install.sh` does not write `SETTINGS_FILE` yet; `self.settings.read_text()` raises `FileNotFoundError`.

- [ ] **Step 3: Add the settings-wiring heredoc to `install.sh`**

Append to `install.sh`:

```bash
INSTALL_DIR="$INSTALL_DIR" SETTINGS_FILE="$SETTINGS_FILE" python3 <<'PY'
import json
import os
from pathlib import Path

install_dir = os.environ["INSTALL_DIR"]
settings = Path(os.environ["SETTINGS_FILE"])

data = json.loads(settings.read_text()) if settings.exists() else {}
hooks = data.setdefault("hooks", {})
hooks["PostToolUseFailure"] = [
    {"hooks": [{"type": "command",
                "command": f"python3 {install_dir}/hooks/halt-reminder.py"}]}
]
hooks["Stop"] = [
    {"hooks": [{"type": "command",
                "command": f"python3 {install_dir}/hooks/turn-audit.py"}]}
]
settings.parent.mkdir(parents=True, exist_ok=True)
settings.write_text(json.dumps(data, indent=2) + "\n")
PY

echo "Installed to $INSTALL_DIR and wired hooks into $SETTINGS_FILE. Restart Claude Code."
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m unittest tests.test_install.TestSettingsCreated -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add install.sh tests/test_install.py
git commit -m "install.sh: wire hooks into settings.json (create when absent)"
```

---

## Task 5: Wire settings.json — merge, preserving existing keys

**Files:**
- Modify: `tests/test_install.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_install.py`:

```python
class TestSettingsMerge(InstallTestBase):
    def test_preserves_other_keys_and_overwrites_stale_hooks(self):
        self.settings.write_text(json.dumps({
            "model": "opus",
            "permissions": {"defaultMode": "auto"},
            "hooks": {
                "Stop": [{"hooks": [{"type": "command",
                                     "command": "python3 /old/turn-audit.py"}]}],
                "PreToolUse": [{"hooks": [{"type": "command",
                                           "command": "echo keep-me"}]}],
            },
        }, indent=2))
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(self.settings.read_text())
        # untouched top-level keys preserved
        self.assertEqual(data["model"], "opus")
        self.assertEqual(data["permissions"]["defaultMode"], "auto")
        # unrelated hook preserved
        self.assertEqual(
            data["hooks"]["PreToolUse"][0]["hooks"][0]["command"], "echo keep-me")
        # stale Stop hook overwritten to the new path
        self.assertEqual(
            data["hooks"]["Stop"][0]["hooks"][0]["command"],
            f"python3 {self.install_dir}/hooks/turn-audit.py")
        # PostToolUseFailure added
        self.assertIn("PostToolUseFailure", data["hooks"])
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `python3 -m unittest tests.test_install.TestSettingsMerge -v`
Expected: PASS — the Task 4 heredoc uses `setdefault("hooks", {})` and assigns only the two specific keys, so other top-level keys and unrelated hook events survive. This test locks that behavior in.

If it FAILS, the heredoc is replacing more than it should; fix it to mutate only `hooks["PostToolUseFailure"]` and `hooks["Stop"]`, then re-run.

- [ ] **Step 3: Commit**

```bash
git add tests/test_install.py
git commit -m "Verify settings.json merge preserves unrelated keys"
```

---

## Task 6: Write INSTALL.txt

**Files:**
- Create: `INSTALL.txt`

- [ ] **Step 1: Write INSTALL.txt**

```text
gordon-christensen — Claude Code operating rules
=================================================

Install (or upgrade) with one command:

    curl -fsSL https://raw.githubusercontent.com/gordon-christensen/claude-rules/main/install.sh | bash

What it does
------------
- Clones the rules into ~/.claude/rules/gordon-christensen
  (re-running pulls the latest main instead of re-cloning).
- Marks the hook scripts executable.
- Wires two hooks into ~/.claude/settings.json, preserving any
  other settings you already have:
    PostToolUseFailure -> hooks/halt-reminder.py
    Stop               -> hooks/turn-audit.py

Upgrade
-------
Re-run the one-liner above, or pull directly:

    git -C ~/.claude/rules/gordon-christensen pull --ff-only

After installing or upgrading, restart Claude Code so the rules
and hooks take effect.

Requirements
------------
git, python3, and curl (for the one-liner).
```

- [ ] **Step 2: Sanity-check the file**

Run: `cat INSTALL.txt`
Expected: the content above, no placeholders.

- [ ] **Step 3: Commit**

```bash
git add INSTALL.txt
git commit -m "Add INSTALL.txt with install + upgrade instructions"
```

---

## Task 7: Full suite green + final review

**Files:** none (verification only)

- [ ] **Step 1: Run the whole install test suite**

Run: `python3 -m unittest tests.test_install -v`
Expected: all tests PASS (TestFreshClone, TestIdempotentRerun, TestHooksExecutable, TestSettingsCreated, TestSettingsMerge).

- [ ] **Step 2: Run the existing hook tests to confirm no regression**

Run: `python3 -m unittest discover -s tests -v`
Expected: install tests + existing `test_hooks.py` all PASS.

- [ ] **Step 3: Lint install.sh**

Run: `bash -n install.sh` (syntax check). If `shellcheck` is available: `shellcheck install.sh`.
Expected: no syntax errors.

- [ ] **Step 4: Final commit if anything changed**

```bash
git add -A
git commit -m "Install script: full suite green" || echo "nothing to commit"
```

---

## Self-Review

**Spec coverage:**
- "clone or update" → Tasks 1, 2 ✓
- "chmod +x hooks" → Task 3 ✓
- "wire settings.json, merge not replace" → Tasks 4, 5 ✓
- "INSTALL.txt with one-liner, what/where, upgrade, requirements" → Task 6 ✓
- "python3 stdlib only" → Task 4 heredoc uses `json`/`os`/`pathlib` ✓
- Out of scope per spec (uninstall, non-`~/.claude` targets beyond the test override) → not included ✓

**Deviation from approved spec:** the env-var overrides (`REPO_URL`/`INSTALL_DIR`/`SETTINGS_FILE`) are an addition for testability; defaults equal the spec's hardcoded values, so production behavior is unchanged. Flagged to the user.

**Placeholder scan:** none — every code/test step contains complete content.

**Type/name consistency:** `INSTALL_DIR`, `SETTINGS_FILE`, `REPO_URL`, `run()`, `InstallTestBase`, `run_install()` used consistently across all tasks. Hook command strings match between Task 4 implementation and Task 4/5 assertions.
