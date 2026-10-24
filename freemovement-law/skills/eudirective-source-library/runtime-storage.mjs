#!/usr/bin/env node
// Shared transient-file helpers for source-library maintenance scripts.
// The repository root is one level above this file; all raw captures, staging
// writes, and scratch output are kept under that root's ignored temp/ folder.
import { mkdir, mkdtemp, rename, rm, writeFile } from 'node:fs/promises';
import { mkdirSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const PROJECT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const PROJECT_TEMP = path.join(PROJECT_ROOT, 'temp');

export function projectTempPath(originalPath) {
  const absolute = path.resolve(originalPath);
  const fromTemp = path.relative(PROJECT_TEMP, absolute);
  if (fromTemp === '' || (!fromTemp.startsWith(`..${path.sep}`) && fromTemp !== '..' && !path.isAbsolute(fromTemp))) {
    return absolute;
  }
  const relative = path.relative(PROJECT_ROOT, absolute);
  if (!relative || relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error(`Path is outside the project root: ${absolute}`);
  }
  return path.join(PROJECT_TEMP, relative);
}

export async function makeProjectTempDir(prefix) {
  const scratch = path.join(PROJECT_TEMP, 'scratch');
  await mkdir(scratch, { recursive: true });
  return mkdtemp(path.join(scratch, prefix));
}

export async function atomicProjectWrite(target, data) {
  await mkdir(path.dirname(target), { recursive: true });
  const stage = path.join(PROJECT_TEMP, 'staging', `${randomUUID()}.tmp`);
  await mkdir(path.dirname(stage), { recursive: true });
  try {
    await writeFile(stage, data);
    await rename(stage, target);
  } catch (error) {
    await rm(stage, { force: true });
    throw error;
  }
}

export function atomicProjectWriteSync(target, data) {
  mkdirSync(path.dirname(target), { recursive: true });
  const stageDir = path.join(PROJECT_TEMP, 'staging');
  mkdirSync(stageDir, { recursive: true });
  const stage = path.join(stageDir, `${randomUUID()}.tmp`);
  try {
    writeFileSync(stage, data);
    renameSync(stage, target);
  } catch (error) {
    rmSync(stage, { force: true });
    throw error;
  }
}
