#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Lint a Claude Code settings.json file (scope-aware).

Usage:
    lint.py <settings.json> [--scope user|project|local|managed] [--json]

Output contract:
    First stdout line: PASS / PASS-WITH-WARNINGS / FAIL
    Subsequent lines: indented per-finding detail.
    Exit: 0 on PASS / PASS-WITH-WARNINGS, 1 on FAIL.

Implements Pass A (parse) + Pass B (value-shape, including managed-only
refusal at non-managed scope and scope-conditional silent-ignore warnings).
Pass C heuristics (e.g. curl-rule fragility) stay prose in SKILL.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Enumerated values: WARN on mismatch (Claude Code may add new values).
ENUMS = {
    "effortLevel": {"low", "medium", "high", "xhigh"},
    "editorMode":  {"normal", "vim"},
    "tui":         {"fullscreen", "default"},
    "theme":       {"dark", "light", "dark-daltonized", "light-daltonized"},
}

# Managed-only keys: FAIL at user/project/local scope.
MANAGED_ONLY = {
    "claudeMd", "claudeMdExcludes",
    "strictKnownMarketplaces", "blockedMarketplaces",
    "strictPluginOnlyCustomization",
    "allowManagedHooksOnly", "allowManagedMcpServersOnly", "allowManagedPermissionRulesOnly",
    "forceLoginMethod", "forceLoginOrgUUID", "forceRemoteSettingsRefresh",
    "channelsEnabled", "policyHelper", "companyAnnouncements",
    "parentSettingsBehavior",
}


def lint(path: Path, scope: str) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []

    if not path.exists():
        return [f"file not found: {path}"], []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"settings.json does not parse: {e}"], []

    if not isinstance(data, dict):
        return ["top-level must be a JSON object"], []

    is_non_managed = scope in {"user", "project", "local"}
    is_project_or_local = scope in {"project", "local"}

    # Managed-only at non-managed scope -> FAIL.
    if is_non_managed:
        for k in MANAGED_ONLY:
            if k in data:
                fails.append(
                    f"managed-only key `{k}` present at `{scope}` scope — refuse "
                    "(MDM/policy-only)"
                )

    # Enums.
    for key, allowed in ENUMS.items():
        if key in data and data[key] not in allowed:
            warns.append(f"`{key}` = {data[key]!r}; expected one of {sorted(allowed)}")

    # permissions block.
    perms = data.get("permissions")
    if perms is not None:
        if not isinstance(perms, dict):
            fails.append("`permissions` must be an object")
        else:
            for k in ("allow", "deny", "ask"):
                v = perms.get(k)
                if v is not None and (
                    not isinstance(v, list) or not all(isinstance(x, str) for x in v)
                ):
                    fails.append(f"`permissions.{k}` must be a list of strings")
            dm = perms.get("defaultMode")
            if dm == "auto" and is_project_or_local:
                warns.append(
                    "`permissions.defaultMode: auto` at project/local scope is "
                    "silently ignored (security); only user/managed scope honours it"
                )
            if dm == "bypassPermissions":
                warns.append(
                    "`permissions.defaultMode: bypassPermissions` — security risk; "
                    "verify intent"
                )

    # env: object of string -> string.
    env = data.get("env")
    if env is not None and (
        not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values())
    ):
        fails.append("`env` must be an object of string → string")

    # hooks: object keyed by event.
    hooks = data.get("hooks")
    if hooks is not None and not isinstance(hooks, dict):
        fails.append("`hooks` must be an object keyed by event name")

    # enabledPlugins: object of string -> bool.
    ep = data.get("enabledPlugins")
    if ep is not None and (
        not isinstance(ep, dict) or not all(isinstance(v, bool) for v in ep.values())
    ):
        fails.append("`enabledPlugins` must be an object of `name@source` → bool")

    # Silent-ignore at project/local scope.
    if is_project_or_local and data.get("disableSkillShellExecution"):
        warns.append(
            f"`disableSkillShellExecution` at {scope} scope is silently ignored "
            "(security); set at user/managed instead"
        )

    return fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("path", type=Path)
    ap.add_argument(
        "--scope", default="user",
        choices=["user", "project", "local", "managed"],
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    fails, warns = lint(args.path, args.scope)

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
