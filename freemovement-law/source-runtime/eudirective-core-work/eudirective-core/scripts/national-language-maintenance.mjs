#!/usr/bin/env node
// Retrieve official national-language counterparts of the English core library.
// Output remains a derived candidate library; this never edits the trusted manifest.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { htmlText } from './source-maintenance.mjs';
import { atomicProjectWrite, projectTempPath } from '../../../runtime-storage.mjs';

const SKILL_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sha = value => createHash('sha256').update(value).digest('hex');
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const safe = value => value.replace(/[^A-Za-z0-9._-]+/g, '_');
const LANGUAGE_PROFILES = {
  HU: { name:'Hungarian', subdir:'hungary/core', words:`a az és hogy nem is egy vagy valamint illetve szerint alapján esetében által közötti között tekintettel figyelembe véve cikk cikke cikkének bekezdés pont rendelet irányelv határozat európai parlament tanács bizottság tagállam tagállamok államok jog jogosult köteles jogok hatály alkalmazandó alkalmazni vízum vízumkérelem kérelmező kérelem területén tartózkodás szabad mozgás családtag állampolgár közösség részére ezen e rendeletben irányelvben céljából feltéve hogy amennyiben továbbá azonban minden valamennyi szükséges kell lehet kellő megfelelő tekintetben értelmében összhangban alapján rendelkezéseinek rendelkezéseit unió európai unió hivatalos lapja magyarország magyar` },
  SV: { name:'Swedish', subdir:'sweden/core', words:`och att det den de som för av är till med på inte ska kan får enligt eller om rätt unionsmedborgare uppehållsrätt uppehållstillstånd tredjelandsmedborgare familjemedlem medlemsstat direktiv förordning domstolen artikel ansökan beslut myndighet arbetstagare arbete anställd socialt bistånd likabehandling omfattas bevilja villkor förevarande mål fastställa bestämmelser rättigheter grundläggande unionsrätt europeiska unionen officiella tidning överklagande klagomål vistelse bosatt fri rörlighet familj medborgare sökande prövning domstol rättslig hänsyn tillämplig medlemsstaterna` },
  DA: { name:'Danish', subdir:'denmark/core', words:`og at det den de som for af er til med på ikke skal kan må ifølge eller om ret unionsborger opholdsret opholdstilladelse tredjelandsstatsborger familiemedlem medlemsstat direktiv forordning domstolen artikel ansøgning afgørelse myndighed arbejdstager arbejde lønmodtager social bistand ligebehandling omfattet bevilge vilkår foreliggende sag fastslå bestemmelser rettigheder grundlæggende unionsret europæiske union officielle tidende klage ophold bosat fri bevægelighed familie statsborger ansøger prøvelse domstol retlig hensyn gældende medlemsstaterne` },
  RO: { name:'Romanian', subdir:'romania/core', words:`și să în în care de la cu pentru este sunt drept cetățean cetățeni stat statelor membru membru directivă regulament decizie cerere solicitant viză ședere reședință permis libera circulație familie familiei muncă lucrător salariat curtea instanța hotărâre drepturi fundamentale dispoziții aplicare aplicabil autorități administrație europeană uniunii oficială jurnal articol alineat cauză cauza acțiune pronunță judecată discriminare proporționalitate condiții condițiile teritoriu resortisant resortisanți străin străini protecție procedură procedura autoritate autorităților obligație obligații poate trebuie acordă acordarea persoană persoane statului statele prezenta prezentei prevederile legislația legislației dreptul dreptului europeană european cetățenie căsătorie soț soție familie cerințe exercitare refuz justificare motivare contestare administrativ comisie parlament consiliu libertate` },
};
const EN_WORDS = new Set(`the and of to in that shall may this for with article court judgment member state states person applicant visa application regulation directive commission council parliament rights residence family free movement shall be is are by from on as`.split(' '));
const OMBUDSMAN_BLOCKS = [
  ['home','how-to-make-a-complaint','can-the-ombudsman-help-me'],
  ['home','how-to-make-a-complaint','how-can-the-european-ombudsman-help'],
  ['home','how-to-make-a-complaint','what-is-maladministration'],
  ['home','how-to-make-a-complaint','what-the-european-ombudsman-cannot-do'],
  ['home','how-to-make-a-complaint','submit-a-complaint'],
  ['home','how-to-make-a-complaint','submit-a-complaint-2'],
  ['checklist-for-making-a-complaint','how-to-make-a-complaint','home'],
];
const languageStats = (text, language) => {
  const words = text.toLowerCase().match(/[a-záéíóöőúüűåäæøăâîșşțţ]+/g) || [];
  const markers = new Set(LANGUAGE_PROFILES[language].words.split(' '));
  const languageHits = words.filter(word => markers.has(word)).length;
  const en = words.filter(word => EN_WORDS.has(word)).length;
  return { word_count: words.length, language_hits: languageHits, en_hits: en, language_ratio: words.length ? languageHits / words.length : 0 };
};
const isTargetLanguage = (text, language) => {
  const stats = languageStats(text, language);
  return stats.word_count >= 150 && stats.language_hits >= 22 && stats.language_hits > stats.en_hits * 1.25 && stats.language_ratio >= 0.025;
};
function sourceType(row) {
  if (row.source_id === 'eu:12012p') return 'charter';
  if (row.source_id.startsWith('eu:commission-eu-law-complaint')) return 'commission_operational_guidance_page';
  if (row.source_id.startsWith('eu:ombudsman-complaint')) return 'ombudsman_operational_guidance_page';
  if (row.source_id === 'eu:visa-code-handbook-i-2024') return 'commission_handbook';
  if (/^eu:6\d{4}cj/.test(row.source_id)) return 'cjeu_judgment';
  if (row.source_id === 'eu:c-2023-1392') return 'commission_notice';
  if (row.source_id === 'eu:52014sc0284') return 'commission_staff_working_document';
  if (/^eu:3\d{4}l/.test(row.source_id)) return 'directive_consolidated';
  if (/^eu:3\d{4}r/.test(row.source_id)) return 'regulation_consolidated';
  if (row.source_id === 'eu:32013h0461') return 'commission_recommendation';
  throw new Error(`Unmapped source type: ${row.source_id}`);
}
function candidateUrl(row, lang) {
  const original = row.retrieved_url || row.official_source;
  const url = new URL(original);
  if (url.hostname.toLowerCase() === 'eur-lex.europa.eu') {
    url.pathname = url.pathname.replace(/\/legal-content\/[A-Z]{2}\//i, `/legal-content/${lang}/`);
    return { url: url.href, mode: 'eurlex-language-path' };
  }
  if (row.source_id === 'eu:commission-eu-law-complaint') {
    url.pathname = url.pathname.replace(/_en$/i, `_${lang.toLowerCase()}`);
    return { url: url.href, mode: 'official-localized-path-candidate' };
  }
  if (row.source_id === 'eu:ombudsman-complaint') {
    url.pathname = url.pathname.replace(/^\/en\//i, `/${lang.toLowerCase()}/`);
    return { url: url.href, mode: 'official-localized-path-candidate' };
  }
  if (row.source_id === 'eu:visa-code-handbook-i-2024') {
    url.pathname = url.pathname.replace(/_en(?=\.|$)/i, `_${lang.toLowerCase()}`);
    return { url: url.href, mode: 'official-localized-file-candidate' };
  }
  return null;
}
function normalizeIdentity(value) { return value.replace(/&amp;/gi, '&').toUpperCase().replace(/[^A-Z0-9]/g, ''); }
function validateEurlexIdentity(row, url, html) {
  const uri = new URL(url).searchParams.get('uri') || '';
  const requested = uri.replace(/^CELEX:/i, '');
  const expected = requested.split('/')[0];
  const content = normalizeIdentity(html);
  if (content.includes(normalizeIdentity(expected))) return;
  const actualCanonical = html.match(/<link\b[^>]*rel\s*=\s*(["'])canonical\1[^>]*>/i)?.[0]?.match(/\bhref\s*=\s*(["'])(.*?)\1/i)?.[2] || '';
  const expectedCanonical = row.canonical_eli_url || row.canonical_document_url || '';
  if (actualCanonical && expectedCanonical) {
    const actualPath = new URL(actualCanonical, url).pathname.replace(/\/(?:eng|hun|swe|dan)$/i, '');
    const expectedPath = new URL(expectedCanonical).pathname.replace(/\/(?:eng|hun|swe|dan)$/i, '');
    if (actualPath.toLowerCase() === expectedPath.toLowerCase()) return;
  }
  const consolidated = expected.match(/^0?(3\d{4})([LR])(\d+)-(\d{4})(\d{2})(\d{2})$/i);
  if (consolidated) {
    const [, year, letter, number, yyyy, mm, dd] = consolidated;
    const segment = letter.toUpperCase() === 'L' ? 'dir' : 'reg';
    const date = `${yyyy}-${mm}-${dd}`;
    const expectedPath = `/eli/${segment}/${Number(year)}/${Number(number)}/${date}/`;
    const base = expected.replace(/-\d{8}$/, '');
    if (content.includes(normalizeIdentity(base)) && actualCanonical && new URL(actualCanonical, url).pathname.toLowerCase().startsWith(expectedPath)) return;
  }
  if (row.source_id === 'eu:12012p' && content.includes('12012P') && content.includes('CHARTER')) return;
  const caseId = row.source_id.match(/^eu:6(\d{4})cj(\d{4})$/i);
  if (caseId) {
    const year = caseId[1].slice(-2), number = String(Number(caseId[2]));
    if (content.includes(normalizeIdentity(`C-${number}/${year}`)) || content.includes(normalizeIdentity(`Case ${number}-${year}`)) || content.includes(normalizeIdentity(`${number}/${year}`))) return;
  }
  throw new Error('EUR-Lex response does not expose the requested document identity/version');
}
function decodeEntities(text) {
  const named = { amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' ',ndash:'–',mdash:'—',rsquo:'’',lsquo:'‘',rdquo:'”',ldquo:'“',laquo:'«',raquo:'»',euro:'€',deg:'°' };
  return text.replace(/&(#x[0-9a-f]+|#\d+|[a-z][a-z0-9]+);/gi, (whole, key) => {
    if (key[0] === '#') { const n = key[1].toLowerCase() === 'x' ? Number.parseInt(key.slice(2), 16) : Number(key.slice(1)); return Number.isInteger(n) && n > 0 && n <= 0x10ffff ? String.fromCodePoint(n) : whole; }
    return named[key] ?? named[key.toLowerCase()] ?? whole;
  });
}
function plainTextFragment(fragment) {
  return decodeEntities(fragment.replace(/<!--[\s\S]*?-->/g, '').replace(/<(script|style|svg|noscript|button|form)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, '').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
}
function commissionPageText(html) {
  const mainStart = html.search(/<main\b(?=[^>]*\bid\s*=\s*["']main-content["'])[^>]*>/i);
  if (mainStart < 0) throw new Error('Localized Commission page lacks main#main-content');
  const mainEnd = html.indexOf('</main>', mainStart);
  if (mainEnd < 0) throw new Error('Hungarian Commission page main element is incomplete');
  const main = html.slice(mainStart, mainEnd + 7);
  const parts = [];
  const matcher = /<(h[1-6]|p|li|blockquote)\b[^>]*>([\s\S]*?)<\/\1\s*>/gi;
  for (const match of main.matchAll(matcher)) { const text = plainTextFragment(match[2]); if (text && !parts.includes(text)) parts.push(`${match[1][0] === 'h' ? '# ' : '- '}${text}`); }
  return parts.join('\n\n');
}
function parseArgs(args) {
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--language' || args[i] === '--library' || args[i] === '--ack') opts[args[i].slice(2)] = args[++i];
    else if (args[i] === '--help') opts.help = true;
    else throw new Error(`Unknown argument ${args[i]}`);
  }
  return opts;
}
const OFFICIAL_HOSTS = new Set(['eur-lex.europa.eu', 'commission.europa.eu', 'home-affairs.ec.europa.eu', 'www.ombudsman.europa.eu']);
function validateRequestUrl(value) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || !OFFICIAL_HOSTS.has(url.hostname.toLowerCase()) || url.username || url.password)
    throw new Error(`Request URL is outside registered official HTTPS hosts: ${url.href}`);
  return url;
}
async function request(value) {
  let url = validateRequestUrl(value);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 45000);
  try {
    for (let hop = 0; hop <= 5; hop++) {
      const response = await fetch(url, { redirect: 'manual', signal: controller.signal, headers: { 'user-agent': 'eudirective-core-national-source-check/1.0', accept: 'text/html,application/xhtml+xml,application/pdf,*/*;q=0.5' } });
      if ([301, 302, 303, 307, 308].includes(response.status)) {
        if (hop === 5) throw new Error('Official source exceeded the five-redirect limit');
        const location = response.headers.get('location');
        if (!location) throw new Error(`Redirect from ${url.href} lacks a Location header`);
        url = validateRequestUrl(new URL(location, url).href);
        continue;
      }
      const bytes = Buffer.from(await response.arrayBuffer());
      return { response, bytes, finalUrl: url.href, contentType: response.headers.get('content-type') || '' };
    }
    throw new Error('Official source redirect limit exceeded');
  } finally { clearTimeout(timeout); }
}
async function extractPdf(bytes) {
  const { getDocument } = await import('pdfjs-dist/legacy/build/pdf.mjs');
  const doc = await getDocument({ data: new Uint8Array(bytes), useSystemFonts: true, isEvalSupported: false }).promise;
  const pages = [];
  for (let n = 1; n <= doc.numPages; n++) {
    const page = await doc.getPage(n), content = await page.getTextContent({ includeMarkedContent: false });
    pages.push(content.items.filter(item => 'str' in item).map(item => item.str).join(' '));
  }
  return pages.join('\n\n---\n\n').replace(/\s+/g, ' ').trim();
}
async function atomicJson(file, value) {
  await atomicProjectWrite(file, `${JSON.stringify(value, null, 2)}\n`);
}
function within(root, relative) {
  const full = path.resolve(root, relative);
  if (full !== root && !full.startsWith(`${root}${path.sep}`)) throw new Error(`Unsafe library-relative path: ${relative}`);
  return full;
}
async function existingContentHash(library, relative) {
  try {
    const markdown = await readFile(within(library, relative), 'utf8');
    const marker = 'before relying on this conversion.\n\n';
    const at = markdown.indexOf(marker);
    return at < 0 ? null : sha(markdown.slice(at + marker.length).trim());
  } catch { return null; }
}
async function acknowledge(library, language, sourceId) {
  const stateFile = path.join(library, `national-language-state-${language}.json`);
  const state = JSON.parse(await readFile(stateFile, 'utf8'));
  const record = state.sources?.[sourceId];
  if (!record?.pending) throw new Error(`No pending ${language} update for ${sourceId}`);
  const staged = projectTempPath(within(library, record.pending.path));
  const current = within(library, record.current_path);
  const bytes = await readFile(staged);
  if (sha(bytes) !== record.pending.markdown_sha256) throw new Error(`Pending Markdown hash mismatch for ${sourceId}`);
  await atomicProjectWrite(current, bytes);
  record.accepted_official_response_sha256 = record.pending.official_response_sha256;
  record.accepted_content_sha256 = record.pending.source_content_sha256;
  record.accepted_markdown_sha256 = record.pending.markdown_sha256;
  delete record.pending;
  record.acknowledged_at = now();
  await atomicJson(stateFile, state);
  const indexFile = path.join(library, `national-language-index-${language}.json`);
  try {
    const index = JSON.parse(await readFile(indexFile, 'utf8'));
    const row = index.entries.find(entry => entry.source_id === sourceId);
    if (row) { row.status = 'retrieved_and_converted_candidate'; row.library_relative_path = record.current_path; delete row.pending_path; }
    index.pending_update_count = index.entries.filter(entry => entry.status === 'official_content_changed_pending_review').length;
    index.retrieved_and_converted_count = index.entries.filter(entry => entry.status === 'retrieved_and_converted_candidate').length;
    index.checked_at = now();
    await atomicJson(indexFile, index);
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  console.log(JSON.stringify({ language, source_id: sourceId, acknowledged: true, current_path: record.current_path }, null, 2));
}
async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log('node scripts/national-language-maintenance.mjs --language HU|SV|DA|RO --library <derived-library-directory>\nnode scripts/national-language-maintenance.mjs --language HU|SV|DA|RO --ack <source-id> --library <derived-library-directory>');
    return;
  }
  const language = String(opts.language || '').toUpperCase();
  if (!LANGUAGE_PROFILES[language]) throw new Error('Supported languages are HU, SV, DA and RO.');
  if (!opts.library) throw new Error('--library is required');
  const library = path.resolve(opts.library);
  if (process.argv.includes('--ack') && !opts.ack) throw new Error('--ack requires a source ID');
  if (opts.ack) return acknowledge(library, language, opts.ack);
  const englishRows = JSON.parse(await readFile(path.join(library, 'retrieval-index.json'), 'utf8')).filter(row => String(row.language).toUpperCase() === 'EN' && row.library_relative_path.startsWith('core/'));
  if (!englishRows.length) throw new Error('No English core records found in retrieval-index.json');
  const indexPath = path.join(library, `national-language-index-${language}.json`);
  const statePath = path.join(library, `national-language-state-${language}.json`);
  let previousIndex = null, state = null;
  try { previousIndex = JSON.parse(await readFile(indexPath, 'utf8')); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  try { state = JSON.parse(await readFile(statePath, 'utf8')); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  if (!state) {
    state = { version: 1, language, sources: {} };
    for (const prior of previousIndex?.entries || []) if (prior.status === 'retrieved_and_converted_candidate' && prior.official_response_sha256 && prior.library_relative_path) {
      state.sources[prior.source_id] = { current_path: prior.library_relative_path, accepted_official_response_sha256: prior.official_response_sha256, accepted_markdown_sha256: prior.markdown_sha256 || null };
    }
  }
  const entries = [];
  for (const row of englishRows) {
    const type = sourceType(row), candidate = candidateUrl(row, language);
    if (!candidate && row.source_id !== 'eu:ombudsman-complaint') {
      entries.push({ source_id: row.source_id, title: row.title, language, english_library_path: row.library_relative_path, status: 'no_registered_language_route', official_source: row.official_source });
      continue;
    }
    try {
      let fetched, text, converter, sourceHash, finalUrl, sourceUrls = [candidate?.url].filter(Boolean);
      if (row.source_id === 'eu:ombudsman-complaint') {
        const blocks = [];
        for (const route of OMBUDSMAN_BLOCKS) {
          const url = `https://www.ombudsman.europa.eu/rest/documents/pageContentByModeAndLang/${route.join('/')}?lang=${language.toLowerCase()}&onlyTitle=false`;
          const response = await request(url);
          if (!response.response.ok) throw new Error(`Ombudsman API HTTP ${response.response.status}`);
          const item = JSON.parse(response.bytes.toString('utf8'));
          if (String(item.codeIso).toLowerCase() !== language.toLowerCase() || String(item.language?.codeISO).toLowerCase() !== language.toLowerCase() || item.etranslated === true || !item.content) throw new Error(`Ombudsman API language/content check failed for ${route.join('/')}`);
          const body = plainTextFragment(item.content);
          if (body.length < 20) throw new Error(`Ombudsman API section was empty: ${route.join('/')}`);
          blocks.push({ route: route.join('/'), title: item.title || route.at(-1), content: body, url: response.finalUrl, bytes: response.bytes });
        }
        text = blocks.map(block => `## ${block.title}\n\n${block.content}`).join('\n\n');
        sourceHash = sha(Buffer.concat(blocks.map(block => block.bytes)));
        sourceUrls = blocks.map(block => block.url);
        finalUrl = sourceUrls[0];
        converter = `Node.js official Ombudsman ${LANGUAGE_PROFILES[language].name} content-set / stable seven-block order`;
      } else {
        fetched = await request(candidate.url);
        if (fetched.response.status !== 200) throw new Error(`HTTP ${fetched.response.status}; official text was not returned`);
        finalUrl = fetched.finalUrl;
        sourceHash = sha(fetched.bytes);
        if (fetched.contentType.toLowerCase().includes('application/pdf') || fetched.bytes.subarray(0, 5).toString() === '%PDF-') {
          text = await extractPdf(fetched.bytes); converter = 'pdfjs-dist 4.10.38 / text-position extraction';
        } else {
          if (!fetched.contentType.toLowerCase().includes('html')) throw new Error(`unexpected content type ${fetched.contentType}`);
          text = row.source_id === 'eu:commission-eu-law-complaint' ? commissionPageText(fetched.bytes.toString('utf8')) : htmlText(decodeEntities(fetched.bytes.toString('utf8')), { source_id: row.source_id, source_type: type });
          converter = row.source_id === 'eu:commission-eu-law-complaint' ? 'Node.js Commission main-content block extraction' : 'Node.js built-in HTML body parser / source-md-v3';
        }
      }
      const stats = languageStats(text, language);
      if (!isTargetLanguage(text, language)) throw new Error(`${LANGUAGE_PROFILES[language].name} text not confirmed (${stats.language_hits} ${language} / ${stats.en_hits} EN lexical hits in ${stats.word_count} words)`);
      if (text.length < 500) throw new Error(`source text too short (${text.length} characters)`);
      if (finalUrl.includes('eur-lex.europa.eu')) validateEurlexIdentity(row, finalUrl, fetched.bytes.toString('utf8'));
      const base = row.library_relative_path.replace(/^core\//, `${LANGUAGE_PROFILES[language].subdir}/`).replace(/_EN(?=\.md$)/, `_${language}`);
      const outputPath = within(library, base);
      const isCjeu = type === 'cjeu_judgment';
      const englishText = isCjeu ? await readFile(within(library, row.library_relative_path), 'utf8') : '';
      const caseLanguage = englishText.match(/Language of the case:\s*([A-Za-z]+)/i)?.[1] || null;
      const translationNote = isCjeu ? `\n- CJEU status: ${LANGUAGE_PROFILES[language].name} translation; language of the case in the English source: \`${caseLanguage || 'not recorded'}\`. The Court states that versions drawn up in the language of the case are authentic.\n` : '\n';
      const body = `# ${row.title}\n\n- Source ID: \`${row.source_id}\`\n- Representation language: \`${language}\`\n- Corresponding English file: \`${row.library_relative_path}\`\n- Official ${LANGUAGE_PROFILES[language].name} source: ${finalUrl}\n- Official response SHA-256: \`${sourceHash}\`\n- Converter: \`${converter}\`${translationNote}\n> Official-source language counterpart retrieved as a local candidate. Confirm document identity, version, completeness, notes, annexes and layout against the linked official source before relying on this conversion.\n\n${text.trim()}\n`;
      const output = Buffer.from(body, 'utf8');
      const markdownHash = sha(output);
      const contentHash = sha(text.trim());
      let record = state.sources[row.source_id];
      if (!record) record = state.sources[row.source_id] = { current_path: base, accepted_official_response_sha256: sourceHash, accepted_content_sha256: contentHash, accepted_markdown_sha256: markdownHash, baseline_status: 'initial_retrieval' };
      else {
        record.current_path ||= base;
        if (!record.accepted_content_sha256) record.accepted_content_sha256 = await existingContentHash(library, record.current_path);
      }
      if (record && record.accepted_content_sha256 && record.accepted_content_sha256 !== contentHash) {
        const stagedRel = path.posix.join('pending', base);
        const stagedPath = projectTempPath(within(library, stagedRel));
        await atomicProjectWrite(stagedPath, output);
        record.current_path ||= base;
        record.pending = { path: stagedRel, official_response_sha256: sourceHash, source_content_sha256: contentHash, markdown_sha256: markdownHash, detected_at: now(), official_source: finalUrl };
      } else {
        const stablePath = within(library, record.current_path || base);
        await atomicProjectWrite(stablePath, output);
        record.current_path ||= base;
        record.accepted_content_sha256 = contentHash;
        record.accepted_official_response_sha256 = sourceHash;
        record.accepted_markdown_sha256 = markdownHash;
        delete record.pending;
      }
      const changed = Boolean(record.pending && record.pending.source_content_sha256 === contentHash);
      entries.push({ source_id: row.source_id, title: row.title, language, english_library_path: row.library_relative_path, library_relative_path: record.current_path, official_source: row.official_source, requested_urls: sourceUrls, final_url: finalUrl, mode: candidate?.mode || 'official-localized-content-api', status: changed ? 'official_content_changed_pending_review' : 'retrieved_and_converted_candidate', official_response_sha256: sourceHash, markdown_sha256: markdownHash, ...(changed ? { pending_path: record.pending.path } : {}), converter, language_evidence: stats, language_of_case: caseLanguage, representation_kind: row.representation_kind, library_content_state: 'national_language_retrieval_candidate_not_trust_promoted' });
    } catch (error) {
      const saved=state.sources[row.source_id],prior=previousIndex?.entries?.find(x=>x.source_id===row.source_id);
      if(saved?.current_path){
        try{
          await readFile(within(library,saved.current_path));
          entries.push({...(prior||{}),source_id:row.source_id,title:row.title,language,english_library_path:row.library_relative_path,library_relative_path:saved.current_path,official_source:prior?.official_source||row.official_source,requested_url:candidate?.url||null,status:'retained_prior_official_conversion',reason:`Live recheck failed: ${error.message}`,official_response_sha256:saved.accepted_official_response_sha256,markdown_sha256:saved.accepted_markdown_sha256,library_content_state:'accepted_prior_official_conversion_live_recheck_failed'});
          continue;
        }catch{}
      }
      entries.push({ source_id: row.source_id, title: row.title, language, english_library_path: row.library_relative_path, official_source: row.official_source, requested_url: candidate?.url || null, mode: candidate?.mode || 'official-localized-content-api', status: 'not_added', reason: error.message });
    }
  }
  state.checked_at = now();
  const result = { version: 2, language, checked_at: state.checked_at, english_core_count: englishRows.length, retrieved_and_converted_count: entries.filter(entry => ['retrieved_and_converted_candidate','retained_prior_official_conversion'].includes(entry.status)).length, live_recheck_failed_count: entries.filter(entry => entry.status === 'retained_prior_official_conversion').length, pending_update_count: entries.filter(entry => entry.status === 'official_content_changed_pending_review').length, not_added_count: entries.filter(entry => !['retrieved_and_converted_candidate','retained_prior_official_conversion','official_content_changed_pending_review'].includes(entry.status)).length, entries };
  await atomicJson(statePath, state);
  await atomicJson(indexPath, result);
  console.log(JSON.stringify({ language, english_core_count: result.english_core_count, retrieved_and_converted_count: result.retrieved_and_converted_count, not_added_count: result.not_added_count, index: path.join(library, `national-language-index-${language}.json`) }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) main().catch(error => { console.error(error.stack || error.message); process.exitCode = 1; });
