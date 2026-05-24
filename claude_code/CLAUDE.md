# Global Preferences

## Environment

- OS: Ubuntu/Kubuntu + WSL, shell: zsh
- Python toolchain: `uv` (not pip/poetry). Use `uv run`, `uv add`, `uv sync`.
- Node toolchain: nvm. Package management with npm/npx unless the project uses pnpm/yarn — follow what's already there.

## Code style

**Python**: formatted and linted with `ruff` (format + check). No `black`, no `flake8`.
Type-annotate function signatures. Prefer `pathlib.Path` over `os.path`. Omit docstrings for obvious helpers; add them where intent isn't clear from the signature alone.

**TypeScript / JavaScript**: formatted with Prettier (project config governs). Prefer `const` and arrow functions. No semicolons unless the project already uses them.

**Terraform**: `terraform fmt` style. One resource per file when reasonable.

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
