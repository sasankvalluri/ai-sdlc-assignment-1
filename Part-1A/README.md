# Part-1A — Smart Todo CLI (Deterministic)

A single-user CLI task manager with deterministic behaviour, developed
via the GitHub Spec Kit SDD flow and gated by a four-check harness.

## Quick start

```bash
cd Part-1A
uv sync                       # install into a hermetic .venv
uv run smart-todo --help

# Add, list, transition:
uv run smart-todo add --title "Buy milk" --priority high --tag home
uv run smart-todo list --json
uv run smart-todo done <id>
```

The default store path is `./tasks.json` in the invocation directory.
Override via `--store <path>` or the `SMART_TODO_STORE` env var.

## Run the harness

```bash
./.harness/run.sh
```

The runner executes four gates (ruff, bandit, pytest, pytest-cov),
emits a JSON record under `evidence/harness-run-<ts>.json`, prints a
terminal summary and exits `0` iff every gate passes.

## Layout

```
Part-1A/
├── pyproject.toml                  # uv project, pytest/ruff/coverage config
├── spec-kit/
│   ├── memory/constitution.md
│   └── specs/001-smart-todo-cli/
│       ├── spec.md
│       ├── clarify.md
│       ├── plan.md
│       └── tasks.md
├── src/smart_todo/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                      # argparse dispatch + exit-code map
│   ├── commands.py                 # pure command functions
│   ├── errors.py                   # typed CLI errors
│   ├── models.py                   # Task dataclass, enums, validators
│   └── store.py                    # atomic JSON persistence
├── tests/                          # specification-derived; one module per REQ
├── .harness/
│   ├── run.py                      # four-gate runner
│   ├── run.sh                      # wrapper
│   └── README.md
└── evidence/
    ├── initial-generation/         # first AI output, before any repair
    ├── final-generation/           # accepted source
    ├── harness-run-*.json          # machine-readable per-run verdict
    └── harness-log.md              # narrative audit trail + ACCEPT decision
```

## Where to start reading

1. `spec-kit/memory/constitution.md` — non-negotiable rules.
2. `spec-kit/specs/001-smart-todo-cli/spec.md` — functional requirements
   and the `A-###` acceptance clauses every test maps to.
3. `evidence/harness-log.md` — what the harness caught, how it was
   repaired, and the final human ACCEPT.
