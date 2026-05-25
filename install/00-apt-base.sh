#!/usr/bin/env bash
# Base APT packages
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

is_debian || { log "apt-get not found — skipping APT base (non-Debian system)."; exit 0; }

log "Installing APT prerequisites (build-essential, curl, git, zsh …)"
sudo apt-get update -qq
# shellcheck disable=SC2046
sudo apt-get install -y $(read_list apt-base)
log "APT prerequisites installed."
