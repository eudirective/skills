#!/usr/bin/env python3
"""C17 fictional draft boundary and tamper tests (not legal validity tests)."""
from copy import deepcopy
import c17_applicant_drafts as d

def rejected(fn):
    try: fn()
    except ValueError: return
    raise AssertionError('unsafe draft accepted')

def run():
    result = []
    for n in range(1, 9):
        a = d.generate(n)
        assert a['case_id'] == f'L{n}' and a['send_authorized'] is False
        assert a['legal_violation_status'] == 'not_determined'
        assert a['verified_legal_merits'] is False and a['requires_human_review']
        assert all(q['citations_for_human_check'] and q['legal_violation_status']=='not_determined' for q in a['questions'])
        assert 'NOT FOR SENDING' in d.render(a)
        assert d.generate(n) == a
        result.append((n,len(a['questions'])))
    import test_c16_coverage as t
    import c6_integration as c
    case, els, actors, ctx, pairs, exts, ledger, docs = t.load_case(2)
    st = c.stage_outputs(case, els, actors, None, ctx, t.SOURCE, pairs, exts, ledger, docs)
    bad=deepcopy(case);bad['privacy_classification']='private'
    rejected(lambda:d.build('L2',bad,st['c12'],st['c13']))
    bad=deepcopy(st['c12']);bad['conclusion']='violation'
    rejected(lambda:d.build('L2',case,bad,st['c13']))
    bad=deepcopy(st['c13']);bad['mode']='not_enrolled'
    rejected(lambda:d.build('L2',case,st['c12'],bad))
    bad=deepcopy(st['c13']);bad['rule_links']*=2
    rejected(lambda:d.build('L2',case,st['c12'],bad))
    rejected(lambda:d.build('L9',case,st['c12'],st['c13']))
    print('C17 PASS: 8 reproducible synthetic drafts; 5 negative boundary checks', result)
if __name__=='__main__':run()
