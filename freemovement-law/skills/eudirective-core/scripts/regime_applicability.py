#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import element_model as em

from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = compatibility_root() / "core-source-pack-manifest-0.6.1.json"
ENGINE_VERSION = "0.1.1"
RULESET_VERSION = "0.1.1"
ACTOR_CONTEXT_VERSION = "0.1.0"
CONTRACT_VERSION = "0.2.0"
ELEMENT_MODEL_VERSION = "0.2.0"

EU_STATUS_POSITIVE = {"established", "eu_citizen_established", "confirmed"}
EU_STATUS_NEGATIVE = {"not_established", "not_eu_citizen", "excluded"}
FAMILY_STATUS_POSITIVE = {"established", "family_member_established", "confirmed", "claimed"}

class RegimeError(Exception):
    pass

def index_elements(bundle):
    out = {}
    if bundle is None:
        return out
    for item in bundle["elements"]:
        out.setdefault(item["element_id"], []).append(item)
    return out

def single_value(idx, element_id):
    entries = idx.get(element_id, [])
    if not entries:
        return None
    if len(entries) != 1:
        raise RegimeError(f"multiple_values_for_singleton:{element_id}")
    return entries[0]["value"]


def validate_actor_context(actor_context, case_id):
    if actor_context is None:
        return None
    validate_obj("actor-context", actor_context)
    if actor_context["case_id"] != case_id:
        raise RegimeError("actor_context_case_binding_mismatch")
    actor_ids = []
    for actor in actor_context["actors"]:
        if actor["actor_id"] in actor_ids:
            raise RegimeError(f"duplicate_actor_id:{actor['actor_id']}")
        actor_ids.append(actor["actor_id"])
    actor_set = set(actor_ids)
    seen = set()
    for item in actor_context["scoped_elements"]:
        if item["actor_id"] not in actor_set:
            raise RegimeError(f"actor_context_unknown_actor:{item['actor_id']}")
        related = item.get("related_actor_id")
        if related is not None and related not in actor_set:
            raise RegimeError(f"actor_context_unknown_related_actor:{related}")
        key = (item["element_id"], item["actor_id"], related)
        if key in seen:
            raise RegimeError("duplicate_actor_scoped_element:" + ":".join(str(x) for x in key))
        seen.add(key)
    return actor_context

def actor_ids_by_role(actor_context, role):
    if actor_context is None:
        return []
    return [a["actor_id"] for a in actor_context["actors"] if role in a["roles"]]

def scoped_value(actor_context, element_id, actor_id, related_actor_id=None):
    if actor_context is None or actor_id is None:
        return None
    matches = []
    for item in actor_context["scoped_elements"]:
        if item["element_id"] != element_id or item["actor_id"] != actor_id:
            continue
        if item.get("related_actor_id") != related_actor_id:
            continue
        matches.append(item)
    if not matches:
        return None
    if len(matches) != 1:
        raise RegimeError(f"multiple_actor_scoped_values:{element_id}:{actor_id}:{related_actor_id}")
    return matches[0]["value"]

def resolve_actor_scope(actor_context):
    if actor_context is None:
        return {
            "status":"legacy_unscoped",
            "applicant_actor_id":None,
            "union_citizen_actor_id":None,
            "relationship_kind":"unknown",
            "review_required":True,
            "detail":"No actor-scoped C5a context is bound; legacy singleton person-status elements can only be used where no family-member actor ambiguity is present."
        }, None
    applicants = actor_ids_by_role(actor_context, "applicant")
    union_citizens = actor_ids_by_role(actor_context, "union_citizen")
    if len(applicants) != 1 or len(union_citizens) != 1:
        detail = f"Actor-scoped C5a context requires exactly one applicant and one relevant Union-citizen actor; found applicants={len(applicants)}, union_citizens={len(union_citizens)}."
        return {
            "status":"blocked",
            "applicant_actor_id":applicants[0] if len(applicants)==1 else None,
            "union_citizen_actor_id":union_citizens[0] if len(union_citizens)==1 else None,
            "relationship_kind":"unknown",
            "review_required":True,
            "detail":detail
        }, "actor_scope_ambiguous"
    applicant = applicants[0]
    union = union_citizens[0]
    relationship_kind = "self" if applicant == union else "family_member"
    return {
        "status":"scoped",
        "applicant_actor_id":applicant,
        "union_citizen_actor_id":union,
        "relationship_kind":relationship_kind,
        "review_required":False,
        "detail":"C5a actor scope binds the applicant and relevant Union-citizen actor explicitly."
    }, None

def normal_token(value):
    if value is None:
        return None
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")

def visa_related(procedure_type):
    token = normal_token(procedure_type) or ""
    return "visa" in token.split("_") or token in {"entry_visa", "short_stay", "short_stay_entry"}

def target_module_roles(topology):
    roles = topology["roles"]
    hints = []
    for role in ["deciding_state", "challenged_authority_state", "intended_residence_state", "residence_state", "work_state"]:
        if roles.get(role) is not None:
            hints.append(role)
    return sorted(set(hints))

def candidate(element_id, kind, disposition, rationale, deps=None, missing=None, sources=None, roles=None, limitations=None, review=True):
    return {
        "element_id": element_id,
        "candidate_kind": kind,
        "disposition": disposition,
        "review_required": review,
        "rationale_codes": sorted(set(rationale or [])),
        "dependency_element_ids": sorted(set(deps or [])),
        "missing_element_ids": sorted(set(missing or [])),
        "source_hint_refs": sorted(set(sources or [])),
        "module_role_hints": sorted(set(roles or [])),
        "limitations": sorted(set(limitations or [])),
    }

def build_candidates(case_obj, topology, element_bundle=None, source_manifest=None, actor_context=None):
    validate_obj("case-input", case_obj)
    validate_obj("topology-resolution", topology)
    if case_obj["privacy_classification"] == "private":
        raise RegimeError("private_data_disabled")
    if topology["case_id"] != case_obj["case_id"] or topology["bound_case_sha256"] != digest_obj(case_obj):
        raise RegimeError("topology_case_binding_mismatch")

    actor_context = validate_actor_context(actor_context, case_obj["case_id"])
    actor_context_digest = digest_obj(actor_context) if actor_context is not None else None
    actor_scope, actor_scope_error = resolve_actor_scope(actor_context)

    idx = {}
    bundle_digest = None
    if element_bundle is not None:
        catalog, _, invariants = em.load_model()
        em.check_bundle(element_bundle, catalog, invariants)
        bundle_digest = digest_obj(element_bundle)
        idx = index_elements(element_bundle)
    if topology["bound_element_bundle_sha256"] != bundle_digest:
        raise RegimeError("topology_element_bundle_binding_mismatch")

    if source_manifest is None:
        source_manifest = load_json(SOURCE_MANIFEST)
    validate_obj("core-source-pack", source_manifest)
    source_ids = {x["source_id"] for x in source_manifest["sources"]}
    source_pack_version = source_manifest["pack_version"]

    required_source_hints = {
        "eu:32004l0038",
        "eu:c-2023-1392",
        "eu:32009r0810",
        "eu:visa-code-handbook-i-2024",
        "eu:32016r0399",
        "eu:32018r1806",
    }
    missing_hints = sorted(required_source_hints - source_ids)
    if missing_hints:
        raise RegimeError("source_hint_missing:" + ",".join(missing_hints))

    unresolved = []
    topology_blocked = topology["resolution_status"] == "blocked"
    legacy_eu_status_raw = single_value(idx, "person_status.eu_citizen_status")
    legacy_eu_status = normal_token(legacy_eu_status_raw)
    legacy_family_status_raw = single_value(idx, "person_status.family_member_status")
    legacy_accompanying = single_value(idx, "relationship.accompanying_or_joining")
    movement_cross_border = single_value(idx, "movement.cross_border")
    free_movement = single_value(idx, "movement.free_movement_exercised")
    returnee_status = topology["contexts"]["returnee"]["status"]
    cross_work_status = topology["contexts"]["cross_border_work"]["status"]

    movement_indicated = movement_cross_border is True or free_movement is True or cross_work_status == "candidate" or returnee_status == "candidate"
    movement_explicit_negative = movement_cross_border is False and free_movement is False and cross_work_status != "candidate" and returnee_status != "candidate"

    scoped_eu_status_raw = None
    scoped_eu_status = None
    scoped_family_status_raw = None
    scoped_family_status = None
    scoped_accompanying = None
    if actor_scope["status"] == "scoped":
        applicant_actor = actor_scope["applicant_actor_id"]
        union_actor = actor_scope["union_citizen_actor_id"]
        scoped_eu_status_raw = scoped_value(actor_context, "person_status.eu_citizen_status", union_actor)
        scoped_eu_status = normal_token(scoped_eu_status_raw)
        if actor_scope["relationship_kind"] == "family_member":
            scoped_family_status_raw = scoped_value(actor_context, "person_status.family_member_status", applicant_actor, union_actor)
            scoped_family_status = normal_token(scoped_family_status_raw)
            scoped_accompanying = scoped_value(actor_context, "relationship.accompanying_or_joining", applicant_actor, union_actor)

    legacy_family_ambiguity = actor_context is None and (legacy_family_status_raw is not None or legacy_accompanying is not None)

    if topology_blocked:
        directive = candidate(
            "legal_regime.directive_2004_38", "direct_framework", "blocked",
            ["topology_blocked"], sources=["eu:32004l0038", "eu:c-2023-1392"],
            limitations=["Conflicting topology must be resolved before applicability review."]
        )
    elif actor_scope_error is not None:
        directive = candidate(
            "legal_regime.directive_2004_38", "direct_framework", "blocked",
            [actor_scope_error], sources=["eu:32004l0038", "eu:c-2023-1392"],
            limitations=["Resolve applicant/relevant-Union-citizen actor scope before Directive candidate generation."]
        )
        unresolved.append({"code":actor_scope_error,"scope":"legal_regime.directive_2004_38","detail":actor_scope["detail"]})
    elif legacy_family_ambiguity:
        directive = candidate(
            "legal_regime.directive_2004_38", "direct_framework", "blocked",
            ["actor_scope_required_for_family_member_case"],
            deps=["person_status.eu_citizen_status","person_status.family_member_status","relationship.accompanying_or_joining"],
            sources=["eu:32004l0038", "eu:c-2023-1392"],
            limitations=["Unscoped singleton person-status elements cannot establish which actor is the relevant Union citizen in a family-member case. Bind an actor-context artifact."]
        )
        unresolved.append({
            "code":"actor_scope_required_for_family_member_case",
            "scope":"legal_regime.directive_2004_38",
            "detail":"Family-member/accompanying signals are present without actor scope. C5a refuses to treat a generic negative or positive EU-citizen-status value as belonging to either the applicant or the relevant Union citizen."
        })
    else:
        use_scoped = actor_scope["status"] == "scoped"
        eu_status_raw = scoped_eu_status_raw if use_scoped else legacy_eu_status_raw
        eu_status = scoped_eu_status if use_scoped else legacy_eu_status
        deps = ["person_status.eu_citizen_status"]
        rationale_prefix = ["actor_scoped_union_citizen"] if use_scoped else ["legacy_unscoped_direct_person"]

        relationship_block = None
        relationship_rationale = []
        if use_scoped and actor_scope["relationship_kind"] == "family_member":
            deps += ["person_status.family_member_status", "relationship.accompanying_or_joining"]
            if scoped_family_status_raw is None:
                relationship_block = ("family_member_status_missing", ["person_status.family_member_status"])
            elif scoped_family_status not in FAMILY_STATUS_POSITIVE:
                relationship_block = ("family_member_status_not_established", [])
            elif scoped_accompanying is not True:
                relationship_block = ("accompanying_or_joining_not_established", ["relationship.accompanying_or_joining"] if scoped_accompanying is None else [])
            else:
                relationship_rationale = ["actor_scoped_family_relationship", "accompanying_or_joining_true"]

        if relationship_block is not None:
            code, missing = relationship_block
            directive = candidate(
                "legal_regime.directive_2004_38", "direct_framework", "blocked",
                rationale_prefix + [code], deps=deps, missing=missing,
                sources=["eu:32004l0038", "eu:c-2023-1392"],
                limitations=["The actor-scoped family relationship must be sufficiently established before C5a can emit a Directive family-member candidate."]
            )
            unresolved.append({"code":code,"scope":"legal_regime.directive_2004_38","detail":"Actor scope is present, but the family-member/accompanying relationship is incomplete or not normalized for candidate generation."})
        elif eu_status in EU_STATUS_NEGATIVE:
            directive = candidate(
                "legal_regime.directive_2004_38", "direct_framework", "not_indicated",
                rationale_prefix + ["relevant_union_citizen_status_negative"], deps=deps,
                sources=["eu:32004l0038", "eu:c-2023-1392"], review=False
            )
        elif eu_status not in EU_STATUS_POSITIVE:
            status_missing = eu_status_raw is None
            directive = candidate(
                "legal_regime.directive_2004_38", "direct_framework", "blocked",
                rationale_prefix + ["relevant_union_citizen_status_missing" if status_missing else "relevant_union_citizen_status_not_normalized"],
                deps=deps, missing=["person_status.eu_citizen_status"] if status_missing else [],
                sources=["eu:32004l0038", "eu:c-2023-1392"],
                limitations=["C5a recognizes only explicit normalized positive Union-citizen-status tokens: established, eu_citizen_established, confirmed."]
            )
            unresolved.append({
                "code":"relevant_union_citizen_status_required" if status_missing else "relevant_union_citizen_status_not_normalized",
                "scope":"legal_regime.directive_2004_38",
                "detail":"A normalized, provenance-bearing status for the relevant Union-citizen actor is required before C5a can produce a Directive 2004/38 candidate."
            })
        elif movement_indicated:
            rationale = rationale_prefix + relationship_rationale + ["relevant_union_citizen_status_positive", "qualifying_movement_signal_present"]
            if returnee_status == "candidate":
                rationale.append("returnee_context_requires_derived_right_review")
            directive = candidate(
                "legal_regime.directive_2004_38", "direct_framework", "candidate",
                rationale, deps=deps + ["movement.cross_border", "movement.free_movement_exercised", "movement.returnee_context"],
                sources=["eu:32004l0038", "eu:c-2023-1392"],
                limitations=["Candidate status is not a finding that the Directive applies to the scoped person/procedure."]
            )
        elif movement_explicit_negative:
            directive = candidate(
                "legal_regime.directive_2004_38", "direct_framework", "blocked",
                rationale_prefix + relationship_rationale + ["qualifying_movement_not_established"],
                deps=deps + ["movement.cross_border", "movement.free_movement_exercised"],
                missing=[], sources=["eu:32004l0038", "eu:c-2023-1392"],
                limitations=["An explicit negative movement signal does not by itself prove legal non-applicability; C5a therefore blocks rather than concludes not applicable."]
            )
        else:
            directive = candidate(
                "legal_regime.directive_2004_38", "direct_framework", "blocked",
                rationale_prefix + relationship_rationale + ["qualifying_movement_signal_missing"], deps=deps,
                missing=["movement.cross_border"], sources=["eu:32004l0038", "eu:c-2023-1392"]
            )

    is_visa = visa_related(case_obj["procedure_type"])
    visa = candidate(
        "legal_regime.visa_code", "procedural_framework",
        "candidate" if is_visa else "not_indicated",
        ["visa_procedure_label"] if is_visa else ["non_visa_procedure_label"],
        deps=["procedure.type"],
        sources=["eu:32009r0810", "eu:visa-code-handbook-i-2024"],
        limitations=["C5a marks procedural relevance only; C5b must resolve any lex-specialis interaction with free-movement law."],
        review=is_visa
    )
    schengen = candidate(
        "legal_regime.schengen", "procedural_framework",
        "candidate" if is_visa else "not_indicated",
        ["visa_or_entry_context"] if is_visa else ["no_schengen_entry_signal"],
        deps=["procedure.type"],
        sources=["eu:32016r0399", "eu:32018r1806"],
        limitations=["This candidate does not determine territorial participation, border conditions, or visa exemption status."],
        review=is_visa
    )

    module_hints = target_module_roles(topology)
    national = candidate(
        "legal_regime.national_procedure", "national_supplement",
        "candidate" if module_hints else "blocked",
        ["national_decision_or_procedure_role_present"] if module_hints else ["national_role_missing"],
        deps=["procedure.type"],
        missing=[] if module_hints else ["geography.deciding_state"],
        roles=module_hints,
        limitations=["National-law content must come from the matching Member-State module; C5a does not invent national rules."],
        review=True
    )

    if returnee_status == "candidate":
        if free_movement is True:
            returnee_review = {
                "status":"candidate",
                "rationale_codes":["returnee_context_asserted","free_movement_exercised_true"],
                "missing_element_ids":[],
                "source_hint_refs":["eu:c-2023-1392"],
                "primary_source_gap":True,
                "review_required":True,
                "detail":"A derived returnee/free-movement review is indicated. C5a does not decide Article 21 TFEU/returnee rights; the current C1 pack lacks a dedicated primary-TFEU source record for that proposition."
            }
            unresolved.append({
                "code":"returnee_primary_tfeu_source_gap",
                "scope":"movement.returnee_context",
                "detail":"The source pack provides current Commission guidance but no dedicated primary-TFEU source record for the returnee proposition. Preserve this as a source/legal-basis gap for later legal review."
            })
        elif free_movement is False:
            returnee_review = {
                "status":"blocked",
                "rationale_codes":["returnee_context_asserted","free_movement_exercised_false"],
                "missing_element_ids":[],
                "source_hint_refs":["eu:c-2023-1392"],
                "primary_source_gap":True,
                "review_required":True,
                "detail":"The asserted returnee context conflicts with free_movement_exercised=false; resolve the factual/legal premise before any derived-right assessment."
            }
        else:
            returnee_review = {
                "status":"blocked",
                "rationale_codes":["returnee_context_asserted","free_movement_exercise_unresolved"],
                "missing_element_ids":["movement.free_movement_exercised"],
                "source_hint_refs":["eu:c-2023-1392"],
                "primary_source_gap":True,
                "review_required":True,
                "detail":"Returnee context is asserted, but qualifying prior free movement is not established in the bound elements."
            }
    elif returnee_status == "not_indicated":
        returnee_review = {
            "status":"not_indicated","rationale_codes":["returnee_context_false"],"missing_element_ids":[],
            "source_hint_refs":["eu:c-2023-1392"],"primary_source_gap":False,"review_required":False,
            "detail":"The bound topology explicitly records no returnee context."
        }
    else:
        returnee_review = {
            "status":"unknown","rationale_codes":["returnee_context_not_established"],"missing_element_ids":["movement.returnee_context"],
            "source_hint_refs":["eu:c-2023-1392"],"primary_source_gap":False,"review_required":True,
            "detail":"C5a does not infer returnee status from geography alone."
        }

    if is_visa and directive["disposition"] == "candidate":
        lex_status = "review_required"
        lex_detail = "Both Directive 2004/38 and Visa Code candidates are present. C5a preserves the interaction; C5b must resolve hierarchy/lex-specialis effects."
    elif is_visa and directive["disposition"] in {"blocked", "unknown"}:
        lex_status = "blocked"
        lex_detail = "Visa Code relevance is indicated but the free-movement candidate is unresolved, so hierarchy/lex-specialis review cannot yet be completed."
    else:
        lex_status = "not_indicated"
        lex_detail = "The current candidate set does not require a Directive/Visa-Code hierarchy comparison."

    out = {
        "engine_version": ENGINE_VERSION,
        "ruleset_version": RULESET_VERSION,
        "contract_version": CONTRACT_VERSION,
        "element_model_version": ELEMENT_MODEL_VERSION,
        "case_id": case_obj["case_id"],
        "bound_case_sha256": digest_obj(case_obj),
        "bound_topology_sha256": digest_obj(topology),
        "bound_element_bundle_sha256": bundle_digest,
        "bound_actor_context_sha256": actor_context_digest,
        "actor_scope": actor_scope,
        "source_pack_version": source_pack_version,
        "source_pack_sha256": digest_obj(source_manifest),
        "resolution_status": "blocked" if topology_blocked else "ready",
        "final_applicability": "not_determined",
        "candidates": sorted([directive, visa, schengen, national], key=lambda x: x["element_id"]),
        "returnee_review": returnee_review,
        "interactions": [{
            "interaction_id":"directive_visa_code_lex_specialis",
            "status":lex_status,
            "candidate_element_ids":["legal_regime.directive_2004_38","legal_regime.visa_code"],
            "detail":lex_detail
        }],
        "unresolved": unresolved + ([{
            "code":"topology_blocked","scope":"case_topology","detail":"Resolve C5a topology conflicts before relying on any regime candidate."
        }] if topology_blocked else []),
        "limitations": [
            "C5a emits applicability candidates and blocked/unknown states only; it never emits a final 'applicable' legal conclusion.",
            "Source hints identify potentially relevant bundled EU/common materials; they are not entailment proof for a candidate.",
            "Hierarchy, lex-specialis effects, Charter scope, and substantive returnee/Article 21 analysis are deferred to later legal-engine stages.",
            "National-law content remains owned by Member-State modules and is represented here only as a module-role hint.",
            "Family-member Directive candidates require explicit applicant/relevant-Union-citizen actor scope; legacy unscoped singleton person-status elements are accepted only where no family-member actor ambiguity is present."
        ]
    }
    validate_obj("legal-regime-candidates", out)
    return out

def main():
    ap = argparse.ArgumentParser(description="Build C5a legal-regime applicability candidates from a bound case/topology pair")
    ap.add_argument("case")
    ap.add_argument("topology")
    ap.add_argument("--elements")
    ap.add_argument("--actors", help="Optional C5a actor-context JSON for applicant/relevant-Union-citizen scoping")
    ap.add_argument("--source-manifest", default=str(SOURCE_MANIFEST))
    ap.add_argument("--output")
    args = ap.parse_args()
    try:
        case_obj = load_json(Path(args.case))
        topology = load_json(Path(args.topology))
        elements = load_json(Path(args.elements)) if args.elements else None
        actors = load_json(Path(args.actors)) if args.actors else None
        source_manifest = load_json(Path(args.source_manifest))
        out = build_candidates(case_obj, topology, elements, source_manifest, actors)
        data = json.dumps(out, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(data, encoding="utf-8")
        print(data, end="")
        return 0
    except (ContractError, em.ElementModelError, RegimeError, OSError) as e:
        print(json.dumps({"status":"invalid","error":str(e)}, sort_keys=True), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
