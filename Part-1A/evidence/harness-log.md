# Harness Log — Smart Todo CLI (Part 1A)

This is my working log while building the Part-1A harness and getting
the implementation through all four gates. The machine-readable records
are in the `harness-run-*.json` files in this directory. This file is
the story around them.

**What the harness checks**

- G1 — `ruff check src tests` (lint)
- G2 — `bandit -r src -ll` (SAST, medium/high only)
- G3 — `pytest -q` (30 spec-derived tests)
- G4 — `pytest --cov-fail-under=85` (line coverage ≥ 85 %)

All four have to be green for ACCEPT. The runner writes a JSON record
to this folder and exits 0 only if everything passed.

---

## Run 1 — `harness-run-20261107T173051Z.json` — FAIL

G1 failed, G3 and G4 also failed. Full output in the JSON record.

**G1 (lint):** 13 ruff violations, mostly unused imports in
`tests/test_persistence.py` (I'd pulled in `os`, `pathlib.Path`,
`unittest.mock`, `pytest`, `StoreError` while poking at the test and
left them in) plus one import-order issue.

**G3 / G4:** Both died at collection with
`_pytest.pathlib.ImportPathMismatchError: tests.conftest`. That one took
me a minute to see — pytest was discovering two `tests/conftest.py`
files, the real one and the copy I'd snapshotted into
`evidence/initial-generation/tests/`. Same module name, different
paths. Collection blew up before any test could run.

### Repair

Two edits, both legitimate — no test deleted, no rule relaxed:

1. `pyproject.toml` — added `[tool.pytest.ini_options] testpaths =
   ["tests"]` and `norecursedirs = [".venv", "evidence", ".harness"]`
   so pytest doesn't walk into snapshot folders. Also added
   `[tool.ruff] exclude = ["evidence", ".venv"]` for the same reason,
   and widened `select` from the ruff default to
   `["E", "F", "I", "B", "UP", "SIM"]` — if the gate is going to be
   called "lint" I'd rather it actually enforce something meaningful.
2. Cleaned up the dead imports in `test_persistence.py`.

---

## Run 2 — `harness-run-20261107T173127Z.json` — FAIL

G1 still red, and now G3/G4 red too — but for a completely different
reason than Run 1.

**G1:** The wider ruff rules I'd just added surfaced genuine issues:
`UP035` (use `collections.abc.Callable` instead of `typing.Callable`),
`UP042` (both `Priority(str, Enum)` and `Status(str, Enum)` should be
`StrEnum` on Python 3.11+), `SIM105` (there's a `try/except OSError:
pass` in `store.py` that ruff wants replaced with
`contextlib.suppress`), plus a few F401s and the `__main__.py` import
order. Fair enough.

**G3:** `3 failed, 27 passed`. The three failures were in
`test_add`, `test_update` and `test_persistence` — all three expected
the deterministic id `0000…0001` and the frozen timestamp
`2026-11-07T10:00:00Z`, but got real UUIDs and real wall-clock values.

I spent a minute staring at this because the conftest *does*
monkeypatch `models.new_id` and `models.now_utc`. The actual cause was
embarrassing. My `new_task` and the three command functions in
`commands.py` had:

```python
def new_task(..., *, id_factory=new_id, clock=now_utc):
```

Python binds default argument values at **function-definition time**,
not call time. So `id_factory` and `clock` were holding frozen
references to the original functions, not module attribute lookups.
The conftest's `monkeypatch.setattr(models, "now_utc", ...)` had no
effect on them.

### Repair

Switched the defaults to `None` and resolved at call time:

```python
def new_task(..., *, id_factory=None, clock=None):
    _id_factory = id_factory if id_factory is not None else new_id
    _clock = clock if clock is not None else now_utc
```

Same change in `commands.add`, `commands.update`, `commands._transition`.
Spec unchanged. No test altered.

---

## Run 3 — `harness-run-20261107T173219Z.json` — FAIL

Good progress: **G3 and G4 are now green** (`30 passed`, 89.15 %
coverage). G1 still red with three ruff findings left — the `StrEnum`
rewrites and the `contextlib.suppress` one, which are
`--unsafe-fixes` in ruff. I looked at each one manually before applying:

- `StrEnum` (Python 3.11+) is a drop-in replacement for `str + Enum`,
  same serialisation and same equality semantics.
- `contextlib.suppress(OSError)` is a one-line equivalent for the
  inner `try/except OSError: pass` around `os.unlink(tmp_path)`.

Both preserve behaviour.

### Repair

- `models.py` — `class Priority(str, Enum)` → `class Priority(StrEnum)`,
  same for `Status`. Import becomes `from enum import StrEnum`.
- `store.py` — `import contextlib`, wrap the cleanup with
  `with contextlib.suppress(OSError):`.

---

## Run 4 — `harness-run-20261107T173259Z.json` — PASS

Everything green.

| Gate | Result |
|------|--------|
| G1 lint | `All checks passed!` |
| G2 SAST | 0 findings |
| G3 tests | `30 passed in 0.08s` |
| G4 coverage | 89.15 % (threshold 85 %) |

Final sources snapshotted to `evidence/final-generation/`.

---

## What the harness caught that I would have missed

The default-argument capture bug (Run 2) is the clearest example. I'd
convinced myself the test fixtures were right because the module
attribute `now_utc` *was* the thing being called — just via a frozen
reference. If I'd only re-read the code I'd have shipped that bug.
Executing the test with the monkeypatch was what made it visible.

The snapshot cross-contamination (Run 1) is a smaller example — I
copied the initial generation into `evidence/` thinking of it as
documentation, not code. Pytest treated it as code. The fix lives in
`pyproject.toml`, not the implementation.

The lint widening (Runs 2 and 3) was the last thing: the ruff default
select is lenient. Once I turned on `UP` and `SIM`, the `str+Enum`
dual inheritance and the `try/except/pass` both became real findings.
They're small but they're real.

---

## Known limitations

- **No file locking on the task store.** Two concurrent invocations
  can race. Documented in `clarify.md` (C-09). Out of scope for v1.
- **Coverage 89 %, not 100 %.** The uncovered lines are mostly
  error-path branches in `store.py` (second `OSError` in the cleanup)
  and the help-wall fallback in `cli.py`. Low-risk, visible in the
  `--cov-report=term-missing` output.
- **Help exit semantics rely on argparse** raising `SystemExit(0)`.
  Tests pin it via `pytest.raises(SystemExit)`.

---

## Decision

**ACCEPT** for Part 1A. — Sasank Valluri, 2026-11-07.

All four gates pass on the final tree (Run 4). Each of the three
failing runs before it has a documented repair that didn't touch the
spec, didn't delete a test and didn't lower any threshold. Residual
risks are disclosed above.

If I were taking this further — concurrency, more coverage of the
error-path branches, and a pre-commit hook that runs
`./.harness/run.sh` so nobody can land a change without re-running the
four gates.
