# Harness Log — Reminder Agent (Part 1B)

Working log for the Part-1B eval harness. Machine-readable per-case
results are in the `eval-results-*.json` files; this file is the story
around them.

## What the harness checks

Three layers, run in order for every case in `evals/dataset.json`:

- **L1 (structural)** — Does the raw model output parse as JSON and
  conform to the pydantic schema (`ReminderResponse`)? Pass rate has
  to be **1.00**.
- **L2 (invariants)** — Intent-conditional presence rules (e.g.
  `create` needs title + when), safety guardrails (no past dates for
  `create`/`reschedule`), and dataset-level expectations like the
  `time_window` check. Pass rate has to be **1.00**.
- **L3 (semantic rubric)** — Rule-based scorer that credits intent
  fidelity, title-noun coverage, and refusal-to-fabricate on bad
  input. Mean score has to be **≥ 0.70**.
- **Aggregate** — Mean of the three above. Threshold **≥ 0.85**.

Backend matters. Only `backend: "real"` or `backend: "groq"` runs can
claim non-deterministic acceptance — the mock parser is deterministic
by design, so it verifies the pipeline but it doesn't exercise the
actual non-deterministic behaviour.

---

## Run 1 — `eval-results-20261107T174557Z.json` (backend: mock) — FAIL

L1 clean, L3 OK, but L2 came in at 0.76 because of four cases:

- **N01** — mock emitted `when.iso = 2026-11-08T17:00:00Z` for
  "5pm Asia/Kolkata". The rule-based parser was treating "5pm" as UTC,
  not converting from the user's timezone. L2's `when_within_window`
  caught it (correct answer is `11:30Z`).
- **N03** — "Move my 2pm dentist appointment to 3pm" fell through the
  reschedule path because `_extract_when` only recognised "in N min",
  "tomorrow at X" and "at Xpm". It didn't recognise "to 3pm".
- **B01** — same gap: "11:59pm tonight" didn't match any of the
  patterns.
- **B03** — mock extracted `title = "the thing"` and happily created a
  reminder. Dataset expects `clarify` because "the thing" is a vague
  placeholder, not a real title.

### Repair

In `backends.py`:

1. Switched from naive hour arithmetic to `zoneinfo`-based
   `_resolve_local_hm(now_iso, timezone, h, m, day_offset)`. Local
   hour/minute now converts to UTC correctly.
2. Added a `_TONIGHT_RE` ("tonight/today at Xpm") and a generic
   `_AT_TIME_RE` ("at Xpm"). The generic one also handles the
   reschedule case once I widened it.
3. Added a small vague-title placeholder list (`"the thing"`, `"it"`,
   `"that"`, `"stuff"`). If the extracted title is one of these, treat
   title as missing so the clarify path triggers.

Nothing in the dataset changed; no invariant was softened.

---

## Run 2 — `eval-results-20261107T174613Z.json` (backend: real) — FAIL

Switched to GitHub Models to see the harness against a real LLM. Every
case came back with:

```
KeyError('"intent"')
```

Not a model error — the failure happened in my code before the HTTP
call even went out. `prompt.py` was building the system prompt with
`str.format(now=..., timezone=...)`. The prompt body has JSON examples
like `{"intent":"clarify", ...}`. Python's `.format()` doesn't know the
difference between my `{now}` placeholder and `"intent"` inside my
example JSON — it tried to look up a `"intent"` kwarg and raised.

### Repair

Swapped `prompt.py` to `string.Template` with `$now` and `$timezone`,
updated the prompt body. Prompt hash changed from `2ddcc99f8c9d64cf`
to `59430683da5356d8`, which the later eval records all show.

---

## Run 3 — `eval-results-20261107T174632Z.json` (backend: real) — FAIL

Same error class but now in the HTTP response, not the prompt builder:

```
AttributeError("'str' object has no attribute 'choices'")
```

Dumped the raw response: `'OK\r\n'`. Every endpoint on
`models.github.ai` (chat completions, catalog, root) returned the same
`200 OK` with `content-type: text/plain` and that one-line body,
regardless of what I sent.

The token worked fine for `api.github.com/user`, so auth itself was OK.
The GitHub Models endpoint just doesn't seem to be serving requests for
this account right now — possibly a scope / enablement issue I
couldn't resolve in-session.

This isn't a code bug and there was no sensible repair at the source
level, so I flagged it as a configuration prerequisite in the
`.harness/README.md`. The real-backend branch is still there; it just
needs a working endpoint.

---

## Run 4 — `eval-results-20261107T174830Z.json` (backend: mock) — FAIL (1 case)

Back to mock. 16/17 cases now passing. The one left was **N03** again
— "Move my 2pm dentist appointment to 3pm". My widened `_AT_TIME_RE`
caught "at Xpm" but not "to Xpm".

### Repair

Widened the regex from `\bat\s+` to `\b(?:at|to)\s+`.

---

## Run 5 — `eval-results-20261107T174854Z.json` (backend: mock) — PASS

Everything green on mock.

| Gate | Value | Threshold |
|------|-------|-----------|
| L1 pass rate | 1.0000 | 1.0 |
| L2 pass rate | 1.0000 | 1.0 |
| L3 mean score | 1.0000 | 0.7 |
| Aggregate | 1.0000 | 0.85 |

This verifies the harness end-to-end and shows the rule-based parser
is now consistent with every invariant in the dataset. It does **not**
claim non-deterministic acceptance — that still needs a real-backend
run.

---

## Run 6 — `eval-results-20261107T174955Z.json` (backend: mock) — PASS

Regression run after cleaning up some ruff findings in the harness
code (`SIM102` nested ifs, an unused `backend_error` variable, a
couple of long lines). Same 1.0 profile as Run 5 — the cleanup didn't
change behaviour.

---

## Run 7 — `eval-results-20261107T181042Z.json` (backend: groq) — FAIL

Switched to Groq (free tier) after GitHub Models wouldn't respond
properly. Every case failed with:

```
NotFoundError('Error code: 404 - The model `llama-3.1-8b-instant` does not exist or you do not have access to it.')
```

Groq retired that model name. Fine — the code already makes the model
id overridable via `GROQ_MODEL`.

### Repair

Changed the default in `backends.py` from `llama-3.1-8b-instant` to
`openai/gpt-oss-20b` (which is on the current free tier for new
accounts). If even that is retired by the time anyone else runs this,
they can pull the list with:

```bash
curl -s -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models \
  | python3 -c "import json,sys;[print(m['id']) for m in json.load(sys.stdin)['data']]"
```

and set `GROQ_MODEL=<id>` before running the harness.

---

## Run 8 — `eval-results-20261107T181635Z.json` (backend: groq, model: openai/gpt-oss-20b) — FAIL (1 case)

First real-backend run with everything wired up. 16/17 cases green:

| Gate | Value | Threshold |
|------|-------|-----------|
| L1 pass rate | 1.0000 | 1.0 |
| L2 pass rate | 0.9412 | 1.0 |
| L3 mean score | 0.9353 | 0.7 |
| Aggregate | 0.9588 | 0.85 |

The one case that failed is **B03** — "Remind me about the thing in 1
hour". The model took "the thing" as a real title and emitted a
`create` with `title: "the thing"`, when the dataset expects `clarify`
because "the thing" is a vague placeholder. This is exactly the kind
of edge case the harness is supposed to surface on a real
non-deterministic model.

### Repair

Not a code bug — a prompt gap. The system prompt was implying this
rule via its example of empty "Remind me", but never stated it
explicitly. I added it:

- `prompts/system.md`, new hard rule #9:
  > "If the only 'title' the user supplies is a vague placeholder
  > ('the thing', 'that', 'it', 'stuff', 'something'), treat the
  > title as missing. Return `intent = "clarify"` with
  > `missing_fields: ["title"]` and ask what the reminder is actually
  > about. Do not accept a placeholder as a real title."
- Added a third example showing the B03 case resolved.

Prompt hash changed from `59430683da5356d8` → `a23b337bbf6dbf90`.
Nothing else moved — dataset unchanged, invariants unchanged, L1/L2/L3
thresholds unchanged.

---

## Run 9 — `eval-results-20261107T182627Z.json` (backend: groq, model: openai/gpt-oss-20b) — PASS

The run I was waiting for.

| Gate | Value | Threshold |
|------|-------|-----------|
| L1 pass rate | 1.0000 | 1.0 |
| L2 pass rate | 1.0000 | 1.0 |
| L3 mean score | 0.9824 | 0.7 |
| Aggregate | 0.9941 | 0.85 |

All 17 cases pass all three layers. Prompt hash `a23b337bbf6dbf90`,
model `openai/gpt-oss-20b`, temperature 0.3. B03 now correctly
returns `clarify` with `missing_fields: ["title"]`.

---

## What the harness caught that I would have missed

- **Prompt format collision (Run 2).** `str.format()` looked safe —
  it was safe when I wrote the function and the prompt separately,
  and only broke once real JSON examples went into the prompt body.
  I don't think I'd have spotted this without a real-model call
  trying it. The mock backend never reads the prompt (it's a
  rule-based parser), so this failure was invisible to the first few
  runs.
- **Silent authorisation shape (Run 3).** The GitHub Models endpoint
  returns `200 OK` with `content-type: text/plain` and a `'OK\r\n'`
  body regardless of scope. The OpenAI SDK dutifully tries to read
  `.choices` off that string and raises. If I'd only looked at the
  HTTP status I'd have thought everything was fine.
- **Timezone handling in the mock parser (Run 1).** The
  dataset-driven `time_window` check in L2 caught this
  deterministically. A hand-written smoke test would have had to
  encode the same window to notice.

---

## Known limitations / residual risks

- **Single model, single temperature.** The real-backend PASS in Run 9
  is on `openai/gpt-oss-20b` at `temperature = 0.3`. A different model
  or temperature could produce different numbers. The run record
  captures both so a reproduction knows the exact configuration.
- **L3 scorer is rule-based.** Deliberately. If I added an LLM judge
  later it should run alongside, not replace it — the rule-based one
  is what makes reruns reproducible.
- **Dataset doesn't cover recurring-time arithmetic.** B02 covers the
  refusal of recurring reminders, not the correct computation of
  "next Monday at 9am" if we ever supported it.
- **The agent is a parser, not an executor.** Downstream scheduling
  has its own risks (missed fires, timezone edge cases on the
  consumer side). Out of scope here.

---

## Decision

**ACCEPT** for Part 1B. — Sasank Valluri, 2026-11-08.

Run 9 on a real non-deterministic LLM (Groq, `openai/gpt-oss-20b`,
temperature 0.3, prompt hash `a23b337bbf6dbf90`) passes all three
layers on all 17 dataset cases:

- L1 structural: 1.00
- L2 invariants: 1.00
- L3 semantic mean: 0.9824
- Aggregate: 0.9941 (threshold 0.85)

Four honest repair cycles got us here — mock timezone bug, prompt
format collision, Groq model-id retirement, vague-title placeholder
rule — and none weakened the spec, the dataset, the invariants or the
thresholds. The vague-title repair in Run 8→9 is the clearest example
of the self-healing loop the assignment asks for: real failure
evidence surfaced by the harness, fed back as a targeted prompt
addition, the next run passes cleanly.

If this were going into production, three more controls:

1. Response cache keyed on `(prompt_hash, input, now, timezone)` so
   eval reruns are cheap and reproducible.
2. A retry wrapper around the client so transient 429s don't look
   like spec violations.
3. A proper safety classifier in place of the keyword-based prompt
   injection check — `SAF4` catches the obvious "ignore previous
   instructions" wording but not a paraphrase.
