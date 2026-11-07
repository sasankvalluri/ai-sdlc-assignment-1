# Assignment 1 — Spec-Driven Development & Harness Engineering

**Course:** AI-Augmented Software Development Life Cycle (SE ZG534)
**Student:** Sasank Valluri
**Semester:** S1 2026
**Submission:** 2026-11-15

This repository is the submission for Assignment 1. It contains two small applications developed using the [GitHub Spec Kit](https://github.com/github/spec-kit) Spec-Driven Development (SDD) workflow, each with an engineered validation harness.

| Part | Focus | Application | Status |
|------|-------|-------------|--------|
| **1A** | Deterministic SDD + harness | Smart Todo CLI | 🚧 in progress |
| **1B** | Non-deterministic AI SDD + eval harness | Natural-Language Reminder Agent | 🚧 in progress |
| **2**  | Reflection questions | See `Reflection-Report.md` | 🚧 in progress |

## Repository layout

```
Assignment-1/
├── README.md                  # this file
├── Reflection-Report.md       # Part 2 responses (also submitted as .docx to LMS)
├── Part-1A/                   # Deterministic — Smart Todo CLI
│   ├── spec-kit/              # constitution, spec, clarify, plan, tasks
│   ├── src/                   # implementation
│   ├── tests/                 # specification-derived unit & contract tests
│   ├── .harness/              # lint, SAST, test runner + harness driver
│   └── evidence/              # initial generation, final, logs, results
└── Part-1B/                   # Non-deterministic — Reminder Agent
    ├── spec-kit/              # SDD artifacts
    ├── src/                   # implementation
    ├── prompts/               # system prompt(s)
    ├── evals/                 # dataset.json — ≥15 cases
    ├── .harness/              # structural / invariant / semantic evaluators
    └── evidence/              # eval-results.json, harness-log.md
```

## Running the harness

Each Part has its own README with run instructions. The short form:

```bash
# Part 1A
cd Part-1A && ./.harness/run.sh

# Part 1B
cd Part-1B && ./.harness/run.sh
```

## Deliverables

1. **Code** — this public GitHub repository.
2. **Demo video** — link in `Reflection-Report.md`.
3. **Reflection Report** — `Reflection-Report.md` (and the exported `.docx`) uploaded to LMS.
