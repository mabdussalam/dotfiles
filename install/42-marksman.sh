#!/usr/bin/env bash
# marksman — Markdown language server (github.com/artempyanykh/marksman).
# Released as a single static Linux binary; we fetch the latest release into
# ~/.local/bin, which .zshrc adds to PATH.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

mkdir -p "$HOME/.local/bin"

if [[ -x "$HOME/.local/bin/marksman" ]]; then
    log "marksman already installed."
    exit 0
fi

log "Installing marksman (Markdown LSP)…"
curl -fsSL -o "$HOME/.local/bin/marksman" \
    https://github.com/artempyanykh/marksman/releases/latest/download/marksman-linux-x64
chmod +x "$HOME/.local/bin/marksman"
log "marksman installed."
