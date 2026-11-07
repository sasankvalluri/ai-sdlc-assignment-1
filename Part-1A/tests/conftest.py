"""Shared fixtures — hermetic store path, frozen clock, deterministic ids."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from smart_todo import commands, models


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "tasks.json"


@pytest.fixture(autouse=True)
def _freeze_time(monkeypatch):
    """Deterministic ISO-8601 UTC timestamp for every test."""
    monkeypatch.setattr(models, "now_utc", lambda: "2026-11-07T10:00:00Z")
    monkeypatch.setattr(commands, "now_utc", lambda: "2026-11-07T10:00:00Z")


@pytest.fixture(autouse=True)
def _seq_ids(monkeypatch):
    """Deterministic monotonic UUIDs so tests can assert on ids."""
    counter = itertools.count(1)

    def _mk() -> str:
        return f"00000000-0000-0000-0000-{next(counter):012d}"

    monkeypatch.setattr(models, "new_id", _mk)


def read_store(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
