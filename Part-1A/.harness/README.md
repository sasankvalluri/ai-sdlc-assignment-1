# Part-1A Harness

Four deterministic gates (constitution Article III):

| Gate | Check | Tool | Pass |
|------|-------|------|------|
| G1 | Lint | `ruff check src tests` | 0 violations |
| G2 | SAST | `bandit -r src -ll` | 0 Medium/High findings |
| G3 | Tests | `pytest -q` | 100% of tests pass |
| G4 | Coverage | `pytest --cov --cov-fail-under=85` | line coverage ≥ 85% |

## Run

```bash
./.harness/run.sh
```

The runner writes `evidence/harness-run-<timestamp>.json` with the per-gate
outcome, stdout/stderr, and an overall pass/fail verdict. Exit 0 iff every
gate passes.

## Non-negotiables

- The runner never modifies source or tests.
- Harness output is a mechanical record. Humans decide ACCEPT/REJECT in
  `evidence/harness-log.md` **after** reading the JSON verdict.
