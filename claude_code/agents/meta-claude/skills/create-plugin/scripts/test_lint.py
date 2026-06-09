#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Tests for create-plugin lint.py. Run: python test_lint.py"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE / "lint.py"
RUN = ["uv", "run", "--quiet", "--with", "pyyaml", "python", str(LINT)]


def _setup_passing(root: Path) -> None:
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "my-plugin", "version": "0.1.0"}),
        encoding="utf-8",
    )


def _setup_warn_bundled_agent_carries_hooks(root: Path) -> None:
    _setup_passing(root)
    (root / "agents").mkdir()
    (root / "agents" / "a.md").write_text(
        "---\nname: a\ndescription: d\nhooks:\n  PostToolUse: []\n---\n",
        encoding="utf-8",
    )


def _setup_warn_bundled_agent_bad_isolation(root: Path) -> None:
    _setup_passing(root)
    (root / "agents").mkdir()
    (root / "agents" / "b.md").write_text(
        "---\nname: b\ndescription: d\nisolation: container\n---\n",
        encoding="utf-8",
    )


def _setup_fail_extra_in_plugin_dir(root: Path) -> None:
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "p", "version": "0.1.0"}),
        encoding="utf-8",
    )
    (root / ".claude-plugin" / "extras.md").write_text("not allowed here", encoding="utf-8")


def _setup_fail_missing_manifest(root: Path) -> None:
    (root / ".claude-plugin").mkdir()


def _setup_fail_no_plugin_dir(_root: Path) -> None:
    # bare directory; no .claude-plugin
    assert _root.is_dir()


def _setup_fail_missing_version(root: Path) -> None:
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "p"}),
        encoding="utf-8",
    )


def _run(setup) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        setup(root)
        r = subprocess.run(RUN + [str(root)], capture_output=True, text=True)
        return r.returncode, r.stdout


class TestLint(unittest.TestCase):
    def test_pass(self):
        code, out = _run(_setup_passing)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS")

    def test_warn_bundled_agent_hooks(self):
        code, out = _run(_setup_warn_bundled_agent_carries_hooks)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("silently ignore", out)

    def test_warn_bundled_agent_bad_isolation(self):
        code, out = _run(_setup_warn_bundled_agent_bad_isolation)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")

    def test_fail_extras_in_plugin_dir(self):
        code, out = _run(_setup_fail_extra_in_plugin_dir)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_missing_manifest(self):
        code, out = _run(_setup_fail_missing_manifest)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_no_plugin_dir(self):
        code, out = _run(_setup_fail_no_plugin_dir)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_missing_version(self):
        code, out = _run(_setup_fail_missing_version)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")


if __name__ == "__main__":
    unittest.main()
