#!/usr/bin/env bash
# HTTPie — human-friendly HTTP client, from the official packages.httpie.io repo.
# Upstream guide: https://httpie.io/docs/cli/debian-and-ubuntu
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

is_debian || { log "apt-get not found — skipping HTTPie (non-Debian system)."; exit 0; }

if command -v http &>/dev/null; then
    log "httpie already installed: $(http --version)"
    exit 0
fi

log "Adding HTTPie apt repo and installing httpie…"
# Upstream repo is amd64-only — hard-coded per upstream docs.
add_apt_repo httpie \
    https://packages.httpie.io/deb/KEY.gpg \
    "deb [arch=amd64 signed-by=/etc/apt/keyrings/httpie.gpg] https://packages.httpie.io/deb ./"
sudo apt-get update -qq
sudo apt-get install -y httpie
log "httpie installed."
