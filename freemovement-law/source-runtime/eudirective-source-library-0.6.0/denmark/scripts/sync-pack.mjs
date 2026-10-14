#!/usr/bin/env node
// Reproducible retrieval, conversion, and update discovery for Danish instruments in the pack.
import { createHash } from 'node:crypto';
import { mkdir, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { atomicProjectWrite, projectTempPath } from '../../../runtime-storage.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MANIFEST_PATH = path.join(ROOT, 'references/pack-manifest.json');
const WORK = projectTempPath(path.join(ROOT, 'work'));
const DOCUMENTS = path.join(ROOT, 'documents');
const HOST = 'www.retsinformation.dk';
const FEED = 'https://www.retsinformation.dk/eli/eli-update-feed.atom';
const VERSION = '0.2.1';
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const sha = b => createHash('sha256').update(b).digest('hex');
const safe = s => s.toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^-|-$/g, '');
const norm = s => String(s ?? '').normalize('NFKC').toLocaleLowerCase('da').replace(/[.,:;()\[\]{}'"’‘“”–—-]+/g, ' ').replace(/[^\p{L}\p{N}]+/gu, ' ').trim().replace(/\s+/g, ' ');
const xmlEntities = s => s.replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos);/gi, (_, e) => {
  if (e[0] === '#') return String.fromCodePoint(e[1].toLowerCase() === 'x' ? parseInt(e.slice(2), 16) : Number(e.slice(1)));
  return ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" })[e.toLowerCase()];
});
function parseXml(xml) {
  const root = { name: '#document', attrs: {}, children: [] }, stack = [root];
  const tokens = xml.match(/<!--[\s\S]*?-->|<!\[CDATA\[[\s\S]*?\]\]>|<\?[\s\S]*?\?>|<![^>]*>|<[^>]+>|[^<]+/g) || [];
  for (const token of tokens) {
    if (token.startsWith('<!--') || token.startsWith('<?') || /^<!DOCTYPE/i.test(token)) continue;
    if (token.startsWith('<![CDATA[')) { stack.at(-1).children.push(token.slice(9, -3)); continue; }
    if (token.startsWith('</')) { if (stack.length > 1) stack.pop(); continue; }
    if (token.startsWith('<')) {
      const m = token.match(/^<([\w:.-]+)([\s\S]*?)\s*\/?>$/); if (!m) continue;
      const attrs = {}; for (const a of m[2].matchAll(/([\w:.-]+)\s*=\s*(["'])([\s\S]*?)\2/g)) attrs[a[1]] = xmlEntities(a[3]);
      const node = { name: m[1].split(':').at(-1), attrs, children: [] }; stack.at(-1).children.push(node);
      if (!/\/\s*>$/.test(token)) stack.push(node);
      continue;
    }
    stack.at(-1).children.push(xmlEntities(token));
  }
  return root;
}
function children(node, name) { return (node?.children || []).filter(x => typeof x === 'object' && x.name === name); }
function first(node, name) { return children(node, name)[0] || null; }
function text(node) { return (node?.children || []).map(x => typeof x === 'string' ? x : text(x)).join(' ').replace(/\s+/g, ' ').trim(); }
function find(node, name) {
  if (node?.name === name) return node;
  for (const child of node?.children || []) if (typeof child === 'object') { const hit = find(child, name); if (hit) return hit; }
  return null;
}
function render(node) {
  if (typeof node === 'string') return node.trim() ? [node.trim()] : [];
  if (!node || ['Meta', 'TitelGruppe'].includes(node.name)) return [];
  const name = node.name;
  if (name === 'Paragraf') {
    const label = text(first(node, 'Explicatus')) || `§ ${node.attrs.localId || ''}`.trim();
    const body = node.children.filter(x => typeof x === 'string' || !['Explicatus'].includes(x.name)).flatMap(render);
    return [`### ${label}`, ...body];
  }
  if (['Kapitel', 'Afsnit', 'Underafsnit', 'Del', 'Bog'].includes(name)) {
    const label = text(first(node, 'Explicatus')) || name;
    const heading = [label, text(first(node, 'Rubrica'))].filter(Boolean).join(' — ');
    const body = node.children.filter(x => typeof x === 'string' || !['Explicatus', 'Rubrica'].includes(x.name)).flatMap(render);
    return [`## ${heading}`, ...body];
  }
  if (name === 'Indentatio') {
    const label = text(first(node, 'Explicatus'));
    const body = node.children.filter(x => typeof x === 'string' || x.name !== 'Explicatus').flatMap(render).join(' ');
    return [`- ${label ? `**${label}** ` : ''}${body}`.trim()];
  }
  if (name === 'Linea') { const value = text(node); return value ? [value] : []; }
  if (name === 'Indledning') { const body = node.children.flatMap(render); return body.length ? body : []; }
  if (['Rubrica', 'Titel', 'ParaRef', 'Fodnote'].includes(name)) { const value = text(node); return value ? [value] : []; }
  if (name === 'Tabel' || name === 'Figur' || name === 'Billede') {
    const value = text(node); return value ? [`[${name}: ${value}]`] : [`[${name} present in official XML; non-text content not represented]`];
  }
  return node.children.flatMap(render);
}
function metadata(root) {
  const meta = find(root, 'Meta'); if (!meta) throw Error('XML has no Meta block');
  const get = key => text(first(meta, key)) || null;
  const rows = {};
  for (const node of meta.children || []) if (typeof node === 'object' && ['Ref_Accn', 'Ref_Af', 'Ref_Text'].includes(node.name)) rows[node.name] = [...(rows[node.name] || []), text(node)];
  return {
    document_id: get('DocumentId'), unique_document_id: get('UniqueDocumentId'), accession: get('AccessionNumber'), title: get('DocumentTitle'),
    year: get('Year'), number: get('Number'), status: get('Status'), start_date: get('StartDate'),
    end_date: get('EndDate'), document_type: get('DocumentType'), references: rows
  };
}
function convertXml(xml, source, observed, fetched) {
  const tree = parseXml(xml), m = metadata(tree);
  const url = new URL(source.eli), pathBits = url.pathname.split('/');
  const expectedYear = pathBits.at(-2), expectedNumber = pathBits.at(-1);
  if (m.year !== expectedYear || String(Number(m.number)) !== String(Number(expectedNumber))) throw Error(`official ELI citation mismatch for ${source.id}: XML is ${m.year}/${m.number}`);
  if (source.expected_document_id && m.document_id !== source.expected_document_id) throw Error(`DocumentId mismatch for ${source.id}: ${m.document_id}`);
  if (source.expected_unique_document_id && m.unique_document_id !== source.expected_unique_document_id) throw Error(`UniqueDocumentId mismatch for ${source.id}: ${m.unique_document_id}`);
  if (source.expected_accession && m.accession !== source.expected_accession) throw Error(`accession mismatch for ${source.id}: ${m.accession}`);
  const content = find(tree, 'DokumentIndhold');
  if (!content) return null;
  const knownTitles = [source.title, ...(source.search_names || [])].map(norm);
  if (m.title && !knownTitles.some(k => k === norm(m.title) || norm(m.title).startsWith(k) || k.startsWith(norm(m.title)))) throw Error(`official title mismatch for ${source.id}: ${m.title}`);
  const body = content.children.flatMap(render).map(s => s.replace(/[ \t]+/g, ' ').trim()).filter(Boolean).join('\n\n').replace(/\n{3,}/g, '\n\n').trim();
  if (body.length < 100) throw Error(`converted body implausibly short for ${source.id}`);
  const warning = [source.currentness_note, m.end_date ? `The official source metadata records this version's end date as ${m.end_date}; verify later consolidations and amendments.` : null].filter(Boolean).map(x => `\n- Currentness review: ${x}`).join('');
  const out = `# ${m.title || source.title}\n\n- Citation: ${source.citation}\n- Official ELI source: ${source.eli}\n- Official document ID: ${m.document_id || 'unavailable'}\n- Official accession: ${m.accession || 'unavailable'}\n- Official status: ${m.status || 'unavailable'}\n- Effective start date: ${m.start_date || 'unavailable'}\n- End date in source metadata: ${m.end_date || 'none recorded'}\n- XML SHA-256: ${observed.xml_sha256}\n- Converter: Denmark XML-to-Markdown ${VERSION}${warning}\n- Coverage: text represented in the official Retsinformation XML; visual page layout and non-text attachments are not represented.\n\n> This is a deterministic text conversion of the linked official XML. It is not a claim that this instrument is the latest consolidation or legally complete.\n\n${body}\n`;
  return { markdown: out, metadata: m, markdown_sha256: sha(Buffer.from(out, 'utf8')) };
}
function extractIndhold(html) {
  const m = html.match(/<div\b(?=[^>]*\bid\s*=\s*["']INDHOLD["'])[^>]*>/i);
  if (!m) throw Error('official rendered HTML has no INDHOLD legal-text container');
  const start = m.index, re = /<\/?div\b[^>]*>/gi; re.lastIndex = start; let depth = 0, hit;
  while ((hit = re.exec(html))) {
    if (/^<\//.test(hit[0])) { depth--; if (depth === 0) return html.slice(start, re.lastIndex); }
    else if (!/\/\s*>$/.test(hit[0])) depth++;
  }
  throw Error('official rendered HTML INDHOLD container did not close');
}
async function convertOfficialHtml(source, xmlMeta, xmlHash, fetched) {
  const eliPath = new URL(source.eli).pathname.slice(1), endpoint = `https://${HOST}/api/document/${eliPath}`;
  const res = await fetch(endpoint, { method: 'POST', redirect: 'manual', headers: { 'user-agent': `denmark-legal-source-system/${VERSION}`, accept: 'application/json', 'content-type': 'application/json' }, body: JSON.stringify({ isRawHtml: true }) });
  if (!res.ok || !/application\/json/i.test(res.headers.get('content-type') || '')) throw Error(`official Retsinformation document endpoint returned HTTP ${res.status}`);
  const records = await res.json();
  if (!Array.isArray(records) || records.length !== 1) throw Error(`official document endpoint returned ${records?.length ?? 'invalid'} records`);
  const doc = records[0];
  if (String(doc.id) !== String(xmlMeta.unique_document_id) || doc.accessionNumber !== xmlMeta.accession) throw Error(`rendered HTML identity mismatch for ${source.id}`);
  if (!doc.documentHtml || norm(doc.title) !== norm(xmlMeta.title)) throw Error(`rendered HTML title/content mismatch for ${source.id}`);
  const officialHtml = extractIndhold(doc.documentHtml), htmlHash = sha(Buffer.from(officialHtml, 'utf8'));
  const coreScript = pathToFileURL(path.resolve(ROOT, '../../eudirective-core-work/eudirective-core/scripts/source-maintenance.mjs')).href;
  const { htmlText } = await import(coreScript);
  const body = htmlText(`<div id="document1">${officialHtml}</div>`, { source_type: 'charter', source_id: source.id });
  if (body.length < 500) throw Error(`official HTML conversion implausibly short for ${source.id}`);
  const markdown = `# ${doc.title}\n\n- Citation: ${source.citation}\n- Official ELI source: ${source.eli}\n- Official rendered HTML endpoint: ${endpoint}\n- Official document ID: ${xmlMeta.document_id}\n- Official accession: ${xmlMeta.accession}\n- Official XML metadata SHA-256: ${xmlHash}\n- Official HTML SHA-256: ${htmlHash}\n- Converter: EU core deterministic HTML tokenizer, scoped to the official INDHOLD legal-text container\n- Coverage: text in Retsinformation's official rendered document HTML; non-text attachments and visual layout are not represented.\n\n> This older record's XML contains metadata only. The text was retrieved from Retsinformation's first-party document endpoint. The fixed ELI identifies a historical instrument and does not prove current consolidation.\n\n${body}\n`;
  return { markdown, html_bytes: Buffer.from(officialHtml, 'utf8'), markdown_sha256: sha(Buffer.from(markdown, 'utf8')), metadata: { ...xmlMeta, html_sha256: htmlHash } };
}
async function fetchOfficial(url, accept) {
  let current = url;
  for (let i = 0; i < 6; i++) {
    const u = new URL(current); if (u.protocol !== 'https:' || u.hostname !== HOST) throw Error(`nonofficial URL/redirect refused: ${current}`);
    const res = await fetch(current, { redirect: 'manual', headers: { 'user-agent': `denmark-legal-source-system/${VERSION}`, accept }, signal: AbortSignal.timeout(45000) });
    if ([301, 302, 303, 307, 308].includes(res.status)) { const loc = res.headers.get('location'); if (!loc) throw Error(`redirect missing Location: ${current}`); current = new URL(loc, current).href; continue; }
    if (!res.ok) throw Error(`HTTP ${res.status} from ${current}`);
    const bytes = Buffer.from(await res.arrayBuffer()); if (!bytes.length) throw Error(`empty response from ${current}`);
    return { bytes, final_url: current, content_type: res.headers.get('content-type'), etag: res.headers.get('etag'), last_modified: res.headers.get('last-modified') };
  }
  throw Error(`too many redirects for ${url}`);
}
function atomEntries(xml, manifest) {
  const root = parseXml(xml), entries = [];
  const visit = n => { if (!n || typeof n !== 'object') return; if (n.name === 'entry') {
    const fields = Object.fromEntries((n.children || []).filter(x => typeof x === 'object').map(x => [x.name, x]));
    const links = (n.children || []).filter(x => typeof x === 'object' && x.name === 'link').map(x => x.attrs.href).filter(Boolean);
    const href = links.find(x => /\/eli\//i.test(x)) || links[0] || null;
    const title = text(fields.title), uri = text(fields.id) || href;
    const titleKey = norm(title), candidates = manifest.documents.filter(d => titleKey && (d.search_names || [d.title]).some(alias => {
      const k = norm(alias); return k && (titleKey === k || titleKey.includes(k) || k.includes(titleKey));
    })).map(d => d.id);
    entries.push({ title, uri, href, updated: text(fields.updated) || null, change_date: text(fields.changeDate) || null, reason_for_change: text(fields.reasonForChange) || null, published_in: text(fields.published_in) || null, summary: text(fields.summary) || null, candidate_source_ids: candidates });
  } else for (const c of n.children || []) if (typeof c === 'object') visit(c); };
  visit(root); return entries;
}
function descendants(node, name) {
  const out = [];
  const visit = n => { for (const c of n?.children || []) if (typeof c === 'object') { if (c.name === name) out.push(c); visit(c); } };
  visit(node); return out;
}
async function mapLimit(items, limit, fn) {
  const out = new Array(items.length); let next = 0;
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (true) { const i = next++; if (i >= items.length) return; out[i] = await fn(items[i], i); }
  }));
  return out;
}
async function getSitemapSnapshot() {
  const top = await fetchOfficial('https://www.retsinformation.dk/eli/sitemap.xml', 'application/xml, text/xml;q=0.9');
  const topTree = parseXml(top.bytes.toString('utf8'));
  const pageUrls = descendants(topTree, 'loc').map(n => text(n)).filter(u => /\/eli\/sitemap\.xml\?page=\d+/.test(u));
  if (!pageUrls.length) throw Error('official ELI sitemap index contains no page URLs');
  const pages = await mapLimit(pageUrls, 5, async rawUrl => {
    const u = new URL(rawUrl); if (u.hostname === 'retsinformation.dk') u.hostname = HOST;
    const r = await fetchOfficial(u.href, 'application/xml, text/xml;q=0.9');
    const tree = parseXml(r.bytes.toString('utf8'));
    return { url: u.href, bytes: r.bytes, entries: descendants(tree, 'url').map(node => ({ loc: text(first(node, 'loc')), lastmod: text(first(node, 'lastmod')) || null })).filter(x => x.loc) };
  });
  const entries = Object.fromEntries(pages.flatMap(p => p.entries.map(e => [new URL(e.loc).pathname, e.lastmod])));
  return { top, pages, entries, hash: sha(Buffer.from(JSON.stringify(entries))) };
}
function titleCandidates(title, manifest, eliPath) {
  const name = norm(title), pinnedPath = new Map(manifest.documents.map(d => [new URL(d.eli).pathname, d]));
  const matches = [];
  for (const source of manifest.documents) {
    if (eliPath === new URL(source.eli).pathname) continue;
    const aliases = [source.title, ...(source.search_names || [])].map(norm).filter(a => a.length >= 8);
    const exact = aliases.some(a => a === name || name.startsWith(a) || a.startsWith(name));
    const related = aliases.some(a => name.includes(a));
    if (!exact && !related) continue;
    const [year, num] = eliPath.match(/^\/eli\/lta\/(\d{4})\/(\d+)$/)?.slice(1) || [];
    const pinnedMatch = new URL(source.eli).pathname.match(/^\/eli\/lta\/(\d{4})\/(\d+)$/);
    const newer = !!year && !!pinnedMatch && (Number(year) > Number(pinnedMatch[1]) || (year === pinnedMatch[1] && Number(num) > Number(pinnedMatch[2])));
    matches.push({ source_id: source.id, kind: exact && newer ? 'possible_new_consolidation' : related ? 'possible_amendment_or_related_instrument' : 'historical_or_same-title-record' });
  }
  return matches;
}
async function readJson(file, fallback) { try { return JSON.parse(await readFile(file, 'utf8')); } catch (e) { if (e.code === 'ENOENT') return fallback; throw e; } }
async function atomic(file, data) { await atomicProjectWrite(file, data); }
const stateFile = path.join(WORK, 'state.json'), reportFile = path.join(WORK, 'latest-report.json');
const manifest = JSON.parse(await readFile(MANIFEST_PATH, 'utf8'));
const mode = process.argv.find(x => ['--check', '--sync', '--discover', '--ack', '--ack-all'].includes(x)) || '--check';
const ackId = mode === '--ack' ? process.argv[process.argv.indexOf('--ack') + 1] : null;
if (mode === '--ack') {
  if (!ackId || !manifest.documents.some(x => x.id === ackId)) throw Error('--ack requires a known source id');
  const candidate = path.join(WORK, 'candidates', `${safe(ackId)}.md`), dest = path.join(DOCUMENTS, manifest.documents.find(x => x.id === ackId).file);
  await atomic(dest, await readFile(candidate));
  const state = await readJson(stateFile, { version: 1, sources: {}, last_atom_check: null });
  state.sources[ackId] ||= {}; state.sources[ackId].accepted_markdown_sha256 = sha(await readFile(dest)); state.sources[ackId].accepted_at = now();
  await atomic(stateFile, JSON.stringify(state, null, 2) + '\n'); await rm(candidate); console.log(JSON.stringify({ accepted: ackId, path: dest }, null, 2));
} else if (mode === '--ack-all') {
  const report=await readJson(reportFile,null);
  if(!report||report.failed_count!==0||report.observations?.length!==manifest.documents.length)throw Error('--ack-all requires a complete successful official-source check');
  for(const item of report.observations){
    const source=manifest.documents.find(x=>x.id===item.source_id),candidate=path.join(WORK,'candidates',`${safe(item.source_id)}.md`);
    if(!source||sha(await readFile(candidate))!==item.markdown_sha256)throw Error(`Candidate hash mismatch: ${item.source_id}`);
  }
  const state=await readJson(stateFile,{version:1,sources:{}});
  for(const item of report.observations){
    const source=manifest.documents.find(x=>x.id===item.source_id),candidate=path.join(WORK,'candidates',`${safe(source.id)}.md`),dest=path.join(DOCUMENTS,source.file);
    await atomic(dest,await readFile(candidate));
    if(sha(await readFile(dest))!==item.markdown_sha256)throw Error(`Accepted file hash mismatch: ${source.id}`);
    state.sources[source.id]||={};state.sources[source.id].accepted_markdown_sha256=item.markdown_sha256;state.sources[source.id].accepted_at=now();
  }
  await atomic(stateFile,JSON.stringify(state,null,2)+'\n');
  for (const item of report.observations) await rm(path.join(WORK, 'candidates', `${safe(item.source_id)}.md`), { force: true });
  console.log(JSON.stringify({accepted:report.observations.length,documents:DOCUMENTS},null,2));
} else {
  const previous = await readJson(stateFile, { version: 1, sources: {}, last_atom_check: null });
  const at = now(), failures = [], observations = [], rawDir = path.join(WORK, 'raw'), candidateDir = path.join(WORK, 'candidates');
  const feedFetch = await fetchOfficial(FEED, 'application/atom+xml, application/xml;q=0.9');
  const feedText = feedFetch.bytes.toString('utf8'); if (!/<(?:\w+:)?feed\b/i.test(feedText)) throw Error('official ELI update feed has unexpected XML shape');
  const feedEntries = atomEntries(feedText, manifest);
  const oldCheck = previous.last_atom_check ? Date.parse(previous.last_atom_check) : null;
  const retentionGap = oldCheck !== null && Date.now() - oldCheck > 55 * 24 * 60 * 60 * 1000;
  const sitemap = await getSitemapSnapshot();
  const oldSitemap = previous.sitemap_entries || null;
  const addedPaths = oldSitemap ? Object.keys(sitemap.entries).filter(p => !(p in oldSitemap)) : [];
  const sitemapDiscovery = [];
  if (oldSitemap && addedPaths.length) {
    const legalPaths = addedPaths.filter(p => /^\/eli\/lta\/\d{4}\/\d+$/.test(p));
    const rows = await mapLimit(legalPaths, 5, async p => {
      try {
        const url = `https://${HOST}${p}/xml`, r = await fetchOfficial(url, 'application/xml, text/xml;q=0.9');
        const meta = metadata(parseXml(r.bytes.toString('utf8')));
        return { eli: `https://${HOST}${p}`, title: meta.title, year: meta.year, number: meta.number, lastmod: sitemap.entries[p], candidates: titleCandidates(meta.title || '', manifest, p) };
      } catch (e) { return { eli: `https://${HOST}${p}`, lastmod: sitemap.entries[p], error: e.message, candidates: [] }; }
    });
    sitemapDiscovery.push(...rows.filter(x => x.candidates.length || x.error));
  }
  const pinnedByPath = new Map(manifest.documents.map(d => [new URL(d.eli).pathname, d]));
  const discovery = [];
  for (const e of feedEntries) {
    if (!e.candidate_source_ids.length || e.published_in !== 'Lovtidende A') continue;
    const uri = e.uri || e.href; let parsed;
    try { parsed = new URL(uri); } catch { continue; }
    if (parsed.hostname !== 'retsinformation.dk' && parsed.hostname !== HOST) continue;
    const bits = parsed.pathname.match(/^\/eli\/lta\/(\d{4})\/(\d+)$/);
    if (!bits) continue;
    const [, year, number] = bits, pinned = pinnedByPath.get(parsed.pathname);
    const candidates = [];
    for (const id of e.candidate_source_ids) {
      const target = manifest.documents.find(d => d.id === id), targetPath = new URL(target.eli).pathname;
      if (parsed.pathname === targetPath) { candidates.push({ source_id: id, kind: 'tracked_eli_change' }); continue; }
      const name = norm(e.title), aliases = [target.title, ...(target.search_names || [])].map(norm), exactName = aliases.some(a => a === name);
      const targetYear = Number(targetPath.match(/^\/eli\/lta\/(\d{4})\//)?.[1] || 0), isNewer = Number(year) > targetYear || (Number(year) === targetYear && Number(number) > Number(targetPath.match(/\/(\d+)$/)?.[1] || 0));
      if (e.reason_for_change === 'NewDocument' && exactName && isNewer) candidates.push({ source_id: id, kind: 'possible_new_consolidation' });
      else if (e.reason_for_change === 'NewDocument' && aliases.some(a => a.length > 7 && name.includes(a))) candidates.push({ source_id: id, kind: 'possible_amendment_or_related_instrument' });
    }
    if (candidates.length) discovery.push({ ...e, pinned_identity: pinned ? pinned.id : null, candidates });
  }
  const staged = [];
  if (mode !== '--discover') for (const source of manifest.documents) {
    try {
      const url = `${source.eli}/xml`, response = await fetchOfficial(url, 'application/xml, text/xml;q=0.9');
      if (!/xml/i.test(response.content_type || '') || !/<Dokument\b/.test(response.bytes.subarray(0, 5000).toString('utf8'))) throw Error(`unexpected official XML response type/body (${response.content_type})`);
      const xmlDigest = sha(response.bytes), observed = { source_id: source.id, source_url: url, final_url: response.final_url, content_type: response.content_type, etag: response.etag, last_modified: response.last_modified, xml_sha256: xmlDigest, bytes: response.bytes.length };
      let converted = convertXml(response.bytes.toString('utf8'), source, observed, at), fallbackHtml = false;
      if (!converted) {
        const xmlMeta = metadata(parseXml(response.bytes.toString('utf8')));
        const year = new URL(source.eli).pathname.split('/').at(-2), number = new URL(source.eli).pathname.split('/').at(-1);
        if (xmlMeta.year !== year || String(Number(xmlMeta.number)) !== String(Number(number))) throw Error(`official PDF metadata identity mismatch for ${source.id}`);
        if (source.expected_document_id && xmlMeta.document_id !== source.expected_document_id) throw Error(`DocumentId mismatch for ${source.id}: ${xmlMeta.document_id}`);
        if (source.expected_unique_document_id && xmlMeta.unique_document_id !== source.expected_unique_document_id) throw Error(`UniqueDocumentId mismatch for ${source.id}: ${xmlMeta.unique_document_id}`);
        if (source.expected_accession && xmlMeta.accession !== source.expected_accession) throw Error(`accession mismatch for ${source.id}: ${xmlMeta.accession}`);
        const expectedTitles = [source.title, ...(source.search_names || [])].map(norm);
        if (xmlMeta.title && !expectedTitles.some(k => norm(xmlMeta.title) === k || norm(xmlMeta.title).startsWith(k) || k.startsWith(norm(xmlMeta.title)))) throw Error(`official title mismatch for ${source.id}: ${xmlMeta.title}`);
        Object.assign(observed, xmlMeta);
        converted = await convertOfficialHtml(source, xmlMeta, xmlDigest, at);
        Object.assign(observed, { html_sha256: converted.metadata.html_sha256, rendered_document_id: xmlMeta.unique_document_id, rendered_accession: xmlMeta.accession });
        fallbackHtml = true;
      }
      const sourceDigest = sha(Buffer.from(`${xmlDigest}:${observed.html_sha256 || ''}`)), old = previous.sources[source.id] || {};
      const change = !old.source_sha256 ? 'first_observation' : old.source_sha256 !== sourceDigest ? 'official_source_changed' : old.markdown_sha256 !== converted.markdown_sha256 ? 'conversion_changed' : 'unchanged';
      Object.assign(observed, { title: converted.metadata.title || observed.title, document_id: converted.metadata.document_id || observed.document_id, accession: converted.metadata.accession || observed.accession, citation_year: converted.metadata.year || observed.year, citation_number: converted.metadata.number || observed.number, official_status: converted.metadata.status || observed.status, start_date: converted.metadata.start_date || observed.start_date, end_date: converted.metadata.end_date || observed.end_date, format_used: fallbackHtml ? 'official XML metadata + first-party official HTML body' : 'official XML', source_sha256: sourceDigest, markdown_sha256: converted.markdown_sha256, change });
      const ended = observed.end_date && Date.parse(`${observed.end_date}T00:00:00Z`) < Date.parse(`${at.slice(0, 10)}T00:00:00Z`);
      if (ended) observed.currentness_signal = 'source-version-end-date-is-before-check-date';
      observations.push(observed);
      if (mode === '--sync' && change !== 'unchanged') staged.push({ source, response, xmlDigest, observed, htmlBytes: converted.html_bytes || null, markdown: converted.markdown });
    } catch (e) { failures.push({ source_id: source.id, official_url: source.eli, error: e.message }); }
  }
  const currentnessReview = observations.filter(x => x.currentness_signal);
  const report = { report_version: 1, skill_version: VERSION, mode, checked_at: at, official_change_channel: FEED, official_feed_sha256: sha(feedFetch.bytes), retention_gap_requires_reconciliation: retentionGap, sitemap_entry_count: Object.keys(sitemap.entries).length, sitemap_added_path_count: addedPaths.length, sitemap_discovery_candidate_count: sitemapDiscovery.length, sitemap_discovery_candidates: sitemapDiscovery, source_count: manifest.documents.length, retrieved_count: observations.length, failed_count: failures.length, change_count: observations.filter(x => x.change !== 'unchanged').length, currentness_review_count: currentnessReview.length, currentness_review: currentnessReview.map(x => ({ source_id: x.source_id, end_date: x.end_date, signal: x.currentness_signal })), discovery_candidate_count: discovery.length, discovery_candidates: discovery, observations, failures, actions: failures.length ? ['No failed item was promoted; fix access or identity errors and rerun.'] : ['Changed documents and discovered legal instruments are candidates. Review amendment/currentness relationships before acknowledgement.'] };
  await atomic(reportFile, JSON.stringify(report, null, 2) + '\n');
  if (mode === '--sync' && observations.length === manifest.documents.length && failures.length === 0) {
    await mkdir(rawDir, { recursive: true }); await mkdir(candidateDir, { recursive: true });
    for (const item of staged) {
      const rawFile = path.join(rawDir, `${item.xmlDigest}.xml`); try { await readFile(rawFile); } catch { await atomic(rawFile, item.response.bytes); }
      if (item.htmlBytes) { const htmlFile = path.join(rawDir, `${item.observed.html_sha256}.html`); try { await readFile(htmlFile); } catch { await atomic(htmlFile, item.htmlBytes); } }
      delete item.observed._html_bytes;
      await atomic(path.join(candidateDir, `${safe(item.source.id)}.md`), item.markdown);
    }
    const next = { ...previous, version: 1, updated_at: at, last_atom_check: retentionGap ? previous.last_atom_check : at, atom_sha256: report.official_feed_sha256, sitemap_entries: sitemap.entries, sitemap_sha256: sitemap.hash, sources: { ...previous.sources } };
    for (const row of observations) next.sources[row.source_id] = { ...(previous.sources[row.source_id] || {}), ...row, last_checked_at: at };
    const atomPath = path.join(rawDir, `atom-${report.official_feed_sha256}.xml`); try { await readFile(atomPath); } catch { await atomic(atomPath, feedFetch.bytes); }
    for (const page of sitemap.pages) { const digest = sha(page.bytes), file = path.join(rawDir, `sitemap-${digest}.xml`); try { await readFile(file); } catch { await atomic(file, page.bytes); } }
    const indexDigest = sha(sitemap.top.bytes), indexFile = path.join(rawDir, `sitemap-index-${indexDigest}.xml`); try { await readFile(indexFile); } catch { await atomic(indexFile, sitemap.top.bytes); }
    await atomic(stateFile, JSON.stringify(next, null, 2) + '\n');
  }
  console.log(JSON.stringify({ mode, source_count: report.source_count, retrieved: report.retrieved_count, failed: report.failed_count, changed_or_first_seen: report.change_count, discovery_candidates: report.discovery_candidate_count, retention_gap_requires_reconciliation: retentionGap, report: reportFile }, null, 2));
  if (failures.length) process.exitCode = 1;
}
