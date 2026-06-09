# Claude Code Configuration

Personal Claude Code setup. The installer **copies** files here into `~/.claude/` as a one-time bootstrap (READMEs are skipped). Existing targets are preserved on re-run, so you can edit live in `~/.claude/` without the installer clobbering your tweaks. Set `FORCE=1` to overwrite (existing files are backed up to `<file>.bak`).

## Layout

Source tree is **bundle-shaped**: agents that own a coherent set of skills live in their own bundle directory under `agents/`, holding both the agent definition and a nested `skills/`. The install script flattens skills into `~/.claude/skills/` since that's what Claude Code's discovery expects. Bundle directories in source are purely organisational; agent-scoping happens via each skill's `agent:` frontmatter, not the filesystem.

```
claude_code/
├── CLAUDE.md                          → ~/.claude/CLAUDE.md
├── settings.json                      → ~/.claude/settings.json
├── agents/
│   └── meta-claude/                   # bundle: agent + its scoped skills
│       ├── meta-claude.md             → ~/.claude/agents/meta-claude.md
│       └── skills/
│           ├── create-subagent/       → ~/.claude/skills/create-subagent/
│           ├── create-hook/           → ~/.claude/skills/create-hook/
│           ├── create-plugin/         → ~/.claude/skills/create-plugin/
│           ├── add-mcp-server/        → ~/.claude/skills/add-mcp-server/
│           ├── modify-settings/       → ~/.claude/skills/modify-settings/
│           ├── doctor/                → ~/.claude/skills/doctor/
│           ├── skill-creator/         → ~/.claude/skills/skill-creator/   (fork of anthropics/skills)
│           └── mcp-builder/           → ~/.claude/skills/mcp-builder/     (fork of anthropics/skills)
├── skills/                            # root-level shared skills (no owning agent)
│   ├── pr-summary/                    → ~/.claude/skills/pr-summary/
│   ├── py-init/                       → ~/.claude/skills/py-init/
│   └── debug-session/                 → ~/.claude/skills/debug-session/
└── hooks/
    └── post-edit-fmt.sh               → ~/.claude/hooks/post-edit-fmt.sh
```

## Skills

Root-level skills are manual-only (`disable-model-invocation: true`) until they prove their value. Invoke explicitly with `/skill-name`.

| Skill           | Invocation                          | Notes                                              |
| --------------- | ----------------------------------- | -------------------------------------------------- |
| `pr-summary`    | `/pr-summary [question]`            | Diff summary + risk checklist                       |
| `py-init`       | `/py-init my-project`               | Bootstrap a uv/ruff Python project                  |
| `debug-session` | `/debug-session traceback goes here`| Stops before applying any fix — requires confirmation |

## Subagents

| Agent | Spawn keyword                       | Owns skills                                                                    |
| ----- | ----------------------------------- | ------------------------------------------------------------------------------ |
| `meta-claude` | "use meta-claude to …" (root auto-spawns on customization phrasings) | `skill-creator`, `mcp-builder` (official forks), `create-subagent`, `create-hook`, `add-mcp-server`, `modify-settings`, `create-plugin`, `doctor` |

`meta-claude` is the Claude Code customization expert: it bootstraps and audits skills, subagents, hooks, MCP server configs, `settings.json` edits, and plugin layouts. Its skills are scoped via `agent: meta-claude` in their frontmatter, so they load only into meta-claude's context — they don't appear as root-level slash commands and don't collide with built-ins like `/doctor`. Design spec lives at `docs/superpowers/specs/2026-05-25-meta-claude-agent-design.md`.

**Forked official skills.** `skill-creator` and `mcp-builder` are copies of [`anthropics/skills`](https://github.com/anthropics/skills) with one local change — `agent: meta-claude` added to their frontmatter to keep them out of the root-level skill picker (per the "agents with specialized skillsets" principle). When upstream ships a new version, re-copy and re-apply the `agent:` line; the upgrade-instruction is in each SKILL.md's frontmatter comment.

**Two MCP skills, different scopes.** `mcp-builder` writes *new MCP server code* (TypeScript / Python). `add-mcp-server` registers an *existing* server in `.mcp.json`. They're complementary.

### Validators

Each hand-authored meta-claude skill ships a validator under `scripts/` plus a sibling test suite:

| Skill | Script | Tests |
| --- | --- | --- |
| `create-subagent`, `create-hook`, `create-plugin`, `add-mcp-server`, `modify-settings` | `scripts/lint.py` | `scripts/test_lint.py` |
| `doctor` | `scripts/scan.py` | `scripts/test_scan.py` |

Shared output contract: first stdout line is `PASS`, `PASS-WITH-WARNINGS`, or `FAIL`; exit code is `0` for PASS/WARN and `1` for FAIL (`doctor` always exits `0` — it's a read-only audit). All scripts accept `--json` for structured output.

Example invocation:

```bash
uv run --quiet --with pyyaml python ~/.claude/skills/create-subagent/scripts/lint.py <args>
```

The forked `skill-creator` and `mcp-builder` skip this scaffolding and use their upstream eval infrastructure instead.

## Hooks

`post-edit-fmt.sh` runs `ruff format` after every Python file `Write`/`Edit`/`MultiEdit`. The hook is wired in `settings.json`.

**Failure surfacing**: `ruff format` only fails on real syntax errors, so when it fails the hook emits JSON `{"decision":"block","reason":"..."}` containing the parser error. Per the [official hook contract](https://code.claude.com/docs/en/hooks), this injects the error as a follow-up prompt — Claude sees the syntax issue and inspects the file. Successful runs are silent.

## LSP

Claude Code has native LSP support (v2.1.50+). `pyright-lsp` and `typescript-lsp` from the `claude-plugins-official` marketplace are pre-enabled in `settings.json`. The binaries they expect are installed by `install.sh`:

| Plugin | Binary | Installed via |
|---|---|---|
| `pyright-lsp` | `pyright-langserver` | `uv tool install pyright` |
| `typescript-lsp` | `typescript-language-server` | `npm -g typescript-language-server` |

For other languages, enable additional plugins from `claude` with `/plugin install <name>@claude-plugins-official`. Two binaries that pair with potential future plugin installs are already on PATH via `install.sh`: `terraform-ls` and `marksman`.

## Tooling — AI dev workflow

| Tool | Purpose | Invocation |
|------|---------|------------|
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | spec-driven dev (proposal → apply → archive) | per-project: `openspec init --tools claude`, then `/opsx:propose <idea>` |

## Adding new skills or agents

**Root-level skill (no owning agent):**

```bash
mkdir -p claude_code/skills/my-skill
# Write claude_code/skills/my-skill/SKILL.md with frontmatter + instructions
```

**Skill scoped to an existing agent (e.g. `meta-claude`):**

```bash
mkdir -p claude_code/agents/meta-claude/skills/my-skill
# In the SKILL.md frontmatter, set `agent: meta-claude`
```

**New agent bundle:**

```bash
mkdir -p claude_code/agents/my-agent/skills
# Write claude_code/agents/my-agent/my-agent.md (the agent definition)
# Add scoped skills under claude_code/agents/my-agent/skills/<name>/SKILL.md
# Each scoped skill's frontmatter carries `agent: my-agent`
```

**Optional validators.** A scoped skill can ship a `scripts/lint.py` (plus `scripts/test_lint.py`) following the contract documented in §Subagents › Validators above. The installer copies whole skill directories, so `scripts/` lands in `~/.claude/skills/<name>/scripts/` automatically — no installer change needed.

`install/60-copy-configs.sh` walks the new layout automatically: per-bundle for agents, per-entry for `skills/` and `hooks/`. No installer changes needed for typical additions — but because re-runs skip existing targets, copy new entries in by hand (or run with `FORCE=1`) if you've already bootstrapped.

## References

- [Skills docs](https://code.claude.com/docs/en/skills)
- [Memory / CLAUDE.md docs](https://code.claude.com/docs/en/memory)
- [Hooks docs](https://code.claude.com/docs/en/hooks)
- [Settings reference](https://code.claude.com/docs/en/settings)
