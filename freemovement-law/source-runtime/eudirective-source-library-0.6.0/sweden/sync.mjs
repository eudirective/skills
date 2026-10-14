#!/usr/bin/env node
// Deterministic, source-scoped Swedish law refresh. Network reads only official publishers.
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { atomicProjectWrite, makeProjectTempDir, projectTempPath } from '../../runtime-storage.mjs';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const MANIFEST = JSON.parse(await readFile(path.join(ROOT, 'manifest.json'), 'utf8'));
const ALLOWED_HOSTS = new Set([
  ...MANIFEST.sources.flatMap(row => row.official_url ? [new URL(row.official_url).hostname] : []),
  ...Object.values(MANIFEST.discovery || {}).filter(value => typeof value === 'string' && /^https:\/\//i.test(value)).map(value => new URL(value).hostname),
]);
const args = new Set(process.argv.slice(2));
const mode = args.has('--sync') ? 'sync' : args.has('--verify') ? 'verify' : 'check';
const sha = b => createHash('sha256').update(b).digest('hex');
const mkdirp = p => mkdir(p, { recursive: true });
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
async function retainRaw(row, bytes) {
  const digest = sha(bytes);
  const ext = bytes.subarray(0, 5).toString() === '%PDF-' ? 'pdf'
    : /^\s*[\[{]/.test(bytes.subarray(0, 64).toString('utf8')) ? 'json' : 'html';
  const rel = path.join('work', 'raw', cleanName(row.id), `${digest}.${ext}`);
  const target = projectTempPath(path.join(ROOT, rel));
  try { await readFile(target); }
  catch {
    await mkdirp(path.dirname(target));
    await atomicProjectWrite(target, bytes);
  }
  return { raw_path: rel.replaceAll('\\', '/'), raw_sha256: digest, raw_bytes: bytes.length };
}
const WORK = projectTempPath(path.join(ROOT, 'work'));
const statePath = path.join(WORK, 'state.json');
let state = { schema_version: 1, checked_at: null, sources: {} };
try { state = JSON.parse(await readFile(statePath, 'utf8')); } catch {}

async function get(url, accept = '*/*') {
  let current = url;
  for (let redirects = 0; redirects < 7; redirects++) {
    const parsed = new URL(current);
    if (parsed.protocol !== 'https:' || !ALLOWED_HOSTS.has(parsed.hostname)) throw new Error(`Unapproved Swedish source URL or redirect: ${current}`);
    let response;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        response = await fetch(current, {
          headers: { 'user-agent': 'SwedenNationalSources/1.0 (reproducible legal-source updater)', accept },
          redirect: 'manual', signal: AbortSignal.timeout(45000),
        });
        if (![429, 500, 502, 503, 504].includes(response.status) || attempt === 2) break;
      } catch (error) {
        if (attempt === 2) throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 400 * 2 ** attempt));
    }
    if ([301, 302, 303, 307, 308].includes(response.status)) {
      const location = response.headers.get('location');
      if (!location) throw new Error(`Redirect without Location: ${current}`);
      current = new URL(location, current).href;
      continue;
    }
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${current}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    if (!bytes.length) throw new Error(`Empty response: ${current}`);
    if (bytes.length > 100_000_000) throw new Error(`Response exceeds 100 MB safety limit: ${current}`);
    return { response, bytes, url: current };
  }
  throw new Error(`Too many Swedish source redirects: ${url}`);
}
function htmlText(html) {
  let s = html.replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<(script|style|nav|header|footer|noscript|svg|form)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<br\b[^>]*>/gi, '\n')
    .replace(/<(br|\/p|\/h[1-6]|\/li|\/tr|\/section|\/article|\/div)\b[^>]*>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;|&#160;/gi, ' ').replace(/&amp;/gi, '&').replace(/&lt;/gi, '<').replace(/&gt;/gi, '>').replace(/&quot;/gi, '"').replace(/&#39;|&apos;/gi, "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&#x([\da-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
    .replace(/[\t\u00a0 ]+/g, ' ').replace(/ *\n */g, '\n').replace(/\n{3,}/g, '\n\n').trim();
  const start = s.search(/SFS nr:\s*\d{4}:\d+/i);
  if (start >= 0) s = s.slice(start);
  return s;
}
async function pdfMarkdown(bytes) {
  const tempDir = await makeProjectTempDir('sweden-pdf-');
  const pdfPath = path.join(tempDir, 'source.pdf');
  await writeFile(pdfPath, bytes);
  try {
    const { getDocument } = await import('pdfjs-dist/legacy/build/pdf.mjs');
    const doc = await getDocument({ data: new Uint8Array(bytes), useSystemFonts: true }).promise;
    const pages = [];
    for (let n = 1; n <= doc.numPages; n++) {
      const page = await doc.getPage(n), content = await page.getTextContent(), [, , width, height] = page.view;
      const lines = [];
      for (const item of content.items) {
        const value = item.str?.trim();
        if (!value) continue;
        const [x, y] = item.transform.slice(4, 6);
        if (y < 25 || /^StyrD\d+\b/i.test(value) || /^(?:\d\s+){5,}\d$/.test(value)) continue;
        if (/^\d{1,3}$/.test(value) && x > width * 0.8 && y < 120) continue;
        let line = lines.find(candidate => Math.abs(candidate.y - y) <= 3.8);
        if (!line) { line = { y, items: [] }; lines.push(line); }
        line.items.push({ x, width: item.width || 0, value, size: item.height || 10 });
      }
      const ordered = lines.sort((a, b) => b.y - a.y).map(line => {
        const parts = line.items.sort((a, b) => a.x - b.x); let out = '', last = null;
        for (const part of parts) {
          const gap = last ? part.x - (last.x + last.width) : 0;
          if (out && gap > Math.max(1.2, part.size * 0.16) && !out.endsWith(' ') && !part.value.startsWith(' ')) out += ' ';
          out += part.value; last = part;
        }
        return out.trim();
      }).filter(Boolean);
      pages.push(ordered.join('\n'));
    }
    return pages.join('\n\n').replace(/[\t ]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
  } finally { await rm(tempDir, { recursive: true, force: true }); }
}
function cleanName(s) { return s.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^-|-$/g, '').toLowerCase(); }
function relFor(row) { return `${row.type === 'sfs-amendment' ? 'amendments' : row.type === 'sfs' ? 'statutes' : row.type === 'migrfs' ? 'migrfs' : 'case-law'}/${cleanName(row.id)}.md`; }
async function record(row, bytes, sourceUrl, text) {
  const hash = sha(bytes), textHash = sha(Buffer.from(text, 'utf8')), old = state.sources[row.id];
  const raw = await retainRaw(row, bytes);
  const file = path.join(ROOT, 'documents', relFor(row));
  let acceptedHash = null;
  try {
    const accepted = await readFile(file, 'utf8');
    const body = accepted.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n\r?\n/, '');
    acceptedHash = sha(Buffer.from(body, 'utf8'));
  } catch {}
  const outcome = acceptedHash === null ? 'new' : acceptedHash === textHash ? 'unchanged' : 'changed';
  const metadata = { id: row.id, source_url: sourceUrl, retrieved_at: now(), http_last_modified: null, etag: null, content_sha256: hash, markdown_sha256: textHash, ...raw, status: outcome };
  if (mode === 'sync' && outcome !== 'unchanged') {
    const target = outcome === 'changed' ? projectTempPath(path.join(ROOT, 'pending', relFor(row))) : file;
    await mkdirp(path.dirname(target));
    const front = `---\nid: ${row.id}\nlabel: ${JSON.stringify(row.label)}\nofficial_source: ${sourceUrl}\nretrieved_at: ${metadata.retrieved_at}\nsource_sha256: ${hash}\n---\n\n`;
    await atomicProjectWrite(target, front + text, 'utf8');
    if (outcome === 'new') await rm(projectTempPath(path.join(ROOT, 'pending', relFor(row))), { force: true });
  }
  state.sources[row.id] = metadata;
  console.log(`${outcome.padEnd(9)} ${row.id}  ${sourceUrl}`);
}

async function syncSfs(row) {
  if (row.type === 'sfs-amendment' && row.official_url) {
    const got = await get(row.official_url, 'application/pdf');
    if (got.bytes.subarray(0, 5).toString() !== '%PDF-') throw new Error(`Official SFS publication was not a PDF: ${got.url}`);
    const text = await pdfMarkdown(got.bytes), normalized = text.toLocaleLowerCase('sv').replace(/[\s:]/g, '');
    if (!normalized.includes(`sfs${row.sfs.replace(':', '')}`.toLocaleLowerCase('sv'))) throw new Error(`SFS publication identity check failed for ${row.id}`);
    await record(row, got.bytes, got.url, text); return;
  }
  const [year, number] = row.sfs.split(':');
  const url = `https://data.riksdagen.se/dokument/sfs-${year}-${number}.html`;
  const got = await get(url, 'text/html');
  const text = htmlText(got.bytes.toString('utf8'));
  const normalized = text.toLocaleLowerCase('sv').replace(/\s/g, '');
  if (!normalized.includes(`sfsnr:${row.sfs}`.toLocaleLowerCase('sv')) || text.length < 500) throw new Error(`SFS identity/content validation failed for ${row.id}`);
  const registerHref = got.bytes.toString('utf8').match(/href=["']([^"']*sfsr\?bet=[^"']+)["']/i)?.[1]?.replace(/&amp;/g, '&');
  let amendmentIds = [];
  if (registerHref) {
    try {
      const reg = await get(new URL(registerHref, got.url).href, 'text/html');
      amendmentIds = [...new Set([...reg.bytes.toString('utf8').matchAll(/SFS\s+(\d{4}:\d+)/gi)].map(m => m[1]))].sort();
    } catch (e) { console.error(`warning   amendment register unavailable for ${row.id}: ${e.message}`); }
  }
  const hadRegister = Array.isArray(state.sources[row.id]?.amendment_ids);
  const previousIds = state.sources[row.id]?.amendment_ids || [];
  const additions = hadRegister ? amendmentIds.filter(id => !previousIds.includes(id)) : [];
  await record(row, got.bytes, got.url, text);
  state.sources[row.id].amendment_ids = amendmentIds;
  state.sources[row.id].new_amendments = additions;
  for (const id of additions) console.log(`candidate amendment ${row.sfs} <- SFS ${id}`);
}
async function getMigrfsCatalog() {
  const got = await get(MANIFEST.discovery.migrationsverket_catalog, 'text/html');
  return { ...got, html: got.bytes.toString('utf8') };
}
function migrfsLinks(html) {
  const entries = new Map();
  for (const m of html.matchAll(/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)) {
    const label = m[2].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    const match = label.match(/MIGRFS\s+(\d{4}[:/]\d+|\d+\/\d{4})/i);
    if (!match) continue;
    const href = m[1].replace(/&amp;/g, '&');
    if (/\.pdf(?:$|\?)/i.test(href)) entries.set(match[1].replace('/', ':'), new URL(href, MANIFEST.discovery.migrationsverket_catalog).href);
  }
  return entries;
}
function normalizeMigrfs(s) { return s.replace('/', ':'); }
async function syncMigrfs(row, links) {
  const key = normalizeMigrfs(row.migrfs), url = links.get(key);
  if (!url) { console.log(`missing   ${row.id}  not listed in current official MIGRFS catalog`); state.sources[row.id] = { ...(state.sources[row.id] || {}), status: 'missing-from-current-catalog', checked_at: now() }; return; }
  const got = await get(url, 'application/pdf');
  if (got.bytes.subarray(0, 5).toString() !== '%PDF-') throw new Error(`Official publisher response was not a PDF: ${url}`);
  const text = await pdfMarkdown(got.bytes);
  if (text.length < 150) throw new Error(`MIGRFS text extraction was empty or too short: ${row.id}`);
  await record(row, got.bytes, got.url, text);
}
async function syncCourt(row) {
  if (!row.official_url) {
    console.log(`needs-official-id          ${row.id}  ${row.discovery_url}`);
    state.sources[row.id] = { ...(state.sources[row.id] || {}), status: 'needs-official-id', checked_at: now(), case_number: row.case_number };
    return;
  }
  const got = await get(row.official_url, 'application/json, application/pdf');
  let text;
  if (got.bytes.subarray(0, 5).toString() === '%PDF-') text = await pdfMarkdown(got.bytes);
  else {
    const publication = JSON.parse(got.bytes.toString('utf8'));
    const normalizeCase = s => String(s || '').toLocaleUpperCase('sv').replace(/[^A-Z0-9]/g, '');
    if (!(publication.malNummerLista || []).some(x => normalizeCase(x) === normalizeCase(row.case_number)) || publication.domstol?.domstolKod !== 'MIOD') throw new Error(`Official API record identity validation failed for ${row.id}`);
    if (row.decision_date && publication.avgorandedatum !== row.decision_date) throw new Error(`Official API decision date mismatch for ${row.id}`);
    if (!publication.innehall) throw new Error(`Official API record has no full-text content for ${row.id}`);
    const heading = `${publication.domstol.domstolNamn}\nMål nr ${row.case_number}\nAvgörandedatum ${publication.avgorandedatum}\n${(publication.referatNummerLista || []).join(', ')}\n`;
    text = heading + '\n' + htmlText(publication.innehall) + '\n';
  }
  if (!text.toLocaleLowerCase('sv').replace(/\s/g, '').includes(row.case_number.toLocaleLowerCase('sv').replace(/\s/g, ''))) throw new Error(`Case number validation failed for ${row.id}`);
  await record(row, got.bytes, got.url, text);
}
async function verifyLocal() {
  const failures = [], checked = [];
  for (const row of MANIFEST.sources) {
    const meta = state.sources[row.id];
    if (!meta?.raw_path || !meta.raw_sha256) { failures.push({ id: row.id, error: 'raw source snapshot is not registered; run --check to retrieve it' }); continue; }
    try {
      const raw = await readFile(projectTempPath(path.join(ROOT, meta.raw_path)));
      if (sha(raw) !== meta.raw_sha256 || sha(raw) !== meta.content_sha256) throw new Error('raw snapshot hash differs from state metadata');
      let text;
      if (raw.subarray(0, 5).toString() === '%PDF-') text = await pdfMarkdown(raw);
      else if (row.type === 'court-case') {
        const publication = JSON.parse(raw.toString('utf8'));
        if (!publication.innehall) throw new Error('official case response has no stored full-text content');
        text = `${publication.domstol?.domstolNamn || ''}\nMål nr ${row.case_number}\nAvgörandedatum ${publication.avgorandedatum || ''}\n${(publication.referatNummerLista || []).join(', ')}\n\n${htmlText(publication.innehall)}\n`;
      } else text = htmlText(raw.toString('utf8'));
      const textHash = sha(Buffer.from(text, 'utf8'));
      const file = path.join(ROOT, 'documents', relFor(row));
      const accepted = await readFile(file, 'utf8');
      const body = accepted.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n\r?\n/, '');
      if (textHash !== meta.markdown_sha256 || sha(Buffer.from(body, 'utf8')) !== textHash) throw new Error('replayed Markdown differs from accepted Markdown or state hash');
      checked.push(row.id);
    } catch (e) { failures.push({ id: row.id, error: e.message }); }
  }
  console.log(JSON.stringify({ mode: 'verify', checked: checked.length, failures }, null, 2));
  if (failures.length) process.exitCode = 1;
}
async function discover() {
  const [mig, lawsPage] = await Promise.all([getMigrfsCatalog(), get(MANIFEST.discovery.migrationsverket_laws_page, 'text/html')]);
  const migLinks = migrfsLinks(mig.html), knownMig = new Set(MANIFEST.sources.filter(x => x.migrfs).map(x => normalizeMigrfs(x.migrfs)));
  const migCandidates = [...migLinks.keys()].filter(x => !knownMig.has(x));
  const amendments = Object.entries(state.sources).flatMap(([id, item]) => (item.new_amendments || []).map(sfs => ({ id, sfs })));
  console.log(`Tracked SFS amendment registers: ${amendments.length} unreviewed new amendment candidates.`);
  for (const item of amendments) console.log(`candidate SFS ${item.sfs} amends ${item.id}`);
  console.log(`Migrationsverket catalog: ${migLinks.size} MIGRFS entries; ${migCandidates.length} unregistered candidates.`);
  for (const item of migCandidates) console.log(`candidate MIGRFS ${item}`);
  const lawText = htmlText(lawsPage.bytes.toString('utf8'));
  const knownSfs = new Set(MANIFEST.sources.filter(x => x.sfs).map(x => x.sfs));
  const lawCandidates = [...new Set([...lawText.matchAll(/\b(\d{4}:\d{1,4})\b/g)].map(m => m[1]))].filter(x => !knownSfs.has(x));
  console.log(`Migrationsverket legal-framework page: ${lawCandidates.length} unregistered SFS references for review.`);
  for (const sfs of lawCandidates) console.log(`candidate SFS ${sfs}: ${MANIFEST.discovery.migrationsverket_laws_page}`);
  const from = state.last_court_catalog_check || MANIFEST.discovery.court_baseline_date;
  const courtUrl = `https://rattspraxis.etjanst.domstol.se/api/v1/publiceringar?domstolkod=MIOD&publicerad_fran_och_med=${encodeURIComponent(from)}&sortorder=publiceringstid&page=1&pagesize=100`;
  const court = await get(courtUrl, 'application/json');
  const publications = JSON.parse(court.bytes.toString('utf8'));
  const knownCases = new Set(MANIFEST.sources.filter(x => x.type === 'court-case').map(x => (x.case_number || '').toUpperCase().replace(/[^A-Z0-9]/g, '')));
  const newCases = publications.filter(x => !(x.malNummerLista || []).some(n => knownCases.has(String(n).toUpperCase().replace(/[^A-Z0-9]/g, ''))));
  console.log(`Sök rättspraxis Migrationsöverdomstolen: ${publications.length} published records since ${from}; ${newCases.length} untracked record candidates.`);
  for (const item of newCases) console.log(`candidate court record ${item.id}: ${(item.malNummerLista || []).join(', ') || item.referatNummerLista?.join(', ') || '(case number not supplied)'} (${item.avgorandedatum})`);
  state.discoveries = {
    checked_at: now(), court_from: from,
    sfs_amendments: amendments,
    migrationsverket_new_migrfs: migCandidates,
    migrationsverket_sfs_references: lawCandidates,
    court_records: newCases.map(x => ({ id: x.id, cases: x.malNummerLista || [], references: x.referatNummerLista || [], decision_date: x.avgorandedatum }))
  };
  const unresolved = MANIFEST.sources.filter(x => x.type === 'court-case' && x.status === 'needs_official_id');
  console.log(`Court decisions: ${unresolved.length} source records require resolving an official publication ID in Sök rättspraxis before automation can pin them.`);
  for (const row of unresolved) console.log(`candidate case ${row.case_number}: ${row.discovery_url}`);
}

if (args.has('--verify')) await verifyLocal();
else if (args.has('--discover')) await discover();
else if (args.has('--ack')) {
  const index = process.argv.indexOf('--ack'), id = process.argv[index + 1];
  const row = MANIFEST.sources.find(x => x.id === id);
  if (!row) throw new Error(`Unknown source id for --ack: ${id || '(missing)'}`);
  const pending = projectTempPath(path.join(ROOT, 'pending', relFor(row))), target = path.join(ROOT, 'documents', relFor(row));
  await mkdirp(path.dirname(target)); await atomicProjectWrite(target, await readFile(pending)); await rm(pending, { force: true });
  state.sources[id] = { ...(state.sources[id] || {}), status: 'accepted-after-review', accepted_at: now() };
  await atomicProjectWrite(statePath, JSON.stringify(state, null, 2) + '\n');
  console.log(`accepted ${id} after review`);
}
else if (args.has('--check') || args.has('--sync')) {
  const catalog = await getMigrfsCatalog(), links = migrfsLinks(catalog.html);
  for (const row of MANIFEST.sources) {
    try {
      if (row.type === 'sfs' || row.type === 'sfs-amendment') await syncSfs(row);
      else if (row.type === 'migrfs') await syncMigrfs(row, links);
      else if (row.type === 'court-case') await syncCourt(row);
    } catch (e) {
      console.error(`error     ${row.id}  ${e.message}`);
      state.sources[row.id] = { ...(state.sources[row.id] || {}), status: 'error', checked_at: now(), error: e.message };
    }
  }
  if (mode === 'sync') {
    await discover();
    state.checked_at = now(); state.last_court_catalog_check = new Date().toISOString().slice(0, 10);
    await atomicProjectWrite(statePath, JSON.stringify(state, null, 2) + '\n');
  } else {
    state.checked_at = now();
    await atomicProjectWrite(statePath, JSON.stringify(state, null, 2) + '\n');
  }
  if (args.has('--discover')) await discover();
} else {
  console.error('Usage: node sync.mjs --check|--sync|--discover|--verify|--ack <source-id>'); process.exitCode = 2;
}
