#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Tests for doctor scan.py — sandboxed via $HOME + cwd."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAN = HERE / "scan.py"
RUN = ["uv", "run", "--quiet", "--with", "pyyaml", "python", str(SCAN)]


def _scan(sandbox: Path, scope: str = "both") -> dict:
    env = {**os.environ, "HOME": str(sandbox)}
    r = subprocess.run(RUN + ["--scope", scope, "--json"],
                       cwd=str(sandbox), env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"scan exited {r.returncode}; stderr={r.stderr!r}")
    if not r.stdout:
        raise RuntimeError(f"scan produced no stdout; stderr={r.stderr!r}")
    return json.loads(r.stdout)


class TestScan(unittest.TestCase):
    def test_empty_sandbox_no_findings(self):
        with tempfile.TemporaryDirectory() as d:
            data = _scan(Path(d))
            self.assertEqual(data["counts"]["FAIL"], 0, msg=data)
            self.assertEqual(data["counts"]["WARN"], 0, msg=data)

    def test_reserved_mcp_name_fails(self):
        with tempfile.TemporaryDirectory() as d:
            sandbox = Path(d)
            (sandbox / ".mcp.json").write_text(json.dumps({
                "mcpServers": {"workspace": {"type": "stdio", "command": "x"}}
            }), encoding="utf-8")
            data = _scan(sandbox, scope="project")
            self.assertGreaterEqual(data["counts"]["FAIL"], 1, msg=data)
            self.assertTrue(any(
                f["category"] == "MCP" and "workspace" in f["message"]
                for f in data["findings"]
            ), msg=data)

    def test_oversized_claude_md_warns(self):
        with tempfile.TemporaryDirectory() as d:
            sandbox = Path(d)
            (sandbox / "CLAUDE.md").write_text("x\n" * 250, encoding="utf-8")
            data = _scan(sandbox, scope="project")
            self.assertTrue(any(
                f["category"] == "CLAUDE.md" and f["level"] == "WARN"
                for f in data["findings"]
            ), msg=data)

    def test_plugin_dir_extra_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            sandbox = Path(d)
            pdir = sandbox / "my-plugin" / ".claude-plugin"
            pdir.mkdir(parents=True)
            (pdir / "plugin.json").write_text(
                '{"name":"x","version":"0.1.0"}', encoding="utf-8")
            (pdir / "extra.md").write_text("nope", encoding="utf-8")
            data = _scan(sandbox, scope="project")
            self.assertGreaterEqual(data["counts"]["FAIL"], 1, msg=data)
            self.assertTrue(any(
                f["category"] == "Plugins" and "extra.md" in f["message"]
                for f in data["findings"]
            ), msg=data)

    def test_oversized_skill_body_warns(self):
        with tempfile.TemporaryDirectory() as d:
            sandbox = Path(d)
            skill_dir = sandbox / ".claude" / "skills" / "huge"
            skill_dir.mkdir(parents=True)
            body = "lorem\n" * 600
            (skill_dir / "SKILL.md").write_text(
                "---\nname: huge\ndescription: too big\n---\n" + body,
                encoding="utf-8",
            )
            data = _scan(sandbox, scope="user")
            self.assertTrue(any(
                f["category"] == "Skills" and "> 500 lines" in f["message"]
                for f in data["findings"]
            ), msg=data)


if __name__ == "__main__":
    unittest.main()
