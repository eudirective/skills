#!/usr/bin/env python3
import argparse
import calendar
from datetime import date, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import json
from pathlib import Path
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import element_model as em
import module_conformance as mc
import topology_engine as te

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACK_FILE = ROOT / "references" / "source-pack" / "core-source-pack-manifest-0.6.1.json"
CORE_ROUTE_CATALOG_FILE = ROOT / "references" / "routes" / "core-eu-route-catalog.json"
ENGINE_VERSION = "0.2.0"
RULESET_VERSION = "0.2.0"
CONTRACT_VERSION = "0.2.0"
ELEMENT_MODEL_VERSION = "0.2.0"

NEGATIVE_STATES = {"none", "no", "false", "not_applicable", "not_asserted", "not_established", "not_dependent", "absent"}
RECOGNIZED_INCLUSION_RULES = {"trigger_date_excluded", "trigger_date_included"}


class C5cError(Exception):
    pass


def index_elements(bundle):
    out = {}
    if bundle is None:
        return out
    for item in bundle["elements"]:
        out.setdefault(item["element_id"], []).append(item)
    return out


def single_element(index, element_id):
    vals = index.get(element_id, [])
    if not vals:
        return None
    if len(vals) != 1:
        raise C5cError(f"multiple_values_for_singleton:{element_id}")
    return vals[0]


def single_value(index, element_id):
    item = single_element(index, element_id)
    return None if item is None else item["value"]


def validate_element_bundle(bundle):
    if bundle is None:
        return
    catalog, _, invariants = em.load_model()
    em.check_bundle(bundle, catalog, invariants)


def source_pack_index(pack):
    return {x["source_id"]: {"origin": "core", "module_id": None, "record": x} for x in pack["sources"]}


def regime_map(regimes):
    return {x["element_id"]: x for x in regimes["candidates"]}


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


def load_module_pairs(module_pairs, case_obj, c5b):
    bindings = []
    sources = {}
    rules = {}
    deadlines = {}
    authorities = {}
    routes = {}
    if not module_pairs:
        if c5b["bindings"].get("module_bindings"):
            raise C5cError("c5b_bound_modules_must_be_replayed")
        return bindings, sources, rules, deadlines, authorities, routes

    for manifest_path, export_path in module_pairs:
        manifest = load_json(Path(manifest_path))
        export = load_json(Path(export_path))
        try:
            mc.validate_pair(manifest, export)
        except mc.ConformanceError as e:
            raise C5cError(f"module_pair_nonconformant:{e}")
        if export["module_family"] not in {"member_state", "applicant_country"}:
            raise C5cError(f"c5c_country_module_required:{export.get('module_id')}")
        if not case_module_request_matches(case_obj, manifest, export):
            raise C5cError(f"module_not_requested_for_case:{export.get('module_id')}:{export.get('jurisdiction')}")

        binding = {
            "module_id": export["module_id"],
            "module_family": export["module_family"],
            "jurisdiction": export["jurisdiction"],
            "manifest_sha256": digest_obj(manifest),
            "export_sha256": digest_obj(export),
        }
        if any(x["module_id"] == binding["module_id"] for x in bindings):
            raise C5cError(f"duplicate_bound_module_id:{binding['module_id']}")
        bindings.append(binding)

        def add_unique(index, key, value, label):
            if key in index:
                raise C5cError(f"duplicate_bound_{label}_id:{key}")
            index[key] = value

        for rec in export.get("source_records", []):
            add_unique(sources, rec["source_id"], {"origin": export["module_family"], "module_id": export["module_id"], "record": rec}, "source")
        for rec in export.get("rule_records", []):
            add_unique(rules, rec["rule_id"], {"origin": export["module_family"], "module_id": export["module_id"], "record": rec}, "rule")
        for rec in export.get("deadline_records", []):
            add_unique(deadlines, rec["deadline_id"], {"origin": export["module_family"], "module_id": export["module_id"], "record": rec}, "deadline")
        for rec in export.get("authority_records", []):
            add_unique(authorities, rec["authority_id"], {"origin": export["module_family"], "module_id": export["module_id"], "record": rec}, "authority")
        for rec in export.get("route_records", []):
            add_unique(routes, rec["route_id"], {"origin": export["module_family"], "module_id": export["module_id"], "record": rec}, "route")

    bindings = sorted(bindings, key=lambda x: x["module_id"])
    binding_map = {x["module_id"]: x for x in bindings}
    for upstream in c5b["bindings"].get("module_bindings", []):
        cur = binding_map.get(upstream["module_id"])
        if cur is None:
            raise C5cError(f"c5b_module_binding_not_replayed:{upstream['module_id']}")
        for key in ("jurisdiction", "manifest_sha256", "export_sha256"):
            if cur[key] != upstream[key]:
                raise C5cError(f"c5b_module_binding_mismatch:{upstream['module_id']}:{key}")
    return bindings, sources, rules, deadlines, authorities, routes


def load_core_route_catalog(core_sources):
    obj = load_json(CORE_ROUTE_CATALOG_FILE)
    validate_obj("core-route-catalog", obj)
    seen = set()
    for route in obj["routes"]:
        if route["route_id"] in seen:
            raise C5cError(f"duplicate_core_route_id:{route['route_id']}")
        seen.add(route["route_id"])
        for ref in route["source_refs"]:
            src = core_sources.get(ref)
            if src is None:
                raise C5cError(f"core_route_source_missing:{route['route_id']}:{ref}")
            freshness = src["record"].get("freshness_state")
            if freshness not in {"current", "fixed_verified"}:
                raise C5cError(f"core_route_source_not_current:{route['route_id']}:{ref}:{freshness}")
            if route["verified_at"] != src["record"].get("verification_date"):
                raise C5cError(f"core_route_verification_date_mismatch:{route['route_id']}:{ref}")
    return obj, {x["route_id"]: x for x in obj["routes"]}


def normalize_state(value):
    if value is None:
        return None
    return str(value).strip().casefold().replace(" ", "_")


def is_negative_state(value):
    return normalize_state(value) in NEGATIVE_STATES


def known_basis_refs(regimes, c5b, core_sources, module_sources, rules):
    refs = set(core_sources) | set(module_sources) | set(rules)
    refs |= {x["element_id"] for x in regimes["candidates"]}
    refs |= {x["relationship_id"] for x in c5b.get("hierarchy_relationships", [])}
    refs |= {x["principle_id"] for x in c5b.get("principle_candidates", [])}
    refs |= {x["request_id"] for x in c5b.get("source_use_assessments", [])}
    return refs


def source_supporting_rules(source_ref, rules):
    return sorted(rid for rid, wrapped in rules.items() if source_ref in wrapped["record"].get("source_refs", []))


def assess_evidence_request(req, idx, regimes, c5b, all_sources, module_sources, rules, upstream_blocked):
    restriction_state = single_value(idx, "evidence.proof_restriction_status")
    freedom_state = single_value(idx, "evidence.freedom_of_proof_state")
    restriction_source = single_value(idx, "evidence.proof_restriction_source_ref")
    basis_refs = sorted(set(req["basis_refs"]))
    result = {
        "request_id": req["request_id"],
        "kind": req["kind"],
        "disposition": "unknown",
        "restriction_claim_state": None if restriction_state is None else str(restriction_state),
        "supplied_freedom_of_proof_state": None if freedom_state is None else str(freedom_state),
        "freedom_of_proof_candidate": "not_indicated",
        "basis_refs": basis_refs,
        "source_refs": [],
        "supporting_rule_refs": [],
        "rationale_codes": [],
        "review_required": True,
        "limitations": [],
    }
    if upstream_blocked:
        result.update({
            "disposition": "blocked",
            "freedom_of_proof_candidate": "blocked",
            "rationale_codes": ["upstream_c5a_c5b_chain_blocked"],
            "limitations": ["C5c does not upgrade an upstream blocked analysis chain into an evidence-law candidate."],
        })
        return result

    cmap = regime_map(regimes)
    directive = cmap.get("legal_regime.directive_2004_38")
    if req["kind"] == "dependency_freedom_of_proof":
        dependency = single_value(idx, "relationship.dependency_status")
        if dependency is None or is_negative_state(dependency):
            result.update({
                "disposition": "not_indicated",
                "rationale_codes": ["dependency_context_not_indicated"],
                "review_required": False,
                "limitations": ["The bundled freedom-of-proof authority is scoped to dependency evidence; C5c does not generalize it to unrelated documentary requirements."],
            })
            return result
        if directive is None or directive.get("disposition") != "candidate":
            result.update({
                "disposition": "blocked" if directive and directive.get("disposition") == "blocked" else "not_indicated",
                "freedom_of_proof_candidate": "blocked" if directive and directive.get("disposition") == "blocked" else "not_indicated",
                "rationale_codes": ["directive_candidate_required_for_dependency_evidence_review"],
                "limitations": ["Dependency evidence review is not promoted without a usable Directive 2004/38 candidate in the bound C5a output."],
            })
            return result
        refs = ["eu:62005cj0001", "eu:32004l0038"]
        for ref in refs:
            if ref not in all_sources:
                raise C5cError(f"required_evidence_source_missing:{ref}")
        result.update({
            "disposition": "candidate",
            "freedom_of_proof_candidate": "candidate",
            "source_refs": refs,
            "rationale_codes": ["dependency_context_present", "directive_candidate_present", "jia_dependency_evidence_review_candidate"],
            "limitations": [
                "This candidate is limited to dependency evidence and does not establish a general freedom-of-proof rule for every free-movement document request.",
                "The bundled Jia representation is identity/version verified source-note material; exact wording and pinpoints require the official judgment.",
                "C5c does not determine whether dependency is legally established or whether any particular evidence is sufficient."
            ],
        })
        return result

    if req["kind"] == "proof_restriction_review":
        if restriction_state is None or is_negative_state(restriction_state):
            result.update({
                "disposition": "not_indicated",
                "rationale_codes": ["proof_restriction_not_indicated"],
                "review_required": False,
                "limitations": ["No authority-imposed closed-proof restriction is indicated in the bound element state."],
            })
            return result
        if restriction_source is None:
            result.update({
                "disposition": "blocked",
                "rationale_codes": ["proof_restriction_source_missing"],
                "limitations": ["A claimed proof restriction cannot be reviewed without a bound source reference."],
            })
            return result
        source_ref = str(restriction_source)
        source = all_sources.get(source_ref)
        if source is None:
            result.update({
                "disposition": "blocked",
                "source_refs": [source_ref],
                "rationale_codes": ["unknown_proof_restriction_source_ref"],
                "limitations": ["The asserted proof restriction source is not present in the bound core/country source set."],
            })
            return result
        supporting_rules = source_supporting_rules(source_ref, rules)
        rationale = ["proof_restriction_claim_bound_to_source"]
        limitations = [
            "C5c preserves the asserted/established label as an input claim; it does not convert that label into a finding that the restriction is legally valid.",
            "A checklist, operational instruction or non-binding guidance is not treated as a closed legal proof rule merely because it exists."
        ]
        record = source["record"]
        origin = source["origin"]
        legal_status = record.get("legal_status")
        if origin == "applicant_country" or legal_status in {"non_binding_official_guidance", "non_binding_soft_law", "official_operational_guidance"}:
            rationale.append("restriction_legal_basis_not_established")
        if origin != "core" and not supporting_rules:
            rationale.append("restriction_rule_not_bound")
        result.update({
            "disposition": "candidate",
            "source_refs": [source_ref],
            "supporting_rule_refs": supporting_rules,
            "rationale_codes": rationale,
            "limitations": limitations,
        })
        return result

    raise C5cError(f"unsupported_evidence_request_kind:{req['kind']}")


def add_months(d, months):
    idx = (d.month - 1) + months
    year = d.year + idx // 12
    month = idx % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def exact_deadline(record, trigger_date, inclusion_rule):
    op = record["calculation"]["operator"]
    amount = record["calculation"].get("amount")
    if amount is None:
        return None, "deadline_amount_missing"
    if inclusion_rule not in RECOGNIZED_INCLUSION_RULES:
        return None, "inclusion_rule_not_machine_interpretable"
    if op == "date_add_days" and record["calendar"] == "calendar_days":
        delta = amount - 1 if inclusion_rule == "trigger_date_included" and amount > 0 else amount
        return trigger_date + timedelta(days=delta), None
    if op == "date_add_months" and record["calendar"] == "months":
        if inclusion_rule != "trigger_date_excluded":
            return None, "month_inclusion_rule_not_machine_interpretable"
        return add_months(trigger_date, amount), None
    if op == "business_days" or record["calendar"] == "business_days":
        return None, "business_day_calendar_identity_missing"
    return None, "deadline_operator_not_exactly_supported"


def normalize_trigger_label(value):
    return " ".join(str(value).strip().casefold().replace("_", " ").split())


def deadline_binding_index(context):
    out = {}
    for binding in context.get("deadline_bindings", []):
        bid = binding["binding_id"]
        if bid in out:
            raise C5cError(f"duplicate_deadline_binding_id:{bid}")
        out[bid] = binding
    return out


def temporal_event_index(context):
    out = {}
    for event in context.get("temporal_events", []):
        event_id = event["event_id"]
        if event_id in out:
            raise C5cError(f"duplicate_temporal_event_id:{event_id}")
        out[event_id] = event
    return out


def validate_timezone_id(value):
    if value is None:
        return "missing"
    try:
        ZoneInfo(str(value))
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return "invalid"
    return "valid_iana_date_only"


def assess_deadline_request(req, deadline_bindings, temporal_events, deadlines, rules, upstream_blocked):
    wrapped = deadlines.get(req["deadline_ref"])
    if wrapped is None:
        raise C5cError(f"unknown_deadline_ref:{req['deadline_ref']}")
    record = wrapped["record"]
    binding_ref = req.get("binding_ref")
    binding = None if binding_ref is None else deadline_bindings.get(binding_ref)
    if binding_ref is not None and binding is None:
        raise C5cError(f"unknown_deadline_binding_ref:{binding_ref}")

    rule_ref = None if binding is None else binding["rule_ref"]
    trigger_ref = None if binding is None else binding["trigger_event_ref"]
    event = None if trigger_ref is None else temporal_events.get(trigger_ref)
    trigger_type = None if event is None else event["event_type"]
    trigger_date_raw = None if event is None else event["event_date"]
    trigger_date_source_ref = None if event is None else event["event_date_source_ref"]
    trigger_date_provenance_kind = None if event is None else event["event_date_provenance_kind"]
    timezone_validation = validate_timezone_id(record.get("timezone"))

    out = {
        "request_id": req["request_id"],
        "deadline_ref": req["deadline_ref"],
        "binding_ref": binding_ref,
        "rule_ref": rule_ref,
        "module_id": wrapped["module_id"],
        "kind": record["kind"],
        "disposition": "candidate",
        "calculation_status": "candidate_only",
        "calculated_date": None,
        "trigger_ref": trigger_ref,
        "trigger_event_type": trigger_type,
        "trigger_date": trigger_date_raw,
        "trigger_date_source_ref": trigger_date_source_ref,
        "trigger_date_provenance_kind": trigger_date_provenance_kind,
        "calendar": record["calendar"],
        "timezone": record.get("timezone"),
        "timezone_validation": timezone_validation,
        "operator": record["calculation"]["operator"],
        "amount": record["calculation"].get("amount"),
        "suspension_state": req["suspension_state"],
        "extension_state": req["extension_state"],
        "source_refs": sorted(record["source_refs"]),
        "suspension_conditions": list(record.get("suspension_conditions", [])),
        "extension_conditions": list(record.get("extension_conditions", [])),
        "effect_on_other_remedies": record.get("effect_on_other_remedies"),
        "rationale_codes": [],
        "review_required": True,
        "detail": "The deadline record is a candidate. Exact date arithmetic requires an explicit per-deadline binding to a source-linked rule and the exact typed trigger event/date evidence used for that request."
    }
    if upstream_blocked:
        out.update({"disposition": "blocked", "calculation_status": "blocked", "rationale_codes": ["upstream_c5a_c5b_chain_blocked"], "detail": "Upstream C5a/C5b is blocked, so C5c does not promote a deadline calculation."})
        return out
    if binding is None:
        out["rationale_codes"].append("scoped_deadline_binding_required")
        return out
    if binding["deadline_ref"] != req["deadline_ref"]:
        out["rationale_codes"].append("deadline_binding_deadline_mismatch")
        return out
    if event is None:
        out["rationale_codes"].append("deadline_trigger_event_ref_not_bound")
        return out
    rule = rules.get(rule_ref)
    if rule is None:
        out["rationale_codes"].append("deadline_rule_ref_not_bound")
        return out
    if rule["module_id"] != wrapped["module_id"]:
        out["rationale_codes"].append("deadline_rule_module_mismatch")
        return out
    if not (set(rule["record"].get("source_refs", [])) & set(record.get("source_refs", []))):
        out["rationale_codes"].append("deadline_rule_source_support_mismatch")
        return out
    if normalize_trigger_label(trigger_type) != normalize_trigger_label(record.get("trigger_event")):
        out["rationale_codes"].append("deadline_trigger_event_mismatch")
        return out
    if trigger_date_provenance_kind in {"model_inference", "user_assertion"}:
        out["rationale_codes"].append("deadline_trigger_date_not_evidence_bound")
        return out
    try:
        d = date.fromisoformat(trigger_date_raw)
    except (TypeError, ValueError):
        out["rationale_codes"].append("deadline_trigger_date_invalid")
        return out
    if timezone_validation == "missing":
        out["rationale_codes"].append("deadline_timezone_missing")
        return out
    if timezone_validation == "invalid":
        out["rationale_codes"].append("deadline_timezone_invalid")
        return out
    if req["suspension_state"] != "none":
        out["rationale_codes"].append("deadline_suspension_not_resolved")
        return out
    if req["extension_state"] != "none":
        out["rationale_codes"].append("deadline_extension_not_resolved")
        return out
    calculated, error = exact_deadline(record, d, record["calculation"].get("inclusion_rule"))
    if error:
        out["rationale_codes"].append(error)
        return out
    out.update({
        "calculation_status": "exact",
        "calculated_date": calculated.isoformat(),
        "rationale_codes": ["deadline_scoped_binding_rule_event_date_bound", "deadline_timezone_id_validated_date_only", "mechanical_date_arithmetic_complete"],
        "detail": "C5c completed deterministic date-only arithmetic from a scoped binding that links this deadline request to a source-linked rule and the typed trigger event/date evidence. The IANA timezone identifier is validated, but date-only arithmetic does not depend on UTC-offset resolution. Legal applicability and substantive trigger satisfaction remain subject to review."
    })
    return out

def normalize_issue(value):
    return " ".join(str(value).strip().casefold().replace("_", " ").split())


def case_cross_border_signal(case_obj):
    g = case_obj.get("geography", {})
    pairs = [
        (g.get("residence_state"), g.get("work_state")),
        (g.get("residence_state"), g.get("intended_residence_state")),
        (g.get("application_country"), g.get("deciding_state")),
        (g.get("application_country"), g.get("representing_state")),
    ]
    for a, b in pairs:
        if a and b and not te.same_jurisdiction(a, b):
            return True
    return False


def assess_route_request(req, core_routes, module_routes, authorities, regimes, case_obj, upstream_blocked):
    if req["route_ref"] in core_routes:
        r = core_routes[req["route_ref"]]
        issue_match = normalize_issue(req["issue_type"]) in {normalize_issue(x) for x in r["issue_types"]}
        target_match = req["target_authority_level"] in set(r["target_authority_levels"])
        out = {
            "request_id": req["request_id"], "route_ref": r["route_id"], "route_origin": "core", "module_id": None,
            "authority_ref": r["authority_ref"], "authority_name": r["authority_name"], "authority_level": r["authority_level"],
            "authority_competence": list(r["authority_competence"]),
            "target_authority_level_validation": "matched" if target_match else "mismatched",
            "disposition": "candidate", "issue_match": "matched" if issue_match else "not_matched",
            "powers": list(r["powers"]), "limits": list(r["limits"]), "source_refs": sorted(r["source_refs"]),
            "legal_basis_refs": [], "verified_at": r["verified_at"], "rationale_codes": [], "review_required": True,
            "detail": "The route is a source-backed escalation candidate only; C5c does not recommend or rank it."
        }
        if upstream_blocked:
            out.update({"disposition": "blocked", "rationale_codes": ["upstream_c5a_c5b_chain_blocked"], "detail": "Upstream C5a/C5b is blocked, so C5c does not promote an escalation candidate."})
            return out
        if not target_match:
            out.update({"disposition": "not_indicated", "rationale_codes": ["target_authority_level_mismatch"], "detail": "The requested target authority level falls outside the route catalogue boundary."})
            return out
        if not issue_match:
            out.update({"disposition": "not_indicated", "rationale_codes": ["route_issue_type_not_advertised"], "detail": "The requested issue type is not advertised by this bounded route catalogue entry."})
            return out
        if r["route_id"] == "eu:route:solvit":
            directive = regime_map(regimes).get("legal_regime.directive_2004_38")
            if not case_cross_border_signal(case_obj) or directive is None or directive.get("disposition") != "candidate":
                out.update({"disposition": "not_indicated", "rationale_codes": ["solvit_cross_border_eu_rights_context_not_established"], "detail": "SOLVIT remains unpromoted because the bound case does not establish both structural cross-border context and a usable EU free-movement regime candidate."})
                return out
        out["rationale_codes"] = ["source_backed_route_candidate", "no_route_ranking_or_recommendation"]
        return out

    wrapped = module_routes.get(req["route_ref"])
    if wrapped is None:
        raise C5cError(f"unknown_route_ref:{req['route_ref']}")
    r = wrapped["record"]
    authority = authorities.get(r["authority_ref"])
    if authority is None:
        raise C5cError(f"route_authority_missing_after_conformance:{r['route_id']}:{r['authority_ref']}")
    issue_match = normalize_issue(req["issue_type"]) in {normalize_issue(x) for x in r.get("issue_types", [])}
    out = {
        "request_id": req["request_id"], "route_ref": r["route_id"], "route_origin": "module", "module_id": wrapped["module_id"],
        "authority_ref": r["authority_ref"], "authority_name": authority["record"]["name"], "authority_level": "unknown",
        "authority_competence": list(authority["record"].get("competence", [])),
        "target_authority_level_validation": "unknown_frozen_contract",
        "disposition": "candidate" if issue_match else "not_indicated", "issue_match": "matched" if issue_match else "not_matched",
        "powers": list(r["powers"]), "limits": list(r["limits"]), "source_refs": sorted(r["source_refs"]),
        "legal_basis_refs": sorted(r["legal_basis_refs"]), "verified_at": r.get("verified_at"),
        "rationale_codes": ["conformant_case_relevant_module_route_bound", "module_authority_level_not_structured_in_frozen_contract", "requested_target_authority_level_not_machine_checked_for_module_route"] if issue_match else ["route_issue_type_not_advertised", "module_authority_level_not_structured_in_frozen_contract", "requested_target_authority_level_not_machine_checked_for_module_route"],
        "review_required": True,
        "detail": "The conformant country-module route is preserved as a candidate. The frozen module contract does not encode a normalized authority-level field, so C5c does not infer one from module family or geography."
    }
    if upstream_blocked:
        out.update({"disposition": "blocked", "rationale_codes": ["upstream_c5a_c5b_chain_blocked"], "detail": "Upstream C5a/C5b is blocked, so C5c does not promote a module route candidate."})
    return out


def build(case_obj, regimes, c5b, element_bundle=None, context=None, module_pairs=None, source_pack=None):
    validate_obj("case-input", case_obj)
    if case_obj.get("privacy_classification") == "private":
        raise C5cError("private_data_disabled")
    validate_obj("legal-regime-candidates", regimes)
    validate_obj("c5b-hierarchy-principles", c5b)
    if case_obj["case_id"] != regimes["case_id"] or case_obj["case_id"] != c5b["case_id"]:
        raise C5cError("case_id_mismatch")
    case_digest = digest_obj(case_obj)
    if regimes["bound_case_sha256"] != case_digest:
        raise C5cError("regime_case_binding_mismatch")
    if c5b["bindings"]["case_sha256"] != case_digest:
        raise C5cError("c5b_case_binding_mismatch")
    if c5b["bindings"]["regime_candidates_sha256"] != digest_obj(regimes):
        raise C5cError("c5b_regime_binding_mismatch")

    if element_bundle is not None:
        validate_element_bundle(element_bundle)
        element_digest = digest_obj(element_bundle)
    else:
        element_digest = None
    expected_element_digest = regimes.get("bound_element_bundle_sha256")
    if expected_element_digest is not None:
        if element_bundle is None:
            raise C5cError("element_bundle_required_for_bound_chain")
        if element_digest != expected_element_digest:
            raise C5cError("regime_element_bundle_binding_mismatch")
        if c5b["bindings"]["element_bundle_sha256"] != element_digest:
            raise C5cError("c5b_element_bundle_binding_mismatch")
    elif element_bundle is not None:
        raise C5cError("unexpected_element_bundle_for_unbound_chain")

    if source_pack is None:
        source_pack = load_json(SOURCE_PACK_FILE)
    validate_obj("core-source-pack", source_pack)
    source_pack_digest = digest_obj(source_pack)
    if regimes["source_pack_sha256"] != source_pack_digest:
        raise C5cError("regime_source_pack_binding_mismatch")
    if c5b["bindings"]["source_pack_sha256"] != source_pack_digest:
        raise C5cError("c5b_source_pack_binding_mismatch")
    core_sources = source_pack_index(source_pack)

    if context is None:
        context = {"context_version": "0.1.0", "case_id": case_obj["case_id"], "evidence_requests": [], "deadline_requests": [], "route_requests": []}
        context_digest = None
    else:
        validate_obj("c5c-context", context)
        if context["case_id"] != case_obj["case_id"]:
            raise C5cError("context_case_id_mismatch")
        context_digest = digest_obj(context)

    bindings, module_sources, rules, deadlines, authorities, module_routes = load_module_pairs(module_pairs, case_obj, c5b)
    all_sources = dict(core_sources)
    for sid, wrapped in module_sources.items():
        if sid in all_sources:
            raise C5cError(f"duplicate_cross_layer_source_id:{sid}")
        all_sources[sid] = wrapped

    route_catalog, core_routes = load_core_route_catalog(core_sources)
    idx = index_elements(element_bundle)
    deadline_bindings = deadline_binding_index(context)
    temporal_events = temporal_event_index(context)
    basis_set = known_basis_refs(regimes, c5b, core_sources, module_sources, rules)
    seen = set()
    for group in (context["evidence_requests"], context["deadline_requests"], context["route_requests"]):
        for req in group:
            if req["request_id"] in seen:
                raise C5cError(f"duplicate_context_request_id:{req['request_id']}")
            seen.add(req["request_id"])
    for req in context["evidence_requests"]:
        unknown = sorted(set(req["basis_refs"]) - basis_set)
        if unknown:
            raise C5cError("unknown_evidence_basis_ref:" + req["request_id"] + ":" + ",".join(unknown))

    upstream_blocked = regimes["resolution_status"] == "blocked" or c5b["resolution_status"] == "blocked"
    evidence = [assess_evidence_request(x, idx, regimes, c5b, all_sources, module_sources, rules, upstream_blocked) for x in context["evidence_requests"]]
    deadline_results = [assess_deadline_request(x, deadline_bindings, temporal_events, deadlines, rules, upstream_blocked) for x in context["deadline_requests"]]
    route_results = [assess_route_request(x, core_routes, module_routes, authorities, regimes, case_obj, upstream_blocked) for x in context["route_requests"]]

    unresolved = []
    for item in evidence:
        if item["disposition"] == "blocked":
            unresolved.append({"code": item["rationale_codes"][0] if item["rationale_codes"] else "evidence_blocked", "scope": item["request_id"], "detail": "; ".join(item["limitations"]) or "Evidence review blocked."})
    for item in deadline_results:
        if item["calculation_status"] != "exact":
            code = item["rationale_codes"][0] if item["rationale_codes"] else "deadline_exact_calculation_not_available"
            unresolved.append({"code": code, "scope": item["request_id"], "detail": item["detail"]})
    for item in route_results:
        if item["disposition"] in {"blocked", "not_indicated"}:
            code = item["rationale_codes"][0] if item["rationale_codes"] else "route_not_promoted"
            unresolved.append({"code": code, "scope": item["request_id"], "detail": item["detail"]})

    result = {
        "engine_version": ENGINE_VERSION,
        "ruleset_version": RULESET_VERSION,
        "contract_version": CONTRACT_VERSION,
        "element_model_version": ELEMENT_MODEL_VERSION,
        "case_id": case_obj["case_id"],
        "bindings": {
            "case_sha256": case_digest,
            "regime_candidates_sha256": digest_obj(regimes),
            "c5b_sha256": digest_obj(c5b),
            "element_bundle_sha256": element_digest,
            "context_sha256": context_digest,
            "source_pack_version": source_pack["pack_version"],
            "source_pack_sha256": source_pack_digest,
            "core_route_catalog_version": route_catalog["catalog_version"],
            "core_route_catalog_sha256": digest_obj(route_catalog),
            "module_bindings": bindings,
        },
        "resolution_status": "blocked" if upstream_blocked else "ready",
        "final_c5c_resolution": "not_determined",
        "evidence_assessments": evidence,
        "deadline_assessments": deadline_results,
        "route_assessments": route_results,
        "unresolved": unresolved,
        "limitations": [
            "C5c produces evidence, deadline and authority/route review candidates; it does not issue a final legal conclusion, final evidence-sufficiency finding or route recommendation.",
            "The Jia-based freedom-of-proof candidate is scoped to dependency evidence and must not be generalized into a universal rule for every documentary requirement.",
            "A proof-restriction label is preserved as an input claim; source existence does not prove that the restriction is legally valid or exhaustive.",
            "Exact deadline arithmetic requires a scoped per-deadline binding to a source-linked rule and typed trigger event/date evidence, a valid IANA timezone identifier, resolved suspension/extension states and a mechanically supported operator/inclusion rule. Legacy singleton time elements do not by themselves authorize exact multi-deadline calculation.",
            "Business-day and source-defined deadlines remain non-exact until a trusted calendar/source-defined calculation contract exists.",
            "Escalation routes are candidates only. Powers and limits are preserved, and C5c does not rank routes, infer missing authority levels from country-module family, or promise individual redress.",
            "Core EU complaint-route catalogue entries are bounded to their verified source scope and do not replace case-specific admissibility or competence review."
        ],
    }
    validate_obj("c5c-evidence-deadline-authority", result)
    return result


def main():
    ap = argparse.ArgumentParser(description="Build C5c evidence/freedom-of-proof, deadline and authority/escalation candidates")
    ap.add_argument("case")
    ap.add_argument("regimes")
    ap.add_argument("c5b")
    ap.add_argument("--elements")
    ap.add_argument("--context")
    ap.add_argument("--module-pair", nargs=2, action="append", metavar=("MANIFEST", "EXPORT"))
    ap.add_argument("--source-pack", default=str(SOURCE_PACK_FILE))
    ap.add_argument("--output")
    args = ap.parse_args()
    try:
        case_obj = load_json(Path(args.case))
        regimes = load_json(Path(args.regimes))
        c5b = load_json(Path(args.c5b))
        elements = load_json(Path(args.elements)) if args.elements else None
        context = load_json(Path(args.context)) if args.context else None
        source_pack = load_json(Path(args.source_pack))
        result = build(case_obj, regimes, c5b, elements, context, args.module_pair, source_pack)
        rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (C5cError, ContractError, OSError, ValueError) as e:
        print(json.dumps({"status": "invalid", "error": str(e)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
