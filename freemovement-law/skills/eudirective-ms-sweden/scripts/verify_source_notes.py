#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
from source_library_paths import module_notes_root
root=Path(__file__).resolve().parents[1]
e=json.loads((root/'references/module-export.json').read_text(encoding='utf-8'))
errors=[]
for r in e['source_records']:
 name=r['source_id'].split(':src:',1)[1]
 path=module_notes_root()/f'{name}.md'
 if not path.is_file(): errors.append('missing:'+name);continue
 h=hashlib.sha256(path.read_bytes()).hexdigest()
 if h!=r['content_sha256']:errors.append('mismatch:'+name)
 if r['content_kind']!='verified_source_note' or r['authenticity_state']!='verified_identity_version':errors.append('not_a_note:'+name)
for f in e['rule_records']:
 if f['interpretation_status']=='direct_text':errors.append('direct_text_without_official_text:'+f['rule_id'])
print(json.dumps({'status':'passed' if not errors else 'failed','checked_notes':len(e['source_records']),'errors':errors},sort_keys=True))
sys.exit(0 if not errors else 2)
