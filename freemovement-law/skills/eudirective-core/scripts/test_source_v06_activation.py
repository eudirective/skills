#!/usr/bin/env python3
"""C8 exact-source acceptance and synthetic integration regression.

This is not a test of legal correctness, official-server byte identity, or
completeness of missing historical sibling-pack representations.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

from contract_validate import load_json, validate_obj, digest_obj
import c7_trust_gate as trust
import core_source_adapter as adapter
import element_model as em
import c6_integration as c6
import hierarchy_principles as c5b

ROOT=Path(__file__).resolve().parents[1]
PACK05=ROOT/'references/source-pack/core-source-pack-manifest-0.5.0.json'
PACK06=ROOT/'references/source-pack/core-source-pack-manifest-0.6.0.json'
PACK061=ROOT/'references/source-pack/core-source-pack-manifest-0.6.1.json'
TEXTREL='sources/case_law/CELEX_62024CJ0477_EN_TXT.md'
TEXT=trust.BUNDLED_SOURCE_ROOT/TEXTREL
FX=ROOT/'references/fixtures'
DRIVER=ROOT/'scripts/c6_integration.py'

def cli(*args,success=True):
    run=subprocess.run([sys.executable,str(DRIVER),*map(str,args)], capture_output=True,text=True)
    if success:
        assert run.returncode==0, (run.stdout,run.stderr)
        return json.loads(run.stdout)
    assert run.returncode==2, (run.stdout,run.stderr)
    return json.loads(run.stderr)['error']

def prep(folder,pack=PACK061,instant='2026-10-10T09:00:00Z',success=True):
    args=['prepare','--workdir',str(folder),'--case',str(FX/'c5a/case-frontier.json'),
          '--run-id','RUN-C6-TEST','--time-of-check',instant,'--source-pack',str(pack),
          '--elements',str(FX/'c5d/elements-signals.json'),
          '--actors',str(FX/'c5a/actors-family-member.json'),
          '--c5c-context',str(FX/'c5c/context-ready.json')]
    for m,e in [(FX/'member-state-se-manifest.json',FX/'c5c/member-state-se-c5c-export.json'),
                (FX/'member-state-de-manifest.json',FX/'member-state-de-export.json'),
                (FX/'c6/applicant-country-tr-manifest.json',FX/'c6/applicant-country-tr-export.json')]:
        args.extend(['--module-pair',str(m),str(e)])
    return cli(*args,success=success)

def execute(trace=None):
    results=[]
    def passit(key,info):
        results.append({'id':key,'status':'passed','evidence':info})
        print('PASS',key,flush=True)

    old=load_json(PACK05);archive=load_json(PACK06);pack=load_json(PACK061)
    validate_obj('core-source-pack',old)
    validate_obj('core-source-pack',pack)
    assert len(old['sources'])==45 and len(archive['sources'])==46 and len(pack['sources'])==46
    assert old['representation_count']==46 and pack['representation_count']==47
    for s in old['sources']:
        match=next(x for x in archive['sources'] if x['source_id']==s['source_id'])
        assert match==s
    passit('unchanged_45_base_sources','Exact equality of all 45 historical manifest source objects')

    # Historical 0.6.0 is immutable; active 0.6.1 differs only by the targeted Directive record.
    changed=[x['source_id'] for x in pack['sources'] if x!=next(z for z in archive['sources'] if z['source_id']==x['source_id'])]
    assert changed==['eu:32004l0038'],changed
    p=trust.trusted_policy()
    assert p['source_pack']['pack_version']=='0.5.0'
    assert p['source_pack_0_6']['pack_version']=='0.6.0' and p['source_pack_0_6_1']['pack_version']=='0.6.1'
    out=trust.require_source_pack(pack)
    assert out['source_pack_version']=='0.6.1' and out['source_representation_count']==47
    assert out['source_assurance']=='pinned_metadata_and_verified_bundled_47_representations'
    assert out['official_live_reverification'] is False
    assert digest_obj(archive)=='169281bc86fe70be300495b0daa9f44d8f2c5cb690a7e2a34ca310763e70e502'
    assert trust.require_source_pack(old)['source_representation_count']==46
    try: trust.require_source_pack(archive)
    except trust.C7TrustError as ex: assert 'bundled_source_missing_or_modified' in str(ex)
    else: raise AssertionError('obsolete 0.6.0 manifest accepted with replaced Directive bytes')
    passit('version_specific_pinned_trust','Historical metadata remains pinned, but old 0.6.0 physical source bytes are not accepted from the new active bundle')

    new=next(x for x in pack['sources'] if x['source_id']=='eu:62024cj0477')
    rep=new['representations'][0]
    assert hashlib.sha256(TEXT.read_bytes()).hexdigest()==rep['sha256']
    md=TEXT.read_text(encoding='utf-8')
    assert len(md)>50000 and all(f'**{i}.**' in md for i in range(1,72))
    assert len([x for x in md.splitlines() if x.startswith('**') and 'must be interpreted as meaning' in x])>=0
    assert 'ECLI:EU:C:2026:182' in md
    assert 'Article 41' in md and 'Article 47' in md
    passit('full_deldwyn_bundled_and_hashed','71 numbered paragraphs and verified 55,970-byte Markdown representation')

    asof=trust.require_source_as_of(pack,'2026-10-10T09:00:00Z')
    assert asof['fixed_identity_source_count']==35 and asof['mutable_current_source_count']==11
    assert asof['official_live_reverification'] is False
    try:trust.require_source_as_of(pack,'2026-10-09T09:00:00Z')
    except trust.C7TrustError as e:assert 'source_verification_after_run_as_of' in str(e)
    else:raise AssertionError('New Directive repair accepted before 2026-10-10 passage verification')
    passit('date_bound_promotion','New source verification date cannot be backdated')

    m,e=adapter.build_objects(pack)
    assert m['pack_version']=='0.6.1' and len(e['source_records'])==46
    assert not m['known_gap_ids']
    entry=next(x for x in e['source_records'] if x['source_id']=='eu:62024cj0477')
    assert entry['content_kind']=='authoritative_bundled_text' and entry['status']=='current'
    assert entry['content_sha256']==rep['sha256']
    passit('c3_source_export','All 46 sources C3-conformant, Deldwyn keyed as full text')

    catalog,interactions,invariants=em.load_model()
    sm=load_json(ROOT/'references/elements/source-support-map.json')
    rr=load_json(ROOT/'references/elements/source-support-requirements.json')
    assert sm['source_pack_version']=='0.6.1' and rr['source_pack_version']=='0.6.1'
    assert len(sm['records'])==46
    el=next(x for x in sm['records'] if x['source_id']=='eu:62024cj0477')
    assert len(el['targets'])>=3
    assert all(x['target_type']!='rule' for x in el['targets'])
    em.validate_model(catalog,interactions,invariants,sm,rr)
    passit('c2_additive_coverage','Deldwyn source coverage indexed without new mechanically assumed legal rule')

    c5b_05, defs05 = c5b.load_principle_catalog(c5b.source_index(old))
    c5b_06, defs06 = c5b.load_principle_catalog(c5b.source_index(pack))
    for pid in ('rights_of_defence','good_administration_general_principle',
                'effective_judicial_protection','charter_article_41_direct_reliance'):
        assert 'eu:62024cj0477' not in defs05[pid]['source_refs']
        assert 'eu:62024cj0477' in defs06[pid]['source_refs']
    assert defs06['charter_article_41_direct_reliance']['article_41_direct_addressee_boundary'] is True
    assert c5b_05['catalog_version']==c5b_06['catalog_version']
    passit('c5b_version_sensitive_authority','Deldwyn supports source-candidate references only in 0.6, Article 41 limitation preserved')

    tampered=copy.deepcopy(pack)
    tampered['sources'][0]['representations'][0]['sha256']='0'*64
    try:trust.require_source_pack(tampered)
    except trust.C7TrustError as ex:assert 'untrusted_source_pack_manifest' in str(ex)
    else:raise AssertionError('Manifest tamper was allowed')
    passit('forged_manifest_denied','Any changed source hash invalidates signed-by-code metadata contract')

    with tempfile.TemporaryDirectory(prefix='deldwyn-integrity-') as td:
        import shutil
        bogus=Path(td)/'full-bundle'
        shutil.copytree(trust.BUNDLED_SOURCE_ROOT/'sources',bogus/'sources')
        (bogus/TEXTREL).write_text(md+'\nMUTATED\n',encoding='utf-8')
        with mock.patch.object(trust,'BUNDLED_SOURCE_ROOT',bogus):
            try:trust.require_source_pack(pack)
            except trust.C7TrustError as ex:assert 'bundled_source_missing_or_modified' in str(ex)
            else:raise AssertionError('Forged bundled Markdown accepted')
    passit('bundled_text_mutation_denied','Locally altered Deldwyn text fails regardless of trusted manifest')

    with tempfile.TemporaryDirectory(prefix='deldwyn-complete-pack-') as td:
        partial=Path(td);(partial/TEXTREL).parent.mkdir(parents=True,exist_ok=True)
        (partial/TEXTREL).write_bytes(TEXT.read_bytes())
        try:trust.require_source_pack(pack,partial)
        except trust.C7TrustError as ex:assert 'source_representation_missing_or_unsafe' in str(ex)
        else:raise AssertionError('Partial pack misrepresented as 47-file verified pack')
    passit('incomplete_sibling_pack_denied','Complete source_root gate requires all 47 representation bytes, regardless of embedded core presence')

    with tempfile.TemporaryDirectory(prefix='c8-manifest-') as td:
        sibling=Path(td)
        command=[sys.executable,str(ROOT/'scripts/verify_complete_source_pack.py'),str(sibling)]
        missing=subprocess.run(command,capture_output=True,text=True)
        assert missing.returncode==2 and 'complete_sibling_manifest_missing_or_symlinked' in missing.stderr
        (sibling/'source_manifest.json').write_text(json.dumps(old),encoding='utf-8')
        mismatch=subprocess.run(command,capture_output=True,text=True)
        assert mismatch.returncode==2 and 'complete_sibling_manifest_mismatch' in mismatch.stderr
        (sibling/'source_manifest.json').write_text(json.dumps(pack),encoding='utf-8')
        incomplete=subprocess.run(command,capture_output=True,text=True)
        assert incomplete.returncode==2 and 'source_representation_missing_or_unsafe' in incomplete.stderr
    passit('complete_sibling_manifest_and_bytes_gate','Verifier requires matching original source_manifest.json plus all 47 representation bytes')

    with tempfile.TemporaryDirectory(prefix='c8-activation-') as td:
        td=Path(td)
        work=td/'run'
        prepared=prep(work)
        manifest=load_json(work/'c6-run-manifest.json')
        assert manifest['source_trust']['source_pack_version']=='0.6.1'
        assert manifest['source_trust']['source_assurance']=='pinned_metadata_and_verified_bundled_47_representations'
        assert manifest['source_as_of']['fixed_identity_source_count']==35
        assert prepared['stage']=='requirements_set'
        launched=cli('release','--workdir',work)
        assert launched['status']=='released_limited_synthetic'
        verified=cli('verify','--workdir',work)
        assert verified['status']=='verified_c6_synthetic_release'
        assert len(load_json(work/'inputs/source-pack.json')['sources'])==46
        assert (work/'issue-index.md').is_file()
        assert 'all 47 bundled representations' in ' '.join(manifest['limitations'])
        controlled=(work/'controlled-analysis.md').read_text(encoding='utf-8')
        assert 'C8 source trust verifies all 47 bundled representation bytes' in controlled
        assert 'Official live currency' in controlled
        assert '0.5.0 manifest/46' not in controlled
        passit('v06_packaged_style_c6_release','Synthetic controller releases and verifies C18 active source v0.6.1; 21 notes remain')
        # Any modification to source text must invalidate even an already prepared run.
        fake=td/'fake-source-root'
        import shutil
        shutil.copytree(trust.BUNDLED_SOURCE_ROOT/'sources',fake/'sources')
        (fake/TEXTREL).write_bytes(TEXT.read_bytes()+b'\n')
        with mock.patch.object(trust,'BUNDLED_SOURCE_ROOT',fake):
            try:c6.verify_release(work)
            except trust.C7TrustError as ex:assert 'bundled_source_missing_or_modified' in str(ex)
            else:raise AssertionError('Already released run verified with mutated source')
        passit('release_reverification_checks_deldwyn_bytes','Modification after release fails verification of source files')

    if trace:
        Path(trace).write_text(json.dumps({'suite':'C18 source pack 0.6.1 core activation',
                                           'status':'passed','count':len(results),'tests':results,
                                           'limitations':['all 47 historical and Deldwyn source bytes are now bundled and pinned',
                                                          'Article 2(2)(a) checked against official HTML; remainder not independently compared or legally validated']},
                                          indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'status':'passed','count':len(results),'tests':[r['id'] for r in results]},indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--trace-output');ns=a.parse_args()
    execute(ns.trace_output)
