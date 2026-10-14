#!/usr/bin/env node
// Deterministic retrieval, conversion, change detection, and official-link discovery for the Hungary pack.
import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { atomicProjectWrite, makeProjectTempDir, projectTempPath } from '../../../runtime-storage.mjs';
import tesseract from 'tesseract.js';
import hungarianOcrData from '@tesseract.js-data/hun';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifest = JSON.parse(await readFile(path.join(ROOT, 'references/manifest.json'), 'utf8'));
const args = new Set(process.argv.slice(2));
const mode = args.has('--verify') ? 'verify' : args.has('--reconvert') ? 'reconvert' : args.has('--sync') ? 'sync' : args.has('--discover') ? 'discover' : 'check';
const sha = value => createHash('sha256').update(value).digest('hex');
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const WORK = projectTempPath(path.join(ROOT, 'work'));
const jsonPath = path.join(WORK, 'state.json');
const reportPath = path.join(WORK, 'latest-report.json');
const reconvertReportPath = path.join(WORK, 'latest-reconversion.json');
const CONVERTER_VERSION = 'hungary-source-md-v2-page-ocr';
let state = { schema_version: 1, sources: {}, discoveries: [] };
try { state = JSON.parse(await readFile(jsonPath, 'utf8')); } catch (e) { if (e.code !== 'ENOENT') throw e; }
const allSources = [...manifest.laws.filter(x => !x.discovery_only).map(x => ({ ...x, kind: 'law' })), ...manifest.oif_pages.filter(x => !x.discovery_only).map(x => ({ ...x, kind: 'oif' }))];
const discoverySources = manifest.discovery.flatMap(row => row.url.includes('{year}')
  ? [0,1,2].map(offset => ({ ...row, id: `${row.id}-${new Date().getUTCFullYear()-offset}`, url: row.url.replace('{year}', String(new Date().getUTCFullYear()-offset)) }))
  : [row]);
const text = b => new TextDecoder('utf-8').decode(b);
function cleanHtml(html) {
  const balancedDivById = id => {
    const open = /<div\b[^>]*>/gi; let m, start = -1;
    while ((m = open.exec(html))) if (new RegExp(`\\bid=["']${id}["']`, 'i').test(m[0])) { start = m.index; break; }
    if (start < 0) return '';
    const tags = /<\/?div\b[^>]*>/gi; tags.lastIndex = start; let depth = 0, t;
    while ((t = tags.exec(html))) { if (/^<\//.test(t[0])) depth--; else if (!/\/\s*>$/.test(t[0])) depth++; if (!depth) return html.slice(start, tags.lastIndex); }
    return '';
  };
  const getBlock = tag => {
    const re = new RegExp(`<${tag}\\b[^>]*>[\\s\\S]*?<\\/${tag}>`, 'i');
    return html.match(re)?.[0] || '';
  };
  let body = balancedDivById('div_Formaconsolidata')
    || getBlock('main') || getBlock('article') || getBlock('body') || html;
  body = body.replace(/<!--([\s\S]*?)-->/g, ' ').replace(/<(script|style|nav|header|footer|noscript|svg|form|aside)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<br\b[^>]*>/gi, '\n').replace(/<\/(p|h[1-6]|li|tr|section|article|div|table|ol|ul)\s*>/gi, '\n')
    .replace(/<[^>]+>/g, ' ').replace(/&nbsp;|&#160;/gi, ' ').replace(/&amp;/gi, '&').replace(/&lt;/gi, '<').replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"').replace(/&#39;|&apos;/gi, "'").replace(/&sect;/gi, '§').replace(/&ndash;/gi, '–').replace(/&mdash;/gi, '—').replace(/&ouml;/gi, 'ö').replace(/&uuml;/gi, 'ü').replace(/&aacute;/gi, 'á').replace(/&eacute;/gi, 'é').replace(/&iacute;/gi, 'í').replace(/&oacute;/gi, 'ó').replace(/&uacute;/gi, 'ú').replace(/&odblac;/gi, 'ő').replace(/&udblac;/gi, 'ű').replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&#x([\da-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16))).replace(/[\t\u00a0 ]+/g, ' ')
    .replace(/ *\n */g, '\n').replace(/\n{3,}/g, '\n\n').trim();
  return body;
}
async function pdfText(bytes) {
  const { getDocument } = await import('pdfjs-dist/legacy/build/pdf.mjs');
  const doc = await getDocument({ data: new Uint8Array(bytes), useSystemFonts: true }).promise;
  const pages = [];
  for (let n = 1; n <= doc.numPages; n++) {
    const page = await doc.getPage(n), content = await page.getTextContent(), [, , width] = page.view;
    const lines = [];
    for (const item of content.items) {
      const value = item.str?.trim(); if (!value) continue;
      const [x, y] = item.transform.slice(4, 6);
      if (y < 18 || /^\d{1,3}$/.test(value) && x > width * 0.85 && y < 100) continue;
      let line = lines.find(x => Math.abs(x.y - y) <= 3.5); if (!line) { line = { y, items: [] }; lines.push(line); }
      line.items.push({ x, w: item.width || 0, s: item.height || 10, value });
    }
    pages.push(lines.sort((a,b) => b.y-a.y).map(line => {
      let out = '', last;
      for (const p of line.items.sort((a,b) => a.x-b.x)) { if (out && last && p.x-(last.x+last.w) > Math.max(1.2,p.s*0.16) && !out.endsWith(' ') && !p.value.startsWith(' ')) out += ' '; out += p.value; last=p; }
      return out.trim();
    }).filter(Boolean).join('\n'));
  }
  const sparsePages = pages.map((page, index) => page.trim().length < 80 ? index : -1).filter(index => index >= 0);
  if (!sparsePages.length) return pages.join('\n\n').replace(/[\t ]+\n/g,'\n').replace(/\n{3,}/g,'\n\n').trim();

  const tempDir = await makeProjectTempDir('hungary-pdf-ocr-');
  const pdfPath = path.join(tempDir, 'source.pdf');
  const imagePrefix = path.join(tempDir, 'page');
  let worker;
  try {
    await writeFile(pdfPath, bytes);
    const rendered = spawnSync(process.env.PDFTOPPM_PATH || 'pdftoppm', ['-png', '-r', '300', pdfPath, imagePrefix], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
    if (rendered.error || rendered.status !== 0) throw Error(`scanned PDF page rendering failed: ${rendered.error?.message || rendered.stderr || rendered.status}`);
    const pageImages = (await readdir(tempDir)).filter(name => /^page-\d+\.png$/i.test(name)).sort((a,b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]));
    if (!pageImages.length) throw Error('scanned PDF rendering produced no page images');
    worker = await tesseract.createWorker('hun', tesseract.OEM.LSTM_ONLY, { langPath: hungarianOcrData.langPath, gzip: hungarianOcrData.gzip, logger: () => {} });
    const scannedPages = [...pages];
    for (const index of sparsePages) {
      const imageName = pageImages[index];
      if (!imageName) throw Error(`scanned PDF rendering omitted page ${index + 1}`);
      const result = await worker.recognize(path.join(tempDir, imageName));
      scannedPages[index] = result.data.text.trim();
    }
    return scannedPages.join('\n\n').replace(/[\t ]+\n/g,'\n').replace(/\n{3,}/g,'\n\n').trim();
  } finally {
    if (worker) await worker.terminate();
    await rm(tempDir, { recursive: true, force: true });
  }
}
function frontmatter(source, url, rawHash, bodyHash, body) {
  const title = source.citation || source.id;
  return `---\nsource_id: ${JSON.stringify(source.id)}\npublisher: ${JSON.stringify(source.publisher || (source.kind === 'law' ? 'Nemzeti Jogszabálytár' : 'Országos Idegenrendészeti Főigazgatóság'))}\ncategory: ${JSON.stringify(source.category)}\nlanguage: hu\nsource_url: ${JSON.stringify(url)}\nraw_sha256: ${rawHash}\nbody_sha256: ${bodyHash}\nconverter: ${CONVERTER_VERSION}\n---\n\n# ${title}\n\n${body.trim()}\n`;
}
async function fetchOfficial(url) {
  let current = url;
  for (let hop = 0; hop < 6; hop++) {
    const u = new URL(current);
    if (u.protocol !== 'https:' || !manifest.official_hosts.includes(u.hostname)) throw Error(`non-official or insecure URL refused: ${current}`);
    let r;
    try { r = await fetch(current, { redirect: 'manual', headers: { 'user-agent': 'HungaryNationalSourceSystem/0.1.0', accept: 'text/html,application/xhtml+xml,application/pdf' } }); }
    catch (e) { throw Error(`request failed (${e.cause?.code || e.cause?.message || e.message}): ${current}`); }
    if ([301,302,303,307,308].includes(r.status)) { const loc=r.headers.get('location'); if (!loc) throw Error(`redirect without Location: ${current}`); current=new URL(loc,current).href; continue; }
    if (!r.ok) throw Error(`HTTP ${r.status} ${r.statusText}: ${current}`);
    const bytes=Buffer.from(await r.arrayBuffer()); if (!bytes.length) throw Error(`empty response: ${current}`);
    return { bytes, url: current, contentType: r.headers.get('content-type') || '' };
  }
  throw Error(`redirect limit reached: ${url}`);
}
async function atomic(file, data) {
  await atomicProjectWrite(file, data);
}
function pageLinks(html, base) {
  const out=[];
  for (const m of html.matchAll(/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)) {
    try { const u=new URL(m[1],base); if (!manifest.official_hosts.includes(u.hostname) || u.protocol !== 'https:') continue;
      const baseUrl=new URL(base); if (u.origin===baseUrl.origin && u.pathname===baseUrl.pathname && u.search===baseUrl.search) continue;
      const label=cleanHtml(m[2]);
      const isNjt = u.hostname === 'njt.jog.gov.hu';
      const relevant = /szabad mozg|idegenrend|mened[eé]k|k[uü]lf[oö]ldi|adatv[eé]delem|k[oö]z[eé]rdek[uű] adat|k[oö]zirat|anyak[oö]nyv|szem[eé]lyi adat|lakc[ií]m|tart[oó]zkod[aá]s|v[ií]zum|elj[aá]r[aá]si d[ií]j|digit[aá]lis [aá]llam/i.test(label);
      const isPdf = /\.pdf(?:$|[?#])/i.test(`${u.pathname}${u.search}`);
      const archiveStatForm = /106[-_ ]?(?:TI|Ált|Alt)|106.*(?:6332|201)[-_ ]?2026/i.test(decodeURIComponent(`${u.href} ${label}`));
      if ((isNjt && u.pathname.includes('/eli/') && relevant) || (!isNjt && (archiveStatForm || isPdf || /formanyomtatv|statisztik|szerz[oő]d[eé]s|adatlap|v[eé]grehajt[aá]si|jogszab[aá]ly|hat[aá]rozat|k[oö]zbeszerz[eé]s|d[ií]j|ad[aá]tv[eé]d/i.test(`${u.href} ${label}`)))) out.push({ url:u.href, label });
    } catch {}
  }
  return [...new Map(out.map(x=>[x.url,x])).values()].sort((a,b)=>a.url.localeCompare(b.url));
}
if (mode === 'verify') {
  const failures=[];
  const expectedIds = new Set(allSources.map(source => source.id));
  const actualIds = new Set(Object.keys(state.sources));
  for (const id of expectedIds) if (!actualIds.has(id)) failures.push({id,error:'active manifest source is missing from saved state'});
  for (const id of actualIds) if (!expectedIds.has(id)) failures.push({id,error:'saved state source is absent from the active manifest'});
  if (expectedIds.size !== allSources.length) failures.push({id:'manifest',error:'duplicate active source IDs'});
  for (const [id, row] of Object.entries(state.sources)) {
    try {
      const raw=await readFile(projectTempPath(path.join(ROOT,row.raw_path)));
      if (sha(raw)!==row.raw_sha256) throw Error('raw hash mismatch');
      const body=raw.subarray(0,5).toString()==='%PDF-' ? await pdfText(raw) : cleanHtml(text(raw));
      if (sha(Buffer.from(body))!==row.body_sha256) throw Error('converted body hash mismatch');
      const md=await readFile(path.join(ROOT,row.markdown_path),'utf8');
      if (!md.includes(`body_sha256: ${row.body_sha256}`) || !md.endsWith(`${body.trim()}\n`)) throw Error('Markdown replay mismatch');
    } catch(e) { failures.push({id,error:e.message}); }
  }
  console.log(JSON.stringify({mode,checked:Object.keys(state.sources).length,failures},null,2));
  if (failures.length) process.exitCode=1;
} else if (mode === 'reconvert') {
  const failures=[], staged=[];
  for (const source of allSources) {
    try {
      const row=state.sources[source.id];
      if (!row) throw Error('source is missing from saved state');
      const raw=await readFile(projectTempPath(path.join(ROOT,row.raw_path)));
      if (sha(raw)!==row.raw_sha256) throw Error('raw hash mismatch');
      const body=raw.subarray(0,5).toString()==='%PDF-' ? await pdfText(raw) : cleanHtml(text(raw));
      if (body.length<120) throw Error(`extracted official content too short (${body.length})`);
      if (source.kind==='law') {
        const lower=body.toLocaleLowerCase('hu'), expected=source.citation.toLocaleLowerCase('hu');
        if (!(source.special_title ? source.special_title.some(x=>lower.includes(x.toLocaleLowerCase('hu'))) : lower.includes(expected))) throw Error(`title/citation validation failed for ${source.citation}`);
      }
      if (source.validation_markers?.length) {
        const lower=body.toLocaleLowerCase('hu'), missing=source.validation_markers.filter(marker=>!lower.includes(marker.toLocaleLowerCase('hu')));
        if (missing.length) throw Error(`source identity validation failed; missing markers: ${missing.join(', ')}`);
      }
      const bodyHash=sha(Buffer.from(body));
      staged.push({source,row,bodyHash,changed:row.body_sha256!==bodyHash,markdown:frontmatter(source,row.url,row.raw_sha256,bodyHash,body)});
    } catch(e) { failures.push({id:source.id,error:e.message}); }
  }
  if (!failures.length) {
    for (const item of staged) {
      await atomic(path.join(ROOT,item.row.markdown_path),item.markdown);
      item.row.body_sha256=item.bodyHash;
      item.row.converter_version=CONVERTER_VERSION;
    }
    state.checked_at=now();
    await atomic(jsonPath,JSON.stringify(state,null,2)+'\n');
  }
  const report={mode,converter_version:CONVERTER_VERSION,checked:staged.length,updated:staged.filter(x=>x.changed).length,failures};
  await atomic(reconvertReportPath,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
  if (failures.length) process.exitCode=1;
} else {
  const failures=[], discoveryFailures=[], fetched=[], discoveries=[], pendingWrites=[];
  for (const source of allSources) {
    try {
      const got=await fetchOfficial(source.url);
      const rawHash=sha(got.bytes), rawExt=got.bytes.subarray(0,5).toString()==='%PDF-'?'pdf':'html';
      const body=rawExt==='pdf' ? await pdfText(got.bytes) : cleanHtml(text(got.bytes));
      if (body.length < 120) throw Error(`extracted official content too short (${body.length})`);
      if (source.kind==='law') {
        const expected = source.citation.toLocaleLowerCase('hu');
        const extracted = body.toLocaleLowerCase('hu');
        if (!(source.special_title ? source.special_title.some(x => extracted.includes(x.toLocaleLowerCase('hu'))) : extracted.includes(expected))) throw Error(`title/citation validation failed for ${source.citation}`);
      }
      if (source.validation_markers?.length) {
        const extracted = body.toLocaleLowerCase('hu');
        const missing = source.validation_markers.filter(marker => !extracted.includes(marker.toLocaleLowerCase('hu')));
        if (missing.length) throw Error(`source identity validation failed; missing markers: ${missing.join(', ')}`);
      }
      const bodyHash=sha(Buffer.from(body)), old=state.sources[source.id];
      const rawRel=`work/raw/${source.id}/${rawHash}.${rawExt}`, mdRel=`documents/${source.kind==='law'?'laws':'oif'}/${source.category}/${source.id}.md`;
      const result={id:source.id,url:got.url,status:old?.body_sha256===bodyHash?'unchanged':old?'changed':'new',raw_sha256:rawHash,body_sha256:bodyHash,content_type:got.contentType};
      fetched.push(result);
      if (mode==='sync') {
        pendingWrites.push({file:projectTempPath(path.join(ROOT,rawRel)),data:got.bytes});
        pendingWrites.push({file:path.join(ROOT,mdRel),data:frontmatter(source,got.url,rawHash,bodyHash,body)});
        state.sources[source.id]={...result,category:source.category,raw_path:rawRel,markdown_path:mdRel,converter_version:CONVERTER_VERSION};
      }
      if (source.kind==='oif' && got.contentType.includes('html')) discoveries.push(...pageLinks(text(got.bytes),got.url).map(x=>({ ...x, discovered_from:source.id })));
    } catch(e) { failures.push({id:source.id,url:source.url,error:e.message}); }
  }
  for (const source of discoverySources) {
    try {
      const got=await fetchOfficial(source.url);
      if (!got.contentType.includes('html')) throw Error(`catalogue is not HTML (${got.contentType})`);
      discoveries.push(...pageLinks(text(got.bytes),got.url).map(x=>({ ...x, discovered_from:source.id })));
    } catch(e) { discoveryFailures.push({id:source.id,url:source.url,error:e.message}); }
  }
  const unique=[...new Map(discoveries.map(x=>[x.url,x])).values()].sort((a,b)=>a.url.localeCompare(b.url));
  const previous=new Set(state.discoveries.map(x=>x.url));
  const novel=unique.filter(x=>!previous.has(x.url));
  if (mode==='sync' && failures.length===0 && discoveryFailures.length===0) {
    try {
      for (const item of pendingWrites) await atomic(item.file,item.data);
      state.discoveries=unique; state.checked_at=now();
      await atomic(jsonPath,JSON.stringify(state,null,2)+'\n');
    } catch (e) { failures.push({id:'sync-commit',error:e.message}); }
  }
  const archiveTargetMatches=(manifest.archive_targets||[]).map(target=>{const expected=(target.official_filename||target.title).toLocaleLowerCase('hu');const matches=unique.filter(x=>{let pathname='';try{pathname=decodeURIComponent(new URL(x.url).pathname)}catch{}return `${pathname} ${x.label}`.toLocaleLowerCase('hu').includes(expected)}).map(x=>x.url);const pinned=state.sources[target.resolved_source_id];return{id:target.id,title:target.title,resolved_source_id:target.resolved_source_id||null,official_file_url:target.official_file_url||null,pinned_source_retrieved:Boolean(pinned),pinned_source_status:pinned?.status||null,discovered_official_matches:matches}});
  const report={schema_version:1,pack:manifest.pack,mode,run_at:now(),source_count:allSources.length,success_count:fetched.length,failure_count:failures.length+discoveryFailures.length,fetched,failures,discovery_failures:discoveryFailures,archive_targets:manifest.archive_targets||[],archive_target_matches:archiveTargetMatches,discovery:{count:unique.length,new_count:novel.length,items:mode==='discover'?unique:novel}};
  await atomic(reportPath,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({mode,sources:allSources.length,ok:fetched.length,failed:failures.length,discovery_failed:discoveryFailures.length,archive_targets:(manifest.archive_targets||[]).length,new_official_links:novel.length,report:reportPath},null,2));
  if (failures.length || discoveryFailures.length) process.exitCode=1;
}
