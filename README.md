# Assignment 1 — Spec-Driven Development & Harness Engineering

Course: AI-Augmented Software Development Life Cycle (SE ZG534), S1 2026
Author: Sasank Valluri
Due: 2026-11-15

This repo is my submission for Assignment 1. It has two small apps I
built using the GitHub Spec Kit SDD workflow and the local validation
harness I wrote for each.

## What's in each part

**Part 1A — Smart Todo CLI.** A deterministic command-line task
manager in Python. Stores tasks in a JSON file, supports CRUD, tag
and status filters, priority ordering, and a strict status state
machine. The harness has four gates: `ruff` for lint, `bandit` for
SAST, `pytest` for the 30 spec-derived tests, and a coverage gate at
85%. See `Part-1A/evidence/harness-log.md` for the history of runs,
three honest repair cycles, and the final ACCEPT.

**Part 1B — Natural-Language Reminder Agent.** A parser that turns
sentences like *"remind me to call mom tomorrow at 5pm"* into a typed
JSON contract. Real backend is Groq (free tier, OpenAI-compatible);
offline backend is a rule-based mock parser used for CI. The eval
harness has three layers — JSON-schema validation, intent / safety
invariants, and a rule-based semantic rubric — run over a 17-case
dataset covering normal, boundary, ambiguous, missing, malformed and
adversarial inputs. Final real-backend run (Groq `openai/gpt-oss-20b`,
temperature 0.3) passes all 17 cases with aggregate 0.9941 against a
0.85 threshold. Four repair cycles are documented in
`Part-1B/evidence/harness-log.md`.

**Part 2 — Reflection.** Five short answers grounded in the artifacts
in this repo. See `Reflection-Report.md`.

## Running the harnesses

```bash
# Part 1A
cd Part-1A && uv sync && ./.harness/run.sh

# Part 1B (offline, rule-based mock parser)
cd Part-1B && uv sync && ./.harness/run.sh --backend mock

# Part 1B (real, Groq free tier — https://console.groq.com/keys)
GROQ_API_KEY="..." ./.harness/run.sh --backend groq
# If Groq retires the default model, pick one from the list and set:
# GROQ_MODEL="<id>" GROQ_API_KEY="..." ./.harness/run.sh --backend groq
```

## Repository layout

```
Assignment-1/
├── README.md                  ← this file
├── Reflection-Report.md       ← Part 2 (also exported to .docx for LMS)
├── Part-1A/
│   ├── spec-kit/              constitution, spec, clarify, plan, tasks
│   ├── src/                   smart_todo package
│   ├── tests/                 30 specification-derived tests
│   ├── .harness/              lint + SAST + test + coverage runner
│   └── evidence/              harness runs, log, snapshots
└── Part-1B/
    ├── spec-kit/              SDD artifacts for the agent
    ├── src/                   pydantic schema, validators, backends, agent, CLI
    ├── prompts/system.md      versioned system prompt (hash recorded per run)
    ├── evals/                 dataset (17 cases) + L3 rubric
    ├── .harness/              three-layer evaluator
    └── evidence/              eval records, log, snapshots
```

## Deliverables

- Code — this public repo at
  https://github.com/sasankvalluri/ai-sdlc-assignment-1
- Demo video — link lives in `Reflection-Report.md` once I've uploaded
  it to Drive / OneDrive.
- Reflection report — `Reflection-Report.md`, exported to `.docx` for
  LMS upload.

## AI assistance

I used an AI coding assistant for drafting the Spec Kit artifacts,
some boilerplate in the implementation, the first draft of the
prompts, and the harness scaffolding — all within the "Acceptable AI
Uses" clause (§11.4 of the brief: SDD and harness development). The
reflection answers are mine; the harness logs are my working notes.
No secrets or API tokens are committed anywhere in this repo.
