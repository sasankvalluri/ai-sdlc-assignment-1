# Technical Plan — Smart Todo CLI (001)

## 1. Technology choices

| Concern | Decision | Rationale |
|---------|----------|-----------|
| Language | Python 3.11 | Standard library covers CLI, JSON, dataclasses, uuid, datetime. No runtime deps needed. |
| Package manager | `uv` | Deterministic lock (`uv.lock`), fast installs, aligns with Spec Kit lab. |
| CLI framework | `argparse` (stdlib) | Zero runtime deps. Keeps the security surface minimal (NFR-001, Article IV). |
| Test runner | `pytest` | Required by Article III G3. |
| Lint | `ruff` | Required by Article III G1. |
| SAST | `bandit` | Required by Article III G2. |
| Coverage | `pytest-cov` | Required by Article III G4. |

## 2. Package & module layout

```
Part-1A/
├── pyproject.toml            # uv-managed
├── src/smart_todo/
│   ├── __init__.py
│   ├── __main__.py           # entry: python -m smart_todo
│   ├── cli.py                # argparse dispatch, exit codes, --help
│   ├── commands.py           # pure functions: add/list/show/update/done/start/cancel/delete
│   ├── store.py              # JSON file I/O, atomic write, schema validation
│   ├── models.py             # Task dataclass, status/priority enums, validators
│   └── errors.py             # typed CLI errors mapped to exit codes
└── tests/
    ├── conftest.py           # tmp-path store fixture, frozen time
    ├── test_add.py           # REQ-001
    ├── test_list.py          # REQ-002
    ├── test_show.py          # REQ-003
    ├── test_update.py        # REQ-004
    ├── test_transitions.py   # REQ-005
    ├── test_delete.py        # REQ-006
    ├── test_persistence.py   # REQ-007
    └── test_help.py          # NFR-003
```

## 3. Design decisions

1. **Pure core, thin CLI.** `commands.py` functions return typed results;
   `cli.py` prints them and maps results to exit codes. This makes each
   acceptance criterion testable without spawning a subprocess.
2. **Atomic persistence (A-007.2).** `store.save()` writes to
   `<path>.tmp.<pid>`, `os.replace` to final path.
3. **Deterministic time.** A module-level `now_utc()` function returns an
   ISO-8601 UTC string. Tests monkeypatch it so timestamps are stable.
4. **UUID generation.** `uuid.uuid4()` by default, overridable via a
   `new_id` callable so tests can inject deterministic ids.
5. **Validation errors as typed exceptions.** `ValidationError` (→ exit 2),
   `NotFoundError` (→ exit 1), `IllegalTransitionError` (→ exit 1),
   `StoreError` (→ exit 3). `cli.py` has one try/except mapping block.

## 4. Mapping to constitution

| Article | Mechanism |
|---------|-----------|
| I Deterministic | Pure functions in `commands.py`; injected `now_utc` and `new_id`. |
| II Spec-controlled | Every test module declares the `REQ-###` it covers in its docstring. |
| III Harness-enforced | `.harness/run.py` runs the four gates in order and emits JSON verdict. |
| IV Safety | argparse only; no `eval`, no `subprocess` outside tests; no network. |
| V Agent/self-healing | Initial generation snapshotted before harness-driven repair. |
| VI Observability | Harness writes `evidence/harness-run-*.json`; narrative in `harness-log.md`. |

## 5. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Timezone drift in tests | Freeze `now_utc` in a conftest fixture. |
| JSON indentation differences | Fix `json.dumps(..., indent=2, sort_keys=False)` and declare key order in spec §3. |
| Argparse implicit help exit 0 | NFR-003 asserts this. |
| Partial writes on crash | Atomic rename (plan §3.2). |
