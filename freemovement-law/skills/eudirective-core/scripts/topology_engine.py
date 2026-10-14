#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import element_model as em

ROOT = Path(__file__).resolve().parents[1]
JURISDICTION_ALIAS_FILE = ROOT / "references" / "jurisdictions" / "country-aliases.json"
ENGINE_VERSION = "0.1.1"
CONTRACT_VERSION = "0.2.0"
ELEMENT_MODEL_VERSION = "0.2.0"

CASE_ROLE_FIELDS = {
    "nationality_state": "nationality",
    "residence_state": "residence_state",
    "work_state": "work_state",
    "intended_residence_state": "intended_residence_state",
    "application_country": "application_country",
    "deciding_state": "deciding_state",
    "representing_state": "representing_state",
    "document_issuing_state": "document_issuing_country",
    "challenged_authority_state": "challenged_authority_state",
}
ELEMENT_ROLE_IDS = {
    "nationality_state": "geography.nationality_state",
    "residence_state": "geography.residence_state",
    "work_state": "geography.work_state",
    "host_state": "geography.host_state",
    "intended_residence_state": "geography.intended_residence_state",
    "application_country": "geography.application_country",
    "deciding_state": "geography.deciding_state",
    "representing_state": "geography.representing_state",
    "document_issuing_state": "geography.issuing_state",
    "challenged_authority_state": "geography.challenged_authority_state",
}
REQUEST_ROLE_TO_TOPOLOGY_ROLE = {
    "residence_state": "residence_state",
    "work_state": "work_state",
    "intended_residence_state": "intended_residence_state",
    "deciding_state": "deciding_state",
    "representing_state": "representing_state",
    "challenged_authority_state": "challenged_authority_state",
    "document_issuing_state": "document_issuing_state",
    "application_context": "application_country",
    "mission_context": "application_country",
}
SIGNAL_IDS = {
    "movement_cross_border": "movement.cross_border",
    "free_movement_exercised": "movement.free_movement_exercised",
    "frontier_worker_context": "movement.frontier_worker_context",
    "returnee_context": "movement.returnee_context",
}

class TopologyError(Exception):
    pass

_JURISDICTION_REGISTRY = None

def jurisdiction_key(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip() or None

def jurisdiction_registry():
    global _JURISDICTION_REGISTRY
    if _JURISDICTION_REGISTRY is None:
        try:
            data = load_json(JURISDICTION_ALIAS_FILE)
        except (ContractError, OSError) as e:
            raise TopologyError(f"jurisdiction_alias_registry_invalid:{e}")
        if data.get("registry_version") != "0.1.0" or data.get("canonical_form") != "ISO_3166_1_alpha_2" or not isinstance(data.get("aliases"), dict):
            raise TopologyError("jurisdiction_alias_registry_invalid")
        for alias, code in data["aliases"].items():
            if not isinstance(alias, str) or not alias or not isinstance(code, str) or not re.fullmatch(r"[A-Z]{2}", code):
                raise TopologyError("jurisdiction_alias_registry_invalid")
        _JURISDICTION_REGISTRY = data
    return _JURISDICTION_REGISTRY

def jurisdiction_aliases():
    return jurisdiction_registry()["aliases"]

def clean_jurisdiction(value):
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    key = jurisdiction_key(raw)
    return jurisdiction_aliases().get(key, raw)

def jurisdiction_identity(value):
    clean = clean_jurisdiction(value)
    if clean is None:
        return None
    key = jurisdiction_key(clean)
    alias = jurisdiction_aliases().get(key)
    return alias if alias is not None else f"raw:{key}"

def same_jurisdiction(a, b):
    if a is None or b is None:
        return False
    return jurisdiction_identity(a) == jurisdiction_identity(b)

def note_normalization(records, scope, raw, canonical):
    if raw is None or canonical is None:
        return
    raw_clean = str(raw).strip()
    if raw_clean and raw_clean != canonical:
        records.append({"scope": scope, "input": raw_clean, "canonical": canonical})

def index_elements(bundle):
    out = {}
    if bundle is None:
        return out
    for item in bundle["elements"]:
        out.setdefault(item["element_id"], []).append(item)
    return out

def single_element_value(idx, element_id):
    entries = idx.get(element_id, [])
    if not entries:
        return None
    if len(entries) != 1:
        raise TopologyError(f"multiple_values_for_singleton:{element_id}")
    return entries[0]["value"]

def build_topology(case_obj, element_bundle=None):
    validate_obj("case-input", case_obj)
    if case_obj["privacy_classification"] == "private":
        raise TopologyError("private_data_disabled")
    bundle_digest = None
    idx = {}
    if element_bundle is not None:
        catalog, _, invariants = em.load_model()
        em.check_bundle(element_bundle, catalog, invariants)
        bundle_digest = digest_obj(element_bundle)
        idx = index_elements(element_bundle)

    geography = case_obj.get("geography", {})
    roles = {
        "nationality_state": None,
        "residence_state": None,
        "work_state": None,
        "host_state": None,
        "intended_residence_state": None,
        "application_country": None,
        "deciding_state": None,
        "representing_state": None,
        "document_issuing_state": None,
        "challenged_authority_state": None,
    }
    conflicts = []
    unresolved = []
    jurisdiction_normalizations = []

    for role in roles:
        raw_case_value = geography.get(CASE_ROLE_FIELDS[role]) if role in CASE_ROLE_FIELDS else None
        raw_element_value = single_element_value(idx, ELEMENT_ROLE_IDS[role]) if ELEMENT_ROLE_IDS[role] in idx else None
        case_value = clean_jurisdiction(raw_case_value)
        element_value = clean_jurisdiction(raw_element_value)
        note_normalization(jurisdiction_normalizations, f"case.geography.{role}", raw_case_value, case_value)
        note_normalization(jurisdiction_normalizations, f"element.{ELEMENT_ROLE_IDS[role]}", raw_element_value, element_value)
        if case_value is not None and element_value is not None and not same_jurisdiction(case_value, element_value):
            conflicts.append({
                "code": "role_value_conflict",
                "role": role,
                "bound_value": case_value,
                "conflicting_value": element_value,
                "detail": "The case-input geography and bound element bundle disagree for the same topology role."
            })
            roles[role] = case_value
        else:
            roles[role] = case_value if case_value is not None else element_value

    signals = {}
    for name, element_id in SIGNAL_IDS.items():
        value = single_element_value(idx, element_id)
        if value is not None and not isinstance(value, bool):
            raise TopologyError(f"non_boolean_signal:{element_id}")
        signals[name] = value

    operational_role_names = [
        "residence_state", "work_state", "host_state", "intended_residence_state",
        "application_country", "deciding_state", "representing_state",
        "document_issuing_state", "challenged_authority_state"
    ]
    grouped = {}
    for role in operational_role_names:
        value = roles[role]
        if value is None:
            continue
        key = jurisdiction_identity(value)
        if key not in grouped:
            grouped[key] = {"jurisdiction": clean_jurisdiction(value), "roles": []}
        grouped[key]["roles"].append(role)
    state_roles = []
    for key in sorted(grouped):
        state_roles.append({"jurisdiction": grouped[key]["jurisdiction"], "roles": sorted(grouped[key]["roles"])})

    multi_state = {
        "status": "established" if len(state_roles) > 1 else "not_established",
        "jurisdiction_count": len(state_roles),
        "basis_refs": sorted([f"geography.{role}" for role in operational_role_names if roles[role] is not None])
    }

    residence = roles["residence_state"]
    work = roles["work_state"]
    if residence is None or work is None:
        cross_status = "undetermined"
        cross_detail = "Residence and work states are both required for a structural cross-border-work candidate."
    elif same_jurisdiction(residence, work):
        cross_status = "not_indicated"
        cross_detail = "Residence and work state are the same in the bound topology."
    else:
        cross_status = "candidate"
        cross_detail = "Residence and work states differ. This is a structural candidate only, not a legal frontier-worker determination."
    if signals["frontier_worker_context"] is True:
        if cross_status == "undetermined":
            cross_status = "candidate"
            cross_detail = "A frontier-worker context is explicitly asserted, but one or both structural state roles remain missing."
        elif cross_status == "not_indicated":
            unresolved.append({
                "code":"frontier_context_conflicts_with_structural_topology",
                "field":"movement.frontier_worker_context",
                "detail":"frontier_worker_context=true conflicts with same-state residence/work geography; preserve the structural result and review the assertion."
            })
    elif signals["frontier_worker_context"] is False and cross_status == "candidate":
        unresolved.append({
            "code":"frontier_context_conflicts_with_structural_topology",
            "field":"movement.frontier_worker_context",
            "detail":"frontier_worker_context=false does not erase the objective residence/work state difference; preserve the structural cross-border-work candidate and review the assertion."
        })
    cross_refs = [x for x in ["geography.residence_state" if residence else None, "geography.work_state" if work else None, "movement.frontier_worker_context" if signals["frontier_worker_context"] is not None else None] if x]

    returnee_signal = signals["returnee_context"]
    target = roles["intended_residence_state"] or roles["deciding_state"] or roles["residence_state"]
    if returnee_signal is True:
        returnee_status = "candidate"
        returnee_detail = "A returnee context is explicitly asserted. C5a preserves it as a review candidate and does not determine derived-right applicability."
        if roles["host_state"] is None:
            unresolved.append({"code":"returnee_host_state_missing","field":"geography.host_state","detail":"A prior/other host-state role is not bound for the asserted returnee context."})
        if target is None:
            unresolved.append({"code":"returnee_target_state_missing","field":"geography.intended_residence_state","detail":"No intended/deciding/current target state is bound for the asserted returnee context."})
    elif returnee_signal is False:
        returnee_status = "not_indicated"
        returnee_detail = "The bound element bundle explicitly records returnee_context=false."
    else:
        returnee_status = "undetermined"
        returnee_detail = "No explicit returnee-context element is bound; C5a does not infer returnee status from geography alone."
        nationality = roles["nationality_state"]
        host = roles["host_state"]
        if nationality is not None and target is not None and same_jurisdiction(nationality, target) and host is not None and not same_jurisdiction(host, target):
            unresolved.append({"code":"returnee_semantic_confirmation_missing","field":"movement.returnee_context","detail":"The topology resembles a return-to-nationality pattern, but an explicit returnee-context assertion is required before candidate generation."})
    returnee_refs = [x for x in ["movement.returnee_context" if returnee_signal is not None else None, "geography.host_state" if roles["host_state"] else None, "geography.nationality_state" if roles["nationality_state"] else None] if x]

    representing = roles["representing_state"]
    representation_status = "present" if representing is not None else "not_present"
    representation_detail = "A representing-state role is bound." if representing is not None else "No representing-state role is bound."

    request_checks = []
    for req in case_obj["module_requests"]:
        topo_role = REQUEST_ROLE_TO_TOPOLOGY_ROLE[req["role"]]
        expected = roles.get(topo_role)
        request_jurisdiction = clean_jurisdiction(req["jurisdiction"])
        note_normalization(jurisdiction_normalizations, f"module_request.{req['request_id']}.jurisdiction", req["jurisdiction"], request_jurisdiction)
        jurisdiction_mismatch = expected is not None and not same_jurisdiction(request_jurisdiction, expected)
        status = "unbound" if expected is None else ("mismatch" if jurisdiction_mismatch else "matched")
        destination = clean_jurisdiction(req.get("destination_state"))
        note_normalization(jurisdiction_normalizations, f"module_request.{req['request_id']}.destination_state", req.get("destination_state"), destination)
        destination_mismatch = False
        expected_destination = None
        if req["family"] == "applicant_country" and destination is not None:
            expected_destination = roles["intended_residence_state"] or roles["deciding_state"]
            destination_mismatch = expected_destination is not None and not same_jurisdiction(destination, expected_destination)
            if destination_mismatch:
                status = "mismatch"
        request_checks.append({
            "request_id": req["request_id"],
            "role": req["role"],
            "jurisdiction": request_jurisdiction,
            "status": status,
            "expected_jurisdiction": expected,
            "destination_state": destination
        })
        if jurisdiction_mismatch:
            conflicts.append({
                "code": "module_request_role_jurisdiction_mismatch",
                "role": req["role"],
                "bound_value": expected,
                "conflicting_value": request_jurisdiction,
                "detail": f"Module request {req['request_id']} jurisdiction contradicts the bound topology role."
            })
        if destination_mismatch:
            conflicts.append({
                "code": "applicant_destination_topology_mismatch",
                "role": "destination_state",
                "bound_value": expected_destination,
                "conflicting_value": destination,
                "detail": f"Applicant-country request {req['request_id']} destination contradicts the intended/deciding destination topology."
            })
        if status == "unbound":
            unresolved.append({
                "code": "module_request_role_unbound",
                "field": req["role"],
                "detail": f"Module request {req['request_id']} cannot be checked against a bound geography role."
            })

    out = {
        "engine_version": ENGINE_VERSION,
        "contract_version": CONTRACT_VERSION,
        "element_model_version": ELEMENT_MODEL_VERSION,
        "case_id": case_obj["case_id"],
        "bound_case_sha256": digest_obj(case_obj),
        "bound_element_bundle_sha256": bundle_digest,
        "jurisdiction_registry_version": jurisdiction_registry()["registry_version"],
        "jurisdiction_registry_sha256": digest_obj(jurisdiction_registry()),
        "resolution_status": "blocked" if conflicts else "ready",
        "roles": roles,
        "state_roles": state_roles,
        "input_signals": signals,
        "contexts": {
            "multi_state": multi_state,
            "cross_border_work": {
                "status": cross_status,
                "basis_refs": sorted(cross_refs),
                "review_required": cross_status == "candidate",
                "detail": cross_detail
            },
            "returnee": {
                "status": returnee_status,
                "basis_refs": sorted(returnee_refs),
                "review_required": returnee_status == "candidate",
                "detail": returnee_detail
            },
            "representation": {
                "status": representation_status,
                "basis_refs": ["geography.representing_state"] if representing is not None else [],
                "review_required": False,
                "detail": representation_detail
            }
        },
        "module_request_checks": sorted(request_checks, key=lambda x: x["request_id"]),
        "jurisdiction_normalizations": sorted(jurisdiction_normalizations, key=lambda x: (x["scope"], x["input"], x["canonical"])),
        "conflicts": conflicts,
        "unresolved": unresolved,
        "limitations": [
            "C5a topology output preserves typed state roles and structural candidates; it does not determine substantive EU-law applicability.",
            "A different residence/work topology is only a cross-border-work candidate; legal frontier-worker status remains review-only and cannot override the structural geography result.",
            "Known country-name/alpha-3 aliases are canonicalized to ISO 3166-1 alpha-2 identifiers before jurisdiction equality checks; unknown labels remain explicit raw identifiers.",
            "Returnee status is not inferred from geography alone; an explicit movement.returnee_context assertion is required."
        ]
    }
    validate_obj("topology-resolution", out)
    return out

def main():
    ap = argparse.ArgumentParser(description="Build a C5a typed topology resolution from case input and an optional element bundle")
    ap.add_argument("case")
    ap.add_argument("--elements")
    ap.add_argument("--output")
    args = ap.parse_args()
    try:
        case_obj = load_json(Path(args.case))
        elements = load_json(Path(args.elements)) if args.elements else None
        out = build_topology(case_obj, elements)
        data = json.dumps(out, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(data, encoding="utf-8")
        print(data, end="")
        return 0
    except (ContractError, em.ElementModelError, TopologyError, OSError) as e:
        print(json.dumps({"status":"invalid","error":str(e)}, sort_keys=True), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
