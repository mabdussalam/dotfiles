#!/usr/bin/env bash
# Post-edit Python auto-formatter for Claude Code.
# Triggered after Write/Edit/MultiEdit on .py files.
#
# Contract (https://code.claude.com/docs/en/hooks):
#   - Exit 0 with no stdout: silent success.
#   - Exit 0 with JSON `{"decision":"block","reason":"..."}` on stdout:
#     `reason` is injected into Claude's context as a follow-up prompt.
#
# `ruff format` only fails on real syntax errors, so surfacing its stderr
# tells Claude there's something to inspect and fix.

set -uo pipefail

FILE_PATH=$(jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)

if [[ -z "$FILE_PATH" || ! -f "$FILE_PATH" || "${FILE_PATH##*.}" != "py" ]]; then
    exit 0
fi

if ! command -v ruff &>/dev/null; then
    exit 0
fi

if ! output=$(ruff format "$FILE_PATH" 2>&1); then
    jq -nc --arg reason "ruff format failed on $FILE_PATH — likely a syntax error introduced by the edit. Inspect and fix:"$'\n\n'"$output" \
        '{decision:"block", reason:$reason, suppressOutput:true}'
fi

exit 0
