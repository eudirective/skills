#!/usr/bin/env python3
"""C14 standalone checker for review-only AI/human semantic proposals.

The checker verifies synthetic registry membership and byte/quote anchors; it
never verifies semantic correctness, human review, author identity or law.
It is NOT a C6 authority or an input enrolment mechanism.
"""
import argparse
from pathlib import Path
import json
from contract_validate import load_json,validate_obj,digest_obj
from c7_trust_gate import require_approved, require_synthetic_run_metadata
from c13_document_evidence import documents_for_case
from c14_interpretation import verify_external_proposals, VERSION, C14Error

def run():
    parser=argparse.ArgumentParser(description='Verify exact quotation anchors in code-enrolled synthetic documents; no semantic certification.')
    parser.add_argument('--case',required=True)
    parser.add_argument('--elements',required=True)
    parser.add_argument('--evidence-set',required=True)
    parser.add_argument('--proposals',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    case=load_json(Path(args.case));elements=load_json(Path(args.elements));ev=load_json(Path(args.evidence_set))
    validate_obj('case-input',case);validate_obj('element-instance-bundle',elements);validate_obj('c13-evidence-set',ev)
    require_approved('case',case);require_approved('elements',elements);require_approved('c13_evidence_set',ev)
    if ev['case_sha256']!=digest_obj(case) or ev['elements_sha256']!=digest_obj(elements):
        raise C14Error('c14_unbound_case_and_evidence_set')
    documents,_=documents_for_case(case,ev)
    proposals=load_json(Path(args.proposals))
    validated=verify_external_proposals(documents,proposals)
    result={'engine_version':VERSION,'case_id':case['case_id'],'scope':'pinned_synthetic_review_only',
       'case_sha256':digest_obj(case),'elements_sha256':digest_obj(elements),
       'evidence_set_sha256':digest_obj(ev),'proposal_set_sha256':digest_obj(proposals),
       'candidate_count':len(validated),'candidates':validated,
       'semantics_established':False,'source_authenticity_established':False,
       'legal_violation_status':'not_determined',
       'limitations':['Byte and text-position anchoring are checked; reviewer identity and proposition meaning are not verified.',
                     'No external proposal enters C6 factual prerequisites automatically.',
                     'Only previously approved fictional evidence sources may be inspected.']}
    dest=Path(args.output)
    if dest.exists():raise C14Error('c14_output_exists')
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'anchored_only_review_pending','candidate_count':len(validated),
                      'sha256':digest_obj(result),'output':str(dest)}))

if __name__=='__main__':run()
