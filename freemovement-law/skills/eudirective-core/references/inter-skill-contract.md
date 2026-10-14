# Inter-skill contract v0.2.0

## Status

C3 frozen development contract. Compatible producer modules may evolve internally, but exports consumed by this core must conform to contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, and element model `0.2.0`.

This is not the eventual portfolio v1.0 contract. Breaking changes before I3 require an explicit contract-version bump and migration evidence.

## Module families

- `core_source`: reusable EU/common source substrate. Jurisdiction `EU`, namespace `eu`, role `common_eu`.
- `member_state`: national law, procedure, institutions, deadlines, remedies, and national attack-angle contributions.
- `applicant_country`: place-of-application operations, mission/VAC evidence, local routes, and local operational attack-angle contributions.

Country modules are data providers. They do not call each other and they do not ship executable logic.

## Manifest identity and compatibility

Every manifest declares:

- `contract_version`;
- `module_family`, `module_id`, `id_namespace`, and `jurisdiction`;
- `module_version` and `pack_version`;
- `freshness_state`;
- `supported_domains` and `supported_roles`;
- explicit `known_gap_ids` that resolve to exported gap records;
- dataset versions, including attack-angle data;
- compatibility with the conformance profile, controller protocol, and element model;
- `data_classification: reusable_non_case`.

Member-State and applicant-country namespaces must equal the lowercase jurisdiction code used by the module. The core source module uses namespace `eu`.

## Role-sensitive composition

A module request is accepted only when its jurisdiction agrees with the corresponding typed geography field for that role. It is satisfied only when family, jurisdiction, and requested role all match. Applicant-country requests additionally name a `destination_state`; that state must agree with the case destination topology and the module must advertise a matching destination-state profile.

Supported Member-State roles are:

- `residence_state`;
- `work_state`;
- `intended_residence_state`;
- `deciding_state`;
- `representing_state`;
- `challenged_authority_state`;
- `document_issuing_state`.

Supported applicant-country roles are `application_context` and `mission_context`.

The core may load more than one Member-State module. A frontier-worker topology must keep residence, work, application, deciding, and other roles distinct even where two roles happen to use the same jurisdiction. Two registered modules may not both claim the same family + jurisdiction + role coverage; ambiguous producers are rejected rather than selected by load order.

## Export record classes

Contract `0.2.0` exports typed records for:

- sources;
- rules;
- authorities;
- gaps;
- operational observations;
- deadlines;
- routes/remedies;
- attack-angle contributions.

Case-specific element instances remain a separate `element-instance-bundle` contract. Country modules do not store applicant case data in reusable exports.

## Legal-layer boundary

Every rule declares `normative_layer`:

- core: `eu_common` only;
- Member State: `national` only;
- applicant country: `local_operational` only.

Every attack-angle contribution declares the corresponding `basis_layer` under the same family boundary.

This prevents a country module from acquiring EU legal hierarchy merely by declaring a rule. National rules may conflict with EU law; the conflict is analysed by the core rather than resolved by export order.

## Source and representation semantics

`authoritative_bundled_text + verified_official` supports exact-text semantics subject to ordinary analysis safeguards.

`verified_source_note + verified_identity_version` is usable identity/version-aware support but not verbatim text. A note-backed reviewed/candidate rule must declare `support_scope`. `direct_text` requires an explicit `text_source_ref` resolving to full verified text.

Unknown, reference-only, or candidate source representations cannot support executable legal records.

## Gaps and conflicts

Manifest gaps are IDs, not free-floating prose. Every `known_gap_id` must resolve to a `gap_record`, and every exported gap must be declared by the manifest.

Gap records preserve:

- area and scope;
- impact (`blocking`, `degrading`, `informational`);
- status, including `conflicting_information` and `insufficient_evidence`;
- detail.

Semantic conflicts are never silently resolved by module order. If they cannot be represented mechanically, preserve them as explicit gaps/completeness states for core review. Shared runtime completeness serialization uses `references/contracts/completeness-record.schema.json`; status and reason remain separate so absence, non-applicability, insufficient evidence, conflicts, and unsupported automation cannot collapse into a generic no-problem result.

## Global identity and collision policy

All reusable record IDs must use the module namespace. IDs are unique across record classes within a module. The controller also rejects duplicate reusable IDs across registered modules.

A module cannot override another module by reusing its record ID. Applicant-country operational records that name a destination state must stay within the destination profiles declared by that module.

## Controlled-analysis reference boundary

Controlled analysis may reference reusable module records only through registered IDs. Findings carry source/rule/authority plus route and attack-angle references; deadline outputs carry explicit deadline-record references; recommendations may reference routes and attack angles. Unknown reusable IDs are rejected before release. This keeps composition traceable without treating schema validity as legal truth.

## Version behavior

The current C3 controller accepts contract `0.2.0` only. A module must explicitly advertise compatibility with controller protocol `0.3.0`, element model `0.2.0`, and conformance profile `0.2.0`.

No silent downgrade, nearest-version guessing, or best-effort coercion is permitted.

## Assurance boundary

Conformance proves serialization, declared ownership, compatibility, reference integrity, role compatibility, and selected composition invariants. It does not prove substantive legal truth, semantic entailment, currentness beyond recorded freshness evidence, anonymity, or host-enforced privacy.

## C5a consumption note

Skill v0.14.0 uses standalone C5a topology/applicability candidate artifacts without changing contract `0.2.0`. Producer modules do not need new fields for C5a. The engines consume the existing typed case geography, element-instance bundle and module-role boundary; a local optional `actor-context` artifact scopes applicant/relevant-Union-citizen identity for family-member candidate generation without changing producer exports; national-law content remains in Member-State exports. A future contract change is required only if real integration proves the frozen interface cannot represent a necessary producer-side fact.


## C5b local consumer overlay

Skill v0.15.0 adds standalone C5b hierarchy/principle artifacts without changing contract `0.2.0`. Producer modules do not gain executable logic or new mandatory fields. When C5b asks an EU/national hierarchy question, it consumes an already-conformant Member-State `rule_record` and verifies that the module is case-relevant by jurisdiction and supported role. C5b binds module manifest/export digests but does not rewrite producer data or infer national law not present in the module.


## C5c standalone consumer boundary (skill v0.16.1)

Skill v0.16.1 retains the standalone C5c evidence/deadline/authority-route artifacts without changing contract `0.2.0`. Producer modules gain no new mandatory fields and no executable logic. C5c consumes already-conformant `source_records`, `rule_records`, `deadline_records`, `authority_records`, and `route_records`; verifies case relevance and exact manifest/export digests; and preserves module data as candidate/review inputs. The frozen module contract still does not encode a normalized authority-level field, so C5c must not infer authority level from module family or geography.

## C5d standalone consumer boundary (skill v0.17.0)

Skill v0.17.0 adds standalone C5d attack-angle synthesis without changing contract `0.2.0`. Producer modules gain no new mandatory fields or executable logic. C5d replays every country module already bound by C5c and may consume existing conformant `attack_angle_records`, but the frozen record format lists prerequisite/disqualifier element IDs without expected-value semantics. The core therefore keeps module attack records candidate/review-only unless a future contract explicitly adds typed value conditions. C5d never rewrites module records, infers missing national law, ranks remedies or exposes stratagem logic to producers.

## C5e downstream consumer boundary (skill v0.18.0)

Skill v0.18.0 adds no producer-module fields and does not change inter-skill contract `0.2.0` or conformance profile `0.2.0`. C5e consumes C5d/C5c plus a local review overlay. Where frozen module `attack_angle_records` provide only prerequisite/disqualifier element IDs, the local handoff may supply explicit expected-value checks against the already-bound element bundle; those checks are core-side review metadata and do not alter the producer contract. Module routes left at `target_authority_level_validation=unknown_frozen_contract` remain non-promotable for suggestion use.

The suggestion layer receives only promoted IDs and metadata through the analysis handoff. Country modules never receive stratagem catalogues, never execute suggestion logic, and never call each other. Catalogue changes are downstream-only and cannot alter producer conformance or legal-analysis results.
