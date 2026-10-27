#!/usr/bin/env node
import {readFileSync, readdirSync, statSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve, join, dirname, relative, sep} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifestRel = 'skills/eudirective-core/references/component-manifest.json';
const manifest = JSON.parse(readFileSync(join(root, manifestRel), 'utf8'));
const plugin = JSON.parse(readFileSync(join(root, 'plugin.json'), 'utf8'));
const legacy = JSON.parse(readFileSync(join(root, '.codex-plugin/plugin.json'), 'utf8'));
const fail = message => { throw Error(message); };
if (plugin.name !== 'freemovement-law' || plugin.version !== legacy.version || manifest.plugin_version !== plugin.version) {
  fail('plugin metadata and component manifest disagree');
}
if (manifest.component_id !== 'eu-core' || !manifest.skill_versions || !manifest.distributed_files) {
  fail('invalid EU-core component manifest');
}
const skills = {};
for (const entry of readdirSync(join(root, 'skills'), {withFileTypes: true})) {
  if (!entry.isDirectory()) continue;
  const skillFile = join(root, 'skills', entry.name, 'SKILL.md');
  let content;
  try { content = readFileSync(skillFile, 'utf8'); } catch { continue; }
  const version = content.match(/^- Current version: `(\d+\.\d+\.\d+)`/m)?.[1]
    ?? content.match(/^\*\*Skill version:\*\* (\d+\.\d+\.\d+)/m)?.[1]
    ?? content.match(/^Skill version: (\d+\.\d+\.\d+)/m)?.[1];
  if (version) skills[entry.name] = version;
}
for (const [name, version] of Object.entries(manifest.skill_versions)) {
  if (skills[name] !== version) fail('skill version mismatch: ' + name);
}
if (Object.keys(skills).length !== Object.keys(manifest.skill_versions).length) fail('component manifest skill list is incomplete');
const expected = manifest.distributed_files;
if (!expected || typeof expected !== 'object' || !/^[a-f0-9]{64}$/.test(manifest.distributed_fingerprint ?? '')) {
  fail('invalid distributed-file manifest');
}
for (const [rel, digest] of Object.entries(expected)) {
  if (typeof rel !== 'string' || rel.startsWith('/') || rel.split('/').includes('..')) fail('unsafe manifest path');
  if (!/^[a-f0-9]{64}$/.test(digest)) fail('invalid manifest digest: ' + rel);
  let bytes;
  try { bytes = readFileSync(join(root, rel)); } catch { fail('distributed file missing: ' + rel); }
  const actualDigest = createHash('sha256').update(bytes).digest('hex');
  if (actualDigest !== digest) fail('distributed file mismatch: ' + rel);
}
if (process.argv.includes('--verify')) console.log('Verified freemovement-law component manifest');
else fail('expected --verify');
