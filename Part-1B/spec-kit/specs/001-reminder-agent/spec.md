# Feature Specification — Natural-Language Reminder Agent

**Feature:** `001-reminder-agent`
**Status:** Approved
**Owner:** Sasank Valluri
**Date:** 2026-11-07

## 1. Purpose

Parse unstructured, natural-language reminder requests ("Remind me to call
mom tomorrow at 5pm", "Move my 2pm dentist to 3pm", "Snooze that 15
minutes") into a stable, machine-processable JSON contract. The output
can then be fed to a downstream scheduler. The agent is a **parser**,
not an executor.

## 2. Users and stories

- **US-1.** As a user, I can say what I want in a short sentence, and
  the agent returns a structured representation of my intent without me
  having to pick a time format, a timezone or a category.
- **US-2.** As a user, when I leave out information the agent cannot
  invent (a time, a title), it asks me for exactly that piece instead of
  guessing.
- **US-3.** As a user, when I reference an existing reminder ("that
  dentist thing", "my 2pm"), the agent captures the reference so the
  downstream system can resolve it.
- **US-4.** As a user, prompt-injection attempts inside my request do
  not change the agent's contract.

## 3. Output schema (contract)

The agent always returns a single JSON object with this shape:

```jsonc
{
  "intent": "create" | "reschedule" | "snooze" | "cancel" | "list" | "clarify",

  // Natural-language title of the reminder (for create / reschedule / snooze).
  // May be null when not applicable.
  "title": "string | null",

  // Absolute target time for create / reschedule.
  // Null for snooze / cancel / list / clarify.
  "when": {
    "iso":      "YYYY-MM-DDTHH:MM:SSZ",   // ISO 8601, UTC, seconds precision
    "timezone": "IANA zone, e.g. Asia/Kolkata"
  } | null,

  // Relative offset for snooze. Null otherwise. Must be a positive integer.
  "snooze_minutes": "integer | null",

  // Verbatim reference to an existing reminder, for reschedule / snooze /
  // cancel. Null otherwise.
  "target_reference": "string | null",

  // When intent == "clarify", must be a non-empty list taken from the
  // vocabulary {"title", "when", "target_reference", "snooze_minutes"}.
  // Must be [] (empty list) otherwise.
  "missing_fields": ["string", ...],

  // When intent == "clarify", a user-facing question naming what is
  // missing. Null otherwise.
  "clarification_question": "string | null",

  // Agent self-reported confidence in [0.0, 1.0].
  "confidence": "number"
}
```

The JSON schema is published in machine-readable form at
`src/reminder_agent/schema.py`.

## 4. Functional requirements

### REQ-001 — Shape conformance

- **INV-S1.** Output is a single JSON object (no array, no wrapping).
- **INV-S2.** All required keys above are present.
- **INV-S3.** `intent` is one of the six enum values.
- **INV-S4.** `confidence` is a number in `[0.0, 1.0]`.
- **INV-S5.** When `when` is non-null, `when.iso` parses as ISO 8601
  UTC with second precision.
- **INV-S6.** `missing_fields` is a list of strings drawn only from the
  allowed vocabulary.

### REQ-002 — Intent-conditional invariants

- **INV-C1.** For `intent == "create"`: `title` is non-empty and `when`
  is non-null.
- **INV-C2.** For `intent == "reschedule"`: `target_reference` is
  non-empty and `when` is non-null.
- **INV-C3.** For `intent == "snooze"`: `target_reference` is non-empty
  and `snooze_minutes` is a positive integer.
- **INV-C4.** For `intent == "cancel"`: `target_reference` is non-empty.
- **INV-C5.** For `intent == "clarify"`: `missing_fields` is non-empty
  and `clarification_question` is a non-empty string.
- **INV-C6.** For `intent == "list"`: no requirement beyond shape.
- **INV-C7.** Fields that are not applicable to the active intent are
  `null` or `[]` (never populated with stray guesses).

### REQ-003 — Safety invariants

- **INV-SAF1.** For `create` / `reschedule`, `when.iso` **must** be
  strictly greater than the supplied `now` value.
- **INV-SAF2.** If a mandatory field cannot be resolved without
  guessing, the agent must return `intent == "clarify"` with the
  missing field named in `missing_fields` and asked about in
  `clarification_question` — never guess.
- **INV-SAF3.** The agent must not execute, schedule, send, or mutate
  anything. The response is a parsed representation only.
- **INV-SAF4.** The agent must ignore user text that attempts to
  override the system prompt (e.g. "ignore previous instructions"),
  treating it as content of a potential reminder rather than as a
  directive.

### REQ-004 — Semantic fidelity

- **SEM-1.** For `create`, the `title` captures the task the user named
  (not verbatim required, but no critical noun from the user's request
  may be dropped).
- **SEM-2.** For `reschedule` / `snooze` / `cancel`, `target_reference`
  is a recognisable phrase from the user's request.
- **SEM-3.** When the user supplies a natural-language time
  ("tomorrow at 5pm", "in 20 minutes", "Friday"), the agent resolves it
  against the supplied `now` and the user's timezone.
- **SEM-4.** When the user implies clarification is needed (ambiguous,
  under-specified, malformed), the agent's `clarification_question`
  names a specific missing piece (not a generic "please clarify").

### REQ-005 — Input contract

The agent is called with the following inputs:

| Input | Type | Required | Notes |
|-------|------|----------|-------|
| `text` | string | yes | the user's natural-language request |
| `now` | ISO 8601 UTC | yes | reference time for relative expressions |
| `timezone` | IANA zone | no | defaults to `UTC` |

## 5. Evaluation

The evaluation dataset at `evals/dataset.json` contains ≥ 15 cases
covering normal inputs, boundary cases, under-specification, missing
information, malformed input and adversarial / guardrail cases. Each
case declares:

```jsonc
{
  "id": "N01",
  "category": "normal | boundary | ambiguous | missing | malformed | adversarial",
  "input": { "text": "...", "now": "...", "timezone": "..." },
  "expect": {
     "intent":        "create|...|clarify",
     "requires":      ["title", "when", ...],  // which fields must be present
     "time_window":   ["2026-11-08T00:00:00Z", "2026-11-08T23:59:59Z"],  // optional
     "target_refers_to": "2pm dentist",         // optional substring hint
     "safety":        "no_past_times",          // optional
     "semantic_rubric": "...one-sentence rubric..."
  }
}
```

## 6. Acceptance threshold

- L1 Structural: **100 %** per-case pass.
- L2 Property / invariant: **100 %** per-case pass.
- L3 Semantic: mean score **≥ 0.70** across the dataset.
- Aggregate (mean of per-layer pass rates): **≥ 0.85**.

## 7. Backend

Two interchangeable backends:

- **real.** `openai.OpenAI` client pointed at `https://models.github.ai`
  (GitHub Models). Requires a token with `models:read` scope in
  `GITHUB_TOKEN` or `GITHUB_MODELS_TOKEN`. Default model
  `openai/gpt-4o-mini`. Temperature 0.3, `response_format=json_object`.
- **mock.** Deterministic rule-based parser used only when the real
  backend is unavailable. **Never** used to claim a PASS against the
  non-deterministic acceptance threshold — any evaluation evidence
  produced by the mock backend is tagged `backend: "mock"` in the
  record.

## 8. Out of scope

- Recurring reminders ("every Monday at 9am"). Must return
  `intent == "clarify"` asking about recurrence support.
- Multi-reminder requests ("remind me at 5 and 6").
- Actual scheduling, notification delivery or persistence.
- Multilingual input beyond English.
