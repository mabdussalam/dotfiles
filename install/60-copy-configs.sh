#!/usr/bin/env bash
# Copy zsh and VS Code dotfiles into place (bootstrap semantics).
# Existing targets are preserved by default — re-running is a no-op for any
# path that already exists, so local tweaks survive. Set FORCE=1 to overwrite,
# backing the existing target up to <target>.bak first.
#
# Claude Code configs are handled by 61-copy-claude.sh.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

# Zsh configs
_copy "$REPO/zsh/.zshrc"  "$HOME/.zshrc"
_copy "$REPO/zsh/.zimrc"  "$HOME/.zimrc"
_copy "$REPO/zsh/.zshenv" "$HOME/.zshenv"

# VS Code (Linux path; directory is created by _copy helper)
VSCODE_USER_DIR="$HOME/.config/Code/User"
_copy "$REPO/vscode/settings.json"    "$VSCODE_USER_DIR/settings.json"
_copy "$REPO/vscode/keybindings.json" "$VSCODE_USER_DIR/keybindings.json"

log "Config copy complete."
