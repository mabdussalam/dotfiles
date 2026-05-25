#!/usr/bin/env bash
# mise — polyglot runtime version manager (https://mise.jdx.dev).
# Installed via the official installer because the upstream self-update
# mechanism is bypassed by the Homebrew bottle.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

# mise installs into ~/.local/bin, which .zshrc adds to PATH for interactive
# shells. Export here so this script (and downstream modules in the same run)
# can find it immediately.
export PATH="$HOME/.local/bin:$PATH"

if command -v mise &>/dev/null; then
    log "mise already installed: $(mise --version)"
    exit 0
fi

log "Installing mise via official installer…"
curl -fsSL https://mise.run | sh
log "mise installed. Run 'mise self-update' later to update."
