"""Prompt loading + hashing for evidence records."""

from __future__ import annotations

import hashlib
from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "system.md"


def load_system_prompt(*, now_iso: str, timezone: str) -> str:
    """Use string.Template with `$now` / `$timezone` so that JSON `{…}`
    inside the prompt body is not misinterpreted as a format field."""
    from string import Template

    template = Template(PROMPT_PATH.read_text(encoding="utf-8"))
    return template.safe_substitute(now=now_iso, timezone=timezone)


def prompt_hash() -> str:
    raw = PROMPT_PATH.read_bytes()
    return hashlib.sha256(raw).hexdigest()[:16]
