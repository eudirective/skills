# Controller protocol v0.3.0

## Purpose

Own deterministic case-state mutation while consuming inter-skill contract `0.2.0`. The controller composes typed reusable modules; it does not execute module code or infer missing national/local rules.

## State sequence

`initialized -> intake_validated -> context_pinned -> requirements_set -> analysis_proposed -> analysis_validated -> released`

Every mutation requires the case ID and expected revision. State writes are atomic. Wrong-case, stale-revision, or invalid-stage mutations fail explicitly.

## Intake

Case input uses contract `0.2.0`. Private-data mode remains disabled in this development controller. Module requests declare family, jurisdiction, role, required/optional status, freshness requirement, and for applicant-country context a destination state. Intake rejects role/jurisdiction requests that contradict the corresponding typed geography field; applicant destination requests must agree with intended/deciding destination topology.

## Module registration

Before registration the controller runs module conformance `0.2.0`.

Registration requires:

- matching manifest/export identity tuple;
- compatible controller/element/profile versions;
- family-appropriate roles and legal layers;
- valid internal source/authority references;
- namespace ownership;
- reusable non-case data classification;
- no duplicate reusable record IDs already registered by another module;
- no overlapping family + jurisdiction + role coverage from two producers.

The controller indexes full verified text separately from other usable verified representations.

## Context freeze

A request is satisfied only by a module matching family + jurisdiction + requested role. Applicant-country requests also require a matching destination-state profile, and applicant operational records that name a destination are constrained to declared profiles.

Required missing modules block context freeze. Optional missing modules remain explicit. Required modules that do not meet the requested freshness assurance remain visible as freshness blockers.

Multiple Member-State modules may coexist. Residence/work/deciding/application roles are not collapsed.

## Requirements and completeness

Runtime requirement statuses are `supported`, `not_supported`, `not_checked`, `not_applicable`, and `blocked`, with reason, scope, and detail. Blocking reasons distinguish insufficient evidence, missing/stale sources, unrechecked sources, required/optional module availability, module incompatibility, conflicting information, unsupported automated evaluation, and other explicit causes.

Module-level gaps are carried separately through the frozen export contract. The controller must not reinterpret a module gap as absence of a problem.

## Analysis validation

Controlled analysis must:

- bind to the current state revision;
- reference only known facts and registered source/rule/authority/deadline/route/attack-angle IDs;
- use only usable verified source representations;
- preserve unresolved required work;
- preserve freshness blockers;
- provide explicit limitations for limited releases.

Full releases cannot bypass required unresolved checks or freshness requirements.

## Release

The controller renders deterministic Markdown and emits validation/release receipts containing the protocol version, contract version, case identity, state-bound analysis digest, module-export digests, requirement snapshot digest, and rendered-output digest.

## Assurance limit

The protocol enforces state, contract, role, identity, compatibility, reference, freshness, and selected completeness boundaries. It does not establish legal truth, resolve semantic conflicts automatically, prove source entailment, or provide host-enforced privacy/outbound guarantees.

## C4 trust-control overlay (skill v0.12.1)

The module-facing protocol version remains `0.3.0`; C4 adds compatible local controller behavior under trust profile `0.1.0` without changing producer manifests/exports.

After deterministic release, the controller may manage outbound control state through:

- `prepare-outbound` — require an eligible minimized outbound view bound to the exact current case revision; store only view/policy digests, purpose/action metadata and a hash of the destination;
- `authorize-outbound` — require an approval record bound to the exact view, purpose, destination, action and prepared revision;
- `revoke-approval` — create a tombstone and increment lifecycle epoch;
- `authorize-retry` — permit another attempt only after `outcome_unknown` and only under a new retry approval;
- `begin-delivery` / `record-delivery` — maintain explicit prepared/authorized/in-flight/acknowledged/rejected/outcome-unknown state without performing the external send itself;
- `checkpoint` / `validate-checkpoint` — bind the exact current state, dependency pins, lifecycle epoch and tombstones.

Delivery attempts are bounded by the minimized outbound policy (1–3). `outcome_unknown` never authorizes blind resubmission. There is no automatic restore command because the local runtime cannot prove that an older checkpoint is safe from lifecycle rollback.

Private-data intake remains disabled. The trust overlay does not prove host isolation, trusted approval identity, secure deletion, anonymity, GDPR compliance or external delivery.

## C5a pre-controller engine boundary (skill v0.14.0)

C5a topology/applicability outputs are standalone, digest-bound candidate artifacts. They are **not** new controller protocol `0.3.0` state transitions and do not change the frozen C3 producer/consumer boundary. C5a must not write `applicable_legal_regime` directly into released controlled analysis. C6 integration must add an explicit validated handoff before these candidate artifacts can influence controller-authoritative release state.


## C5b pre-controller hierarchy/principles boundary (skill v0.15.0)

C5b runs before controller-authoritative analysis integration. Its output is digest-bound candidate/review material with `final_hierarchy_resolution=not_determined`. It may classify binding force, preserve lex-specialis overlap, gate Charter scope, and identify source-backed principle candidates. It cannot set controller completeness, legal findings, release eligibility, or authoritative conflict/disapplication outcomes. C6 must integrate C5b through controlled analysis rather than storing its candidate labels as completed findings.


## C5c pre-controller evidence/deadline/authority boundary (skill v0.16.1)

C5c remains a standalone candidate/review stage outside controller-authoritative release state. It binds exact C5a/C5b/case/element/source/module artifacts and emits `final_c5c_resolution=not_determined`. Exact deadline arithmetic, evidence review candidates and authority/route candidates must not be written into controller-authoritative completed/released state until C6 defines and validates the controlled-analysis integration path.

## C5d pre-controller attack-angle boundary (skill v0.17.0)

C5d remains a standalone review-hypothesis stage outside controller-authoritative release state. It binds the exact C5a/C5b/C5c/case/element/source/module chain and emits `final_attack_angle_resolution=not_determined`. A C5d `supported` label means only supported for review by the encoded factual signal plus source/provenance bindings; it must not be stored as an established violation, remedy entitlement, route priority or strategic recommendation. C6 must define the controlled-analysis handoff before C5d hypotheses can influence released findings.

## C5e pre-controller suggestion boundary (skill v0.18.0)

C5e remains outside controller-authoritative released analysis. The deterministic controller protocol stays `0.3.0`; no new controller stage or authoritative state flag is introduced in v0.18.0.

`analysis_handoff.py` and `suggestion_engine.py` operate on exact digests of C5c/C5d and reviewed support records. Their outputs are downstream candidate artifacts only. They must not be written back as completed/approved/provenance-verified/released controller state, and they must not mutate C5a-C5d findings. `recommendation_status=not_ranked` is mandatory until a later C5f ranking/recommendation boundary is implemented.
