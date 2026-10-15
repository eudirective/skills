import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
test('checked-in manifest reflects actual plugin, skill, and library versions',()=>{
  const result=execFileSync(process.execPath,['freemovement-law/scripts/version_manifest.mjs','--verify'],{encoding:'utf8'});
  assert.match(result,/Verified FreeMovement versions/);
});
