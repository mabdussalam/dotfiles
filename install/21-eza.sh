#!/usr/bin/env bash
# eza — modern ls replacement, installed from the official deb.gierens.de repo.
# Upstream guide: https://github.com/eza-community/eza/blob/main/INSTALL.md
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

is_debian || { log "apt-get not found — skipping eza (non-Debian system)."; exit 0; }

if command -v eza &>/dev/null; then
    log "eza already installed: $(eza --version | head -1)"
    exit 0
fi

log "Adding eza apt repo and installing eza…"
add_apt_repo gierens \
    https://raw.githubusercontent.com/eza-community/eza/main/deb.asc \
    "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main"
sudo apt-get update -qq
sudo apt-get install -y eza
log "eza installed."
