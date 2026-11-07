"""Orchestrator: build inputs, call backend, run Layer-1/Layer-2 validation."""

from __future__ import annotations

from dataclasses import dataclass, field

from .backends import Backend, BackendCall, build
from .prompt import prompt_hash
from .schema import ReminderResponse
from .validators import CheckResult, check_invariants, validate_schema


@dataclass
class AgentResult:
    input_text: str
    now_iso: str
    timezone: str
    call: BackendCall
    prompt_hash: str
    parsed: ReminderResponse | None
    l1: list[CheckResult] = field(default_factory=list)
    l2: list[CheckResult] = field(default_factory=list)

    @property
    def structural_ok(self) -> bool:
        return all(r.passed for r in self.l1)

    @property
    def invariants_ok(self) -> bool:
        return all(r.passed for r in self.l2)


class Agent:
    def __init__(self, backend: Backend | None = None, *, backend_name: str = "real") -> None:
        self._backend = backend if backend is not None else build(backend_name)

    def parse(self, *, text: str, now_iso: str, timezone: str = "UTC") -> AgentResult:
        call = self._backend.generate(text=text, now_iso=now_iso, timezone=timezone)
        parsed, l1 = validate_schema(call.raw_output)
        l2: list[CheckResult] = (
            check_invariants(parsed, now_iso=now_iso, input_text=text)
            if parsed is not None
            else []
        )
        return AgentResult(
            input_text=text,
            now_iso=now_iso,
            timezone=timezone,
            call=call,
            prompt_hash=prompt_hash(),
            parsed=parsed,
            l1=l1,
            l2=l2,
        )
