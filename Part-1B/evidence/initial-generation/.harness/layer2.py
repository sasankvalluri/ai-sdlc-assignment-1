"""Layer 2 — intent-conditional + dataset-expected invariants.

Two groups of checks run here:

1. Agent-level invariants from `reminder_agent.validators.check_invariants`
   (C1..C7, SAF1, SAF4). These are intent-conditional guards and safety
   rules that must hold on **every** response regardless of the test
   case.

2. Dataset-case invariants derived from each case's `expect` block:
   `intent` matches, `requires` fields are populated, `time_window`
   contains `when.iso`, `target_refers_to` is a substring of
   `target_reference`, `missing_fields_contain` is a subset, and
   `safety: no_past_times` enforces the invariant for adversarial cases
   even when the agent legitimately clarifies.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import asdict, dataclass

from reminder_agent.schema import ReminderResponse
from reminder_agent.validators import CheckResult, check_invariants


@dataclass
class L2Report:
    passed: bool
    agent_invariants: list[dict]
    dataset_invariants: list[dict]


def _check(name: str, passed: bool, detail: str = "") -> CheckResult:
    return CheckResult(layer="L2D", name=name, passed=passed, detail=detail)


def _parse_iso(value: str) -> _dt.datetime:
    return _dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)


def evaluate(
    parsed: ReminderResponse,
    *,
    case: dict,
    now_iso: str,
    input_text: str,
) -> L2Report:
    agent_checks = check_invariants(parsed, now_iso=now_iso, input_text=input_text)

    expect = case["expect"]
    ds_checks: list[CheckResult] = []

    # 1. intent matches
    ds_checks.append(
        _check(
            "intent_matches_expected",
            parsed.intent.value == expect["intent"],
            f"got={parsed.intent.value} expected={expect['intent']}",
        )
    )

    # 2. required fields populated
    for req in expect.get("requires", []):
        if req == "title":
            ok = bool(parsed.title)
        elif req == "when":
            ok = parsed.when is not None
        elif req == "target_reference":
            ok = bool(parsed.target_reference)
        elif req == "snooze_minutes":
            ok = bool(parsed.snooze_minutes)
        elif req == "missing_fields":
            ok = bool(parsed.missing_fields)
        elif req == "clarification_question":
            ok = bool(parsed.clarification_question)
        else:
            ok = False
        ds_checks.append(_check(f"requires_{req}", ok))

    # 3. time window (optional)
    if "time_window" in expect and parsed.when is not None:
        lo, hi = (_parse_iso(expect["time_window"][0]), _parse_iso(expect["time_window"][1]))
        when_dt = _parse_iso(parsed.when.iso)
        ds_checks.append(
            _check(
                "when_within_window",
                lo <= when_dt <= hi,
                f"when={parsed.when.iso} window=[{expect['time_window'][0]}, {expect['time_window'][1]}]",
            )
        )

    # 4. target_refers_to substring (optional)
    if "target_refers_to" in expect:
        needle = expect["target_refers_to"].lower()
        hay = (parsed.target_reference or "").lower()
        ds_checks.append(
            _check(
                "target_reference_contains",
                needle in hay,
                f"needle={needle!r} hay={hay!r}",
            )
        )

    # 5. missing_fields superset (optional)
    if "missing_fields_contain" in expect:
        need = set(expect["missing_fields_contain"])
        have = set(parsed.missing_fields)
        ds_checks.append(
            _check(
                "missing_fields_contain",
                need.issubset(have),
                f"need={sorted(need)} have={sorted(have)}",
            )
        )

    # 6. snooze_minutes equals (optional)
    if "snooze_minutes_equals" in expect:
        ds_checks.append(
            _check(
                "snooze_minutes_equals",
                parsed.snooze_minutes == expect["snooze_minutes_equals"],
                f"got={parsed.snooze_minutes} expected={expect['snooze_minutes_equals']}",
            )
        )

    # 7. safety: no_past_times (optional, but critical for adversarial)
    if expect.get("safety") == "no_past_times":
        if parsed.when is not None:
            now_dt = _parse_iso(now_iso)
            when_dt = _parse_iso(parsed.when.iso)
            ds_checks.append(
                _check(
                    "safety_no_past_times",
                    when_dt > now_dt,
                    f"when={parsed.when.iso} now={now_iso}",
                )
            )
        else:
            ds_checks.append(_check("safety_no_past_times", True, "when is null"))

    all_checks = agent_checks + ds_checks
    return L2Report(
        passed=all(r.passed for r in all_checks),
        agent_invariants=[asdict(r) for r in agent_checks],
        dataset_invariants=[asdict(r) for r in ds_checks],
    )
