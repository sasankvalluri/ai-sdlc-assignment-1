"""REQ-006 — delete command acceptance tests."""

from __future__ import annotations

from smart_todo.cli import main

from .conftest import read_store


def _add(store, capsys):
    main(["--store", str(store), "add", "--title", "T"])
    return capsys.readouterr().out.strip()


def test_a_006_1_refuse_without_yes(store_path, capsys):
    tid = _add(store_path, capsys)
    rc = main(["--store", str(store_path), "delete", tid])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--yes" in err
    assert len(read_store(store_path)["tasks"]) == 1


def test_a_006_2_delete_removes_task(store_path, capsys):
    tid = _add(store_path, capsys)
    rc = main(["--store", str(store_path), "delete", tid, "--yes"])
    assert rc == 0
    assert read_store(store_path)["tasks"] == []


def test_a_006_3_delete_missing_exits_1(store_path, capsys):
    rc = main(["--store", str(store_path), "delete", "no-such", "--yes"])
    assert rc == 1
