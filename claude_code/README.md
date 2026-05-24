# Claude Code Configuration

Personal Claude Code setup. All files here are symlinked into `~/.claude/` by `install.sh` (READMEs are skipped).

## File map

| File in `claude_code/`                       | Lands at                                         | Purpose                                                      |
| -------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------ |
| `settings.json`                              | `~/.claude/settings.json`                        | Model, effort, env vars, plugin toggles                      |
| `CLAUDE.md`                                  | `~/.claude/CLAUDE.md`                            | Global instructions loaded into every session                |
| `skills/pr-summary/SKILL.md`                 | `~/.claude/skills/pr-summary/SKILL.md`           | `/pr-summary` — diff summary + risk checklist                |
| `skills/py-init/SKILL.md`                    | `~/.claude/skills/py-init/SKILL.md`              | `/py-init [name]` — bootstrap a uv/ruff Python project       |
| `skills/debug-session/SKILL.md`              | `~/.claude/skills/debug-session/SKILL.md`        | `/debug-session [problem]` — structured debug: hypothesize, verify, propose fix before touching code |
| `hooks/post-edit-fmt.sh`                     | `~/.claude/hooks/post-edit-fmt.sh`               | Auto-format Python (ruff), JS/TS (prettier), Terraform after every file edit |

## Skills

Invoke with `/skill-name` or describe your intent and Claude will load the relevant skill automatically.

| Skill           | Invocation                          | Notes                                              |
| --------------- | ----------------------------------- | -------------------------------------------------- |
| `pr-summary`    | `/pr-summary [question]`            | `disable-model-invocation` not set — Claude can trigger it |
| `py-init`       | `/py-init my-project`               | `disable-model-invocation: true` — manual only     |
| `debug-session` | `/debug-session traceback goes here`| Stops before applying any fix — requires confirmation |

## Hooks

`post-edit-fmt.sh` runs `ruff format` after every Python file `Write`/`Edit`/`MultiEdit`. The hook is wired in `settings.json`.

**Failure surfacing**: `ruff format` only fails on real syntax errors, so when it fails the hook emits JSON `{"decision":"block","reason":"..."}` containing the parser error. Per the [official hook contract](https://code.claude.com/docs/en/hooks), this injects the error as a follow-up prompt — Claude sees the syntax issue and inspects the file. Successful runs are silent.

## LSP

Claude Code has native LSP support (v2.1.50+). `pyright-lsp` and `typescript-lsp` from the official Anthropic marketplace are pre-enabled in `settings.json`. The binaries they expect are installed by `install.sh`:

| Plugin | Binary | Installed via |
|---|---|---|
| `pyright-lsp` | `pyright-langserver` | `uv tool install pyright` |
| `typescript-lsp` | `typescript-language-server` | `npm -g typescript-language-server` |

For other languages, install from inside `claude`: `/plugin install <name>@claude-plugins-official`. Required binaries (also on PATH via `install.sh`): `bash-language-server`, `terraform-ls`, `marksman`.

## Tooling — AI dev workflow

| Tool | Purpose | Invocation |
|------|---------|------------|
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | spec-driven dev (proposal → apply → archive) | per-project: `openspec init --tools claude`, then `/opsx:propose <idea>` |

## Adding new skills

```bash
mkdir -p claude_code/skills/my-skill
# Write claude_code/skills/my-skill/SKILL.md with frontmatter + instructions
```

The symlink loop in `install.sh` picks up the whole `skills/` directory tree automatically — no changes to `install.sh` needed.

## References

- [Skills docs](https://code.claude.com/docs/en/skills)
- [Memory / CLAUDE.md docs](https://code.claude.com/docs/en/memory)
- [Hooks docs](https://code.claude.com/docs/en/hooks)
- [Settings reference](https://code.claude.com/docs/en/settings)
