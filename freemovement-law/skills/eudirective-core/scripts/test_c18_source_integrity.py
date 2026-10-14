#!/usr/bin/env python3
"""C18 source-scoped, provenance, tamper, downgrade, and live-date regression.

These are not independent legal-merits or original-PDF byte authentication tests.
"""
import copy
import json
import tempfile
import shutil
from pathlib import Path
from unittest import mock

from contract_validate import load_json, digest_obj
import c7_trust_gate as trust
import c18_source_integrity as integrity
import c6_integration as c6
from verify_bundled_source_pack import inspect as verify_bundle

ROOT = Path(__file__).resolve().parents[1]
PACK = integrity.PACK
TEST_TIME='2026-10-10T11:00:00Z'

def deny(call,match):
    try:call()
    except Exception as ex:
        assert match in str(ex),('unexpected failure',match,str(ex))
    else:raise AssertionError('expected denial: '+match)

def main():
    passed=[]
    def ok(label):
        passed.append(label); print('PASS',label,flush=True)
    m=load_json(integrity.MANIFEST)
    prev=load_json(integrity.ARCHIVE)
    a=integrity.audit()
    assert a['identity_only_note_count']==21 and a['representation_count']==47
    assert a['article_2_2_a']['status']=='restored_targeted_official_html_excerpt_checked'
    assert a['private_applicant_readiness']=='blocked'
    assert len(a['source_records'])==46 and verify_bundle()['source_pack_version']=='0.6.1'
    ok('47_pinned_source_bytes_and_21_explicit_full_text_gaps')
    assert len([s for s in a['source_records'] if s['has_full_source_gap']])==21
    assert all(r['official_original_byte_equivalence']=='not_verified' for s in a['source_records'] for r in s['representations'])
    ok('no_hash_as_official_verbatim_or_legal_merits')
    rep=next(x for x in m['sources'] if x['source_id']==integrity.ART2_ID)['representations'][0]
    oldrep=next(x for x in prev['sources'] if x['source_id']==integrity.ART2_ID)['representations'][0]
    assert (rep['sha256'],rep['bytes'])!= (oldrep['sha256'],oldrep['bytes'])
    assert all(s==next(x for x in prev['sources'] if x['source_id']==s['source_id'])
               for s in m['sources'] if s['source_id']!=integrity.ART2_ID)
    assert 'the spouse;' in (PACK/integrity.ART2_REL).read_text()
    ok('single_officially_checked_clause_repair_preserves_45_other_source_records')
    assert trust.require_source_pack(m)['source_manifest_sha256']==digest_obj(m)
    deny(lambda:trust.require_source_as_of(m,'2026-10-09T12:00:00Z'), 'source_verification_after_run_as_of')
    assert trust.require_source_as_of(m,TEST_TIME)['official_live_reverification'] is False
    ok('source_as_of_does_not_backdate_2026_10_10_correction')
    for old in (prev,load_json(PACK/'core-source-pack-manifest-0.5.0.json')):
        deny(lambda old=old:c6.require_input('source_pack',old), 'c18_active_source_pack_required')
    assert c6.require_input('source_pack',m)['source_pack_version']=='0.6.1'
    ok('historical_manifests_cannot_initiate_new_c6_cases')
    fake=copy.deepcopy(m)
    fake['sources'][0]['verification_date']='2099-01-01'
    deny(lambda:trust.require_source_pack(fake),'untrusted_source_pack_manifest')
    ok('caller_cannot_self_upgrade_source_currentness')
    with tempfile.TemporaryDirectory(prefix='c18-integrity-') as temp:
        copyroot=Path(temp)/'copy'
        shutil.copytree(PACK/'sources',copyroot/'sources')
        target=copyroot/integrity.ART2_REL
        original=target.read_bytes()
        # Replacing the corrected clause by the former gap must invalidate trusted bytes.
        target.write_bytes(original.replace(b'(a)\n\nthe spouse;\n\n',b''))
        with mock.patch.object(trust,'BUNDLED_SOURCE_ROOT',copyroot):
            deny(lambda:trust.require_source_pack(m),'bundled_source_missing_or_modified')
        ok('restored_clause_cannot_be_removed_without_trust_failure')
        target.write_bytes(original)
        note=copyroot/'sources/reference/eu_61962cj0026.md'
        note.write_bytes(note.read_bytes()+b'\nfalse full court text\n')
        with mock.patch.object(trust,'BUNDLED_SOURCE_ROOT',copyroot):
            deny(lambda:trust.require_source_pack(m),'bundled_source_missing_or_modified')
        ok('identity_only_note_cannot_be_silently_relabelled')
    with tempfile.TemporaryDirectory(prefix='c18-meta-') as temp:
        rp=Path(temp)/'receipt.json'
        edited=load_json(integrity.REPAIR)
        edited['verified_scope']='Entire Directive independently certified'
        rp.write_text(json.dumps(edited))
        with mock.patch.object(integrity,'REPAIR',rp):
            # Even preserving exact law text, an unsupported widened verification claim fails.
            deny(integrity.audit,'art2_provenance_bytes_modified')
            edited['exact_article_fragment']='the partner;'
            rp.write_text(json.dumps(edited))
            deny(integrity.audit,'art2_provenance_bytes_modified')
    ok('forged_article_proof_cannot_upgrade_evidence_scope')
    print(json.dumps({'status':'passed','count':len(passed),'tests':passed,'limitations':['Only deterministic/local verification; legal expertise and official full-text comparisons unverified.']},sort_keys=True))
if __name__=='__main__':main()
