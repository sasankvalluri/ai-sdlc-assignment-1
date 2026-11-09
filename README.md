# Assignment 1 — Spec-Driven Development & Harness Engineering

Course: AI-Augmented Software Development Life Cycle (SE ZG534), S1 2026
Author: Sasank Valluri

This repo is my submission for Assignment 1. It has two small apps I
built using the GitHub Spec Kit SDD workflow and the local validation
harness I wrote for each.

## What's in each part

**Part 1A — Smart Todo CLI.** A small deterministic command-line task
manager in Python. Tasks live in a JSON file. CRUD, tag and status
filters, priority ordering, and a strict status lifecycle .
The harness has four gates — lint (`ruff`), SAST (`bandit`), 30
spec-derived tests (`pytest`), and coverage at 85 %. There were three
honest repair cycles getting it to green; they're all in
`Part-1A/evidence/harness-log.md`.

**Part 1B — Natural-Language Reminder Agent.** Turns a sentence like
*"remind me to call mom tomorrow at 5pm"* into a typed JSON object. The
real backend runs on Groq's free tier (OpenAI-compatible API); there's
a rule-based mock parser for offline work. The eval harness is three
layers — JSON-schema check, intent and safety invariants, rule-based
semantic rubric — across a 17-case dataset covering normal, boundary,
ambiguous, missing, malformed and adversarial inputs. The final run on
Groq `openai/gpt-oss-20b` at temperature 0.3 passes all 17 cases,
aggregate 0.9941. .

**Part 2 — Reflection.** Five short answers in `Reflection-Report.md`,
each tied to actual evidence in the repo (run ids, file paths, a
prompt-hash change). 

## Running the harnesses

```bash
# Part 1A
cd Part-1A && uv sync && ./.harness/run.sh

# Part 1B (offline, rule-based mock parser)
cd Part-1B && uv sync && ./.harness/run.sh --backend mock

# Part 1B (real, Groq free tier — https://console.groq.com/keys)
GROQ_API_KEY="..." ./.harness/run.sh --backend groq

```

## Repository layout

```
Assignment-1/
├── README.md                  ← this file
├── Reflection-Report.md        
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
- Demo video — https://drive.google.com/file/d/1h0cfWJslcR0oJHJiM8l8OEkwym3vT76v/view
- Reflection report — `Reflection-Report.md`,

## AI assistance

I used an AI coding assistant for drafting the Spec Kit artifacts,
some boilerplate in the implementation, the first draft of the
prompts, and the harness scaffolding — all within the "Acceptable AI
Uses" clause. The
reflection answers are mine; the harness logs are my working notes.
No secrets or API tokens are committed anywhere in this repo.
