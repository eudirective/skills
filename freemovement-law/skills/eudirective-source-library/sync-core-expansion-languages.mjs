#!/usr/bin/env node
// Retrieve only the 23 added EU sources in the four established EU-language mirrors.
// Uses the official Cellar REST route (with a source-specific Official Journal
// route where needed), identity/version/language checks, content-addressed raw
// snapshots under project-root temp/, deterministic Markdown, and per-language state.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { atomicProjectWrite, projectTempPath } from './runtime-storage.mjs';
import { htmlText } from './eudirective-core-work/eudirective-core/scripts/source-maintenance.mjs';

const ROOT=path.dirname(fileURLToPath(import.meta.url));
const INDEX=path.join(ROOT,'retrieval-index.json');
const MANIFEST=path.join(ROOT,'core-source-pack-manifest-0.7.0.json');
const LANGS={
 HU:{name:'Hungarian',words:`a az és hogy nem is egy vagy valamint illetve szerint alapján esetében által közötti között tekintettel figyelembe véve cikk cikke cikkének bekezdés pont rendelet irányelv határozat európai parlament tanács bizottság tagállam tagállamok államok jog jogosult köteles jogok hatály alkalmazandó alkalmazni vízum vízumkérelem kérelmező kérelem területén tartózkodás szabad mozgás családtag állampolgár közösség részére ezen e rendeletben irányelvben céljából feltéve hogy amennyiben továbbá azonban minden valamennyi szükséges kell kellő megfelelő tekintetben értelmében összhangban alapján rendelkezéseinek rendelkezéseit unió hivatalos lapja magyarország magyar`},
 SV:{name:'Swedish',words:`och att det den de som för av är till med på inte ska kan får enligt eller om rätt unionsmedborgare uppehållsrätt uppehållstillstånd tredjelandsmedborgare familjemedlem medlemsstat direktiv förordning domstolen artikel ansökan beslut myndighet arbetstagare arbete anställd socialt bistånd likabehandling omfattas bevilja villkor förevarande mål fastställa bestämmelser rättigheter grundläggande unionsrätt europeiska unionen officiella tidning överklagande klagomål vistelse bosatt fri rörlighet familj medborgare sökande prövning domstol rättslig hänsyn tillämplig medlemsstaterna`},
 DA:{name:'Danish',words:`og at det den de som for af er til med på ikke skal kan må ifølge eller om ret unionsborger opholdsret opholdstilladelse tredjelandsstatsborger familiemedlem medlemsstat direktiv forordning domstolen artikel ansøgning afgørelse myndighed arbejdstager arbejde lønmodtager social bistand ligebehandling omfattet bevilge vilkår foreliggende sag fastslå bestemmelser rettigheder grundlæggende unionsret europæiske union officielle tidende klage ophold bosat fri bevægelighed familie statsborger ansøger prøvelse domstol retlig hensyn gældende medlemsstaterne`},
 RO:{name:'Romanian',words:`și să în în care de la cu pentru este sunt drept cetățean cetățeni stat statelor membru membru directivă regulament decizie cerere solicitant viză ședere reședință permis libera circulație familie familiei muncă lucrător salariat social asistență curtea instanța hotărâre drepturi fundamentale dispoziții aplicare aplicabil autorități administrație europeană uniunii oficială jurnal articol alineat cauză cauza acțiune pronunță judecată discriminare proporționalitate condiții condițiile teritoriu resortisant resortisanți străin străini protecție procedură procedura autoritate autorităților obligație obligații poate trebuie acordă acordarea persoană persoane statului statele prezenta prezentei prevederile legislația legislației dreptul dreptului cetățenie căsătorie soț soție cerințe exercitare refuz justificare motivare contestare administrativ comisie parlament consiliu libertate`},
};
const EN_WORDS=new Set(`the and of to in that shall may this for with article court judgment member state states person applicant visa application regulation directive commission council parliament rights residence family free movement is are by from on as`.split(' '));
const sha=b=>createHash('sha256').update(b).digest('hex');
const atomic=async(file,data)=>atomicProjectWrite(file,data);
const readJson=async f=>JSON.parse(await readFile(f,'utf8'));
const writeJson=(f,x)=>atomic(f,JSON.stringify(x,null,2)+'\n');
const safe=s=>s.replace(/[^A-Za-z0-9._-]+/g,'_');
const within=(base,rel)=>{const f=path.resolve(ROOT,rel);if(f!==ROOT&&!f.startsWith(ROOT+path.sep))throw Error(`unsafe relative path ${rel}`);return f;};
const langStats=(text,lang)=>{const words=text.toLowerCase().match(/[a-záéíóöőúüűåäæøăâîșşțţ]+/g)||[],markers=new Set(LANGS[lang].words.split(' ')),hits=words.filter(x=>markers.has(x)).length,en=words.filter(x=>EN_WORDS.has(x)).length;return {word_count:words.length,language_hits:hits,en_hits:en,language_ratio:words.length?hits/words.length:0};};
function languageValid(text,lang){const s=langStats(text,lang);return {ok:s.word_count>=150&&s.language_hits>=22&&s.language_hits>s.en_hits*1.25&&s.language_ratio>=0.025,stats:s};}
function caseLanguage(english){return english.match(/Language of the case:\s*([A-Za-z]+)/i)?.[1]||null;}
function caseNo(sourceId){const id=sourceId.replace(/^eu:/i,'');const m=id.match(/^6\d{4}CJ(\d{4})$/i);return m?`C-${Number(m[1])}/${id.slice(3,5)}`:null;}
function localizedUrl(value, lang) {
  const u = new URL(value);
  if (u.hostname !== 'eur-lex.europa.eu') throw Error(`non-EUR-Lex source ${value}`);
  u.pathname = u.pathname.replace(/\/legal-content\/[A-Z]{2}\//i, `/legal-content/${lang}/`);
  return u.href;
}
const CELLAR_ACCEPT_LANGUAGE = { HU: 'hun', SV: 'swe', DA: 'dan', RO: 'ron' };
const CELLAR_SOURCE_OVERRIDES = {
  // Retain the full Official Journal text, including its recitals. The Cellar
  // consolidated rendition omits the recital block. The Hungarian official
  // corrigendum is applied as four deterministic text replacements below.
  'eu:32018r1725': { celex: '32018R1725', mode: 'cellar-official-oj-text' },
};
function celexFromUrl(value) {
  const raw = new URL(value).searchParams.get('uri') || '';
  const celex = raw.replace(/^CELEX:/i, '').trim();
  if (!/^[0-9A-Z()/-]+$/i.test(celex)) throw Error(`invalid CELEX locator in ${value}`);
  return celex;
}
function officialLanguagePage(row, lang, sourceUrl) {
  if (row.source_id === 'eu:32018r1725') return `https://eur-lex.europa.eu/legal-content/${lang}/ALL/?uri=CELEX:32018R1725`;
  return localizedUrl(sourceUrl, lang);
}
function cellarUrl(celex, lang) {
  const u = new URL(`https://publications.europa.eu/resource/celex/${encodeURIComponent(celex)}`);
  u.searchParams.set('language', lang.toLowerCase());
  return u.href;
}
async function fetchCellar(url, lang) {
  let current = new URL(url);
  if (current.protocol !== 'https:' || current.hostname !== 'publications.europa.eu' || !current.pathname.startsWith('/resource/celex/')) {
    throw Error(`blocked Cellar URL ${url}`);
  }
  for (let hop = 0; hop < 6; hop++) {
    if (current.protocol !== 'https:' || current.hostname !== 'publications.europa.eu' || !current.pathname.startsWith('/resource/')) {
      throw Error(`Cellar redirect left the official HTTPS resource host: ${current.href}`);
    }
    const response = await fetch(current.href, {
      redirect: 'manual',
      signal: AbortSignal.timeout(45000),
      headers: {
        'user-agent': 'eudirective-core-language-library/0.7.0',
        'accept-language': CELLAR_ACCEPT_LANGUAGE[lang],
        'accept': 'application/xhtml+xml',
      },
    });
    if ([301, 302, 303, 307, 308].includes(response.status)) {
      const location = response.headers.get('location');
      if (!location) throw Error(`Cellar HTTP ${response.status} without a Location header`);
      const next = new URL(location, current);
      if (next.hostname !== 'publications.europa.eu' || !next.pathname.startsWith('/resource/cellar/')) {
        throw Error(`Cellar redirect left the official publication resource: ${next.href}`);
      }
      next.protocol = 'https:';
      current = next;
      continue;
    }
    if (response.status === 404) return { notFound: true, requestedUrl: url };
    if (response.status !== 200) throw Error(`Cellar HTTP ${response.status}; official text was not returned`);
    const bytes = Buffer.from(await response.arrayBuffer());
    const contentType = (response.headers.get('content-type') || '').split(';')[0].toLowerCase();
    if (contentType !== 'application/xhtml+xml' || bytes.length < 1000 || bytes.length > 10_000_000 || !/<html\b|<!doctype html/i.test(bytes.subarray(0, 12000).toString('utf8'))) {
      throw Error(`invalid Cellar response (${contentType}, ${bytes.length} bytes)`);
    }
    return {
      bytes,
      finalUrl: current.href,
      requestedUrl: url,
      contentType,
      etag: response.headers.get('etag'),
      lastModified: response.headers.get('last-modified'),
    };
  }
  throw Error('Cellar redirect limit exceeded');
}
async function fetchOfficial(row, lang) {
  const sourceUrl = row.retrieved_url || row.official_source;
  if (!sourceUrl || new URL(sourceUrl).hostname !== 'eur-lex.europa.eu') throw Error(`missing official EUR-Lex locator for ${row.source_id}`);
  const celex = celexFromUrl(sourceUrl);
  const override = CELLAR_SOURCE_OVERRIDES[row.source_id];
  const requestedCelex = override?.celex || celex;
  const requestUrl = cellarUrl(requestedCelex, lang);
  const result = await fetchCellar(requestUrl, lang);
  if (result.notFound) throw Error(`Cellar returned HTTP 404 for ${requestUrl}`);
  return {
    ...result,
    sourceUrl: officialLanguagePage(row, lang, sourceUrl),
    requestedUrls: [requestUrl],
    requestedCelex,
    language: lang,
    retrievalMode: override?.mode || 'cellar-current-version',
    usedFallback: false,
  };
}
function actNumber(row) {
  const fromTitle = row.title.match(/\b(\d{1,4}\/\d{4})\b/);
  if (fromTitle) return fromTitle[1];
  const id = row.source_id.replace(/^eu:/i, '').toUpperCase();
  const match = id.match(/^3(\d{4})[A-Z](\d{4})$/);
  return match ? `${Number(match[2])}/${match[1]}` : null;
}
function identityValid(row, fetched, html) {
  const normalized = s => s.toUpperCase().replace(/[^A-Z0-9]/g, '');
  const header = normalized(html.slice(0, 12000));
  const content = normalized(html);
  const actId = actNumber(row);
  if (actId && header.includes(normalized(actId))) return true;
  const caseId = caseNo(row.source_id);
  return Boolean(caseId && (header.includes(normalized(caseId)) || content.includes(normalized(caseId))));
}
function versionValid(row, fetched, html) {
  if (!row.current_version_date) return true;
  const [year, month, day] = row.current_version_date.split('-');
  const dateForms = [`${day}.${month}.${year}`, `${year}.${month}.${day}`, `${year}-${month}-${day}`];
  const header = html.slice(0, 12000);
  const lang = fetched.language;
  const languageMarker = lang ? new RegExp(`\\b${lang}\\b`) : null;
  if (!dateForms.some(value => header.includes(value)) || !languageMarker?.test(header)) return false;
  const actId = actNumber(row);
  return Boolean(actId && header.replace(/<[^>]*>/g, ' ').includes(actId));
}
function relativeFor(row, lang) {
  const p = row.library_relative_path.replace(/^core\//, `core/${lang.toLowerCase()}/`);
  return p.replace(/_EN(?=\.md$)/, `_${lang}`);
}
function versionDateText(value) {
  return value ? value.split('-').reverse().join('.') : null;
}
const HU_2018_1725_CORRIGENDUM = {
  celex: '32018R1725R(01)',
  url: 'https://eur-lex.europa.eu/legal-content/HU/TXT/?uri=CELEX%3A32018R1725R%2801%29',
  published: '2019-11-11',
  replacements: [
    ['Az adatfeldolgozás jogszerűsége érdekében', 'Az adatkezelés jogszerűsége érdekében'],
    ['genetikai és biometrikus adatok,', 'genetikai adatok, a természetes személyek egyedi azonosítását célzó biometrikus adatok,'],
    ['különösen az adatvédelemhez való jogukat', 'különösen a személyes adatok védelméhez való jogukat'],
    ['genetikai adatok, biometrikus adatok, az egészségre', 'genetikai adatok, a természetes személyek egyedi azonosítását célzó biometrikus adatok, az egészségre'],
  ],
};
function applyOfficialErrata(row, lang, input) {
  if (row.source_id !== 'eu:32018r1725' || lang !== 'HU') return { body: input, applied: [] };
  let body = input;
  const applied = [];
  for (const [before, after] of HU_2018_1725_CORRIGENDUM.replacements) {
    const count = body.split(before).length - 1;
    if (count !== 1) throw Error(`Hungarian corrigendum target must occur once; found ${count}: ${before}`);
    body = body.replace(before, after);
    applied.push({ before, after });
  }
  return { body, applied };
}
function conversion(row, lang, sourceUrl, retrievalUrl, sourceHash, html, body, caseLang, currentVersionDate, retrievalMode, appliedErrata = []) {
  const caseNote = row.source_id.startsWith('eu:6')
    ? `\n- CJEU representation: ${caseLang && caseLang.toLowerCase() === LANGS[lang].name.toLowerCase() ? 'language of the case; authentic version' : `official EUR-Lex translation; language of the case: \`${caseLang || 'not recorded'}\`; the language-of-case version is authentic`}.\n`
    : '';
  const versionNote = currentVersionDate
    ? `\n- EUR-Lex current consolidated version date: \`${currentVersionDate}\`.\n`
    : '';
  const fullTextNote = row.source_id === 'eu:32018r1725'
    ? `\n- Full-text note: the local copy retains the Official Journal recitals. EUR-Lex lists language-specific corrigenda for HU, DE and IT; those for DE and IT do not alter this ${lang} text.\n`
    : '';
  const errataNote = appliedErrata.length
    ? `\n- Applied official corrigendum: \`${HU_2018_1725_CORRIGENDUM.celex}\`, published ${HU_2018_1725_CORRIGENDUM.published}; four exact corrections applied. Source: ${HU_2018_1725_CORRIGENDUM.url}\n`
    : '';
  const publisherCaveat = row.source_id.startsWith('eu:6')
    ? '> This is an official EUR-Lex language representation. For CJEU case law, the authentic text is the judgment in the language of the case.'
    : '> Local text reviewed against the official publisher response. Consolidated EUR-Lex texts are informational; the Official Journal language text remains the authentic published act.';
  return `# ${row.title}\n\n- Source ID: \`${row.source_id}\`\n- Representation language: \`${lang}\`\n- Corresponding English file: \`${row.library_relative_path}\`\n- Official EUR-Lex language page: ${sourceUrl}\n- Publications Office Cellar response: ${retrievalUrl}\n- Official response SHA-256: \`${sourceHash}\`\n- Converter: \`Node.js built-in HTML body parser / source-md-v3\`${versionNote}${caseNote}${fullTextNote}${errataNote}\n${publisherCaveat}\n\n${body.trim()}\n`;
}
async function syncLanguage(lang, rows) {
  const indexFile = path.join(ROOT, `national-language-index-${lang}.json`);
  const stateFile = path.join(ROOT, `national-language-state-${lang}.json`);
  const oldIndex = await readJson(indexFile);
  const state = await readJson(stateFile);
  const added = [];
  for (const row of rows) {
    const english = await readFile(within(ROOT, row.library_relative_path), 'utf8');
    const caseLang = row.source_id.startsWith('eu:6') ? caseLanguage(english) : null;
    const oldEntry = oldIndex.entries.find(x => x.source_id === row.source_id);
    const priorState = state.sources[row.source_id] || {};
    const relative = relativeFor(row, lang);
    try {
      const fetched = await fetchOfficial(row, lang);
      const html = fetched.bytes.toString('utf8');
      if (!identityValid(row, fetched, html)) {
        throw Error(`official response identity mismatch (source=${row.source_id}; CELEX=${fetched.requestedCelex}; final=${fetched.finalUrl}; case=${caseNo(row.source_id) || 'n/a'})`);
      }
      if (!versionValid(row, fetched, html)) throw Error(`publisher response lacks expected current-version evidence for ${row.current_version_date}`);
      const extracted = htmlText(html, { source_id: row.source_id, source_type: row.representation_kind === 'verified_source_note' ? 'cjeu_judgment' : 'source' });
      const corrected = applyOfficialErrata(row, lang, extracted);
      const body = corrected.body;
      const appliedErrata = corrected.applied;
      const checked = languageValid(body, lang);
      if (!checked.ok) throw Error(`${LANGS[lang].name} language check failed (${checked.stats.language_hits} language / ${checked.stats.en_hits} English lexical hits in ${checked.stats.word_count} words)`);
      if (body.length < 500) throw Error(`short conversion (${body.length} chars)`);
      const currentVersionDate = row.current_version_date || null;
      if (fetched.usedFallback && (!currentVersionDate || !html.includes(versionDateText(currentVersionDate)) || !html.toUpperCase().includes(lang))) {
        throw Error('fallback response lacks the recorded current-version date or target-language marker');
      }
      const sourceHash = sha(fetched.bytes);
      const markdown = Buffer.from(conversion(row, lang, fetched.sourceUrl, fetched.finalUrl, sourceHash, html, body, caseLang, currentVersionDate, fetched.retrievalMode, appliedErrata));
      const markdownHash = sha(markdown);
      const contentHash = sha(body.trim());
      const rawRel = `core/raw/expansion-languages/${lang}/${safe(row.identity || row.source_id)}--${sourceHash}.html`;
      await atomic(projectTempPath(within(ROOT, rawRel)), fetched.bytes);
      let status = oldEntry?.acceptance_state === 'accepted_local_representation' ? 'accepted_local_representation' : 'retrieved_and_converted_candidate';
      let savedPath = relative;
      if (priorState.accepted_content_sha256 && priorState.accepted_content_sha256 !== contentHash) {
        const pending = path.posix.join('pending', relative);
        await atomic(projectTempPath(within(ROOT, pending)), markdown);
        priorState.pending = {
          path: pending,
          official_response_sha256: sourceHash,
          source_content_sha256: contentHash,
          markdown_sha256: markdownHash,
          detected_at: new Date().toISOString(),
          official_source: fetched.sourceUrl,
          retrieval_url: fetched.finalUrl,
          retrieval_mode: fetched.retrievalMode,
          applied_errata: appliedErrata,
          raw_path: rawRel,
        };
        status = 'official_content_changed_pending_review';
        savedPath = priorState.current_path || relative;
      } else {
        await atomic(within(ROOT, relative), markdown);
        state.sources[row.source_id] = {
          ...priorState,
          current_path: relative,
          accepted_official_response_sha256: sourceHash,
          accepted_content_sha256: contentHash,
          accepted_markdown_sha256: markdownHash,
          raw_path: rawRel,
          baseline_status: priorState.current_path ? 'unchanged_official_text' : 'initial_retrieval',
        };
      }
      added.push({
        source_id: row.source_id,
        title: row.title,
        language: lang,
        english_library_path: row.library_relative_path,
        library_relative_path: savedPath,
        official_source: row.official_source,
        official_language_page: fetched.sourceUrl,
        requested_urls: fetched.requestedUrls,
        final_url: fetched.finalUrl,
        requested_celex: fetched.requestedCelex,
        current_version_date: currentVersionDate,
        retrieval_mode: fetched.retrievalMode,
        applied_errata: appliedErrata,
        status,
        acceptance_state: oldEntry?.acceptance_state || 'reviewed_pending_acceptance',
        official_response_sha256: sourceHash,
        markdown_sha256: markdownHash,
        raw_path: rawRel,
        converter: 'Node.js built-in HTML body parser / source-md-v3',
        language_evidence: checked.stats,
        language_of_case: caseLang,
        representation_kind: row.representation_kind || 'bundled_text',
        library_content_state: status,
        ...(priorState.pending ? { pending_path: priorState.pending.path } : {}),
      });
    } catch (e) {
      const saved = state.sources[row.source_id];
      if (saved?.current_path) {
        try {
          await readFile(within(ROOT, saved.current_path));
          added.push({
            ...oldEntry,
            source_id: row.source_id,
            title: row.title,
            language: lang,
            english_library_path: row.library_relative_path,
            status: oldEntry?.acceptance_state === 'accepted_local_representation' ? 'accepted_local_representation' : 'retained_prior_official_conversion',
            reason: `Live recheck failed: ${e.message}`,
          });
          continue;
        } catch {}
      }
      added.push({ source_id: row.source_id, title: row.title, language: lang, english_library_path: row.library_relative_path, official_source: row.official_source, status: 'not_added', reason: e.message, language_of_case: caseLang });
    }
  }
  const entryMap = new Map((oldIndex.entries || []).map(x => [x.source_id, x]));
  for (const x of added) entryMap.set(x.source_id, x);
  const entries = [...entryMap.values()].sort((a, b) => a.source_id.localeCompare(b.source_id));
  state.checked_at = new Date().toISOString();
  const acceptedStates = ['accepted_local_representation'];
  const retrievableStates = ['retrieved_and_converted_candidate', 'retained_prior_official_conversion', 'official_content_changed_pending_review', ...acceptedStates];
  const result = {
    version: 4,
    language: lang,
    checked_at: state.checked_at,
    source_pack_version: '0.7.0',
    english_core_count: 69,
    retrieved_and_converted_count: entries.filter(x => retrievableStates.includes(x.status)).length,
    accepted_local_representation_count: entries.filter(x => acceptedStates.includes(x.status)).length,
    live_recheck_failed_count: entries.filter(x => x.status === 'retained_prior_official_conversion').length,
    pending_update_count: entries.filter(x => x.status === 'official_content_changed_pending_review').length,
    not_added_count: entries.filter(x => !retrievableStates.includes(x.status)).length,
    entries,
  };
  await writeJson(stateFile, state);
  await writeJson(indexFile, result);
  return {
    language: lang,
    checked: added.length,
    available: added.filter(x => ['retrieved_and_converted_candidate', 'accepted_local_representation'].includes(x.status)).length,
    pending: added.filter(x => x.status === 'official_content_changed_pending_review').length,
    not_added: added.filter(x => x.status === 'not_added').length,
    failures: added.filter(x => x.status === 'not_added').map(x => ({ source_id: x.source_id, reason: x.reason })),
    index: indexFile,
  };
}
async function verify(rows, langs) {
  const failures = [];
  const checked = [];
  for (const lang of langs) {
    const index = await readJson(path.join(ROOT, `national-language-index-${lang}.json`));
    const state = await readJson(path.join(ROOT, `national-language-state-${lang}.json`));
    const entries = new Map(index.entries.map(x => [x.source_id, x]));
    for (const row of rows) {
      const item = entries.get(row.source_id);
      if (!['retrieved_and_converted_candidate', 'retained_prior_official_conversion', 'official_content_changed_pending_review', 'accepted_local_representation'].includes(item?.status)) continue;
      try {
        const record = state.sources[row.source_id];
        const rawPath = item.status === 'official_content_changed_pending_review' ? item.raw_path : record.raw_path;
        const raw = await readFile(projectTempPath(within(ROOT, rawPath)));
        const mdPath = item.status === 'official_content_changed_pending_review'
          ? projectTempPath(within(ROOT, item.pending_path))
          : within(ROOT, item.library_relative_path);
        const md = await readFile(mdPath);
        if (sha(raw) !== item.official_response_sha256 || sha(md) !== item.markdown_sha256) throw Error('stored source or Markdown hash mismatch');
        if (item.status !== 'official_content_changed_pending_review' && sha(md) !== record.accepted_markdown_sha256) throw Error('accepted Markdown hash mismatch');
        const html = raw.toString('utf8');
        if (!identityValid(row, { requestedCelex: item.requested_celex }, html)) throw Error('offline source identity check failed');
        if (!versionValid(row, { requestedCelex: item.requested_celex, language: lang }, html)) throw Error('offline source version check failed');
        const extracted = htmlText(html, { source_id: row.source_id, source_type: row.representation_kind === 'verified_source_note' ? 'cjeu_judgment' : 'source' });
        const corrected = applyOfficialErrata(row, lang, extracted);
        const body = corrected.body;
        if (!languageValid(body, lang).ok) throw Error('offline language check failed');
        const expected = Buffer.from(conversion(row, lang, item.official_language_page, item.final_url, item.official_response_sha256, html, body, item.language_of_case, item.current_version_date, item.retrieval_mode, corrected.applied));
        if (!md.equals(expected)) throw Error('offline deterministic conversion replay mismatch');
        checked.push({ source_id: row.source_id, language: lang, status: item.status });
      } catch (e) {
        failures.push({ source_id: row.source_id, language: lang, error: e.message });
      }
    }
  }
  console.log(JSON.stringify({ verified: checked.length, failures }, null, 2));
  if (failures.length) process.exitCode = 1;
}

async function main() {
  const [command = 'sync', ...args] = process.argv.slice(2);
  const manifest = await readJson(MANIFEST);
  const index = await readJson(INDEX);
  const targets = manifest.sources.slice(-23);
  const targetById = new Map(targets.map(source => [source.source_id, source]));
  const rows = index
    .filter(x => x.language === 'EN' && x.library_relative_path.startsWith('core/') && targetById.has(x.source_id))
    .map(x => ({ ...x, current_version_date: targetById.get(x.source_id).current_version_date || null }));
  if (rows.length !== 23) throw Error(`expected 23 English additions, found ${rows.length}`);
  let langs;
  if (args.includes('--all')) langs = Object.keys(LANGS);
  else {
    const at = args.indexOf('--language');
    langs = at >= 0 ? String(args[at + 1] || '').toUpperCase().split(',').filter(Boolean) : [];
  }
  if (command === '--verify' || command === 'verify') {
    langs = langs.length ? langs : Object.keys(LANGS);
    return verify(rows, langs);
  }
  if (command === '--ack') {
    const lang = String(args[0] || '').toUpperCase();
    const id = args[1];
    const stateFile = path.join(ROOT, `national-language-state-${lang}.json`);
    const state = await readJson(stateFile);
    const record = state.sources[id];
    if (!LANGS[lang] || !record?.pending) throw Error('expected --ack LANGUAGE SOURCE_ID with a pending update');
    const pending = record.pending;
    const raw = await readFile(projectTempPath(within(ROOT, pending.path)));
    if (sha(raw) !== pending.markdown_sha256) throw Error('pending Markdown hash mismatch');
    await atomic(within(ROOT, record.current_path), raw);
    record.accepted_official_response_sha256 = pending.official_response_sha256;
    record.accepted_content_sha256 = pending.source_content_sha256;
    record.accepted_markdown_sha256 = pending.markdown_sha256;
    record.raw_path = pending.raw_path;
    delete record.pending;
    record.acknowledged_at = new Date().toISOString();
    await writeJson(stateFile, state);
    const idxFile = path.join(ROOT, `national-language-index-${lang}.json`);
    const idx = await readJson(idxFile);
    const entry = idx.entries.find(x => x.source_id === id);
    entry.status = entry.acceptance_state === 'accepted_local_representation' ? 'accepted_local_representation' : 'retrieved_and_converted_candidate';
    entry.library_relative_path = record.current_path;
    delete entry.pending_path;
    entry.official_response_sha256 = pending.official_response_sha256;
    entry.markdown_sha256 = pending.markdown_sha256;
    entry.raw_path = pending.raw_path;
    idx.pending_update_count = idx.entries.filter(x => x.status === 'official_content_changed_pending_review').length;
    await writeJson(idxFile, idx);
    console.log(JSON.stringify({ language: lang, source_id: id, acknowledged: true }, null, 2));
    return;
  }
  if (!['sync', '--sync'].includes(command)) throw Error('Use sync --language HU|SV|DA|RO, sync --all, verify [--language HU|SV|DA|RO], or --ack LANGUAGE SOURCE_ID');
  if (!langs.length) throw Error('select --language HU|SV|DA|RO or --all');
  for (const lang of langs) {
    if (!LANGS[lang]) throw Error(`unsupported language ${lang}`);
    console.log(JSON.stringify(await syncLanguage(lang, rows)));
  }
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main().catch(e=>{console.error(e.stack||e.message);process.exitCode=1;});
