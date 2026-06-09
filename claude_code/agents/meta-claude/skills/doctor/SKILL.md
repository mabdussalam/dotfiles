---
name: doctor
description: >
  Read-only audit of the user's Claude Code configuration. Scans skills, agents,
  hooks, MCP servers, settings.json, and CLAUDE.md for documented gotchas, size
  warnings, deprecated patterns, and misconfigurations. Writes nothing. Use when
  the user says "audit my Claude Code config", "what's wrong with my setup",
  "doctor", "check my .claude/".
agent: meta-claude
disable-model-invocation: false
argument-hint: "[scope: user|project|both — default both] [--fix-suggest]"
allowed-tools: [Read, Bash, WebFetch, AskUserQuestion]
---

# doctor — Claude Code configuration audit

Read-only static analysis of a Claude Code configuration tree. Reports findings
classified as PASS / NOTE / WARN / FAIL with citations to the canonical docs.
This skill writes nothing — `Write` and `Edit` are deliberately excluded from
`allowed-tools`.

## 1. Inputs

- `scope`: one of `user`, `project`, `both`. Default `both`.
- `--fix-suggest` (optional flag): when set, each finding is followed by a
  suggested `meta-claude` invocation that *would* address it. The skill does
  not execute any of those suggestions; it only prints them.

Parse `argument-hint` from the user's invocation. If nothing parses, fall
through to section 2.

## 2. Resolve audit scope

If `scope` is not provided:

- Ask the user via `AskUserQuestion`:
  - `user` — scan `~/.claude/` only
  - `project` — scan the current working directory's `.claude/` only
  - `both` — scan both (default)

If `both` is selected and the cwd is not inside a git repository (check with
`git rev-parse --is-inside-work-tree`), ask whether to skip the project scan.
Do not assume.

Resolved paths used downstream:

- User scope: `~/.claude/`
- Project scope: `$PWD/.claude/` (and `$PWD/.mcp.json` for MCP)

## 3. Knowledge anchor

The embedded check list below is the source of truth for the common path. When
a finding hinges on a feature whose current shape is unclear, `WebFetch` the
relevant page before reporting:

- Skills → <https://code.claude.com/docs/en/skills.md>
- Subagents → <https://code.claude.com/docs/en/sub-agents.md>
- Hooks → <https://code.claude.com/docs/en/hooks.md>
- MCP → <https://code.claude.com/docs/en/mcp.md>
- Settings → <https://code.claude.com/docs/en/settings.md>
- Memory → <https://code.claude.com/docs/en/memory.md>
- Plugins → <https://code.claude.com/docs/en/plugins.md>

Every finding in the report cites the URL most relevant to its category.

## 4. Scan

**Implementation.** The mechanical checks below are implemented in
`scripts/scan.py`. Invoke:

    uv run --quiet --with pyyaml python ~/.claude/skills/doctor/scripts/scan.py [--scope user|project|both] [--fix-suggest] [--json]

The script always exits 0 (audit, not lint). Findings are advisory — read
them and decide what to act on. The category prose below is the
source-of-truth specification; the script implements the strictly
mechanical subset (heuristic checks like "raw ANSI escapes in script
stdout that look like notifications" stay out of the script — they would
over-flag).

Drive the scan from Bash. For each resolved scope root, walk the directories
below and apply the listed checks. A check that cannot run (e.g. file missing)
is not a finding — it is silently skipped unless its absence is itself a
finding (noted explicitly below).

### A. Skills — `<scope>/.claude/skills/*/SKILL.md`

- Body length >500 lines → **WARN**. Skill body stays in context once invoked.
- Combined `description` + `when_to_use` >1536 chars → **WARN**. Silently
  clipped at `maxSkillDescriptionChars`.
- Missing `description` field in frontmatter → **WARN**. Claude needs it to
  decide invocation.
- `disable-model-invocation: true` AND `agent:` set → **NOTE**. Skill cannot
  be preloaded; only manual invocation works.
- Frontmatter does not parse as YAML → **FAIL** for that skill.

Cite: <https://code.claude.com/docs/en/skills.md>

### B. Subagents — `<scope>/.claude/agents/*.md`

- Missing required `name` or `description` → **FAIL**.
- `tools` list includes `Agent` → **WARN**. Subagents cannot spawn subagents.
- `skills:` list non-empty → **NOTE**. Preloads full skill bodies into the
  agent's prompt — expensive on every spawn.
- Filename stem does not match the `name:` frontmatter value → **NOTE**.
  Cosmetic but confusing.
- `permissionMode: auto` → **NOTE**. Research preview; provider- and
  model-gated.

Cite: <https://code.claude.com/docs/en/sub-agents.md>

### C. Hooks — `hooks` blocks in `<scope>/.claude/settings.json` and `~/.claude/settings.json`

- Hook entry points to a script path that does not exist on disk → **WARN**
  (unwired hook).
- Hook script source contains `exit 1` in a context plainly intended to block
  the action → **WARN**. `exit 1` is non-blocking; blocking requires `exit 2`.
- Hook script writes raw ANSI escape sequences to stdout for notifications →
  **WARN**. Hooks run without a TTY; use the `terminalSequence` JSON field
  instead.
- Hook `event` name not in the documented set → **WARN**.

Cite: <https://code.claude.com/docs/en/hooks.md>

### D. MCP servers — `<scope>/.mcp.json` and `~/.claude.json` `mcpServers` entries

- Server name equals reserved value `workspace` → **FAIL**.
- `type: sse` → **WARN**. Deprecated; suggest `http`.
- Bearer token literal in `headers` at project scope → **WARN**. Committed
  secret.
- `headersHelper` present at project scope → **WARN**. Unsandboxed; requires
  workspace trust to run.

Cite: <https://code.claude.com/docs/en/mcp.md>

### E. settings.json

Managed-only keys present at non-managed scope → **WARN**. The set:

- `claudeMd`, `claudeMdExcludes`
- `strictKnownMarketplaces`, `blockedMarketplaces`
- `strictPluginOnlyCustomization`
- `allowManagedHooksOnly`, `allowManagedMcpServersOnly`,
  `allowManagedPermissionRulesOnly`
- `forceLoginMethod`, `forceLoginOrgUUID`, `forceRemoteSettingsRefresh`
- `channelsEnabled`, `policyHelper`, `companyAnnouncements`
- `parentSettingsBehavior`

Additional checks:

- `permissions.defaultMode: "auto"` or `disableSkillShellExecution` at
  project or local scope → **NOTE**. Silently ignored at those scopes.
- `defaultMode: "bypassPermissions"` anywhere → **WARN**. Security risk.
- Deprecated slash commands referenced from CLAUDE.md or skill bodies →
  **WARN**. Examples: `/vim` removed in 2.1.92, `/pr-comments` removed in
  2.1.91.

Cite: <https://code.claude.com/docs/en/settings.md>

### F. CLAUDE.md — user, project, and any subdirectory CLAUDE.md

- Any CLAUDE.md >200 lines → **WARN**. Memory bloat.
- `@imports` chain deeper than 5 hops → **WARN**.

Cite: <https://code.claude.com/docs/en/memory.md>

### G. Plugin layout — any `.claude-plugin/` directory in scope

- Any file other than `plugin.json` inside `.claude-plugin/` → **FAIL**.
- Plugin agents whose frontmatter contains `hooks`, `mcpServers`, or
  `permissionMode` → **WARN**. Silently ignored for plugin-bundled agents.

Cite: <https://code.claude.com/docs/en/plugins.md>

## 5. Lint

This skill produces no artifact, so there is nothing to lint in the
write-then-validate sense. The "lint" equivalent is the scan itself —
every check in §4 is fail-closed: when a required file does not parse,
the relevant subject reports `FAIL` rather than silently passing. The
script in §4 reflects this — it exits 0 always; the FAIL count in the
findings list is the actionable signal.

## 6. Report

Print to stdout. Format:

```
Claude Code Doctor — <YYYY-MM-DD>
Scope: <user|project|both>

PASS:  <N> checks
NOTES: <N> (informational, non-actionable)
WARN:  <N> (suggested fixes)
FAIL:  <N> (broken configs)

--- Findings ---
[FAIL] <category>: <description>  (<doc URL>)
[WARN] <category>: <description>  (<doc URL>)
[NOTE] <category>: <description>  (<doc URL>)
```

`<category>` is one of `Skills`, `Subagents`, `Hooks`, `MCP`, `Settings`,
`CLAUDE.md`, `Plugins`. Order findings FAIL → WARN → NOTE, then by category.

If `--fix-suggest` was set, append one indented line under each finding:

```
    Suggested: ask meta-claude to <verb> <object> (e.g. "use meta-claude to
    modify-settings and remove `defaultMode: bypassPermissions` from
    ~/.claude/settings.json").
```

The skill never executes the suggestion — it only prints it for the user (or
the parent agent) to act on.

If a class has zero findings, omit its section. If every check passes, the
report ends after the counts line with `No findings.`.
