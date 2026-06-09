# meta-claude evals

Evals for the `meta-claude` Claude Code subagent. The goal is to measure
whether meta-claude correctly **routes** an incoming user request to the
right child skill (or, when appropriate, answers inline / asks for
disambiguation).

The routing contract that this eval validates lives in §2 of
`../meta-claude.md` (the "Routing table").

## Purpose

For each prompt in `routing/prompts.jsonl` we ask the question:

> Given user prompt X, does meta-claude invoke the right child skill —
> or correctly answer inline, or correctly ask a clarifying question?

Detection is rule-based, not LLM-judged. The runner invokes meta-claude as
the **root** agent via `claude --agent meta-claude -p <prompt>`, parses the
`stream-json` event log, and classifies the first routing tool call:

- A `Skill` tool call with `skill=<name>` -> route `<name>`.
- An `AskUserQuestion` tool call (and no preceding `Skill`) -> route `ASK`.
- No `Skill` and no `AskUserQuestion` -> route `null` (inline answer).

Running meta-claude as root (rather than as a subagent dispatched from a
generic root) isolates the routing decision and avoids paying for the root
→ subagent hop on every prompt.

## Layout

```
evals/
  README.md                # this file
  routing/
    prompts.jsonl          # the 32 routing prompts (id, prompt, expected)
    run.py                 # runner: spawns `claude -p` per prompt, classifies the route
    report.py              # aggregator: pretty-prints a results JSON
    results/
      .gitkeep             # results/*.json are gitignored — only the dir is tracked
```

## How to run

### Quickstart

```sh
cd routing
python run.py --verbose
```

This will:

1. Read `prompts.jsonl` (32 prompts).
2. For each prompt, run `claude --agent meta-claude -p <prompt>` 3 times in
   parallel (5 workers by default).
3. Classify each run's route from the stream-json output.
4. Write `results/<UTC-ISO-timestamp>.json` and print a one-line summary.

Then render the human-readable report:

```sh
python report.py
```

### Tunables

```
run.py
  --prompts PATH             # default: ./prompts.jsonl
  --output PATH              # default: ./results/<timestamp>.json
  --num-workers N            # default: 5
  --timeout SECS             # default: 120 (per-prompt)
  --runs-per-prompt N        # default: 3 — bump for tighter variance estimates
  --model NAME               # default: user's configured model
  --verbose                  # PASS/FAIL per prompt to stderr
```

`report.py` only takes `--results PATH`. With no flag it picks the most
recent file in `results/`.

## Reading the report

`report.py` prints four sections:

1. **Header** — timestamp, model, prompt count, runs per prompt, overall
   accuracy.
2. **By expected class** — accuracy broken down by the expected route
   bucket. This is the first place to look for systematic miscoding
   (e.g. `ASK` consistently misrouting to `create-hook`).
3. **Confusion matrix** — rows are the expected route, columns are the
   observed (majority) route. The diagonal is correct routing; off-diagonal
   cells are misrouting. `null` and `ASK` are included as their own
   rows/cols. Watch the column totals: if one skill (e.g. `create-hook`)
   is "stealing" prompts that belong to other skills, you'll see its
   column dominate.
4. **Failures** — every prompt where the majority observed route did not
   match `expected`. Includes id, truncated prompt, and the expected -> got
   delta.

## Adding new prompts

Each line of `prompts.jsonl` is a single JSON object:

```json
{"id": "<slug>", "prompt": "<user-facing text>", "expected": "<route>"}
```

- `id` — kebab-case, prefixed with the expected route bucket plus a
  numeric suffix (e.g. `create-hook-04`, `ask-04`, `inline-03`). Keep
  ids globally unique.
- `prompt` — the raw user text, exactly as a user would type it. Don't
  prefix with "please" or wrap in templating.
- `expected` — one of:
  - a string skill name (`"create-hook"`, `"modify-settings"`, ...)
  - JSON `null` for prompts that should be answered inline (facts,
    diagnostic questions)
  - `"ASK"` for prompts that are genuinely ambiguous — meta-claude
    should ask the user to disambiguate before routing

Add new prompts at the end of the file, grouped with their bucket. If you
add a new expected bucket (a new skill route), no code change is needed —
the runner and the report key off whatever string appears in `expected`.

## Target

- **Overall accuracy ≥ 85%** on the current 32-prompt set with
  `--runs-per-prompt 3`. **Current baseline (2026-05-27): 90.6% (29/32)**
  with all 8 child-skill buckets at 100% and `null` at 100%.
- **No single skill should consistently steal prompts** that belong to
  *another skill*. Concretely: in the skill-vs-skill area of the confusion
  matrix, no off-diagonal cell should hold more than 1 prompt. (Two or
  more prompts misrouting the same way is a routing-table problem in
  `meta-claude.md`, not noise.)
- `null` (inline-answer) accuracy should be ≥ 80%; if it drops, meta-claude
  is over-eager to dispatch.

### The ASK bucket is a known limitation

The current baseline scores **0/3 on the ASK bucket**, and this is treated
as expected behaviour rather than a routing-table bug. Investigation showed
that the three prompts in the ASK bucket each have a defensible "natural
primitive":

- `"format files on save"` matches `create-hook`'s "fire X after Y"
  trigger phrase exactly.
- `"check security automatically when I edit code"` is a textbook
  `PostToolUse` hook scenario.
- `"set up MCP for Notion"` has a known existing MCP server to register,
  so `add-mcp-server` is the right call in practice.

The model decisively picks the natural primitive instead of asking, and
that is usually the right behaviour for a real user. The routing table's
**Ambiguous** row in §2 still exists for genuinely under-specified prompts
(e.g. "make claude help me with my python code") — it just doesn't fire
on these particular examples. Do not aggressively widen the Ambiguous row
to force ASK on these; the cost is regression on the non-ambiguous skill
routes that the table currently handles at 100%.

If you want to test the Ambiguous row itself, replace the three ASK
prompts with prompts that have no defensible natural primitive. Until
then, treat the ASK bucket as a tripwire for behaviour change rather
than a target.

## Known caveats

- **Live `claude` calls.** The runner shells out to
  `claude --agent meta-claude -p <prompt>`. You need Claude Code installed,
  on `PATH`, authenticated, and on a version where `--agent` is supported.
  The runner strips `CLAUDECODE` from the environment so it can be invoked
  from inside an interactive Claude Code session.
- **meta-claude must be installed.** Either at
  `~/.claude/agents/meta-claude.md` (after `install/61-copy-claude.sh`) or
  under a project-local `.claude/agents/`. `--agent meta-claude` will
  fail loudly if the agent is not on disk. The runner sets cwd to the
  discovered project root (walking up for a `.claude/` directory).
- **Run-to-run variance.** A single run is noisy; `--runs-per-prompt 3`
  is the minimum to compute a sane majority. Bump to 5 if you want to
  detect ≤10% accuracy regressions.
- **Cost.** Default config is 32 prompts × 3 runs = 96 Claude calls per
  invocation. Each call boots meta-claude directly and may invoke one child
  Skill before stopping, so end-to-end runtime is a couple of minutes with
  5 workers and per-call cost is non-trivial. Don't run this in a tight
  loop.
- **Timeouts default to 120s.** If you see timeouts in `results/*.json`
  (recorded as `observed: null` with low `duration_sec` relative to the
  cap), raise `--timeout`.

## Results commit policy

Individual run snapshots in `results/` are **not** committed — only the
directory is tracked via `.gitkeep`. If you establish a benchmark run as
a regression baseline, commit it under a stable filename
(e.g. `results/baseline-2026Q2.json`) and reference it from the routing
table or from a follow-up PR description. Day-to-day eval output stays
local.
