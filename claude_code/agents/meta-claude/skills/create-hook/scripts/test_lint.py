#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Tests for create-hook lint.py. Run: python test_lint.py"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE / "lint.py"
RUN = ["uv", "run", "--quiet", "--with", "pyyaml", "python", str(LINT)]

PASSING = {
    "hooks": {
        "PostToolUse": [
            {"matcher": "Write|Edit", "hooks": [
                {"type": "command", "command": "echo hi"}
            ]}
        ]
    }
}

WARNING_UNKNOWN_EVENT = {
    "hooks": {
        "MyCustomEvent": [
            {"matcher": "", "hooks": [{"type": "command", "command": "echo hi"}]}
        ]
    }
}

WARNING_URL = {
    "hooks": {
        "PostToolUse": [
            {"matcher": "", "hooks": [
                {"type": "url", "url": "https://example.com"}
            ]}
        ]
    }
}

FAILING_BAD_REGEX = {
    "hooks": {
        "PostToolUse": [
            {"matcher": "(unclosed", "hooks": [
                {"type": "command", "command": "echo hi"}
            ]}
        ]
    }
}

FAILING_BAD_TYPE = {
    "hooks": {
        "PostToolUse": [
            {"matcher": "", "hooks": [
                {"type": "magical", "command": "echo hi"}
            ]}
        ]
    }
}

FAILING_HOOKS_NOT_OBJECT = {"hooks": ["not", "an", "object"]}


def _run(obj) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(obj, f)
        path = f.name
    try:
        r = subprocess.run(RUN + [path], capture_output=True, text=True)
        return r.returncode, r.stdout
    finally:
        Path(path).unlink()


class TestLint(unittest.TestCase):
    def test_pass(self):
        code, out = _run(PASSING)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS")

    def test_warn_unknown_event(self):
        code, out = _run(WARNING_UNKNOWN_EVENT)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")

    def test_warn_url_type(self):
        code, out = _run(WARNING_URL)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("non-2xx", out)

    def test_fail_bad_regex(self):
        code, out = _run(FAILING_BAD_REGEX)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_bad_type(self):
        code, out = _run(FAILING_BAD_TYPE)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_hooks_not_object(self):
        code, out = _run(FAILING_HOOKS_NOT_OBJECT)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")


if __name__ == "__main__":
    unittest.main()
