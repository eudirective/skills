# C27 abstract case-state and atomic-coverage engine

C27 provides a **non-sending, schema-limited multi-proceeding state and coverage tracker**. The registered 251 checks are discovery prompts, *not evidence of actually performed legal analysis*. Its main real-case workflow is **in-conversation, model-led**: read the user-provided record, maintain the proceeding/event/disclosure model, and show relevant gaps. The CLI exists only for fictional fixtures or abstract non-identifying categorical representations. Do not pass actual correspondence, names, concrete dates, locations, narratives, passport numbers, case numbers, or distinctive fact combinations to it. It is not privacy-certified and does not enable C6/C7/C17/C21 real-case intake.

Read `references/state-engine/check-registry.json` and maintain separately for **every proceeding**: claimed legal regime, authority classification when known, authority role, stage, lodging status, decisions versus notification, document operations, disclosure recipients, authority acknowledgment and actual reliance, authority's grounds/positions, deadline triggers, grievance events and links to other proceedings. Never infer official receipt or formal lodging merely from a submitted online form, an appointment, or documents shown.

**Per-response coverage:** select atomic checks by applicability to each proceeding; mark `assessed`, `partial`, `not_checked`, `not_applicable` (with reason), `blocked`, or `unavailable`. Separate checks done now from earlier work, and recheck dependent assessments after facts change. Do not mark synthetic-only functionality as executed on real applicant data. **No checked item means 'no legal problem' merely because it was not triggered.** The report should surface the material omissions and unresolved stage questions, but remain concise unless detailed checklist requested.

The script `scripts/c27_case_state.py` deterministically replays opaque categorical events and checks report structure:
```
python scripts/c27_case_state.py checklist
python scripts/c27_case_state.py inspect --input evaluations/fixtures/c27/multi-proceeding.json
python scripts/c27_case_state.py compare --previous evaluations/fixtures/c27/initial.json --input evaluations/fixtures/c27/multi-proceeding.json
python scripts/test_c27_case_state.py
```
`inspect --full` shows individual check dispositions. No local persistence or network calls are performed. The host model must not claim that script execution, source review or legal verification happened when it did not. No automatic cross-session memory or first-turn hook is promised.

### Procedural and documentary safeguards

* `lodgement_attempted`, `lodgement_disputed`, and `lodgement_confirmed` are distinct. Reported confirmation is less certain than a viewed official record.
* A disclosure is scoped to its recorded recipient. `sent`, transport delivery, receipt acknowledgment, content acknowledgment and actual reliance are separate states. Authority silence or an appointment is **not waiver** of competence or disclosure requirements.
* A document can be requested, shown, submitted, accepted, rejected, or returned independently of legal sufficiency.
* Decisions taken, decisions notified and service-date calculation are distinct. The CLI does not compute a legally operative deadline.
* A review/appeal/complaint is its own proceeding, optionally linked to a parent; the parent's legal status is never overwritten.
* Corrections preserve prior event history and re-run projections. A response's previous check assessment becomes stale when later proceeding events require reconsideration.
* Every check records its capability boundary. The registry includes model-guidance, synthetic-only and not-implemented classifications; no status asserts legal adjudication.
