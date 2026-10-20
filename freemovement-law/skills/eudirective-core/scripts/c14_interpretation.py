#!/usr/bin/env python3
"""C14 offline, *review-only* multilingual proposition proposals with exact text anchors.

A regex cue, even if correctly anchored, is NOT semantic proof. C14 candidates are
not forwarded into the C12 evidence-value channel or the C6 legal findings. A
separate proposal verifier can verify LLM/human suggestions' text provenance,
not their semantics or reviewer identity. No network access or arbitrary files.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import hashlib
import re
from contract_validate import load_json, digest_obj

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT/'references/evidence/c14-clause-grammar.json'
VERSION='0.1.0'
LANGUAGES={'en','sv','tr'}
KNOWN_FACT_KEYS={
    'element:procedure.access_state', 'fact:mission_requires_vfs_only',
    'fact:eu_family_direct_request', 'fact:visa_refusal_exists',
    'fact:decision_notice_date','fact:appeal_submission_date',
    'fact:appeal_received_by_correct_authority',
    'fact:authority_possesses_information',
    'fact:decisive_former_spouse_information',
    'fact:information_requested_predecision',
    'fact:applicant_cannot_obtain_information',
    'fact:authority_communication_state',
    'fact:confidentiality_review_state',
}

class C14Error(Exception): pass


def sha(data):return hashlib.sha256(data).hexdigest()


def _canonical_date(value):
    try:
        return date.fromisoformat(value).isoformat() if date.fromisoformat(value).isoformat()==value else None
    except ValueError:return None


def load_grammar(root=ROOT):
    catalog=load_json(root/'references/evidence/c14-clause-grammar.json')
    if catalog.get('grammar_version')!=VERSION:raise C14Error('wrong_c14_grammar_version')
    if catalog.get('scope')!='synthetic_only_candidate_interpretations':raise C14Error('c14_grammar_scope')
    prepared=[];seen=set()
    for p in catalog['rules']:
        if set(p)!={'id','fact_key','language','pattern','reported_value','extractor'}:raise C14Error('invalid_grammar_rule_keys')
        if p['id'] in seen:raise C14Error('duplicate_c14_rule_id')
        seen.add(p['id'])
        if p['language'] not in LANGUAGES or p['fact_key'] not in KNOWN_FACT_KEYS:raise C14Error('unknown_c14_fact_or_language')
        if len(p['pattern'])>400 or p['extractor'] not in ('literal','iso_date'):raise C14Error('unbounded_c14_rule')
        if p['extractor']=='literal' and type(p['reported_value']) not in (str,bool):raise C14Error('invalid_c14_value')
        if p['extractor']=='iso_date' and (p['reported_value'] is not None or p['fact_key'] not in ('fact:decision_notice_date','fact:appeal_submission_date')):
            raise C14Error('invalid_c14_date_rule')
        try:regex=re.compile(p['pattern'],flags=re.IGNORECASE | re.UNICODE)
        except re.error as exc:raise C14Error('broken_c14_regex:'+p['id']) from exc
        if p['extractor']=='iso_date' and 'date' not in regex.groupindex:raise C14Error('c14_date_group_missing')
        prepared.append((p,regex))
    if len(prepared)>100:raise C14Error('c14_rule_budget_exceeded')
    return prepared,digest_obj(catalog)


def _clause_context(text,start,end):
    # Do not cross a sentence boundary, except date delimiters where period is not
    # a sentence end. Quotes and previous attribution trigger review, never proof.
    left=max(text.rfind('\n',0,start),text.rfind(';',0,start),text.rfind('?',0,start),text.rfind('!',0,start))
    right=min((v for v in (text.find('\n',end),text.find(';',end),text.find('?',end),text.find('!',end)) if v!=-1),default=len(text))
    return text[left+1:right], text[left+1:start]


def _interpretation_cautions(text,start,end,quote,language):
    ctx,before=_clause_context(text,start,end)
    lower=ctx.casefold()
    pre=before.casefold()
    flags=[]
    if ('?' in text[max(0,start-2):min(len(text),end+2)] or
        re.search(r'\b(?:whether|if|suppose|assuming|hypothetically|what if|om|ifall|eğer|acaba)\b', lower)):
        flags.append('question_or_conditional_context')
    if re.search(r'\b(?:might|maybe|may have|could|possibly|perhaps|eventually|kanske|eventuellt|olabilir|belki)\b',lower):
        flags.append('epistemic_qualification')
    # If a cue is embedded in a quotation, provenance of the quoted speaker is
    # unresolved even when the document containing the quote is pinned.
    prev_quotes=before.count('"')+before.count('“')+before.count('«')
    if prev_quotes%2 or re.search(r'\b(?:alleges?|claims?|quoted?|according to|cites?|iddia|uppger|citat)\b',pre):
        flags.append('quoted_or_reported_other_speaker')
    if re.search(r'\b(?:not true|incorrect|false statement|disputed|denies having|yanlış|doğru değil|felaktigt|inte korrekt)\b',lower):
        flags.append('explicit_dispute_near_statement')
    # The source's identity and intent remain unverified in all cases.
    return sorted(set(flags))


def extract_candidates(documents, prepared, *, include_tentative=True):
    observations=[]
    for doc in documents:
        for locator,text in doc['segments']:
            for rule,regex in prepared:
                for match in regex.finditer(text):
                    if len(observations)>=350:raise C14Error('c14_candidate_budget_exceeded')
                    value=rule['reported_value']
                    if rule['extractor']=='iso_date':
                        value=_canonical_date(match.group('date'))
                        if value is None:continue
                    start,end=match.span()
                    if start==end or end-start>400:continue
                    quote=text[start:end]
                    cautions=_interpretation_cautions(text,start,end,quote,rule['language'])
                    observations.append({
                        'candidate_id':'c14:candidate:%04d'%(len(observations)+1),
                        'fact_key':rule['fact_key'],'proposed_value':value,
                        'document_ref':doc['document_ref'],'document_sha256':doc['sha256'],
                        'locator':locator,'segment_sha256':sha(text.encode('utf-8')),
                        'start':start,'end':end,'quote':quote,'language':rule['language'],
                        'grammar_id':rule['id'],
                        'interpretation_status':'candidate_requires_review',
                        'cautions':cautions,
                        'authenticity_status':'not_authenticated','fact_truth_status':'not_determined',
                    })
    # Remove redundant exact duplicates, but preserve conflicting values and
    # distinct text spans; never resolve disagreement by order of rule matching.
    observations.sort(key=lambda r:(r['document_ref'],r['locator'],r['start'],r['end'],r['fact_key'],str(r['proposed_value']),r['grammar_id']))
    seen=set();unique=[]
    for item in observations:
        key=(item['document_ref'],item['locator'],item['start'],item['end'],item['fact_key'],type(item['proposed_value']),str(item['proposed_value']))
        if key in seen:continue
        seen.add(key);item['candidate_id']='c14:candidate:%04d'%(len(unique)+1);unique.append(item)
    return unique


def resolve_candidate_issues(candidates, legacy_observations):
    issues=[]
    grouped={}
    for c in candidates:grouped.setdefault(c['fact_key'],[]).append(c)
    for k,rows in grouped.items():
        vals={(type(x['proposed_value']).__name__,str(x['proposed_value'])) for x in rows}
        if len(vals)>1: issues.append('c14:conflicting_interpretations:'+k)
        for row in rows:
            if row['cautions']:issues.append('c14:attribution_or_modality_review:'+row['candidate_id'])
    legacy_keys={x['fact_key'] for x in legacy_observations}
    for k in grouped:
        if k not in legacy_keys:issues.append('c14:unreviewed_new_evidence_candidate:'+k)
    return sorted(set(issues))


def verify_external_proposals(documents, proposals):
    """Check LLM/human proposal *anchors*, NOT truth or semantic entailment.

    Proposals do not enter C6 review readiness automatically. Reviewer identity and
    whether a passage entails the claimed proposition remain open questions.
    """
    if not isinstance(proposals,dict) or set(proposals)!={'proposal_version','proposals'} or proposals['proposal_version']!='0.1.0':
        raise C14Error('invalid_c14_proposal_bundle')
    if not isinstance(proposals['proposals'],list) or len(proposals['proposals'])>100:raise C14Error('c14_proposal_count_limit')
    segments={}
    for doc in documents:
        for locator,text in doc['segments']:
            segments[(doc['document_ref'],locator)]=(doc['sha256'],sha(text.encode('utf-8')),text)
    checked=[]
    for p in proposals['proposals']:
        fields={'document_ref','locator','document_sha256','segment_sha256','start','end','quote','fact_key','proposed_value','language','explanation'}
        if not isinstance(p,dict) or set(p)!=fields:raise C14Error('c14_proposal_fields_invalid')
        if p['fact_key'] not in KNOWN_FACT_KEYS or p['language'] not in LANGUAGES:raise C14Error('c14_unknown_proposal_scope')
        if type(p['proposed_value']) not in (str,bool):raise C14Error('c14_proposal_value_invalid')
        if p['fact_key'] in ('fact:decision_notice_date','fact:appeal_submission_date') and _canonical_date(p['proposed_value']) is None:
            raise C14Error('c14_proposal_date_invalid')
        key=(p['document_ref'],p['locator']); item=segments.get(key)
        if item is None:raise C14Error('c14_proposal_document_unknown')
        raw_hash,txt_hash,txt=item
        if p['document_sha256']!=raw_hash or p['segment_sha256']!=txt_hash:raise C14Error('c14_proposal_hash_mismatch')
        start,end=p['start'],p['end']
        if type(start) is not int or type(end) is not int or start<0 or start>=end or end>len(txt) or end-start>400:
            raise C14Error('c14_proposal_offset_invalid')
        if txt[start:end]!=p['quote']:raise C14Error('c14_proposal_quote_not_anchored')
        if type(p['explanation']) is not str or len(p['explanation'])>600:
            raise C14Error('c14_proposal_explanation_invalid')
        checked.append({'source_verified':True,'semantic_status':'requires_human_review','reviewer_identity':'not_verified',**p})
    return checked


def load_topic_lexicon(root=ROOT):
    obj=load_json(root/'references/evidence/c14-topic-lexicon.json')
    if obj.get('lexicon_version')!='0.1.0' or obj.get('scope')!='untyped_passage_discovery_for_human_or_model_review_only':
        raise C14Error('wrong_topic_lexicon_version_or_scope')
    compiled=[];seen=set()
    for rule in obj['filters']:
        if set(rule)!={'id','fact_key','all_of'}:raise C14Error('invalid_topic_rule_keys')
        if rule['id'] in seen or rule['fact_key'] not in KNOWN_FACT_KEYS or not (1<=len(rule['all_of'])<=4):
            raise C14Error('invalid_topic_rule')
        seen.add(rule['id'])
        if any(len(p)>300 for p in rule['all_of']):raise C14Error('unbounded_topic_expression')
        compiled.append((rule,[re.compile(p,re.IGNORECASE | re.UNICODE) for p in rule['all_of']]))
    return compiled,digest_obj(obj)


def retrieve_review_targets(documents, lexicon):
    """Find topical passages for open-ended model/human interpretation.

    No `reported_value`: retrieval is neither polarity classification nor evidence.
    Keep all citations reconstructible from the extracted (not raw-byte) text.
    """
    targets=[]
    for doc in documents:
        for locator,text in doc['segments']:
            # Keep sentence-scale spans; do not join unrelated documents or pages.
            for m in re.finditer(r'[^\n.!?;]+(?:[.!?;]|$)',text):
                sample=m.group().strip()
                if not sample:continue
                if len(sample)>400:continue
                start=text.find(sample,m.start(),m.end())
                end=start+len(sample)
                for rule,all_of in lexicon:
                    if all(p.search(sample) for p in all_of):
                        if len(targets)>=300:raise C14Error('topic_candidate_budget_exceeded')
                        targets.append({'target_id':'c14:topic:%04d'%(len(targets)+1),
                                        'fact_key':rule['fact_key'],'document_ref':doc['document_ref'],
                                        'document_sha256':doc['sha256'], 'locator':locator,
                                        'segment_sha256':sha(text.encode('utf-8')),
                                        'start':start,'end':end,'quote':sample,
                                        'topic_id':rule['id'],'interpretation_status':'requires_interpretation_review',
                                        'proposed_value':None,
                                        'authenticity_status':'not_authenticated','fact_truth_status':'not_determined'})
    return targets
