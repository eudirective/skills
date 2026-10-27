import {readFileSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const skillRoot = resolve(here, '..');
const packageRoot = resolve(skillRoot, '../..');
const local = resolve(skillRoot, 'references/component-manifest.json');
const plugin = JSON.parse(readFileSync(resolve(packageRoot, 'plugin.json'), 'utf8'));
const pluginName = plugin.name;
const indexUrl = 'https://raw.githubusercontent.com/eudirective/skills/main/component-index.json';
const listingUrl = 'https://api.github.com/repos/eudirective/public-data/contents?ref=main';
const SHA40 = /^[a-f0-9]{40}$/;
const SHA64 = /^[a-f0-9]{64}$/;

async function get(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: { 'User-Agent': 'freemovement-version-check', 'Accept': 'application/vnd.github+json' },
    });
    if (!response.ok) throw Error('GitHub HTTP ' + response.status);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
  }
  return JSON.stringify(value);
}

function validateInstalled(installed) {
  if (!installed || installed.schema_version !== '1.0.0' || !installed.component_id ||
      !/^\d+\.\d+\.\d+$/.test(installed.plugin_version) ||
      !installed.skill_versions || typeof installed.skill_versions !== 'object' ||
      !installed.upstream_trees || !SHA64.test(installed.input_fingerprint ?? '') ||
      !SHA64.test(installed.distributed_fingerprint ?? '') || !installed.compatibility) {
    throw Error('invalid installed component manifest');
  }
}

function publishedComponent(index, name, componentId) {
  if (!index || index.schema_version !== '1.0.0' ||
      index.source_repository !== 'eudirective/public-data' || !Array.isArray(index.components)) {
    throw Error('invalid published component index');
  }
  const matches = index.components.filter(row => row?.plugin_name === name);
  if (matches.length !== 1) throw Error('published component is missing or ambiguous: ' + name);
  const published = matches[0];
  if (published.component_id !== componentId) throw Error('published component identity mismatch: ' + name);
  for (const field of ['plugin_version', 'skill_versions', 'source_contract_version', 'input_fingerprint', 'distributed_fingerprint', 'compatibility']) {
    if (published[field] === undefined) throw Error('published component is missing ' + field);
  }
  return published;
}

export function compare(installed, index, liveTrees, name = pluginName) {
  validateInstalled(installed);
  if (!liveTrees || !SHA40.test(liveTrees['source-library'] ?? '') || !SHA40.test(liveTrees['module-notes'] ?? '')) {
    throw Error('invalid live public-data fingerprints');
  }
  const published = publishedComponent(index, name, installed.component_id);
  const differences = [];
  const row = (component, installedValue, githubValue) => {
    if (canonical(installedValue ?? null) !== canonical(githubValue ?? null)) {
      differences.push({component, installed: installedValue ?? null, github: githubValue ?? null});
    }
  };
  row('plugin', installed.plugin_version, published.plugin_version);
  for (const skill of new Set([...Object.keys(installed.skill_versions), ...Object.keys(published.skill_versions)])) {
    row('skill:' + skill, installed.skill_versions[skill], published.skill_versions[skill]);
  }
  row('source-contract', installed.source_contract_version, published.source_contract_version);
  row('package:input-fingerprint', installed.input_fingerprint, published.input_fingerprint);
  row('package:distributed-fingerprint', installed.distributed_fingerprint, published.distributed_fingerprint);
  row('compatibility', installed.compatibility, published.compatibility);
  for (const tree of ['source-library', 'module-notes']) {
    const bundled = index.upstream_trees?.[tree];
    if (!SHA40.test(bundled ?? '')) throw Error('published component index has an invalid ' + tree + ' tree fingerprint');
    row('package:upstream:' + tree, installed.upstream_trees[tree], bundled);
    row('github:upstream-mirror:' + tree, bundled, liveTrees[tree]);
  }
  return differences;
}

export function availabilityStatus(installed, index, differences, name = pluginName) {
  const selected = publishedComponent(index, name, installed.component_id);
  if (name !== 'freemovement-law') {
    const core = publishedComponent(index, 'freemovement-law', 'eu-core');
    if (canonical(selected.compatibility) !== canonical(core.compatibility) ||
        canonical(installed.compatibility) !== canonical(core.compatibility)) {
      return 'available_incompatible';
    }
  }
  const packageDifferences = differences.filter(item => !item.component.startsWith('github:upstream-mirror:'));
  return packageDifferences.length ? 'available_outdated' : 'available_compatible';
}

export async function run(read = get, options = {}) {
  const name = options.pluginName ?? pluginName;
  const manifestPath = options.manifestPath ?? local;
  try {
    const installed = JSON.parse(readFileSync(manifestPath, 'utf8'));
    const [index, entries] = await Promise.all([read(indexUrl), read(listingUrl)]);
    if (!Array.isArray(entries)) throw Error('public-data root listing is malformed');
    const liveTrees = {};
    for (const tree of ['source-library', 'module-notes']) {
      const item = entries.find(entry => entry?.name === tree && entry?.type === 'dir');
      if (!item || !SHA40.test(item.sha ?? '')) throw Error('public-data ' + tree + ' tree is unavailable or malformed');
      liveTrees[tree] = item.sha;
    }
    const differences = compare(installed, index, liveTrees, name);
    const availability = availabilityStatus(installed, index, differences, name);
    const packageDifferences = differences.filter(item => !item.component.startsWith('github:upstream-mirror:'));
    const upstreamDifferences = differences.filter(item => item.component.startsWith('github:upstream-mirror:'));
    const status = availability === 'available_incompatible' ? 'incompatible' :
      packageDifferences.length ? 'mismatch' : upstreamDifferences.length ? 'upstream_mismatch' : 'current';
    return {status, availability, plugin_name: name, differences};
  } catch (error) {
    return {status: 'check_failed', availability: 'discovery_unknown', plugin_name: name,
      reason: String(error?.message ?? error)};
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = await run();
  if (process.argv.includes('--json')) console.log(JSON.stringify(result, null, 2));
  else if (result.status === 'current') console.log('Verified ' + pluginName + ' package and source fingerprints.');
  else if (result.status === 'mismatch') console.log(pluginName + ' differs from its published component. Check the listed package differences and available update.');
  else if (result.status === 'incompatible') console.log(pluginName + ' does not meet the published core compatibility contract.');
  else if (result.status === 'upstream_mismatch') console.log('The published package snapshot differs from current public-data; this alone does not establish that a newer package is available.');
  else console.log('FreeMovement version check for ' + pluginName + ' unsuccessful: ' + result.reason + '. Update availability could not be confirmed.');
}
