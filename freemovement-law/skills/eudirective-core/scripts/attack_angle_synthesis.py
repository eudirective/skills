#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import element_model as em
import module_conformance as mc
import topology_engine as te

from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACK_FILE = compatibility_root() / "core-source-pack-manifest-0.6.1.json"
CORE_ATTACK_CATALOG_FILE = ROOT / "references" / "attack-angles" / "core-attack-angle-catalog.json"
ENGINE_VERSION = "0.1.0"
RULESET_VERSION = "0.1.0"
CONTRACT_VERSION = "0.2.0"
ELEMENT_MODEL_VERSION = "0.2.0"

REGIME_SOURCE_MAP = {
    "legal_regime.directive_2004_38": "eu:32004l0038",
    "legal_regime.visa_code": "eu:32009r0810",
    "legal_regime.schengen": "eu:32016r0399",
    "legal_regime.gdpr": "eu:32016r0679",
}
ADVERSE_ACCESS_STATES = {
    "blocked", "denied", "unavailable", "inaccessible", "delayed", "refused", "obstructed",
    "appointment_unavailable", "no_appointment", "lodgement_prevented", "digital_only_no_alternative",
}
ADVERSE_COMPLAINT_STATES = {
    "missing", "absent", "unavailable", "not_provided", "inaccessible", "denied", "no_route", "review_unavailable",
}
ADVERSE_DEADLINE_STATES = {"overdue", "exceeded", "missed", "late", "breached", "past_due"}
ADVERSE_COMPETENCE_STATES = {
    "outside_competence", "not_competent", "incompetent", "lacks_competence", "competence_denied", "competence_disputed",
}


class C5dError(Exception):
    pass


def normalize_state(value):
    if value is None:
        return None
    return str(value).strip().casefold().replace(" ", "_")


def validate_element_bundle(bundle):
    if bundle is None:
        return
    catalog, _, invariants = em.load_model()
    em.check_bundle(bundle, catalog, invariants)


def element_index(bundle):
    out = {}
    if bundle is None:
        return out
    for item in bundle["elements"]:
        out.setdefault(item["element_id"], []).append(item)
    return out


def single_element(idx, element_id):
    vals = idx.get(element_id, [])
    if not vals:
        return None
    if len(vals) != 1:
        raise C5dError(f"multiple_values_for_singleton:{element_id}")
    return vals[0]


def single_value(idx, element_id):
    item = single_element(idx, element_id)
    return None if item is None else item.get("value")


def fact_source_refs(idx, element_ids):
    refs = []
    for eid in element_ids:
        item = single_element(idx, eid)
        if item and item.get("source_ref"):
            refs.append(item["source_ref"])
    return sorted(set(refs))


def source_pack_index(pack):
    return {x["source_id"]: {"origin": "core", "module_id": None, "record": x} for x in pack["sources"]}


def regime_map(regimes):
    return {x["element_id"]: x for x in regimes.get("candidates", [])}


def principle_map(c5b):
    return {x["principle_id"]: x for x in c5b.get("principle_candidates", [])}


def c5c_evidence_map(c5c):
    return {x["request_id"]: x for x in c5c.get("evidence_assessments", [])}


def case_module_request_matches(case_obj, manifest, export):
    family = export["module_family"]
    for req in case_obj.get("module_requests", []):
        if req.get("family") != family:
            continue
        if not te.same_jurisdiction(req.get("jurisdiction"), export.get("jurisdiction")):
            continue
        if req.get("role") not in manifest.get("supported_roles", []):
            continue
        if family == "applicant_country":
            destination = req.get("destination_state")
            if destination is None:
                continue
            if not any(te.same_jurisdiction(destination, x) for x in manifest.get("destination_state_profiles_available", [])):
                continue
        return True
    return False


def add_unique(index, key, value, kind):
    if key in index:
        raise C5dError(f"duplicate_{kind}_id:{key}")
    index[key] = value


def load_module_pairs(module_pairs, case_obj, c5c_obj):
    bindings = []
    sources = {}
    rules = {}
    authorities = {}
    routes = {}
    attacks = []
    if not module_pairs:
        if c5c_obj["bindings"].get("module_bindings"):
            raise C5dError("c5c_bound_modules_must_be_replayed")
        return bindings, sources, rules, authorities, routes, attacks

    for manifest_path, export_path in module_pairs:
        manifest = load_json(Path(manifest_path))
        export = load_json(Path(export_path))
        try:
            mc.validate_pair(manifest, export)
        except mc.ConformanceError as e:
            raise C5dError(f"module_pair_nonconformant:{e}")
        if export["module_family"] not in {"member_state", "applicant_country"}:
            raise C5dError(f"c5d_country_module_required:{export.get('module_id')}")
        if not case_module_request_matches(case_obj, manifest, export):
            raise C5dError(f"c5d_case_irrelevant_module:{export['module_id']}")
        binding = {
            "module_id": export["module_id"],
            "module_family": export["module_family"],
            "jurisdiction": export["jurisdiction"],
            "manifest_sha256": digest_obj(manifest),
            "export_sha256": digest_obj(export),
        }
        bindings.append(binding)
        for rec in export.get("source_records", []):
            add_unique(sources, rec["source_id"], {"module_id": export["module_id"], "record": rec}, "source")
        for rec in export.get("rule_records", []):
            add_unique(rules, rec["rule_id"], {"module_id": export["module_id"], "record": rec}, "rule")
        for rec in export.get("authority_records", []):
            add_unique(authorities, rec["authority_id"], {"module_id": export["module_id"], "record": rec}, "authority")
        for rec in export.get("route_records", []):
            add_unique(routes, rec["route_id"], {"module_id": export["module_id"], "record": rec}, "route")
        for rec in export.get("attack_angle_records", []):
            attacks.append({"module_id": export["module_id"], "module_family": export["module_family"], "record": rec})

    bindings = sorted(bindings, key=lambda x: x["module_id"])
    binding_map = {x["module_id"]: x for x in bindings}
    for upstream in c5c_obj["bindings"].get("module_bindings", []):
        cur = binding_map.get(upstream["module_id"])
        if cur is None:
            raise C5dError(f"c5c_module_binding_not_replayed:{upstream['module_id']}")
        for key in ("jurisdiction", "manifest_sha256", "export_sha256"):
            if cur[key] != upstream[key]:
                raise C5dError(f"c5c_module_binding_mismatch:{upstream['module_id']}:{key}")
    if set(binding_map) != {x["module_id"] for x in c5c_obj["bindings"].get("module_bindings", [])}:
        extra = sorted(set(binding_map) - {x["module_id"] for x in c5c_obj["bindings"].get("module_bindings", [])})
        if extra:
            raise C5dError("c5d_unbound_extra_modules:" + ",".join(extra))
    return bindings, sources, rules, authorities, routes, attacks


def active_regimes(regimes):
    return {x["element_id"] for x in regimes.get("candidates", []) if x.get("disposition") == "candidate"}


def active_principles(c5b):
    return {x["principle_id"] for x in c5b.get("principle_candidates", []) if x.get("disposition") == "candidate"}


def filter_catalog_sources(pattern, active_regime_ids):
    refs = []
    for ref in pattern.get("source_refs", []):
        mapped_regimes = {rid for rid, sid in REGIME_SOURCE_MAP.items() if sid == ref}
        if mapped_regimes and not (mapped_regimes & active_regime_ids):
            continue
        refs.append(ref)
    return refs


def principle_sources(c5b, principle_ids):
    out = []
    for item in c5b.get("principle_candidates", []):
        if item.get("principle_id") in principle_ids and item.get("disposition") == "candidate":
            out.extend(item.get("source_refs", []))
    return sorted(set(out))


def route_sources(c5c_obj):
    out = []
    for item in c5c_obj.get("route_assessments", []):
        if item.get("disposition") == "candidate":
            out.extend(item.get("source_refs", []))
    return sorted(set(out))


def resolve_pattern_basis(pattern, regimes, c5b, c5c_obj):
    ar = active_regimes(regimes)
    ap = active_principles(c5b)
    regime_ok = not pattern["regime_any_of"] or bool(ar & set(pattern["regime_any_of"]))
    principle_ok = not pattern["principle_any_of"] or bool(ap & set(pattern["principle_any_of"]))
    sources = filter_catalog_sources(pattern, ar)
    sources.extend(principle_sources(c5b, pattern["principle_any_of"]))
    return regime_ok, principle_ok, sorted(set(sources))


def base_angle(pattern, procedural_stage):
    return {
        "attack_angle_id": pattern["attack_angle_id"],
        "origin": "core_catalog",
        "module_id": None,
        "label": pattern["label"],
        "issue_type": pattern["issue_type"],
        "basis_layer": pattern["basis_layer"],
        "assessment_status": "candidate",
        "legal_violation_status": "not_determined",
        "evidence_state": "partial",
        "prerequisites_state": "satisfied",
        "exclusion_state": "none_indicated",
        "completeness_state": "partial",
        "supporting_finding_refs": [],
        "supporting_element_refs": [],
        "source_refs": [],
        "rule_refs": [],
        "authority_refs": [],
        "route_refs": [],
        "fact_source_refs": [],
        "procedural_stage": None if procedural_stage is None else str(procedural_stage),
        "evidence_needs": list(pattern["evidence_needs"]),
        "missing_evidence": [],
        "false_positive_risks": list(pattern["false_positive_risks"]),
        "severity_hint": pattern["severity_hint"],
        "rationale_codes": [],
        "review_required": True,
        "limitations": list(pattern["limitations"]) + [pattern["support_scope"]],
    }


def mark_blocked(angle, code):
    angle["assessment_status"] = "blocked"
    angle["evidence_state"] = "not_checked"
    angle["prerequisites_state"] = "unresolved"
    angle["completeness_state"] = "blocked"
    angle["rationale_codes"] = [code]
    angle["limitations"].append("C5d does not upgrade a blocked upstream analysis chain into an attack-angle finding.")
    return angle


def assess_core_pattern(pattern, idx, regimes, c5b, c5c_obj, upstream_blocked):
    stage = single_value(idx, "procedure.stage")
    angle = base_angle(pattern, stage)
    regime_ok, principle_ok, basis_sources = resolve_pattern_basis(pattern, regimes, c5b, c5c_obj)
    kind = pattern["signal_kind"]
    triggered = False

    if kind == "proof_restriction_claim":
        matches = [x for x in c5c_obj.get("evidence_assessments", []) if x.get("kind") == "proof_restriction_review" and x.get("disposition") == "candidate"]
        if matches and regime_ok:
            triggered = True
            for item in matches:
                angle["supporting_finding_refs"].append(item["request_id"])
                angle["source_refs"].extend(item.get("source_refs", []))
                angle["rule_refs"].extend(item.get("supporting_rule_refs", []))
            angle["supporting_element_refs"] = ["evidence.proof_restriction_status", "evidence.proof_restriction_source_ref"]
            angle["fact_source_refs"] = fact_source_refs(idx, angle["supporting_element_refs"])
            angle["rationale_codes"] = ["c5c_proof_restriction_candidate_bound", "legal_validity_not_inferred"]
            angle["missing_evidence"] = list(pattern["evidence_needs"])
            angle["assessment_status"] = "candidate"
            angle["evidence_state"] = "partial"

    elif kind == "dependency_freedom_of_proof_candidate":
        matches = [x for x in c5c_obj.get("evidence_assessments", []) if x.get("kind") == "dependency_freedom_of_proof" and x.get("freedom_of_proof_candidate") == "candidate"]
        if matches and regime_ok:
            triggered = True
            for item in matches:
                angle["supporting_finding_refs"].append(item["request_id"])
                angle["source_refs"].extend(item.get("source_refs", []))
            angle["supporting_element_refs"] = ["relationship.dependency_status"]
            angle["fact_source_refs"] = fact_source_refs(idx, angle["supporting_element_refs"])
            angle["rationale_codes"] = ["dependency_scoped_freedom_of_proof_candidate"]
            angle["assessment_status"] = "candidate"
            angle["evidence_state"] = "partial"
            angle["missing_evidence"] = list(pattern["evidence_needs"])

    elif kind == "exact_deadline_adverse_state":
        deadline_state = normalize_state(single_value(idx, "procedure.deadline_state"))
        exact = [x for x in c5c_obj.get("deadline_assessments", []) if x.get("calculation_status") == "exact" and x.get("disposition") == "candidate"]
        if exact and deadline_state in ADVERSE_DEADLINE_STATES:
            triggered = True
            for item in exact:
                angle["supporting_finding_refs"].append(item["request_id"])
                angle["source_refs"].extend(item.get("source_refs", []))
                if item.get("rule_ref"):
                    angle["rule_refs"].append(item["rule_ref"])
                if item.get("trigger_date_source_ref"):
                    angle["fact_source_refs"].append(item["trigger_date_source_ref"])
            angle["supporting_element_refs"] = ["procedure.deadline_state"]
            angle["fact_source_refs"].extend(fact_source_refs(idx, angle["supporting_element_refs"]))
            angle["rationale_codes"] = ["exact_c5c_deadline_plus_adverse_timeliness_state", "deadline_applicability_still_review_required"]
            angle["evidence_state"] = "sufficient_for_review" if angle["fact_source_refs"] else "partial"
            angle["assessment_status"] = "supported" if angle["fact_source_refs"] else "candidate"
            angle["completeness_state"] = "complete_for_review" if angle["fact_source_refs"] else "partial"
            if not angle["fact_source_refs"]:
                angle["missing_evidence"].append("Independent evidence supporting the adverse timeliness state.")

    elif kind == "procedure_access_adverse":
        access_state = normalize_state(single_value(idx, "procedure.access_state"))
        if access_state in ADVERSE_ACCESS_STATES and regime_ok:
            triggered = True
            angle["supporting_element_refs"] = ["procedure.access_state"]
            angle["fact_source_refs"] = fact_source_refs(idx, angle["supporting_element_refs"])
            for item in regimes.get("candidates", []):
                if item.get("element_id") in pattern["regime_any_of"] and item.get("disposition") == "candidate":
                    angle["supporting_finding_refs"].append(item["element_id"])
                    angle["source_refs"].extend(item.get("source_refs", []))
            angle["rationale_codes"] = ["explicit_adverse_procedural_access_state", "active_eu_regime_candidate"]
            angle["evidence_state"] = "sufficient_for_review" if angle["fact_source_refs"] else "partial"
            angle["assessment_status"] = "supported" if angle["fact_source_refs"] else "candidate"
            angle["completeness_state"] = "complete_for_review" if angle["fact_source_refs"] else "partial"
            if not angle["fact_source_refs"]:
                angle["missing_evidence"].append("Evidence supporting the adverse procedural-access state.")

    elif kind == "complaint_path_adverse":
        state = normalize_state(single_value(idx, "procedure.complaint_path_state"))
        if state in ADVERSE_COMPLAINT_STATES and principle_ok:
            triggered = True
            angle["supporting_element_refs"] = ["procedure.complaint_path_state"]
            angle["fact_source_refs"] = fact_source_refs(idx, angle["supporting_element_refs"])
            for item in c5b.get("principle_candidates", []):
                if item.get("principle_id") in pattern["principle_any_of"] and item.get("disposition") == "candidate":
                    angle["supporting_finding_refs"].append(item["principle_id"])
                    angle["source_refs"].extend(item.get("source_refs", []))
            angle["rationale_codes"] = ["explicit_adverse_complaint_path_state", "source_backed_principle_candidate"]
            angle["evidence_state"] = "sufficient_for_review" if angle["fact_source_refs"] else "partial"
            angle["assessment_status"] = "supported" if angle["fact_source_refs"] else "candidate"
            angle["completeness_state"] = "complete_for_review" if angle["fact_source_refs"] else "partial"
            if not angle["fact_source_refs"]:
                angle["missing_evidence"].append("Evidence supporting the asserted complaint/review-path state.")

    elif kind == "authority_competence_adverse":
        state = normalize_state(single_value(idx, "authority.competence"))
        if state in ADVERSE_COMPETENCE_STATES:
            route_items = [x for x in c5c_obj.get("route_assessments", []) if x.get("disposition") == "candidate"]
            if route_items:
                triggered = True
                angle["supporting_element_refs"] = ["authority.competence"]
                angle["fact_source_refs"] = fact_source_refs(idx, angle["supporting_element_refs"])
                for item in route_items:
                    angle["supporting_finding_refs"].append(item["request_id"])
                    angle["source_refs"].extend(item.get("source_refs", []))
                    if item.get("authority_ref"):
                        angle["authority_refs"].append(item["authority_ref"])
                    if item.get("route_ref"):
                        angle["route_refs"].append(item["route_ref"])
                angle["rationale_codes"] = ["explicit_adverse_authority_competence_state", "source_backed_route_candidate"]
                angle["evidence_state"] = "sufficient_for_review" if angle["fact_source_refs"] else "partial"
                angle["assessment_status"] = "supported" if angle["fact_source_refs"] else "candidate"
                angle["completeness_state"] = "complete_for_review" if angle["fact_source_refs"] else "partial"
                if not angle["fact_source_refs"]:
                    angle["missing_evidence"].append("Evidence supporting the adverse competence state.")

    elif kind == "proportionality_plus_adverse_signal":
        if principle_ok:
            access_adverse = normalize_state(single_value(idx, "procedure.access_state")) in ADVERSE_ACCESS_STATES
            proof_claim = any(x.get("kind") == "proof_restriction_review" and x.get("disposition") == "candidate" for x in c5c_obj.get("evidence_assessments", []))
            complaint_adverse = normalize_state(single_value(idx, "procedure.complaint_path_state")) in ADVERSE_COMPLAINT_STATES
            if access_adverse or proof_claim or complaint_adverse:
                triggered = True
                for item in c5b.get("principle_candidates", []):
                    if item.get("principle_id") == "proportionality" and item.get("disposition") == "candidate":
                        angle["supporting_finding_refs"].append(item["principle_id"])
                        angle["source_refs"].extend(item.get("source_refs", []))
                if access_adverse:
                    angle["supporting_element_refs"].append("procedure.access_state")
                if complaint_adverse:
                    angle["supporting_element_refs"].append("procedure.complaint_path_state")
                if proof_claim:
                    angle["supporting_element_refs"].append("evidence.proof_restriction_status")
                angle["fact_source_refs"] = fact_source_refs(idx, angle["supporting_element_refs"])
                angle["rationale_codes"] = ["proportionality_candidate_plus_concrete_adverse_signal", "substantive_proportionality_not_determined"]
                angle["assessment_status"] = "candidate"
                angle["evidence_state"] = "partial"
                angle["missing_evidence"] = list(pattern["evidence_needs"])

    if not triggered:
        return None
    if upstream_blocked:
        return mark_blocked(angle, "upstream_c5a_c5b_c5c_chain_blocked")
    if not regime_ok:
        angle["assessment_status"] = "blocked"
        angle["prerequisites_state"] = "missing"
        angle["completeness_state"] = "blocked"
        angle["rationale_codes"] = ["required_regime_candidate_missing"]
    if not principle_ok:
        angle["assessment_status"] = "blocked"
        angle["prerequisites_state"] = "missing"
        angle["completeness_state"] = "blocked"
        angle["rationale_codes"] = ["required_principle_candidate_missing"]

    angle["source_refs"].extend(basis_sources)
    angle["source_refs"] = sorted(set(angle["source_refs"]))
    angle["rule_refs"] = sorted(set(angle["rule_refs"]))
    angle["authority_refs"] = sorted(set(angle["authority_refs"]))
    angle["route_refs"] = sorted(set(angle["route_refs"]))
    angle["fact_source_refs"] = sorted(set(angle["fact_source_refs"]))
    angle["supporting_finding_refs"] = sorted(set(angle["supporting_finding_refs"]))
    angle["supporting_element_refs"] = sorted(set(angle["supporting_element_refs"]))
    if not angle["source_refs"] and angle["assessment_status"] not in {"blocked", "not_indicated"}:
        angle["assessment_status"] = "insufficient_evidence"
        angle["evidence_state"] = "missing"
        angle["completeness_state"] = "partial"
        angle["rationale_codes"].append("legal_source_support_missing")
        angle["missing_evidence"].append("Source support for the legal/procedural basis of this review angle.")
    return angle


def assess_module_attack(wrapped, idx, all_sources, upstream_blocked):
    rec = wrapped["record"]
    missing_prereqs = [eid for eid in rec.get("prerequisite_element_ids", []) if single_element(idx, eid) is None]
    present_disqualifiers = [eid for eid in rec.get("disqualifier_element_ids", []) if single_element(idx, eid) is not None]
    missing_sources = [ref for ref in rec.get("source_refs", []) if ref not in all_sources]
    stage = single_value(idx, "procedure.stage")
    angle = {
        "attack_angle_id": rec["attack_angle_id"],
        "origin": "module_record",
        "module_id": wrapped["module_id"],
        "label": rec["label"],
        "issue_type": rec["issue_type"],
        "basis_layer": rec["basis_layer"],
        "assessment_status": "candidate",
        "legal_violation_status": "not_determined",
        "evidence_state": "partial",
        "prerequisites_state": "satisfied" if not missing_prereqs else "missing",
        "exclusion_state": "unresolved" if present_disqualifiers else "none_indicated",
        "completeness_state": "partial",
        "supporting_finding_refs": [],
        "supporting_element_refs": sorted(set(rec.get("prerequisite_element_ids", []) + rec.get("disqualifier_element_ids", []))),
        "source_refs": sorted(set(rec.get("source_refs", []))),
        "rule_refs": [],
        "authority_refs": sorted(set(rec.get("authority_refs", []))),
        "route_refs": sorted(set(rec.get("route_refs", []))),
        "fact_source_refs": fact_source_refs(idx, rec.get("prerequisite_element_ids", [])),
        "procedural_stage": None if stage is None else str(stage),
        "evidence_needs": list(rec.get("evidence_needs", [])),
        "missing_evidence": [f"Missing prerequisite element: {x}" for x in missing_prereqs],
        "false_positive_risks": [
            "Module attack-angle records are declarative review inputs; prerequisite element IDs do not encode expected values in contract 0.2.0.",
            "Presence of a source or national rule does not by itself establish non-compliance."
        ],
        "severity_hint": rec.get("severity_hint"),
        "rationale_codes": ["conformant_module_attack_angle_record_bound"],
        "review_required": True,
        "limitations": [rec["support_scope"]],
    }
    if upstream_blocked:
        return mark_blocked(angle, "upstream_c5a_c5b_c5c_chain_blocked")
    if rec.get("support_status") == "unsupported_automation":
        angle["assessment_status"] = "blocked"
        angle["prerequisites_state"] = "unresolved"
        angle["completeness_state"] = "blocked"
        angle["rationale_codes"] = ["module_attack_angle_unsupported_automation"]
    elif missing_sources:
        angle["assessment_status"] = "blocked"
        angle["evidence_state"] = "missing"
        angle["completeness_state"] = "blocked"
        angle["rationale_codes"] = ["module_attack_angle_source_missing"]
        angle["missing_evidence"].extend(f"Missing source reference: {x}" for x in missing_sources)
    elif missing_prereqs:
        angle["assessment_status"] = "insufficient_evidence"
        angle["evidence_state"] = "missing"
        angle["completeness_state"] = "partial"
        angle["rationale_codes"].append("module_attack_angle_prerequisites_missing")
    elif present_disqualifiers:
        angle["assessment_status"] = "candidate"
        angle["prerequisites_state"] = "satisfied"
        angle["exclusion_state"] = "unresolved"
        angle["rationale_codes"].append("module_disqualifier_value_semantics_unresolved")
    else:
        angle["assessment_status"] = "candidate"
        angle["evidence_state"] = "partial"
        angle["rationale_codes"].append("module_record_requires_semantic_review")
    return angle


def validate_source_refs(angles, all_sources):
    for angle in angles:
        for ref in angle.get("source_refs", []):
            if ref not in all_sources:
                raise C5dError(f"attack_angle_source_ref_unknown:{angle['attack_angle_id']}:{ref}")


def build(case_obj, regimes, c5b, c5c_obj, element_bundle=None, module_pairs=None, source_pack=None, catalog=None):
    validate_obj("case-input", case_obj)
    if case_obj.get("privacy_classification") == "private":
        raise C5dError("private_data_disabled")
    validate_obj("legal-regime-candidates", regimes)
    validate_obj("c5b-hierarchy-principles", c5b)
    validate_obj("c5c-evidence-deadline-authority", c5c_obj)
    case_id = case_obj["case_id"]
    if any(x["case_id"] != case_id for x in (regimes, c5b, c5c_obj)):
        raise C5dError("case_id_mismatch")

    case_digest = digest_obj(case_obj)
    regime_digest = digest_obj(regimes)
    c5b_digest = digest_obj(c5b)
    c5c_digest = digest_obj(c5c_obj)
    if regimes["bound_case_sha256"] != case_digest:
        raise C5dError("regime_case_binding_mismatch")
    if c5b["bindings"]["case_sha256"] != case_digest or c5b["bindings"]["regime_candidates_sha256"] != regime_digest:
        raise C5dError("c5b_binding_mismatch")
    if c5c_obj["bindings"]["case_sha256"] != case_digest:
        raise C5dError("c5c_case_binding_mismatch")
    if c5c_obj["bindings"]["regime_candidates_sha256"] != regime_digest:
        raise C5dError("c5c_regime_binding_mismatch")
    if c5c_obj["bindings"]["c5b_sha256"] != c5b_digest:
        raise C5dError("c5c_c5b_binding_mismatch")

    if element_bundle is not None:
        validate_element_bundle(element_bundle)
        element_digest = digest_obj(element_bundle)
    else:
        element_digest = None
    expected_element_digest = regimes.get("bound_element_bundle_sha256")
    if expected_element_digest is not None:
        if element_bundle is None:
            raise C5dError("element_bundle_required_for_bound_chain")
        if element_digest != expected_element_digest:
            raise C5dError("regime_element_bundle_binding_mismatch")
        if c5b["bindings"]["element_bundle_sha256"] != element_digest:
            raise C5dError("c5b_element_bundle_binding_mismatch")
        if c5c_obj["bindings"]["element_bundle_sha256"] != element_digest:
            raise C5dError("c5c_element_bundle_binding_mismatch")
    elif element_bundle is not None:
        raise C5dError("unexpected_element_bundle_for_unbound_chain")

    if source_pack is None:
        source_pack = load_json(SOURCE_PACK_FILE)
    validate_obj("core-source-pack", source_pack)
    source_pack_digest = digest_obj(source_pack)
    if regimes["source_pack_sha256"] != source_pack_digest:
        raise C5dError("regime_source_pack_binding_mismatch")
    if c5b["bindings"]["source_pack_sha256"] != source_pack_digest:
        raise C5dError("c5b_source_pack_binding_mismatch")
    if c5c_obj["bindings"]["source_pack_sha256"] != source_pack_digest:
        raise C5dError("c5c_source_pack_binding_mismatch")
    core_sources = source_pack_index(source_pack)

    if catalog is None:
        catalog = load_json(CORE_ATTACK_CATALOG_FILE)
    validate_obj("core-attack-angle-catalog", catalog)
    catalog_ids = set()
    for pat in catalog["patterns"]:
        if pat["attack_angle_id"] in catalog_ids:
            raise C5dError(f"duplicate_core_attack_angle_id:{pat['attack_angle_id']}")
        catalog_ids.add(pat["attack_angle_id"])
        for ref in pat.get("source_refs", []):
            if ref not in core_sources:
                raise C5dError(f"core_attack_catalog_source_missing:{pat['attack_angle_id']}:{ref}")
        for rid in pat.get("regime_any_of", []):
            if rid not in REGIME_SOURCE_MAP and rid not in {x["element_id"] for x in regimes.get("candidates", [])}:
                raise C5dError(f"core_attack_catalog_regime_unknown:{pat['attack_angle_id']}:{rid}")
        for pid in pat.get("principle_any_of", []):
            if pid not in {x["principle_id"] for x in c5b.get("principle_candidates", [])} and pid not in {
                "direct_effect", "primacy", "disapplication", "consistent_interpretation", "equivalence", "effectiveness",
                "proportionality", "legal_certainty", "legitimate_expectations", "grimaldi_soft_law", "rights_of_defence",
                "good_administration_general_principle", "effective_judicial_protection", "charter_article_41_direct_reliance"
            }:
                raise C5dError(f"core_attack_catalog_principle_unknown:{pat['attack_angle_id']}:{pid}")

    bindings, module_sources, rules, authorities, routes, module_attacks = load_module_pairs(module_pairs, case_obj, c5c_obj)
    all_sources = dict(core_sources)
    for sid, wrapped in module_sources.items():
        if sid in all_sources:
            raise C5dError(f"duplicate_cross_layer_source_id:{sid}")
        all_sources[sid] = {"origin": "module", "module_id": wrapped["module_id"], "record": wrapped["record"]}

    idx = element_index(element_bundle)
    upstream_blocked = any(x["resolution_status"] == "blocked" for x in (regimes, c5b, c5c_obj))
    angles = []
    for pattern in catalog["patterns"]:
        angle = assess_core_pattern(pattern, idx, regimes, c5b, c5c_obj, upstream_blocked)
        if angle is not None:
            angles.append(angle)
    for wrapped in module_attacks:
        angles.append(assess_module_attack(wrapped, idx, all_sources, upstream_blocked))

    seen = set()
    for angle in angles:
        if angle["attack_angle_id"] in seen:
            raise C5dError(f"duplicate_attack_angle_id:{angle['attack_angle_id']}")
        seen.add(angle["attack_angle_id"])
    validate_source_refs(angles, all_sources)

    unresolved = []
    if upstream_blocked:
        unresolved.append("upstream_c5a_c5b_c5c_chain_blocked")
    for angle in angles:
        if angle["assessment_status"] in {"blocked", "insufficient_evidence"}:
            unresolved.append(f"{angle['attack_angle_id']}:{angle['assessment_status']}")
        if angle["exclusion_state"] == "unresolved":
            unresolved.append(f"{angle['attack_angle_id']}:exclusion_state_unresolved")

    result = {
        "engine_version": ENGINE_VERSION,
        "ruleset_version": RULESET_VERSION,
        "contract_version": CONTRACT_VERSION,
        "element_model_version": ELEMENT_MODEL_VERSION,
        "case_id": case_id,
        "bindings": {
            "case_sha256": case_digest,
            "regime_candidates_sha256": regime_digest,
            "c5b_sha256": c5b_digest,
            "c5c_sha256": c5c_digest,
            "element_bundle_sha256": element_digest,
            "source_pack_version": source_pack["pack_version"],
            "source_pack_sha256": source_pack_digest,
            "core_attack_catalog_version": catalog["catalog_version"],
            "core_attack_catalog_sha256": digest_obj(catalog),
            "module_bindings": bindings,
        },
        "resolution_status": "blocked" if upstream_blocked else "ready",
        "final_attack_angle_resolution": "not_determined",
        "attack_angles": sorted(angles, key=lambda x: x["attack_angle_id"]),
        "unresolved": sorted(set(unresolved)),
        "limitations": [
            "C5d synthesizes review hypotheses from bound C5a-C5c outputs and conformant module records; it does not establish a legal violation, illegality, bad faith or entitlement to a remedy.",
            "A source, deadline, principle, checklist, authority statement or missing field never creates an attack angle by itself; a concrete factual/procedural signal and the required upstream support must also be present.",
            "Supported status means supported for legal/procedural review by the encoded trigger plus source/evidence bindings; legal_violation_status remains not_determined.",
            "Module attack-angle records remain declarative review inputs because contract 0.2.0 lists prerequisite/disqualifier element IDs but does not encode their expected values.",
            "C5d does not rank remedies, choose escalation strategy, apply stratagems or feed suggestions back into legal analysis.",
            "C5d does not auto-generate GDPR/data-minimisation allegations merely because personal data or a GDPR regime candidate exists; authority-processing purpose/necessity/excess facts need a dedicated factual model or source-backed module pattern.",
            "Unresolved lex-specialis relationships remain unresolved and do not become contradiction/non-compliance attack angles merely because two regimes coexist."
        ],
    }
    validate_obj("c5d-attack-angle-synthesis", result)
    return result


def main():
    ap = argparse.ArgumentParser(description="Build C5d source-bound attack-angle review hypotheses from the exact C5a-C5c chain")
    ap.add_argument("case")
    ap.add_argument("regimes")
    ap.add_argument("c5b")
    ap.add_argument("c5c")
    ap.add_argument("--elements")
    ap.add_argument("--module-pair", nargs=2, action="append", metavar=("MANIFEST", "EXPORT"))
    ap.add_argument("--source-pack", default=str(SOURCE_PACK_FILE))
    ap.add_argument("--catalog", default=str(CORE_ATTACK_CATALOG_FILE))
    ap.add_argument("--output")
    args = ap.parse_args()
    try:
        result = build(
            load_json(Path(args.case)),
            load_json(Path(args.regimes)),
            load_json(Path(args.c5b)),
            load_json(Path(args.c5c)),
            load_json(Path(args.elements)) if args.elements else None,
            args.module_pair,
            load_json(Path(args.source_pack)),
            load_json(Path(args.catalog)),
        )
        rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (C5dError, ContractError, OSError, ValueError) as e:
        print(json.dumps({"status": "invalid", "error": str(e)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
