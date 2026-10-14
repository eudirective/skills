#!/usr/bin/env node
// Official Publications Office fallback for CELEX 32013H0461 Swedish text.
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {atomicProjectWrite, projectTempPath} from '../runtime-storage.mjs';

const root=path.dirname(fileURLToPath(import.meta.url));
const resolver='https://publications.europa.eu/resource/celex/32013H0461.SWE';
const out=path.join(root,'sweden/core/eu/eu_32013h0461_SV.md');
const work=projectTempPath(path.join(root,'work'));
const raw=path.join(work,'raw/solvit-2013-461-sv.xhtml');
const stateFile=path.join(work,'solvit-2013-461-sv-state.json');
const hash=b=>createHash('sha256').update(b).digest('hex');

async function source(){
  const r=await fetch(resolver,{redirect:'manual',headers:{accept:'application/xhtml+xml','user-agent':'visa-skills-source-maintenance/2.0'},signal:AbortSignal.timeout(30000)});
  if(![301,302,303,307,308].includes(r.status))throw Error('Publications Office resolver did not supply an XHTML document');
  const location=new URL(r.headers.get('location'),resolver);
  if(location.hostname!=='publications.europa.eu'||!location.pathname.startsWith('/resource/cellar/'))throw Error('Resolver left official Publications Office');
  location.protocol='https:';
  const result=await fetch(location,{redirect:'manual',headers:{accept:'application/xhtml+xml','user-agent':'visa-skills-source-maintenance/2.0'},signal:AbortSignal.timeout(30000)});
  if(!result.ok||result.url!==location.href)throw Error('Official XHTML retrieval failed');
  const bytes=Buffer.from(await result.arrayBuffer());
  if(!result.headers.get('content-type')?.includes('xhtml'))throw Error('Source is not official XHTML');
  return {bytes,url:location.href};
}
function convert(bytes,url){
  const html=bytes.toString('utf8'),start=html.indexOf('<div class="eli-container">');
  if(start<0||!html.includes('L_2013249SV'))throw Error('Swedish Official Journal identity mismatch');
  const content=html.slice(start,html.indexOf('</body>',start));
  const clean=content.replace(/<!--([\s\S]*?)-->/g,' ')
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,' ')
    .replace(/<\/(?:p|div|tr|h[1-6]|li)>|<br\s*\/?>/gi,'\n')
    .replace(/<[^>]+>/g,' ')
    .replace(/&#(x[\da-f]+|\d+);/gi,(_,n)=>{const v=n[0].toLowerCase()==='x'?parseInt(n.slice(1),16):parseInt(n,10);return String.fromCodePoint(v);})
    .replace(/&nbsp;/g,' ').replace(/&amp;/g,'&').replace(/&quot;/g,'"')
    .replace(/[\t ]+/g,' ').replace(/ *\n */g,'\n').replace(/\n{3,}/g,'\n\n').trim();
  if(clean.length<15000||!/KOMMISSIONENS REKOMMENDATION/.test(clean)||!/om principerna för Solvit/i.test(clean)||!/2013\/461\/EU/.test(clean))throw Error('Swedish recommendation text identity or length mismatch');
  return `# Kommissionens rekommendation 2013/461/EU om principerna för Solvit\n\n- Language: SV\n- Official source: ${resolver}\n- Retrieved XHTML: ${url}\n- Source SHA-256: ${hash(bytes)}\n\n${clean}\n`;
}
async function run(action='sync'){
  if(!['sync','verify'].includes(action))throw Error('Usage: node sync-swedish-recommendation.mjs sync|verify');
  const state=JSON.parse(await readFile(stateFile,'utf8').catch(()=>'{}'));
  const item=action==='sync'?await source():{bytes:await readFile(raw),url:state.final_url};
  const md=convert(item.bytes,item.url),sourceHash=hash(item.bytes),mdHash=hash(md);
  if(action==='verify'){
    if(state.source_sha256!==sourceHash||state.markdown_sha256!==mdHash||await readFile(out,'utf8')!==md)throw Error('Saved Swedish recommendation fails source/conversion verification');
    console.log(JSON.stringify({status:'verified',source_sha256:sourceHash,markdown_sha256:mdHash}));return;
  }
  await atomicProjectWrite(raw,item.bytes);await atomicProjectWrite(out,md);
  const entry={source_url:resolver,final_url:item.url,source_sha256:sourceHash,markdown_sha256:mdHash,checked_at:new Date().toISOString()};
  await atomicProjectWrite(stateFile,JSON.stringify(entry,null,2)+'\n');
  const indexFile=path.join(root,'retrieval-index.json'),index=JSON.parse(await readFile(indexFile,'utf8'));
  const record=index.find(x=>x.source_id==='eu:32013h0461'&&x.language==='SV');
  if(!record)throw Error('Registered Swedish representation not found');
  Object.assign(record,{relative_path:'sweden/core/eu/eu_32013h0461_SV.md',library_relative_path:'sweden/core/eu/eu_32013h0461_SV.md',official_source:resolver,retrieved_url:item.url,canonical_eli_url:'https://eur-lex.europa.eu/eli/reco/2013/461/oj/swe',canonical_document_url:resolver,official_html_sha256:sourceHash,markdown_sha256:mdHash,status:'retrieved_and_converted',retrieved_at:entry.checked_at,retrieval_time:entry.checked_at,converter:'Node.js Publications Office XHTML / solvit-sv-v1',library_content_state:'retrieved_full_text_candidate_not_trust_promoted'});
  delete record.reason;delete record.quality_note;
  await atomicProjectWrite(indexFile,JSON.stringify(index,null,2)+'\n');
  const mirrorIndexFile=path.join(root,'national-language-index-SV.json'),mirrorIndex=JSON.parse(await readFile(mirrorIndexFile,'utf8'));
  const mirror=mirrorIndex.entries.find(x=>x.source_id==='eu:32013h0461');
  if(!mirror)throw Error('Swedish mirror record not found');
  Object.assign(mirror,{official_source:resolver,requested_urls:[resolver],final_url:item.url,mode:'publications-office-xhtml',official_response_sha256:sourceHash,markdown_sha256:mdHash,converter:'Node.js Publications Office XHTML / solvit-sv-v1'});
  await atomicProjectWrite(mirrorIndexFile,JSON.stringify(mirrorIndex,null,2)+'\n');
  const mirrorStateFile=path.join(root,'national-language-state-SV.json'),mirrorState=JSON.parse(await readFile(mirrorStateFile,'utf8'));
  Object.assign(mirrorState.sources['eu:32013h0461'],{accepted_official_response_sha256:sourceHash,accepted_content_sha256:hash(md.split('\n\n').slice(2).join('\n\n').replace(/\s+/g,' ').trim()),accepted_markdown_sha256:mdHash,baseline_status:'official_publications_office_retrieval'});
  await atomicProjectWrite(mirrorStateFile,JSON.stringify(mirrorState,null,2)+'\n');
  console.log(JSON.stringify({status:'synced',source_sha256:sourceHash,markdown_sha256:mdHash,document:out}));
}
await run(process.argv[2]||'sync');
