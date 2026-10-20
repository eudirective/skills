import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { atomicProjectWriteSync } from '../runtime-storage.mjs';

const root = path.dirname(fileURLToPath(import.meta.url));
const indexPath = path.join(root, 'retrieval-index.json');
const rows = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
const moved = [];
let coreCount = 0;

function sha256(file) {
  return createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function corePath(row) {
  if (row.source_id === 'eu:visa-code-handbook-i-2024') {
    return `core/guidance/handbooks/${path.posix.basename(row.library_relative_path)}`;
  }
  const match = row.manifest_relative_path.match(/^sources\/(eu|case_law\/notes|case_law\/full_text|guidance\/notes)\//);
  if (!match) throw new Error(`No core category for ${row.manifest_relative_path}`);
  return `core/${match[1]}/${path.posix.basename(row.library_relative_path)}`;
}

for (const row of rows) {
  if (row.library_relative_path.startsWith('pending-invalid/')) {
    if (row.language !== 'SV' || row.library_content_state !== 'invalid_nonmatching_payload_pending') {
      throw new Error(`Unexpected pending row: ${row.source_id}/${row.language}`);
    }
    continue;
  }
  if (row.language !== 'EN') throw new Error(`Non-English content cannot enter core: ${row.source_id}/${row.language}`);
  coreCount++;
  const from = path.join(root, row.library_relative_path);
  const toRelative = corePath(row);
  const to = path.join(root, toRelative);
  if (!fs.existsSync(from)) throw new Error(`Missing input file: ${row.library_relative_path}`);
  if (sha256(from) !== row.markdown_sha256) throw new Error(`Input hash mismatch: ${row.library_relative_path}`);
  if (from !== to && fs.existsSync(to)) throw new Error(`Destination already exists: ${toRelative}`);
  if (from !== to) moved.push({ from, to, fromRelative: row.library_relative_path, toRelative });
  row.relative_path = toRelative;
  row.library_relative_path = toRelative;
}

if (coreCount !== 46) throw new Error(`Expected 46 English EU core files, found ${coreCount}`);

try {
  for (const item of moved) {
    fs.mkdirSync(path.dirname(item.to), { recursive: true });
    fs.renameSync(item.from, item.to);
  }
  for (const row of rows) {
    const actual = sha256(path.join(root, row.library_relative_path));
    if (actual !== row.markdown_sha256) throw new Error(`Post-move hash mismatch: ${row.library_relative_path}`);
  }
  atomicProjectWriteSync(indexPath, `${JSON.stringify(rows, null, 2)}\n`);
} catch (error) {
  for (const item of moved.slice().reverse()) {
    if (fs.existsSync(item.to)) {
      fs.mkdirSync(path.dirname(item.from), { recursive: true });
      fs.renameSync(item.to, item.from);
    }
  }
  throw error;
}

console.log(`Verified ${coreCount} English EU core files; moved ${moved.length} into place, including the Visa Code Handbook under guidance/handbooks, and left the pending invalid entry outside core.`);
