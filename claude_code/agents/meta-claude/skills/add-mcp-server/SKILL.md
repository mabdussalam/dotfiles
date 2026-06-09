---
name: add-mcp-server
description: >
  Add an MCP server to the appropriate config (.mcp.json or ~/.claude.json). Handles
  transport, env vars, headers, OAuth, and scope selection. Use when the user says
  "add MCP server", "connect to <service>", "register MCP", "set up Linear/Slack/...".
agent: meta-claude
disable-model-invocation: false
argument-hint: "<server-name> <transport> [URL or command]"
allowed-tools: [Read, Write, Edit, Bash, WebFetch, AskUserQuestion]
---

# add-mcp-server

Adds one MCP server entry to a Claude Code config file. Lint passes before reporting
success. The skill is generic — it does not know the user's repo layout; it asks.

## 1. Inputs

Required:

- **`name`** — server identifier used as the key under `mcpServers`. Must NOT be the
  reserved name `workspace` (Claude Code skips and warns on this). Avoid spaces and
  characters that would need shell-quoting.
- **`transport`** — one of:
  - `http` (**recommended**; `streamable-http` is an accepted alias)
  - `sse` (**deprecated** — if user picks this, suggest `http` instead)
  - `stdio` (local subprocess; **does not auto-reconnect**)
- **endpoint** — either:
  - For `http`/`sse`: a `url` (string starting with `http`; prefer `https`).
  - For `stdio`: a `command` (string) plus optional `args` (array of strings).

Optional:

- `env` — object of `K: V` strings (typically only useful for `stdio`).
- `headers` — object of `K: V` strings for `http`/`sse` (e.g. `Authorization`).
- `oauth` — object: `clientId`, `callbackPort`, `authServerMetadataUrl`, `scopes`.
- `headersHelper` — shell command emitting JSON headers on stdout (refreshes per call).
- `timeout` — positive int (ms).
- `alwaysLoad` — bool; if `true`, exempts this server's tools from `ToolSearch`
  deferral (requires Claude Code 2.1.121+).

If any required input is missing, ask via `AskUserQuestion` — never assume.

## 2. Resolve write path

Ask the user via `AskUserQuestion` which **scope** the server should live in. Three
choices, mapped to a concrete file path:

- **local** — stored in `~/.claude.json` under the current project's entry. This is
  the default that Claude Code's own `claude mcp add` uses. Private to this user,
  scoped to this project.
- **project** — `<project-root>/.mcp.json`. Committed to the repo, shared with
  collaborators. Claude Code **always prompts the user on first use** of a server
  added at this scope, for security.
- **user** — `~/.claude.json` global section. Available to this user across all
  projects.

Refuse to proceed if the chosen `name` is `workspace` — Claude Code reserves it and
will skip the entry with a warning. Ask the user for a different name.

If a server with the same `name` already exists at the chosen scope, ask the user
whether to **skip**, **overwrite**, or **rename**. Never silently overwrite.

## 3. Knowledge anchor

Embedded shape (zero-network common path). If the user asks for a field not listed
here, `WebFetch https://code.claude.com/docs/en/mcp.md` and read before writing.

### Transports

| Transport | Reconnect on disconnect | Notes |
|---|---|---|
| `http` | Yes — exponential backoff, up to 5 tries | Recommended. `streamable-http` is an alias. |
| `sse` | Yes — exponential backoff, up to 5 tries | **Deprecated.** Suggest `http`. |
| `stdio` | **No** — process death is terminal for the session | Local subprocess. |

### JSON shape (`.mcp.json` or the `mcpServers` block of `~/.claude.json`)

```json
{
  "mcpServers": {
    "<name>": {
      "type": "http",
      "url": "https://example.com/mcp",
      "headers": {"Authorization": "Bearer ${TOKEN}"},
      "oauth": {
        "clientId": "...",
        "callbackPort": 9999,
        "authServerMetadataUrl": "https://example.com/.well-known/oauth-authorization-server",
        "scopes": ["read", "write"]
      },
      "headersHelper": "command-to-run",
      "timeout": 30000,
      "alwaysLoad": true
    }
  }
}
```

For `stdio`:

```json
{
  "mcpServers": {
    "<name>": {
      "type": "stdio",
      "command": "/usr/local/bin/some-mcp",
      "args": ["--flag", "value"],
      "env": {"API_KEY": "${API_KEY}"}
    }
  }
}
```

### Env expansion

These fields support `${VAR}` and `${VAR:-default}` substitution at load time:
`command`, `args`, `env` (values), `url`, `headers` (values). Prefer this over
hard-coding secrets — especially at **project** scope, where the file is committed.

### Reserved name

`workspace` — Claude Code refuses to load any server with this name.

### Output size limits

- Soft warning at **10 000 tokens** of tool output.
- Hard default cap at **25 000 tokens**.
- Raise the cap via the `MAX_MCP_OUTPUT_TOKENS` env var on the Claude Code process,
  or server-side via `_meta.anthropic/maxResultSizeChars` (≤500 000).
- `alwaysLoad: true` (Claude Code 2.1.121+) keeps a server's tools out of the
  `ToolSearch` deferral pool.

### Security

- `headersHelper` runs **unsandboxed** and requires workspace trust when present at
  `project` or `local` scope.
- Bearer tokens or other secrets embedded literally in `headers` at **project**
  scope will be committed to the repo. Always use `${VAR}` substitution there.

If uncertain about any field → `WebFetch https://code.claude.com/docs/en/mcp.md`.

## 4. Author

Steps, in order:

1. **Resolve target file** from chosen scope:
   - project → `<project-root>/.mcp.json` (create if absent, with `{"mcpServers": {}}`).
   - local → `~/.claude.json`, write under `projects.<cwd>.mcpServers`.
   - user → `~/.claude.json`, write under top-level `mcpServers`.
2. **Read the file** if it exists. If it does not exist and scope is `project`,
   create a minimal skeleton. **Never** create `~/.claude.json` from scratch — if
   it does not exist, stop and ask the user (Claude Code itself should create it).
3. **Merge** the new entry into the `mcpServers` map idempotently:
   - Preserve every other existing key (the file holds settings, project state,
     auth, history — touch nothing else).
   - Add or replace only the single `mcpServers.<name>` entry.
4. **Write back** with stable 2-space indentation and a trailing newline. Use
   `Read` + `Edit` for surgical changes when the file already exists; only use
   `Write` for newly-created `.mcp.json` skeletons.

## 5. Lint

After writing, run the bundled validator:

    uv run --quiet --with pyyaml python ~/.claude/skills/add-mcp-server/scripts/lint.py <.mcp.json>

Read the first stdout line: `PASS` / `PASS-WITH-WARNINGS` / `FAIL`. On `PASS-WITH-WARNINGS` or `FAIL`, surface every following indented detail line verbatim to the parent. On `FAIL`, do not claim success.

The script implements Pass A (JSON parse + `mcpServers` shape) and Pass B (reserved-name guard on `workspace`, transport enum, http/stdio required-field checks, deprecated `sse` warning, literal-Bearer-token warning). **Pass C** below stays prose — these heuristics would over-flag if scripted.

### Pass C — footgun heuristics

- Server name `workspace` → **FAIL** (refuse to write).
- Scope is `project` AND a `headers` value contains what looks like a literal
  bearer token (matches `Bearer [A-Za-z0-9._-]{20,}` and does NOT contain `${`) →
  **WARN**: "secret will be committed; use `${VAR}` substitution".
- Scope is `project` AND `headersHelper` is set → **WARN**: "`headersHelper` runs
  unsandboxed and requires workspace trust".
- `type` is `stdio` → **WARN**: "stdio does not auto-reconnect on disconnect; use
  `http` when the server supports it".

## 6. Report

After lint, print:

- **path written** (absolute).
- **server name** and **transport**.
- **lint status**: `PASS`, `PASS-WITH-WARNINGS` (list each warning), or `FAIL`
  (list each failure).

Do not claim success unless Pass A and Pass C both PASS. Pass-B violations on
value-shape fields that affect required keys (e.g. missing `url` for `http`)
are FAIL; the rest are WARN.
