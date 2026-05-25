#!/usr/bin/env bash
# VS Code extensions — delegated to vscode/scripts/install-extensions.sh,
# which reads the managed extension list and idempotently installs each.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

if command -v code &>/dev/null; then
    bash "$REPO/vscode/scripts/install-extensions.sh"
else
    log "'code' CLI not on PATH — skipping extension install."
    log "Run '$REPO/vscode/scripts/install-extensions.sh' manually after VS Code is installed."
fi
