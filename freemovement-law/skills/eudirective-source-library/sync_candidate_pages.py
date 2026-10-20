#!/usr/bin/env python3
"""Bounded, no-auth capture and replay for official candidate manifests."""
from __future__ import annotations
import hashlib, html, importlib.util, json, re, sys, tempfile, time, urllib.parse, urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

BASE=Path(__file__).resolve().parent; ROOT=BASE.parent
MAX_BYTES=24*1024*1024; TIMEOUT=25; DELAY=1.0
UA='eudirective-source-library/1.0 (public-source review; eudirective@proton.me)'
SKIP={'script','style','noscript','svg','nav','header','footer','form'}
BLOCK={'address','article','br','dd','div','dl','dt','h1','h2','h3','h4','h5','h6','li','ol','p','section','table','td','th','tr','ul'}
def sha(b):return hashlib.sha256(b).hexdigest()
def slug(x):return re.sub(r'[^a-z0-9]+','-',str(x).lower()).strip('-')
def inside(p):
 q=(ROOT/p).resolve()
 if not q.is_relative_to(ROOT):raise ValueError('path escapes source-library root')
 return q
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with open(fd,'wb',closefd=True) as f:f.write(data);f.flush()
  Path(name).replace(path)
 finally:Path(name).unlink(missing_ok=True)
def save(rel,data):
 p=inside(rel)
 if not p.exists():atomic(p,data)
class Redirect(urllib.request.HTTPRedirectHandler):
 def __init__(self,hosts):super().__init__();self.hosts=hosts
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  u=urllib.parse.urlparse(newurl);host=(u.hostname or '').lower()
  if host not in self.hosts:raise ValueError('redirect outside official-host allowlist')
  if u.scheme=='http':
   u=u._replace(scheme='https');newurl=urllib.parse.urlunparse(u)
  if u.scheme!='https':raise ValueError('redirect is not HTTPS')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url,hosts):
 u=urllib.parse.urlparse(url)
 if u.scheme!='https' or (u.hostname or '').lower() not in hosts:raise ValueError('URL outside official-host allowlist')
 # urllib requires non-ASCII path/query characters to be percent-encoded. Keep
 # the candidate URL intact in metadata while requesting its UTF-8 URL form.
 request_url=urllib.parse.urlunsplit((u.scheme,u.netloc,urllib.parse.quote(u.path,safe="/%:@!$&'()*+,;=-._~"),urllib.parse.quote(u.query,safe="/%?&=:@!$'()*+,;~"),u.fragment))
 op=urllib.request.build_opener(Redirect(hosts));req=urllib.request.Request(request_url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/pdf,application/json,*/*;q=0.8'})
 with op.open(req,timeout=TIMEOUT) as r:
  final=r.geturl();f=urllib.parse.urlparse(final)
  if f.scheme!='https' or (f.hostname or '').lower() not in hosts:raise ValueError('final URL outside official-host allowlist')
  data=r.read(MAX_BYTES+1)
  if len(data)>MAX_BYTES:raise ValueError('response exceeds 24 MiB cap')
  if not data:raise ValueError('empty response')
  return data,final,r.headers.get_content_type().lower()
class Region(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.skip=[];self.parts=[];self.found=False;self.selector=''
 def handle_starttag(self,t,a):
  attrs=dict(a)
  if self.skip:
   if t not in self.VOID:self.skip.append(t)
   return
  if not self.found:
   if t in {'main','article'} or (t in {'div','section'} and attrs.get('id') in {'main','content','main-content'}):
    self.found=True;self.selector=t+(('#'+attrs['id']) if attrs.get('id') else '')
    if t not in self.VOID:self.stack.append(t)
   elif t=='body':self.found=True;self.selector='body';self.stack.append(t)
   return
  if t in SKIP:
   if t not in self.VOID:self.skip.append(t)
   return
  if t=='br':self.parts.append('\n')
  elif t not in self.VOID:
   self.stack.append(t)
   if t in BLOCK:self.parts.append('\n')
 def handle_endtag(self,t):
  if self.skip:
   i=len(self.skip)-1
   while i>=0 and self.skip[i]!=t:i-=1
   if i>=0:del self.skip[i:]
   return
  i=len(self.stack)-1
  while i>=0 and self.stack[i]!=t:i-=1
  if i>=0:
   del self.stack[i:]
   if t in BLOCK:self.parts.append('\n')
 def handle_data(self,d):
  if self.found and self.stack and not self.skip and d.strip():self.parts.append(d)
 def text(self):
  x=''.join(self.parts).replace('\xa0',' ').replace('\r','\n');lines=[re.sub(r'[ \t]+',' ',s).strip() for s in x.splitlines()];o=[]
  for s in lines:
   if s or (o and o[-1]):o.append(s)
  return '\n'.join(o).strip()
def page_title(raw):
 s=decode_html(raw)
 for pat in (r'<title[^>]*>(.*?)</title>',r'<h1[^>]*>(.*?)</h1>'):
  m=re.search(pat,s,re.I|re.S)
  if m:
   x=html.unescape(re.sub(r'<[^>]*>',' ',m.group(1)));x=re.sub(r'\s+',' ',x).strip()
   if x:return x
 return 'Official source page'
def decode_html(raw):
 enc=None
 head=raw[:4096]
 for pat in (br'<\?xml[^>]*encoding=["\']([A-Za-z0-9._-]+)',br'<meta[^>]*charset=["\']?\s*([A-Za-z0-9._-]+)',br'<meta[^>]*content=["\'][^"\']*charset=([A-Za-z0-9._-]+)'):
  m=re.search(pat,head,re.I)
  if m:
   try:
    enc=m.group(1).decode('ascii'); ''.encode(enc); break
   except (LookupError,UnicodeDecodeError):enc=None
 return raw.decode(enc or 'utf-8','replace').lstrip('\ufeff')
def entry_type(entry):return entry.get('source_type') or entry.get('class') or entry.get('type') or 'official_source_candidate'
def version_note(entry):
 return entry.get('version_evidence') or entry.get('version_status') or entry.get('verification_status') or 'No source-version evidence in the candidate manifest.'
def render(entry,country,received,resolved,ctype,digest,selector,body):
 lines=[f"# {entry.get('title',entry.get('name',entry['id']))}",'',f"- Jurisdiction: {country}",f"- Candidate ID: `{entry['id']}`",f"- Source type: `{entry_type(entry)}`",f"- Candidate URL: {entry['url']}",f"- Resolved URL: {resolved}",f"- Retrieved: {received}",f"- Media type: `{ctype}`",f"- Publisher/version evidence: {version_note(entry)}",f"- Extraction: `{selector}`",f"- Exact response SHA-256: `{digest}`",'', '> **Review candidate.** Not accepted into the trusted source corpus. Check source identity, current version, scope, completeness, and reuse conditions before reliance.','','## Captured source text','',body,'']
 return ('\n'.join(lines).rstrip()+'\n').encode()
def get_entries(m):
 for k in ('sources','documents','items','candidates'):
  if isinstance(m.get(k),list):return k,m[k]
 raise ValueError('candidate manifest has no supported source list')
def old_record(old,i):return next((r for r in old.get('records',[]) if r.get('candidate_id')==i),None)
def capture(country,entry,hosts,prior,output_folder='candidates'):
 received=datetime.now(timezone.utc).isoformat(timespec='seconds');request_url=entry.get('retrieval_url') or entry['url'];raw,resolved,ctype=fetch(request_url,hosts);digest=sha(raw);name=slug(entry['id']);ext='pdf' if ctype=='application/pdf' else ('json' if ctype in {'application/json','application/ld+json'} else 'html');raw_rel=f'temp/{country}/raw/{name}-{digest}.{ext}';save(raw_rel,raw)
 rec={'candidate_id':entry['id'],'source_url':entry['url'],'request_url':request_url,'resolved_url':resolved,'retrieved_at':received,'source_content_type':ctype,'source_bytes':len(raw),'source_sha256':digest,'raw_path':raw_rel,'accepted':False}
 olddigest=prior.get('source_sha256') if prior else None
 changed=bool(not entry.get('replace_prior_capture',False) and ((prior and prior.get('review_state')=='changed_pending_review') or (olddigest and olddigest!=digest)))
 if ctype=='application/pdf' and raw.startswith(b'%PDF-'):
  save(f'temp/{country}/pdf/{name}-{digest}.pdf',raw);rec['candidate_source_path']=f'temp/{country}/pdf/{name}-{digest}.pdf'
  if importlib.util.find_spec('pypdf'):
   from pypdf import PdfReader
   reader=PdfReader(BytesIO(raw));pages=[]
   for n,page in enumerate(reader.pages,1):pages.append(f'<!-- page {n} -->\n'+(page.extract_text() or ''))
   body='\n\n'.join(pages).strip()
   if body:
    selector=f'PDF text extraction; {len(reader.pages)} pages';out=f'source-library/{country}/{output_folder}/{name}.md';md=render(entry,country,received,resolved,ctype,digest,selector,body);status='changed_review_candidate' if changed else 'converted_review_candidate';
    if changed:out=f'temp/{country}/pending/{name}-{digest[:16]}.md' if output_folder=='candidates' else f'temp/{country}/pending/{output_folder}/{name}-{digest[:16]}.md'
    atomic(inside(out),md);rec.update({'candidate_text_path':out,'converted_sha256':sha(md),'converted_bytes':len(md),'content_selector':selector,'retrieval_status':status,'review_state':'changed_pending_review' if changed else 'review_candidate'});return rec
  rec.update({'retrieval_status':'official_pdf_preserved_text_extraction_unavailable','retrieval_note':'PDF bytes preserved exactly; no local PDF text extractor is available.'});return rec
 if ctype in {'application/json','application/ld+json'}:
  obj=json.loads(raw);body='```json\n'+json.dumps(obj,ensure_ascii=False,indent=2)+'\n```';selector='formatted JSON record'
 elif ctype in {'text/html','application/xhtml+xml','application/octet-stream'} and raw.lstrip().lower().startswith((b'<!doctype html',b'<html',b'<!--',b'<?xml')):
  parser=Region();parser.feed(decode_html(raw));body=parser.text();selector=parser.selector or 'no primary region'
  if len(body)<80:
   rec.update({'retrieval_status':'discovery_surface_no_text','retrieval_note':'Public HTML response contained no sufficiently long extractable source body.'});return rec
 else:raise ValueError(f'unexpected response format: {ctype}')
 out=f'source-library/{country}/{output_folder}/{name}.md';md=render(entry,country,received,resolved,ctype,digest,selector,body);status='changed_review_candidate' if changed else 'converted_review_candidate'
 if changed:out=f'temp/{country}/pending/{name}-{digest[:16]}.md' if output_folder=='candidates' else f'temp/{country}/pending/{output_folder}/{name}-{digest[:16]}.md'
 atomic(inside(out),md);rec.update({'candidate_text_path':out,'converted_sha256':sha(md),'converted_bytes':len(md),'content_selector':selector,'retrieval_status':status,'review_state':'changed_pending_review' if changed else 'review_candidate'});return rec
def manifest_paths(country,manifest_name=None,output_folder_override=None):
 pack=BASE/country;manifest_name=manifest_name or 'candidate-manifest.json'
 if Path(manifest_name).name!=manifest_name or not manifest_name.endswith('.json'):raise ValueError('manifest must be a JSON filename in the jurisdiction references directory')
 mp=pack/'references'/manifest_name
 if not mp.is_file():raise ValueError(f'candidate manifest not found: {mp}')
 default=manifest_name=='candidate-manifest.json'
 cp=pack/'references'/(f'{country}-capture-results.json' if default else f'{Path(manifest_name).stem}-capture-results.json')
 output_folder=output_folder_override or ('candidates' if default else 'monitor-candidates')
 if not re.fullmatch(r'[a-z0-9][a-z0-9-]*',output_folder):raise ValueError('output folder must be a simple lowercase name')
 return pack,mp,cp,output_folder
def sync(country,manifest_name=None,output_folder_override=None):
 pack,mp,cp,output_folder=manifest_paths(country,manifest_name,output_folder_override)
 m=json.loads(mp.read_text(encoding='utf8'));key,entries=get_entries(m);hosts={str(x).lower() for x in m.get('official_hosts',[])}
 for e in entries:
  h=urllib.parse.urlparse(e.get('url','')).hostname
  if h:hosts.add(h.lower())
 old=json.loads(cp.read_text(encoding='utf8')) if cp.exists() else {'records':[]};results=[]
 for n,e in enumerate(entries):
  print('retrieving',e['id'],flush=True)
  try:r=capture(country,e,hosts,old_record(old,e['id']),output_folder)
  except Exception as exc:r={'candidate_id':e['id'],'source_url':e.get('url'),'retrieval_status':'retrieval_or_conversion_error','retrieval_note':f'{type(exc).__name__}: {exc}','accepted':False};print('review',e['id'],r['retrieval_note'],flush=True)
  results.append(r)
  if n<len(entries)-1:time.sleep(DELAY)
 byid={r['candidate_id']:r for r in results}
 for e in entries:
  r=byid[e['id']];e['retrieved']=bool(r.get('source_sha256'));e['accepted']=False;e['retrieval_status']=r['retrieval_status']
  for k in ('candidate_text_path','candidate_source_path','source_sha256','converted_sha256','source_bytes','resolved_url','retrieval_note'):
   if k in r:e[k]=r[k]
  e.pop('replace_prior_capture',None)
 counts={}
 for r in results:counts[r['retrieval_status']]=counts.get(r['retrieval_status'],0)+1
 m['status']='partially_retrieved_review_candidates';m['accepted_source_count']=0;m['candidate_source_count']=len(entries);m['retrieved_review_candidate_count']=sum(bool(r.get('source_sha256')) for r in results);m['converted_review_candidate_count']=sum(bool(r.get('candidate_text_path')) for r in results)
 m['retrieval_status']=f"{m['converted_review_candidate_count']} candidate pages converted; {counts.get('official_pdf_preserved_text_extraction_unavailable',0)} PDFs preserved without text extraction; {counts.get('discovery_surface_no_text',0)} discovery surfaces had no stable body; failures are recorded per item; no source accepted"
 cap={'jurisdiction':country,'as_of_date':date.today().isoformat(),'method':'Ordinary allowlisted HTTPS GET only; no authentication, challenge bypass or form submission. Exact response bytes are hashed; changes stage for review.','request_policy':{'timeout_seconds':TIMEOUT,'max_response_bytes':MAX_BYTES,'delay_seconds':DELAY},'records':results,'accepted_source_count':0}
 atomic(mp,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());atomic(cp,(json.dumps(cap,ensure_ascii=False,indent=2)+'\n').encode())
def verify(country,manifest_name=None,output_folder_override=None):
 pack,mp,cp,output_folder=manifest_paths(country,manifest_name,output_folder_override);m=json.loads(mp.read_text());key,entries=get_entries(m);src={e['id']:e for e in entries};cap=json.loads(cp.read_text());errors=[]
 for r in cap['records']:
  try:
   if not r.get('raw_path'):continue
   raw=inside(r['raw_path']).read_bytes()
   if sha(raw)!=r['source_sha256']:raise ValueError('source hash mismatch')
   if r.get('candidate_text_path'):
    ctype=r['source_content_type'];entry=src[r['candidate_id']]
    if ctype in {'application/json','application/ld+json'}:body='```json\n'+json.dumps(json.loads(raw),ensure_ascii=False,indent=2)+'\n```';selector='formatted JSON record'
    elif ctype=='application/pdf':
     from pypdf import PdfReader
     reader=PdfReader(BytesIO(raw));body='\n\n'.join(f'<!-- page {n} -->\n'+(page.extract_text() or '') for n,page in enumerate(reader.pages,1)).strip();selector=f'PDF text extraction; {len(reader.pages)} pages'
    else:
     parser=Region();parser.feed(decode_html(raw));body=parser.text();selector=parser.selector or 'no primary region'
    md=render(entry,country,r['retrieved_at'],r['resolved_url'],ctype,r['source_sha256'],selector,body)
    if sha(md)!=r['converted_sha256'] or sha(inside(r['candidate_text_path']).read_bytes())!=r['converted_sha256']:raise ValueError('conversion replay mismatch')
   if r.get('candidate_source_path') and sha(inside(r['candidate_source_path']).read_bytes())!=r['source_sha256']:raise ValueError('preserved PDF hash mismatch')
   print('verified',r['candidate_id'])
  except Exception as exc:errors.append(f"{r.get('candidate_id')}: {exc}")
 if errors:raise SystemExit('\n'.join(errors))
def convert_saved_pdfs(country,manifest_name=None,output_folder_override=None):
 """Convert already captured official PDFs without making network requests."""
 pack,mp,cp,output_folder=manifest_paths(country,manifest_name,output_folder_override)
 m=json.loads(mp.read_text(encoding='utf8'));key,entries=get_entries(m);entry_by_id={e['id']:e for e in entries}
 cap=json.loads(cp.read_text(encoding='utf8'));converted=0
 from pypdf import PdfReader
 for r in cap.get('records',[]):
  if r.get('source_content_type')!='application/pdf' or r.get('candidate_text_path') or not r.get('raw_path'):
   continue
  raw=inside(r['raw_path']).read_bytes()
  if sha(raw)!=r.get('source_sha256'):
   raise ValueError(f"{r.get('candidate_id')}: captured PDF hash mismatch")
  reader=PdfReader(BytesIO(raw));body='\n\n'.join(f'<!-- page {n} -->\n'+(page.extract_text() or '') for n,page in enumerate(reader.pages,1)).strip()
  if not body:
   continue
  entry=entry_by_id[r['candidate_id']];selector=f'PDF text extraction; {len(reader.pages)} pages';
  out=f"source-library/{country}/{output_folder}/{slug(entry['id'])}.md"
  changed=r.get('review_state')=='changed_pending_review'
  if changed:
   out=f"temp/{country}/pending/{output_folder}/{slug(entry['id'])}-{r['source_sha256'][:16]}.md" if output_folder!='candidates' else f"temp/{country}/pending/{slug(entry['id'])}-{r['source_sha256'][:16]}.md"
  md=render(entry,country,r['retrieved_at'],r['resolved_url'],r['source_content_type'],r['source_sha256'],selector,body)
  atomic(inside(out),md);r.update({'candidate_text_path':out,'converted_sha256':sha(md),'converted_bytes':len(md),'content_selector':selector,'retrieval_status':'changed_review_candidate' if changed else 'converted_review_candidate','review_state':'changed_pending_review' if changed else 'review_candidate'});r.pop('retrieval_note',None)
  converted+=1
 for e in entries:
  r=old_record({'records':cap.get('records',[])},e['id'])
  if not r:continue
  e['retrieved']=bool(r.get('source_sha256'));e['accepted']=False;e['retrieval_status']=r.get('retrieval_status')
  for k in ('candidate_text_path','candidate_source_path','source_sha256','converted_sha256','source_bytes','resolved_url','retrieval_note'):
   if k in r:e[k]=r[k]
  for k in ('retrieval_note','candidate_text_path','candidate_source_path','source_sha256','converted_sha256','source_bytes','resolved_url'):
   if k not in r:e.pop(k,None)
 counts={}
 for r in cap.get('records',[]):counts[r.get('retrieval_status')]=counts.get(r.get('retrieval_status'),0)+1
 m['accepted_source_count']=0;m['candidate_source_count']=len(entries);m['retrieved_review_candidate_count']=sum(bool(r.get('source_sha256')) for r in cap.get('records',[]));m['converted_review_candidate_count']=sum(bool(r.get('candidate_text_path')) for r in cap.get('records',[]));m['status']='partially_retrieved_review_candidates';m['retrieval_status']=f"{m['converted_review_candidate_count']} candidate pages converted; {counts.get('official_pdf_preserved_text_extraction_unavailable',0)} PDFs preserved without text extraction; {counts.get('discovery_surface_no_text',0)} discovery surfaces had no stable body; failures are recorded per item; no source accepted"
 atomic(mp,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());atomic(cp,(json.dumps(cap,ensure_ascii=False,indent=2)+'\n').encode())
 print(f'converted {converted} saved PDFs offline')
def main():
 if len(sys.argv) not in {3,4,5} or sys.argv[1] in {'-h','--help'}:raise SystemExit('usage: sync_candidate_pages.py COUNTRY sync|verify|convert [MANIFEST_JSON_FILENAME] [OUTPUT_FOLDER]')
 country=sys.argv[1].lower();mode=sys.argv[2]
 if not re.fullmatch(r'[a-z][a-z0-9-]*',country) or not (BASE/country).is_dir():raise SystemExit('unknown source-library jurisdiction')
 manifest_name=sys.argv[3] if len(sys.argv)==4 else None
 if len(sys.argv)==5:manifest_name=sys.argv[3];output_folder=sys.argv[4]
 else:output_folder=None
 if mode=='sync':sync(country,manifest_name,output_folder)
 elif mode=='verify':verify(country,manifest_name,output_folder)
 elif mode=='convert':convert_saved_pdfs(country,manifest_name,output_folder)
 else:raise SystemExit('mode must be sync or verify')
if __name__=='__main__':main()
