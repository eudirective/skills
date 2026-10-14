#!/usr/bin/env node
// Local-only bridge from the eudirective plugin to this machine's approved source packs.
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { cp, mkdir, readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const PLUGIN_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PLUGIN_NAME = 'freemovement-law';
const PLUGIN_PARENT = path.dirname(PLUGIN_ROOT);
const VERSION_CACHE_INSTALL = path.basename(PLUGIN_PARENT).toLowerCase() === PLUGIN_NAME;
const INSTALL_HOME = VERSION_CACHE_INSTALL ? PLUGIN_PARENT : PLUGIN_ROOT;
const DATA_ROOT = path.join(INSTALL_HOME, 'data');
const BUNDLE_ROOT = path.join(PLUGIN_ROOT, 'source-runtime');
const LIBRARY = path.join(DATA_ROOT, 'eudirective-source-library-0.6.0');
const CORE = path.join(DATA_ROOT, 'eudirective-core-work', 'eudirective-core');
const REQUIRED_DEPENDENCIES = ['pdfjs-dist', 'tesseract.js', '@tesseract.js-data/hun'];
let readyPromise;

const packs = {
  'eu-core': {
    title: 'EU core source pack', scope: 'Registered English EU core sources.', actions: ['inventory', 'check', 'convert'],
    run(action, input) {
      const script = path.join(CORE, 'scripts', 'source-maintenance.mjs');
      const manifest = path.join(LIBRARY, 'compatibility', 'core-source-pack', 'core-source-pack-0.6.1', 'core-source-pack-manifest-0.6.0.json');
      if (action === 'inventory') return [script, ['inventory', '--language', 'EN', '--manifest', manifest]];
      if (action === 'check') return [script, ['scan', '--language', 'EN', '--output', path.join(LIBRARY, 'core'), '--manifest', manifest, '--continue-on-error', ...(input.source_id ? ['--source-id', input.source_id] : [])]];
      return [script, ['convert', '--language', 'EN', '--output', path.join(LIBRARY, 'core'), '--manifest', manifest, ...(input.source_id ? ['--source-id', input.source_id] : [])]];
    }
  },
  'eu-core-additions': {
    title: 'EU core additions', scope: 'Separately registered EU core expansion sources.', actions: ['sync', 'verify'],
    run(action) { return [path.join(LIBRARY, 'sync-core-expansion.mjs'), [action]]; }
  },
  'eu-core-language-mirror': {
    title: 'EU core national-language mirror', scope: 'Hungarian, Swedish, Danish, and Romanian versions of the 23 expansion sources.', actions: ['sync', 'verify', 'ack'],
    run(action, input) {
      const script = path.join(LIBRARY, 'sync-core-expansion-languages.mjs');
      if (action === 'ack') return [script, ['--ack', input.language, input.source_id]];
      if (action === 'verify') return [script, ['verify', '--language', input.language]];
      return [script, ['sync', '--language', input.language]];
    }
  },
  'eu-core-language-legacy': {
    title: 'EU core language availability check', scope: 'Official HU, SV, DA, or RO versions across the registered English core inventory.', actions: ['check', 'ack'],
    run(action, input) {
      const script = path.join(CORE, 'scripts', 'national-language-maintenance.mjs');
      const args = ['--language', input.language, '--library', LIBRARY];
      if (action === 'ack') args.push('--ack', input.source_id);
      return [script, args];
    }
  },
  'eu-guidance': {
    title: 'EU guidance sources', scope: 'Registered EU guidance sources.', actions: ['sync', 'verify', 'ack'],
    run(action, input) { return [path.join(LIBRARY, 'sync-guidance.mjs'), [action, input.source_id || '']]; }
  },
  'denmark': {
    title: 'Denmark national sources', scope: 'Danish official law and case-law pack.', actions: ['check', 'sync', 'discover', 'ack'],
    run(action, input) {
      const flags = { check: '--check', sync: '--sync', discover: '--discover', ack: '--ack' };
      return [path.join(LIBRARY, 'denmark', 'scripts', 'sync-pack.mjs'), [flags[action], ...(action === 'ack' ? [input.source_id] : [])]];
    }
  },
  'sweden': {
    title: 'Sweden national sources', scope: 'Swedish official law and case-law pack.', actions: ['check', 'sync', 'discover', 'verify', 'ack'],
    run(action, input) {
      const flags = { check: '--check', sync: '--sync', discover: '--discover', verify: '--verify', ack: '--ack' };
      return [path.join(LIBRARY, 'sweden', 'sync.mjs'), [flags[action], ...(action === 'ack' ? [input.source_id] : [])]];
    }
  },
  'hungary': {
    title: 'Hungary national sources', scope: 'Hungarian law and official transparency/statistical publication pack.', actions: ['check', 'sync', 'discover', 'verify', 'reconvert'],
    run(action) {
      const flags = { check: '--check', sync: '--sync', discover: '--discover', verify: '--verify', reconvert: '--reconvert' };
      return [path.join(LIBRARY, 'hungary', 'scripts', 'sync-hungary.mjs'), [flags[action]]];
    }
  },
  'romania': {
    title: 'Romania national sources', scope: 'Romanian legislation, official statistics, and case-law pack.', actions: ['check', 'sync', 'discover', 'ack'],
    run(action, input) {
      const flags = { check: '--check', sync: '--sync', discover: '--discover', ack: '--ack' };
      return [path.join(LIBRARY, 'romania', 'scripts', 'sync-romania.mjs'), [flags[action], ...(action === 'ack' ? [input.source_id] : [])]];
    }
  },
  'denmark-guidance': {
    title: 'Denmark guidance sources', scope: 'Registered Danish guidance sources.', actions: ['sync', 'verify', 'ack'],
    run(action, input) { return [path.join(LIBRARY, 'denmark', 'scripts', 'sync-guidance.mjs'), [action, input.source_id || '']]; }
  },
  'sweden-guidance': {
    title: 'Sweden guidance sources', scope: 'Registered Swedish guidance sources.', actions: ['sync', 'verify', 'ack'],
    run(action, input) { return [path.join(LIBRARY, 'sweden', 'sync-guidance.mjs'), [action, input.source_id || '']]; }
  },
  'swedish-recommendation': {
    title: 'Swedish Commission Recommendation 2013/461/EU representation', scope: 'Official Swedish XHTML representation in the Sweden EU mirror.', actions: ['sync', 'verify'],
    run(action) { return [path.join(LIBRARY, 'sync-swedish-recommendation.mjs'), [action]]; }
  },
  'romania-guidance': {
    title: 'Romania guidance sources', scope: 'Registered Romanian guidance sources.', actions: ['sync', 'verify', 'ack'],
    run(action, input) { return [path.join(LIBRARY, 'romania', 'scripts', 'sync-guidance.mjs'), [action, input.source_id || '']]; }
  },
  '2020-visa-handbook': {
    title: '2020 Visa Code handbook language reference', scope: 'Registered multilingual 2020 handbook edition.', actions: ['inventory', 'sync', 'verify'],
    run(action) { return [path.join(CORE, 'scripts', 'visa-handbook-language-reference.mjs'), [action]]; }
  }
};

const languages = new Set(['HU', 'SV', 'DA', 'RO']);
function validate(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Tool arguments must be an object.');
  const pack_id = String(input.pack_id || ''), action = String(input.action || '');
  if (!packs[pack_id]) throw new Error(`Unknown pack_id: ${pack_id}`);
  if (!packs[pack_id].actions.includes(action)) throw new Error(`Action ${action || '(empty)'} is unavailable for ${pack_id}.`);
  const language = input.language == null ? '' : String(input.language).toUpperCase();
  if (language && !languages.has(language) && !(pack_id === 'eu-core' && language === 'EN')) throw new Error('language must be EN, HU, SV, DA, or RO as applicable.');
  const source_id = input.source_id == null ? '' : String(input.source_id);
  if (source_id && !/^[A-Za-z0-9:._-]{1,200}$/.test(source_id)) throw new Error('source_id has invalid characters.');
  if (['eu-core-language-mirror', 'eu-core-language-legacy'].includes(pack_id) && !language) throw new Error('language is required for this pack.');
  if (action === 'ack' && !source_id) throw new Error('source_id is required for acknowledgement.');
  return { pack_id, action, language, source_id };
}

async function dependencyVersions(root) {
  const versions = {};
  for (const name of REQUIRED_DEPENDENCIES) {
    const manifest = path.join(root, 'node_modules', ...name.split('/'), 'package.json');
    try { versions[name] = JSON.parse(await readFile(manifest, 'utf8')).version; }
    catch { versions[name] = null; }
  }
  return versions;
}

async function dependencyRoot() {
  const candidates = VERSION_CACHE_INSTALL ? [INSTALL_HOME] : [PLUGIN_ROOT, path.dirname(PLUGIN_ROOT), path.dirname(path.dirname(PLUGIN_ROOT)), path.dirname(path.dirname(path.dirname(PLUGIN_ROOT)))];
  for (const candidate of candidates) {
    const versions = await dependencyVersions(candidate);
    if (versions['pdfjs-dist'] === '4.10.38' && versions['tesseract.js'] === '7.0.0' && versions['@tesseract.js-data/hun'] === '1.0.0') return candidate;
  }
  return VERSION_CACHE_INSTALL ? INSTALL_HOME : PLUGIN_ROOT;
}

async function mergeRuntimeBundle(source, destination) {
  await mkdir(destination, { recursive: true });
  for (const entry of await readdir(source, { withFileTypes: true })) {
    const from = path.join(source, entry.name), to = path.join(destination, entry.name);
    if (entry.isDirectory()) {
      await mergeRuntimeBundle(from, to);
    } else if (entry.isFile()) {
      if (/^national-language-state-/i.test(entry.name) && existsSync(to)) continue;
      await cp(from, to, { force: true });
    }
  }
}

async function ensureReady() {
  if (!readyPromise) readyPromise = (async () => {
    if (Number(process.versions.node.split('.')[0]) < 20) throw new Error(`Node.js 20 or later is required for source retrieval; this host runs ${process.versions.node}.`);
    if (!existsSync(path.join(BUNDLE_ROOT, 'runtime-storage.mjs'))) throw new Error(`Bundled source runtime is missing from ${BUNDLE_ROOT}. Rebuild the plugin package.`);
    await mkdir(DATA_ROOT, { recursive: true });
    await mergeRuntimeBundle(BUNDLE_ROOT, DATA_ROOT);
    if (!existsSync(path.join(LIBRARY, 'core-source-pack-manifest-0.7.0.json')) || !existsSync(path.join(CORE, 'scripts', 'source-maintenance.mjs'))) {
      throw new Error(`Bundled source runtime did not initialize in ${DATA_ROOT}.`);
    }

    const depsRoot = await dependencyRoot();
    const versions = await dependencyVersions(depsRoot);
    if (versions['pdfjs-dist'] !== '4.10.38' || versions['tesseract.js'] !== '7.0.0' || versions['@tesseract.js-data/hun'] !== '1.0.0') {
      const packageFile = path.join(PLUGIN_ROOT, 'package.json');
      const lockFile = path.join(PLUGIN_ROOT, 'package-lock.json');
      if (!existsSync(packageFile) || !existsSync(lockFile)) throw new Error('Pinned runtime dependencies are not installed, and the plugin package is missing package.json or package-lock.json.');
      await mkdir(depsRoot, { recursive: true });
      if (depsRoot !== PLUGIN_ROOT) {
        await cp(packageFile, path.join(depsRoot, 'package.json'));
        await cp(lockFile, path.join(depsRoot, 'package-lock.json'));
      }
      const npmCandidates = [
        process.env.npm_execpath,
        path.join(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js'),
        path.resolve(path.dirname(process.execPath), '..', 'lib', 'node_modules', 'npm', 'bin', 'npm-cli.js')
      ].filter(Boolean);
      const npmCli = npmCandidates.find(candidate => candidate.toLowerCase().endsWith('.js') && existsSync(candidate));
      if (!npmCli) throw new Error('npm CLI was not found beside Node.js; install Node.js 20+ with npm and retry.');
      const install = spawnSync(process.execPath, [npmCli, 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], {
        cwd: depsRoot, encoding: 'utf8', windowsHide: true,
        env: { ...process.env, npm_config_cache: path.join(DATA_ROOT, 'temp', 'npm-cache') },
        timeout: 20 * 60 * 1000, maxBuffer: 8 * 1024 * 1024
      });
      if (install.error || install.status !== 0) {
        const detail = [install.stdout?.trim(), install.stderr?.trim(), install.error?.message].filter(Boolean).join('\n');
        throw new Error(`Could not install the plugin's pinned Node dependencies at ${depsRoot}. Run npm ci there and retry. ${detail}`);
      }
      const installed = await dependencyVersions(depsRoot);
      if (installed['pdfjs-dist'] !== '4.10.38' || installed['tesseract.js'] !== '7.0.0' || installed['@tesseract.js-data/hun'] !== '1.0.0') throw new Error(`Pinned Node dependencies did not install correctly at ${depsRoot}.`);
    }
  })();
  try { await readyPromise; }
  catch (error) { readyPromise = null; throw error; }
}

async function execute(input) {
  const args = validate(input);
  await ensureReady();
  const [script, scriptArgs] = packs[args.pack_id].run(args.action, args);
  const safeRoot = p => p.startsWith(LIBRARY + path.sep) || p.startsWith(CORE + path.sep);
  if (!safeRoot(script) || !existsSync(script)) throw new Error(`Registered source script is missing or outside the allowed roots: ${script}`);
  const result = spawnSync(process.execPath, [script, ...scriptArgs.filter(Boolean)], {
    cwd: DATA_ROOT, encoding: 'utf8', windowsHide: true,
    timeout: 30 * 60 * 1000, maxBuffer: 16 * 1024 * 1024
  });
  if (result.error) throw new Error(`Source operation could not start: ${result.error.message}`);
  const output = [result.stdout?.trim(), result.stderr?.trim()].filter(Boolean).join('\n');
  return { content: [{ type: 'text', text: JSON.stringify({ pack_id: args.pack_id, action: args.action, exit_code: result.status, output }) }], isError: result.status !== 0 };
}

const tools = [
  { name: 'list_source_packs', description: 'List the fixed, source-scoped official legal and guidance packs and actions.', inputSchema: { type: 'object', properties: {}, additionalProperties: false } },
  {
    name: 'run_source_pack_action',
    description: 'Run a fixed action from a bundled allowlisted pack. Source code and registries initialize into a persistent plugin data folder on first use; pinned Node dependencies are bootstrapped in the plugin runtime location when missing. check/sync/discover use registered official publishers; verify replays local integrity checks where available; convert writes Markdown for EU core sources; ack accepts one pending source candidate and requires source_id.',
    inputSchema: {
      type: 'object', properties: {
        pack_id: { type: 'string', enum: Object.keys(packs) },
        action: { type: 'string', enum: [...new Set(Object.values(packs).flatMap(p => p.actions))] },
        language: { type: 'string', enum: ['EN', 'HU', 'SV', 'DA', 'RO'] },
        source_id: { type: 'string', description: 'Registered source ID; required for ack.' }
      }, required: ['pack_id', 'action'], additionalProperties: false
    }
  }
];

function send(message) { process.stdout.write(`${JSON.stringify(message)}\n`); }
function response(id, result) { return { jsonrpc: '2.0', id, result }; }
async function handle(msg) {
  if (!msg || msg.jsonrpc !== '2.0' || msg.method?.startsWith('notifications/')) return;
  const id = msg.id;
  try {
    if (msg.method === 'initialize') return send(response(id, { protocolVersion: '2025-06-18', capabilities: { tools: {} }, serverInfo: { name: 'eudirective-local-source-library', version: '0.2.0' } }));
    if (msg.method === 'ping') return send(response(id, {}));
    if (msg.method === 'tools/list') return send(response(id, { tools }));
    if (msg.method === 'tools/call') {
      const { name, arguments: args = {} } = msg.params || {};
      if (name === 'list_source_packs') {
        const rows = Object.entries(packs).map(([pack_id, p]) => ({ pack_id, title: p.title, scope: p.scope, actions: p.actions }));
        return send(response(id, { content: [{ type: 'text', text: JSON.stringify(rows, null, 2) }] }));
      }
      if (name === 'run_source_pack_action') return send(response(id, await execute(args)));
      throw new Error(`Unknown tool: ${name}`);
    }
    if (id !== undefined) send({ jsonrpc: '2.0', id, error: { code: -32601, message: `Unknown method: ${msg.method}` } });
  } catch (error) {
    if (id !== undefined) send({ jsonrpc: '2.0', id, error: { code: -32000, message: error?.message || String(error) } });
  }
}

let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buffer += chunk;
  while (true) {
    const nl = buffer.indexOf('\n');
    if (nl < 0) break;
    const line = buffer.slice(0, nl).trim(); buffer = buffer.slice(nl + 1);
    if (!line) continue;
    try { void handle(JSON.parse(line)); }
    catch (error) { send({ jsonrpc: '2.0', id: null, error: { code: -32700, message: error.message } }); }
  }
});

if (!existsSync(PLUGIN_ROOT)) throw new Error(`Plugin root unavailable: ${PLUGIN_ROOT}`);
