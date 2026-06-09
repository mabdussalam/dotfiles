#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Lint a Claude Code plugin layout.

Usage:
    lint.py <plugin-root-dir> [--json]

Output contract:
    First stdout line: PASS / PASS-WITH-WARNINGS / FAIL
    Subsequent lines: indented per-finding detail.
    Exit: 0 on PASS / PASS-WITH-WARNINGS, 1 on FAIL.

Implements Pass A (parse) + Pass B (structure + bundled-subagent checks).
Pass C heuristics stay prose in the parent SKILL.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def split_frontmatter(text: str):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    try:
        return yaml.safe_load(text[4:end])
    except yaml.YAMLError:
        return None


def lint(root: Path) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []

    if not root.is_dir():
        return [f"plugin root is not a directory: {root}"], []

    pdir = root / ".claude-plugin"
    if not pdir.is_dir():
        return [f"missing `.claude-plugin/` directory at {root}"], []

    manifest = pdir / "plugin.json"
    if not manifest.is_file():
        fails.append("missing `.claude-plugin/plugin.json`")
        data = None
    else:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fails.append(f"`.claude-plugin/plugin.json` does not parse: {e}")
            data = None

    if isinstance(data, dict):
        for k in ("name", "version"):
            if k not in data:
                fails.append(f"plugin.json missing required key `{k}`")
    elif data is not None:
        fails.append("plugin.json must be a JSON object")

    # `.claude-plugin/` must contain ONLY plugin.json (highest-leverage gotcha).
    for child in pdir.iterdir():
        if child.name != "plugin.json":
            fails.append(
                f"`.claude-plugin/{child.name}` present — only `plugin.json` "
                "is allowed in `.claude-plugin/`; everything else lives at plugin root"
            )

    # Plugin-bundled subagents under agents/**.md
    agents_dir = root / "agents"
    if agents_dir.is_dir():
        for amd in agents_dir.rglob("*.md"):
            text = amd.read_text(encoding="utf-8")
            fm = split_frontmatter(text)
            if not isinstance(fm, dict):
                continue
            for k in ("hooks", "mcpServers", "permissionMode"):
                if k in fm:
                    warns.append(
                        f"`{amd.relative_to(root)}` carries `{k}` in frontmatter; "
                        "plugin-bundled subagents silently ignore this field (security)"
                    )
            iso = fm.get("isolation")
            if iso is not None and iso != "worktree":
                warns.append(
                    f"`{amd.relative_to(root)}` has `isolation: {iso}`; only "
                    "`worktree` is honoured for plugin-bundled subagents"
                )

    return fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("root", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    fails, warns = lint(args.root)

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
