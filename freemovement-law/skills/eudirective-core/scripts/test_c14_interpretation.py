#!/usr/bin/env python3
"""C14 multilingual *wording* evaluation; never legal-merits certification."""
from pathlib import Path
from email.message import EmailMessage
import argparse, copy, hashlib, json
from contract_validate import load_json, validate_obj
import c14_interpretation as c14
import c13_document_evidence as c13
ROOT=Path(__file__).resolve().parents[1]


def byte_doc(text,fmt):
    if fmt=='eml':
        msg=EmailMessage();msg['From']='unverified@example.invalid';msg.set_content(text)
        return msg.as_bytes()
    if fmt=='html':return ('<html><body><p>'+text+'</p></body></html>').encode('utf-8')
    return text.encode('utf-8')


def bench(data):
    grammar,_=c14.load_grammar()
    results=[]
    for case in data['cases']:
        raw=byte_doc(case['text'],case['format']);segments,warnings=c13.parse_document(raw,case['format'])
        docs=[{'document_ref':case['id'],'sha256':hashlib.sha256(raw).hexdigest(),'format':case['format'],'segments':segments,'warnings':warnings}]
        candidates=[x for x in c14.extract_candidates(docs,grammar) if x['fact_key']==case['target_fact_key']]
        acceptable=[x for x in candidates if not x['cautions']]
        values=[]
        for x in acceptable:
            v=x['proposed_value']
            if not any(type(v)==type(q) and v==q for q in values):values.append(v)
        actual=None if not values else values[0] if len(values)==1 else 'conflict'
        target=case['expected_assertion']
        correct=(type(target)==type(actual) and target==actual)
        anchored=all(next(t for k,t in segments if k==x['locator'])[x['start']:x['end']]==x['quote'] for x in candidates)
        assert anchored
        results.append({'id':case['id'],'language':case['language'],'scenario':case['scenario'],'context':case['context'],
                        'expected':target,'predicted':actual,'exact':correct,'candidate_count':len(candidates),
                        'cautioned_candidates':len(candidates)-len(acceptable)})
    def metrics(sub):
        n=len(sub);gold=sum(r['expected'] is not None for r in sub)
        found=sum(r['predicted'] is not None for r in sub)
        tp=sum(r['expected'] is not None and r['exact'] for r in sub)
        fp=sum(r['expected'] is None and r['predicted'] is not None for r in sub)
        wrong=sum(r['expected'] is not None and r['predicted'] is not None and not r['exact'] for r in sub)
        return {'total':n,'exact_matches':sum(r['exact'] for r in sub), 'exact_accuracy':round(sum(r['exact'] for r in sub)/n,3) if n else None,
                'gold_supported_statements':gold,'correct_supported_statements':tp,
                'recall_supported':round(tp/gold,3) if gold else None,
                'predicted_supported':found,'unsupported_positive_predictions':fp,'incorrect_nonnull_predictions':wrong,
                'precision_correct_predictions':round(tp/found,3) if found else None}
    return {'dataset':data.get('benchmark_version'), 'development_origin':data.get('method'),
            'metrics':metrics(results),'per_language':{x:metrics([r for r in results if r['language']==x]) for x in sorted({r['language'] for r in results})},
            'per_scenario':{x:metrics([r for r in results if r['scenario']==x]) for x in sorted({r['scenario'] for r in results})},
            'context_slices':{x:metrics([r for r in results if r['context']==x]) for x in sorted({r['context'] for r in results})},
            'failures':[r for r in results if not r['exact']], 'rows':results}


def topic_bench(data):
    lexicon,_=c14.load_topic_lexicon()
    observations=[]
    for case in data['cases']:
        raw=byte_doc(case['text'],case['format'])
        seg,_=c13.parse_document(raw,case['format'])
        docs=[{'document_ref':case['id'],'sha256':hashlib.sha256(raw).hexdigest(), 'segments':seg}]
        targets=[r for r in c14.retrieve_review_targets(docs,lexicon) if r['fact_key']==case['target_fact_key']]
        for target in targets:
            assert next(t for loc,t in seg if loc==target['locator'])[target['start']:target['end']]==target['quote']
            assert target['proposed_value'] is None and target['interpretation_status']=='requires_interpretation_review'
        observations.append({'id':case['id'],'language':case['language'],'gold_asserted':case['expected_assertion'] is not None,
                             'retrieved':bool(targets),'n_targets':len(targets)})
    def tally(sub):
        good=sum(x['gold_asserted'] for x in sub)
        negatives=len(sub)-good
        retrieved_good=sum(x['gold_asserted'] and x['retrieved'] for x in sub)
        retrieved_neg=sum(not x['gold_asserted'] and x['retrieved'] for x in sub)
        return {'n':len(sub),'gold_asserted':good,'retrieved_asserted':retrieved_good,
                'retrieval_recall':round(retrieved_good/good,3) if good else None,
                'negative_cases':negatives,'negative_review_load':retrieved_neg,
                'review_load_fraction':round(retrieved_neg/negatives,3) if negatives else None}
    return {'aggregate':tally(observations),
            'per_language':{lang:tally([x for x in observations if x['language']==lang]) for lang in sorted({x['language'] for x in observations})},
            'missed_assertion_ids':[x['id'] for x in observations if x['gold_asserted'] and not x['retrieved']],
            'retrieval_never_establishes_meaning_or_facts':True}


def legacy_36_regression():
    rows=load_json(ROOT/'evaluations/c13-heldout-lexical-benchmark.json')['cases']
    c13_pats,_=c13.patterns_verified();c14_pats,_=c14.load_grammar()
    count=0;failed=[]
    for r in rows:
        raw=byte_doc(r['text'],r['format']);seg,_=c13.parse_document(raw,r['format'])
        docs=[{'document_ref':r['sample_id'],'sha256':hashlib.sha256(raw).hexdigest(), 'segments':seg}]
        vals=[x['reported_value'] for x in c13.observe(docs,c13_pats) if x['fact_key']==r['fact_key']]
        vals.extend(x['proposed_value'] for x in c14.extract_candidates(docs,c14_pats) if x['fact_key']==r['fact_key'] and not x['cautions'])
        uniq=[]
        for v in vals:
            if not any(type(v)==type(u) and v==u for u in uniq):uniq.append(v)
        got='conflict' if len(uniq)>1 else uniq[0] if uniq else None
        expected=r['expected_documentary_statement']
        if type(got)==type(expected) and got==expected:count+=1
        else:failed.append(r['sample_id'])
    return {'n':len(rows),'surface_candidate_match_count':count,'failed_ids':failed,
            'development_regression_only':True,'c14_candidates_not_promoted_into_c12':True}


def audit():
    tests=[]
    def verify_invalid(fn,term):
        try:fn()
        except c14.C14Error as exc:
            assert term in str(exc),(term,str(exc));return
        raise AssertionError('not_rejected:'+term)
    # Mixed language candidate anchoring and quote/source position.
    en='You must apply through VFS only.';sv='VFS är inte obligatoriskt.';tr='Vize başvurunuz reddedilmiştir.'
    entries=[]
    for i,(lang,txt) in enumerate([('en',en),('sv',sv),('tr',tr)]):
        raw=txt.encode();entries.append({'document_ref':f'c14:test:{lang}', 'sha256':hashlib.sha256(raw).hexdigest(),
          'format':'txt','segments':[('text:body',txt)],'warnings':[]})
    grammar,_=c14.load_grammar();cand=c14.extract_candidates(entries,grammar)
    assert len(cand)>=3 and {c['language'] for c in cand}=={'en','sv','tr'}
    assert all(c['interpretation_status']=='candidate_requires_review' and c['fact_truth_status']=='not_determined' for c in cand)
    tests.append('all_three_languages_review_only')
    sentence='The applicant alleges: "You must apply through VFS only."'
    docs=[{'document_ref':'c14:test:quoted','sha256':hashlib.sha256(sentence.encode()).hexdigest(),
           'format':'txt','segments':[('text:body',sentence)],'warnings':[]}]
    quoted=c14.extract_candidates(docs,grammar)
    assert quoted and any('quoted_or_reported_other_speaker' in x['cautions'] for x in quoted)
    tests.append('quotation_attribution_caution')
    conditional='If you must apply through VFS only, please ask why.'
    docs=[{'document_ref':'c14:test:conditional','sha256':hashlib.sha256(conditional.encode()).hexdigest(),
           'format':'txt','segments':[('text:body',conditional)],'warnings':[]}]
    conditional_c=c14.extract_candidates(docs,grammar)
    assert conditional_c and all('question_or_conditional_context' in c['cautions'] for c in conditional_c)
    tests.append('conditional_modality_caution')
    # Proposals are checked against pinned bytes, do not gain fact or legal status.
    obs=cand[0]
    p={k:obs[k] for k in ('document_ref','locator','document_sha256','segment_sha256','start','end','quote','fact_key','language')}
    p['proposed_value']=obs['proposed_value'];p['explanation']='A hypothetical proposer associated this passage with the controlled fact key.'
    validated=c14.verify_external_proposals(entries,{'proposal_version':'0.1.0','proposals':[p]})
    assert validated[0]['source_verified'] and validated[0]['semantic_status']=='requires_human_review'
    tests.append('model_proposal_text_anchored_without_semantic_promotion')
    bad=copy.deepcopy(p);bad['document_ref']='does-not-exist'
    verify_invalid(lambda:c14.verify_external_proposals(entries,{'proposal_version':'0.1.0','proposals':[bad]}),'document_unknown')
    tests.append('fabricated_proposal_document_rejected')
    bad=copy.deepcopy(p);bad['quote']='different text'
    verify_invalid(lambda:c14.verify_external_proposals(entries,{'proposal_version':'0.1.0','proposals':[bad]}),'quote_not_anchored')
    tests.append('fabricated_proposal_quote_rejected')
    bad=copy.deepcopy(p);bad['document_sha256']='0'*64
    verify_invalid(lambda:c14.verify_external_proposals(entries,{'proposal_version':'0.1.0','proposals':[bad]}),'hash_mismatch')
    tests.append('unregistered_proposal_bytes_rejected')
    bad=copy.deepcopy(p);bad['fact_key']='fact:unregistered'
    verify_invalid(lambda:c14.verify_external_proposals(entries,{'proposal_version':'0.1.0','proposals':[bad]}),'unknown_proposal_scope')
    tests.append('invented_fact_key_rejected')
    case=load_json(ROOT/'references/fixtures/c10/L1/case.json')
    elements=load_json(ROOT/'references/fixtures/c10/L1/elements.json')
    ev=load_json(ROOT/'references/fixtures/c13/L1-evidence-set.json')
    docs,_=c13.documents_for_case(case,ev)
    # A C13 report must pin a C14 grammar and carry only unreviewed candidates.
    stub={'assessments':[]}
    report=c13.build(case,elements,stub,ev)
    validate_obj('c13-evidence-assessment',report)
    assert report['engine_version']=='0.2.0' and report['bindings']['c14_grammar_sha256']
    assert all(x['interpretation_status']=='candidate_requires_review' for x in report['c14_interpretation_candidates'])
    assert report['bindings']['c14_topic_sha256'] and all(t['proposed_value'] is None for t in report['c14_review_targets'])
    tests.append('c13_c14_schema_and_pin_valid')
    novel='We are unable to offer a way to file your application without using the outsourcing company.'
    raw=novel.encode(); docs=[{'document_ref':'c14:test:novel','sha256':hashlib.sha256(raw).hexdigest(),
                               'segments':[('text:body',novel)]}]
    old=c13.observe(docs,c13.patterns_verified()[0])
    proposed=c14.extract_candidates(docs,c14.load_grammar()[0])
    topics=c14.retrieve_review_targets(docs,c14.load_topic_lexicon()[0])
    assert not old and not proposed and any(t['fact_key']=='fact:mission_requires_vfs_only' for t in topics)
    tests.append('unknown_provider_paraphrase_visible_without_claim_of_illegality')
    return tests


def run():
    cases=load_json(ROOT/'evaluations/c14-frozen-multilingual-wording-benchmark.json')
    checks=audit()
    hard=load_json(ROOT/'evaluations/c14-untuned-adversarial-benchmark.json')
    result={'suite':'C14 review-only document interpretation, multilingual synthetic wording challenge',
            'status':'passed','assertion_groups':len(checks),'assertions':checks,
            'development_wording_suite':bench(cases),
            'untuned_adversarial_wording_suite':bench(hard),
            'topic_retrieval_dev':topic_bench(cases),
            'topic_retrieval_adversarial':topic_bench(hard),
            'historical_c13_wording_regression':legacy_36_regression(),
            'scope_notice':'This is not independent legal adjudication, authenticity verification, or production multilingual NLP accuracy.'}
    return result

if __name__=='__main__':
    o=run();print(json.dumps(o,ensure_ascii=False,indent=2))
