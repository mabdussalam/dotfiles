---
name: debug-session
description: Structured debugging session for a reported error or unexpected behavior. Use when given a traceback, error message, or symptom to investigate. Gathers context, forms hypotheses, and proposes a fix without making changes until confirmed.
allowed-tools: Read Bash(git *) Bash(rg *) Bash(fd *) Bash(uv run *) Bash(node *) Bash(npx *)
---

## Debug brief

**Problem**: $ARGUMENTS

## Current state

```!
git status --short
```

## Instructions

Work through the problem methodically — no guessing, no shotgun changes.

### Phase 1 — Understand

1. Restate the problem in one sentence.
2. Identify the failure boundary: what was expected vs what happened.
3. Locate the relevant code using `rg` and `Read`. Follow imports if needed.

### Phase 2 — Hypothesize

List up to three root-cause hypotheses, ordered by likelihood. For each, note:
- What evidence supports it
- What would falsify it

### Phase 3 — Verify

Run the minimal reproduction or inspection that confirms/eliminates the top hypothesis. Use `uv run` for Python, `node`/`npx` for JS. Read logs or tracebacks carefully.

### Phase 4 — Fix proposal

Describe the fix precisely before touching any files. Include:
- Which file(s) change and why
- Any side-effects or follow-on work
- Whether tests need updating

**Stop here and ask for confirmation before applying the fix.**

If $ARGUMENTS is empty, ask what the problem is before proceeding.
