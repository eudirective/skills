# Script contracts


## core_source_adapter.py

Input: validated `eudirective-core-source-pack` manifest. Output: a C3-frozen `core_source` module manifest and export conforming to contract `0.2.0`. Preserve source-pack freshness semantics exactly enough to distinguish live-current sources from `baseline_verified_not_live_rechecked`; never upgrade baseline integrity to current. Logical sources with multiple language representations receive a deterministic aggregate content digest.

## source_inventory.py

Input: UTF-8 JSON source inventory. Output: one JSON status line. Validate schema, unique source/proposition IDs, authority-first owner family, required jurisdiction for non-EU material, and hash/retrieval requirements for `current` sources. Do not infer legal authority beyond recorded ownership metadata.

## element_model.py

`validate-model` checks element/family/interaction/invariant cross-references and registered mechanical checks. `check <bundle>` validates an atomic element bundle, supplier permissions, value types and mechanical invariants. Review-only invariants remain visible as review requirements rather than being silently automated.

## contract_validate.py

Input: UTF-8 JSON file plus bundled schema name. Output: one JSON status line. Exit 0 on valid; 2 on invalid. Reject duplicate keys, NaN/Infinity, excessive depth/size, forbidden executable-style keys, unknown schema fields, and Draft 2020-12 schema violations.


## module_conformance.py

Input: a module manifest/export pair conforming structurally to contract `0.2.0`. Output: one conformance status record. Enforce manifest/export identity, namespace ownership, exact compatibility with conformance profile `0.2.0`, controller protocol `0.3.0` and element model `0.2.0`, family-specific roles and normative/attack layers, explicit gap linkage, reusable-non-case classification, internal source/authority references, and attack-angle element references. Do not infer substantive legal correctness.

## case_controller.py

Own state mutation under controller protocol `0.3.0` while consuming C3 inter-skill contract `0.2.0`. Preserve explicit module freshness requirements and requirement completeness as status + reason + scope + detail. Maintain separate full-text and usable-source indexes from module `content_kind`/`authenticity_state`. `authoritative_source_ids` means verified full text only; `usable_source_ids` additionally includes identity/version-verified source notes. Reject `direct_text` unless its explicit `text_source_ref` resolves to full verified text. Note-backed reviewed/candidate rules must carry `support_scope`. Reject controlled-analysis references that resolve only to unusable source content. Full release must reject any required module that does not meet the case freshness requirement.

Own state mutation. Every mutating command must preserve case identity, expected revision, atomic write behavior, minimal audit events and explicit stage guards. Do not add arbitrary Python/shell/callback execution.

## run_selftest.py

Exercise the real bundled validator/controller/source/element entrypoints and fail nonzero if an assertion fails. Expand it whenever a deterministic control is added.


## finalize_core_sources.py

Input: the current independently packaged core source pack. Output: a validated/re-finalized source pack 0.5.0 with verified representation state, source identity/version metadata and deterministic checksums. It must not read Member-State source packs. `verified_source_note` is sufficient for C1 modelling/routing but not exact wording or pinpoints.


## v0.6.0 source-text completion correction

C1 is complete only when every required source has either verified official bundled text or an identity/version-verified normalized source note. Candidate files and unverified reference notes never satisfy the gate. Exact wording and pinpoints require the official source or fuller verified text.


## source_text_ingest.py (current optional fuller-text acquisition)

Input: a core source-pack directory plus `plan`, `fetch`, or `import`. `fetch` must use an explicit `--verified-date`, an identity-specific/canonical official HTTPS URL, and an approved-host redirect policy. Successful fetch creates `bundled_text` with `authenticity_state=verified_official`, records acquisition/final URLs, and pins the observed SHA-256. `import` never authenticates by filename/shape alone: with no pinned digest it stores `candidate_text` / `unverified_candidate` and leaves the blocker count unchanged; with a pinned digest it promotes only on exact SHA-256 match. Reject mismatches, wrong types, undersized payloads, anti-bot pages, untrusted redirects, and missing verification dates. Regenerate ingestion metadata and checksums after any mutation.

## source_text_gate.py (current C1 contract)

C1 passes when every logical source has at least one verified usable representation: either `bundled_text` + `verified_official` or `verified_source_note` + `verified_identity_version`. Verify representation files and hashes, require current/fixed verification metadata for verified notes, and reject representation/authenticity-state contradictions. `candidate_text` and `curated_reference_note` never satisfy the gate.

## core_source_adapter.py (current C1 contract)

Prefer authenticated bundled text. When it is absent but a `verified_source_note` exists, export it as current/fixed identity-version-aware support with explicit `content_kind=verified_source_note` and `authenticity_state=verified_identity_version`; do not describe its digest as authoritative judgment text. Only unverified reference/candidate representations export with `status=unknown` and a source-completeness gap.

## trust_controls.py

Input: `protected-data` plus `privacy-policy` under trust profile `0.1.0`. Output: separate protected, analysis and outbound view artifacts. For synthetic/public data, enforce exact purpose/destination/action profile selection, semantic/type-compatible bounded declarative transforms, direct-identifier policy, policy digest, residual-linkability scoring, explicit limitations and 1–3 delivery-attempt budget. ISO date transforms must reject malformed/arbitrary strings; when direct identifiers are disallowed, reject substring/count transforms before applying any risk reduction. Reject private data while host/runtime enforcement is not independently demonstrated. Do not execute policy expressions or claim anonymity.

## case_controller.py — C4 compatible overlay

The module-facing controller protocol remains `0.3.0`. C4 adds compatible post-release control operations under trust profile `0.1.0`: prepare outbound, authorize outbound, revoke approval, authorize retry, begin/record delivery, checkpoint and checkpoint validation. Bind approvals to exact view/purpose/destination/action/prepared revision; store recipient and approver references as hashes; persist revocation tombstones and lifecycle epoch; reject blind retry and attempt-budget overflow; bind dependency pins into validation/release receipts. `begin-delivery` records controller state only and does not itself perform an external send. Do not add automatic checkpoint restore without a stronger trusted lifecycle anchor.

## topology_engine.py

Input: contract `0.2.0` `case-input` plus an optional element-model `0.2.0` `element-instance-bundle`. Output: `topology-resolution` engine `0.1.1`. Bind exact case and element digests; preserve nationality/residence/work/host/intended-residence/application/deciding/representing/document-issuing/challenged-authority roles; canonicalize known country-name/alpha-3 aliases before equality checks and bind the exact registry version/digest into the topology output; block conflicting duplicate role values and module-request topology mismatches; emit structural cross-border-work and explicit returnee candidates only; never let a contextual frontier-worker false value erase objective residence/work divergence. Reject private case input. Do not infer legal frontier-worker or returnee status from geography alone.

## regime_applicability.py

Input: exact case, C5a topology output, the same bound element bundle, optional `actor-context` for applicant/relevant-Union-citizen scoping, and the bundled core source-pack manifest. Output: `legal-regime-candidates` engine/ruleset `0.1.1`. Verify case/topology/element/optional-actor/source-pack binding. Emit only `candidate`, `blocked`, `unknown`, or `not_indicated` states for the existing legal-regime model elements and keep `final_applicability=not_determined`. Fail closed on unscoped family-member ambiguity; when actor context is present, resolve the relevant Union-citizen status and family relationship from scoped values. Preserve returnee/Article 21 review as a separate candidate/gap record and defer Directive/Visa-Code hierarchy to C5b. Treat source hints as provenance/discovery aids only and national procedure as Member-State-module-owned content.


## hierarchy_principles.py

Input: contract `0.2.0` `case-input`, exact C5a `legal-regime-candidates` output, the same bound element bundle, optional `c5b-context`, optional conformant Member-State manifest/export pairs, bundled core source pack 0.5.0, and bounded principle catalogue 0.1.0. Output: `c5b-hierarchy-principles` engine/ruleset `0.1.0`. Verify case/regime/element/source-pack bindings; validate principle catalogue sources; preserve Directive/Visa Code lex-specialis as unresolved; gate Charter review on explicit EU-law scope; require principle basis refs; enforce the Article 41 Member-State boundary; reject non-binding material as binding law or primacy basis; bind national-rule questions only to conformant case-relevant Member-State modules; never emit a final hierarchy/conflict/disapplication conclusion; reject private data.


## evidence_deadline_authority.py

Input: contract `0.2.0` `case-input`, exact C5a `legal-regime-candidates`, exact C5b `c5b-hierarchy-principles`, the same bound element bundle, optional typed `c5c-context`, optional conformant case-relevant country-module pairs, core source pack 0.5.0, and core route catalogue 0.1.0. Output: `c5c-evidence-deadline-authority` engine/ruleset `0.2.0`. Verify exact case/regime/C5b/element/source/module bindings and replay any module already bound by C5b. Keep Jia freedom-of-proof use dependency-scoped; bind proof-restriction claims to sources/rules without converting labels into legal validity; calculate exact dates only from scoped per-deadline bindings to a source-linked rule and typed trigger-event/date evidence; reject missing/mismatched bindings, inferred/asserted dates, invalid timezone IDs, opaque inclusion rules, unresolved suspension/extension and business-day calculations without a trusted calendar; preserve authority competence/powers/limits and route competence boundaries without route ranking/recommendation; reject private data and blocked-upstream upgrades.

## attack_angle_synthesis.py

Input: contract `0.2.0` `case-input`, exact C5a `legal-regime-candidates`, exact C5b `c5b-hierarchy-principles`, exact C5c `c5c-evidence-deadline-authority`, the same bound element bundle, any country-module pairs already bound by C5c, source pack 0.5.0, and bounded core attack-angle catalogue 0.1.0. Output: `c5d-attack-angle-synthesis` engine/ruleset `0.1.0`.

Verify exact case/regime/C5b/C5c/element/source/module digests and replay all C5c-bound modules. Core patterns must require both a concrete factual/procedural signal and the required upstream basis. Never promote source presence, unresolved lex-specialis, an exact deadline without adverse timeliness state, unknown competence, or GDPR relevance alone into an attack angle. `supported` means supported for review only; every angle keeps `legal_violation_status=not_determined`. Consume module `attack_angle_records` conservatively because contract 0.2.0 does not encode expected prerequisite/disqualifier values. Do not rank remedies, recommend routes, invoke stratagems, or mutate upstream analysis. Reject private data.

## analysis_handoff.py

Input: exact contract `0.2.0` case, exact C5c output, exact C5d output, optional bound element bundle, replayed country-module pairs, and `analysis-review-record` v0.1. Output: `analysis-handoff` engine v0.1.0.

Bind case/C5c/C5d/element/review/module digests. Require explicit review before promotion. Promote core angles only when C5d marks them supported, sufficient-for-review, prerequisite-satisfied, exclusion-clear and complete-for-review. For module angles, replay the originating module record and require a complete value-level check for every declared prerequisite/disqualifier; prerequisite values need fact provenance. Do not promote module routes with `target_authority_level_validation=unknown_frozen_contract`. Keep `legal_conclusion_status=not_determined`. Reject private data.

## suggestion_engine.py

Input: exact `analysis-handoff`, `c5e-context` model-proposed candidate set, adapted stratagem catalogue 0.1.0 and original abstract catalogue 0.1.0. Output: `c5e-suggestion-candidates` engine/ruleset 0.1.0.

Allow only support references present in the handoff. Require adapted patterns for action candidates; original patterns are optional abstract analogues and must share the same ordinal. Block falsification-dependent candidates and explicit disclosure-duty conflicts. Return unknown disclosure duties, uncleared inaction/deadline-waiver risk, and new legal/factual questions to analysis rather than accepting an action. Permit non-applicable and explicit no-action results. Never rank or mark a candidate as a recommendation. Catalogue mutation must not affect upstream analysis or handoff digests.

## suggestion_engine.py — v0.19.0 baseline comparison extension

Input: `c5e-context` v0.1 or v0.2, analysis handoff and both stratagem catalogues. Output: `c5e-suggestion-candidates` engine/ruleset 0.2.0. v0.2 permits neutral/direct baseline actions identified by `candidate_kind=direct_action` and `baseline_kind`, which must not be recast as a stratagem. Direct compliance requires eligible support references. All inaction/no-action must have explicit clearance of deadline, waiver and other prejudice risks. Unknown duty or inaction risk returns to analysis. No ranking or recommendation is added in C5e.

## suggestion_ranking.py

Input: `analysis-handoff`, exact `c5e-context`, exact `c5e-suggestion-candidates` and a `c5f-context` v0.1 review pinned by SHA-256 to all three. Output: `c5f-ranked-suggestions` engine/ruleset 0.1.0. Replay C5e and verify every digest. Require a review for **each** C5e candidate plus the five baseline comparison classes; reject invented support refs and stale bindings. Defer unknown/stale/opposed requirements and unresolved counterevidence. Exclude explicitly rejected unsafe options. Use ordinal Pareto tiers, not arbitrary probability scoring; when alternatives are incomparable retain a tied top tier and list tradeoffs. Relations must be typed and cycles rejected; chains are conditional, require explicit evidence of order/compatibility and a reassessment trigger. Never execute steps, give final legal conclusions or mutate upstream findings. Identity assurance is `unverified_local`; rankings are for review only.

## c6_integration.py — v0.22.0 synthetic release boundary

Commands: `prepare`, `release`, `verify`; inputs: strict synthetic `case-input`, element bundle, optional C5 actor/hierarchy/evidence contexts, pinned source-pack manifest 0.6.0 (0.5.0 retained for regression) and C3-conformant country module manifest/export pairs. `prepare` snapshots and hashes all inputs, adapts EU pack, calls the existing `case_controller.py` transitions, runs C5a->C5d, and writes `c6-run-manifest` 0.2.1 plus stage snapshots/policy hashes. `release` replays the exact chain, optionally accepts **all three** externally provided C5d/C5e/C5f review artifacts, calls C5e/C5f unchanged, projects a conservative `cannot_assess`/mechanical-candidate limited analysis, and uses the original controller for proposal/validation/release. `verify` replays both chains, stage/analysis/receipts, compares the controller's exact controlled-analysis render and independently bound strategy bytes. Every mutation requiring a new stage, identity, policy, module, proposal or review must begin a new run. Never infer professional reviewer authentication, legal correctness, host isolation, or action authority. Tests: `scripts/test_c6_integration.py` (separate from the 156 legacy regressions).

## c7_trust_gate.py / c7_issue_index.py — C7 development boundaries

`c7_trust_gate.require_source_pack()` verifies the complete C1 manifest v0.5.0 (46 representation declarations) or v0.6.0 (47 declarations) against a code-root-pinned SHA-256 policy. The v0.6.0 trust gate rehashes the bundled Deldwyn judgment Markdown on every prepare/release/verify run. The prior 46 representation bytes are absent and are not claimed checked. Passing `source_root` verifies local bytes for every representation against the pinned manifest, but not independent official currency. `require_approved(role, obj)` accepts only exact fictional JSON digests enrolled in the code-pinned policy for case, elements, C5a–C5c context, module pairs and supplied C5d/C5e/C5f reviews. Any policy change requires updating the hard-coded trust digest as a reviewed code release. This gate applies to **C6 integration**, not arbitrary independent source-maintenance scripts.

`c7_issue_index.build()` deterministically projects **all** staged C5 unresolved/limitation records and all unregistered controller candidate IDs to a replayable JSON companion, with source-stage digest, exact pointer and value digest; `render()` creates human-readable complete Markdown. C6 `release` writes a non-retryable `release-attempt.json`, derives both issue-index companions and the conservative controller analysis, and binds the issue-index JSON/Markdown digests in the release receipt. `verify` rebuilds and compares all outputs exactly. Never use a stale C6 v0.1.0 manifest with the C7 driver; its run-manifest version is now 0.2.1.


## verify_complete_source_pack.py — C8 complete-sibling source admission

Requires a physical 0.6.0 sibling directory with `source_manifest.json` *identical* to the independently code-pinned catalogue and all 47 source representation bytes. Reject missing/symlinked/mismatched manifests and missing, substituted or symlinked representations. Verification of local bytes cannot independently authenticate past source acquisition or establish live currency. This check cannot pass until the original full v0.5.0 archive has been supplied and the delta has been applied.

## C11a/b review-extension script contract (v0.24.0)

- `scripts/legal_assessment.py` consumes already-conformant, digest-bound synthetic C5d/case/elements/source/module objects. No user-controlled rule expression is evaluated and no narrative facts are mined. Contract extension `c11a-b-0.1.0` is **not** a change to C3 country exports.
- `references/legal-assessment/c11-rule-profiles.json` is a pinned development-only set of exact-value review rules. Add conditions only after source review and counterexamples; profiles are not national substantive law.
- `references/contracts/c11-legal-assessment.schema.json` validates the synthetic result record. `c11-legal-assessment.md` is a verified sidecar with source/pinpoint *hints*, missing facts, contrary observations and open exceptions.
- `scripts/c6_integration.py` includes the C11 stage in exact prepared replay, uses C11 to filter controlled review candidate projection, refuses C5e review promotion of unsupported predicates, and pins sidecar hashes into the release receipt. C7 issue indexing includes all C11 unresolved and limitation records.
- `scripts/test_c11_legal_assessment.py` covers 8 exact C10 case contexts and source-value negative probes; it is mechanical, not legal-expert scoring.

## C12 maintenance note — 2026-10-10

C12 keeps EU rules inside the core and national rule **authoring** in country-owned sidecars; enrolment snapshots under `references/fixtures/c12` exist only to support the frozen C7 synthetic allowlist. Do not treat them as the source of national law or let them become a route to new private cases. The new C12 stage is digest-bound to C5d, source manifest, module export, extensions, evidence ledger and pinned synthetic document registry. Historical C11 country profiles were removed from the active core rule list; C11 remains a conservative EU-only compatibility screen. A successful `supported_for_review` status means the encoded *factual* test is satisfied in controlled fiction, never that the legal merits or authenticity are established. Re-run `scripts/test_c12_rule_resolution.py`, C6/C7 tests, source/matcher tests, and post-package checks after any change. Preserve novel unassessed issue visibility and C7's exact-fixture gate.

## v0.26.0 C13 raw-format evidence code contract

Keep the in-package PDF/EML/HTML/TXT fixture registry and C13 recogniser catalogue code-pinned in C6. Never accept free-form document paths or user-provided regexes in the C6 allowlist. C13's extracted text spans are proof of reproducible local text extraction *only*, not authenticity, origin, legal service or true facts. C13 may suppress a C12 review candidate but cannot promote a blocked one. The `c13` stage and report are replayed and hash-bound in the C6 prepare/release/verify chain. Update `c7-issue-index` schemas, C6 manifest schema, receipt binding, approved fixture hashes and C7 policy code digest atomically.

## v0.27.0 C14 interpretation and proposal verification

The original 24 C13 English cues remain the sole source of document-to-C12 corroboration; C14 must not silently promote a model/keyword candidate into C12. `scripts/c14_interpretation.py` reads fixed code-pinned English/Swedish/Turkish clause patterns and a separate topic lexicon. Both generate exact offset-anchored review records *without authenticated speaker or factual status*. Generic topic targets deliberately carry `proposed_value=null` and belong in the C13 exhaustive issue index. `scripts/c14_review_proposals.py` uses only approved synthetic fixture pairs; it checks typed source and text anchoring but returns semantic review pending, not expert approval. Keep the C13 0.2.0 schema, C6 CODE_PINS and release-verification reconstruction in sync. Before release run C13/C14 tests, C6/C7 synthetic integration and post-archive tests; report both controlled and untuned adversarial benchmark accuracy without combining them into a misleading score. Do not hide failures from unknown paraphrases or authority-attribution ambiguity.


## 2026-10-10 source-pack restoration (v0.27.1)

The historical C8/C7 text above describes the **earlier** metadata-only v0.22.0–v0.27.0 state. The original 0.5.0 archive was subsequently recovered via the authorized Project Library copy and SHA-256-verified against every 0.5.0 representation. The verified Deldwyn delta was then applied. The v0.27.1 core now includes all 47 declared representation bytes, and C7 requires each bundled file to match its pinned size and SHA-256. This updates the physical distribution assurance only; source freshness and legal correctness remain unreviewed. The standalone sibling pack 0.6.0 is also complete.

## C15 synthetic complete-case model proposal contract (v0.28.0)

- `scripts/c15_casework.py` builds a review-only dossier only from the 14 locally pinned C15 fictional documents. It uses C13's bounded raw-document parser but does **not** add any case to the C7 approved fixture list, alter the C3 schema, or create C6 authoritative stage outputs.
- Input document registry `references/fixtures/c15/pilot-01/manifest.json` is raw-byte pinned by `MANIFEST_SHA256` in the script. Any changed doc byte, registry member or path must block. A feature addition needs a reviewed code and fixture release; never add a free-form path option for private files.
- `retrieve` uses a bounded model-authored exact EU source query set. Before processing it verifies all 47 physical source representations with the C1 release gate. Its snippets have SHA-256, offsets, source IDs and documented note/full-text distinctions. Retrieval is neither meaning nor currentness validation.
- `verify` requires the prepared case index to match the exact pinned source fixture, legal citations to match verified extracted local source text and retrieved spans, crossreferences to be resolvable, and all 14 documents to be used or declared unmapped. It explicitly rejects any automatic violation finding and never authenticates a human reviewer.
- Keep 3 separate assurance statements: mechanically checked anchors, unverified semantic entailment, and unverified substantive legal merits. The example interpretation is developer authored from developer authored test materials, not a blind result. Run `scripts/test_c15_casework.py` and C1–C14 regression tests after editing.
- Do not permit this pilot script to load private or arbitrary new documents, accept national-law assertions as EU source citations, access the network, or authorize any outbound action. The separate national modules remain the custodians of national law and procedures.
