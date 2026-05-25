#!/usr/bin/env bash
# HashiCorp apt repo — used for terraform-ls (Terraform language server).
# Upstream guide: https://developer.hashicorp.com/terraform/install
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

is_debian || { log "apt-get not found — skipping HashiCorp repo (non-Debian system)."; exit 0; }

if command -v terraform-ls &>/dev/null; then
    log "terraform-ls already installed."
    exit 0
fi

log "Adding HashiCorp apt repo and installing terraform-ls…"
add_apt_repo hashicorp \
    https://apt.releases.hashicorp.com/gpg \
    "deb [arch=$(deb_arch) signed-by=/etc/apt/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(ubuntu_codename) main"
sudo apt-get update -qq
sudo apt-get install -y terraform-ls
log "terraform-ls installed."
