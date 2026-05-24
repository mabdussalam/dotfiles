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

The `post-edit-fmt.sh` hook runs ruff, prettier, or terraform fmt after every `Write`/`Edit`/`MultiEdit`. It is intentionally non-blocking: formatter errors are silently discarded so they never interrupt Claude.

**To activate**, add the following to `~/.claude/settings.json` (not managed here — see note below):

```json
"hooks": {
  "PostToolUse": [
    {
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [
        {
          "type": "command",
          "command": "~/.claude/hooks/post-edit-fmt.sh"
        }
      ]
    }
  ]
}
```

> `settings.json` is managed separately and excluded from this README's symlink table to avoid conflicts with other tooling that writes to it.

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
