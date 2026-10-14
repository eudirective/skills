#!/usr/bin/env python3
"""C1 recovery regression: all 47 present, missing/altered/unknown denied."""
import copy
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import c7_trust_gate as trust
import verify_bundled_source_pack as gate
from contract_validate import load_json

ROOT = Path(__file__).resolve().parents[1]
PACK = trust.BUNDLED_SOURCE_ROOT
MANIFEST = PACK/'core-source-pack-manifest-0.6.1.json'


def must_block(func, text):
    try: func()
    except (trust.C7TrustError,gate.SourceReleaseError) as ex:
        assert text in str(ex), (text,str(ex))
    else: raise AssertionError('expected block: '+text)


def main():
    tests=[]
    def passed(name):
        tests.append(name)
        print('PASS',name,flush=True)
    manifest=load_json(MANIFEST)
    report=gate.inspect()
    assert report['logical_sources']==46 and report['source_representations']==47
    assert report['verified_source_notes']==21 and report['bundled_text_representations']==26
    assert trust.require_source_pack(manifest)['source_assurance']=='pinned_metadata_and_verified_bundled_47_representations'
    passed('all_47_bytes_present_and_code_pinned')
    # Verified source notes are not verbatim court opinions.
    assert any(x['kind']=='verified_source_note' for s in manifest['sources'] for x in s['representations'])
    assert report['complete_verbatim_official_texts'] is False
    passed('physical_completeness_not_full_official_text')
    with tempfile.TemporaryDirectory(prefix='c1-restoration-') as tmp:
        original=Path(tmp)/'source-pack'
        shutil.copytree(PACK/'sources',original/'sources')
        assert gate.inspect(original)['source_representations']==47
        passed('isolated_pack_copy_complete')
        directive=original/'sources/eu/CELEX_02004L0038-20110616_EN_TXT.md'
        original_bytes=directive.read_bytes()
        directive.unlink()
        must_block(lambda:gate.inspect(original),'bundled_source_missing_or_modified')
        must_block(lambda:trust.require_source_pack(manifest,original),'source_representation_missing_or_unsafe')
        passed('missing_primary_legislation_blocks_release')
        directive.write_bytes(original_bytes)
        note=original/'sources/reference/eu_61962cj0026.md'
        note_bytes=note.read_bytes()
        note.write_bytes(note_bytes+b' injected')
        must_block(lambda:gate.inspect(original),'bundled_source_missing_or_modified')
        passed('modified_source_note_blocks_release')
        note.write_bytes(note_bytes)
        unexpected=original/'sources/reference/unknown_extra_source.md'
        unexpected.write_text('unregistered source',encoding='utf-8')
        must_block(lambda:gate.inspect(original),'unexpected_files')
        passed('unlisted_document_blocks_release')
        unexpected.unlink()
        assert gate.inspect(original)['source_representations']==47
        passed('repair_and_reverify_passes')
    fake=copy.deepcopy(manifest)
    fake['sources'][0]['representations'][0]['sha256']='0'*64
    must_block(lambda:trust.require_source_pack(fake),'untrusted_source_pack_manifest')
    passed('altered_manifest_blocks_release')
    print(json.dumps({'status':'passed','count':len(tests),'tests':tests},sort_keys=True))

if __name__=='__main__':main()
