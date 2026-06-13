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
