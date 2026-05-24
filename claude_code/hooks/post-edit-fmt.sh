#!/usr/bin/env bash
# Post-edit auto-formatter hook for Claude Code.
# Triggered after Write/Edit/MultiEdit tool use.
#
# Receives JSON on stdin; exits 0 (success) or 1 (non-blocking warn).
# Does NOT block the edit — formatting errors are informational only.
#
# Wire up in ~/.claude/settings.json under hooks.PostToolUse:
#   {
#     "matcher": "Write|Edit|MultiEdit",
#     "hooks": [{ "type": "command", "command": "~/.claude/hooks/post-edit-fmt.sh" }]
#   }

set -euo pipefail

# Parse the edited file path from stdin JSON
FILE_PATH=$(jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)

if [[ -z "$FILE_PATH" || ! -f "$FILE_PATH" ]]; then
    exit 0
fi

EXT="${FILE_PATH##*.}"

case "$EXT" in
    py)
        if command -v ruff &>/dev/null; then
            ruff format --quiet "$FILE_PATH" 2>/dev/null || true
            ruff check --fix --quiet "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    js|jsx|ts|tsx|json|css|md|yaml|yml)
        # Only run prettier if a config exists nearby (respects project opt-in)
        if command -v prettier &>/dev/null && \
           { [[ -f ".prettierrc" ]] || [[ -f ".prettierrc.json" ]] || \
             [[ -f ".prettierrc.js" ]] || [[ -f "prettier.config.js" ]] || \
             grep -q '"prettier"' package.json 2>/dev/null; }; then
            prettier --write --log-level silent "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    tf|tfvars)
        if command -v terraform &>/dev/null; then
            terraform fmt -write=true "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
esac

exit 0
