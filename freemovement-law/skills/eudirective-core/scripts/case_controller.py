#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import sys

from contract_validate import ContractError, canonical_bytes, digest_obj, load_json, validate_obj
from module_conformance import ConformanceError, validate_pair as validate_module_pair

PROTOCOL_VERSION = "0.3.0"
CONTRACT_VERSION = "0.2.0"
TRUST_PROFILE_VERSION = "0.1.0"
ELEMENT_MODEL_VERSION = "0.2.0"
CONFORMANCE_PROFILE_VERSION = "0.2.0"
MAX_REGISTERED_MODULES = 32
MAX_OUTBOUND_RECORDS = 16
MAX_HISTORY_EVENTS = 512
STAGES = ["initialized","intake_validated","context_pinned","requirements_set","analysis_proposed","analysis_validated","released"]
TESTED = {"supported", "not_supported", "not_applicable"}
STATUSES = TESTED | {"not_checked", "blocked"}
REASONS = {"none","not_evaluated","insufficient_evidence","source_missing_or_stale","source_not_live_rechecked","required_module_unavailable","optional_context_unavailable","module_incompatible","conflicting_information","unsupported_automated_evaluation","other"}
FRESHNESS_REQUIREMENTS = {"live_current","baseline_integrity"}
ROLE_GEOGRAPHY_FIELDS = {
    "residence_state": "residence_state",
    "work_state": "work_state",
    "intended_residence_state": "intended_residence_state",
    "deciding_state": "deciding_state",
    "representing_state": "representing_state",
    "challenged_authority_state": "challenged_authority_state",
    "document_issuing_state": "document_issuing_country",
    "application_context": "application_country",
    "mission_context": "application_country",
}

class ControllerError(Exception):
    pass

def atomic_write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def load_state(path: Path):
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ControllerError(f"cannot read state: {e}")
    if obj.get("protocol_version") != PROTOCOL_VERSION:
        raise ControllerError("unsupported controller protocol version")
    if obj.get("stage") not in STAGES:
        raise ControllerError("invalid controller stage")
    return obj

def check_mutation(state, case_id, expected_revision, allowed_stages):
    if state.get("case_id") != case_id:
        raise ControllerError("wrong_case")
    if state.get("revision") != expected_revision:
        raise ControllerError(f"stale_revision: expected current {state.get('revision')}")
    if state.get("stage") not in allowed_stages:
        raise ControllerError(f"invalid_transition: {state.get('stage')} not in {sorted(allowed_stages)}")

def event(state, action, detail=None):
    history = state.setdefault("history", [])
    if len(history) >= MAX_HISTORY_EVENTS:
        raise ControllerError("history_event_budget_exhausted")
    before = state["revision"]
    state["revision"] += 1
    history.append({"seq":len(history)+1,"action":action,"before_revision":before,"after_revision":state["revision"],"detail":detail or {}})

def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def parse_time(value):
    try:
        v=value[:-1]+"+00:00" if value.endswith("Z") else value
        dt=datetime.fromisoformat(v)
        if dt.tzinfo is None:
            raise ValueError("timezone required")
        return dt.astimezone(timezone.utc)
    except Exception as e:
        raise ControllerError(f"invalid_time:{e}")

def dependency_pins():
    return {
        "inter_skill_contract": CONTRACT_VERSION,
        "controller_protocol": PROTOCOL_VERSION,
        "element_model": ELEMENT_MODEL_VERSION,
        "conformance_profile": CONFORMANCE_PROFILE_VERSION,
        "trust_profile": TRUST_PROFILE_VERSION,
    }

def trust_state(state):
    return state.setdefault("trust_controls", {"lifecycle_epoch":0,"approval_tombstones":[],"outbound_records":{}})

def outbound_record(state, outbound_id):
    rec=trust_state(state)["outbound_records"].get(outbound_id)
    if not rec:
        raise ControllerError("unknown_outbound_id")
    return rec

def approval_is_expired(summary, time_of_check):
    valid_until=summary.get("valid_until")
    return bool(valid_until and parse_time(time_of_check) > parse_time(valid_until))

def validate_approval_binding(state, rec, approval, decision, time_of_check):
    validate_obj("approval-record", approval)
    if approval["decision"] != decision: raise ControllerError("approval_wrong_decision")
    if approval["case_id"] != state["case_id"]: raise ControllerError("approval_wrong_case")
    if approval["outbound_id"] != rec["outbound_id"]: raise ControllerError("approval_wrong_outbound")
    if approval["outbound_view_sha256"] != rec["view_sha256"]: raise ControllerError("approval_view_mismatch")
    if approval["purpose"] != rec["purpose"]: raise ControllerError("approval_purpose_mismatch")
    if sha256_text(approval["destination"]) != rec["destination_sha256"]: raise ControllerError("approval_destination_mismatch")
    if approval["action"] != rec["action"]: raise ControllerError("approval_action_mismatch")
    if approval["bound_prepared_revision"] != rec["prepared_revision"]: raise ControllerError("approval_revision_mismatch")
    if approval["approval_id"] in trust_state(state)["approval_tombstones"]: raise ControllerError("approval_revoked")
    if approval.get("valid_until") and parse_time(time_of_check) > parse_time(approval["valid_until"]): raise ControllerError("approval_expired")
    if parse_time(time_of_check) < parse_time(approval["approved_at"]): raise ControllerError("approval_not_yet_valid")
    if state.get("case",{}).get("privacy_classification") == "private" and approval["identity_assurance"] != "host_verified":
        raise ControllerError("private_outbound_requires_host_verified_approval")
    return {
        "approval_id": approval["approval_id"],
        "approval_sha256": digest_obj(approval),
        "approver_ref_sha256": sha256_text(approval["approver_ref"]),
        "identity_assurance": approval["identity_assurance"],
        "approved_at": approval["approved_at"],
        "valid_until": approval.get("valid_until"),
    }

def emit(obj):
    print(json.dumps(obj, sort_keys=True, ensure_ascii=False))

def module_key(manifest):
    return f"{manifest['module_family']}:{manifest['module_id']}:{manifest['jurisdiction']}"

def validate_manifest_export(manifest_path, export_path):
    manifest = load_json(Path(manifest_path)); export = load_json(Path(export_path))
    try:
        validate_module_pair(manifest, export)
    except ConformanceError as e:
        raise ControllerError(str(e))
    # Internal source references must exist.
    source_ids = {r["source_id"] for r in export["source_records"]}
    if len(source_ids) != len(export["source_records"]):
        raise ControllerError("duplicate_source_id")
    full_text_source_ids = {
        r["source_id"] for r in export["source_records"]
        if r.get("content_kind") == "authoritative_bundled_text" and r.get("authenticity_state") == "verified_official"
    }
    verified_note_source_ids = {
        r["source_id"] for r in export["source_records"]
        if r.get("content_kind") == "verified_source_note" and r.get("authenticity_state") == "verified_identity_version"
    }
    usable_source_ids = full_text_source_ids | verified_note_source_ids
    # Backward-compatible field name, now deliberately means full verified text only.
    authoritative_source_ids = full_text_source_ids
    rule_ids = {r["rule_id"] for r in export["rule_records"]}
    auth_ids = {r["authority_id"] for r in export["authority_records"]}
    op_ids = {r["record_id"] for r in export["operational_records"]}
    deadline_ids = {r["deadline_id"] for r in export["deadline_records"]}
    route_ids = {r["route_id"] for r in export["route_records"]}
    attack_angle_ids = {r["attack_angle_id"] for r in export["attack_angle_records"]}
    gap_ids = {r["gap_id"] for r in export["gap_records"]}
    for r in export["rule_records"]:
        refs = set(r["source_refs"])
        unknown = refs - source_ids
        if unknown:
            raise ControllerError(f"rule_unknown_source_refs:{sorted(unknown)}")
        unusable = refs - usable_source_ids
        if unusable:
            raise ControllerError(f"rule_unusable_source_refs:{sorted(unusable)}")
        if r["interpretation_status"] == "direct_text":
            text_ref = r.get("text_source_ref")
            if not text_ref or text_ref not in refs:
                raise ControllerError("direct_text_missing_text_source_ref")
            if text_ref not in full_text_source_ids:
                raise ControllerError(f"direct_text_requires_full_text_source:{text_ref}")
        note_refs = refs & verified_note_source_ids
        if note_refs and r["interpretation_status"] != "direct_text" and not r.get("support_scope"):
            raise ControllerError(f"note_backed_rule_requires_support_scope:{sorted(note_refs)}")
    for r in export["authority_records"]:
        unknown = set(r["source_refs"]) - source_ids
        if unknown:
            raise ControllerError(f"authority_unknown_source_refs:{sorted(unknown)}")
        unverified = set(r["source_refs"]) - usable_source_ids
        if unverified:
            raise ControllerError(f"authority_unverified_source_refs:{sorted(unverified)}")
    for r in export["operational_records"]:
        unknown = set(r["source_refs"]) - source_ids
        if unknown:
            raise ControllerError(f"operational_unknown_source_refs:{sorted(unknown)}")
        unverified = set(r["source_refs"]) - usable_source_ids
        if unverified:
            raise ControllerError(f"operational_unverified_source_refs:{sorted(unverified)}")
    for r in export["deadline_records"]:
        unknown = set(r["source_refs"]) - source_ids
        if unknown:
            raise ControllerError(f"deadline_unknown_source_refs:{sorted(unknown)}")
        unverified = set(r["source_refs"]) - usable_source_ids
        if unverified:
            raise ControllerError(f"deadline_unverified_source_refs:{sorted(unverified)}")
    for r in export["route_records"]:
        unknown = (set(r["source_refs"]) | set(r["legal_basis_refs"])) - source_ids
        if unknown:
            raise ControllerError(f"route_unknown_source_refs:{sorted(unknown)}")
        unverified = (set(r["source_refs"]) | set(r["legal_basis_refs"])) - usable_source_ids
        if unverified:
            raise ControllerError(f"route_unverified_source_refs:{sorted(unverified)}")
        if r["authority_ref"] not in auth_ids:
            raise ControllerError(f"route_unknown_authority_ref:{r['authority_ref']}")
    return manifest, export, source_ids, authoritative_source_ids, usable_source_ids, rule_ids, auth_ids, op_ids, deadline_ids, route_ids, attack_angle_ids, gap_ids

def cmd_init(args):
    path = Path(args.state)
    if path.exists():
        raise ControllerError("state_exists")
    parse_time(args.time_of_check)  # Generic controller backstop; C6 adds canonical UTC and fixture-only gate.
    state = {"protocol_version":PROTOCOL_VERSION,"trust_profile_version":TRUST_PROFILE_VERSION,"dependency_pins":dependency_pins(),"case_id":args.case_id,"run_id":args.run_id,"profile":args.profile,"time_of_check":args.time_of_check,"private_data_enabled":False,"revision":0,"stage":"initialized","case":None,"core_freshness_requirement":"live_current","module_requests":[],"modules":{},"missing_optional_modules":[],"stale_required_modules":[],"freshness_blocked_required_modules":[],"reference_index":{"fact_ids":[],"source_ids":[],"authoritative_source_ids":[],"usable_source_ids":[],"rule_ids":[],"authority_ids":[],"operational_ids":[],"deadline_ids":[],"route_ids":[],"attack_angle_ids":[],"gap_ids":[],"owned_ids":[]},"requirements":{},"analysis":None,"validation_receipt":None,"release_receipt":None,"trust_controls":{"lifecycle_epoch":0,"approval_tombstones":[],"outbound_records":{}},"history":[]}
    atomic_write_json(path, state); emit({"status":"initialized","revision":0,"stage":"initialized"})

def cmd_status(args):
    s = load_state(Path(args.state))
    allowed = {
        "initialized":["accept-case"],
        "intake_validated":["register-module","freeze-context"],
        "context_pinned":["set-requirements"],
        "requirements_set":["update-requirement","propose-analysis"],
        "analysis_proposed":["validate-analysis"],
        "analysis_validated":["release"],
        "released":["prepare-outbound","authorize-outbound","revoke-approval","authorize-retry","begin-delivery","record-delivery"]
    }[s["stage"]]
    allowed = allowed + ["checkpoint"]
    emit({"case_id":s["case_id"],"run_id":s["run_id"],"revision":s["revision"],"stage":s["stage"],"profile":s["profile"],"allowed_operations":allowed,"missing_optional_modules":s.get("missing_optional_modules",[]),"requirements":s.get("requirements",{}),"stale_required_modules":s.get("stale_required_modules",[]),"freshness_blocked_required_modules":s.get("freshness_blocked_required_modules",[]),"private_data_enabled":s.get("private_data_enabled",False),"trust_profile_version":s.get("trust_profile_version"),"lifecycle_epoch":trust_state(s)["lifecycle_epoch"],"outbound_states":{k:v["delivery_state"] for k,v in trust_state(s)["outbound_records"].items()}})

def cmd_accept_case(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"initialized"})
    obj=load_json(Path(args.input)); validate_obj("case-input",obj)
    if obj["case_id"] != args.case_id: raise ControllerError("wrong_case_input")
    if obj["privacy_classification"] == "private": raise ControllerError("private_data_disabled_c4_pending")
    s["case"]={"sha256":digest_obj(obj),"privacy_classification":obj["privacy_classification"],"procedure_type":obj["procedure_type"],"procedure_stage":obj["procedure_stage"]}
    s["core_freshness_requirement"]=obj.get("core_freshness_requirement","live_current")
    s["module_requests"]=[]
    geography=obj.get("geography",{})
    for req in obj["module_requests"]:
        field=ROLE_GEOGRAPHY_FIELDS.get(req["role"])
        expected=geography.get(field) if field else None
        if expected is not None and req["jurisdiction"].lower()!=str(expected).lower():
            raise ControllerError(f"module_request_geography_mismatch:{req['request_id']}:{req['role']}:{req['jurisdiction']}:{expected}")
        if req["family"]=="applicant_country":
            intended=geography.get("intended_residence_state") or geography.get("deciding_state")
            if intended is not None and req.get("destination_state") and req["destination_state"].lower()!=str(intended).lower():
                raise ControllerError(f"applicant_destination_geography_mismatch:{req['request_id']}:{req['destination_state']}:{intended}")
        item=dict(req); item["freshness_requirement"]=item.get("freshness_requirement","live_current"); s["module_requests"].append(item)
    s["reference_index"]["fact_ids"]=sorted({x["fact_id"] for x in obj["facts"]})
    s["stage"]="intake_validated"; event(s,"accept-case",{"input_sha256":s["case"]["sha256"]}); atomic_write_json(p,s); emit({"status":"accepted","revision":s["revision"],"stage":s["stage"],"sha256":s["case"]["sha256"]})

def cmd_register_module(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"intake_validated"})
    m,e,sources,authoritative_sources,usable_sources,rules,auths,ops,deadlines,routes,attack_angles,gaps=validate_manifest_export(args.manifest,args.export)
    key=module_key(m)
    if key in s["modules"]: raise ControllerError("module_already_registered")
    if len(s["modules"]) >= MAX_REGISTERED_MODULES: raise ControllerError("module_budget_exhausted")
    for existing in s["modules"].values():
        if existing["family"]==m["module_family"] and existing["jurisdiction"].lower()==m["jurisdiction"].lower():
            overlap=sorted(set(existing.get("supported_roles",[])) & set(m.get("supported_roles",[])))
            if overlap:
                raise ControllerError(f"ambiguous_module_role_coverage:{m['module_family']}:{m['jurisdiction']}:{','.join(overlap)}")
    new_owned=set(sources)|set(rules)|set(auths)|set(ops)|set(deadlines)|set(routes)|set(attack_angles)|set(gaps)
    collisions=new_owned & set(s["reference_index"].get("owned_ids",[]))
    if collisions: raise ControllerError("duplicate_global_record_ids:"+",".join(sorted(collisions)))
    s["modules"][key]={"family":m["module_family"],"module_id":m["module_id"],"id_namespace":m["id_namespace"],"jurisdiction":m["jurisdiction"],"module_version":m["module_version"],"pack_version":m["pack_version"],"freshness_state":m["freshness_state"],"supported_roles":m["supported_roles"],"destination_state_profiles_available":m.get("destination_state_profiles_available",[]),"manifest_sha256":digest_obj(m),"export_sha256":digest_obj(e),"source_ids":sorted(sources),"authoritative_source_ids":sorted(authoritative_sources),"usable_source_ids":sorted(usable_sources),"rule_ids":sorted(rules),"authority_ids":sorted(auths),"operational_ids":sorted(ops),"deadline_ids":sorted(deadlines),"route_ids":sorted(routes),"attack_angle_ids":sorted(attack_angles),"gap_ids":sorted(gaps),"owned_ids":sorted(new_owned)}
    for field, vals in [("source_ids",sources),("authoritative_source_ids",authoritative_sources),("usable_source_ids",usable_sources),("rule_ids",rules),("authority_ids",auths),("operational_ids",ops),("deadline_ids",deadlines),("route_ids",routes),("attack_angle_ids",attack_angles),("gap_ids",gaps),("owned_ids",new_owned)]:
        s["reference_index"][field]=sorted(set(s["reference_index"][field])|set(vals))
    event(s,"register-module",{"module_key":key,"manifest_sha256":digest_obj(m),"export_sha256":digest_obj(e)}); atomic_write_json(p,s); emit({"status":"registered","module_key":key,"revision":s["revision"],"stage":s["stage"]})

def request_satisfied(req, modules):
    for m in modules.values():
        if m["family"]!=req["family"] or m["jurisdiction"].lower()!=req["jurisdiction"].lower():
            continue
        if req["role"] not in m.get("supported_roles",[]):
            continue
        if req["family"]=="applicant_country":
            destination=req.get("destination_state")
            if destination and destination not in m.get("destination_state_profiles_available",[]):
                continue
        return True
    return False

def freshness_meets(actual, required):
    if required not in FRESHNESS_REQUIREMENTS:
        raise ControllerError(f"unsupported_freshness_requirement:{required}")
    if required == "live_current":
        return actual == "current"
    return actual in {"current", "baseline_verified_not_live_rechecked"}

def required_freshness_for_module(state, module):
    if module["family"] == "core_source":
        return state.get("core_freshness_requirement", "live_current")
    matches=[req for req in state["module_requests"] if req["required"] and req["family"]==module["family"] and req["jurisdiction"].lower()==module["jurisdiction"].lower() and req["role"] in module.get("supported_roles",[]) and (req["family"]!="applicant_country" or not req.get("destination_state") or req.get("destination_state") in module.get("destination_state_profiles_available",[]))]
    if not matches:
        return None
    return "live_current" if any(req.get("freshness_requirement","live_current")=="live_current" for req in matches) else "baseline_integrity"

def cmd_freeze_context(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"intake_validated"})
    if not any(m["family"]=="core_source" for m in s["modules"].values()): raise ControllerError("missing_core_source_pack")
    missing_required=[]; missing_optional=[]
    for req in s["module_requests"]:
        if not request_satisfied(req,s["modules"]):
            (missing_required if req["required"] else missing_optional).append(req["request_id"])
    if missing_required: raise ControllerError("missing_required_modules:"+",".join(sorted(missing_required)))
    stale_required=[]; freshness_blocks=[]
    for key,m in s["modules"].items():
        required_freshness=required_freshness_for_module(s,m)
        if required_freshness is None:
            continue
        if m["freshness_state"] == "stale":
            stale_required.append(key)
        if not freshness_meets(m["freshness_state"], required_freshness):
            freshness_blocks.append({"module_key":key,"actual_freshness":m["freshness_state"],"required_freshness":required_freshness})
    s["missing_optional_modules"]=sorted(missing_optional); s["stale_required_modules"]=sorted(stale_required); s["freshness_blocked_required_modules"]=sorted(freshness_blocks,key=lambda x:x["module_key"]); s["stage"]="context_pinned"; event(s,"freeze-context",{"missing_optional_modules":s["missing_optional_modules"],"stale_required_modules":s["stale_required_modules"],"freshness_blocked_required_modules":s["freshness_blocked_required_modules"]}); atomic_write_json(p,s); emit({"status":"context_pinned","revision":s["revision"],"missing_optional_modules":s["missing_optional_modules"],"stale_required_modules":s["stale_required_modules"],"freshness_blocked_required_modules":s["freshness_blocked_required_modules"]})

def cmd_set_requirements(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"context_pinned"})
    obj=load_json(Path(args.input)); validate_obj("requirement-set",obj)
    reqs={}
    for r in obj["requirements"]:
        if r["requirement_id"] in reqs: raise ControllerError("duplicate_requirement_id")
        reqs[r["requirement_id"]]={"area":r["area"],"scope":r.get("scope","case"),"required_for_full_release":r["required_for_full_release"],"description":r.get("description",""),"status":"not_checked","reason":"not_evaluated","detail":""}
    s["requirements"]=reqs; s["stage"]="requirements_set"; event(s,"set-requirements",{"count":len(reqs),"input_sha256":digest_obj(obj)}); atomic_write_json(p,s); emit({"status":"requirements_set","revision":s["revision"],"count":len(reqs)})

def cmd_update_requirement(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"requirements_set"})
    if args.requirement_id not in s["requirements"]: raise ControllerError("unknown_requirement")
    if args.status not in STATUSES: raise ControllerError("invalid_requirement_status")
    reason=getattr(args,"reason",None)
    if args.status in TESTED:
        reason=reason or "none"
        if reason != "none": raise ControllerError("tested_requirement_reason_must_be_none")
    elif args.status == "not_checked":
        reason=reason or "not_evaluated"
    else:
        if not reason or reason in {"none","not_evaluated"}: raise ControllerError("blocked_requirement_requires_reason")
    if reason not in REASONS: raise ControllerError("invalid_requirement_reason")
    req=s["requirements"][args.requirement_id]; req["status"]=args.status; req["reason"]=reason; req["detail"]=getattr(args,"detail",None) or ""
    event(s,"update-requirement",{"requirement_id":args.requirement_id,"status":args.status,"reason":reason,"scope":req.get("scope","case")}); atomic_write_json(p,s); emit({"status":"updated","revision":s["revision"],"requirement_id":args.requirement_id,"requirement_status":args.status,"reason":reason,"scope":req.get("scope","case")})

def cmd_propose_analysis(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"requirements_set"})
    obj=load_json(Path(args.input)); validate_obj("controlled-analysis",obj)
    if obj["case_id"]!=args.case_id: raise ControllerError("analysis_wrong_case")
    if obj["bound_state_revision"]!=s["revision"]: raise ControllerError(f"analysis_stale_revision: expected {s['revision']}")
    s["analysis"]={"sha256":digest_obj(obj),"analysis_id":obj["analysis_id"],"requested_release_mode":obj["requested_release_mode"]}; s["stage"]="analysis_proposed"; event(s,"propose-analysis",{"analysis_sha256":s["analysis"]["sha256"]}); atomic_write_json(p,s); emit({"status":"analysis_proposed","revision":s["revision"],"sha256":s["analysis"]["sha256"]})

def all_refs(obj):
    out={"fact_ids":set(),"source_ids":set(),"rule_ids":set(),"authority_ids":set(),"deadline_ids":set(),"route_ids":set(),"attack_angle_ids":set()}
    for f in obj["findings"]:
        out["fact_ids"].update(f["fact_refs"]); out["source_ids"].update(f["source_refs"]); out["rule_ids"].update(f["rule_refs"]); out["authority_ids"].update(f["authority_refs"]); out["route_ids"].update(f.get("route_refs",[])); out["attack_angle_ids"].update(f.get("attack_angle_refs",[]))
    for d in obj["deadlines"]:
        out["source_ids"].update(d["source_refs"]); out["rule_ids"].update(d.get("rule_refs",[])); out["deadline_ids"].update(d.get("deadline_refs",[]))
    for r in obj["recommendations"]:
        out["fact_ids"].update(r["fact_refs"]); out["source_ids"].update(r["source_refs"]); out["authority_ids"].update(r["authority_refs"]); out["route_ids"].update(r.get("route_refs",[])); out["attack_angle_ids"].update(r.get("attack_angle_refs",[]))
    return out

def cmd_validate_analysis(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"analysis_proposed"})
    obj=load_json(Path(args.input)); validate_obj("controlled-analysis",obj)
    if obj["case_id"]!=args.case_id: raise ControllerError("analysis_wrong_case")
    if digest_obj(obj)!=s["analysis"]["sha256"]: raise ControllerError("analysis_changed_since_proposal")
    refs=all_refs(obj)
    for field in refs:
        known=set(s["reference_index"][field]); unknown=refs[field]-known
        if unknown: raise ControllerError(f"unknown_{field}:"+",".join(sorted(unknown)))
    unverified_sources=refs["source_ids"]-set(s["reference_index"].get("usable_source_ids",[]))
    if unverified_sources: raise ControllerError("unverified_source_ids:"+",".join(sorted(unverified_sources)))
    unresolved=[rid for rid,r in s["requirements"].items() if r["required_for_full_release"] and r["status"] not in TESTED]
    mode=obj["requested_release_mode"]
    if mode=="full" and unresolved: raise ControllerError("full_release_blocked_unresolved:"+",".join(sorted(unresolved)))
    if mode=="full" and s.get("freshness_blocked_required_modules"):
        raise ControllerError("full_release_blocked_freshness:"+",".join(x["module_key"] for x in s["freshness_blocked_required_modules"]))
    if mode=="limited" and (unresolved or s.get("freshness_blocked_required_modules")) and not obj["limitations"]: raise ControllerError("limited_release_requires_limitations")
    receipt={"protocol_version":PROTOCOL_VERSION,"contract_version":CONTRACT_VERSION,"trust_profile_version":TRUST_PROFILE_VERSION,"case_id":s["case_id"],"state_revision_before_validation":s["revision"],"analysis_sha256":digest_obj(obj),"release_mode":mode,"unresolved_required":sorted(unresolved),"freshness_blocked_required_modules":s.get("freshness_blocked_required_modules",[]),"module_export_digests":sorted(m["export_sha256"] for m in s["modules"].values()),"requirement_snapshot_sha256":digest_obj(s["requirements"]),"dependency_pins_sha256":digest_obj(s["dependency_pins"])}
    receipt["receipt_sha256"]=digest_obj(receipt)
    s["validation_receipt"]=receipt; s["stage"]="analysis_validated"; event(s,"validate-analysis",{"receipt_sha256":receipt["receipt_sha256"],"release_mode":mode}); atomic_write_json(p,s)
    Path(args.receipt).write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    emit({"status":"analysis_validated","revision":s["revision"],"receipt_sha256":receipt["receipt_sha256"],"release_mode":mode,"unresolved_required":sorted(unresolved)})

def render_markdown(obj, requirements, missing_optional, freshness_blocks):
    lines=["# Controlled analysis", "", obj["summary"], "", "## Applicable legal regime"]
    lines += [f"- {x}" for x in obj["applicable_legal_regime"]] or ["- None recorded."]
    lines += ["", "## Findings"]
    if obj["findings"]:
        for f in obj["findings"]:
            lines += [f"### {f['finding_id']}", f"Status: `{f['status']}`", "", f["claim"], ""]
            if f["uncertainties"]: lines += ["Uncertainties:"]+[f"- {x}" for x in f["uncertainties"]]+[""]
    else: lines += ["No findings recorded.",""]
    lines += ["## Deadlines"]
    if obj["deadlines"]:
        for d in obj["deadlines"]: lines += [f"- **{d['label']}**: {d['status']}" + (f" — {d['date']}" if d.get('date') else "")]
    else: lines += ["- No deadlines recorded."]
    lines += ["", "## Recommendations"]
    if obj["recommendations"]:
        for r in obj["recommendations"]: lines += [f"- **{r['priority']}** — {r['action']}"]
    else: lines += ["- No recommendations recorded."]
    lines += ["", "## Completeness"]
    for rid in sorted(requirements):
        r=requirements[rid]; line=f"- `{rid}`: `{r['status']}`; reason=`{r.get('reason','none')}`; scope=`{r.get('scope','case')}`"
        if r.get("detail"): line += f" — {r['detail']}"
        lines += [line]
    if missing_optional: lines += [f"- Missing optional module: `{x}`" for x in missing_optional]
    if freshness_blocks:
        for x in freshness_blocks: lines += [f"- Freshness blocked: `{x['module_key']}` actual=`{x['actual_freshness']}` required=`{x['required_freshness']}`"]
    lines += ["", "## Limitations"]
    lines += [f"- {x}" for x in obj["limitations"]] or ["- None recorded."]
    lines += ["", "---", f"Rendered deterministically by eudirective-core controller protocol v{PROTOCOL_VERSION}.", ""]
    return "\n".join(lines)

def cmd_release(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"analysis_validated"})
    obj=load_json(Path(args.input)); validate_obj("controlled-analysis",obj)
    if digest_obj(obj)!=s["validation_receipt"]["analysis_sha256"]: raise ControllerError("analysis_changed_after_validation")
    rec=json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    if rec.get("receipt_sha256")!=s["validation_receipt"]["receipt_sha256"]: raise ControllerError("validation_receipt_mismatch")
    check=dict(rec); claimed=check.pop("receipt_sha256",None)
    if digest_obj(check)!=claimed: raise ControllerError("validation_receipt_corrupt")
    out=render_markdown(obj,s["requirements"],s.get("missing_optional_modules",[]),s.get("freshness_blocked_required_modules",[])).encode("utf-8")
    Path(args.output).write_bytes(out)
    rr={"protocol_version":PROTOCOL_VERSION,"contract_version":CONTRACT_VERSION,"trust_profile_version":TRUST_PROFILE_VERSION,"case_id":s["case_id"],"analysis_sha256":digest_obj(obj),"validation_receipt_sha256":claimed,"rendered_sha256":hashlib.sha256(out).hexdigest(),"rendered_bytes":len(out),"release_mode":obj["requested_release_mode"],"dependency_pins_sha256":digest_obj(s["dependency_pins"])}; rr["receipt_sha256"]=digest_obj(rr)
    Path(args.release_receipt).write_text(json.dumps(rr,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    s["release_receipt"]=rr; s["stage"]="released"; event(s,"release",{"rendered_sha256":rr["rendered_sha256"],"receipt_sha256":rr["receipt_sha256"]}); atomic_write_json(p,s); emit({"status":"released","revision":s["revision"],"rendered_sha256":rr["rendered_sha256"],"receipt_sha256":rr["receipt_sha256"]})


def cmd_prepare_outbound(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"released"})
    obj=load_json(Path(args.input)); validate_obj("outbound-view",obj)
    if obj["case_id"] != s["case_id"]: raise ControllerError("outbound_wrong_case")
    if obj["bound_case_revision"] != s["revision"]: raise ControllerError(f"outbound_stale_revision: expected {s['revision']}")
    if not obj["eligible"]: raise ControllerError("outbound_not_eligible")
    ts=trust_state(s)
    if len(ts["outbound_records"]) >= MAX_OUTBOUND_RECORDS: raise ControllerError("outbound_record_budget_exhausted")
    if obj["outbound_id"] in ts["outbound_records"]: raise ControllerError("outbound_id_exists")
    prepared_revision=s["revision"]+1
    rec={
        "outbound_id":obj["outbound_id"],"view_sha256":digest_obj(obj),"policy_sha256":obj["policy_sha256"],"purpose":obj["purpose"],
        "destination_kind":obj["destination_kind"],"destination_sha256":sha256_text(obj["destination"]),"action":obj["action"],
        "max_attempts":obj["max_attempts"],"prepared_revision":prepared_revision,"authorization":None,"retry_authorizations":[],
        "attempt_count":0,"delivery_state":"prepared","last_delivery_result":None
    }
    ts["outbound_records"][obj["outbound_id"]]=rec
    event(s,"prepare-outbound",{"outbound_id":obj["outbound_id"],"view_sha256":rec["view_sha256"],"purpose":rec["purpose"],"destination_sha256":rec["destination_sha256"],"action":rec["action"]})
    atomic_write_json(p,s); emit({"status":"outbound_prepared","revision":s["revision"],"outbound_id":obj["outbound_id"],"view_sha256":rec["view_sha256"]})

def cmd_authorize_outbound(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"released"})
    approval=load_json(Path(args.approval)); rec=outbound_record(s,args.outbound_id)
    if rec["delivery_state"] != "prepared": raise ControllerError("outbound_not_prepared")
    summary=validate_approval_binding(s,rec,approval,"approve",args.time_of_check)
    if rec.get("authorization"): raise ControllerError("outbound_already_authorized")
    used={x.get("approval_id") for x in trust_state(s)["outbound_records"].values() for x in ([x.get("authorization")] + x.get("retry_authorizations",[])) if x}
    if summary["approval_id"] in used: raise ControllerError("approval_id_reused")
    rec["authorization"]=summary; rec["delivery_state"]="authorized"
    event(s,"authorize-outbound",{"outbound_id":rec["outbound_id"],"approval_id":summary["approval_id"],"approval_sha256":summary["approval_sha256"]})
    atomic_write_json(p,s); emit({"status":"outbound_authorized","revision":s["revision"],"outbound_id":rec["outbound_id"],"approval_id":summary["approval_id"]})

def cmd_revoke_approval(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"released"})
    ts=trust_state(s)
    if args.approval_id in ts["approval_tombstones"]: raise ControllerError("approval_already_revoked")
    found=False
    for rec in ts["outbound_records"].values():
        if rec.get("authorization") and rec["authorization"]["approval_id"]==args.approval_id:
            found=True
            if rec["delivery_state"] in {"authorized","prepared"}: rec["delivery_state"]="prepared"
        for a in rec.get("retry_authorizations",[]):
            if a["approval_id"]==args.approval_id:
                found=True
                if rec["delivery_state"]=="retry_authorized": rec["delivery_state"]="outcome_unknown"
    if not found: raise ControllerError("unknown_approval_id")
    ts["approval_tombstones"].append(args.approval_id); ts["approval_tombstones"].sort(); ts["lifecycle_epoch"]+=1
    event(s,"revoke-approval",{"approval_id":args.approval_id,"lifecycle_epoch":ts["lifecycle_epoch"]})
    atomic_write_json(p,s); emit({"status":"approval_revoked","revision":s["revision"],"approval_id":args.approval_id,"lifecycle_epoch":ts["lifecycle_epoch"]})

def cmd_authorize_retry(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"released"})
    approval=load_json(Path(args.approval)); rec=outbound_record(s,args.outbound_id)
    if rec["delivery_state"] != "outcome_unknown": raise ControllerError("retry_requires_outcome_unknown")
    if rec["attempt_count"] >= rec["max_attempts"]: raise ControllerError("delivery_attempt_budget_exhausted")
    summary=validate_approval_binding(s,rec,approval,"retry",args.time_of_check)
    used={x.get("approval_id") for x in trust_state(s)["outbound_records"].values() for x in ([x.get("authorization")] + x.get("retry_authorizations",[])) if x}
    if summary["approval_id"] in used: raise ControllerError("approval_id_reused")
    rec["retry_authorizations"].append(summary); rec["delivery_state"]="retry_authorized"
    event(s,"authorize-retry",{"outbound_id":rec["outbound_id"],"approval_id":summary["approval_id"],"approval_sha256":summary["approval_sha256"],"attempt_count":rec["attempt_count"]})
    atomic_write_json(p,s); emit({"status":"retry_authorized","revision":s["revision"],"outbound_id":rec["outbound_id"],"approval_id":summary["approval_id"]})

def cmd_begin_delivery(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"released"})
    rec=outbound_record(s,args.outbound_id); ts=trust_state(s)
    if rec["attempt_count"] >= rec["max_attempts"]: raise ControllerError("delivery_attempt_budget_exhausted")
    if rec["attempt_count"] == 0:
        if rec["delivery_state"] != "authorized" or not rec.get("authorization"): raise ControllerError("delivery_not_authorized")
        approval=rec["authorization"]
    else:
        if rec["delivery_state"] != "retry_authorized" or not rec.get("retry_authorizations"): raise ControllerError("retry_not_authorized")
        approval=rec["retry_authorizations"][-1]
    if approval["approval_id"] in ts["approval_tombstones"]: raise ControllerError("approval_revoked")
    if approval_is_expired(approval,args.time_of_check): raise ControllerError("approval_expired")
    rec["attempt_count"]+=1; rec["delivery_state"]="in_flight"; rec["last_delivery_result"]=None
    event(s,"begin-delivery",{"outbound_id":rec["outbound_id"],"attempt":rec["attempt_count"],"approval_id":approval["approval_id"]})
    atomic_write_json(p,s); emit({"status":"in_flight","revision":s["revision"],"outbound_id":rec["outbound_id"],"attempt":rec["attempt_count"]})

def cmd_record_delivery(args):
    p=Path(args.state); s=load_state(p); check_mutation(s,args.case_id,args.expected_revision,{"released"})
    rec=outbound_record(s,args.outbound_id)
    if rec["delivery_state"] != "in_flight": raise ControllerError("delivery_not_in_flight")
    rec["delivery_state"]=args.result; rec["last_delivery_result"]=args.result
    event(s,"record-delivery",{"outbound_id":rec["outbound_id"],"attempt":rec["attempt_count"],"result":args.result})
    atomic_write_json(p,s); emit({"status":args.result,"revision":s["revision"],"outbound_id":rec["outbound_id"],"attempt":rec["attempt_count"]})

def cmd_checkpoint(args):
    s=load_state(Path(args.state)); check_mutation(s,args.case_id,args.expected_revision,set(STAGES))
    base={"trust_profile_version":TRUST_PROFILE_VERSION,"case_id":s["case_id"],"controller_protocol":PROTOCOL_VERSION,"state_revision":s["revision"],"lifecycle_epoch":trust_state(s)["lifecycle_epoch"],"state_sha256":digest_obj(s),"approval_tombstones":list(trust_state(s)["approval_tombstones"]),"dependency_pins_sha256":digest_obj(s["dependency_pins"]),"snapshot":s}
    cp=dict(base); cp["checkpoint_sha256"]=digest_obj(base); validate_obj("control-checkpoint",cp); atomic_write_json(Path(args.checkpoint),cp)
    emit({"status":"checkpoint_written","case_id":s["case_id"],"revision":s["revision"],"checkpoint_sha256":cp["checkpoint_sha256"],"lifecycle_epoch":cp["lifecycle_epoch"]})

def cmd_validate_checkpoint(args):
    s=load_state(Path(args.state)); cp=load_json(Path(args.checkpoint)); validate_obj("control-checkpoint",cp)
    claimed=cp["checkpoint_sha256"]; base=dict(cp); base.pop("checkpoint_sha256")
    if digest_obj(base)!=claimed: raise ControllerError("checkpoint_corrupt")
    if cp["case_id"]!=s["case_id"]: raise ControllerError("checkpoint_wrong_case")
    if cp["state_sha256"]!=digest_obj(cp["snapshot"]): raise ControllerError("checkpoint_snapshot_digest_mismatch")
    if cp["dependency_pins_sha256"]!=digest_obj(s["dependency_pins"]): raise ControllerError("checkpoint_dependency_mismatch")
    if cp["state_revision"]!=s["revision"]: raise ControllerError("checkpoint_not_current_revision")
    if cp["lifecycle_epoch"]!=trust_state(s)["lifecycle_epoch"]: raise ControllerError("checkpoint_lifecycle_epoch_stale")
    if set(cp["approval_tombstones"])!=set(trust_state(s)["approval_tombstones"]): raise ControllerError("checkpoint_tombstone_mismatch")
    if cp["state_sha256"]!=digest_obj(s): raise ControllerError("checkpoint_state_mismatch")
    emit({"status":"checkpoint_valid","case_id":s["case_id"],"revision":s["revision"],"checkpoint_sha256":claimed,"lifecycle_epoch":cp["lifecycle_epoch"]})

def parser():
    ap=argparse.ArgumentParser(description="Deterministic case controller for eudirective-core protocol v0.3.0")
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("init"); p.add_argument("--state",required=True); p.add_argument("--case-id",required=True); p.add_argument("--run-id",required=True); p.add_argument("--profile",choices=["cooperative_local","enforced_sensitive_data"],required=True); p.add_argument("--time-of-check",required=True); p.set_defaults(fn=cmd_init)
    p=sub.add_parser("status"); p.add_argument("--state",required=True); p.set_defaults(fn=cmd_status)
    def mut(name, fn, extra=None):
        p=sub.add_parser(name); p.add_argument("--state",required=True); p.add_argument("--case-id",required=True); p.add_argument("--expected-revision",required=True,type=int)
        if extra: extra(p)
        p.set_defaults(fn=fn)
    mut("accept-case",cmd_accept_case,lambda p:p.add_argument("--input",required=True))
    def reg(p): p.add_argument("--manifest",required=True); p.add_argument("--export",required=True)
    mut("register-module",cmd_register_module,reg)
    mut("freeze-context",cmd_freeze_context)
    mut("set-requirements",cmd_set_requirements,lambda p:p.add_argument("--input",required=True))
    def upr(p): p.add_argument("--requirement-id",required=True); p.add_argument("--status",choices=sorted(STATUSES),required=True); p.add_argument("--reason",choices=sorted(REASONS)); p.add_argument("--detail")
    mut("update-requirement",cmd_update_requirement,upr)
    mut("propose-analysis",cmd_propose_analysis,lambda p:p.add_argument("--input",required=True))
    def va(p): p.add_argument("--input",required=True); p.add_argument("--receipt",required=True)
    mut("validate-analysis",cmd_validate_analysis,va)
    def rel(p): p.add_argument("--input",required=True); p.add_argument("--receipt",required=True); p.add_argument("--output",required=True); p.add_argument("--release-receipt",required=True)
    mut("release",cmd_release,rel)
    mut("prepare-outbound",cmd_prepare_outbound,lambda p:p.add_argument("--input",required=True))
    def auth(p): p.add_argument("--outbound-id",required=True); p.add_argument("--approval",required=True); p.add_argument("--time-of-check",required=True)
    mut("authorize-outbound",cmd_authorize_outbound,auth)
    mut("authorize-retry",cmd_authorize_retry,auth)
    mut("revoke-approval",cmd_revoke_approval,lambda p:p.add_argument("--approval-id",required=True))
    def begin(p): p.add_argument("--outbound-id",required=True); p.add_argument("--time-of-check",required=True)
    mut("begin-delivery",cmd_begin_delivery,begin)
    def record(p): p.add_argument("--outbound-id",required=True); p.add_argument("--result",choices=["acknowledged","rejected","outcome_unknown"],required=True)
    mut("record-delivery",cmd_record_delivery,record)
    mut("checkpoint",cmd_checkpoint,lambda p:p.add_argument("--checkpoint",required=True))
    p=sub.add_parser("validate-checkpoint"); p.add_argument("--state",required=True); p.add_argument("--checkpoint",required=True); p.set_defaults(fn=cmd_validate_checkpoint)
    return ap

def main():
    args=parser().parse_args()
    try:
        args.fn(args); return 0
    except (ControllerError, ConformanceError, ContractError, OSError, json.JSONDecodeError) as e:
        print(json.dumps({"status":"rejected","error":str(e)},sort_keys=True),file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
