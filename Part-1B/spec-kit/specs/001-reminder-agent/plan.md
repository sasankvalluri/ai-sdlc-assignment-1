# Technical Plan — Reminder Agent (001)

## 1. Technology choices

| Concern | Decision | Rationale |
|---------|----------|-----------|
| Language | Python 3.11 | Pydantic v2, StrEnum, typing niceties. |
| Package manager | `uv` | Deterministic lock. |
| LLM backend | GitHub Models (OpenAI-compatible) | Free on the student's existing GitHub account; needs only a PAT with `models:read`. |
| LLM client | `openai>=1.0` | Standard OpenAI SDK with `base_url` override. |
| Schema | `pydantic` + `jsonschema` | Pydantic models for runtime validation; jsonschema export for L1. |
| Time | `python-dateutil` + `datetime` | ISO-8601 parsing and UTC comparison. |
| Tests | `pytest` | Required by harness. |
| Lint / SAST | `ruff`, `bandit` | Same gates as Part-1A for hygiene. |

## 2. Layout

```
Part-1B/
├── pyproject.toml
├── src/reminder_agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                 # 'reminder parse <text>' CLI
│   ├── agent.py               # orchestrator: build prompt → call backend → validate
│   ├── backends.py            # RealBackend (GitHub Models) + MockBackend
│   ├── schema.py              # pydantic models + JSON Schema export
│   ├── validators.py          # L1/L2 pure functions (reused by harness)
│   └── prompt.py              # loads prompts/system.md, formats with now/timezone
├── prompts/
│   └── system.md              # versioned system prompt
├── evals/
│   ├── dataset.json           # 15+ cases
│   └── rubric.md              # L3 scoring rubric
├── .harness/
│   ├── run.py                 # three-layer eval runner
│   ├── layer1.py              # structural validators (reused from src)
│   ├── layer2.py              # invariant/property checks
│   ├── layer3.py              # semantic rubric + LLM-as-judge
│   └── README.md
└── evidence/
    ├── initial-generation/
    ├── final-generation/
    ├── eval-results-*.json
    └── harness-log.md
```

## 3. Design decisions

1. **Pydantic as the single source of truth.** `ReminderResponse` is a
   pydantic model; `schema.json` is derived from it. L1 uses the derived
   schema, not a hand-maintained copy.
2. **Backends behind an interface.** `Backend.generate(text, now, tz)
   -> str` returns a JSON string. Both real and mock implement it. The
   agent orchestrator does not know which it is talking to.
3. **Prompt lives on disk.** `prompts/system.md` is loaded and
   SHA-256-hashed per run; the hash goes into the eval record so a
   prompt change invalidates past results.
4. **Harness is independent of app code.** `.harness/` imports
   `reminder_agent.validators` but defines its own `main()` so the
   evaluation can run even if the CLI breaks.
5. **L3 fallback.** If no LLM judge is available (no token), L3 degrades
   to a rule-based scorer (substring presence of key nouns, time-window
   match, etc.). Falling back is recorded in the eval record as
   `l3_mode: "rule-based"`.

## 4. Mapping to constitution

| Article | Mechanism |
|---------|-----------|
| I Contract-first | `ReminderResponse` pydantic model; schema.json derived; validators run on every call. |
| II Invariant-first | L2 checks in `src/reminder_agent/validators.py` reused by both runtime and harness. |
| III 3-layer harness | `.harness/run.py` orchestrates L1 → L2 → L3 in order. |
| IV Safety | Guardrail checks in L2 (past times, injection, missing-info), tests in dataset. |
| V Non-determinism & repro | Model id, temperature, prompt hash recorded in every eval result. |
| VI Self-healing | Failures funnel back into prompt + code; dataset frozen. |
| VII Evidence | Timestamped JSON records + harness-log.md. |

## 5. Risks

- Model regressions when GitHub changes default model weights.
  Mitigation: pin `openai/gpt-4o-mini` in config.
- Rate limiting on free tier. Mitigation: eval dataset is small (15+),
  and we cache results per (text, now, tz, prompt_hash) in
  `.harness/cache/`.
- LLM judge drift. Mitigation: rubric is explicit; the judge's score
  per case is logged so post-hoc review is possible.
