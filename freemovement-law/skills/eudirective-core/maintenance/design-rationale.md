# Design rationale

Preserve the three-family split. The core owns reusable reasoning and control logic; country skills remain independently versioned declarative data/source providers.

v0.1.0 proved that a script-owned controller and independent module contracts were feasible. v0.2.0 deliberately replaces the earlier golden-case assumption with an element-first model: source ownership -> elements/interactions/invariants -> contracts -> reasoning engines.

This avoids using a finite set of narratives as an oracle for a highly combinatorial legal domain. Atomic fixtures protect structural behavior; substantive legal correctness remains source-backed and reviewable.

The source inventory is intentionally staging-oriented. Do not claim the EU/common source migration is complete until real sources, hashes, effective dates and references are populated and checked.

The controller stores digests and reference IDs rather than copying raw narratives because audit/state files are disclosure surfaces. This remains an initial minimisation step, not a full privacy implementation.

Do not broaden the trigger boundary to routine applicant-facing analysis until core legal engines, at least one Member-State module, element/contract conformance, and integrated release gates have real evidence.


v0.3.0 introduced the first real EU/common source-pack baseline. v0.4.0 closes the previously separate source-pack/controller lane with a deterministic adapter and makes freshness assurance explicit. Baseline byte integrity is not equivalent to live-current legal freshness, so the controller now evaluates the freshness requirement declared by the case instead of treating every non-`current` module as generically stale.

Completeness remains a controlled status vocabulary, but runtime requirement records now also retain reason, scope and detail. This avoids losing the distinction between insufficient evidence, unsupported automation, stale sources, unrechecked sources and other blocking causes before C3/P1 contract hardening.


v0.5.0 completes the C1 foundational core source baseline before any Member-State source work. The pack distinguishes mutable currentness from immutable fixed-source verification and adds the foundational EU-law authorities required for the C2 element-model pass. Country-source work is deliberately deferred rather than run in parallel with C1.


## v0.6.0 source-text completion correction

C1 is complete when every required logical source has a verified usable representation tied to the correct official identity and fixed/current/consolidated version. Full bundled text is preferred but not mandatory. `scripts/source_text_gate.py` enforces this representation gate; exact quotations and pinpoints remain analysis-time official-source checks.


## v0.7.0 — authoritative-byte ingestion

The previous release correctly blocked C1 but still left source acquisition as an external/manual step. v0.7.0 makes acquisition itself deterministic: official network fetch and offline import converge on the same validation, representation, hashing, metadata and checksum path. Network availability remains an environment dependency; the skill must report transport failure without downgrading the source or inventing content.

## v0.8.0 — source-authenticity hardening

Adversarial evaluation showed that v0.7.0 treated accepted filename + file shape as sufficient offline provenance. v0.8.0 separates acquisition from authenticity: provenance-free local files are `candidate_text` only; they cannot satisfy C1. Promotion requires either a restricted official-HTTPS fetch bound to the expected source endpoint or an exact match to a digest already pinned in the trusted manifest. The gate now checks authenticity state as well as bytes/hash presence. Adapter exports expose content/authenticity state per source so reference notes cannot masquerade as authoritative text.

## v0.11.0 — C3 contract freeze

C3 freezes the development producer/consumer boundary at contract 0.2.0 instead of freezing country implementations. The interface is role-sensitive and destination-profile-aware, preserves separate legal layers, rejects global reusable-ID collisions, and makes module compatibility explicit. This enables independent Member-State and applicant-country development without allowing module order or generic jurisdiction matching to become hidden reasoning. Portfolio v1.0 remains deferred until real multi-family integration evidence exists.

## v0.12.0 — C4 deterministic trust/privacy/lifecycle foundation

C4 is implemented as a local deterministic control layer without changing the frozen C3 producer interface. The module-facing controller protocol stays `0.3.0`; a separate trust profile `0.1.0` owns view minimisation, outbound binding, approvals, retry discipline, lifecycle tombstones, dependency pins and checkpoints.

Private-data mode remains disabled because local Python controls cannot prove host-enforced storage/tool/output isolation. The C4 implementation therefore uses synthetic/public fixtures and explicitly distinguishes deterministic minimisation from anonymity. Recovery is conservative: checkpoints are integrity/currentness evidence only and there is no automatic restore path that could resurrect revoked approvals or regress delivery state.

## v0.12.1 — C4 transform-semantics hardening

The 0.12.1 patch keeps trust profile `0.1.0` and its schema shape but enforces the semantics that profile already claimed: date generalisation is permitted only for valid ISO temporal values, and a profile that disallows direct identifiers cannot use substring/count transforms to leak pieces or lengths of direct identifiers. Rejected transforms receive no linkability-risk reduction. This closes the evaluator-discovered transform-smuggling gap without changing the frozen C3 producer boundary.

## v0.13.0 — C5a topology/applicability candidate foundation

C5a begins the reusable legal-engine phase without breaking the C3 producer boundary. The topology engine binds the exact case/element inputs and preserves distinct country roles rather than collapsing them into a destination-state narrative. Structural patterns such as residence/work divergence are emitted only as review candidates. Returnee status is not inferred from geography alone.

The applicability engine is deliberately candidate-only. It can identify potentially relevant Directive 2004/38, Visa Code, Schengen and national-procedure frameworks, preserve a Directive/Visa-Code hierarchy interaction for C5b, and expose missing/unnormalized prerequisites. It cannot emit final applicability. Source references are hints bound to the current C1 pack, not entailment proof. The returnee path explicitly records the absence of a dedicated primary-TFEU source record instead of laundering Commission guidance into primary-law completeness.


## v0.14.0 — C5a adversarial repair

The workflow evaluation of v0.13.0 exposed three structural weaknesses that the green deterministic suite had not covered: singleton person-status elements were actor-ambiguous in family-member cases, `frontier_worker_context=false` could override objective residence/work divergence, and simple country-name/code aliases could false-block topology.

The 0.14.0 hardening release keeps the frozen C3 producer contract and element model unchanged. Family-member actor identity is represented in a local C5a `actor-context` artifact rather than by breaking producer contracts prematurely. Known jurisdiction aliases are canonicalized deterministically to ISO alpha-2 identifiers through a bundled registry. Structural residence/work comparison is authoritative for the structural cross-border-work candidate; a contradictory frontier-context assertion is recorded as an unresolved review issue rather than an override.


## v0.15.0 — C5b hierarchy/principles candidate stage

C5b deliberately avoids a numeric legal hierarchy because CJEU interpretation, primary law, secondary legislation and non-binding guidance do not form a safe one-dimensional ranking for issue resolution. The engine instead preserves source legal-status classes, requires explicit scoped questions, binds national rules only from conformant case-relevant Member-State modules, and keeps lex-specialis/conflict/disapplication outcomes unresolved. A bounded principle catalogue supplies source-backed candidate mechanisms without allowing the model to invent a principle or authority.


## v0.16.0 — C5c evidence/deadline/authority candidate stage

C5c keeps source-backed evidence claims, mechanical date arithmetic and escalation-route metadata in separate sublanes because they have different proof burdens. A proof-restriction assertion is not a legal-validity finding; Jia is scoped to dependency evidence rather than generalized. Exact deadline calculation is permitted only where the frozen model already binds rule, trigger and event date and where timezone, suspension/extension and operator/inclusion semantics are explicit. Business-day calculations remain non-exact without a trusted holiday-calendar identity. Route evaluation preserves competence, powers and limits but deliberately stops before recommendation/ranking; authority level is not guessed where the frozen producer contract does not encode it.

## v0.16.1 C5c scoped temporal bindings

C5c no longer treats the singleton timeline elements as sufficient proof of which event/date belongs to which deadline request. The C5c context now supports request-selected `deadline_bindings` that bind one deadline to one actual rule reference and one typed temporal-event identity. The referenced temporal-event record separately carries the event type/date evidence, so changing only an event identifier cannot silently reuse an unrelated date. This is intentionally an internal C5c repair and does not change the frozen C3 producer contract or element-model version. Legacy C5c context `0.1.0` remains structurally accepted, but exact deadline calculation fails closed without a scoped binding.

The engine validates IANA timezone identity before exact arithmetic. Current operators are date-only, so timezone database offset semantics do not affect the calculated date; the timezone check prevents a meaningless or fabricated identifier from satisfying an exactness prerequisite.

## v0.17.0 C5d source-plus-signal synthesis

Attack-angle synthesis is downstream of legal analysis, not a substitute for it. A source or abstract principle cannot generate non-compliance by itself. The C5d engine therefore requires an explicit factual/procedural signal plus the relevant C5a-C5c support and preserves `legal_violation_status=not_determined` even where the review hypothesis is marked `supported`.

The initial core catalogue is intentionally narrower than the architecture wish-list. GDPR/data minimisation is not auto-generated because the current element model lacks authority-processing purpose/necessity/excess predicates. Digital-only access is treated through the general access-impediment signal rather than a per se defect. Missing reasons, consultation duties and contradiction analysis remain future model work rather than hard-coded assumptions.

Country-module attack-angle records are consumed but not promoted to established/supported solely from `support_status=reviewed`. The frozen module schema names prerequisite/disqualifier element IDs but does not encode required values, so the core can only verify presence and keep semantic review explicit.

## v0.18.0 C5e promotion barrier and suggestion generation

C5e introduces a hard one-way boundary between legal/procedural analysis and strategy generation. C5d status labels do not become recommendation-grade merely because they are named `supported`; a separate digest-bound review record is required before any attack angle or route enters the suggestion layer. This avoids trust-by-label and makes the review-to-strategy transition inspectable.

The frozen producer contract remains 0.2.0. Module attack-angle records therefore still lack expected prerequisite/disqualifier values. Rather than weakening the boundary, the handoff accepts a local value-level overlay that is checked against the actual bound element bundle and requires provenance for prerequisite facts. Module routes whose target authority level remains structurally unknown are not promoted.

The adapted/generalized Thirty-Six Stratagems are the preferred operational layer. The original/classical catalogue is retained only as an abstract heuristic analogue because English renderings vary and because historical formulations must not become legal or ethical authority. C5e validates model-proposed candidates but deliberately stops before ranking or recommendation; C5f owns that boundary. Catalogue changes are downstream-only and cannot alter C5a-C5d analysis or the analysis-handoff digest.

## v0.19.0 C5f — conservative preference semantics

A simple weighted-score formula would disguise subjective legal-strength and remedy-power estimates as quantitative certainty and could turn a merely labelled reviewer conclusion into an unqualified legal recommendation. Instead C5f requires a digest-pinned review of every C5e candidate, evaluates all five direct/no-action baselines, separates unsupported/exploratory conjectures and expressly excluded options, and constructs Pareto ordinal priority tiers with explicit non-comparability. A single preferred option is only **preferred for review**, not action authority. The exact C5e replay prevents stale or relabelled candidate outputs from laundering into ranking. C5e supports direct procedural alternatives without forcing artificial stratagem analogues, and no action now requires an explicit prejudice/waiver check. Sequences are not execution plans: they require known compatible/ordered relationships, no pairwise conflict, and renewed analysis after material responses. Frozen C3 and substantive legal-analysis stages remain unchanged.

## v0.20.0 C6 deterministic integration decision

The existing C3 controller already implements canonical transitions and release receipts; adding a parallel case-state engine would create inconsistent authority. C6 therefore composes C5a–C5f using the original controller. The first release projection is intentionally narrow: it records C5d hypotheses as `cannot_assess`, preserves only sourced mechanically scoped deadline dates with explicit qualifications, and leaves substantive legal-merits review unchecked. It cannot claim full release merely because the engine chain is structurally valid. Reviewer-supplied C5e/C5f comparison is separately replayed and rendered, bound to the analysis receipt but not inside legal findings. Restricting the integration driver to synthetic data keeps the unresolved host privacy/outbound guarantees outside the advertised feature. An independent C7 evaluation, not local mock tests, will be the next hardening gate.

## v0.22.0 Deldwyn catalogue activation

Preserve 0.5.0 manifest trust for historical synthetic regression and add an exact 0.6.0 metadata digest trust root rather than weakening source-policy checks. Bundle and rehash only the newly verified 17-page Deldwyn text. The unavailable 46 old representation files are not synthesized or portrayed as locally verified. C2 coverage targets change additively, C3 contract and controller remain frozen, and all legal implications stay review-only. Activation produces an exact-tested core catalogue, NOT a complete physical v0.6.0 sibling pack.

## C12 maintenance note — 2026-10-10

C12 keeps EU rules inside the core and national rule **authoring** in country-owned sidecars; enrolment snapshots under `references/fixtures/c12` exist only to support the frozen C7 synthetic allowlist. Do not treat them as the source of national law or let them become a route to new private cases. The new C12 stage is digest-bound to C5d, source manifest, module export, extensions, evidence ledger and pinned synthetic document registry. Historical C11 country profiles were removed from the active core rule list; C11 remains a conservative EU-only compatibility screen. A successful `supported_for_review` status means the encoded *factual* test is satisfied in controlled fiction, never that the legal merits or authenticity are established. Re-run `scripts/test_c12_rule_resolution.py`, C6/C7 tests, source/matcher tests, and post-package checks after any change. Preserve novel unassessed issue visibility and C7's exact-fixture gate.


## 2026-10-10 source-pack restoration (v0.27.1)

The historical C8/C7 text above describes the **earlier** metadata-only v0.22.0–v0.27.0 state. The original 0.5.0 archive was subsequently recovered via the authorized Project Library copy and SHA-256-verified against every 0.5.0 representation. The verified Deldwyn delta was then applied. The v0.27.1 core now includes all 47 declared representation bytes, and C7 requires each bundled file to match its pinned size and SHA-256. This updates the physical distribution assurance only; source freshness and legal correctness remain unreviewed. The standalone sibling pack 0.6.0 is also complete.


## v0.36.0 - C23 read-only applicant guidance

The original blanket exclusion of real-person EU-family visa questions caused a model to answer a real case as an unverified journalistic summary while declining the skill's controlled logic. Preserve a distinction between (a) **in-chat, user-authorised, read-only advisory reasoning**, which may analyse real first-hand accounts and guide complaints, and (b) the **Python-controlled C6/C7/C13/C17/C21 pipelines**, which still cannot ingest arbitrary private documents or send. No private host/security claim is made for the chat lane. Scope comparison of ordinary Schengen lists versus mobile-EU-family rules is now a mandatory reasoning step, with a strict non-identifying feature-only comparator as a narrow verification aid. Independent C15f legal-semantic grading remains a prerequisite for stronger assurances, not a reason to decline a practical sourced answer.
