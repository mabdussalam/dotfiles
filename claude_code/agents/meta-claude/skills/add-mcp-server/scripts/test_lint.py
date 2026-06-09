#!/usr/bin/env -S uv run --quiet --with pyyaml python3
"""Tests for add-mcp-server lint.py. Run: python test_lint.py"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE / "lint.py"
RUN = ["uv", "run", "--quiet", "--with", "pyyaml", "python", str(LINT)]

PASSING = {"mcpServers": {"linear": {"type": "http", "url": "https://example.com"}}}

WARNING_SSE = {"mcpServers": {"old-server": {"type": "sse", "url": "https://example.com"}}}

WARNING_LITERAL_BEARER = {
    "mcpServers": {
        "leaky": {
            "type": "http",
            "url": "https://example.com",
            "headers": {"Authorization": "Bearer sk-abc123"},
        }
    }
}

WARNING_NO_MCP_BLOCK = {"otherKey": "value"}

FAILING_RESERVED = {"mcpServers": {"workspace": {"type": "stdio", "command": "x"}}}

FAILING_HTTP_NO_URL = {"mcpServers": {"bad": {"type": "http"}}}

FAILING_STDIO_NO_COMMAND = {"mcpServers": {"bad": {"type": "stdio"}}}


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

    def test_warn_sse(self):
        code, out = _run(WARNING_SSE)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("deprecated", out)

    def test_warn_literal_bearer(self):
        code, out = _run(WARNING_LITERAL_BEARER)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")
        self.assertIn("Bearer", out)

    def test_warn_no_mcp_block(self):
        code, out = _run(WARNING_NO_MCP_BLOCK)
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(out.splitlines()[0], "PASS-WITH-WARNINGS")

    def test_fail_reserved_name(self):
        code, out = _run(FAILING_RESERVED)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")
        self.assertIn("workspace", out)

    def test_fail_http_no_url(self):
        code, out = _run(FAILING_HTTP_NO_URL)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")

    def test_fail_stdio_no_command(self):
        code, out = _run(FAILING_STDIO_NO_COMMAND)
        self.assertEqual(code, 1, msg=out)
        self.assertEqual(out.splitlines()[0], "FAIL")


if __name__ == "__main__":
    unittest.main()
