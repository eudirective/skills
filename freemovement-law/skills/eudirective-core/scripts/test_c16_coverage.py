#!/usr/bin/env python3
"""C16 frozen fictional eight-scenario coverage and adversarial integrity tests.

A passing test is a mechanical assessment of authored synthetic predicates, NOT
independent/legal-expert verification of rights, infringements or real evidence.
"""
from pathlib import Path
import copy,hashlib,json
from contract_validate import load_json,digest_obj,validate_obj
import c6_integration as c6
import c7_trust_gate as trust
import c12_rule_resolution as c12
import c13_document_evidence as c13
import module_conformance

ROOT=Path(__file__).resolve().parents[1]
FX=ROOT/'references/fixtures/c10'
SOURCE=load_json(ROOT/'references/source-pack/core-source-pack-manifest-0.6.1.json')
NEW=(2,3,6,7,8)
REQUIRED={
 2:['eu:c16:visa-fee-v-provider-charge','se:c16:istanbul-service-fee','tr:c16:istanbul-vfs-choice'],
 3:['eu:c16:exclusive-proof-visa','se:c16:document-list-review'],
 6:['eu:c16:prior-card-entry-gate','se:c16:visa-card-route'],
 7:['se:c16:jo-supervision-boundary'],
 8:['eu:c16:electronic-proof-format','se:c16:electronic-format-review','tr:c16:electronic-population-extract']
}

def load_case(n):
    folder=FX/f'L{n}';case=load_json(folder/'case.json');els=load_json(folder/'elements.json')
    actors=load_json(folder/'actors.json')
    ctx=load_json(folder/'c5c-context.json') if (folder/'c5c-context.json').exists() else None
    pairs=[];extensions=[]
    for label,fam in [('sweden','member_state'),('turkiye','applicant_country')]:
        if any(m['family']==fam for m in case['module_requests']):
            pair=(str(FX/(label+'-module-manifest.json')),str(FX/(label+'-module-export.json')))
            pairs.append(pair)
            extensions.append(load_json(ROOT/'references/fixtures/c12'/(label+'-rule-extension.json')))
    ledger=load_json(ROOT/f'references/fixtures/c12/L{n}-fact-ledger.json')
    doc_set=load_json(ROOT/f'references/fixtures/c13/L{n}-evidence-set.json')
    return case,els,actors,ctx,pairs,extensions,ledger,doc_set

def denied(fn,msg):
    try:fn()
    except Exception as exc:
        if msg not in str(exc):raise AssertionError('wrong exception: '+str(exc)) from exc
        return
    raise AssertionError('accepted forbidden data: '+msg)

def run():
    checks=[];summary={}
    trust.require_source_pack(SOURCE)
    for n in range(1,9):
        if n not in NEW:continue
        case,els,actors,ctx,pairs,exts,ledger,doc_set=load_case(n)
        assert case['privacy_classification']=='synthetic'
        for role,content in [('case',case),('elements',els),('actors',actors),('c12_fact_ledger',ledger),('c13_evidence_set',doc_set)]:
            trust.require_approved(role,content)
        for extension in exts:trust.require_approved('c12_rule_extension',extension)
        stages=c6.stage_outputs(case,els,actors,None,ctx,SOURCE,pairs,exts,ledger,doc_set)
        c12r=stages['c12'];c13r=stages['c13']
        validate_obj('c12-legal-resolution',c12r);validate_obj('c13-evidence-assessment',c13r)
        assert c12r['engine_version']=='0.2.0' and c13r['mode']=='enrolled'
        by_id={x['assessment_id']:x for x in c12r['assessments']}
        by_docs={x['assessment_id']:x for x in c13r['rule_links']}
        for rid in REQUIRED[n]:
            assert by_id[rid]['status']=='supported_for_review',(n,rid,by_id[rid])
            assert by_docs[rid]['status']=='passage_anchored_for_review',(n,rid,by_docs[rid])
            assert by_id[rid]['legal_violation_status']=='not_determined'
            assert all(x['source_assurance'] in ('bundled_text_integrity_checked_not_completeness','curated_source_note_only','country_source_summary_only') for x in by_id[rid]['source_citations'])
        assert c13r['legal_violation_status']=='not_determined'
        assert len(c13r['documents'])>=2 and len(c13r['observations'])>=4
        assert all(o['document_sha256'] and o['quote'] and o['fact_truth_status']=='not_determined' for o in c13r['observations'])
        assert all(x['fact_truth_status']=='not_determined' for x in c13r['fact_checks'])
        assert not any('c16_topic_not_activated' in u for u in c12r['unresolved'])
        # Do not hide issues that lack a profiled C16 rule.
        assert all(x['status']=='novel_unassessed' for x in c12r['novel_issues'])
        # Ineligible topics are never treated as legal compliance findings.
        for rid,assessment in by_id.items():
            if ':c16:' in rid and rid not in REQUIRED[n]:
                assert assessment['status']=='not_applicable'
                assert assessment['legal_violation_status']=='not_determined'
        summary['L'+str(n)]={'activated':REQUIRED[n],'document_refs':doc_set['document_refs'],
            'reported_statements':len(c13r['observations']), 'novel_unassessed':len(c12r['novel_issues'])}
        checks.append('L'+str(n)+'_C12_C13_typed_evidence_and_source_ownership')

    # The old three cases have no new activated C16 rules and remain fully c13-anchored.
    for n in (1,4,5):
        case,els,actors,ctx,pairs,exts,ledger,docs=load_case(n)
        stages=c6.stage_outputs(case,els,actors,None,ctx,SOURCE,pairs,exts,ledger,docs)
        new=[r for r in stages['c12']['assessments'] if ':c16:' in r['assessment_id']]
        assert new and all(r['status']=='not_applicable' for r in new)
        assert all(x['status'] in ('passage_anchored_for_review','not_applicable') for x in stages['c13']['rule_links'])
        assert stages['c13']['unresolved']==[]
        checks.append(f'L{n}_old_documentary_compatibility')

    n=3
    case,els,actors,ctx,pairs,exts,ledger,doc_set=load_case(n)
    base=c6.stage_outputs(case,els,actors,None,ctx,SOURCE,pairs,exts,ledger,doc_set)
    wrong=copy.deepcopy(ledger)
    next(x for x in wrong['records'] if x['fact_key']=='fact:alternate_evidence_offered')['document_ref']='synthetic:edocument-extract'
    result=c12.build(case,els,base['c5d'],SOURCE,pairs,exts,wrong)
    assert next(x for x in result['assessments'] if x['assessment_id']=='eu:c16:exclusive-proof-visa')['status']=='unresolved'
    checks.append('cross_case_document_reference_does_not_support_checklist_claim')
    wrong=copy.deepcopy(ledger)
    next(x for x in wrong['records'] if x['fact_key']=='fact:alternate_evidence_offered')['value']=False
    result=c12.build(case,els,base['c5d'],SOURCE,pairs,exts,wrong)
    assert next(x for x in result['assessments'] if x['assessment_id']=='eu:c16:exclusive-proof-visa')['status']=='unresolved'
    checks.append('wrong_ledger_value_cannot_override_document_bytes')
    wrong=copy.deepcopy(doc_set);wrong['document_refs'].append('synthetic:c13:L8-extract')
    denied(lambda:c13.build(case,els,base['c12'],wrong),'missing_or_cross_case_document')
    checks.append('cross_case_raw_document_selection_refused')
    registry=load_json(ROOT/'references/evidence/c13-document-index.json')
    wrong=copy.deepcopy(registry)
    next(x for x in wrong['documents'] if x['case_fixture']=='L3')['sha256']='0'*64
    denied(lambda:c13.documents_for_case(case,doc_set,registry=wrong),'modified_document_bytes')
    checks.append('changed_raw_document_sha_rejected')
    # Wrong producer source is neither EU law nor Swedish law.
    forged=copy.deepcopy(exts[0]);forged['rules'][-1]['source_citations'][0]['source_id']='tr:src:turkiye-nvi-population'
    denied(lambda:c12.build(case,els,base['c5d'],SOURCE,pairs,[forged,exts[1]],ledger),'country_rule_claims_other_module_source')
    checks.append('swedish_rule_cannot_claim_turkish_source')
    forged=copy.deepcopy(exts[0]);forged['rules'][-1]['activation']['operator']='date'
    forged['rules'][-1]['activation']['expected_values']=[]
    denied(lambda:c12.build(case,els,base['c5d'],SOURCE,pairs,[forged,exts[1]],ledger),'activation_requires_one_of')
    checks.append('activation_date_operator_rejected')
    forged=copy.deepcopy(exts[0]);forged['rules'][-1]['activation']['fact_key']='__import__:os'
    denied(lambda:c12.build(case,els,base['c5d'],SOURCE,pairs,[forged,exts[1]],ledger),'illegal_fact_prefix')
    checks.append('reject_non_data_activation_expression')
    # A claim that the VFS charge was compulsory must not inherit the fixture's optional-route finding.
    case,els,actors,ctx,pairs,exts,ledger,doc_set=load_case(2)
    base=c6.stage_outputs(case,els,actors,None,ctx,SOURCE,pairs,exts,ledger,doc_set)
    bad=copy.deepcopy(ledger)
    next(x for x in bad['records'] if x['fact_key']=='fact:vfs_route_optional')['value']=False
    out=c12.build(case,els,base['c5d'],SOURCE,pairs,exts,bad)
    assert next(x for x in out['assessments'] if x['assessment_id']=='eu:c16:visa-fee-v-provider-charge')['status']=='unresolved'
    checks.append('unsubstantiated_optional_fee_claim_not_promoted')
    # A Swedish nonbinding operational note cannot be elevated to verified statutory text.
    assert all(r['source_assurance']=='country_source_summary_only' for x in base['c12']['assessments'] if x['assessment_id']=='se:c16:istanbul-service-fee' for r in x['source_citations'])
    checks.append('national_notes_not_relabelled_full_statutes')
    eu=load_json(ROOT/'references/legal-assessment/c12-eu-rules.json')
    for rule in eu['rules']:
        assert all(s['source_id'].startswith('eu:') for s in rule['source_citations'])
    for label in ('sweden','turkiye'):
        current=load_json(ROOT/'references/fixtures/c12'/(label+'-rule-extension.json'))
        country=load_json(ROOT.parent/('eudirective-ms-sweden' if label=='sweden' else 'eudirective-ac-turkiye')/'references/c12-rule-extension.json')
        assert current==country
        assert current['extension_version']=='0.2.0'
    checks.append('country_owned_rules_equal_distributed_module_sidecars')
    # Preserve security boundary unchanged after adding five enrolled C12/C13 cases.
    denied(lambda:trust.require_synthetic_run_metadata('RUN-ANY-CASE','2026-10-10T10:00:00Z'),'unapproved_synthetic_run_id')
    checks.append('code_pinned_run_ids_not_expanded')
    print(json.dumps({'suite':'C16 eight scenario source and documentary coverage', 'status':'passed',
        'checks':len(checks), 'check_names':checks,'new_scenarios':summary,
        'legal_merits_graded':False,'C15f_expert_or_blinded_eval_run':False},ensure_ascii=False,indent=2))

if __name__=='__main__':run()
