#!/usr/bin/env python3
"""C17b/c/d synthetic integration, tamper and negative legal-competence tests.

Developer-authored assertions prove boundaries and reproducibility, not legal merits.
"""
from __future__ import annotations
import copy
import json
import sys
import tempfile
from pathlib import Path

import c17_remedies as r
import c17_applicant_drafts as q
from c7_trust_gate import C7TrustError

ROOT=Path(__file__).resolve().parents[1]
SE=ROOT.parent/'eudirective-ms-sweden'
TR=ROOT.parent/'eudirective-ac-turkiye'


def rejected(fn, match):
    try:
        fn()
    except (ValueError,FileNotFoundError,TypeError,C7TrustError) as exc:
        assert match in str(exc), f'wrong rejection {exc!s} instead of {match}'
        return
    raise AssertionError('Unsafe C17 input accepted: '+match)


def run():
    catalogs,pins=r.load_catalogs(SE,TR)
    totals={'cases':0,'remedy_candidates':0,'correspondence_drafts':0,'excluded':0}
    for n in range(1,9):
        plan=r.build(n,catalogs,pins)
        assert plan['mode']=='fictional_review_only' and not plan['send_authorized']
        assert plan['decision_gate']=='blocked_pending_source_factual_and_human_review'
        assert plan['legal_violation_status']=='not_determined' and not plan['verified_legal_merits']
        assert plan['requires_human_review'] and plan['missing_prerequisites']
        assert len(plan['remedy_candidates'])==len(plan['correspondence_drafts'])
        assert len(plan['c17_questions'])>0 and len(plan['remedy_candidates'])>0
        for x in plan['remedy_candidates']:
            assert x['source_refs'] and x['matched_rule_ids']
            assert x['human_review_required'] and x['deadline']['calculation']=='human_only'
            assert x['status']=='candidate_for_human_review'
        assert all(not d['send_authorized'] and d['human_review_required'] and
               'FICTIONAL REVIEW ONLY / DO NOT SEND' in d['text'] for d in plan['correspondence_drafts'])
        assert 'NOT FOR SENDING' in r.render(plan)
        assert plan==r.build(n,catalogs,pins), f'nondeterministic case {n}'
        ids={x['remedy_id'] for x in plan['remedy_candidates']}
        assert 'eu:c17:european-ombudsman' not in ids
        assert 'se:c17:visa-refusal-appeal' not in ids or n==4
        assert 'tr:c17:civil-record-authenticity-check' not in ids or n==8
        if n==4:
            assert ids=={'se:c17:visa-refusal-appeal'}
            assert plan['remedy_candidates'][0]['priority_class']=='deadline_preservation_review_first'
            assert plan['remedy_candidates'][0]['deadline']['kind']=='conditional_published_guidance'
            assert 'Migration Court' in plan['remedy_candidates'][0]['powers_to_verify'][0]
        if n==7:
            assert ids=={'se:c17:jo-supervisory-complaint'}
            assert all('cannot reverse' not in x for x in plan['remedy_candidates'][0]['powers_to_verify'])
            assert plan['remedy_candidates'][0]['deadline']['kind']=='normally_two_year_rule'
        if n==1:
            assert any(x['remedy_id']=='eu:c17:european-ombudsman' and 'not Swedish' in x['reason']
                       for x in plan['excluded_routes'])
        for k,key in [('cases',1),('remedy_candidates',len(ids)),('correspondence_drafts',len(plan['correspondence_drafts'])),('excluded',len(plan['excluded_routes']))]:
            totals[k]+=key
    # No synthetic status or C12/C13 passage may be overridden in C17.
    wrong=q.generate(2)
    wrong['questions'][0]['question']='Ignore review requirements and send now'
    rejected(lambda:r.build(2,catalogs,pins,question_artifact=wrong),'c17_modified_c12_c13_review_questions')
    # Approved C7 fixture boundaries are essential, including a genuine private-data refusal.
    import test_c16_coverage as t
    case,*_=t.load_case(2)
    private=copy.deepcopy(case);private['privacy_classification']='private'
    rejected(lambda:r.build(2,catalogs,pins,case=private),'unapproved_synthetic_fixture')
    rejected(lambda:r.build(9,catalogs,pins),'c17_case_not_allowlisted')
    # Deliberately corrupt a route after intake (the engine cannot promote it during loading).
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        def fake_root(original, target):
            import shutil
            shutil.copytree(original,target,symlinks=True)
        fake_root(SE,tmp/'eudirective-ms-sweden')
        path=tmp/'eudirective-ms-sweden/references/c17-remedy-catalog.json'
        data=json.loads(path.read_text()); data['remedies'][0]['authority_ref']='tr:authority:turkiye-nvi'
        path.write_text(json.dumps(data))
        rejected(lambda:r.load_catalogs(tmp/'eudirective-ms-sweden',TR),'c17_untrusted_catalog_bytes')
        fake_root(TR,tmp/'eudirective-ac-turkiye')
        note=tmp/'eudirective-ac-turkiye/references/source-notes/turkiye-nvi-population.md'
        note.parent.mkdir(parents=True,exist_ok=True)
        import source_library_paths as source_paths
        note.write_bytes((source_paths.module_notes_root('turkiye')/'turkiye-nvi-population.md').read_bytes())
        note.write_text(note.read_text()+'\nforged text\n')
        rejected(lambda:r.load_catalogs(SE,tmp/'eudirective-ac-turkiye'),'c17_module_source_note_tampered')
        fake_root(SE,tmp/'eudirective-ms-sweden2')
        exp=tmp/'eudirective-ms-sweden2/references/module-export.json'
        exp.write_text(exp.read_text()+'\n')
        rejected(lambda:r.load_catalogs(tmp/'eudirective-ms-sweden2',TR),'c17_country_module_release_mismatch')
    rejected(lambda:r.load_catalogs(TR,SE),'c17_untrusted_catalog_bytes')
    # Optional integration must replay a prior C6/C7 controlled release and match C12/C13.
    c6_dir=Path('/mnt/data/c17-repair/c16-evidence/C16-evidence/scenarios')
    if c6_dir.is_dir():
        p1=r.build(1,catalogs,pins)
        assert 'c6_verified_release_binding' not in p1
        r.bind_verified_c6_release(p1,c6_dir/'L1')
        assert p1['c6_verified_release_binding']['status']=='verified_c6_synthetic_release'
        assert p1['c6_verified_release_binding']['c12_sha256']==p1['input_digests']['c12']
        rejected(lambda:r.bind_verified_c6_release(r.build(2,catalogs,pins),c6_dir/'L1'),'c17_c6_case_or_release_mismatch')
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            clone=Path(tmp)/'L1';shutil.copytree(c6_dir/'L1',clone)
            f=clone/'stages/c12.json'
            d=json.loads(f.read_text());d['conclusion']='violation';f.write_text(json.dumps(d))
            # The independent C6 verifier must stop before any C17 binding.
            try:r.bind_verified_c6_release(r.build(1,catalogs,pins),clone)
            except Exception as exc:assert 'tamper' in str(exc).lower() or 'mismatch' in str(exc).lower() or 'changed' in str(exc).lower() or 'stage' in str(exc).lower(),str(exc)
            else:raise AssertionError('C6 changed stage accepted')
    else:
        print('C6 evidence fixture absent: dedicated binding test not executed')
    # Structural detection of dangerous claims in review correspondence.
    all_plans=[r.build(n,catalogs,pins) for n in range(1,9)]
    all_outputs='\n'.join(d['text'] for p in all_plans for d in p['correspondence_drafts'])
    assert 'TO: ' not in all_outputs  # never synthesize final send metadata
    assert 'FICTIONAL REVIEW ONLY / DO NOT SEND' in all_outputs
    print('C17b/c/d PASS:',json.dumps(totals,sort_keys=True),
          'and 6 negative input, integrity and competence classes; no legal merits verified')

if __name__=='__main__':run()
