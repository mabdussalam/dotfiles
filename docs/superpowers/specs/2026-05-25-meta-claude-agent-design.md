# Meta-Claude Agent — Design

**Date:** 2026-05-25
**Status:** Design approved, pending plan
**Owner:** Mohammad Habiba

## Summary

A subagent named `meta-claude` plus seven scoped builder skills that together act as a customization expert for Claude Code itself. The agent answers questions about Claude Code's customization surface (skills, subagents, hooks, MCP servers, settings, output styles, plugins) and produces validated artifacts when asked. It is generic — it has no knowledge of the user's dotfiles repo and writes wherever the user tells it.

## Goals

- Lower friction for creating new Claude Code customizations (skills, agents, hooks, MCP servers).
- Encode the documented frontmatter shapes, allowed values, and top gotchas in one place so they are not re-discovered each time.
- Be portable: agent and skills are self-contained and could later be promoted to a plugin without redesign.

## Non-goals

- Not a docs reader / chatbot. It builds artifacts; it does not lecture.
- Not a marketplace publisher. Promotion to plugin layout is in scope; submitting to a marketplace is not.
- Not opinionated about the user's dotfiles repo layout. It writes to paths the user provides.
- Not a runtime test harness. Validation is static (lint, schema, frontmatter). Live execution of generated artifacts is out of v1.

## Architecture

Pattern **B** from brainstorming: a thin orchestrator agent plus modular builder skills.

```
claude_code/
  agents/
    meta-claude.md                    # orchestrator (~150 lines)
  skills/
    create-skill/SKILL.md             # bootstrap a SKILL.md
    create-subagent/SKILL.md          # bootstrap an agent definition
    create-hook/SKILL.md              # add a hook (script + settings entry)
    add-mcp-server/SKILL.md           # add an MCP server config
    modify-settings/SKILL.md          # guarded edits to settings.json
    create-plugin/SKILL.md            # promote artifacts to plugin layout
    doctor/SKILL.md                   # read-only audit
```

Symlinks (existing `install/60-symlinks.sh` loop) land these in `~/.claude/agents/` and `~/.claude/skills/`. The `claude_code/agents/` directory does not exist yet; the symlink loop must be confirmed to walk it the same way it walks `claude_code/skills/`. This is flagged for verification in the implementation plan, not blocking here.

## Agent: `meta-claude`

**Frontmatter:**

```yaml
---
name: meta-claude
description: >
  Use when the user wants to create, modify, or audit Claude Code customizations:
  skills, subagents, hooks, MCP servers, slash commands, output styles, settings.json,
  or plugins. Owns frontmatter shapes, file locations, and the common gotchas.
  Always asks the user where to write before producing files.
tools: [Read, Write, Edit, Bash, WebFetch, Skill, AskUserQuestion]
model: inherit
---
```

**Why these choices:**

- `tools` is an allowlist; the agent has only what it needs. No `Agent` tool — subagents cannot spawn subagents per the docs.
- `model: inherit` — uses the parent session's model with no override surprises.
- No `skills:` preload — skills are agent-scoped via their own `agent:` field (see below); preloading would put all seven skill bodies in the agent prompt and bloat every spawn.
- No `permissionMode` — inherits from parent; the docs note parent `bypassPermissions`/`acceptEdits`/`auto` overrides child anyway.

**Body sections (~150 lines target):**

1. **Identity & scope.** What meta-claude does and does not do.
2. **Routing table.** For each user-request shape ("create a skill that…", "add an MCP server for…", "why isn't my hook firing?"), which skill to invoke or "no skill — answer inline + cite the docs page."
3. **Cross-cutting rules.** Always ask the user for the write path before writing. Always run frontmatter + schema lint before claiming done. Surface line-count warnings (skills >500 lines, CLAUDE.md >200 lines, skill description+when_to_use >1536 chars).
4. **Knowledge anchors.** Curated mapping from primitive → canonical doc URL on `code.claude.com/docs/en/`, so live-fetch is one-shot when uncertain.
5. **Common gotchas (top ~10).** High-leverage warnings from the docs survey. Examples: hook exit-code 1 is non-blocking; `.claude-plugin/` only holds `plugin.json`; subagents cannot spawn subagents; plugin agents silently ignore `hooks`/`mcpServers`/`permissionMode`; the reserved MCP server name `workspace`; `disable-model-invocation` blocks preload; `defaultMode: "auto"` is ignored from project/local settings.

## Skills

**Common frontmatter pattern:**

```yaml
---
name: <action>
description: >
  <action-specific> — used by meta-claude to decide when to invoke this skill.
  Front-loaded with keywords matching the user's natural phrasing.
agent: meta-claude              # scopes skill to meta-claude's context only
disable-model-invocation: false # auto-invocable within meta-claude
argument-hint: "[free-text]"
allowed-tools: [Read, Write, Edit, Bash, WebFetch, AskUserQuestion]
---
```

**Common body sections.** Every skill follows the same shape so meta-claude can rely on it:

1. **Inputs.** What the skill expects (name, purpose, target write path).
2. **Resolve write path.** Ask the user via `AskUserQuestion` if not provided. Never assume.
3. **Knowledge anchor.** The specific `code.claude.com/docs/en/<page>.md` URL to WebFetch if uncertain about the current frontmatter schema for this artifact type.
4. **Author.** Write the file with the documented minimal frontmatter. Surface line-count or character-count budgets that apply.
5. **Lint.** Three-pass: frontmatter parse + required fields; value-shape (enums, caps); footgun check (artifact-specific warnings from the docs survey).
6. **Report.** Print the path written and the lint result. Do not claim success without lint passing.

**Per-skill summary:**

| Skill | Purpose | Writes | Key lint |
|---|---|---|---|
| `create-skill` | Bootstrap a new SKILL.md | `<path>/skills/<name>/SKILL.md` | frontmatter shape; description+when_to_use ≤1536 chars; body ≤500 lines |
| `create-subagent` | Bootstrap an agent definition | `<path>/agents/<name>.md` | required `name` + `description`; `tools` allowlist valid; `model` value valid |
| `create-hook` | Add hook to settings.json + script | hook script + settings.json edit | event name valid; matcher syntax; exit-code-1-is-non-blocking warning surfaced |
| `add-mcp-server` | Add an MCP server config | `.mcp.json` or `~/.claude.json` | transport valid; reserved name `workspace` blocked; scope chosen explicitly |
| `modify-settings` | Guarded edit to settings.json | settings.json | JSON parses; managed-only keys refused at user/project scope; diff shown before applying |
| `create-plugin` | Promote artifacts to plugin layout | `<path>/plugin/.claude-plugin/plugin.json` + structure | manifest schema; `.claude-plugin/` only holds `plugin.json`; `claude plugin validate` if available |
| `doctor` | Read-only audit | nothing | reports oversized SKILL.md, deprecated commands, unwired hooks, managed-only keys at wrong scope |

## Knowledge strategy — hybrid

Two layers:

1. **Embedded core (frozen).** Each skill body carries the documented minimal frontmatter shape, allowed values, and three to five top gotchas for its artifact type. The agent body carries the routing table and ten cross-cutting gotchas. Source: the docs survey performed during brainstorming. The common path is zero-network.

2. **Live fetch.** Two triggers:
   - **Schema uncertainty.** Agent or skill wants a frontmatter field not in its embedded knowledge → `WebFetch https://code.claude.com/docs/en/<page>.md`.
   - **Version-gated feature.** User asks about something tagged "vX.Y+" in the embedded gotchas → fetch to confirm current version compatibility before writing.

3. **Refresh signal.** Out of scope for v1. A future `refresh-docs` skill (or a `doctor` subcommand) can re-fetch all anchored pages and diff against embedded snippets, flagging drift.

## Validation strategy

Three lint passes, run after every write:

- **A. Frontmatter parse + required fields.** Parse YAML; check required keys per artifact type. Fail closed on missing required fields.
- **B. Value-shape.** Enumerated values checked against embedded enums (model names, hook events, MCP transports). Caps checked (skill description ≤1536 chars; skill body ≤500 lines warning).
- **C. Footgun.** Artifact-specific gotchas: hook `exit 1` is non-blocking (warn if author wrote it); `.claude-plugin/` directory only holds `plugin.json` (fail otherwise); managed-only settings keys at user/project scope (refuse); reserved MCP name `workspace` (refuse).

Lint runs as a small Python or bash script invoked via the agent's `Bash` tool. Output is structured (JSON or simple PASS / PASS-WITH-WARNINGS / FAIL with reasons). No live execution in v1.

## Invocation flow

```
User → Root Claude:  "create a hook that runs prettier on JS edits"
   │
   ▼
Root Claude matches meta-claude's description and auto-spawns it via the Agent tool,
passing the user's request verbatim.
   │
   ▼
meta-claude (own context window):
   1. Routes to create-hook skill (per routing table).
   2. Asks user for write path via AskUserQuestion.
   3. Invokes create-hook via Skill tool.
        ├─ create-hook reads embedded knowledge for hook frontmatter + events list.
        ├─ If user named a non-standard event → WebFetch hooks docs page.
        ├─ Writes script + edits settings.json.
        └─ Runs 3-pass lint; returns PASS / WARN / FAIL.
   4. Reports back to root: "Wrote <script-path> + edited <settings-path>. Lint: <result>."
   │
   ▼
Root Claude summarizes to the user, surfacing warnings unchanged.
```

**Auto-spawn keyword anchors** in meta-claude's description: "create skill, create agent, create subagent, create hook, add MCP server, modify settings.json, create plugin, audit Claude Code config, customize Claude Code, claude code customization, write SKILL.md, write agent definition."

**Manual invocation** is always available: the user says "use meta-claude to …" or root explicitly delegates.

## Failure modes

- **Lint fails after write** — meta-claude reports FAIL with reason, offers to fix and re-lint. Does not silently retry.
- **Write path conflicts with existing file** — meta-claude refuses to overwrite; asks the user (skip / overwrite / rename).
- **WebFetch fails** — falls back to embedded knowledge; surfaces "couldn't verify against live docs — using embedded snapshot from <date>" in the report.
- **User asks about something out of scope** (e.g., "review this PR") — meta-claude declines and suggests root Claude handle it.

## Open questions deferred to the implementation plan

1. **`claude_code/agents/` symlink behaviour.** Confirm `install/60-symlinks.sh` walks `agents/` the same way it walks `skills/`. If it does not, extend it.
2. **Lint script language.** Bash + `python -c 'import yaml; ...'` vs. a small standalone Python script. Pick during plan.
3. **`disable-model-invocation` default for the seven skills.** Set to `false` here (auto-invocable within meta-claude's context). Could be flipped if the agent ends up firing them too eagerly.
4. **`doctor` audit scope.** v1 scans `~/.claude/` and the project `.claude/`. Output format (table, JSON, both) to be decided in the plan.

## Out of scope for v1

- Live execution / smoke-test of generated hooks, MCP servers, plugins.
- `refresh-docs` skill that re-fetches and diffs against embedded snapshots.
- Promotion to a publishable plugin (`.claude-plugin/plugin.json`) with marketplace submission.
- Slash-command exposure of individual skills at root (they remain agent-scoped).
- Community sentiment research — the brainstorming session deferred this; revisit if a future scope question depends on it.

## References

- Claude Code docs index: <https://code.claude.com/docs/llms.txt>
- Skills: <https://code.claude.com/docs/en/skills.md>
- Subagents: <https://code.claude.com/docs/en/sub-agents.md>
- Plugins: <https://code.claude.com/docs/en/plugins.md>
- MCP servers: <https://code.claude.com/docs/en/mcp.md>
- Hooks: <https://code.claude.com/docs/en/hooks.md>
- Settings: <https://code.claude.com/docs/en/settings.md>
- Memory / CLAUDE.md: <https://code.claude.com/docs/en/memory.md>
- Permissions: <https://code.claude.com/docs/en/permissions.md>
- Output styles: <https://code.claude.com/docs/en/output-styles.md>
- Agent teams: <https://code.claude.com/docs/en/agent-teams.md>
- Status line: <https://code.claude.com/docs/en/statusline.md>
- Keybindings: <https://code.claude.com/docs/en/keybindings.md>
