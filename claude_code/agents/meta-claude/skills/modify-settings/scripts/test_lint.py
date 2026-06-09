#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Tests for modify-settings lint.py. Run: python test_lint.py"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE / "lint.py"
RUN = ["uv", "run", "--quiet", "--with", "pyyaml", "python", str(LINT)]


def _run(obj, scope: str = "user") -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(obj, f)
        path = f.name
    try:
        r = subprocess.run(RUN + [path, "--scope", scope],
                           capture_output=True, text=True)
        return r.returncode, r.stdout
    finally:
        Path(path).unlink()


class TestLint(unittest.TestCase):
    def test_pass(self):
        code, out = _run({"model": "claude-opus-4-7", "effortLevel": "high"})
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS")

    def test_warn_unknown_enum_value(self):
        code, out = _run({"effortLevel": "ridiculous"})
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("effortLevel", out)

    def test_warn_bypass_permissions(self):
        code, out = _run({"permissions": {"defaultMode": "bypassPermissions"}})
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("security risk", out)

    def test_warn_auto_mode_at_project(self):
        code, out = _run(
            {"permissions": {"defaultMode": "auto"}}, scope="project"
        )
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("silently ignored", out)

    def test_pass_auto_mode_at_user(self):
        code, out = _run(
            {"permissions": {"defaultMode": "auto"}}, scope="user"
        )
        self.assertEqual(code, 0, msg=out)
        # At user scope, "auto" is allowed; no warning.
        self.assertEqual(out.splitlines()[0], "PASS")

    def test_warn_disable_skill_shell_at_local(self):
        code, out = _run({"disableSkillShellExecution": True}, scope="local")
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("silently ignored", out)

    def test_fail_managed_only_at_user(self):
        code, out = _run({"forceLoginMethod": "sso"}, scope="user")
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")
        self.assertIn("managed-only", out)

    def test_pass_managed_only_at_managed(self):
        code, out = _run({"forceLoginMethod": "sso"}, scope="managed")
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS")

    def test_fail_permissions_allow_wrong_shape(self):
        code, out = _run({"permissions": {"allow": "not-a-list"}})
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_env_wrong_shape(self):
        code, out = _run({"env": {"GOOD": "ok", "BAD": 123}})
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_enabled_plugins_wrong_shape(self):
        code, out = _run({"enabledPlugins": {"x@y": "not-a-bool"}})
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_invalid_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not json")
            path = f.name
        try:
            r = subprocess.run(RUN + [path, "--scope", "user"],
                               capture_output=True, text=True)
        finally:
            Path(path).unlink()
        self.assertEqual(r.returncode, 1, msg=r.stdout)
        self.assertEqual(r.stdout.splitlines()[0], "FAIL")

    def test_json_output(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"model": "claude-opus-4-7"}, f)
            path = f.name
        try:
            r = subprocess.run(RUN + [path, "--scope", "user", "--json"],
                               capture_output=True, text=True)
        finally:
            Path(path).unlink()
        data = json.loads(r.stdout)
        self.assertEqual(data["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
