#!/usr/bin/env node
// Bundle only retrieval code and registered-source metadata for fresh installs.
import { cp, mkdir, readdir, rm, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const pluginRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const projectRoot = path.resolve(pluginRoot, '../../..');
const bundleRoot = path.join(pluginRoot, 'source-runtime');
const librarySource = path.join(projectRoot, 'eudirective-source-library-0.6.0');
const coreSource = path.join(projectRoot, 'eudirective-core-work', 'eudirective-core');
const excludedDirectories = new Set([
  'accepted', 'archive', 'cache', 'core', 'documents', 'evals', 'evaluations',
  'fixtures', 'node_modules', 'pending', 'raw', 'scratch', 'staging', 'temp',
  'work',
]);
const allowedExtensions = new Set(['.json', '.md', '.mjs', '.pem']);

function safeTarget(target) {
  const resolved = path.resolve(target);
  if (path.dirname(resolved) !== pluginRoot || path.basename(resolved) !== 'source-runtime') {
    throw new Error(`Refusing to replace unexpected bundle path: ${resolved}`);
  }
  return resolved;
}

async function copyFiltered(source, destination) {
  const entries = await readdir(source, { withFileTypes: true });
  await mkdir(destination, { recursive: true });
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name, 'en'))) {
    if (entry.isDirectory()) {
      if (excludedDirectories.has(entry.name.toLowerCase())) continue;
      await copyFiltered(path.join(source, entry.name), path.join(destination, entry.name));
      continue;
    }
    if (!entry.isFile()) continue;
    if (!allowedExtensions.has(path.extname(entry.name).toLowerCase())) continue;
    if (/^(latest-|state\.)/i.test(entry.name)) continue;
    await cp(path.join(source, entry.name), path.join(destination, entry.name));
  }
}

if (!(await stat(librarySource).catch(() => null)) || !(await stat(coreSource).catch(() => null))) {
  throw new Error('Source library or eudirective core source-maintenance directory is missing.');
}

const target = safeTarget(bundleRoot);
await rm(target, { recursive: true, force: true });
await mkdir(target, { recursive: true });
await cp(path.join(projectRoot, 'runtime-storage.mjs'), path.join(target, 'runtime-storage.mjs'));
await copyFiltered(librarySource, path.join(target, 'eudirective-source-library-0.6.0'));

const runtimeCore = path.join(target, 'eudirective-core-work', 'eudirective-core');
for (const script of [
  'source-maintenance.mjs',
  'guidance-source-maintenance.mjs',
  'national-language-maintenance.mjs',
  'visa-handbook-language-reference.mjs',
  'visa-handbook-register.mjs',
]) {
  await cp(path.join(coreSource, 'scripts', script), path.join(runtimeCore, 'scripts', script));
}
// The source-library bundle is the only shipped location for source text. The
// skill's pinned compatibility representations are copied into its
// compatibility/ folder above, not duplicated under the runtime scripts.

const trainingData = path.join(librarySource, 'hungary', 'hun.traineddata');
if (await stat(trainingData).catch(() => null)) {
  await cp(trainingData, path.join(target, 'eudirective-source-library-0.6.0', 'hungary', 'hun.traineddata'));
}

console.log(JSON.stringify({ bundle: target, scope: 'scripts, source registries, manifests, and Hungary OCR data; retrieved documents and state are excluded' }, null, 2));
