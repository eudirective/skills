#!/usr/bin/env python3
"""Capture Luxembourg sources, using the official Casemates ELI XML route for laws."""
from __future__ import annotations
import hashlib,json,re,sys,time,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from datetime import date,datetime,timezone
from io import BytesIO
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import sync_candidate_pages as generic
PACK=Path(__file__).resolve().parent;ROOT=PACK.parents[1]
MANIFEST=PACK/'references/candidate-manifest.json';CAP=PACK/'references/luxembourg-captures.json'
MAX_BYTES=24*1024*1024;TIMEOUT=25;DELAY=1.0
UA='eudirective-source-library/1.0 (public-source review; eudirective@proton.me)'
AKN='http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD13'
STRUCT={'part','chapter','section','subsection','subsubsection','article','paragraph','point','subpoint','item','list','ol','ul','li','alinea','p','content','block','table','tr','td','th'}
def sha(b):return hashlib.sha256(b).hexdigest()
def local(tag):return tag.rsplit('}',1)[-1]
def text(node):return re.sub(r'\s+',' ',''.join(node.itertext())).strip()
def fetch_xml(url,hosts):
 u=urllib.parse.urlparse(url)
 if u.scheme!='https' or (u.hostname or '').lower() not in hosts:raise ValueError('content-negotiation URL outside allowlist')
 op=urllib.request.build_opener(generic.Redirect(hosts));req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/xml'})
 with op.open(req,timeout=TIMEOUT) as r:
  final=r.geturl();f=urllib.parse.urlparse(final)
  if f.scheme!='https' or (f.hostname or '').lower() not in hosts:raise ValueError('final XML URL outside allowlist')
  raw=r.read(MAX_BYTES+1)
  if len(raw)>MAX_BYTES:raise ValueError('XML response exceeds 24 MiB cap')
  ctype=r.headers.get_content_type().lower()
  if ctype not in {'application/xml','text/xml'} or not raw.lstrip().startswith(b'<?xml'):raise ValueError(f'Expected LegalDocML XML, received {ctype}')
  return raw,final,ctype

def xml_body(root):
 body=next((x for x in root.iter() if local(x.tag)=='body'),None)
 if body is None:raise ValueError('LegalDocML response has no body')
 lines=[]
 def add(value=''):
  value=re.sub(r'\s+',' ',value).strip()
  if value:lines.append(value)
 def walk(node,level=2):
  name=local(node.tag)
  if name in {'section','part','chapter','subsection','subsubsection'}:
   num=next((text(c) for c in node if local(c.tag)=='num'), '')
   heading=next((text(c) for c in node if local(c.tag)=='heading'), '')
   add('#'*min(level,5)+' '+(' '.join(x for x in (num,heading) if x)))
   for c in node:
    if local(c.tag) not in {'num','heading','meta','notes'}:walk(c,level+1)
  elif name=='article':
   num=next((text(c) for c in node if local(c.tag)=='num'), '')
   heading=next((text(c) for c in node if local(c.tag)=='heading'), '')
   add('### '+('Art. '+num if num else 'Article')+(' — '+heading if heading else ''))
   for c in node:
    if local(c.tag) in {'num','heading','meta','notes'}:continue
    if local(c.tag) in {'paragraph','point','subpoint','item','alinea','p','content','block','table','ol','ul','list'}:
     val=text(c)
     if val:add(val)
     elif len(c):
      for child in c:walk(child,level+1)
    else:walk(c,level+1)
  elif name in {'paragraph','point','subpoint','item','alinea','p','content','block','td','th','li'}:
   val=text(node)
   if val:add(val)
   else:
    for c in node:walk(c,level+1)
  elif name in {'meta','notes','note','noteRef','proprietary','identification'}:return
  else:
   for c in node:walk(c,level+1)
 for child in body:
  if local(child.tag) not in {'meta','notes'}:walk(child,2)
 out=[]
 for line in lines:
  if line or (out and out[-1]):out.append(line)
 result='\n\n'.join(out).strip()
 if len(result)<100:raise ValueError(f'LegalDocML body unexpectedly short ({len(result)} characters)')
 return result

def render(entry,received,resolved,ctype,digest,body):
 v=entry.get('version_evidence') or entry.get('verification_status') or 'No version evidence in candidate manifest.'
 lines=[f"# {entry['title']}",'','- Jurisdiction: Luxembourg',f"- Candidate ID: `{entry['id']}`",f"- Source type: `{entry.get('source_type','official_source_candidate')}`",f"- Candidate URL: {entry['url']}",f"- Retrieved representation: {resolved}",f"- Retrieved: {received}",f"- Media type: `{ctype}`",f"- Publisher/version evidence: {v}",'- Representation: Casemates content-negotiated LegalDocML XML',f"- Exact response SHA-256: `{digest}`",'', '> **Review candidate.** Not accepted into the trusted source corpus. Legilux notes that consolidated texts are documentary and have no legal force; verify the authentic Mémorial act, amendments, version, and reuse conditions before reliance.','','## Captured legal text','',body,'']
 return ('\n'.join(lines).rstrip()+'\n').encode()
def eligible(entry):return urllib.parse.urlparse(entry['url']).hostname=='legilux.public.lu' and '/eli/' in urllib.parse.urlparse(entry['url']).path

def capture_legilux(entry,hosts,prior):
 original=urllib.parse.urlparse(entry['url']);url=urllib.parse.urlunparse(('https','data.legilux.public.lu',original.path,original.params,original.query,original.fragment))
 raw,resolved,ctype=fetch_xml(url,hosts);digest=sha(raw);name=generic.slug(entry['id']);rawrel=f'temp/luxembourg/raw/{name}-{digest}.xml';generic.save(rawrel,raw)
 # Existing shell-only captures do not contain a converted source text; replace them with the official XML candidate.
 changed=bool(prior and prior.get('candidate_text_path') and prior.get('source_sha256')!=digest)
 output=f'source-library/luxembourg/candidates/{name}.md'
 if changed:output=f'temp/luxembourg/pending/{name}-{digest[:16]}.md'
 root=ET.fromstring(raw);body=xml_body(root);received=datetime.now(timezone.utc).isoformat(timespec='seconds');md=render(entry,received,resolved,ctype,digest,body);generic.atomic(generic.inside(output),md)
 return {'candidate_id':entry['id'],'source_url':entry['url'],'resolved_url':resolved,'retrieved_at':received,'source_content_type':ctype,'source_bytes':len(raw),'source_sha256':digest,'raw_path':rawrel,'candidate_text_path':output,'converted_sha256':sha(md),'converted_bytes':len(md),'content_selector':'LegalDocML body; structural section/article conversion','representation_type':'legaldocml_xml','retrieval_status':'changed_review_candidate' if changed else 'converted_review_candidate','review_state':'changed_pending_review' if changed else 'review_candidate','accepted':False}

def sync():
 m=json.loads(MANIFEST.read_text(encoding='utf8'));key,entries=generic.get_entries(m);hosts={str(h).lower() for h in m.get('official_hosts',[])}
 hosts.add('data.legilux.public.lu')
 for e in entries:
  h=urllib.parse.urlparse(e['url']).hostname
  if h:hosts.add(h.lower())
 prior_data=json.loads(CAP.read_text(encoding='utf8')) if CAP.exists() else json.loads((PACK/'references/luxembourg-capture-results.json').read_text(encoding='utf8')) if (PACK/'references/luxembourg-capture-results.json').exists() else {'records':[]}
 results=[]
 for i,e in enumerate(entries):
  print('retrieving',e['id'],flush=True);prior=generic.old_record(prior_data,e['id'])
  try:r=capture_legilux(e,hosts,prior) if eligible(e) else generic.capture('luxembourg',e,hosts,prior)
  except Exception as exc:r={'candidate_id':e['id'],'source_url':e.get('url'),'retrieval_status':'retrieval_or_conversion_error','retrieval_note':f'{type(exc).__name__}: {exc}','accepted':False};print('review',e['id'],r['retrieval_note'],flush=True)
  results.append(r)
  if i<len(entries)-1:time.sleep(DELAY)
 byid={r['candidate_id']:r for r in results}
 for e in entries:
  r=byid[e['id']];e['retrieved']=bool(r.get('source_sha256'));e['accepted']=False;e['retrieval_status']=r['retrieval_status']
  for k in ('candidate_text_path','candidate_source_path','source_sha256','converted_sha256','source_bytes','resolved_url','retrieval_note'):
   if k in r:e[k]=r[k]
 counts={}
 for r in results:counts[r['retrieval_status']]=counts.get(r['retrieval_status'],0)+1
 m['status']='partially_retrieved_review_candidates';m['accepted_source_count']=0;m['candidate_source_count']=len(entries);m['retrieved_review_candidate_count']=sum(bool(r.get('source_sha256')) for r in results);m['converted_review_candidate_count']=sum(bool(r.get('candidate_text_path')) for r in results)
 m['retrieval_status']=f"{m['converted_review_candidate_count']} HTML/LegalDocML texts converted; {counts.get('official_pdf_preserved_text_extraction_unavailable',0)} PDFs preserved without text extraction; {counts.get('discovery_surface_no_text',0)} portal surfaces had no text; failures are recorded per item; no source accepted"
 cap={'jurisdiction':'Luxembourg','as_of_date':date.today().isoformat(),'method':'Ordinary allowlisted HTTPS GET. Legal texts use the official Casemates ELI content-negotiation endpoint with Accept: application/xml; other public pages use direct HTTPS GET. No login, registration, challenge bypass or form submission.','publisher_terms':'Casemates documents CC BY 4.0 for its identified dataset/content. This does not establish reuse rights for unrelated government publishers, mission PDFs, court records or every linked page. All outputs remain review candidates.','request_policy':{'timeout_seconds':TIMEOUT,'max_response_bytes':MAX_BYTES,'delay_seconds':DELAY},'records':results,'accepted_source_count':0}
 generic.atomic(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());generic.atomic(CAP,(json.dumps(cap,ensure_ascii=False,indent=2)+'\n').encode())

def convert_pdfs():
 from pypdf import PdfReader
 m=json.loads(MANIFEST.read_text(encoding='utf8'));key,entries=generic.get_entries(m);src={e['id']:e for e in entries};cap=json.loads(CAP.read_text(encoding='utf8'))
 for r in cap['records']:
  if r.get('source_content_type')!='application/pdf' or r.get('candidate_text_path') or not r.get('raw_path'):continue
  raw=generic.inside(r['raw_path']).read_bytes();reader=PdfReader(BytesIO(raw));pages=[]
  for n,page in enumerate(reader.pages,1):pages.append(f'<!-- page {n} -->\n'+(page.extract_text() or ''))
  body='\n\n'.join(pages).strip()
  if not body:
   r['retrieval_note']='PDF preserved exactly; text layer is empty, so OCR would be required.';continue
  selector=f'PDF text extraction; {len(reader.pages)} pages';e=src[r['candidate_id']];name=generic.slug(e['id']);out=f'source-library/luxembourg/candidates/{name}.md';md=generic.render(e,'luxembourg',r['retrieved_at'],r['resolved_url'],r['source_content_type'],r['source_sha256'],selector,body);generic.atomic(generic.inside(out),md)
  r.update({'candidate_text_path':out,'converted_sha256':sha(md),'converted_bytes':len(md),'content_selector':selector,'retrieval_status':'converted_review_candidate','review_state':'review_candidate'});e.update({'candidate_text_path':out,'converted_sha256':sha(md),'retrieval_status':'converted_review_candidate'})
 counts={}
 for r in cap['records']:counts[r['retrieval_status']]=counts.get(r['retrieval_status'],0)+1
 m['retrieved_review_candidate_count']=sum(bool(r.get('source_sha256')) for r in cap['records']);m['converted_review_candidate_count']=sum(bool(r.get('candidate_text_path')) for r in cap['records']);m['retrieval_status']=f"{m['converted_review_candidate_count']} HTML/LegalDocML/PDF texts converted; {counts.get('discovery_surface_no_text',0)} portal surfaces had no text; failures are recorded per item; no source accepted"
 generic.atomic(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());generic.atomic(CAP,(json.dumps(cap,ensure_ascii=False,indent=2)+'\n').encode())
def verify():
 m=json.loads(MANIFEST.read_text(encoding='utf8'));key,entries=generic.get_entries(m);src={e['id']:e for e in entries};cap=json.loads(CAP.read_text(encoding='utf8'));errors=[]
 for r in cap['records']:
  try:
   if not r.get('raw_path'):continue
   raw=generic.inside(r['raw_path']).read_bytes()
   if sha(raw)!=r['source_sha256']:raise ValueError('source hash mismatch')
   if r.get('candidate_source_path') and sha(generic.inside(r['candidate_source_path']).read_bytes())!=r['source_sha256']:raise ValueError('PDF hash mismatch')
   if r.get('candidate_text_path'):
    e=src[r['candidate_id']]
    if r.get('representation_type')=='legaldocml_xml':body=xml_body(ET.fromstring(raw));md=render(e,r['retrieved_at'],r['resolved_url'],r['source_content_type'],r['source_sha256'],body)
    else:
     ctype=r['source_content_type']
     if ctype in {'application/json','application/ld+json'}:body='```json\n'+json.dumps(json.loads(raw),ensure_ascii=False,indent=2)+'\n```';selector='formatted JSON record'
     elif ctype=='application/pdf':
      from pypdf import PdfReader
      reader=PdfReader(BytesIO(raw));body='\n\n'.join(f'<!-- page {n} -->\n'+(page.extract_text() or '') for n,page in enumerate(reader.pages,1)).strip();selector=f'PDF text extraction; {len(reader.pages)} pages'
     else:
      parser=generic.Region();parser.feed(raw.decode('utf8','replace'));body=parser.text();selector=parser.selector or 'no primary region'
     md=generic.render(e,'luxembourg',r['retrieved_at'],r['resolved_url'],ctype,r['source_sha256'],selector,body)
    if sha(md)!=r['converted_sha256'] or sha(generic.inside(r['candidate_text_path']).read_bytes())!=r['converted_sha256']:raise ValueError('deterministic conversion replay mismatch')
   print('verified',r['candidate_id'])
  except Exception as exc:errors.append(f"{r.get('candidate_id')}: {exc}")
 if errors:raise SystemExit('\n'.join(errors))
def main():
 mode=sys.argv[1] if len(sys.argv)>1 else ''
 if mode=='sync':sync()
 elif mode=='verify':verify()
 elif mode=='convert-pdfs':convert_pdfs()
 else:raise SystemExit('usage: sync_luxembourg.py sync|convert-pdfs|verify')
if __name__=='__main__':main()
