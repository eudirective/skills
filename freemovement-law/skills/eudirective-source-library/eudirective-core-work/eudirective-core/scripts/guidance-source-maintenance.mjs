#!/usr/bin/env node
// Official guidance retrieval shared by the four owning source packs.
import { createHash, X509Certificate } from 'node:crypto';
import { readFile, mkdir, access, rm } from 'node:fs/promises';
import https from 'node:https';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { atomicProjectWrite, projectTempPath } from '../../../runtime-storage.mjs';
import { pageDateMetadata } from './source-maintenance.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const workspace = path.resolve(here, '../../..');
const locations = {
  denmark: ['eudirective-source-library-0.6.0/denmark', 'documents/guidance'],
  sweden: ['eudirective-source-library-0.6.0/sweden', 'documents/guidance'],
  romania: ['eudirective-source-library-0.6.0/romania', 'documents'],
  eu: ['eudirective-source-library-0.6.0', 'core/guidance/official'],
};
const sha = value => createHash('sha256').update(value).digest('hex');
const normalize = value => value.replace(/\s+/g, ' ').trim();
const MAX_RESPONSE_BYTES = 30_000_000;
const entities = { amp:'&', lt:'<', gt:'>', quot:'"', apos:"'", nbsp:' ', ndash:'–', mdash:'—', hellip:'…', sect:'§',
  aelig:'æ', AElig:'Æ', oslash:'ø', Oslash:'Ø', aring:'å', Aring:'Å', ouml:'ö', Ouml:'Ö', auml:'ä', Auml:'Ä',
  eacute:'é', Eacute:'É', agrave:'à', rsquo:'’', lsquo:'‘', rdquo:'”', ldquo:'“', bull:'•' };
function decode(s) {
  return s.replace(/&(#x[\da-f]+|#\d+|[a-zA-Z]+);/gi, (m, x) => {
    if (x[0] === '#') { const n = x[1].toLowerCase() === 'x' ? parseInt(x.slice(2),16) : parseInt(x.slice(1),10); return n > 0 && n <= 0x10ffff ? String.fromCodePoint(n) : m; }
    return entities[x] ?? m;
  });
}
function htmlText(html) {
  const body = (html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/i) || html.match(/<article\b[^>]*>([\s\S]*?)<\/article>/i) || [,''])[1] || html;
  return decode(body.replace(/<!--([\s\S]*?)-->/g,' ')
    .replace(/<(script|style|nav|header|footer|aside|form|button|svg|noscript)\b[^>]*>[\s\S]*?<\/\1>/gi,' ')
    .replace(/<\/(?:h[1-6]|p|div|li|tr|section|article|table)>|<br\s*\/?>/gi,'\n')
    .replace(/<[^>]+>/g,' ').replace(/[\t ]+/g,' ').replace(/ *\n */g,'\n').replace(/\n{3,}/g,'\n\n')).trim();
}
function decodeText(bytes, contentType = '', label = 'official response') {
  const declared = contentType.match(/charset\s*=\s*["']?([^;"'\s]+)/i)?.[1];
  const meta = bytes.subarray(0, 4096).toString('ascii').match(/<meta\b[^>]*\bcharset\s*=\s*["']?([^\s"'/>;]+)/i)?.[1]
    || bytes.subarray(0, 4096).toString('ascii').match(/<meta\b[^>]*http-equiv\s*=\s*["']content-type["'][^>]*content\s*=\s*["'][^"']*charset=([^\s;"']+)/i)?.[1];
  const charset = declared || meta || 'utf-8';
  try { return new TextDecoder(charset, { fatal: true }).decode(bytes); }
  catch { throw Error(`unsupported or invalid ${charset} text encoding at ${label}`); }
}
async function readLimited(response, label) {
  const declared = Number(response.headers.get('content-length'));
  if (Number.isFinite(declared) && declared > MAX_RESPONSE_BYTES) throw Error(`Response exceeds ${MAX_RESPONSE_BYTES} byte limit at ${label}`);
  if (!response.body) return Buffer.alloc(0);
  const reader = response.body.getReader(), chunks = []; let size = 0;
  try {
    while (true) {
      const {done,value}=await reader.read(); if(done)break;
      size+=value.byteLength;
      if(size>MAX_RESPONSE_BYTES){await reader.cancel();throw Error(`Response exceeds ${MAX_RESPONSE_BYTES} byte limit at ${label}`);}
      chunks.push(Buffer.from(value));
    }
  } finally { reader.releaseLock(); }
  return Buffer.concat(chunks,size);
}
async function fetchBytes(url, allowedHosts, ca) {
  for (let redirects=0; redirects<6; redirects++) {
    const u = new URL(url);
    if (u.protocol !== 'https:' || !allowedHosts.includes(u.hostname)) throw Error('Unapproved source URL: '+url);
    const result = ca ? await new Promise((resolve,reject) => {
      let timer;
      const request = https.get(url, {ca, headers:{'user-agent':'visa-skills-guidance-source-maintenance/2.1'}}, response => {
        const parts=[]; let size=0;
        response.on('data', b=>{size+=b.length; if(size>30_000_000)response.destroy(Error('Response too large')); else parts.push(b);});
        response.on('end',()=>{clearTimeout(timer);resolve({status:response.statusCode,location:response.headers.location,type:response.headers['content-type']||'',bytes:Buffer.concat(parts)});});
        response.on('error',error=>{clearTimeout(timer);reject(error);});
      });
      timer=setTimeout(()=>request.destroy(Error('Request timeout')),45000);
      request.on('error',error=>{clearTimeout(timer);reject(error);});
    }) : await (async()=>{const r=await fetch(url,{redirect:'manual',headers:{'user-agent':'visa-skills-guidance-source-maintenance/2.1'},signal:AbortSignal.timeout(45000)});return {status:r.status,location:r.headers.get('location'),type:r.headers.get('content-type')||'',bytes:await readLimited(r,url)};})();
    if ([301,302,303,307,308].includes(result.status)) { if(!result.location)throw Error('Redirect without location'); url=new URL(result.location,url).href; continue; }
    if (result.status !== 200) throw Error('HTTP '+result.status+' at '+url);
    return {...result,url};
  }
  throw Error('Too many redirects');
}
async function pdfText(bytes) {
  const pdfjs = await import('pdfjs-dist/legacy/build/pdf.mjs');
  const doc = await pdfjs.getDocument({data:new Uint8Array(bytes),useSystemFonts:true}).promise;
  const pages=[];
  for(let p=1;p<=doc.numPages;p++){
    const page=await doc.getPage(p), tc=await page.getTextContent();
    const lines=[];let previousY=null,line=[];
    for(const item of tc.items){
      if(!item.str)continue;
      const y=item.transform?.[5]??0;
      if(previousY!==null && Math.abs(y-previousY)>3){lines.push(line.join(' '));line=[];}
      line.push(item.str);previousY=y;
    }
    if(line.length)lines.push(line.join(' '));
    pages.push(lines.join('\n'));
  }
  return {text:pages.join('\n\n'),pages:doc.numPages};
}
async function convert(bytes, ext, contentType = '') {
  if(ext==='pdf')return await pdfText(bytes);
  const text=decodeText(bytes,contentType);
  if(ext==='json')return {text:'```json\n'+JSON.stringify(JSON.parse(text),null,2)+'\n```',pages:null};
  return {text:htmlText(text),pages:null};
}
function makeMarkdown(source, finalUrl, rawHash, converted, ext, documentRequestUrl=finalUrl) {
  const discovery = source.catalog_lookup
    ? `- Official catalogue: ${source.url}\n- Catalogue record: ${source.catalog_lookup.row_title}\n- Catalogue download URL: ${documentRequestUrl}\n`
    : `- Official source: ${source.url}\n`;
  return `# ${source.title}\n\n${discovery}- Retrieved document: ${finalUrl}\n- Source format: ${ext.toUpperCase()}\n- Source SHA-256: ${rawHash}\n${converted.pages ? `- PDF pages: ${converted.pages}\n` : ''}\n${converted.text.trim()}\n`;
}
async function loadConfig(pack) {
  if(!locations[pack])throw Error('Unknown pack '+pack);
  const [folder, docs] = locations[pack], root=path.join(workspace,folder);
  const manifest=JSON.parse(await readFile(path.join(root,'references/guidance-manifest.json'),'utf8'));
  const work=projectTempPath(path.join(root,'work/guidance'));
  const stateFile=path.join(work,'state.json');
  const state=JSON.parse(await readFile(stateFile,'utf8').catch(()=>'{"sources":{},"pending":{},"observations":{}}'));
  state.sources ||= {}; state.pending ||= {}; state.observations ||= {};
  return {pack,root,docs:path.join(root,docs),manifest,work,stateFile,state};
}
function documentPath(config,source){
  if(config.pack==='romania'){
    const category=source.document_class;
    if(!['guidance','forms','procedure','case_law','legislation','oversight'].includes(category))throw Error(`Romania guidance source has no valid document_class: ${source.id}`);
    return path.join(config.docs,category,source.id+'.md');
  }
  return path.join(config.docs,source.id+'.md');
}
function catalogueDocumentUrl(bytes,source){
  let catalogue;
  try{catalogue=JSON.parse(bytes.toString('utf8'));}catch{throw Error('Official visa-document catalogue is not valid JSON');}
  if(!Array.isArray(catalogue.data))throw Error('Official visa-document catalogue has no data array');
  const matches=catalogue.data.filter(row=>Array.isArray(row)&&normalize(String(row[0]||''))===normalize(source.catalog_lookup.row_title));
  if(matches.length!==1)throw Error(`Expected one exact catalogue record for ${source.catalog_lookup.row_title}; found ${matches.length}`);
  const column=Number(source.catalog_lookup.file_column??4),candidate=String(matches[0][column]||'').trim();
  let parsed;
  try{parsed=new URL(candidate);}catch{throw Error('Catalogue record has no valid document URL');}
  if(parsed.protocol!=='https:'||!source.allowed_hosts.includes(parsed.hostname)||!/^\/document\/download\/[0-9a-f-]{36}(?:_en)?$/i.test(parsed.pathname)||parsed.search||parsed.hash)throw Error('Catalogue document URL failed the expected Commission download-path check');
  return parsed.href;
}
async function lifosCA(root) {
  const ca=await readFile(path.join(root,'references/certs/isrg-root-yr.pem'));
  const cert=new X509Certificate(ca);
  if(cert.fingerprint256!=='E5:7B:7E:6F:15:0C:41:91:02:E8:D5:C0:55:72:9F:F9:67:B9:D1:A8:29:BF:00:CE:C8:9C:A6:04:EB:F4:A8:6F' || !cert.verify(cert.publicKey))throw Error('LIFOS trust root does not match pinned official certificate');
  return ca;
}
async function retrieve(src, config) {
  const isLifos=src.url.startsWith('https://lifos.migrationsverket.se/');
  const ca=isLifos?await lifosCA(config.root):undefined;
  let landing=null, documentRequestUrl=src.url, response;
  if(src.catalog_lookup){
    landing=await fetchBytes(src.url,src.allowed_hosts,ca);
    documentRequestUrl=catalogueDocumentUrl(landing.bytes,src);
    response=await fetchBytes(documentRequestUrl,src.allowed_hosts,ca);
  }else response=await fetchBytes(src.url,src.allowed_hosts,ca);
  if(isLifos){
    landing=response;
    const html=response.bytes.toString('utf8');
    const attachment=[...html.matchAll(/<a\b[^>]*href="([^"]*documentAttachmentId=\d+[^"]*)"[^>]*>([^<]+\.pdf)<\/a>/gi)][0];
    if(!attachment)throw Error('Official LIFOS page has no PDF attachment');
    response=await fetchBytes(new URL(attachment[1].replace(/&amp;/g,'&'),response.url).href,src.allowed_hosts,ca);
  }
  const mediaType=response.type.split(';')[0].trim().toLowerCase();
  const ext=response.bytes.subarray(0,5).toString()==='%PDF-'?'pdf':mediaType==='application/json'||mediaType.endsWith('+json')?'json':mediaType==='text/html'||mediaType==='application/xhtml+xml'?'html':null;
  if(!ext)throw Error(`Unexpected official response type ${response.type||'(missing)'}`);
  if(isLifos && ext!=='pdf')throw Error('LIFOS attachment is not a PDF');
  if(ext==='pdf'&&!['application/pdf','application/octet-stream'].includes(mediaType))throw Error(`PDF signature conflicts with response type ${response.type}`);
  const converted=await convert(response.bytes,ext,response.type);
  if(normalize(converted.text).length<100)throw Error('Extracted source body too short');
  if(src.identity && !new RegExp(src.identity,'i').test(converted.text))throw Error('Configured source identity missing from extracted content');
  const pageHtml=src.catalog_lookup?'':landing?decodeText(landing.bytes,landing.type,src.url):ext==='html'?decodeText(response.bytes,response.type,response.url):'';
  const pageDates=pageHtml?pageDateMetadata(pageHtml):{};
  return {response,landing,documentRequestUrl,ext,converted,pageDates,contentHash:sha(normalize(converted.text)),rawHash:sha(response.bytes)};
}
export async function run(pack,action='sync',sourceId=null) {
  if(!['sync','verify','ack'].includes(action))throw Error('Usage: <denmark|sweden|romania|eu> <sync|verify|ack SOURCE_ID>');
  const c=await loadConfig(pack), report={pack,checked_at:new Date().toISOString(),results:[]};
  if(action==='ack'){
    const source=c.manifest.sources.find(row=>row.id===sourceId),pending=c.state.pending[sourceId];
    if(!source||!pending)throw Error('ack requires a known source ID with a pending update');
    const candidate=path.join(c.work,pending.candidate_path),bytes=await readFile(candidate);
    if(sha(bytes)!==pending.markdown_sha256)throw Error(`Pending Markdown hash mismatch: ${sourceId}`);
    const acceptedPath=documentPath(c,source);
    await mkdir(path.dirname(acceptedPath),{recursive:true});
    await atomicProjectWrite(acceptedPath,bytes);
    c.state.sources[sourceId]={...pending,accepted_at:report.checked_at};
    delete c.state.pending[sourceId];
    await atomicProjectWrite(c.stateFile,JSON.stringify(c.state,null,2)+'\n');
    await rm(candidate,{force:true});
    report.results.push({id:sourceId,status:'accepted_after_review',markdown_sha256:pending.markdown_sha256});
    await atomicProjectWrite(path.join(c.work,'latest-ack.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({pack,action,accepted:sourceId}));
    return report;
  }
  for(const src of c.manifest.sources){
    try {
      const mdPath=documentPath(c,src);
      if(action==='verify'){
        const accepted=c.state.sources[src.id], pending=c.state.pending[src.id], saved=accepted||pending||c.state.observations[src.id];
        if(!saved)throw Error('No saved accepted source or pending observation');
        const rawPath=saved.raw_path?path.join(c.work,saved.raw_path):path.join(c.work,'raw',src.id+'.'+saved.format);
        const bytes=await readFile(rawPath);
        if(sha(bytes)!==saved.raw_sha256)throw Error('Raw SHA-256 mismatch');
        const pageHtml=saved.landing_raw_path&&saved.landing_format!=='json'? decodeText(await readFile(path.join(c.work,saved.landing_raw_path)),saved.landing_content_type||'text/html',src.url) : saved.format==='html'?decodeText(bytes,saved.content_type||'text/html',src.url):'';
        const currentPageDates=pageHtml?pageDateMetadata(pageHtml):{};
        if(JSON.stringify(currentPageDates)!==JSON.stringify(saved.page_dates||{}))throw Error('Saved webpage date observations do not match the preserved official HTML');
        if(src.catalog_lookup){
          if(!saved.landing_raw_path)throw Error('Saved source is missing its official catalogue snapshot');
          const catalogue=await readFile(path.join(c.work,saved.landing_raw_path));
          if(catalogueDocumentUrl(catalogue,src)!==saved.document_request_url)throw Error('Saved catalogue record does not match the acquired PDF URL');
        }
        const converted=await convert(bytes,saved.format,saved.content_type||'');
        if(sha(normalize(converted.text))!==saved.content_sha256)throw Error('Conversion SHA-256 mismatch');
        const md=makeMarkdown(src,saved.final_url,saved.raw_sha256,converted,saved.format,saved.document_request_url||saved.final_url);
        if(accepted){if(await readFile(mdPath,'utf8')!==md)throw Error('Accepted Markdown does not match raw conversion');}
        else if(!pending)throw Error('Source has no accepted baseline or pending review record');
        if(saved.landing_sha256){const landingPath=saved.landing_raw_path?path.join(c.work,saved.landing_raw_path):path.join(c.work,'raw',src.id+'.landing.html');const landing=await readFile(landingPath);if(sha(landing)!==saved.landing_sha256)throw Error('Landing-page SHA-256 mismatch');}
        if(pending){const pendingRaw=await readFile(path.join(c.work,pending.raw_path)),candidate=await readFile(path.join(c.work,pending.candidate_path));if(sha(pendingRaw)!==pending.raw_sha256||sha(candidate)!==pending.markdown_sha256)throw Error('Pending source or Markdown hash mismatch');if(src.catalog_lookup){if(!pending.landing_raw_path)throw Error('Pending source is missing its official catalogue snapshot');const pendingCatalogue=await readFile(path.join(c.work,pending.landing_raw_path));if(sha(pendingCatalogue)!==pending.landing_sha256||catalogueDocumentUrl(pendingCatalogue,src)!==pending.document_request_url)throw Error('Pending catalogue snapshot does not match the acquired PDF URL');}const pendingText=await convert(pendingRaw,pending.format,pending.content_type||'');if(sha(normalize(pendingText.text))!==pending.content_sha256||candidate.toString('utf8')!==makeMarkdown(src,pending.final_url,pending.raw_sha256,pendingText,pending.format,pending.document_request_url||pending.final_url))throw Error('Pending Markdown differs from saved source conversion');}
        report.results.push({id:src.id,status:'verified',raw_sha256:saved.raw_sha256,content_sha256:saved.content_sha256,pages:converted.pages});
      } else {
        const item=await retrieve(src,c);
        const previous=c.state.sources[src.id];
        let status=!previous?'new':previous.content_sha256!==item.contentHash?'changed':previous.raw_sha256!==item.rawHash?'source-bytes-changed':'unchanged';
        const dateValues=dates=>Object.fromEntries(Object.entries(dates||{}).map(([field,value])=>[field,value?.date||null]));
        const pageDateChangeState=!previous||previous.page_dates===undefined?'baseline_required':JSON.stringify(dateValues(previous.page_dates))!==JSON.stringify(dateValues(item.pageDates))?'official_page_dates_changed':Object.keys(item.pageDates).length?'unchanged':'not_exposed';
        await mkdir(path.join(c.work,'raw'),{recursive:true}); await mkdir(c.docs,{recursive:true});
        const rawRel=path.posix.join('raw',`${src.id}--${item.rawHash}.${item.ext}`);
        await atomicProjectWrite(path.join(c.work,rawRel),item.response.bytes);
        let landingRel=null;
        if(item.landing){const landingHash=sha(item.landing.bytes),landingFormat=src.catalog_lookup?'json':'html';landingRel=path.posix.join('raw',`${src.id}--${landingHash}.landing.${landingFormat}`);await atomicProjectWrite(path.join(c.work,landingRel),item.landing.bytes);}
        const md=makeMarkdown(src,item.response.url,item.rawHash,item.converted,item.ext,item.documentRequestUrl);
        const observation={source_url:src.url,document_request_url:item.documentRequestUrl,final_url:item.response.url,format:item.ext,content_type:item.response.type||'',raw_path:rawRel,raw_sha256:item.rawHash,content_sha256:item.contentHash,markdown_sha256:sha(md),pages:item.converted.pages,landing_raw_path:landingRel,landing_format:item.landing?(src.catalog_lookup?'json':'html'):null,landing_content_type:item.landing?.type||'',landing_sha256:item.landing?sha(item.landing.bytes):null,page_dates:item.pageDates,previous_page_dates:previous?.page_dates||null,page_date_change_state:pageDateChangeState,checked_at:report.checked_at};
        c.state.observations[src.id]=observation;
        if(!previous){
          const bundled=await readFile(mdPath).catch(e=>{if(e.code==='ENOENT')return null;throw e;});
          if(bundled?.toString('utf8')===md){c.state.sources[src.id]={...observation,accepted_markdown_sha256:sha(bundled),accepted_at:report.checked_at};delete c.state.pending[src.id];status='baseline_matched';}
          else {const candidateRel=path.posix.join('pending',`${src.id}--${item.contentHash}.md`),candidate=path.join(c.work,candidateRel);await atomicProjectWrite(candidate,md);c.state.pending[src.id]={...observation,candidate_path:candidateRel};status=bundled?'bundled_copy_changed_pending_review':'first_observation_pending_review';}
        }
        else if(status==='changed'){
          const candidateRel=path.posix.join('pending',`${src.id}--${item.contentHash}.md`),candidate=path.join(c.work,candidateRel);
          const priorPending=c.state.pending[src.id];
          await atomicProjectWrite(candidate,md);c.state.pending[src.id]={...observation,candidate_path:candidateRel};
          if(priorPending?.candidate_path&&priorPending.candidate_path!==candidateRel)await rm(path.join(c.work,priorPending.candidate_path),{force:true});
        } else if(c.state.pending[src.id]){
          await rm(path.join(c.work,c.state.pending[src.id].candidate_path),{force:true});delete c.state.pending[src.id];
        }
        report.results.push({id:src.id,status:status==='changed'?'changed_pending_review':status,format:item.ext,bytes:item.response.bytes.length,pages:item.converted.pages,raw_sha256:item.rawHash,content_sha256:item.contentHash,page_dates:item.pageDates,previous_page_dates:previous?.page_dates||null,page_date_change_state:pageDateChangeState, ...(c.state.pending[src.id]?{candidate_path:c.state.pending[src.id].candidate_path}:{})});
      }
    } catch(e){report.results.push({id:src.id,status:'error',error:String(e.message||e)});}
    console.log(`${pack} ${report.results.at(-1).id}: ${report.results.at(-1).status}`);
  }
  if(action==='sync') {await mkdir(c.work,{recursive:true});await atomicProjectWrite(c.stateFile,JSON.stringify(c.state,null,2)+'\n');}
  await mkdir(c.work,{recursive:true});await atomicProjectWrite(path.join(c.work,'latest-'+action+'.json'),JSON.stringify(report,null,2)+'\n');
  const errors=report.results.filter(x=>x.status==='error').length;
  console.log(JSON.stringify({pack,action,total:report.results.length,errors,report:path.join(c.work,'latest-'+action+'.json')}));
  if(errors)process.exitCode=1;
  return report;
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await run(process.argv[2],process.argv[3],process.argv[4]);
