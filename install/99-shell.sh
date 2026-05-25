#!/usr/bin/env bash
# Default shell → zsh via chsh. Handles the common WSL/container case where
# chsh fails by printing the manual fallback instead of aborting the script.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

ZSH_PATH="$(command -v zsh)" || die "zsh not on PATH — run install/00-apt-base.sh first."

if [[ "$SHELL" == "$ZSH_PATH" ]]; then
    log "Default shell is already zsh ($ZSH_PATH). Nothing to do."
    exit 0
fi

# Ensure zsh is in /etc/shells
if ! grep -qF "$ZSH_PATH" /etc/shells 2>/dev/null; then
    log "Adding $ZSH_PATH to /etc/shells…"
    echo "$ZSH_PATH" | sudo tee -a /etc/shells >/dev/null
fi

log "Running: chsh -s $ZSH_PATH"
if chsh -s "$ZSH_PATH" 2>/dev/null; then
    log "Default shell changed to zsh. Re-login or open a new terminal for it to take effect."
else
    printf '\n'
    warn "chsh failed (common in some WSL setups or containers)."
    printf '   To switch to zsh manually, add the following to the end of your ~/.bashrc:\n\n'
    printf '       export SHELL=%s\n' "$(command -v zsh)"
    printf '       exec \\$(command -v zsh) -l\n\n'
fi
