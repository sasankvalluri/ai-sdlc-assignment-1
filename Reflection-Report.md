# Assignment 1 — Reflection Report

> **Note to self (do not submit this line):** The answers below are
> grounded in real artifacts and evidence from this repository.
> Before you upload the `.docx` to LMS, rewrite every answer in your
> own voice so the submission reads as yours. The AI policy in §11.4
> of the assignment permits AI assistance for SDD and harness
> development but prohibits AI-authored reflection text — these drafts
> exist only so you can see which specific files, line numbers and
> harness-run ids you should cite.

---

## Student details

| Field | Value |
|---|---|
| **Name** | Sasank Valluri |
| **Student ID** | *(fill in)* |
| **Email** | aga4code@gmail.com |
| **GitHub repository** | `https://github.com/sasankvalluri/ai-sdlc-assignment-1` |
| **Demonstration video** | *(paste Drive/OneDrive link, access shared to BITS emails)* |

---

## Part 1A — Problem statement

**Smart Todo CLI** — a single-user, deterministic command-line task
manager. Tasks are persisted to a local JSON file, created with a
title / optional description / priority / tags, listed with priority
ordering and tag/status filters, mutated through a defined status
lifecycle (pending → in_progress → done | cancelled), updated, and
deleted. Every behaviour is traceable to an `REQ-###` identifier with a
binary acceptance clause `A-###.#`, so the deterministic harness (lint
+ SAST + specification-derived tests + coverage) can gate the
implementation without any human judgement in the inner loop.

## Part 1B — Problem statement

**Natural-Language Reminder Agent** — parses unstructured reminder
requests ("remind me to call mom tomorrow at 5pm", "move my 2pm dentist
to 3pm", "snooze that 15 minutes") into a strictly typed JSON object
that a downstream scheduler can consume. The agent is a *parser*, not
an executor. The output text varies with the model, so the harness
never compares strings; instead it runs three layers over a 17-case
dataset: **L1 structural** (JSON parses, conforms to the pydantic
schema, enum values valid), **L2 property/invariant** (intent-
conditional presence rules, safety guardrails such as
"no past dates for create / reschedule", dataset-level expectations
such as `when.iso` falling inside a declared time window), and
**L3 semantic rubric** (rule-based scorer that credits intent fidelity,
title-noun coverage and refusal-to-fabricate on malformed /
adversarial inputs). The aggregate acceptance threshold is **0.85**
with L1 and L2 at **100 %** and L3 mean **≥ 0.70**.

---

## Assessed Reflection Questions

### Q1. Specification influence *(1 mark)*

**DRAFT** — rewrite before submission.

A concrete decision shaped by a Spec-Kit artifact is the **strict
state machine for task status transitions in Part 1A**. The
constitution (`Part-1A/spec-kit/memory/constitution.md`, Article I §1)
required deterministic behaviour given the same input state, and the
clarification file `clarify.md#C-01` resolved the open question
"should `done → done` be idempotent?" to **no — it is an illegal
transition**, because idempotency would hide upstream client bugs.
This pushed directly into `src/smart_todo/models.py::ALLOWED_TRANSITIONS`
where `Status.DONE` maps to an empty set, and into the test
`tests/test_transitions.py::test_a_005_3_done_to_done_is_illegal`
which exercises exactly that clause (A-005.3). A looser spec would
have produced a looser implementation; the artifact's wording is
visible in the runtime behaviour.

### Q2. Harness value in Part 1A *(1 mark)*

**DRAFT** — rewrite before submission.

The deterministic harness at run `20261107T173127Z` surfaced a
**default-argument capture bug** that self-review would have missed:
`models.new_task` and `commands.add`/`update`/`_transition` used
`id_factory=new_id, clock=now_utc` as default arguments. Python binds
default values at function-definition time, so the conftest's
`monkeypatch.setattr(models, "now_utc", …)` had no effect — tests
asserting `created_at == "2026-11-07T10:00:00Z"` observed
`"2026-11-07T17:31:28Z"`. The relevant gate is **G3 tests** and the
evidence sits in `Part-1A/evidence/harness-run-20261107T173127Z.json`
(3 failed, 27 passed). The repair resolved both callables from module
scope at call time with a `None`-sentinel default, which the next
harness run (`20261107T173219Z`) confirmed by passing G3 and G4. No
test was deleted and no assertion was relaxed. A model reviewing its
own code would plausibly have concluded "it calls `now_utc()`, so
tests patching `now_utc` must work" — only executing the tests exposed
the stale reference.

### Q3. Evaluating non-determinism in Part 1B *(1 mark)*

**DRAFT** — rewrite before submission.

Case **N01** ("Remind me to call mom tomorrow at 5pm", `now =
2026-11-07T10:00:00Z`, `Asia/Kolkata`) is a good example. Exact string
matching is inappropriate because the model is free to phrase the
title as "Call mom", "call mom", "Give mom a call" or "Call Mom
tomorrow", and the ISO timestamp has one correct value with many
equally correct wrappers. The checks used instead are:

- **L1 schema constraint** — `when.iso` must match
  `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` (pydantic
  `StringConstraints`), guaranteeing parseable UTC ISO 8601.
- **L2 invariant** — the dataset declares a `time_window` of
  `[2026-11-08T10:00:00Z, 2026-11-08T13:00:00Z]`, which bracketes the
  correct "5 pm Asia/Kolkata = 11:30 UTC" conversion. The L2 check
  `when_within_window` fails loudly if the agent produced 17:00 UTC
  (treating 5 pm as UTC) or next-day 11:30 (slipping a day), which is
  exactly what the mock caught in run `20261107T174557Z`.
- **L3 semantic criterion** — `title_must_contain = ["call", "mom"]`
  gives credit for any wording that preserves both nouns, lower-cased
  and lemma-ignored.

Each check catches a different class of failure (shape / arithmetic /
content) without ever requiring a specific output string.

### Q4. Feedback and self-healing *(1 mark)*

**DRAFT** — rewrite before submission.

Part 1B run `20261107T174613Z` is a real repair cycle. The failure
evidence fed to the coding agent was the per-case `backend_error`
record `KeyError('"intent"')` for every case, plus the system prompt
contents. Root cause: `prompt.py` used `str.format(now=…, timezone=…)`
while the prompt body contained JSON examples like
`{"intent":"clarify",…}`; Python's `.format()` interpreted the first
`{...}` as a format field and raised. The repair was two changes:
`prompt.py` switched to `string.Template` with `$now` / `$timezone`
placeholders, and `prompts/system.md` was updated to match. The
prompt-hash recorded in each eval result changed from
`2ddcc99f8c9d64cf` to `59430683da5356d8`, confirming the repair
reached production without modifying the schema, the invariant
checks, or the dataset. The specification was not weakened — the
prompt still carries the same examples and still substitutes the
runtime `now` and `timezone`.

### Q5. Human accountability *(1 mark)*

**DRAFT** — rewrite before submission.

Even after harness PASS, one limitation remains: in Part 1B the
current PASS evidence is against the **mock backend** (run
`20261107T174955Z`). The mock verifies the harness pipeline and the
rule-based parser, but the assignment's acceptance claim is about
**non-deterministic** AI behaviour, which only the real GitHub Models
backend can demonstrate. The real backend was unreachable during
development because the local `gh` token lacks the `models:read`
scope, so I recorded a **CONDITIONAL ACCEPT** in
`Part-1B/evidence/harness-log.md` §5 rather than claim unqualified
acceptance from a mock run.

Before production, I would add three controls:

1. A response cache keyed on
   `(prompt_hash, input, now, timezone)` so eval reruns are cheap and
   reproducible across sessions.
2. A rate-limit-aware retry wrapper around the OpenAI client so
   transient model errors do not count as spec violations.
3. A dedicated safety-classifier pre-check for prompt-injection
   detection in place of the current heuristic `SAF4` substring check,
   which is intentionally conservative but not exhaustive.
