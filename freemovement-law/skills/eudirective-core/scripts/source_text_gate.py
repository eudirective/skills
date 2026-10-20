#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(65536),b''): h.update(chunk)
    return h.hexdigest()

def usable_reps(source: dict) -> list[dict]:
    out=[]
    for r in source.get('representations',[]):
        if r.get('kind')=='bundled_text' and r.get('authenticity_state')=='verified_official': out.append(r)
        elif r.get('kind')=='verified_source_note' and r.get('authenticity_state')=='verified_identity_version': out.append(r)
    return out

def expected_text_state(source: dict) -> str:
    reps=source.get('representations',[])
    if any(r.get('kind')=='bundled_text' and r.get('authenticity_state')=='verified_official' for r in reps): return 'bundled_verified'
    if any(r.get('kind')=='verified_source_note' and r.get('authenticity_state')=='verified_identity_version' for r in reps): return 'verified_source_note'
    if any(r.get('kind')=='candidate_text' for r in reps): return 'candidate_unverified'
    return 'reference_only'

def inspect(pack: Path) -> dict:
    m=json.loads((pack/'source_manifest.json').read_text(encoding='utf-8')); blocked=[]
    for source in m.get('sources',[]):
        reps=source.get('representations',[])
        for rep in reps:
            rel=rep.get('relative_path')
            if not rel: raise ValueError(f"representation path missing for {source.get('source_id')}")
            path=pack/rel
            if not path.is_file(): raise ValueError(f'missing representation file: {rel}')
            if sha256(path)!=rep.get('sha256'): raise ValueError(f'representation hash mismatch: {rel}')
            k,a=rep.get('kind'),rep.get('authenticity_state')
            if k=='bundled_text' and a!='verified_official': raise ValueError(f'bundled_text lacks verified_official authenticity: {rel}')
            if k=='verified_source_note' and a!='verified_identity_version': raise ValueError(f'verified_source_note lacks verified_identity_version: {rel}')
            if k=='candidate_text' and a!='unverified_candidate': raise ValueError(f'candidate_text has invalid authenticity state: {rel}')
            if k=='curated_reference_note' and a!='reference_only': raise ValueError(f'curated_reference_note has invalid authenticity state: {rel}')
        expected=expected_text_state(source); actual=source.get('text_completeness_state')
        if actual!=expected: raise ValueError(f"text completeness mismatch for {source.get('source_id')}: expected {expected}, got {actual}")
        usable=usable_reps(source)
        if any(r.get('kind')=='verified_source_note' for r in usable):
            if source.get('freshness_state') not in {'fixed_verified','current'}: raise ValueError(f"verified source note has unsupported freshness: {source.get('source_id')}")
            if not source.get('verification_date'): raise ValueError(f"verified source note missing verification date: {source.get('source_id')}")
            if source.get('freshness_state')=='current' and source.get('verification_date')!=m.get('live_verification_date'):
                raise ValueError(f"mutable verified source note not checked on pack live verification date: {source.get('source_id')}")
        if not usable:
            blocked.append({'source_id':source.get('source_id'),'identity':source.get('identity'),'title':source.get('title'),'canonical_url':source.get('canonical_url'),'text_completeness_state':actual,'representation_kinds':sorted({str(r.get('kind')) for r in reps}),'reason':'no verified usable source representation'})
    return {'status':'complete' if not blocked else 'blocked','gate':'c1_source_representation_complete','pack_version':m.get('pack_version'),'logical_source_count':len(m.get('sources',[])),'blocked_source_count':len(blocked),'blocked_sources':blocked}

def main()->int:
    ap=argparse.ArgumentParser(description='Check whether every C1 core source has a verified usable representation'); ap.add_argument('pack'); ap.add_argument('--json-output'); args=ap.parse_args()
    try: result=inspect(Path(args.pack))
    except Exception as exc:
        print(json.dumps({'status':'invalid','error':str(exc)},sort_keys=True),file=sys.stderr); return 2
    text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)
    if args.json_output: Path(args.json_output).write_text(text+'\n',encoding='utf-8')
    print(text); return 0 if result['status']=='complete' else 3
if __name__=='__main__': raise SystemExit(main())
