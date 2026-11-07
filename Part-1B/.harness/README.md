# Part-1B Harness

Three-layer evaluation (constitution Article III):

| Layer | Check | Threshold |
|-------|-------|-----------|
| L1 | Structural / schema | 100 % per-case pass |
| L2 | Property + dataset invariants | 100 % per-case pass |
| L3 | Semantic rubric (rule-based) | mean score ≥ 0.70, per-case ≥ 0.70 |
| Aggregate | Mean of {L1 rate, L2 rate, L3 mean} | ≥ 0.85 |

## Run

```bash
./.harness/run.sh                # auto-selects backend
./.harness/run.sh --backend real # force GitHub Models (needs token)
./.harness/run.sh --backend mock # force offline rule-based parser
```

The runner picks `real` when `GITHUB_MODELS_TOKEN` or `GITHUB_TOKEN` is
set, otherwise `mock`. The `backend` field in the evidence record
(`evidence/eval-results-<ts>.json`) records which one was used — only
`backend: "real"` results count toward the acceptance claim.

## Getting a token for the real backend

```bash
gh auth refresh -s models:read   # add scope to your existing gh auth
export GITHUB_TOKEN=$(gh auth token)
./.harness/run.sh --backend real
```
