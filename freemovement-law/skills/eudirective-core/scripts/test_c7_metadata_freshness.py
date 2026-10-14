#!/usr/bin/env python3
"""C7.1 adversarial CLI and source-date regression; synthetic fixtures only."""
import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import case_controller
import c7_trust_gate as trust
from contract_validate import load_json
from test_c6_integration import FX, PACK, run


def cli_prepare(workdir, run_id='RUN-C6-TEST', when='2026-10-10T09:00:00Z', success=True):
    args = ['prepare', '--workdir', workdir, '--case', FX/'c5a/case-frontier.json',
            '--run-id', run_id, '--time-of-check', when,
            '--source-pack', PACK, '--elements', FX/'c5d/elements-signals.json',
            '--actors', FX/'c5a/actors-family-member.json',
            '--c5c-context', FX/'c5c/context-ready.json']
    for m,e in [
        (FX/'member-state-se-manifest.json', FX/'c5c/member-state-se-c5c-export.json'),
        (FX/'member-state-de-manifest.json', FX/'member-state-de-export.json'),
        (FX/'c6/applicant-country-tr-manifest.json', FX/'c6/applicant-country-tr-export.json'),
    ]:
        args.extend(['--module-pair', m, e])
    return run(*args, success=success)


def execute(trace_output=None):
    traces=[]
    def passed(name, detail):
        traces.append({'name':name, 'status':'passed', 'observation':detail,
                       'legal_merits_review':'not_performed'})
        print('PASS ' + name, flush=True)

    pack=load_json(PACK)
    assert trust.require_source_pack(pack)['source_representation_count']==47
    good=trust.require_source_as_of(pack, '2026-10-10T09:00:00Z')
    assert good['fixed_identity_source_count']==35 and good['mutable_current_source_count']==11
    assert good['official_live_reverification'] is False
    passed('as_of_metadata_counts_and_non_live_scope', '35 fixed identities, 11 mutable sources; no live recheck claimed')
    assert trust.source_freshness_class({'source_type':'cjeu_judgment','freshness_state':'fixed_verified'})=='fixed_identity'
    assert trust.source_freshness_class({'source_type':'commission_operational_guidance_page','freshness_state':'current'})=='operational_guidance'
    assert trust.SOURCE_AGE_LIMITS_DAYS['operational_guidance']<trust.SOURCE_AGE_LIMITS_DAYS['legislation_consolidation']
    passed('judgment_and_mutable_guidance_differ', 'identity-fixed judgments do not inherit operational-guidance expiration')

    with tempfile.TemporaryDirectory(prefix='c7-metadata-') as temp:
        root=Path(temp)
        baseline=root/'allowed';cli_prepare(baseline)
        assert load_json(baseline/'c6-run-manifest.json')['source_as_of']==good
        assert case_controller.load_state(baseline/'state.json')['time_of_check']==good['as_of_time']
        passed('approved_run_metadata_bound_to_controller', 'as-of record pinned to C6 manifest and state')
        run('release','--workdir',baseline)
        assert run('verify','--workdir',baseline)['status']=='verified_c6_synthetic_release'
        passed('as_of_aware_packaged_style_release_verifies', 'limited, synthetic-only release and replay')

        def deny_run(name, rid, instant, prefix):
            workdir=root/name
            error=cli_prepare(workdir,run_id=rid,when=instant,success=False)
            assert error.startswith(prefix), (name,error)
            assert not workdir.exists(), (name,'workspace_created')
            passed(name,'rejected before workspace: '+prefix)

        deny_run('arbitrary_person_name_run_id', 'RUN-C6-TEST-Alice-Smith', '2026-10-10T09:00:00Z', 'unapproved_synthetic_run_id')
        deny_run('email_encoded_run_id', 'alice@example.invalid', '2026-10-10T09:00:00Z', 'unapproved_synthetic_run_id')
        deny_run('path_encoded_run_id', '../../fictional-case', '2026-10-10T09:00:00Z', 'unapproved_synthetic_run_id')
        deny_run('text_in_timestamp', 'RUN-C6-TEST', '2026-10-10T09:00:00Z;Alice Example <alice@example.invalid>', 'invalid_synthetic_time_of_check')
        deny_run('timestamp_without_zone', 'RUN-C6-TEST', '2026-10-10T09:00:00', 'invalid_synthetic_time_of_check')
        deny_run('non_utc_zone', 'RUN-C6-TEST', '2026-10-10T12:00:00+03:00', 'invalid_synthetic_time_of_check')
        deny_run('nonexistent_calendar_date', 'RUN-C6-TEST', '2026-02-30T09:00:00Z', 'invalid_synthetic_time_of_check')
        deny_run('future_timestamp_2099', 'RUN-C6-TEST', '2099-01-01T09:00:00Z', 'source_freshness_as_of_blocked:')
        deny_run('expired_operational_guidance', 'RUN-C6-TEST', '2026-10-14T09:00:00Z', 'source_freshness_as_of_blocked:')
        deny_run('backdated_before_source_verified', 'RUN-C6-TEST', '2026-10-04T09:00:00Z', 'source_verification_after_run_as_of')

        # No alteration of a trusted manifest is accepted as a way to create
        # a longer freshness window, regardless of its as-of timestamp.
        mutated=copy.deepcopy(pack)
        mutated['live_verification_date']='2099-01-01'
        try:trust.require_source_as_of(mutated,'2099-01-01T09:00:00Z')
        except trust.C7TrustError as e:assert str(e)=='untrusted_source_pack_manifest'
        else:raise AssertionError('self-attested new verification date accepted')
        passed('manifest_self_reverification_denied', 'pinned source identity cannot be rebound by altering verification date')

        changed=root/'changed'
        import shutil
        shutil.copytree(baseline,changed)
        index=load_json(changed/'c6-run-manifest.json')
        index['source_as_of']['as_of_time']='2026-10-10T10:00:00Z'
        (changed/'c6-run-manifest.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
        assert 'controller_identity_or_time_mismatch' in run('verify','--workdir',changed,success=False)
        passed('serialized_as_of_rebinding_denied', 'verification recomputes as-of statement rather than trusting edited manifest')

        state_dir=root/'direct-controller'
        state_dir.mkdir()
        raw=subprocess.run([sys.executable,str(Path(__file__).parent/'case_controller.py'),
                            'init','--state',str(state_dir/'state.json'),'--case-id','TEST-1',
                            '--run-id','TEST-1','--profile','cooperative_local',
                            '--time-of-check','not-a-date'],capture_output=True,text=True)
        assert raw.returncode!=0 and 'invalid_time' in raw.stderr and not (state_dir/'state.json').exists(),(raw.stdout,raw.stderr)
        passed('generic_controller_direct_invalid_clock_denied', 'controller refuses malformed time even without C6 integration gate')

    if trace_output:
        out=Path(trace_output)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps({'suite':'C7.1 metadata and as-of freshness','version':'0.21.1',
                'status':'passed','count':len(traces),'traces':traces,
                'limitations':['No host privacy, official source revalidation or legal-merits review performed.']},
                indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'status':'passed','count':len(traces),'tests':[x['name'] for x in traces]},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--trace-output');args=p.parse_args()
    execute(args.trace_output)
