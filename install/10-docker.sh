#!/usr/bin/env bash
# Docker Engine from the official docker.com apt repo.
# Upstream guide: https://docs.docker.com/engine/install/ubuntu/
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

is_debian || { log "apt-get not found — skipping Docker (non-Debian system)."; exit 0; }

if command -v docker &>/dev/null; then
    log "docker already installed: $(docker --version)"
else
    log "Adding Docker apt repo and installing Docker CE…"
    add_apt_repo docker \
        https://download.docker.com/linux/ubuntu/gpg \
        "deb [arch=$(deb_arch) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(ubuntu_codename) stable"
    sudo apt-get update -qq
    sudo apt-get install -y \
        docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
    log "Docker installed."
fi

# Group membership: idempotent — only usermod if user not yet in docker group.
# `id -nG` lists groups by name; grep -qx matches a whole group name (so a
# hypothetical user "docker" doesn't false-positive against the group name).
if ! id -nG "$USER" | tr ' ' '\n' | grep -qx docker; then
    sudo usermod -aG docker "$USER"
    log "Added $USER to docker group. Re-login or run 'newgrp docker'."
fi
