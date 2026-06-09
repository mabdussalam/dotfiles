#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""doctor — read-only audit of a Claude Code configuration.

Usage:
    scan.py [--scope user|project|both] [--fix-suggest] [--json]

Scans:
    user scope    -> $HOME/.claude/
    project scope -> $PWD/.claude/ + $PWD/.mcp.json + $PWD/CLAUDE.md

Read-only. Exits 0 always (findings are advisory). Implements the
mechanical checks from SKILL.md §4 (categories A–G). Heuristics stay
prose in SKILL.md.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

DOCS = {
    "Skills":    "https://code.claude.com/docs/en/skills.md",
    "Subagents": "https://code.claude.com/docs/en/sub-agents.md",
    "Hooks":     "https://code.claude.com/docs/en/hooks.md",
    "MCP":       "https://code.claude.com/docs/en/mcp.md",
    "Settings":  "https://code.claude.com/docs/en/settings.md",
    "CLAUDE.md": "https://code.claude.com/docs/en/memory.md",
    "Plugins":   "https://code.claude.com/docs/en/plugins.md",
}

MANAGED_ONLY = {
    "claudeMd", "claudeMdExcludes",
    "strictKnownMarketplaces", "blockedMarketplaces",
    "strictPluginOnlyCustomization",
    "allowManagedHooksOnly", "allowManagedMcpServersOnly", "allowManagedPermissionRulesOnly",
    "forceLoginMethod", "forceLoginOrgUUID", "forceRemoteSettingsRefresh",
    "channelsEnabled", "policyHelper", "companyAnnouncements",
    "parentSettingsBehavior",
}

RESERVED_MCP_NAMES = {"workspace"}

KNOWN_HOOK_EVENTS = {
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


@dataclass
class Finding:
    level: str        # FAIL | WARN | NOTE
    category: str
    message: str
    url: str
    suggested_fix: str | None = None


def split_frontmatter(text: str):
    if not text.startswith("---\n"):
        return None, ""
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, ""
    try:
        return yaml.safe_load(text[4:end]), text[end + 5:]
    except yaml.YAMLError:
        return None, ""


def _add(findings: list[Finding], level: str, cat: str, msg: str, suggested: str | None = None) -> None:
    findings.append(Finding(level, cat, msg, DOCS[cat], suggested))


def scan_skills(root: Path, findings: list[Finding]) -> None:
    sdir = root / "skills"
    if not sdir.is_dir():
        return
    for skill_md in sdir.glob("*/SKILL.md"):
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue
        fm, body = split_frontmatter(text)
        if fm is None or not isinstance(fm, dict):
            _add(findings, "FAIL", "Skills",
                 f"{skill_md} missing/malformed frontmatter")
            continue
        if len(body.splitlines()) > 500:
            _add(findings, "WARN", "Skills",
                 f"{skill_md} body > 500 lines (stays in context once invoked)")
        desc = fm.get("description", "")
        wtu = fm.get("when_to_use", "")
        if isinstance(desc, str) and isinstance(wtu, str) and len(desc) + len(wtu) > 1536:
            _add(findings, "WARN", "Skills",
                 f"{skill_md} description+when_to_use > 1536 chars (silent clip)")
        if not desc:
            _add(findings, "WARN", "Skills", f"{skill_md} missing `description`")
        if fm.get("disable-model-invocation") is True and fm.get("agent"):
            _add(findings, "NOTE", "Skills",
                 f"{skill_md} has `disable-model-invocation: true` AND `agent:` — cannot be preloaded")


def scan_subagents(root: Path, findings: list[Finding]) -> None:
    adir = root / "agents"
    if not adir.is_dir():
        return
    for amd in adir.glob("*.md"):
        try:
            text = amd.read_text(encoding="utf-8")
        except OSError:
            continue
        fm, _ = split_frontmatter(text)
        if fm is None or not isinstance(fm, dict):
            _add(findings, "FAIL", "Subagents",
                 f"{amd} missing/malformed frontmatter")
            continue
        for k in ("name", "description"):
            if k not in fm:
                _add(findings, "FAIL", "Subagents", f"{amd} missing required `{k}`")
        tools = fm.get("tools")
        if isinstance(tools, list) and "Agent" in tools:
            _add(findings, "WARN", "Subagents",
                 f"{amd} lists `Agent` in tools — no-op for plain subagents")
        skills = fm.get("skills")
        if isinstance(skills, list) and skills:
            _add(findings, "NOTE", "Subagents",
                 f"{amd} preloads {len(skills)} skill(s) — expensive on every spawn")
        name = fm.get("name")
        if isinstance(name, str) and amd.stem != name:
            _add(findings, "NOTE", "Subagents",
                 f"{amd} filename stem != `name: {name}` (cosmetic)")


def scan_settings_and_hooks(settings_path: Path, scope: str, findings: list[Finding]) -> None:
    if not settings_path.exists():
        return
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _add(findings, "FAIL", "Settings", f"{settings_path} does not parse: {e}")
        return
    if not isinstance(data, dict):
        return

    is_non_managed = scope in {"user", "project", "local"}
    is_project_or_local = scope in {"project", "local"}

    if is_non_managed:
        for k in MANAGED_ONLY:
            if k in data:
                _add(findings, "WARN", "Settings",
                     f"{settings_path}: managed-only key `{k}` at {scope} scope")

    perms = data.get("permissions")
    if isinstance(perms, dict):
        dm = perms.get("defaultMode")
        if dm == "auto" and is_project_or_local:
            _add(findings, "NOTE", "Settings",
                 f"{settings_path}: `defaultMode: auto` at {scope} silently ignored")
        if dm == "bypassPermissions":
            _add(findings, "WARN", "Settings",
                 f"{settings_path}: `defaultMode: bypassPermissions` is a security risk")

    if data.get("disableSkillShellExecution") and is_project_or_local:
        _add(findings, "NOTE", "Settings",
             f"{settings_path}: `disableSkillShellExecution` at {scope} silently ignored")

    hooks = data.get("hooks")
    if isinstance(hooks, dict):
        for event, groups in hooks.items():
            if event not in KNOWN_HOOK_EVENTS:
                _add(findings, "WARN", "Hooks",
                     f"{settings_path}: event `{event}` not in documented set")
            if not isinstance(groups, list):
                continue
            for group in groups:
                if not isinstance(group, dict):
                    continue
                for h in group.get("hooks", []):
                    if not isinstance(h, dict):
                        continue
                    if h.get("type") == "command":
                        cmd = h.get("command") or ""
                        first = cmd.split()[0] if cmd.split() else cmd
                        if first.startswith(("/", "~", "./")):
                            expanded = os.path.expanduser(first)
                            if not Path(expanded).exists():
                                _add(findings, "WARN", "Hooks",
                                     f"{settings_path}: hook command points to missing script `{expanded}`")


def scan_mcp(path: Path, findings: list[Finding]) -> None:
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _add(findings, "FAIL", "MCP", f"{path} does not parse: {e}")
        return
    if not isinstance(data, dict):
        return
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return
    for name, cfg in servers.items():
        if name in RESERVED_MCP_NAMES:
            _add(findings, "FAIL", "MCP",
                 f"{path}: reserved server name `{name}` (Claude Code will skip and warn)")
        if isinstance(cfg, dict) and cfg.get("type") == "sse":
            _add(findings, "WARN", "MCP",
                 f"{path}: server `{name}` uses deprecated `sse` transport (prefer `http`)")


def scan_claude_md(root: Path, findings: list[Finding]) -> None:
    candidates = []
    top = root / "CLAUDE.md"
    if top.is_file():
        candidates.append(top)
    if root.is_dir():
        for p in root.rglob("CLAUDE.md"):
            if p != top:
                candidates.append(p)
    for md in candidates:
        try:
            lines = md.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        if len(lines) > 200:
            _add(findings, "WARN", "CLAUDE.md",
                 f"{md} > 200 lines ({len(lines)}) — memory bloat")


def scan_plugin_dirs(root: Path, findings: list[Finding]) -> None:
    if not root.is_dir():
        return
    for pdir in root.rglob(".claude-plugin"):
        if not pdir.is_dir():
            continue
        for child in pdir.iterdir():
            if child.name != "plugin.json":
                _add(findings, "FAIL", "Plugins",
                     f"`{pdir}/{child.name}` present — only `plugin.json` allowed in `.claude-plugin/`")
        plugin_root = pdir.parent
        agents_dir = plugin_root / "agents"
        if agents_dir.is_dir():
            for amd in agents_dir.rglob("*.md"):
                try:
                    text = amd.read_text(encoding="utf-8")
                except OSError:
                    continue
                fm, _ = split_frontmatter(text)
                if not isinstance(fm, dict):
                    continue
                for k in ("hooks", "mcpServers", "permissionMode"):
                    if k in fm:
                        _add(findings, "WARN", "Plugins",
                             f"{amd} carries `{k}` in frontmatter — silently ignored for plugin-bundled subagents")


def run_user_scope(findings: list[Finding]) -> None:
    home = Path(os.environ.get("HOME", str(Path.home())))
    root = home / ".claude"
    scan_skills(root, findings)
    scan_subagents(root, findings)
    scan_settings_and_hooks(root / "settings.json", "user", findings)
    scan_mcp(home / ".claude.json", findings)
    scan_claude_md(root, findings)
    scan_plugin_dirs(root, findings)


def run_project_scope(findings: list[Finding]) -> None:
    cwd = Path.cwd()
    root = cwd / ".claude"
    if root.is_dir():
        scan_skills(root, findings)
        scan_subagents(root, findings)
        scan_settings_and_hooks(root / "settings.json", "project", findings)
        scan_settings_and_hooks(root / "settings.local.json", "local", findings)
    scan_mcp(cwd / ".mcp.json", findings)
    scan_claude_md(cwd, findings)
    scan_plugin_dirs(cwd, findings)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--scope", default="both", choices=["user", "project", "both"])
    ap.add_argument("--fix-suggest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    findings: list[Finding] = []
    if args.scope in {"user", "both"}:
        run_user_scope(findings)
    if args.scope in {"project", "both"}:
        run_project_scope(findings)

    counts = {"FAIL": 0, "WARN": 0, "NOTE": 0}
    for f in findings:
        counts[f.level] = counts.get(f.level, 0) + 1

    if args.json:
        print(json.dumps({
            "date": _dt.date.today().isoformat(),
            "scope": args.scope,
            "counts": counts,
            "findings": [asdict(f) for f in findings],
        }, indent=2))
        return 0

    print(f"Claude Code Doctor — {_dt.date.today().isoformat()}")
    print(f"Scope: {args.scope}")
    print()
    print(f"NOTES: {counts['NOTE']}  WARN: {counts['WARN']}  FAIL: {counts['FAIL']}")
    print()

    if not findings:
        print("No findings.")
        return 0

    order = {"FAIL": 0, "WARN": 1, "NOTE": 2}
    findings.sort(key=lambda f: (order[f.level], f.category))
    print("--- Findings ---")
    for f in findings:
        print(f"[{f.level}] {f.category}: {f.message}  ({f.url})")
        if args.fix_suggest and f.suggested_fix:
            print(f"    Suggested: {f.suggested_fix}")

    return 0  # read-only audit: never errors out


if __name__ == "__main__":
    sys.exit(main())
