#!/usr/bin/env bash
# uv — Python package/project manager (https://astral.sh/uv).
# Installed via the official installer because the upstream self-update
# mechanism is bypassed by the Homebrew bottle.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

# uv installs into ~/.local/bin (see also 40-mise.sh for the same reason).
export PATH="$HOME/.local/bin:$PATH"

if command -v uv &>/dev/null; then
    log "uv already installed: $(uv --version)"
    exit 0
fi

log "Installing uv via official installer…"
curl -LsSf https://astral.sh/uv/install.sh | sh
log "uv installed. Run 'uv self update' later to update."
