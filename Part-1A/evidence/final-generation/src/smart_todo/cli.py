"""Argparse dispatch and exit-code mapping (spec §6)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import commands
from .errors import CLIError, ValidationError
from .models import Task

DEFAULT_STORE = "tasks.json"


def _store_path(args: argparse.Namespace) -> Path:
    override = getattr(args, "store", None) or os.environ.get("SMART_TODO_STORE")
    return Path(override or DEFAULT_STORE)


def _print_task_table(tasks: list[Task]) -> None:
    if not tasks:
        print("(no tasks)")
        return
    rows = [("ID", "PRI", "STATUS", "TAGS", "TITLE")]
    for t in tasks:
        rows.append(
            (
                t.id[:8],
                t.priority.value,
                t.status.value,
                ",".join(t.tags),
                t.title,
            )
        )
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(r)))


def _print_task_json(task: Task) -> None:
    print(json.dumps(task.to_dict(), indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="smart-todo", description="Deterministic todo CLI.")
    p.add_argument("--store", help="Path to the JSON task store (default: ./tasks.json).")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="Add a task.")
    pa.add_argument("--title", required=True)
    pa.add_argument("--description", default=None)
    pa.add_argument("--priority", default=None)
    pa.add_argument("--tag", dest="tags", action="append", default=None)

    pl = sub.add_parser("list", help="List tasks.")
    pl.add_argument("--tag", default=None)
    pl.add_argument("--status", default=None)
    pl.add_argument("--json", dest="as_json", action="store_true")

    ps = sub.add_parser("show", help="Show a task as JSON.")
    ps.add_argument("id")

    pu = sub.add_parser("update", help="Update mutable fields.")
    pu.add_argument("id")
    pu.add_argument("--title", default=None)
    pu.add_argument("--description", default=None)
    pu.add_argument("--priority", default=None)
    pu.add_argument("--tag", dest="tags", action="append", default=None)

    for name in ("start", "done", "cancel"):
        pt = sub.add_parser(name, help=f"Transition to {name}.")
        pt.add_argument("id")

    pd = sub.add_parser("delete", help="Delete a task (requires --yes).")
    pd.add_argument("id")
    pd.add_argument("--yes", action="store_true")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = _store_path(args)
    try:
        if args.cmd == "add":
            task = commands.add(
                path,
                title=args.title,
                description=args.description,
                priority=args.priority,
                tags=args.tags,
            )
            print(task.id)
            return 0

        if args.cmd == "list":
            try:
                tasks = commands.list_tasks(path, tag=args.tag, status=args.status)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            if args.as_json:
                print(
                    json.dumps(
                        [t.to_dict() for t in tasks], indent=2, ensure_ascii=False
                    )
                )
            else:
                _print_task_table(tasks)
            return 0

        if args.cmd == "show":
            _print_task_json(commands.show(path, args.id))
            return 0

        if args.cmd == "update":
            task = commands.update(
                path,
                args.id,
                title=args.title,
                description=args.description,
                priority=args.priority,
                tags=args.tags,
            )
            _print_task_json(task)
            return 0

        if args.cmd in ("start", "done", "cancel"):
            fn = getattr(commands, args.cmd)
            task = fn(path, args.id)
            _print_task_json(task)
            return 0

        if args.cmd == "delete":
            if not args.yes:
                raise ValidationError("refusing to delete without --yes")
            commands.delete(path, args.id)
            return 0

        # argparse guarantees required=True, but keep a safety net.
        parser.print_help(sys.stderr)
        return 2

    except CLIError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    sys.exit(main())
