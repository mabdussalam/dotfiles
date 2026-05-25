#!/usr/bin/env bash
# Python tools via `uv tool install` — each gets its own isolated venv and
# its bin shimmed onto PATH (uv tool's shim dir is ~/.local/bin).
# Tool list: install/lists/uv-tools.txt
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

export PATH="$HOME/.local/bin:$PATH"

command -v uv &>/dev/null || die "uv not on PATH — run install/41-uv.sh first."

while read -r tool; do
    if uv tool list 2>/dev/null | grep -q "^$tool "; then
        log "$tool already installed via uv."
    else
        log "Installing $tool via 'uv tool install'…"
        uv tool install "$tool" || warn "uv tool install $tool failed (continuing)."
    fi
done < <(read_list uv-tools)
