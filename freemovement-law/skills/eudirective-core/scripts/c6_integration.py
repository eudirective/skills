#!/usr/bin/env python3
"""C6 synthetic-only controller integration; no legal merits or action authorization."""
import argparse
import contextlib
import hashlib
import io
import os
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import case_controller as controller
import core_source_adapter as adapter
import module_conformance as conformance
import element_model
import topology_engine as topology
import regime_applicability as regimes
import hierarchy_principles as hierarchy
import evidence_deadline_authority as evidence
import attack_angle_synthesis as attacks
import legal_assessment as legal_assessment
import c12_rule_resolution as c12
import c13_document_evidence as c13
import analysis_handoff as handoff_engine
import suggestion_engine as suggestions
import suggestion_ranking as ranking
import c7_trust_gate as trust_gate
import c7_issue_index as issue_index

from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACK = compatibility_root() / 'core-source-pack-manifest-0.6.1.json'
C6_VERSION = '0.5.0'
STAGE_SCHEMAS = {'topology': 'topology-resolution', 'regimes': 'legal-regime-candidates',
                 'c5b': 'c5b-hierarchy-principles', 'c5c': 'c5c-evidence-deadline-authority',
                 'c5d': 'c5d-attack-angle-synthesis', 'c11': 'c11-legal-assessment', 'c12':'c12-legal-resolution', 'c13':'c13-evidence-assessment'}
CODE_PINS = [
    'scripts/case_controller.py', 'scripts/c6_integration.py', 'scripts/core_source_adapter.py',
    'scripts/c7_trust_gate.py', 'scripts/c7_issue_index.py',
    'scripts/c18_source_integrity.py', 'references/source-pack/c18-directive-art2-restoration.json',
    '../eudirective-source-library/compatibility/core-source-pack/core-source-pack-0.6.1/core-source-pack-manifest-0.6.1.json',
    'references/trust/c7-trust-policy.json', 'references/contracts/c7-issue-index.schema.json',
    'scripts/contract_validate.py', 'scripts/module_conformance.py', 'scripts/element_model.py',
    'scripts/topology_engine.py', 'scripts/regime_applicability.py',
    'scripts/hierarchy_principles.py', 'scripts/evidence_deadline_authority.py',
    'scripts/attack_angle_synthesis.py', 'scripts/legal_assessment.py', 'scripts/c12_rule_resolution.py',
    'scripts/c13_document_evidence.py', 'scripts/c14_interpretation.py', 'scripts/c14_review_proposals.py',
    'references/evidence/c14-clause-grammar.json', 'references/evidence/c14-topic-lexicon.json',
    'references/evidence/c13-extraction-patterns.json',
    'references/evidence/c13-document-index.json',
    'references/contracts/c13-evidence-set.schema.json',
    'references/contracts/c13-evidence-assessment.schema.json',
    'references/contracts/c11-legal-assessment.schema.json',
    'references/legal-assessment/c11-rule-profiles.json',
    'references/legal-assessment/c12-eu-rules.json',
    'references/legal-assessment/c12-document-index.json',
    'references/contracts/c12-rule-extension.schema.json',
    'references/contracts/c12-fact-ledger.schema.json',
    'references/contracts/c12-legal-resolution.schema.json',
    'scripts/analysis_handoff.py',
    'scripts/suggestion_engine.py', 'scripts/suggestion_ranking.py',
    'references/attack-angles/core-attack-angle-catalog.json',
    'references/stratagems/adapted-stratagem-catalog.json',
    'references/stratagems/original-stratagem-catalog.json',
    'references/routes/core-eu-route-catalog.json',
    'references/jurisdictions/country-aliases.json',
    'references/contracts/controlled-analysis.schema.json',
    'references/contracts/c6-run-manifest.schema.json',
    'references/fixtures/c12/documents/c12-synthetic-01.json',
    'references/fixtures/c12/documents/c12-synthetic-02.json',
    'references/fixtures/c12/documents/c12-synthetic-03.json',
    'references/fixtures/c12/documents/c12-synthetic-04.json',
    'references/fixtures/c12/documents/c12-synthetic-05.json',
    'references/fixtures/c12/documents/c12-synthetic-06.json',
    'references/fixtures/c12/documents/c12-synthetic-07.json',
    'references/fixtures/c12/documents/c12-synthetic-08.json',
    'references/fixtures/c12/documents/c12-synthetic-09.json',
    'references/fixtures/c12/documents/c12-synthetic-10.json',
    'references/fixtures/c12/documents/c12-synthetic-11.json',
    'references/fixtures/c12/documents/c12-synthetic-12.json',
    'references/fixtures/c12/documents/c12-synthetic-13.json',
    'references/fixtures/c13/documents/L1-request.eml',
    'references/fixtures/c13/documents/L1-reply.eml',
    'references/fixtures/c13/documents/L4-decision.pdf',
    'references/fixtures/c13/documents/L4-appeal.eml',
    'references/fixtures/c13/documents/L5-authority.html',
    'references/fixtures/c13/documents/L5-request.eml',
    'references/fixtures/c13/documents/L5-third-party.txt',
    'references/fixtures/c13/documents/L2-vfs-receipt.eml',
    'references/fixtures/c13/documents/L2-choice.txt',
    'references/fixtures/c13/documents/L3-checklist.eml',
    'references/fixtures/c13/documents/L3-alternatives.eml',
    'references/fixtures/c13/documents/L6-visa-gate.eml',
    'references/fixtures/c13/documents/L6-explanatory.txt',
    'references/fixtures/c13/documents/L7-complaint.eml',
    'references/fixtures/c13/documents/L7-jo-note.txt',
    'references/fixtures/c13/documents/L8-paper-demand.eml',
    'references/fixtures/c13/documents/L8-extract.txt',
]

class C6Error(Exception):
    pass


def fail_if(condition, message):
    if condition:
        raise C6Error(message)


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def file_hash(path):
    return sha_bytes(path.read_bytes())


def write_json(path, obj):
    controller.atomic_write_json(path, obj)


def write_bytes_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.c7-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def controller_op(func, state_path, case_id, **kwargs):
    if func is controller.cmd_init:
        args = SimpleNamespace(state=str(state_path), case_id=case_id, **kwargs)
    else:
        state = controller.load_state(state_path)
        args = SimpleNamespace(state=str(state_path), case_id=case_id,
                               expected_revision=state['revision'], **kwargs)
    with contextlib.redirect_stdout(io.StringIO()):
        func(args)
    return controller.load_state(state_path)


def index_file(workdir, relative):
    fail_if(not relative or relative.startswith('/') or '\\' in relative or '..' in Path(relative).parts,
            'unsafe_index_path')
    path = workdir / relative
    fail_if(not path.is_file() or path.is_symlink(), f'missing_or_symlinked_artifact:{relative}')
    return {'path': relative, 'file_sha256': file_hash(path),
            'content_sha256': digest_obj(load_json(path, allow_internal_issue_code=relative.startswith('stages/')))}


def stage_outputs(case, elements, actors, c5b_context, c5c_context, source_pack, country_pairs, c12_extensions=(), c12_ledger=None, c13_evidence_set=None):
    members = [pair for pair in country_pairs if load_json(Path(pair[0]))['module_family'] == 'member_state']
    top = topology.build_topology(case, elements)
    r = regimes.build_candidates(case, top, elements, source_pack, actors)
    b = hierarchy.build(case, r, elements, c5b_context, members, source_pack)
    c = evidence.build(case, r, b, elements, c5c_context, country_pairs, source_pack)
    d = attacks.build(case, r, b, c, elements, country_pairs, source_pack)
    assessed = legal_assessment.build(case, elements, d, source_pack, country_pairs)
    resolved = c12.build(case, elements, d, source_pack, country_pairs, c12_extensions, c12_ledger)
    documentary = c13.build(case, elements, resolved, c13_evidence_set)
    results = {'topology': top, 'regimes': r, 'c5b': b, 'c5c': c, 'c5d': d, 'c11': assessed, 'c12':resolved, 'c13':documentary}
    for name, obj in results.items():
        validate_obj(STAGE_SCHEMAS[name], obj)
    return results


def require_input(role, obj):
    if role == 'source_pack':
        if obj.get('pack_version') != '0.6.1':
            raise trust_gate.C7TrustError('c18_active_source_pack_required')
        assurance = trust_gate.require_source_pack(obj)
        from c18_source_integrity import audit as c18_audit
        c18_audit()  # enforce restored Article 2, single-source delta and reported 21-note gaps
        return assurance
    return trust_gate.require_approved(role, obj)


def preflight_inputs(args):
    """Reject unapproved data before creating the case workspace (no raw snapshots)."""
    trust_gate.require_synthetic_run_metadata(args.run_id, args.time_of_check)
    selected = [('case', args.case, 'case-input'),
                ('elements', args.elements, 'element-instance-bundle'),
                ('actors', args.actors, 'actor-context'),
                ('c5b_context', args.c5b_context, 'c5b-context'),
                ('c5c_context', args.c5c_context, 'c5c-context'),
                ('source_pack', args.source_pack, 'core-source-pack')]
    for role, source, schema in selected:
        if source is not None:
            value = load_json(Path(source))
            validate_obj(schema, value)
            require_input(role, value)
    as_of_assurance = trust_gate.require_source_as_of(load_json(Path(args.source_pack)), args.time_of_check)
    if args.c13_evidence_set:
        obj=load_json(Path(args.c13_evidence_set))
        validate_obj('c13-evidence-set',obj)
        trust_gate.require_approved('c13_evidence_set',obj)
    if args.c12_fact_ledger:
        obj=load_json(Path(args.c12_fact_ledger))
        validate_obj('c12-fact-ledger',obj)
        trust_gate.require_approved('c12_fact_ledger',obj)
    for ext_file in args.c12_rule_extension:
        obj=load_json(Path(ext_file))
        validate_obj('c12-rule-extension',obj)
        trust_gate.require_approved('c12_rule_extension',obj)
    for manifest_file, export_file in args.module_pair:
        for role, name, schema in [('module_manifest', manifest_file, 'module-manifest'),
                                    ('module_export', export_file, 'module-export')]:
            value = load_json(Path(name))
            validate_obj(schema, value)
            require_input(role, value)
    return as_of_assurance


def snapshot(workdir, relative, source, schema=None, approval_role=None):
    obj = load_json(Path(source))
    if schema:
        validate_obj(schema, obj)
    if approval_role:
        require_input(approval_role, obj)
    dest = workdir / relative
    write_json(dest, obj)
    return dest


def make_input(workdir, key, path, schema=None, approval_role=None):
    if path is None:
        return None, None
    rel = f'inputs/{key}.json'
    dest = snapshot(workdir, rel, path, schema, approval_role)
    return dest, index_file(workdir, rel)


def load_indexed(workdir, item):
    if item is None:
        return None
    current = index_file(workdir, item['path'])
    fail_if(current != item, f'artifact_modified:{item["path"]}')
    return load_json(workdir / item['path'], allow_internal_issue_code=item['path'].startswith('stages/'))


def check_code_pins(pins):
    fail_if(set(pins) != set(CODE_PINS), 'code_pin_set_mismatch')
    for relative in CODE_PINS:
        path = ROOT / relative
        fail_if(not path.is_file() or file_hash(path) != pins[relative], f'code_or_policy_modified:{relative}')


def prepare(args):
    workdir = Path(args.workdir).resolve()
    fail_if(workdir.exists(), 'workdir_already_exists')
    fail_if(not args.module_pair, 'c6_requires_conformant_country_module_pairs')
    source_as_of = preflight_inputs(args)
    workdir.mkdir(parents=True)
    inputs = {}
    case_path, inputs['case'] = make_input(workdir, 'case', args.case, 'case-input', 'case')
    case = load_json(case_path)
    fail_if(case['privacy_classification'] != 'synthetic', 'c6_synthetic_only_private_and_public_intake_disabled')
    elements_path, inputs['elements'] = make_input(workdir, 'elements', args.elements, 'element-instance-bundle', 'elements')
    elements = load_json(elements_path) if elements_path else None
    if elements:
        element_model.check_bundle(elements, *element_model.load_model()[::2])
    actors_path, inputs['actors'] = make_input(workdir, 'actors', args.actors, 'actor-context', 'actors')
    b_path, inputs['c5b_context'] = make_input(workdir, 'c5b-context', args.c5b_context, 'c5b-context', 'c5b_context')
    c_path, inputs['c5c_context'] = make_input(workdir, 'c5c-context', args.c5c_context, 'c5c-context', 'c5c_context')
    source_path, inputs['source_pack'] = make_input(workdir, 'source-pack', args.source_pack, 'core-source-pack', 'source_pack')
    ledger_path, inputs['c12_fact_ledger'] = make_input(workdir, 'c12-fact-ledger',args.c12_fact_ledger, 'c12-fact-ledger','c12_fact_ledger')
    c13_path,inputs['c13_evidence_set']=make_input(workdir,'c13-evidence-set',args.c13_evidence_set,'c13-evidence-set','c13_evidence_set')
    extension_paths=[]
    for ei, ext_file in enumerate(args.c12_rule_extension):
        ep, entry=make_input(workdir, f'c12-ext-{ei:02d}',ext_file,'c12-rule-extension','c12_rule_extension')
        extension_paths.append(ep)
        inputs[f'c12_extension_{ei:02d}']=entry
    source_trust = trust_gate.require_source_pack(load_json(source_path))
    core_m, core_e = adapter.build_objects(load_json(source_path))
    write_json(workdir / 'inputs/core-manifest.json', core_m)
    write_json(workdir / 'inputs/core-export.json', core_e)
    inputs['core_manifest'] = index_file(workdir, 'inputs/core-manifest.json')
    inputs['core_export'] = index_file(workdir, 'inputs/core-export.json')
    pairs = []
    for i, pair in enumerate(args.module_pair):
        m_path, m_idx = make_input(workdir, f'module-{i:02d}-manifest', pair[0], 'module-manifest', 'module_manifest')
        e_path, e_idx = make_input(workdir, f'module-{i:02d}-export', pair[1], 'module-export', 'module_export')
        conformance.validate_pair(load_json(m_path), load_json(e_path))
        pairs.append((m_path, e_path))
        inputs[f'module_{i:02d}_manifest'] = m_idx
        inputs[f'module_{i:02d}_export'] = e_idx
    fail_if(len(pairs) > controller.MAX_REGISTERED_MODULES - 1, 'module_budget_exceeded')
    fail_if(len(extension_paths)>len(pairs), 'more_c12_extensions_than_modules')
    state_path = workdir / 'state.json'
    state = controller_op(controller.cmd_init, state_path, case['case_id'], run_id=args.run_id,
                          profile='cooperative_local', time_of_check=args.time_of_check)
    state = controller_op(controller.cmd_accept_case, state_path, case['case_id'], input=str(case_path))
    state = controller_op(controller.cmd_register_module, state_path, case['case_id'],
                          manifest=str(workdir / inputs['core_manifest']['path']),
                          export=str(workdir / inputs['core_export']['path']))
    for mp, ep in pairs:
        state = controller_op(controller.cmd_register_module, state_path, case['case_id'],
                              manifest=str(mp), export=str(ep))
    state = controller_op(controller.cmd_freeze_context, state_path, case['case_id'])
    stages = stage_outputs(case, elements, load_json(actors_path) if actors_path else None,
                           load_json(b_path) if b_path else None, load_json(c_path) if c_path else None,
                           load_json(source_path), [(str(x), str(y)) for x, y in pairs],
                           [load_json(p) for p in extension_paths], load_json(ledger_path) if ledger_path else None,
                           load_json(c13_path) if c13_path else None)
    indexed_stages = {}
    for name, obj in stages.items():
        relative = f'stages/{name}.json'
        write_json(workdir / relative, obj)
        indexed_stages[name] = index_file(workdir, relative)
    requirements = {'contract_version': '0.2.0', 'requirements': [
        {'requirement_id': 'c6:mechanical-chain', 'area': 'source_provenance', 'scope': 'case',
         'required_for_full_release': True, 'description': 'C5a-C5d plus C11a/b fact-value review exact synthetic chain and controller composition checked'},
        {'requirement_id': 'c6:legal-merits-review', 'area': 'legal_regime', 'scope': 'case',
         'required_for_full_release': True, 'description': 'Substantive legal correctness and case merits require independent review'},
        {'requirement_id': 'c6:source-freshness', 'area': 'source_freshness', 'scope': 'sources',
         'required_for_full_release': True, 'description': 'Required module freshness labels and code-pinned EU source metadata-age policy meet the synthetic as-of check; actual official currency is not established'},
        {'requirement_id': 'c6:optional-context', 'area': 'local_context', 'scope': 'case',
         'required_for_full_release': False, 'description': 'Optional jurisdictional context completeness'},
    ]}
    write_json(workdir / 'inputs/requirements.json', requirements)
    inputs['requirements'] = index_file(workdir, 'inputs/requirements.json')
    state = controller_op(controller.cmd_set_requirements, state_path, case['case_id'],
                          input=str(workdir / 'inputs/requirements.json'))
    state = controller_op(controller.cmd_update_requirement, state_path, case['case_id'],
                          requirement_id='c6:mechanical-chain', status='supported', reason=None, detail='')
    fresh = not state.get('freshness_blocked_required_modules')
    state = controller_op(controller.cmd_update_requirement, state_path, case['case_id'],
                          requirement_id='c6:source-freshness',
                          status='supported' if fresh else 'blocked',
                          reason=None if fresh else 'source_missing_or_stale',
                          detail='' if fresh else 'Required module freshness assurance not satisfied')
    optional = state['missing_optional_modules']
    state = controller_op(controller.cmd_update_requirement, state_path, case['case_id'],
                          requirement_id='c6:optional-context',
                          status='blocked' if optional else 'not_applicable',
                          reason='optional_context_unavailable' if optional else None,
                          detail=','.join(optional))
    write_json(workdir / 'prepared-controller-state.json', state)
    manifest = {
        'c6_version': C6_VERSION, 'case_id': case['case_id'], 'run_id': args.run_id,
        'controller_protocol': controller.PROTOCOL_VERSION, 'contract_version': controller.CONTRACT_VERSION,
        'source_trust': source_trust, 'source_as_of': source_as_of,
        'element_model_version': controller.ELEMENT_MODEL_VERSION, 'status': 'prepared_review_needed',
        'prepared_revision': state['revision'], 'prepared_state_sha256': digest_obj(state),
        'inputs': inputs, 'country_module_count': len(pairs), 'c12_extension_count':len(extension_paths),
        'c13_enrolled':c13_path is not None, 'stages': indexed_stages,
        'script_and_policy_sha256': {p: file_hash(ROOT / p) for p in CODE_PINS},
        'limitations': ['Synthetic-only case; no authenticated reviewer or host-private-data capability.',
                        'C5a-C5d and C11a/b profiles never establish legal violations, substantive applicability or remedies.',
                        'C6 legal-merits review remains not checked; controller release must be limited.',
                        ('C8 source assurance: ' + source_trust['source_assurance'] + '; the 0.6.1 catalogue requires all 47 bundled representations to match their SHA-256 digests. This does not independently revalidate official-site currency, authorship or substantive legal correctness.'),
                        'C7 intake accepts only code-policy-pinned fictional fixture content; host private-data protection is not proven.',
                        'C13 only extracts legacy passage-anchored statements from pinned fictional documents; C14 adds unreviewed multilingual interpretation candidates; no real-file authentication or merits review.'],
    }
    validate_obj('c6-run-manifest', manifest)
    write_json(workdir / 'c6-run-manifest.json', manifest)
    return {'status': 'prepared_review_needed', 'case_id': case['case_id'], 'stage': state['stage'],
            'controller_revision': state['revision'], 'c5d_sha256': digest_obj(stages['c5d']),
            'manifest_sha256': digest_obj(manifest), 'required_freshness_blockers': state['freshness_blocked_required_modules'],
            'missing_optional_modules': state['missing_optional_modules']}


def verify_prepared(workdir, allow_released=False):
    manifest = load_json(workdir / 'c6-run-manifest.json')
    validate_obj('c6-run-manifest', manifest)
    check_code_pins(manifest['script_and_policy_sha256'])
    inputs = {key: load_indexed(workdir, idx) for key, idx in manifest['inputs'].items()}
    case = inputs['case']
    for key, role in [('case','case'),('elements','elements'),('actors','actors'),
                      ('c5b_context','c5b_context'),('c5c_context','c5c_context')]:
        if inputs[key] is not None:
            trust_gate.require_approved(role, inputs[key])
    verified_trust = trust_gate.require_source_pack(inputs['source_pack'])
    fail_if(verified_trust != manifest['source_trust'], 'c7_source_attestation_mismatch')
    trust_gate.require_synthetic_run_metadata(manifest['run_id'], manifest['source_as_of']['as_of_time'])
    actual_as_of = trust_gate.require_source_as_of(inputs['source_pack'], manifest['source_as_of']['as_of_time'])
    fail_if(actual_as_of != manifest['source_as_of'], 'c7_source_as_of_attestation_mismatch')
    if inputs.get('c13_evidence_set') is not None:
        trust_gate.require_approved('c13_evidence_set',inputs['c13_evidence_set'])
    fail_if((inputs.get('c13_evidence_set') is not None)!=manifest['c13_enrolled'], 'c13_enrollment_mismatch')
    if inputs.get('c12_fact_ledger') is not None:
        trust_gate.require_approved('c12_fact_ledger',inputs['c12_fact_ledger'])
    for j in range(manifest['c12_extension_count']):
        trust_gate.require_approved('c12_rule_extension', inputs[f'c12_extension_{j:02d}'])
    for i in range(manifest['country_module_count']):
        trust_gate.require_approved('module_manifest', inputs[f'module_{i:02d}_manifest'])
        trust_gate.require_approved('module_export', inputs[f'module_{i:02d}_export'])
    fail_if(case['privacy_classification'] != 'synthetic' or case['case_id'] != manifest['case_id'], 'case_identity_changed')
    prepared_state = load_json(workdir / 'prepared-controller-state.json')
    fail_if(digest_obj(prepared_state) != manifest['prepared_state_sha256'], 'prepared_state_changed')
    state = controller.load_state(workdir / 'state.json')
    fail_if(state['case_id'] != manifest['case_id'] or state['run_id'] != manifest['run_id'] or
            state['time_of_check'] != manifest['source_as_of']['as_of_time'] or
            prepared_state['time_of_check'] != manifest['source_as_of']['as_of_time'],
            'controller_identity_or_time_mismatch')
    m, e = adapter.build_objects(inputs['source_pack'])
    fail_if(digest_obj(m) != digest_obj(inputs['core_manifest']) or
            digest_obj(e) != digest_obj(inputs['core_export']), 'source_pack_adapter_changed')
    # Reject mutated serialized stage files before any expensive legal-engine replay.
    # Replay still runs on untouched-looking artifacts to detect forged digest rebinding.
    for stage_name in STAGE_SCHEMAS:
        load_indexed(workdir, manifest['stages'][stage_name])
    pairs = []
    for i in range(manifest['country_module_count']):
        mp = workdir / manifest['inputs'][f'module_{i:02d}_manifest']['path']
        ep = workdir / manifest['inputs'][f'module_{i:02d}_export']['path']
        conformance.validate_pair(load_json(mp), load_json(ep))
        pairs.append((str(mp), str(ep)))
    replay = stage_outputs(case, inputs['elements'], inputs['actors'], inputs['c5b_context'],
                           inputs['c5c_context'], inputs['source_pack'], pairs,
                           [inputs[f'c12_extension_{i:02d}'] for i in range(manifest['c12_extension_count'])],
                           inputs['c12_fact_ledger'], inputs['c13_evidence_set'])
    for name, obj in replay.items():
        old = load_indexed(workdir, manifest['stages'][name])
        fail_if(old != obj or digest_obj(old) != manifest['stages'][name]['content_sha256'],
                f'c5_stage_replay_mismatch:{name}')
    fail_if(state['case']['sha256'] != digest_obj(case), 'controller_case_binding_mismatch')
    fail_if(state['dependency_pins'] != prepared_state['dependency_pins'], 'controller_dependency_mismatch')
    fail_if(state['modules'] != prepared_state['modules'] or
            state['reference_index'] != prepared_state['reference_index'] or
            state['requirements'] != prepared_state['requirements'] or
            state.get('missing_optional_modules') != prepared_state.get('missing_optional_modules') or
            state.get('freshness_blocked_required_modules') != prepared_state.get('freshness_blocked_required_modules'),
            'controller_registered_context_modified')
    if not allow_released:
        fail_if(state['stage'] != 'requirements_set' or state['revision'] != manifest['prepared_revision'] or
                digest_obj(state) != manifest['prepared_state_sha256'], 'controller_prepared_revision_changed')
    else:
        fail_if(state['stage'] != 'released' or state['revision'] != manifest['prepared_revision'] + 3,
                'released_controller_state_invalid')
        fail_if(state['history'][:len(prepared_state['history'])] != prepared_state['history'] or
                [e['action'] for e in state['history'][len(prepared_state['history']):]] !=
                ['propose-analysis', 'validate-analysis', 'release'], 'controller_release_transition_mismatch')
    return manifest, inputs, replay, state, pairs


def neat(s):
    return ' '.join(str(s).split())[:240].replace('`', "'").replace('|', '/')


def review_screen_passes(screening, stages):
    """C13 can only hold back a C12 candidate, never certify or upgrade it."""
    if screening is None or screening['status']!='supported_for_review':
        return False
    if stages['c13']['mode']!='enrolled':
        return True
    links={x['assessment_id']:x for x in stages['c13']['rule_links']}
    matched=links.get(screening.get('assessment_id'))
    return bool(matched and matched['status']=='passage_anchored_for_review')


def controlled_projection(case, stages, state):
    """Project review candidates to cannot_assess; never promote into legal findings."""
    reference = state['reference_index']
    usable = set(reference['usable_source_ids'])
    known_rules = set(reference['rule_ids'])
    known_auth = set(reference['authority_ids'])
    known_routes = set(reference['route_ids'])
    known_attacks = set(reference['attack_angle_ids'])
    findings = []
    missing_refs = set()
    c11_by_angle = {a['attack_angle_id']:a for a in stages['c11']['assessments'] if a['attack_angle_id']}
    c12_by_angle={a['attack_angle_id']:a for a in stages['c12']['assessments'] if a['attack_angle_id']}
    for angle in stages['c5d']['attack_angles']:
        c12_enrolled=bool(stages['c12']['bindings']['fact_ledger_sha256'] or stages['c12']['bindings']['country_rule_extensions'])
        screening = (c12_by_angle.get(angle['attack_angle_id']) if c12_enrolled else None) or c11_by_angle.get(angle['attack_angle_id'])
        if not review_screen_passes(screening, stages):
            continue
        # Only a supported-for-review or candidate issue belongs in the user-visible
        # findings. Unsupported / insufficient-evidence records remain fully
        # available in the exhaustive C7 issue index, not as apparent findings.
        if angle['assessment_status'] not in {'candidate', 'supported'}:
            continue
        sources = sorted(set(angle['source_refs']) & usable)
        missing_refs.update(set(angle['source_refs']) - usable)
        rules = sorted(set(angle['rule_refs']) & known_rules)
        missing_refs.update(set(angle['rule_refs']) - known_rules)
        auth = sorted(set(angle['authority_refs']) & known_auth)
        missing_refs.update(set(angle['authority_refs']) - known_auth)
        routes = sorted(set(angle['route_refs']) & known_routes)
        missing_refs.update(set(angle['route_refs']) - known_routes)
        aids = [angle['attack_angle_id']] if angle['attack_angle_id'] in known_attacks else []
        if not aids:
            # Core catalogues are not frozen country-module records: no false claim of controller ID registration.
            missing_refs.add(angle['attack_angle_id'])
        findings.append({
            'finding_id': 'c6:angle:%03d' % (len(findings)+1), 'status': 'cannot_assess',
            'claim': 'Review hypothesis only: ' + neat(angle['label']) + '. No legal violation is determined.',
            'fact_refs': [], 'source_refs': sources, 'rule_refs': rules, 'authority_refs': auth,
            'route_refs': routes, 'attack_angle_refs': aids,
            'uncertainties': ['C5d assessment=' + angle['assessment_status'],
                              'legal_violation_status=not_determined',
                              'C12/C11 fact-pattern status=' + screening['status'] + '; legal violation not determined.',
                              'Case-specific exceptions and evidence require legal review.'],
        })
    deadlines = []
    for item in stages['c5c']['deadline_assessments']:
        refs = set(item['source_refs'])
        missing_refs.update(refs - usable)
        can_calc = item['calculation_status'] == 'exact' and bool(refs) and refs <= usable and \
            item['deadline_ref'] in reference['deadline_ids'] and item['rule_ref'] in known_rules
        deadlines.append({
            'deadline_id': 'c6:deadline:%03d' % (len(deadlines)+1),
            'label': neat(item['request_id']) + ' (mechanical candidate; not a final legal deadline)',
            'status': 'calculated' if can_calc else 'unknown',
            'date': item['calculated_date'] if can_calc else None,
            'source_refs': sorted(refs & usable),
            'rule_refs': [item['rule_ref']] if can_calc else [],
            'deadline_refs': [item['deadline_ref']] if can_calc else [],
            'limitations': ['C5c status=' + item['calculation_status'],
                            'Date does not establish that the underlying legal rule applies to the case.'],
        })
    limitations = [
        'C6 SYNTHETIC TEST ONLY. Limited controller release, not case-specific legal advice.',
        'C5a-C5d and C11-C13 final legal determinations remain not_determined.',
        'C13 documentary status: '+stages['c13']['mode']+'; C14 candidate interpretations are review-only and do not establish authority authenticity or factual truth.',
        'C12 NOVEL ISSUES: ' + str(len(stages['c12']['novel_issues'])) +
        ' unprofiled candidate(s) explicitly preserved in c12-legal-resolution.md and complete issue-index; do not assume they are irrelevant.',
        'Directive 2004/38/Visa Code lex-specialis relationship remains unresolved where indicated.',
        'National source and factual assertions require case-specific substantive review.',
        'Controller-registered source references include verified identity/version notes that do not establish verbatim source wording or pinpoint quotations.',
        'C5e/C5f strategic options are entirely outside this controlled legal analysis.',
        'Private data mode, external delivery, authenticated reviewers and publication authorization are not enabled.',
    ]
    if state.get('missing_optional_modules'):
        limitations.append('Missing optional module requests: ' + ', '.join(state['missing_optional_modules']))
    if state.get('freshness_blocked_required_modules'):
        limitations.append('Required module freshness blockers: ' + ', '.join(x['module_key'] for x in state['freshness_blocked_required_modules']))
    record = issue_index.build(stages, state)
    limitations.append('C7 COMPLETE ISSUE INDEX: see companion issue-index.md and issue-index.json (all ' +
                       str(record['issue_count']) + ' issues, no hidden overflow); index JSON SHA-256: ' + digest_obj(record))
    for key, count in sorted(record['counts_by_stage_and_category'].items()):
        limitations.append('C7 index count ' + key + ': ' + str(count) + '. Full values and source-stage pointers in companion index.')
    for name in ('regimes', 'c5b', 'c5c', 'c5d'):
        if stages[name].get('resolution_status') == 'blocked':
            limitations.append(name + ': blocked; no downstream legal promotion permitted.')
    if stages['regimes'].get('source_pack_version') == '0.6.1':
        limitations.append('C8 source trust verifies all 47 bundled representation bytes against the pinned source manifest, including 21 identity-only source notes and the targeted Article 2(2)(a) correction. Official live currency, document authenticity and legal correctness have not been independently established.')
    else:
        limitations.append('C7 source trust pins the 0.5.0 manifest/46 representation digests, not their missing representation bytes or a live official-source check.')
    obj = {
        'contract_version': controller.CONTRACT_VERSION,
        'analysis_id': 'c6:analysis:' + state['run_id'],
        'case_id': case['case_id'], 'bound_state_revision': state['revision'],
        'requested_release_mode': 'limited',
        'applicable_legal_regime': [
            'C5a review candidate (NOT final applicability): ' + neat(x['element_id']) +
            ' / ' + neat(x['disposition']) for x in stages['regimes']['candidates']
        ],
        'findings': findings, 'deadlines': deadlines,
        'recommendations': [], 'limitations': limitations,
        'summary': 'Synthetic deterministic C6 analysis integration only. Legal applicability, violations, route entitlements and remedies have not been determined. Findings are review hypotheses, not established legal conclusions.',
    }
    validate_obj('controlled-analysis', obj)
    return obj


def render_strategy(handoff, c5e, c5f, analysis_sha, release_sha):
    lines = ['# Strategy review only', '',
             'This document is not part of the controller-validated legal analysis. No proposed action is authorized.', '',
             'Legal conclusion: `not_determined`.', '',
             'Analysis digest: `' + analysis_sha + '`',
             'Controller release receipt: `' + release_sha + '`', '']
    if handoff is None:
        lines.extend(['## Review needed', '',
                      'No explicit, digest-bound C5d review and C5e/C5f reviewer contexts were supplied.',
                      'No hypotheses have been promoted for strategy, and no ranking is available.', ''])
    else:
        lines.extend(['## Reviewed handoff', '',
                      'Status: `' + handoff['handoff_status'] + '`',
                      'Eligible attack angles: ' + str(len(handoff['eligible_attack_angles'])),
                      'Eligible routes: ' + str(len(handoff['eligible_routes'])), '',
                      '## Candidate options', ''])
        for c in c5e['candidates']:
            lines.append('- `' + neat(c['suggestion_id']) + '` (' + neat(c['candidate_kind']) +
                         '): ' + neat(c['action_summary']) + ' — review only')
        for group, heading in [('non_applicable', 'Non-applicable'), ('blocked', 'Blocked'),
                               ('analysis_returns', 'Return to analysis')]:
            if c5e[group]:
                lines.extend(['', '## ' + heading])
                for c in c5e[group]:
                    lines.append('- `' + neat(c['suggestion_id']) + '`')
        lines.extend(['', '## C5f ranking', '',
                      'Ranking status: `' + c5f['ranking_status'] + '`',
                      'Recommendation status: `' + c5f['recommendation_status'] + '`',
                      'Preferred candidate, if any: `' + str(c5f.get('preferred_suggestion_id')) + '`',
                      'This preference is only for further review and never permission to execute.', ''])
        for t in c5f.get('priority_tiers', []):
            lines.append('- Tier ' + str(t['tier']) + ': ' + ', '.join(t['suggestion_ids']))
        lines.extend(['', '## Five ordinary baseline alternatives', ''])
        for b in c5f['baseline_comparison']:
            label = b['baseline_kind'].replace('_', ' ')
            lines.append('- ' + neat(label) + ': `' + neat(b['review_status']) + '`; ' + neat(b['rationale']) +
                         ('; option `' + neat(b['suggestion_id']) + '`' if b['suggestion_id'] else ''))
        for key, heading in [('deferred_options', 'Deferred options (unresolved review)'),
                             ('excluded_options', 'Excluded options (adverse review)')]:
            if c5f[key]:
                lines.extend(['', '## ' + heading, ''])
                for item in c5f[key]:
                    lines.append('- `' + neat(item['suggestion_id']) + '`: ' +
                                 neat(', '.join(item['reasons'])))
        if c5f['top_tier_tradeoffs']:
            lines.extend(['', '## Top-tier tradeoffs', ''])
            for item in c5f['top_tier_tradeoffs']:
                lines.append('- `' + neat(item['first_id']) + '` versus `' + neat(item['second_id']) +
                             '`; first: ' + neat(', '.join(item['first_advantages']) or 'none') +
                             '; second: ' + neat(', '.join(item['second_advantages']) or 'none') +
                             '; not comparable: ' + neat(', '.join(item['noncomparable_factors']) or 'none'))
        if c5f['conflicts']:
            lines.extend(['', '## Incompatible options', ''])
            for item in c5f['conflicts']:
                lines.append('- `' + neat(item['first_id']) + '` and `' + neat(item['second_id']) +
                             '` are marked conflicting by the review context.')
        if c5f['conditional_sequences']:
            lines.extend(['', '## Conditional sequences', ''])
            for item in c5f['conditional_sequences']:
                lines.append('- `' + neat(item['sequence_id']) + '` (' + neat(item['sequence_status']) +
                             '): ' + neat(' -> '.join(item['steps'])) +
                             '; reassess after ' + neat(item['reassessment_trigger']) +
                             ('; blockers ' + neat(', '.join(item['blockers'])) if item['blockers'] else ''))
        if c5f['analysis_returns']:
            lines.extend(['', '## Questions requiring new analysis', ''])
            for item in c5f['analysis_returns']:
                lines.append('- `' + neat(item['suggestion_id']) + '`: ' + neat(item['question']))
        lines.extend(['', '## Ranking and reviewer limitations', ''])
        for item in c5f['limitations']:
            lines.append('- ' + neat(item))
        lines.append('Every option, even when ranked first, requires fresh merits and risk review before any action.')
    return ('\n'.join(lines).rstrip() + '\n').encode('utf-8')


def release(args):
    workdir = Path(args.workdir).resolve()
    # An interrupted attempt cannot be retried in the old workspace, even if
    # the controller no longer has a prepared stage after a partial transition.
    fail_if(any((workdir / p).exists() for p in ('release-attempt.json', 'analysis.json', 'c6-release-receipt.json')),
            'release_already_attempted')
    manifest, inputs, stages, state, country_pairs = verify_prepared(workdir)
    review_paths = [args.review, args.c5e_context, args.c5f_context]
    fail_if(any(review_paths) and not all(review_paths), 'all_three_explicit_review_artifacts_required')
    handoff = c5e = c5f = None
    if all(review_paths):
        rev = load_json(Path(args.review)); ctx = load_json(Path(args.c5e_context)); fctx = load_json(Path(args.c5f_context))
        for role, value in [('c5d_review',rev),('c5e_context',ctx),('c5f_context',fctx)]:
            trust_gate.require_approved(role, value)
        c11_by_id={x['attack_angle_id']:x for x in stages['c11']['assessments'] if x['attack_angle_id']}
        c12_by_id={x['attack_angle_id']:x for x in stages['c12']['assessments'] if x['attack_angle_id']}
        for item in rev['attack_angle_reviews']:
            if item['disposition'] != 'reject':
                c12_enrolled=bool(stages['c12']['bindings']['fact_ledger_sha256'] or stages['c12']['bindings']['country_rule_extensions'])
                screening=(c12_by_id.get(item['attack_angle_id']) if c12_enrolled else None) or c11_by_id.get(item['attack_angle_id'])
                fail_if(not review_screen_passes(screening,stages),
                        'c13_or_c11_blocks_unsupported_suggestion_promotion:'+item['attack_angle_id'])
        handoff = handoff_engine.build(inputs['case'], stages['c5c'], stages['c5d'], rev,
                                      inputs['elements'], country_pairs)
        fail_if(handoff['handoff_status'] == 'blocked', 'review_handoff_blocked')
        c5e = suggestions.build(handoff, ctx)
        c5f = ranking.build(handoff, ctx, c5e, fctx)
        for role, value in [('c5d_review',rev), ('c5e_context',ctx), ('c5f_context',fctx)]:
            trust_gate.require_approved(role, value)
    # Mark a single attempt before output side effects. A crash requires a fresh run; no in-place resume.
    write_json(workdir / 'release-attempt.json',
               {'status':'started_uncommitted', 'manifest_sha256':digest_obj(manifest),
                'prepared_revision': manifest['prepared_revision']})
    # No review data is silently synthesized; all reviewer artifacts are captured verbatim (parsed JSON) after checks.
    for name, source in zip(('c5d-review','c5e-context','c5f-context'), review_paths):
        if source is not None:
            snapshot(workdir, 'review/' + name + '.json', source)
    if handoff is not None:
        for name, obj in [('handoff', handoff), ('c5e-candidates', c5e), ('c5f-ranked', c5f)]:
            write_json(workdir / ('review/' + name + '.json'), obj)
    indexed_issues = issue_index.build(stages, state)
    write_json(workdir / 'issue-index.json', indexed_issues)
    index_render = issue_index.render(indexed_issues)
    write_bytes_atomic(workdir / 'issue-index.md', index_render)
    write_json(workdir / 'c13-evidence-assessment.json',stages['c13'])
    c13_md=c13.render(stages['c13'])
    write_bytes_atomic(workdir / 'c13-evidence-assessment.md',c13_md)
    write_json(workdir / 'c12-legal-resolution.json', stages['c12'])
    c12_md=c12.render(stages['c12'])
    write_bytes_atomic(workdir / 'c12-legal-resolution.md', c12_md)
    write_json(workdir / 'c11-legal-assessment.json', stages['c11'])
    c11_md = legal_assessment.render(stages['c11'])
    write_bytes_atomic(workdir / 'c11-legal-assessment.md', c11_md)
    analysis = controlled_projection(inputs['case'], stages, state)
    write_json(workdir / 'analysis.json', analysis)
    # The original controller owns proposal, validation, release and deterministic legal-analysis rendering.
    state_path = workdir / 'state.json'
    state = controller_op(controller.cmd_propose_analysis, state_path, inputs['case']['case_id'],
                          input=str(workdir / 'analysis.json'))
    state = controller_op(controller.cmd_validate_analysis, state_path, inputs['case']['case_id'],
                          input=str(workdir / 'analysis.json'), receipt=str(workdir / 'validation-receipt.json'))
    state = controller_op(controller.cmd_release, state_path, inputs['case']['case_id'],
                          input=str(workdir / 'analysis.json'), receipt=str(workdir / 'validation-receipt.json'),
                          output=str(workdir / 'controlled-analysis.md'),
                          release_receipt=str(workdir / 'release-receipt.json'))
    release_rec = load_json(workdir / 'release-receipt.json')
    output = render_strategy(handoff, c5e, c5f, digest_obj(analysis), release_rec['receipt_sha256'])
    write_bytes_atomic(workdir / 'strategy-review-only.md', output)
    receipt = {
        'c6_version': C6_VERSION, 'case_id': state['case_id'],
        'manifest_sha256': digest_obj(manifest),
        'analysis_sha256': digest_obj(analysis),
        'controller_release_receipt_sha256': release_rec['receipt_sha256'],
        'analysis_render_sha256': file_hash(workdir / 'controlled-analysis.md'),
        'issue_index_sha256': digest_obj(indexed_issues),
        'issue_index_render_sha256': sha_bytes(index_render),
        'c13_assessment_sha256':digest_obj(stages['c13']),
        'c13_assessment_render_sha256':sha_bytes(c13_md),
        'c12_resolution_sha256':digest_obj(stages['c12']),
        'c12_resolution_render_sha256':sha_bytes(c12_md),
        'c11_assessment_sha256': digest_obj(stages['c11']),
        'c11_assessment_render_sha256': sha_bytes(c11_md),
        'trusted_policy_sha256': trust_gate.TRUST_POLICY_SHA256,
        'strategy_render_sha256': sha_bytes(output),
        'strategy_state': 'reviewed_only' if handoff is not None else 'review_needed',
        'review_artifacts': {name: index_file(workdir, 'review/'+name+'.json')
                             for name in ('c5d-review','c5e-context','c5f-context', 'handoff','c5e-candidates','c5f-ranked')
                             if (workdir / 'review' / (name+'.json')).is_file()},
        'legal_conclusion_status': 'not_determined', 'action_executed': False,
        'review_identity_assurance': 'unverified_local' if handoff else 'not_reviewed',
    }
    receipt['receipt_sha256'] = digest_obj(receipt)
    write_json(workdir / 'c6-release-receipt.json', receipt)
    verify_release(workdir)
    return {'status': 'released_limited_synthetic', 'case_id': state['case_id'],
            'controller_revision': state['revision'], 'strategy_state': receipt['strategy_state'],
            'c6_release_sha256': receipt['receipt_sha256'], 'action_executed': False}


def verify_release(workdir):
    manifest, inputs, stages, state, country_pairs = verify_prepared(workdir, allow_released=True)
    receipt = load_json(workdir / 'c6-release-receipt.json')
    claimed = receipt['receipt_sha256']
    fail_if(digest_obj({k:v for k,v in receipt.items() if k != 'receipt_sha256'}) != claimed,
            'c6_receipt_digest_invalid')
    fail_if(receipt['manifest_sha256'] != digest_obj(manifest) or receipt['case_id'] != state['case_id'],
            'c6_manifest_or_case_rebound')
    fail_if(load_json(workdir / 'release-attempt.json') !=
            {'status':'started_uncommitted', 'manifest_sha256':digest_obj(manifest),
             'prepared_revision':manifest['prepared_revision']}, 'c7_release_attempt_record_invalid')
    expected_index = issue_index.build(stages, load_json(workdir / 'prepared-controller-state.json'))
    fail_if(load_json(workdir / 'issue-index.json', allow_internal_issue_code=True) != expected_index or
            digest_obj(expected_index) != receipt['issue_index_sha256'], 'c7_issue_index_mismatch')
    expected_issue_md = issue_index.render(expected_index)
    fail_if((workdir / 'issue-index.md').read_bytes() != expected_issue_md or
            sha_bytes(expected_issue_md) != receipt['issue_index_render_sha256'], 'c7_issue_index_render_mismatch')
    fail_if(load_json(workdir / 'c13-evidence-assessment.json') != stages['c13'] or
            receipt['c13_assessment_sha256']!=digest_obj(stages['c13']), 'c13_assessment_tampered')
    c13_md=c13.render(stages['c13'])
    fail_if((workdir/'c13-evidence-assessment.md').read_bytes()!=c13_md or
            receipt['c13_assessment_render_sha256']!=sha_bytes(c13_md), 'c13_assessment_render_tampered')
    fail_if(load_json(workdir / 'c12-legal-resolution.json') != stages['c12'] or
            receipt['c12_resolution_sha256']!=digest_obj(stages['c12']), 'c12_resolution_tampered')
    c12_md=c12.render(stages['c12'])
    fail_if((workdir/'c12-legal-resolution.md').read_bytes()!=c12_md or
            receipt['c12_resolution_render_sha256']!=sha_bytes(c12_md), 'c12_resolution_render_tampered')
    fail_if(load_json(workdir / 'c11-legal-assessment.json') != stages['c11'] or
            receipt['c11_assessment_sha256'] != digest_obj(stages['c11']),
            'c11_assessment_tampered')
    c11_markdown = legal_assessment.render(stages['c11'])
    fail_if((workdir/'c11-legal-assessment.md').read_bytes()!=c11_markdown or
            receipt['c11_assessment_render_sha256'] != sha_bytes(c11_markdown),
            'c11_assessment_render_tampered')
    fail_if(receipt['trusted_policy_sha256'] != trust_gate.TRUST_POLICY_SHA256, 'c7_trust_policy_rebound')
    analysis = load_json(workdir / 'analysis.json')
    expected_analysis = controlled_projection(inputs['case'], stages,
                                            load_json(workdir / 'prepared-controller-state.json'))
    fail_if(analysis != expected_analysis or digest_obj(analysis) != receipt['analysis_sha256'],
            'controlled_projection_changed_or_tampered')
    validate_obj('controlled-analysis', analysis)
    fail_if(state['analysis']['sha256'] != digest_obj(analysis) or
            state['validation_receipt']['analysis_sha256'] != digest_obj(analysis),
            'controller_analysis_binding_mismatch')
    validation = load_json(workdir / 'validation-receipt.json')
    release_rec = load_json(workdir / 'release-receipt.json')
    fail_if(validation != state['validation_receipt'] or release_rec != state['release_receipt'],
            'controller_receipts_mismatch')
    fail_if(digest_obj({k:v for k,v in validation.items() if k!='receipt_sha256'}) != validation['receipt_sha256'] or
            digest_obj({k:v for k,v in release_rec.items() if k!='receipt_sha256'}) != release_rec['receipt_sha256'],
            'controller_receipt_corrupt')
    expected_md = controller.render_markdown(analysis, state['requirements'],
                                            state.get('missing_optional_modules', []),
                                            state.get('freshness_blocked_required_modules', [])).encode('utf-8')
    fail_if((workdir / 'controlled-analysis.md').read_bytes() != expected_md or
            sha_bytes(expected_md) != release_rec['rendered_sha256'] or
            file_hash(workdir / 'controlled-analysis.md') != receipt['analysis_render_sha256'],
            'controlled_analysis_render_mismatch')
    fail_if(release_rec['receipt_sha256'] != receipt['controller_release_receipt_sha256'] or
            release_rec['analysis_sha256'] != digest_obj(analysis), 'controller_release_digest_mismatch')
    handoff = c5e = c5f = None
    if receipt['strategy_state'] == 'reviewed_only':
        indexes = receipt['review_artifacts']
        fail_if(set(indexes) != {'c5d-review','c5e-context','c5f-context','handoff','c5e-candidates','c5f-ranked'},
                'incomplete_review_artifact_set')
        data = {key: load_indexed(workdir, item) for key,item in indexes.items()}
        for role, value in [('c5d_review',data['c5d-review']),('c5e_context',data['c5e-context']),
                            ('c5f_context',data['c5f-context'])]:
            trust_gate.require_approved(role, value)
        c11_by_id={x['attack_angle_id']:x for x in stages['c11']['assessments'] if x['attack_angle_id']}
        c12_by_id={x['attack_angle_id']:x for x in stages['c12']['assessments'] if x['attack_angle_id']}
        for item in data['c5d-review']['attack_angle_reviews']:
            if item['disposition'] != 'reject':
                c12_enrolled=bool(stages['c12']['bindings']['fact_ledger_sha256'] or stages['c12']['bindings']['country_rule_extensions'])
                screening=(c12_by_id.get(item['attack_angle_id']) if c12_enrolled else None) or c11_by_id.get(item['attack_angle_id'])
                fail_if(not review_screen_passes(screening,stages),
                        'c13_or_c11_blocks_unsupported_suggestion_promotion:'+item['attack_angle_id'])
        handoff = handoff_engine.build(inputs['case'], stages['c5c'], stages['c5d'],
                                      data['c5d-review'], inputs['elements'], country_pairs)
        c5e = suggestions.build(handoff, data['c5e-context'])
        c5f = ranking.build(handoff, data['c5e-context'], c5e, data['c5f-context'])
        fail_if(any(data[n] != obj for n,obj in (('handoff',handoff),('c5e-candidates',c5e),('c5f-ranked',c5f))),
                'review_replay_mismatch')
    else:
        fail_if(receipt['strategy_state'] != 'review_needed' or receipt['review_artifacts'],
                'review_needed_has_review_artifacts')
    expected_strategy = render_strategy(handoff,c5e,c5f,digest_obj(analysis),release_rec['receipt_sha256'])
    fail_if((workdir / 'strategy-review-only.md').read_bytes() != expected_strategy or
            sha_bytes(expected_strategy) != receipt['strategy_render_sha256'], 'strategy_render_mismatch')
    fail_if(receipt['legal_conclusion_status'] != 'not_determined' or
            receipt['action_executed'] is not False or analysis['recommendations'],
            'strategy_legal_boundary_violation')
    return {'status':'verified_c6_synthetic_release', 'case_id': state['case_id'],
            'strategy_state': receipt['strategy_state'], 'analysis_sha256':digest_obj(analysis),
            'c6_release_sha256': receipt['receipt_sha256']}


def main():
    ap = argparse.ArgumentParser(description='C6 synthetic-only controlled legal-analysis integration')
    subs = ap.add_subparsers(dest='operation', required=True)
    pre = subs.add_parser('prepare')
    pre.add_argument('--workdir', required=True)
    pre.add_argument('--case', required=True)
    pre.add_argument('--run-id', required=True)
    pre.add_argument('--time-of-check', required=True)
    pre.add_argument('--source-pack', default=str(SOURCE_PACK))
    pre.add_argument('--elements'); pre.add_argument('--actors'); pre.add_argument('--c5b-context'); pre.add_argument('--c5c-context')
    pre.add_argument('--module-pair', nargs=2, action='append', metavar=('MANIFEST','EXPORT'), required=True)
    pre.add_argument('--c12-rule-extension',action='append',default=[],metavar='COUNTRY_RULE_EXTENSION')
    pre.add_argument('--c12-fact-ledger',metavar='SYNTHETIC_EVIDENCE_LEDGER')
    pre.add_argument('--c13-evidence-set',metavar='APPROVED_SYNTHETIC_DOCUMENT_SET')
    rel = subs.add_parser('release')
    rel.add_argument('--workdir', required=True)
    rel.add_argument('--review'); rel.add_argument('--c5e-context'); rel.add_argument('--c5f-context')
    ver = subs.add_parser('verify'); ver.add_argument('--workdir', required=True)
    args = ap.parse_args()
    try:
        if args.operation == 'prepare':
            result = prepare(args)
        elif args.operation == 'release':
            result = release(args)
        else:
            result = verify_release(Path(args.workdir).resolve())
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 0
    except (C6Error, ContractError, controller.ControllerError, conformance.ConformanceError,
            topology.TopologyError, regimes.RegimeError, hierarchy.C5bError, evidence.C5cError,
            attacks.C5dError, legal_assessment.AssessmentError, c12.C12Error, c13.C13Error, handoff_engine.HandoffError, suggestions.SuggestionError,
            ranking.RankingError, element_model.ElementModelError, trust_gate.C7TrustError,
            OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'invalid', 'error': str(exc)}, sort_keys=True), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
