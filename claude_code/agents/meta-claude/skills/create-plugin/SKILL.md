---
name: create-plugin
description: >
  Promote local .claude/ artifacts (skills, agents, hooks, MCP servers) into a
  proper plugin layout with .claude-plugin/plugin.json. Validates structure and
  runs 'claude plugin validate' if available. Use when the user says "make a
  plugin", "bundle into a plugin", "promote to plugin", "publish skill".
agent: meta-claude
disable-model-invocation: false
argument-hint: "<plugin-name> [source-paths]"
allowed-tools: [Read, Write, Edit, Bash, WebFetch, AskUserQuestion]
---

# create-plugin

Bundles loose `.claude/` artifacts into a Claude Code plugin directory. Owns
the plugin manifest schema, the canonical directory layout, and the most
common layout mistakes.

## 1. Inputs

Collect from the user (via `AskUserQuestion` if not supplied):

- **`name`** — kebab-case identifier. Becomes the namespace for skills
  (`/<plugin-name>:<skill-name>`). Required.
- **`source-paths`** — list of existing skills, agents, hook scripts, or MCP
  configs to bundle. Accept absolute paths. At least one required.
- **Metadata** — `description` (required), `displayName`, `version`
  (default `1.0.0`), `author` (`{name, email?, url?}`), `homepage`,
  `repository`, `license` (default `MIT`), `keywords` (array of strings).

If the user is vague ("bundle my stuff"), enumerate candidate paths under
`~/.claude/` and ask which to include — do not guess.

## 2. Resolve write path

Always ask the user where the plugin should live. Prompt example:

> "Where should I create the plugin? (e.g., `~/projects/<name>-plugin/`)"

Rules:

- Refuse to write into an existing **non-empty** directory without explicit
  user confirmation (`AskUserQuestion`: overwrite / pick different path /
  abort).
- An empty directory or a brand-new path is fine.
- Expand `~` and resolve to an absolute path before writing.

## 3. Knowledge anchor

### Directory layout (CRITICAL)

```
<plugin-root>/
  .claude-plugin/
    plugin.json          # ← ONLY this file goes inside .claude-plugin/
  skills/
    <name>/SKILL.md
  agents/
    <name>.md
  hooks/
    hooks.json           # plugin hook config
  commands/              # legacy custom-command directory (skills preferred)
  .mcp.json              # plugin's MCP servers
  .lsp.json              # plugin's LSP servers
  monitors/              # experimental, 2.1.105+
  bin/                   # binaries on PATH when plugin loaded
  settings.json          # plugin's own settings overlay
```

**Do NOT** put `skills/`, `agents/`, `hooks/`, etc. inside `.claude-plugin/`.
That directory holds **only `plugin.json`**. This is the single most common
plugin layout mistake — lint fails closed on it.

### `plugin.json` schema

```json
{
  "name": "<kebab-case>",
  "displayName": "Human Friendly Name",
  "version": "1.0.0",
  "description": "...",
  "author": {"name": "...", "email": "...", "url": "..."},
  "homepage": "...",
  "repository": "...",
  "license": "MIT",
  "keywords": ["..."],
  "experimental": {"themes": false, "monitors": false},
  "dependencies": {}
}
```

- `name` is the namespace prefix for skills (`/<plugin-name>:<skill-name>`).
- `displayName` requires Claude Code **2.1.143+**. Warn the user if used.
- If `version` is omitted, the git SHA at install time is used per commit.

### Plugin-component variables

Available inside plugin artifacts (hooks, commands, MCP configs):

- `${CLAUDE_PLUGIN_ROOT}` — the plugin's directory.
- `${CLAUDE_PLUGIN_DATA}` — writeable state dir; persists across plugin
  updates.
- `${CLAUDE_PROJECT_DIR}` — the user's current project root.
- `${user_config.*}` — values from the user's plugin config.
- `${ENV_VAR}` — process env vars.

### Plugin subagent restrictions (security)

When an agent file is shipped inside a plugin (`agents/<name>.md`), the
following frontmatter keys are **silently ignored**:

- `hooks`
- `mcpServers`
- `permissionMode`

Only `isolation: worktree` is a valid `isolation` value for plugin agents.

If a source agent uses any of these, warn the user explicitly during the
report — silent ignore plus user not noticing is a security footgun.

### Validation hook

If `claude` is on PATH, run `claude plugin validate <plugin-root>` and
surface its output verbatim in the report.

### If uncertain

Fetch the canonical docs:

- `https://code.claude.com/docs/en/plugins.md`
- `https://code.claude.com/docs/en/plugins-reference.md`

## 4. Author

Produce the directory tree:

1. Create `<plugin-root>/.claude-plugin/` and write `plugin.json` with the
   user-provided metadata. Default values: `version=1.0.0`, `license=MIT`.
2. For each `source-path`, classify and copy/move into the right top-level
   directory:
   - Skill (`SKILL.md` inside a named dir) → `<plugin-root>/skills/<name>/`.
   - Agent (`.md` with frontmatter `name:` and `description:`) →
     `<plugin-root>/agents/<name>.md`.
   - Hook script → `<plugin-root>/hooks/<name>`. Preserve `+x` bit.
   - MCP config (`.mcp.json` fragment) → merge into
     `<plugin-root>/.mcp.json`.
3. Preserve all frontmatter on copied artifacts verbatim.
4. If the user is migrating hook entries from a `settings.json`, generate
   `<plugin-root>/hooks/hooks.json` with the same `event → matcher →
   hooks[]` shape used in settings.
5. Before overwriting any pre-existing file inside `<plugin-root>`, ask the
   user (overwrite / skip / rename).

## 5. Lint

After writing, run the bundled validator:

    uv run --quiet --with pyyaml python ~/.claude/skills/create-plugin/scripts/lint.py <plugin-root-dir>

Read the first stdout line: `PASS` / `PASS-WITH-WARNINGS` / `FAIL`. On `PASS-WITH-WARNINGS` or `FAIL`, surface every following indented detail line verbatim to the parent. On `FAIL`, do not claim success.

The script implements Pass A (plugin.json parse + `.claude-plugin/` exists) and Pass B (required manifest keys, `.claude-plugin/` contains only `plugin.json` — the central gotcha, bundled-subagent frontmatter checks for `hooks`/`mcpServers`/`permissionMode` and `isolation`). **Pass C** below stays prose — these heuristics would over-flag if scripted.

### Pass C — footgun heuristics

- **Anything inside `.claude-plugin/` other than `plugin.json`** → FAIL with
  message: `"CRITICAL: .claude-plugin/ holds only plugin.json — move other
  files to the plugin root."`
- Plugin agents (any `.md` under `agents/`) whose frontmatter contains
  `hooks`, `mcpServers`, or `permissionMode` → WARN ("silently ignored on
  plugin agents").
- Plugin agents whose `isolation` is set to anything other than `worktree`
  → WARN.
- If `claude` CLI is on PATH: run `claude plugin validate <plugin-root>`
  and include its full output. A non-zero exit promotes the overall lint
  result to FAIL.

Exit codes: PASS = 0, PASS-WITH-WARNINGS = 0 with warnings in report,
FAIL = non-zero, and the report makes the cause explicit.

## 6. Report

Print:

- Absolute path of the plugin root.
- Files created or moved (one per line, relative to plugin root).
- Lint result: PASS / PASS-WITH-WARNINGS / FAIL.
- Verbatim output of `claude plugin validate` if run.
- All WARN and FAIL messages from passes A–C.

On FAIL, do not claim success. Offer to fix and re-lint.
