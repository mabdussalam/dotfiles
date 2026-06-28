---
name: create-subagent
description: >
  Create or modify a Claude Code subagent — author a new agent .md with valid
  frontmatter at the user-chosen path, or make targeted edits to an existing
  one, then lint it. Use when the user says "create an agent", "create a
  subagent", "scaffold an agent", "new agent definition", "modify this agent",
  "edit the agent", "iterate on this subagent", "change the agent's routing".
agent: meta-claude
disable-model-invocation: false
argument-hint: "<agent-name> [— role to create, or change to make]"
allowed-tools: [Read, Write, Edit, Bash, WebFetch, AskUserQuestion]
---

# create-subagent

Authors or edits a single Claude Code subagent definition. Either writes a new
`.md` file or makes targeted edits to an existing one, then runs a three-pass
lint. Does nothing else.

## 0. Mode — create or modify

Decide up front, because the two paths diverge:

- **create** — no agent of this name/path exists yet. Collect inputs (§1),
  choose a scope (§2), author the file (§4), lint (§5).
- **modify** — an agent file already exists and the user wants it changed
  (routing tweak, new frontmatter field, reworded description, etc.). Skip
  scaffolding: locate the file (§2, modify branch), `Read` it, make the
  smallest targeted `Edit`s that satisfy the request (§4, modify branch),
  then lint (§5).

If it is unclear which mode applies, ask via `AskUserQuestion`. "Edit / iterate
on / change this agent" implies **modify**; "create / scaffold a new agent"
implies **create**.

## 1. Inputs (create mode)

Modify mode skips this — it reads the existing file instead (§2). For a new
agent, collect from the user (ask via `AskUserQuestion` for anything missing):

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

## 2. Resolve the target path

**Create mode** — ask the user via `AskUserQuestion` which scope:

- **user-global** → `~/.claude/agents/<name>.md`
- **project** → `<project-root>/.claude/agents/<name>.md`
- **custom** → user types an absolute path

If the target file already exists, stop and ask (skip / overwrite / rename); if
the user actually wants it changed, that's a **modify** — switch branches.

**Modify mode** — locate the existing file: `$PWD/.claude/agents/<name>.md`
(project) or `~/.claude/agents/<name>.md` (user-global), or whatever path the
user names. Resolve scope per meta-claude §3 (cwd/project-first; confirm if both
copies exist or the target is unclear). `Read` the file before editing so
changes are targeted, not a blind rewrite.

## 3. Knowledge anchor — subagent frontmatter shape

The agent identity comes from the `name:` frontmatter, **not** the filename.
Keep them matching for human clarity, but Claude routes by the frontmatter
value.

**Required fields:**

- `name` — kebab-case string, matches the routing identifier.
- `description` — when-to-use sentence(s); front-loaded with keywords.

**Optional fields:**

- `tools` — array of tool names; an allowlist (e.g., `[Read, Edit, Bash]`).
  `Agent(name)` syntax can restrict which subagents this agent may spawn — but
  the `Agent` tool is a **no-op while the agent runs as a nested subagent**
  (subagents can't spawn subagents); it's live only when the agent is loaded as
  a root persona.
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

## 4. Author or edit

**Create mode** — write the agent `.md` with:

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

**Modify mode** — make the smallest `Edit`s that satisfy the request:

- Preserve every section you were not asked to change. Do not rewrite the body.
- **Do not change `name:`** unless explicitly asked — it is the routing key.
  Changing it silently re-registers the agent under a new identity and orphans
  the old one. For a genuine rename, change `name:` *and* the filename, and tell
  the user the old routing key is now dead.
- If the edit introduces a frontmatter field, validate it against §3's field
  list first; `WebFetch` the docs if the field's current shape is unclear.

## 5. Lint

After writing or editing, run the bundled validator:

    uv run --quiet --with pyyaml python ~/.claude/skills/create-subagent/scripts/lint.py <agent.md>

Read the first stdout line: `PASS` / `PASS-WITH-WARNINGS` / `FAIL`. On `PASS-WITH-WARNINGS` or `FAIL`, surface every following indented detail line verbatim to the parent. On `FAIL`, do not claim success.

The script implements Pass A (frontmatter parse) and Pass B (value-shape: required fields, kebab-case `name`, known `tools`, known `model`, filename-stem match, 1536-char combined cap on `description` + `when_to_use`). **Pass C** below stays prose — these heuristics would over-flag if scripted.

### Pass C — footgun heuristics

Each line is a lint trigger; see §3 for the underlying rationale.

- `tools` includes `Agent` → WARN: no-op while the agent runs as a nested
  subagent (live only as a root persona).
- `skills` is non-empty → WARN: preloading is expensive on every spawn.
- Filename does not match `name:` value → WARN: cosmetic but confusing.
- `permissionMode: auto` → WARN: research preview; parent's mode usually wins.

## 6. Report

Print:

- The absolute path written, and whether it was **created** or **modified**.
- The lint result (`PASS` / `PASS-WITH-WARNINGS` / `FAIL`).
- All warnings and failures verbatim.

On `FAIL`: **do not claim success.** Offer to fix the issues and re-lint.
Do not silently retry.

## Constraints

- Write or edit **only** the target agent `.md`. Touch no other file.
- Never commit to git. Never run `git add` / `git commit`.
- Refuse to overwrite an existing file without explicit user confirmation.
