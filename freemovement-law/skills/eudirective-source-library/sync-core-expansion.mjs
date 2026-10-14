#!/usr/bin/env node
// Official EUR-Lex retrieval, conversion, hash validation and change detection
// for the 24 sources added from the 2026-10-11 gap review.
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile, rename } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { atomicProjectWrite, projectTempPath } from '../runtime-storage.mjs';
import { currentVersion, htmlText, validateDocumentIdentity } from '../eudirective-core-work/eudirective-core/scripts/source-maintenance.mjs';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const CORE = path.join(ROOT, 'core');
const MANIFEST = path.join(ROOT, 'core-source-pack-manifest-0.7.0.json');
const INDEX = path.join(ROOT, 'retrieval-index.json');
const STATE = projectTempPath(path.join(CORE, 'state', 'expansion-state.json'));
const REPORT = projectTempPath(path.join(CORE, 'state', 'expansion-latest.json'));
const sha = b => createHash('sha256').update(b).digest('hex');
const safe = s => s.replace(/[^A-Za-z0-9._-]+/g, '_');
const atomic = async (p, value) => atomicProjectWrite(p, value);
const readJson = async p => JSON.parse(await readFile(p, 'utf8'));
const json = async (p, x) => atomic(p, JSON.stringify(x, null, 2) + '\n');
const celexUrl = id => `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:${id}`;

const cases = [
  ['62021CJ0154','C-154/21 Österreichische Post',['gdpr','right_of_access','recipients']],
  ['62021CJ0487','C-487/21 CRIF',['gdpr','right_of_access','copies']],
  ['62021CJ0579','C-579/21 Pankki S',['gdpr','right_of_access','access_logs']],
  ['62020CJ0175','C-175/20 SIA SS',['gdpr','purpose_limitation','data_minimisation']],
  ['62021CJ0634','C-634/21 SCHUFA',['gdpr','automated_decision_making','article_22']],
  ['62022CJ0203','C-203/22 Dun & Bradstreet Austria',['gdpr','automated_decision_making','article_15']],
  ['62021CJ0132','C-132/21 BE',['gdpr','supervisory_authority','judicial_remedies']],
  ['62021CJ0768','C-768/21 Land Hessen',['gdpr','supervisory_authority','corrective_measures']],
  ['62021CJ0300','C-300/21 Österreichische Post',['gdpr','compensation','article_82']],
  ['62023CJ0413','C-413/23 P EDPS v SRB',['eu_data_protection','pseudonymisation','identifiability']],
  ['62012CJ0084','C-84/12 Koushkaki',['visa_code','refusal','discretion']],
  ['62016CJ0403','C-403/16 El Hassani',['visa_code','refusal','judicial_review']],
  ['62019CJ0225','Joined Cases C-225/19 and C-226/19 R.N.N.S. and K.A.',['visa_code','refusal','inter_member_state_consultation','effective_remedy']],
  ['62011CJ0300','C-300/11 ZZ',['free_movement','national_security','effective_judicial_protection']],
  ['62012CJ0457','C-457/12 S and G',['free_movement','workers','derived_residence']],
  ['62017CJ0240','C-240/17 E',['schengen','entry_ban','residence_permit']],
  ['62021CJ0205','C-205/21',['law_enforcement_data_protection','biometrics','retention']],
  ['62022CJ0118','C-118/22',['law_enforcement_data_protection','biometrics','retention']],
];
const laws = [
  ['32008R0767','Regulation (EC) No 767/2008 concerning the Visa Information System (VIS)',['vis','data_access','data_remedies']],
  ['32018R1861','Regulation (EU) 2018/1861 on the establishment, operation and use of the Schengen Information System (SIS) in the field of border checks',['sis','border_checks','data_access','data_remedies']],
  ['32018R1862','Regulation (EU) 2018/1862 on the establishment, operation and use of the Schengen Information System (SIS) in the field of police cooperation and judicial cooperation in criminal matters',['sis','law_enforcement_data_protection','data_access']],
  ['32017R2226','Regulation (EU) 2017/2226 establishing the Entry/Exit System (EES)',['ees','data_access','data_remedies']],
  ['32018R1725','Regulation (EU) 2018/1725 on the protection of natural persons with regard to the processing of personal data by the Union institutions, bodies, offices and agencies',['eu_data_protection','eu_institutions','data_subject_rights']],
];

function source(id, title, tags, legalType) {
  const isCase = id.startsWith('6');
  const lower = id.toLowerCase();
  const rel = isCase ? `sources/case_law/full_text/eu_${lower}_EN.md` : `sources/eu/CELEX_${id}_EN_TXT.md`;
  return {
    source_id: `eu:${lower}`, identity: id, title, source_type: isCase ? 'cjeu_judgment' : 'regulation_consolidated',
    authority_level: 'eu', jurisdiction: 'EU', issuing_authority: isCase ? 'Court of Justice of the European Union' : 'European Union',
    legal_status: isCase ? 'binding_judicial_interpretation' : 'binding_secondary_law', canonical_owner_family: 'core', canonical_url: celexUrl(id),
    baseline_date: '2026-10-11', current_version_date: null, freshness_state: 'new_official_record', verification_basis: 'official_eurlex_identity_and_payload',
    verification_date: null, coverage_tags: tags, text_completeness_state: 'retrieved_full_text_candidate_not_trust_promoted', trusted_ingest_sha256: null,
    representations: [{ language: 'EN', kind: 'bundled_text', relative_path: rel, original_combined_pack_path: null,
      acquisition_url: celexUrl(id), source_policy: isCase ? 'eurlex-fixed-html' : 'eurlex-current-consolidation',
      update_intent: isCase ? 'fixed_identity_refresh' : 'living_consolidation', authenticity_state: 'verified_official',
      verification_method: 'official_identity_version_and_byte_hash_check', verified_at: null, bytes: null, sha256: null, final_url: null }],
  };
}

async function initialize() {
  const prior = await readJson(path.join(ROOT, '../eudirective-core-work/eudirective-core/references/source-pack/core-source-pack-manifest-0.6.0.json'));
  const added = [...cases, ...laws].map(([id,title,tags]) => source(id,title,tags));
  const ids = new Set(prior.sources.map(s => s.identity.toUpperCase()));
  const duplicates = added.filter(s => ids.has(s.identity));
  if (duplicates.length) throw Error(`review list is no longer absent: ${duplicates.map(s=>s.identity).join(', ')}`);
  const all = [...prior.sources, ...added];
  const expanded = { ...prior, manifest_version:'0.7.0', pack_version:'0.7.0', logical_source_count:all.length,
    representation_count:all.reduce((n,s)=>n+s.representations.length,0), live_verification_date:null,
    completion_status:'expanded_official_retrieval_in_progress',
    freshness_claim:'The 24 records from the 2026-10-11 gap review are maintained by sync-core-expansion.mjs. Retrieval state, official payload hashes, converted Markdown hashes, and discovered linked CELEX references are checked separately. These additions are not trust-promoted into the skill bundle.', sources:all };
  await json(MANIFEST, expanded);
  return expanded;
}

async function get(url, retries=4) {
  const u = new URL(url);
  if (u.protocol !== 'https:' || u.hostname !== 'eur-lex.europa.eu') throw Error(`blocked non-official URL: ${url}`);
  let error;
  for (let i=0;i<=retries;i++) {
    try {
      const res = await fetch(url, { headers:{'User-Agent':'eudirective-source-library/0.7.0','Accept-Language':'en','Accept':'text/html,application/xhtml+xml'}, redirect:'follow', signal:AbortSignal.timeout(45000) });
      if (!res.ok) throw Error(`HTTP ${res.status}`);
      if (new URL(res.url).protocol !== 'https:' || new URL(res.url).hostname !== 'eur-lex.europa.eu') throw Error(`redirect left the official EUR-Lex host: ${res.url}`);
      const bytes=Buffer.from(await res.arrayBuffer()), type=(res.headers.get('content-type')||'').split(';')[0].toLowerCase();
      if (type!=='text/html' && type!=='application/xhtml+xml') throw Error(`unexpected content type ${type}`);
      const head=bytes.subarray(0,6000).toString('utf8');
      if (bytes.length<1000 || !/<html\b|<!doctype html/i.test(head) || /captcha|verify that you're not a robot|request blocked/i.test(head)) throw Error('invalid HTML or access interstitial');
      return {bytes,final_url:res.url,content_type:type,etag:res.headers.get('etag'),last_modified:res.headers.get('last-modified')};
    } catch(e) { error=e; if(i<retries) await new Promise(r=>setTimeout(r,700*(2**i))); }
  }
  throw error;
}
function discoverCelex(html) { return [...new Set([...html.matchAll(/(?:[?&]|^)uri=CELEX:([0-9][0-9A-Z]+(?:-[0-9]{8})?)/gi)].map(m=>m[1].toUpperCase()))].sort(); }
function titleFromText(text, s) {
  if (s.source_type==='cjeu_judgment') return s.title;
  const m=text.match(/(?:REGULATION|REGULATION\s*\([^)]+\))\s+(?:\(EU\)[^\n]{0,180}|\(EC\)[^\n]{0,180})/i);
  return m?.[0]?.replace(/\s+/g,' ').trim() || s.title;
}
async function retrieveOne(s, state) {
  const id=s.identity, landing=await get(s.canonical_url), landingText=landing.bytes.toString('utf8');
  let effective=landing, effectiveIdentity=id, version=null;
  if (s.source_type==='regulation_consolidated') {
    try { version=currentVersion(s,landingText); effective=await get(version.url); effectiveIdentity=version.identity; }
    catch (e) { if (!/current consolidated version unavailable/.test(e.message)) throw e; }
  } else {
    const u=new URL(s.canonical_url); u.pathname='/legal-content/EN/TXT/HTML/'; effective=await get(u.href);
  }
  if (s.source_type==='cjeu_judgment') validateDocumentIdentity(s,effective.bytes,effectiveIdentity,'EN');
  else if (!version) {
    const upper=effective.bytes.toString('utf8').toUpperCase();
    const normalized=id.toUpperCase();
    if (!upper.includes(`CELEX:${normalized}`) && !upper.includes(`CELEX%3A${normalized}`) && !upper.includes(normalized)) throw Error(`official EUR-Lex payload does not identify ${effectiveIdentity}`);
  }
  const html=effective.bytes.toString('utf8'), body=htmlText(html,s);
  if (body.length<200) throw Error(`short conversion ${body.length} chars`);
  const rel=s.representations[0].relative_path, outRel=`core/${s.source_type==='cjeu_judgment'?'case_law/full_text':'eu'}/eu_${id.toLowerCase()}_EN.md`;
  const markdown=`# ${titleFromText(body,s)}\n\n- Source ID: \`${s.source_id}\`\n- Representation language: \`EN\`\n- Official identity: \`${effectiveIdentity}\`\n- Official source: ${effective.final_url}\n- Landing page: ${s.canonical_url}\n- Source HTML SHA-256: \`${sha(effective.bytes)}\`\n- Converter: \`Node.js EUR-Lex HTML body parser / source-md-v3\`\n\n> Converted from the official EUR-Lex document body. Check exact wording, tables, footnotes, completeness and legal pinpoints against the linked official source before legal reliance.\n\n${body}\n`;
  const data=Buffer.from(markdown), target=path.join(ROOT,outRel), existing=await readFile(target).catch(()=>null), prior=state.records?.[s.source_id];
  const sourceHash=sha(effective.bytes), markdownHash=sha(data), linked=discoverCelex(landingText), newLinked=prior?linked.filter(x=>!(prior.linked_celex||[]).includes(x)):[];
  const changeState=!prior?'new_source_added':(prior.source_sha256!==sourceHash||prior.markdown_sha256!==markdownHash||prior.effective_identity!==effectiveIdentity?'official_source_changed':newLinked.length?'new_linked_celex_references':'unchanged');
  let status='retrieved_and_converted', savedPath=outRel;
  if (prior && changeState!=='unchanged' && existing && !existing.equals(data)) { savedPath=`core/pending/${path.basename(outRel)}`; await atomic(projectTempPath(path.join(ROOT,savedPath)),data); status='changed_conversion_staged_for_review'; }
  else if (!existing) await atomic(target,data);
  const rawRel=`core/raw/expansion/${safe(id)}--${sourceHash}.html`;
  await atomic(projectTempPath(path.join(ROOT,rawRel)),effective.bytes);
  if (!prior || changeState==='unchanged') {
    s.title=titleFromText(body,s); s.verification_date=new Date().toISOString().slice(0,10); s.freshness_state='retrieved_official';
    s.current_version_date=version?.identity?.match(/-(\d{8})$/)?.[1]?.replace(/(\d{4})(\d{2})(\d{2})/,'$1-$2-$3')||null;
    const rep=s.representations[0]; rep.bytes=data.length; rep.sha256=markdownHash; rep.final_url=effective.final_url; rep.verified_at=s.verification_date;
  }
  return {source_id:s.source_id,identity:id,effective_identity:effectiveIdentity,title:titleFromText(body,s),source_url:effective.final_url,landing_url:s.canonical_url,
    landing_sha256:sha(landing.bytes),source_sha256:sourceHash,markdown_sha256:markdownHash,markdown_path:savedPath,raw_path:rawRel,
    effective_url:effective.final_url,content_type:effective.content_type,etag:effective.etag,last_modified:effective.last_modified,
    linked_celex:linked,new_linked_celex:newLinked,change_state:changeState,status};
}

async function verify(manifest) {
  const failures=[], verified=[];
  const report=await readJson(REPORT);
  const observations=Object.fromEntries(report.items.map(x=>[x.source_id,x]));
  for(const s of manifest.sources.slice(-23)) {
    try { const state=await readJson(STATE), r=state.records[s.source_id]; if(!r)throw Error('missing retrieval state');
      const raw=await readFile(projectTempPath(path.join(ROOT,r.raw_path))); if(sha(raw)!==r.source_sha256)throw Error('raw-source hash mismatch');
      const markdownPath=r.markdown_path.startsWith('core/pending/')?projectTempPath(path.join(ROOT,r.markdown_path)):path.join(ROOT,r.markdown_path);
      const markdown=await readFile(markdownPath); if(sha(markdown)!==r.markdown_sha256)throw Error('Markdown hash mismatch');
      const o=observations[s.source_id]; if(!o)throw Error('missing latest observation');
      const body=htmlText(raw.toString('utf8'),s), expected=`# ${titleFromText(body,s)}\n\n- Source ID: \`${s.source_id}\`\n- Representation language: \`EN\`\n- Official identity: \`${r.effective_identity}\`\n- Official source: ${o.effective_url}\n- Landing page: ${s.canonical_url}\n- Source HTML SHA-256: \`${r.source_sha256}\`\n- Converter: \`Node.js EUR-Lex HTML body parser / source-md-v3\`\n\n> Converted from the official EUR-Lex document body. Check exact wording, tables, footnotes, completeness and legal pinpoints against the linked official source before legal reliance.\n\n${body}\n`;
      if(!markdown.equals(Buffer.from(expected)))throw Error('offline deterministic conversion replay mismatch');
      verified.push({source_id:s.source_id,raw_sha256:sha(raw),markdown_sha256:sha(markdown),replay:'byte_identical',status:'verified'});
    }catch(e){failures.push({source_id:s.source_id,error:e.message});}
  }
  console.log(JSON.stringify({verified:verified.length,replay:'byte_identical',failures},null,2)); if(failures.length)process.exitCode=1;
}

async function main() {
  const command=process.argv[2]||'sync';
  let manifest=await readJson(MANIFEST).catch(()=>null); if(!manifest)manifest=await initialize();
  if(manifest.manifest_version!=='0.7.0'||manifest.logical_source_count!==69||manifest.representation_count!==70)throw Error('expanded manifest count/version mismatch');
  if(command==='verify') return verify(manifest);
  const state=await readJson(STATE).catch(()=>({version:1,records:{}})), items=[];
  for(const s of manifest.sources.slice(-23)) {
    try { items.push(await retrieveOne(s,state)); }
    catch(e) { items.push({source_id:s.source_id,identity:s.identity,change_state:'retrieval_failed',status:'retrieval_failed',error:e.message}); }
  }
  state.version=1; state.updated_at=new Date().toISOString(); state.records??={};
  for(const r of items) if(r.status!=='retrieval_failed') {
    const prior=state.records[r.source_id], observed={source_sha256:r.source_sha256,landing_sha256:r.landing_sha256,markdown_sha256:r.markdown_sha256,effective_identity:r.effective_identity,linked_celex:r.linked_celex,raw_path:r.raw_path,markdown_path:r.markdown_path,fetched_at:state.updated_at};
    if(!prior || r.change_state==='unchanged') state.records[r.source_id]=observed;
    else state.records[r.source_id]={...prior,last_checked_at:state.updated_at,pending_observation:observed};
  }
  const failures=items.filter(x=>x.status==='retrieval_failed');
  if (!failures.length) { manifest.completion_status='official_retrieval_conversion_and_hash_validation_complete'; manifest.live_verification_date=new Date().toISOString().slice(0,10); }
  await json(STATE,state); await json(MANIFEST,manifest);
  const oldIndex=await readJson(INDEX), map=new Map(oldIndex.map(x=>[x.source_id,x]));
  for(const r of items) if(r.status!=='retrieval_failed') { const s=manifest.sources.find(x=>x.source_id===r.source_id); map.set(r.source_id,{source_id:r.source_id,title:r.title,language:'EN',relative_path:r.markdown_path,official_source:s.canonical_url,manifest_expected_sha256:s.representations[0].sha256,official_html_sha256:r.source_sha256,markdown_sha256:r.markdown_sha256,retrieved_at:state.updated_at,converter:'Node.js EUR-Lex HTML body parser / source-md-v3',status:r.status,retrieved_url:r.effective_url,canonical_eli_url:null,canonical_document_url:r.effective_url,source_report_request_url:s.canonical_url,manifest_relative_path:s.representations[0].relative_path,library_relative_path:r.markdown_path,representation_kind:'bundled_text',library_content_state:'retrieved_full_text_candidate_not_trust_promoted',effective_identity:r.effective_identity,raw_path:r.raw_path}); }
  await json(INDEX,[...map.values()].sort((a,b)=>a.source_id.localeCompare(b.source_id)));
  const report={version:1,checked_at:state.updated_at,manifest_version:'0.7.0',scope_count:23,retrieved_count:items.length-failures.length,conversion_count:items.filter(x=>x.markdown_sha256).length,failures,items};
  await json(REPORT,report);
  console.log(JSON.stringify({manifest_version:'0.7.0',scope_count:23,retrieved:report.retrieved_count,converted:report.conversion_count,failures,report:REPORT},null,2));
  if(failures.length)process.exitCode=1;
}

if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href) main().catch(e=>{console.error(e.stack||e.message);process.exitCode=1;});
