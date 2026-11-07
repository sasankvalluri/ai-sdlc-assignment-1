"""Layer 1 — structural / schema validation.

Thin wrapper around `reminder_agent.validators.validate_schema` so the
harness is independent of the application CLI.
"""

from __future__ import annotations

from dataclasses import asdict

from reminder_agent.validators import validate_schema


def evaluate(raw_output: str) -> dict:
    parsed, results = validate_schema(raw_output)
    return {
        "passed": all(r.passed for r in results),
        "checks": [asdict(r) for r in results],
        "parsed": parsed.model_dump() if parsed is not None else None,
    }
