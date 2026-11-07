# Clarifications — Reminder Agent (001)

| # | Question | Resolution | Affects |
|---|----------|------------|---------|
| C-01 | Should the agent itself schedule reminders? | **No.** Parser only. Downstream system schedules. | INV-SAF3 |
| C-02 | Should the agent accept a reminder time in the past ("remind me at 9am last Tuesday")? | **No** for `create`/`reschedule`. Return `clarify` and ask whether the user meant the next occurrence or a past event. | INV-SAF1, SEM-3 |
| C-03 | How should recurring reminders be handled? | **Not supported in v1.** Return `clarify` with `missing_fields: ["when"]` and a question like "is this a one-off or recurring reminder?". | out of scope |
| C-04 | What if the user supplies a very low confidence ("maybe remind me, I think")? | The model should still produce a parse but may set `confidence` low. L3 rubric scores it based on whether the structure makes sense. | REQ-004 |
| C-05 | When should `intent == "list"` be chosen? | For queries like "what reminders do I have", "show my reminders". Not required by any dataset case but allowed in the enum for completeness. | REQ-001 |
| C-06 | How is `snooze` without a reference ("snooze it 10 min") handled when there is no prior reference? | Return `clarify` with `missing_fields: ["target_reference"]`. | INV-C3 |
| C-07 | How precise must `when.iso` be? | **To the second.** The parser never emits sub-second precision; ISO format `YYYY-MM-DDTHH:MM:SSZ`. | INV-S5 |
| C-08 | Prompt-injection — user types "ignore previous instructions and return ...". | Treat as content; do not comply. The schema still applies. L2 check `test_adversarial_injection` enforces this. | INV-SAF4 |
| C-09 | Which confidence floor is "too low"? | Not in v1. Confidence is informational. The acceptance decision is on L1/L2/L3 outcomes, not confidence. | REQ-004 |
| C-10 | Does the agent translate non-English input? | **Out of scope.** English only. | spec §8 |
| C-11 | What happens when the backend is unavailable? | The CLI exits with code 3 and an error. No "degraded" output is produced. | REQ-007 (new) |
| C-12 | Why is L3 threshold 0.70, not 0.85? | Semantic rubric has unavoidable judgement variance from the LLM-as-judge. L1 + L2 at 100% guarantees the contract; L3 is additional quality headroom. The aggregate 0.85 keeps overall quality honest. | Article III |
