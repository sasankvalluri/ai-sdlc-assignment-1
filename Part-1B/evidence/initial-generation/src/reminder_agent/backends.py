"""Backends for the agent. Two implementations:

- RealBackend  — GitHub Models (OpenAI-compatible endpoint), requires a
  GitHub PAT with scope `models:read` in GITHUB_TOKEN /
  GITHUB_MODELS_TOKEN.
- MockBackend  — deterministic rule-based parser used for offline
  development and CI. Evaluations run against MockBackend are tagged
  "backend: mock" in the eval record and must NOT be used to claim
  non-deterministic acceptance.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .prompt import load_system_prompt

GITHUB_MODELS_BASE_URL = "https://models.github.ai/inference"
DEFAULT_MODEL = "openai/gpt-4o-mini"


@dataclass
class BackendCall:
    raw_output: str
    model_id: str
    temperature: float
    backend: str


class Backend(ABC):
    @abstractmethod
    def generate(self, *, text: str, now_iso: str, timezone: str) -> BackendCall: ...


# ---------------------------------------------------------------------------
# Real (GitHub Models)
# ---------------------------------------------------------------------------


class RealBackend(Backend):
    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        base_url: str = GITHUB_MODELS_BASE_URL,
    ) -> None:
        token = os.environ.get("GITHUB_MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError(
                "RealBackend requires GITHUB_MODELS_TOKEN or GITHUB_TOKEN "
                "(PAT with scope 'models:read'). See README."
            )
        # Lazy import so a missing openai install does not break mock runs.
        from openai import OpenAI

        self._client = OpenAI(base_url=base_url, api_key=token)
        self._model = model
        self._temperature = temperature

    def generate(self, *, text: str, now_iso: str, timezone: str) -> BackendCall:
        system = load_system_prompt(now_iso=now_iso, timezone=timezone)
        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
        )
        content = resp.choices[0].message.content or ""
        return BackendCall(
            raw_output=content,
            model_id=self._model,
            temperature=self._temperature,
            backend="real",
        )


# ---------------------------------------------------------------------------
# Mock — deterministic rule-based parser (offline only)
# ---------------------------------------------------------------------------


_REL_MIN_RE = re.compile(r"in\s+(\d+)\s+min(?:ute)?s?", re.I)
_REL_HOUR_RE = re.compile(r"in\s+(\d+)\s+hour[s]?", re.I)
_SNOOZE_RE = re.compile(r"snooze.*?(\d+)\s*(min|minute|minutes)?", re.I)
_TOMORROW_TIME_RE = re.compile(
    r"tomorrow(?:\s+at)?\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.I
)
_TONIGHT_RE = re.compile(r"tonight\s*(?:at\s*)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.I)


def _plus_minutes(now_iso: str, minutes: int) -> str:
    base = _dt.datetime.strptime(now_iso, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=_dt.timezone.utc
    )
    return (base + _dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tomorrow_at(now_iso: str, h: int, m: int) -> str:
    base = _dt.datetime.strptime(now_iso, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=_dt.timezone.utc
    )
    target = (base + _dt.timedelta(days=1)).replace(hour=h, minute=m, second=0, microsecond=0)
    return target.strftime("%Y-%m-%dT%H:%M:%SZ")


class MockBackend(Backend):
    """A naive, fully deterministic parser. Covers enough patterns for
    structural + invariant tests. Does not pretend to be good at
    language understanding — the point of the mock is to let the
    harness run offline without claiming acceptance."""

    def generate(self, *, text: str, now_iso: str, timezone: str) -> BackendCall:
        obj = self._parse(text.strip(), now_iso, timezone)
        return BackendCall(
            raw_output=json.dumps(obj, ensure_ascii=False),
            model_id="mock/rule-based-v1",
            temperature=0.0,
            backend="mock",
        )

    # -- intent detection ---------------------------------------------------

    def _parse(self, text: str, now_iso: str, timezone: str) -> dict:
        envelope = {
            "intent": "clarify",
            "title": None,
            "when": None,
            "snooze_minutes": None,
            "target_reference": None,
            "missing_fields": [],
            "clarification_question": None,
            "confidence": 0.3,
        }
        lower = text.lower()

        if not text:
            return self._clarify(envelope, ["title", "when"], "What should I remind you about, and when?")

        if any(k in lower for k in ("list my", "show my", "what reminders")):
            envelope["intent"] = "list"
            envelope["confidence"] = 0.8
            return envelope

        if "cancel" in lower:
            ref = self._extract_reference(text)
            if not ref:
                return self._clarify(envelope, ["target_reference"], "Which reminder should I cancel?")
            envelope.update(intent="cancel", target_reference=ref, confidence=0.8)
            return envelope

        if "snooze" in lower:
            m = _SNOOZE_RE.search(lower)
            ref = self._extract_reference(text)
            if not m:
                return self._clarify(envelope, ["snooze_minutes"], "How many minutes should I snooze it?")
            if not ref:
                return self._clarify(envelope, ["target_reference"], "Which reminder should I snooze?")
            envelope.update(
                intent="snooze",
                target_reference=ref,
                snooze_minutes=int(m.group(1)),
                confidence=0.8,
            )
            return envelope

        if any(k in lower for k in ("reschedule", "move my", "change my")):
            ref = self._extract_reference(text)
            when_iso = self._extract_when(text, now_iso)
            if not ref:
                return self._clarify(envelope, ["target_reference"], "Which reminder should I reschedule?")
            if not when_iso:
                return self._clarify(envelope, ["when"], "What time should I move it to?")
            envelope.update(
                intent="reschedule",
                target_reference=ref,
                when={"iso": when_iso, "timezone": timezone},
                confidence=0.75,
            )
            return envelope

        # Recurring not supported.
        if re.search(r"\bevery\s+(day|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", lower):
            return self._clarify(
                envelope,
                ["when"],
                "Recurring reminders aren't supported yet — do you want this just once?",
            )

        # Default to create.
        when_iso = self._extract_when(text, now_iso)
        title = self._extract_title(text)
        if not title and not when_iso:
            return self._clarify(envelope, ["title", "when"], "What should I remind you about, and when?")
        if not title:
            return self._clarify(envelope, ["title"], "What should I remind you about?")
        if not when_iso:
            return self._clarify(envelope, ["when"], f"When should I remind you to {title}?")

        envelope.update(
            intent="create",
            title=title,
            when={"iso": when_iso, "timezone": timezone},
            confidence=0.8,
        )
        return envelope

    @staticmethod
    def _clarify(env: dict, missing: list[str], question: str) -> dict:
        env["intent"] = "clarify"
        env["missing_fields"] = missing
        env["clarification_question"] = question
        env["confidence"] = 0.5
        return env

    @staticmethod
    def _extract_when(text: str, now_iso: str) -> str | None:
        m = _REL_MIN_RE.search(text)
        if m:
            return _plus_minutes(now_iso, int(m.group(1)))
        m = _REL_HOUR_RE.search(text)
        if m:
            return _plus_minutes(now_iso, int(m.group(1)) * 60)
        m = _TOMORROW_TIME_RE.search(text)
        if m:
            h = int(m.group(1))
            mm = int(m.group(2) or 0)
            ampm = (m.group(3) or "").lower()
            if ampm == "pm" and h < 12:
                h += 12
            if ampm == "am" and h == 12:
                h = 0
            return _tomorrow_at(now_iso, h, mm)
        return None

    @staticmethod
    def _extract_title(text: str) -> str | None:
        m = re.search(r"remind\s+me\s+to\s+(.+?)(?:\s+(?:tomorrow|in|at|on|next|every|tonight)|$)", text, re.I)
        if m:
            return m.group(1).strip().rstrip(".!? ")
        m = re.search(r"remind\s+me\s+about\s+(.+?)(?:\s+(?:tomorrow|in|at|on|next|every|tonight)|$)", text, re.I)
        if m:
            return m.group(1).strip().rstrip(".!? ")
        return None

    @staticmethod
    def _extract_reference(text: str) -> str | None:
        m = re.search(r"\b(?:my|the|that)\s+([\w\s:-]+?)(?:\s+(?:to|for|at|on)|$)", text, re.I)
        if m:
            return m.group(1).strip().rstrip(".!? ")
        return None


def build(backend_name: str) -> Backend:
    if backend_name == "real":
        return RealBackend()
    if backend_name == "mock":
        return MockBackend()
    raise ValueError(f"unknown backend: {backend_name!r}")
