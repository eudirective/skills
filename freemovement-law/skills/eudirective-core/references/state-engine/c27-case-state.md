# C27 — case state, disclosures, and atomic check coverage

**Version:** 0.2; used by eudirective-core v0.50.0. The registry contains **301 individual checks in 23 families**, including 36 individually indexed adapted stratagem screens and 14 legal-principle screens. A catalogue entry is a prompt for review, **not evidence of completed analysis**.

## Normal applicant guidance: in-conversation, read-only

Before every substantive reply, reconstruct **each separate proceeding** (visa, residence, border, appeal, staff complaint, file access, GDPR access) with its applicant-claimed versus authority-classified type, current and historical stage, attributed facts, documents shown or submitted, prior applicant communications and specific recipients, official positions, evidence conflicts, deadlines and requested remedies. Distinguish an enquiry, appointment, online form, attempted submission, confirmed formal lodging, decision, notification, appeal and closure. Track stage changes without rewriting independent rights or grievances.

Use the atomic check registry `references/state-engine/check-registry.json` and explicitly decide which checks are relevant. An untriggered check means **not indicated by the current structured signals**, not legally inapplicable. Mark a check as assessed only when the particular issue was considered and the source, evidence or reason can be named. Model assessment, checked source material and executed Python code must not be conflated.

For a normal answer, lead with the requested guidance and end with a concise coverage summary. When jurisdiction roles, proceeding or stage, material facts, source consultation, module availability/conformance or execution changes, state which relevant modules informed this answer, which were used earlier in this chat, and which relevant modules were not used. For every partly reviewed item, name what is missing and how it limits the assessment. Keep model/source review distinct from engine/validator/retrieval execution. After each explicit FreeMovement invocation, refresh the compact consultation dashboard; it is also required when the user requests a dashboard or audit. An implicit continuation may omit it unless material assessment or module/source use changes. See `references/consultation-routing.md` for trigger and source-ledger rules. For a requested expanded audit, use the proceeding-grouped display in that reference; preserve each recorded C27 scope and check IDs, status, method, evidence/source references, reason, and exact `scope_exclusion` value when present. Prioritize lodging, deadlines, prior disclosures and independent grievances.

Provide the 301-entry expanded checklist on request. Never manufacture exact counts of completed checks in a real case merely because instructions were read. Do not claim host execution, persistence, source live verification or independent legal-semantic validation without actual evidence.

## Abstract deterministic CLI

`scripts/c27_case_state.py` accepts **fictional fixtures or deliberately abstract, non-identifying categorical representations only**. Do not send real applicant correspondence, names, passport numbers, precise dates, geographic combinations or raw narratives into it. Caller-selected `mode=abstract_nonidentifying` does not guarantee anonymisation. The CLI has no outbound network calls, sending, private-case storage, live law checks or deadline calculation. It does not unlock C6/C7/C17/C21 private-case engine restrictions.

```bash
python scripts/c27_case_state.py checklist
python scripts/c27_case_state.py inspect --input evaluations/fixtures/c27/multi-proceeding.json
python scripts/c27_case_state.py inspect --full --input evaluations/fixtures/c27/multi-proceeding.json
python scripts/c27_case_state.py compare --previous evaluations/fixtures/c27/initial.json --input evaluations/fixtures/c27/multi-proceeding.json
python scripts/test_c27_case_state.py
```

Input schemas `c27-abstract-session/0.1.0` and `0.2.0` are accepted; output schema is `c27-case-state-report/0.2.0`. `requested_focus` adds deliberately selected triggers, notably `stratagem` (36 screens), `legal_principle` (14), `soft_law`, `strategy` and `disclosure`. Model-led catalog screens **do not execute** the C5e synthetic scripts. Reported assessed checks require event/source references, while restricted or unimplemented capabilities cannot be marked assessed. The status and sources are still **self-reported and schema-checked**, not independently authenticated.

## Historical and evidentiary safeguards

- **Two distinct event orders:** append position tracks when information entered the abstract case; optional `occurred_order` is an opaque relative chronology. A late-discovered earlier event is flagged. No actual dates, notification-service findings or legally binding clock are inferred.
- **Append-only corrections:** an `event_correction` retains prior record identities and reports a `correction_log`. Reclassifying original procedure type/regime needs `correction_reason=classification_revision`. An earlier answer may cite an event later corrected, but must be reassessed afterward; a subsequent answer may not treat the corrected event as current evidence.
- **Formal lodging:** a specifically typed documentary formal-lodgement record or application-lodgement receipt from an appropriate authority may support *documented* procedural metadata. Appointment, provider check-in, payment, document-return and unclassified receipts do not establish formal lodging.
- **Documents:** the same opaque document ID may appear in several proceedings, with independent presentation/submission records. A shared document does not imply that another authority received it.
- **Corrections of documentary/disclosure identity:** if corrected source material changes what was transmitted or which document was supplied, later acknowledgments and document links are quarantined as unresolved; do not transfer an old receipt to newly classified information or crash the case.
- **Disclosures:** sent, transport delivered, receipt acknowledgment, content acknowledgment, actual reliance and transmission failure are separately source-attributed. Neither late observations nor conflicting reports silently erase prior states. Sent material does not prove officer knowledge, concession, or statutory waiver.
- **Check provenance:** evidentiary event IDs must exist by the relevant response, belong to its proceeding, and not have been corrected before the recorded assessment. Unavailable capability states cannot be marked executed. A `not_applicable` decision requires a coded scope reason and an attributable source/event.
- **Grievance exclusion:** an excluded grievance has a reason code, which remains a pointer requiring a specific legal explanation in substantive advice.
- **Coverage gaps:** historical stages remain available for relevance selection. Outstanding checks are prioritized by declared severity, not simply the first registry entries. An ordinary application need not perform all 301 checks; unassessed remains unassessed.

These deterministic tests validate state structure, audit links and privacy input boundaries only. Semantic legality, authenticity, judgment on applicability, real ChatGPT routing, installed package refresh and cross-session persistence remain external verification tasks.

