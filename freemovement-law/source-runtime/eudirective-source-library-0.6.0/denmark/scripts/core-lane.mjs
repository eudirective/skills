#!/usr/bin/env node
// Run the shared EU/CJEU source maintenance only for source IDs in this pack.
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CORE = path.resolve(ROOT, '../../eudirective-core-work/eudirective-core');
const mode = process.argv[2] || '--check';
const idsFile = path.join(ROOT, 'references/core-source-ids.json');
const output = path.resolve(ROOT, '../../temp/eudirective-source-library-0.6.0/denmark/core-lane');
if (!['--check', '--sync'].includes(mode)) throw Error('usage: node scripts/core-lane.mjs --check|--sync');
const run = args => {
  const res = spawnSync(process.execPath, ['scripts/source-maintenance.mjs', ...args], { cwd: CORE, stdio: 'inherit' });
  if (res.error) throw res.error;
  return res.status;
};
const scanStatus = run(['scan', '--language', 'EN', '--output', output, '--source-ids-file', idsFile, '--continue-on-error']);
const convertStatus = mode === '--sync' ? run(['convert', '--language', 'EN', '--output', output, '--source-ids-file', idsFile]) : 0;
if (scanStatus !== 0 || convertStatus !== 0) throw Error(`core EU/CJEU updater scan=${scanStatus}, convert=${convertStatus}; inspect its report for per-source failures`);
