# C25 modifier invariants (not normal-use instructions)

C25 originally added applicant-strategy guidance and a strictly categorical **synthetic** strategy audit (historical schema 0.2.0). C26 advances the active audit schema to 0.3.0 for event-level review, evidence plans and defense-attribution basis. Do not confuse checklist completion with a successful complaint, legal strategy, or validated model behavior.

- C25's actual applicant-assistance workflow belongs in `references/c25-applicant-strategy.md` and `references/c25-evidence-acquisition.md`; `maintenance/` is never a runtime dependency.
- Keep grievance (authority alleged act) distinct from defense (actual invoked ground vs hypothetical). Do not suppress legally decisive threshold analysis merely because the authority did not mention it. Do not promote early email disclosure to confirmed reading/waiver.
- Keep independent staff-conduct, evidence-access and direct-lodgement tracks despite weaknesses in visa entitlement/territorial competence. Distinguish conduct of staff, contractor and security personnel; check national competence.
- Protect the distinction between Article 15 access to personal data, national administrative file access, and preservation/security retention. Article 18 can apply to specific situations but is not an automatic CCTV freeze.
- All national controller contacts, procedural powers and current remedy deadlines must be checked against official sources at use time; do not port Romania's DPO or consular rules into EU-wide defaults.
- `scripts/c25_strategy_gate.py` must accept *strictly enumerated fictional abstract features* only; no narrative, names, dates, identifiers, jurisdiction combinations, free-text notes, storage, external sending, or persistent private state. It imports C24 for the existing source-index integrity check, not a legal merits ruling. Its flags are prompts for human review.
- The worked Romanian/UAE case remains an evaluation-only fixture. Hidden independent first-response and multi-turn samples should include cases that do not mention Romania, the UAE or an expired resident document.
- Re-run C25 and prior C24/C23/C22/C21/C6/C7 tests plus archive extraction. Record missing real-model responses as `not_executed`, never pass.

## C26 repair invariants (2026-10-11)

- The synthetic C25 input schema advances from `0.2.0` to **`0.3.0`**. Old fixtures must be consciously migrated; never silently fill missing event dispositions, authority-source types or evidence plans with favorable defaults. Preserve optional tool CLI `preview` and independent runtime input restrictions.
- `event_reviews` must have one separately checked row for each reported event, even when multiple events map to one grievance issue. `grievances` remains a summary; do not use issue-code deduplication as proof every act was analyzed.
- Each defense `attribution_basis` is a **self-described evidence type**, not authenticated evidence; human reviewers must inspect the underlying authority statement and chronology. An applicant's own disclosure cannot justify classifying an objection as expressly invoked.
- `evidence_plans` must add a targeted record category and an actionable next step for GDPR, preservation, procedural access and conduct investigation. Labels still cannot prove that these recommendations appeared in the actual ChatGPT answer or that the controller or legal route is correct. Keep `human_review_required` unconditionally.
- Keep generic tourist-visa/CCTV matters outside *positive* trigger evaluations. Use them as negative-route tests absent a genuine EU-family or EU free-movement nexus. Do not broad-invoke this skill for generic privacy or immigration.
- After schema changes, run the full C25 unit tests, old C24/C23/C22/C21 privacy tests, C6/C7 stability where feasible, source integrity, fresh ZIP extraction, and structural validation. Public unedited ChatGPT transcripts with version attribution are still needed before claiming behavior is reliable.
