# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal dotfiles for macOS/Linux (Ubuntu/Kubuntu, native and WSL). It is **source-of-truth config plus a bootstrap installer** — there is no application to build or run. Work here is almost always: editing a config under `zsh/`, `vscode/`, or `claude_code/`; editing an installer module under `install/`; or editing/validating a Claude Code skill under `claude_code/agents/`.

## Common commands

```bash
./install.sh                      # full setup — runs every install/[0-9]*.sh in numeric order
./install/61-copy-claude.sh       # run ONE phase standalone (each module is independently runnable)
FORCE=1 ./install/61-copy-claude.sh   # overwrite existing targets (backs each up to ~/.dotfiles-backups/<run>/ first)
./bootstrap.zsh                   # brew-only convenience re-run
```

There is no project-level lint/test runner. The only executable tests are the per-skill validators under `claude_code/agents/meta-claude/skills/*/scripts/`:

```bash
# Run a validator (the contract these scripts implement):
uv run --quiet --with pyyaml python claude_code/agents/meta-claude/skills/<skill>/scripts/lint.py <args>
# Run that validator's test suite:
uv run --quiet --with pyyaml python3 claude_code/agents/meta-claude/skills/<skill>/scripts/test_lint.py
# meta-claude routing eval (spawns real `claude --agent meta-claude` per prompt):
python claude_code/agents/meta-claude/evals/routing/run.py
```

Validator output contract: first stdout line is `PASS` / `PASS-WITH-WARNINGS` / `FAIL`; exit `0` for PASS/WARN, `1` for FAIL (`doctor`'s `scan.py` doesn't emit the status line and always exits `0` — it's a read-only audit). All accept `--json`.

## Installer architecture

`install.sh` is a thin orchestrator: it globs `install/[0-9]*.sh` and runs each in numeric order. The numeric prefix encodes ordering (apt base → vendor repos → homebrew → runtimes → config copy → node → npm → vscode → shell). Every module is **standalone-runnable and idempotent** — re-running is safe and skips already-done work.

- **`install/_lib.sh`** is sourced (not executed) by every module. It owns all shared logic: `log/warn/die`, platform probes (`is_debian`, `ubuntu_codename`), idempotent apt-repo registration (`add_apt_repo`), brew shellenv loading, list parsing (`read_list`), and the `_copy` helper.
- **`_copy` defines "bootstrap semantics"** used everywhere configs land in `$HOME`: if the target exists, **skip** it (local edits survive re-runs); with `FORCE=1`, move it into a timestamped backup dir (`~/.dotfiles-backups/<run>/`, mirroring the target's path and kept *outside* the live config tree so backups are never rediscovered as skills) and overwrite. Legacy symlinks from the older symlink-based installer are removed before copying. This is why a plain re-run never clobbers your live `~/.claude/` or `~/.zshrc` — you must pass `FORCE=1` to push repo changes out.
- **Package/tool lists** live in `install/lists/*.txt` (apt-base, npm-globals, uv-tools), parsed by `read_list` (strips `#` comments and blanks). Add a tool by editing the list, not the module.
- `60-copy-configs.sh` handles zsh + VS Code; `61-copy-claude.sh` handles only `~/.claude/`. Keep that separation — `61` is deliberately scoped so it touches nothing else.

## claude_code/ — source is "bundle-shaped", install is "flattened"

This is the subtlest part of the repo. The source tree groups an agent with the skills it owns under `claude_code/agents/<bundle>/` (agent `.md` + nested `skills/`), but **Claude Code discovers skills only at the top of `~/.claude/skills/`**. So `61-copy-claude.sh` flattens every skill — bundled or root-level — into `~/.claude/skills/<name>/`, copies agent `.md` files to `~/.claude/agents/`, and copies `CLAUDE.md`/`settings.json` to `~/.claude/`.

Consequences to keep in mind when editing:

- **Bundle directories are purely organisational.** Agent-scoping is NOT done by the filesystem — it's done by each skill's `agent: <name>` frontmatter. A skill scoped to `meta-claude` loads only into that agent's context and won't appear as a root-level slash command.
- **`evals/` and `scripts/` at a bundle root are skipped by the installer** (they're dev tooling, not runtime skills). Skill-internal `scripts/` dirs (the validators) *are* copied, because the installer copies whole skill directories.
- **READMEs are skipped** on copy.
- Because re-runs skip existing targets, after adding a new skill/agent you must copy it in by hand or run the relevant phase with `FORCE=1`.
- `skill-creator` and `mcp-builder` are **forks of `anthropics/skills`** with one local change: `agent: meta-claude` added to frontmatter. On upstream updates, re-copy and re-apply that line.

The authoritative, detailed map of source-path → install-path and the skill/agent inventory is `claude_code/README.md` — read it before restructuring anything under `claude_code/`.

## Conventions

- New installer module: name it `install/<NN>-<topic>.sh`, `source _lib.sh`, keep it idempotent and standalone-runnable, and pick `NN` to slot into the existing ordering.
- New tool: add it to the appropriate `install/lists/*.txt` rather than hardcoding in a module.
- New hand-authored meta-claude skill: ship a `scripts/lint.py` + `scripts/test_lint.py` following the output contract above; the installer picks up `scripts/` automatically.
- `claude_code/CLAUDE.md` (which installs to `~/.claude/CLAUDE.md`) is a *user-global* preference file, distinct from this repo-level CLAUDE.md. Don't conflate the two.
