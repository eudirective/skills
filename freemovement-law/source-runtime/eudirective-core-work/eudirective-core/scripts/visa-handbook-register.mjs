#!/usr/bin/env node
// Retrieves the superseded 2020 Handbook I annex by official Commission register ID.
import {createHash} from 'node:crypto';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {atomicProjectWrite,projectTempPath} from '../../../runtime-storage.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../../../eudirective-source-library-0.6.0/visa-code-handbook-i-2020');
const work=projectTempPath(path.join(root,'work'));
const rawDir=projectTempPath(path.join(root,'raw'));
const metaUrl='https://ec.europa.eu/transparency/documents-register/api/search/C%282020%29395?lang=en';
const filesBase='https://ec.europa.eu/transparency/documents-register/api/files/C%282020%29395_1/';
const catalogueUrl='https://ec.europa.eu/assets/home/visa-documents/visa-documents.json';
const digest=b=>createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(await readFile(path.join(root,'manifest.json'),'utf8'));
const stateFile=path.join(work,'state.json');
const state=JSON.parse(await readFile(stateFile,'utf8').catch(()=>'{"languages":{}}'));
state.languages||={};

async function official(url){
  const u=new URL(url);
  if(u.protocol!=='https:'||u.hostname!=='ec.europa.eu'||!u.pathname.startsWith('/transparency/documents-register/api/'))throw Error('Unapproved Commission register URL '+url);
  const r=await fetch(url,{redirect:'manual',headers:{'user-agent':'visa-skills-source-maintenance/2.0'},signal:AbortSignal.timeout(90000)});
  if(!r.ok)throw Error(`Commission register HTTP ${r.status}: ${url}`);
  if(r.url!==url)throw Error('Unexpected Commission register redirect');
  return Buffer.from(await r.arrayBuffer());
}
async function sourceText(bytes){
  const pdfjs=await import('pdfjs-dist/legacy/build/pdf.mjs');
  const doc=await pdfjs.getDocument({data:new Uint8Array(bytes),useSystemFonts:true,isEvalSupported:false}).promise;
  const pages=[];
  for(let n=1;n<=doc.numPages;n++){
    const tc=await (await doc.getPage(n)).getTextContent({includeMarkedContent:false});
    let y=null,line=[],lines=[];
    for(const item of tc.items){if(!item.str)continue;const ny=item.transform?.[5]??0;if(y!==null&&Math.abs(ny-y)>3){lines.push(line.join(' '));line=[];}line.push(item.str);y=ny;}
    if(line.length)lines.push(line.join(' '));pages.push(lines.join('\n'));
  }
  return {text:pages.join('\n\n'),pages:doc.numPages};
}
function verifyIdentity(text,language){
  const front=text.slice(0,1200).replace(/\s+/g,' ').trim();
  if(!new RegExp('^'+language+'\\s+'+language+'\\b','i').test(front))throw Error(`PDF language marker is not ${language}`);
  if(!/C\s*\(\s*2020\s*\)\s*395\s+final/i.test(front))throw Error('PDF does not identify C(2020) 395 final');
  if(text.length<20000)throw Error('Handbook text unexpectedly short');
}
function markdown(lang,sourceUrl,hash,body){
  return `# Visa Code Handbook I (2020) — ${lang.name}\n\n- Edition: Commission Implementing Decision C(2020) 395 final, annex\n- Status: superseded language reference; use the 2024 edition for current guidance\n- Language: ${lang.code}\n- Official Commission register PDF: ${sourceUrl}\n- Source SHA-256: ${hash}\n- PDF pages: ${body.pages}\n\n${body.text.trim()}\n`;
}
async function register(){
  const bytes=await official(metaUrl),record=JSON.parse(bytes.toString('utf8'));
  if(record.reference!=='C(2020)395')throw Error('Commission register reference mismatch');
  const annex=record.attachments?.find(x=>x.sequence===1&&x.main===false);
  if(!annex||!annex.linguisticVersions?.en)throw Error('Commission register annex missing');
  return {bytes,record,annex};
}
export async function run(action='sync'){
  if(!['sync','verify','inventory'].includes(action))throw Error('Usage: node scripts/visa-handbook-register.mjs <sync|verify|inventory>');
  const reg=action==='verify'?null:await register();
  if(action==='inventory'){console.log(JSON.stringify({reference:reg.record.reference,annex_languages:Object.keys(reg.annex.linguisticVersions).sort(),declared_languages:manifest.languages.map(x=>x.code),register_url:metaUrl},null,2));return;}
  const report={edition:'C(2020) 395 final',action,checked_at:new Date().toISOString(),register_url:metaUrl,results:[]};
  let savedRegister=null;
  if(action==='verify'){
    const registerPath=state.register_path?projectTempPath(path.join(root,state.register_path)):path.join(rawDir,'commission-register-record.json');
    const raw=await readFile(registerPath);
    if(digest(raw)!==state.register_sha256)throw Error('Saved Commission register metadata hash mismatch');
    savedRegister=JSON.parse(raw.toString('utf8'));
  }
  if(action==='sync'){
    await mkdir(rawDir,{recursive:true});
    const registerHash=digest(reg.bytes),registerRel=`raw/commission-register-record--${registerHash}.json`;
    await atomicProjectWrite(projectTempPath(path.join(root,registerRel)),reg.bytes);
    state.register_sha256=registerHash;state.register_url=metaUrl;state.register_path=registerRel;
    report.register_languages=Object.keys(reg.annex.linguisticVersions).map(x=>x.toUpperCase()).sort();
    report.new_register_languages=report.register_languages.filter(x=>!manifest.languages.some(y=>y.code===x));
  }
  for(const lang of manifest.languages){
    const code=lang.code,low=code.toLowerCase(),version=reg?.annex.linguisticVersions?.[low];
    try{
      if(action==='sync'&&!version){state.languages[code]={status:'not_published_in_register',checked_at:report.checked_at};report.results.push({language:code,status:'not_published_in_register'});continue;}
      const saved=state.languages[code];
      if(action==='verify'&&!saved?.source_url){
        const annex=savedRegister.attachments.find(x=>x.sequence===1&&x.main===false);
        if(!annex.linguisticVersions?.[low]){report.results.push({language:code,status:'not_published_in_register'});continue;}
        throw Error('No saved source');
      }
      const url=action==='sync'?filesBase+version.ersId:saved.source_url;
      const bytes=action==='sync'?await official(url):await readFile(saved.raw_path?projectTempPath(path.join(root,saved.raw_path)):path.join(rawDir,`${code}.pdf`));
      if(bytes.subarray(0,5).toString()!=='%PDF-'||!bytes.subarray(-4096).includes(Buffer.from('%%EOF')))throw Error('Incomplete PDF');
      const hash=digest(bytes),body=await sourceText(bytes);
      verifyIdentity(body.text,code);
      const md=markdown(lang,url,hash,body);
      const file=path.join(root,'accepted',`visa-code-handbook-i-2020_${code}.md`);
      if(action==='verify'){
        if(saved.source_sha256!==hash)throw Error('Source SHA-256 mismatch');
        if(await readFile(file,'utf8')!==md)throw Error('Markdown differs from saved PDF conversion');
        report.results.push({language:code,status:'verified',bytes:bytes.length,pages:body.pages,sha256:hash});
      }else{
        const status=!saved?.source_sha256?'new':saved.source_sha256===hash?'unchanged':'changed';
        await mkdir(path.dirname(file),{recursive:true});
        const rawRel=`raw/${code}--${hash}.pdf`;
        await atomicProjectWrite(projectTempPath(path.join(root,rawRel)),bytes);
        await atomicProjectWrite(file,md);
        state.languages[code]={status:'accepted',source_url:url,raw_path:rawRel,source_sha256:hash,markdown_sha256:digest(md),ers_id:version.ersId,pages:body.pages,bytes:bytes.length,checked_at:report.checked_at};
        report.results.push({language:code,status,bytes:bytes.length,pages:body.pages,sha256:hash,ers_id:version.ersId});
      }
      console.log(`${code}: ${report.results.at(-1).status} (${body.pages} pages)`);
    }catch(e){report.results.push({language:code,status:'error',error:String(e.message||e)});console.log(`${code}: error ${e.message}`);}
  }
  if(action==='sync'){
    try{
      const response=await fetch(catalogueUrl,{headers:{'user-agent':'visa-skills-source-maintenance/2.0'},signal:AbortSignal.timeout(30000)});
      if(!response.ok||new URL(response.url).hostname!=='ec.europa.eu')throw Error('Official catalogue response invalid');
      const bytes=Buffer.from(await response.arrayBuffer()),data=JSON.parse(bytes.toString('utf8'));
      if(!Array.isArray(data.data))throw Error('Official catalogue has no data array');
      const entries=data.data.filter(x=>/Visa Code Handbook I(?!I)/i.test(String(x[0]||''))).map(x=>({title:x[0],date:x[3],url:x[4]}));
      report.edition_catalog={url:catalogueUrl,sha256:digest(bytes),entries,known_2024_listed:entries.some(x=>String(x.title).includes('C(2024) 4319')),newer_than_2024:entries.filter(x=>{const m=String(x.title).match(/C\((\d{4})\)\s*(\d+)/);return m&&(Number(m[1])>2024||(Number(m[1])===2024&&Number(m[2])>4319));})};
      const catalogueHash=digest(bytes),catalogueRel=`raw/visa-documents-catalogue--${catalogueHash}.json`;
      await atomicProjectWrite(projectTempPath(path.join(root,catalogueRel)),bytes);
      report.edition_catalog.raw_path=catalogueRel;
    }catch(e){report.edition_catalog={status:'error',error:String(e.message||e)};}
  }
  if(action==='sync'){state.updated_at=report.checked_at;await atomicProjectWrite(stateFile,JSON.stringify(state,null,2)+'\n');}
  await atomicProjectWrite(path.join(work,`latest-${action}.json`),JSON.stringify(report,null,2)+'\n');
  if(action==='sync')await atomicProjectWrite(path.join(work,'latest-report.json'),JSON.stringify(report,null,2)+'\n');
  const failures=report.results.filter(x=>x.status==='error').length+(report.edition_catalog?.status==='error'?1:0);
  console.log(JSON.stringify({action,available:report.results.filter(x=>!['error','not_published_in_register'].includes(x.status)).length,not_published:report.results.filter(x=>x.status==='not_published_in_register').length,failures}));
  if(failures)process.exitCode=1;
  return report;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await run(process.argv[2]||'sync');
