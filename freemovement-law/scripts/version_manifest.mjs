#!/usr/bin/env node
import {readFileSync,readdirSync,existsSync,writeFileSync} from 'node:fs';
import {resolve,join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');const json=p=>JSON.parse(readFileSync(p,'utf8'));
const p=json(join(root,'plugin.json')),legacy=json(join(root,'.codex-plugin/plugin.json'));
if(p.version!==legacy.version||p.name!==legacy.name)throw Error('plugin metadata mismatch');
const skills={};for(const ent of readdirSync(join(root,'skills'),{withFileTypes:true})){const f=join(root,'skills',ent.name,'SKILL.md');if(!ent.isDirectory()||!existsSync(f))continue;const s=readFileSync(f,'utf8');const match=s.match(/^- Current version: `(\d+\.\d+\.\d+)`/m)||s.match(/Skill version: [^\s]+ v(\d+\.\d+\.\d+)/);if(!match)throw Error('skill version missing: '+ent.name);skills[ent.name]=match[1]}
const f=join(root,'skills/eudirective-core/references/session-version-manifest.json');const old=json(f);const idx=process.argv.indexOf('--library-tree');const sha=idx>=0?process.argv[idx+1]:old.library.tree_sha;
if(!/^[0-9a-f]{40}$/.test(sha))throw Error('invalid tree SHA');
const dir=join(root,'skills/eudirective-source-library');const names=readdirSync(dir).filter(n=>/^core-source-pack-manifest-\d+\.\d+\.\d+\.json$/.test(n)).sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));const pack=json(join(dir,names.at(-1))).pack_version;
const sorted=Object.fromEntries(Object.entries(skills).sort(([a],[b])=>a.localeCompare(b)));
const result={schema_version:1,plugin:{name:p.name,version:p.version},skills:sorted,library:{repository:'eudirective/public-data',path:'source-library',tree_sha:sha,core_pack_version:pack}};
if(process.argv.includes('--stamp')){writeFileSync(f,JSON.stringify(result,null,2)+'\n');console.log('Stamped FreeMovement versions')}else if(process.argv.includes('--verify')){if(JSON.stringify(old)!==JSON.stringify(result))throw Error('installed version manifest not synchronized');console.log('Verified FreeMovement versions')}else throw Error('expected --stamp or --verify');
