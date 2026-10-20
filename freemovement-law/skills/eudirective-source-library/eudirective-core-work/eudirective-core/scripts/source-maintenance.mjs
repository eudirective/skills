#!/usr/bin/env node
// Deterministic official-source retrieval, conversion and review detection.
// Node.js built-ins are used for HTTP, HTML and state; pdfjs-dist is pinned for PDF text.
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile, rename, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { atomicProjectWrite, projectTempPath } from '../../../runtime-storage.mjs';

export const VERSION = '1.0.1';
const MAX_RESPONSE_BYTES = 50_000_000;
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DEFAULT_MANIFEST = path.resolve(ROOT, '../../eudirective-source-library-0.6.0/core-source-pack-manifest-0.7.0.json');
const EURLEX = new Set(['eur-lex.europa.eu']);
const OP_HOSTS = {
  commission_operational_guidance_page: new Set(['commission.europa.eu']),
  ombudsman_operational_guidance_page: new Set(['www.ombudsman.europa.eu', 'ombudsman.europa.eu']),
  commission_handbook: new Set(['home-affairs.ec.europa.eu']),
};
const CONSOLIDATED = new Set(['directive_consolidated', 'regulation_consolidated']);
const STATIC = new Set(Object.keys(OP_HOSTS));
const DOC_TYPES = new Set(['charter','directive_consolidated','regulation_consolidated','commission_recommendation','commission_staff_working_document','commission_notice','cjeu_judgment']);
const ID_ALIAS = { 'eu:c-2023-1392': '52023XC01392' };
const URL_ALIAS = { 'eu:c-2023-1392': 'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:52023XC01392' };
const URI_ALIAS = { 'eu:12012p': '12012P/TXT' };
const URL_WORK_PART = { 'eu:12012p': 'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:12012P/TXT' };
const OMB_BLOCKS = [
 ['home','how-to-make-a-complaint','can-the-ombudsman-help-me'],
 ['home','how-to-make-a-complaint','how-can-the-european-ombudsman-help'],
 ['home','how-to-make-a-complaint','what-is-maladministration'],
 ['home','how-to-make-a-complaint','what-the-european-ombudsman-cannot-do'],
 ['home','how-to-make-a-complaint','submit-a-complaint'],
 ['home','how-to-make-a-complaint','submit-a-complaint-2'],
 ['checklist-for-making-a-complaint','how-to-make-a-complaint','home'],
];
const sha = b => createHash('sha256').update(b).digest('hex');
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const safe = s => s.replace(/[^A-Za-z0-9._-]+/g, '_');
const writeAtomic = async (p, data) => atomicProjectWrite(p, data);
const readJson = async p => JSON.parse(await readFile(p, 'utf8'));
const writeJson = (p, obj) => writeAtomic(p, JSON.stringify(obj, null, 2) + '\n');

function validateUrl(src, value) {
  const u = new URL(value), hosts = OP_HOSTS[src.source_type] ?? EURLEX;
  if (u.protocol !== 'https:' || !hosts.has(u.hostname.toLowerCase())) throw Error(`nonofficial host/protocol for ${src.source_id}: ${value}`);
  if (!STATIC.has(src.source_type)) {
    const raw = (u.searchParams.get('uri') || '').replace(/^CELEX:/i, '').toUpperCase();
    const ids = new Set([src.identity.toUpperCase(), (ID_ALIAS[src.source_id] || '').toUpperCase(), (URI_ALIAS[src.source_id] || '').toUpperCase()].filter(Boolean));
    const base = ('0' + src.identity.slice(1)).toUpperCase();
    const isDateVersion = CONSOLIDATED.has(src.source_type) && new RegExp(`^${base}-\\d{8}$`).test(raw);
    if (!ids.has(raw) && raw !== base && !isDateVersion) throw Error(`URL identity mismatch for ${src.source_id}: ${value}`);
  }
  return u;
}
function officialUrl(src) { return URL_ALIAS[src.source_id] || src.canonical_url; }
function htmlUrl(value) { const u = new URL(value); u.pathname = u.pathname.replace('/AUTO/', '/TXT/HTML/').replace(/\/TXT\/$/, '/TXT/HTML/'); return u.href; }
function docUrl(src, landing) { return URL_WORK_PART[src.source_id] || htmlUrl(landing); }
function representationKey(src, rep) { return `${src.source_id}::${rep.language.toUpperCase()}::${rep.relative_path}`; }
function retrievedMarkdownPath(src,rep){return `markdown/retrieved-full-text/${safe(src.source_id)}_${rep.language.toUpperCase()}.md`;}
function localizedUrl(value, language) {
  const u=new URL(value), code=language.toUpperCase();
  u.pathname=u.pathname.replace(/(\/legal-content\/)[A-Z]{2}(\/)/i,`$1${code}$2`);
  return u.href;
}
function representationDocumentUrl(src, rep, identity) {
  if(STATIC.has(src.source_type)) return localizedUrl(rep.acquisition_url,rep.language);
  if(src.source_type==='commission_handbook'||/\/TXT\/PDF\//i.test(rep.acquisition_url)||/\.pdf(?:\?|$)/i.test(rep.acquisition_url)) return localizedUrl(rep.acquisition_url,rep.language);
  const base=src.source_type==='charter'?URL_WORK_PART[src.source_id]:URL_ALIAS[src.source_id]||rep.acquisition_url;
  const u=new URL(localizedUrl(base,rep.language));
  u.pathname=u.pathname.replace('/AUTO/','/TXT/HTML/').replace(/\/TXT\/$/,'/TXT/HTML/');
  u.searchParams.set('uri',`CELEX:${identity}`);
  return u.href;
}
function declaredLanguage(html) {
  const root=html.match(/<(?:html|body)\b[^>]*>/i)?.[0]||'';
  const metas=[...html.matchAll(/<meta\b[^>]*>/gi)].map(x=>x[0]);
  const languageMeta=metas.find(t=>/WT\.z_usr_lan|dc\.language|name\s*=\s*["']language/i.test(t));
  const value=attr(root,'lang')||attr(root,'xml:lang')||(languageMeta&&attr(languageMeta,'content'));
  return value?.split(/[-_]/)[0].trim().toUpperCase()||null;
}
function languageByLexicon(text) {
  const words=(text.toLowerCase().match(/[a-zåäöéü]+/g)||[]), counts=new Map();
  const lex={EN:new Set('the of and to in that is for with shall may by from which this be as on or an are it not where has have were can must their these those article court'.split(' ')),SV:new Set('och att det som för är till av på inte ska har en ett den domstolen enligt med eller detta dessa vara kan får sådan där samt från'.split(' '))};
  for(const lang of ['EN','SV'])counts.set(lang,words.filter(w=>lex[lang].has(w)).length);
  const en=counts.get('EN'),sv=counts.get('SV'),total=words.length;
  if(total<100)return null;
  if(en>=sv*1.35&&en/total>=0.04)return 'EN';
  if(sv>=en*1.35&&sv/total>=0.04)return 'SV';
  return null;
}
function validateRepresentationLanguage(rep, bytes, contentType, src={source_type:'charter',source_id:'language-check'}) {
  if(contentType==='application/json-page-content-set') return;
  if(contentType==='application/pdf') return; // PDF language is checked against extracted text during conversion.
  const html=bytes.toString('utf8'), declared=declaredLanguage(html);
  const actual=declared||languageByLexicon(htmlText(html,src));
  if(!actual) throw Error(`source language is not declared or recognizable for ${rep.relative_path}`);
  if(actual!==rep.language.toUpperCase()) throw Error(`language mismatch for ${rep.relative_path}: expected ${rep.language}, source declares ${actual}`);
}
const ELI_LANGUAGE = Object.freeze({ EN: 'ENG', SV: 'SWE' });
function eliLanguage(language) {
  const segment = ELI_LANGUAGE[String(language || '').toUpperCase()];
  if (!segment) throw Error(`unsupported EUR-Lex ELI language: ${language}`);
  return segment;
}
function validateDocumentIdentity(src, bytes, identity, language = 'EN') {
  const html=bytes.toString('utf8'), links=[...html.matchAll(/<link\b[^>]*rel\s*=\s*(["'])canonical\1[^>]*>/gi)].map(m=>attr(m[0],'href'));
  const canonical=links.map(x=>decodeURIComponent(x).toUpperCase());
  const eliLang=eliLanguage(language);
  const celex=(ID_ALIAS[src.source_id]||identity).toUpperCase();
  if(canonical.some(x=>new RegExp(`[?&]URI=CELEX:${celex.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?:$|[&#])`,'i').test(x))) return;
  if(src.source_id==='eu:12012p'&&html.toUpperCase().includes(`HTTPS://EUR-LEX.EUROPA.EU/ELI/TREATY/CHAR_2012/OJ/${eliLang}`)) return;
  const match=celex.match(/^[03](\d{4})([LR])(\d+)(?:-(\d{8}))?$/);
  if(match){const [,year,letter,number,date]=match,kind=letter==='L'?'dir':'reg',eli=`/ELI/${kind}/${year}/${Number(number)}${date?`/${date.slice(0,4)}-${date.slice(4,6)}-${date.slice(6,8)}`:''}/${eliLang}`.toUpperCase();if(canonical.some(x=>x.includes(eli)))return;}
  const reco=celex.match(/^3(\d{4})H(\d+)$/);if(reco&&canonical.some(x=>x.includes(`/ELI/RECO/${reco[1]}/${Number(reco[2])}/OJ/${eliLang}`)))return;
  const notice=celex.match(/^5(\d{4})XC(\d+)$/);if(notice&&canonical.some(x=>x.includes(`/ELI/C/${notice[1]}/${Number(notice[2])}/OJ/${eliLang}`)))return;
  const swd=celex.match(/^5(\d{4})SC(\d+)$/);if(swd&&canonical.some(x=>x.includes(`/LEGAL-CONTENT/EN/TXT/?URI=SWD:SWD_${swd[1]}_${swd[2].padStart(4,'0')}`)))return;
  const caseId=celex.match(/^6(\d{4})CJ(\d{4})$/);
  if(caseId){const body=(html.match(/<body\b[^>]*>([\s\S]*?)<\/body\s*>/i)?.[1]||'').slice(0,12000),text=decodeHtml(body.replace(/<[^>]*>/g,' ')).replace(/[‐‑‒–—]/g,'-').replace(/\s+/g,' ');const exact=`Case C-${Number(caseId[2])}/${caseId[1].slice(2)}`;if(new RegExp(`^\\s*${exact.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}\\b`,'i').test(text))return;}
  throw Error(`downloaded document canonical identity does not match ${identity} for ${src.source_id}`);
}

async function get(url, src, timeoutMs = 45000, accept = 'text/html,application/xhtml+xml') {
  let current = url;
  for (let n = 0; n <= 8; n++) {
    validateUrl(src, current);
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(current, { redirect: 'manual', signal: controller.signal, headers: { 'User-Agent': `eudirective-core-source-maintenance/${VERSION}`, 'Accept-Language': 'en', Accept: accept } });
      if ([301,302,303,307,308].includes(res.status)) {
        const loc = res.headers.get('location'); if (!loc) throw Error(`redirect without Location at ${current}`);
        current = new URL(loc, current).href; validateUrl(src, current); continue;
      }
      if (!res.ok) throw Error(`HTTP ${res.status} for ${current}`);
      const bytes = await readLimitedBody(res, current), type = (res.headers.get('content-type') || '').split(';')[0].trim().toLowerCase();
      return { bytes, meta: { request_url: url, final_url: current, content_type: type, etag: res.headers.get('etag'), last_modified: res.headers.get('last-modified'), fetched_at: now(), sha256: sha(bytes) } };
    } finally { clearTimeout(timer); }
  }
  throw Error(`too many redirects for ${url}`);
}
async function readLimitedBody(response, label) {
  const declared = Number(response.headers.get('content-length'));
  if (Number.isFinite(declared) && declared > MAX_RESPONSE_BYTES) throw Error(`response exceeds ${MAX_RESPONSE_BYTES} byte limit for ${label}`);
  if (!response.body) return Buffer.alloc(0);
  const reader = response.body.getReader(), chunks = []; let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      size += value.byteLength;
      if (size > MAX_RESPONSE_BYTES) { await reader.cancel(); throw Error(`response exceeds ${MAX_RESPONSE_BYTES} byte limit for ${label}`); }
      chunks.push(Buffer.from(value));
    }
  } finally { reader.releaseLock(); }
  return Buffer.concat(chunks, size);
}
function validatePayload(src, bytes, type) {
  if (type==='application/pdf') {
    if (type !== 'application/pdf' || !bytes.subarray(0, 5).equals(Buffer.from('%PDF-')) || !bytes.subarray(-4096).includes(Buffer.from('%%EOF'))) throw Error(`incomplete/non-PDF official resource for ${src.source_id}`);
  } else {
    const s = bytes.subarray(0, 50000).toString('utf8').toLowerCase();
    if (bytes.length < 1000 || !/<html\b|<!doctype html/.test(s)) throw Error(`expected substantial HTML for ${src.source_id}`);
    if (/captcha|access denied|verify that you're not a robot/.test(s)) throw Error(`interstitial received for ${src.source_id}`);
  }
}
function stripTags(html) {
  return html.replace(/<!--[\s\S]*?-->/g, '').replace(/<script\b[^>]*>[\s\S]*?<\/script\s*>/gi, '').replace(/<style\b[^>]*>[\s\S]*?<\/style\s*>/gi, '').replace(/<noscript\b[^>]*>[\s\S]*?<\/noscript\s*>/gi, '');
}
function decodeHtml(s) {
  const named = { amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' ',ndash:'–',mdash:'—',rsquo:'’',lsquo:'‘',rdquo:'”',ldquo:'“',laquo:'«',raquo:'»',bdquo:'„',sbquo:'‚',euro:'€',sect:'§',copy:'©',hellip:'…',
    aacute:'á',agrave:'à',acirc:'â',atilde:'ã',auml:'ä',aring:'å',aelig:'æ',ccedil:'ç',eacute:'é',egrave:'è',ecirc:'ê',euml:'ë',iacute:'í',igrave:'ì',icirc:'î',iuml:'ï',ntilde:'ñ',oacute:'ó',ograve:'ò',ocirc:'ô',otilde:'õ',ouml:'ö',oslash:'ø',uacute:'ú',ugrave:'ù',ucirc:'û',uuml:'ü',yacute:'ý',yuml:'ÿ',
    Aacute:'Á',Agrave:'À',Acirc:'Â',Atilde:'Ã',Auml:'Ä',Aring:'Å',AElig:'Æ',Ccedil:'Ç',Eacute:'É',Egrave:'È',Ecirc:'Ê',Euml:'Ë',Iacute:'Í',Igrave:'Ì',Icirc:'Î',Iuml:'Ï',Ntilde:'Ñ',Oacute:'Ó',Ograve:'Ò',Ocirc:'Ô',Otilde:'Õ',Ouml:'Ö',Oslash:'Ø',Uacute:'Ú',Ugrave:'Ù',Ucirc:'Û',Uuml:'Ü',Yacute:'Ý',Yuml:'Ÿ' };
  return s.replace(/&(#x[\da-f]+|#\d+);?|&([a-z][a-z0-9]+)(;|(?=\s|<))/gi, (whole,numeric,name) => { if (numeric) { const n = numeric[1].toLowerCase() === 'x' ? parseInt(numeric.slice(2),16) : Number(numeric.slice(1)); return Number.isInteger(n)&&n>0&&n<=0x10ffff ? String.fromCodePoint(n) : `\uE000${whole}\uE001`; } const value=named[name] ?? named[name.toLowerCase()];return value??`\uE000${whole}\uE001`; });
}
function attr(tag, key) { const m = tag.match(new RegExp(`\\b${key}\\s*=\\s*(["'])(.*?)\\1`, 'i')); return m?.[2] ?? ''; }
function elementSlice(html, start, tag) {
  const re = new RegExp(`<\\/?${tag}\\b[^>]*>`, 'gi'); re.lastIndex = start;
  let depth=0, m;
  while((m=re.exec(html))){if(/^<\//.test(m[0])){depth--;if(depth===0)return html.slice(start,re.lastIndex);}else if(!/\/>$/.test(m[0]))depth++;}
  throw Error(`unclosed ${tag} container`);
}
function container(html, src) {
  if (DOC_TYPES.has(src.source_type)) {
    const documentDiv = html.match(/<div\b(?=[^>]*\bid\s*=\s*["']document1["'])[^>]*>/i);
    const body = html.match(/<body\b[^>]*>/i);
    const start = documentDiv?.index ?? body?.index;
    if (start === undefined || start < 0) throw Error(`HTML body/document1 missing for ${src.source_id}`);
    return elementSlice(html,start,documentDiv?'div':'body');
  }
  if (src.source_type === 'commission_operational_guidance_page') {
    const m = html.match(/<main\b(?=[^>]*\bid\s*=\s*["']main-content["'])[^>]*>/i);
    if (!m) throw Error(`main#main-content missing for ${src.source_id}`);
    return elementSlice(html,m.index,'main');
  }
  return html;
}
function htmlText(html, src) {
  html = stripTags(container(html, src));
  html = html.replace(/<a\b(?=[^>]*(?:class\s*=\s*["'][^"']*linkToTop|href\s*=\s*["']#document1))[^>]*>\s*Top\s*<\/a>/gi, '');
  const skip = new Set(['script','style','noscript','svg','nav','header','aside','footer','form','button','head']);
  let out = '', ignored = [];
  const voidTags = new Set(['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']);
  const tokens = html.match(/<!--[\s\S]*?-->|<![^>]*>|<[^>]*>|[^<]+/g) || [];
  for (const token of tokens) {
    if (!token.startsWith('<')) { if (!ignored.length) { const t=decodeHtml(token).replace(/\s+/g,' ').trim(); if(t) { if(out && !/[\s\n]$/.test(out)) out+=' '; out+=t; } } continue; }
    if (/^<!/.test(token)) continue;
    const close = /^<\//.test(token), name = token.match(/^<\/?\s*([\w:-]+)/)?.[1]?.toLowerCase(); if (!name) continue;
    if (ignored.length) {
      const current = ignored.at(-1);
      if (close) { current.depth--; if (current.depth <= 0) ignored.pop(); }
      else if (!voidTags.has(name) && !/\/>$/.test(token)) current.depth++;
      continue;
    }
    if (!close) {
      const hint=(attr(token,'id')+' '+attr(token,'class')).toLowerCase();
      if (skip.has(name) || /breadcrumb|cookie|skiplink|share-tools|linktotop|link-to-top|banner|bgtool|bglang/.test(hint)) { if (!voidTags.has(name) && !/\/>$/.test(token)) ignored.push({name,depth:1}); continue; }
      if (/^h[1-6]$/.test(name)) { out+='\n\n'+'#'.repeat(Number(name[1]))+' '; }
      else if (['p','div','section','li','tr','blockquote','table','br','hr'].includes(name)) out+='\n';
      if(name==='li') out+='- ';
      if(name==='tr') out+='| ';
      if(name==='td'||name==='th') out+=' ';
    } else {
      if(name==='td'||name==='th') out+=' |';
      if (/^h[1-6]$/.test(name) || ['p','div','section','li','tr','blockquote','table'].includes(name)) out+='\n';
    }
  }
  const text=out.replace(/[ \t]+\n/g,'\n').replace(/\n{3,}/g,'\n\n').trim();
  const unresolved=text.match(/\uE000([\s\S]*?)\uE001/);
  if(unresolved)throw Error(`unsupported HTML entity ${unresolved[1]}; conversion failed closed`);
  return text;
}
function anchors(html) { return [...html.matchAll(/<a\b[^>]*href\s*=\s*(["'])(.*?)\1[^>]*>([\s\S]*?)<\/a\s*>/gi)].map(m=>({href:m[2],label:decodeHtml(m[3].replace(/<[^>]*>/g,'')).replace(/\s+/g,' ').trim()})); }
function currentVersion(src, html) {
  if (!CONSOLIDATED.has(src.source_type)) return null;
  const m=html.match(/Access\s+current\s+version\s*\(\s*(\d{2})\/(\d{2})\/(\d{4})\s*\)/i) || html.match(/Current\s+consolidated\s+version\s*:[\s\S]{0,300}?(\d{2})\/(\d{2})\/(\d{4})/i);
  if(!m) throw Error(`current consolidated version unavailable for ${src.identity}`);
  const [,dd,mm,yyyy]=m, date=`${yyyy}${mm}${dd}`, base=('0'+src.identity.slice(1)).toUpperCase();
  const a=anchors(html).find(x=>decodeURIComponent(x.href).toUpperCase().includes(`CELEX:${base}-${date}`));
  if(!a) throw Error(`current dated CELEX link ${base}-${date} missing`);
  return {url:htmlUrl(new URL(a.href,src.canonical_url).href),identity:`${base}-${date}`};
}
const EN_MONTHS = Object.fromEntries('january february march april may june july august september october november december'.split(' ').map((name,index)=>[name,index+1]));
function isoDate(value) {
  const s=String(value||'').trim();
  let m=s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/); if(m)return `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
  m=s.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/); if(m)return `${m[3]}-${m[2].padStart(2,'0')}-${m[1].padStart(2,'0')}`;
  m=s.match(/^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$/); if(m&&EN_MONTHS[m[2].toLowerCase()])return `${m[3]}-${String(EN_MONTHS[m[2].toLowerCase()]).padStart(2,'0')}-${m[1].padStart(2,'0')}`;
  return null;
}
function officialMetadataText(html) {
  return decodeHtml(stripTags(String(html||'').replace(/<\/(?:dt|dd|tr|th|td|p|li|h[1-6]|div|br)\s*>/gi,'\n')))
    .replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
}
function pageDateMetadata(html) {
  const raw=String(html||''), out={};
  const aliases={
    page_published:['datepublished','article:published_time','dc.date.issued','dcterms.issued','date.issued'],
    page_created:['datecreated','dcterms.created'],
    page_modified:['datemodified','article:modified_time','dc.date.modified','dcterms.modified','date.modified','last-modified','lastupdated','date.updated'],
    page_last_reviewed:['lastreviewed','date.lastreviewed','last-reviewed','lastreview']
  };
  const dateFrom=value=>{const s=decodeHtml(String(value||''));const m=s.match(/\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4}/);return m&&isoDate(m[0]);};
  for(const [field,keys] of Object.entries(aliases)){
    for(const tag of raw.matchAll(/<meta\b[^>]*>/gi)){
      const attrs=Object.fromEntries([...tag[0].matchAll(/([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g)].map(m=>[m[1].toLowerCase(),m[2]??m[3]??m[4]??'']));
      const key=(attrs.name||attrs.property||attrs.itemprop||'').toLowerCase().replace(/[^a-z0-9:._-]/g,'');
      if(keys.includes(key)){const date=dateFrom(attrs.content);if(date){out[field]={date,source:`page metadata ${key}`};break;}}
    }
  }
  const text=officialMetadataText(raw);
  const visible={page_published:/\b(?:published|publication date|date published)\b\s*:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i,page_modified:/\b(?:last updated|last modified|date modified|updated on|modified on)\b\s*:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i,page_last_reviewed:/\b(?:last reviewed|date reviewed|reviewed on)\b\s*:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i};
  for(const [field,re] of Object.entries(visible)){if(out[field])continue;const m=text.match(re),date=m&&isoDate(m[1]);if(date)out[field]={date,source:`visible page label: ${m[0].split(/\s+/).slice(0,-1).join(' ')}`};}
  for(const script of raw.matchAll(/<script\b[^>]*type\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)){
    let json;try{json=JSON.parse(script[1]);}catch{continue;}
    const visit=value=>{if(!value||typeof value!=='object')return;for(const [key,item] of Object.entries(value)){const k=key.toLowerCase(),field=k==='datepublished'?'page_published':k==='datecreated'?'page_created':k==='datemodified'?'page_modified':k==='lastreviewed'?'page_last_reviewed':null;if(field&&!out[field]){const date=dateFrom(item);if(date)out[field]={date,source:`JSON-LD ${key}`};}if(Array.isArray(item))item.forEach(visit);else if(item&&typeof item==='object')visit(item);}};visit(json);
  }
  return out;
}
function extractOfficialDates(src, landingHtml, payloadHtml, version) {
  const landingText=officialMetadataText(landingHtml), documentText=payloadHtml?officialMetadataText(payloadHtml):'';
  const fields=pageDateMetadata(landingHtml);
  const patterns={
    date_document:/\b(?:date of document|document date|date of adoption|adopted on)\b\s*:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i,
    date_signature:/\b(?:date of signature|signed on)\b\s*:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i,
    date_publication:/\b(?:date of publication|publication date)\b\s*:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i,
    date_effect:/\b(?:date of effect|date of entry into force|entry into force date)\b\s*:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i,
    date_application:/\b(?:date of application|application date)\b\s*:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i,
    date_end_of_validity:/\b(?:end of validity|date of end of validity)\b\s*:?\s*(\d{4}-\d{1,2}-\d{2}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i
  };
  for(const [field,re] of Object.entries(patterns)){
    const match=landingText.match(re)||documentText.match(re), date=match&&isoDate(match[1]);
    if(date)fields[field]={date,source:landingText.match(re)?'official EUR-Lex metadata page':'official act text'};
  }
  if(!fields.date_document){
    const heading=documentText.slice(0,5000).match(/\bof\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})/i), date=heading&&isoDate(heading[1]);
    if(date)fields.date_document={date,source:'date stated in the official act heading'};
  }
  if(!fields.date_publication){
    const citation=documentText.match(/\b(?:OJ|Official Journal)\s+(?:of the European Union\s+)?[LC]\s*,?\s*[^,\n]{0,40}?\b(\d{1,2}[./]\d{1,2}[./]\d{4})\b/i), date=citation&&isoDate(citation[1]);
    if(date)fields.date_publication={date,source:'official-journal citation in the act'};
  }
  if(version){const date=version.identity.match(/-(\d{4})(\d{2})(\d{2})$/);if(date)fields.current_consolidated_version_date={date:`${date[1]}-${date[2]}-${date[3]}`,source:'EUR-Lex current-consolidated-version identifier'};}
  if(src.current_version_date&&!fields.current_consolidated_version_date)fields.registered_current_version_date={date:src.current_version_date,source:'bundled source manifest'};
  return fields;
}
function linkedCelex(html) { return [...new Set([...html.matchAll(/(?:[?&]|^)uri=CELEX:([0-9][0-9A-Z]+(?:-[0-9]{8})?)/gi)].map(m=>m[1].toUpperCase()))].sort(); }

async function fetchOmbBlock(src, route, root) {
  const url='https://www.ombudsman.europa.eu/rest/documents/pageContentByModeAndLang/'+route.join('/')+'?lang=en&onlyTitle=false';
  const {bytes,meta}=await get(url,src,45000,'application/json');
  const obj=JSON.parse(bytes.toString('utf8'));
  if ((obj.codeIso||'').toLowerCase()!=='en' || typeof obj.content!=='string' || !obj.content.trim()) throw Error(`invalid English content block ${route.join('/')}`);
  const raw=`raw/${safe(src.source_id)}.blocks/${route.join('--')}.json`;
  await writeAtomic(projectTempPath(path.join(root,raw)),bytes);
  return {route,title:obj.title||route[2],url,sha256:meta.sha256,raw_path:raw,content:obj.content};
}
async function retrieve(src,rep,root,timeout) {
  const key=representationKey(src,rep), landingUrl=localizedUrl(officialUrl(src),rep.language), l=await get(landingUrl,src,timeout), landing=l.bytes; validatePayload(src,landing,l.meta.content_type);
  let effectiveUrl=landingUrl, identity=ID_ALIAS[src.source_id]||src.identity, payload=landing, meta=l.meta, version=currentVersion(src,landing.toString('utf8'));
  if(version){identity=version.identity;effectiveUrl=representationDocumentUrl(src,rep,identity);({bytes:payload,meta}=await get(effectiveUrl,src,timeout));validatePayload(src,payload,meta.content_type);}
  else if(!STATIC.has(src.source_type)){effectiveUrl=representationDocumentUrl(src,rep,URI_ALIAS[src.source_id]||identity);({bytes:payload,meta}=await get(effectiveUrl,src,timeout,/\/TXT\/PDF\//i.test(effectiveUrl)||src.source_type==='commission_handbook'?'application/pdf':'text/html,application/xhtml+xml'));validatePayload(src,payload,meta.content_type);}
  let blocks=[];
  if(src.source_id==='eu:ombudsman-complaint'){
    for(const route of OMB_BLOCKS) blocks.push(await fetchOmbBlock(src,route,root));
    meta={...meta,sha256:sha(Buffer.concat(blocks.map(x=>Buffer.from(x.sha256,'hex')))),content_type:'application/json-page-content-set'};
  }
  validateRepresentationLanguage(rep,payload,meta.content_type,src);
  if(!STATIC.has(src.source_type)&&meta.content_type!=='application/pdf') validateDocumentIdentity(src,payload,identity,rep.language);
  const ext=meta.content_type==='application/pdf'?'.pdf':'.html', rawPath=`raw/${safe(src.source_id)}--${safe(rep.language)}${ext}`;
  await writeAtomic(projectTempPath(path.join(root,rawPath)),payload);
  const official_dates=extractOfficialDates(src,landing.toString('utf8'),meta.content_type==='application/pdf'?'':payload.toString('utf8'),version);
  return {source_id:src.source_id,representation_key:key,representation_language:rep.language,relative_path:rep.relative_path,identity:src.identity,title:src.title,source_type:src.source_type,catalog_url:src.canonical_url,canonical_url:landingUrl,retrieved_url:effectiveUrl,effective_identity:identity,manifest_current_version_date:src.current_version_date,current_consolidated_identity:version?.identity||null,official_dates,landing_sha256:l.meta.sha256,content_sha256:meta.sha256,content_type:meta.content_type,etag:meta.etag||null,last_modified:meta.last_modified||null,fetched_at:meta.fetched_at,raw_path:rawPath,linked_celex:linkedCelex(landing.toString('utf8')),related_payloads:blocks.map(({content,...b})=>b),status:'candidate_observation_requires_review',landing_path:STATIC.has(src.source_type)?rawPath:null};
}
function compare(records,manifest,state) {
  const prior=state.sources||{}, known=Object.fromEntries(manifest.sources.map(s=>[s.source_id,s])),events=[];
  for(const r of records){const old=prior[r.representation_key],src=known[r.source_id];let kind='unchanged';
    r.previous_official_dates=old?.official_dates||null;
    r.previous_current_consolidated_identity=old?.current_consolidated_identity||null;
    const observed=(r.current_consolidated_identity||'').split('-').at(-1)||'', expected=(src.current_version_date||'').replaceAll('-','');
    if(!old) kind='baseline_required';
    if(r.current_consolidated_identity && ((!old&&expected&&observed!==expected)||(old&&r.current_consolidated_identity!==old.current_consolidated_identity))) kind='new_consolidated_version';
    else if(old&&(r.content_sha256!==old.content_sha256||r.landing_sha256!==old.landing_sha256)) kind='official_content_changed';
    const dateValues=dates=>Object.fromEntries(Object.entries(dates||{}).map(([field,value])=>[field,value?.date||null]));
    const oldDates=dateValues(old?.official_dates), newDates=dateValues(r.official_dates);
    const dateChanged=Boolean(old&&JSON.stringify(oldDates)!==JSON.stringify(newDates));
    r.date_change_state=!old?'baseline_required':dateChanged?'official_date_metadata_changed':Object.keys(newDates).length?'unchanged':'official_date_metadata_unavailable';
    const registeredDate=src.current_version_date||null, observedDate=r.official_dates?.current_consolidated_version_date?.date||null;
    r.consolidated_date_check={registered_date:registeredDate,observed_date:observedDate,status:registeredDate&&observedDate?(registeredDate===observedDate?'match':'mismatch'):registeredDate?'official_date_unavailable':observedDate?'registry_date_missing':'not_applicable'};
    if(dateChanged&&kind==='unchanged')kind='official_date_metadata_changed';
    if(r.consolidated_date_check.status==='mismatch'&&kind==='unchanged')kind='consolidated_date_registry_mismatch';
    const added=old?r.linked_celex.filter(x=>!(old.linked_celex||[]).includes(x)):[];
    if(added.length&&kind==='unchanged')kind='new_linked_celex_references'; if(added.length)r.new_linked_celex=added;
    r.change_state=kind;
    if(kind!=='unchanged')events.push({source_id:r.source_id,representation_key:r.representation_key,language:r.representation_language,relative_path:r.relative_path,identity:r.identity,change_state:kind,date_change_state:r.date_change_state,previous_official_dates:r.previous_official_dates,official_dates:r.official_dates,consolidated_date_check:r.consolidated_date_check,previous_current_consolidated_identity:r.previous_current_consolidated_identity,current_consolidated_identity:r.current_consolidated_identity,manifest_current_version_date:r.manifest_current_version_date,new_linked_celex:added,content_sha256:r.content_sha256,action:'human_review_before_manifest_or_trusted_source_update'});
  }
  return {report_version:1,checked_at:now(),manifest_version:manifest.manifest_version,scope_count:records.length,change_count:events.length,events,observations:records};
}
function validatePathTaxonomy(sources){let cjeu=0,notes=0,full=0,guidance=0;for(const src of sources)for(const rep of src.representations){const p=rep.relative_path.replaceAll('\\','/');if(src.source_type==='cjeu_judgment'){cjeu++;const prefix=rep.kind==='verified_source_note'?'sources/case_law/notes/':rep.kind==='bundled_text'?'sources/case_law/full_text/':null;if(!prefix||!p.startsWith(prefix))throw Error(`CJEU path taxonomy mismatch: ${src.source_id} ${rep.kind} ${p}`);if(rep.kind==='verified_source_note')notes++;else full++;}else if(['commission_operational_guidance_page','ombudsman_operational_guidance_page'].includes(src.source_type)){guidance++;if(!p.startsWith('sources/guidance/notes/'))throw Error(`operational guidance path taxonomy mismatch: ${src.source_id} ${p}`);}else if(!p.startsWith('sources/eu/'))throw Error(`EU/common law path must remain under sources/eu/: ${src.source_id} ${p}`);}if(cjeu!==51||notes!==19||full!==32||guidance!==2)throw Error(`taxonomy count mismatch: CJEU=${cjeu}, notes=${notes}, full_text=${full}, guidance=${guidance}`);return {cjeu,notes,full,guidance};}
async function loadManifest(p){const m=await readJson(p); const reps=Array.isArray(m.sources)?m.sources.reduce((n,s)=>n+(Array.isArray(s.representations)?s.representations.length:0),0):0; if(m.manifest_version!=='0.7.0'||!Array.isArray(m.sources)||m.sources.length!==69||new Set(m.sources.map(s=>s.source_id)).size!==69||m.representation_count!==70||reps!==70)throw Error('manifest must be exactly 0.7.0 / 69 unique sources / 70 representations'); const paths=new Set();for(const s of m.sources){validateUrl(s,officialUrl(s));for(const rep of s.representations){if(!rep.language||!rep.relative_path||paths.has(rep.relative_path))throw Error(`invalid or duplicate manifest representation path: ${rep.relative_path}`);paths.add(rep.relative_path);validateUrl(s,representationDocumentUrl(s,rep,URI_ALIAS[s.source_id]||ID_ALIAS[s.source_id]||s.identity));}}validatePathTaxonomy(m.sources);return m;}
function normalizeState(state,manifest){const byId=Object.fromEntries(manifest.sources.map(s=>[s.source_id,s]));if(state.version>=2){const remap=(entries,isPending=false)=>Object.fromEntries(Object.entries(entries||{}).map(([oldKey,value])=>{const bits=oldKey.split('::'),sourceId=value?.source_id||bits[0],language=(value?.representation_language||value?.language||bits[1]||'').toUpperCase(),src=byId[sourceId],rep=src?.representations.find(r=>r.language.toUpperCase()===language);if(!src||!rep)return [oldKey,value];const key=representationKey(src,rep);return [key,isPending?{...value,source_id:src.source_id,representation_key:key,language:rep.language,relative_path:rep.relative_path}:value];}));return {...state,sources:remap(state.sources),pending:remap(state.pending,true)};}const sources={},pending={};for(const [oldId,value] of Object.entries(state.sources||{})){const src=byId[oldId];if(!src)continue;const en=src.representations.find(r=>r.language.toUpperCase()==='EN');if(en)sources[representationKey(src,en)]=value;}
  for(const [oldId,event] of Object.entries(state.pending||{})){const src=byId[oldId];if(!src)continue;const en=src.representations.find(r=>r.language.toUpperCase()==='EN');if(!en)continue;const key=representationKey(src,en);pending[key]={...event,source_id:src.source_id,representation_key:key,language:en.language,relative_path:en.relative_path};}
  return {...state,version:2,migrated_legacy_record_level_state:true,sources,pending};}
function registry(m){const rows=m.sources.slice().sort((a,b)=>a.source_id.localeCompare(b.source_id)).flatMap(s=>s.representations.map(rep=>{const url=representationDocumentUrl(s,rep,URI_ALIAS[s.source_id]||ID_ALIAS[s.source_id]||s.identity);return `| \`${s.source_id}\` | \`${rep.language}\` | \`${rep.relative_path}\` | \`${s.source_type}\` | [${ID_ALIAS[s.source_id]||s.identity}](${url}) | ${rep.update_intent} |`;}));return [`# Official source registry — eudirective-core ${m.manifest_version}`,'',`Scope is exactly ${m.logical_source_count} logical sources / ${m.representation_count} manifest representations. Each representation has its own language-bound URL and output path. Hosts and document identities are allowlisted. This generated index is not proof that source bytes or currentness were freshly checked.`,'','| Source ID | Language | Output path | Type | Official source | Update handling |','|---|---|---|---|---|---|',...rows,''].join('\n');}
async function toMarkdown(src,rep,r,root){let body,conv,languageNote='';
  if(r.related_payloads?.length){const pieces=[];for(const b of r.related_payloads){const j=await readJson(projectTempPath(path.join(root,b.raw_path)));pieces.push(`# ${j.title||b.title}\n\n${htmlText(j.content,src)}`);}body=pieces.join('\n\n');conv='Node.js html-body parser / source-md-v3';}
  else {const raw=await readFile(projectTempPath(path.join(root,r.raw_path)));if(raw.subarray(0,5).toString()==='%PDF-'){
      const {getDocument}=await import('pdfjs-dist/legacy/build/pdf.mjs'); const doc=await getDocument({data:new Uint8Array(raw),useSystemFonts:true,isEvalSupported:false}).promise; const pages=[];
      for(let n=1;n<=doc.numPages;n++){const page=await doc.getPage(n),tc=await page.getTextContent({includeMarkedContent:false});let lines=[],lastY=null;for(const item of tc.items){if(!('str'in item))continue;const y=Math.round(item.transform?.[5]||0);if(lastY!==null&&Math.abs(y-lastY)>2)lines.push('\n');else if(lines.length&& !lines.at(-1).endsWith('\n'))lines.push(' ');lines.push(item.str);lastY=y;}pages.push(lines.join('').trim());}body=pages.join('\n\n---\n\n');conv='pdfjs-dist 4.10.38 / text-position extraction';
      const meta=await doc.getMetadata().catch(()=>null), pdfLang=meta?.info?.Language||meta?.metadata?.get?.('dc:language')||null,detected=languageByLexicon(body),expected=rep.language.toUpperCase(),declared=pdfLang?.split(/[-_]/)[0].toUpperCase()||null;
      if(detected&&detected!==expected)throw Error(`PDF text language mismatch: expected ${expected}, detected ${detected}`);
      if(!detected&&declared!==expected)throw Error(`PDF language could not be validated as ${expected}`);
      if(declared&&declared!==expected)languageNote=`\n- PDF metadata language note: declared \`${pdfLang}\`; extracted text independently matched \`${expected}\``;
      if(src.source_type==='commission_handbook'&&!body.toLowerCase().includes('visa code handbook'))throw Error(`PDF title/body does not identify the registered Commission Handbook`);
      if(src.source_id==='eu:62024cj0477'&&(!/deldwyn/i.test(body)||!/C-477\/24/i.test(body)))throw Error('PDF text does not identify Deldwyn (C-477/24)');
    }else{body=htmlText(raw.toString('utf8'),src);conv='Node.js built-in tokenizer / source-md-v3';}}
  body=body.replace(/[ \t]+\n/g,'\n').replace(/\n{3,}/g,'\n\n').trim();
  if(body.length<200)throw Error(`implausibly short conversion for ${r.representation_key}`);
  if(src.source_type==='charter'&&(/table\s+of\s+contents/i.test(body)||!/\bArticle\s+1\b/i.test(body)))throw Error('Charter body incomplete or table of contents');
  const label=r.content_type==='application/pdf'?'Source PDF':r.content_type==='application/json-page-content-set'?'Source API content-set':'Source HTML';
  return {text:`# ${src.title}\n\n- Source ID: \`${src.source_id}\`\n- Representation language: \`${rep.language}\`\n- Representation path: \`${rep.relative_path}\`\n- Official identity: \`${r.effective_identity}\`\n- Official source: ${r.retrieved_url}\n- ${label} SHA-256: \`${r.content_sha256}\`\n- Converter: \`${conv}\`${languageNote}\n\n> Deterministic text conversion of the official source. Verify quotations, article numbering, tables, footnotes, completeness, and legal effect against the linked official source before legal reliance.\n\n${body}\n` ,converter:conv};
}
async function main(){const args=process.argv.slice(2);if(!args.length||args.includes('--help')){console.log('node scripts/source-maintenance.mjs inventory [--language EN|SV] [--source-id ID ...] [--markdown] [--output FILE]\nnode scripts/source-maintenance.mjs scan --language EN|SV --output DIR [--manifest FILE] [--source-id ID ...] [--source-ids-file FILE] [--continue-on-error]\nnode scripts/source-maintenance.mjs convert --language EN|SV --output DIR [--manifest FILE] [--source-id ID ...] [--source-ids-file FILE]\nnode scripts/source-maintenance.mjs ack REPRESENTATION_KEY... --output DIR [--manifest FILE]');return;}
  const command=args.shift(),opts={},ids=[],sourceIds=[];for(let i=0;i<args.length;i++){const a=args[i];if(a==='--markdown'||a==='--continue-on-error')opts[a.slice(2)]=true;else if(a==='--source-id')sourceIds.push(args[++i]);else if(a.startsWith('--'))opts[a.slice(2)]=args[++i];else ids.push(a);}
  if(opts.language){opts.language=String(opts.language).toUpperCase();if(!['EN','SV'].includes(opts.language))throw Error('--language must be EN or SV for the registered core representations');}
  const fullManifest=await loadManifest(path.resolve(opts.manifest||DEFAULT_MANIFEST));
  if(opts['source-ids-file']){const listed=await readJson(path.resolve(opts['source-ids-file']));if(!Array.isArray(listed)||listed.some(x=>typeof x!=='string'))throw Error('--source-ids-file must contain a JSON array of source IDs');sourceIds.push(...listed);}
  const unknown=sourceIds.filter(id=>!fullManifest.sources.some(s=>s.source_id===id));if(unknown.length)throw Error(`unknown source ID(s): ${unknown.join(', ')}`);
  const selectedIds=new Set(sourceIds),manifest=selectedIds.size?{...fullManifest,sources:fullManifest.sources.filter(s=>selectedIds.has(s.source_id))}:fullManifest;
  if(command==='inventory'){const targets=manifest.sources.flatMap(src=>src.representations.filter(rep=>!opts.language||rep.language.toUpperCase()===opts.language).map(rep=>({source_id:src.source_id,representation_key:representationKey(src,rep),language:rep.language,relative_path:rep.relative_path,identity:ID_ALIAS[src.source_id]||src.identity,title:src.title,source_type:src.source_type,official_url:representationDocumentUrl(src,rep,URI_ALIAS[src.source_id]||ID_ALIAS[src.source_id]||src.identity),update_intent:rep.update_intent})));const text=opts.markdown?registry(manifest):JSON.stringify({manifest_version:manifest.manifest_version,logical_source_count:new Set(targets.map(t=>t.source_id)).size,representation_count:targets.length,representations:targets},null,2)+'\n';if(opts.output)await writeAtomic(path.resolve(opts.output),text);else process.stdout.write(text);return;}
  if(!opts.output)throw Error('--output is required');const root=path.resolve(opts.output);await mkdir(root,{recursive:true});const statePath=path.join(root,'state/source-state.json'),reportPath=path.join(root,`state/latest-observations${opts.language?`-${opts.language}`:''}.json`);
  if(command==='ack'){if(!ids.length)throw Error('ack requires reviewed representation keys');const state=normalizeState(await readJson(statePath).catch(()=>({version:1,sources:{},pending:{}})),manifest),known=new Set(manifest.sources.flatMap(s=>s.representations.map(r=>representationKey(s,r))));for(const id of ids){if(!known.has(id)||!state.pending?.[id])throw Error(`unknown representation key or no pending review: ${id}`);if(state.pending[id].change_state==='retrieval_failed')throw Error(`cannot acknowledge failed retrieval: ${id}`);}for(const id of ids)delete state.pending[id];state.acknowledged_at=now();await writeJson(statePath,state);const report=await readJson(reportPath).catch(()=>null);if(report){report.pending_review=Object.values(state.pending).sort((a,b)=>a.representation_key.localeCompare(b.representation_key));report.change_count=report.pending_review.length;report.acknowledged_at=state.acknowledged_at;await writeJson(reportPath,report);}console.log(JSON.stringify({acknowledged:[...new Set(ids)].sort(),still_pending:Object.keys(state.pending)},null,2));return;}
  if(command==='convert'){const report=await readJson(reportPath),sources=Object.fromEntries(manifest.sources.map(s=>[s.source_id,s])),reps=Object.fromEntries(manifest.sources.flatMap(s=>s.representations.map(r=>[representationKey(s,r),r]))),selected=report.observations.filter(r=>!opts.language||r.representation_language.toUpperCase()===opts.language),errors=[];for(const r of selected){try{const rep=reps[r.representation_key];if(!rep)throw Error(`unregistered representation ${r.representation_key}`);const result=await toMarkdown(sources[r.source_id],rep,r,root),dest=retrievedMarkdownPath(sources[r.source_id],rep);await writeAtomic(path.join(root,dest),result.text);r.markdown_path=dest;r.manifest_relative_path=rep.relative_path;r.markdown_content_status='retrieved_full_text_candidate_not_trust_promoted';r.markdown_sha256=sha(Buffer.from(result.text));r.converter=result.converter;}catch(e){errors.push({representation_key:r.representation_key,error:e.message});}}report.conversion_errors=errors;report.converted_count=selected.length-errors.length;await writeJson(reportPath,report);console.log(JSON.stringify({language:opts.language||'ALL',converted:report.converted_count,errors},null,2));if(errors.length)process.exitCode=1;return;}
  if(command!=='scan')throw Error(`unknown command: ${command}`);
  const prev=normalizeState(await readJson(statePath).catch(()=>({version:1,sources:{},pending:{}})),manifest),records=[],failures=[];
  const targets=manifest.sources.slice().sort((a,b)=>a.source_id.localeCompare(b.source_id)).flatMap(src=>src.representations.filter(rep=>!opts.language||rep.language.toUpperCase()===opts.language).map(rep=>({src,rep}))).sort((a,b)=>representationKey(a.src,a.rep).localeCompare(representationKey(b.src,b.rep)));
  for(const {src,rep} of targets){const key=representationKey(src,rep);try{records.push(await retrieve(src,rep,root,Number(opts.timeout||45000)));}catch(e){const failure={source_id:src.source_id,representation_key:key,language:rep.language,relative_path:rep.relative_path,error:e.message};failures.push(failure);if(!opts['continue-on-error'])break;}}
  const report=compare(records,manifest,prev);report.failures=failures;report.logical_source_count=new Set(targets.map(x=>x.src.source_id)).size;report.scope_count=targets.length;report.retrieved_count=records.length;
  const pending={...(prev.pending||{})};for(const r of records)if(pending[r.representation_key]?.change_state==='retrieval_failed')delete pending[r.representation_key];for(const e of report.events)pending[e.representation_key]=e;for(const f of failures){const old=pending[f.representation_key];if(old&&old.change_state!=='retrieval_failed')pending[f.representation_key]={...old,last_retrieval_error:f.error};else pending[f.representation_key]={source_id:f.source_id,representation_key:f.representation_key,language:f.language,relative_path:f.relative_path,change_state:'retrieval_failed',error:f.error,action:'retry_or_review_official_source_before_acknowledgement'};}report.pending_review=Object.values(pending).sort((a,b)=>a.representation_key.localeCompare(b.representation_key));report.change_count=report.pending_review.length;await writeJson(reportPath,report);
  const sources={...(prev.sources||{})};for(const r of records)sources[r.representation_key]=Object.fromEntries(['content_sha256','landing_sha256','current_consolidated_identity','official_dates','linked_celex','fetched_at'].map(k=>[k,r[k]]));
  await writeJson(statePath,{version:2,updated_at:now(),sources,pending});console.log(JSON.stringify({language:opts.language||'ALL',retrieved:records.length,scope_representations:targets.length,logical_sources:new Set(targets.map(x=>x.src.source_id)).size,changes:report.change_count,failures,report:reportPath},null,2));if(failures.length)process.exitCode=1;
}
export { representationKey, representationDocumentUrl, retrievedMarkdownPath, validatePathTaxonomy, normalizeState, declaredLanguage, validateRepresentationLanguage, validateDocumentIdentity, htmlText, currentVersion, isoDate, officialMetadataText, pageDateMetadata, extractOfficialDates, compare, loadManifest };
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href) main().catch(e=>{console.error(e.stack||e.message);process.exitCode=1;});
