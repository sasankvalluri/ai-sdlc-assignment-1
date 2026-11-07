"""REQ-007 — persistence acceptance tests."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from smart_todo.cli import main
from smart_todo.errors import StoreError
from smart_todo import store as store_mod

from .conftest import read_store


def test_a_007_1_store_auto_created(store_path):
    assert not store_path.exists()
    assert main(["--store", str(store_path), "add", "--title", "T"]) == 0
    assert store_path.exists()
    assert read_store(store_path) == {
        "version": 1,
        "tasks": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "title": "T",
                "description": "",
                "priority": "medium",
                "tags": [],
                "status": "pending",
                "created_at": "2026-11-07T10:00:00Z",
                "updated_at": "2026-11-07T10:00:00Z",
            }
        ],
    }


def test_a_007_2_atomic_write_uses_temp_and_replace(store_path, monkeypatch):
    seen = {"tmp": None, "replaced": False}

    orig_mkstemp = store_mod.tempfile.mkstemp
    orig_replace = store_mod.os.replace

    def wrapped_mkstemp(*args, **kwargs):
        fd, path = orig_mkstemp(*args, **kwargs)
        seen["tmp"] = path
        return fd, path

    def wrapped_replace(src, dst):
        seen["replaced"] = True
        assert src == seen["tmp"]
        assert str(dst) == str(store_path)
        return orig_replace(src, dst)

    monkeypatch.setattr(store_mod.tempfile, "mkstemp", wrapped_mkstemp)
    monkeypatch.setattr(store_mod.os, "replace", wrapped_replace)
    assert main(["--store", str(store_path), "add", "--title", "T"]) == 0
    assert seen["replaced"]
    # tmp file was in the same directory
    assert Path(seen["tmp"]).parent == store_path.parent


def test_a_007_3_malformed_store_exits_3(store_path, capsys):
    store_path.write_text("this is not json", encoding="utf-8")
    rc = main(["--store", str(store_path), "list"])
    assert rc == 3
    err = capsys.readouterr().err
    assert "cannot read store" in err or "unsupported" in err
    # File is unchanged
    assert store_path.read_text(encoding="utf-8") == "this is not json"
