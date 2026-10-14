#!/usr/bin/env python3
"""Independent C6 synthetic CLI and tamper tests; no semantic legal truth oracle."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from contract_validate import digest_obj, load_json, validate_obj
import case_controller as cc
import analysis_handoff as ah
import suggestion_engine as sg
import suggestion_ranking as sr

from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / 'references/fixtures'
DRIVER = ROOT / 'scripts/c6_integration.py'
PACK = compatibility_root() / 'core-source-pack-manifest-0.6.1.json'


def run(*args, success=True):
    proc = subprocess.run([sys.executable, str(DRIVER), *map(str,args)], capture_output=True, text=True)
    if success:
        assert proc.returncode == 0, proc.stderr
        return json.loads(proc.stdout)
    assert proc.returncode == 2, (proc.stdout,proc.stderr)
    return json.loads(proc.stderr)['error']


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return path


def prepare(workdir, custom=None):
    custom = custom or {}
    args = ['prepare', '--workdir', str(workdir), '--case', str(custom.get('case', FX/'c5a/case-frontier.json')),
            '--run-id', 'RUN-C6-TEST', '--time-of-check', '2026-10-10T12:00:00Z',
            '--source-pack', str(custom.get('source_pack', PACK)),
            '--elements', str(custom.get('elements', FX/'c5d/elements-signals.json')),
            '--actors', str(custom.get('actors', FX/'c5a/actors-family-member.json')),
            '--c5c-context', str(custom.get('c5c_context', FX/'c5c/context-ready.json'))]
    pairs = custom.get('pairs', [
        (FX/'member-state-se-manifest.json', FX/'c5c/member-state-se-c5c-export.json'),
        (FX/'member-state-de-manifest.json', FX/'member-state-de-export.json'),
        (FX/'c6/applicant-country-tr-manifest.json', FX/'c6/applicant-country-tr-export.json'),
    ])
    for m,e in pairs:
        args.extend(['--module-pair', str(m), str(e)])
    return run(*args, success=custom.get('success',True))


def reviewer_files(workdir):
    # An explicit fictional reviewer decision is formed only by the test harness, never by the C6 driver.
    case = load_json(workdir/'inputs/case.json')
    d = load_json(workdir/'stages/c5d.json')
    c = load_json(workdir/'stages/c5c.json')
    elem = load_json(workdir/'inputs/elements.json')
    pairs = [(str(workdir/('inputs/module-%02d-manifest.json'%i)), str(workdir/('inputs/module-%02d-export.json'%i))) for i in range(3)]
    access = next(x for x in d['attack_angles'] if x['attack_angle_id']=='core:attack:procedural-access-review')
    assert access['assessment_status'] == 'supported'
    review = {'review_version':'0.1.0','case_id':case['case_id'],'c5d_sha256':digest_obj(d),
              'reviewer_ref':'reviewer:c6-synthetic','identity_assurance':'system_fixture',
              'attack_angle_reviews':[
                  {'attack_angle_id':'core:attack:procedural-access-review',
                   'disposition':'validate_for_suggestion',
                   'rationale':'Synthetic test review checks recorded access signal and evidence only, not illegality.',
                   'reviewed_evidence_refs':['synthetic:appointment-record','eu:32004l0038'],
                   'module_value_checks':[]}], 'route_reviews':[]}
    validate_obj('analysis-review-record',review)
    h = ah.build(case,c,d,review,elem,pairs)
    assert h['handoff_status']=='ready' and len(h['eligible_attack_angles'])==1, h
    ctx = {
        'context_version':'0.1.0','case_id':case['case_id'],
        'objective':{'objective_id':'obj:access','statement':'Establish the available written appointment channel without extra disclosure.'},
        'proposals':[{
            'suggestion_id':'sug:clarify-basis','candidate_kind':'action',
            'adapted_stratagem_id':'adapted:13','original_stratagem_id':'original:13',
            'applicability':'applicable','supporting_attack_angle_refs':['core:attack:procedural-access-review'],
            'supporting_route_refs':[],
            'action_summary':'Ask a narrow written question about the asserted appointment requirement and alternatives.',
            'mechanism_summary':'Obtain an attributable response without claiming a violation.',
            'assumptions':['A written response channel exists.'],
            'prerequisites':['Preserve evidence of the initial appointment request.'],
            'expected_effect':'Get a documented authority position.',
            'risks':['The reply may be uninformative.'],
            'reversibility':'high','information_value':'high','burden_cost':'low',
            'disclosure_duty_status':'none_known',
            'disclosure_review_rationale':'The narrow inquiry does not depend on breaching affirmative disclosure duties.',
            'falsification_required':False,'inaction_or_delay':False,'deadline_waiver_review':'not_applicable',
            'requires_new_determination':False,'new_question':None
        }]}
    s = sg.build(h,ctx)
    assert len(s['candidates'])==1, s
    factors = {'urgency':'high','remedy_power':'not_applicable','legal_support_strength':'medium',
               'evidentiary_value':'high','reversibility':'high','route_compatibility':'not_applicable',
               'burden_cost':'low','systemic_value':'medium'}
    ranking_ctx = {
        'context_version':'0.1.0','case_id':case['case_id'],'objective_id':'obj:access',
        'bindings':{'handoff_sha256':digest_obj(h), 'c5e_context_sha256':digest_obj(ctx),
                    'c5e_candidates_sha256':digest_obj(s)},
        'review':{'reviewer_ref':'reviewer:c6-synthetic','identity_assurance':'unverified_local',
                  'rationale':'Fixture-only independent explicit comparison; no legal success claims.'},
        'baseline_comparison':[{'baseline_kind':b,'review_status':'not_applicable','suggestion_id':None,
                                'rationale':'Synthetic reviewer finds no distinct grounded '+b+' comparator in this narrow test.'}
                               for b in sorted(sr.BASELINES)],
        'candidate_assessments':[{
            'suggestion_id':'sug:clarify-basis','disposition':'include','assumptions_state':'current',
            'factual_basis_state':'reviewed','counterevidence_state':'reviewed_no_material_conflict',
            'prerequisites_state':'satisfied','adverse_effects_state':'clear',
            'basis_classification':'documented_fact_and_review','ratings':factors,
            'rating_basis_refs':['core:attack:procedural-access-review'],
            'review_rationale':'Fictional reviewer assessed limited information gain, not illegality.'
        }], 'relations':[],'sequences':[]}
    expected=sr.build(h,ctx,s,ranking_ctx)
    assert expected['recommendation_status']=='single_preferred_for_review',expected
    refs=workdir/'explicit-reviewer-inputs'
    return [dump(refs/'review.json',review),dump(refs/'c5e-context.json',ctx),dump(refs/'c5f-context.json',ranking_ctx)]


def launch_reviewed(workdir):
    paths=reviewer_files(workdir)
    return run('release','--workdir',str(workdir), '--review',str(paths[0]),
               '--c5e-context',str(paths[1]),'--c5f-context',str(paths[2]))


def expected_error(proc, needle):
    assert needle in proc, (needle,proc)


def execute():
    passed=[]
    with tempfile.TemporaryDirectory() as outer:
        d=Path(outer)
        a=d/'basic'; prepared=prepare(a)
        assert prepared['stage']=='requirements_set' and prepared['controller_revision']>=7
        passed.append('c6_three_role_country_module_composition')
        assert cc.load_state(a/'state.json')['case']['privacy_classification']=='synthetic'
        assert len(cc.load_state(a/'state.json')['modules'])==4
        passed.append('c6_original_controller_owns_stage_and_module_registration')
        assert cc.load_state(a/'state.json')['requirements']['c6:legal-merits-review']['status']=='not_checked'
        passed.append('c6_legal_merits_requirement_remains_unchecked')
        result=run('release','--workdir',a)
        assert result['status']=='released_limited_synthetic' and result['strategy_state']=='review_needed'
        passed.append('c6_review_absent_causes_limited_release_not_fake_approval')
        verified=run('verify','--workdir',a)
        assert verified['status']=='verified_c6_synthetic_release'
        passed.append('c6_serialized_controller_release_and_reverify')
        ana=load_json(a/'analysis.json')
        assert ana['requested_release_mode']=='limited' and not ana['recommendations']
        assert ana['findings'] and all(x['status']=='cannot_assess' for x in ana['findings'])
        assert 'review only' in (a/'strategy-review-only.md').read_text().lower()
        passed.append('c6_no_legal_candidate_promoted_to_violation_or_recommendation')
        assert any(x['status']=='calculated' for x in ana['deadlines'])
        assert all('legal deadline' in x['label'] for x in ana['deadlines'])
        passed.append('c6_exact_scoped_deadline_still_review_only')
        b=d/'duplicate';prepare(b);run('release','--workdir',b)
        assert (b/'controlled-analysis.md').read_bytes()==(a/'controlled-analysis.md').read_bytes()
        assert (b/'strategy-review-only.md').read_bytes()==(a/'strategy-review-only.md').read_bytes()
        passed.append('c6_byte_deterministic_release')

        reviewed=d/'reviewed';prepare(reviewed)
        launch=launch_reviewed(reviewed)
        assert launch['strategy_state']=='reviewed_only'
        assert run('verify','--workdir',reviewed)['strategy_state']=='reviewed_only'
        assert load_json(reviewed/'review/c5f-ranked.json')['recommendation_status']=='single_preferred_for_review'
        assert load_json(reviewed/'analysis.json') == load_json(a/'analysis.json')
        passed.append('c6_explicit_c5e_c5f_review_and_exact_replay')
        passed.append('c6_strategy_independence_from_legal_analysis')

        # Copy released bundles; mutate one content item at a time and require re-verification to reject it.
        alterations = [
            ('case', 'inputs/case.json', lambda x: {**x,'user_objective':'Changed after release'}),
            ('country_module', 'inputs/module-00-export.json',lambda x:{**x,'module_version':'9.9.9'}),
            ('source_pack','inputs/source-pack.json', lambda x:{**x,'pack_version':'0.0.0'}),
            ('c5d','stages/c5d.json', lambda x: {**x,'legal_violation_status':'established'}),
            ('review','review/c5d-review.json', lambda x:{**x,'c5d_sha256':'0'*64}),
            ('reviewer_proposal','review/c5e-context.json', lambda x:{**x,'proposals':[]}),
            ('ranking_baselines','review/c5f-context.json', lambda x:{**x,'baseline_comparison':[]}),
            ('analysis','analysis.json', lambda x:{**x,'requested_release_mode':'full'}),
            ('controller','state.json', lambda x:{**x,'revision':x['revision']+1}),
            ('controller_validation_receipt','validation-receipt.json',lambda x:{**x,'receipt_sha256':'0'*64}),
            ('c6_receipt','c6-release-receipt.json',lambda x:{**x,'legal_conclusion_status':'determined'}),
        ]
        for label,rel,mutate in alterations:
            target=d/('tamper-'+label)
            shutil.copytree(reviewed,target)
            fp=target/rel
            dump(fp,mutate(load_json(fp)))
            assert run('verify','--workdir',target,success=False)
            passed.append('c6_reject_changed_'+label)
        tamper=d/'changed_markdown';shutil.copytree(reviewed,tamper)
        with (tamper/'strategy-review-only.md').open('a') as handle:handle.write('\nExecute immediately.\n')
        assert 'strategy_render_mismatch' in run('verify','--workdir',tamper,success=False)
        passed.append('c6_reject_unbound_strategy_text')
        tamper=d/'changed_analysis_markdown';shutil.copytree(a,tamper)
        with (tamper/'controlled-analysis.md').open('a') as handle:handle.write('\nUnreviewed addition.\n')
        assert 'controlled_analysis_render_mismatch' in run('verify','--workdir',tamper,success=False)
        passed.append('c6_reject_unbound_legal_text')

        wrong=d/'stale_review';prepare(wrong)
        paths=reviewer_files(wrong); review_obj=load_json(paths[0]); review_obj['c5d_sha256']='f'*64;dump(paths[0],review_obj)
        assert 'unapproved_synthetic_fixture:c5d_review' in run('release','--workdir',wrong,'--review',paths[0],'--c5e-context',paths[1],'--c5f-context',paths[2],success=False)
        assert cc.load_state(wrong/'state.json')['stage']=='requirements_set'
        passed.append('c6_stale_positive_review_rejected_before_controller_transition')
        no_rank=d/'missing_ranking_baseline';prepare(no_rank)
        paths=reviewer_files(no_rank); obj=load_json(paths[2]); obj['baseline_comparison']=[];dump(paths[2],obj)
        assert 'unapproved_synthetic_fixture:c5f_context' in run('release','--workdir',no_rank,'--review',paths[0],'--c5e-context',paths[1],'--c5f-context',paths[2],success=False)
        passed.append('c6_unexamined_c5f_baselines_block_release_with_review')
        missing=d/'missing_module'
        er=prepare(missing,{'pairs':[(FX/'member-state-se-manifest.json', FX/'c5c/member-state-se-c5c-export.json'),(FX/'member-state-de-manifest.json', FX/'member-state-de-export.json')], 'success':False})
        assert 'missing_required_modules' in er
        passed.append('c6_missing_required_applicant_module_fails_closed')

        optional=d/'optional'
        oc=FX/'c7/optional-case.json'
        prepare(optional,{'case':oc,'pairs':[(FX/'member-state-se-manifest.json', FX/'c5c/member-state-se-c5c-export.json'),(FX/'member-state-de-manifest.json', FX/'member-state-de-export.json')]})
        run('release','--workdir',optional)
        assert cc.load_state(optional/'state.json')['missing_optional_modules'] == ['req:c5a-tr-local']
        assert 'Missing optional module' in (optional/'controlled-analysis.md').read_text()
        passed.append('c6_missing_optional_local_context_is_scoped')

        mp=FX/'c7/stale-member-manifest.json';ep=FX/'c7/stale-member-export.json'
        stale=d/'stale'
        prepare(stale,{'pairs':[(FX/'member-state-se-manifest.json', FX/'c5c/member-state-se-c5c-export.json'),(mp,ep),(FX/'c6/applicant-country-tr-manifest.json', FX/'c6/applicant-country-tr-export.json')]})
        assert cc.load_state(stale/'state.json')['freshness_blocked_required_modules']
        run('release','--workdir',stale)
        assert 'Freshness blocked' in (stale/'controlled-analysis.md').read_text()
        passed.append('c6_stale_member_source_fails_full_but_limited_remains_truthful')

        private=d/'private';case=load_json(FX/'c5a/case-frontier.json');case['privacy_classification']='private'
        cp=d/'private-case.json';dump(cp,case)
        assert 'unapproved_synthetic_fixture:case' in prepare(private,{'case':cp,'success':False})
        passed.append('c6_private_mode_remains_disabled')

        bad=d/'bad_destination'
        tm=FX/'c7/wrong-tr-manifest.json';te=FX/'c7/wrong-tr-export.json'
        er=prepare(bad,{'pairs':[(FX/'member-state-se-manifest.json', FX/'c5c/member-state-se-c5c-export.json'),(FX/'member-state-de-manifest.json',FX/'member-state-de-export.json'),(tm,te)],'success':False})
        assert 'missing_required_modules' in er
        passed.append('c6_wrong_applicant_destination_profile_rejected')

        incorrect=d/'incompatible'
        imp=FX/'c7/incompatible-manifest.json'
        er=prepare(incorrect,{'pairs':[(FX/'member-state-se-manifest.json', FX/'c5c/member-state-se-c5c-export.json'),(imp,FX/'member-state-de-export.json'),(FX/'c6/applicant-country-tr-manifest.json', FX/'c6/applicant-country-tr-export.json')], 'success':False})
        assert 'incompatible_controller_protocol' in er
        passed.append('c6_incompatible_module_rejected')

        invalid=d/'full_attempt';prepare(invalid)
        old=load_json(invalid/'prepared-controller-state.json')
        import c6_integration as c6
        stages={k:load_json(invalid/f'stages/{k}.json') for k in c6.STAGE_SCHEMAS}
        analysis=c6.controlled_projection(load_json(invalid/'inputs/case.json'),stages,old)
        analysis['requested_release_mode']='full'
        ap=invalid/'full-analysis.json';dump(ap,analysis)
        c6.controller_op(cc.cmd_propose_analysis,invalid/'state.json',old['case_id'],input=str(ap))
        try:
            c6.controller_op(cc.cmd_validate_analysis, invalid/'state.json', old['case_id'],input=str(ap),receipt=str(invalid/'full-validation.json'))
        except cc.ControllerError as e:
            assert 'full_release_blocked_unresolved' in str(e)
        else:
            raise AssertionError('controller accepted fake full legal release')
        passed.append('c6_full_mode_blocked_without_independent_legal_merits_review')
    print(json.dumps({'status':'passed','count':len(passed),'tests':passed},indent=2))
    return passed

if __name__=='__main__':
    execute()
