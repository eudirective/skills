#!/usr/bin/env python3
"""C11a/b value-sensitive, source-bound review assessments (NOT merits rulings).

Only closed, code-pinned JSON profiles and element/case fields may be matched.
No natural-language case facts, user-controlled predicates, external I/O, or
legal-violation promotion are permitted. The frozen C3 module interface is not
changed. Missing data and adverse data are represented separately.
"""
import argparse
import json
import sys
from pathlib import Path

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import element_model
import module_conformance

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / 'references/legal-assessment/c11-rule-profiles.json'
ENGINE_VERSION = '0.1.0'
CONTRACT_EXTENSION = 'c11a-b-0.1.0'
VALID_CASE_FIELDS = {'procedure_type', 'procedure_stage', 'document_issuing_country'}

class AssessmentError(Exception):
    pass


def read_field(case, idx, field):
    """Explicitly allowlisted structured facts, never natural-language facts."""
    prefix, _, key = field.partition(':')
    if prefix == 'case':
        if key not in VALID_CASE_FIELDS:
            raise AssessmentError('unapproved_case_field:'+key)
        if key == 'document_issuing_country':
            return case['geography'].get(key), None
        return case.get(key), None
    if prefix == 'element':
        if key not in idx:
            return None, None
        return idx[key]['value'], idx[key].get('source_ref')
    raise AssessmentError('unapproved_field_prefix:'+field)


def source_inventory(source_pack, module_pairs):
    sources = {r['source_id']: {'origin':'core', 'assurance':
               ('bundled_in_core' if r['source_id']=='eu:62024cj0477'
                else 'catalogue_metadata_not_reverified_here'), 'url':r['canonical_url']}
               for r in source_pack['sources']}
    for manifest_path, export_path in module_pairs:
        m = load_json(Path(manifest_path)); ex = load_json(Path(export_path))
        module_conformance.validate_pair(m, ex)
        for r in ex.get('source_records', []):
            sid = r['source_id']
            if sid in sources:
                raise AssessmentError('duplicate_source_id:'+sid)
            sources[sid] = {'origin':'country_module', 'assurance':'official_source_summary_note_only', 'url':r['locator']}
    return sources


def check_profile(profile, attack_ids, sources, element_ids):
    if profile.get('profile_version')!='0.1.0' or profile.get('status')!='synthetic_review_only':
        raise AssessmentError('profile_version_or_status_invalid')
    seen=set()
    for row in profile['rules']:
        rid = row['id']
        if rid in seen:raise AssessmentError('duplicate_rule:'+rid)
        seen.add(rid)
        if row['kind']=='attack' and row['attack_angle_id'] not in attack_ids:
            # A pinned profile may target another module which is absent in this case.
            # No assessment is emitted for an absent attack identifier.
            continue
        elif row['kind']=='topic' and row['attack_angle_id'] is not None:
            raise AssessmentError('topic_attack_binding_forbidden')
        if not row.get('procedure_types'):
            raise AssessmentError('unscoped_rule:'+rid)
        if not row.get('source_citations'):
            raise AssessmentError('uncited_rule:'+rid)
        for src in row['source_citations']:
            if not src.get('source_id') or not src.get('pinpoint_hint'):
                raise AssessmentError('invalid_rule_source_record:'+rid)
        for test in row['tests']:
            prefix, _, key = test['field'].partition(':')
            if prefix=='case' and key not in VALID_CASE_FIELDS:
                raise AssessmentError('unapproved_case_field:'+key)
            if prefix=='element' and key not in element_ids:
                raise AssessmentError('unknown_element:'+key)
            if prefix not in ('case', 'element'):
                raise AssessmentError('unapproved_field_prefix:'+prefix)
            if not test['allowed_values'] or any(type(v) not in (bool, str, int) for v in test['allowed_values']):
                raise AssessmentError('invalid_allowed_values:'+rid)


def build(case, elements, c5d, source_pack, module_pairs=(), profile=None):
    validate_obj('case-input',case)
    if case['privacy_classification']!='synthetic':
        raise AssessmentError('private_data_disabled')
    validate_obj('c5d-attack-angle-synthesis', c5d)
    validate_obj('core-source-pack',source_pack)
    if digest_obj(case)!=c5d['bindings']['case_sha256']:
        raise AssessmentError('unbound_c5d_case')
    if elements is not None:
        validate_obj('element-instance-bundle',elements)
        element_model.check_bundle(elements, *element_model.load_model()[::2])
    edigest=digest_obj(elements) if elements is not None else None
    if edigest!=c5d['bindings']['element_bundle_sha256']:
        raise AssessmentError('unbound_c5d_elements')
    if digest_obj(source_pack)!=c5d['bindings']['source_pack_sha256']:
        raise AssessmentError('unbound_c5d_source_pack')
    idx={}
    for item in (elements or {}).get('elements',[]):
        if item['element_id'] in idx:
            raise AssessmentError('duplicate_structured_element:'+item['element_id'])
        idx[item['element_id']]=item
    sources=source_inventory(source_pack,module_pairs)
    bindings=[]
    for mpath,epath in module_pairs:
        m=load_json(Path(mpath));ex=load_json(Path(epath))
        bindings.append({'module_id':ex['module_id'], 'module_family':ex['module_family'], 'jurisdiction':ex['jurisdiction'],
                         'manifest_sha256':digest_obj(m), 'export_sha256':digest_obj(ex)})
    bindings=sorted(bindings,key=lambda x:x['module_id'])
    if bindings!=c5d['bindings']['module_bindings']:
        raise AssessmentError('c11_module_bindings_mismatch')
    if profile is None:profile=load_json(PROFILE_PATH)
    available_ids={a['attack_angle_id'] for a in c5d['attack_angles']}
    catalog_ids=set(available_ids)
    for _,export_path in module_pairs:
        ex=load_json(Path(export_path))
        catalog_ids.update(x['attack_angle_id'] for x in ex.get('attack_angle_records',[]))
    core_catalog=load_json(ROOT/'references/attack-angles/core-attack-angle-catalog.json')
    catalog_ids.update(x['attack_angle_id'] for x in core_catalog['patterns'])
    check_profile(profile,catalog_ids,sources,{e['element_id'] for e in element_model.load_model()[0]['elements']})
    by_attack={a['attack_angle_id']:a for a in c5d['attack_angles']}
    assessments=[]; covered=set()
    for rule in profile['rules']:
        aid=rule['attack_angle_id']
        if rule['kind']=='attack' and aid not in by_attack:
            continue
        if rule['kind']=='attack':covered.add(aid)
        upstream=by_attack.get(aid)
        missing_sources=[s['source_id'] for s in rule['source_citations'] if s['source_id'] not in sources]
        source_citations=[{'source_id':s['source_id'], 'pinpoint_hint':s['pinpoint_hint'],
                           'provenance_level':sources[s['source_id']]['assurance'],
                           'url':sources[s['source_id']]['url']}
                          for s in rule['source_citations'] if s['source_id'] in sources]
        facts=[]; contra=[]; missing=[]; tests=[]
        in_scope=case.get('procedure_type') in rule['procedure_types']
        if not in_scope:
            status='not_applicable'
        else:
            for t in rule['tests']:
                value,ref=read_field(case,idx,t['field'])
                if value is None:
                    outcome='missing'; missing.append('Required structured field: '+t['field'])
                elif value in t['allowed_values']:
                    outcome='matched';facts.append({'field':t['field'],'value':value,'fact_source_ref':ref})
                    if t['field'].startswith('element:') and ref is None:
                        missing.append('Independent factual provenance for '+t['field'])
                else:
                    outcome='contrary';contra.append({'field':t['field'],'value':value,'fact_source_ref':ref,
                        'expected_values':t['allowed_values']})
                tests.append({'field':t['field'], 'test_result':outcome,
                              'expected_values':t['allowed_values']})
            missing.extend('Missing bound source: '+sid for sid in missing_sources)
            if contra:
                status='contradicted'
            elif missing or rule['missing_structured_questions']:
                status='unresolved'
            else:
                status='supported_for_review'
            # The C3 module records lack value semantics and may be code-pinned
            # as non-automatable. Never bypass their upstream block.
            if upstream and upstream['assessment_status'] in ('blocked','insufficient_evidence') and status=='supported_for_review':
                status='unresolved'
                missing.append('Upstream C5d record is '+upstream['assessment_status']+'; cannot upgrade it')
            if c5d['resolution_status']=='blocked' and status=='supported_for_review':
                status='unresolved';missing.append('Upstream C5d stage blocked')
        if in_scope:
            missing.extend(rule['missing_structured_questions'])
        rec={
            'assessment_id':rule['id'], 'kind':rule['kind'],'attack_angle_id':aid,
            'label':rule['label'], 'status':status,
            'legal_violation_status':'not_determined',
            'upstream_c5d_status':upstream['assessment_status'] if upstream else None,
            'procedure_type':case.get('procedure_type'),
            'predicate_tests':tests, 'material_facts':facts, 'contrary_facts':contra,
            'missing_facts':sorted(set(missing)),
            'exceptions_to_review':rule['exceptions_to_review'] if in_scope else [],
            'alternative_evidence_to_review':rule['contrary_evidence_to_review'] if in_scope else [],
            'source_citations':source_citations if in_scope else [],
            'limitations':rule['limitations']+["C11 evaluates structured facts only. Legal applicability, exceptions and violations remain unadjudicated."],
        }
        assessments.append(rec)
    # Explicitly represent undeveloped attack angles rather than pretending a
    # country/module candidate is legally assessed.
    for aid in sorted(set(by_attack)-covered):
        a=by_attack[aid]
        assessments.append({'assessment_id':'c11:unprofiled:'+aid, 'kind':'attack','attack_angle_id':aid,
                            'label':a['label'],'status':'unresolved','legal_violation_status':'not_determined',
                            'upstream_c5d_status':a['assessment_status'],'procedure_type':case.get('procedure_type'),
                            'predicate_tests':[], 'material_facts':[], 'contrary_facts':[],
                            'missing_facts':['No C11 fact-value rule profile exists for this angle.'],
                            'exceptions_to_review':[], 'alternative_evidence_to_review':[],
                            'source_citations':[], 'limitations':['C5d candidate cannot be treated as assessed in C11.']})
    assessments.sort(key=lambda a:a['assessment_id'])
    unresolved=[a['assessment_id']+':'+a['status']+':'+v for a in assessments
                if a['status']=='unresolved' for v in a['missing_facts']]
    out={
      'engine_version':ENGINE_VERSION,'contract_extension':CONTRACT_EXTENSION,
      'case_id':case['case_id'],
      'bindings':{'case_sha256':digest_obj(case),'elements_sha256':edigest,
                  'c5d_sha256':digest_obj(c5d),'source_pack_sha256':digest_obj(source_pack),
                  'profiles_sha256':digest_obj(profile),'module_bindings':bindings},
      'conclusion':'not_determined', 'assessments':assessments,
      'unresolved':sorted(set(unresolved)),
      'limitations':[
          'C11a/b is a deterministic, value-sensitive synthetic review layer; not independently graded merits or legal advice.',
          'No natural-language facts are parsed, no authorities contacted, no action is executed.',
          'Module source notes are not complete current national law; pinpoint hints require independent confirmation.',
          'No result can establish a legal violation, remedy entitlement, deadline or final applicability.',
          'Absence of contrary evidence in input does not prove the absence of exceptions.',
          'Only C11 rule profiles bundled with and pinned by the core are used; the C3 contract remains frozen.'
      ]}
    validate_obj('c11-legal-assessment',out)
    return out


def render(out):
    lines=['# C11a/b value-sensitive legal-assessment review', '',
           '**Synthetic only. This report cannot establish any infringement.**', '',
           'Case: `'+out['case_id']+'`', 'Outcome: `not_determined`', '',
           '## Assessments', '']
    for a in out['assessments']:
        lines.extend(['### '+a['assessment_id'], '', '- Topic: '+a['label'],
                      '- Predicate status: `'+a['status']+'`; legal violation: `not_determined`',
                      '- Upstream C5d: `'+str(a['upstream_c5d_status'])+'`', ''])
        if a['material_facts']:
            lines.append('Material structured facts:')
            for x in a['material_facts']:
                lines.append('- `'+x['field']+'` = `'+str(x['value'])+'`; evidence reference: `'+str(x['fact_source_ref'])+'`')
        if a['contrary_facts']:
            lines.append('Contradictory structured facts:')
            for x in a['contrary_facts']:
                lines.append('- `'+x['field']+'` = `'+str(x['value'])+'`; expected one of '+repr(x['expected_values']))
        if a['missing_facts']:
            lines.append('Missing facts:')
            lines.extend('- '+x for x in a['missing_facts'])
        if a['exceptions_to_review']:
            lines.append('Exceptions/applicability to review:')
            lines.extend('- '+x for x in a['exceptions_to_review'])
        if a['alternative_evidence_to_review']:
            lines.append('Contrary/alternative evidence to review:')
            lines.extend('- '+x for x in a['alternative_evidence_to_review'])
        if a['source_citations']:
            lines.append('Source and pinpoint **review hints**, not reverified quotations:')
            lines.extend('- `'+x['source_id']+'` ('+x['provenance_level']+'): '+x['pinpoint_hint'] for x in a['source_citations'])
        lines.append('')
    lines.extend(['## Bound source and profile hashes', '',
                  '- C5d digest: `'+out['bindings']['c5d_sha256']+'`',
                  '- Profile digest: `'+out['bindings']['profiles_sha256']+'`',
                  '', 'Every conclusion remains not_determined.'])
    return ('\n'.join(lines).rstrip()+'\n').encode('utf-8')


def main():
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--elements',required=True)
    p.add_argument('--c5d',required=True);p.add_argument('--source-pack',required=True)
    p.add_argument('--module-pair',action='append',nargs=2,default=[]);p.add_argument('--output',required=True)
    args=p.parse_args()
    try:
        value=build(load_json(Path(args.case)),load_json(Path(args.elements)),load_json(Path(args.c5d)),
                    load_json(Path(args.source_pack)),args.module_pair)
        Path(args.output).write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps({'status':'c11_assessed_synthetic','sha256':digest_obj(value),'count':len(value['assessments'])}))
        return 0
    except (AssessmentError,ContractError,OSError,ValueError,KeyError,TypeError,module_conformance.ConformanceError) as exc:
        print(json.dumps({'status':'invalid','error':str(exc)}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
