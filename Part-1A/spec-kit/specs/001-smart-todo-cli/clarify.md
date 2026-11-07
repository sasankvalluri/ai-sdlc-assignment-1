# Clarifications — Smart Todo CLI (001)

Resolved ambiguities after `/speckit.clarify`. Each entry references the
affected `REQ`/acceptance clause.

| # | Question | Resolution | Affects |
|---|----------|------------|---------|
| C-01 | Should `done → done` be idempotent? | **No** — A-005.3 declares it illegal. Idempotency would hide client bugs. | REQ-005 |
| C-02 | Is the default store path `./tasks.json` relative to the invocation CWD or a fixed user home path? | **Invocation CWD** — simpler, keeps tests hermetic. Overridable via `--store <path>` or env `SMART_TODO_STORE`. | REQ-007 |
| C-03 | Tag matching: case-sensitive or case-insensitive? | **Case-sensitive.** Tags are stored lowercase (validation A-001.4 already forbids uppercase), so matching equality is unambiguous. | REQ-002 |
| C-04 | Does `list` show all statuses by default? | **Yes.** `--status` is opt-in; omitting it includes every status. | REQ-002 |
| C-05 | What priority is applied when `--priority` is omitted on `add`? | **`medium`.** Documented as the default in REQ-001. | REQ-001 |
| C-06 | `update --tag` with zero occurrences — does it clear tags? | **No.** Omitting `--tag` keeps the existing list. To clear tags the caller supplies `--tag ""` which is rejected by the regex, so the only way to clear tags is via a future `--no-tags` flag — **out of scope** for v1. | REQ-004 |
| C-07 | Where does `--json` output route — stdout or a file? | **Stdout.** This keeps commands pipeable. | REQ-002 |
| C-08 | Are the sort keys stable across runs for ties on both priority and `created_at`? | **Yes** — ties on both keys are resolved by `id` ascending. Documented here because A-002.1 only mentions the first two keys. | REQ-002 |
| C-09 | What happens on concurrent invocations? | **Undefined** — v1 is single-user single-process. A future requirement will add file locking. Documented as a known limitation. | NFR |
| C-10 | How is `created_at` generated? | `datetime.datetime.now(datetime.timezone.utc)` truncated to seconds, serialised via `isoformat()` with the `Z` suffix. | REQ-001 |
