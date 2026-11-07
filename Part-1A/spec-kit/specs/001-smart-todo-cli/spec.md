# Feature Specification — Smart Todo CLI

**Feature:** `001-smart-todo-cli`
**Status:** Approved
**Owner:** Sasank Valluri
**Date:** 2026-11-07

## 1. Purpose

A single-user command-line task manager that persists tasks to a local
JSON file. The CLI supports CRUD on tasks, tag-based filtering, priority
ordering and controlled status transitions. The behaviour is fully
deterministic: identical inputs yield identical outputs.

## 2. Primary users & stories

- **US-1.** As a user, I can add a task with a title, optional description,
  priority and tags so that I can record work I need to do.
- **US-2.** As a user, I can list tasks, optionally filtered by tag or
  status, ordered by priority then creation time, so that I can see
  the most important work first.
- **US-3.** As a user, I can transition a task's status through a defined
  lifecycle so that stale or completed work is not confused with active
  work.
- **US-4.** As a user, I can update a task's mutable fields or delete it
  so that my task list stays accurate.

## 3. Data model

```
Task
├── id            : str       — UUID v4, server-generated, immutable
├── title         : str       — 1..200 chars, trimmed, required
├── description   : str       — 0..2000 chars, optional, default ""
├── priority      : enum      — one of {"low", "medium", "high"}
├── tags          : list[str] — 0..20 elements; each tag matches ^[a-z0-9-]{1,30}$
├── status        : enum      — one of {"pending", "in_progress", "done", "cancelled"}
├── created_at    : str       — ISO 8601 UTC, immutable
└── updated_at    : str       — ISO 8601 UTC, updated on every mutation
```

Persistence file (default path `./tasks.json`):

```json
{
  "version": 1,
  "tasks": [ { ...Task }, ... ]
}
```

## 4. Functional requirements

### REQ-001 — add

The `add` command creates a task.

```
smart-todo add --title "<title>" [--description "<text>"]
               [--priority low|medium|high] [--tag <t>]...
```

- **Acceptance A-001.1.** Given an empty store, when `add --title "Buy milk"`
  is run, then a new task is persisted with status `pending`, priority
  `medium`, tags `[]`, description `""`, and the command prints the new
  task's `id` on stdout followed by a newline. Exit code is `0`.
- **Acceptance A-001.2.** Given `--priority` is not in `{low, medium, high}`,
  then the command prints the validation error to stderr and exits `2`.
  The store is unchanged.
- **Acceptance A-001.3.** Given `--title` is empty or whitespace-only,
  then the command exits `2` and the store is unchanged.
- **Acceptance A-001.4.** Given any tag fails the pattern
  `^[a-z0-9-]{1,30}$`, then the command exits `2` and the store is
  unchanged.

### REQ-002 — list

```
smart-todo list [--tag <t>] [--status <s>] [--json]
```

- **Acceptance A-002.1.** List order **must** be: priority descending
  (`high` → `medium` → `low`), then `created_at` ascending for ties.
- **Acceptance A-002.2.** Given `--tag foo`, only tasks whose `tags`
  contain `foo` are returned.
- **Acceptance A-002.3.** Given `--status done`, only tasks with
  `status == done` are returned.
- **Acceptance A-002.4.** With `--json`, stdout is a single valid JSON
  array of task objects (keys in the order declared in §3). Without
  `--json`, output is a human-readable table.

### REQ-003 — show

```
smart-todo show <id>
```

- **Acceptance A-003.1.** When the id exists, the command prints the task
  as pretty JSON and exits `0`.
- **Acceptance A-003.2.** When the id does not exist, the command exits
  `1` and prints `task not found: <id>` to stderr.

### REQ-004 — update

```
smart-todo update <id> [--title <t>] [--description <d>]
                       [--priority <p>] [--tag <t>]...
```

- **Acceptance A-004.1.** Only the supplied fields change. Omitted fields
  are preserved exactly.
- **Acceptance A-004.2.** Passing `--tag` replaces the full tag list.
  Passing no `--tag` leaves tags unchanged.
- **Acceptance A-004.3.** On success, `updated_at` is set to the current
  UTC time (ISO 8601). `created_at` is never changed.

### REQ-005 — status transition

```
smart-todo start <id>     # pending      -> in_progress
smart-todo done  <id>     # pending|in_progress -> done
smart-todo cancel <id>    # pending|in_progress -> cancelled
```

The allowed state machine:

```
          start                done
pending ───────▶ in_progress ────────▶ done
   │                   │
   │ cancel            │ cancel
   ▼                   ▼
cancelled ◀──────── cancelled
```

- **Acceptance A-005.1.** Illegal transitions (e.g. `start` on a `done`
  task) exit `1` and print
  `illegal transition: <current> -> <target>` to stderr. The store is
  unchanged.
- **Acceptance A-005.2.** Legal transitions update `status` and
  `updated_at` only.
- **Acceptance A-005.3.** Transitioning to the same status (`done` on a
  task already `done`) is **not** idempotent — it is an illegal
  transition and exits `1`.

### REQ-006 — delete

```
smart-todo delete <id> --yes
```

- **Acceptance A-006.1.** Without `--yes`, the command exits `2` with
  `refusing to delete without --yes` on stderr.
- **Acceptance A-006.2.** With `--yes` and a valid id, the task is removed
  and the command exits `0`.
- **Acceptance A-006.3.** With `--yes` and an unknown id, the command
  exits `1`.

### REQ-007 — persistence integrity

- **Acceptance A-007.1.** The store file is created if it does not exist
  (with `{"version": 1, "tasks": []}`).
- **Acceptance A-007.2.** Writes are atomic: the CLI writes to a temp
  file in the same directory and renames.
- **Acceptance A-007.3.** On a malformed store file, every command exits
  `3` and leaves the file untouched.

## 5. Non-functional requirements

- **NFR-001.** No command performs network I/O.
- **NFR-002.** No command reads or writes files outside the store
  directory or standard streams.
- **NFR-003.** `smart-todo --help` and `smart-todo <cmd> --help` exit `0`
  and print usage.
- **NFR-004.** Startup to first output under 150 ms on a 1k-task store.

## 6. Exit-code contract

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Logical error (not found, illegal transition) |
| 2 | Validation error (bad arguments) |
| 3 | I/O or persistence error |

## 7. Out of scope

- Multi-user concurrency, networking, calendars, notifications, GUI.
- Recurrence, subtasks, dependencies between tasks.
- Internationalisation (titles/descriptions are stored verbatim as UTF-8).
