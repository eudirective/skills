# Known failure modes

- Treating a narrative test case as the canonical legal answer for a combinatorial domain.
- Adding a one-off field or Sweden-specific branch instead of extending the element model first.
- Treating schema/invariant validity as proof that a source supports a legal claim.
- Letting the model set completion, approval, provenance-verification or release flags directly.
- Letting an applicant-country module provide the controlling legal hierarchy or overall conclusion.
- Treating an optional applicant-country module as permission to invent local facts.
- Letting `not_checked`, blocked, stale or unsupported work become `not_supported` or `no problem`.
- Registering a module by filename rather than validating manifest/export identity and contract version.
- Releasing prose that differs from the validated controlled-analysis artifact.
- Claiming private-data safety because Python scripts are deterministic while the host still permits alternate output/tool paths.
- Adding arbitrary extension fields or executable rule expressions to country exports.
- Copying raw case narratives into controller history, logs, receipts, fixtures or distributable module assets.
- Promoting staged source metadata to `current` without hashes/retrieval evidence.

- Mapping `baseline_verified_not_live_rechecked` to `current` merely to satisfy the controller.
- Treating every non-current freshness state as the same failure when the workflow only requires baseline integrity.
- Collapsing completeness reasons into a single `blocked` token and losing whether the cause was freshness, evidence, module availability, conflict or unsupported automation.
- Recreating core-source module manifests by hand instead of using the deterministic source-pack adapter.

- Re-entering a Member-State pack while the core source milestone is incomplete.
- Treating a curated reference note as if it were the official judgment text.
- Treating a fixed immutable judgment as stale merely because it was not re-consolidated, or treating a mutable regulation as current without an official current-version check.


## v0.6.0 source-text completion correction

Do not confuse source identity/version verification with exact-text verification. A `verified_source_note` may satisfy C1 for modelling and routing, but it must never silently support exact quotations or paragraph/article pinpoints. Those uses require the official source or fuller verified text.

- Treating an HTTP 200 response as authoritative source text without validating file type or anti-bot/interstitial content.
- Marking a network fetch failure as a source failure rather than a transport failure.
- Reconstructing a missing judgment from snippets, summaries, or model memory instead of importing authoritative bytes.
- Updating the source manifest without regenerating pack-level checksums and ingestion metadata.

## v0.7.0 ingestion workflow

C1 remains blocked at 21 sources in this sandbox, but the completion operation is now deterministic. Use `source_text_ingest.py`; do not hand-edit representations to bypass the gate.

## v0.8.0 authenticity controls

- Treating filename, PDF magic bytes, MIME type, or file size as proof that an offline file is the named official authority.
- Letting a provenance-free offline import reduce the C1 blocker count.
- Pinning a digest from the same untrusted offline file and then treating the circular match as authentication.
- Following a redirect from an official source endpoint to an unapproved host and still labelling the result official.
- Exporting a curated reference note or unverified candidate with `status=current` in a way that makes it look usable as source text.
- Reusing a historical verification date by default on a later ingestion run.

- Treating family + jurisdiction as sufficient module matching while ignoring the requested role.
- Letting applicant-country context for one destination state satisfy another destination-state profile.
- Allowing a Member-State or applicant-country export to claim the EU/common normative layer.
- Resolving semantic conflicts by module registration order.
- Reusing a reusable record ID across modules and silently overwriting provenance.
- Treating conformance as proof of substantive legal correctness.

## v0.12.0 C4 controls

- Treating deterministic minimisation or a low linkability score as proof of anonymity.
- Enabling private-data mode merely because local Python code rejects unsafe operations while the host still exposes uncontrolled paths.
- Storing raw recipient addresses or approver identifiers in controller audit history instead of hashes/bound artifacts.
- Reusing an approval after purpose, recipient, action, view bytes or prepared revision changed.
- Retrying an `outcome_unknown` delivery without a separate retry approval.
- Exceeding the policy attempt budget or treating `begin-delivery` as proof that a network send occurred.
- Restoring an old checkpoint without a trusted lifecycle boundary and thereby resurrecting revoked approvals or duplicate-send state.
- Treating `unverified_local` approval identity as trusted human identity.
- Assuming controller checkpoints guarantee secure deletion of host files, caches, logs or backups.

## v0.12.1 C4 transform hardening

- Do not generalize dates by slicing arbitrary strings; invalid ISO temporal values must fail closed.
- Do not use date/count transforms to partially disclose a `direct_identifier` when `allow_direct_identifiers=false`.
- Do not apply transform risk reduction until compatibility has been validated and the transform is actually accepted.
- Field classifications and risk tags remain declared inputs rather than independently trusted facts; private-data mode therefore remains disabled until a stronger provenance/host boundary exists.

## v0.13.0 C5a topology/applicability controls

- Collapsing residence, work, application, deciding, representing, host or issuing roles into one generic destination state.
- Treating different residence/work states as proof of legal frontier-worker status.
- Inferring returnee status from a home-state-looking topology without an explicit `movement.returnee_context` input.
- Treating a `candidate` framework as `applicable` or a blocked candidate as `not_applicable`.
- Inferring EU-citizen status from nationality geography or arbitrary prose instead of a normalized provenance-bearing element.
- Letting a stale topology or different element bundle feed the applicability stage after digest binding changes.
- Resolving Directive/Visa-Code lex specialis inside C5a instead of preserving the interaction for C5b.
- Treating `source_hint_refs` as proof that a source entails the candidate conclusion.
- Inventing national procedure instead of emitting Member-State role hints.
- Hiding the returnee primary-TFEU source gap because a secondary/current guidance source exists.


## v0.14.0 C5a adversarial repairs

- Do not treat singleton `person_status.eu_citizen_status` as actor-scoped in a family-member case. If family-member/accompanying signals are present without `actor-context`, fail closed with `actor_scope_required_for_family_member_case`.
- Do not let `movement.frontier_worker_context=false` erase objective residence/work-state divergence. Preserve the structural candidate and surface `frontier_context_conflicts_with_structural_topology`.
- Do not compare known country names/codes as raw strings. Canonicalize through the bundled jurisdiction alias registry before equality checks. Unknown labels remain explicit and may still require review.
- Do not treat the jurisdiction registry as a statement about sovereignty, recognition, EU membership, Schengen participation, or legal territorial scope.
- Do not use actor-context output to claim final Directive applicability; it only repairs subject identity for candidate generation.


## v0.15.0 C5b failure boundaries

- Do not infer Directive/Visa Code priority from the fact that both are binding secondary law.
- Do not infer Charter scope merely because an EU-law regime is a candidate; require the scoped EU-law-scope element.
- Do not treat a requested principle name as support. Principle IDs must exist in the bundled catalogue, their sources must resolve, and the request must bind an existing C5a regime/source basis.
- Do not use an unrelated Member-State module or an unknown national rule to manufacture a hierarchy conflict.
- Do not use non-binding guidance/recommendations as a primacy/disapplication basis or recode them as binding rules.
- Do not let a blocked C5a chain become a C5b principle candidate.
- C5b does not prove substantive direct effect, conflict, disapplication, proportionality, effectiveness, Charter infringement or national-law correctness.


## v0.16.0 C5c failure boundaries

- Generalizing Jia dependency-evidence reasoning into a universal freedom-of-proof rule.
- Treating `proof_restriction_status=established` as proof that a closed-document rule is legally valid.
- Treating a checklist, local operational source or non-binding guidance as a binding closed-proof rule without a source/rule basis.
- Calculating an exact deadline when the bound rule ID, trigger ID, event date, timezone, inclusion rule, suspension state or extension state is missing/ambiguous.
- Counting business days without a trusted business-day/holiday calendar identity.
- Interpreting source-defined deadline rules through free-form text.
- Inferring authority level from module family, country name or route label when the frozen contract does not encode it.
- Treating SOLVIT, Commission complaints or Ombudsman complaints as interchangeable remedies or guaranteed individual redress.
- Ranking/recommending an escalation route inside C5c instead of preserving it as a downstream suggestion input.
- Allowing C5c to upgrade a blocked C5a/C5b chain.

## v0.16.1 C5c temporal-binding repair

- Do not treat a country-module route target level as matched merely because the route remains a candidate; `target_authority_level_validation=unknown_frozen_contract` must remain visible until a future contract supplies normalized authority levels.
- Do not treat the presence of a global `time.deadline_trigger_ref` as proof that the date being used belongs to that trigger.
- Do not compare `time.deadline_rule_ref` to a deadline-record ID; it denotes a rule reference.
- Do not use singleton case-level time elements as a multi-deadline binding mechanism. Exact C5c arithmetic requires a scoped `deadline_bindings` record selected by the request.
- Do not accept an invalid timezone identifier merely because a non-empty string is present.
- Do not describe `deadline_scoped_binding_rule_event_date_bound` as proving legal applicability or substantive trigger satisfaction. It proves only the scoped mechanical inputs used for arithmetic.

## v0.17.0 C5d attack-angle failure modes

- **Source-only allegation:** a legal source, checklist or principle creates an attack angle without a factual/procedural trigger. Reject; source presence is not a violation signal.
- **Deadline laundering:** an exact calculated date is treated as proof of delay. Reject; require an independently adverse `procedure.deadline_state` and preserve deadline applicability review.
- **Proof-list illegality shortcut:** a source-bound document list is treated as unlawful merely because freedom-of-proof material exists. Keep candidate-only unless issue-specific legal/factual review supports more.
- **Unknown competence = incompetence:** missing/unknown authority level or competence is treated as a defect. Reject; only an explicitly adverse competence state with source-backed authority/route material can trigger the core pattern.
- **Lex-specialis contradiction:** coexistence of Directive/Visa Code candidates is treated as non-compliance. Reject; unresolved hierarchy is not an attack angle.
- **GDPR-by-presence:** personal data or a GDPR regime signal alone creates a data-minimisation allegation. Reject until purpose/necessity/excess facts are modeled or a source-backed module pattern exists.
- **Module reviewed-label promotion:** `support_status=reviewed` in a country attack record is treated as established. Keep candidate/review-only because expected prerequisite/disqualifier values are not encoded in contract 0.2.0.
- **Strategy feedback:** route ranking or stratagem logic changes attack-angle output. Reject; C5d is analysis-only and C5e/C5f must remain one-way downstream consumers.

## v0.18.0 C5e handoff/suggestion failure modes

- **Promotion by label:** treating C5d `candidate` or `supported` as automatically safe for strategy. Reject; require the digest-bound review handoff and promotion-grade checks.
- **Module prerequisite presence-as-truth:** promoting a module attack angle because prerequisite element IDs exist. Reject; require complete expected-value semantics and provenance for prerequisite facts.
- **Unknown module route target treated as matched:** using `unknown_frozen_contract` as route compatibility. Reject; do not promote the route.
- **Stratagem-as-authority:** using an original or adapted stratagem to create a fact, legal rule, attack angle, or source weight. Reject.
- **Catalogue feedback:** changing stratagem wording changes C5a-C5d or the handoff. Reject; upstream digests must remain identical.
- **Falsification smuggling:** a proposal depends on a false statement, forged evidence, or fabricated strength while its stratagem is otherwise valid. Block.
- **Disclosure-duty laundering:** informational advantage is used to evade an affirmative disclosure duty. Block explicit conflict; return unknown duty status to analysis.
- **Inaction without waiver/deadline review:** waiting is proposed without checking limitation, waiver, appeal, evidence-loss or other prejudice risk. Return to analysis.
- **Invented support:** suggestion text names an attack angle/route outside the handoff. Block.
- **Premature recommendation:** C5e candidates are presented as ranked advice. Reject; `recommendation_status` remains `not_ranked` until C5f.

## v0.19.0 C5f comparison and sequence failure modes

- **Stale reviewer assessment:** an old review for suggestion ID X is applied after X's text, assumptions or basis changed. Reject unless handoff/C5e context/C5e result hashes match exactly, then replay C5e.
- **Unreviewed candidate suppressed:** only favorable options are put into the ranking context. Reject; every C5e candidate must be dispositioned.
- **Baselines disguised as inapplicable:** a direct/no-action option exists but review ignores it. Reject; require explicit representation and an honest rationale for other baselines.
- **Arbitrary numerical legal score:** ordinal legal-strength labels become false probabilities or binding conclusions. Use Pareto tiers with visible reviewer rationale, never mathematical legal entitlement.
- **Contrary evidence omitted:** known material contrary evidence or unknown adverse effects are counted as support. Exclude or defer and re-enter analysis; never auto-upgrade.
- **Incompatible strategies bundled:** a sequence includes a conflicting pair, unreviewed order, cycle or stale prerequisite. Reject or defer; every sequence is conditional on re-evaluation.
- **Falsification/mandatory disclosure smuggled through a baseline:** direct alternatives receive no exemption from C5e disclosure, falsification or inaction gates.
- **False certainty from reviewer labels:** `identity_assurance=unverified_local` is not professional authentication. A `single_preferred_for_review` status is not permission to execute or legal advice.

## v0.20.0 C6 integrated-release failure modes

- **Second controller or self-promotion:** direct C5 stage labels go to an uncontrolled Markdown document or mark a violation established without controller validation. Reject: use original `propose-analysis`, `validate-analysis`, `release`; C5d allegations remain `cannot_assess` and legal-merits review remains `not_checked`.
- **Forged review-by-tool:** C6 synthesizes a positive reviewer decision from candidate labels, pretends local reviewer identity is authenticated, or rates route power without source-based review. Reject; accept only explicit case/digest-bound review artifacts and report `unverified_local` identity.
- **Silently stale dependency:** an input, module, stage result, script, catalogue, policy, C5e text, C5f baseline or controller revision changes but an old receipt still passes. Reject with verified snapshot/script hashes, exact replay and serialized controller revision checks; do not repair in place.
- **Legal/strategy output mixing:** C5f `single_preferred_for_review` is inserted into controller `recommendations`, or Markdown is appended to an already validated legal report. Reject: zero controlled-analysis recommendations, exactly deterministic rendering and separately verified review-only strategy bytes.
- **Full release from a limited candidate chain:** source freshness, optional/required role gaps or missing substantive review are hidden by a success status. Preserve scoped completeness and block full release; a limited release is not a merits approval.
- **Private case and outbound leakage:** passing test fixtures is treated as proof of host isolation, secure deletion or network authorization. C6 accepts synthetic-only cases, makes no outbound call and verifies neither external delivery nor host privacy.

## v0.21.0 C7 integrity, intake and report hardening

- Do not let caller-edited source-pack `sha256`, `freshness_state` or `authenticity_state` self-certify `current` at the C6 integration boundary. Compare the complete pack and every representation hash to a **code-root-pinned** detached release policy before creating a workspace, then recheck at verification.
- The code-pinned metadata gate does **not** verify absent EU-source representation bytes, official retrieval or live current law; do not describe its successful label as full official-source verification.
- Do not let `privacy_classification=synthetic` serve as authorization for arbitrary case strings, evidence, country-module content or reviewer input. Only bundled digest-enrolled fictional fixtures may enter the C7 test controller. Do not expand this into production privacy claims.
- Do not truncate `unresolved[:12]` or `limitations[:10]` and claim the Markdown is a complete account. Supply the full, digest-bound `issue-index.json` and `issue-index.md` with the limited controlled report; verification must reconstruct all values and pointers from frozen stages.
- A controller `stage=released` without the exact C7 receipt and companion index is an interrupted attempt, **not** proof of successful C7 release. Same-run retry must fail and require a fresh workspace.
- Test mutation, fault/restart, and real-prompt semantic/legal correctness as separate evidence categories; synthetic traces and 107 mock prompts are not independently reviewed legal outcomes.

## v0.21.1 C7 metadata/as-of remediation

- **Run metadata is an input channel.** A trusted case fixture does not authorize arbitrary `--run-id` or `--time-of-check` strings to enter persisted state or reports. Restrict C6 run labels to code-approved opaque identifiers, validate canonical UTC dates, and reject before workspace creation; validate controller-init dates independently as a backstop. Do not claim path-based host isolation.
- **An undated `current` label is not current indefinitely.** Compare the source's pinned verified date against the exact synthetic run date; immutable fixed judgments get chronology checks, while legislation (30d), Commission guidance (14d) and operational pages (7d) receive separate conservative local freshness windows. Reject future/backdated claims and unsupported classifications. These are engineering test windows, not legal currentness guarantees.
- **As-of state must be part of the C6 release identity.** Pin the result in C6 prepared manifest 0.2.1; replay it at release and verification and reject controller timestamp or source-as-of mutation before expensive stage replay.
- **New sources cannot be smuggled into a frozen source pack.** Deldwyn C-477/24 is a candidate for reviewed C1 source-pack 0.6.0+, requiring source identity/text/scope review, source-support mapping and trust-policy release. Do not silently count it as one of the 45 accepted C1 sources.

## v0.24.0 C11a/b value-sensitive legal assessment boundaries

- **Presence-as-breach**: country-module prerequisite element ID or C5d candidate is not evidence that its adverse value occurred. Screen C5d through code-pinned C11 field-value profiles before any controlled candidate projection or strategic handoff.
- **Narrative-date fabrication**: C10 fictional prose mentions an appeal timing but supplies no scoped structured receipt or filing events. Keep the appeal assessment unresolved; do not infer an expiry date or admissibility.
- **Wrong-procedure leakage**: entry-visa rules cannot govern all residence-card matters and vice versa. Type and scope must be explicit before evaluating predicates.
- **Deldwyn generalisation**: a disputed record does not suffice for the former-spouse decisive-evidence disclosure holding; demand specific authority reliance, request/refusal, access impossibility and confidentiality balancing. Charter Article 41 direct addressees must not be misdescribed.
- **Suppressed issue disappearance**: C11 screening can block promotion, not delete unresolved C5d or C11 materials; keep all gaps in the C7 index and bound reports.
- **False legal certainty from predicates**: `supported_for_review` establishes only the profile's input-value match. Legal entitlement, unlawfulness, the rule's force, national exceptions and factual truth are not mechanically established.
- **Review-promotion bypass**: a reviewer passing `validate_for_suggestion` on an angle contradicted/unresolved at C11 must be refused, even if C5e's old C5d-value overlay could otherwise promote it.
- **Code/policy replay hole**: pin the C11 script, closed rule profiles and output schema with C6 code-root hashes, and verify C11 staged JSON, generated report, release receipt and exhaustive index before accepting the released state.

## C12 maintenance note — 2026-10-10

C12 keeps EU rules inside the core and national rule **authoring** in country-owned sidecars; enrolment snapshots under `references/fixtures/c12` exist only to support the frozen C7 synthetic allowlist. Do not treat them as the source of national law or let them become a route to new private cases. The new C12 stage is digest-bound to C5d, source manifest, module export, extensions, evidence ledger and pinned synthetic document registry. Historical C11 country profiles were removed from the active core rule list; C11 remains a conservative EU-only compatibility screen. A successful `supported_for_review` status means the encoded *factual* test is satisfied in controlled fiction, never that the legal merits or authenticity are established. Re-run `scripts/test_c12_rule_resolution.py`, C6/C7 tests, source/matcher tests, and post-package checks after any change. Preserve novel unassessed issue visibility and C7's exact-fixture gate.

## v0.26.0 C13 evidence evaluation failure boundaries

- Never call text extracted from a raw email/PDF a verified authority fact; hash does not establish sender or factual truth.
- Never silently OCR an image-only PDF, flatten ambiguous dates into legal service, or infer a statutory appeal deadline.
- Never promote an unsupported C12 rule merely because a text snippet contains an expected phrase.
- Detect contradictory statements, absent passages, bad UTF-8, PDF extraction gaps, script-hidden HTML, tampering and cross-case document reuse.
- Record lexical false negatives separately from absence of evidence.
- No user-provided documents, no live inbox and no network/host-private-data path are enabled by these tests.


## C23 applicant-facing one-shot failures to guard against

- Rejects or downgrades a user-provided actual case because the C6/C21 synthetic pipeline is not authorised. The controlled script lane is synthetic-only; model guidance in chat is distinct.
- Uses recurring 'not independently verified' labels to avoid analyzing reported consular conduct or proposing evidence preservation and complaint routes.
- Identifies a country-specific ordinary Schengen checklist but fails to compare its **personal scope** with the EU-family exception; inappropriately asks for the officer's exact checklist before deciding the legal exclusion.
- Treats an expired third-country residence permit as proof of unlawful presence, or turns an Article 6 territorial competence question into an ordinary tourism/document requirement.
- Concludes that *every* attempted application had to be admitted irrespective of working hours or consular competence; neglects document receipts, urgency, procedural status and safe written inquiries.
- Interprets mechanical comparator output as proof that a user-provided narrative is correct or that a legal violation is officially established. Tests are not C15f.

## v0.37.0 C24 model-response and update risks

- **One-shot-only correctness:** a scripted comparator passing cannot prove that ChatGPT maps narratives to predicates or changes advice after a user answers. Test recorded replies and follow-ups separately.
- **Silent withdrawal:** a changed cross-border destination, prior residence or family relationship must invalidate the affected rule and remedy; do not restate the earlier answer unchanged.
- **Predicates masquerading as evidence:** user account, source document, reviewer inference and legal text are different provenance classes; the C24 strict categories document mapping but cannot verify testimony.
- **National remedy inventiveness:** the EU source index does not validate national authority powers, national appeal periods or current procedural rules. Keep such routes open until checked.
- **Host privacy overclaim:** feature-only inputs may be linkable; neither the Python gate nor a ChatGPT conversation proves secure real-case intake.

## C25 applicant-strategy and evidence discovery

- Ranking legal hypotheticals by doctrinal interest rather than assessing whether an authority raised them, what it knew, what remedy is sought and whether addressing them proactively backfires.
- Interpreting an adverse fact disclosed in correspondence as an expressly invoked ground, proof an officer read it, or a waiver of statutory competence.
- Letting weakness in the applicant's visa entitlement extinguish an independently actionable conduct/process complaint.
- Demanding CCTV or independent corroboration before assisting with a first-hand misconduct allegation.
- Ignoring GDPR Article 15 access because the applicant never alleged a GDPR breach, or treating it as unlimited document disclosure.
- Treating an access request as a binding preservation order or asserting Article 18 automatically freezes all CCTV.
- Treating the synthetic C25 issue-enumeration report as a legal analysis or independent evidence of model behavior; hidden real-model tests remain outstanding.
- Restoring Romanian/UAE worked facts to normal-use guidance and thereby anchoring future unrelated cases to territorial competence.

## C26 repair: applicant strategy evaluation risks (2026-10-11)

- **Event deduplication hides harm:** two reported acts map to one broad grievance label. Require event-specific review before grouping the final complaint.
- **GDPR-by-token:** `gdpr_access_considered` is selected but the applicant receives no scoped, targeted access step; test route, likely controller, data categories, limitations and separate urgency.
- **Authority-position self-certification:** a fictional `expressly_invoked` label is not proof a consul invoked that ground. Require human comparison to authority-source passages and chronology in recorded replies.
- **Positive-trigger scope drift:** a generic tourist-visa or CCTV dispute without an EU-family context must not be counted as successful eudirective Core activation.
- **Mock greenwashing:** source-byte and unit tests are not legal-semantic certification or first-response evidence; keep live-response grading pending.
