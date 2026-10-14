#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from contract_validate import ContractError, load_json, validate_obj

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / 'references' / 'conformance' / 'module-conformance-profile-0.2.0.json'
ELEMENT_CATALOG = ROOT / 'references' / 'elements' / 'element-catalog.json'
CONTRACT_VERSION = '0.2.0'
CONTROLLER_PROTOCOL_VERSION = '0.3.0'
ELEMENT_MODEL_VERSION = '0.2.0'
PROFILE_VERSION = '0.2.0'

class ConformanceError(Exception):
    pass

def load_profile():
    p = load_json(PROFILE_PATH)
    validate_obj('module-conformance-profile', p)
    return p

def owned_record_ids(export):
    fields = {
        'source_records':'source_id', 'rule_records':'rule_id', 'authority_records':'authority_id',
        'gap_records':'gap_id', 'operational_records':'record_id', 'deadline_records':'deadline_id',
        'route_records':'route_id', 'attack_angle_records':'attack_angle_id'
    }
    out=[]
    for field,key in fields.items():
        for rec in export.get(field,[]): out.append((field, rec[key]))
    return out

def usable_sources(export):
    full=set(); notes=set()
    for r in export['source_records']:
        if r.get('content_kind')=='authoritative_bundled_text' and r.get('authenticity_state')=='verified_official': full.add(r['source_id'])
        if r.get('content_kind')=='verified_source_note' and r.get('authenticity_state')=='verified_identity_version': notes.add(r['source_id'])
    return full, notes, full|notes

def require_namespace(namespace, record_id):
    if not record_id.startswith(namespace + ':'):
        raise ConformanceError(f'id_outside_namespace:{record_id}:expected_prefix={namespace}:')

def validate_pair(manifest, export, profile=None):
    validate_obj('module-manifest', manifest)
    validate_obj('module-export', export)
    profile = profile or load_profile()
    family=manifest['module_family']; policy=profile['family_policies'][family]
    for k in ('contract_version','module_family','module_id','id_namespace','jurisdiction','module_version','pack_version'):
        if manifest[k] != export[k]: raise ConformanceError(f'manifest_export_mismatch:{k}')
    if manifest['contract_version'] != CONTRACT_VERSION: raise ConformanceError('incompatible_contract')
    comp=manifest['compatibility']
    if comp['conformance_profile_version'] != PROFILE_VERSION: raise ConformanceError('incompatible_conformance_profile')
    if CONTROLLER_PROTOCOL_VERSION not in comp['controller_protocol_versions']: raise ConformanceError('incompatible_controller_protocol')
    if ELEMENT_MODEL_VERSION not in comp['element_model_versions']: raise ConformanceError('incompatible_element_model')
    if not set(manifest['supported_roles']).issubset(set(policy['allowed_roles'])): raise ConformanceError('unsupported_module_role')
    if family=='applicant_country' and not manifest.get('destination_state_profiles_available'): raise ConformanceError('applicant_country_missing_destination_profiles')
    if family in {'member_state','applicant_country'} and manifest['id_namespace'] != manifest['jurisdiction'].lower():
        raise ConformanceError(f'namespace_jurisdiction_mismatch:{manifest["id_namespace"]}:{manifest["jurisdiction"]}')
    if manifest['data_classification'] != 'reusable_non_case': raise ConformanceError('case_data_not_allowed_in_module')

    # All reusable record ids are owned by the declared namespace and unique across classes.
    seen={}
    for field,rid in owned_record_ids(export):
        require_namespace(manifest['id_namespace'],rid)
        if rid in seen: raise ConformanceError(f'duplicate_record_id:{rid}:{seen[rid]}:{field}')
        seen[rid]=field

    source_ids={r['source_id'] for r in export['source_records']}
    full,notes,usable=usable_sources(export)
    authority_ids={r['authority_id'] for r in export['authority_records']}
    gap_ids={r['gap_id'] for r in export['gap_records']}
    if set(manifest['known_gap_ids']) - gap_ids:
        raise ConformanceError('manifest_unknown_gap_ids:'+','.join(sorted(set(manifest['known_gap_ids'])-gap_ids)))
    if gap_ids - set(manifest['known_gap_ids']):
        raise ConformanceError('export_unlisted_gap_ids:'+','.join(sorted(gap_ids-set(manifest['known_gap_ids']))))

    for r in export['rule_records']:
        if r['normative_layer'] not in policy['allowed_normative_layers']: raise ConformanceError(f'forbidden_normative_layer:{r["rule_id"]}:{r["normative_layer"]}')
        refs=set(r['source_refs'])
        if refs-source_ids: raise ConformanceError(f'rule_unknown_source_refs:{r["rule_id"]}')
        if refs-usable: raise ConformanceError(f'rule_unusable_source_refs:{r["rule_id"]}')
        if r['interpretation_status']=='direct_text':
            ref=r.get('text_source_ref')
            if not ref or ref not in refs: raise ConformanceError(f'direct_text_missing_text_source_ref:{r["rule_id"]}')
            if ref not in full: raise ConformanceError(f'direct_text_requires_full_text_source:{ref}')
        if refs & notes and r['interpretation_status']!='direct_text' and not r.get('support_scope'):
            raise ConformanceError(f'note_backed_rule_requires_support_scope:{r["rule_id"]}')

    for r in export['authority_records']:
        if set(r['source_refs'])-usable: raise ConformanceError(f'authority_unusable_source_refs:{r["authority_id"]}')
    for r in export['operational_records']:
        if set(r['source_refs'])-usable: raise ConformanceError(f'operational_unusable_source_refs:{r["record_id"]}')
        if family == 'applicant_country':
            destination = r.get('destination_state')
            if destination is not None and destination not in manifest.get('destination_state_profiles_available', []):
                raise ConformanceError(f'applicant_operational_destination_outside_profile:{r["record_id"]}:{destination}')
    for r in export['deadline_records']:
        if set(r['source_refs'])-usable: raise ConformanceError(f'deadline_unusable_source_refs:{r["deadline_id"]}')
    for r in export['route_records']:
        refs=set(r['source_refs'])|set(r['legal_basis_refs'])
        if refs-usable: raise ConformanceError(f'route_unusable_source_refs:{r["route_id"]}')
        if r['authority_ref'] not in authority_ids: raise ConformanceError(f'route_unknown_authority_ref:{r["route_id"]}:{r["authority_ref"]}')

    catalog=load_json(ELEMENT_CATALOG); validate_obj('element-catalog',catalog)
    element_ids={e['element_id'] for e in catalog['elements']}
    route_ids={r['route_id'] for r in export['route_records']}
    for r in export['attack_angle_records']:
        if r['basis_layer'] not in policy['allowed_attack_layers']: raise ConformanceError(f'forbidden_attack_layer:{r["attack_angle_id"]}:{r["basis_layer"]}')
        if set(r['source_refs'])-usable: raise ConformanceError(f'attack_angle_unusable_source_refs:{r["attack_angle_id"]}')
        unknown=(set(r['prerequisite_element_ids'])|set(r['disqualifier_element_ids']))-element_ids
        if unknown: raise ConformanceError(f'attack_angle_unknown_elements:{r["attack_angle_id"]}:{sorted(unknown)}')
        unknown_auth=set(r.get('authority_refs',[]))-authority_ids
        if unknown_auth: raise ConformanceError(f'attack_angle_unknown_authority_refs:{r["attack_angle_id"]}:{sorted(unknown_auth)}')
        unknown_routes=set(r.get('route_refs',[]))-route_ids
        if unknown_routes: raise ConformanceError(f'attack_angle_unknown_route_refs:{r["attack_angle_id"]}:{sorted(unknown_routes)}')

    return {
        'status':'conformant','contract_version':CONTRACT_VERSION,'profile_version':PROFILE_VERSION,
        'module_family':family,'module_id':manifest['module_id'],'jurisdiction':manifest['jurisdiction'],
        'owned_record_count':len(seen),'usable_source_count':len(usable),'full_text_source_count':len(full),
        'supported_roles':manifest['supported_roles'],'known_gap_count':len(gap_ids)
    }

def validate_paths(manifest_path, export_path):
    return validate_pair(load_json(Path(manifest_path)), load_json(Path(export_path)))

def main():
    ap=argparse.ArgumentParser(description='Validate module conformance against inter-skill contract v0.2.0')
    ap.add_argument('manifest'); ap.add_argument('export'); args=ap.parse_args()
    try:
        out=validate_paths(args.manifest,args.export); print(json.dumps(out,sort_keys=True)); return 0
    except (ConformanceError,ContractError,OSError,json.JSONDecodeError) as e:
        print(json.dumps({'status':'rejected','error':str(e)},sort_keys=True),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
