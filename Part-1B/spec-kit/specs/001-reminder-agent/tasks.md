# Task Breakdown — Reminder Agent (001)

| # | Task | Produces | Covers |
|---|------|----------|--------|
| T-01 | pyproject.toml with deps: openai, pydantic, jsonschema, python-dateutil; dev-deps: pytest, pytest-cov, ruff, bandit. | pyproject.toml | plan §1 |
| T-02 | schema.py — pydantic `ReminderResponse`, `WhenSpec`, enums, `to_json_schema()`. | src/reminder_agent/schema.py | REQ-001 |
| T-03 | validators.py — L1 `validate_schema(obj)`, L2 `check_invariants(obj, input_text, now)` returning typed `CheckResult` list. | src/reminder_agent/validators.py | REQ-001..003 |
| T-04 | prompt.py + prompts/system.md — load, format with `{now}` and `{timezone}`, hash for evidence. | prompts/system.md, src/.../prompt.py | REQ-005 |
| T-05 | backends.py — Backend ABC, RealBackend (openai SDK → GitHub Models), MockBackend (rule-based parser matching dataset cases). | src/reminder_agent/backends.py | REQ-007 |
| T-06 | agent.py — orchestrator: build messages, call backend, parse JSON, run validators, return typed result + raw. | src/reminder_agent/agent.py | all REQ |
| T-07 | cli.py — `reminder parse "<text>" [--now <iso>] [--tz <zone>] [--backend real|mock]`. | src/reminder_agent/cli.py | REQ-005 |
| T-08 | evals/dataset.json — ≥ 15 cases across the six categories (normal, boundary, ambiguous, missing, malformed, adversarial). | evals/dataset.json | spec §5 |
| T-09 | evals/rubric.md — explicit L3 criteria. | evals/rubric.md | SEM-* |
| T-10 | .harness/layer1.py — structural check on the raw JSON string. | layer1 | Article III |
| T-11 | .harness/layer2.py — invariant checks per case, driven by the dataset `expect` block. | layer2 | Article III |
| T-12 | .harness/layer3.py — rubric scorer + optional LLM-as-judge; records `l3_mode`. | layer3 | Article III |
| T-13 | .harness/run.py — orchestrate, write `eval-results-<ts>.json`, compute aggregate, exit non-zero if below threshold. | harness runner | Article III |
| T-14 | Snapshot initial generation, run harness, capture ≥ 1 real failure. | evidence | Article VI |
| T-15 | Repair cycle: adjust prompt / code / schema / guardrail based on feedback. | updated src + prompt | Article VI |
| T-16 | Snapshot final generation; re-run harness; record human ACCEPT/REJECT in harness-log.md. | evidence | Article VII |
