"""REQ-002 — list command acceptance tests."""

from __future__ import annotations

import json

from smart_todo.cli import main


def _seed(store):
    # Insert tasks in deliberately "wrong" priority order to verify sort.
    main(["--store", str(store), "add", "--title", "Low 1", "--priority", "low", "--tag", "work"])
    main(["--store", str(store), "add", "--title", "High 1", "--priority", "high", "--tag", "work"])
    main(["--store", str(store), "add", "--title", "Med 1", "--priority", "medium"])
    main(["--store", str(store), "add", "--title", "High 2", "--priority", "high", "--tag", "home"])


def test_a_002_1_sort_priority_desc_then_created_at_asc(store_path, capsys):
    _seed(store_path)
    capsys.readouterr()  # discard add output
    rc = main(["--store", str(store_path), "list", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    arr = json.loads(out)
    titles = [t["title"] for t in arr]
    # priority DESC: High 1, High 2 (both high, tie broken by created_at asc), Med 1, Low 1
    assert titles == ["High 1", "High 2", "Med 1", "Low 1"]


def test_a_002_2_tag_filter(store_path, capsys):
    _seed(store_path)
    capsys.readouterr()
    rc = main(["--store", str(store_path), "list", "--tag", "home", "--json"])
    assert rc == 0
    arr = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in arr] == ["High 2"]


def test_a_002_3_status_filter(store_path, capsys):
    _seed(store_path)
    capsys.readouterr()
    # Start/done the "Med 1" task: first list to get its id
    rc = main(["--store", str(store_path), "list", "--json"])
    arr = json.loads(capsys.readouterr().out)
    med = next(t for t in arr if t["title"] == "Med 1")
    main(["--store", str(store_path), "start", med["id"]])
    capsys.readouterr()
    rc = main(["--store", str(store_path), "list", "--status", "in_progress", "--json"])
    assert rc == 0
    arr = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in arr] == ["Med 1"]


def test_a_002_3_invalid_status_exits_2(store_path, capsys):
    _seed(store_path)
    capsys.readouterr()
    rc = main(["--store", str(store_path), "list", "--status", "nope"])
    assert rc == 2


def test_a_002_4_json_output_shape(store_path, capsys):
    _seed(store_path)
    capsys.readouterr()
    rc = main(["--store", str(store_path), "list", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    arr = json.loads(out)
    assert isinstance(arr, list)
    keys = list(arr[0].keys())
    assert keys == [
        "id", "title", "description", "priority", "tags",
        "status", "created_at", "updated_at",
    ]


def test_a_002_4_table_output_when_no_json(store_path, capsys):
    _seed(store_path)
    capsys.readouterr()
    rc = main(["--store", str(store_path), "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "TITLE" in out
    assert "High 1" in out
