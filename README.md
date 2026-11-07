# Assignment 1 — Spec-Driven Development & Harness Engineering

**Course:** AI-Augmented Software Development Life Cycle (SE ZG534)
**Semester:** S1 2026
**Student:** Sasank Valluri
**Submission deadline:** 2026-11-15

This repository is the submission for Assignment 1. It contains two
small applications developed using the [GitHub Spec Kit](https://github.com/github/spec-kit)
Spec-Driven Development (SDD) workflow, each with an engineered
validation harness.

| Part | Focus | Application | Harness | Status |
|------|-------|-------------|---------|--------|
| **1A** | Deterministic SDD + harness | [Smart Todo CLI](Part-1A/) | ruff + bandit + pytest + ≥ 85 % coverage | ACCEPT (final run `20261107T173259Z`) |
| **1B** | Non-deterministic AI SDD + eval harness | [Reminder Agent](Part-1B/) | L1 structural + L2 invariants + L3 semantic | CONDITIONAL ACCEPT — needs one real-backend run |
| **2** | Reflection | [Reflection-Report.md](Reflection-Report.md) | — | DRAFT, awaiting rewrite in own voice |

## Repository layout

```
Assignment-1/
├── README.md                  # this file
├── Reflection-Report.md       # Part 2 responses (draft, to be re-authored and exported to .docx)
├── Part-1A/                   # Deterministic — Smart Todo CLI
│   ├── spec-kit/              # constitution, spec, clarify, plan, tasks
│   ├── src/                   # implementation
│   ├── tests/                 # 30 specification-derived tests
│   ├── .harness/              # lint + SAST + test + coverage runner
│   └── evidence/              # initial/final snapshots, 4 harness runs, log, ACCEPT
└── Part-1B/                   # Non-deterministic — Reminder Agent
    ├── spec-kit/              # SDD artifacts
    ├── src/                   # pydantic schema, validators, backends, agent, CLI
    ├── prompts/               # versioned system prompt (SHA-256 recorded per run)
    ├── evals/                 # 17-case dataset + L3 rubric
    ├── .harness/              # three-layer evaluator
    └── evidence/              # initial/final snapshots, 6 eval records, log, CONDITIONAL ACCEPT
```

## Running the harnesses

```bash
# Part 1A — deterministic
cd Part-1A && uv sync && ./.harness/run.sh

# Part 1B — non-deterministic (mock = offline, real = GitHub Models)
cd Part-1B && uv sync && ./.harness/run.sh --backend mock
# For real backend:
gh auth refresh -h github.com -s models:read
export GITHUB_TOKEN=$(gh auth token)
./.harness/run.sh --backend real
```

## Deliverables

1. **Code** — this public GitHub repository.
2. **Demo video** — link in `Reflection-Report.md` (paste a Drive/OneDrive
   URL readable by any BITS email id).
3. **Reflection Report** — `Reflection-Report.md`, rewritten in the
   student's voice and exported to `.docx` using the LMS template.

## AI policy compliance

- AI assistance was used for Spec-Kit artifact drafting, implementation
  code, prompts, dataset structure, and harness scaffolding — all
  within §11.4 "Acceptable AI Uses" (Spec-driven development and
  harness development).
- The reflection answers in `Reflection-Report.md` are supplied as
  **drafts** grounded in this repository's actual evidence files; they
  must be rewritten in the student's own words before submission.
- No secrets, tokens or credentials appear anywhere in the
  repository.
