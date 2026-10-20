# C14 — Multilingual interpretation and review (synthetic-only)

**eudirective Core v0.27.0 · C13 documentary envelope v0.2.0 · C14 candidate engine v0.1.0**

## Runtime procedure

1. Use only the existing C7 approved fictional case/element/evidence-set combinations. Never ingest private applicant documents, unlisted URLs, arbitrary file paths, or user-supplied expressions into the controller.
2. Run `python scripts/c13_document_evidence.py` through the C6 `prepare`, `release`, `verify` flow. Its earlier C13 cue observations remain mechanically reconciled with C12. **Do not change their legal meaning or treat passage matches as true facts.**
3. Inspect **C14 interpretation candidates**: regex-generated, cross-language proposed values (English, Swedish, Turkish), each with exact source offset/segment hash and `candidate_requires_review`. Quoted speech, hypotheticals and modal qualifications trigger explicit cautions; other candidates remain unreviewed anyway.
4. Inspect **C14 open review targets**: broader topical passages with **no proposed value**. They deliberately prioritize visibility over classification precision. A missing target is not proof that no legal issue exists.
5. To assess an open target's meaning, read its exact quoted passage, the adjacent paragraph and other relevant documents. Distinguish writer's own statement, a quote/third-party allegation, hypothetical, negation, a decision's date versus service, and document contents versus truth. Optionally ask a model to draft a *proposal bundle*; do not grant the model any right to certify the proposition. Where the meaning is contested, keep the candidate unresolved.
6. For every model-drafted proposal, include its actual `document_ref`, `locator`, full byte and segment SHA-256, character `start`/`end`, verbatim `quote`, supported `fact_key`, typed `proposed_value`, language, and a short interpretative explanation. The exact proposal data contract is enforced by `c14_interpretation.verify_external_proposals` and the standalone checker.
7. Run the offline checker (example below). It verifies only that the proposed quote occurs exactly at the asserted location inside a C7-approved synthetic source. It **cannot verify entailment, authorship, or truth**; all proposals remain `requires_human_review` and **never enter C6/C12 rule readiness automatically**.
8. Report observations, interpretation candidates, quoted and disputed statements, missing links, and an explicit evaluation limitation. Never infer illegality, appeal competence, deadline expiration, lawful authority conduct or GDPR compliance from C14 output.

## Standalone model/human proposal validation

```bash
python scripts/c14_review_proposals.py \
  --case references/fixtures/c10/L1/case.json \
  --elements references/fixtures/c10/L1/elements.json \
  --evidence-set references/fixtures/c13/L1-evidence-set.json \
  --proposals /tmp/review-proposals.json \
  --output /tmp/review-proposal-verification.json
```

The proposals JSON is a single object with `proposal_version: "0.1.0"` and `proposals` (up to 100). Each proposal must contain only the fields `document_ref`, `locator`, `document_sha256`, `segment_sha256`, `start`, `end`, `quote`, `fact_key`, `proposed_value`, `language`, and `explanation`. The `reported_value` is not independently checked for semantic entailment. Reject any hash/offset/quote mismatch. The checker never updates the C7 allowlist and never promotes a proposal into a C12 premise.

## Evaluation and failure criteria

Run `python scripts/test_c14_interpretation.py` for registered-fixture text anchoring, quote/conditional cautions, proposal tamper rejection, and the **136-case controlled multilingual suite**. The **61-case untuned adversarial suite**, authored after freezing the grammar, is a separate diagnostic. Preserve its poor recall honestly; do not tune against that suite and continue calling it an untouched test set.

The earlier 36 C13 wording cases are *historical regression items*, not unseen legal examples. The evaluation outputs separately distinguish controlled-suite exact matches, untuned-challenge exact matches, review-target recall, and review load from ambiguous or irrelevant targets. All sample labels are **developer-authored synthetic language labels**, not third-party adjudication or independent legal-expert scoring.

The topic retriever is deliberately open-ended and will flag many negative/irrelevant passages. A reviewer must not equate topic relevance with an allegation. For any new modelling claim, collect an independently constructed, untouched and expert-graded corpus of multilingual correspondence with source offsets and verified counterexamples before claiming validated language understanding.

## Modification boundaries

C3 country exports remain frozen. C14 data belongs to the EU/common interpretation machinery; national laws remain in the Sweden and Türkiye modules. The C14 engine/grammar/topic lexicon and C13 schema are included in C6 code pins, so changes demand a new reviewed release. C14 does not add new C6 enrolment, a writable external database, private-document intake, outbound telemetry, OCR, or external service calls. Maintain the `not_determined` legal-conclusion boundary and the full C7 issue index.
