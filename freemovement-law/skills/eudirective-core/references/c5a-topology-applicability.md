# C5a topology and legal-regime applicability

## Status

C5a engine/ruleset version `0.1.1` is implemented in `eudirective-core` v0.14.0 while preserving the frozen C3 producer boundary: inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, and element model `0.2.0` remain unchanged.

C5a has two one-way stages:

1. `topology_engine.py` binds distinct geographic roles and structural movement contexts.
2. `regime_applicability.py` consumes that bound topology plus the same element bundle and emits legal-regime **candidates**, blocked states, interaction flags, actor-scope state, and unresolved gaps.

Neither stage emits a final legal conclusion.

## Topology stage

The topology engine consumes a validated `case-input` and, when supplied, a validated `element-instance-bundle`. It keeps these roles distinct:

- nationality state;
- residence state;
- work state;
- host state;
- intended residence state;
- application country;
- deciding state;
- representing state;
- document-issuing state;
- challenged-authority state.

Known country-name and alpha-3 aliases are canonicalized through `references/jurisdictions/country-aliases.json` to ISO 3166-1 alpha-2 identifiers before jurisdiction equality checks. The topology output binds the registry version and SHA-256 digest and records any changed representation in `jurisdiction_normalizations`. Unknown labels remain explicit raw identifiers rather than being guessed.

Case-input geography and element-bundle geography are bound by exact digest. If both provide the same role and remain different after deterministic canonicalization, the topology result is `blocked`; the engine does not choose one silently.

A different residence/work state creates only a `cross_border_work=candidate` structural signal. It does not establish legal frontier-worker status. `movement.frontier_worker_context` is a separate contextual assertion and cannot erase the structural geography. If `frontier_worker_context=false` conflicts with different residence/work states, C5a preserves the structural candidate and adds `frontier_context_conflicts_with_structural_topology` for review.

Returnee status is stricter: C5a does not infer it from nationality/host/target geography alone. `movement.returnee_context=true` must be present before a returnee candidate is emitted.

Module requests are checked against the same canonicalized topology. A role/jurisdiction or applicant destination mismatch blocks the topology result instead of being relabelled silently.

## Actor scope for family-member cases

The frozen element model contains singleton person-status elements and therefore cannot by itself identify which person a value belongs to when a case contains both a non-EU applicant and a relevant Union citizen.

C5a v0.14.0 fixes that ambiguity with a local, optional `actor-context` artifact. This does **not** change the frozen producer contract or element model. The actor-context schema binds:

- one applicant actor;
- one relevant Union-citizen actor;
- actor-scoped `person_status.eu_citizen_status`;
- actor-scoped `person_status.family_member_status` where relevant;
- actor-scoped `relationship.accompanying_or_joining` where relevant.

For a family-member case, pass the actor context with `--actors`. The applicability output binds its exact digest as `bound_actor_context_sha256` and reports the resolved `actor_scope`.

If family-member/accompanying signals are present but no actor context is supplied, C5a fails closed with `actor_scope_required_for_family_member_case`. It does not assign a generic positive or negative EU-citizen-status value to either the applicant or the Union citizen by guesswork.

For a direct-person case with no family-member ambiguity, the legacy singleton `person_status.eu_citizen_status` path remains available for backward compatibility.

## Applicability-candidate stage

The applicability engine is bound to:

- the exact case digest;
- the exact topology digest, which itself binds the jurisdiction-registry version/digest;
- the exact element-bundle digest used by topology;
- the optional exact actor-context digest;
- the exact bundled C1 source-pack manifest digest.

It emits exactly four current model-backed framework candidates:

- `legal_regime.directive_2004_38`;
- `legal_regime.visa_code`;
- `legal_regime.schengen`;
- `legal_regime.national_procedure`.

Candidate dispositions are `candidate`, `not_indicated`, `blocked`, or `unknown`. The top-level `final_applicability` is always `not_determined` in C5a.

For the relevant Union-citizen actor, recognized positive tokens are `established`, `eu_citizen_established`, and `confirmed`; recognized negative tokens are `not_established`, `not_eu_citizen`, and `excluded`. Any other or missing value blocks the Directive candidate rather than guessing. Actor-scoped family-member candidate generation additionally requires a recognized family-member status and `accompanying_or_joining=true` for the scoped applicant/Union-citizen pair.

Visa/Schengen relevance is generated from a visa/entry procedure label as a review candidate. Where a Directive candidate and Visa Code candidate coexist, C5a emits `directive_visa_code_lex_specialis=review_required`. C5a does not resolve hierarchy or lex specialis; that belongs to C5b.

National procedure is represented only as a candidate plus Member-State role hints. C5a does not synthesize national legal content.

## Returnee/Article 21 handling

C5a preserves an explicit returnee context in a separate `returnee_review` record rather than inventing a new frozen-contract regime element. When `movement.returnee_context=true` and `movement.free_movement_exercised=true`, the record becomes `candidate` and remains review-required.

The current C1 pack contains Commission free-movement guidance but no dedicated primary-TFEU source record for the returnee proposition. C5a therefore exposes `returnee_primary_tfeu_source_gap` rather than pretending the primary-law basis is fully represented. C5b/source maintenance can resolve that gap later.

## Source-hint semantics

`source_hint_refs` identify bundled EU/common sources that are plausibly relevant to the candidate. They are discovery/provenance hints only. They do not prove entailment, applicability, exact wording, or legal correctness.

Current hints include:

- Directive 2004/38: `eu:32004l0038`, `eu:c-2023-1392`;
- Visa Code: `eu:32009r0810`, `eu:visa-code-handbook-i-2024`;
- Schengen/visa-list context: `eu:32016r0399`, `eu:32018r1806`;
- returnee review: `eu:c-2023-1392`, with an explicit primary-source gap.

## Commands

Build topology:

```bash
python scripts/topology_engine.py case.json --elements elements.json --output topology.json
```

Build applicability candidates for a direct-person case:

```bash
python scripts/regime_applicability.py case.json topology.json --elements elements.json --output regimes.json
```

Build applicability candidates for a family-member case with explicit actor scope:

```bash
python scripts/regime_applicability.py case.json topology.json --elements elements.json --actors actors.json --output regimes.json
```

Validate inputs/outputs independently:

```bash
python scripts/contract_validate.py --schema actor-context actors.json
python scripts/contract_validate.py --schema topology-resolution topology.json
python scripts/contract_validate.py --schema legal-regime-candidates regimes.json
```

## Assurance limits

C5a proves deterministic binding, role separation, selected structural candidate rules, deterministic jurisdiction canonicalization for the bundled alias registry, source-hint existence, explicit family-member actor scoping, and fail-closed handling of conflicting/missing normalized inputs. It does not prove substantive Directive/Visa Code/Schengen/national-law applicability, frontier-worker status, returnee rights, Article 21 TFEU effects, hierarchy/lex-specialis outcomes, or applicant-facing legal correctness.

The jurisdiction registry is a deterministic identity aid, not a legal statement about territorial status, EU/Schengen participation, sovereignty, or recognition. Unknown labels remain explicit rather than being silently mapped.

C5a outputs are not yet controller-authoritative legal findings. C6 integration must consume them through a controlled-analysis gate rather than copying candidate labels directly into released prose.
