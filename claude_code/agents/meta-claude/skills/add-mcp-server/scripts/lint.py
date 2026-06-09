#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Lint a .mcp.json (or any JSON file containing an `mcpServers` block).

Usage:
    lint.py <file.json> [--json]

Output contract:
    First stdout line: PASS / PASS-WITH-WARNINGS / FAIL
    Subsequent lines: indented per-finding detail.
    Exit: 0 on PASS / PASS-WITH-WARNINGS, 1 on FAIL.

Implements Pass A (parse) + Pass B (value-shape + reserved-name guard).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESERVED_NAMES = {"workspace"}
KNOWN_TRANSPORTS = {"stdio", "http", "sse"}


def lint(path: Path) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []

    if not path.exists():
        return [f"file not found: {path}"], []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"file does not parse as JSON: {e}"], []

    if not isinstance(data, dict):
        return ["top-level must be a JSON object"], []

    servers = data.get("mcpServers")
    if servers is None:
        warns.append("no `mcpServers` block (nothing to lint)")
        return fails, warns
    if not isinstance(servers, dict):
        return ["`mcpServers` must be an object keyed by server name"], []

    for name, cfg in servers.items():
        if name in RESERVED_NAMES:
            fails.append(
                f"server name `{name}` is reserved — Claude Code will skip and warn"
            )
        if not isinstance(cfg, dict):
            fails.append(f"`mcpServers.{name}` must be an object")
            continue

        t = cfg.get("type")
        if t is None or t not in KNOWN_TRANSPORTS:
            warns.append(
                f"`mcpServers.{name}.type` is {t!r}; expected one of {sorted(KNOWN_TRANSPORTS)}"
            )

        if t == "sse":
            warns.append(
                f"`mcpServers.{name}` uses deprecated `sse` transport; prefer `http`"
            )

        if t == "http" and not isinstance(cfg.get("url"), str):
            fails.append(f"`mcpServers.{name}.url` required (string) for http transport")

        if t == "stdio" and not isinstance(cfg.get("command"), str):
            fails.append(f"`mcpServers.{name}.command` required (string) for stdio transport")

        headers = cfg.get("headers")
        if isinstance(headers, dict):
            for hk, hv in headers.items():
                if hk.lower() == "authorization" and isinstance(hv, str):
                    has_bearer = "bearer" in hv.lower()
                    is_interpolated = hv.startswith("${")
                    if has_bearer and not is_interpolated:
                        warns.append(
                            f"`mcpServers.{name}.headers.{hk}` contains a literal Bearer "
                            "token; use `${ENV_VAR}` interpolation to avoid committing secrets"
                        )

    return fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("path", type=Path)
    ap.add_argument("--json", action="store_true")
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
