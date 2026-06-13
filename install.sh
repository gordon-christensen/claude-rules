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

chmod +x "$INSTALL_DIR"/hooks/*.py

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
