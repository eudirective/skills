#!/usr/bin/env python3
"""Post-C12 legacy C11 EU-only compatibility and conservative screening checks."""
import copy,json
from pathlib import Path
from contract_validate import load_json,digest_obj,validate_obj
import c6_integration as c6
import legal_assessment as c11

ROOT=Path(__file__).resolve().parents[1];FIXTURES=ROOT/'references/fixtures/c10'
SOURCE=load_json(ROOT/'references/source-pack/core-source-pack-manifest-0.6.1.json')

def stage(n):
    d=FIXTURES/f'L{n}';case=load_json(d/'case.json');e=load_json(d/'elements.json');act=load_json(d/'actors.json');ctx=load_json(d/'c5c-context.json') if (d/'c5c-context.json').exists() else None
    pairs=[]
    for slug,family in [('sweden','member_state'),('turkiye','applicant_country')]:
        if any(req['family']==family for req in case['module_requests']):
            pairs.append((str(FIXTURES/(slug+'-module-manifest.json')),str(FIXTURES/(slug+'-module-export.json'))))
    return case,e,pairs,c6.stage_outputs(case,e,act,None,ctx,SOURCE,pairs)

def get(obj,rid):return next(x for x in obj['assessments'] if x['assessment_id']==rid)

def run():
    checks=[]
    for n in range(1,9):
        case,e,pairs,out=stage(n);v=out['c11'];validate_obj('c11-legal-assessment',v)
        assert v['bindings']['case_sha256']==digest_obj(case)
        assert all(a['legal_violation_status']=='not_determined' for a in v['assessments'])
        checks.append('L'+str(n)+'_legacy_c11_eu_rules_and_unprofiled_issues')
    case,e,pairs,out=stage(1)
    assert get(out['c11'],'c11:attack:core-access')['status']=='supported_for_review'
    assert not any(x['assessment_id']=='c11:attack:se-access' for x in out['c11']['assessments'])
    assert get(out['c11'],'c11:unprofiled:se:attack:administrative-access')['status']=='unresolved'
    checks.append('legacy_c11_no_national_rules_and_unprofiled_conservative')
    case,e,pairs,out=stage(5)
    assert not any(x['assessment_id']=='c11:attack:se-file' for x in out['c11']['assessments'])
    checks.append('deldwyn_moved_to_eu_c12_and_sweden_module_sidecar')
    case,e,pairs,out=stage(1)
    bad=copy.deepcopy(e);bad['elements'][0]['value']='changed'
    try:c11.build(case,bad,out['c5d'],SOURCE,pairs)
    except c11.AssessmentError as er:assert 'unbound_c5d_elements' in str(er)
    else:raise AssertionError('unbound C11 input not rejected')
    checks.append('c11_legacy_digest_boundary_retained')
    print(json.dumps({'status':'passed','assertion_groups':len(checks),'checks':checks},indent=2))
if __name__=='__main__':run()
