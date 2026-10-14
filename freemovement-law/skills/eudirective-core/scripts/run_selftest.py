#!/usr/bin/env python3
import contextlib
import copy
import io
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'scripts'
sys.path.insert(0,str(SCRIPTS))
import contract_validate as cv
import case_controller as cc
import element_model as em
import source_inventory as si
import core_source_adapter as csa
import source_text_gate as stg
import source_text_ingest as sti
import module_conformance as mc
import trust_controls as tc
import topology_engine as te
import regime_applicability as ra
import hierarchy_principles as hp
import evidence_deadline_authority as c5c
import attack_angle_synthesis as c5d
import analysis_handoff as ah
import suggestion_engine as sg
import suggestion_ranking as sr

FX=ROOT/'references'/'fixtures'

def quiet(fn,args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(args)

def expect_error(fn,args,needle):
    try:
        quiet(fn,args)
    except (cc.ControllerError,cv.ContractError,tc.TrustControlError,te.TopologyError,ra.RegimeError,hp.C5bError,c5c.C5cError,c5d.C5dError,ah.HandoffError,sg.SuggestionError,sr.RankingError) as e:
        if needle not in str(e):
            raise AssertionError(f"expected error containing {needle!r}, got {e!r}")
        return
    raise AssertionError(f"expected rejection containing {needle!r}")

def validate_fixture(fn,schema):
    obj=cv.load_json(FX/fn); cv.validate_obj(schema,obj); return obj

def init_args(state,run='RUN-1'):
    return NS(state=str(state),case_id='CASE-SYN-001',run_id=run,profile='cooperative_local',time_of_check='2026-10-04T20:00:00Z')

def mut(state,rev,**kw):
    base={'state':str(state),'case_id':'CASE-SYN-001','expected_revision':rev}; base.update(kw); return NS(**base)

def prepare_to_requirements(td,run='RUN-1'):
    td=Path(td); state=td/'state.json'
    quiet(cc.cmd_init,init_args(state,run))
    quiet(cc.cmd_accept_case,mut(state,0,input=str(FX/'case-input-minimal.json')))
    quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json')))
    quiet(cc.cmd_register_module,mut(state,2,manifest=str(FX/'member-state-se-manifest.json'),export=str(FX/'member-state-se-export.json')))
    quiet(cc.cmd_freeze_context,mut(state,3))
    quiet(cc.cmd_set_requirements,mut(state,4,input=str(FX/'requirement-set.json')))
    return state

def write_analysis(path,revision,source_override=None,mode='full',limitations=None):
    ana=json.loads((FX/'controlled-analysis.json').read_text())
    ana['bound_state_revision']=revision; ana['requested_release_mode']=mode
    if source_override is not None: ana['findings'][0]['source_refs']=source_override
    if limitations is not None: ana['limitations']=limitations
    path.write_text(json.dumps(ana,indent=2)+"\n")
    return ana

def prepare_to_release(td,run='RUN-C4'):
    td=Path(td); state=prepare_to_requirements(td,run)
    quiet(cc.cmd_update_requirement,mut(state,5,requirement_id='check:regime',status='supported',reason=None,detail=None))
    ap=td/'analysis.json'; write_analysis(ap,6)
    quiet(cc.cmd_propose_analysis,mut(state,6,input=str(ap)))
    vr=td/'validation.json'; quiet(cc.cmd_validate_analysis,mut(state,7,input=str(ap),receipt=str(vr)))
    out=td/'released.md'; rr=td/'release.json'; quiet(cc.cmd_release,mut(state,8,input=str(ap),receipt=str(vr),output=str(out),release_receipt=str(rr)))
    return state, ap, vr, out, rr

def c4_view_for_state(state,outbound_id='OUT-C4',destination='https://feedback.example.test/ingest'):
    data=cv.load_json(FX/'privacy'/'protected-synthetic.json'); data['bound_case_revision']=json.loads(Path(state).read_text())['revision']
    policy=cv.load_json(FX/'privacy'/'privacy-policy.json')
    return tc.build_views(data,policy,outbound_id,'compliance_feedback','feedback_service',destination,'feedback')[2]

def write_approval(path,rec,approval_id,decision='approve',destination='https://feedback.example.test/ingest',approved_at='2026-10-06T10:05:00Z',valid_until='2026-10-07T10:05:00Z'):
    obj={
      'trust_profile_version':'0.1.0','approval_id':approval_id,'case_id':'CASE-SYN-001','outbound_id':rec['outbound_id'],'decision':decision,
      'outbound_view_sha256':rec['view_sha256'],'purpose':rec['purpose'],'destination':destination,'action':rec['action'],
      'bound_prepared_revision':rec['prepared_revision'],'approver_ref':'user:synthetic','identity_assurance':'unverified_local',
      'approved_at':approved_at,'valid_until':valid_until}
    path.write_text(json.dumps(obj,indent=2)+'\n'); cv.validate_obj('approval-record',obj); return obj

def main():
    results=[]
    mapping={'case-input-minimal.json':'case-input','core-source-manifest.json':'module-manifest','core-source-export.json':'module-export','member-state-se-manifest.json':'module-manifest','member-state-se-export.json':'module-export','requirement-set.json':'requirement-set','controlled-analysis.json':'controlled-analysis','applicant-country-xx-manifest.json':'module-manifest','applicant-country-xx-export.json':'module-export','member-state-de-manifest.json':'module-manifest','member-state-de-export.json':'module-export'}
    for fn,sc in mapping.items(): validate_fixture(fn,sc)
    results.append('positive_contract_fixtures')

    # C3 frozen module conformance profile accepts each module family.
    for base in ['core-source','member-state-se','member-state-de','applicant-country-xx']:
        m=cv.load_json(FX/f'{base}-manifest.json'); e=cv.load_json(FX/f'{base}-export.json'); out=mc.validate_pair(m,e); assert out['status']=='conformant'
    results.append('c3_module_family_conformance_valid')

    # Malformed modules are rejected for namespace, legal-layer and compatibility violations.
    with tempfile.TemporaryDirectory() as td:
        m=cv.load_json(FX/'applicant-country-xx-manifest.json')
        e=cv.load_json(FX/'conformance'/'invalid-applicant-namespace-export.json')
        try: mc.validate_pair(m,e)
        except mc.ConformanceError as x: assert 'id_outside_namespace' in str(x)
        else: raise AssertionError('out-of-namespace applicant export accepted')
        e=cv.load_json(FX/'conformance'/'invalid-applicant-national-rule-export.json')
        try: mc.validate_pair(m,e)
        except mc.ConformanceError as x: assert 'forbidden_normative_layer' in str(x)
        else: raise AssertionError('applicant-country national legal rule accepted')
        m=cv.load_json(FX/'conformance'/'invalid-incompatible-manifest.json'); e=cv.load_json(FX/'member-state-se-export.json')
        try: mc.validate_pair(m,e)
        except mc.ConformanceError as x: assert 'incompatible_controller_protocol' in str(x)
        else: raise AssertionError('incompatible controller protocol accepted')
    results.append('c3_malformed_modules_rejected')

    # Contract boundary rejects executable-style extension keys.
    with tempfile.TemporaryDirectory() as td:
        bad=json.loads((FX/'member-state-se-export.json').read_text()); bad['command']='do-not-run'; p=Path(td)/'bad.json'; p.write_text(json.dumps(bad))
        try: cv.load_json(p)
        except cv.ContractError as e: assert 'forbidden executable-style key' in str(e)
        else: raise AssertionError('executable-style field was accepted')
    results.append('executable_field_rejected')

    # Private data is deliberately disabled in this foundation release.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=td/'state.json'; quiet(cc.cmd_init,init_args(state))
        case=json.loads((FX/'case-input-minimal.json').read_text()); case['privacy_classification']='private'; cp=td/'private.json'; cp.write_text(json.dumps(case))
        expect_error(cc.cmd_accept_case,mut(state,0,input=str(cp)),'private_data_disabled')
    results.append('private_data_disabled')

    # Identity and revision guards.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=td/'state.json'; quiet(cc.cmd_init,init_args(state))
        expect_error(cc.cmd_accept_case,NS(state=str(state),case_id='WRONG',expected_revision=0,input=str(FX/'case-input-minimal.json')),'wrong_case')
        quiet(cc.cmd_accept_case,mut(state,0,input=str(FX/'case-input-minimal.json')))
        expect_error(cc.cmd_register_module,mut(state,0,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json')),'stale_revision')
    results += ['wrong_case_rejected','stale_revision_rejected']

    # Required module gap blocks context; optional module gap remains explicit.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=td/'state.json'; quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(FX/'case-input-minimal.json'))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json')))
        expect_error(cc.cmd_freeze_context,mut(state,2),'missing_required_modules')
    results.append('required_module_gap_blocks')
    with tempfile.TemporaryDirectory() as td:
        state=prepare_to_requirements(td); s=json.loads(Path(state).read_text()); assert s['missing_optional_modules']==['req:xx-local']
    results.append('optional_module_gap_preserved')

    # Optional applicant-country module can be registered against the same controller contract.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=td/'state.json'; quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(FX/'case-input-minimal.json'))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json'))); quiet(cc.cmd_register_module,mut(state,2,manifest=str(FX/'member-state-se-manifest.json'),export=str(FX/'member-state-se-export.json'))); quiet(cc.cmd_register_module,mut(state,3,manifest=str(FX/'applicant-country-xx-manifest.json'),export=str(FX/'applicant-country-xx-export.json'))); quiet(cc.cmd_freeze_context,mut(state,4)); st=json.loads(state.read_text()); assert st['missing_optional_modules']==[]
    results.append('applicant_country_composition')

    # Multi-Member-State topology is representable and can require both national modules.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); case=json.loads((FX/'case-input-minimal.json').read_text()); case['geography']['residence_state']='SE'; case['geography']['work_state']='DE'; case['module_requests']=[{'request_id':'req:se','family':'member_state','jurisdiction':'SE','role':'residence_state','required':True},{'request_id':'req:de','family':'member_state','jurisdiction':'DE','role':'work_state','required':True}]; cp=td/'case.json'; cp.write_text(json.dumps(case)); state=td/'state.json'; quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(cp))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json'))); quiet(cc.cmd_register_module,mut(state,2,manifest=str(FX/'member-state-se-manifest.json'),export=str(FX/'member-state-se-export.json'))); quiet(cc.cmd_register_module,mut(state,3,manifest=str(FX/'member-state-de-manifest.json'),export=str(FX/'member-state-de-export.json'))); quiet(cc.cmd_freeze_context,mut(state,4))
    results.append('multi_member_state_composition')

    # Role matching is exact: a residence-only module cannot satisfy deciding-state work.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); m=cv.load_json(FX/'member-state-se-manifest.json'); m['supported_roles']=['residence_state']; mp=td/'m.json'; mp.write_text(json.dumps(m)); state=td/'state.json'
        quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(FX/'case-input-minimal.json'))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json'))); quiet(cc.cmd_register_module,mut(state,2,manifest=str(mp),export=str(FX/'member-state-se-export.json'))); expect_error(cc.cmd_freeze_context,mut(state,3),'missing_required_modules:req:se')
    results.append('c3_role_specific_module_matching')

    # Applicant-country context must match the requested destination-state profile.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); m=cv.load_json(FX/'applicant-country-xx-manifest.json'); m['destination_state_profiles_available']=['DE']; e=cv.load_json(FX/'applicant-country-xx-export.json'); e['operational_records'][0]['destination_state']='DE'; mp=td/'m.json'; ep=td/'e.json'; mp.write_text(json.dumps(m)); ep.write_text(json.dumps(e)); case=cv.load_json(FX/'case-input-minimal.json'); case['module_requests']=[r for r in case['module_requests'] if r['family']=='applicant_country']; case['module_requests'][0]['required']=True; cp=td/'case.json'; cp.write_text(json.dumps(case)); state=td/'state.json'
        quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(cp))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json'))); quiet(cc.cmd_register_module,mut(state,2,manifest=str(mp),export=str(ep))); expect_error(cc.cmd_freeze_context,mut(state,3),'missing_required_modules:req:xx-local')
    results.append('c3_applicant_destination_profile_matching')

    # Frontier-worker topology composes distinct residence/work/application modules without collapsing roles.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); cp=FX/'conformance'/'case-frontier-worker-topology.json'; cid='CASE-C3-FRONTIER-TOPOLOGY'; state=td/'state.json'; init=NS(state=str(state),case_id=cid,run_id='RUN-C3',profile='cooperative_local',time_of_check='2026-10-06T10:00:00Z'); quiet(cc.cmd_init,init)
        def cm(rev,**kw): b={'state':str(state),'case_id':cid,'expected_revision':rev}; b.update(kw); return NS(**b)
        quiet(cc.cmd_accept_case,cm(0,input=str(cp))); quiet(cc.cmd_register_module,cm(1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json'))); quiet(cc.cmd_register_module,cm(2,manifest=str(FX/'member-state-se-manifest.json'),export=str(FX/'member-state-se-export.json'))); quiet(cc.cmd_register_module,cm(3,manifest=str(FX/'member-state-de-manifest.json'),export=str(FX/'member-state-de-export.json'))); quiet(cc.cmd_register_module,cm(4,manifest=str(FX/'applicant-country-xx-manifest.json'),export=str(FX/'applicant-country-xx-export.json'))); quiet(cc.cmd_freeze_context,cm(5)); st=json.loads(state.read_text()); assert st['missing_optional_modules']==[] and len(st['modules'])==4
    results.append('c3_frontier_worker_multistate_topology')

    # Two modules cannot silently contribute the same reusable record id.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); m=cv.load_json(FX/'member-state-se-manifest.json'); e=cv.load_json(FX/'member-state-se-export.json'); m['module_id']='member-state-se-secondary'; m['supported_roles']=['work_state']; e['module_id']='member-state-se-secondary'; mp=td/'m.json'; ep=td/'e.json'; mp.write_text(json.dumps(m)); ep.write_text(json.dumps(e)); state=td/'state.json'; quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(FX/'case-input-minimal.json'))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json'))); quiet(cc.cmd_register_module,mut(state,2,manifest=str(FX/'member-state-se-manifest.json'),export=str(FX/'member-state-se-export.json'))); expect_error(cc.cmd_register_module,mut(state,3,manifest=str(mp),export=str(ep)),'duplicate_global_record_ids')
    results.append('c3_duplicate_global_ids_rejected')

    # Duplicate producer coverage for the same family/jurisdiction/role is ambiguous and rejected before context freeze.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); m=cv.load_json(FX/'member-state-se-manifest.json'); e=cv.load_json(FX/'member-state-se-export.json'); m['module_id']='member-state-se-overlap'; e['module_id']='member-state-se-overlap'; mp=td/'m.json'; ep=td/'e.json'; mp.write_text(json.dumps(m)); ep.write_text(json.dumps(e)); state=td/'state.json'; quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(FX/'case-input-minimal.json'))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json'))); quiet(cc.cmd_register_module,mut(state,2,manifest=str(FX/'member-state-se-manifest.json'),export=str(FX/'member-state-se-export.json'))); expect_error(cc.cmd_register_module,mut(state,3,manifest=str(mp),export=str(ep)),'ambiguous_module_role_coverage')
    results.append('c3_ambiguous_role_coverage_rejected')

    # Module requests must agree with the typed geography topology instead of silently relabelling a state.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); case=cv.load_json(FX/'case-input-minimal.json'); case['module_requests'][0]['jurisdiction']='DE'; cp=td/'bad-topology.json'; cp.write_text(json.dumps(case)); state=td/'state.json'; quiet(cc.cmd_init,init_args(state)); expect_error(cc.cmd_accept_case,mut(state,0,input=str(cp)),'module_request_geography_mismatch')
    results.append('c3_request_geography_mismatch_rejected')

    # Applicant-country operational records cannot claim destination profiles the manifest does not expose.
    with tempfile.TemporaryDirectory() as td:
        m=cv.load_json(FX/'applicant-country-xx-manifest.json'); e=cv.load_json(FX/'applicant-country-xx-export.json'); e['operational_records'][0]['destination_state']='FR'
        try: mc.validate_pair(m,e)
        except mc.ConformanceError as x: assert 'applicant_operational_destination_outside_profile' in str(x)
        else: raise AssertionError('applicant operational record outside declared destination profile accepted')
    results.append('c3_applicant_record_destination_profile_enforced')

    # Controlled analysis references to C3 route/attack/deadline records are resolved against the registered modules.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=prepare_to_requirements(td); quiet(cc.cmd_update_requirement,mut(state,5,requirement_id='check:regime',status='supported')); ap=td/'analysis.json'; ana=write_analysis(ap,6); ana['findings'][0]['route_refs']=['se:route:missing']; ap.write_text(json.dumps(ana,indent=2)+'\n'); quiet(cc.cmd_propose_analysis,mut(state,6,input=str(ap))); expect_error(cc.cmd_validate_analysis,mut(state,7,input=str(ap),receipt=str(td/'vr.json')),'unknown_route_ids')
    results.append('c3_controlled_analysis_record_refs_enforced')

    # Full release cannot bypass not_checked required work.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=prepare_to_requirements(td); ap=td/'analysis.json'; write_analysis(ap,5)
        quiet(cc.cmd_propose_analysis,mut(state,5,input=str(ap)))
        expect_error(cc.cmd_validate_analysis,mut(state,6,input=str(ap),receipt=str(td/'vr.json')),'full_release_blocked_unresolved')
    results.append('full_release_blocked_when_not_checked')

    # Limited release is allowed with unresolved required work only when limitations are explicit.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=prepare_to_requirements(td); ap=td/'analysis.json'; write_analysis(ap,5,mode='limited',limitations=['Required legal-regime check remains unresolved.']); vr=td/'validation.json'
        quiet(cc.cmd_propose_analysis,mut(state,5,input=str(ap))); quiet(cc.cmd_validate_analysis,mut(state,6,input=str(ap),receipt=str(vr))); rec=json.loads(vr.read_text()); assert rec['release_mode']=='limited' and rec['unresolved_required']==['check:regime']
    results.append('limited_release_preserves_unresolved')

    # Stale required modules block a full release.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=td/'state.json'; quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(FX/'case-input-minimal.json'))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(FX/'core-source-manifest.json'),export=str(FX/'core-source-export.json'))); sm=json.loads((FX/'member-state-se-manifest.json').read_text()); sm['freshness_state']='stale'; smp=td/'stale_manifest.json'; smp.write_text(json.dumps(sm)); quiet(cc.cmd_register_module,mut(state,2,manifest=str(smp),export=str(FX/'member-state-se-export.json'))); quiet(cc.cmd_freeze_context,mut(state,3)); quiet(cc.cmd_set_requirements,mut(state,4,input=str(FX/'requirement-set.json'))); quiet(cc.cmd_update_requirement,mut(state,5,requirement_id='check:regime',status='supported')); ap=td/'analysis.json'; write_analysis(ap,6); quiet(cc.cmd_propose_analysis,mut(state,6,input=str(ap))); expect_error(cc.cmd_validate_analysis,mut(state,7,input=str(ap),receipt=str(td/'vr.json')),'full_release_blocked_freshness')
    results.append('stale_required_module_blocks_full_release')

    # Unknown source references are rejected even when object shape is valid.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=prepare_to_requirements(td); quiet(cc.cmd_update_requirement,mut(state,5,requirement_id='check:regime',status='supported')); ap=td/'analysis.json'; write_analysis(ap,6,['eu:src:fixture','se:src:does-not-exist'])
        quiet(cc.cmd_propose_analysis,mut(state,6,input=str(ap)))
        expect_error(cc.cmd_validate_analysis,mut(state,7,input=str(ap),receipt=str(td/'vr.json')),'unknown_source_ids')
    results.append('unknown_source_reference_rejected')

    # Unauthenticated source representations cannot back rules or controlled analysis.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        bad=json.loads((FX/'core-source-export.json').read_text())
        bad['source_records'][0]['content_kind']='curated_reference_note'
        bad['source_records'][0]['authenticity_state']='reference_only'
        bad['source_records'][0]['status']='unknown'
        ep=td/'export.json'; ep.write_text(json.dumps(bad))
        try: cc.validate_manifest_export(str(FX/'core-source-manifest.json'),str(ep))
        except cc.ControllerError as e: assert 'rule_unusable_source_refs' in str(e)
        else: raise AssertionError('rule backed only by unauthenticated source was accepted')
    results.append('unverified_source_cannot_back_rule')

    # Happy path: optional local gap and optional not_checked requirement do not block full release.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state=prepare_to_requirements(td,'RUN-HAPPY'); quiet(cc.cmd_update_requirement,mut(state,5,requirement_id='check:regime',status='supported')); ap=td/'analysis.json'; write_analysis(ap,6); vr=td/'validation.json'; out=td/'out.md'; rr=td/'release.json'
        quiet(cc.cmd_propose_analysis,mut(state,6,input=str(ap))); quiet(cc.cmd_validate_analysis,mut(state,7,input=str(ap),receipt=str(vr))); quiet(cc.cmd_release,mut(state,8,input=str(ap),receipt=str(vr),output=str(out),release_receipt=str(rr)))
        final=json.loads(Path(state).read_text()); assert final['stage']=='released'; assert out.exists(); rendered=out.read_text(); assert 'Synthetic controlled analysis' in rendered; assert f'controller protocol v{cc.PROTOCOL_VERSION}' in rendered; assert json.loads(rr.read_text())['rendered_sha256']
    results.append('happy_path_release')

    # Source ownership inventory is structurally valid and enforces family ownership.
    src_obj=cv.load_json(FX/'source-inventory-synthetic.json'); src_result=si.validate_inventory(src_obj); assert src_result['source_count']==3
    results.append('source_inventory_valid')
    with tempfile.TemporaryDirectory() as td:
        bad=json.loads((FX/'source-inventory-synthetic.json').read_text()); bad['sources'][0]['canonical_owner_family']='member_state'
        try: si.validate_inventory(bad)
        except si.SourceInventoryError as e: assert 'wrong_owner' in str(e)
        else: raise AssertionError('misowned EU source was accepted')
    results.append('source_owner_boundary_rejected')
    # C1 core source-pack manifest is structurally valid and complete under the verified-representation standard.
    real_manifest=cv.load_json(ROOT/'references'/'source-pack'/'core-source-pack-manifest-0.5.0.json')
    cv.validate_obj('core-source-pack',real_manifest)
    assert real_manifest['logical_source_count']==45 and real_manifest['representation_count']==46
    assert real_manifest['completion_status']=='c1_source_representation_complete'
    assert all(src['canonical_owner_family']=='core' and src['authority_level']=='eu' for src in real_manifest['sources'])
    assert all(src['freshness_state'] in {'current','fixed_verified'} for src in real_manifest['sources'])
    assert not any('swedish_laws' in rep['relative_path'].lower() for src in real_manifest['sources'] for rep in src['representations'])
    tags={tag for src in real_manifest['sources'] for tag in src.get('coverage_tags',[])}
    for tag in {'primacy','direct_effect','soft_law_recommendations','good_administration_general_principle','charter_article_51_scope','dependency_evidence_freedom_of_proof'}: assert tag in tags
    assert sum(1 for src in real_manifest['sources'] if src.get('text_completeness_state')=='verified_source_note')==21
    assert sum(1 for src in real_manifest['sources'] if src.get('text_completeness_state')=='bundled_verified')==24
    assert all('trusted_ingest_sha256' in src for src in real_manifest['sources'])
    results.append('c1_complete_core_source_manifest_truthful')

    # The current pack has no required source-representation blockers; fuller-text acquisition is optional enhancement work.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); (td/'source_manifest.json').write_text(json.dumps(real_manifest)); (td/'PACK_METADATA.json').write_text('{}')
        ip=sti.plan(td); assert ip['blocked_source_count']==0 and ip['sources']==[]
    results.append('source_representation_plan_has_zero_c1_blockers')

    def single_source_pack(root, trusted=None):
        root=Path(root); root.mkdir(parents=True,exist_ok=True)
        m=json.loads(json.dumps(real_manifest)); src=next(x for x in m['sources'] if x['source_id']=='eu:61962cj0026'); m['sources']=[src]; m['logical_source_count']=1
        note=b'# reference note only\n'; rel='sources/reference/eu_61962cj0026.md'; rp=root/rel; rp.parent.mkdir(parents=True,exist_ok=True); rp.write_bytes(note)
        src['representations']=[{'kind':'curated_reference_note','language':'EN','relative_path':rel,'sha256':sti.sha256_bytes(note),'bytes':len(note),'source_policy':'official-reference','update_intent':'verify_identity_and_relevance','original_combined_pack_path':None,'authenticity_state':'reference_only','verification_method':'not_applicable','acquisition_url':None,'final_url':None,'verified_at':None}]
        src['text_completeness_state']='reference_only'; src['trusted_ingest_sha256']=trusted; m['representation_count']=1; m['completion_status']='c1_source_representation_pending'
        (root/'source_manifest.json').write_text(json.dumps(m)); (root/'PACK_METADATA.json').write_text('{}')
        return m

    # Provenance-free offline import stages an unverified candidate and still does not create a verified representation.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); pack=td/'pack'; single_source_pack(pack)
        imp=td/'imports'; imp.mkdir(); sample=imp/'61962CJ0026.pdf'; fake=b'%PDF-1.4\n'+b'A'*5000+b'\n%%EOF\n'; sample.write_bytes(fake)
        out=sti.execute(pack,'import',imp,['eu:61962cj0026'],'2026-10-06',0,False)
        assert out['verified_ingested']==0 and out['candidates_staged']==1 and out['remaining_blockers']==1 and out['status']=='partial'
        changed=json.loads((pack/'source_manifest.json').read_text()); src=changed['sources'][0]
        assert src['text_completeness_state']=='candidate_unverified'
        assert not any(r.get('kind')=='bundled_text' for r in src['representations'])
        assert any(r.get('kind')=='candidate_text' and r.get('authenticity_state')=='unverified_candidate' for r in src['representations'])
        assert stg.inspect(pack)['blocked_source_count']==1
    results.append('offline_import_without_trust_stays_blocked')

    # A pinned digest remains a stronger optional trust anchor for fuller text: exact match promotes, mismatch rejects.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); fake=b'%PDF-1.4\n'+b'B'*5000+b'\n%%EOF\n'; pack=td/'pack'; single_source_pack(pack,sti.sha256_bytes(fake))
        imp=td/'imports'; imp.mkdir(); (imp/'61962CJ0026.pdf').write_bytes(fake)
        out=sti.execute(pack,'import',imp,['eu:61962cj0026'],'2026-10-06',0,False)
        assert out['verified_ingested']==1 and out['candidates_staged']==0 and out['remaining_blockers']==0 and out['status']=='complete'
        changed=json.loads((pack/'source_manifest.json').read_text()); src=changed['sources'][0]
        assert src['text_completeness_state']=='bundled_verified'
        assert any(r.get('kind')=='bundled_text' and r.get('verification_method')=='pinned_sha256_match' for r in src['representations'])
        assert stg.inspect(pack)['status']=='complete'
    results.append('offline_import_exact_pinned_digest_promotes')

    with tempfile.TemporaryDirectory() as td:
        td=Path(td); pack=td/'pack'; single_source_pack(pack,'0'*64)
        imp=td/'imports'; imp.mkdir(); (imp/'61962CJ0026.pdf').write_bytes(b'%PDF-1.4\n'+b'C'*5000+b'\n%%EOF\n')
        out=sti.execute(pack,'import',imp,['eu:61962cj0026'],'2026-10-06',0,False)
        assert out['verified_ingested']==0 and out['failed']==1 and out['remaining_blockers']==1
    results.append('offline_import_digest_mismatch_rejected')

    # Official fetch URL policy remains available for optional fuller-text acquisition.
    sample=next(x for x in real_manifest['sources'] if x['source_id']=='eu:61962cj0026')
    sti.validate_official_url(sample,sti.source_download_url(sample),initial=True)
    try: sti.validate_official_url(sample,'https://example.com/fake.pdf',initial=False)
    except ValueError: pass
    else: raise AssertionError('untrusted redirect host accepted')
    try: sti.require_date('')
    except ValueError: pass
    else: raise AssertionError('missing verification date accepted')
    results.append('official_fetch_provenance_policy_enforced')

    # The completed pack adapts deterministically; verified notes remain distinguishable from full bundled text.
    adapted_manifest, adapted_export = csa.build_objects(real_manifest)
    assert adapted_manifest['freshness_state']=='current' and adapted_manifest['known_gap_ids']==[]
    assert len(adapted_export['source_records'])==45
    note_record=next(x for x in adapted_export['source_records'] if x['source_id']=='eu:61962cj0026')
    assert note_record['content_kind']=='verified_source_note' and note_record['authenticity_state']=='verified_identity_version' and note_record['status']=='current'
    assert not [g for g in adapted_export['gap_records'] if g['gap_id'].startswith('eu:gap:source_representation:')]
    cv.validate_obj('module-manifest',adapted_manifest); cv.validate_obj('module-export',adapted_export)
    assert csa.build_objects(real_manifest)==(adapted_manifest,adapted_export)
    results.append('c1_complete_source_pack_adapter_valid')

    # Verified source notes may support scoped reviewed/candidate interpretations, never direct_text.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); export=json.loads((FX/'core-source-export.json').read_text())
        export['source_records'][0]['content_kind']='verified_source_note'; export['source_records'][0]['authenticity_state']='verified_identity_version'; export['source_records'][0]['status']='current'
        rule=export['rule_records'][0]; rule['interpretation_status']='reviewed_interpretation'; rule.pop('text_source_ref',None); rule['support_scope']='Identity/version-verified indexed proposition scope; exact wording not asserted.'
        ep=td/'export.json'; ep.write_text(json.dumps(export)); cc.validate_manifest_export(str(FX/'core-source-manifest.json'),str(ep))
    results.append('verified_source_note_can_back_scoped_reviewed_rule')

    with tempfile.TemporaryDirectory() as td:
        td=Path(td); export=json.loads((FX/'core-source-export.json').read_text())
        export['source_records'][0]['content_kind']='verified_source_note'; export['source_records'][0]['authenticity_state']='verified_identity_version'; export['source_records'][0]['status']='current'
        rule=export['rule_records'][0]; rule['interpretation_status']='reviewed_interpretation'; rule.pop('text_source_ref',None); rule['support_scope']=None
        ep=td/'export.json'; ep.write_text(json.dumps(export)); cv.validate_obj('module-export',export)
        try: cc.validate_manifest_export(str(FX/'core-source-manifest.json'),str(ep))
        except cc.ControllerError as e:
            if 'note_backed_rule_requires_support_scope' not in str(e): raise
        else: raise AssertionError('note-backed reviewed rule without support_scope was accepted')
    results.append('note_backed_rule_requires_support_scope')

    # Representation-scope laundering is rejected even if a note has the correct logical source identity.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); export=json.loads((FX/'core-source-export.json').read_text())
        export['source_records'][0]['content_kind']='verified_source_note'; export['source_records'][0]['authenticity_state']='verified_identity_version'; export['source_records'][0]['status']='current'
        export['rule_records'][0]['proposition']='The moon is made of cheese.'
        ep=td/'export.json'; ep.write_text(json.dumps(export)); cv.validate_obj('module-export',export)
        try: cc.validate_manifest_export(str(FX/'core-source-manifest.json'),str(ep))
        except cc.ControllerError as e:
            if 'direct_text_requires_full_text_source' not in str(e): raise
        else: raise AssertionError('direct_text from verified source note was accepted')
    results.append('direct_text_from_verified_note_rejected')

    # Live-current freshness and representation completeness are independent dimensions.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); mp=td/'manifest.json'; ep=td/'export.json'; mp.write_text(json.dumps(adapted_manifest)); ep.write_text(json.dumps(adapted_export))
        case=json.loads((FX/'case-input-minimal.json').read_text()); case['module_requests']=[]; case.pop('core_freshness_requirement',None); cp=td/'case.json'; cp.write_text(json.dumps(case))
        state=td/'state.json'; quiet(cc.cmd_init,init_args(state)); quiet(cc.cmd_accept_case,mut(state,0,input=str(cp))); quiet(cc.cmd_register_module,mut(state,1,manifest=str(mp),export=str(ep))); quiet(cc.cmd_freeze_context,mut(state,2)); st=json.loads(state.read_text()); assert st['freshness_blocked_required_modules']==[] and st['stale_required_modules']==[]; assert 'eu:61962cj0026' in st['reference_index']['usable_source_ids'] and 'eu:61962cj0026' not in st['reference_index']['authoritative_source_ids']
    results.append('live_current_freshness_and_c1_representation_complete')

    # A baseline-only source cannot be silently upgraded by the adapter.
    baseline_manifest=json.loads(json.dumps(real_manifest)); baseline_manifest['sources'][0]['freshness_state']='baseline_verified_not_live_rechecked'
    baseline_adapted,_=csa.build_objects(baseline_manifest); assert baseline_adapted['freshness_state']=='baseline_verified_not_live_rechecked'
    results.append('adapter_preserves_unrechecked_baseline_state')

    # Requirement completeness preserves status, reason, scope, and detail instead of collapsing all blocks.
    with tempfile.TemporaryDirectory() as td:
        state=prepare_to_requirements(td); quiet(cc.cmd_update_requirement,mut(state,5,requirement_id='check:regime',status='blocked',reason='insufficient_evidence',detail='identity evidence missing')); st=json.loads(Path(state).read_text()); req=st['requirements']['check:regime']; assert req['status']=='blocked' and req['reason']=='insufficient_evidence' and req['scope']=='case' and req['detail']=='identity evidence missing'
        expect_error(cc.cmd_update_requirement,mut(state,6,requirement_id='check:regime',status='blocked'),'blocked_requirement_requires_reason')
    results.append('completeness_reason_scope_preserved')

    # C3 completeness vocabulary treats not_applicable as resolved and keeps status/reason orthogonal.
    with tempfile.TemporaryDirectory() as td:
        state=prepare_to_requirements(td); quiet(cc.cmd_update_requirement,mut(state,5,requirement_id='check:regime',status='not_applicable')); st=json.loads(Path(state).read_text()); req=st['requirements']['check:regime']; assert req['status']=='not_applicable' and req['reason']=='none'
        rec={'contract_version':'0.2.0','requirement_id':'check:regime','status':'not_applicable','reason':'none','scope':'case','detail':''}; cv.validate_obj('completeness-record',rec)
    results.append('c3_completeness_vocabulary_frozen')

    # Element model validates cross-references and exposes review-only versus mechanical invariants.
    catalog,interactions,invariants=em.load_model(); assert catalog['model_version']=='0.2.0' and len(catalog['elements'])==114 and len(interactions['rules'])==25 and len(invariants['invariants'])==24
    results.append('element_model_crossrefs_valid')

    valid_atomic=['topology-distinct-roles','deadline-complete','unsupported-operator-explicit','valid-local-context']
    for name in valid_atomic:
        obj=cv.load_json(FX/'elements'/f'{name}.json'); out=em.check_bundle(obj,catalog,invariants); assert out['status']=='valid'
    results.append('atomic_element_fixtures_valid')

    invalid_atomic={
        'deadline-missing-trigger':'deadline_missing_trigger',
        'incomplete-no-problem':'incomplete_state_cannot_support_no_problem',
        'stale-current-support':'stale_source_cannot_support_current_law',
        'national-rule-unlinked':'national_rule_missing_source_ref',
        'unsupported-operator-hidden':'unsupported_operator_not_recorded',
        'outbound-no-purpose':'outbound_eligibility_missing_purpose',
        'approval-recipient-changed':'changed_recipient_requires_approval_invalidation',
        'case-data-module-asset':'case_workspace_data_in_distributable_module_asset',
        'applicant-overall-conclusion':'supplier_not_allowed:conclusion.overall:applicant_country',
    }
    for name,needle in invalid_atomic.items():
        obj=cv.load_json(FX/'elements'/f'{name}.json')
        try: em.check_bundle(obj,catalog,invariants)
        except em.ElementModelError as e:
            if needle not in str(e): raise AssertionError(f'{name}: expected {needle!r}, got {e!r}')
        else: raise AssertionError(f'{name}: invalid atomic fixture was accepted')
    results.append('atomic_invariant_rejections')

    def c2_bundle(items,bid='C2-ATOMIC'):
        return {'model_version':'0.2.0','bundle_id':bid,'elements':[{'element_id':eid,'value':val,'supplied_by':sup,'provenance_kind':'policy'} for eid,val,sup in items]}

    c2_invalid=[
      (c2_bundle([('legal_principle.id','primacy','core'),('legal_principle.applicability_status','applicable','core')],'C2-PRINCIPLE'),'legal_principle_missing_source_ref'),
      (c2_bundle([('legal_regime.charter','applicable','core'),('legal_regime.eu_law_scope_established',False,'core')],'C2-CHARTER'),'charter_applicability_missing_eu_scope'),
      (c2_bundle([('evidence.proof_restriction_status','asserted','core')],'C2-PROOF'),'proof_restriction_missing_source_ref'),
      (c2_bundle([('attack_angle.assessment_status','supported','core'),('attack_angle.evidence_state','sufficient','core')],'C2-ATTACK'),'supported_attack_angle_missing_source_ref'),
      (c2_bundle([('source.representation_kind','verified_source_note','core'),('conclusion.exact_wording_supported',True,'core')],'C2-QUOTE'),'verified_source_note_cannot_support_exact_wording'),
      (c2_bundle([('time.duration_days',12,'deterministic_calculation')],'C2-TIME'),'duration_missing_typed_event'),
    ]
    for obj,needle in c2_invalid:
        try: em.check_bundle(obj,catalog,invariants)
        except em.ElementModelError as e:
            if needle not in str(e): raise AssertionError(f'expected {needle!r}, got {e!r}')
        else: raise AssertionError(f'C2 atomic invalid accepted: {needle}')
    valid_c2=c2_bundle([
      ('legal_principle.id','primacy','core'),('legal_principle.applicability_status','applicable','core'),('legal_principle.source_ref','eu:61964cj0006','core'),
      ('legal_regime.charter','applicable','core'),('legal_regime.eu_law_scope_established',True,'core'),
      ('source.representation_kind','verified_source_note','core'),('conclusion.exact_wording_supported',False,'core'),('conclusion.pinpoint_supported',False,'core'),
      ('time.duration_days',12,'deterministic_calculation'),('time.event_type','lodgement','case_workspace'),('time.event_date','2026-09-22','case_workspace')
    ],'C2-VALID')
    assert em.check_bundle(valid_c2,catalog,invariants)['status']=='valid'
    results.append('c2_atomic_invariant_boundaries')

    support=cv.load_json(ROOT/'references'/'elements'/'source-support-map.json'); cv.validate_obj('source-support-map',support)
    support_req=cv.load_json(ROOT/'references'/'elements'/'source-support-requirements.json'); cv.validate_obj('source-support-requirements',support_req)
    active_manifest=cv.load_json(ROOT/'references'/'source-pack'/'core-source-pack-manifest-0.6.1.json')
    assert len(support['records'])==46 and {r['source_id'] for r in support['records']}=={s['source_id'] for s in active_manifest['sources']}
    em.validate_model(catalog,interactions,invariants,support,support_req)
    results.append('c2_source_support_map_complete')

    # A hollow all-to-one map must fail the independent reverse-coverage baseline.
    collapsed=copy.deepcopy(support)
    for rec in collapsed['records']:
        rec['targets']=[{'target_type':'element','target_id':'legal_principle.id','support_role':'foundation'}]
    try: em.validate_model(catalog,interactions,invariants,collapsed,support_req)
    except em.ElementModelError as e:
        if 'source_support_required_' not in str(e): raise
    else: raise AssertionError('collapsed all-to-one source-support map was accepted')
    results.append('c2_source_support_reverse_coverage_enforced')


    # C4 privacy schemas and deterministic three-view construction are valid for synthetic/public data.
    pdata=cv.load_json(FX/'privacy'/'protected-synthetic.json'); ppolicy=cv.load_json(FX/'privacy'/'privacy-policy.json')
    cv.validate_obj('protected-data',pdata); cv.validate_obj('privacy-policy',ppolicy)
    protected,analysis_view,outbound=tc.build_views(pdata,ppolicy,'OUT-C4-FIX','compliance_feedback','feedback_service','https://feedback.example.test/ingest','feedback')
    assert len(protected['fields'])==4 and len(analysis_view['fields'])==4
    assert {x['field_id'] for x in outbound['fields']}=={'event.date','case.issue','case.topology'}
    assert next(x for x in outbound['fields'] if x['field_id']=='event.date')['value']=='2026-10'
    assert outbound['eligible'] is True and outbound['minimisation_summary']['dropped_fields']==1 and outbound['linkability_score']<=ppolicy['max_linkability_score']
    results.append('c4_three_view_minimisation_valid')

    # C4 transformations are semantic/type bounded: date transforms cannot slice arbitrary identifiers or malformed strings.
    bad_policy=copy.deepcopy(ppolicy)
    bad_policy['purpose_profiles'][0]['field_rules'].append({'field_id':'person.name','transform':'date_to_year'})
    try: tc.build_views(pdata,bad_policy,'OUT-C4-BAD-ID','compliance_feedback','feedback_service','https://feedback.example.test/ingest','feedback')
    except tc.TrustControlError as e:
        assert 'direct_identifier_transform_forbidden:person.name:date_to_year' in str(e)
    else: raise AssertionError('direct identifier substring transform was accepted')
    results.append('c4_direct_identifier_transform_smuggling_rejected')

    malformed=copy.deepcopy(pdata)
    next(f for f in malformed['fields'] if f['field_id']=='event.date')['value']='UNIQUE-ID-ABCDEF'
    try: tc.build_views(malformed,ppolicy,'OUT-C4-BAD-DATE','compliance_feedback','feedback_service','https://feedback.example.test/ingest','feedback')
    except tc.TrustControlError as e:
        assert 'date_to_month_requires_iso_temporal:event.date' in str(e)
    else: raise AssertionError('malformed date transform was accepted')
    results.append('c4_malformed_date_transform_rejected')

    invalid_month=copy.deepcopy(pdata)
    next(f for f in invalid_month['fields'] if f['field_id']=='event.date')['value']='2026-99'
    try: tc.build_views(invalid_month,ppolicy,'OUT-C4-BAD-MONTH','compliance_feedback','feedback_service','https://feedback.example.test/ingest','feedback')
    except tc.TrustControlError as e:
        assert 'date_to_month_requires_iso_temporal:event.date' in str(e)
    else: raise AssertionError('invalid ISO month was accepted')
    results.append('c4_invalid_iso_temporal_rejected')

    # Private data stays disabled until host/runtime enforcement is independently demonstrated.
    private=copy.deepcopy(pdata); private['privacy_classification']='private'
    try: tc.build_views(private,ppolicy,'OUT-PRIVATE','compliance_feedback','feedback_service','https://feedback.example.test/ingest','feedback')
    except tc.TrustControlError as e:
        if 'private_data_host_enforcement_not_verified' not in str(e): raise
    else: raise AssertionError('private data view construction was enabled without host enforcement')
    results.append('c4_private_data_host_gate_enforced')

    # Outbound preparation is revision-bound and exact view changes invalidate preparation.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state,_,_,_,_=prepare_to_release(td); st=json.loads(state.read_text()); view=c4_view_for_state(state); vp=td/'outbound.json'; vp.write_text(json.dumps(view))
        stale=copy.deepcopy(view); stale['bound_case_revision']=st['revision']-1; sp=td/'stale.json'; sp.write_text(json.dumps(stale)); expect_error(cc.cmd_prepare_outbound,mut(state,st['revision'],input=str(sp)),'outbound_stale_revision')
        quiet(cc.cmd_prepare_outbound,mut(state,st['revision'],input=str(vp))); st=json.loads(state.read_text()); assert st['trust_controls']['outbound_records']['OUT-C4']['view_sha256']==cv.digest_obj(view)
    results.append('c4_outbound_revision_and_digest_binding')

    # Approval is purpose/recipient/action/view bound; destination changes invalidate it.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state,_,_,_,_=prepare_to_release(td); st=json.loads(state.read_text()); view=c4_view_for_state(state); vp=td/'outbound.json'; vp.write_text(json.dumps(view)); quiet(cc.cmd_prepare_outbound,mut(state,st['revision'],input=str(vp))); st=json.loads(state.read_text()); rec=st['trust_controls']['outbound_records']['OUT-C4']
        bad=td/'bad-approval.json'; write_approval(bad,rec,'APR-BAD',destination='https://other.example.test/ingest'); expect_error(cc.cmd_authorize_outbound,mut(state,st['revision'],outbound_id='OUT-C4',approval=str(bad),time_of_check='2026-10-06T10:06:00Z'),'approval_destination_mismatch')
        good=td/'approval.json'; write_approval(good,rec,'APR-1'); quiet(cc.cmd_authorize_outbound,mut(state,st['revision'],outbound_id='OUT-C4',approval=str(good),time_of_check='2026-10-06T10:06:00Z')); st=json.loads(state.read_text()); assert st['trust_controls']['outbound_records']['OUT-C4']['delivery_state']=='authorized'
        serialized=state.read_text(); assert 'https://feedback.example.test/ingest' not in serialized and 'user:synthetic' not in serialized
    results.append('c4_approval_binding_and_privacy_safe_state')

    # Outcome-unknown never retries blindly: a separately bound retry approval is required and attempts are bounded.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state,_,_,_,_=prepare_to_release(td); st=json.loads(state.read_text()); view=c4_view_for_state(state); vp=td/'outbound.json'; vp.write_text(json.dumps(view)); quiet(cc.cmd_prepare_outbound,mut(state,st['revision'],input=str(vp))); st=json.loads(state.read_text()); rec=st['trust_controls']['outbound_records']['OUT-C4']; ap=td/'approval.json'; write_approval(ap,rec,'APR-1'); quiet(cc.cmd_authorize_outbound,mut(state,st['revision'],outbound_id='OUT-C4',approval=str(ap),time_of_check='2026-10-06T10:06:00Z')); st=json.loads(state.read_text()); quiet(cc.cmd_begin_delivery,mut(state,st['revision'],outbound_id='OUT-C4',time_of_check='2026-10-06T10:07:00Z')); st=json.loads(state.read_text()); quiet(cc.cmd_record_delivery,mut(state,st['revision'],outbound_id='OUT-C4',result='outcome_unknown')); st=json.loads(state.read_text()); expect_error(cc.cmd_begin_delivery,mut(state,st['revision'],outbound_id='OUT-C4',time_of_check='2026-10-06T10:08:00Z'),'retry_not_authorized')
        rp=td/'retry.json'; write_approval(rp,rec,'APR-2',decision='retry',approved_at='2026-10-06T10:09:00Z'); quiet(cc.cmd_authorize_retry,mut(state,st['revision'],outbound_id='OUT-C4',approval=str(rp),time_of_check='2026-10-06T10:10:00Z')); st=json.loads(state.read_text()); quiet(cc.cmd_begin_delivery,mut(state,st['revision'],outbound_id='OUT-C4',time_of_check='2026-10-06T10:11:00Z')); st=json.loads(state.read_text()); quiet(cc.cmd_record_delivery,mut(state,st['revision'],outbound_id='OUT-C4',result='outcome_unknown')); st=json.loads(state.read_text()); expect_error(cc.cmd_authorize_retry,mut(state,st['revision'],outbound_id='OUT-C4',approval=str(rp),time_of_check='2026-10-06T10:12:00Z'),'delivery_attempt_budget_exhausted')
    results.append('c4_no_blind_retry_and_attempt_budget')

    # Revocation creates a lifecycle tombstone and blocks use of the revoked approval.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state,_,_,_,_=prepare_to_release(td); st=json.loads(state.read_text()); view=c4_view_for_state(state); vp=td/'outbound.json'; vp.write_text(json.dumps(view)); quiet(cc.cmd_prepare_outbound,mut(state,st['revision'],input=str(vp))); st=json.loads(state.read_text()); rec=st['trust_controls']['outbound_records']['OUT-C4']; ap=td/'approval.json'; write_approval(ap,rec,'APR-1'); quiet(cc.cmd_authorize_outbound,mut(state,st['revision'],outbound_id='OUT-C4',approval=str(ap),time_of_check='2026-10-06T10:06:00Z')); st=json.loads(state.read_text()); quiet(cc.cmd_revoke_approval,mut(state,st['revision'],approval_id='APR-1')); st=json.loads(state.read_text()); assert st['trust_controls']['lifecycle_epoch']==1 and 'APR-1' in st['trust_controls']['approval_tombstones']; expect_error(cc.cmd_begin_delivery,mut(state,st['revision'],outbound_id='OUT-C4',time_of_check='2026-10-06T10:07:00Z'),'delivery_not_authorized')
    results.append('c4_revocation_tombstone_enforced')

    # Checkpoints are integrity-bound to the exact current state and lifecycle epoch; stale checkpoints are rejected.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state,_,_,_,_=prepare_to_release(td); st=json.loads(state.read_text()); cp=td/'checkpoint.json'; quiet(cc.cmd_checkpoint,mut(state,st['revision'],checkpoint=str(cp))); quiet(cc.cmd_validate_checkpoint,NS(state=str(state),checkpoint=str(cp)))
        view=c4_view_for_state(state); vp=td/'outbound.json'; vp.write_text(json.dumps(view)); quiet(cc.cmd_prepare_outbound,mut(state,st['revision'],input=str(vp))); st=json.loads(state.read_text()); expect_error(cc.cmd_validate_checkpoint,NS(state=str(state),checkpoint=str(cp)),'checkpoint_not_current_revision')
    results.append('c4_checkpoint_currentness_enforced')

    # Dependency pins travel into validation/release receipts without changing the frozen producer contract.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); state,_,vr,_,rr=prepare_to_release(td); st=json.loads(state.read_text()); v=json.loads(vr.read_text()); r=json.loads(rr.read_text()); assert st['dependency_pins']['controller_protocol']=='0.3.0' and st['dependency_pins']['trust_profile']=='0.1.0'; assert v['dependency_pins_sha256']==cv.digest_obj(st['dependency_pins']) and r['dependency_pins_sha256']==cv.digest_obj(st['dependency_pins'])
    results.append('c4_dependency_pins_bound_to_receipts')

    # C5a topology preserves distinct state roles and creates only structural candidates.
    c5_frontier_case=cv.load_json(FX/'c5a'/'case-frontier.json')
    c5_frontier_elements=cv.load_json(FX/'c5a'/'elements-frontier.json')
    topology=te.build_topology(c5_frontier_case,c5_frontier_elements)
    assert topology['resolution_status']=='ready'
    assert topology['roles']['residence_state']=='SE' and topology['roles']['work_state']=='DE' and topology['roles']['application_country']=='TR'
    assert topology['contexts']['cross_border_work']['status']=='candidate' and topology['contexts']['cross_border_work']['review_required'] is True
    assert topology['contexts']['returnee']['status']=='not_indicated'
    assert {x['status'] for x in topology['module_request_checks']}=={'matched'}
    cv.validate_obj('topology-resolution',topology)
    results.append('c5a_topology_frontier_roles_preserved')

    # A duplicate topology role that disagrees across bound inputs blocks the topology instead of choosing one silently.
    conflicting=copy.deepcopy(c5_frontier_elements)
    conflicting['bundle_id']='c5a-conflicting-topology'
    conflicting['elements'].append({'element_id':'geography.residence_state','value':'DE','supplied_by':'case_workspace','provenance_kind':'user_assertion'})
    blocked_topology=te.build_topology(c5_frontier_case,conflicting)
    assert blocked_topology['resolution_status']=='blocked'
    assert any(x['code']=='role_value_conflict' and x['role']=='residence_state' for x in blocked_topology['conflicts'])
    results.append('c5a_topology_conflict_blocks')

    # C5a private-data input remains disabled at the engine boundary as well as in the controller.
    private_case=copy.deepcopy(c5_frontier_case); private_case['privacy_classification']='private'
    try: te.build_topology(private_case,c5_frontier_elements)
    except te.TopologyError as e: assert 'private_data_disabled' in str(e)
    else: raise AssertionError('C5a topology accepted private data')
    results.append('c5a_private_data_gate_preserved')

    # Missing/unnormalized EU-citizen status blocks Directive candidate generation rather than inferring applicability.
    c5_missing=cv.load_json(FX/'c5a'/'elements-missing-eu-status.json')
    missing_topology=te.build_topology(c5_frontier_case,c5_missing)
    missing_regimes=ra.build_candidates(c5_frontier_case,missing_topology,c5_missing)
    d38=next(x for x in missing_regimes['candidates'] if x['element_id']=='legal_regime.directive_2004_38')
    assert d38['disposition']=='blocked' and 'person_status.eu_citizen_status' in d38['missing_element_ids']
    assert missing_regimes['final_applicability']=='not_determined'
    results.append('c5a_directive_candidate_requires_explicit_eu_status')

    # An arbitrary status string is unresolved, not silently treated as positive and not mislabeled as a missing element.
    unnormalized=copy.deepcopy(c5_frontier_elements)
    unnormalized['bundle_id']='c5a-unnormalized-eu-status'
    next(x for x in unnormalized['elements'] if x['element_id']=='person_status.eu_citizen_status')['value']='German citizen'
    unnormalized_topology=te.build_topology(c5_frontier_case,unnormalized)
    unnormalized_regimes=ra.build_candidates(c5_frontier_case,unnormalized_topology,unnormalized)
    d38_un=next(x for x in unnormalized_regimes['candidates'] if x['element_id']=='legal_regime.directive_2004_38')
    assert d38_un['disposition']=='blocked' and d38_un['missing_element_ids']==[]
    assert 'relevant_union_citizen_status_not_normalized' in d38_un['rationale_codes']
    assert any(x['code']=='relevant_union_citizen_status_not_normalized' for x in unnormalized_regimes['unresolved'])
    results.append('c5a_unnormalized_eu_status_fails_closed')

    # Applicant-country destination metadata cannot contradict the intended/deciding destination topology.
    bad_destination=copy.deepcopy(c5_frontier_case)
    next(x for x in bad_destination['module_requests'] if x['family']=='applicant_country')['destination_state']='DE'
    bad_destination_topology=te.build_topology(bad_destination,c5_frontier_elements)
    assert bad_destination_topology['resolution_status']=='blocked'
    assert any(x['code']=='applicant_destination_topology_mismatch' and x['role']=='destination_state' and x['bound_value']=='SE' and x['conflicting_value']=='DE' for x in bad_destination_topology['conflicts'])
    results.append('c5a_applicant_destination_mismatch_blocks')

    # Visa/Schengen candidates are generated without collapsing their interaction with free-movement law.
    frontier_regimes=ra.build_candidates(c5_frontier_case,topology,c5_frontier_elements)
    cand={x['element_id']:x for x in frontier_regimes['candidates']}
    assert cand['legal_regime.directive_2004_38']['disposition']=='candidate'
    assert cand['legal_regime.visa_code']['disposition']=='candidate'
    assert cand['legal_regime.schengen']['disposition']=='candidate'
    assert frontier_regimes['interactions'][0]['status']=='review_required'
    assert frontier_regimes['final_applicability']=='not_determined'
    results.append('c5a_visa_schengen_and_directive_candidates_preserved')

    # Returnee context remains a downstream legal-review candidate and exposes the primary-source gap.
    c5_returnee_case=cv.load_json(FX/'c5a'/'case-returnee.json')
    c5_returnee_elements=cv.load_json(FX/'c5a'/'elements-returnee.json')
    returnee_topology=te.build_topology(c5_returnee_case,c5_returnee_elements)
    returnee_regimes=ra.build_candidates(c5_returnee_case,returnee_topology,c5_returnee_elements)
    assert returnee_topology['contexts']['returnee']['status']=='candidate'
    assert returnee_regimes['returnee_review']['status']=='candidate' and returnee_regimes['returnee_review']['primary_source_gap'] is True
    assert any(x['code']=='returnee_primary_tfeu_source_gap' for x in returnee_regimes['unresolved'])
    assert returnee_regimes['final_applicability']=='not_determined'
    results.append('c5a_returnee_context_preserved_without_final_conclusion')

    # Regime applicability is cryptographically bound to the exact topology/element inputs.
    stale_topology=copy.deepcopy(topology); stale_topology['bound_case_sha256']='0'*64
    try: ra.build_candidates(c5_frontier_case,stale_topology,c5_frontier_elements)
    except ra.RegimeError as e: assert 'topology_case_binding_mismatch' in str(e)
    else: raise AssertionError('stale topology binding accepted')
    try: ra.build_candidates(c5_frontier_case,topology,c5_missing)
    except ra.RegimeError as e: assert 'topology_element_bundle_binding_mismatch' in str(e)
    else: raise AssertionError('different element bundle accepted against bound topology')
    results.append('c5a_topology_and_element_bindings_enforced')

    # An explicit frontier-worker-context negative cannot erase objective residence/work divergence.
    frontier_false=copy.deepcopy(c5_frontier_elements)
    frontier_false['bundle_id']='c5a-frontier-false-structural-difference'
    next(x for x in frontier_false['elements'] if x['element_id']=='movement.frontier_worker_context')['value']=False
    frontier_false_topology=te.build_topology(c5_frontier_case,frontier_false)
    assert frontier_false_topology['contexts']['cross_border_work']['status']=='candidate'
    assert any(x['code']=='frontier_context_conflicts_with_structural_topology' for x in frontier_false_topology['unresolved'])
    results.append('c5a_frontier_false_cannot_erase_structural_difference')

    # Known jurisdiction aliases canonicalize before equality checks, so SE and Sweden are not a conflict.
    alias_elements=copy.deepcopy(c5_frontier_elements)
    alias_elements['bundle_id']='c5a-jurisdiction-alias'
    alias_elements['elements'].append({'element_id':'geography.residence_state','value':'Sweden','supplied_by':'case_workspace','provenance_kind':'user_assertion'})
    alias_topology=te.build_topology(c5_frontier_case,alias_elements)
    assert alias_topology['resolution_status']=='ready' and alias_topology['roles']['residence_state']=='SE'
    assert any(x['input']=='Sweden' and x['canonical']=='SE' for x in alias_topology['jurisdiction_normalizations'])
    jurisdiction_registry=cv.load_json(ROOT/'references'/'jurisdictions'/'country-aliases.json')
    assert alias_topology['jurisdiction_registry_version']==jurisdiction_registry['registry_version']
    assert alias_topology['jurisdiction_registry_sha256']==cv.digest_obj(jurisdiction_registry)
    results.append('c5a_jurisdiction_alias_canonicalization')

    # Family-member signals without explicit actor scope must fail closed instead of assigning a generic EU-status value to the wrong person.
    family_elements=cv.load_json(FX/'c5a'/'elements-family-member-unscoped.json')
    family_topology=te.build_topology(c5_frontier_case,family_elements)
    family_unscoped=ra.build_candidates(c5_frontier_case,family_topology,family_elements)
    family_d38=next(x for x in family_unscoped['candidates'] if x['element_id']=='legal_regime.directive_2004_38')
    assert family_d38['disposition']=='blocked' and 'actor_scope_required_for_family_member_case' in family_d38['rationale_codes']
    assert any(x['code']=='actor_scope_required_for_family_member_case' for x in family_unscoped['unresolved'])
    results.append('c5a_family_member_unscoped_actor_scope_fails_closed')

    # Explicit applicant/relevant-Union-citizen scope permits a family-member Directive review candidate without changing final applicability.
    family_actors=cv.load_json(FX/'c5a'/'actors-family-member.json')
    cv.validate_obj('actor-context',family_actors)
    family_scoped=ra.build_candidates(c5_frontier_case,family_topology,family_elements,actor_context=family_actors)
    scoped_d38=next(x for x in family_scoped['candidates'] if x['element_id']=='legal_regime.directive_2004_38')
    assert scoped_d38['disposition']=='candidate' and 'actor_scoped_family_relationship' in scoped_d38['rationale_codes']
    assert family_scoped['actor_scope']['applicant_actor_id']=='actor:applicant' and family_scoped['actor_scope']['union_citizen_actor_id']=='actor:union-citizen'
    assert family_scoped['bound_actor_context_sha256']==cv.digest_obj(family_actors) and family_scoped['final_applicability']=='not_determined'
    results.append('c5a_family_member_actor_scope_candidate')

    # Every emitted C5a EU/common source hint resolves to the bundled C1 source pack; national content remains module-owned.
    source_ids={s['source_id'] for s in real_manifest['sources']}
    for c in frontier_regimes['candidates']:
        assert set(c['source_hint_refs']) <= source_ids
    assert set(frontier_regimes['returnee_review']['source_hint_refs']) <= source_ids
    assert cand['legal_regime.national_procedure']['source_hint_refs']==[] and cand['legal_regime.national_procedure']['module_role_hints']
    cv.validate_obj('legal-regime-candidates',frontier_regimes)
    results.append('c5a_source_hints_resolve_and_national_boundary_preserved')


    # C5b principle catalogue/context schemas are valid and all catalogue sources resolve to the C1 pack.
    principle_catalog=cv.load_json(ROOT/'references'/'principles'/'principle-catalog.json'); cv.validate_obj('principle-catalog',principle_catalog)
    c5b_principles_context=cv.load_json(FX/'c5b'/'context-principles.json'); cv.validate_obj('c5b-context',c5b_principles_context)
    principle_ids=[p['principle_id'] for p in principle_catalog['principles']]
    assert len(principle_ids)==len(set(principle_ids))
    assert {r for p in principle_catalog['principles'] for r in p['source_refs']} <= source_ids
    results.append('c5b_principle_catalog_sources_resolve')

    # Build a scope-established C5a chain for C5b tests.
    c5b_elements=cv.load_json(FX/'c5b'/'elements-eu-scope.json')
    c5b_topology=te.build_topology(c5_frontier_case,c5b_elements)
    c5b_regimes=ra.build_candidates(c5_frontier_case,c5b_topology,c5b_elements)

    # Coexisting Directive/Visa Code candidates stay an unresolved lex-specialis question; binding-force metadata is not an automatic winner rule.
    c5b_base=hp.build(c5_frontier_case,c5b_regimes,c5b_elements)
    lex=next(x for x in c5b_base['hierarchy_relationships'] if x['relationship_id']=='directive_visa_code_lex_specialis')
    assert lex['status']=='unresolved' and lex['review_required'] is True
    cls={x['source_ref']:x for x in c5b_base['source_classifications']}
    assert cls['eu:32004l0038']['binding_force']=='binding_secondary_law'
    assert cls['eu:32009r0810']['binding_force']=='binding_secondary_law'
    assert c5b_base['final_hierarchy_resolution']=='not_determined'
    results.append('c5b_lex_specialis_overlap_remains_unresolved')

    # Charter scope is not inferred from regime candidacy when the explicit EU-law-scope element is missing.
    missing_scope_topology=te.build_topology(c5_frontier_case,c5_frontier_elements)
    missing_scope_regimes=ra.build_candidates(c5_frontier_case,missing_scope_topology,c5_frontier_elements)
    missing_scope_c5b=hp.build(c5_frontier_case,missing_scope_regimes,c5_frontier_elements)
    assert missing_scope_c5b['charter_scope']['disposition']=='blocked'
    assert missing_scope_c5b['charter_scope']['eu_law_scope_state']=='missing'
    assert any(x['code']=='eu_law_scope_missing' for x in missing_scope_c5b['unresolved'])
    results.append('c5b_charter_scope_missing_fails_closed')

    # Explicit EU-law scope permits a Charter review candidate but still not a final Charter applicability conclusion.
    assert c5b_base['charter_scope']['disposition']=='candidate'
    assert c5b_base['charter_scope']['eu_law_scope_state']=='established'
    assert c5b_base['final_hierarchy_resolution']=='not_determined'
    results.append('c5b_charter_scope_candidate_requires_established_scope')

    # Explicit negative EU-law scope suppresses the Charter candidate rather than being overridden by EU-regime candidates.
    c5b_false_elements=cv.load_json(FX/'c5b'/'elements-eu-scope-false.json')
    c5b_false_topology=te.build_topology(c5_frontier_case,c5b_false_elements)
    c5b_false_regimes=ra.build_candidates(c5_frontier_case,c5b_false_topology,c5b_false_elements)
    c5b_false=hp.build(c5_frontier_case,c5b_false_regimes,c5b_false_elements)
    assert c5b_false['charter_scope']['disposition']=='not_indicated'
    assert c5b_false['charter_scope']['eu_law_scope_state']=='not_established'
    results.append('c5b_charter_scope_explicit_negative_preserved')

    # Principle requests remain candidate-only and enforce the Article 41 Member-State addressee boundary.
    c5b_principles=hp.build(c5_frontier_case,c5b_regimes,c5b_elements,c5b_principles_context)
    pc={x['principle_id']:x for x in c5b_principles['principle_candidates']}
    assert pc['proportionality']['disposition']=='candidate'
    assert pc['charter_article_41_direct_reliance']['disposition']=='blocked'
    assert 'article_41_direct_addressee_boundary' in pc['charter_article_41_direct_reliance']['rationale_codes']
    results.append('c5b_principle_candidate_and_article41_boundary')

    # Non-binding recommendations/guidance cannot be recoded as binding, but bounded interpretive use remains a candidate.
    c5b_soft_context=cv.load_json(FX/'c5b'/'context-softlaw.json')
    c5b_soft=hp.build(c5_frontier_case,c5b_regimes,c5b_elements,c5b_soft_context)
    su={x['request_id']:x for x in c5b_soft['source_use_assessments']}
    assert su['softlaw:solvit-binding']['disposition']=='blocked'
    assert 'non_binding_source_cannot_be_recoded_as_binding' in su['softlaw:solvit-binding']['rationale_codes']
    assert su['guidance:free-movement-interpretive']['disposition']=='candidate'
    assert su['guidance:free-movement-interpretive']['binding_force']=='non_binding_guidance'
    results.append('c5b_soft_law_binding_force_boundary')

    # A possible EU/national conflict must bind an actual conformant Member-State rule and stays unresolved; no automatic disapplication occurs.
    c5b_conflict_context=cv.load_json(FX/'c5b'/'context-national-conflict.json')
    c5b_conflict=hp.build(c5_frontier_case,c5b_regimes,c5b_elements,c5b_conflict_context,[(str(FX/'member-state-se-manifest.json'),str(FX/'member-state-se-export.json'))])
    rel=next(x for x in c5b_conflict['hierarchy_relationships'] if x['relationship_id']=='hierarchy:synthetic-national-conflict')
    assert rel['status']=='unresolved'
    assert {'primacy','disapplication','consistent_interpretation','equivalence','effectiveness'} <= set(rel['principle_ids'])
    assert 'no_automatic_disapplication' in rel['rationale_codes']
    assert c5b_conflict['bindings']['module_bindings'][0]['module_id']=='member-state-se'
    results.append('c5b_eu_national_conflict_binds_conformant_rule')

    # Unknown national rule IDs cannot be smuggled into a hierarchy question.
    bad_conflict=copy.deepcopy(c5b_conflict_context); bad_conflict['hierarchy_questions'][0]['national_rule_refs']=['se:rule:missing']
    try: hp.build(c5_frontier_case,c5b_regimes,c5b_elements,bad_conflict,[(str(FX/'member-state-se-manifest.json'),str(FX/'member-state-se-export.json'))])
    except hp.C5bError as e: assert 'unknown_bound_national_rule_ref' in str(e)
    else: raise AssertionError('unknown national rule accepted by C5b')
    results.append('c5b_unknown_national_rule_rejected')

    # A non-binding EU source cannot be used as the basis for primacy/disapplication against a national rule.
    nonbinding_conflict=copy.deepcopy(c5b_conflict_context); nonbinding_conflict['hierarchy_questions'][0]['eu_source_refs']=['eu:c-2023-1392']
    nonbinding_result=hp.build(c5_frontier_case,c5b_regimes,c5b_elements,nonbinding_conflict,[(str(FX/'member-state-se-manifest.json'),str(FX/'member-state-se-export.json'))])
    rel_nb=next(x for x in nonbinding_result['hierarchy_relationships'] if x['relationship_id']=='hierarchy:synthetic-national-conflict')
    assert rel_nb['status']=='blocked' and 'non_binding_eu_source_cannot_ground_primacy_conflict' in rel_nb['rationale_codes']
    results.append('c5b_nonbinding_source_cannot_ground_primacy_conflict')

    # C5b is bound to the exact C5a case/element/source chain and preserves the private-data gate.
    try: hp.build(c5_frontier_case,c5b_regimes,c5_frontier_elements)
    except hp.C5bError as e: assert 'regime_element_bundle_binding_mismatch' in str(e)
    else: raise AssertionError('C5b accepted a different element bundle from the bound C5a chain')
    private_c5b_case=copy.deepcopy(c5_frontier_case); private_c5b_case['privacy_classification']='private'
    try: hp.build(private_c5b_case,c5b_regimes,c5b_elements)
    except hp.C5bError as e: assert 'private_data_disabled' in str(e)
    else: raise AssertionError('C5b accepted private case data')
    results.append('c5b_bindings_and_private_gate_enforced')

    # Principle candidates must bind to an existing regime/source basis; arbitrary model-request labels cannot create a candidate.
    bad_basis=copy.deepcopy(c5b_principles_context); bad_basis['principle_requests'][0]['basis_refs']=['legal_regime.does_not_exist']
    try: hp.build(c5_frontier_case,c5b_regimes,c5b_elements,bad_basis)
    except hp.C5bError as e: assert 'unknown_principle_basis_ref' in str(e)
    else: raise AssertionError('C5b accepted an unknown principle basis reference')
    results.append('c5b_principle_basis_must_resolve')

    # National rules from a conformant but case-irrelevant Member-State module cannot be injected into the hierarchy stage.
    unrelated_case=copy.deepcopy(c5_frontier_case)
    for req in unrelated_case['module_requests']:
        if req['family']=='member_state' and req['jurisdiction']=='SE':
            req['jurisdiction']='DE'
    # Rebuild C5a chain against the changed case while preserving a usable C5b scope bundle.
    unrelated_topology=te.build_topology(unrelated_case,c5b_elements)
    unrelated_regimes=ra.build_candidates(unrelated_case,unrelated_topology,c5b_elements)
    unrelated_context=copy.deepcopy(c5b_conflict_context); unrelated_context['case_id']=unrelated_case['case_id']
    try: hp.build(unrelated_case,unrelated_regimes,c5b_elements,unrelated_context,[(str(FX/'member-state-se-manifest.json'),str(FX/'member-state-se-export.json'))])
    except hp.C5bError as e: assert 'member_state_module_not_requested_for_case:SE' in str(e)
    else: raise AssertionError('case-irrelevant national module accepted by C5b')
    results.append('c5b_case_irrelevant_member_state_module_rejected')

    # A blocked C5a chain cannot be upgraded into a principle candidate by a C5b request.
    blocked_regimes=ra.build_candidates(c5_frontier_case,blocked_topology,conflicting)
    blocked_context=copy.deepcopy(c5b_principles_context)
    try:
        blocked_out=hp.build(c5_frontier_case,blocked_regimes,conflicting,blocked_context)
    except hp.C5bError:
        raise
    blocked_pc={x['principle_id']:x for x in blocked_out['principle_candidates']}
    assert blocked_out['resolution_status']=='blocked'
    assert blocked_pc['proportionality']['disposition']=='blocked'
    assert 'c5a_resolution_blocked' in blocked_pc['proportionality']['rationale_codes']
    results.append('c5b_blocked_c5a_chain_cannot_upgrade_principle')

    # C5c route catalogue and fixtures are source-bound and structurally valid.
    c5c_route_catalog=cv.load_json(ROOT/'references'/'routes'/'core-eu-route-catalog.json'); cv.validate_obj('core-route-catalog',c5c_route_catalog)
    assert {r for x in c5c_route_catalog['routes'] for r in x['source_refs']} <= source_ids
    c5c_elements=cv.load_json(FX/'c5c'/'elements-ready.json'); cv.validate_obj('element-instance-bundle',c5c_elements)
    c5c_context=cv.load_json(FX/'c5c'/'context-ready.json'); cv.validate_obj('c5c-context',c5c_context)
    c5c_core_context=cv.load_json(FX/'c5c'/'context-core-routes.json'); cv.validate_obj('c5c-context',c5c_core_context)
    c5c_export=cv.load_json(FX/'c5c'/'member-state-se-c5c-export.json'); cv.validate_obj('module-export',c5c_export)
    assert mc.validate_pair(cv.load_json(FX/'member-state-se-manifest.json'),c5c_export)['status']=='conformant'
    results.append('c5c_catalog_and_fixtures_valid')

    # Build an actor-scoped family-member chain with evidence/deadline state for C5c.
    c5c_topology=te.build_topology(c5_frontier_case,c5c_elements)
    c5c_regimes=ra.build_candidates(c5_frontier_case,c5c_topology,c5c_elements,actor_context=family_actors)
    c5c_c5b=hp.build(c5_frontier_case,c5c_regimes,c5c_elements)
    c5c_pair=[(str(FX/'member-state-se-manifest.json'),str(FX/'c5c'/'member-state-se-c5c-export.json'))]
    c5c_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,c5c_context,c5c_pair)
    cv.validate_obj('c5c-evidence-deadline-authority',c5c_out)
    assert c5c_out['final_c5c_resolution']=='not_determined' and c5c_out['resolution_status']=='ready'
    results.append('c5c_chain_binding_and_output_valid')

    # Jia-based freedom-of-proof treatment is a dependency-scoped review candidate, not a universal document rule.
    ev={x['request_id']:x for x in c5c_out['evidence_assessments']}
    dep=ev['evidence:dependency-proof']
    assert dep['disposition']=='candidate' and dep['freedom_of_proof_candidate']=='candidate'
    assert set(dep['source_refs'])=={'eu:62005cj0001','eu:32004l0038'}
    assert any('limited to dependency evidence' in x for x in dep['limitations'])
    results.append('c5c_dependency_freedom_of_proof_scoped')

    # A closed-proof assertion remains an input claim and is bound to its source/rule without becoming legally valid by label.
    restriction=ev['evidence:restriction']
    assert restriction['disposition']=='candidate' and restriction['restriction_claim_state']=='asserted'
    assert restriction['supporting_rule_refs']==['se:rule:fixture'] and restriction['freedom_of_proof_candidate']=='not_indicated'
    assert any('does not convert that label' in x for x in restriction['limitations'])
    results.append('c5c_proof_restriction_source_rule_binding')

    # Unknown restriction source identifiers block the evidence review rather than being invented or silently ignored.
    unknown_source_elements=copy.deepcopy(c5c_elements); unknown_source_elements['bundle_id']='c5c-unknown-restriction-source'
    next(x for x in unknown_source_elements['elements'] if x['element_id']=='evidence.proof_restriction_source_ref')['value']='se:src:missing'
    unknown_top=te.build_topology(c5_frontier_case,unknown_source_elements)
    unknown_reg=ra.build_candidates(c5_frontier_case,unknown_top,unknown_source_elements,actor_context=family_actors)
    unknown_b=hp.build(c5_frontier_case,unknown_reg,unknown_source_elements)
    unknown_ctx=copy.deepcopy(c5c_context); unknown_ctx['deadline_requests']=[]; unknown_ctx['route_requests']=[]; unknown_ctx['evidence_requests']=[unknown_ctx['evidence_requests'][1]]
    unknown_out=c5c.build(c5_frontier_case,unknown_reg,unknown_b,unknown_source_elements,unknown_ctx,c5c_pair)
    assert unknown_out['evidence_assessments'][0]['disposition']=='blocked'
    assert 'unknown_proof_restriction_source_ref' in unknown_out['evidence_assessments'][0]['rationale_codes']
    results.append('c5c_unknown_proof_restriction_source_blocks')

    # Exact deadline arithmetic is allowed only from the bound rule/trigger/date and explicit calculation assumptions.
    dl=c5c_out['deadline_assessments'][0]
    assert dl['calculation_status']=='exact' and dl['calculated_date']=='2026-10-11'
    assert dl['suspension_conditions']==[] and dl['extension_conditions']==[] and dl['effect_on_other_remedies']=='fixture only'
    results.append('c5c_exact_calendar_deadline_bound')

    # Rule binding uses the actual rule identifier, not the deadline-record identifier.
    assert dl['rule_ref']=='se:rule:fixture'
    assert next(x for x in c5c_elements['elements'] if x['element_id']=='time.deadline_rule_ref')['value']=='se:rule:fixture'
    results.append('c5c_deadline_rule_ref_semantics_match_model')

    # An unrelated or unresolvable event identity cannot reuse the scoped date and still yield an exact deadline.
    wrong_event_ctx=copy.deepcopy(c5c_context); wrong_event_ctx['evidence_requests']=[]; wrong_event_ctx['route_requests']=[]
    wrong_event_ctx['deadline_bindings'][0]['trigger_event_ref']='event:completely-unrelated'
    wrong_event_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,wrong_event_ctx,c5c_pair)
    assert wrong_event_out['deadline_assessments'][0]['calculation_status']=='candidate_only'
    assert 'deadline_trigger_event_ref_not_bound' in wrong_event_out['deadline_assessments'][0]['rationale_codes']
    results.append('c5c_deadline_trigger_identity_must_resolve')

    # Two deadline requests can bind independently to distinct typed events without singleton cross-talk.
    multi_ctx=copy.deepcopy(c5c_context); multi_ctx['evidence_requests']=[]; multi_ctx['route_requests']=[]
    multi_ctx['deadline_requests'].append({'request_id':'deadline:calendar-2','deadline_ref':'se:deadline:c5c-calendar-2','binding_ref':'binding:calendar-2','suspension_state':'none','extension_state':'none'})
    multi_ctx['deadline_bindings'].append({'binding_id':'binding:calendar-2','deadline_ref':'se:deadline:c5c-calendar-2','rule_ref':'se:rule:fixture','trigger_event_ref':'event:notice'})
    multi_ctx['temporal_events'].append({'event_id':'event:notice','event_type':'synthetic notice event','event_date':'2026-10-03','event_date_source_ref':'synthetic:notice-record','event_date_provenance_kind':'document'})
    multi_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,multi_ctx,c5c_pair)
    md={x['request_id']:x for x in multi_out['deadline_assessments']}
    assert md['deadline:calendar']['calculated_date']=='2026-10-11' and md['deadline:calendar']['calculation_status']=='exact'
    assert md['deadline:calendar-2']['calculated_date']=='2026-10-08' and md['deadline:calendar-2']['calculation_status']=='exact'
    assert md['deadline:calendar']['trigger_ref']=='event:lodged' and md['deadline:calendar-2']['trigger_ref']=='event:notice'
    results.append('c5c_multiple_deadlines_independently_scoped')

    # Suspension/extension uncertainty blocks exact arithmetic without deleting the deadline candidate.
    suspend_ctx=copy.deepcopy(c5c_context); suspend_ctx['evidence_requests']=[]; suspend_ctx['route_requests']=[]; suspend_ctx['deadline_requests'][0]['suspension_state']='possible'
    suspend_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,suspend_ctx,c5c_pair)
    assert suspend_out['deadline_assessments'][0]['disposition']=='candidate' and suspend_out['deadline_assessments'][0]['calculation_status']=='candidate_only'
    assert 'deadline_suspension_not_resolved' in suspend_out['deadline_assessments'][0]['rationale_codes']
    results.append('c5c_deadline_suspension_blocks_exact')

    # Business-day calculation stays non-exact until a trusted business-day calendar identity exists.
    business_ctx=copy.deepcopy(c5c_context); business_ctx['evidence_requests']=[]; business_ctx['route_requests']=[]
    business_ctx['deadline_requests'][0].update({'deadline_ref':'se:deadline:c5c-business','binding_ref':'binding:business'})
    business_ctx['deadline_bindings']=[{'binding_id':'binding:business','deadline_ref':'se:deadline:c5c-business','rule_ref':'se:rule:fixture','trigger_event_ref':'event:lodged'}]
    business_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,business_ctx,c5c_pair)
    assert business_out['deadline_assessments'][0]['calculation_status']=='candidate_only'
    assert 'business_day_calendar_identity_missing' in business_out['deadline_assessments'][0]['rationale_codes']
    results.append('c5c_business_day_calendar_fails_closed')

    # Model-inferred trigger dates cannot produce an exact deadline even when the scoped event identity is otherwise valid.
    inferred_ctx=copy.deepcopy(c5c_context); inferred_ctx['evidence_requests']=[]; inferred_ctx['route_requests']=[]
    inferred_ctx['temporal_events'][0]['event_date_provenance_kind']='model_inference'
    inferred_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,inferred_ctx,c5c_pair)
    assert inferred_out['deadline_assessments'][0]['calculation_status']=='candidate_only'
    assert 'deadline_trigger_date_not_evidence_bound' in inferred_out['deadline_assessments'][0]['rationale_codes']
    results.append('c5c_model_inferred_deadline_date_rejected')

    # Opaque inclusion rules cannot be guessed into exact deadline semantics.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); unsafe=copy.deepcopy(c5c_export); unsafe['deadline_records'][0]['calculation']['inclusion_rule']='fixture only'
        ep=td/'export.json'; ep.write_text(json.dumps(unsafe)); assert mc.validate_pair(cv.load_json(FX/'member-state-se-manifest.json'),unsafe)['status']=='conformant'
        unsafe_pair=[(str(FX/'member-state-se-manifest.json'),str(ep))]
        unsafe_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,{**copy.deepcopy(c5c_context),'evidence_requests':[],'route_requests':[]},unsafe_pair)
        assert unsafe_out['deadline_assessments'][0]['calculation_status']=='candidate_only'
        assert 'inclusion_rule_not_machine_interpretable' in unsafe_out['deadline_assessments'][0]['rationale_codes']
    results.append('c5c_opaque_inclusion_rule_fails_closed')

    # Invalid timezone identifiers cannot satisfy exactness merely because a non-empty string is present.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); bad_tz=copy.deepcopy(c5c_export); bad_tz['deadline_records'][0]['timezone']='Not/A_Real_Zone'
        ep=td/'export.json'; ep.write_text(json.dumps(bad_tz)); assert mc.validate_pair(cv.load_json(FX/'member-state-se-manifest.json'),bad_tz)['status']=='conformant'
        bad_tz_pair=[(str(FX/'member-state-se-manifest.json'),str(ep))]
        bad_tz_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,{**copy.deepcopy(c5c_context),'evidence_requests':[],'route_requests':[]},bad_tz_pair)
        assert bad_tz_out['deadline_assessments'][0]['calculation_status']=='candidate_only'
        assert bad_tz_out['deadline_assessments'][0]['timezone_validation']=='invalid'
        assert 'deadline_timezone_invalid' in bad_tz_out['deadline_assessments'][0]['rationale_codes']
    results.append('c5c_invalid_timezone_fails_closed')

    # Legacy v0.1 contexts remain accepted but cannot produce exact deadlines without a scoped binding.
    legacy_ctx={'context_version':'0.1.0','case_id':c5_frontier_case['case_id'],'evidence_requests':[],'deadline_requests':[{'request_id':'legacy:deadline','deadline_ref':'se:deadline:c5c-calendar','suspension_state':'none','extension_state':'none'}],'route_requests':[]}
    legacy_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,legacy_ctx,c5c_pair)
    assert legacy_out['deadline_assessments'][0]['calculation_status']=='candidate_only'
    assert 'scoped_deadline_binding_required' in legacy_out['deadline_assessments'][0]['rationale_codes']
    results.append('c5c_legacy_deadline_context_fails_closed')

    # Unknown deadline IDs are rejected at the typed context boundary.
    bad_deadline_ctx=copy.deepcopy(c5c_context); bad_deadline_ctx['evidence_requests']=[]; bad_deadline_ctx['route_requests']=[]; bad_deadline_ctx['deadline_requests'][0]['deadline_ref']='se:deadline:missing'
    try: c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,bad_deadline_ctx,c5c_pair)
    except c5c.C5cError as e: assert 'unknown_deadline_ref' in str(e)
    else: raise AssertionError('unknown deadline reference accepted by C5c')
    results.append('c5c_unknown_deadline_ref_rejected')

    # Conformant case-relevant module routes preserve authority competence/powers/limits but remain unranked candidates.
    route=c5c_out['route_assessments'][0]
    assert route['disposition']=='candidate' and route['authority_competence']==['fixture competence']
    assert route['powers']==['fixture power'] and route['limits']==['fixture only'] and route['authority_level']=='unknown' and route['target_authority_level_validation']=='unknown_frozen_contract'
    assert 'module_authority_level_not_structured_in_frozen_contract' in route['rationale_codes']
    results.append('c5c_module_route_authority_boundary_preserved')

    # Core EU routes enforce bounded competence: SOLVIT/Commission may be candidates, Ombudsman is not a Member-State-authority route.
    core_routes_out=c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,c5c_core_context,c5c_pair)
    routes={x['route_ref']:x for x in core_routes_out['route_assessments']}
    assert routes['eu:route:solvit']['disposition']=='candidate'
    assert routes['eu:route:commission-eu-law-complaint']['disposition']=='candidate'
    assert routes['eu:route:ombudsman']['disposition']=='not_indicated' and routes['eu:route:ombudsman']['target_authority_level_validation']=='mismatched' and 'target_authority_level_mismatch' in routes['eu:route:ombudsman']['rationale_codes']
    results.append('c5c_core_route_competence_boundaries')

    # Evidence basis references must resolve to the bound C5a/C5b/source/module chain.
    bad_basis_ctx=copy.deepcopy(c5c_context); bad_basis_ctx['deadline_requests']=[]; bad_basis_ctx['route_requests']=[]; bad_basis_ctx['evidence_requests'][0]['basis_refs']=['legal_regime.does_not_exist']; bad_basis_ctx['evidence_requests']=bad_basis_ctx['evidence_requests'][:1]
    try: c5c.build(c5_frontier_case,c5c_regimes,c5c_c5b,c5c_elements,bad_basis_ctx,c5c_pair)
    except c5c.C5cError as e: assert 'unknown_evidence_basis_ref' in str(e)
    else: raise AssertionError('unknown evidence basis accepted by C5c')
    results.append('c5c_evidence_basis_must_resolve')

    # C5c is bound to exact upstream artifacts and preserves the private-data gate.
    tampered_c5b=copy.deepcopy(c5c_c5b); tampered_c5b['bindings']['regime_candidates_sha256']='0'*64
    try: c5c.build(c5_frontier_case,c5c_regimes,tampered_c5b,c5c_elements,c5c_context,c5c_pair)
    except c5c.C5cError as e: assert 'c5b_regime_binding_mismatch' in str(e)
    else: raise AssertionError('tampered C5b binding accepted by C5c')
    private_c5c_case=copy.deepcopy(c5_frontier_case); private_c5c_case['privacy_classification']='private'
    try: c5c.build(private_c5c_case,c5c_regimes,c5c_c5b,c5c_elements,c5c_context,c5c_pair)
    except c5c.C5cError as e: assert 'private_data_disabled' in str(e)
    else: raise AssertionError('C5c accepted private case data')
    results.append('c5c_bindings_and_private_gate_enforced')

    # Any country modules already bound by C5b must be replayed exactly into C5c.
    empty_c5c_context={'context_version':'0.1.0','case_id':c5_frontier_case['case_id'],'evidence_requests':[],'deadline_requests':[],'route_requests':[]}
    try: c5c.build(c5_frontier_case,c5b_regimes,c5b_conflict,c5b_elements,empty_c5c_context)
    except c5c.C5cError as e: assert 'c5b_bound_modules_must_be_replayed' in str(e)
    else: raise AssertionError('C5c ignored bound C5b module provenance')
    results.append('c5c_replays_upstream_module_bindings')

    # A blocked upstream chain cannot be upgraded into an evidence, deadline or route candidate.
    blocked_c5c_ctx={'context_version':'0.1.0','case_id':c5_frontier_case['case_id'],'evidence_requests':[{'request_id':'blocked:evidence','kind':'proof_restriction_review','scope':'blocked chain','basis_refs':['legal_regime.directive_2004_38']}],'deadline_requests':[],'route_requests':[{'request_id':'blocked:route','route_ref':'eu:route:commission-eu-law-complaint','issue_type':'possible_member_state_eu_law_breach','target_authority_level':'member_state_authority'}]}
    blocked_c5c=c5c.build(c5_frontier_case,blocked_regimes,blocked_out,conflicting,blocked_c5c_ctx)
    assert blocked_c5c['resolution_status']=='blocked'
    assert blocked_c5c['evidence_assessments'][0]['disposition']=='blocked' and blocked_c5c['route_assessments'][0]['disposition']=='blocked'
    results.append('c5c_blocked_upstream_chain_cannot_upgrade')

    # C5d attack-angle synthesis: validate catalogue/fixtures and exact chain binding.
    c5d_catalog=cv.load_json(ROOT/'references'/'attack-angles'/'core-attack-angle-catalog.json'); cv.validate_obj('core-attack-angle-catalog',c5d_catalog)
    c5d_elements=cv.load_json(FX/'c5d'/'elements-signals.json'); cv.validate_obj('element-instance-bundle',c5d_elements); c5d.validate_element_bundle(c5d_elements)
    c5d_topology=te.build_topology(c5_frontier_case,c5d_elements)
    c5d_regimes=ra.build_candidates(c5_frontier_case,c5d_topology,c5d_elements,actor_context=family_actors)
    c5d_c5b=hp.build(c5_frontier_case,c5d_regimes,c5d_elements)
    c5d_c5c=c5c.build(c5_frontier_case,c5d_regimes,c5d_c5b,c5d_elements,c5c_context,c5c_pair)
    c5d_out=c5d.build(c5_frontier_case,c5d_regimes,c5d_c5b,c5d_c5c,c5d_elements,c5c_pair)
    cv.validate_obj('c5d-attack-angle-synthesis',c5d_out)
    assert c5d_out['resolution_status']=='ready' and c5d_out['final_attack_angle_resolution']=='not_determined'
    ids={x['attack_angle_id'] for x in c5d_out['attack_angles']}
    assert {'core:attack:deadline-timeliness-review','core:attack:procedural-access-review','core:attack:proof-restriction-review','core:attack:authority-competence-review','se:attack:fixture-procedure'} <= ids
    assert all(x['legal_violation_status']=='not_determined' for x in c5d_out['attack_angles'])
    results.append('c5d_catalog_fixture_and_chain_valid')

    # Legal-source presence alone cannot create access/deadline/competence angles.
    no_signal=copy.deepcopy(c5d_elements); no_signal['bundle_id']='c5d-no-signals'
    no_signal['elements']=[x for x in no_signal['elements'] if x['element_id'] not in {'procedure.access_state','procedure.deadline_state','authority.competence'}]
    ns_top=te.build_topology(c5_frontier_case,no_signal); ns_reg=ra.build_candidates(c5_frontier_case,ns_top,no_signal,actor_context=family_actors); ns_b=hp.build(c5_frontier_case,ns_reg,no_signal); ns_c=c5c.build(c5_frontier_case,ns_reg,ns_b,no_signal,c5c_context,c5c_pair); ns_d=c5d.build(c5_frontier_case,ns_reg,ns_b,ns_c,no_signal,c5c_pair)
    ns_ids={x['attack_angle_id'] for x in ns_d['attack_angles']}
    assert 'core:attack:procedural-access-review' not in ns_ids and 'core:attack:deadline-timeliness-review' not in ns_ids and 'core:attack:authority-competence-review' not in ns_ids
    results.append('c5d_source_presence_alone_no_attack')

    # An exact C5c deadline is not itself a delay attack angle; an adverse timeliness state is separately required.
    no_deadline_state=copy.deepcopy(c5d_elements); no_deadline_state['bundle_id']='c5d-no-deadline-state'; no_deadline_state['elements']=[x for x in no_deadline_state['elements'] if x['element_id']!='procedure.deadline_state']
    nd_top=te.build_topology(c5_frontier_case,no_deadline_state); nd_reg=ra.build_candidates(c5_frontier_case,nd_top,no_deadline_state,actor_context=family_actors); nd_b=hp.build(c5_frontier_case,nd_reg,no_deadline_state); nd_c=c5c.build(c5_frontier_case,nd_reg,nd_b,no_deadline_state,c5c_context,c5c_pair); nd_d=c5d.build(c5_frontier_case,nd_reg,nd_b,nd_c,no_deadline_state,c5c_pair)
    assert 'core:attack:deadline-timeliness-review' not in {x['attack_angle_id'] for x in nd_d['attack_angles']}
    results.append('c5d_deadline_requires_independent_adverse_state')

    # A source/rule-bound proof restriction remains a review candidate, not an illegality finding.
    pa=next(x for x in c5d_out['attack_angles'] if x['attack_angle_id']=='core:attack:proof-restriction-review')
    assert pa['assessment_status']=='candidate' and pa['legal_violation_status']=='not_determined' and pa['rule_refs']==['se:rule:fixture']
    results.append('c5d_proof_restriction_not_auto_violation')

    # Unknown authority competence is not a competence defect.
    unknown_comp=copy.deepcopy(c5d_elements); unknown_comp['bundle_id']='c5d-unknown-competence'
    for x in unknown_comp['elements']:
        if x['element_id']=='authority.competence':
            x['value']='unknown'
    uc_top=te.build_topology(c5_frontier_case,unknown_comp); uc_reg=ra.build_candidates(c5_frontier_case,uc_top,unknown_comp,actor_context=family_actors); uc_b=hp.build(c5_frontier_case,uc_reg,unknown_comp); uc_c=c5c.build(c5_frontier_case,uc_reg,uc_b,unknown_comp,c5c_context,c5c_pair); uc_d=c5d.build(c5_frontier_case,uc_reg,uc_b,uc_c,unknown_comp,c5c_pair)
    assert 'core:attack:authority-competence-review' not in {x['attack_angle_id'] for x in uc_d['attack_angles']}
    results.append('c5d_unknown_authority_not_defect')

    # Unresolved Directive/Visa Code lex-specialis coexistence is not itself a contradiction/non-compliance attack angle.
    assert any(x['relationship_id']=='directive_visa_code_lex_specialis' and x['status']=='unresolved' for x in c5d_c5b['hierarchy_relationships'])
    assert not any(x['issue_type'] in {'lex_specialis','regime_contradiction'} for x in c5d_out['attack_angles'])
    results.append('c5d_unresolved_lex_specialis_not_attack')

    # GDPR/data presence cannot auto-generate a privacy attack without dedicated authority-processing facts.
    gdpr=copy.deepcopy(c5d_elements); gdpr['bundle_id']='c5d-gdpr-presence-only'; gdpr['elements'].append({'element_id':'legal_regime.gdpr','value':'candidate','supplied_by':'core','provenance_kind':'mechanical_calculation'})
    gd_top=te.build_topology(c5_frontier_case,gdpr); gd_reg=ra.build_candidates(c5_frontier_case,gd_top,gdpr,actor_context=family_actors); gd_b=hp.build(c5_frontier_case,gd_reg,gdpr); gd_c=c5c.build(c5_frontier_case,gd_reg,gd_b,gdpr,c5c_context,c5c_pair); gd_d=c5d.build(c5_frontier_case,gd_reg,gd_b,gd_c,gdpr,c5c_pair)
    assert not any('privacy' in x['issue_type'] or 'data_minim' in x['issue_type'] for x in gd_d['attack_angles'])
    results.append('c5d_gdpr_presence_not_auto_attack')

    # Module-declared attack records stay candidate-only because contract 0.2.0 does not encode expected prerequisite/disqualifier values.
    ma=next(x for x in c5d_out['attack_angles'] if x['attack_angle_id']=='se:attack:fixture-procedure')
    assert ma['origin']=='module_record' and ma['assessment_status']=='candidate' and ma['legal_violation_status']=='not_determined'
    results.append('c5d_module_attack_record_candidate_only')

    # Supported core status requires fact provenance; an unproven access assertion remains a candidate.
    weak_access=copy.deepcopy(c5d_elements); weak_access['bundle_id']='c5d-weak-access'
    for x in weak_access['elements']:
        if x['element_id']=='procedure.access_state':
            x.pop('source_ref',None); x['provenance_kind']='user_assertion'
    wa_top=te.build_topology(c5_frontier_case,weak_access); wa_reg=ra.build_candidates(c5_frontier_case,wa_top,weak_access,actor_context=family_actors); wa_b=hp.build(c5_frontier_case,wa_reg,weak_access); wa_c=c5c.build(c5_frontier_case,wa_reg,wa_b,weak_access,c5c_context,c5c_pair); wa_d=c5d.build(c5_frontier_case,wa_reg,wa_b,wa_c,weak_access,c5c_pair)
    waa=next(x for x in wa_d['attack_angles'] if x['attack_angle_id']=='core:attack:procedural-access-review')
    assert waa['assessment_status']=='candidate' and waa['evidence_state']=='partial'
    results.append('c5d_supported_status_requires_fact_provenance')

    # Proportionality is not generated from an abstract principle candidate without a concrete adverse signal.
    prop_elements=copy.deepcopy(c5d_elements); prop_elements['bundle_id']='c5d-prop-no-adverse'
    prop_elements['elements']=[x for x in prop_elements['elements'] if x['element_id'] not in {'procedure.access_state','procedure.deadline_state','authority.competence','evidence.proof_restriction_status','evidence.proof_restriction_source_ref'}]
    prop_top=te.build_topology(c5_frontier_case,prop_elements); prop_reg=ra.build_candidates(c5_frontier_case,prop_top,prop_elements,actor_context=family_actors)
    prop_ctx=cv.load_json(FX/'c5b'/'context-principles.json'); prop_b=hp.build(c5_frontier_case,prop_reg,prop_elements,prop_ctx)
    empty_c5c_ctx={'context_version':'0.2.0','case_id':c5_frontier_case['case_id'],'evidence_requests':[],'deadline_requests':[],'route_requests':[],'deadline_bindings':[],'temporal_events':[]}
    prop_c=c5c.build(c5_frontier_case,prop_reg,prop_b,prop_elements,empty_c5c_ctx)
    prop_d=c5d.build(c5_frontier_case,prop_reg,prop_b,prop_c,prop_elements)
    assert any(x['principle_id']=='proportionality' and x['disposition']=='candidate' for x in prop_b['principle_candidates'])
    assert 'core:attack:proportionality-review' not in {x['attack_angle_id'] for x in prop_d['attack_angles']}
    results.append('c5d_proportionality_requires_concrete_adverse_signal')

    # Upstream blockage cannot be laundered into supported attack angles.
    blocked_d=c5d.build(c5_frontier_case,blocked_regimes,blocked_out,blocked_c5c,conflicting)
    assert blocked_d['resolution_status']=='blocked' and blocked_d['final_attack_angle_resolution']=='not_determined'
    assert not any(x['assessment_status']=='supported' for x in blocked_d['attack_angles'])
    results.append('c5d_blocked_upstream_no_upgrade')

    # Exact C5c module bindings must be replayed by C5d.
    try: c5d.build(c5_frontier_case,c5d_regimes,c5d_c5b,c5d_c5c,c5d_elements)
    except c5d.C5dError as e: assert 'c5c_bound_modules_must_be_replayed' in str(e)
    else: raise AssertionError('C5d accepted a chain without replaying C5c-bound modules')
    results.append('c5d_module_binding_replay_enforced')

    # Catalog source integrity is deterministic and fail-closed.
    bad_catalog=copy.deepcopy(c5d_catalog); bad_catalog['patterns'][1]['source_refs']=['eu:missing-source']
    try: c5d.build(c5_frontier_case,c5d_regimes,c5d_c5b,c5d_c5c,c5d_elements,c5c_pair,catalog=bad_catalog)
    except c5d.C5dError as e: assert 'core_attack_catalog_source_missing' in str(e)
    else: raise AssertionError('C5d accepted a catalog source that is absent from the source pack')
    results.append('c5d_catalog_source_integrity_enforced')

    # Private data remains blocked before synthesis.
    private_c5d_case=copy.deepcopy(c5_frontier_case); private_c5d_case['privacy_classification']='private'
    try: c5d.build(private_c5d_case,c5d_regimes,c5d_c5b,c5d_c5c,c5d_elements,c5c_pair)
    except c5d.C5dError as e: assert 'private_data_disabled' in str(e)
    else: raise AssertionError('C5d processed private case data')
    results.append('c5d_private_data_gate_enforced')

    # C5d -> C5e handoff requires an explicit digest-bound review; C5d labels alone never promote themselves.
    review={
      'review_version':'0.1.0','case_id':c5_frontier_case['case_id'],'c5d_sha256':cv.digest_obj(c5d_out),
      'reviewer_ref':'reviewer:fixture','identity_assurance':'system_fixture',
      'attack_angle_reviews':[
        {'attack_angle_id':'core:attack:procedural-access-review','disposition':'validate_for_suggestion','rationale':'Fixture review confirms the bound access signal and its supporting evidence are suitable for suggestion generation.','reviewed_evidence_refs':['synthetic:appointment-record','eu:32004l0038'],'module_value_checks':[]},
        {'attack_angle_id':'core:attack:proof-restriction-review','disposition':'validate_for_suggestion','rationale':'Fixture asks the handoff to reject a merely candidate proof-restriction angle rather than laundering it downstream.','reviewed_evidence_refs':['se:src:fixture'],'module_value_checks':[]}
      ],
      'route_reviews':[]
    }
    cv.validate_obj('analysis-review-record',review)
    handoff=ah.build(c5_frontier_case,c5d_c5c,c5d_out,review,c5d_elements,c5c_pair)
    cv.validate_obj('analysis-handoff',handoff)
    assert handoff['handoff_status']=='ready' and handoff['legal_conclusion_status']=='not_determined'
    assert {x['attack_angle_id'] for x in handoff['eligible_attack_angles']}=={'core:attack:procedural-access-review'}
    assert 'attack:core:attack:proof-restriction-review:core_angle_not_promotion_grade' in handoff['rejected']
    results.append('c5e_handoff_explicit_review_and_grade_gate')

    # A copied or stale review cannot be replayed against a different C5d artifact.
    bad_review=copy.deepcopy(review); bad_review['c5d_sha256']='0'*64
    try: ah.build(c5_frontier_case,c5d_c5c,c5d_out,bad_review,c5d_elements,c5c_pair)
    except ah.HandoffError as e: assert 'review_c5d_binding_mismatch' in str(e)
    else: raise AssertionError('stale C5d review accepted by analysis handoff')
    results.append('c5e_handoff_review_digest_binding_enforced')

    # Module attack records need value-level overlay semantics; mere prerequisite-element presence cannot promote them.
    module_review=copy.deepcopy(review); module_review['attack_angle_reviews']=[{
      'attack_angle_id':'se:attack:fixture-procedure','disposition':'validate_for_suggestion',
      'rationale':'Fixture review supplies the missing expected-value semantics for the module prerequisite.',
      'reviewed_evidence_refs':['se:src:fixture'],
      'module_value_checks':[{'role':'prerequisite','element_id':'procedure.stage','operator':'equals','expected_value':'visa_application_processing'}]
    }]
    module_handoff=ah.build(c5_frontier_case,c5d_c5c,c5d_out,module_review,c5d_elements,c5c_pair)
    assert not module_handoff['eligible_attack_angles'] and any('module_prerequisite_fact_provenance_missing:procedure.stage' in x for x in module_handoff['rejected'])
    results.append('c5e_module_angle_requires_value_semantics_and_fact_provenance')

    # If the same module prerequisite has value-level semantics and provenance, it can be promoted without altering legal_violation_status upstream.
    module_elements=copy.deepcopy(c5d_elements); module_elements['bundle_id']='c5e-module-provenance'
    for x in module_elements['elements']:
        if x['element_id']=='procedure.stage':
            x['provenance_kind']='document'; x['source_ref']='synthetic:stage-record'
    mt=te.build_topology(c5_frontier_case,module_elements); mr=ra.build_candidates(c5_frontier_case,mt,module_elements,actor_context=family_actors); mb=hp.build(c5_frontier_case,mr,module_elements); mc5=c5c.build(c5_frontier_case,mr,mb,module_elements,c5c_context,c5c_pair); md=c5d.build(c5_frontier_case,mr,mb,mc5,module_elements,c5c_pair)
    module_review2=copy.deepcopy(module_review); module_review2['c5d_sha256']=cv.digest_obj(md)
    mh2=ah.build(c5_frontier_case,mc5,md,module_review2,module_elements,c5c_pair)
    assert {x['attack_angle_id'] for x in mh2['eligible_attack_angles']}=={'se:attack:fixture-procedure'}
    assert next(x for x in md['attack_angles'] if x['attack_angle_id']=='se:attack:fixture-procedure')['legal_violation_status']=='not_determined'
    results.append('c5e_module_overlay_can_promote_without_legal_upgrade')

    # Module routes with target authority level unknown under the frozen contract cannot be promoted by a review label alone.
    route_review=copy.deepcopy(review); route_review['attack_angle_reviews']=[]; route_review['route_reviews']=[{'route_ref':'se:route:fixture','disposition':'validate_for_suggestion','rationale':'Fixture attempts route promotion while target authority level remains structurally unknown.'}]
    rh=ah.build(c5_frontier_case,c5d_c5c,c5d_out,route_review,c5d_elements,c5c_pair)
    assert not rh['eligible_routes'] and 'route:se:route:fixture:target_authority_level_not_validated' in rh['rejected']
    results.append('c5e_module_route_unknown_target_not_promoted')

    # Stratagem catalogues are complete, ordinally paired, and the adapted layer is preferred for operational generation.
    adapted=cv.load_json(ROOT/'references'/'stratagems'/'adapted-stratagem-catalog.json'); original=cv.load_json(ROOT/'references'/'stratagems'/'original-stratagem-catalog.json')
    cv.validate_obj('stratagem-catalog',adapted); cv.validate_obj('stratagem-catalog',original)
    assert len(adapted['patterns'])==36 and len(original['patterns'])==36
    assert all(x['preferred_for_generation'] for x in adapted['patterns']) and all(x['operational_role']=='reference_only' for x in original['patterns'])
    results.append('c5e_dual_stratagem_catalogues_valid')

    # C5e accepts a supported, lawful candidate but never upgrades it to a recommendation.
    ctx={
      'context_version':'0.1.0','case_id':c5_frontier_case['case_id'],
      'objective':{'objective_id':'obj:access','statement':'Obtain a lawful, reviewable route to lodge the application with minimal unnecessary disclosure.'},
      'proposals':[{
        'suggestion_id':'sug:clarify-basis','candidate_kind':'action','adapted_stratagem_id':'adapted:13','original_stratagem_id':'original:13','applicability':'applicable',
        'supporting_attack_angle_refs':['core:attack:procedural-access-review'],'supporting_route_refs':[],
        'action_summary':'Ask a narrow written question identifying the legal basis and available alternative lodgement channel before choosing a stronger response.',
        'mechanism_summary':'Use a limited probe to obtain an authority position and create a reliable record without assuming the access issue is unlawful.',
        'assumptions':['The authority can provide a written procedural answer.'],'prerequisites':['Preserve the existing appointment/access evidence.'],
        'expected_effect':'Increase information and fix the authority position in the record.','risks':['The authority may give a generic answer.'],
        'reversibility':'high','information_value':'high','burden_cost':'low','disclosure_duty_status':'none_known','disclosure_review_rationale':'The proposed question does not depend on withholding information subject to an identified affirmative disclosure duty.',
        'falsification_required':False,'inaction_or_delay':False,'deadline_waiver_review':'not_applicable','requires_new_determination':False,'new_question':None
      }]
    }
    cv.validate_obj('c5e-context',ctx)
    sug=sg.build(handoff,ctx,adapted,original); cv.validate_obj('c5e-suggestion-candidates',sug)
    assert len(sug['candidates'])==1 and sug['recommendation_status']=='not_ranked' and sug['candidates'][0]['validation_status']=='candidate'
    results.append('c5e_candidate_generation_not_recommendation')

    # Unsupported attack-angle invention is blocked at the suggestion boundary.
    bad_ctx=copy.deepcopy(ctx); bad_ctx['proposals'][0]['suggestion_id']='sug:invent'; bad_ctx['proposals'][0]['supporting_attack_angle_refs']=['core:attack:invented']
    bad=sg.build(handoff,bad_ctx,adapted,original)
    assert not bad['candidates'] and 'unsupported_attack_angle_reference' in bad['blocked'][0]['validation_reasons']
    results.append('c5e_cannot_create_attack_angle_by_reference')

    # Falsification-dependent tactics are blocked even when a valid stratagem and support record exist.
    lie_ctx=copy.deepcopy(ctx); lie_ctx['proposals'][0]['suggestion_id']='sug:false'; lie_ctx['proposals'][0]['adapted_stratagem_id']='adapted:27'; lie_ctx['proposals'][0]['original_stratagem_id']='original:27'; lie_ctx['proposals'][0]['falsification_required']=True
    lie=sg.build(handoff,lie_ctx,adapted,original)
    assert not lie['candidates'] and 'falsification_dependent_tactic_forbidden' in lie['blocked'][0]['validation_reasons']
    results.append('c5e_falsification_dependent_tactic_rejected')

    # Unknown disclosure duties and uncleared inaction/deadline risk return to analysis instead of becoming action candidates.
    delay_ctx=copy.deepcopy(ctx); q=delay_ctx['proposals'][0]; q['suggestion_id']='sug:wait'; q['adapted_stratagem_id']='adapted:04'; q['original_stratagem_id']='original:04'; q['inaction_or_delay']=True; q['deadline_waiver_review']='unknown'; q['disclosure_duty_status']='unknown'; q['disclosure_review_rationale']='The current analysis has not established whether any affirmative disclosure duty or waiver risk applies to waiting.'
    delay=sg.build(handoff,delay_ctx,adapted,original)
    assert not delay['candidates'] and delay['analysis_returns'][0]['validation_status']=='analysis_return'
    assert 'inaction_delay_deadline_waiver_not_cleared' in delay['analysis_returns'][0]['validation_reasons'] and 'disclosure_duty_requires_analysis_return' in delay['analysis_returns'][0]['validation_reasons']
    results.append('c5e_inaction_and_disclosure_uncertainty_return_to_analysis')

    # New factual/legal questions explicitly return to analysis and cannot mutate the existing handoff.
    ret_ctx=copy.deepcopy(ctx); q=ret_ctx['proposals'][0]; q['suggestion_id']='sug:new-question'; q['candidate_kind']='analysis_return'; q['requires_new_determination']=True; q['new_question']='Does the asserted appointment condition have a binding source and an alternative channel?'
    before=cv.digest_obj(handoff); ret=sg.build(handoff,ret_ctx,adapted,original); after=cv.digest_obj(handoff)
    assert before==after and not ret['candidates'] and ret['analysis_returns'][0]['new_question']
    results.append('c5e_analysis_return_does_not_mutate_analysis')

    # The whole stratagem layer may correctly produce no action/non-applicable output.
    none_ctx=copy.deepcopy(ctx); q=none_ctx['proposals'][0]; q['suggestion_id']='sug:none'; q['candidate_kind']='no_action'; q['adapted_stratagem_id']=None; q['original_stratagem_id']=None; q['supporting_attack_angle_refs']=[]; q['applicability']='applicable'; q['inaction_or_delay']=True; q['deadline_waiver_review']='clear'; q['action_summary']='Take no additional action at this stage.'; q['mechanism_summary']='No stratagem-based action currently improves on preserving the existing position.'
    none=sg.build(handoff,none_ctx,adapted,original)
    assert len(none['candidates'])==1 and none['candidates'][0]['candidate_kind']=='no_action'
    results.append('c5e_explicit_no_action_allowed')

    # Changing the stratagem catalog cannot change the upstream legal-analysis or handoff digests.
    mutated=copy.deepcopy(adapted); mutated['patterns'][12]['name']='Renamed probe pattern for independence test'
    analysis_digest_before=cv.digest_obj(c5d_out); handoff_digest_before=cv.digest_obj(handoff)
    mut_sug=sg.build(handoff,ctx,mutated,original)
    assert cv.digest_obj(c5d_out)==analysis_digest_before and cv.digest_obj(handoff)==handoff_digest_before and mut_sug['bindings']['adapted_catalog_sha256']!=sug['bindings']['adapted_catalog_sha256']
    results.append('c5e_catalog_mutation_analysis_independence')

    # Private case data remains blocked at the handoff boundary.
    private_review=copy.deepcopy(review); private_review['case_id']=private_c5d_case['case_id']
    try: ah.build(private_c5d_case,c5d_c5c,c5d_out,private_review,c5d_elements,c5c_pair)
    except ah.HandoffError as e: assert 'private_data_disabled' in str(e)
    else: raise AssertionError('analysis handoff processed private case data')
    results.append('c5e_private_data_gate_enforced')

    # C5f ranking: exact C5e replay, explicit baseline review, and reviewer-only priority tiers.
    factors={'urgency':'high','remedy_power':'not_applicable','legal_support_strength':'medium',
             'evidentiary_value':'high','reversibility':'high','route_compatibility':'not_applicable',
             'burden_cost':'low','systemic_value':'medium'}
    assess={
      'suggestion_id':'sug:clarify-basis','disposition':'include','assumptions_state':'current',
      'factual_basis_state':'reviewed','counterevidence_state':'reviewed_no_material_conflict',
      'prerequisites_state':'satisfied','adverse_effects_state':'clear',
      'basis_classification':'documented_fact_and_review','ratings':factors,'rating_basis_refs':['core:attack:procedural-access-review'],
      'review_rationale':'Synthetic reviewer confirmed that support is limited to the promoted procedural-access question, not a legal violation.'
    }
    baseline_kinds=sorted(sr.BASELINES)
    baselines=[{'baseline_kind':k,'review_status':'not_applicable','suggestion_id':None,
                 'rationale':'Synthetic review found no currently grounded distinct '+k+' comparator in this deliberately narrow fixture.'}
               for k in baseline_kinds]
    rank_ctx={
      'context_version':'0.1.0','case_id':ctx['case_id'],'objective_id':ctx['objective']['objective_id'],
      'bindings':{'handoff_sha256':cv.digest_obj(handoff),'c5e_context_sha256':cv.digest_obj(ctx),
                  'c5e_candidates_sha256':cv.digest_obj(sug)},
      'review':{'reviewer_ref':'reviewer:synthetic','identity_assurance':'unverified_local',
                'rationale':'Synthetic review checks evidence ties, known limitations and alternatives without claiming verified professional identity.'},
      'baseline_comparison':baselines,'candidate_assessments':[assess], 'relations':[], 'sequences':[]
    }
    cv.validate_obj('c5f-context',rank_ctx)
    ranked=sr.build(handoff,ctx,sug,rank_ctx)
    assert ranked['ranking_status']=='ready_for_review' and ranked['recommendation_status']=='single_preferred_for_review'
    assert ranked['preferred_suggestion_id']=='sug:clarify-basis' and ranked['legal_conclusion_status']=='not_determined'
    assert ranked['review_identity_assurance']=='unverified_local'
    cv.validate_obj('c5f-ranked-suggestions',ranked)
    results.append('c5f_reviewer_gated_single_priority_for_review')

    # Fabricating, removing, or relabelling a C5e candidate is rejected by exact replay.
    forged=copy.deepcopy(sug); forged['candidates'][0]['validation_status']='recommendation'
    try: sr.build(handoff,ctx,forged,rank_ctx)
    except sr.RankingError as e: assert 'ranking_review_binding_mismatch:c5e_candidates_sha256' in str(e)
    else: raise AssertionError('C5f trusted forged C5e output')
    results.append('c5f_replays_exact_c5e_and_rejects_forged_labels')

    # All C5e candidates must be individually assessed; no selective omission permitted.
    missing_reviews=copy.deepcopy(rank_ctx); missing_reviews['candidate_assessments']=[]
    try: sr.build(handoff,ctx,sug,missing_reviews)
    except sr.RankingError as e: assert 'all_c5e_candidates_must_be_assessed' in str(e)
    else: raise AssertionError('unreviewed C5e candidate silently omitted')
    results.append('c5f_cannot_cherry_pick_unreviewed_candidates')

    # A strong legal-support rating must cite a bounded reference; an arbitrary one is not accepted.
    unsupported=copy.deepcopy(rank_ctx); unsupported['candidate_assessments'][0]['rating_basis_refs']=['invented:source']
    try: sr.build(handoff,ctx,sug,unsupported)
    except sr.RankingError as e: assert 'rating_reference_outside_handoff' in str(e)
    else: raise AssertionError('free-form legal support invented in ranking')
    results.append('c5f_ratings_bound_to_promoted_support')

    # Unknown opposing evidence and changed assumptions defer options and require new review, never create preference.
    adverse=copy.deepcopy(rank_ctx); adverse['candidate_assessments'][0]['counterevidence_state']='material_conflict'
    adverse['candidate_assessments'][0]['assumptions_state']='changed'
    bad_rank=sr.build(handoff,ctx,sug,adverse)
    assert not bad_rank['priority_tiers'] and bad_rank['preferred_suggestion_id'] is None
    assert bad_rank['ranking_status']=='no_eligible_options' and any('assumptions_changed' in r for r in bad_rank['excluded_options'][0]['reasons'])
    assert bad_rank['analysis_returns']
    results.append('c5f_changed_assumptions_and_contrary_evidence_invalidate_rank')

    # No-action with unchecked deadline/waiver rights cannot pass C5e merely by mislabelling inaction=false.
    invalid_none=copy.deepcopy(none_ctx)
    invalid_none['proposals'][0]['inaction_or_delay']=False
    invalid_none['proposals'][0]['deadline_waiver_review']='not_applicable'
    rejected_none=sg.build(handoff,invalid_none,adapted,original)
    assert not rejected_none['candidates'] and 'no_action_requires_cleared_inaction_risk' in rejected_none['analysis_returns'][0]['validation_reasons']
    results.append('c5f_no_action_requires_precleared_waiver_risk')

    # A non-stratagem clarification is a comparable baseline, not a forced adapted-stratagem match.
    combo=copy.deepcopy(ctx); combo['context_version']='0.2.0'
    q=copy.deepcopy(combo['proposals'][0]); q['suggestion_id']='sug:direct-clarify'; q['candidate_kind']='direct_action'
    q['adapted_stratagem_id']=None; q['original_stratagem_id']=None; q['baseline_kind']='request_clarification'
    q['supporting_attack_angle_refs']=[]; q['supporting_route_refs']=[]
    q['action_summary']='Request ordinary clarification without relying on a stratagem or asserting a specific entitlement.'
    combo['proposals'].append(q)
    direct=sg.build(handoff,combo,adapted,original)
    assert len(direct['candidates'])==2 and any(x['candidate_kind']=='direct_action' for x in direct['candidates'])
    direct_assessment=copy.deepcopy(assess); direct_assessment['suggestion_id']='sug:direct-clarify'
    direct_assessment['ratings']=dict(factors,legal_support_strength='not_applicable',remedy_power='not_applicable',systemic_value='low')
    direct_assessment['rating_basis_refs']=[]
    combo_r=copy.deepcopy(rank_ctx); combo_r['candidate_assessments'].append(direct_assessment)
    combo_r['bindings']['c5e_context_sha256']=cv.digest_obj(combo)
    combo_r['bindings']['c5e_candidates_sha256']=cv.digest_obj(direct)
    for x in combo_r['baseline_comparison']:
        if x['baseline_kind']=='request_clarification':
            x['review_status']='represented'; x['suggestion_id']='sug:direct-clarify'
            x['rationale']='The neutral direct clarification is represented by a distinct reviewed C5e option.'
    ranked_combo=sr.build(handoff,combo,direct,combo_r)
    assert ranked_combo['recommendation_status']=='alternatives_for_review' and ranked_combo['preferred_suggestion_id'] is None
    assert {'sug:direct-clarify','sug:clarify-basis'}<=set(ranked_combo['priority_tiers'][0]['suggestion_ids'])
    results.append('c5f_direct_baseline_compared_without_forced_stratagem')

    # A second distinct stratagem may be chained only with an explicit documented relation; chains stay conditional.
    chain=copy.deepcopy(combo); q=copy.deepcopy(chain['proposals'][0]); q['suggestion_id']='sug:record-next'; q['adapted_stratagem_id']='adapted:22'; q['original_stratagem_id']='original:22'
    q['action_summary']='After a material authority response, request written confirmation of its exact procedural position.'
    chain['proposals'].append(q)
    chain_out=sg.build(handoff,chain,adapted,original)
    chain_r=copy.deepcopy(combo_r); chain_assessment=copy.deepcopy(assess); chain_assessment['suggestion_id']='sug:record-next'
    chain_r['bindings']['c5e_context_sha256']=cv.digest_obj(chain)
    chain_r['bindings']['c5e_candidates_sha256']=cv.digest_obj(chain_out)
    chain_r['candidate_assessments'].append(chain_assessment)
    chain_r['relations']=[{'first_id':'sug:clarify-basis','second_id':'sug:record-next','relationship':'response_before',
        'rationale':'The follow-up is conditional on the authority response and cannot proceed on a guessed answer.'}]
    chain_r['sequences']=[{'sequence_id':'chain:ask-then-record','steps':['sug:clarify-basis','sug:record-next'],
        'purpose':'Preserve the initial question, obtain a response, then decide whether a confirming follow-up helps.',
        'reassessment_trigger':'A material authority response, changed deadline, new fact, or change in available legal route.'}]
    chained=sr.build(handoff,chain,chain_out,chain_r)
    assert chained['conditional_sequences'][0]['sequence_status']=='conditional_for_review'
    assert chained['conditional_sequences'][0]['reassessment_trigger']
    results.append('c5f_response_gated_sequence_requires_reassessment')

    # A conflict is explicit; conflicting steps can never be combined into one sequence.
    conflict=copy.deepcopy(chain_r); conflict['relations'].append({
        'first_id':'sug:direct-clarify','second_id':'sug:record-next','relationship':'conflict',
        'rationale':'Synthetic reviewer declares these two moves incompatible given the specific case constraints.'})
    conflict['sequences'].append({'sequence_id':'chain:incompatible','steps':['sug:direct-clarify','sug:record-next'],
        'purpose':'Attempt a deliberately incompatible two-step chain to exercise fail-closed behavior.',
        'reassessment_trigger':'Any material new response or change in the constraints requires renewed validation.'})
    conflict_rank=sr.build(handoff,chain,chain_out,conflict)
    assert len(conflict_rank['conflicts'])==1
    assert next(x for x in conflict_rank['conditional_sequences'] if x['sequence_id']=='chain:incompatible')['sequence_status']=='deferred'
    results.append('c5f_conflicting_stratagems_never_automatically_chained')

    # Cyclic sequencing is structurally inconsistent and must be rejected, not silently re-ordered.
    cycle=copy.deepcopy(chain_r); cycle['relations'].append({
        'first_id':'sug:record-next','second_id':'sug:clarify-basis','relationship':'precedes',
        'rationale':'Contradictory reverse ordering deliberately creates a sequencing cycle.'})
    try: sr.build(handoff,chain,chain_out,cycle)
    except sr.RankingError as e: assert 'precedes_cycle' in str(e)
    else: raise AssertionError('C5f accepted circular precedence')
    results.append('c5f_precedence_cycles_rejected')

    # Omitting a baseline, even in a single candidate test, prevents unique preference.
    incomplete=copy.deepcopy(rank_ctx)
    incomplete['baseline_comparison'][0]['review_status']='unresolved'
    incomplete['baseline_comparison'][0]['rationale']='A relevant direct alternative has not yet been assessed for case compatibility.'
    inc=sr.build(handoff,ctx,sug,incomplete)
    assert inc['ranking_status']=='incomplete' and inc['preferred_suggestion_id'] is None
    results.append('c5f_unresolved_baseline_blocks_unique_preference')

    # Comparison never feeds back into analysis or mutates C5e; different reviews change ranking only.
    hash_hand=cv.digest_obj(handoff); hash_sug=cv.digest_obj(sug)
    _=sr.build(handoff,ctx,sug,adverse)
    assert hash_hand==cv.digest_obj(handoff) and hash_sug==cv.digest_obj(sug)
    results.append('c5f_ranking_one_way_analysis_immutable')

    # Reusing the same review after a change to the action text is an explicit stale-review failure.
    revised_ctx=copy.deepcopy(ctx)
    revised_ctx['proposals'][0]['action_summary']='Rephrased procedural clarification proposal after new information.'
    revised_c5e=sg.build(handoff,revised_ctx,adapted,original)
    try: sr.build(handoff,revised_ctx,revised_c5e,rank_ctx)
    except sr.RankingError as e: assert 'ranking_review_binding_mismatch' in str(e)
    else: raise AssertionError('stale rank review accepted after proposal changed')
    results.append('c5f_review_digest_pins_exact_proposal_text')

    # Rebinding a tampered C5e output cannot defeat deterministic replay.
    tamper=copy.deepcopy(sug); tamper['candidates'][0]['action_summary']='Altered after C5e validation.'
    rebound=copy.deepcopy(rank_ctx); rebound['bindings']['c5e_candidates_sha256']=cv.digest_obj(tamper)
    try: sr.build(handoff,ctx,tamper,rebound)
    except sr.RankingError as e: assert 'c5e_replay_mismatch' in str(e)
    else: raise AssertionError('C5f accepted altered C5e even after digest rebinding')
    results.append('c5f_exact_replay_detects_rebound_forged_output')

    # Even if a reviewer marks one baseline inapplicable, an existing direct-action candidate must be accounted for.
    missed=copy.deepcopy(combo_r)
    for b in missed['baseline_comparison']:
        if b['baseline_kind']=='request_clarification':
            b['review_status']='not_applicable'; b['suggestion_id']=None
            b['rationale']='Deliberately hides an already present direct clarification comparator.'
    try: sr.build(handoff,combo,direct,missed)
    except sr.RankingError as e: assert 'existing_baseline_not_represented' in str(e)
    else: raise AssertionError('existing direct baseline omitted from review')
    results.append('c5f_existing_baseline_cannot_be_misclassified_away')

    # Exploratory strategic conjecture is not evidence-backed priority input.
    guess=copy.deepcopy(rank_ctx)
    guess['candidate_assessments'][0]['basis_classification']='exploratory_possibility'
    unranked=sr.build(handoff,ctx,sug,guess)
    assert unranked['preferred_suggestion_id'] is None
    assert 'exploratory_possibility_not_rankable' in unranked['deferred_options'][0]['reasons']
    results.append('c5f_facts_inferences_and_exploratory_guesses_distinct')

    # Explicitly disqualified stratagem does not veto a fully reviewed safe no-action baseline.
    safe_mix=copy.deepcopy(ctx); safe_mix['context_version']='0.2.0'
    safe_none=copy.deepcopy(none_ctx['proposals'][0]); safe_none['baseline_kind']=None
    safe_mix['proposals'].append(safe_none)
    safe_set=sg.build(handoff,safe_mix,adapted,original)
    safe_review=copy.deepcopy(rank_ctx)
    safe_review['bindings']['c5e_context_sha256']=cv.digest_obj(safe_mix)
    safe_review['bindings']['c5e_candidates_sha256']=cv.digest_obj(safe_set)
    safe_review['candidate_assessments'][0]['disposition']='reject'
    safe_none_assess=copy.deepcopy(assess)
    safe_none_assess['suggestion_id']='sug:none'
    safe_none_assess['ratings']=dict(factors,legal_support_strength='not_applicable',remedy_power='not_applicable')
    safe_none_assess['rating_basis_refs']=[]
    safe_review['candidate_assessments'].append(safe_none_assess)
    for b in safe_review['baseline_comparison']:
        if b['baseline_kind']=='no_action':
            b['review_status']='represented'; b['suggestion_id']='sug:none'
            b['rationale']='The no-action comparator has undergone a specific deadline and waiver review.'
    no_action_rank=sr.build(handoff,safe_mix,safe_set,safe_review)
    assert no_action_rank['preferred_suggestion_id']=='sug:none'
    assert any(x['suggestion_id']=='sug:clarify-basis' for x in no_action_rank['excluded_options'])
    results.append('c5f_rejected_stratagem_allows_safe_no_action_to_lead')

    # When two different options cannot be strictly ordered, expose the actual compared factors.
    assert ranked_combo['top_tier_tradeoffs']
    assert 'legal_support_strength' in ranked_combo['top_tier_tradeoffs'][0]['noncomparable_factors']
    assert not ranked_combo['tradeoffs_truncated']
    results.append('c5f_priority_ties_disclose_metric_tradeoffs')

    # Unknown disclosure requirements on a proposed no-action baseline return to analysis.
    uncertain_none=copy.deepcopy(none_ctx); uncertain_none['proposals'][0]['disclosure_duty_status']='unknown'
    uncertain_none['proposals'][0]['disclosure_review_rationale']='Disclosure obligations have not been reviewed for this case and cannot be assumed absent.'
    unresolved_none=sg.build(handoff,uncertain_none,adapted,original)
    assert len(unresolved_none['analysis_returns'])==1 and not unresolved_none['candidates']
    results.append('c5f_no_action_unknown_disclosure_returns_to_analysis')

    # End-to-end CLI smoke test validates serialized source artifacts rather than just Python APIs.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        files=[]
        for filename,obj in [('handoff.json',handoff),('c5e-context.json',ctx),('c5e-candidates.json',sug),('c5f-context.json',rank_ctx)]:
            fp=td/filename; fp.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); files.append(str(fp))
        result=subprocess.run([sys.executable,str(SCRIPTS/'suggestion_ranking.py'),*files,'--output',str(td/'c5f-ranked.json')],capture_output=True,text=True)
        assert result.returncode==0, result.stderr
        output=cv.load_json(td/'c5f-ranked.json')
        assert output['preferred_suggestion_id']=='sug:clarify-basis'
        cv.validate_obj('c5f-ranked-suggestions',output)
    results.append('c5f_cli_end_to_end_serialized_artifacts')

    print(json.dumps({'status':'passed','count':len(results),'tests':results},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
