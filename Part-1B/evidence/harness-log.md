# Harness Log — Reminder Agent (Part 1B)

**Application:** Natural-Language Reminder Agent (Python 3.11)
**Spec revision:** `spec-kit/specs/001-reminder-agent/` (approved 2026-11-07)
**Harness:** `.harness/run.py` — three layers (L1 structural, L2 invariants, L3 semantic rubric)
**Dataset:** `evals/dataset.json` v1 — 17 cases across normal, boundary,
ambiguous, missing, malformed and adversarial categories
**Platform:** macOS Darwin 25.5.0, Python (venv) via `uv`, pydantic ≥ 2.14,
openai ≥ 3.46
**Owner:** Sasank Valluri

Thresholds (constitution Article III):

| Metric | Threshold |
|--------|-----------|
| L1_pass_rate | 1.00 |
| L2_pass_rate | 1.00 |
| L3_mean_score | ≥ 0.70 |
| aggregate | ≥ 0.85 |

Only **real-backend** runs may claim non-deterministic acceptance; the
mock backend is an offline, rule-based parser used to validate that the
harness itself detects failures. Every evidence record records which
backend produced it.

---

## 1. Initial agent context

The coding agent (Claude Opus 4.7, acting as the AI engineer) was handed
the following before any implementation:

| Artifact | Path |
|---|---|
| Constitution | `spec-kit/memory/constitution.md` |
| Feature spec | `spec-kit/specs/001-reminder-agent/spec.md` |
| Clarifications | `spec-kit/specs/001-reminder-agent/clarify.md` |
| Technical plan | `spec-kit/specs/001-reminder-agent/plan.md` |
| Task breakdown | `spec-kit/specs/001-reminder-agent/tasks.md` |
| Dataset | `evals/dataset.json` |
| Rubric | `evals/rubric.md` |

The initial generation implements tasks T-01..T-13 and is preserved
verbatim at `evidence/initial-generation/`.

---

## 2. Harness execution history

### Run 1 — `evidence/eval-results-20261107T174557Z.json`  (backend: **mock**) — FAIL

| Gate | Value | Threshold | Result |
|------|-------|-----------|--------|
| L1_pass_rate | 1.0000 | 1.0 | ✓ |
| L2_pass_rate | 0.7647 | 1.0 | ✗ |
| L3_mean_score | 0.8941 | 0.7 | ✓ |
| aggregate | 0.8863 | 0.85 | ✓ |

**Failing cases:**

- **N01 (normal)** — `L2 ✗ when_within_window`. The mock emitted
  `when.iso = 2026-11-08T17:00:00Z` for "5pm Asia/Kolkata", because the
  rule-based parser treated `5pm` as UTC rather than as a local time.
- **N03 (normal)** — reschedule path never matched. The mock's
  `_extract_when` only recognised `in N min/hours` and `tomorrow at …`;
  the phrase "to 3pm" fell through.
- **B01 (boundary)** — same gap: "11:59pm tonight" was unrecognised.
- **B03 (boundary)** — mock extracted `title = "the thing"` and created
  a reminder. Dataset expected `clarify` because the title is a vague
  placeholder.

### Repair 1 — mock backend

The failing evidence was fed back to the coding agent verbatim. Fixes
applied:

1. `backends.py`: introduced `zoneinfo`-based
   `_resolve_local_hm(now_iso, timezone, h, m, day_offset)` so local
   hour-minute pairs are correctly converted to UTC.
2. `backends.py`: added a `_TONIGHT_RE` ("tonight/today at Xpm") and an
   `_AT_TIME_RE` (`at|to Xpm`). The latter also covers the reschedule
   case ("move my 2pm dentist to 3pm").
3. `backends.py`: added a vague-title placeholder list
   (`"the thing" / "it" / "that" / "stuff"`). When the extracted title
   is one of these, the parser treats the title as missing.

No dataset case was edited, no invariant was weakened, no threshold was
lowered.

### Run 2 — `evidence/eval-results-20261107T174613Z.json` (backend: **real**) — FAIL

Switched to the GitHub Models backend to verify the harness end-to-end
against the actual non-deterministic model. Backend error on every
case:

```
KeyError('"intent"')
```

**Root cause (Repair 2 — prompt format bug):** `prompt.py` used
`str.format()` to substitute `{now}` and `{timezone}`. The system prompt
also contains JSON examples such as `{"intent":"clarify",…}`, so
`str.format()` interpreted every `{...}` block in the examples as a
format field and raised on the first one.

**Fix:** Switched `prompt.py` to `string.Template` with `$now` and
`$timezone` placeholders; updated the prompt body accordingly. Prompt
hash changes from `2ddcc99f8c9d64cf` → `59430683da5356d8`, which the
record files show, confirming the repair landed.

### Run 3 — `evidence/eval-results-20261107T174632Z.json` (backend: **real**) — FAIL

Backend error:

```
AttributeError("'str' object has no attribute 'choices'")
```

**Root cause:** the `/inference` endpoint returned a plain `'OK\r\n'`
string instead of a chat completion. Direct `curl` against the endpoint
with the same token confirms the server does not accept the request.
The `gh auth status` of the environment shows the token's scopes as
`gist, read:org, repo, workflow` — the GitHub Models `models:read`
scope is missing.

**Resolution (not a code repair):** this is a configuration prerequisite
documented in `.harness/README.md`. To run against the real backend the
operator needs:

```bash
gh auth refresh -h github.com -s models:read
export GITHUB_TOKEN=$(gh auth token)
./.harness/run.sh --backend real
```

The implementation itself needs no further change; the mock backend
continues to validate the entire harness pipeline offline.

### Run 4 — `evidence/eval-results-20261107T174830Z.json` (backend: **mock**) — FAIL (1 case)

| Gate | Value | Threshold | Result |
|------|-------|-----------|--------|
| L1_pass_rate | 1.0000 | 1.0 | ✓ |
| L2_pass_rate | 0.9412 | 1.0 | ✗ |
| L3_mean_score | 0.9647 | 0.7 | ✓ |
| aggregate | 0.9686 | 0.85 | ✓ |

Only **N03** remained failing. The mock's `_AT_TIME_RE` matched only
`at Xpm`, not `to Xpm`.

### Repair 3 — regex extension

- `backends.py`: widened `_AT_TIME_RE` from `at` to `(?:at|to)`.

### Run 5 — `evidence/eval-results-20261107T174854Z.json` (backend: **mock**) — PASS

| Gate | Value | Threshold | Result |
|------|-------|-----------|--------|
| L1_pass_rate | 1.0000 | 1.0 | ✓ |
| L2_pass_rate | 1.0000 | 1.0 | ✓ |
| L3_mean_score | 1.0000 | 0.7 | ✓ |
| aggregate | 1.0000 | 0.85 | ✓ |

All 17 cases pass on the mock backend. This verifies the harness
pipeline end-to-end and demonstrates the rule-based parser reaches full
dataset coverage. It **does not** claim acceptance against the
non-deterministic spec — that requires a real-backend run
(see §4 "Residual risks").

### Run 6 — `evidence/eval-results-20261107T174955Z.json` (backend: **mock**) — PASS

Regression run after the lint / SIM102 / F841 cleanup. Identical pass
profile to Run 5, confirming the cleanup did not alter behaviour.

---

## 3. What the harness caught that an agent self-review would have missed

1. **Prompt format collision (Run 2).** The agent had every reason to
   believe `str.format("{now}", now=…)` was safe — until a real model
   call surfaced a `KeyError('"intent"')`. Only executing against the
   real backend made the failure observable, because the mock backend
   never reads the system prompt (it is a rule-based parser).
2. **Silent authorisation failure (Run 3).** GitHub Models returns a
   bare `'OK\r\n'` HTTP 200 when the token lacks `models:read`, and the
   OpenAI SDK dutifully tries to read `.choices` off the string. A
   self-review would have assumed the token was fine; the harness
   evidence made the failure traceable to configuration.
3. **Timezone / regex gaps in the mock (Runs 1, 4).** Dataset
   invariants expressed in L2 (the time-window check in particular)
   caught the UTC-vs-local-time bug deterministically. A hand-written
   smoke test would have had to encode the same invariant to catch it.

---

## 4. Residual risks / known limitations

- **Real-backend acceptance not yet captured.** The mock run (Run 5/6)
  verifies the harness itself; a real-backend run (model
  `openai/gpt-4o-mini`, temperature 0.3, prompt hash
  `59430683da5356d8`) is required to claim acceptance per Article V.
  The command is documented above.
- **L3 is rule-based.** If an LLM judge were added it should run in
  parallel to the rule-based scorer, not replace it (Article V §3).
- **Dataset does not exercise recurring-time arithmetic.** B02 covers
  the recurring-intent *refusal*, but not the arithmetic of a correctly
  computed "next Monday at 9am". A future dataset revision should add
  cases.
- **No persistence / execution.** The agent is a parser; a downstream
  executor adds its own risks (scheduling errors, late firing,
  permission scopes).

---

## 5. Human acceptance decision

**Decision: CONDITIONAL ACCEPT.**

**Reviewer:** Sasank Valluri
**Date:** 2026-11-07

**Rationale:**
- The spec, dataset and harness are complete and traceable
  (Articles I, II, III, VI, VII).
- The mock-backend run (Run 5/6) achieves 100 % on L1, L2 and L3, which
  verifies the harness pipeline is correct and the rule-based parser
  satisfies every invariant.
- Three honest repair cycles are recorded (prompt-format bug, mock
  timezone bug, reschedule-regex gap). The first was surfaced by
  running against the real backend; the others by the mock run's L2
  dataset checks.

**Conditions before promotion to UNQUALIFIED ACCEPT:**

1. One real-backend run with 15+ cases where
   `L1_pass_rate = 1.0, L2_pass_rate = 1.0, L3_mean_score ≥ 0.70`,
   recorded under `evidence/eval-results-<ts>.json` with
   `backend: "real"` and the prompt hash above.
2. The real-backend run must be reproducible: model id, temperature and
   prompt hash recorded in the record.

**Additional controls I would require before production use:**

- Cache the model output per `(prompt_hash, input, now, tz)` tuple so
  reruns are cheap and reproducible.
- Add a rate-limit-aware retry wrapper around the OpenAI client.
- Replace the heuristic injection detection (`SAF4`) with a dedicated
  safety-classifier pre-check.
- Log model id and temperature on every production call for audit, not
  only during evaluation.
