#!/usr/bin/env bash
# npm global tools — LSP servers consumed by Claude Code's official plugins,
# plus OpenSpec for spec-driven workflows.
# Package list: install/lists/npm-globals.txt
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

# Make nvm-installed node/npm available when this module runs standalone.
# (When invoked by the orchestrator after 70-node.sh, PATH is already set.)
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ -s "$NVM_DIR/nvm.sh" ]] && ! command -v npm &>/dev/null; then
    set +euo pipefail
    # shellcheck source=/dev/null
    \. "$NVM_DIR/nvm.sh"
    set -euo pipefail
fi

command -v npm &>/dev/null || die "npm not on PATH — run install/70-node.sh first."

while read -r pkg; do
    if npm ls -g --depth=0 "$pkg" &>/dev/null; then
        log "$pkg already installed."
    else
        log "Installing $pkg…"
        npm install -g "$pkg"
    fi
done < <(read_list npm-globals)
