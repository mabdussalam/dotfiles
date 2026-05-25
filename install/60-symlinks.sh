#!/usr/bin/env bash
# Symlink all dotfiles into place.
# Handles zsh, VS Code, and Claude Code configs. Existing real files are
# backed up to <file>.bak; existing symlinks pointing elsewhere are replaced.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

# Helper: symlink $1 → $2, backing up an existing real file.
_link() {
    local src="$1"
    local dst="$2"
    local dst_dir
    dst_dir="$(dirname "$dst")"

    mkdir -p "$dst_dir"

    # If dst already points to src exactly, nothing to do
    if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then
        log "[skip] $dst already linked"
        return
    fi

    # Back up existing real file (not a symlink)
    if [[ -e "$dst" && ! -L "$dst" ]]; then
        log "[backup] $dst → ${dst}.bak"
        mv "$dst" "${dst}.bak"
    fi

    # Remove stale symlink pointing elsewhere
    if [[ -L "$dst" ]]; then
        rm "$dst"
    fi

    ln -sfn "$src" "$dst"
    log "[linked] $src → $dst"
}

# Zsh configs
_link "$REPO/zsh/.zshrc"  "$HOME/.zshrc"
_link "$REPO/zsh/.zimrc"  "$HOME/.zimrc"
_link "$REPO/zsh/.zshenv" "$HOME/.zshenv"

# VS Code (Linux path; directory is created by _link helper)
VSCODE_USER_DIR="$HOME/.config/Code/User"
_link "$REPO/vscode/settings.json"    "$VSCODE_USER_DIR/settings.json"
_link "$REPO/vscode/keybindings.json" "$VSCODE_USER_DIR/keybindings.json"

# Claude Code — link every file/dir present under claude_code/, skip README files
CLAUDE_DIR="$HOME/.claude"
mkdir -p "$CLAUDE_DIR"
for item in "$REPO/claude_code/"*; do
    basename_item="$(basename "$item")"
    # Skip README files (any capitalisation)
    if [[ "${basename_item,,}" == readme* ]]; then
        log "[skip] claude_code/$basename_item (README)"
        continue
    fi
    _link "$item" "$CLAUDE_DIR/$basename_item"
done

log "Config symlinking complete."
