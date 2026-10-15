#!/usr/bin/env node
// Retrieve and convert the Czechia official guidance lane. Czech statute text
// requires a registered e-Sbírka API key and is reported separately as blocked.
import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, copyFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { atomicProjectWrite } from '../../../runtime-storage.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WORK = path.join(ROOT, 'work');
const RAW = path.join(WORK, 'raw');
const CANDIDATES = path.join(WORK, 'candidates');
const ACCEPTED = path.join(ROOT, 'accepted');
const MANIFEST_PATH = path.join(ROOT, 'references', 'candidate-manifest.json');
const STATE_PATH = path.join(WORK, 'state.json');
const REPORT_PATH = path.join(WORK, 'latest-report.json');
const VERSION = '0.1.0';
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
function decodeEntities(value) {
  return String(value).replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos|nbsp|ndash|mdash|rsquo|lsquo|rdquo|ldquo|sect|copy|hellip|acute|bdquo|bull);/gi, (whole, entity) => {
    if (entity[0] === '#') {
      const number = entity[1].toLowerCase() === 'x' ? parseInt(entity.slice(2), 16) : Number(entity.slice(1));
      return Number.isInteger(number) && number > 0 && number <= 0x10ffff ? String.fromCodePoint(number) : whole;
    }
    return ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', ndash: '–', mdash: '—', rsquo: '’', lsquo: '‘', rdquo: '”', ldquo: '“', sect: '§', copy: '©', hellip: '…', acute: '´', bdquo: '„', bull: '•' })[entity.toLowerCase()] || whole;
  });
}
function attr(tag, key) { return tag.match(new RegExp(`\\b${key}\\s*=\\s*(["'])(.*?)\\1`, 'i'))?.[2] || ''; }
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
function convertHtml(fragment) {
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
      stack.push({ name, skip });
      if (skip) continue;
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
      if (name === 'li' || blocks.has(name)) boundary();
    }
  }
  return out.replace(/[\t\u00a0 ]+\n/g, '\n').replace(/\n[\t ]+/g, '\n').replace(/\n{3,}/g, '\n\n').replace(/[ \t]{2,}/g, ' ').replace(/^#{1,6}(?:\s*#+)?\s*$/gm, '').replace(/^#{1,6} \*+$/gm, '').replace(/\n{3,}/g, '\n\n').trim();
}
function pageTitle(html, fallback) {
  const value = html.match(/<title\b[^>]*>([\s\S]*?)<\/title\s*>/i)?.[1] || html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1\s*>/i)?.[1] || fallback;
  return convertHtml(value).replace(/\s*[|–-]\s*(?:Ministry|Portal|Government).*$/i, '').trim() || fallback;
}
async function fetchOfficial(url, hosts) {
  let current = url;
  for (let redirect = 0; redirect <= 5; redirect++) {
    const parsed = new URL(current);
    if (parsed.protocol !== 'https:' || !hosts.includes(parsed.hostname)) throw new Error(`Refused non-allowlisted URL or redirect: ${current}`);
    const response = await fetch(current, { redirect: 'manual', headers: { accept: 'text/html,application/xhtml+xml', 'user-agent': `czechia-source-library/${VERSION}` } });
    if ([301, 302, 303, 307, 308].includes(response.status)) {
      const location = response.headers.get('location');
      if (!location) throw new Error(`Redirect without Location from ${current}`);
      current = new URL(location, current).href;
      continue;
    }
    if (!response.ok) throw new Error(`HTTP ${response.status} from ${current}`);
    const contentType = response.headers.get('content-type') || '';
    if (!/text\/html|application\/xhtml\+xml/i.test(contentType)) throw new Error(`Unexpected content type ${contentType || '(missing)'} from ${current}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    if (bytes.length < 500) throw new Error(`Source response was too short (${bytes.length} bytes) from ${current}`);
    return { bytes, final_url: current, content_type: contentType, etag: response.headers.get('etag'), last_modified: response.headers.get('last-modified') };
  }
  throw new Error(`Too many redirects from ${url}`);
}
function makeMarkdown(source, html, body, method) {
  const title = pageTitle(html, source.title), content = convertHtml(body);
  if (content.length < 200) throw new Error(`Converted main content is too short for ${source.id} (${content.length} characters).`);
  return {
    title,
    method,
    markdown: `# ${source.title}\n\n- Source ID: \`${source.id}\`\n- Source type: \`${source.source_type}\`\n- Content language: \`${source.language}\`\n- Official page title: ${title}\n- Official URL: ${source.url}\n- Conversion: Czechia official HTML to Markdown ${VERSION}\n- Coverage: page content extracted from ${method}; site chrome and linked attachments are excluded.\n\n> Review candidate from the official source. Conversion does not independently establish legal force, currentness, or completeness.\n\n${content}\n`
  };
}

const manifest = await readFile(MANIFEST_PATH, 'utf8').then(JSON.parse);
const state = await json(STATE_PATH, { version: 1, sources: {} });
const mode = process.argv.find(arg => ['--check', '--sync', '--verify', '--ack'].includes(arg)) || '--check';
if (mode === '--ack') {
  const id = process.argv[process.argv.indexOf('--ack') + 1];
  const source = manifest.documents.find(item => item.id === id);
  if (!source || source.monitor_only || source.source_type === 'national_legislation') throw new Error('--ack requires a retrieved official guidance candidate ID.');
  const candidate = path.join(CANDIDATES, `${safe(id)}.md`), target = path.join(ACCEPTED, `${safe(id)}.md`);
  const bytes = await readFile(candidate);
  await atomic(target, bytes);
  state.sources[id] = { ...(state.sources[id] || {}), accepted_markdown_sha256: sha(bytes), accepted_at: now() };
  await atomic(STATE_PATH, `${JSON.stringify(state, null, 2)}\n`);
  console.log(JSON.stringify({ accepted: id, path: target, sha256: sha(bytes) }, null, 2));
} else if (mode === '--verify') {
  const failures = [];
  for (const [id, row] of Object.entries(state.sources)) {
    if (!row.raw_path || !row.candidate_path) continue;
    try {
      const source = manifest.documents.find(item => item.id === id);
      const raw = await readFile(path.join(ROOT, row.raw_path));
      const candidate = await readFile(path.join(ROOT, row.candidate_path));
      if (sha(raw) !== row.source_bytes_sha256) throw new Error('saved source-byte hash mismatch');
      const html = raw.toString('utf8'), extracted = sourceBody(html), converted = makeMarkdown(source, html, extracted.html, extracted.method).markdown;
      if (sha(Buffer.from(converted, 'utf8')) !== row.markdown_sha256 || sha(candidate) !== row.markdown_sha256) throw new Error('offline conversion replay or candidate hash mismatch');
    } catch (error) { failures.push({ source_id: id, error: error.message }); }
  }
  console.log(JSON.stringify({ verified: Object.keys(state.sources).length - failures.length, failure_count: failures.length, failures }, null, 2));
  if (failures.length) process.exitCode = 1;
} else {
  const checkedAt = now(), observations = [], failures = [], blocked = [], monitorOnly = [];
  const guidance = manifest.documents.filter(item => !item.monitor_only && item.source_type !== 'national_legislation' && item.source_type !== 'constitutional_text');
  for (const source of manifest.documents) {
    if (source.monitor_only) { monitorOnly.push({ source_id: source.id, status: 'discovery_channel_not_fetched' }); continue; }
    if (source.source_type === 'national_legislation' || source.source_type === 'constitutional_text') {
      blocked.push({ source_id: source.id, status: 'blocked_api_registration', note: 'e-Sbírka legal text retrieval requires an issued API key; the REST endpoint returned 401 without one.' });
    }
  }
  const queue = [...guidance]; let cursor = 0;
  async function worker() {
    while (cursor < queue.length) {
      const source = queue[cursor++];
      try {
        const response = await fetchOfficial(source.url, manifest.official_hosts || []);
        const html = response.bytes.toString('utf8'), extracted = sourceBody(html), converted = makeMarkdown(source, html, extracted.html, extracted.method);
        const sourceHash = sha(response.bytes), markdownBytes = Buffer.from(converted.markdown, 'utf8'), markdownHash = sha(markdownBytes);
        const previous = state.sources[source.id] || {}, sourceUnchanged = previous.source_bytes_sha256 === sourceHash, markdownUnchanged = previous.markdown_sha256 === markdownHash;
        const status = sourceUnchanged && markdownUnchanged ? 'unchanged' : !sourceUnchanged && markdownUnchanged ? 'source_changed_markdown_unchanged' : 'candidate_ready';
        const rawPath = path.join('work', 'raw', safe(source.id), `${sourceHash}.html`);
        const candidatePath = path.join('work', 'candidates', `${safe(source.id)}.md`);
        if (mode === '--sync') {
          await atomic(path.join(ROOT, rawPath), response.bytes);
          if (!markdownUnchanged) await atomic(path.join(ROOT, candidatePath), markdownBytes);
          state.sources[source.id] = { source_bytes_sha256: sourceHash, markdown_sha256: markdownHash, raw_path: rawPath, candidate_path: candidatePath, checked_at: checkedAt, final_url: response.final_url, content_type: response.content_type, etag: response.etag, last_modified: response.last_modified, extractor: converted.method, ...(previous.accepted_markdown_sha256 ? { accepted_markdown_sha256: previous.accepted_markdown_sha256, accepted_at: previous.accepted_at } : {}) };
        }
        observations.push({ source_id: source.id, status, official_url: source.url, final_url: response.final_url, language: source.language, source_bytes_sha256: sourceHash, markdown_sha256: markdownHash, source_bytes: response.bytes.length, markdown_characters: converted.markdown.length, extraction: converted.method });
      } catch (error) { failures.push({ source_id: source.id, official_url: source.url, error: error.message }); }
    }
  }
  await Promise.all([worker(), worker()]);
  const report = { report_version: 1, pack: manifest.pack, pack_version: VERSION, mode, checked_at: checkedAt, candidate_source_count: manifest.candidate_source_count, guidance_target_count: guidance.length, retrieved_count: observations.length, failed_count: failures.length, blocked_law_count: blocked.length, monitor_only_target_count: monitorOnly.length, observations, blocked, monitor_only: monitorOnly, failures, actions: ['Review source identity and candidate Markdown before acknowledgement.', 'National legislation remains blocked until e-Sbírka API registration is available.', 'A successful retrieval or conversion does not establish currentness or completeness.'] };
  if (mode === '--sync') {
    await atomic(STATE_PATH, `${JSON.stringify(state, null, 2)}\n`);
    await atomic(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`);
  }
  console.log(JSON.stringify({ mode, guidance_targets: guidance.length, retrieved: observations.length, failed: failures.length, law_targets_blocked: blocked.length, monitor_only: monitorOnly.length, report: REPORT_PATH }, null, 2));
  if (failures.length) process.exitCode = 1;
}
