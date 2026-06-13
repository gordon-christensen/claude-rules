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
        # A bare clone to serve as the REPO_URL install.sh clones from.
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


class TestIdempotentRerun(InstallTestBase):
    def test_second_run_succeeds_and_keeps_files(self):
        first = self.run_install()
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_install()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue((self.install_dir / "verification.md").is_file())


class TestHooksExecutable(InstallTestBase):
    def test_hook_scripts_are_executable(self):
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ("halt-reminder.py", "turn-audit.py"):
            p = self.install_dir / "hooks" / name
            self.assertTrue(os.access(p, os.X_OK), f"{name} not executable")


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
