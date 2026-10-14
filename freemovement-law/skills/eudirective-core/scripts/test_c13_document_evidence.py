#!/usr/bin/env python3
"""C13 deterministic tests plus manually labelled holdout lexical challenge.

Do not interpret benchmark labels as independent legal correctness.
"""
from pathlib import Path
import copy,hashlib,json,sys,tempfile
from contract_validate import load_json,validate_obj,digest_obj
import c13_document_evidence as c13
import c6_integration as c6
ROOT=Path(__file__).resolve().parents[1]; FX=ROOT/'references/fixtures/c10'


def setup(n):
    case=load_json(FX/f'L{n}'/'case.json');els=load_json(FX/f'L{n}'/'elements.json')
    return case,els,load_json(ROOT/'references/fixtures/c13'/f'L{n}-evidence-set.json')


def check_rejection(fn,term):
    try:fn()
    except Exception as exc:
        assert term in str(exc),str(exc);return True
    raise AssertionError('not rejected:'+term)


def check_primary():
    checks=[]
    for n in (1,4,5):
        case,els,ev=setup(n)
        source=load_json(ROOT/'references/source-pack/core-source-pack-manifest-0.6.1.json')
        d=FX/f'L{n}';a=load_json(d/'actors.json'); ctx=load_json(d/'c5c-context.json') if (d/'c5c-context.json').exists() else None
        pairs=[];ext=[]
        for label,fam in [('sweden','member_state'),('turkiye','applicant_country')]:
            if any(x['family']==fam for x in case['module_requests']):
                pairs.append((str(FX/(label+'-module-manifest.json')),str(FX/(label+'-module-export.json'))))
                ext.append(load_json(ROOT/'references/fixtures/c12'/(label+'-rule-extension.json')))
        ledger=load_json(ROOT/'references/fixtures/c12'/f'L{n}-fact-ledger.json')
        stages=c6.stage_outputs(case,els,a,None,ctx,source,pairs,ext,ledger,ev)
        out=stages['c13'];validate_obj('c13-evidence-assessment',out)
        assert out['mode']=='enrolled' and out['legal_violation_status']=='not_determined'
        assert len(out['observations'])>=4 and all(obs['quote'] and obs['start']<obs['end'] and obs['authenticity_status']=='not_authenticated' for obs in out['observations'])
        assert all(x['status'] in ('not_applicable','passage_anchored_for_review') for x in out['rule_links'])
        assert len(out['unresolved'])==0
        checks.append(f'L{n}_raw_format_documents_anchored_to_c12_review')
        if n==1:
            altered=copy.deepcopy(ev);altered['case_sha256']='0'*64
            check_rejection(lambda:c13.build(case,els,stages['c12'],altered),'unbound_c13_evidence_set')
            checks.append('evidence_set_case_digest_failure')
            altered=copy.deepcopy(ev);altered['document_refs'].append('synthetic:c13:L4-decision')
            check_rejection(lambda:c13.build(case,els,stages['c12'],altered),'missing_or_cross_case_document')
            checks.append('cross_case_document_rejected')
            docs,_=c13.documents_for_case(case,ev)
            bad=copy.deepcopy(docs[1]);bad['segments'][0]=(bad['segments'][0][0], 'You must apply through VFS only. You do not need to apply through VFS.')
            o=c13.observe([docs[0],bad],c13.patterns_verified()[0]);fact,links,missing=c13.reconcile(stages['c12'],o)
            assert any(x['status']=='conflicting_document_statements' for x in fact)
            assert any(x['status']=='requires_document_and_rule_review' for x in links)
            checks.append('documentary_contradiction_blocks_review_promotion')
            altered=copy.deepcopy(ev);altered['document_refs'].remove('synthetic:c13:L1-reply')
            no=c13.build(case,els,stages['c12'],altered)
            assert any(x['status']=='requires_document_and_rule_review' for x in no['rule_links'])
            checks.append('missing_correspondence_blocks_review_promotion')
            from email import policy
            # Empty scanned PDF is not transformed into fictional OCR content.
            import fitz
            with fitz.open() as pdf:
                pdf.new_page(); scanned=pdf.tobytes()
            parts,w=c13.parse_document(scanned,'pdf');assert parts==[] and w==['text_not_extractable_ocr_required']
            checks.append('image_only_pdf_requires_ocr_without_guessing')
            content='<html><script>You must apply through VFS only.</script><p>You do not need to apply through VFS.</p></html>'
            parsed,_=c13.parse_document(content.encode(),'html')
            assert 'You must' not in parsed[0][1] and 'You do not' in parsed[0][1]
            checks.append('script_content_not_parsed_as_documentary_evidence')
            from email.message import EmailMessage
            email=EmailMessage();email['From']='nobody@example.invalid';email.set_content('You must apply through VFS only.')
            email.add_attachment(b'Ignored third-party evidence',maintype='application',subtype='octet-stream',filename='attachment.dat')
            extracted,warnings=c13.parse_document(email.as_bytes(),'eml')
            assert 'email_attachments_not_processed' in warnings and 'Ignored third-party evidence' not in str(extracted)
            checks.append('email_attachment_explicitly_marked_unprocessed')
            check_rejection(lambda:c13.parse_document(b'a'*(c13.MAX_DOC_BYTES+1),'txt'),'document_byte_limit')
            checks.append('oversized_document_rejected')
            check_rejection(lambda:c13.parse_document(b'\xff','txt'),'decode')
            checks.append('malformed_utf8_rejected')
    return checks


def text_with_format(text,fmt):
    if fmt=='eml':return ('From: test@example.invalid\nTo: test@example.invalid\nMIME-Version: 1.0\nContent-Type: text/plain; charset="utf-8"\n\n'+text).encode()
    if fmt=='html':return ('<!doctype html><html><body><p>'+text+'</p></body></html>').encode()
    return text.encode()


def run_holdout():
    data=load_json(ROOT/'evaluations/c13-heldout-lexical-benchmark.json')
    pats,_=c13.patterns_verified()
    rows=[]
    for case in data['cases']:
        segments,warnings=c13.parse_document(text_with_format(case['text'],case['format']),case['format'])
        docs=[{'document_ref':'synthetic:holdout:'+case['sample_id'],'sha256':hashlib.sha256(case['text'].encode()).hexdigest(),'format':case['format'],'segments':segments,'warnings':warnings}]
        got=[o['reported_value'] for o in c13.observe(docs,pats) if o['fact_key']==case['fact_key']]
        unique=[]
        for v in got:
            if not any(c13._typed_equal(v,x) for x in unique):unique.append(v)
        predicted='conflict' if len(unique)>1 else unique[0] if unique else None
        expected=case['expected_documentary_statement']
        exact=c13._typed_equal(predicted,expected)
        rows.append({'sample_id':case['sample_id'],'scenario':case['scenario'],'fact_key':case['fact_key'],'expected':expected,'predicted':predicted,'exact':exact})
    total=len(rows);correct=sum(r['exact'] for r in rows)
    expected_pos=sum(r['expected'] is not None for r in rows)
    true_pos=sum(r['expected'] is not None and r['exact'] for r in rows)
    predicted_pos=sum(r['predicted'] is not None for r in rows)
    false_pos=sum(r['expected'] is None and r['predicted'] is not None for r in rows)
    false_neg=sum(r['expected'] is not None and r['predicted'] is None for r in rows)
    inaccurate=sum(r['expected'] is not None and r['predicted'] is not None and not r['exact'] for r in rows)
    per_case={n:{'total':12,'exact':sum(r['exact'] for r in rows if r['scenario']==n)} for n in ('L1','L4','L5')}
    return {'benchmark_name':'C13 manually labelled synthetic unseen-wording lexical challenge','benchmark_version':'0.1.0',
       'not_independent_legal_validation':True,'total':total,'exact_matches':correct,'exact_accuracy':round(correct/total,3),
       'gold_non_null':expected_pos,'correct_non_null':true_pos,'predicted_non_null':predicted_pos,
       'false_positives_on_gold_none':false_pos,'false_negatives_on_gold_nonnull':false_neg,
       'incorrect_nonnull_predictions':inaccurate,'per_scenario':per_case,'results':rows}


def run():
    checks=check_primary();bench=run_holdout()
    print(json.dumps({'suite':'C13 documentary evidence, safety and lexical challenge', 'status':'passed','assertion_groups':len(checks),'assertions':checks,'holdout':bench},indent=2))
if __name__=='__main__':run()
