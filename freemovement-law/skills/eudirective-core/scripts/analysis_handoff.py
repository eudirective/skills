#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import attack_angle_synthesis as c5d
import element_model as em

ENGINE_VERSION = "0.1.0"

class HandoffError(Exception):
    pass

def element_index(bundle):
    out={}
    if bundle is None:
        return out
    catalog,_,invariants=em.load_model()
    em.check_bundle(bundle,catalog,invariants)
    for item in bundle["elements"]:
        out.setdefault(item["element_id"],[]).append(item)
    return out

def single_element(idx,eid):
    vals=idx.get(eid,[])
    if not vals:
        return None
    if len(vals)!=1:
        raise HandoffError(f"multiple_values_for_singleton:{eid}")
    return vals[0]

def condition_true(item,operator,expected_present,expected):
    if operator=="present":
        return item is not None
    if operator=="absent":
        return item is None
    if item is None:
        return False
    value=item.get("value")
    if operator=="equals":
        if not expected_present: raise HandoffError("expected_value_required:equals")
        return value==expected
    if operator=="not_equals":
        if not expected_present: raise HandoffError("expected_value_required:not_equals")
        return value!=expected
    if operator=="in":
        if not expected_present or not isinstance(expected,list): raise HandoffError("expected_array_required:in")
        return value in expected
    raise HandoffError(f"unknown_operator:{operator}")

def evidence_ref_pool(angle):
    out=set()
    for k in ("supporting_finding_refs","supporting_element_refs","source_refs","rule_refs","authority_refs","route_refs","fact_source_refs"):
        out.update(str(x) for x in angle.get(k,[]))
    return out

def module_record_map(attacks):
    out={}
    for w in attacks:
        aid=w["record"]["attack_angle_id"]
        if aid in out: raise HandoffError(f"duplicate_module_attack_angle_id:{aid}")
        out[aid]=w
    return out

def verify_module_value_checks(angle, wrapped, checks, idx):
    rec=wrapped["record"]
    expected_roles={}
    for eid in rec.get("prerequisite_element_ids",[]): expected_roles[("prerequisite",eid)]=True
    for eid in rec.get("disqualifier_element_ids",[]): expected_roles[("disqualifier",eid)]=True
    seen=set()
    for chk in checks:
        key=(chk["role"],chk["element_id"])
        if key not in expected_roles:
            raise HandoffError(f"module_value_check_not_declared:{angle['attack_angle_id']}:{chk['role']}:{chk['element_id']}")
        if key in seen: raise HandoffError(f"duplicate_module_value_check:{angle['attack_angle_id']}:{chk['role']}:{chk['element_id']}")
        seen.add(key)
        item=single_element(idx,chk["element_id"])
        ok=condition_true(item,chk["operator"],"expected_value" in chk,chk.get("expected_value"))
        if chk["role"]=="prerequisite":
            if not ok: return False, f"module_prerequisite_value_not_satisfied:{chk['element_id']}"
            if item is not None and not item.get("source_ref") and item.get("provenance_kind")!="mechanical_calculation":
                return False, f"module_prerequisite_fact_provenance_missing:{chk['element_id']}"
        else:
            if ok: return False, f"module_disqualifier_value_satisfied:{chk['element_id']}"
    missing=sorted(set(expected_roles)-seen)
    if missing:
        return False, "module_value_checks_incomplete:"+",".join(f"{r}:{e}" for r,e in missing)
    return True, "module_value_checks_satisfied"

def build(case_obj,c5c_obj,c5d_obj,review,element_bundle=None,module_pairs=None):
    validate_obj("case-input",case_obj)
    if case_obj.get("privacy_classification")=="private": raise HandoffError("private_data_disabled")
    validate_obj("c5c-evidence-deadline-authority",c5c_obj)
    validate_obj("c5d-attack-angle-synthesis",c5d_obj)
    validate_obj("analysis-review-record",review)
    case_id=case_obj["case_id"]
    if c5c_obj["case_id"]!=case_id or c5d_obj["case_id"]!=case_id or review["case_id"]!=case_id:
        raise HandoffError("case_id_mismatch")
    case_digest=digest_obj(case_obj); c5c_digest=digest_obj(c5c_obj); c5d_digest=digest_obj(c5d_obj)
    if c5d_obj["bindings"]["case_sha256"]!=case_digest or c5d_obj["bindings"]["c5c_sha256"]!=c5c_digest:
        raise HandoffError("c5d_binding_mismatch")
    if review["c5d_sha256"]!=c5d_digest: raise HandoffError("review_c5d_binding_mismatch")
    if element_bundle is not None:
        idx=element_index(element_bundle); element_digest=digest_obj(element_bundle)
    else:
        idx={}; element_digest=None
    if c5d_obj["bindings"]["element_bundle_sha256"]!=element_digest:
        raise HandoffError("element_bundle_binding_mismatch")

    try:
        bindings,_,_,_,_,module_attacks=c5d.load_module_pairs(module_pairs,case_obj,c5c_obj)
    except c5d.C5dError as e:
        raise HandoffError(str(e))
    if bindings!=c5d_obj["bindings"].get("module_bindings",[]):
        raise HandoffError("c5d_module_binding_mismatch")
    module_map=module_record_map(module_attacks)

    angle_map={x["attack_angle_id"]:x for x in c5d_obj.get("attack_angles",[])}
    route_map={x["route_ref"]:x for x in c5c_obj.get("route_assessments",[])}
    eligible_angles=[]; eligible_routes=[]; rejected=[]; unresolved=[]
    seen=set()
    for rev in review["attack_angle_reviews"]:
        aid=rev["attack_angle_id"]
        if aid in seen: raise HandoffError(f"duplicate_attack_review:{aid}")
        seen.add(aid)
        angle=angle_map.get(aid)
        if angle is None: raise HandoffError(f"unknown_attack_angle_review:{aid}")
        if not set(rev["reviewed_evidence_refs"]).issubset(evidence_ref_pool(angle)):
            raise HandoffError(f"review_evidence_ref_outside_angle:{aid}")
        if rev["disposition"]=="reject":
            rejected.append(f"attack:{aid}:review_rejected")
            continue
        if c5d_obj["resolution_status"]!="ready":
            rejected.append(f"attack:{aid}:c5d_not_ready"); continue
        if angle["origin"]=="core_catalog":
            required=(angle["assessment_status"]=="supported" and angle["evidence_state"]=="sufficient_for_review" and angle["prerequisites_state"]=="satisfied" and angle["exclusion_state"]=="none_indicated" and angle["completeness_state"]=="complete_for_review")
            if not required:
                rejected.append(f"attack:{aid}:core_angle_not_promotion_grade"); continue
            if rev["module_value_checks"]:
                raise HandoffError(f"module_value_checks_on_core_angle:{aid}")
        else:
            wrapped=module_map.get(aid)
            if wrapped is None: raise HandoffError(f"module_attack_definition_missing:{aid}")
            ok,reason=verify_module_value_checks(angle,wrapped,rev["module_value_checks"],idx)
            if not ok:
                rejected.append(f"attack:{aid}:{reason}"); continue
            if not angle.get("source_refs"):
                rejected.append(f"attack:{aid}:module_angle_source_missing"); continue
        eligible_angles.append({
            "attack_angle_id":aid,"origin":angle["origin"],"issue_type":angle["issue_type"],"basis_layer":angle["basis_layer"],
            "supporting_finding_refs":angle.get("supporting_finding_refs",[]),"source_refs":angle.get("source_refs",[]),"route_refs":angle.get("route_refs",[]),
            "review_rationale":rev["rationale"]
        })

    seen_routes=set()
    for rev in review["route_reviews"]:
        rid=rev["route_ref"]
        if rid in seen_routes: raise HandoffError(f"duplicate_route_review:{rid}")
        seen_routes.add(rid)
        route=route_map.get(rid)
        if route is None: raise HandoffError(f"unknown_route_review:{rid}")
        if rev["disposition"]=="reject":
            rejected.append(f"route:{rid}:review_rejected"); continue
        if c5c_obj["resolution_status"]!="ready" or route["disposition"]!="candidate" or route["issue_match"]!="matched":
            rejected.append(f"route:{rid}:route_not_promotion_grade"); continue
        if route["target_authority_level_validation"] in {"mismatched","unknown_frozen_contract"}:
            rejected.append(f"route:{rid}:target_authority_level_not_validated"); continue
        eligible_routes.append({
            "route_ref":rid,"route_origin":route["route_origin"],"authority_ref":route["authority_ref"],"authority_level":route["authority_level"],
            "powers":route.get("powers",[]),"limits":route.get("limits",[]),"source_refs":route.get("source_refs",[]),"review_rationale":rev["rationale"]
        })

    if c5d_obj["resolution_status"]!="ready" or c5c_obj["resolution_status"]!="ready": unresolved.append("upstream_analysis_not_ready")
    status="ready" if (eligible_angles or eligible_routes) and not unresolved else ("blocked" if unresolved else "empty")
    result={
        "engine_version":ENGINE_VERSION,"case_id":case_id,
        "bindings":{"case_sha256":case_digest,"c5c_sha256":c5c_digest,"c5d_sha256":c5d_digest,"element_bundle_sha256":element_digest,"review_record_sha256":digest_obj(review),"module_bindings":bindings},
        "handoff_status":status,"legal_conclusion_status":"not_determined",
        "eligible_attack_angles":sorted(eligible_angles,key=lambda x:x["attack_angle_id"]),
        "eligible_routes":sorted(eligible_routes,key=lambda x:x["route_ref"]),
        "rejected":sorted(set(rejected)),"unresolved":sorted(set(unresolved)),
        "limitations":[
            "This handoff validates suggestion eligibility only; it does not convert a review hypothesis into a legal violation or remedy entitlement.",
            "Every promoted attack angle requires an explicit digest-bound review record; C5d candidate or supported-for-review labels alone are insufficient.",
            "Module attack angles require a complete value-level overlay for every declared prerequisite and disqualifier plus fact provenance for prerequisite values.",
            "Module routes whose target authority level remains unknown under the frozen contract are not promoted for suggestion use.",
            "The review identity is unverified_local unless a stronger host identity mechanism is independently demonstrated."
        ]
    }
    validate_obj("analysis-handoff",result)
    return result

def main():
    ap=argparse.ArgumentParser(description="Build a digest-bound C5d-to-C5e analysis handoff")
    ap.add_argument("case"); ap.add_argument("c5c"); ap.add_argument("c5d"); ap.add_argument("review")
    ap.add_argument("--elements"); ap.add_argument("--module-pair",nargs=2,action="append",metavar=("MANIFEST","EXPORT")); ap.add_argument("--output")
    a=ap.parse_args()
    try:
        r=build(load_json(Path(a.case)),load_json(Path(a.c5c)),load_json(Path(a.c5d)),load_json(Path(a.review)),load_json(Path(a.elements)) if a.elements else None,a.module_pair)
        s=json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
        if a.output: Path(a.output).write_text(s,encoding="utf-8")
        print(s,end=""); return 0
    except (HandoffError,ContractError,OSError,ValueError) as e:
        print(json.dumps({"status":"invalid","error":str(e)},sort_keys=True),file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
