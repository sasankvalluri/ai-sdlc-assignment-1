"""REQ-005 — status transition acceptance tests."""

from __future__ import annotations

import json

from smart_todo.cli import main


def _add(store, capsys):
    main(["--store", str(store), "add", "--title", "T"])
    return capsys.readouterr().out.strip()


def test_a_005_2_legal_transition_updates_status(store_path, capsys):
    tid = _add(store_path, capsys)
    assert main(["--store", str(store_path), "start", tid]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "in_progress"
    assert main(["--store", str(store_path), "done", tid]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "done"


def test_a_005_1_illegal_transition_exits_1(store_path, capsys):
    tid = _add(store_path, capsys)
    main(["--store", str(store_path), "done", tid])
    capsys.readouterr()
    rc = main(["--store", str(store_path), "start", tid])
    assert rc == 1
    err = capsys.readouterr().err
    assert "illegal transition: done -> in_progress" in err


def test_a_005_3_done_to_done_is_illegal(store_path, capsys):
    tid = _add(store_path, capsys)
    main(["--store", str(store_path), "done", tid])
    capsys.readouterr()
    rc = main(["--store", str(store_path), "done", tid])
    assert rc == 1
    err = capsys.readouterr().err
    assert "illegal transition: done -> done" in err


def test_a_005_cancel_from_in_progress(store_path, capsys):
    tid = _add(store_path, capsys)
    main(["--store", str(store_path), "start", tid])
    capsys.readouterr()
    assert main(["--store", str(store_path), "cancel", tid]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "cancelled"


def test_a_005_start_on_cancelled_is_illegal(store_path, capsys):
    tid = _add(store_path, capsys)
    main(["--store", str(store_path), "cancel", tid])
    capsys.readouterr()
    rc = main(["--store", str(store_path), "start", tid])
    assert rc == 1
