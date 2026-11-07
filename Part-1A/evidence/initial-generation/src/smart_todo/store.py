"""Persistence layer with atomic writes (REQ-007)."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .errors import StoreError
from .models import Task

STORE_VERSION = 1


@dataclass
class Store:
    version: int = STORE_VERSION
    tasks: list[Task] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"version": self.version, "tasks": [t.to_dict() for t in self.tasks]}


def load(path: Path) -> Store:
    if not path.exists():
        return Store()
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise StoreError(f"cannot read store at {path}: {exc}") from exc

    if not isinstance(data, dict) or data.get("version") != STORE_VERSION:
        raise StoreError(f"unsupported store schema at {path}")

    raw_tasks = data.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise StoreError(f"malformed tasks list in {path}")

    tasks = [Task.from_dict(t) for t in raw_tasks]
    return Store(version=STORE_VERSION, tasks=tasks)


def save(path: Path, store: Store) -> None:
    """Atomic write — temp file in the same dir, then os.replace (A-007.2)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(store.to_dict(), indent=2, ensure_ascii=False) + "\n"

    fd, tmp_path = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise StoreError(f"cannot write store at {path}: {exc}") from exc
