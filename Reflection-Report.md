# Assignment 1 — Reflection Report

## Student details

| Field | Value |
|---|---|
| Name | Sasank Valluri |
| Student ID | *(fill in)* |
| Email | aga4code@gmail.com |
| GitHub repository | https://github.com/sasankvalluri/ai-sdlc-assignment-1 |
| Demonstration video | *(paste Drive/OneDrive link here)* |

---

## Part 1A — Problem statement

I picked the Smart Todo CLI option. It's a small single-user command-line
tool that stores tasks in a JSON file, lets me add/list/update/delete
tasks, filter by tag or status, and move a task through a status
lifecycle (pending → in_progress → done or cancelled). Everything is
intended to be deterministic — same input state, same command, same
output — which made it a good fit for a strict harness with lint, SAST,
unit tests and coverage.

## Part 1B — Problem statement

For the non-deterministic part I built a Natural-Language Reminder
Agent. It takes a sentence like *"remind me to call mom tomorrow at 5pm"*
or *"snooze that meeting 15 min"* and turns it into a typed JSON object
a downstream scheduler could consume. The wording of the output is left
to the model; the shape and the invariants are fixed. The eval harness
has three layers — a schema check, intent-conditional invariants
(including safety rules like "no past dates for create"), and a
rule-based semantic rubric — and runs over a dataset of 17 cases
covering normal input, boundaries, ambiguous requests, missing info,
malformed input and adversarial prompts.

---

## Reflection answers

### Q1. Specification influence

One decision that came directly out of a Spec-Kit artifact: the strict
state machine for task status transitions in Part 1A. During the
clarify step I had to answer whether `done → done` should be
idempotent. It felt tempting to just make it a no-op, but the clarify
entry (C-01) ended up saying no — hiding a repeated completion would
also hide an upstream bug. That wording then shaped two things in the
code: the `ALLOWED_TRANSITIONS` table in `models.py` maps `Status.DONE`
to an empty set, and there's a test in `test_transitions.py`
(`test_a_005_3_done_to_done_is_illegal`) that specifically exercises
A-005.3 and expects exit code 1. So the decision isn't hiding somewhere
in the implementation — you can trace it from the clarify entry
straight to the test name.

### Q2. Harness value in Part 1A

The one that got me was a default-argument capture bug. My `new_task`
and the three command functions had `id_factory=new_id` and
`clock=now_utc` as default parameters. When I read my own code I was
sure the test fixtures would work — they monkeypatch
`models.new_id` and `models.now_utc` on the module, and the code calls
those names. What I forgot is that Python binds default-argument values
at function-definition time, so the defaults held a frozen reference to
the original functions no matter what I patched later.

The harness run `20261107T173127Z` showed it clearly: three tests
expected id `0000…0001` and timestamp `2026-11-07T10:00:00Z`, and got
real UUIDs and real wall-clock values. The failing output in
`evidence/harness-run-20261107T173127Z.json` pointed straight at the
line. I'd probably have talked myself out of this one if I only
re-read the code; the harness was what forced me to look.

The fix was to switch the defaults to `None` and resolve
`new_id` / `now_utc` from the module namespace inside the function
body. The next run passed those three tests without changing the
assertions.

### Q3. Evaluating non-determinism in Part 1B

Case N01 from the dataset is a good example — input
*"Remind me to call mom tomorrow at 5pm"* with `now = 2026-11-07T10:00:00Z`
and `timezone = Asia/Kolkata`. Exact string matching would be useless
here: the model is free to write the title as `"call mom"`,
`"Call Mom"`, `"give mom a call"` or anything else that preserves the
intent. And the ISO time has one correct value but infinite ways to
describe it in prose.

I use three different checks for this one case:

- **Schema** — `when.iso` has to match the regex
  `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` (enforced by pydantic's
  `StringConstraints`). Anything else fails L1.
- **Invariant** — the dataset says the correct answer falls in
  `[2026-11-08T10:00:00Z, 2026-11-08T13:00:00Z]`. That window is 5pm
  Asia/Kolkata (which is 11:30 UTC) with some slack. If the model
  treats "5pm" as UTC or slips a day, L2 flags it immediately — which
  is actually how I caught the mock backend's timezone bug on the first
  run.
- **Semantic rubric** — the dataset lists `title_must_contain: ["call",
  "mom"]`. Any wording that keeps both words passes, case-insensitive.

Each layer catches a different class of failure (shape, arithmetic,
content). None of them need the model to produce a specific string.

### Q4. Feedback and self-healing

Run `20261107T174613Z` in Part 1B is a real one. Every case came back
with `KeyError('"intent"')` from the OpenAI client. I was confused for a
minute — the schema looked right, the code looked right. The harness
eval record held the smoking gun: the failure happened inside
`prompt.py` before the HTTP call, not on the response.

The cause was that I'd built the system prompt with Python's
`str.format()`, substituting `{now}` and `{timezone}`. Inside the prompt
body I had JSON examples like `{"intent":"clarify", ...}`. Python's
`.format()` doesn't know the difference between my placeholders and the
JSON — it saw `{"intent"...` and tried to look up a key called
`"intent"` in my kwargs. KeyError.

Fix was small: switch `prompt.py` to `string.Template` and change the
placeholders in `prompts/system.md` from `{now}` to `$now`. You can see
the repair in the prompt hash — it changes from `2ddcc99f8c9d64cf` to
`59430683da5356d8` across the eval records.

Nothing in the spec, dataset or threshold moved — the prompt still has
the same examples, still substitutes the runtime time and timezone.

### Q5. Human accountability

The honest limitation is that the aggregate PASS I have on record for
Part 1B is a mock-backend run. The mock parser is deterministic by
design — it verifies the harness pipeline works end-to-end, but it
doesn't exercise the actual non-deterministic behaviour of an LLM. In
`evidence/harness-log.md` I called it a **CONDITIONAL ACCEPT** for that
reason.

The real-backend runs I attempted during development ran into
infrastructure problems — first a prompt-format bug (fixed in Run 2),
then the GitHub Models endpoint returning bare `OK\r\n` on every path
regardless of token, then Groq rejecting my default model name because
my free-tier account didn't have access to it. Each of those is
documented in the harness log, and the code now supports
`--backend groq` with a `GROQ_MODEL` override so the real-backend run
can happen as soon as I have a working model id.

Before using this in anything like production I'd want three things:

1. A response cache keyed on `(prompt_hash, input, now, timezone)` so
   I can rerun evals without burning free-tier quota and so results are
   reproducible.
2. A retry wrapper around the model client so a transient 429 doesn't
   get counted as a spec violation.
3. A proper safety classifier in place of the keyword-based prompt
   injection check I'm using right now — `SAF4` catches the obvious
   "ignore previous instructions" phrasing but it wouldn't catch a
   paraphrase.

The ACCEPT decision is mine, and I'm comfortable with the CONDITIONAL
label — the harness itself is sound, the pipeline is sound, and the
only thing between now and an unconditional ACCEPT is one working
backend run with a model id my account can actually use.
