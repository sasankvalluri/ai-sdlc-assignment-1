# Harness Log — Smart Todo CLI (Part 1A)

**Application:** Smart Todo CLI (Python 3.11, argparse)
**Spec revision:** `spec-kit/specs/001-smart-todo-cli/` (approved 2026-11-07)
**Harness:** `.harness/run.py` — four gates (G1 lint, G2 SAST, G3 tests, G4 coverage)
**Platform:** macOS Darwin 25.5.0, Python (venv) via `uv`, ruff 0.17.4, bandit 1.9.4, pytest 9.2.0
**Owner:** Sasank Valluri

This log is the narrative audit trail required by constitution Article VI.
All quoted output is verbatim from the harness-run JSON files in the same
directory.

---

## 1. Initial agent context

The coding agent (Claude Opus 4.7, acting as the AI engineer in this
assignment) was handed the following specification bundle **before** writing
any implementation code:

| Artifact | Path |
|---|---|
| Constitution | `spec-kit/memory/constitution.md` |
| Feature spec | `spec-kit/specs/001-smart-todo-cli/spec.md` |
| Clarifications | `spec-kit/specs/001-smart-todo-cli/clarify.md` |
| Technical plan | `spec-kit/specs/001-smart-todo-cli/plan.md` |
| Task breakdown | `spec-kit/specs/001-smart-todo-cli/tasks.md` |

The initial generation implements tasks T-01 through T-08 from
`tasks.md`. The pre-harness source is preserved verbatim under
`evidence/initial-generation/`.

---

## 2. Harness execution history

### Run 1 — `evidence/harness-run-20261107T173051Z.json` — **FAIL**

| Gate | Result | Observed |
|------|--------|---------|
| G1 lint | ✗ | `Found 13 errors` (12 F401 unused imports + 1 I001 import block ordering) |
| G2 SAST | ✓ | 0 Medium/High findings |
| G3 tests | ✗ | `_pytest.pathlib.ImportPathMismatchError: tests.conftest` — collection error |
| G4 coverage | ✗ | Same collection error as G3 |

**Failure evidence fed back to agent (verbatim):**

> `tests/test_persistence.py` has unused imports `os`, `pathlib.Path`,
> `unittest.mock`, `pytest`, `smart_todo.errors.StoreError`, and an
> unordered import block.
>
> pytest is also discovering the snapshot tests under
> `evidence/initial-generation/tests/` and clashing with the real
> `tests/conftest.py` (two files resolving to the same module name
> `tests.conftest`).

**Root-cause analysis performed by agent:**
- Issue A is dead code the generation left behind — strict cleanup.
- Issue B is a configuration gap: the harness is supposed to run against
  live sources, not the preserved initial-generation snapshot.

**Repair applied — no spec weakening:**
1. `pyproject.toml`: added `[tool.pytest.ini_options] testpaths = ["tests"]`
   and `norecursedirs = [".venv", "evidence", ".harness"]`.
2. `pyproject.toml`: added `[tool.ruff] exclude = ["evidence", ".venv"]`
   and widened `select` to `["E", "F", "I", "B", "UP", "SIM"]` so the gate
   genuinely enforces the constitution's "language-appropriate static
   check" rather than the ruff default minimum.
3. `tests/test_persistence.py`: removed unused imports; sorted import
   block.

No test was deleted, no rule was lowered, no snapshot was moved.

---

### Run 2 — `evidence/harness-run-20261107T173127Z.json` — **FAIL**

| Gate | Result | Observed |
|------|--------|---------|
| G1 lint | ✗ | `Found 11 errors` — new rules from the widened select surfaced genuine code issues (UP035 `typing.Callable`, UP042 `str,Enum` dual inheritance, SIM105 `try/except/pass`, F401 unused `Priority`, `field`, `Path`, I001 `__main__` import order) |
| G2 SAST | ✓ | 0 Medium/High findings |
| G3 tests | ✗ | `3 failed, 27 passed` — `test_a_001_1_default_fields`, `test_a_007_1_store_auto_created`, `test_a_004_3_updated_at_refreshed`: expected deterministic id `0000…0001` and timestamp `2026-11-07T10:00:00Z`, observed real `uuid4` and wall-clock values |
| G4 coverage | ✗ | Same failures as G3 |

**Failure evidence fed back to agent (verbatim excerpt):**

> ```
> assert data["created_at"] == "2026-11-07T10:00:00Z"
> AssertionError: assert '2026-11-07T17:31:28Z' == '2026-11-07T10:00:00Z'
> ```
>
> The conftest monkeypatches `smart_todo.models.now_utc` and
> `smart_todo.models.new_id`, but `models.new_task` and
> `commands.add`/`update`/`_transition` capture those callables in
> **default arguments** (`id_factory=new_id, clock=now_utc`). Python
> binds default-argument values at function-definition time, so the
> monkeypatched module attribute is never consulted.

**Root cause:** A classic Python default-argument capture trap. This
affected determinism (constitution Article I §1) in the implementation,
not in the spec. The spec is unchanged.

**Repair applied — resolve `new_id` and `now_utc` at call-time:**

- `src/smart_todo/models.py::new_task`: switched defaults to `None` and
  resolved via the module-level lookup inside the function body.
- `src/smart_todo/commands.py::add`, `update`, `_transition`: same pattern.
- A code comment references harness-run `20261107T173128Z G3` to preserve
  the paper trail.

---

### Run 3 — `evidence/harness-run-20261107T173219Z.json` — **FAIL**

| Gate | Result | Observed |
|------|--------|---------|
| G1 lint | ✗ | 3 remaining — UP042 `Priority(str, Enum)`, UP042 `Status(str, Enum)`, SIM105 `try/except/pass` in `store.py` |
| G2 SAST | ✓ | 0 findings |
| G3 tests | ✓ | **30 passed in 0.08s** (default-arg repair succeeded) |
| G4 coverage | ✓ | 30 passed, **89.15% coverage** (≥ 85% threshold) |

**Failure evidence fed back to agent (verbatim):**

> ```
> UP042 Class Priority inherits from both `str` and `enum.Enum`
>   help: Inherit from `enum.StrEnum`
> SIM105 Use `contextlib.suppress(OSError)` instead of `try-except-pass`
> ```

The three findings are ruff's `--unsafe-fixes` candidates (semantic
rewrites, not formatting). The agent inspected each and confirmed the
rewrite preserves behaviour:

- `StrEnum` (added in Python 3.11) is the sanctioned replacement for
  `str + Enum`: serialisation and value comparisons are identical.
- `contextlib.suppress(OSError)` is a one-line equivalent to the inner
  `try/except OSError: pass` cleanup around `os.unlink(tmp_path)`.

**Repair applied — no spec weakening:**

- `models.py`: `class Priority(str, Enum)` → `class Priority(StrEnum)`.
  Same for `Status`. Import updated to `from enum import StrEnum`.
- `store.py`: inner cleanup wrapped with `contextlib.suppress(OSError)`.
  `import contextlib` added.

---

### Run 4 — `evidence/harness-run-20261107T173259Z.json` — **PASS**

| Gate | Result | Observed |
|------|--------|---------|
| G1 lint | ✓ | `All checks passed!` |
| G2 SAST | ✓ | 0 Medium/High findings |
| G3 tests | ✓ | **30 passed in 0.08s** |
| G4 coverage | ✓ | 30 passed, **89.15% coverage** |

Final source preserved under `evidence/final-generation/`.

---

## 3. What the harness caught that an agent self-review would have missed

1. **Default-argument capture bug (Run 2).** The agent read its own code
   and judged the determinism contract satisfied — the module-level
   `now_utc` function *was* being called, just via a stale reference.
   Only executing the tests with a monkeypatched module made the bug
   observable.
2. **Snapshot cross-contamination (Run 1).** Preserving
   `evidence/initial-generation/tests/` created a duplicate `tests`
   module. A self-review would have seen the snapshot's intent (keep the
   initial generation) and not noticed the pytest consequence until the
   runner failed.
3. **Latent style drift that turned into real rewrites (Runs 2 & 3).**
   Widening the ruff ruleset exposed `str+Enum` dual inheritance and a
   needless `try/except/pass` — small but genuine code-quality fixes a
   human review on a tight deadline would plausibly have waved through.

---

## 4. Residual risks / known limitations

- `tasks.json` has no file locking. Two concurrent invocations can race.
  Documented in `clarify.md#C-09`; explicitly out of scope for v1.
- Coverage is **89.15 %**, not 100 %. Uncovered lines are mostly
  error-path branches in `store.py` (double `OSError` on cleanup) and
  `cli.py`'s help-wall fallback. These are low-risk and documented in
  the coverage output.
- Help parsing relies on `argparse` raising `SystemExit(0)`, which is
  implementation-defined. The tests pin it via `pytest.raises(SystemExit)`.

---

## 5. Human acceptance decision

**Decision: ACCEPT** for Part 1A submission.

**Reviewer:** Sasank Valluri
**Date:** 2026-11-07

**Rationale:**
- All four harness gates (lint, SAST, tests, coverage) PASS on the final
  source.
- Every acceptance clause A-001.1 .. A-007.3 and NFR-003 has a
  specification-derived, passing test (`tasks.md` acceptance-to-test map).
- The repair cycles above are genuine and tracked in the harness JSON;
  no test was deleted, no rule was lowered, no snapshot was edited.
- Residual risks (concurrency, help exit semantics) are disclosed and
  bounded.

**Additional controls I would require before production use:**
- Add `fcntl.flock` around every `store.load`/`store.save` pair to close
  the concurrency gap.
- Promote the harness invocation into a pre-commit hook so a future
  contributor cannot land a change without re-running the four gates.
