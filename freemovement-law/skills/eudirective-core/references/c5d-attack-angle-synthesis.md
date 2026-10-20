# C5d attack-angle synthesis

C5d is a downstream legal-analysis stage. It consumes the exact bound C5a/C5b/C5c chain and produces **review hypotheses**, not allegations, remedies or strategy.

## Inputs

Use:

- contract `0.2.0` `case-input`;
- exact `legal-regime-candidates` output from C5a;
- exact `c5b-hierarchy-principles` output from C5b;
- exact `c5c-evidence-deadline-authority` output from C5c;
- the same element bundle bound by the upstream chain;
- the core source pack `0.5.0`;
- the bounded core attack-angle catalogue `0.1.0`;
- any conformant country-module pairs already bound by C5c.

C5d must replay every C5c-bound module with the same manifest/export digests. It must not add an unbound country module at this stage.

## Output meaning

`assessment_status` is deliberately narrower than a legal conclusion:

- `supported` means the review hypothesis has the encoded adverse factual signal, legal/source support and fact provenance needed to justify **review**;
- `candidate` means a review hypothesis is indicated but material evidence or substantive legal conditions remain unresolved;
- `insufficient_evidence` means the pattern is structurally indicated but support is missing;
- `blocked` means the upstream chain or a required deterministic boundary blocks promotion;
- `not_indicated` is reserved by the schema but the initial engine omits untriggered catalogue entries instead of emitting a long negative list.

Every angle carries `legal_violation_status=not_determined`. `supported` never means unlawful, disproportionate, incompetent, late in law, or entitled to a remedy.

## Core catalogue v0.1.0

The initial deterministic catalogue covers only patterns for which the current element/upstream models expose a concrete signal:

- source/rule-bound proof-restriction review;
- dependency-scoped open-proof review;
- exact-deadline plus independently adverse timeliness state;
- appointment/lodgement/procedural-access impediment;
- complaint/review-path issues when a source-backed C5b principle candidate also exists;
- explicitly adverse authority-competence state with source-backed route material;
- proportionality review only when a C5b proportionality candidate is paired with a concrete adverse procedural/evidentiary signal.

Do not add a pattern merely because a legal source exists. Each pattern requires a factual/procedural signal and the indicated upstream basis.

## Important false-positive controls

### Deadlines

An exact C5c calculation alone cannot create a delay attack angle. C5d additionally requires `procedure.deadline_state` to carry an explicit adverse timeliness state. C5d does not compare the calculated date with wall-clock time.

### Proof restrictions

A source-bound checklist/document restriction stays a review candidate. It does not become an unlawful closed-list finding merely because an authority stated it or because an alternative proof principle exists.

### Authority competence

Unknown, absent or unstructured authority level/competence is not treated as a defect. A competence angle requires an explicitly adverse competence state and source-backed route material.

### Lex specialis

The unresolved Directive/Visa Code relationship from C5b is not a contradiction attack angle. Overlap remains an unresolved hierarchy question until issue-specific legal analysis resolves it.

### GDPR/data minimisation

Do not generate a GDPR/data-minimisation allegation merely because personal data exists or a GDPR regime is potentially relevant. The current element model does not yet encode the authority-processing purpose/necessity/excess predicates needed for a safe deterministic pattern. Use a source-backed country-module attack record or extend the factual model first.

## Country-module attack-angle records

Contract `0.2.0` already lets country modules export declarative `attack_angle_records`. C5d consumes these only from conformant, case-relevant modules whose exact digests are already bound by C5c.

The frozen record format lists prerequisite/disqualifier **element IDs**, but it does not encode required values. Therefore the core must not treat a reviewed module record as automatically established. In v0.17.0 module records remain candidate/review inputs:

- missing prerequisite element IDs -> `insufficient_evidence`;
- disqualifier element IDs present -> exclusion state remains `unresolved` because value semantics are not encoded;
- `support_status=unsupported_automation` -> `blocked`;
- source refs must resolve within the replayed module/source set.

A future contract may add typed expected-value semantics; do not infer them from labels now.

## Downstream boundary

C5d must not:

- rank routes or remedies;
- recommend escalation;
- invoke stratagems;
- infer motive/bad faith;
- change C5a applicability, C5b hierarchy/principle or C5c evidence/deadline/authority results;
- turn source gaps, stale data or unsupported automation into legal violations.

C5e consumes only an explicit promotion-grade `analysis-handoff` produced by `scripts/analysis_handoff.py`; it does not consume C5d labels directly. C5f may later rank C5e candidates. Neither suggestion catalogue may feed back into C5d or earlier analysis.
