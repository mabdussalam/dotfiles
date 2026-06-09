#!/usr/bin/env python3
"""Routing eval for the meta-claude subagent.

For each prompt in prompts.jsonl, run `claude --agent meta-claude -p <prompt>`
and classify which child skill (if any) meta-claude invoked. Compare against
the expected route, aggregate, and write a JSON report.

Routes:
  - <skill-name> : meta-claude invoked Skill(skill=<skill-name>)
  - "ASK"        : meta-claude invoked AskUserQuestion (disambiguation)
  - null         : meta-claude answered inline (no Skill, no AskUserQuestion)

Running meta-claude as the root agent (rather than dispatching to it as a
subagent from a generic root) isolates the routing decision and avoids paying
for the root → subagent hop on every prompt.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import select
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


# ---------------------------------------------------------------------------
# Project discovery (mirrors skill-creator/scripts/run_eval.py)
# ---------------------------------------------------------------------------


def find_project_root() -> Path:
    """Walk up from cwd looking for a .claude/ directory; fall back to cwd."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


# ---------------------------------------------------------------------------
# Per-prompt runner
# ---------------------------------------------------------------------------


def _classify_tool_use(name: str, tool_input: dict) -> str | None:
    """Map a tool_use event to a route token, or return None if not a routing signal.

    meta-claude runs as the root agent (via `claude --agent meta-claude`), so
    Skill / AskUserQuestion calls reflect its direct routing decision.
    """
    if name == "Skill":
        skill = tool_input.get("skill")
        if isinstance(skill, str) and skill:
            return skill
        # Skill call with unparsed/empty input: treat as unknown skill marker.
        return "__skill_unknown__"
    if name == "AskUserQuestion":
        return "ASK"
    return None


def run_single_prompt(
    prompt: str,
    timeout: int,
    project_root: str,
    model: str | None,
) -> tuple[str | None, float]:
    """Run one prompt through `claude -p` and return (observed_route, duration_sec).

    observed_route is one of:
      - a string skill name (first Skill tool_use)
      - "ASK" (first AskUserQuestion tool_use, if no Skill seen first)
      - None (no routing tool calls -> inline answer)

    We short-circuit as soon as we have a definitive Skill or AskUserQuestion
    signal, or when we see a `result` event / `message_stop` after collecting
    no routing signals.
    """
    cmd = [
        "claude",
        "--agent", "meta-claude",
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if model:
        cmd.extend(["--model", model])

    # Strip CLAUDECODE so nesting claude -p inside a Claude Code session works.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    start = time.time()
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=project_root,
        env=env,
    )
    # stdout=PIPE always yields a non-None pipe; assert for type-checker clarity.
    assert process.stdout is not None
    stdout = process.stdout

    observed: str | None = None
    ask_observed = False
    buffer = ""

    # Track partial tool_use blocks from stream_event deltas so we can capture
    # the skill name as soon as it streams in.
    pending_tool_name: str | None = None
    accumulated_json = ""

    try:
        while True:
            if time.time() - start > timeout:
                break

            if process.poll() is not None:
                remaining = stdout.read()
                if remaining:
                    buffer += remaining.decode("utf-8", errors="replace")
                # Drain final buffer below, then exit loop.
                lines, buffer = _split_lines(buffer)
                for line in lines:
                    observed, ask_observed, _ = _ingest_line(line, observed, ask_observed)
                break

            ready, _, _ = select.select([stdout], [], [], 1.0)
            if not ready:
                continue

            try:
                chunk = os.read(stdout.fileno(), 8192)
            except OSError:
                break
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")

            lines, buffer = _split_lines(buffer)
            for line in lines:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                etype = event.get("type")

                # ----- partial stream events --------------------------------
                if etype == "stream_event":
                    se = event.get("event", {})
                    se_type = se.get("type", "")

                    if se_type == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_name = cb.get("name", "")
                            tool_input = cb.get("input", {}) or {}
                            # If input is already populated, classify immediately.
                            route = _classify_tool_use(tool_name, tool_input)
                            if route is not None:
                                if route == "ASK":
                                    if observed is None:
                                        ask_observed = True
                                elif route != "__skill_unknown__":
                                    if observed is None:
                                        observed = route
                                    return observed, time.time() - start
                                else:
                                    # Skill but name not in start payload — wait for deltas.
                                    pending_tool_name = "Skill"
                                    accumulated_json = ""
                            elif tool_name == "Skill":
                                pending_tool_name = "Skill"
                                accumulated_json = ""
                            elif tool_name == "AskUserQuestion":
                                if observed is None:
                                    ask_observed = True
                                pending_tool_name = None
                            else:
                                # Read, Write, Bash, etc. — not a routing signal.
                                pending_tool_name = None

                    elif se_type == "content_block_delta" and pending_tool_name == "Skill":
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            accumulated_json += delta.get("partial_json", "")
                            # Try to parse what we have. As soon as we can pull
                            # out a "skill" field, lock in the route.
                            skill_name = _try_extract_skill(accumulated_json)
                            if skill_name and observed is None:
                                observed = skill_name
                                return observed, time.time() - start

                    elif se_type == "content_block_stop":
                        if pending_tool_name == "Skill" and observed is None:
                            skill_name = _try_extract_skill(accumulated_json)
                            if skill_name:
                                observed = skill_name
                                return observed, time.time() - start
                        pending_tool_name = None
                        accumulated_json = ""

                    elif se_type == "message_stop":
                        # End of an assistant message; no more deltas for this turn.
                        pending_tool_name = None
                        accumulated_json = ""

                # ----- full assistant messages ------------------------------
                elif etype == "assistant":
                    message = event.get("message", {})
                    for item in message.get("content", []):
                        if item.get("type") != "tool_use":
                            continue
                        tool_name = item.get("name", "")
                        tool_input = item.get("input", {}) or {}
                        route = _classify_tool_use(tool_name, tool_input)
                        if route is None:
                            continue
                        if route == "ASK":
                            if observed is None:
                                ask_observed = True
                            continue
                        if route == "__skill_unknown__":
                            continue
                        if observed is None:
                            observed = route
                            return observed, time.time() - start

                # ----- terminal result --------------------------------------
                elif etype == "result":
                    # Final event. Decide route now.
                    if observed is None and ask_observed:
                        observed = "ASK"
                    return observed, time.time() - start
    finally:
        if process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception:
                pass

    # Fell out of the loop without a `result` event (timeout or EOF).
    if observed is None and ask_observed:
        observed = "ASK"
    return observed, time.time() - start


def _split_lines(buffer: str) -> tuple[list[str], str]:
    """Pull complete newline-terminated lines from buffer; return (lines, rest)."""
    if "\n" not in buffer:
        return [], buffer
    parts = buffer.split("\n")
    rest = parts[-1]
    lines = [p.strip() for p in parts[:-1] if p.strip()]
    return lines, rest


def _ingest_line(line, observed, ask_observed):
    """Stub used by the final-drain path; mirrors the in-loop logic for `assistant`/`result` events only."""
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return observed, ask_observed, False
    etype = event.get("type")
    if etype == "assistant":
        message = event.get("message", {})
        for item in message.get("content", []):
            if item.get("type") != "tool_use":
                continue
            tool_name = item.get("name", "")
            tool_input = item.get("input", {}) or {}
            route = _classify_tool_use(tool_name, tool_input)
            if route is None or route == "__skill_unknown__":
                continue
            if route == "ASK":
                if observed is None:
                    ask_observed = True
                continue
            if observed is None:
                observed = route
    elif etype == "result":
        return observed, ask_observed, True
    return observed, ask_observed, False


def _try_extract_skill(partial: str) -> str | None:
    """Best-effort extraction of the `skill` field from a partial JSON blob."""
    # First try a clean parse.
    try:
        obj = json.loads(partial)
        if isinstance(obj, dict):
            v = obj.get("skill")
            if isinstance(v, str) and v:
                return v
    except Exception:
        pass
    # Fall back to a string search; tolerant of unfinished JSON.
    key = '"skill"'
    idx = partial.find(key)
    if idx == -1:
        return None
    rest = partial[idx + len(key):]
    # Skip past colon and whitespace.
    i = 0
    while i < len(rest) and rest[i] in ' \t:':
        i += 1
    if i >= len(rest) or rest[i] != '"':
        return None
    i += 1
    end = rest.find('"', i)
    if end == -1:
        return None
    name = rest[i:end]
    return name or None


# ---------------------------------------------------------------------------
# Worker entry (top-level for ProcessPoolExecutor)
# ---------------------------------------------------------------------------


def _worker(item: dict, run_idx: int, timeout: int, project_root: str, model: str | None):
    try:
        observed, duration = run_single_prompt(
            prompt=item["prompt"],
            timeout=timeout,
            project_root=project_root,
            model=model,
        )
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  worker error for {item['id']} run {run_idx}: {exc}", file=sys.stderr)
        return item["id"], run_idx, None, 0.0
    return item["id"], run_idx, observed, duration


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _majority(values: list) -> object:
    """Return the most common value; ties broken by first occurrence."""
    if not values:
        return None
    counter = collections.Counter()
    order = {}
    for i, v in enumerate(values):
        # Counter doesn't like None as a sentinel issue, but works fine.
        key = ("__null__" if v is None else v)
        counter[key] += 1
        order.setdefault(key, i)
    best = max(counter.items(), key=lambda kv: (kv[1], -order[kv[0]]))
    key = best[0]
    return None if key == "__null__" else key


def _bucket_key(expected) -> str:
    if expected is None:
        return "null"
    return str(expected)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Routing eval for the meta-claude Claude Code subagent.",
    )
    script_dir = Path(__file__).resolve().parent
    parser.add_argument(
        "--prompts",
        default=str(script_dir / "prompts.jsonl"),
        help="Path to prompts.jsonl (default: sibling prompts.jsonl)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write JSON results (default: results/<UTC-ISO>.json)",
    )
    parser.add_argument("--num-workers", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=120, help="Per-prompt timeout in seconds")
    parser.add_argument("--runs-per-prompt", type=int, default=3)
    parser.add_argument("--model", default=None, help="Override model (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print per-prompt PASS/FAIL to stderr")
    args = parser.parse_args()

    prompts_path = Path(args.prompts).resolve()
    if not prompts_path.exists():
        print(f"Error: prompts file not found: {prompts_path}", file=sys.stderr)
        return 2

    prompts: list[dict] = []
    with prompts_path.open() as fh:
        for ln, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                prompts.append(json.loads(raw))
            except json.JSONDecodeError as e:
                print(f"Error: invalid JSON on line {ln} of {prompts_path}: {e}", file=sys.stderr)
                return 2

    if not prompts:
        print("Error: no prompts loaded.", file=sys.stderr)
        return 2

    project_root = str(find_project_root())
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        results_dir = script_dir / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        output_path = results_dir / f"{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(
            f"Routing eval: {len(prompts)} prompts × {args.runs_per_prompt} runs "
            f"= {len(prompts) * args.runs_per_prompt} calls "
            f"(workers={args.num_workers}, timeout={args.timeout}s)",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)

    # Collect runs per prompt-id.
    runs_by_id: dict[str, list[dict]] = {p["id"]: [] for p in prompts}

    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        future_to_meta = {}
        for item in prompts:
            for run_idx in range(args.runs_per_prompt):
                fut = executor.submit(
                    _worker,
                    item,
                    run_idx,
                    args.timeout,
                    project_root,
                    args.model,
                )
                future_to_meta[fut] = (item, run_idx)

        for fut in as_completed(future_to_meta):
            item, run_idx = future_to_meta[fut]
            try:
                pid, _, observed, duration = fut.result()
            except Exception as exc:
                print(
                    f"  prompt {item['id']} run {run_idx} crashed: {exc}",
                    file=sys.stderr,
                )
                pid, observed, duration = item["id"], None, 0.0

            runs_by_id[pid].append({"observed": observed, "duration_sec": round(duration, 2)})

            if args.verbose:
                status_obs = "null" if observed is None else observed
                expected = "null" if item["expected"] is None else item["expected"]
                marker = "PASS" if observed == item["expected"] else "FAIL"
                print(
                    f"  [{marker}] {item['id']:<24} expected={expected:<16} observed={status_obs:<16} "
                    f"({duration:.1f}s)",
                    file=sys.stderr,
                )

    # Build per-prompt results.
    results: list[dict] = []
    for item in prompts:
        runs = runs_by_id[item["id"]]
        observed_values = [r["observed"] for r in runs]
        majority = _majority(observed_values)
        results.append({
            "id": item["id"],
            "prompt": item["prompt"],
            "expected": item["expected"],
            "runs": runs,
            "majority_observed": majority,
            "pass": majority == item["expected"],
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    by_expected: dict[str, dict] = {}
    for r in results:
        key = _bucket_key(r["expected"])
        bucket = by_expected.setdefault(key, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if r["pass"]:
            bucket["passed"] += 1

    output = {
        "timestamp_utc": timestamp,
        "model": args.model,
        "num_prompts": total,
        "runs_per_prompt": args.runs_per_prompt,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "accuracy": (passed / total) if total else 0.0,
            "by_expected": by_expected,
        },
    }

    output_path.write_text(json.dumps(output, indent=2))

    pct = (100.0 * passed / total) if total else 0.0
    print(f"Accuracy: {passed}/{total} ({pct:.1f}%) -> {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
