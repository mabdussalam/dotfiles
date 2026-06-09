#!/usr/bin/env bash
# Copy Claude Code config into ~/.claude/ (bootstrap semantics).
#
# Standalone-runnable: this script touches ONLY ~/.claude/ and never zsh,
# VS Code, apt, or anything else. Re-running is safe — existing targets are
# preserved by default, so local edits survive. Set FORCE=1 to overwrite,
# backing each existing target up to <target>.bak first (same semantics as
# the shared _copy helper used by 60-copy-configs.sh).
#
# Source layout (bundle-aware copy):
#   claude_code/CLAUDE.md, settings.json     → ~/.claude/<file>
#   claude_code/skills/<name>/               → ~/.claude/skills/<name>/   (per skill dir)
#   claude_code/hooks/<file>                 → ~/.claude/hooks/<file>     (per hook file)
#   claude_code/agents/<bundle>/<agent>.md   → ~/.claude/agents/<agent>.md
#   claude_code/agents/<bundle>/skills/<n>/  → ~/.claude/skills/<n>/      (flattened —
#       Claude Code discovers skills at the top of ~/.claude/skills/; the bundle dir
#       is purely organisational in source. Agent scoping happens via the skill's
#       `agent:` frontmatter, not the filesystem.)
#   claude_code/agents/<plain>.md            → ~/.claude/agents/<plain>.md (unbundled)
#
# Each skill / hook / agent is copied as an independent unit, so bundles and
# root-level entries coexist under ~/.claude/.
#
# Bundle-root dirs named `evals` or `scripts` are skipped — they're dev
# tooling for the bundle itself (e.g. eval harnesses) and must not be
# installed as runtime skills.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh"

CLAUDE_DIR="$HOME/.claude"
mkdir -p "$CLAUDE_DIR"

# Migration: if a previous install symlinked whole dirs (skills, hooks, agents),
# remove those symlinks so we can populate them per-entry.
for d in skills hooks agents; do
    if [[ -L "$CLAUDE_DIR/$d" ]]; then
        log "[migrate] removing whole-dir symlink $CLAUDE_DIR/$d"
        rm "$CLAUDE_DIR/$d"
    fi
done
mkdir -p "$CLAUDE_DIR/skills" "$CLAUDE_DIR/hooks" "$CLAUDE_DIR/agents"

for item in "$REPO/claude_code/"*; do
    basename_item="$(basename "$item")"
    if [[ "${basename_item,,}" == readme* ]]; then
        log "[skip] claude_code/$basename_item (README)"
        continue
    fi

    case "$basename_item" in
        agents)
            for bundle in "$item"/*/; do
                [[ -d "$bundle" ]] || continue
                shopt -s nullglob
                for agent_md in "$bundle"*.md; do
                    _copy "$agent_md" "$CLAUDE_DIR/agents/$(basename "$agent_md")"
                done
                if [[ -d "${bundle}skills" ]]; then
                    for skill in "${bundle}skills/"*/; do
                        skill_name="$(basename "$skill")"
                        # Skip dev-only dirs at the bundle root (eval harnesses,
                        # helper scripts). These live alongside skills in source
                        # but are NOT runtime skills.
                        case "$skill_name" in
                            evals|scripts)
                                log "[skip] $skill ($skill_name is dev tooling, not a skill)"
                                continue
                                ;;
                        esac
                        _copy "$skill" "$CLAUDE_DIR/skills/$skill_name"
                    done
                fi
                shopt -u nullglob
            done
            shopt -s nullglob
            for agent_md in "$item"/*.md; do
                _copy "$agent_md" "$CLAUDE_DIR/agents/$(basename "$agent_md")"
            done
            shopt -u nullglob
            ;;
        skills|hooks)
            for entry in "$item"/*; do
                [[ -e "$entry" ]] || continue
                _copy "$entry" "$CLAUDE_DIR/$basename_item/$(basename "$entry")"
            done
            ;;
        *)
            _copy "$item" "$CLAUDE_DIR/$basename_item"
            ;;
    esac
done

log "Claude Code config copy complete."
