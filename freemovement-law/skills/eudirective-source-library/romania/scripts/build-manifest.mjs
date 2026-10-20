#!/usr/bin/env node
// Compile the fixed Romanian source inventory from the included user-provided list.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const input = path.join(ROOT, 'references/source-list.md');
const output = path.join(ROOT, 'references/manifest.json');
const text = await readFile(input, 'utf8');
const sectionRows = [...text.matchAll(/^## (\d+)\. (.+)$/gm)];
const sourceRows = [];
const documentClassFor = sourceType => ({
  national_legislation: 'legislation',
  court_decision: 'case_law',
  official_guidance: 'guidance',
})[sourceType] || null;
const norm = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');
for (let si = 0; si < sectionRows.length; si++) {
  const number = Number(sectionRows[si][1]), section = sectionRows[si][2];
  const start = sectionRows[si].index + sectionRows[si][0].length;
  const end = sectionRows[si + 1]?.index ?? text.length;
  for (const line of text.slice(start, end).split(/\r?\n/).filter(x => /^- /.test(x))) {
    const bold = line.match(/^\s*- \*\*(.+?)\*\*/)?.[1];
    const detail = line.replace(/^\s*- /, '').replace(/^\*\*.+?\*\*\s*/, '').replace(/\s*\[[^\]]+\]\(https?:\/\/[^)]+\)/g, '').replace(/\s+/g, ' ').trim();
    const links = [...line.matchAll(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g)];
    for (const [index, match] of links.entries()) {
      const label = match[1], url = new URL(match[2]);
      const documentedPortalWsdl = url.href === 'http://portalquery.just.ro/query.asmx?WSDL';
      if (url.protocol !== 'https:' && !documentedPortalWsdl) throw Error(`non-HTTPS URL in source list without a documented official exception: ${url.href}`);
      const portalId = url.pathname.match(/^\/Public\/DetaliiDocument(?:Afis)?\/(\d+)\/?$/i)?.[1] || null;
      const portalFormKey = url.pathname.match(/^\/Public\/FormaPrintabila\/([A-Za-z0-9]+)\/?$/i)?.[1] || null;
      const scjRecordId = url.hostname === 'www.scj.ro' ? url.searchParams.get('customQuery[0].Value') : null;
      let source_type;
      if (number <= 6) source_type = 'national_legislation';
      else if (number <= 8 || number === 10) source_type = 'court_decision';
      else if (portalId || portalFormKey || /eviza\.mae\.ro|igi\.mai\.gov\.ro|politiadefrontiera\.ro/i.test(url.hostname)) source_type = portalId || portalFormKey ? 'portal_decision_or_act' : 'official_guidance';
      else if (number === 9 && /(^|\.)avp\.ro$|dataprotection\.ro|cncd\.ro/i.test(url.hostname)) source_type = 'official_guidance_directory';
      else source_type = 'discovery_repository';
      const monitor_only = source_type === 'discovery_repository' || source_type === 'official_guidance_directory';
      const source_quality = number === 10 ? url.hostname === 'www.scj.ro' || url.hostname === 'legislatie.just.ro' ? 'official_text' : url.hostname === 'apjgalati.ro' ? 'court_authored_digest' : 'reproduced_judgment' : null;
      const id = portalId ? `ro-portal-${portalId}` : portalFormKey ? `ro-portal-form-${portalFormKey.toLowerCase()}` : scjRecordId ? `ro-scj-${scjRecordId}` : `ro-${norm(url.hostname)}-${norm(url.pathname || 'home') || 'home'}`;
      const description = detail.replace(/\s+[—–]\s+/g, ' — ').replace(/[.;:]$/, '');
      const document_class = documentClassFor(source_type);
      sourceRows.push({
        id, title: bold || label, description, section_number: number, section_title: section,
        source_type, language: 'ro', url: url.href, retrieval_format: documentedPortalWsdl ? 'soap_wsdl' : 'html', portal_document_id: portalId, portal_form_key: portalFormKey, scj_record_id: scjRecordId,
        document_class,
        document_path: !monitor_only && document_class ? `documents/${document_class}/${id}.md` : null,
        citation_hint: bold || null, monitor_only,
        search_title: bold || null,
        source_quality,
        source_note: documentedPortalWsdl ? 'Officially documented public WSDL for case and hearing queries. It is not a complete published-judgments feed; its endpoint is HTTP-only, so only this exact official WSDL URL is permitted over HTTP.' : source_quality === 'court_authored_digest' ? 'Court-authored digest hosted by a professional association; not the complete official judgment.' : source_quality === 'reproduced_judgment' ? 'Third-party reproduction; not verified against the official original and not an official court publication.' : label === 'Decision' || label === 'Judgment' ? 'Court decision; preserve admission/inadmissibility status stated in the supplied inventory.' : null
      });
    }
  }
}
const duplicates = sourceRows.filter((x, i) => sourceRows.findIndex(y => y.id === x.id) !== i);
if (duplicates.length) throw Error(`duplicate source IDs: ${duplicates.map(x => x.id).join(', ')}`);
const hosts = [...new Set(sourceRows.filter(x => x.source_quality !== 'reproduced_judgment' && x.source_quality !== 'court_authored_digest').map(x => new URL(x.url).hostname))].sort();
const secondaryHosts = [...new Set(sourceRows.filter(x => x.source_quality === 'reproduced_judgment' || x.source_quality === 'court_authored_digest').map(x => new URL(x.url).hostname))].sort();
const manifest = {
  manifest_version: '0.1.0',
  pack: 'romania-national-legal-sources',
  inventory_source: 'references/source-list.md',
  inventory_research_date: '2026-10-11',
  scope: 'Romanian national legislation, Romanian court decisions, and Romanian authority guidance/repositories listed in the supplied inventory. EU and CJEU source texts are excluded.',
  official_hosts: hosts,
  secondary_hosts: secondaryHosts,
  source_count: sourceRows.length,
  documents: sourceRows
};
await mkdir(path.dirname(output), { recursive: true });
await writeFile(output, JSON.stringify(manifest, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ source_count: sourceRows.length, source_types: Object.fromEntries([...new Set(sourceRows.map(x => x.source_type))].map(t => [t, sourceRows.filter(x => x.source_type === t).length])), monitor_only: sourceRows.filter(x => x.monitor_only).length, output }, null, 2));
