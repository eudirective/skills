#!/usr/bin/env node
// Retrieve official Czech guidance and e-Sbírka's public date-bound PDF
// representations of consolidated acts, then preserve review-only candidates.
import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, copyFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { atomicProjectWrite, projectTempPath } from '../../runtime-storage.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WORK = projectTempPath(path.join(ROOT, 'work'));
const RAW = path.join(WORK, 'raw');
const DOCUMENTS = path.join(ROOT, 'documents');
const MANIFEST_PATH = path.join(ROOT, 'references', 'source-register.json');
const STATE_PATH = path.join(WORK, 'state.json');
const REPORT_PATH = path.join(WORK, 'latest-report.json');
const VERSION = '0.4.2';
const HTML_CONVERSION_VERSION = '0.3.0';
const MAX_SOURCE_BYTES = 25 * 1024 * 1024;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const safe = value => String(value).toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^-|-$/g, '');
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

async function json(file, fallback) {
  try { return JSON.parse(await readFile(file, 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return fallback; throw error; }
}
async function atomic(file, data) {
  await mkdir(path.dirname(file), { recursive: true });
  await atomicProjectWrite(file, data);
}
function workFile(relative, area) {
  if (typeof relative !== 'string') throw new Error('Saved work path must be a string.');
  const portable = relative.replace(/\\/g, '/');
  if (portable.startsWith('/') || /^[A-Za-z]:/.test(portable) || portable.split('/').includes('..')) {
    throw new Error(`Refused unsafe saved work path: ${relative}`);
  }
  if (area === 'raw') {
    if (!portable.startsWith('work/raw/')) throw new Error(`Saved path is outside work/raw: ${relative}`);
    return projectTempPath(path.resolve(ROOT, ...portable.split('/')));
  }
  if (!portable.startsWith('work/pending/')) throw new Error(`Saved review path is outside work/pending/: ${relative}`);
  return projectTempPath(path.resolve(ROOT, ...portable.split('/')));
}
function candidateClass(source) {
  const type = source.source_type;
  if (type === 'national_legislation' || type === 'constitutional_text') return 'legislation';
  if (type === 'official_guidance' || type === 'official_public_service_guidance' || type === 'official_consular_guidance') return 'guidance';
  if (type === 'official_application_form_pdf') return 'forms';
  if (type === 'official_guidance_directory' || type === 'official_forms_directory' || type === 'official_mission_directory' || type === 'discovery_repository') return 'discovery';
  throw new Error(`No candidate folder mapping for source type ${type || '(missing)'}.`);
}
function candidateRelativePath(source) { return path.posix.join('work', 'pending', candidateClass(source), `${safe(source.id)}.md`); }
function errorDetails(error) {
  const cause = error?.cause;
  return [error?.message || String(error), cause?.code, cause?.message]
    .filter((value, index, values) => value && values.indexOf(value) === index)
    .join(' — ');
}
function decodeEntities(value) {
  return String(value).replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos|nbsp|ndash|mdash|rsquo|lsquo|rdquo|ldquo|sect|copy|hellip|acute|bdquo|bull);/gi, (whole, entity) => {
    if (entity[0] === '#') {
      const number = entity[1].toLowerCase() === 'x' ? parseInt(entity.slice(2), 16) : Number(entity.slice(1));
      return Number.isInteger(number) && number > 0 && number <= 0x10ffff ? String.fromCodePoint(number) : whole;
    }
    return ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', ndash: '–', mdash: '—', rsquo: '’', lsquo: '‘', rdquo: '”', ldquo: '“', sect: '§', copy: '©', hellip: '…', acute: '´', bdquo: '„', bull: '•' })[entity.toLowerCase()] || whole;
  });
}
function attr(tag, key) {
  const attributes = tag.replace(/^<\s*[^\s/>]+/, '').replace(/\/?\s*>$/, '');
  const pattern = /([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;
  let match;
  while ((match = pattern.exec(attributes))) {
    if (match[1].toLowerCase() === key.toLowerCase()) return match[2] ?? match[3] ?? match[4] ?? '';
  }
  return '';
}
function decodeHtml(bytes, contentType = '') {
  const labels = [];
  const header = contentType.match(/\bcharset\s*=\s*([^;\s]+)/i)?.[1];
  if (header) labels.push(header.replace(/^['"]|['"]$/g, ''));
  const probe = bytes.toString('latin1');
  for (const meta of probe.match(/<meta\b[^>]*>/gi) || []) {
    const direct = attr(meta, 'charset');
    if (direct) labels.push(direct);
    const content = attr(meta, 'content');
    const equiv = attr(meta, 'http-equiv');
    if (content && /^content-type$/i.test(equiv)) {
      const declared = content.match(/\bcharset\s*=\s*([^;\s]+)/i)?.[1];
      if (declared) labels.push(declared.replace(/^['"]|['"]$/g, ''));
    }
  }
  let encoding = 'utf-8';
  if (labels.length) {
    const canonical = labels.map(label => {
      try { return new TextDecoder(label).encoding; }
      catch { throw new Error(`Unsupported HTML character encoding: ${label}`); }
    });
    if (canonical.some(label => label !== canonical[0])) throw new Error(`Conflicting HTML character encodings: ${labels.join(', ')}`);
    encoding = canonical[0];
  }
  try { return new TextDecoder(encoding, { fatal: true }).decode(bytes); }
  catch (error) { throw new Error(`Could not decode HTML as ${encoding}: ${error.message}`); }
}
function extractElement(html, name, id = '', className = '') {
  const opening = new RegExp(`<${name}\\b[^>]*>`, 'gi'); let match;
  while ((match = opening.exec(html))) {
    if (id && attr(match[0], 'id').toLowerCase() !== id.toLowerCase()) continue;
    if (className && !attr(match[0], 'class').split(/\s+/).includes(className)) continue;
    const tags = new RegExp(`<\\/?${name}\\b[^>]*>`, 'gi'); tags.lastIndex = match.index;
    let depth = 0, tag;
    while ((tag = tags.exec(html))) {
      if (/^<\//.test(tag[0])) depth--;
      else if (!/\/\s*>$/.test(tag[0])) depth++;
      if (!depth) return html.slice(match.index, tags.lastIndex);
    }
    throw new Error(`unclosed source element <${name}>`);
  }
  return '';
}
function sourceBody(html) {
  for (const tag of ['main', 'article']) {
    const body = extractElement(html, tag);
    if (body.length > 300) return { html: body, method: `<${tag}>` };
  }
  for (const id of ['main', 'content', 'primary']) {
    const body = extractElement(html, 'div', id);
    if (body.length > 300) return { html: body, method: `#${id}` };
  }
  for (const className of ['gov3-container', 'main-content']) {
    const body = extractElement(html, 'div', '', className);
    if (body.length > 300) return { html: body, method: `.${className}` };
  }
  throw new Error('No stable main/article content region found on official page.');
}
function linkTarget(href, baseUrl) {
  if (!href || !baseUrl || href.trim().startsWith('#')) return '';
  try {
    const target = new URL(href, baseUrl);
    return ['https:', 'http:'].includes(target.protocol) ? target.href : '';
  } catch { return ''; }
}
function convertHtml(fragment, baseUrl = '') {
  const tokens = fragment.match(/<!--[\s\S]*?-->|<![^>]*>|<[^>]*>|[^<]+/g) || [];
  const skipped = new Set(['script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside', 'form', 'button', 'select', 'option']);
  const blocks = new Set(['p', 'div', 'section', 'article', 'main', 'blockquote', 'tr', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']);
  const stack = []; let out = '';
  const boundary = () => { out = out.replace(/[ \t]+$/g, ''); if (out && !out.endsWith('\n\n')) out += '\n\n'; };
  for (const token of tokens) {
    if (token.startsWith('<!--') || /^<!/i.test(token)) continue;
    if (!token.startsWith('<')) { if (!stack.some(item => item.skip)) out += decodeEntities(token).replace(/\s+/g, ' '); continue; }
    const closing = /^<\//.test(token), name = token.match(/^<\/?\s*([\w:-]+)/)?.[1]?.toLowerCase();
    if (!name) continue;
    if (!closing) {
      const hint = `${attr(token, 'id')} ${attr(token, 'class')}`.toLowerCase();
      const skip = skipped.has(name) || /breadcrumb|cookie|skiplink|pagination|share|toolbar|sidebar|menu|navigation|social/.test(hint);
      const link = name === 'a' && !skip ? linkTarget(attr(token, 'href'), baseUrl) : '';
      stack.push({ name, skip, link, linkStart: out.length });
      if (skip) continue;
      if (link) out += '[';
      if (blocks.has(name)) boundary();
      if (/^h[1-6]$/.test(name)) out += `${'#'.repeat(Number(name[1]))} `;
      if (name === 'li') { boundary(); out += '- '; }
      if (name === 'br') boundary();
      if (name === 'td' || name === 'th') { if (out && !out.endsWith('\n') && !out.endsWith(' ')) out += ' | '; }
    } else {
      const position = stack.map(item => item.name).lastIndexOf(name);
      if (position < 0) continue;
      const row = stack[position]; stack.splice(position);
      if (row.skip) continue;
      if (row.link) {
        const label = out.slice(row.linkStart + 1).trim();
        if (label) out += `](<${row.link}>)`;
        else out = out.slice(0, row.linkStart);
      }
      if (name === 'li' || blocks.has(name)) boundary();
    }
  }
  return out.replace(/[\t\u00a0 ]+\n/g, '\n').replace(/\n[\t ]+/g, '\n').replace(/\n{3,}/g, '\n\n').replace(/[ \t]{2,}/g, ' ').replace(/^#{1,6}(?:\s*#+)?\s*$/gm, '').replace(/^#{1,6} \*+$/gm, '').replace(/\n{3,}/g, '\n\n').trim();
}
function pageTitle(html, fallback) {
  const value = html.match(/<title\b[^>]*>([\s\S]*?)<\/title\s*>/i)?.[1] || html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1\s*>/i)?.[1] || fallback;
  return convertHtml(value).replace(/\s*[|–-]\s*(?:Ministry|Portal|Government).*$/i, '').trim() || fallback;
}
function pageHeading(html) {
  const headings = [...html.matchAll(/<h1\b[^>]*>([\s\S]*?)<\/h1\s*>/gi)];
  return headings.map(match => convertHtml(match[1])).find(value => value.trim())?.trim() || '';
}
function normalizeHeading(value) {
  return String(value).normalize('NFKC').replace(/[’‘]/g, "'").replace(/[“”]/g, '"').replace(/\s+/g, ' ').trim().toLocaleLowerCase('en');
}
async function readBoundedBody(response, url) {
  if (!response.body) throw new Error(`Empty response body from ${url}`);
  const reader = response.body.getReader(), chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_SOURCE_BYTES) {
        await reader.cancel();
        throw new Error(`Source response exceeded the ${MAX_SOURCE_BYTES}-byte limit from ${url}`);
      }
      chunks.push(Buffer.from(value));
    }
  } finally { reader.releaseLock(); }
  return Buffer.concat(chunks, size);
}
async function fetchOfficial(url, hosts, expectedFormat = 'html') {
  let current = url;
  for (let redirect = 0; redirect <= 5; redirect++) {
    const parsed = new URL(current);
    if (parsed.protocol !== 'https:' || !hosts.includes(parsed.hostname)) throw new Error(`Refused non-allowlisted URL or redirect: ${current}`);
    const accept = expectedFormat === 'pdf' ? 'application/pdf' : 'text/html,application/xhtml+xml';
    const response = await fetch(current, { redirect: 'manual', signal: AbortSignal.timeout(30_000), headers: { accept, 'user-agent': `czechia-source-library/${VERSION}` } });
    if ([301, 302, 303, 307, 308].includes(response.status)) {
      const location = response.headers.get('location');
      if (!location) throw new Error(`Redirect without Location from ${current}`);
      current = new URL(location, current).href;
      continue;
    }
    if (!response.ok) throw new Error(`HTTP ${response.status} from ${current}`);
    const contentType = response.headers.get('content-type') || '';
    const validType = expectedFormat === 'pdf' ? /application\/pdf/i.test(contentType) : /text\/html|application\/xhtml\+xml/i.test(contentType);
    if (!validType) throw new Error(`Unexpected ${expectedFormat} content type ${contentType || '(missing)'} from ${current}`);
    const declaredLength = Number(response.headers.get('content-length'));
    if (Number.isFinite(declaredLength) && declaredLength > MAX_SOURCE_BYTES) throw new Error(`Source response exceeded the ${MAX_SOURCE_BYTES}-byte limit from ${current}`);
    const bytes = await readBoundedBody(response, current);
    if (bytes.length < 500) throw new Error(`Source response was too short (${bytes.length} bytes) from ${current}`);
    if (expectedFormat === 'pdf' && bytes.subarray(0, 5).toString('ascii') !== '%PDF-') throw new Error(`Response did not have a PDF signature from ${current}`);
    return { bytes, final_url: current, content_type: contentType, format: expectedFormat, etag: response.headers.get('etag'), last_modified: response.headers.get('last-modified') };
  }
  throw new Error(`Too many redirects from ${url}`);
}
function actReference(source) {
  const match = source.url.match(/\/sb\/(\d{4})\/(\d+)\/?$/);
  if (!match) throw new Error(`Cannot derive an e-Sbírka stable download route from ${source.url}`);
  return { year: match[1], number: match[2], origin: new URL(source.url).origin };
}
function stableDownloadUrl(source, asOfDate) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(asOfDate)) throw new Error(`Invalid consolidation date: ${asOfDate}`);
  const { year, number, origin } = actReference(source);
  return `${origin}/sb/${year}/${number}/${asOfDate}.pdf`;
}
async function pdfText(bytes) {
  const { getDocument } = await import('pdfjs-dist/legacy/build/pdf.mjs');
  const document = await getDocument({ data: new Uint8Array(bytes), useSystemFonts: true }).promise;
  const pages = [];
  for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber++) {
    const page = await document.getPage(pageNumber), content = await page.getTextContent();
    const lines = [];
    for (const item of content.items) {
      const value = item.str?.trim();
      if (!value) continue;
      const [x, y] = item.transform.slice(4, 6);
      let line = lines.find(row => Math.abs(row.y - y) <= 3.5);
      if (!line) { line = { y, items: [] }; lines.push(line); }
      line.items.push({ x, width: item.width || 0, value });
    }
    pages.push(lines.sort((a, b) => b.y - a.y).map(line => {
      let output = '', previous;
      for (const item of line.items.sort((a, b) => a.x - b.x)) {
        const gap = previous ? item.x - (previous.x + previous.width) : 0;
        if (output && gap > 1.5 && !output.endsWith(' ') && !item.value.startsWith(' ')) output += ' ';
        output += item.value;
        previous = item;
      }
      return output.trim();
    }).filter(Boolean).join('\n'));
  }
  return pages.join('\n\n').replace(/[\t\u00a0 ]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
}
function validateActIdentity(source, content) {
  const { year, number } = actReference(source);
  const normalized = content.normalize('NFKC').replace(/\s+/g, ' ');
  const citation = new RegExp(`\\b${number}\\s*\\/\\s*${year}\\s*Sb\\.?`, 'i');
  if (!citation.test(normalized)) throw new Error(`Downloaded PDF did not contain the expected Czech citation ${number}/${year} Sb.`);
}
function makeActMarkdown(source, response, asOfDate, content) {
  if (content.length < 1000) throw new Error(`Official PDF exposed too little act text (${content.length} characters).`);
  validateActIdentity(source, content);
  return {
    method: `e-Sbírka PDF text extraction as of ${asOfDate}`,
    markdown: `# ${source.title}\n\n- Source ID: \`${source.id}\`\n- Source type: \`${source.source_type}\`\n- Content language: \`${source.language}\`\n- Official record URL: ${source.url}\n- Retrieved URL: ${response.final_url}\n- Consolidation date requested: ${asOfDate}\n- Source format: official e-Sbírka PDF (informative consolidated text)\n- Source bytes SHA-256: \`${sha(response.bytes)}\`\n- Conversion: Czechia e-Sbírka PDF text extraction ${VERSION}\n- Coverage: PDF text items are grouped into lines and pages; visual layout, exact table structure, and footnote placement may not be preserved.\n\n> Review candidate only. e-Sbírka describes consolidated text as informative. The requested date identifies the consolidation snapshot; it does not establish legal force, completeness, or applicability.\n\n${content}\n`
  };
}
async function fetchPublicAct(source, hosts, asOfDate) {
  const downloadUrl = stableDownloadUrl(source, asOfDate);
  const response = await fetchOfficial(downloadUrl, hosts, 'pdf');
  const content = await pdfText(response.bytes);
  validateActIdentity(source, content);
  if (content.length < 1000) throw new Error(`Official PDF exposed too little act text (${content.length} characters).`);
  return { ...response, content, download_url: downloadUrl, retrieval_as_of: asOfDate };
}
async function replayActMarkdown(source, row, bytes) {
  const retrievalDate = row.retrieval_as_of || row.final_url?.match(/\/(\d{4}-\d{2}-\d{2})\.pdf(?:$|\?)/)?.[1];
  if (!retrievalDate) throw new Error('saved stable-download candidate has no consolidation date');
  const response = { bytes, final_url: row.final_url };
  return makeActMarkdown(source, response, retrievalDate, await pdfText(bytes)).markdown;
}
async function renderSavedMarkdown(source, row, bytes) {
  const format = row.format || path.extname(String(row.raw_path || '')).slice(1).replace(/^\./, '');
  if (format === 'pdf') {
    const retrievalDate = row.retrieval_as_of || row.final_url?.match(/\/(\d{4}-\d{2}-\d{2})\.pdf(?:$|\?)/)?.[1];
    if (!retrievalDate) throw new Error('saved stable-download candidate has no consolidation date');
    return { markdown: await replayActMarkdown(source, row, bytes), method: `e-Sbírka PDF text extraction as of ${retrievalDate}` };
  }
  if (format !== 'html') throw new Error(`Unsupported saved source format: ${format || '(missing)'}`);
  const html = decodeHtml(bytes, row.content_type || ''), extracted = sourceBody(html);
  const sourceWithRetrievedUrl = row.final_url ? { ...source, retrieved_url: row.final_url } : source;
  const converted = makeMarkdown(sourceWithRetrievedUrl, html, extracted.html, extracted.method);
  return { markdown: converted.markdown, method: extracted.method };
}
function makeMarkdown(source, html, body, method) {
  const title = pageTitle(html, source.title), heading = pageHeading(html), content = convertHtml(body, source.retrieved_url || source.url);
  if (!source.expected_heading) throw new Error(`Manifest is missing expected_heading for ${source.id}.`);
  if (!heading || normalizeHeading(heading) !== normalizeHeading(source.expected_heading)) {
    throw new Error(`Official page heading mismatch for ${source.id}: expected “${source.expected_heading}”, found “${heading || '(missing)'}”.`);
  }
  if (content.length < 200) throw new Error(`Converted main content is too short for ${source.id} (${content.length} characters).`);
  return {
    title,
    method,
    markdown: `# ${source.title}\n\n- Source ID: \`${source.id}\`\n- Source type: \`${source.source_type}\`\n- Content language: \`${source.language}\`\n- Official page heading: ${heading}\n- Official page title: ${title}\n- Official record URL: ${source.url}\n- Retrieved URL: ${source.retrieved_url || source.url}\n- Conversion: Czechia official HTML to Markdown ${HTML_CONVERSION_VERSION}\n- Coverage: page content extracted from ${method}; site chrome is omitted, and HTTP(S) links are preserved as links. Linked attachment contents are not fetched by this rule.\n\n> Review the official page directly; record its displayed date/version, scope, and any legal-status or content caveat. For a legal-text question, consult a specific Gazette act only when a material gap remains.\n\n${content}\n`
  };
}

const manifest = await readFile(MANIFEST_PATH, 'utf8').then(JSON.parse);
const state = await json(STATE_PATH, { version: 1, sources: {} });
const mode = process.argv.find(arg => ['--check', '--sync', '--verify', '--reconvert', '--ack'].includes(arg)) || '--check';
if (mode === '--ack') {
  const id = process.argv[process.argv.indexOf('--ack') + 1];
  const source = manifest.documents.find(item => item.id === id);
  if (!source || source.monitor_only || candidateClass(source) !== 'guidance') throw new Error('--ack requires a retrieved official guidance candidate ID.');
  const row = state.sources[id];
  if (!row?.raw_path || !row?.candidate_path) throw new Error(`Cannot acknowledge ${id}: no saved official retrieval state exists.`);
  const raw = await readFile(workFile(row.raw_path, 'raw'));
  if (sha(raw) !== row.source_bytes_sha256) throw new Error(`Cannot acknowledge ${id}: saved official source-byte hash mismatch.`);
  const candidate = await readFile(workFile(row.candidate_path, 'candidates'));
  if (sha(candidate) !== row.markdown_sha256) throw new Error(`Cannot acknowledge ${id}: candidate differs from its recorded hash.`);
  const converted = await renderSavedMarkdown(source, row, raw);
  if (sha(Buffer.from(converted.markdown, 'utf8')) !== row.markdown_sha256) throw new Error(`Cannot acknowledge ${id}: candidate does not match an offline replay of the saved official source.`);
  const target = path.join(DOCUMENTS, 'guidance', `${safe(id)}.md`), bytes = candidate;
  await atomic(target, bytes);
  const manifestItem = manifest.documents.find(item => item.id === id);
  manifestItem.accepted = true;
  manifestItem.document_path = path.posix.join('documents', 'guidance', `${safe(id)}.md`);
  await atomic(MANIFEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`);
  state.sources[id] = { ...(state.sources[id] || {}), accepted_document_path: manifestItem.document_path, accepted_markdown_sha256: sha(bytes), accepted_at: now() };
  await atomic(STATE_PATH, `${JSON.stringify(state, null, 2)}\n`);
  console.log(JSON.stringify({ accepted: id, path: target, sha256: sha(bytes) }, null, 2));
} else if (mode === '--verify') {
  const failures = [];
  for (const [id, row] of Object.entries(state.sources)) {
    if (!row.raw_path || (!row.candidate_path && !row.accepted_document_path)) continue;
    try {
      const source = manifest.documents.find(item => item.id === id);
      const raw = await readFile(workFile(row.raw_path, 'raw'));
      if (!source) throw new Error('source ID is missing from the current manifest');
      if (sha(raw) !== row.source_bytes_sha256) throw new Error('saved source-byte hash mismatch');
      const converted = await renderSavedMarkdown(source, row, raw);
      if (sha(Buffer.from(converted.markdown, 'utf8')) !== row.markdown_sha256) throw new Error('offline conversion replay hash mismatch');
      let candidate;
      if (row.candidate_path) {
        try { candidate = await readFile(workFile(row.candidate_path, 'candidates')); }
        catch (error) { if (error.code !== 'ENOENT') throw error; }
      }
      if (candidate && sha(candidate) !== row.markdown_sha256) throw new Error('saved review candidate hash mismatch');
      if (row.accepted_markdown_sha256) {
        const acceptedPath = row.accepted_document_path ? path.resolve(ROOT, ...row.accepted_document_path.split('/')) : path.join(DOCUMENTS, 'guidance', `${safe(id)}.md`);
        const accepted = await readFile(acceptedPath);
        if (sha(accepted) !== row.accepted_markdown_sha256) throw new Error('saved accepted-copy hash mismatch');
        if (!candidate && row.accepted_from_conversion_sha256 !== row.markdown_sha256) throw new Error('accepted copy has no candidate and lacks its conversion provenance hash');
      } else if (!candidate) {
        throw new Error('no review candidate or accepted document is available');
      }
    } catch (error) { failures.push({ source_id: id, error: error.message }); }
  }
  console.log(JSON.stringify({ verified: Object.keys(state.sources).length - failures.length, failure_count: failures.length, failures }, null, 2));
  if (failures.length) process.exitCode = 1;
} else if (mode === '--reconvert') {
  const checkedAt = now(), observations = [], failures = [];
  for (const [id, row] of Object.entries(state.sources)) {
    if (!row.raw_path || !row.candidate_path) continue;
    try {
      const source = manifest.documents.find(item => item.id === id);
      if (!source) throw new Error('source ID is missing from the current manifest');
      if (source.monitor_only) throw new Error('monitor-only sources cannot produce converted candidates');
      const raw = await readFile(workFile(row.raw_path, 'raw'));
      if (sha(raw) !== row.source_bytes_sha256) throw new Error('saved source-byte hash mismatch');
      let previousCandidate;
      try { previousCandidate = await readFile(workFile(row.candidate_path, 'candidates')); }
      catch (error) { if (error.code !== 'ENOENT') throw error; }
      if (previousCandidate && sha(previousCandidate) !== row.markdown_sha256) throw new Error('saved candidate differs from its recorded hash; refusing to overwrite a manual edit');
      const converted = await renderSavedMarkdown(source, row, raw);
      const markdownBytes = Buffer.from(converted.markdown, 'utf8'), markdownHash = sha(markdownBytes);
      const changed = markdownHash !== row.markdown_sha256 || !previousCandidate;
      if (changed) await atomic(workFile(row.candidate_path, 'candidates'), markdownBytes);
      state.sources[id] = { ...row, markdown_sha256: markdownHash, extractor: converted.method, ...(changed ? { reconverted_at: checkedAt } : {}) };
      observations.push({ source_id: id, status: changed ? 'candidate_reconverted_for_review' : 'candidate_unchanged', source_bytes_sha256: row.source_bytes_sha256, previous_markdown_sha256: row.markdown_sha256, markdown_sha256: markdownHash, candidate_path: row.candidate_path });
    } catch (error) { failures.push({ source_id: id, error: errorDetails(error) }); }
  }
  const report = { report_version: 2, pack: manifest.pack, pack_version: VERSION, mode, checked_at: checkedAt, source_count: observations.length + failures.length, reconverted_count: observations.filter(item => item.status === 'candidate_reconverted_for_review').length, unchanged_count: observations.filter(item => item.status === 'candidate_unchanged').length, failure_count: failures.length, observations, failures, note: 'Reconversion used saved official source bytes, did not make network requests, and did not accept or promote any candidate.' };
  await atomic(STATE_PATH, `${JSON.stringify(state, null, 2)}\n`);
  await atomic(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report, null, 2));
  if (failures.length) process.exitCode = 1;
} else {
  const checkedAt = now(), asOfDate = checkedAt.slice(0, 10), observations = [], failures = [], blocked = [], monitorOnly = [];
  const legislation = manifest.documents.filter(item => !item.monitor_only && (item.source_type === 'national_legislation' || item.source_type === 'constitutional_text'));
  const guidance = manifest.documents.filter(item => !item.monitor_only && item.source_type !== 'national_legislation' && item.source_type !== 'constitutional_text');
  for (const source of manifest.documents) {
    if (source.monitor_only) { monitorOnly.push({ source_id: source.id, status: 'discovery_channel_not_fetched' }); continue; }
  }
  const queue = [...guidance.map(source => ({ source, lane: 'guidance' })), ...legislation.map(source => ({ source, lane: 'stable_url_pdf' }))]; let cursor = 0;
  async function worker() {
    while (cursor < queue.length) {
      const task = queue[cursor++], { source, lane } = task;
      try {
        const response = lane === 'stable_url_pdf'
          ? await fetchPublicAct(source, manifest.official_hosts || [], asOfDate)
          : await fetchOfficial(source.url, manifest.official_hosts || [], 'html');
        const html = lane === 'guidance' ? decodeHtml(response.bytes, response.content_type) : '';
        const extracted = lane === 'guidance' ? sourceBody(html) : null;
        const converted = lane === 'stable_url_pdf'
          ? makeActMarkdown(source, response, asOfDate, response.content)
          : makeMarkdown({ ...source, retrieved_url: response.final_url }, html, extracted.html, extracted.method);
        const sourceHash = sha(response.bytes), markdownBytes = Buffer.from(converted.markdown, 'utf8'), markdownHash = sha(markdownBytes);
        const previous = state.sources[source.id] || {}, sourceUnchanged = previous.source_bytes_sha256 === sourceHash, markdownUnchanged = previous.markdown_sha256 === markdownHash;
        const status = sourceUnchanged && markdownUnchanged ? 'unchanged' : !sourceUnchanged && markdownUnchanged ? 'source_changed_markdown_unchanged' : 'candidate_ready';
        const rawPath = path.posix.join('work', 'raw', safe(source.id), `${sourceHash}.${response.format}`);
        const candidatePath = previous.candidate_path || candidateRelativePath(source);
        if (mode === '--sync') {
          let candidateBytes;
          try { candidateBytes = await readFile(workFile(candidatePath, 'candidates')); }
          catch (error) { if (error.code !== 'ENOENT') throw error; }
          if (candidateBytes && !previous.markdown_sha256) throw new Error(`Untracked candidate exists for ${source.id}; refusing to overwrite it.`);
          if (candidateBytes && sha(candidateBytes) !== previous.markdown_sha256) throw new Error(`Candidate was manually changed for ${source.id}; refusing to overwrite it.`);
          let acceptedCopyUnchanged = false;
          if (!candidateBytes && markdownUnchanged && previous.accepted_document_path && previous.accepted_from_conversion_sha256 === markdownHash && previous.accepted_markdown_sha256) {
            const acceptedPath = path.resolve(ROOT, ...previous.accepted_document_path.split('/'));
            try { acceptedCopyUnchanged = sha(await readFile(acceptedPath)) === previous.accepted_markdown_sha256; }
            catch (error) { if (error.code !== 'ENOENT') throw error; }
          }
          const candidateNeedsWrite = (!candidateBytes && !acceptedCopyUnchanged) || !markdownUnchanged;
          await atomic(workFile(rawPath, 'raw'), response.bytes);
          if (candidateNeedsWrite) await atomic(workFile(candidatePath, 'candidates'), markdownBytes);
          state.sources[source.id] = { source_bytes_sha256: sourceHash, markdown_sha256: markdownHash, raw_path: rawPath, format: response.format, candidate_path: candidatePath, checked_at: checkedAt, ...(response.retrieval_as_of ? { retrieval_as_of: response.retrieval_as_of } : {}), final_url: response.final_url, content_type: response.content_type, etag: response.etag, last_modified: response.last_modified, extractor: converted.method, ...(previous.accepted_document_path ? { accepted_document_path: previous.accepted_document_path, accepted_markdown_sha256: previous.accepted_markdown_sha256, accepted_from_conversion_sha256: previous.accepted_from_conversion_sha256, accepted_at: previous.accepted_at } : {}) };
        }
        observations.push({ source_id: source.id, status, lane, official_url: source.url, ...(response.download_url ? { download_url: response.download_url, consolidation_date_requested: response.retrieval_as_of } : {}), final_url: response.final_url, content_type: response.content_type, format: response.format, language: source.language, source_bytes_sha256: sourceHash, markdown_sha256: markdownHash, source_bytes: response.bytes.length, markdown_characters: converted.markdown.length, extraction: converted.method });
      } catch (error) {
        if (lane === 'stable_url_pdf') blocked.push({ source_id: source.id, status: 'stable_url_pdf_unavailable_or_unverified', official_url: source.url, attempted_download_url: (() => { try { return stableDownloadUrl(source, asOfDate); } catch { return null; } })(), consolidation_date_requested: asOfDate, note: errorDetails(error) });
        else failures.push({ source_id: source.id, official_url: source.url, error: errorDetails(error) });
      }
    }
  }
  await Promise.all([worker(), worker()]);
  const report = { report_version: 2, pack: manifest.pack, pack_version: VERSION, mode, checked_at: checkedAt, source_record_count: manifest.source_record_count, pending_review_artifact_count: manifest.pending_review_artifact_count, guidance_target_count: guidance.length, stable_url_pdf_target_count: legislation.length, retrieved_count: observations.length, failed_count: failures.length, blocked_law_count: blocked.length, monitor_only_target_count: monitorOnly.length, observations, blocked, monitor_only: monitorOnly, failures, actions: ['Review source identity, consolidation date, and temporary Markdown conversions; the acknowledgement action remains limited to guidance records.', 'Legislation uses the public e-Sbírka stable download URL with the check date and PDF format; the route is keyless and is not an API.', 'A successful retrieval or conversion does not establish currentness, legal force, completeness, or applicability.'] };
  if (mode === '--sync') {
    await atomic(STATE_PATH, `${JSON.stringify(state, null, 2)}\n`);
    await atomic(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`);
  }
  const summary = { mode, guidance_targets: guidance.length, stable_url_pdf_targets: legislation.length, retrieved: observations.length, failed: failures.length, law_targets_blocked: blocked.length, monitor_only: monitorOnly.length, report: REPORT_PATH };
  console.log(JSON.stringify(mode === '--check' ? { ...report, read_only: true } : summary, null, 2));
  if (failures.length) process.exitCode = 1;
}
