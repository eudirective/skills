#!/usr/bin/env python3
"""C15 synthetic-only model-proposal casework; deterministic provenance verification.

No LLM API is called here. A language model or analyst interprets prepared evidence
and writes an explicit, untrusted proposal JSON. This verifier checks provenance
and workflow contracts, NOT entailment, original authorship or legal correctness.
The C7/C6 controller allowlist is not modified or bypassed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path, PurePosixPath

from contract_validate import load_json, digest_obj
from c13_document_evidence import parse_document
from verify_bundled_source_pack import inspect as inspect_source_pack
from source_library_paths import compatibility_root

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'references/fixtures/c15/pilot-01/manifest.json'
PACK=compatibility_root()
MANIFEST_SHA256='bd8e183bf89277fb0a57697f1af63b48b715885e011462b97693f2ae2546e257'
VERSION='0.1.0'
MAX_FACTS=80
MAX_QUESTIONS=25
MAX_PROPOSAL_BYTES=120_000

class C15Error(ValueError):pass

def hash_bytes(v):return hashlib.sha256(v).hexdigest()
def dump(obj):return json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
def ensure(cond, reason):
    if not cond: raise C15Error(reason)

def exact_fields(obj, fields, reason):
    ensure(isinstance(obj,dict) and set(obj)==set(fields),reason)

def safe_bundled_path(rel,prefix,root=ROOT):
    ensure(isinstance(rel,str) and len(rel)<250,'invalid_relative_path')
    p=PurePosixPath(rel)
    ensure(not p.is_absolute() and '..' not in p.parts and rel.startswith(prefix),'unapproved_relative_path')
    path=root.joinpath(*p.parts)
    ensure(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),'unsafe_or_absent_bundled_file')
    return path

def pinned_fixture():
    raw=PILOT.read_bytes()
    ensure(hash_bytes(raw)==MANIFEST_SHA256,'c15_pilot_manifest_integrity_mismatch')
    m=load_json(PILOT)
    exact_fields(m,['manifest_version','case_id','classification','legal_merits','documents','restrictions'],'c15_manifest_keys')
    ensure(m['manifest_version']==VERSION and m['case_id']=='CASE-C15-PILOT-01' and m['classification']=='synthetic' and m['legal_merits']=='not_determined','c15_unapproved_case')
    ensure(len(m['documents'])==14,'c15_enrolled_document_count_changed')
    return m

def source_manifest():
    result=inspect_source_pack()
    ensure(result.get('status')=='verified_locally_complete','c15_source_pack_incomplete')
    data=load_json(PACK/'core-source-pack-manifest-0.6.1.json')
    sources={x['source_id']:x for x in data['sources']}
    ensure(len(sources)==46,'c15_source_registry_count_changed')
    return data,sources

def build_case_index():
    manifest=pinned_fixture()
    docs=[]
    for item in manifest['documents']:
        exact_fields(item,['document_id','format','relative_path','bytes','sha256','declared_role'],'invalid_c15_document_registry')
        p=safe_bundled_path(item['relative_path'],'references/fixtures/c15/pilot-01/documents/')
        raw=p.read_bytes()
        ensure(len(raw)==item['bytes'] and hash_bytes(raw)==item['sha256'],'c15_document_bytes_changed:'+item['document_id'])
        segments,warnings=parse_document(raw,item['format'])
        ensure(segments and all(t.strip() for _,t in segments),'c15_unextractable_document:'+item['document_id'])
        docs.append({'document_id':item['document_id'],'declared_role':item['declared_role'],
                     'sha256':item['sha256'],'format':item['format'], 'relative_path':item['relative_path'],
                     'segments':[{'locator':loc,'sha256':hash_bytes(t.encode('utf-8')),'text':t} for loc,t in segments],
                     'warnings':warnings,'authenticity':'not_authenticated','truth':'not_determined'})
    ensure(len({d['document_id'] for d in docs})==len(docs),'c15_duplicate_documents')
    return {'pipeline_version':VERSION,'case_id':manifest['case_id'],'synthetic_only':True,
            'manifest_sha256':hash_bytes(PILOT.read_bytes()),'documents':docs,
            'limitations':['Documents are fictional and authorship is not authenticated.',
                           'Extracted words are not factual truths or legal conclusions.',
                           'This C15 lane is not a C6 release or a C7 approved new controller case.']}

def read_case_index(path):
    obj=load_json(path)
    expected=build_case_index()
    ensure(obj==expected,'c15_case_index_not_identical_to_pinned_fixture')
    return obj

def save_new(path,value):
    ensure(not path.exists(),'output_already_exists')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value,encoding='utf-8')

def prep(args):
    out=Path(args.output_dir)
    ensure(not out.exists() or (out.is_dir() and not any(out.iterdir())),'output_dir_not_empty')
    index=build_case_index();out.mkdir(parents=True,exist_ok=True)
    save_new(out/'case-index.json',dump(index))
    text=['# C15 fictional evidence dossier','',
          'Skill: eudirective-core v0.28.0','',
          'This is a fictional dossier. Content is evidence of statements, not independently verified facts.','']
    for doc in index['documents']:
        text.extend(['## '+doc['document_id']+' ('+doc['declared_role']+')',
                     'SHA-256: `'+doc['sha256']+'`',''])
        for s in doc['segments']:
            text.extend(['Locator: `'+s['locator']+'` (character offsets in extracted text):','',
                         '```text',s['text'].rstrip(),'```',''])
    save_new(out/'case-context.md','\n'.join(text)+'\n')
    print(dump({'status':'prepared_synthetic_only','document_count':len(index['documents']),
                'index_digest':digest_obj(index),'output_dir':str(out)}))

def source_text(record):
    reps=record['representations']
    rep=next((r for r in reps if r['kind']=='bundled_text'),None)
    if rep is None:rep=next((r for r in reps if r['kind']=='verified_source_note'),None)
    ensure(rep is not None,'source_has_no_usable_representation')
    p=safe_bundled_path(rep['relative_path'],'sources/',PACK)
    b=p.read_bytes()
    ensure(len(b)==rep['bytes'] and hash_bytes(b)==rep['sha256'],'c15_source_hash_invalid')
    text=b.decode('utf-8',errors='strict')
    return rep,text

def candidate_windows(content,term,max_len=800):
    # Lexical shortlist for model research, never a semantic or legal verdict.
    for m in re.finditer(re.escape(term),content,re.IGNORECASE):
        s=max(0,m.start()-240);e=min(len(content),m.end()+400)
        if e-s>max_len:e=s+max_len
        yield s,e,content[s:e]

def retrieve(args):
    idx=read_case_index(Path(args.index))
    data,sources=source_manifest()
    req=load_json(Path(args.requests))
    exact_fields(req,['query_version','queries'],'invalid_c15_query_envelope')
    ensure(req['query_version']==VERSION and isinstance(req['queries'],list) and 1<=len(req['queries'])<=15,'c15_bad_query_count')
    outputs=[];seen_q=set()
    for query in req['queries']:
        exact_fields(query,['query_id','source_ids','terms'],'invalid_c15_query_fields')
        qid=query['query_id']
        ensure(isinstance(qid,str) and re.fullmatch('[a-z][a-z0-9-]{1,30}',qid) and qid not in seen_q,'c15_invalid_query_id')
        seen_q.add(qid)
        ids=query['source_ids'];terms=query['terms']
        ensure(isinstance(ids,list) and 1<=len(ids)<=5 and len(set(ids))==len(ids) and set(ids)<=set(sources),'c15_invalid_query_source_scope')
        ensure(isinstance(terms,list) and 1<=len(terms)<=5 and all(isinstance(x,str) and 3<=len(x)<=60 and re.search('[A-Za-z0-9]',x) for x in terms),'c15_invalid_query_terms')
        hits=[]
        for sid in ids:
            rep,content=source_text(sources[sid]);seen_spans=set();candidates=[]
            for term in terms:
                for start,end,t in candidate_windows(content,term):
                    if (start,end) in seen_spans:continue
                    seen_spans.add((start,end))
                    score=sum(1 for tt in terms if tt.casefold() in t.casefold())
                    candidates.append((score,start,end,t))
            candidates.sort(key=lambda x:(-x[0],x[1]))
            for score,start,end,t in candidates[:5]:
                hits.append({'query_id':qid,'source_id':sid,
                     'relative_path':rep['relative_path'],'kind':rep['kind'],'source_sha256':rep['sha256'],
                     'text_start':start,'text_end':end,'excerpt':t,'term_hits':score,
                     'pinpoint_verified':False,'official_currentness_checked':False})
        outputs.append({'query_id':qid,'terms':terms,'source_ids':ids,'hits':hits,
                        'status':'retrieved_local_text' if hits else 'no_local_match'})
    obj={'pipeline_version':VERSION,'case_id':idx['case_id'],'case_index_sha256':digest_obj(idx),
         'source_manifest_sha256':digest_obj(data),'queries':outputs,
         'scope':'local_text_retrieval_only_no_legal_entailment'}
    save_new(Path(args.output),dump(obj))
    print(dump({'status':'retrieval_complete','queries':len(outputs),'hits':sum(len(x['hits']) for x in outputs),'sha256':digest_obj(obj)}))

def load_retrieval(path,idx):
    obj=load_json(path)
    ensure(obj['case_index_sha256']==digest_obj(idx) and obj['case_id']==idx['case_id'] and obj['pipeline_version']==VERSION,'c15_retrieval_case_binding_failed')
    manifest,sources=source_manifest()
    ensure(obj['source_manifest_sha256']==digest_obj(manifest),'c15_retrieval_source_manifest_changed')
    for q in obj['queries']:
        for h in q['hits']:
            sid=h['source_id'];ensure(sid in sources and h['query_id']==q['query_id'] and sid in q['source_ids'],'c15_retrieval_scope_forgery')
            rep,text=source_text(sources[sid]);a,b=h['text_start'],h['text_end']
            ensure(type(a)==int and type(b)==int and 0<=a<b<=len(text),'c15_retrieval_invalid_offset')
            ensure(text[a:b]==h['excerpt'] and rep['sha256']==h['source_sha256'] and rep['relative_path']==h['relative_path'] and rep['kind']==h['kind'],'c15_retrieval_hash_or_quote_forgery')
    return obj,sources

ATTRIBUTIONS={'applicant_assertion':{'applicant_statement','applicant_correspondence'},
              'purported_official_statement':{'purported_official_message','purported_official_guidance'},
              'provider_record':{'provider_receipt','provider_generic_checklist','provider_eu_family_guidance'},
              'third_party_statement':{'housing_statement'},
              'reported_statement':{'applicant_statement','applicant_correspondence','housing_statement','purported_official_message','purported_official_guidance','provider_receipt','provider_generic_checklist','provider_eu_family_guidance'}}
DISPOSITIONS={'potential_concern','unresolved','no_violation_established','not_applicable','novel_unassessed'}

def anchored_quote(quote,text,start,end,why):
    ensure(isinstance(quote,str) and 10<=len(quote)<=600,'invalid_quote_length:'+why)
    ensure(type(start)==int and type(end)==int and 0<=start<end<=len(text) and end-start<=600,'invalid_quote_offsets:'+why)
    ensure(text[start:end]==quote,'quote_not_in_source_at_offsets:'+why)

def validated_proposal(idx,ret,proposal,sources):
    exact_fields(proposal,['proposal_version','case_id','case_index_sha256','retrieval_sha256','facts','legal_questions','unmapped_evidence','overall_limitations'],'invalid_c15_proposal_fields')
    ensure(proposal['proposal_version']==VERSION and proposal['case_id']==idx['case_id'] and proposal['case_index_sha256']==digest_obj(idx) and proposal['retrieval_sha256']==digest_obj(ret),'c15_proposal_identity_or_digest_mismatch')
    ensure(isinstance(proposal['facts'],list) and 1<=len(proposal['facts'])<=MAX_FACTS and isinstance(proposal['legal_questions'],list) and 1<=len(proposal['legal_questions'])<=MAX_QUESTIONS,'c15_proposal_item_bounds')
    ensure(isinstance(proposal['overall_limitations'],list) and all(isinstance(x,str) and 1<=len(x)<=400 for x in proposal['overall_limitations']),'c15_limitation_validation_failed')
    ensure(isinstance(proposal['unmapped_evidence'],list) and len(proposal['unmapped_evidence'])<=50,'c15_unmapped_validation_failed')
    docs={x['document_id']:x for x in idx['documents']};fids=set()
    for fact in proposal['facts']:
        exact_fields(fact,['id','proposition','attribution','temporal_label','evidence','qualifications'],'c15_invalid_fact_fields')
        fid=fact['id']
        ensure(isinstance(fid,str) and re.fullmatch('F[0-9]{2,3}',fid) and fid not in fids,'c15_duplicate_or_invalid_fact_id')
        fids.add(fid)
        ensure(isinstance(fact['proposition'],str) and 10<=len(fact['proposition'])<=500,'c15_invalid_fact_proposition')
        ensure(fact['attribution'] in ATTRIBUTIONS,'c15_invalid_attribution')
        label=fact['temporal_label']
        if label is not None:
            ensure(type(label)==str,'c15_temporal_label_type')
            try:ensure(date.fromisoformat(label).isoformat()==label,'c15_temporal_label_not_canonical')
            except ValueError:raise C15Error('c15_invalid_temporal_label')
        ensure(isinstance(fact['evidence'],list) and 1<=len(fact['evidence'])<=4,'c15_fact_evidence_missing')
        ensure(isinstance(fact['qualifications'],list) and all(isinstance(q,str) and len(q)<=350 for q in fact['qualifications']),'c15_fact_qualifications_invalid')
        for ev in fact['evidence']:
            exact_fields(ev,['document_id','locator','document_sha256','segment_sha256','start','end','quote'],'c15_invalid_document_anchor')
            d=docs.get(ev['document_id']);ensure(d is not None,'c15_unknown_document_ref')
            ensure(d['declared_role'] in ATTRIBUTIONS[fact['attribution']],'c15_attribution_not_from_document_role')
            ensure(ev['document_sha256']==d['sha256'],'c15_document_digest_mismatch')
            segment=next((s for s in d['segments'] if s['locator']==ev['locator']),None)
            ensure(segment is not None and segment['sha256']==ev['segment_sha256'],'c15_segment_not_bound')
            anchored_quote(ev['quote'],segment['text'],ev['start'],ev['end'],'document')
    qids=set();found_source_ids=set()
    hits=[h for q in ret['queries'] for h in q['hits']]
    for item in proposal['legal_questions']:
        exact_fields(item,['id','title','disposition','support_fact_ids','qualifying_fact_ids','legal_sources','legal_analysis','exceptions_and_counterarguments','unresolved_questions','country_law_needed','possible_next_steps'],'c15_invalid_issue_fields')
        qid=item['id'];ensure(isinstance(qid,str) and re.fullmatch('Q[0-9]{2,3}',qid) and qid not in qids,'c15_duplicate_issue_id')
        qids.add(qid)
        ensure(item['disposition'] in DISPOSITIONS,'c15_final_violation_status_forbidden')
        ensure(isinstance(item['title'],str) and len(item['title'])<=170 and isinstance(item['legal_analysis'],str) and 30<=len(item['legal_analysis'])<=1500,'c15_invalid_analysis')
        for field in ('support_fact_ids','qualifying_fact_ids'):
            ensure(isinstance(item[field],list) and len(item[field])<=15 and set(item[field])<=fids,'c15_missing_fact_cross_reference')
        for field in ('exceptions_and_counterarguments','unresolved_questions','country_law_needed','possible_next_steps'):
            ensure(isinstance(item[field],list) and len(item[field])<=15 and all(isinstance(z,str) and 0<len(z)<=500 for z in item[field]),'c15_invalid_review_questions')
        ensure(item['support_fact_ids'] or item['qualifying_fact_ids'],'c15_empty_issue_facts')
        ensure(isinstance(item['legal_sources'],list) and len(item['legal_sources'])<=8,'c15_invalid_source_citation_count')
        if not item['legal_sources']:
            ensure(item['disposition'] in ('novel_unassessed','unresolved'),'c15_no_source_cannot_assert_legal_concern')
        for cite in item['legal_sources']:
            exact_fields(cite,['source_id','source_sha256','relative_path','pinpoint_hint','start','end','quote'],'c15_invalid_legal_citation_fields')
            sid=cite['source_id'];ensure(sid in sources,'c15_unknown_eu_source')
            rep,original=source_text(sources[sid])
            ensure(cite['source_sha256']==rep['sha256'] and cite['relative_path']==rep['relative_path'],'c15_unbound_eu_source_citation')
            anchored_quote(cite['quote'],original,cite['start'],cite['end'],'eu_source')
            ensure(isinstance(cite['pinpoint_hint'],str) and 3<=len(cite['pinpoint_hint'])<=100,'c15_missing_citation_pinpoint')
            if rep['kind']=='bundled_text' and sid=='eu:32004l0038':
                m=re.fullmatch(r'Article ([0-9]+)(?:\([0-9]+\))?',cite['pinpoint_hint'])
                ensure(m is not None,'c15_directive_pinpoint_bad_syntax')
                sections=list(re.finditer(r'(?m)^Article ([0-9]+)\s*$',original[:cite['start']]))
                ensure(sections and sections[-1].group(1)==m.group(1),'c15_directive_pinpoint_wrong_article')
            ensure(any(h['source_id']==sid and h['source_sha256']==rep['sha256'] and h['text_start']<=cite['start'] and cite['end']<=h['text_end'] for h in hits),'c15_citation_not_in_retrieved_evidence')
            found_source_ids.add(sid)
            if rep['kind']=='verified_source_note':
                ensure(item['disposition'] in ('unresolved','novel_unassessed'),'c15_source_note_cannot_form_positive_concern')
    for ref in proposal['unmapped_evidence']:
        ensure(isinstance(ref,str) and ref in docs,'c15_unknown_unmapped_evidence')
    ensure(set(x['document_id'] for f in proposal['facts'] for x in f['evidence']) | set(proposal['unmapped_evidence']) == set(docs),'c15_incomplete_case_document_coverage')
    return {'fact_count':len(fids),'question_count':len(qids),'eu_sources_cited':sorted(found_source_ids),
            'document_coverage':len(docs),'document_coverage_complete':True,
            'quote_provenance':'verified_exact','semantic_entailment':'not_checked',
            'source_authenticity':'not_authenticated','independent_legal_review':'not_performed',
            'legal_violation_status':'not_determined','c6_release_status':'not_requested'}

def output_markdown(idx,proposal,assessment):
    lines=['# C15 complete-case synthetic legal assessment (review draft)', '',
           'Skill: eudirective-core v0.28.0','','**Case:** '+idx['case_id']+' (fiction only)',
           '**Verification:** exact document/source anchors checked; semantic interpretation and legal merits **not independently verified**.',
           '**No legal violation or formal remedy is established by this report.**','',
           '## Reconstructed documentary chronology (candidate)']
    for f in sorted(proposal['facts'],key=lambda x:(x['temporal_label'] or '9999',x['id'])):
        date_ = f['temporal_label'] or 'date unresolved'
        lines.extend(['',f"**{date_} | {f['id']} ({f['attribution']}):** {f['proposition']}"])
        for ev in f['evidence']:
            lines.append('- '+ev['document_id']+'/'+ev['locator']+': `'+str(ev['start'])+'-'+str(ev['end'])+'` '+json.dumps(ev['quote'],ensure_ascii=False))
        for qualifier in f['qualifications']:lines.append('- Qualification: '+qualifier)
    lines+=['','## Legal questions (unapproved merits candidates)','']
    for q in proposal['legal_questions']:
        lines.extend(['### '+q['id']+' — '+q['title'],'', '**Status: '+q['disposition']+' (requires review)**','',q['legal_analysis'],'',
                      'Support facts: '+(', '.join(q['support_fact_ids']) or 'none'),
                      'Qualifying/counter facts: '+(', '.join(q['qualifying_fact_ids']) or 'none')])
        for c in q['legal_sources']:
            lines.append('- EU source '+c['source_id']+' / '+c['relative_path']+' offsets '+str(c['start'])+'-'+str(c['end'])+ ' / '+c['pinpoint_hint']+': '+json.dumps(c['quote'],ensure_ascii=False))
        for label,field in [('Exceptions/counterarguments','exceptions_and_counterarguments'),('Missing issues','unresolved_questions'),('National-law sources needed','country_law_needed'),('Possible review actions','possible_next_steps')]:
            if q[field]:lines.append('- '+label+': '+'; '.join(q[field]))
        lines.append('')
    lines.extend(['## Source, privacy, and completeness limitations','',
                  '- All documents are invented. Hashes identify byte versions; they do not establish authorship or authenticity.',
                  '- Exact citation spans do not prove semantic entailment or current legal validity.',
                  '- 21 EU source representations are source notes, not complete texts; national source notes require primary-law checking.',
                  '- The bundled Directive 2004/38 text appears to omit part of Article 2(2); do not claim the restoration verified every substantive passage.',
                  '- C15 is a separate demonstration/review lane. It is not a controller-authoritative C6 release or a real-case intake.'])
    for item in proposal['overall_limitations']:lines.append('- '+item)
    lines.append('')
    return '\n'.join(lines)

def check(args):
    idx=read_case_index(Path(args.index))
    ret,sources=load_retrieval(Path(args.retrieval),idx)
    pp=Path(args.proposals)
    ensure(pp.stat().st_size<=MAX_PROPOSAL_BYTES,'c15_proposal_file_too_large')
    proposal=load_json(pp)
    assessment=validated_proposal(idx,ret,proposal,sources)
    v={'pipeline_version':VERSION,'case_id':idx['case_id'],'case_index_sha256':digest_obj(idx),
       'retrieval_sha256':digest_obj(ret),'proposal_sha256':digest_obj(proposal),
       'assessment':assessment,'review_state':'human_and_legal_expert_review_required',
       'no_automatic_promotion_to_c6':True}
    save_new(Path(args.output),dump(v))
    save_new(Path(args.report),output_markdown(idx,proposal,assessment))
    print(dump({'status':'anchored_review_draft','facts':assessment['fact_count'],
         'questions':assessment['question_count'],'documents':assessment['document_coverage'],
         'merits_verified':False,'output':args.output,'report':args.report}))

def main():
    parser=argparse.ArgumentParser(description='C15 fictional case: prepare, retrieve verified EU excerpts, check model/analyst proposals.')
    subs=parser.add_subparsers(dest='cmd',required=True)
    p=subs.add_parser('prepare');p.add_argument('--output-dir',required=True);p.set_defaults(func=prep)
    p=subs.add_parser('retrieve');p.add_argument('--index',required=True);p.add_argument('--requests',required=True);p.add_argument('--output',required=True);p.set_defaults(func=retrieve)
    p=subs.add_parser('verify');p.add_argument('--index',required=True);p.add_argument('--retrieval',required=True);p.add_argument('--proposals',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);p.set_defaults(func=check)
    args=parser.parse_args()
    try:args.func(args)
    except (C15Error,KeyError,ValueError,TypeError,OSError,UnicodeError) as err:parser.exit(2,'C15 verification blocked: '+str(err)+'\n')
if __name__=='__main__': main()
