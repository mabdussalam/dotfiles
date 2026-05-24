---
name: pr-summary
description: Summarize the current PR's diff and flag risks. Use when asked to review changes, summarize a PR, write a PR description, or check what changed.
disable-model-invocation: true
allowed-tools: Bash(git *)
---

## PR context

Diff:
!`git diff $(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null || echo HEAD~1) HEAD`

Changed files:
!`git diff --name-status $(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null || echo HEAD~1) HEAD`

Commits:
!`git log $(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null || echo HEAD~1)..HEAD --oneline`

## Task

Write a concise PR summary:

1. **What changed** — 2–4 bullet points covering the substance, not the mechanics.
2. **Risks / review checklist** — flag missing tests, error handling gaps, hardcoded values, migration concerns, security surface changes, or anything a reviewer should scrutinize.
3. **Suggested PR title** — imperative mood, ≤72 chars.

If $ARGUMENTS is provided, treat it as additional context or a specific question about the diff.

Be direct. No filler.
