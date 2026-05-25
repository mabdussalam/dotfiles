#!/usr/bin/env bash
# nvm + Node — install nvm (if missing), then install the Node version
# specified by repo-root .nvmrc (lts/*) and pin it as the default.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
    log "nvm not found. Installing latest nvm…"
    # PROFILE=/dev/null prevents the installer from editing ~/.bashrc/~/.zshrc;
    # our .zshrc/.zshenv handle nvm sourcing themselves.
    NVM_INSTALL_URL="https://raw.githubusercontent.com/nvm-sh/nvm/HEAD/install.sh"
    curl -fsSL "$NVM_INSTALL_URL" | PROFILE=/dev/null bash
    log "nvm installed."
else
    log "nvm already installed."
fi

# Load nvm into this session (without modifying shell profile again).
# nvm.sh references unset vars internally, so relax errexit/nounset/pipefail
# JUST for the source line, then restore — we still want errexit to catch
# failures from `nvm install` / `nvm alias` below.
export NVM_DIR="$HOME/.nvm"
set +euo pipefail
# shellcheck source=/dev/null
\. "$NVM_DIR/nvm.sh"
set -euo pipefail

log "nvm version: $(nvm --version)"

# Install Node version specified by .nvmrc (lts/*), run from repo root so
# nvm picks up the right file regardless of caller cwd.
log "Installing Node from .nvmrc…"
(cd "$REPO" && nvm install)
nvm alias default 'lts/*'
log "Node ready: $(node --version), npm: $(npm --version)"
