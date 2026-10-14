#!/usr/bin/env python3
"""C12 synthetic-only, source-bound rule resolution (never legal adjudication).

Core owns evaluation logic and EU rules; national rules arrive as typed C3-bound
country-owned sidecars. A document reference alone is never evidentiary support:
synthetic source bytes, digest, ledger statement, and element value must agree.
This deliberately does NOT authenticate real-world documents or interpret prose.
"""
import hashlib
from datetime import date
from pathlib import Path, PurePosixPath

from contract_validate import digest_obj, load_json, validate_obj, ContractError
import element_model
import module_conformance

ROOT=Path(__file__).resolve().parents[1]
EU_RULES=ROOT/'references/legal-assessment/c12-eu-rules.json'
DOCUMENTS=ROOT/'references/legal-assessment/c12-document-index.json'
VERSION='0.2.0'
CASE_FACTS={'procedure_type','procedure_stage','document_issuing_country'}

class C12Error(Exception):pass


def read_case(case, key):
    if key not in CASE_FACTS:raise C12Error('unknown_case_field:'+key)
    return case['geography'].get(key) if key=='document_issuing_country' else case.get(key)


def load_document_registry():
    index=load_json(DOCUMENTS)
    if index.get('index_version')!='0.1.0':raise C12Error('invalid_document_registry_version')
    result={}
    for record in index.get('documents',[]):
        ref=record['document_ref']; rel=record['relative_path']
        if ref in result:raise C12Error('duplicate_document_registry_ref')
        path=PurePosixPath(rel)
        if path.is_absolute() or '..' in path.parts or not str(path).startswith('references/fixtures/c12/documents/'):
            raise C12Error('unsafe_document_registry_path')
        f=ROOT.joinpath(*path.parts)
        if not f.is_file() or f.is_symlink() or not f.resolve().is_relative_to(ROOT.resolve()):
            raise C12Error('unavailable_pinned_document:'+ref)
        if hashlib.sha256(f.read_bytes()).hexdigest()!=record['sha256']:
            raise C12Error('changed_pinned_document_bytes:'+ref)
        doc=load_json(f)
        if doc.get('document_ref')!=ref or doc.get('synthetic_only') is not True:
            raise C12Error('document_registry_identity_mismatch:'+ref)
        result[ref]={'sha256':record['sha256'],'assertions':doc['assertions'],'case_fixture':doc.get('case_fixture')}
    return result


def source_lookup(source_pack,pairs):
    sources={x['source_id']:{'origin':'eu_core', 'assurance':
       'bundled_text_integrity_checked_not_completeness' if any(y['kind']=='bundled_text' for y in x['representations']) else 'curated_source_note_only'}
       for x in source_pack['sources']}
    modules={}
    for mp,ep in pairs:
        m=load_json(Path(mp));e=load_json(Path(ep))
        module_conformance.validate_pair(m,e)
        if e['module_id'] in modules:raise C12Error('duplicate_c12_module')
        modules[e['module_id']]=e
        for x in e.get('source_records',[]):
            sid=x['source_id']
            if sid in sources:raise C12Error('duplicate_c12_source:'+sid)
            sources[sid]={'origin':e['module_id'],'assurance':'country_source_summary_only'}
    return sources,modules


def check_rule(rule,owner,source_lookup_,source_owner):
    keys={'rule_id','label','procedure_types','attack_angle_id','conditions','exception_questions','source_citations','limitations'}
    if set(rule) not in (keys,keys|{'activation'}):raise C12Error('malformed_rule_keys:'+rule.get('rule_id','?'))
    rid=rule['rule_id']
    if not rule['procedure_types'] or not rule['conditions'] or not rule['source_citations']:
        raise C12Error('incomplete_rule:'+rid)
    if 'activation' in rule and rule['activation']['operator']!='one_of':
        raise C12Error('activation_requires_one_of:'+rid)
    if len(rule['conditions'])>30:raise C12Error('too_many_conditions')
    for cond in rule['conditions']+([rule['activation']] if 'activation' in rule else []):
        k=cond['fact_key']; operator=cond['operator'];vals=cond['expected_values']
        prefix,_,suffix=k.partition(':')
        if prefix=='case' and suffix not in CASE_FACTS:raise C12Error('illegal_case_key:'+k)
        if prefix=='element' and suffix not in element_model.ELEMENT_IDS_CACHE:
            raise C12Error('illegal_element_key:'+k)
        if prefix=='fact' and (not suffix or len(suffix)>100 or any(not(c.islower() or c.isdigit() or c=='_') for c in suffix)):
            raise C12Error('illegal_fact_key:'+k)
        if prefix not in ('case','element','fact'):raise C12Error('illegal_fact_prefix:'+k)
        if operator not in ('one_of','date') or (operator=='one_of' and not vals) or (operator=='date' and vals):
            raise C12Error('illegal_predicate_operator:'+rid)
        if len(vals)>60 or any(type(v) not in (str,int,bool) for v in vals):raise C12Error('illegal_predicate_values')
    for citation in rule['source_citations']:
        sid=citation['source_id']
        if sid not in source_lookup_:
            if owner=='eu_core' and sid.startswith('eu:'):continue
            raise C12Error('rule_source_missing:'+rid+':'+sid)
        if owner=='eu_core' and source_lookup_[sid]['origin']!='eu_core':
            raise C12Error('eu_rule_claims_national_source:'+rid)
        if owner!='eu_core' and source_lookup_[sid]['origin']!=source_owner:
            raise C12Error('country_rule_claims_other_module_source:'+rid)
        if not citation['pinpoint_hint']:raise C12Error('missing_pinpoint_hint:'+rid)


def verify_evidence_ledger(case, elements, ledger, documents):
    if ledger is None:return {},[],None
    validate_obj('c12-fact-ledger',ledger)
    if case['privacy_classification']!='synthetic' or ledger['case_sha256']!=digest_obj(case) or ledger['elements_sha256']!=digest_obj(elements):
        raise C12Error('unbound_case_fact_ledger')
    case_label=case['case_id'].split('-')[-1]
    records={};unverified=[]
    for record in ledger['records']:
        ref=record['document_ref'];key=record['fact_key'];val=record['value']
        doc=documents.get(ref)
        if not doc or (doc['case_fixture'] and doc['case_fixture']!=case_label):
            unverified.append({'fact_key':key,'document_ref':ref,'reason':'missing_or_wrong_case_document'})
            continue
        if not any(x.get('fact_key')==key and type(x.get('value'))==type(val) and x.get('value')==val for x in doc['assertions']):
            unverified.append({'fact_key':key,'document_ref':ref,'reason':'claim_not_in_document_bytes'})
            continue
        records.setdefault(key,[]).append({'value':val,'document_ref':ref,'sha256':doc['sha256']})
    return records,unverified,digest_obj(ledger)


def value_for(cond,case,idx,records,failed):
    key=cond['fact_key'];prefix,_,suffix=key.partition(':')
    if prefix=='case':
        return read_case(case,suffix),'case_structural_metadata',None
    if prefix=='element':
        element=idx.get(suffix)
        if element is None:return None,'missing_element',None
        actual=element['value'];ref=element.get('source_ref')
        proof=[x for x in records.get(key,[]) if x['document_ref']==ref and type(x['value'])==type(actual) and x['value']==actual]
        if not proof:return None,'unverified_element_evidence',ref
        if len({(type(v['value']).__name__,str(v['value'])) for v in records.get(key,[])})>1:
            return None,'disputed_document_records',ref
        return actual,'bound_synthetic_document_bytes',ref
    good=records.get(key,[])
    if not good:
        reason='invalid_document_reference' if any(x['fact_key']==key for x in failed) else 'missing_evidence'
        return None,reason,None
    if len({(type(v['value']).__name__,str(v['value'])) for v in good})>1:
        return None,'disputed_document_records',None
    return good[0]['value'],'bound_synthetic_document_bytes',good[0]['document_ref']


def assess_rule(rule,case,idx,records,failed,sources,attack_index):
    aid=rule['attack_angle_id'];upstream=attack_index.get(aid) if aid else None
    in_scope=case['procedure_type'] in rule['procedure_types']
    tests=[];support=[];contrary=[];missing=[];scope_note=None
    if in_scope and 'activation' in rule:
        # C16's fixture-topic activation is NOT a legal-applicability ruling.
        # When no bounded synthetic trigger is evidenced, do not assert the topic
        # has been researched, and do not burden unrelated historical cases.
        ac=rule['activation'];av,aq,ar=value_for(ac,case,idx,records,failed)
        matched=(av is not None and ac['operator']=='one_of' and
                 any(type(av)==type(v) and av==v for v in ac['expected_values']))
        if not matched:
            in_scope=False
            scope_note='C16 topic not activated by bounded synthetic evidence ('+ac['fact_key']+':'+aq+'); not a legal inapplicability finding.'
    if in_scope:
        for cond in rule['conditions']:
            key=cond['fact_key']; val,quality,ref=value_for(cond,case,idx,records,failed)
            if val is None:
                status='unverified' if quality in ('unverified_element_evidence','invalid_document_reference','disputed_document_records') else 'missing'
                missing.append(key+':'+quality)
            elif cond['operator']=='one_of':
                status='matched' if any(type(val)==type(v) and val==v for v in cond['expected_values']) else 'contrary'
            else:
                try:
                    valid=type(val)==str and date.fromisoformat(val).isoformat()==val
                except ValueError:valid=False
                status='matched' if valid else 'contrary'
            line={'fact_key':key,'result':status,'value':val,'quality':quality,'document_ref':ref}
            tests.append(line)
            if status=='matched':support.append(line)
            if status=='contrary':contrary.append(line)
        if rule['rule_id']=='se:c12:visa-appeal-timing':
            a=next((x['value'] for x in support if x['fact_key']=='fact:decision_notice_date'),None)
            b=next((x['value'] for x in support if x['fact_key']=='fact:appeal_submission_date'),None)
            if a and b and date.fromisoformat(b)<date.fromisoformat(a):
                missing.append('Temporal inconsistency: appeal submission precedes recorded notice.')
    if in_scope:
        missing_sources=[s['source_id'] for s in rule['source_citations'] if s['source_id'] not in sources]
        missing.extend('unavailable_primary_source:'+sid for sid in missing_sources)
    if not in_scope:state='not_applicable'
    elif contrary:state='contradicted'
    elif missing:state='unresolved'
    else:state='supported_for_review'
    if upstream and upstream['assessment_status'] in ('blocked','insufficient_evidence') and state=='supported_for_review':
        state='unresolved';missing.append('C5d upstream candidate blocked: '+upstream['assessment_status'])
    return {'assessment_id':rule['rule_id'],'label':rule['label'],'status':state,
        'attack_angle_id':aid,'upstream_c5d_status':upstream['assessment_status'] if upstream else None,
        'predicate_results':tests, 'supported_facts':support,'contrary_facts':contrary,'missing_or_unverified':missing,
        'exception_questions':rule['exception_questions'] if in_scope else [],
        'source_citations':[{'source_id':s['source_id'],'pinpoint_hint':s['pinpoint_hint'],
            'source_assurance':sources.get(s['source_id'],{'assurance':'not_in_active_source_pack'})['assurance']} for s in rule['source_citations']] if in_scope else [],
        'limitations':rule['limitations']+([scope_note] if scope_note else []), 'legal_violation_status':'not_determined'}


def build(case,elements,c5d,source_pack,module_pairs=(),rule_extensions=(),fact_ledger=None):
    validate_obj('case-input',case);validate_obj('c5d-attack-angle-synthesis',c5d)
    validate_obj('core-source-pack',source_pack)
    if case['privacy_classification']!='synthetic':raise C12Error('private_case_disabled')
    if digest_obj(case)!=c5d['bindings']['case_sha256'] or digest_obj(elements)!=c5d['bindings']['element_bundle_sha256'] or digest_obj(source_pack)!=c5d['bindings']['source_pack_sha256']:
        raise C12Error('unbound_c12_upstream')
    sources,modules=source_lookup(source_pack,module_pairs)
    if not hasattr(element_model,'ELEMENT_IDS_CACHE'):
        element_model.ELEMENT_IDS_CACHE={x['element_id'] for x in element_model.load_model()[0]['elements']}
    idx={x['element_id']:x for x in (elements or {}).get('elements',[])}
    if len(idx)!=len((elements or {}).get('elements',[])):raise C12Error('duplicate_elements')
    docs=load_document_registry()
    records,failed,ledger_digest=verify_evidence_ledger(case,elements,fact_ledger,docs)
    eu=load_json(EU_RULES)
    if eu.get('owner')!='eu_core' or eu.get('rules_version')!='0.2.0':raise C12Error('incorrect_eu_rule_pack')
    rules=list(eu['rules']); bindings=[];seen=set()
    for ext in rule_extensions:
        validate_obj('c12-rule-extension',ext)
        mid=ext['producer_module_id'];mod=modules.get(mid)
        if mod is None:raise C12Error('unenrolled_module_rule_extension:'+mid)
        if ext['producer_module_family']!=mod['module_family'] or ext['jurisdiction']!=mod['jurisdiction'] or ext['bound_export_sha256']!=digest_obj(mod):
            raise C12Error('country_rule_export_binding_mismatch:'+mid)
        if mid in seen:raise C12Error('duplicate_country_rule_extension:'+mid)
        seen.add(mid)
        # Only country-owned sources are legal bases for country-owned rules.
        for r in ext['rules']:
            check_rule(r,'country',sources,mid)
        rules.extend(ext['rules'])
        bindings.append({'module_id':mid,'extension_sha256':digest_obj(ext),'bound_export_sha256':ext['bound_export_sha256']})
    for r in eu['rules']:check_rule(r,'eu_core',sources,'eu_core')
    ids=[r['rule_id'] for r in rules]
    if len(ids)!=len(set(ids)):raise C12Error('duplicate_rule_id')
    attack_index={r['attack_angle_id']:r for r in c5d['attack_angles']}
    assessments=[assess_rule(r,case,idx,records,failed,sources,attack_index) for r in rules]
    assessed_attacks={r['attack_angle_id'] for r in rules if r['attack_angle_id']}
    novel=[{'attack_angle_id':x['attack_angle_id'],'label':x['label'],
            'upstream_status':x['assessment_status'],
            'reason':'Candidate not covered by a C12 rule; requires research, cannot be suppressed as irrelevant.',
            'source_refs':x['source_refs'],'status':'novel_unassessed'}
           for x in c5d['attack_angles'] if x['attack_angle_id'] not in assessed_attacks]
    outstanding=sorted(set(v for a in assessments for v in a['missing_or_unverified']))
    if failed:
        outstanding.extend(sorted(set('unverified_document_ref:'+x['document_ref']+':'+x['fact_key'] for x in failed)))
    out={'engine_version':VERSION,'case_id':case['case_id'],'conclusion':'not_determined',
       'bindings':{'case_sha256':digest_obj(case),'elements_sha256':digest_obj(elements),
                   'c5d_sha256':digest_obj(c5d),'source_pack_sha256':digest_obj(source_pack),
                   'eu_rules_sha256':digest_obj(eu),'document_index_sha256':digest_obj(load_json(DOCUMENTS)),
                   'fact_ledger_sha256':ledger_digest,'country_rule_extensions':sorted(bindings,key=lambda r:r['module_id'])},
       'assessments':assessments,'novel_issues':novel,'unresolved':outstanding,
       'unverified_evidence_records':failed,
       'limitations':['Synthetic only; structured JSON document surrogates are not authentic documents or independently verified facts.',
        'Source notes and pinpoints are review hints, not certified current national law.',
        'C16 not_applicable for non-activated topics means no qualifying bounded fixture trigger, NOT a legal determination of inapplicability.',
        'Rules can reach review-readiness, never establish a legal violation or appeal deadline.',
        'Unprofiled candidate issues remain prominently visible, not claims of infringements.',
        'C3 and C2 contracts unchanged; country rules are separately bound sidecar data.']}
    validate_obj('c12-legal-resolution',out)
    return out


def render(out):
    lines=['# C12 legal rule resolution (fictional development tests)', '',
      '**Never a legal determination or evidentiary authentication.**', '',
      'Case: `'+out['case_id']+'`; final legal conclusion: `not_determined`', '',
      '## Structured legal assessments', '']
    for a in out['assessments']:
        lines+=['### '+a['assessment_id'],'',
                '- '+a['label'],'- Predicate status: `'+a['status']+'` — violation `not_determined`.']
        for x in a['predicate_results']:
            lines.append('- '+x['fact_key']+': `'+x['result']+'`; provenance `'+x['quality']+'`; document `'+str(x['document_ref'])+'`.')
        for m in a['missing_or_unverified']:lines.append('- Noted gap/trigger: '+m)
        for exc in a['exception_questions']:lines.append('- Exception/review: '+exc)
        for s in a['source_citations']:lines.append('- Source review hint: '+s['source_id']+' '+s['pinpoint_hint']+' ('+s['source_assurance']+')')
        lines.append('')
    lines+=['## Novel / unprofiled issues — must not be hidden', '']
    for n in out['novel_issues']:lines.append('- `'+n['attack_angle_id']+'` '+n['label']+': '+n['reason'])
    if not out['novel_issues']:lines.append('No unprofiled C5d candidates identified in this synthetic fixture.')
    lines+=['','## Unverified / missing facts','']
    for msg in out['unresolved']:lines.append('- '+msg)
    lines+=['','**No legal violations, deadline entitlements, or external actions are established.**','']
    return ('\n'.join(lines)).encode('utf-8')
