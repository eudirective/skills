#!/usr/bin/env node
// Retrieve and monitor the Romanian national-only source inventory.
import { createHash } from 'node:crypto';
import { mkdir, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { atomicProjectWrite, projectTempPath } from '../../../runtime-storage.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WORK = projectTempPath(path.join(ROOT, 'work'));
const DOCUMENTS = path.join(ROOT, 'documents');
const MANIFEST_PATH = path.join(ROOT, 'references/manifest.json');
const VERSION = '0.2.1';
const PORTAL = 'legislatie.just.ro';
const OFFICIAL_HTTP_WSDL = 'http://portalquery.just.ro/query.asmx?WSDL';
const NOW = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const sha = b => createHash('sha256').update(b).digest('hex');
const safe = s => s.toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^-|-$/g, '');
function acceptedPath(source) {
  if (!source.document_class || !source.document_path) throw Error(`missing reviewed-document path for ${source.id}`);
  const destination = path.resolve(ROOT, source.document_path);
  if (!destination.startsWith(DOCUMENTS + path.sep)) throw Error(`reviewed-document path escapes documents/: ${source.document_path}`);
  if (path.basename(destination) !== `${safe(source.id)}.md`) throw Error(`reviewed-document filename does not match source ID: ${source.id}`);
  return destination;
}
const unescapeHtml = s => String(s).replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos|nbsp|ndash|mdash|rsquo|lsquo|rdquo|ldquo|sect|copy|hellip);/gi, (whole, ent) => {
  if (ent[0] === '#') { const n = ent[1].toLowerCase() === 'x' ? parseInt(ent.slice(2), 16) : Number(ent.slice(1)); return Number.isInteger(n) && n > 0 && n <= 0x10ffff ? String.fromCodePoint(n) : whole; }
  return ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', ndash: '–', mdash: '—', rsquo: '’', lsquo: '‘', rdquo: '”', ldquo: '“', sect: '§', copy: '©', hellip: '…' })[ent.toLowerCase()] || whole;
});
const norm = s => unescapeHtml(String(s ?? '')).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('ro').replace(/[^\p{L}\p{N}]+/gu, ' ').trim().replace(/\s+/g, ' ');
async function json(file, fallback) { try { return JSON.parse(await readFile(file, 'utf8')); } catch (e) { if (e.code === 'ENOENT') return fallback; throw e; } }
async function atomic(file, value) { await atomicProjectWrite(file, value); }
async function fetchManifestSource(url, accept = 'text/html,application/xhtml+xml') {
  let current = url;
  for (let i = 0; i < 8; i++) {
    const u = new URL(current);
    const manifest = await manifestPromise, permitted = new Set([...(manifest.official_hosts || []), ...(manifest.secondary_hosts || [])]);
    if ((u.protocol !== 'https:' && current !== OFFICIAL_HTTP_WSDL) || !permitted.has(u.hostname)) throw Error(`unapproved source URL/redirect refused: ${current}`);
    let res, lastError;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        res = await fetch(current, { redirect: 'manual', headers: { 'user-agent': `romanian-national-legal-source-system/${VERSION}`, accept } });
        if (![429, 500, 502, 503, 504].includes(res.status) || attempt === 2) break;
      } catch (error) {
        lastError = error;
        if (attempt === 2) break;
      }
      await new Promise(resolve => setTimeout(resolve, [250, 800][attempt]));
    }
    if (!res) throw new Error(`official request failed after retries for ${current}: ${lastError?.message || 'no response'}`);
    if ([301, 302, 303, 307, 308].includes(res.status)) { const loc = res.headers.get('location'); if (!loc) throw Error(`redirect without Location from ${current}`); current = new URL(loc, current).href; continue; }
    if (!res.ok) throw Error(`HTTP ${res.status} from ${current}`);
    const bytes = Buffer.from(await res.arrayBuffer());
    if (!bytes.length) throw Error(`empty official response from ${current}`);
    return { bytes, final_url: current, content_type: res.headers.get('content-type'), etag: res.headers.get('etag'), last_modified: res.headers.get('last-modified') };
  }
  throw Error(`too many official redirects: ${url}`);
}
function attr(tag, key) { return tag.match(new RegExp(`\\b${key}\\s*=\\s*(["'])(.*?)\\1`, 'i'))?.[2] || ''; }
function elementById(html, id) {
  const opening = /<div\b[^>]*>/gi; let m, start = -1;
  while ((m = opening.exec(html))) if (attr(m[0], 'id').toLowerCase() === id.toLowerCase()) { start = m.index; break; }
  if (start < 0) return null;
  const tags = /<\/?div\b[^>]*>/gi; tags.lastIndex = start; let depth = 0, t;
  while ((t = tags.exec(html))) { if (/^<\//.test(t[0])) depth--; else if (!/\/\s*>$/.test(t[0])) depth++; if (!depth) return html.slice(start, tags.lastIndex); }
  throw Error(`unclosed official content container #${id}`);
}
function elementByTag(html, tagName) {
  const rx = new RegExp(`<${tagName}\\b[^>]*>`, 'i'), m = rx.exec(html); if (!m) return null;
  const start = m.index, tag = new RegExp(`<\\/?${tagName}\\b[^>]*>`, 'gi'); tag.lastIndex = start; let depth = 0, t;
  while ((t = tag.exec(html))) { if (/^<\//.test(t[0])) depth--; else if (!/\/\s*>$/.test(t[0])) depth++; if (!depth) return html.slice(start, tag.lastIndex); }
  throw Error(`unclosed official <${tagName}> container`);
}
function extractPortalContent(html, source) {
  const content = elementById(html, 'div_Formaconsolidata');
  if (!content || content.length < 250) throw Error(`official portal page has no populated consolidated text container for ${source.id}`);
  return content;
}
function elementByClass(html, className) {
  const opening = /<div\b[^>]*>/gi; let m;
  while ((m = opening.exec(html))) if (attr(m[0], 'class').split(/\s+/).includes(className)) {
    const tags = /<\/?div\b[^>]*>/gi; tags.lastIndex = m.index; let depth = 0, t;
    while ((t = tags.exec(html))) { if (/^<\//.test(t[0])) depth--; else if (!/\/\s*>$/.test(t[0])) depth++; if (!depth) return html.slice(m.index, tags.lastIndex); }
  }
  return null;
}
function extractPortalPrint(html, source) {
  const body = elementByTag(html, 'body');
  if (!body || body.length < 500) throw Error(`official printable form has no body for ${source.id}`);
  return body;
}
function extractScjJudgment(html, source) {
  const hidden = [...html.matchAll(/<input\b[^>]*>/gi)].map(x => x[0]).find(x => attr(x, 'data-key').toLowerCase() === 'id' && attr(x, 'data-idx') === '0');
  if (!hidden || attr(hidden, 'data-val') !== String(source.scj_record_id)) throw Error(`official ÎCCJ record ID mismatch for ${source.id}`);
  const details = elementById(html, 'jurisprudence_details');
  if (!details || details.length < 500) throw Error(`official ÎCCJ judgment body is missing for ${source.id}`);
  const citation = source.title.match(/\b(\d{1,4})\s*\/\s*(\d{4})\b/);
  if (citation) {
    const body = norm(convertHtml(details));
    if (!body.includes(`${citation[1]} ${citation[2]}`)) throw Error(`official ÎCCJ decision number/year mismatch for ${source.id}`);
  }
  return details;
}
function extractSecondaryJudgment(html, source) {
  const host = new URL(source.url).hostname;
  let fragment = null;
  if (host === 'legeaz.net') {
    const article = elementByClass(html, 'l-article');
    const start = article?.indexOf('<p>ROMÂNIA</p>') ?? -1;
    const related = start >= 0 ? article.toLowerCase().indexOf('vezi și alte spețe', start) : -1;
    const pager = start >= 0 ? article.indexOf('&larr;', start) : -1;
    const end = [related, pager].filter(index => index > start).sort((a, b) => a - b)[0] ?? -1;
    if (start >= 0 && end > start) fragment = article.slice(start, end);
  }
  else if (host === 'apjgalati.ro') fragment = elementByTag(html, 'article');
  else if (host === 'www.jurisprudenta.com') {
    const body = elementByClass(html, 'body-content');
    const heading = body?.search(/<h1\b/i) ?? -1;
    const articleColumn = heading >= 0 ? elementByClass(body.slice(heading), 'col-md-8') : null;
    if (articleColumn) fragment = articleColumn;
  }
  if (!fragment || fragment.length < 500) throw Error(`stable case-text container missing for secondary source ${source.id}`);
  const citation = source.title.match(/\b(\d{1,4})\s*\/\s*(\d{4})\b/);
  if (citation && !norm(convertHtml(fragment)).includes(`${citation[1]} ${citation[2]}`)) throw Error(`decision number/year not present in secondary source body for ${source.id}`);
  return fragment;
}
function extractGuidance(html, source) {
  if (new URL(source.url).hostname === 'eviza.mae.ro') {
    const part = elementByClass(html, 'mainLinks') || elementByClass(html, 'spage-bg');
    if (part && part.length > 300) return part;
  }
  const mainDiv = elementById(html, 'main'); if (mainDiv && mainDiv.length > 300) return mainDiv;
  for (const tag of ['main', 'article']) { const part = elementByTag(html, tag); if (part && part.length > 300) return part; }
  const roleMain = html.match(/<div\b(?=[^>]*\brole\s*=\s*["']main["'])[^>]*>/i);
  if (roleMain) { const id = attr(roleMain[0], 'id'); if (id) { const part = elementById(html, id); if (part && part.length > 300) return part; } }
  throw Error(`no stable main/article container on official guidance page ${source.url}`);
}
function convertHtml(fragment) {
  const tokens = fragment.match(/<!--[\s\S]*?-->|<![^>]*>|<[^>]*>|[^<]+/g) || [];
  const skip = new Set(['script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside', 'form', 'button', 'select', 'option']);
  const blocks = new Set(['p', 'div', 'section', 'article', 'main', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr', 'table']);
  const stack = []; let out = '', listDepth = 0;
  const boundary = () => { out = out.replace(/[ \t]+$/g, ''); if (out && !out.endsWith('\n\n')) out += '\n\n'; };
  for (const token of tokens) {
    if (token.startsWith('<!--') || /^<!/i.test(token)) continue;
    if (!token.startsWith('<')) { if (!stack.some(x => x.skip)) out += unescapeHtml(token).replace(/\s+/g, ' '); continue; }
    const closing = /^<\//.test(token), name = token.match(/^<\/?\s*([\w:-]+)/)?.[1]?.toLowerCase(); if (!name) continue;
    if (!closing) {
      const hint = `${attr(token, 'id')} ${attr(token, 'class')}`.toLowerCase();
      const ignored = skip.has(name) || /breadcrumb|cookie|skiplink|pagination|share|toolbar|sidebar|menu|cuprins|print|navigation/.test(hint);
      if (ignored) { stack.push({ name, skip: true }); continue; }
      if (blocks.has(name)) boundary();
      if (/^h[1-6]$/.test(name)) out += `${'#'.repeat(Number(name[1]))} `;
      if (name === 'li') { boundary(); out += '- '; listDepth++; }
      if (name === 'br') boundary();
      if (name === 'td' || name === 'th') { if (out && !out.endsWith('\n') && !out.endsWith(' ')) out += ' | '; }
      stack.push({ name, skip: false });
    } else {
      const pos = stack.map(x => x.name).lastIndexOf(name); if (pos < 0) continue;
      const row = stack[pos]; stack.splice(pos);
      if (row.skip) continue;
      if (name === 'li') { listDepth = Math.max(0, listDepth - 1); boundary(); }
      if (blocks.has(name)) boundary();
    }
  }
  return out.replace(/[\t\u00a0 ]+\n/g, '\n').replace(/\n[\t ]+/g, '\n').replace(/\n{3,}/g, '\n\n').replace(/[ \t]{2,}/g, ' ').trim();
}
function titleFrom(html) {
  const raw = html.match(/<title\b[^>]*>([\s\S]*?)<\/title\s*>/i)?.[1] || html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1\s*>/i)?.[1] || '';
  return convertHtml(raw).replace(/\s*[|–-]\s*Portal Legislativ\s*$/i, '').trim();
}
function contentLanguage(html, source) {
  if (new URL(source.url).hostname === 'eviza.mae.ro') return 'en';
  const root = html.match(/<html\b[^>]*>/i)?.[0] || '', meta = html.match(/<meta\b[^>]*name\s*=\s*(["'])language\1[^>]*>/i)?.[0] || '';
  return (attr(root, 'lang') || attr(root, 'xml:lang') || attr(meta, 'content') || 'ro').split(/[-_]/)[0].toLowerCase();
}
function historyIds(html) {
  const area = elementById(html, 'istoric_fa') || '';
  return [...area.matchAll(/href\s*=\s*(["'])(.*?)\1/gi)].map(x => { const m = x[2].match(/\/Public\/DetaliiDocument(?:Afis)?\/(\d+)/i); return m?.[1] || null; }).filter(Boolean).sort((a, b) => Number(a) - Number(b));
}
function candidateMarkdown(source, pageTitle, language, body) {
  const secondary = source.source_quality === 'reproduced_judgment' || source.source_quality === 'court_authored_digest';
  const quality = source.source_quality === 'official_text' ? 'Official court or justice-portal text' : source.source_quality === 'reproduced_judgment' ? 'Third-party reproduction; not verified against the official original' : source.source_quality === 'court_authored_digest' ? 'Court-authored digest hosted by a professional association; not the complete judgment' : 'Official publisher source';
  const coverage = secondary ? 'Text extracted from the identified secondary case-law page or court-authored digest; it is not an official original judgment.' : source.scj_record_id ? 'Judgment text extracted from the official ÎCCJ jurisprudence record after matching its record ID and decision number.' : source.portal_document_id ? 'Decision text extracted from the official Portal Legislativ consolidated-text container.' : 'Text extracted from the source-specific main article; page layout and content outside that container are excluded.';
  const sourceLabel = secondary ? 'Source' : 'Official source';
  const notice = secondary ? 'This is a reproducible secondary source. It is not an official judgment text and has not been checked against the court original.' : 'This is a deterministic conversion of the listed official source. It does not independently establish legal force, currentness, completeness, or the procedural status of a case.';
  return `# ${source.title}\n\n- Source ID: \`${source.id}\`\n- Source type: \`${source.source_type}\`\n- Source quality: ${quality}\n- Content language: \`${language}\`\n- Source page title: ${pageTitle || source.title}\n- ${sourceLabel}: ${source.url}\n- Converter: Romania source HTML to Markdown ${VERSION}\n- Coverage: ${coverage}\n${source.source_note ? `- Source note: ${source.source_note}\n` : ''}\n> ${notice}\n\n${body}\n`;
}
function portalSearchTerm(source, observations) {
  const row = observations.find(x => x.source_id === source.id), title = row?.page_title || source.search_title || source.title;
  const citation = title.match(/\b(\d{1,4})\s+(?:\([^)]*\)\s*)?(\d{2})\/(\d{2})\/(\d{4})\b/);
  if (citation) return `${citation[1]} ${citation[4]}`;
  const stated = source.title.match(/\b(\d{1,4})\s*\/\s*(\d{4})\b/);
  if (stated) return `${stated[1]} ${stated[2]}`;
  return source.search_title || source.title;
}
function parsePortalResults(html, url) {
  const total = Number(html.match(/(\d+)\s+document\(e\) găsit/i)?.[1] || 0), rows = [];
  for (const m of html.matchAll(/<a\b[^>]*href\s*=\s*(["'])(.*?)\1[^>]*>([\s\S]*?)<\/a\s*>/gi)) {
    const href = unescapeHtml(m[2]).replace(/^~\//, '/'), id = href.match(/\/Public\/DetaliiDocument(?:Afis)?\/(\d+)/i)?.[1];
    if (!id) continue;
    const title = convertHtml(m[3]).replace(/^\d+\.\s*/, '').trim();
    if (title) rows.push({ document_id: id, official_url: new URL(href, url).href, official_title: title });
  }
  return { total, rows: [...new Map(rows.map(x => [x.document_id, x])).values()] };
}
async function portalSearch(term) {
  const match = term.match(/^(\d{1,4})\s+(\d{4})$/);
  const variants = [...new Set([term, ...(match ? [`Legea ${match[1]}/${match[2]}`] : [])])];
  let lastError;
  for (const query of variants) {
    const url = new URL('https://legislatie.just.ro/Public/RezultateCautare'); url.searchParams.set('titlu', query);
    try {
      const response = await fetchManifestSource(url.href), html = response.bytes.toString('utf8');
      if (!/Rezultate C[aă]utare/i.test(html)) throw Error('official Portal Legislativ search returned an unexpected page');
      return { ...parsePortalResults(html, response.final_url), bytes: response.bytes, final_url: response.final_url, request_url: url.href, query };
    } catch (e) { lastError = e; if (!/HTTP 5\d\d/.test(e.message)) throw e; }
  }
  throw lastError;
}
const manifestPromise = readFile(MANIFEST_PATH, 'utf8').then(JSON.parse);
const manifest = await manifestPromise;
const mode = process.argv.find(x => ['--check', '--sync', '--discover', '--ack', '--ack-all', '--search-check'].includes(x)) || '--check';
const ackId = mode === '--ack' ? process.argv[process.argv.indexOf('--ack') + 1] : null;
const statePath = path.join(WORK, 'state.json'), reportPath = path.join(WORK, 'latest-report.json');
if (mode === '--search-check') {
  const source = manifest.documents.find(x => x.source_type === 'national_legislation'), result = await portalSearch(portalSearchTerm(source, []));
  console.log(JSON.stringify({ search_url: result.request_url, results: result.rows.length, result_total: result.total, response_sha256: sha(result.bytes) }, null, 2));
} else if (mode === '--ack') {
  const source = manifest.documents.find(x => x.id === ackId); if (!source || source.monitor_only) throw Error('--ack requires a known converted source ID');
  const candidate = path.join(WORK, 'candidates', `${safe(ackId)}.md`), dest = acceptedPath(source);
  await mkdir(path.dirname(dest), { recursive: true });
  await atomic(dest, await readFile(candidate));
  const state = await json(statePath, { version: 1, sources: {}, search_hits: {} }); state.sources[ackId] ||= {}; state.sources[ackId].accepted_markdown_sha256 = sha(await readFile(dest)); state.sources[ackId].accepted_at = NOW();
  await atomic(statePath, JSON.stringify(state, null, 2) + '\n'); await rm(candidate); console.log(JSON.stringify({ accepted: ackId, path: dest }, null, 2));
} else if (mode === '--ack-all') {
  const report = await json(reportPath, null);
  if (!report || report.mode !== '--sync') throw Error('--ack-all requires a completed --sync report');
  const converted=report.observations.filter(x=>x.markdown_sha256), state=await json(statePath,{version:1,sources:{},search_hits:{}});
  for(const item of converted){
    const source=manifest.documents.find(x=>x.id===item.source_id);
    if(!source||source.monitor_only)throw Error(`Unknown converted source ${item.source_id}`);
    const candidate=path.join(WORK,'candidates',`${safe(source.id)}.md`),bytes=await readFile(candidate);
    if(sha(bytes)!==item.markdown_sha256)throw Error(`Candidate hash mismatch: ${source.id}`);
  }
  for(const item of converted){
    const source=manifest.documents.find(x=>x.id===item.source_id);
    const candidate=path.join(WORK,'candidates',`${safe(source.id)}.md`),dest=acceptedPath(source);
    await mkdir(path.dirname(dest),{recursive:true});
    await atomic(dest,await readFile(candidate));
    if(sha(await readFile(dest))!==item.markdown_sha256)throw Error(`Accepted document hash mismatch: ${source.id}`);
    state.sources[source.id]||={};state.sources[source.id].accepted_markdown_sha256=item.markdown_sha256;state.sources[source.id].accepted_at=NOW();
  }
  await atomic(statePath,JSON.stringify(state,null,2)+'\n');
  for (const item of converted) await rm(path.join(WORK, 'candidates', `${safe(item.source_id)}.md`), { force: true });
  console.log(JSON.stringify({accepted:converted.length,documents:DOCUMENTS},null,2));
} else {
  const previous = await json(statePath, { version: 1, sources: {}, search_hits: {} }), checkedAt = NOW();
  const observations = [], failures = [], candidates = [], staged = [], rawDir = path.join(WORK, 'raw');
  const sources = manifest.documents;
  for (const source of sources) {
    try {
      const got = await fetchManifestSource(source.url, source.retrieval_format === 'soap_wsdl' ? 'application/xml,text/xml' : 'text/html,application/xhtml+xml'), html = got.bytes.toString('utf8');
      if (source.retrieval_format === 'soap_wsdl') {
        if (!/xml/i.test(got.content_type || '') || !/<(?:wsdl:)?definitions\b/i.test(html.slice(0, 10000))) throw Error(`unexpected official WSDL response (${got.content_type})`);
      } else if (!/html/i.test(got.content_type || '') || !/<html\b|<!doctype html/i.test(html.slice(0, 10000))) throw Error(`unexpected official HTML response (${got.content_type})`);
      let fragment = null;
      if (!source.monitor_only) fragment = source.scj_record_id ? extractScjJudgment(html, source) : source.portal_document_id ? extractPortalContent(html, source) : source.portal_form_key ? extractPortalPrint(html, source) : source.source_quality === 'reproduced_judgment' || source.source_quality === 'court_authored_digest' ? extractSecondaryJudgment(html, source) : extractGuidance(html, source);
      const body = fragment ? convertHtml(fragment) : '';
      if (fragment && body.length < 150) throw Error(`converted official source body is implausibly short (${body.length} characters)`);
      const sourceHash = sha(got.bytes), bodyHash = fragment ? sha(Buffer.from(fragment, 'utf8')) : null, pageTitle = titleFrom(html), history = source.portal_document_id ? [...new Set([source.portal_document_id, ...historyIds(html)])].sort((a, b) => Number(a) - Number(b)) : [];
      const language = contentLanguage(html, source);
      const markdown = fragment ? candidateMarkdown(source, pageTitle, language, body) : null, markdownHash = markdown ? sha(Buffer.from(markdown, 'utf8')) : null;
      let stageMarkdown = false;
      if (mode === '--sync' && markdown) {
        const acceptedFile = acceptedPath(source);
        try { stageMarkdown = sha(await readFile(acceptedFile)) !== markdownHash; }
        catch { stageMarkdown = true; }
      }
      const old = previous.sources[source.id] || {}, change = !old.source_sha256 ? 'first_observation' : old.body_sha256 !== bodyHash ? 'legal_content_changed' : old.markdown_sha256 !== markdownHash ? 'conversion_changed' : old.source_sha256 !== sourceHash ? 'official_page_changed' : 'unchanged';
      const newHistory = Array.isArray(old.history_document_ids) ? history.filter(id => !old.history_document_ids.includes(id)) : [];
      for (const id of newHistory) candidates.push({ source_id: source.id, kind: 'possible_new_consolidation_or_historical_form', official_url: `https://${PORTAL}/Public/DetaliiDocument/${id}`, title: source.title, requires_review: true });
      const row = { source_id: source.id, url: source.url, final_url: got.final_url, content_type: got.content_type, etag: got.etag, last_modified: got.last_modified, page_title: pageTitle, content_language: language, source_sha256: sourceHash, body_sha256: bodyHash, markdown_sha256: markdownHash, body_characters: body.length, history_document_ids: history, newly_seen_history_document_ids: newHistory, change, retrieved_at: checkedAt, monitor_only: source.monitor_only };
      observations.push(row);
      if (mode === '--sync') staged.push({ source, got, sourceHash, markdown, stageMarkdown, row });
    } catch (e) { failures.push({ source_id: source.id, url: source.url, error: e.message }); }
  }

  let searchReport = { status: 'not_run', query_count: 0, failed_count: 0, candidates: [] };
  {
    const legalSources = manifest.documents.filter(x => x.source_type === 'national_legislation'), seen = { ...(previous.search_hits || {}) }, found = new Map(), searchFailures = [], hasBaseline = Object.keys(seen).length > 0;
    for (const source of legalSources) {
      try {
        if (searchReport.query_count) await new Promise(resolve => setTimeout(resolve, 150));
        const result = await portalSearch(portalSearchTerm(source, observations)), rawPath = path.join(rawDir, `search-${sha(result.bytes)}.html`);
        let newCount = 0;
        for (const hit of result.rows) {
          const key = `${source.id}|${hit.official_url}`, firstSeen = !seen[key];
          seen[key] = { first_seen_at: seen[key]?.first_seen_at || checkedAt, last_seen_at: checkedAt, title: hit.official_title };
          if (firstSeen && hasBaseline && hit.document_id !== String(source.portal_document_id || '')) {
            const old = found.get(hit.official_url) || { official_url: hit.official_url, document_id: hit.document_id, official_title: hit.official_title, candidate_source_ids: [], kind: 'official_portal_title_search_candidate' };
            old.candidate_source_ids.push(source.id); found.set(hit.official_url, old); newCount++;
          }
        }
        searchReport.query_count++;
        if (mode === '--sync') staged.push({ rawOnly: true, bytes: result.bytes, rawPath });
        searchReport.candidates_total = (searchReport.candidates_total || 0) + result.total;
        searchReport.visible_result_count = (searchReport.visible_result_count || 0) + result.rows.length;
        searchReport.new_hit_count = (searchReport.new_hit_count || 0) + newCount;
      } catch (e) { searchFailures.push({ source_id: source.id, search_title: portalSearchTerm(source, observations), error: e.message }); }
    }
    searchReport = { status: hasBaseline ? 'complete' : 'baseline_required', query_count: searchReport.query_count, failed_count: searchFailures.length, failures: searchFailures, result_total_sum: searchReport.candidates_total || 0, result_links_observed: searchReport.visible_result_count || 0, newly_seen_hits: hasBaseline ? (searchReport.new_hit_count || 0) : 0, candidates: [...found.values()].map(x => ({ ...x, candidate_source_ids: [...new Set(x.candidate_source_ids)].sort(), requires_review: true })) };
    candidates.push(...searchReport.candidates);
    if (mode === '--sync') previous.search_hits = seen;
  }
  const report = { report_version: 1, skill_version: VERSION, mode, checked_at: checkedAt, scope: manifest.scope, source_count: manifest.source_count, retrieval_target_count: sources.length, retrieved_count: observations.length, failed_count: failures.length, changed_count: observations.filter(x => x.change !== 'unchanged').length, converted_count: observations.filter(x => x.markdown_sha256).length, monitor_only_target_count: sources.filter(x => x.monitor_only).length, monitor_only_retrieved_count: observations.filter(x => x.monitor_only).length, history_candidate_count: candidates.filter(x => x.kind === 'possible_new_consolidation_or_historical_form').length, portal_title_search: searchReport, discovery_candidate_count: candidates.length, discovery_candidates: candidates, observations, failures, actions: ['Review every change and discovery candidate against the linked official record before acknowledgement.', 'A hash or successful retrieval does not establish currentness or legal completeness.'] };
  await atomic(reportPath, JSON.stringify(report, null, 2) + '\n');
  if (mode === '--sync') {
    await mkdir(rawDir, { recursive: true }); await mkdir(path.join(WORK, 'candidates'), { recursive: true });
    for (const item of staged) {
      if (item.rawOnly) { try { await readFile(item.rawPath); } catch { await atomic(item.rawPath, item.bytes); } continue; }
      const rawFile = path.join(rawDir, `${item.sourceHash}.html`); try { await readFile(rawFile); } catch { await atomic(rawFile, item.got.bytes); }
      if (item.markdown && item.stageMarkdown) await atomic(path.join(WORK, 'candidates', `${safe(item.source.id)}.md`), item.markdown);
      previous.sources[item.source.id] = { ...(previous.sources[item.source.id] || {}), ...item.row, last_checked_at: checkedAt };
    }
    const activeIds = new Set(sources.map(source => source.id));
    previous.retired_sources ||= {};
    for (const [id, record] of Object.entries(previous.sources || {})) {
      if (activeIds.has(id)) continue;
      previous.retired_sources[id] = { ...record, retired_at: checkedAt, retirement_reason: 'record is not present in the current Romania manifest' };
      delete previous.sources[id];
    }
    previous.version = 1; previous.updated_at = checkedAt;
    await atomic(statePath, JSON.stringify(previous, null, 2) + '\n');
  }
  console.log(JSON.stringify({ mode, targets: report.retrieval_target_count, retrieved: report.retrieved_count, failed: report.failed_count, converted: report.converted_count, changed: report.changed_count, history_candidates: report.history_candidate_count, portal_title_queries: report.portal_title_search.query_count, portal_search_failures: report.portal_title_search.failed_count, discovery_candidates: report.discovery_candidate_count, report: reportPath }, null, 2));
  if (failures.length || searchReport.failed_count) process.exitCode = 1;
}
