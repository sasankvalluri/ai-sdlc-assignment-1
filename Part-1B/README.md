# Part-1B — Natural-Language Reminder Agent (Non-Deterministic AI)

Parses unstructured reminder requests ("remind me to call mom tomorrow
at 5pm", "move my 2pm dentist to 3pm", "snooze that 15 min") into a
typed JSON contract. Backed by GitHub Models (OpenAI-compatible) in
production and an offline rule-based parser for CI. Evaluated by a
three-layer harness (structural + invariants + semantic rubric).

## Quick start

```bash
cd Part-1B
uv sync
```

### Parse a single request

```bash
# Offline (rule-based mock backend, no token needed)
uv run reminder parse "Remind me to call mom tomorrow at 5pm" \
    --now 2026-11-07T10:00:00Z --tz Asia/Kolkata --backend mock

# Real (GitHub Models — requires token with models:read scope)
gh auth refresh -h github.com -s models:read
export GITHUB_TOKEN=$(gh auth token)
uv run reminder parse "Remind me to call mom tomorrow at 5pm" \
    --now 2026-11-07T10:00:00Z --tz Asia/Kolkata --backend real
```

### Run the 3-layer evaluation harness

```bash
./.harness/run.sh                 # auto: real if token present, else mock
./.harness/run.sh --backend mock  # offline
./.harness/run.sh --backend real  # non-deterministic acceptance
```

Each run writes `evidence/eval-results-<ts>.json` with per-case L1/L2/L3
outcomes plus the model id, temperature and prompt hash.

## Thresholds

| Metric | Threshold |
|--------|-----------|
| L1 structural pass rate | 100 % |
| L2 invariants pass rate | 100 % |
| L3 semantic mean score | ≥ 0.70 |
| aggregate (mean of the three) | ≥ 0.85 |

## Layout

```
Part-1B/
├── pyproject.toml
├── spec-kit/
│   ├── memory/constitution.md
│   └── specs/001-reminder-agent/{spec,clarify,plan,tasks}.md
├── src/reminder_agent/
│   ├── schema.py        # pydantic contract
│   ├── validators.py    # L1/L2 pure functions
│   ├── prompt.py        # loader + SHA-256 hash
│   ├── backends.py      # Real (GitHub Models) + Mock (rule-based)
│   ├── agent.py         # orchestrator
│   └── cli.py           # `reminder parse ...`
├── prompts/system.md    # versioned system prompt
├── evals/
│   ├── dataset.json     # 17 cases (6 categories)
│   └── rubric.md
├── .harness/
│   ├── run.py           # three-layer runner
│   ├── layer1/2/3.py
│   └── README.md
└── evidence/
    ├── initial-generation/   # pre-repair snapshot
    ├── final-generation/     # accepted snapshot
    ├── eval-results-*.json   # one per run
    └── harness-log.md
```

## Reading order

1. `spec-kit/memory/constitution.md` — AI-specific principles.
2. `spec-kit/specs/001-reminder-agent/spec.md` — schema, invariants,
   safety, acceptance threshold.
3. `evals/dataset.json` and `evals/rubric.md` — what the harness runs
   against.
4. `evidence/harness-log.md` — what the harness caught, how it was
   repaired, and the final (conditional) ACCEPT.

## Non-determinism

- Model: `openai/gpt-4o-mini` (via GitHub Models).
- Temperature: `0.3`.
- Output is parsed, validated and scored — not compared as strings.
- Each run's `prompt_hash` is recorded; changing the prompt invalidates
  past evidence.
