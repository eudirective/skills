# C17b/c/d — fictional, source-owned remedy and correspondence review

**Scope note:** This document governs the **C17 fictional Python remedy generator**, not the separate C23 user-facing **in-chat, read-only** guidance workflow. Its synthetic-only restrictions must not be used to refuse discussion of a real applicant account. For real advisory cases, read `references/c23-applicant-case-guidance.md`; never feed raw private material into C17 scripts.

Milestone date: 2026-10-10. **Developer-only synthetic integration. Not an applicant-use, private-data, legal-advice or sending system.** C17b remedies catalogue, C17c conditional review queue/evidence, and C17d non-send correspondence are implemented across the three skill roots. This is not C15f independent legal validation.

## Ownership and prerequisites

- EU and Union-level routes: `eudirective-core/references/c17-remedy-catalog.json`.
- Swedish visa refusals, appeal, administrative access and JO oversight: resolve the `member_state` module registered for `SE` in `references/national-source-routing.json` and read its registered C17 catalogue path.
- Swedish mission access in Türkiye and Turkish civil-record acquisition: `eudirective-ac-turkiye/references/c17-remedy-catalog.json`. **This does not grant Turkish authorities Swedish visa-appeal competence.**
- Both country catalogues remain in their own independently installable skills, never imported as national legal rules into the core. The core separately pins the identities and hashes of each country module/export/catalogue. Source-note hashes, country-conformance contracts and C12 sidecars are checked. A missing, mismatched, cross-country, unapproved or altered component fails closed.
- Require approved fictional C7 case/elements/fact and C13 document inputs; recompute source/passage-anchored C12/C13 review questions before linking routes. No private applicant files, ad hoc country rules or new C7 run IDs.

Run from an extracted core package with the registered country packages available beside it:

```bash
cd eudirective-core
python scripts/test_c17_remedies.py
python scripts/c17_remedies.py --output-dir /tmp/c17-drafts
```

Optionally bind each draft to an **already-released, verified C6/C7 synthetic** workdir (`L1` through `L8`):

```bash
python scripts/c17_remedies.py --c6-evidence-root /path/to/previously-released-C6-workdirs --output-dir /tmp/c17-bound
```

C6 verification reruns its complete controlled replay and checks C12/C13 digests against the C17 output. This is a provenance/engineering link; C17 outputs are **not** controller-released findings and no correspondence is approved to send. No C6 binding is claimed if the optional workdirs are omitted. A modified previous C6 workdir blocks this path.

## Candidate construction and human queue

Review candidates are triggered **only** by an approved C12 rule that also has a C13 passage-anchored question; scenario labels by themselves never create legal entitlement. Require matching procedure stage, issuer/authority ownership and supported country source IDs. Competing or missing conditions remain review blockers. Source-linked remedies specify authority, proposed power, limits, prerequisites, evidence to preserve, intended outcome, conditional deadlines and the source to reopen. They remain `candidate_for_human_review` with `legal_violation_status=not_determined`.

Priorities are only a **review queue**, not an auto-recommended action sequence: a possible formal appeal is flagged for immediate *independent deadline review*; clarification, evidence acquisition, JO, SOLVIT and Commission processes are parallel considerations. **Do not delay an appeal while awaiting another route.** Never compute an appeal last day or imply a JO complaint suspends one.

## Negative competence and deadline controls

- Swedish visa refusal appeal is considered only for the specifically enrolled L4 appeal stage and corresponding C12/C13 refusal/timing evidence. Guidance from Sweden Abroad reports **three weeks after receipt**. No last day is calculated; service, applicable law, holidays, extension conditions, proof of filing and competent forum are independent human checks. Unchanged appeals may be forwarded to the Migration Court through the published consular procedure; **direct judicial filing is not implemented**.
- JO may investigate and criticise administrative conduct; it cannot change visa decisions or award damages. Published guidance describes a normal two-year limitation for JO consideration, not an appeal period. JO complaints can enter the public record. Complaint is not a substitute for appeal.
- The European Ombudsman covers EU institutions and bodies, **not a Swedish consulate**. The engine explicitly blocks that route for Swedish-mission scenarios, even when an EU legal issue is present.
- SOLVIT is informal, and a Commission complaint is systemic EU-law enforcement; neither grants binding case-specific relief, guarantees action or pauses national deadlines.
- Turkish civil-record acquisition is not an avenue to reverse Swedish decisions. Any VFS service charge must be distinguished from visa fees; a checklist or e-document request is not automatically unlawful.

## Review-only correspondence

Every listed candidate yields a **fictional, conditional text outline**: clarification, supervisory complaint, judicial-referral-aware appeal, systemic complaint, or evidence-acquisition request. Text uses a **recipient placeholder**, alleged issues requiring verification, a requested type of response, and human-source-reference IDs. Never infer name, address, real sender, legal wrongdoing, or authority consent. Every JSON/Markdown artifact says `send_authorized=false`; no send functionality is bundled. The outlines are teaching/review materials, not ready-to-send legal submissions.

## Source defects and independent validation

On 2026-10-10 an official EUR-Lex rendering confirmed Article 2(2)(a)'s spouse definition. A separately pinned **short official-source excerpt** is retained in this skill at `tests/fixtures/core-source-pack-0.6.1/c17/article2-official-excerpt.json`; its digest is checked during synthetic replay. The C1 0.6.1 test fixture contains the targeted repair, while its other C1 representations include 21 source-identity notes rather than full texts. Swedish/Türkiye module notes are not complete verified laws. Neither this scoped excerpt check nor mechanical tests constitute independent legal-merits evaluation.

C15f independent blinded human/expert adjudication is still unavailable. Unknown or conflicting interpretations, privacy-host guarantees, real case eligibility, deadline last dates, administrative judicial competence outside the enrolled routes and current national provisions remain **not verified**. Never promote this C17 version to real-case applicant use without resolving those gates.

## Mechanical regression and release checks

Run `test_c17_applicant_drafts.py`, `test_c17_remedies.py`, `test_c16_coverage.py`, `test_c6_integration.py`, `test_c7_hardening.py`, `test_c7_metadata_freshness.py`, `verify_bundled_source_pack.py`, `run_selftest.py`, and country `verify_source_notes.py`; validate the `c17-remedy-catalog` and `c17-review-plan` schemas and inspect output examples. Retest the three **extracted ZIPs**, including cross-package catalogue hashes and C6 receipt binding. Developer-authored tests measure deterministic boundaries, not independent legal truth. Do not omit failed/unfinished suites in reports.

## C18 status update (2026-10-10)
The C17-era separately pinned excerpt predated and motivated the source-level repair. The C1 v0.6.1 test fixture contains the Article 2(2)(a) spouse clause, verified against the official EUR-Lex HTML passage in the limited scope documented by `c18-directive-art2-restoration.json`. The previous v0.6.0 text and manifest remain historical. Twenty-one other source notes and independent semantic review remain open; real-case and sending restrictions are unchanged.
