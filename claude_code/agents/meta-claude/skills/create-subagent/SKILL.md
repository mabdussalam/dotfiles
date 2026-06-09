---
name: create-subagent
description: >
  Bootstrap a new Claude Code subagent — write an agent .md file with valid
  frontmatter at the user-chosen path, then lint it. Use when the user says
  "create an agent", "create a subagent", "scaffold an agent", "new agent definition".
agent: meta-claude
disable-model-invocation: false
argument-hint: "<agent-name> [— short role]"
allowed-tools: [Read, Write, Edit, Bash, WebFetch, AskUserQuestion]
---

# create-subagent

Bootstraps a single Claude Code subagent definition. Writes one `.md` file and
runs a three-pass lint. Does nothing else.

## 1. Inputs

Collect from the user (ask via `AskUserQuestion` for anything missing):

- **name** (required) — kebab-case identifier (e.g., `pr-reviewer`). This is
  the routing key; it must match the `name:` frontmatter field exactly.
- **role / description** (required) — one or two sentences describing when
  Claude should auto-spawn this agent. Front-load keywords from likely user
  phrasings.
- **tools** (optional) — allowlist of tool names; omit for full inheritance.
- **model** (optional) — `sonnet | opus | haiku | inherit | <full-id>`.
  Defaults to `inherit` if omitted.
- **isolation** (optional) — set to `worktree` if the agent should run in a
  temporary git worktree.

## 2. Resolve write path

Ask the user via `AskUserQuestion` which scope:

- **user-global** → `~/.claude/agents/<name>.md`
- **project** → `<project-root>/.claude/agents/<name>.md`
- **custom** → user types an absolute path

If the target file already exists, **refuse to overwrite** without explicit
confirmation. Re-ask: skip, overwrite, or rename.

## 3. Knowledge anchor — subagent frontmatter shape

The agent identity comes from the `name:` frontmatter, **not** the filename.
Keep them matching for human clarity, but Claude routes by the frontmatter
value.

**Required fields:**

- `name` — kebab-case string, matches the routing identifier.
- `description` — when-to-use sentence(s); front-loaded with keywords.

**Optional fields:**

- `tools` — array of tool names; an allowlist (e.g., `[Read, Edit, Bash]`).
  `Agent(name)` syntax can restrict which subagents this agent may spawn —
  **moot here**, because subagents cannot spawn subagents at all.
- `disallowedTools` — applied first if both `tools` and `disallowedTools` are
  present.
- `model` — `sonnet | opus | haiku | inherit | <full-id>` (e.g.,
  `claude-opus-4-7`).
- `permissionMode` — `default | acceptEdits | plan | bypassPermissions`.
  Parent's mode usually overrides child's; setting this is often a no-op.
- `maxTurns` — positive integer.
- `skills` — array of skill names to **preload** into the agent prompt.
  Expensive; use sparingly. Prefer scoping skills via each skill's `agent:`
  field.
- `mcpServers` — inline definitions or by-reference names.
- `hooks` — lifecycle hooks scoped to this agent.
- `memory` — `user | project | local`; sets the MEMORY.md location, e.g.
  `~/.claude/agent-memory/<name>/`.
- `background` — boolean.
- `effort` — `low | medium | high | xhigh`.
- `isolation: worktree` — runs the agent in a temporary git worktree.
- `color` — cosmetic only.
- `initialPrompt` — string injected as the first user turn.

If uncertain about any field's current schema:
`WebFetch https://code.claude.com/docs/en/sub-agents.md`.

## 4. Author

Write the agent `.md` with:

1. **YAML frontmatter** using the fields above. Minimal frontmatter is just
   `name` and `description`.
2. **Body** structured as:
   - **Identity & scope** — one paragraph: what this agent does and what it
     does not do.
   - **Responsibilities** — bulleted list of the agent's owned tasks.
   - **Routing / decision rules** — if the agent dispatches to skills or
     decides between branches, document the rules here.
   - **Constraints** — what the agent must not do (e.g., "never commit",
     "never overwrite without asking").
   - **Output format expected** — what the agent returns to the caller
     (path written + lint status, structured report, etc.).

## 5. Lint

After writing, run the bundled validator:

    uv run --quiet --with pyyaml python ~/.claude/skills/create-subagent/scripts/lint.py <agent.md>

Read the first stdout line: `PASS` / `PASS-WITH-WARNINGS` / `FAIL`. On `PASS-WITH-WARNINGS` or `FAIL`, surface every following indented detail line verbatim to the parent. On `FAIL`, do not claim success.

The script implements Pass A (frontmatter parse) and Pass B (value-shape: required fields, kebab-case `name`, known `tools`, known `model`, filename-stem match, 1536-char combined cap on `description` + `when_to_use`). **Pass C** below stays prose — these heuristics would over-flag if scripted.

### Pass C — footgun heuristics

- `tools` includes `Agent` → WARN: subagents cannot spawn other subagents;
  the `Agent` tool will be unavailable in this agent's runtime regardless.
- `skills` is non-empty → WARN: preloading puts full skill bodies into the
  agent prompt on every spawn (expensive). Prefer agent-scoping each skill
  via the skill's own `agent:` field.
- Filename does not match `name:` value → WARN: cosmetic only, but
  confusing. Identity routes by the frontmatter field.
- `permissionMode: auto` → WARN: research preview; only honored on certain
  models / providers; parent's mode overrides in most cases.

## 6. Report

Print:

- The absolute path written.
- The lint result (`PASS` / `PASS-WITH-WARNINGS` / `FAIL`).
- All warnings and failures verbatim.

On `FAIL`: **do not claim success.** Offer to fix the issues and re-lint.
Do not silently retry.

## Constraints

- Write **only** the target agent `.md`. Touch no other file.
- Never commit to git. Never run `git add` / `git commit`.
- Refuse to overwrite an existing file without explicit user confirmation.
