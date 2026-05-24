# Global Preferences

## Environment

- OS: Ubuntu/Kubuntu + WSL, shell: zsh
- Python toolchain: `uv` (not pip/poetry). Use `uv run`, `uv add`, `uv sync`.
- Node toolchain: nvm. Package management with npm/npx unless the project uses pnpm/yarn — follow what's already there.

## Code style

**Python**: Type-annotate function signatures. Prefer `pathlib.Path` over `os.path`. Omit docstrings for obvious helpers; add them where intent isn't clear from the signature alone.

**TypeScript / JavaScript**: Prefer `const` and arrow functions. No semicolons unless the project already uses them.

**Terraform**: One resource per file when reasonable.

**SQL**: uppercase keywords, lowercase identifiers.

**Markdown**: `markdownlint` compatible. Hard-wrap at 100 chars in prose sections.

## CLI tool preferences

When suggesting commands, prefer these over legacy equivalents:

| Task | Prefer |
|---|---|
| Search text | `rg` (ripgrep) |
| Find files | `fd` |
| List files | `eza` |
| View files | `bat` |
| HTTP requests | `httpie` (`http`/`https`) |
| JSON/YAML processing | `jq` / `yq` |
| Python env/run | `uv run` / `uvx` |
| Runtime versions | `mise` |

## Comments and verbosity

- Write concise, high-signal comments. Explain *why*, not *what*.
- No filler phrases ("This function...", "Note that...", "Simply...").
- Responses: be direct. Skip preamble and recap. Lead with the answer or the change.

## Tests

Run tests with the project's existing runner. For Python, prefer `pytest` via `uv run pytest`.
Don't add tests for trivial getters/setters; do add them for business logic and edge cases.

## Git

Commit messages: imperative mood, ≤72 chars subject, blank line before body if needed.
Don't commit generated files, lock files, or `.env` variants unless they're already tracked.

## Working style — subagents

Prefer spawning subagents (via the Agent tool) over running tasks inline. Root context is expensive — spend it on requirements, design decisions, and integration. Delegate execution.

**Delegate to a subagent when:**
- A task requires reading ≥ 3 files or running ≥ 3 commands
- Work can be spec'd and reviewed as output (a search, a refactor, an analysis)
- Tasks are parallelisable — send multiple agents in one message for concurrent work
- The work is self-contained and doesn't need interactive back-and-forth

**Root Claude owns:**
- Understanding requirements and surfacing ambiguities early
- Breaking work into independently-delegatable pieces
- Reviewing subagent output and integrating findings
- Keeping the overall plan coherent

When in doubt, delegate. A sharp root context makes better decisions.
