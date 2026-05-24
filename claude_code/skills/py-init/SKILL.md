---
name: py-init
description: Bootstrap a new Python project with uv: pyproject.toml, ruff config, .python-version, and optional src layout. Use when starting a new Python package or script project.
disable-model-invocation: true
argument-hint: [project-name]
---

## Task

Bootstrap a production-ready Python project named `$ARGUMENTS` using `uv`.

### Steps

1. **Create and enter the project directory** (skip if already in it):
   ```bash
   uv init $ARGUMENTS --no-readme
   cd $ARGUMENTS
   ```

2. **Configure `pyproject.toml`** — ensure these sections exist (merge, don't overwrite):

   ```toml
   [tool.ruff]
   line-length = 100
   target-version = "py312"

   [tool.ruff.lint]
   select = ["E", "F", "I", "UP", "B", "SIM"]
   ignore = ["E501"]

   [tool.ruff.format]
   quote-style = "double"

   [tool.pytest.ini_options]
   testpaths = ["tests"]
   ```

3. **Add dev dependencies**:
   ```bash
   uv add --dev ruff pytest
   ```

4. **Create `.python-version`** if missing (use the project's required version or default to `3.12`).

5. **Create `tests/__init__.py`** and `tests/test_placeholder.py` with a single passing smoke test.

6. **Run a quick sanity check**:
   ```bash
   uv run ruff check .
   uv run pytest
   ```

Report what was created. If `$ARGUMENTS` is empty, apply the ruff/pytest config to the current directory instead.
