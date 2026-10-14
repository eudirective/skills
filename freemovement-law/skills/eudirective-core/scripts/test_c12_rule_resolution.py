#!/usr/bin/env python3
"""C12 deterministic contract tests. These are not independent legal merits tests."""
from pathlib import Path
import copy,json
from contract_validate import load_json,digest_obj,validate_obj
import c6_integration as c6
import c12_rule_resolution as c12

from source_library_paths import compatibility_root

ROOT=Path(__file__).resolve().parents[1]
FX=ROOT/'references/fixtures/c10'
LEDGERS=ROOT/'references/fixtures/c12'
SOURCE=load_json(compatibility_root()/'core-source-pack-manifest-0.6.1.json')

def setup(n):
    d=FX/f'L{n}';case=load_json(d/'case.json');e=load_json(d/'elements.json')
    actors=load_json(d/'actors.json');ctx=load_json(d/'c5c-context.json') if (d/'c5c-context.json').exists() else None
    pairs=[];ext=[]
    for name,family in [('sweden','member_state'),('turkiye','applicant_country')]:
        if any(x['family']==family for x in case['module_requests']):
            pairs.append((str(FX/(name+'-module-manifest.json')),str(FX/(name+'-module-export.json'))))
            ext.append(load_json(LEDGERS/(name+'-rule-extension.json')))
    ledger=load_json(LEDGERS/(f'L{n}-fact-ledger.json')) if (LEDGERS/(f'L{n}-fact-ledger.json')).exists() else None
    return case,e,actors,ctx,pairs,ext,ledger

def find(out,rid):return next(x for x in out['assessments'] if x['assessment_id']==rid)

def expect_error(fn,fragment):
    try:fn()
    except Exception as err:
        assert fragment in str(err),(fragment,str(err));return
    raise AssertionError('not rejected:'+fragment)

def run():
    checks=[]
    results={}
    for n in (1,4,5):
        case,e,actors,ctx,pairs,ext,ledger=setup(n)
        stages=c6.stage_outputs(case,e,actors,None,ctx,SOURCE,pairs,ext,ledger)
        report=stages['c12'];validate_obj('c12-legal-resolution',report)
        assert report['conclusion']=='not_determined'
        assert all(a['legal_violation_status']=='not_determined' for a in report['assessments'])
        assert report['bindings']['fact_ledger_sha256']==digest_obj(ledger)
        assert report['novel_issues'] and 'Novel / unprofiled' in c12.render(report).decode()
        results[n]=stages
        checks.append(f'L{n}_source_bound_fictional_assessment_and_novelty')
    for rid in ('eu:c12:direct-consular-access','se:c12:direct-access','tr:c12:direct-channel'):
        assert find(results[1]['c12'],rid)['status']=='supported_for_review',rid
    checks.append('L1_direct_access_structured_predicates_now_resolvable')
    assert find(results[4]['c12'],'se:c12:visa-appeal-timing')['status']=='supported_for_review'
    assert find(results[5]['c12'],'eu:c12:deldwyn-specific-disclosure')['status']=='supported_for_review'
    checks+=['L4_appeal_dates_typed_and_review_ready_not_deadline_calculation','L5_deldwyn_conditions_resolved_without_legal_merits_promotion']
    # Bad document reference cannot support the fact, even with the right scalar value.
    case,e,actors,ctx,pairs,ext,ledger=setup(1)
    forged=copy.deepcopy(ledger)
    for item in forged['records']:
        if item['fact_key']=='element:procedure.access_state':item['document_ref']='synthetic:nonexistent-document'
    out=c12.build(case,e,results[1]['c5d'],SOURCE,pairs,ext,forged)
    assert find(out,'eu:c12:direct-consular-access')['status']=='unresolved'
    assert any(x['reason']=='missing_or_wrong_case_document' for x in out['unverified_evidence_records'])
    checks.append('nonexistent_document_reference_cannot_substantiate_element')
    forged=copy.deepcopy(ledger)
    for item in forged['records']:
        if item['fact_key']=='element:procedure.access_state':item['value']='available'
    out=c12.build(case,e,results[1]['c5d'],SOURCE,pairs,ext,forged)
    assert find(out,'eu:c12:direct-consular-access')['status']=='unresolved'
    checks.append('document_bytes_disagree_with_ledger_claim')
    forged=copy.deepcopy(ledger)
    forged['case_sha256']='0'*64
    expect_error(lambda:c12.build(case,e,results[1]['c5d'],SOURCE,pairs,ext,forged),'unbound_case_fact_ledger')
    checks.append('ledger_bound_to_exact_case_and_elements')
    bad=copy.deepcopy(ext[0]);bad['bound_export_sha256']='0'*64
    expect_error(lambda:c12.build(case,e,results[1]['c5d'],SOURCE,pairs,[bad,ext[1]],ledger),'country_rule_export_binding_mismatch')
    checks.append('national_rule_extension_bound_to_frozen_c3_export')
    bad=copy.deepcopy(ext[0]);bad['rules'][0]['source_citations'][0]['source_id']='tr:src:sweden-istanbul-eu-family'
    expect_error(lambda:c12.build(case,e,results[1]['c5d'],SOURCE,pairs,[bad,ext[1]],ledger),'country_rule_claims_other_module_source')
    checks.append('country_cannot_claim_other_country_source_ownership')
    bad=copy.deepcopy(ext[0]);bad['rules'][0]['conditions'][0]['fact_key']='case:arbitrary_payload'
    expect_error(lambda:c12.build(case,e,results[1]['c5d'],SOURCE,pairs,[bad,ext[1]],ledger),'illegal_case_key')
    checks.append('forbid_untyped_arbitrary_fact_access')
    # Outside target legal regime => not applicable, NOT 'contradicted' or violation.
    assert find(results[1]['c12'],'eu:c12:deldwyn-specific-disclosure')['status']=='not_applicable'
    assert find(results[5]['c12'],'eu:c12:direct-consular-access')['status']=='not_applicable'
    checks.append('legal_regime_separation_deldwyn_vs_visa')
    case,e,actors,ctx,pairs,ext,ledger=setup(4)
    damaged=copy.deepcopy(ledger)
    for item in damaged['records']:
        if item['fact_key']=='fact:appeal_submission_date':item['value']='2026-08-20'
    bad=c12.build(case,e,results[4]['c5d'],SOURCE,pairs,ext,damaged)
    assert find(bad,'se:c12:visa-appeal-timing')['status']=='unresolved'
    checks.append('incorrect_appeal_date_is_not_presumed_authentic')
    # Country-specific profiles never live in the active C11/ EU catalogs.
    eu=load_json(ROOT/'references/legal-assessment/c12-eu-rules.json')
    legacy=load_json(ROOT/'references/legal-assessment/c11-rule-profiles.json')
    assert all(s['source_id'].startswith('eu:') for r in eu['rules'] for s in r['source_citations'])
    assert all(s['source_id'].startswith('eu:') for r in legacy['rules'] for s in r['source_citations'])
    checks.append('country_rules_not_hardcoded_into_active_eu_rule_catalogue')
    print(json.dumps({'suite':'C12 rule resolution and evidence integrity','status':'passed','assertion_groups':len(checks),
                      'checks':checks,'scenarios':{f'L{n}':{'statuses':{x['assessment_id']:x['status'] for x in st['c12']['assessments']},
                                                             'novel_issue_count':len(st['c12']['novel_issues'])} for n,st in results.items()}},indent=2))

if __name__=='__main__':run()
