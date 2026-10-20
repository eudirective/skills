#!/usr/bin/env node
// Compare the official-source Markdown outputs with Swedish transcriptions in the source ZIP.
import { readFile, readdir, writeFile } from 'node:fs/promises';
import { inflateRawSync } from 'node:zlib';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { projectTempPath } from '../../runtime-storage.mjs';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const zipPath = process.argv[2] || 'H:\\Downloads\\sweden\\sweden legal pack.zip';
const manifest = JSON.parse(await readFile(path.join(ROOT, 'manifest.json'), 'utf8'));
const zip = await readFile(zipPath);
function findEocd(b) {
  for (let p = b.length - 22; p >= Math.max(0, b.length - 65558); p--) if (b.readUInt32LE(p) === 0x06054b50) return p;
  throw new Error('ZIP end-of-central-directory record not found');
}
function zipEntries(b) {
  const end = findEocd(b), count = b.readUInt16LE(end + 10); let p = b.readUInt32LE(end + 16); const entries = [];
  for (let i = 0; i < count; i++) {
    if (b.readUInt32LE(p) !== 0x02014b50) throw new Error(`Bad ZIP central directory entry at ${p}`);
    const flags = b.readUInt16LE(p + 8), method = b.readUInt16LE(p + 10), csize = b.readUInt32LE(p + 20), nlen = b.readUInt16LE(p + 28), elen = b.readUInt16LE(p + 30), clen = b.readUInt16LE(p + 32), offset = b.readUInt32LE(p + 42);
    const name = b.subarray(p + 46, p + 46 + nlen).toString(flags & 0x800 ? 'utf8' : 'latin1');
    if (!name.endsWith('/') && name.toLowerCase().endsWith('.md')) {
      const ln = b.readUInt16LE(offset + 26), le = b.readUInt16LE(offset + 28), start = offset + 30 + ln + le, packed = b.subarray(start, start + csize);
      const data = method === 0 ? packed : method === 8 ? inflateRawSync(packed) : null;
      if (!data) throw new Error(`Unsupported ZIP compression method ${method} in ${name}`);
      entries.push({ name, text: data.toString('utf8') });
    }
    p += 46 + nlen + elen + clen;
  }
  return entries;
}
const archive = zipEntries(zip).filter(x => /^(swedish_laws_md_verified|swedish_laws_md_verified_batch[234])\//.test(x.name) && !/VERIFICATION|SHA256SUMS|Detaljer för valt avgörande/i.test(x.name));
function keyFor(row, text, name = '') {
  if (row.sfs) return text.slice(0, 5000).match(/SFS\s*(?:nr\s*[:.]?\s*)?(\d{4})\s*[:\-]\s*(\d{1,4})/i)?.slice(1).join(':') || null;
  if (row.migrfs) {
    const file = name.toLowerCase().split('/').pop();
    const legacy = file.match(/^migrfs0?5[_-]?2011\.md$/i);
    if (legacy) return '5/2011';
    const byName = file.match(/^migrfs[_-]?(\d{4})[_-](\d+)\.md$/i);
    if (byName) return `${byName[1]}:${Number(byName[2])}`;
    const m = text.slice(0, 2500).match(/MIGRFS\s*(\d{1,4})\s*[:/]\s*(\d{4})|MIGRFS\s*(\d{4})\s*[:/]\s*(\d{1,4})/i);
    if (!m) return null;
    return m[1] ? `${m[1]}/${m[2]}` : `${m[3]}:${m[4]}`;
  }
  if (row.case_number) return text.slice(0, 5000).match(/UM\s*\d+\s*[-‐‑–]\s*\d+/i)?.[0].toUpperCase().replace(/\s+/g, '').replace(/[‐‑–]/g, '-') || null;
  return null;
}
function expectedKey(row) {
  if (row.sfs) return row.sfs;
  if (row.migrfs) return row.migrfs;
  if (row.case_number) return row.case_number.toUpperCase().replace(/\s+/g, '');
}
function norm(s) {
  return s.normalize('NFKC').toLocaleLowerCase('sv')
    .replace(/<!--\s*(?:pdf\s*)?page\s+\d+\s*-->/gi, ' ')
    .replace(/^---[\s\S]*?---\s*/m, ' ')
    .replace(/```(?:text)?/gi, ' ')
    .replace(/\bpage\s+\d+\b/gi, ' ')
    .replace(/[^\p{L}\p{N}]+/gu, ' ').trim().replace(/\s+/g, ' ');
}
function similarity(a, b) {
  const aw = norm(a).split(' '), bw = norm(b).split(' ');
  const grams = xs => { const s = new Set(); for (let i = 0; i + 3 < xs.length; i++) s.add(xs.slice(i, i + 4).join(' ')); return s; };
  const ag = grams(aw), bg = grams(bw); let common = 0; for (const x of ag) if (bg.has(x)) common++;
  return ag.size + bg.size ? Number((2 * common / (ag.size + bg.size)).toFixed(4)) : 0;
}
const files = [];
async function walk(dir) { for (const e of await readdir(dir, { withFileTypes: true })) { const p = path.join(dir, e.name); if (e.isDirectory()) await walk(p); else if (p.endsWith('.md')) files.push(p); } }
await walk(path.join(ROOT, 'documents'));
const outputs = [];
for (const row of manifest.sources) {
  const rel = `${row.type === 'sfs-amendment' ? 'amendments' : row.type === 'sfs' ? 'statutes' : row.type === 'migrfs' ? 'migrfs' : 'case-law'}/${row.id.toLowerCase().replace(/[^a-z0-9._-]+/g, '-')}.md`;
  const acceptedPath = path.join(ROOT, 'documents', rel), pendingPath = projectTempPath(path.join(ROOT, 'pending', rel));
  let outputPath = acceptedPath;
  try { await readFile(pendingPath); outputPath = pendingPath; } catch {}
  let retrieved = ''; try { retrieved = await readFile(outputPath, 'utf8'); } catch { outputPath = null; }
  const archiveMatches = archive.filter(x => keyFor(row, x.text, x.name)?.toLocaleLowerCase('sv') === expectedKey(row)?.toLocaleLowerCase('sv'));
  const originalEntry = [...archiveMatches].sort((a, b) => b.text.length - a.text.length)[0];
  const original = originalEntry?.text || '';
  const a = norm(original), b = norm(retrieved);
  const marker = s => s.match(/Ändrad\s*:?\s*t\.o\.m\.\s*SFS\s*\d{4}:\d{1,4}/i)?.[0] || s.match(/t\.o\.m\.\s*SFS\s*\d{4}:\d{1,4}/i)?.[0] || null;
  outputs.push({
    id: row.id, label: row.label, output_file: outputPath ? path.relative(ROOT, outputPath).replaceAll('\\', '/') : null,
    archive_files: archiveMatches.map(x => x.name), archive_duplicate_count: archiveMatches.length,
    comparison_source_file: originalEntry?.name || null,
    retrieved_found: !!outputPath, archive_found: archiveMatches.length > 0,
    exact_normalized_text_match: !!original && !!retrieved && a === b,
    four_word_shingle_dice: original && retrieved ? similarity(original, retrieved) : null,
    archive_characters_normalized: a.length, retrieved_characters_normalized: b.length,
    archive_amended_through: marker(original), retrieved_amended_through: marker(retrieved),
    result: !retrieved ? 'missing_retrieval' : !original ? 'missing_archive_match' : a === b ? 'exact_text' : 'text_differs'
  });
}
const report = {
  schema_version: 1, compared_at: new Date().toISOString(), zip_file: zipPath,
  method: 'Normalize Unicode, strip Markdown page markers/front matter, then compare letter-number text; four-word shingle Dice is a text-overlap indicator, not an accuracy score.',
  counts: {
    manifest: outputs.length, retrieved: outputs.filter(x => x.retrieved_found).length,
    archive_matched: outputs.filter(x => x.archive_found).length,
    exact_normalized_text: outputs.filter(x => x.exact_normalized_text_match).length,
    differing_text: outputs.filter(x => x.result === 'text_differs').length,
    missing: outputs.filter(x => x.result === 'missing_archive_match' || x.result === 'missing_retrieval').length
  },
  items: outputs
};
const reportPath = projectTempPath(path.join(ROOT, 'work/pack-comparison.json'));
await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ report: reportPath, counts: report.counts, items: outputs.map(x => ({ id: x.id, result: x.result, exact: x.exact_normalized_text_match, overlap: x.four_word_shingle_dice, archive: x.archive_files[0] || null, archive_duplicates: x.archive_duplicate_count, archive_amended_through: x.archive_amended_through, retrieved_amended_through: x.retrieved_amended_through })) }, null, 2));
