#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
import sys

from contract_validate import ContractError, load_json, validate_obj, digest_obj

from source_library_paths import compatibility_root

ROOT=Path(__file__).resolve().parents[1]
ELEMENT_DIR=ROOT/'references'/'elements'

class ElementModelError(Exception):
    pass

def load_model():
    catalog=load_json(ELEMENT_DIR/'element-catalog.json'); validate_obj('element-catalog',catalog)
    interactions=load_json(ELEMENT_DIR/'interaction-rules.json'); validate_obj('interaction-rules',interactions)
    invariants=load_json(ELEMENT_DIR/'invariant-catalog.json'); validate_obj('invariant-catalog',invariants)
    support=load_json(ELEMENT_DIR/'source-support-map.json'); validate_obj('source-support-map',support)
    support_requirements=load_json(ELEMENT_DIR/'source-support-requirements.json'); validate_obj('source-support-requirements',support_requirements)
    validate_model(catalog,interactions,invariants,support,support_requirements)
    return catalog,interactions,invariants

def validate_model(catalog,interactions,invariants,support=None,support_requirements=None):
    fam_ids=[x['family_id'] for x in catalog['families']]
    if len(fam_ids)!=len(set(fam_ids)):
        raise ElementModelError('duplicate_family_id')
    elements={}
    for e in catalog['elements']:
        eid=e['element_id']
        if eid in elements:
            raise ElementModelError(f'duplicate_element_id:{eid}')
        if e['family'] not in fam_ids:
            raise ElementModelError(f'unknown_family:{eid}:{e["family"]}')
        elements[eid]=e
    invs={}
    known_checks=set(CHECKS)
    for inv in invariants['invariants']:
        iid=inv['invariant_id']
        if iid in invs:
            raise ElementModelError(f'duplicate_invariant_id:{iid}')
        for eid in inv['related_elements']:
            if eid not in elements:
                raise ElementModelError(f'invariant_unknown_element:{iid}:{eid}')
        if inv['enforcement']=='mechanical':
            if not inv['check_name'] or inv['check_name'] not in known_checks:
                raise ElementModelError(f'unknown_mechanical_check:{iid}:{inv["check_name"]}')
        invs[iid]=inv
    seen_rules=set()
    for rule in interactions['rules']:
        rid=rule['rule_id']
        if rid in seen_rules:
            raise ElementModelError(f'duplicate_interaction_rule_id:{rid}')
        seen_rules.add(rid)
        for eid in rule['inputs']:
            if eid not in elements:
                raise ElementModelError(f'interaction_unknown_element:{rid}:{eid}')
        if rule['invariant_id'] is not None and rule['invariant_id'] not in invs:
            raise ElementModelError(f'interaction_unknown_invariant:{rid}:{rule["invariant_id"]}')
        if rule['machine_checkable'] and rule['invariant_id'] is None:
            raise ElementModelError(f'machine_rule_without_invariant:{rid}')
    if support is not None:
        known_sources=set()
        source_manifest=compatibility_root()/'core-source-pack-manifest-0.6.1.json'
        if source_manifest.is_file():
            sm=load_json(source_manifest); known_sources={x['source_id'] for x in sm.get('sources',[])}
        seen_support=set()
        for rec in support.get('records',[]):
            sid=rec['source_id']
            if sid in seen_support: raise ElementModelError(f'duplicate_source_support:{sid}')
            seen_support.add(sid)
            if known_sources and sid not in known_sources: raise ElementModelError(f'unknown_source_support_source:{sid}')
            for target in rec['targets']:
                tt,tid=target['target_type'],target['target_id']
                if tt=='element' and tid not in elements: raise ElementModelError(f'source_support_unknown_element:{sid}:{tid}')
                if tt=='interaction' and tid not in seen_rules: raise ElementModelError(f'source_support_unknown_interaction:{sid}:{tid}')
                if tt=='invariant' and tid not in invs: raise ElementModelError(f'source_support_unknown_invariant:{sid}:{tid}')
        if known_sources and seen_support != known_sources:
            missing=sorted(known_sources-seen_support); extra=sorted(seen_support-known_sources)
            raise ElementModelError(f'source_support_coverage_mismatch:missing={missing}:extra={extra}')
        if support_requirements is not None:
            if support_requirements.get('model_version') != catalog.get('model_version'):
                raise ElementModelError('source_support_requirements_model_version_mismatch')
            if support_requirements.get('source_pack_version') != support.get('source_pack_version'):
                raise ElementModelError('source_support_requirements_pack_version_mismatch')
            coverage={}
            for rec in support.get('records',[]):
                sid=rec['source_id']
                for target in rec['targets']:
                    key=(target['target_type'],target['target_id'])
                    slot=coverage.setdefault(key,{'roles':set(),'sources':set()})
                    slot['roles'].add(target['support_role']); slot['sources'].add(sid)
            seen_req=set()
            for req in support_requirements.get('required_targets',[]):
                key=(req['target_type'],req['target_id'])
                if key in seen_req:
                    raise ElementModelError(f'duplicate_source_support_requirement:{key[0]}:{key[1]}')
                seen_req.add(key)
                tt,tid=key
                if tt=='element' and tid not in elements: raise ElementModelError(f'source_support_requirement_unknown_element:{tid}')
                if tt=='interaction' and tid not in seen_rules: raise ElementModelError(f'source_support_requirement_unknown_interaction:{tid}')
                if tt=='invariant' and tid not in invs: raise ElementModelError(f'source_support_requirement_unknown_invariant:{tid}')
                got=coverage.get(key)
                if not got:
                    raise ElementModelError(f'source_support_required_target_missing:{tt}:{tid}')
                missing_roles=set(req['required_roles'])-got['roles']
                if missing_roles:
                    raise ElementModelError(f'source_support_required_role_missing:{tt}:{tid}:{sorted(missing_roles)}')
                if len(got['sources']) < req['min_source_count']:
                    raise ElementModelError(f'source_support_required_source_count:{tt}:{tid}:{len(got["sources"])}<{req["min_source_count"]}')
    return True

def scalar_index(bundle):
    out={}
    for item in bundle['elements']:
        out.setdefault(item['element_id'],[]).append(item['value'])
    return out

def entries_index(bundle):
    out={}
    for item in bundle['elements']:
        out.setdefault(item['element_id'],[]).append(item)
    return out

def first(index,key,default=None):
    vals=index.get(key,[])
    return vals[0] if vals else default

def has(index,key):
    return bool(index.get(key))

def ensure_value_type(e,value):
    t=e['value_type']
    ok=False
    if t in ('string','status','jurisdiction','date','datetime'):
        ok=isinstance(value,str)
    elif t=='boolean': ok=isinstance(value,bool)
    elif t=='integer': ok=isinstance(value,int) and not isinstance(value,bool)
    elif t=='number': ok=isinstance(value,(int,float)) and not isinstance(value,bool)
    elif t=='string_array': ok=isinstance(value,list) and all(isinstance(x,str) for x in value)
    elif t=='object': ok=isinstance(value,dict)
    if not ok:
        raise ElementModelError(f'value_type_mismatch:{e["element_id"]}:expected_{t}')
    if t=='jurisdiction' and (len(value)<2 or len(value)>80):
        raise ElementModelError(f'invalid_jurisdiction:{e["element_id"]}')
    if t=='date' and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        raise ElementModelError(f'invalid_date:{e["element_id"]}')

def check_supplier_allowed(bundle,catalog,idx,entries):
    defs={e['element_id']:e for e in catalog['elements']}
    for item in bundle['elements']:
        eid=item['element_id']
        if eid not in defs:
            raise ElementModelError(f'unknown_element:{eid}')
        d=defs[eid]
        if item['supplied_by'] not in d['allowed_suppliers']:
            raise ElementModelError(f'supplier_not_allowed:{eid}:{item["supplied_by"]}')
        ensure_value_type(d,item['value'])
        if d['provenance_required'] and not item.get('provenance_kind'):
            raise ElementModelError(f'provenance_required:{eid}')
        if item['provenance_kind'] in {'document','authority_statement','public_source','module_export'} and not item.get('source_ref'):
            # Synthetic fixtures may use module_export without an external URI, but must still name a source/module ref.
            raise ElementModelError(f'source_ref_required:{eid}')
    for eid,d in defs.items():
        count=len(entries.get(eid,[]))
        if d['cardinality'] in ('one','zero_or_one') and count>1:
            raise ElementModelError(f'cardinality_exceeded:{eid}')

def check_deadline_requires_trigger_source(bundle,catalog,idx,entries):
    if has(idx,'time.calculated_deadline'):
        if not has(idx,'time.deadline_trigger_ref'):
            raise ElementModelError('deadline_missing_trigger')
        if not has(idx,'time.deadline_rule_ref'):
            raise ElementModelError('deadline_missing_rule')

def check_escalation_requires_competence(bundle,catalog,idx,entries):
    if has(idx,'strategy.escalation_authority_ref'):
        if not has(idx,'authority.jurisdiction'):
            raise ElementModelError('escalation_authority_missing_jurisdiction')
        if not has(idx,'authority.competence'):
            raise ElementModelError('escalation_authority_missing_competence')

def check_incomplete_not_negative(bundle,catalog,idx,entries):
    blocked={'not_checked','blocked','insufficient_evidence','source_missing','source_stale','module_absent','optional_context_absent','unresolved_conflict','unsupported_automated_evaluation','cannot_assess'}
    if first(idx,'conclusion.no_problem') is True and any(v in blocked for v in idx.get('completeness.status',[])):
        raise ElementModelError('incomplete_state_cannot_support_no_problem')

def check_stale_source_blocks_current(bundle,catalog,idx,entries):
    if 'stale' in idx.get('source.freshness',[]) and first(idx,'conclusion.current_law_supported') is True:
        raise ElementModelError('stale_source_cannot_support_current_law')

def check_national_rule_source_linked(bundle,catalog,idx,entries):
    if has(idx,'rule.national_rule_id') and not has(idx,'rule.source_ref'):
        raise ElementModelError('national_rule_missing_source_ref')

def check_unsupported_operator_explicit(bundle,catalog,idx,entries):
    if first(idx,'rule.operator_supported') is False:
        if 'unsupported_automated_evaluation' not in idx.get('completeness.status',[]):
            raise ElementModelError('unsupported_operator_not_recorded')

def check_outbound_requires_purpose(bundle,catalog,idx,entries):
    if first(idx,'privacy_control.outbound_eligibility') is True and not has(idx,'privacy_control.purpose'):
        raise ElementModelError('outbound_eligibility_missing_purpose')

def check_approval_recipient_binding(bundle,catalog,idx,entries):
    bound=first(idx,'privacy_control.approval_bound_recipient'); current=first(idx,'privacy_control.current_recipient')
    if bound is not None and current is not None and bound != current and first(idx,'privacy_control.approval_valid') is True:
        raise ElementModelError('changed_recipient_requires_approval_invalidation')

def check_case_data_not_module_asset(bundle,catalog,idx,entries):
    if first(idx,'asset.kind')=='module_asset' and first(idx,'asset.distributable') is True:
        if any(x['supplied_by']=='case_workspace' for x in bundle['elements']):
            raise ElementModelError('case_workspace_data_in_distributable_module_asset')

def check_optional_local_gap_scoped(bundle,catalog,idx,entries):
    # Review-oriented invariant. Mechanical check only catches an explicit global-failure encoding.
    if first(idx,'module.optional_local_available') is False and first(idx,'completeness.scope')=='global_failure':
        raise ElementModelError('optional_local_gap_encoded_as_global_failure')

def check_principle_requires_source(bundle,catalog,idx,entries):
    status=first(idx,'legal_principle.applicability_status')
    if has(idx,'legal_principle.id') or status in {'applicable','applies','material','supports','limits'}:
        if not has(idx,'legal_principle.source_ref'):
            raise ElementModelError('legal_principle_missing_source_ref')

def check_charter_requires_eu_scope(bundle,catalog,idx,entries):
    status=first(idx,'legal_regime.charter')
    if status in {'applicable','applies','engaged'} and first(idx,'legal_regime.eu_law_scope_established') is not True:
        raise ElementModelError('charter_applicability_missing_eu_scope')

def check_proof_restriction_requires_source(bundle,catalog,idx,entries):
    status=first(idx,'evidence.proof_restriction_status')
    if status in {'required','asserted','established','applies','restricted','closed_list'} and not has(idx,'evidence.proof_restriction_source_ref'):
        raise ElementModelError('proof_restriction_missing_source_ref')

def check_supported_attack_angle_requires_support(bundle,catalog,idx,entries):
    status=first(idx,'attack_angle.assessment_status')
    if status in {'supported','established','prima_facie_supported'}:
        if not has(idx,'attack_angle.source_ref'):
            raise ElementModelError('supported_attack_angle_missing_source_ref')
        ev=first(idx,'attack_angle.evidence_state')
        if ev is None or ev in {'missing','insufficient','conflicting_unresolved','not_checked'}:
            raise ElementModelError('supported_attack_angle_missing_evidence')

def check_verified_note_not_exact_wording(bundle,catalog,idx,entries):
    if first(idx,'source.representation_kind')=='verified_source_note':
        if first(idx,'conclusion.exact_wording_supported') is True:
            raise ElementModelError('verified_source_note_cannot_support_exact_wording')
        if first(idx,'conclusion.pinpoint_supported') is True:
            raise ElementModelError('verified_source_note_cannot_support_pinpoint')

def check_duration_requires_typed_event(bundle,catalog,idx,entries):
    if has(idx,'time.duration_days') and (not has(idx,'time.event_type') or not has(idx,'time.event_date')):
        raise ElementModelError('duration_missing_typed_event')

CHECKS={
 'supplier_allowed':check_supplier_allowed,
 'deadline_requires_trigger_source':check_deadline_requires_trigger_source,
 'escalation_requires_competence':check_escalation_requires_competence,
 'incomplete_not_negative':check_incomplete_not_negative,
 'stale_source_blocks_current':check_stale_source_blocks_current,
 'national_rule_source_linked':check_national_rule_source_linked,
 'unsupported_operator_explicit':check_unsupported_operator_explicit,
 'outbound_requires_purpose':check_outbound_requires_purpose,
 'approval_recipient_binding':check_approval_recipient_binding,
 'case_data_not_module_asset':check_case_data_not_module_asset,
 'optional_local_gap_scoped':check_optional_local_gap_scoped,
 'principle_requires_source':check_principle_requires_source,
 'charter_requires_eu_scope':check_charter_requires_eu_scope,
 'proof_restriction_requires_source':check_proof_restriction_requires_source,
 'supported_attack_angle_requires_support':check_supported_attack_angle_requires_support,
 'verified_note_not_exact_wording':check_verified_note_not_exact_wording,
 'duration_requires_typed_event':check_duration_requires_typed_event,
}

def check_bundle(bundle,catalog,invariants):
    validate_obj('element-instance-bundle',bundle)
    idx=scalar_index(bundle); entries=entries_index(bundle)
    # universal catalog/supplier/type check first
    check_supplier_allowed(bundle,catalog,idx,entries)
    executed=['supplier_allowed']
    review_required=[]
    for inv in invariants['invariants']:
        if inv['enforcement']=='mechanical' and inv['check_name']!='supplier_allowed':
            CHECKS[inv['check_name']](bundle,catalog,idx,entries); executed.append(inv['check_name'])
        elif inv['enforcement']=='review':
            review_required.append(inv['invariant_id'])
    return {'status':'valid','bundle_id':bundle['bundle_id'],'sha256':digest_obj(bundle),'mechanical_checks':executed,'review_required':review_required}

def main():
    ap=argparse.ArgumentParser(description='Validate the eudirective-core element model and atomic element bundles')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('validate-model')
    p=sub.add_parser('check'); p.add_argument('path')
    args=ap.parse_args()
    try:
        catalog,interactions,invariants=load_model()
        if args.cmd=='validate-model':
            print(json.dumps({'status':'valid','model_version':catalog['model_version'],'families':len(catalog['families']),'elements':len(catalog['elements']),'interactions':len(interactions['rules']),'invariants':len(invariants['invariants']),'catalog_sha256':digest_obj(catalog)},sort_keys=True))
            return 0
        bundle=load_json(Path(args.path))
        print(json.dumps(check_bundle(bundle,catalog,invariants),sort_keys=True))
        return 0
    except (ContractError,ElementModelError,OSError) as e:
        print(json.dumps({'status':'invalid','error':str(e)},sort_keys=True),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
