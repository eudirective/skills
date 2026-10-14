#!/usr/bin/env python3
"""Mandatory fail-closed, deterministic source-byte release gate for core 0.28.0.

Checks every manifest-declared file: size, SHA-256, path safety and an exact
source-file inventory. Digests prove local archival integrity, NOT independent
official-publication authenticity, currentness or legal merits.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

from contract_validate import load_json, validate_obj
import c7_trust_gate as trust
from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'references/source-pack/core-source-pack-manifest-0.6.1.json'
SOURCE_DIR = compatibility_root()

class SourceReleaseError(Exception):
    pass


def inspect(bundle_root: Path = SOURCE_DIR) -> dict:
    manifest = load_json(MANIFEST)
    validate_obj('core-source-pack', manifest)
    if manifest['pack_version'] != '0.6.1':
        raise SourceReleaseError('release_requires_active_source_manifest_0.6.1')
    # The manifest is code-root pinned; the in-skill source path is also pinned.
    if bundle_root.resolve() == SOURCE_DIR.resolve():
        receipt = trust.require_source_pack(manifest)
    else:
        # Permits test-only side folders with the same 47-file inventory.
        from unittest.mock import patch
        with patch.object(trust, 'BUNDLED_SOURCE_ROOT', bundle_root):
            receipt = trust.require_source_pack(manifest)
    required = {}
    for src in manifest['sources']:
        for r in src['representations']:
            p = PurePosixPath(r['relative_path'])
            if (p.is_absolute() or '..' in p.parts or p.parts[0] != 'sources'
                    or '\\' in r['relative_path'] or r['relative_path'] in required):
                raise SourceReleaseError('invalid_or_duplicate_manifest_path')
            required[r['relative_path']] = r
    observed = {}
    base = bundle_root / 'sources'
    for p in base.rglob('*'):
        if p.is_symlink():
            raise SourceReleaseError('symlinked_source_artifact:' + str(p))
        if p.is_file():
            rel = p.relative_to(bundle_root).as_posix()
            observed[rel] = p
    if set(observed) != set(required):
        raise SourceReleaseError(json.dumps({
            'unexpected_files': sorted(set(observed)-set(required)),
            'missing_files': sorted(set(required)-set(observed))
        }, sort_keys=True))
    for rel, r in required.items():
        f = observed[rel]
        if f.stat().st_size != r['bytes'] or hashlib.sha256(f.read_bytes()).hexdigest() != r['sha256']:
            raise SourceReleaseError('size_or_hash_mismatch:' + rel)
    result = {
        'status': 'verified_locally_complete',
        'core_version': '0.36.0',
        'source_pack_version': manifest['pack_version'],
        'logical_sources': len(manifest['sources']),
        'source_representations': len(required),
        'bundled_text_representations': sum(r['kind']=='bundled_text' for r in required.values()),
        'verified_source_notes': sum(r['kind']=='verified_source_note' for r in required.values()),
        'bytes_checked': sum(r['bytes'] for r in required.values()),
        'trust_assurance': receipt['source_assurance'],
        'official_live_reverification': False,
        'complete_verbatim_official_texts': False,
    }
    if (result['logical_sources'],result['source_representations']) != (46,47):
        raise SourceReleaseError('source_counts_not_46_47')
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args()
    try:
        result=inspect()
        data=json.dumps(result,sort_keys=True,indent=2)+'\n'
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            args.json_output.write_text(data,encoding='utf-8')
        print(data,end='')
        return 0
    except Exception as err:
        print(json.dumps({'status':'blocked','reason':str(err)},sort_keys=True),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
