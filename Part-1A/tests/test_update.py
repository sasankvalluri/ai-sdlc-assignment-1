"""REQ-004 — update command acceptance tests."""

from __future__ import annotations

import json

from smart_todo import commands, models
from smart_todo.cli import main


def _add_and_get_id(store, capsys, **extra):
    args = ["--store", str(store), "add", "--title", "T"]
    for k, v in extra.items():
        args += [f"--{k}", v]
    main(args)
    return capsys.readouterr().out.strip()


def test_a_004_1_only_supplied_fields_change(store_path, capsys):
    task_id = _add_and_get_id(store_path, capsys, priority="low")
    rc = main([
        "--store", str(store_path), "update", task_id,
        "--title", "New title",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["title"] == "New title"
    assert data["priority"] == "low"  # preserved


def test_a_004_2_tag_replaces(store_path, capsys, monkeypatch):
    # First add with two tags
    rc = main([
        "--store", str(store_path), "add", "--title", "T",
        "--tag", "a", "--tag", "b",
    ])
    task_id = capsys.readouterr().out.strip()
    assert rc == 0
    # Replace tags with a single new one
    rc = main([
        "--store", str(store_path), "update", task_id,
        "--tag", "c",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tags"] == ["c"]


def test_a_004_3_updated_at_refreshed(store_path, capsys, monkeypatch):
    task_id = _add_and_get_id(store_path, capsys)
    # Jump the clock before the update
    monkeypatch.setattr(models, "now_utc", lambda: "2026-11-08T12:34:56Z")
    monkeypatch.setattr(commands, "now_utc", lambda: "2026-11-08T12:34:56Z")
    rc = main([
        "--store", str(store_path), "update", task_id, "--title", "T2",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["created_at"] == "2026-11-07T10:00:00Z"
    assert data["updated_at"] == "2026-11-08T12:34:56Z"


def test_a_004_invalid_priority_on_update_exits_2(store_path, capsys):
    task_id = _add_and_get_id(store_path, capsys)
    rc = main([
        "--store", str(store_path), "update", task_id, "--priority", "nope",
    ])
    assert rc == 2
