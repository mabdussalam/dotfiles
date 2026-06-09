#!/usr/bin/env python3
"""Print a human-readable report from a meta-claude routing eval result file.

Usage:
    python report.py                 # loads the most recent results/*.json
    python report.py --results PATH  # loads a specific result file
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _bucket_key(expected) -> str:
    if expected is None:
        return "null"
    return str(expected)


def _observed_key(observed) -> str:
    if observed is None:
        return "null"
    return str(observed)


def _find_latest_results(results_dir: Path) -> Path | None:
    if not results_dir.is_dir():
        return None
    candidates = [
        p for p in results_dir.iterdir()
        if p.is_file() and p.suffix == ".json"
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _pad(s: str, w: int) -> str:
    if len(s) >= w:
        return s
    return s + " " * (w - len(s))


def _truncate(s: str, w: int) -> str:
    if len(s) <= w:
        return s
    return s[: max(0, w - 1)] + "…"


def render_report(data: dict) -> str:
    out: list[str] = []
    ts = data.get("timestamp_utc", "?")
    model = data.get("model") or "(default)"
    num_prompts = data.get("num_prompts", 0)
    runs_per_prompt = data.get("runs_per_prompt", 0)
    summary = data.get("summary", {})
    passed = summary.get("passed", 0)
    total = summary.get("total", num_prompts)
    accuracy = summary.get("accuracy", 0.0)

    out.append(f"Meta-Claude Routing Eval — {ts}")
    out.append(f"Model: {model} | Prompts: {num_prompts} | Runs per prompt: {runs_per_prompt}")
    pct = 100.0 * accuracy
    out.append(f"Accuracy: {passed}/{total} ({pct:.1f}%)")
    out.append("")

    # ---- By-expected-class table -------------------------------------------
    out.append("By expected class:")
    by_expected: dict = summary.get("by_expected", {})
    # Stable ordering: skills A-Z, then "null", then "ASK".
    ordered_keys = sorted(
        by_expected.keys(),
        key=lambda k: (
            2 if k == "ASK" else (1 if k == "null" else 0),
            k,
        ),
    )
    label_w = max((len(k) for k in ordered_keys), default=0)
    label_w = max(label_w, 16)
    for key in ordered_keys:
        bucket = by_expected[key]
        b_total = bucket.get("total", 0)
        b_pass = bucket.get("passed", 0)
        b_pct = (100.0 * b_pass / b_total) if b_total else 0.0
        out.append(f"  {_pad(key, label_w)}  {b_pass}/{b_total}  {b_pct:5.1f}%")
    out.append("")

    # ---- Confusion matrix --------------------------------------------------
    results: list[dict] = data.get("results", [])
    expected_labels: list[str] = []
    observed_labels: list[str] = []
    for r in results:
        e = _bucket_key(r.get("expected"))
        o = _observed_key(r.get("majority_observed"))
        if e not in expected_labels:
            expected_labels.append(e)
        if o not in observed_labels:
            observed_labels.append(o)

    def _label_order(labels: list[str]) -> list[str]:
        return sorted(
            labels,
            key=lambda k: (
                2 if k == "ASK" else (1 if k == "null" else 0),
                k,
            ),
        )

    rows = _label_order(expected_labels)
    cols = _label_order(observed_labels)
    # Ensure null/ASK exist as columns even if no run ever produced them.
    for must in ("null", "ASK"):
        if must not in cols:
            cols.append(must)
    cols = _label_order(cols)
    for must in ("null", "ASK"):
        if must not in rows:
            rows.append(must)
    rows = _label_order(rows)

    counts: dict[tuple[str, str], int] = {}
    for r in results:
        e = _bucket_key(r.get("expected"))
        o = _observed_key(r.get("majority_observed"))
        counts[(e, o)] = counts.get((e, o), 0) + 1

    out.append("Confusion matrix (rows=expected, cols=observed):")
    row_label_w = max(len(r) for r in rows + ["expected"])
    col_widths = {c: max(len(c), 3) for c in cols}
    header = " " * (row_label_w + 2) + "  ".join(_pad(c, col_widths[c]) for c in cols)
    out.append(header)
    for r in rows:
        cells = "  ".join(
            _pad(str(counts.get((r, c), 0)), col_widths[c]) for c in cols
        )
        out.append(f"  {_pad(r, row_label_w)}  {cells}")
    out.append("")

    # ---- Failure list ------------------------------------------------------
    failures = [r for r in results if not r.get("pass")]
    out.append(f"Failures ({len(failures)}):")
    if not failures:
        out.append("  (none)")
    else:
        id_w = max((len(r["id"]) for r in failures), default=0)
        for r in failures:
            pid = _pad(r["id"], id_w)
            prompt_txt = _truncate(r.get("prompt", ""), 60)
            expected = _bucket_key(r.get("expected"))
            observed = _observed_key(r.get("majority_observed"))
            out.append(
                f"  {pid}  \"{prompt_txt}\"  -> expected {expected}, got {observed}"
            )

    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a human-readable report from a meta-claude routing eval JSON file.",
    )
    parser.add_argument(
        "--results",
        default=None,
        help="Path to a results JSON (default: most recent in sibling results/)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent

    if args.results:
        results_path = Path(args.results).resolve()
    else:
        latest = _find_latest_results(script_dir / "results")
        if latest is None:
            print(
                "Error: no results/*.json found. Run run.py first or pass --results PATH.",
                file=sys.stderr,
            )
            return 2
        results_path = latest

    if not results_path.exists():
        print(f"Error: results file not found: {results_path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(results_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {results_path}: {e}", file=sys.stderr)
        return 2

    sys.stdout.write(render_report(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
