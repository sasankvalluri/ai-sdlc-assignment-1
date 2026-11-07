"""Deterministic harness runner — four gates, JSON verdict, no shortcuts.

Gates (constitution Article III):
  G1  Lint              ruff check src tests
  G2  Security (SAST)   bandit -r src -ll        (medium/high issues)
  G3  Tests             pytest -q
  G4  Coverage          pytest --cov=src/smart_todo --cov-fail-under=85

Writes evidence/harness-run-<ts>.json. Exits 0 iff every gate is PASS.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence"


@dataclass
class GateResult:
    gate: str
    name: str
    passed: bool
    returncode: int
    stdout: str
    stderr: str
    rule: str = ""
    expected: str = ""
    observed: str = ""


@dataclass
class HarnessRun:
    timestamp: str
    cwd: str
    passed: bool
    gates: list[GateResult] = field(default_factory=list)


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def gate_lint() -> GateResult:
    rc, out, err = _run(["uv", "run", "ruff", "check", "src", "tests"])
    return GateResult(
        gate="G1",
        name="lint",
        passed=rc == 0,
        returncode=rc,
        stdout=out,
        stderr=err,
        rule="ruff check",
        expected="0 violations",
        observed=out.strip().splitlines()[-1] if out.strip() else "",
    )


def gate_security() -> GateResult:
    # -ll = report Medium and High severity only
    rc, out, err = _run(["uv", "run", "bandit", "-r", "src", "-ll", "-q"])
    return GateResult(
        gate="G2",
        name="security",
        passed=rc == 0,
        returncode=rc,
        stdout=out,
        stderr=err,
        rule="bandit -r src -ll",
        expected="0 Medium/High findings",
        observed="OK" if rc == 0 else "findings present (see stdout)",
    )


def gate_tests() -> GateResult:
    rc, out, err = _run(["uv", "run", "pytest", "-q"])
    return GateResult(
        gate="G3",
        name="tests",
        passed=rc == 0,
        returncode=rc,
        stdout=out,
        stderr=err,
        rule="pytest -q",
        expected="100% pass",
        observed=(out.strip().splitlines() or [""])[-1],
    )


def gate_coverage() -> GateResult:
    rc, out, err = _run(
        [
            "uv", "run", "pytest",
            "--cov=src/smart_todo",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
            "-q",
        ]
    )
    return GateResult(
        gate="G4",
        name="coverage",
        passed=rc == 0,
        returncode=rc,
        stdout=out,
        stderr=err,
        rule="coverage ≥ 85%",
        expected="line coverage ≥ 85%",
        observed=(out.strip().splitlines() or [""])[-1],
    )


def main(argv: list[str] | None = None) -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    gates = [gate_lint(), gate_security(), gate_tests(), gate_coverage()]
    run = HarnessRun(
        timestamp=ts,
        cwd=str(ROOT),
        passed=all(g.passed for g in gates),
        gates=gates,
    )
    out_path = EVIDENCE / f"harness-run-{ts}.json"
    out_path.write_text(
        json.dumps(
            {
                "timestamp": run.timestamp,
                "cwd": run.cwd,
                "passed": run.passed,
                "gates": [asdict(g) for g in run.gates],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Human-readable summary on terminal
    print("=" * 70)
    print(f"Smart Todo CLI — harness @ {ts}")
    print("=" * 70)
    for g in gates:
        mark = "✓ PASS" if g.passed else "✗ FAIL"
        print(f"  {mark}  {g.gate}  {g.name:<10} rc={g.returncode}  {g.observed}")
    print("-" * 70)
    print(f"Overall: {'PASS' if run.passed else 'FAIL'}")
    print(f"Evidence: {out_path}")
    print("=" * 70)

    if not run.passed:
        for g in gates:
            if not g.passed:
                print(f"\n--- {g.gate} {g.name} stdout ---")
                print(g.stdout[-2000:])
                print(f"--- {g.gate} {g.name} stderr ---")
                print(g.stderr[-2000:])

    return 0 if run.passed else 1


if __name__ == "__main__":
    sys.exit(main())
