"""REQ-001 — add command acceptance tests."""

from __future__ import annotations

from smart_todo.cli import main

from .conftest import read_store


def test_a_001_1_default_fields(store_path, capsys):
    rc = main(["--store", str(store_path), "add", "--title", "Buy milk"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out  # new task id printed
    data = read_store(store_path)
    assert data["version"] == 1
    assert len(data["tasks"]) == 1
    task = data["tasks"][0]
    assert task["title"] == "Buy milk"
    assert task["description"] == ""
    assert task["priority"] == "medium"
    assert task["tags"] == []
    assert task["status"] == "pending"
    assert task["created_at"] == "2026-11-07T10:00:00Z"
    assert task["updated_at"] == "2026-11-07T10:00:00Z"
    assert task["id"] == out


def test_a_001_2_invalid_priority_exits_2(store_path, capsys):
    rc = main(["--store", str(store_path), "add", "--title", "T", "--priority", "urgent"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "priority" in err
    assert not store_path.exists() or read_store(store_path)["tasks"] == []


def test_a_001_3_empty_title_exits_2(store_path, capsys):
    rc = main(["--store", str(store_path), "add", "--title", "   "])
    assert rc == 2
    err = capsys.readouterr().err
    assert "title" in err
    assert not store_path.exists() or read_store(store_path)["tasks"] == []


def test_a_001_4_invalid_tag_exits_2(store_path, capsys):
    rc = main(["--store", str(store_path), "add", "--title", "T", "--tag", "Bad Tag"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "tag" in err
    assert not store_path.exists() or read_store(store_path)["tasks"] == []


def test_a_001_valid_tags_accepted(store_path):
    rc = main([
        "--store", str(store_path), "add", "--title", "Groceries",
        "--tag", "home", "--tag", "urgent-1",
    ])
    assert rc == 0
    tasks = read_store(store_path)["tasks"]
    assert tasks[0]["tags"] == ["home", "urgent-1"]
