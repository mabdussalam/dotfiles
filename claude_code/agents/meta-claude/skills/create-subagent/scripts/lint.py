#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Lint a Claude Code subagent definition (.md with YAML frontmatter).

Usage:
    lint.py <agent.md> [--json]

Output contract:
    First stdout line: PASS / PASS-WITH-WARNINGS / FAIL
    Following lines: per-finding detail (indented).
    Exit code: 0 on PASS or PASS-WITH-WARNINGS, 1 on FAIL.

Implements Pass A (parse) + Pass B (value-shape). Pass C (footgun
heuristics) stays prose in the parent SKILL.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

KNOWN_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep",
    "WebFetch", "WebSearch", "Skill", "AskUserQuestion", "TodoWrite",
    "NotebookEdit", "Task", "Agent",
}

# Models rotate; treat unknowns as WARN, not FAIL.
KNOWN_MODELS = {"inherit", "opus", "sonnet", "haiku"}
KNOWN_MODEL_PREFIXES = ("claude-",)

NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]*")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_text, body). frontmatter is None if missing/malformed."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, text
    return text[4:end], text[end + 5:]


def lint(path: Path) -> tuple[list[str], list[str]]:
    """Return (fails, warns) lists of human-readable findings."""
    fails: list[str] = []
    warns: list[str] = []

    if not path.exists():
        return [f"file not found: {path}"], []

    text = path.read_text(encoding="utf-8")
    fm_text, _ = split_frontmatter(text)

    if fm_text is None:
        return [
            "missing or malformed YAML frontmatter (must start with `---` and close with `---`)"
        ], []

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        return [f"YAML frontmatter does not parse: {e}"], []

    if not isinstance(fm, dict):
        return ["frontmatter must be a YAML mapping"], []

    for key in ("name", "description"):
        if key not in fm:
            fails.append(f"required field missing: `{key}`")

    name = fm.get("name")
    if isinstance(name, str):
        if not NAME_RE.fullmatch(name):
            fails.append(f"`name` must be lowercase kebab-case (got: {name!r})")
        if path.stem != name:
            warns.append(
                f"filename stem `{path.stem}` does not match `name: {name}` "
                "(cosmetic; identity comes from frontmatter)"
            )

    tools = fm.get("tools")
    if tools is not None:
        if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
            fails.append("`tools` must be a list of strings")
        else:
            for t in tools:
                if t not in KNOWN_TOOLS:
                    warns.append(f"unknown tool name `{t}` (might be new; verify against docs)")
            if "Agent" in tools:
                warns.append(
                    "`Agent` in tools allowlist: no-op when this agent is spawned as a "
                    "subagent (documented gotcha). Useful only if also loaded as a root persona."
                )

    model = fm.get("model")
    if model is not None:
        if not isinstance(model, str):
            fails.append("`model` must be a string")
        elif model not in KNOWN_MODELS and not any(model.startswith(p) for p in KNOWN_MODEL_PREFIXES):
            warns.append(f"unknown model value `{model}` (might be a new id; verify against docs)")

    desc = fm.get("description", "")
    wtu = fm.get("when_to_use", "")
    if isinstance(desc, str) and isinstance(wtu, str):
        combined = len(desc) + len(wtu)
        if combined > 1536:
            warns.append(
                f"`description` + `when_to_use` is {combined} chars "
                "(> 1536; silently clipped at `maxSkillDescriptionChars`)"
            )

    return fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("path", type=Path)
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    fails, warns = lint(args.path)

    if fails:
        status, exit_code = "FAIL", 1
    elif warns:
        status, exit_code = "PASS-WITH-WARNINGS", 0
    else:
        status, exit_code = "PASS", 0

    if args.json:
        print(json.dumps({"status": status, "fails": fails, "warnings": warns}, indent=2))
    else:
        print(status)
        for f in fails:
            print(f"  FAIL: {f}")
        for w in warns:
            print(f"  WARN: {w}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
