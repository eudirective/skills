import test from 'node:test';import assert from 'node:assert/strict';import {compare} from './session_version_check.mjs';
const sha='a'.repeat(40), b='b'.repeat(40);
const src=()=>({plugin:{version:'0.43.2'},skills:{core:'0.42.2',sweden:'0.7.1'},library:{tree_sha:sha,core_pack_version:'0.7.0'}});
test('matching versions silent',()=>assert.deepEqual(compare(src(),src(),sha),[]));
test('plugin mismatch',()=>{const x=src();x.plugin.version='0.43.1';assert.equal(compare(x,src(),sha)[0].component,'plugin')});
test('every skill matched including missing',()=>{const x=src();delete x.skills.sweden;assert.equal(compare(x,src(),sha)[0].component,'skill:sweden')});
test('library changes without version change',()=>assert.deepEqual(compare(src(),src(),b).map(x=>x.component),['library:tree','github:library-mirror']));
test('invalid tree fails',()=>assert.throws(()=>compare(src(),src(),'bad')));
