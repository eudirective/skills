# Element-first legal and procedural model

## Status

C2 model version: `0.2.0` (source-informed). The model is built from composable elements, interactions and invariants; it does not use narrative golden cases as an architecture oracle.

## Layers

1. Element families represent primitive facts, statuses, procedure state, legal regimes, evidence, time, authorities, legal principles, attack angles, completeness, strategy, privacy/control and source state.
2. Element definitions state type, cardinality, permitted suppliers, provenance expectation, absence effect and consumers.
3. Interaction rules state dependencies and semantic boundaries.
4. Invariants separate mechanically enforceable structure from legal/review judgments.
5. `source-support-map.json` indexes the 45-source C1 corpus to model objects. `source-support-requirements.json` independently records the accepted reverse model-to-source coverage baseline for legally material C2 targets. These are conformance/coverage evidence, not entailment proof.

## C2 distinctions

Keep primitive facts distinct from derived legal status; procedure events distinct from conclusions; source identity/currentness distinct from exact-wording support; evidence value distinct from epistemic state; and attack-angle support distinct from strategic priority. Preserve residence, work, host, application, deciding and representing state roles separately. Multiple Member-State modules may be needed in one case.

A `verified_source_note` is sufficient for source identity/version-aware modelling, routing, and reviewed/candidate interpretation within its recorded scope. It cannot support `direct_text` by itself. Exact wording/pinpoints require an explicit full-text source reference resolving to authoritative verified text.

## Supplier boundary

- `core`: EU/common controlled state and reasoning outputs.
- `member_state`: national declarative exports.
- `applicant_country`: local/place-of-application evidence.
- `case_workspace`: case-specific facts and assertions.
- `deterministic_calculation`: script-derived values.
- `model_candidate`: proposed interpretation awaiting a gate/review.

Applicant-country context may alter factual support but may not redefine legal hierarchy or issue the overall legal conclusion. Private case data never becomes a distributable module asset.

## Mechanical versus review invariants

Use code only where structured state is enough to decide failure. C2 mechanically enforces, among other things, deadline triggers, source freshness, operator support, principle/source linkage, Charter/EU-law-scope linkage, proof-restriction provenance, supported attack-angle evidence/source linkage, source-note quotation limits, and typed-event duration linkage.

Keep substantive judgments under review where code would pretend to resolve law: frontier-worker applicability, Article 41 versus general-principle boundaries, soft-law weight, scoped completeness consequences, and the substantive meaning of conflicting evidence.

## Atomic fixtures and generated combinations

Use small fixtures for one structural interaction at a time. They are not whole-case answer keys and must not be labelled golden cases. Generated/adversarial combinations are for finding schema gaps, coupling mistakes and invariant failures; they do not create canonical substantive legal answers.

## Change discipline

When a legal problem cannot be represented: identify the missing element/interaction, assign ownership, add the narrow representation, add a mechanical invariant only where objectively testable, and update source-support coverage if necessary. Do not patch around gaps with country-specific branches in core code.
