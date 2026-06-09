#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Lint a Claude Code hook wiring (settings.json hooks block + optional script).

Usage:
    lint.py <settings.json> [--script <hook-script>] [--json]

Output contract:
    First stdout line: PASS / PASS-WITH-WARNINGS / FAIL
    Subsequent lines: indented per-finding detail.
    Exit: 0 on PASS / PASS-WITH-WARNINGS, 1 on FAIL.

Implements Pass A (parse) + Pass B (value-shape). Pass C (heuristics
like `exit 1`-as-block detection, raw ANSI escapes) stays prose in
the parent SKILL.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

KNOWN_EVENTS = {
    "SessionStart", "SessionEnd", "Setup",
    "UserPromptSubmit", "UserPromptExpansion",
    "PreToolUse", "PostToolUse", "PostToolUseFailure", "PostToolBatch",
    "PermissionRequest", "PermissionDenied",
    "Notification",
    "SubagentStart", "SubagentStop",
    "TaskCreated", "TaskCompleted",
    "Stop", "StopFailure",
    "TeammateIdle", "InstructionsLoaded", "ConfigChange",
    "CwdChanged", "FileChanged",
    "WorktreeCreate", "WorktreeRemove",
    "PreCompact", "PostCompact",
    "Elicitation", "ElicitationResult",
}

KNOWN_HOOK_TYPES = {"command", "url", "prompt", "server"}
SIMPLE_MATCHER_RE = re.compile(r"[A-Za-z0-9_]+(\|[A-Za-z0-9_]+)*")


def is_simple_matcher(s: str) -> bool:
    """Empty / `*` / pipe-separated identifiers => simple matcher."""
    if s == "" or s == "*":
        return True
    return bool(SIMPLE_MATCHER_RE.fullmatch(s))


def lint(settings_path: Path, script_path: Path | None) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []

    if not settings_path.exists():
        return [f"settings file not found: {settings_path}"], []

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"settings.json does not parse: {e}"], []

    if not isinstance(data, dict):
        return ["top-level must be a JSON object"], []

    hooks = data.get("hooks")
    if hooks is None:
        warns.append("no `hooks` block in settings.json (nothing to lint)")
    elif not isinstance(hooks, dict):
        fails.append("`hooks` must be an object keyed by event name")
    else:
        for event, groups in hooks.items():
            if event not in KNOWN_EVENTS:
                warns.append(f"event `{event}` not in documented set (could be new; verify in docs)")
            if not isinstance(groups, list):
                fails.append(f"`hooks.{event}` must be an array")
                continue
            for i, group in enumerate(groups):
                if not isinstance(group, dict):
                    fails.append(f"`hooks.{event}[{i}]` must be an object")
                    continue
                matcher = group.get("matcher", "")
                if not isinstance(matcher, str):
                    fails.append(f"`hooks.{event}[{i}].matcher` must be a string")
                elif not is_simple_matcher(matcher):
                    try:
                        re.compile(matcher)
                    except re.error as e:
                        fails.append(
                            f"`hooks.{event}[{i}].matcher` is neither a simple matcher "
                            f"nor a valid regex: {e}"
                        )
                inner = group.get("hooks")
                if not isinstance(inner, list) or not inner:
                    fails.append(f"`hooks.{event}[{i}].hooks` must be a non-empty array")
                    continue
                for j, h in enumerate(inner):
                    if not isinstance(h, dict):
                        fails.append(f"`hooks.{event}[{i}].hooks[{j}]` must be an object")
                        continue
                    htype = h.get("type")
                    if htype not in KNOWN_HOOK_TYPES:
                        fails.append(
                            f"`hooks.{event}[{i}].hooks[{j}].type` must be one of "
                            f"{sorted(KNOWN_HOOK_TYPES)} (got: {htype!r})"
                        )
                    if htype == "command":
                        cmd = h.get("command")
                        if not isinstance(cmd, str):
                            fails.append(
                                f"`hooks.{event}[{i}].hooks[{j}].command` must be a string"
                            )
                        else:
                            first = cmd.split()[0] if cmd.split() else cmd
                            expanded = os.path.expanduser(first)
                            looks_like_path = first.startswith(("/", "~", "./"))
                            if looks_like_path:
                                p = Path(expanded)
                                if not p.exists():
                                    warns.append(
                                        f"hook script `{expanded}` not found on disk (unwired hook)"
                                    )
                                elif not os.access(expanded, os.X_OK):
                                    warns.append(
                                        f"hook script `{expanded}` exists but is not executable"
                                    )
                    elif htype == "url":
                        if not isinstance(h.get("url"), str):
                            fails.append(
                                f"`hooks.{event}[{i}].hooks[{j}].url` must be a string"
                            )
                        warns.append(
                            f"`hooks.{event}[{i}].hooks[{j}]` is type=url: "
                            "non-2xx responses are non-blocking"
                        )

    if script_path is not None:
        if not script_path.exists():
            warns.append(f"--script path not found: {script_path}")
        elif not os.access(script_path, os.X_OK):
            warns.append(f"--script path not executable: {script_path}")

    return fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("settings", type=Path)
    ap.add_argument("--script", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    fails, warns = lint(args.settings, args.script)

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
