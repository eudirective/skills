#!/usr/bin/env python3
"""C15 local deterministic tests (not semantic or legal-expert scoring)."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import c15_casework as c15
from contract_validate import load_json
from c7_trust_gate import APPROVED_SYNTHETIC_RUN_IDS,require_approved,C7TrustError

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'references/fixtures/c15/pilot-01'

def main():
    tests=[]
    def passed(name):
        tests.append(name);print('PASS',name,flush=True)
    def must_block(f,tag):
        try:f()
        except (c15.C15Error,ValueError,KeyError,TypeError) as e:
            assert tag in str(e),(tag,str(e))
        else:raise AssertionError('should block: '+tag)

    idx=c15.build_case_index();assert len(idx['documents'])==14 and idx['synthetic_only']
    passed('14_pinned_fictional_documents')
    src,source_index=c15.source_manifest();assert len(source_index)==46
    assert sum(len(s['representations']) for s in src['sources'])==47
    passed('restored_47_sources_verifiable')
    proposals=load_json(FIXTURE/'model-proposals.json')
    queries=load_json(FIXTURE/'retrieval-queries.json')
    assert len(proposals['facts'])==15 and len(proposals['legal_questions'])==8
    passed('bounded_model_proposal_fixture')
    with tempfile.TemporaryDirectory(prefix='c15-casework-') as tmp:
        t=Path(tmp);case_dir=t/'case'
        c15.prep(type('A',(),{'output_dir':str(case_dir)}))
        assert (case_dir/'case-index.json').is_file()
        passed('fresh_prep_outputs')
        request=t/'queries.json';request.write_text(json.dumps(queries))
        retrieval=t/'retrieval.json'
        c15.retrieve(type('A',(),{'index':str(case_dir/'case-index.json'),'requests':str(request),'output':str(retrieval)}))
        ret,sources=c15.load_retrieval(retrieval,idx)
        assert sum(len(q['hits']) for q in ret['queries'])>=12
        passed('exact_source_retrieval')
        score=c15.validated_proposal(idx,ret,proposals,sources)
        assert score['document_coverage']==14 and score['question_count']==8
        assert score['legal_violation_status']=='not_determined' and score['semantic_entailment']=='not_checked'
        passed('proposal_quotes_and_cross_refs_validated')
        verified=t/'verification.json';md=t/'review.md'
        pp=t/'proposals.json';pp.write_text(json.dumps(proposals))
        c15.check(type('A',(),{'index':str(case_dir/'case-index.json'),'retrieval':str(retrieval),'proposals':str(pp),'output':str(verified),'report':str(md)}))
        assert 'not independently verified' in md.read_text() and 'no_violation_established' in md.read_text()
        passed('complete_case_review_report_conservative')
        forged=copy.deepcopy(proposals);forged['facts'][0]['evidence'][0]['start']+=1
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'quote_not_in_source_at_offsets')
        passed('shifted_document_quote_rejected')
        forged=copy.deepcopy(proposals);forged['facts'][0]['evidence'][0]['document_sha256']='0'*64
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_document_digest_mismatch')
        passed('forged_document_sha_rejected')
        forged=copy.deepcopy(proposals);forged['facts'][0]['evidence'][0]['document_id']='D90'
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_unknown_document_ref')
        passed('unknown_document_rejected')
        forged=copy.deepcopy(proposals);forged['facts'][3]['attribution']='applicant_assertion'
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_attribution_not_from_document_role')
        passed('speaker_role_mismatch_rejected')
        forged=copy.deepcopy(proposals);forged['legal_questions'][0]['legal_sources'][0]['source_sha256']='0'*64
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_unbound_eu_source_citation')
        passed('forged_eu_source_rejected')
        forged=copy.deepcopy(proposals);forged['legal_questions'][0]['legal_sources'][0]['pinpoint_hint']='Article 6(1)'
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_directive_pinpoint_wrong_article')
        passed('wrong_directive_article_rejected')
        forged=copy.deepcopy(proposals);forged['legal_questions'][0]['legal_sources'][0]['start']-=4
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'quote_not_in_source_at_offsets')
        passed('misquoted_legal_text_rejected')
        forged=copy.deepcopy(proposals);forged['legal_questions'][0]['disposition']='violation_established'
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_final_violation_status_forbidden')
        passed('automatic_illegality_finding_rejected')
        forged=copy.deepcopy(proposals);forged['facts']=[f for f in forged['facts'] if f['id']!='F15']
        # Q06 refers to F15, so missing fact crossref must reject.
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_missing_fact_cross_reference')
        passed('missing_fact_cross_reference_rejected')
        forged=copy.deepcopy(proposals);forged['legal_questions'][0]['support_fact_ids']=[]
        forged['legal_questions'][0]['qualifying_fact_ids']=[]
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_empty_issue_facts')
        passed('empty_legal_issue_facts_rejected')
        forged=copy.deepcopy(proposals);forged['legal_questions'][0]['legal_sources']=[]
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_no_source_cannot_assert_legal_concern')
        passed('legal_concern_without_sources_rejected')
        forged=copy.deepcopy(proposals);forged['unmapped_evidence']=['D99']
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_unknown_unmapped_evidence')
        passed('invented_unmapped_document_rejected')
        forged=copy.deepcopy(proposals);forged['case_id']='CASE-C15-SOMEONE-REAL'
        must_block(lambda:c15.validated_proposal(idx,ret,forged,sources),'c15_proposal_identity_or_digest_mismatch')
        passed('arbitrary_case_id_rejected')
        changed=copy.deepcopy(ret);changed['queries'][0]['hits'][0]['excerpt']='this was never said'
        changed_path=t/'bad-retrieval.json';changed_path.write_text(json.dumps(changed))
        must_block(lambda:c15.load_retrieval(changed_path,idx),'c15_retrieval_hash_or_quote_forgery')
        passed('forged_retrieval_blocked')
        m=FIXTURE/'manifest.json'
        original=c15.PILOT
        with patch.object(c15,'PILOT',t/'fake-manifest.json'):
            (t/'fake-manifest.json').write_bytes(m.read_bytes()+b'\n')
            must_block(c15.pinned_fixture,'c15_pilot_manifest_integrity_mismatch')
        passed('changed_allowlist_manifest_blocked')
        assert 'RUN-C15-PILOT' not in APPROVED_SYNTHETIC_RUN_IDS
        with __import__('unittest').TestCase().assertRaises(C7TrustError):
            require_approved('case',{'case_id':'CASE-C15-PILOT-01'})
        passed('c7_allowlist_not_expanded')
        try:c15.prep(type('A',(),{'output_dir':str(case_dir)}))
        except c15.C15Error as e:assert 'output_dir_not_empty' in str(e)
        else:raise AssertionError('output overwrite permitted')
        passed('nonempty_output_dir_rejected')
    print(json.dumps({'status':'passed','assertion_groups':len(tests),'groups':tests},indent=2))

if __name__=='__main__':main()
