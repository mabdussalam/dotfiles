#!/usr/bin/env bash
# Homebrew — install non-interactively if missing, then `brew bundle`.
# We keep install + bundle in one module because bundle needs brew on PATH
# in the current shell, which load_brew_shellenv handles.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

if ! command -v brew &>/dev/null; then
    log "Homebrew not found. Installing non-interactively…"
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    log "Homebrew already installed. Updating…"
    brew update
fi

# Make brew available in this shell session for the bundle step below.
load_brew_shellenv

log "Homebrew ready: $(brew --version | head -1)"

log "Running brew bundle…"
brew bundle --file="$REPO/Brewfile"
log "brew bundle complete."
