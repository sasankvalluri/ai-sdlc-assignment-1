# Smart Todo CLI — Project Constitution

**Scope:** Assignment 1 — Part 1A (deterministic application).
**Last updated:** 2026-11-07

The constitution defines principles that every downstream Spec Kit artifact
(spec, clarify, plan, tasks, implementation) must respect. Any deviation
must be reflected in an upstream artifact change *before* code is written.

---

## Article I — Deterministic behaviour

1. Given the same input state (persisted task file) and the same command
   invocation, the CLI **must** produce identical output and exit code.
2. All timestamps written to the task file **must** be ISO 8601 UTC
   (`YYYY-MM-DDTHH:MM:SSZ`). Time handling never depends on the local
   timezone.
3. No command may mutate state unless it exits with code `0`.

## Article II — Specification-controlled development

1. Every behaviour is traceable to a `REQ-###` identifier in `spec.md`.
2. Acceptance criteria in `spec.md` use the form "given … when … then …" so
   that each criterion yields a binary pass/fail test.
3. If the implementation needs a behaviour not covered by `spec.md`, the
   specification is updated and re-approved **first**.

## Article III — Harness-enforced quality

The implementation is only accepted when **all** of the following gates
pass on an unmodified working tree:

| Gate | Tool | Pass criterion |
|------|------|----------------|
| G1 Lint | `ruff check` | 0 violations |
| G2 Security (SAST) | `bandit -r src` | 0 Medium/High issues |
| G3 Unit & contract tests | `pytest` | 100% of spec-derived tests pass |
| G4 Coverage | `pytest --cov` | ≥ 85% line coverage of `src/` |

The harness runner emits a single machine-readable JSON verdict. Human
acceptance is only recorded after all gates report PASS.

## Article IV — Safety & integrity

1. The CLI must not read or write any file outside the configured
   task-store path except for `stdout`/`stderr`.
2. No command may execute an external process, open a network socket or
   evaluate user-supplied strings as code.
3. Secrets (API keys, tokens) are never required, read or logged.
4. Destructive commands (`delete`, `purge`) **must** require an explicit
   `--yes` flag or an interactive confirmation.

## Article V — Agent & self-healing discipline

1. The AI coding agent receives the approved specification context before
   implementation. Acceptance criteria may not be weakened, removed or
   paraphrased by the agent.
2. When the harness reports failure, the failure evidence (gate, rule,
   expected vs. observed) is fed back verbatim to the agent and the repair
   runs against the **same** harness gates.
3. Tests, lint rules and SAST configuration are **not** edited to make a
   failure disappear. Legitimate changes require a spec revision.
4. The first generated implementation is preserved under
   `evidence/initial-generation/` before any repair is applied.

## Article VI — Observability & evidence

1. Every harness invocation writes a timestamped record to
   `evidence/harness-run-<timestamp>.json`.
2. `evidence/harness-log.md` contains the narrative audit trail: what the
   agent generated, what failed, what was fed back, what changed, and the
   final human ACCEPT/REJECT decision with justification.
