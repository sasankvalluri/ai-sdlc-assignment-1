# Task Breakdown — Smart Todo CLI (001)

Tasks are ordered so each depends only on earlier ones. Each task names the
`REQ` and acceptance ids it realises.

| # | Task | Produces | Covers |
|---|------|----------|--------|
| T-01 | Create `pyproject.toml` with console script `smart-todo = smart_todo.cli:main` and dev-deps `pytest`, `pytest-cov`, `ruff`, `bandit`. | `pyproject.toml` | Plan §1 |
| T-02 | Implement `models.py`: `Priority`, `Status` enums; `Task` dataclass with validators matching spec §3. | `src/smart_todo/models.py` | §3 types |
| T-03 | Implement `errors.py`: `ValidationError`, `NotFoundError`, `IllegalTransitionError`, `StoreError`. | `src/smart_todo/errors.py` | §6 exit codes |
| T-04 | Implement `store.py`: `load(path)`, `save(path, store)` with atomic rename, store version `1`. | `src/smart_todo/store.py` | REQ-007 |
| T-05 | Implement `commands.py` functions: `add`, `list_tasks`, `show`, `update`, `start`, `done`, `cancel`, `delete`. | `src/smart_todo/commands.py` | REQ-001..006 |
| T-06 | Implement `cli.py` argparse dispatch, exit-code mapping, `--json` plumbing. | `src/smart_todo/cli.py` | all REQ, NFR-003 |
| T-07 | Write `tests/conftest.py` with `tmp_store` fixture, frozen `now_utc`, deterministic `new_id`. | `tests/conftest.py` | plan §3.3 |
| T-08 | Write unit tests one module per REQ, with each test referencing its acceptance id in its name (e.g. `test_add_a_001_1_defaults`). | `tests/test_*.py` | all A-* |
| T-09 | Write `.harness/run.py` running ruff → bandit → pytest → coverage, emitting `evidence/harness-run-<ts>.json` and a terminal summary. | `.harness/run.py` | Article III |
| T-10 | Write `.harness/run.sh` wrapper that invokes `uv run python .harness/run.py "$@"`. | `.harness/run.sh` | Article III |
| T-11 | Snapshot the first harness run (expected to fail at least once) to `evidence/initial-generation/`. | evidence | Article V |
| T-12 | Feed failure evidence back, repair, re-run harness. Snapshot final to `evidence/final-generation/`. | evidence | Article V |
| T-13 | Write `evidence/harness-log.md` — narrative audit trail ending with ACCEPT/REJECT decision. | `evidence/harness-log.md` | Article VI |

## Acceptance-to-test map

| Acceptance | Test file / test name |
|------------|-----------------------|
| A-001.1 defaults | `test_add.py::test_a_001_1_default_fields` |
| A-001.2 bad priority | `test_add.py::test_a_001_2_invalid_priority_exits_2` |
| A-001.3 empty title | `test_add.py::test_a_001_3_empty_title_exits_2` |
| A-001.4 bad tag | `test_add.py::test_a_001_4_invalid_tag_exits_2` |
| A-002.1 priority sort | `test_list.py::test_a_002_1_sort_priority_desc_then_created_at_asc` |
| A-002.2 tag filter | `test_list.py::test_a_002_2_tag_filter` |
| A-002.3 status filter | `test_list.py::test_a_002_3_status_filter` |
| A-002.4 json output | `test_list.py::test_a_002_4_json_output_shape` |
| A-003.1 show ok | `test_show.py::test_a_003_1_show_ok` |
| A-003.2 show missing | `test_show.py::test_a_003_2_show_missing_exits_1` |
| A-004.1 partial update | `test_update.py::test_a_004_1_only_supplied_fields_change` |
| A-004.2 tag replace | `test_update.py::test_a_004_2_tag_replaces` |
| A-004.3 updated_at | `test_update.py::test_a_004_3_updated_at_refreshed` |
| A-005.1 illegal | `test_transitions.py::test_a_005_1_illegal_transition_exits_1` |
| A-005.2 legal | `test_transitions.py::test_a_005_2_legal_transition_updates_status` |
| A-005.3 same-state illegal | `test_transitions.py::test_a_005_3_done_to_done_is_illegal` |
| A-006.1 no-yes | `test_delete.py::test_a_006_1_refuse_without_yes` |
| A-006.2 delete ok | `test_delete.py::test_a_006_2_delete_removes_task` |
| A-006.3 delete missing | `test_delete.py::test_a_006_3_delete_missing_exits_1` |
| A-007.1 auto-create | `test_persistence.py::test_a_007_1_store_auto_created` |
| A-007.2 atomic write | `test_persistence.py::test_a_007_2_atomic_write` |
| A-007.3 malformed | `test_persistence.py::test_a_007_3_malformed_store_exits_3` |
| NFR-003 help | `test_help.py::test_nfr_003_help_exits_0` |
