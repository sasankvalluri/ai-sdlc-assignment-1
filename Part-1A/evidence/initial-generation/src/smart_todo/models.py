"""Task model, enums and validators (spec §3)."""

from __future__ import annotations

import datetime as _dt
import re
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .errors import ValidationError

TAG_RE = re.compile(r"^[a-z0-9-]{1,30}$")
MAX_TITLE = 200
MAX_DESC = 2000
MAX_TAGS = 20


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


_PRIORITY_RANK = {Priority.LOW: 0, Priority.MEDIUM: 1, Priority.HIGH: 2}


def priority_rank(p: Priority) -> int:
    return _PRIORITY_RANK[p]


def now_utc() -> str:
    """ISO 8601 UTC timestamp truncated to seconds (constitution Article I)."""
    return (
        _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: Priority
    tags: list[str]
    status: Status
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["priority"] = self.priority.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        try:
            return cls(
                id=data["id"],
                title=data["title"],
                description=data.get("description", ""),
                priority=Priority(data["priority"]),
                tags=list(data.get("tags", [])),
                status=Status(data["status"]),
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
        except (KeyError, ValueError) as exc:
            raise ValidationError(f"invalid task record: {exc}") from exc


def validate_title(value: str) -> str:
    v = value.strip()
    if not v:
        raise ValidationError("title must not be empty")
    if len(v) > MAX_TITLE:
        raise ValidationError(f"title longer than {MAX_TITLE} characters")
    return v


def validate_description(value: str | None) -> str:
    v = value or ""
    if len(v) > MAX_DESC:
        raise ValidationError(f"description longer than {MAX_DESC} characters")
    return v


def validate_priority(value: str | None) -> Priority:
    if value is None:
        return Priority.MEDIUM
    try:
        return Priority(value)
    except ValueError as exc:
        raise ValidationError(
            f"priority must be one of low|medium|high (got {value!r})"
        ) from exc


def validate_tags(values: list[str] | None) -> list[str]:
    tags = list(values or [])
    if len(tags) > MAX_TAGS:
        raise ValidationError(f"too many tags (max {MAX_TAGS})")
    for t in tags:
        if not isinstance(t, str) or not TAG_RE.match(t):
            raise ValidationError(f"invalid tag {t!r}; must match {TAG_RE.pattern}")
    return tags


def new_task(
    title: str,
    description: str | None,
    priority: str | None,
    tags: list[str] | None,
    *,
    id_factory=new_id,
    clock=now_utc,
) -> Task:
    ts = clock()
    return Task(
        id=id_factory(),
        title=validate_title(title),
        description=validate_description(description),
        priority=validate_priority(priority),
        tags=validate_tags(tags),
        status=Status.PENDING,
        created_at=ts,
        updated_at=ts,
    )


# Allowed state transitions (spec REQ-005). Note: same-state is NOT allowed.
ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    Status.PENDING: {Status.IN_PROGRESS, Status.DONE, Status.CANCELLED},
    Status.IN_PROGRESS: {Status.DONE, Status.CANCELLED},
    Status.DONE: set(),
    Status.CANCELLED: set(),
}
