#!/usr/bin/env bash
# Trippy — network diagnostic tool, from the official PPA.
# Upstream: https://github.com/fujiapple852/trippy
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

is_debian || { log "apt-get not found — skipping Trippy (non-Debian system)."; exit 0; }

if command -v trip &>/dev/null; then
    log "trippy already installed: $(trip --version)"
    exit 0
fi

# add-apt-repository writes one of these two filenames depending on codename
UBUNTU_CODENAME="$(ubuntu_codename)"
if [[ ! -f "/etc/apt/sources.list.d/fujiapple-ubuntu-trippy-${UBUNTU_CODENAME}.list" \
   && ! -f "/etc/apt/sources.list.d/fujiapple-ubuntu-trippy.list" ]]; then
    log "Adding Trippy PPA (fujiapple/trippy)…"
    sudo add-apt-repository -y ppa:fujiapple/trippy
fi

log "Installing trippy…"
sudo apt-get update -qq
sudo apt-get install -y trippy
log "trippy installed."
