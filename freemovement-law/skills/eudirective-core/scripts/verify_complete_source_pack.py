#!/usr/bin/env python3
"""Verify all original 0.6.0 sibling source representations against the core's pinned manifest.

Never infer complete sibling-pack status from metadata alone.
"""
from pathlib import Path
import json,sys,argparse
from contract_validate import load_json,validate_obj
import c7_trust_gate as trust
from source_library_paths import compatibility_root

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=compatibility_root()/'core-source-pack-manifest-0.6.1.json'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('complete_pack_dir',help='Full sibling source-pack directory, containing sources/... for all 47 representations')
    a=ap.parse_args()
    try:
        obj=load_json(MANIFEST)
        validate_obj('core-source-pack',obj)
        candidate=Path(a.complete_pack_dir)
        # A complete sibling pack must contain and exactly match the pinned
        # manifest as well as every representation. Do not silently construct
        # the manifest from trusted core metadata when the source directory has
        # no source_manifest.json or has one with conflicting declarations.
        source_manifest = candidate / 'source_manifest.json'
        if source_manifest.is_symlink() or not source_manifest.is_file():
            raise trust.C7TrustError('complete_sibling_manifest_missing_or_symlinked')
        external_obj = load_json(source_manifest)
        if trust.digest_obj(external_obj) != trust.digest_obj(obj):
            raise trust.C7TrustError('complete_sibling_manifest_mismatch')
        info=trust.require_source_pack(external_obj,candidate)
        print(json.dumps({'status':'verified_complete_local_source_pack','source_count':46,'representation_count':47,'trust':info},sort_keys=True))
        return 0
    except (OSError,ValueError,trust.C7TrustError) as e:
        print(json.dumps({'status':'blocked','reason':str(e),'representation_count_verified':None},sort_keys=True),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
