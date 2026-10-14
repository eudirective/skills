# Release and version policy

- Patch: compatible bug fix, wording, tests or stricter validation that does not break documented valid inputs.
- Minor: compatible model/contract additions, new controller operations or new legal-engine modules.
- Major: breaking contract changes, changed skill-family ownership or widened trigger boundary that alters compatibility assumptions.

Before packaging: run the self-test, direct CLI smoke tests, quick_validate.py, lint_description.py and semantic review. Keep implicit invocation narrow until recorded real-prompt and integration evidence exists.

C3 is accepted at development contract `0.2.0`. Treat this as a frozen producer/consumer interface for MS0/applicant-country template work, but not as portfolio v1.0. Breaking changes before I3 require an explicit contract-version bump and migration evidence.

- C1 source-pack completion is a prerequisite for activating Member-State source work under the current program sequence. Do not use country-pack progress as evidence for core completeness.


## v0.6.0 source-text completion correction

C1 release readiness requires a verified usable representation for every required logical source. Byte-identical transport is not required. The release must state whether a representation is full bundled text or an identity/version-verified source note and preserve the quotation/pinpoint limitation.


For v0.8.x, a source may leave the C1 blocker list only when `source_text_gate.py` finds `bundled_text` with `authenticity_state=verified_official`. A provenance-free offline file is only a candidate. Offline promotion requires exact match to a digest already pinned in the trusted manifest; the digest must not be derived from the same untrusted import. Official fetches must remain on approved HTTPS hosts and use an explicit verification date.


## v0.10.0 pre-C3 hardening

Treat the direct-text/full-text distinction and the independent reverse source-support coverage baseline as compatibility-significant pre-C3 controls. Do not weaken either merely to make a producer export pass. C3 subsequently revised the provisional contract to 0.2.0 while preserving these guarantees.

## v0.11.0 C3 contract freeze

Freeze inter-skill contract `0.2.0`, conformance profile `0.2.0`, and controller protocol `0.3.0`. Preserve role-sensitive composition, typed geography/request consistency, applicant destination profiles, applicant destination-record/profile consistency, namespace ownership, global ID collision rejection, duplicate role-provider rejection, family-specific normative layers, explicit gap IDs, controlled-analysis reusable-record reference validation, reusable-non-case classification, and compatibility declarations. These controls are interface-significant and must not be weakened to accommodate a producer module.

## v0.12.0 C4 trust-control foundation

Keep the frozen C3 producer boundary at contract/profile `0.2.0` and controller protocol `0.3.0`; C4 introduces trust profile `0.1.0` as a compatible local control layer. Before release, require all C4 deterministic tests to pass, including private-data host gating, view minimisation, approval binding, no-blind-retry, revocation tombstones, dependency pins and current-state checkpoint validation. Do not advertise private-data, secure-deletion, trusted-identity or external-delivery guarantees until the deployment host independently demonstrates them.

## v0.12.1 C4 hardening gate

Require adversarial regressions showing that direct-identifier transform smuggling, malformed date strings, and invalid ISO temporal values fail closed before packaging. Keep trust profile `0.1.0` because this patch tightens implementation to the already-declared transform semantics rather than widening the contract.

## v0.13.0 C5a legal-engine gate

C5a is a compatible minor addition because it adds standalone candidate-producing engines and schemas without changing inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, or trust profile `0.1.0`. Before packaging, require regressions for role preservation, role-conflict blocking, private-data rejection, normalized EU-status gating, Directive/Visa/Schengen candidate coexistence, returnee/source-gap preservation, exact input binding, and source-hint/national ownership. Do not describe C5a as final legal applicability or controller-integrated analysis.


## v0.14.0 C5a adversarial repair gate

Treat 0.14.0 as a compatible minor hardening release: keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, and trust profile `0.1.0` unchanged. Before packaging, require regressions proving (1) unscoped family-member status fails closed rather than producing a false negative, (2) explicit applicant/relevant-Union-citizen actor scope can produce a family-member Directive review candidate, (3) `frontier_worker_context=false` cannot erase a structural residence/work difference, and (4) known jurisdiction aliases such as `SE` and `Sweden` canonicalize to one identity.


## v0.15.0 C5b release gate

Treat 0.15.0 as a compatible minor workflow/model addition. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, and trust profile `0.1.0` unchanged. Before packaging require deterministic regressions for unresolved lex-specialis overlap, Charter scope gating, source-backed principle requests, Article 41 boundary, non-binding soft-law handling, conformant case-relevant national rule binding, unknown/unrelated rule/module rejection, exact C5a chain binding, private-data rejection, and blocked-C5a non-upgrade.


## v0.16.0 C5c release gate

Treat 0.16.0 as a compatible minor workflow/model addition. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, C5b engine `0.1.0`, and trust profile `0.1.0` unchanged. Before packaging require deterministic regressions for dependency-scoped freedom-of-proof, proof-restriction source/rule binding, unknown restriction sources, exact calendar deadline arithmetic, suspension/extension blocking, business-day fail-closed behavior, inferred-date rejection, opaque inclusion rules, unknown deadline IDs, country-module authority competence preservation, core EU route competence boundaries, evidence-basis validation, exact upstream/private-data binding, replay of C5b-bound modules, and blocked-upstream non-upgrade.

## v0.16.1 C5c temporal-binding repair gate

Treat 0.16.1 as a compatible fail-closed repair. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, C5b engine `0.1.0`, and trust profile `0.1.0` unchanged. C5c engine/ruleset becomes `0.2.0`. Before packaging require regressions for unrelated trigger-event identity, true rule-reference semantics, two independently scoped exact deadlines, invalid timezone identity, legacy C5c context fail-closed behavior, and all prior C5c boundaries.

## v0.17.0 C5d release gate

Treat 0.17.0 as a compatible minor legal-engine addition. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, C5b engine `0.1.0`, C5c engine `0.2.0`, and trust profile `0.1.0` unchanged. Add C5d engine/ruleset `0.1.0` plus core attack-angle catalogue `0.1.0`.

Before packaging require deterministic regressions for: source-plus-signal gating; exact deadline plus independent adverse-state gating; proof-restriction non-upgrade; unknown-competence non-defect; unresolved lex-specialis non-attack; GDPR-presence non-attack; module-record candidate-only behavior; fact provenance before `supported`; proportionality concrete-signal gating; exact module replay; catalogue source integrity; blocked-upstream non-upgrade; private-data rejection; and all prior C1-C5c tests. Mock eval remains pipeline-only evidence.

## v0.18.0 C5e release gate

Treat 0.18.0 as a compatible minor downstream-suggestion addition. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, C5b engine `0.1.0`, C5c engine `0.2.0`, C5d engine `0.1.0`, and trust profile `0.1.0` unchanged. Add analysis-handoff engine `0.1.0`, C5e suggestion engine/ruleset `0.1.0`, and original/adapted stratagem catalogues `0.1.0`.

Before packaging require regressions for explicit-review promotion, review-digest binding, module value semantics/provenance, unknown module-route target rejection, complete dual catalogues, candidate-not-recommendation state, unsupported attack-angle rejection, falsification rejection, disclosure/inaction return-to-analysis, non-mutating analysis return, explicit no-action, catalogue independence, private-data rejection, and all prior C1-C5d tests. Mock eval remains pipeline-only evidence.

## v0.19.0 C5f reviewer comparison gate

C5f adds version `0.1.0` review-context/output contracts with no C3 interface changes. Before accepting ranking, replay exact C5e candidates, verify all five direct/wait/no-action baselines and every candidate, preserve unknown/unsafe exclusions, and reject unsupported precedence, cycles and unconditional chains. `single_preferred_for_review` is not execution authorization.

## v0.20.0 C6 controlled synthetic release gate

This compatible minor addition does not alter C3 contract/profile `0.2.0`, controller protocol `0.3.0`, source pack `0.5.0`, element model `0.2.0`, or C5a–C5f engine versions. Add C6 driver/run manifest `0.1.0`, synthetic TR mock module and serialized CLI integration tests. Require existing 156 regressions plus C6 positive/review/negative tests, exact stage replay and script/policy hashes, controller-owned limited analysis validation/release, review-only separated strategy, changed-digest invalidation, and continued fail-closed private/full-release/outbound behavior. Do not claim reviewer authentication, independent legal accuracy, production host privacy or external delivery. After release, proceed to C7 independent hardening.

## v0.21.0 C7 fixed-fixture release gate

This minor, restrictive hardening release leaves C3 contract/profile 0.2.0, controller protocol 0.3.0, C1 pack version 0.5.0 and C5a–C5f legal/strategy engines unchanged. It revises only the C6 run-manifest contract to 0.2.0 (required source-trust record) and adds code-pinned metadata/source-representation declarations, allowlisted synthetic fixture content, complete companion issue indexes and a fail-closed release-attempt marker. A prior C6 v0.1.0 workdir requires a new run; silent migration or in-place rewriting is forbidden.

Before distributing: replay the evaluator's fabricated 64-zero source SHA; reject unapproved synthetic-labelled identifier-like text **before** a snapshot; enumerate all 31+ synthetic unresolved records without elision; mutate the issue companion after release and demand failed verification; inject interrupts at proposal, validation and release; run the full C1–C5f and C6 regressions plus C7 tests, schema/compile/link checks and fresh packaged-archive smoke verification. Compare source pack to a separately trusted identity, not a digest supplied by the pack itself.

The code-pinned policy is a local **release metadata** trust root, not a signed publisher attestation. Source representation bytes are not bundled. Existing C1 legal-source currentness is historical metadata until independently refreshed. Passing local tests does not permit real case intake, independent legal-conclusion claims, real reviewer identity, network delivery, publication or private-data host safety. External workflow evaluator/manual semantic review remains open after the local package passes.

## v0.21.1 C7.1 metadata and as-of repair

Compatible patch to the C6 synthetic-only integration boundary. It preserves source pack 0.5.0, C3 contracts 0.2.0, controller protocol 0.3.0, existing C5 engines and the code-pinned source/fixture policy. The prepared-run manifest advances to 0.2.1 and older C6 workspaces cannot silently migrate because the pinned code/schema and source-as-of field change.

Before releasing v0.21.1, run the exact independent 2026-10-09 probes: a fictional name/email in free-form `--run-id` or appended to `--time-of-check` must fail without creating a workspace; year 2099 must fail the pinned core metadata-age check; known fixed judgments must not be put on mutable operational-page age windows; direct controller initialization of a malformed date must fail; source-as-of mutation must block verification. Rerun C1-C7 deterministic suites, new metadata test, both structural validators, CLI release smoke from the final packaged ZIP, ZIP integrity and hash synchronization. All assertions of legal merits, publisher signatures, authenticated reviewer and host privacy remain explicitly unverified.

## v0.22.0 source-catalogue release (2026-10-09)

The active default moves to 0.6.0 metadata and bundled Deldwyn text while keeping 0.5.0 replay support. Full sibling v0.6.0 assembly and official-site revalidation remain separate release gates. Reuse the existing full C1–C7 tests and add Deldwyn-specific source-integrity and synthetic-controller regression. Do not label this source-pack complete without 47/47 byte matches.
