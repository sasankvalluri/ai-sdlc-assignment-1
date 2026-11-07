"""REQ-003 — show command acceptance tests."""

from __future__ import annotations

import json

from smart_todo.cli import main


def test_a_003_1_show_ok(store_path, capsys):
    main(["--store", str(store_path), "add", "--title", "Buy milk"])
    task_id = capsys.readouterr().out.strip()
    rc = main(["--store", str(store_path), "show", task_id])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["id"] == task_id
    assert data["title"] == "Buy milk"


def test_a_003_2_show_missing_exits_1(store_path, capsys):
    rc = main(["--store", str(store_path), "show", "deadbeef"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err
