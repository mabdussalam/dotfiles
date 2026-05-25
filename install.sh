#!/usr/bin/env bash
# Full one-command setup for a fresh Ubuntu/Kubuntu machine (native or WSL).
# See README.md for usage. bootstrap.zsh is a brew-only convenience wrapper.
#
# This file is a thin orchestrator: it runs every executable module under
# install/[0-9]*.sh in glob (numeric) order. Each module is standalone-runnable
# and idempotent — to run a single phase, invoke the file directly, e.g.
#     ./install/10-docker.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULES=( "$SCRIPT_DIR/install/"[0-9]*.sh )
TOTAL=${#MODULES[@]}

printf '\n======================================================================\n'
printf '  Dotfiles installer — %d phases — repo: %s\n' "$TOTAL" "$SCRIPT_DIR"
printf '======================================================================\n\n'

i=0
for mod in "${MODULES[@]}"; do
    i=$((i+1))
    name=$(basename "$mod" .sh)
    printf '=> [%d/%d] %s\n' "$i" "$TOTAL" "$name"
    bash "$mod"
    printf '\n'
done

printf '======================================================================\n'
printf '  Installation complete!\n'
printf '======================================================================\n\n'
printf '  Next steps:\n'
printf '   1. Open a NEW terminal (or run "exec zsh") — Zim will bootstrap\n'
printf '      itself and install plugins on first launch.\n'
printf '   2. If you use Powerlevel10k, run "p10k configure" to set up the\n'
printf '      prompt, or copy your existing ~/.p10k.zsh into place.\n'
printf '   3. If VS Code extensions were skipped, run:\n'
printf '      %s/vscode/scripts/install-extensions.sh\n' "$SCRIPT_DIR"
printf '   4. Claude Code LSP plugins (pyright-lsp, typescript-lsp) are pre-enabled\n'
printf '      in claude_code/settings.json — they activate on next "claude" launch.\n'
printf '      For other languages, install plugins from the official marketplace:\n'
printf '        /plugin install <name>@claude-plugins-official\n'
printf '   5. Per-project bootstrap of OpenSpec (spec-driven workflow):\n'
printf '        cd your-project && openspec init --tools claude\n\n'
