"""Pure command functions. CLI layer maps return values to stdout + exit codes."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from . import store as store_mod
from .errors import IllegalTransitionError, NotFoundError
from .models import (
    ALLOWED_TRANSITIONS,
    Status,
    Task,
    new_task,
    now_utc,
    priority_rank,
    validate_description,
    validate_priority,
    validate_tags,
    validate_title,
)


def add(
    path: Path,
    *,
    title: str,
    description: str | None,
    priority: str | None,
    tags: list[str] | None,
    clock: Callable[[], str] | None = None,
    id_factory=None,
) -> Task:
    s = store_mod.load(path)
    kwargs = {}
    if clock is not None:
        kwargs["clock"] = clock
    if id_factory is not None:
        kwargs["id_factory"] = id_factory
    task = new_task(title, description, priority, tags, **kwargs)
    s.tasks.append(task)
    store_mod.save(path, s)
    return task


def list_tasks(
    path: Path,
    *,
    tag: str | None = None,
    status: str | None = None,
) -> list[Task]:
    s = store_mod.load(path)
    items = s.tasks
    if tag is not None:
        items = [t for t in items if tag in t.tags]
    if status is not None:
        st = Status(status)  # may raise ValueError -> caller converts
        items = [t for t in items if t.status == st]
    items = sorted(
        items,
        key=lambda t: (-priority_rank(t.priority), t.created_at, t.id),
    )
    return items


def show(path: Path, task_id: str) -> Task:
    s = store_mod.load(path)
    for t in s.tasks:
        if t.id == task_id:
            return t
    raise NotFoundError(f"task not found: {task_id}")


def update(
    path: Path,
    task_id: str,
    *,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    tags: list[str] | None = None,
    clock: Callable[[], str] | None = None,
) -> Task:
    _clock = clock if clock is not None else now_utc
    s = store_mod.load(path)
    for i, t in enumerate(s.tasks):
        if t.id == task_id:
            new_title = validate_title(title) if title is not None else t.title
            new_desc = (
                validate_description(description) if description is not None else t.description
            )
            new_prio = validate_priority(priority) if priority is not None else t.priority
            new_tags = validate_tags(tags) if tags is not None else t.tags
            updated = Task(
                id=t.id,
                title=new_title,
                description=new_desc,
                priority=new_prio,
                tags=new_tags,
                status=t.status,
                created_at=t.created_at,
                updated_at=_clock(),
            )
            s.tasks[i] = updated
            store_mod.save(path, s)
            return updated
    raise NotFoundError(f"task not found: {task_id}")


def _transition(
    path: Path,
    task_id: str,
    target: Status,
    *,
    clock: Callable[[], str] | None = None,
) -> Task:
    _clock = clock if clock is not None else now_utc
    s = store_mod.load(path)
    for i, t in enumerate(s.tasks):
        if t.id == task_id:
            if target not in ALLOWED_TRANSITIONS[t.status]:
                raise IllegalTransitionError(
                    f"illegal transition: {t.status.value} -> {target.value}"
                )
            updated = Task(
                id=t.id,
                title=t.title,
                description=t.description,
                priority=t.priority,
                tags=t.tags,
                status=target,
                created_at=t.created_at,
                updated_at=_clock(),
            )
            s.tasks[i] = updated
            store_mod.save(path, s)
            return updated
    raise NotFoundError(f"task not found: {task_id}")


def start(path: Path, task_id: str, **kwargs) -> Task:
    return _transition(path, task_id, Status.IN_PROGRESS, **kwargs)


def done(path: Path, task_id: str, **kwargs) -> Task:
    return _transition(path, task_id, Status.DONE, **kwargs)


def cancel(path: Path, task_id: str, **kwargs) -> Task:
    return _transition(path, task_id, Status.CANCELLED, **kwargs)


def delete(path: Path, task_id: str) -> None:
    s = store_mod.load(path)
    for i, t in enumerate(s.tasks):
        if t.id == task_id:
            del s.tasks[i]
            store_mod.save(path, s)
            return
    raise NotFoundError(f"task not found: {task_id}")
