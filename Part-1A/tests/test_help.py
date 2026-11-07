"""NFR-003 — --help works and exits 0."""

from __future__ import annotations

import pytest

from smart_todo.cli import main


def test_nfr_003_help_exits_0(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "smart-todo" in out


def test_nfr_003_subcommand_help_exits_0(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["add", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--title" in out
