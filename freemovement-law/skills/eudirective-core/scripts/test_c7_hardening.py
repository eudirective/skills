#!/usr/bin/env python3
"""C7 independent-from-C6 regression probes, synthetic-only; no legal merits oracle."""
import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import c6_integration as c6
import c7_issue_index as issues
import c7_trust_gate as trust
import case_controller as controller
from contract_validate import digest_obj, load_json
from test_c6_integration import FX, PACK, prepare, run, dump


def execute(evidence_path=None):
    traces = []
    def record(name, status, observation):
        assert status == 'passed', (name, observation)
        traces.append({'name':name, 'status':status, 'observation':observation,
                       'category':'deterministic_cli_or_in_memory_probe',
                       'legal_merits_review':'not_performed'})
        print('TRACE ' + name + ': ' + status, flush=True)

    p = load_json(PACK)
    attested = trust.require_source_pack(p)
    assert attested['source_representation_count'] == 47
    assert attested['source_assurance'] == 'pinned_metadata_and_verified_bundled_47_representations'
    assert attested['official_live_reverification'] is False
    record('pinned_source_metadata_baseline', 'passed', '47 representation bytes pinned; current official source and legal merits not verified')

    with tempfile.TemporaryDirectory() as scratch:
        home = Path(scratch)
        mutated_pack = copy.deepcopy(p)
        mutated_pack['sources'][0]['representations'][0]['sha256'] = '0' * 64
        src = dump(home / 'bad-source.json', mutated_pack)
        msg = prepare(home / 'forged-source', {'source_pack':src, 'success':False})
        assert 'untrusted_source_pack_manifest' in msg and not (home/'forged-source').exists(), msg
        record('altered_representation_sha_rejected_before_snapshot', 'passed', 'forged digest rejected, no case workspace created')

        modified_freshness = copy.deepcopy(p)
        modified_freshness['sources'][0]['freshness_state'] = 'stale'
        loc = dump(home / 'altered-freshness.json', modified_freshness)
        msg = prepare(home / 'freshness', {'source_pack':loc, 'success':False})
        assert 'untrusted_source_pack_manifest' in msg and not (home/'freshness').exists(), msg
        record('freshness_relabel_rejected', 'passed', 'metadata changes cannot override code-pinned source release')

        fake = load_json(FX / 'c5a/case-frontier.json')
        fake['user_objective'] = 'Fake user ID: P12345678, name Alice Example, email alice@example.invalid'
        bad_case = dump(home / 'synthetic-with-identifiers.json', fake)
        msg = prepare(home / 'identifier-injection', {'case':bad_case, 'success':False})
        assert 'unapproved_synthetic_fixture:case' in msg and not (home/'identifier-injection').exists(), msg
        record('synthetic_label_does_not_authorize_identifier_like_content', 'passed', 'fictional injected data rejected before workspace creation')

        fake_elem = load_json(FX / 'c5d/elements-signals.json')
        fake_elem['elements'][0]['value'] = 'approved_fixture_bypass_attempt'
        ef = dump(home / 'altered-elements.json', fake_elem)
        msg = prepare(home / 'bad-elements', {'elements':ef, 'success':False})
        assert 'unapproved_synthetic_fixture:elements' in msg and not (home/'bad-elements').exists(), msg
        record('fixture_policy_rejects_unapproved_element_data', 'passed', 'caller cannot define the approved evidence bundle')

        fake_mod = load_json(FX / 'member-state-de-export.json')
        fake_mod['module_version'] = '0.0.1'
        mf = dump(home / 'altered-country-export.json',fake_mod)
        pairs = [(FX/'member-state-se-manifest.json', FX/'c5c/member-state-se-c5c-export.json'),
                 (FX/'member-state-de-manifest.json', mf),
                 (FX/'c6/applicant-country-tr-manifest.json', FX/'c6/applicant-country-tr-export.json')]
        msg=prepare(home/'bad-country', {'pairs':pairs, 'success':False})
        assert 'unapproved_synthetic_fixture:module_export' in msg and not (home/'bad-country').exists(), msg
        record('arbitrary_country_export_denied', 'passed', 'reusable fixture module is not an unlimited intake channel')

        tampered = copy.deepcopy(trust.trusted_policy())
        tampered['approved_inputs']['case']['0'*64] = 'invented-fixture.json'
        alt = dump(home/'altered-trust-root.json', tampered)
        with mock.patch.object(trust, 'POLICY_FILE', alt):
            try:
                trust.require_approved('case', load_json(FX / 'c5a/case-frontier.json'))
            except trust.C7TrustError as exc:
                assert 'trusted_policy_integrity_mismatch' in str(exc), str(exc)
            else:
                raise AssertionError('self-signed fixture policy unexpectedly accepted')
        record('policy_self_rebinding_rejected', 'passed', 'new approved hash cannot be enrolled by editing the data-only trust policy')

        sibling = home / 'sibling'; first_rep = p['sources'][0]['representations'][0]['relative_path']
        (sibling/first_rep).parent.mkdir(parents=True, exist_ok=True)
        (sibling/first_rep).write_text('not actual official source text',encoding='utf-8')
        try:
            trust.require_source_pack(p, sibling)
        except trust.C7TrustError as exc:
            assert 'source_representation_bytes_mismatch' in str(exc),str(exc)
        else:
            raise AssertionError('unmatched actual representation bytes were accepted')
        record('optional_actual_source_bytes_rejected_if_wrong', 'passed', 'trusted manifest cannot bless substituted source text when sibling bytes are supplied')

        baseline=home/'basic';prepare(baseline)
        run('release','--workdir',baseline)
        assert run('verify','--workdir',baseline)['status']=='verified_c6_synthetic_release'
        record('c7_limited_release_end_to_end', 'passed', 'prepared, controller-released and re-verified using trusted synthetic fixtures')
        index = load_json(baseline/'issue-index.json')
        assert len(index['issues'])==index['issue_count'] and index['issue_count']>20
        assert all(x['value_sha256']==digest_obj(x['value']) and
                   x['stage_sha256']==index['source_stage_digests'][x['stage']] for x in index['issues'])
        assert str(index['issue_count']) in (baseline/'controlled-analysis.md').read_text()
        record('full_issue_index_bound_to_report', 'passed', str(index['issue_count'])+' individually hashed entries; report names companion and digest')

        original_stages={n:load_json(baseline/f'stages/{n}.json') for n in c6.STAGE_SCHEMAS}
        original_stages['c5d']['unresolved']=['fictional missing consideration %02d'%i for i in range(31)]
        original_stages['c5d']['limitations']=['fictional caveat %02d'%i for i in range(23)]
        record_src = controller.load_state(baseline/'state.json')
        exhaustive=issues.build(original_stages,record_src)
        vals=[x['value'] for x in exhaustive['issues'] if x['stage']=='c5d' and x['category']=='unresolved']
        assert len(vals)==31 and vals==original_stages['c5d']['unresolved']
        md=issues.render(exhaustive).decode('utf-8')
        assert 'fictional missing consideration 30' in md and 'fictional caveat 22' in md
        record('large_unresolved_and_limitation_lists_lossless', 'passed', '31 unresolved and 23 limitations all retained beyond former [12]/[10] caps')

        tamper=home/'modified-issue-index';shutil.copytree(baseline,tamper)
        item=load_json(tamper/'issue-index.json');item['issues'][0]['value']='Forged assessment';dump(tamper/'issue-index.json',item)
        msg=run('verify','--workdir',tamper,success=False)
        assert 'c7_issue_index_mismatch' in msg, msg
        record('changed_issue_index_json_rejected', 'passed', 'digest-bound full issue index cannot silently change after release')

        tamper=home/'modified-issue-markdown';shutil.copytree(baseline,tamper)
        with (tamper/'issue-index.md').open('a') as output:output.write('\nHidden additional finding.\n')
        msg=run('verify','--workdir',tamper,success=False)
        assert 'c7_issue_index_render_mismatch' in msg, msg
        record('changed_issue_index_markdown_rejected', 'passed', 'full human-readable issue companion re-rendered for exact-byte verification')

        reviewed=home/'review';prepare(reviewed)
        a=FX/'c7/c5d-review.json';b=FX/'c7/c5e-context.json';c=FX/'c7/c5f-context.json'
        result=run('release','--workdir',reviewed,'--review',a,'--c5e-context',b,'--c5f-context',c)
        assert result['strategy_state']=='reviewed_only'
        assert run('verify','--workdir',reviewed)['strategy_state']=='reviewed_only'
        assert load_json(reviewed/'analysis.json')==load_json(baseline/'analysis.json')
        record('explicit_review_strategy_still_analysis_independent', 'passed', 'approved fixture reviewer path replayed; legal analysis remains unchanged')

        rogue=home/'rogue-review';prepare(rogue)
        rev=load_json(a);rev['reviewer_ref']='reviewer:fictional-new'
        patched= dump(home/'untrusted-review.json',rev)
        msg=run('release','--workdir',rogue,'--review',patched,'--c5e-context',b,'--c5f-context',c,success=False)
        assert 'unapproved_synthetic_fixture:c5d_review' in msg
        assert not (rogue/'release-attempt.json').exists() and controller.load_state(rogue/'state.json')['stage']=='requirements_set'
        record('untrusted_reviewer_denied_before_processing', 'passed', 'arbitrary review text not used to produce strategy or release')

        # Crash at each original controller boundary: no finalized C7 receipt
        # can be asserted, and repeating release in same run must fail closed.
        for failing_op in ('cmd_propose_analysis', 'cmd_validate_analysis', 'cmd_release'):
            interrupted=home/('interrupt-'+failing_op);prepare(interrupted)
            args=SimpleNamespace(workdir=str(interrupted),review=None,c5e_context=None,c5f_context=None)
            original = c6.controller_op
            target = getattr(controller,failing_op)
            def fault(func,*argv,**kwargs):
                if func is target:
                    raise c6.C6Error('fault_injected_'+failing_op)
                return original(func,*argv,**kwargs)
            with mock.patch.object(c6,'controller_op',side_effect=fault):
                try:
                    c6.release(args)
                except c6.C6Error as exc:
                    assert str(exc)=='fault_injected_'+failing_op
                else:
                    raise AssertionError('release survived injected fault at '+failing_op)
            assert (interrupted/'release-attempt.json').exists()
            assert not (interrupted/'c6-release-receipt.json').exists()
            assert run('verify','--workdir',interrupted,success=False)
            assert 'release_already_attempted' in run('release','--workdir',interrupted,success=False)
            record('interrupted_'+failing_op+'_fails_closed', 'passed', 'no success receipt and same-run retry rejected')

    if evidence_path:
        evidence_path=Path(evidence_path)
        evidence_path.parent.mkdir(parents=True,exist_ok=True)
        evidence_path.write_text(json.dumps({'suite':'C7 hardening independent deterministic probes',
            'release_target':'eudirective-core v0.21.1', 'status':'passed',
            'test_count':len(traces),'traces':traces,
            'limitations':['Synthetic fixtures only; host privacy and official current-law checks not performed.',
                           'Recorded deterministic traces are not external semantic/legal reviewer assessments.',
                           'A bundled code-pinned trust policy does not independently authenticate the host or skill distribution.']},
            sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'passed','count':len(traces),'tests':[x['name'] for x in traces]},indent=2))
    return traces

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--trace-output')
    args=parser.parse_args()
    execute(args.trace_output)
