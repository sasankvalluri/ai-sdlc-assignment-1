# Part-1B — Natural-Language Reminder Agent

Takes a sentence like *"remind me to call mom tomorrow at 5pm"* or
*"move my 2pm dentist to 3pm"* and turns it into a typed JSON object
a downstream scheduler could consume. The real backend is Groq's free
tier (OpenAI-compatible API). There's also an offline rule-based mock
parser that runs without any API key so CI and offline development
work.

The evaluation harness has three layers: a JSON-schema check, a set of
intent/safety invariants, and a rule-based semantic rubric. It runs
over 17 cases covering normal input, boundaries, ambiguous requests,
missing info, malformed input and adversarial prompts (including
prompt injection).

## Quick start

```bash
cd Part-1B
uv sync
```

### Parse a single request

```bash
# Offline — rule-based parser, no API key needed
uv run reminder parse "Remind me to call mom tomorrow at 5pm" \
    --now 2026-11-07T10:00:00Z --tz Asia/Kolkata --backend mock

# Real — Groq free tier (sign up at https://console.groq.com/keys)
export GROQ_API_KEY=gsk_...
uv run reminder parse "Remind me to call mom tomorrow at 5pm" \
    --now 2026-11-07T10:00:00Z --tz Asia/Kolkata --backend groq
```

### Run the harness

```bash
./.harness/run.sh --backend groq   # real model, needs GROQ_API_KEY
./.harness/run.sh --backend mock   # offline, deterministic
./.harness/run.sh                  # auto: groq if key, else mock
```

Every run writes `evidence/eval-results-<ts>.json` with per-case
L1/L2/L3 results plus the backend, model id, temperature and prompt
hash so the configuration behind a result is always auditable.

If Groq retires the default model (`openai/gpt-oss-20b`), list what
your account actually has access to and override:

```bash
curl -s -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models \
  | python3 -c "import json,sys;[print(m['id']) for m in json.load(sys.stdin)['data']]"

GROQ_MODEL="<id-from-above>" ./.harness/run.sh --backend groq
```

## Thresholds

| Metric | Threshold |
|--------|-----------|
| L1 structural pass rate | 100 % |
| L2 invariants pass rate | 100 % |
| L3 semantic mean score | ≥ 0.70 |
| aggregate | ≥ 0.85 |

Final run on Groq (`openai/gpt-oss-20b`, temperature 0.3) hit 1.00 /
1.00 / 0.98 with aggregate 0.9941 — see
`evidence/eval-results-20261107T182627Z.json` and the narrative in
`evidence/harness-log.md`.

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
│   ├── backends.py      # Groq + GitHub Models + mock
│   ├── agent.py         # orchestrator
│   └── cli.py           # `reminder parse ...`
├── prompts/system.md    # versioned system prompt
├── evals/
│   ├── dataset.json     # 17 cases, 6 categories
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

## Where to start reading

1. `spec-kit/memory/constitution.md` — the rules the agent has to live
   by.
2. `spec-kit/specs/001-reminder-agent/spec.md` — schema, invariants,
   safety, acceptance threshold.
3. `evals/dataset.json` and `evals/rubric.md` — what the harness runs
   against.
4. `evidence/harness-log.md` — what the harness caught, how I fixed
   it, and the final ACCEPT.
