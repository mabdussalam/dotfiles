#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Tests for create-subagent lint.py. Run: python test_lint.py"""
from __future__ import annotations

import json as _json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE / "lint.py"
RUN = ["uv", "run", "--quiet", "--with", "pyyaml", "python", str(LINT)]

PASSING = """---
name: hello-bot
description: A friendly subagent that greets the user.
tools: [Read, Bash]
model: inherit
---

# hello-bot

Body content.
"""

WARNING = """---
name: hello-bot
description: A friendly subagent that greets the user.
tools: [Read, NewExperimentalTool, Agent]
model: gpt-9-future
---
"""

FAILING_MISSING_DESC = """---
name: hello-bot
tools: [Read]
---
"""

FAILING_BAD_NAME = """---
name: BadName_WithCaps
description: bad name format
---
"""


def _run(content: str, filename: str = "hello-bot.md") -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / filename
        p.write_text(content, encoding="utf-8")
        r = subprocess.run(RUN + [str(p)], capture_output=True, text=True)
        return r.returncode, r.stdout


class TestLint(unittest.TestCase):
    def test_pass(self):
        code, out = _run(PASSING)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS")

    def test_warn_unknown_tool_and_agent(self):
        code, out = _run(WARNING)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("NewExperimentalTool", out)
        self.assertIn("Agent", out)

    def test_fail_missing_description(self):
        code, out = _run(FAILING_MISSING_DESC)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_bad_name(self):
        code, out = _run(FAILING_BAD_NAME)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_filename_mismatch_warns(self):
        # name says hello-bot but file is named other-name.md
        code, out = _run(PASSING, filename="other-name.md")
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("filename stem", out)

    def test_json_output(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "hello-bot.md"
            p.write_text(PASSING, encoding="utf-8")
            r = subprocess.run(RUN + [str(p), "--json"], capture_output=True, text=True)
        data = _json.loads(r.stdout)
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(data["fails"], [])


if __name__ == "__main__":
    unittest.main()
