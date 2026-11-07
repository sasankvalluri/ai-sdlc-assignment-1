# Part-1A — Smart Todo CLI

A small single-user command-line task manager. Stores tasks in a JSON
file. Same input, same command — same output. I built it through the
GitHub Spec Kit SDD flow and put a four-gate harness around it.

## Quick start

```bash
cd Part-1A
uv sync
uv run smart-todo --help

# Add, list, transition
uv run smart-todo add --title "Buy milk" --priority high --tag home
uv run smart-todo list --json
uv run smart-todo done <id>
```

By default the task file is `./tasks.json` in whatever directory you
run it from. Override with `--store <path>` or `SMART_TODO_STORE`.

## Run the harness

```bash
./.harness/run.sh
```

Four gates in order: `ruff` for lint, `bandit` for SAST (medium/high
only), `pytest` for the 30 spec-derived tests, and `pytest-cov` with
an 85 % threshold. Writes a JSON record to `evidence/` and exits `0`
only when every gate's green.

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

1. `spec-kit/memory/constitution.md` — the rules I agreed not to break.
2. `spec-kit/specs/001-smart-todo-cli/spec.md` — functional requirements
   and the `A-###` acceptance clauses. Every test name maps back to
   one of these.
3. `evidence/harness-log.md` — what the harness caught, how I fixed it,
   and the final ACCEPT.
