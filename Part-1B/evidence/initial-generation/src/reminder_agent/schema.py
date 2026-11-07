"""Output contract — pydantic models that are the single source of truth
for shape validation. The JSON Schema used by harness Layer 1 is derived
from these models via `to_json_schema()`."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing_extensions import Annotated


class Intent(StrEnum):
    CREATE = "create"
    RESCHEDULE = "reschedule"
    SNOOZE = "snooze"
    CANCEL = "cancel"
    LIST = "list"
    CLARIFY = "clarify"


ALLOWED_MISSING_FIELDS = {"title", "when", "target_reference", "snooze_minutes"}


class WhenSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    iso: Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")]
    timezone: Annotated[str, StringConstraints(min_length=1, max_length=64)]


class ReminderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    title: str | None = None
    when: WhenSpec | None = None
    snooze_minutes: int | None = Field(default=None, ge=1, le=10080)
    target_reference: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


def to_json_schema() -> dict[str, Any]:
    """JSON Schema derived from the pydantic model (harness Layer 1)."""
    return ReminderResponse.model_json_schema()
