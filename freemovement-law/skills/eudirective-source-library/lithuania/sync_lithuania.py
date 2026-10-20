#!/usr/bin/env python3
"""Capture Lithuanian official candidate pages and TAR dataset texts."""
from __future__ import annotations
import hashlib, html, json, re, sys, tempfile, time, urllib.parse, urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PACK=Path(__file__).resolve().parent; ROOT=PACK.parents[1]
MANIFEST=PACK/'references/candidate-manifest.json'; CAPTURES=PACK/'references/lithuania-captures.json'
API='https://get.data.gov.lt/datasets/gov/lrsk/teises_aktai/Suvestine'
MAX_BYTES=16*1024*1024; TIMEOUT=25; DELAY=0.8
UA='eudirective-source-library/1.0 (public-source review; eudirective@proton.me)'
SKIP={'script','style','noscript','svg','nav','header','footer','form'}
BLOCK={'address','article','br','dd','div','dl','dt','h1','h2','h3','h4','h5','h6','li','ol','p','section','table','td','th','tr','ul'}


def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def inside(rel:str)->Path:
 p=(ROOT/rel).resolve()
 if not p.is_relative_to(ROOT):raise ValueError(f'path outside repository: {rel}')
 return p
def atomic(path:Path,data:bytes)->None:
 path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with open(fd,'wb',closefd=True) as f:f.write(data);f.flush()
  Path(name).replace(path)
 finally:Path(name).unlink(missing_ok=True)
def save(rel:str,data:bytes)->None:
 p=inside(rel)
 if not p.exists():atomic(p,data)

class Redirect(urllib.request.HTTPRedirectHandler):
 def __init__(self,hosts:set[str]):super().__init__();self.hosts=hosts
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  u=urllib.parse.urlparse(newurl)
  if u.scheme!='https' or (u.hostname or '').lower() not in self.hosts:raise ValueError('redirect outside official host allowlist')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url:str,hosts:set[str],accept:str='text/html,application/xhtml+xml,application/pdf,application/json,*/*;q=0.8')->tuple[bytes,str,str]:
 u=urllib.parse.urlparse(url)
 if u.scheme!='https' or (u.hostname or '').lower() not in hosts:raise ValueError('URL outside official host allowlist')
 op=urllib.request.build_opener(Redirect(hosts));req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':accept})
 with op.open(req,timeout=TIMEOUT) as r:
  final=r.geturl();f=urllib.parse.urlparse(final)
  if f.scheme!='https' or (f.hostname or '').lower() not in hosts:raise ValueError('final URL outside official host allowlist')
  data=r.read(MAX_BYTES+1)
  if len(data)>MAX_BYTES:raise ValueError('response exceeds 16 MiB cap')
  if not data:raise ValueError('empty response')
  return data,final,r.headers.get_content_type().lower()

class Extract(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.skip=[];self.parts=[];self.found=False;self.selector=''
 def handle_starttag(self,t,a):
  if self.skip:
   if t not in self.VOID:self.skip.append(t)
   return
  if not self.found:
   if t in {'main','article'} or (t=='div' and dict(a).get('id') in {'content','main-content'}):
    self.found=True;self.selector=t+('#'+dict(a).get('id','') if dict(a).get('id') else '')
    if t not in self.VOID:self.stack.append(t)
   elif t=='body' and not self.found:self.found=True;self.selector='body';self.stack.append(t)
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
  raw=''.join(self.parts).replace('\xa0',' ').replace('\r','\n')
  lines=[re.sub(r'[ \t]+',' ',x).strip() for x in raw.splitlines()]
  out=[]
  for x in lines:
   if x or (out and out[-1]):out.append(x)
  return '\n'.join(out).strip()
def title(raw:bytes)->str:
 s=raw.decode('utf8','replace')
 for pat in (r'<title[^>]*>(.*?)</title>',r'<h1[^>]*>(.*?)</h1>'):
  m=re.search(pat,s,re.I|re.S)
  if m:
   v=html.unescape(re.sub(r'<[^>]*>',' ',m.group(1)));v=re.sub(r'\s+',' ',v).strip()
   if v:return v
 return 'Official Lithuanian source page'
def slug(s:str)->str:return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def meta_md(source:dict,received:str,resolved:str,ctype:str,rawhash:str,version:str,body:str)->bytes:
 lines=[f"# {source['title']}",'',f"- Jurisdiction: Lithuania",f"- Candidate ID: `{source['id']}`",f"- Source type: `{source.get('source_type','')}`",f"- Candidate URL: {source['url']}",f"- Resolved URL: {resolved}",f"- Retrieved: {received}",f"- Media type: `{ctype}`",f"- Publisher/version evidence: {version}",f"- Exact response SHA-256: `{rawhash}`",'', '> **Review candidate.** Not accepted into the trusted source corpus. Verify identity, scope, version, authority and reuse conditions before reliance.','','## Captured source text','',body,'']
 return ('\n'.join(lines).rstrip()+'\n').encode()

def api_url(query:str)->str:return API+'?'+urllib.parse.quote(query,safe="'=&,_<>.")
def get_versions(doc_id:str,hosts:set[str])->tuple[bytes,list[dict],str]:
 q=f"dokumento_id='{doc_id}'&_limit=200&_select=dokumento_id,suvestines_id,nuoroda,galioja_nuo,galioja_iki"
 b,u,t=fetch(api_url(q),hosts,'application/json')
 if t!='application/json':raise ValueError(f'TAR API metadata is {t}, not JSON')
 obj=json.loads(b);rows=obj.get('_data',[])
 if obj.get('_page',{}).get('next'):raise ValueError('more than 200 API versions; pagination not captured')
 return b,rows,u
def get_api_text(doc_id:str,version_id:str,hosts:set[str])->tuple[bytes,dict,str]:
 q=f"dokumento_id='{doc_id}'&suvestines_id='{version_id}'&_limit=2"
 b,u,t=fetch(api_url(q),hosts,'application/json')
 if t!='application/json':raise ValueError(f'TAR API text is {t}, not JSON')
 obj=json.loads(b);rows=obj.get('_data',[])
 if len(rows)!=1:raise ValueError(f'exact API identity query returned {len(rows)} records')
 row=rows[0]
 if row.get('dokumento_id')!=doc_id or row.get('suvestines_id')!=version_id or not isinstance(row.get('tekstas_lt'),str):raise ValueError('TAR API record identity/text validation failed')
 return b,row,u
def tar_id(source:dict)->str|None:
 u=urllib.parse.urlparse(source['url'])
 if u.hostname not in {'e-tar.lt','www.e-tar.lt'}:return None
 p=u.path
 if 'legalAct/' in p:
  part=p.split('legalAct/',1)[1].split('/',1)[0]
  if part!='legalActSearch' and re.fullmatch(r'[A-Za-z0-9.]+',part):return part
  return None
 if '/rs/actualedition/' not in p:return None
 record=source.get('publisher_identifier',{}).get('record','').split(';',1)[0].strip()
 if record and re.fullmatch(r'[A-Za-z0-9.]+',record):return record
 return None

def capture_api(source:dict,hosts:set[str],received:str)->dict:
 doc=tar_id(source)
 if not doc:raise ValueError('no stable TAR identifier in candidate URL or publisher metadata')
 meta=rows=meta_url=None;api_id=None;tried=[]
 ids=[doc]
 if doc.startswith('TAR.'):ids.append(doc[4:])
 else:ids.append('TAR.'+doc)
 for candidate_id in dict.fromkeys(ids):
  tried.append(candidate_id)
  try:
   candidate_meta,candidate_rows,candidate_url=get_versions(candidate_id,hosts)
   if candidate_rows:
    meta,rows,meta_url,api_id=candidate_meta,candidate_rows,candidate_url,candidate_id
    break
  except Exception:
   continue
 if not rows:raise ValueError('official TAR API returned no version rows for IDs: '+', '.join(tried))
 doc=api_id
 mid=f"temp/lithuania/raw/{source['id']}-versions-{sha(meta)}.json";save(mid,meta)
 today=date.today().isoformat()
 def day(v):return (v or '')[:10]
 active=[r for r in rows if day(r.get('galioja_nuo'))<=today and (not r.get('galioja_iki') or day(r.get('galioja_iki'))>=today)]
 version_state='active_as_listed_by_dataset' if active else 'latest_prior_not_current'
 pool=active or [r for r in rows if day(r.get('galioja_nuo'))<=today]
 if not pool:raise ValueError('dataset contains no version beginning on/before retrieval date')
 row=max(pool,key=lambda r:day(r.get('galioja_nuo')))
 version_id=row.get('suvestines_id')
 if not version_id:raise ValueError('current version record lacks suvestines_id')
 time.sleep(DELAY)
 raw,full,api_record_url=get_api_text(doc,version_id,hosts)
 digest=sha(raw);raw_rel=f"temp/lithuania/raw/{source['id']}-{digest}.json";save(raw_rel,raw)
 body=full['tekstas_lt'].replace('\r\n','\n').replace('\r','\n').strip()
 if len(body)<40:raise ValueError('TAR API text is unexpectedly short')
 version=f"TAR API version {version_id}; valid {row.get('galioja_nuo')} through {row.get('galioja_iki') or 'open-ended'}; API metadata {version_state}. Not reconciled with live e-TAR page."
 md=meta_md(source,received,full.get('nuoroda') or api_record_url,'application/json',digest,version,body)
 out=f"source-library/lithuania/candidates/{slug(source['id'])}.md";conv=sha(md);atomic(inside(out),md)
 return {'candidate_id':source['id'],'source_url':source['url'],'resolved_url':full.get('nuoroda') or api_record_url,'api_metadata_url':meta_url,'api_record_url':api_record_url,'api_document_id':doc,'retrieved_at':received,'source_content_type':'application/json','source_bytes':len(raw),'source_sha256':digest,'raw_path':raw_rel,'versions_raw_path':mid,'versions_sha256':sha(meta),'candidate_text_path':out,'converted_sha256':conv,'converted_bytes':len(md),'retrieval_status':'converted_review_candidate_api_currentness_unverified' if active else 'converted_review_candidate_api_version_not_current','version_id':version_id,'valid_from':row.get('galioja_nuo'),'valid_to':row.get('galioja_iki'),'api_version_state':version_state,'api_version_count':len(rows),'accepted':False,'metadata':version,'body':body}

def capture_html(source:dict,hosts:set[str],received:str)->dict:
 raw,resolved,ctype=fetch(source['url'],hosts)
 digest=sha(raw);name=slug(source['id']);ext='pdf' if ctype=='application/pdf' else ('json' if ctype=='application/json' else 'html')
 raw_rel=f"temp/lithuania/raw/{name}-{digest}.{ext}";save(raw_rel,raw)
 rec={'candidate_id':source['id'],'source_url':source['url'],'resolved_url':resolved,'retrieved_at':received,'source_content_type':ctype,'source_bytes':len(raw),'source_sha256':digest,'raw_path':raw_rel,'accepted':False}
 if ctype=='application/pdf' and raw.startswith(b'%PDF-'):
  rec.update({'retrieval_status':'official_pdf_preserved_text_extraction_unavailable','candidate_source_path':f'temp/lithuania/pdfs/{name}-{digest}.pdf'})
  save(rec['candidate_source_path'],raw);return rec
 if ctype=='application/json':
  try: obj=json.loads(raw)
  except Exception as e:raise ValueError(f'invalid JSON: {e}')
  body='```json\n'+json.dumps(obj,ensure_ascii=False,indent=2)+'\n```';ctype_note='application/json'
 elif ctype in {'text/html','application/xhtml+xml','application/octet-stream'} and raw.lstrip().lower().startswith((b'<!doctype html',b'<html',b'<!--')):
  parser=Extract();parser.feed(raw.decode('utf8','replace'));body=parser.text();ctype_note=ctype
  if len(body)<40:
   rec.update({'retrieval_status':'discovery_surface_no_stable_body','retrieval_note':'Public page retrieved, but no sufficiently long primary content was extracted.'});return rec
 else:raise ValueError(f'unexpected response format {ctype}')
 md=meta_md(source,received,resolved,ctype_note,digest,source.get('version_evidence','No publisher version evidence recorded in candidate manifest.'),body)
 out=f"source-library/lithuania/candidates/{slug(source['id'])}.md";atomic(inside(out),md)
 rec.update({'candidate_text_path':out,'converted_sha256':sha(md),'converted_bytes':len(md),'content_selector':getattr(parser,'selector','JSON API') if ctype not in {'application/json'} else 'JSON','retrieval_status':'converted_review_candidate','body':body})
 return rec

def update_manifest(m:dict,results:list[dict])->None:
 byid={r['candidate_id']:r for r in results}
 for s in m['documents']:
  r=byid[s['id']];s['retrieved']=bool(r.get('source_sha256'));s['retrieval_status']=r['retrieval_status'];s['accepted']=False
  for k in ('candidate_text_path','candidate_source_path','source_sha256','converted_sha256','resolved_url','version_id','valid_from','valid_to','api_version_state','api_version_count','retrieval_note'):
   if k in r:s[k]=r[k]
 counts={}
 for r in results:counts[r['retrieval_status']]=counts.get(r['retrieval_status'],0)+1
 m['retrieved_review_candidate_count']=sum(bool(r.get('source_sha256')) for r in results)
 m['converted_review_candidate_count']=sum(bool(r.get('candidate_text_path')) for r in results)
 m['accepted_source_count']=0;m['status']='partially_retrieved_review_candidates'
 m['retrieval_status']=f"{m['converted_review_candidate_count']} HTML/API texts converted; {counts.get('official_pdf_preserved_text_extraction_unavailable',0)} PDFs preserved without text extraction; direct publisher failures and discovery-only records retained per candidate; no source accepted"

def sync():
 m=json.loads(MANIFEST.read_text());hosts=set(m.get('official_hosts',[]))
 for source in m.get('documents',[]):
  host=urllib.parse.urlparse(source['url']).hostname
  if host:hosts.add(host.lower())
 hosts.add('get.data.gov.lt')
 results=[]
 for i,s in enumerate(m['documents']):
  received=datetime.now(timezone.utc).isoformat(timespec='seconds');print('retrieving',s['id'],flush=True)
  direct_error=None
  try:
   if urllib.parse.urlparse(s['url']).hostname in {'e-tar.lt','www.e-tar.lt'} and tar_id(s):
    try:
     raw,_,_=fetch(s['url'],hosts)
     # Preserve a directly readable current e-TAR response if the publisher supplies it.
     if raw: results.append(capture_html_from_preloaded(s,raw,s['url'],received));continue
    except Exception as exc:direct_error=f'{type(exc).__name__}: {exc}'
    time.sleep(DELAY)
    r=capture_api(s,hosts,received);r['direct_publisher_result']=direct_error;results.append(r)
   else:results.append(capture_html(s,hosts,received))
  except Exception as exc:
   note=f'{type(exc).__name__}: {exc}'
   if direct_error:note=f'direct publisher request {direct_error}; API fallback {note}'
   results.append({'candidate_id':s['id'],'source_url':s['url'],'retrieved_at':received,'retrieval_status':'retrieval_or_conversion_error','retrieval_note':note,'direct_publisher_result':direct_error,'accepted':False})
   print('review',s['id'],results[-1]['retrieval_note'],flush=True)
  if i<len(m['documents'])-1:time.sleep(DELAY)
 update_manifest(m,results)
 cap={'jurisdiction':'Lithuania','as_of_date':date.today().isoformat(),'method':'Ordinary allowlisted HTTPS GET only. e-TAR direct pages are tried once; if blocked, the official data.gov.lt TAR Suvestine API is queried by exact TAR identifier and version identifier. No authentication, browser automation, form submission or challenge bypass.','request_policy':{'timeout_seconds':TIMEOUT,'max_response_bytes':MAX_BYTES,'delay_seconds':DELAY},'publisher_terms':'The TAR open dataset catalogue identifies CC BY 4.0 for that dataset only. This does not establish the terms for every directly fetched e-TAR, government, court, guidance or form source. No candidate accepted.','records':results,'accepted_source_count':0}
 atomic(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());atomic(CAPTURES,(json.dumps(cap,ensure_ascii=False,indent=2)+'\n').encode())

def capture_html_from_preloaded(source:dict,raw:bytes,resolved:str,received:str)->dict:
 digest=sha(raw);name=slug(source['id']);save(f'temp/lithuania/raw/{name}-{digest}.html',raw)
 ctype='text/html';parser=Extract();parser.feed(raw.decode('utf8','replace'));body=parser.text()
 if len(body)<40:raise ValueError('direct e-TAR body too short')
 md=meta_md(source,received,resolved,ctype,digest,source.get('version_evidence',''),body)
 out=f"source-library/lithuania/candidates/{name}.md";atomic(inside(out),md)
 return {'candidate_id':source['id'],'source_url':source['url'],'resolved_url':resolved,'retrieved_at':received,'source_content_type':ctype,'source_bytes':len(raw),'source_sha256':digest,'raw_path':f'temp/lithuania/raw/{name}-{digest}.html','candidate_text_path':out,'converted_sha256':sha(md),'converted_bytes':len(md),'retrieval_status':'converted_review_candidate','accepted':False}

def verify():
 if not CAPTURES.exists():raise SystemExit('No capture manifest')
 cap=json.loads(CAPTURES.read_text());manifest=json.loads(MANIFEST.read_text());sources={x['id']:x for x in manifest['documents']};errors=[]
 for r in cap['records']:
  try:
   if not r.get('raw_path'):continue
   raw=inside(r['raw_path']).read_bytes()
   if sha(raw)!=r['source_sha256']:raise ValueError('source hash mismatch')
   if r.get('versions_raw_path') and sha(inside(r['versions_raw_path']).read_bytes())!=r['versions_sha256']:raise ValueError('version metadata hash mismatch')
   if r.get('candidate_text_path'):
    source=sources[r['candidate_id']]
    if r.get('api_record_url'):
     obj=json.loads(raw);rows=obj.get('_data',[])
     if len(rows)!=1:raise ValueError('API response no longer contains exactly one source record')
     row=rows[0]
     if row.get('dokumento_id')!=r.get('api_document_id') or row.get('suvestines_id')!=r.get('version_id'):raise ValueError('API record identity mismatch')
     body=row.get('tekstas_lt','').replace('\r\n','\n').replace('\r','\n').strip();version=r['metadata'];resolved=row.get('nuoroda') or r['api_record_url'];ctype='application/json'
    else:
     ctype=r['source_content_type'];resolved=r['resolved_url'];version=source.get('version_evidence','No publisher version evidence recorded in candidate manifest.')
     if ctype=='application/json':body='```json\n'+json.dumps(json.loads(raw),ensure_ascii=False,indent=2)+'\n```'
     else:
      parser=Extract();parser.feed(raw.decode('utf8','replace'));body=parser.text()
    rebuilt=meta_md(source,r['retrieved_at'],resolved,ctype,r['source_sha256'],version,body)
    if sha(rebuilt)!=r['converted_sha256']:raise ValueError('deterministic conversion replay mismatch')
    if sha(inside(r['candidate_text_path']).read_bytes())!=r['converted_sha256']:raise ValueError('candidate text hash mismatch')
   if r.get('candidate_source_path') and sha(inside(r['candidate_source_path']).read_bytes())!=r['source_sha256']:raise ValueError('PDF hash mismatch')
   print('verified',r['candidate_id'])
  except Exception as e:errors.append(f"{r.get('candidate_id')}: {e}")
 if errors:raise SystemExit('\n'.join(errors))
def main():
 mode=sys.argv[1] if len(sys.argv)>1 else ''
 if mode=='sync':sync()
 elif mode=='verify':verify()
 else:raise SystemExit('usage: sync_lithuania.py sync|verify')
if __name__=='__main__':main()
