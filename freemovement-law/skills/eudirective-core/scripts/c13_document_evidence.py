#!/usr/bin/env python3
"""C13 synthetic-only unstructured document evidence and typed-C12 reconciliation.

Text extraction is deterministic for pinned UTF-8/plain MIME/HTML/text-native PDF.
Observed language is a statement in a document, NOT an authenticated fact, lawful
service, a proven authority act, or a legal violation. English cue patterns are
bounded test constructions, not general-purpose NLP or legal judgments.
"""
from __future__ import annotations
from datetime import date
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
import hashlib, io, re

from contract_validate import digest_obj, load_json, validate_obj
import c14_interpretation as c14

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'references/evidence/c13-document-index.json'
PATTERNS=ROOT/'references/evidence/c13-extraction-patterns.json'
VERSION='0.2.0'
MAX_DOC_BYTES=300_000
MAX_TEXT_CHARS=80_000
MAX_SEGMENTS=30

class C13Error(Exception): pass

class _PlainHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','svg','iframe','noscript'):
            self.skip+=1
        elif tag in ('p','div','br','li','h1','h2','h3','tr') and not self.skip:
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style','svg','iframe','noscript'):
            if self.skip:self.skip-=1
        elif tag in ('p','div','li','tr') and not self.skip:self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
    def output(self):return ''.join(self.parts)


def _hash(value):return hashlib.sha256(value).hexdigest()


def parse_document(raw, fmt):
    """Return segments (locator, extracted text), warnings; refuse OCR/inference.

    Offsets refer to extracted Unicode text of the identified segment; for PDF
    that is PyMuPDF-extracted page text, NOT original PDF byte offsets.
    """
    if len(raw)>MAX_DOC_BYTES:raise C13Error('document_byte_limit')
    if fmt in ('txt','md'):
        segments=[('text:body',raw.decode('utf-8',errors='strict'))]
    elif fmt=='html':
        p=_PlainHTML();p.feed(raw.decode('utf-8',errors='strict'))
        segments=[('html:visible_text',p.output())]
    elif fmt=='eml':
        mail=BytesParser(policy=policy.default).parsebytes(raw)
        warnings=['email_attachments_not_processed'] if mail.is_multipart() and any(p.get_content_disposition()=='attachment' for p in mail.walk()) else []
        body=mail.get_body(preferencelist=('plain','html')) if mail.is_multipart() else mail
        if body is None or body.get_content_disposition()=='attachment':
            return [], ['no_supported_email_body']
        mime=body.get_content_type()
        if mime not in ('text/plain','text/html'):return [], ['unsupported_email_body_mime']
        content=body.get_content()
        if not isinstance(content,str):return [], ['email_body_decode_failed']
        if mime=='text/html':
            p=_PlainHTML();p.feed(content);content=p.output()
        segments=[('email:body:1',content)]
    elif fmt=='pdf':
        try:
            import fitz
        except ImportError as exc:raise C13Error('pymupdf_dependency_unavailable') from exc
        with fitz.open(stream=raw,filetype='pdf') as pdf:
            if pdf.needs_pass:raise C13Error('password_protected_pdf')
            if pdf.page_count>MAX_SEGMENTS:raise C13Error('pdf_page_limit')
            segments=[('pdf:page:'+str(i+1),p.get_text('text',sort=True)) for i,p in enumerate(pdf)]
        if not any(text.strip() for _,text in segments):
            return [], ['text_not_extractable_ocr_required']
    else:raise C13Error('unsupported_document_format:'+str(fmt))
    if len(segments)>MAX_SEGMENTS:raise C13Error('too_many_document_segments')
    if sum(len(t) for _,t in segments)>MAX_TEXT_CHARS:raise C13Error('document_extracted_text_limit')
    return segments,warnings if fmt=='eml' else []


def documents_for_case(case,evidence_set,*,root=ROOT,registry=None):
    if evidence_set is None:return [],None
    validate_obj('c13-evidence-set',evidence_set)
    if case['privacy_classification']!='synthetic':raise C13Error('c13_synthetic_only')
    registry=registry or load_json(root/'references/evidence/c13-document-index.json')
    if registry.get('index_version')!='0.1.0':raise C13Error('document_index_version_mismatch')
    items={}
    for item in registry.get('documents',[]):
        ident=item['document_ref']
        if ident in items:raise C13Error('duplicate_document_ref')
        items[ident]=item
    chosen=[];seen=set();scenario=case['case_id'].split('-')[-1]
    for ident in evidence_set['document_refs']:
        if ident in seen:raise C13Error('duplicate_case_document')
        seen.add(ident);entry=items.get(ident)
        if not entry or entry['case_fixture']!=scenario:
            raise C13Error('missing_or_cross_case_document:'+ident)
        rel=PurePosixPath(entry['relative_path'])
        if rel.is_absolute() or '..' in rel.parts or not str(rel).startswith('references/fixtures/c13/documents/'):
            raise C13Error('unsafe_registry_relative_path')
        path=root.joinpath(*rel.parts)
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise C13Error('missing_document_bytes:'+ident)
        raw=path.read_bytes()
        if _hash(raw)!=entry['sha256']:raise C13Error('modified_document_bytes:'+ident)
        segments,warnings=parse_document(raw,entry['format'])
        chosen.append({'document_ref':ident,'sha256':entry['sha256'],'format':entry['format'],
                       'declared_source_kind':entry['declared_source_kind'],
                       'segments':segments,'warnings':warnings})
    return chosen,digest_obj(registry)


def patterns_verified(*,root=ROOT):
    obj=load_json(root/'references/evidence/c13-extraction-patterns.json')
    if obj.get('patterns_version')!='0.1.0':raise C13Error('incorrect_c13_patterns_version')
    prepared=[];seen=set()
    for p in obj['patterns']:
        if set(p)-{'pattern_id','fact_key','pattern','extractor','value','source_interpretation'}:
            raise C13Error('unknown_pattern_field')
        if p['pattern_id'] in seen:raise C13Error('duplicate_pattern_id')
        seen.add(p['pattern_id'])
        if not p['fact_key'].startswith(('fact:','element:')):raise C13Error('invalid_pattern_fact_prefix')
        if p['extractor'] not in ('literal','capture_date') or len(p['pattern'])>350:
            raise C13Error('unbounded_or_unsupported_pattern')
        if p['extractor']=='literal' and type(p.get('value')) not in (str,int,bool):
            raise C13Error('incorrect_literal_pattern')
        if p['source_interpretation']!='reported_statement_only':raise C13Error('pattern_claims_unearned_authenticity')
        try: reg=re.compile(p['pattern'])
        except re.error as exc:raise C13Error('invalid_pattern_regex:'+p['pattern_id']) from exc
        if p['extractor']=='capture_date' and 'date' not in reg.groupindex:
            raise C13Error('missing_date_capture')
        prepared.append((p,reg))
    return prepared,digest_obj(obj)


def observe(documents,patterns):
    observations=[]
    for doc in documents:
        for locator,text in doc['segments']:
            for p,regex in patterns:
                for match in regex.finditer(text):
                    if len(observations)>=350:raise C13Error('observation_budget_exceeded')
                    value=p.get('value')
                    if p['extractor']=='capture_date':
                        value=match.group('date')
                        try:
                            if date.fromisoformat(value).isoformat()!=value:continue
                        except ValueError:continue
                    obs={'observation_id':'c13:observation:%04d'%(len(observations)+1),
                         'fact_key':p['fact_key'],'reported_value':value,
                         'document_ref':doc['document_ref'], 'document_sha256':doc['sha256'],
                         'locator':locator,'segment_sha256':_hash(text.encode('utf-8')),
                         'start':match.start(),'end':match.end(),
                         'quote':text[match.start():match.end()], 'pattern_id':p['pattern_id'],
                         'evidence_assurance':'bytes_pinned_passage_anchored_statement_only',
                         'authenticity_status':'not_authenticated','fact_truth_status':'not_determined'}
                    # Independent, exact character offset verification; no trust in untested substring pointers.
                    if text[obs['start']:obs['end']]!=obs['quote']:
                        raise C13Error('internal_quote_anchor_failure')
                    observations.append(obs)
    return sorted(observations,key=lambda x:(x['fact_key'],x['document_ref'],x['locator'],x['start'],x['pattern_id']))


def _typed_equal(a,b):return type(a)==type(b) and a==b


def reconcile(c12_report,observations):
    grouped={}
    for o in observations:grouped.setdefault(o['fact_key'],[]).append(o)
    fact_checks=[]; rule_links=[];unresolved=[]
    for a in c12_report['assessments']:
        if a['status']=='not_applicable':
            rule_links.append({'assessment_id':a['assessment_id'],'status':'not_applicable','blocking_fact_keys':[]})
            continue
        blocked=[]
        for pred in a['predicate_results']:
            key=pred['fact_key']
            if key.startswith('case:'):continue
            observed=grouped.get(key,[])
            values=[]
            for o in observed:
                if not any(_typed_equal(o['reported_value'],v) for v in values):values.append(o['reported_value'])
            expected=pred['value']
            if not observed:status='not_observed_in_documents'
            elif len(values)>1:status='conflicting_document_statements'
            elif expected is None:status='upstream_value_missing'
            elif _typed_equal(values[0],expected):status='document_statement_matches_upstream_value'
            else:status='document_statement_contradicts_upstream_value'
            if status!='document_statement_matches_upstream_value':
                blocked.append(key)
                unresolved.append(key+':'+status)
            fact_checks.append({'assessment_id':a['assessment_id'],'fact_key':key,
                                'c12_value':expected,'document_reported_values':values,
                                'observation_ids':[x['observation_id'] for x in observed],
                                'status':status, 'fact_truth_status':'not_determined'})
        if a['status']!='supported_for_review':
            overall='requires_document_and_rule_review'
            if not blocked:blocked.append('c12_prerequisites_'+a['status'])
        else:overall='passage_anchored_for_review' if not blocked else 'requires_document_and_rule_review'
        rule_links.append({'assessment_id':a['assessment_id'],'status':overall,'blocking_fact_keys':sorted(set(blocked))})
    return fact_checks,rule_links,sorted(set(unresolved))


def build(case,elements,c12_report,evidence_set=None):
    # Keep old C6 fixtures runnable without implied documentary scrutiny.
    base={'engine_version':VERSION,'case_id':case['case_id'],'mode':'not_enrolled' if evidence_set is None else 'enrolled',
          'legal_violation_status':'not_determined',
          'bindings':{'case_sha256':digest_obj(case),'elements_sha256':digest_obj(elements),
                      'c12_sha256':digest_obj(c12_report),'evidence_set_sha256':digest_obj(evidence_set) if evidence_set else None,
                      'document_index_sha256':None,'pattern_catalog_sha256':None,'c14_grammar_sha256':None,'c14_topic_sha256':None},
          'documents':[], 'observations':[], 'c14_interpretation_candidates':[], 'c14_review_targets':[], 'fact_checks':[],'rule_links':[], 'unresolved':[],
          'limitations':['C13 is not legal-merits review, document authentication, or independent confirmation of factual truth.',
             'Only pinned synthetic documents; actual applicant files and network access are forbidden.',
             'Legacy C13 cues are narrow English heuristics; absence never establishes lawful conduct.',
             'C14 multilingual interpretations are unreviewed suggestions, excluded from documentary reconciliation and legal findings.',
             'All evidence statements require interpretative and provenance review.']}
    if evidence_set is None:
        base['unresolved'].append('C13 raw-document review not enrolled; C12 synthetic surrogate results cannot stand in for authentic evidence.')
        validate_obj('c13-evidence-assessment',base)
        return base
    validate_obj('c13-evidence-set',evidence_set)
    if evidence_set['case_sha256']!=digest_obj(case) or evidence_set['elements_sha256']!=digest_obj(elements):
        raise C13Error('unbound_c13_evidence_set')
    docs,idx_digest=documents_for_case(case,evidence_set)
    patterns,pattern_digest=patterns_verified()
    obs=observe(docs,patterns)
    c14_grammar,c14_digest=c14.load_grammar()
    c14_candidates=c14.extract_candidates(docs,c14_grammar)
    c14_issues=c14.resolve_candidate_issues(c14_candidates,obs)
    c14_topics,c14_topic_digest=c14.load_topic_lexicon()
    c14_targets=c14.retrieve_review_targets(docs,c14_topics)
    legacy_keys={x['fact_key'] for x in obs}
    c14_issues += ['c14:open_topic_requires_interpretation:'+k for k in sorted({x['fact_key'] for x in c14_targets}) if k not in legacy_keys]
    checks,rule_links,unresolved=reconcile(c12_report,obs)
    unresolved.extend(c14_issues)
    extraction_gaps=sorted({d['document_ref']+':'+w for d in docs for w in d['warnings']})
    if extraction_gaps:
        # An unreadable selected document may contain decisive contrary material.
        # Do not silently accept a different passage as the complete record.
        for link in rule_links:
            if link['status']=='passage_anchored_for_review':
                link['status']='requires_document_and_rule_review'
                link['blocking_fact_keys'].append('unprocessed_selected_document_material')
        unresolved.extend('extractor_gap:'+x for x in extraction_gaps)
    base['bindings']['document_index_sha256']=idx_digest
    base['bindings']['pattern_catalog_sha256']=pattern_digest
    base['bindings']['c14_grammar_sha256']=c14_digest
    base['bindings']['c14_topic_sha256']=c14_topic_digest
    base['c14_interpretation_candidates']=c14_candidates
    base['c14_review_targets']=c14_targets
    base['documents']=[{'document_ref':d['document_ref'],'format':d['format'],
                        'declared_source_kind':d['declared_source_kind'],
                        'sha256':d['sha256'],'extraction_warnings':d['warnings'],
                        'segments':[{'locator':loc,'segment_sha256':_hash(t.encode('utf-8')),'characters':len(t)}
                                    for loc,t in d['segments']]} for d in docs]
    base['observations']=obs
    base['fact_checks']=checks
    base['rule_links']=rule_links
    base['unresolved']=sorted(set(unresolved))
    validate_obj('c13-evidence-assessment',base)
    return base


def render(report):
    lines=['# C13 documentary evidence assessment — fictional development case','',
           '**No document authenticated; no legal violation or factual truth established.**','',
           '- Case: `'+report['case_id']+'`','- C13 enrollment: `'+report['mode']+'`','',
           '## Document bytes and extraction status','']
    for d in report['documents']:
        lines.append('- `'+d['document_ref']+'`: '+d['format']+' / '+d['declared_source_kind']+' SHA-256 `'+d['sha256']+'`, '
                     +str(len(d['segments']))+' extracted segment(s); '+(', '.join(d['extraction_warnings']) or 'no extraction warnings')+'.')
    lines+=['','## Exact passage-anchored statements (not facts)','']
    for o in report['observations']:
        lines.append('- `'+o['observation_id']+'` '+o['fact_key']+' = `'+repr(o['reported_value'])+'`; '
                     +o['document_ref']+' `'+o['locator']+'` ['+str(o['start'])+':'+str(o['end'])+']: '
                     +repr(o['quote']))
    lines+=['','## C14 multilingual interpretation candidates — NOT corroborated','']
    for v in report['c14_interpretation_candidates']:
        lines.append('- `'+v['candidate_id']+'` ('+v['language']+', '+v['grammar_id']+') '+v['fact_key']+' => `'+repr(v['proposed_value'])+'`; '+v['document_ref']+' `'+v['locator']+'` ['+str(v['start'])+':'+str(v['end'])+']: '+repr(v['quote'])+'; '+(', '.join(v['cautions']) or 'no detected qualification')+'; **human meaning review required**.')
    lines+=['','## C14 open-ended review targets — UNKNOWN proposition and polarity','']
    for v in report['c14_review_targets']:
        lines.append('- `'+v['target_id']+'` '+v['fact_key']+' / '+v['topic_id']+'; '+v['document_ref']+' `'+v['locator']+'` ['+str(v['start'])+':'+str(v['end'])+']: '+repr(v['quote'])+'; **NO VALUE assigned: reviewer required**.')
    lines+=['','## Rule evidence checks','']
    for x in report['rule_links']:
        lines.append('- `'+x['assessment_id']+'`: `'+x['status']+'`'+(' — '+', '.join(x['blocking_fact_keys']) if x['blocking_fact_keys'] else '')+'.')
    lines+=['','## Unresolved limitations','']
    lines.extend('- '+v for v in report['unresolved'])
    lines.extend('- '+v for v in report['limitations'])
    lines+=['','**C13 is a bounded offline extraction-and-trace audit, not a legal-evidence adjudicator.**','']
    return '\n'.join(lines).encode('utf-8')
