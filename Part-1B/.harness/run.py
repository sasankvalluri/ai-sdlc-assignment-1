"""Three-layer evaluation runner.

Pipeline (Article III):
    dataset  →  backend call  →  L1 schema  →  L2 invariants  →  L3 semantic
                                           ↘ eval-results-<ts>.json ↙
Aggregate decision:
    L1 per-case pass rate  must be 1.00
    L2 per-case pass rate  must be 1.00
    L3 mean per-case score must be ≥ 0.70
    overall aggregate (mean of the three rates/scores) must be ≥ 0.85
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import statistics
import sys
import time
from dataclasses import asdict
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent
sys.path.insert(0, str(ROOT / "src"))

from reminder_agent.agent import Agent  # noqa: E402
from reminder_agent.backends import build  # noqa: E402
from reminder_agent.prompt import prompt_hash  # noqa: E402

sys.path.insert(0, str(HARNESS_DIR))

from layer1 import evaluate as l1_evaluate  # noqa: E402
from layer2 import evaluate as l2_evaluate  # noqa: E402
from layer3 import evaluate as l3_evaluate  # noqa: E402

DATASET = ROOT / "evals" / "dataset.json"
EVIDENCE = ROOT / "evidence"
L1_PASS_THRESHOLD = 1.0
L2_PASS_THRESHOLD = 1.0
L3_SCORE_THRESHOLD = 0.70
AGGREGATE_THRESHOLD = 0.85


def _ts() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="reminder-harness")
    p.add_argument("--backend", choices=["real", "groq", "mock"], default=None,
                   help="Backend to use; default: groq if GROQ_API_KEY set, "
                        "else real if GITHUB_TOKEN set, else mock.")
    p.add_argument("--max-cases", type=int, default=None,
                   help="Cap the number of cases (debug).")
    return p.parse_args(argv)


def _select_backend(explicit: str | None) -> str:
    if explicit:
        return explicit
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("GITHUB_MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        return "real"
    return "mock"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    backend_name = _select_backend(args.backend)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    ts = _ts()

    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    if args.max_cases:
        cases = cases[: args.max_cases]

    try:
        agent = Agent(backend=build(backend_name))
    except RuntimeError as exc:
        print(f"backend init failed: {exc}", file=sys.stderr)
        return 3

    per_case: list[dict] = []
    for case in cases:
        t0 = time.monotonic()
        try:
            res = agent.parse(
                text=case["input"]["text"],
                now_iso=case["input"]["now"],
                timezone=case["input"].get("timezone", "UTC"),
            )
        except Exception as exc:  # noqa: BLE001
            per_case.append(
                {
                    "id": case["id"],
                    "category": case["category"],
                    "input": case["input"],
                    "expect": case["expect"],
                    "backend_error": repr(exc),
                    "duration_s": round(time.monotonic() - t0, 3),
                    "l1": {"passed": False, "checks": []},
                    "l2": {"passed": False, "agent_invariants": [], "dataset_invariants": []},
                    "l3": {"score": 0.0, "passed": False, "notes": ["backend error"]},
                }
            )
            continue

        l1 = l1_evaluate(res.call.raw_output)
        l2 = {"passed": False, "agent_invariants": [], "dataset_invariants": []}
        l3 = {"score": 0.0, "passed": False, "notes": ["L1 failed; L3 not scored"]}

        if l1["passed"] and res.parsed is not None:
            l2_report = l2_evaluate(
                res.parsed, case=case, now_iso=case["input"]["now"], input_text=case["input"]["text"]
            )
            l2 = {
                "passed": l2_report.passed,
                "agent_invariants": l2_report.agent_invariants,
                "dataset_invariants": l2_report.dataset_invariants,
            }
            l3_score = l3_evaluate(res.parsed, case=case)
            l3 = asdict(l3_score)

        per_case.append(
            {
                "id": case["id"],
                "category": case["category"],
                "input": case["input"],
                "expect": case["expect"],
                "raw_output": res.call.raw_output,
                "backend": res.call.backend,
                "model_id": res.call.model_id,
                "temperature": res.call.temperature,
                "duration_s": round(time.monotonic() - t0, 3),
                "l1": l1,
                "l2": l2,
                "l3": l3,
            }
        )

    # Aggregate
    total = len(per_case)
    l1_rate = sum(1 for c in per_case if c["l1"]["passed"]) / total
    l2_rate = sum(1 for c in per_case if c["l2"]["passed"]) / total
    l3_scores = [c["l3"]["score"] for c in per_case]
    l3_mean = statistics.mean(l3_scores) if l3_scores else 0.0
    aggregate = statistics.mean([l1_rate, l2_rate, l3_mean])

    gates = {
        "L1_pass_rate": {
            "value": round(l1_rate, 4),
            "threshold": L1_PASS_THRESHOLD,
            "passed": l1_rate >= L1_PASS_THRESHOLD,
        },
        "L2_pass_rate": {
            "value": round(l2_rate, 4),
            "threshold": L2_PASS_THRESHOLD,
            "passed": l2_rate >= L2_PASS_THRESHOLD,
        },
        "L3_mean_score": {
            "value": round(l3_mean, 4),
            "threshold": L3_SCORE_THRESHOLD,
            "passed": l3_mean >= L3_SCORE_THRESHOLD,
        },
        "aggregate": {
            "value": round(aggregate, 4),
            "threshold": AGGREGATE_THRESHOLD,
            "passed": aggregate >= AGGREGATE_THRESHOLD,
        },
    }
    overall = all(g["passed"] for g in gates.values())

    record = {
        "timestamp": ts,
        "backend": backend_name,
        "prompt_hash": prompt_hash(),
        "dataset_version": dataset.get("version"),
        "case_count": total,
        "gates": gates,
        "passed": overall,
        "cases": per_case,
    }
    out_path = EVIDENCE / f"eval-results-{ts}.json"
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    _print_summary(record, out_path)
    return 0 if overall else 1


def _print_summary(record: dict, out_path: Path) -> None:
    print("=" * 72)
    print(f"Reminder Agent — 3-layer eval @ {record['timestamp']}")
    print(f"backend={record['backend']}  prompt_hash={record['prompt_hash']}  n={record['case_count']}")
    print("=" * 72)
    for case in record["cases"]:
        mark_l1 = "✓" if case["l1"]["passed"] else "✗"
        mark_l2 = "✓" if case["l2"]["passed"] else "✗"
        mark_l3 = "✓" if case["l3"]["passed"] else "✗"
        print(
            f"  {case['id']:>4}  {case['category']:<12}"
            f"  L1 {mark_l1}  L2 {mark_l2}  L3 {mark_l3} ({case['l3']['score']:.2f})"
        )
    print("-" * 72)
    for gate, info in record["gates"].items():
        mark = "✓" if info["passed"] else "✗"
        print(f"  {mark}  {gate:<18} value={info['value']:.4f}  threshold={info['threshold']}")
    print("-" * 72)
    print(f"Overall: {'PASS' if record['passed'] else 'FAIL'}")
    print(f"Evidence: {out_path}")
    print("=" * 72)
    # Print failure detail for the first few failing cases.
    for case in record["cases"]:
        if case["l1"]["passed"] and case["l2"]["passed"] and case["l3"]["passed"]:
            continue
        print(f"\n--- case {case['id']} ({case['category']}) ---")
        print(f"input: {case['input']['text']!r}")
        print(f"raw:   {case.get('raw_output', '<no output>')[:400]}")
        if not case["l1"]["passed"]:
            for c in case["l1"]["checks"]:
                if not c["passed"]:
                    print(f"  L1 ✗ {c['name']}: {c['detail']}")
        if not case["l2"]["passed"]:
            for c in case["l2"]["agent_invariants"] + case["l2"]["dataset_invariants"]:
                if not c["passed"]:
                    print(f"  L2 ✗ {c['name']}: {c['detail']}")
        if not case["l3"]["passed"]:
            print(f"  L3 score={case['l3']['score']:.2f}: {case['l3']['notes']}")


if __name__ == "__main__":
    sys.exit(main())
