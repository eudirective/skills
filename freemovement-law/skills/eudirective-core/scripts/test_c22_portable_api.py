#!/usr/bin/env python3
"""C22a portable direct/CLI equivalence and fail-closed synthetic-only checks."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from jsonschema import Draft202012Validator

import c22_portable_api as api

from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts' / 'c22_portable_api.py'


def cli(operation, *, fixture=None, profile=None, output_dir=None):
    args = [sys.executable, str(CLI), operation]
    if fixture is not None:
        args += ['--fixture', fixture]
    if profile is not None:
        args += ['--profile', profile]
    if output_dir is not None:
        args += ['--output-dir', str(output_dir)]
    result = subprocess.run(args, capture_output=True, text=True, timeout=90)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise AssertionError('invalid or missing structured stdout ' + repr(result.stdout))
    return result.returncode, data


class C22aPortabilityTests(unittest.TestCase):
    def safe(self, result):
        self.assertFalse(result['private_data_enabled'])
        self.assertFalse(result['external_disclosure_authorized'])
        self.assertEqual(result['interface_version'], api.INTERFACE_VERSION)

    def test_direct_and_cli_capabilities_identical(self):
        code, data = cli('capabilities')
        self.assertEqual(code, 0)
        self.assertEqual(data, api.invoke('capabilities'))
        self.safe(data)
        self.assertNotIn('mcp', data['execution_mode'])
        self.assertEqual(len(data['enrolled_fixture_tokens']), 9)

    def test_direct_and_cli_source_audit_identical(self):
        code, data = cli('source_audit')
        self.assertEqual(code, 0)
        self.assertEqual(data, api.invoke('source_audit'))
        self.safe(data)
        self.assertEqual(data['representation_count'], 47)
        self.assertEqual(data['identity_only_gaps'], 21)
        self.assertEqual(data['legal_semantic_validation'], 'not_performed')

    def test_three_profiles_roundtrip_and_cli_equivalence(self):
        for profile in sorted(api.ALLOWED_PROFILES):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / 'preview'
                direct = api.invoke('privacy_preview', fixture='c21-demo', profile=profile,
                                    output_dir=output)
                self.assertEqual(direct['status'], 'synthetic_preview_written')
                self.safe(direct)
                code, verified = cli('privacy_verify', fixture='c21-demo',
                                     profile=profile, output_dir=output)
                self.assertEqual(code, 0)
                self.assertEqual(verified, api.invoke('privacy_verify', fixture='c21-demo',
                                                     profile=profile, output_dir=output))
                self.assertEqual(verified['view_sha256'], direct['view_sha256'])
                self.assertEqual(verified['status'], 'verified_synthetic_replay_only')
                self.assertNotIn('SYN-C21-ONE', json.dumps(verified))

    def test_all_eight_c17_plans_enrolled_and_replayable(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(1, 9):
                fixture = f'L{i}'
                with self.subTest(fixture=fixture):
                    output = Path(tmp) / fixture
                    code, preview = cli('c17_feedback_preview', fixture=fixture, output_dir=output)
                    self.assertEqual(code, 0, preview)
                    self.assertEqual(preview['status'], 'synthetic_preview_written')
                    self.safe(preview)
                    replay = api.invoke('c17_feedback_verify', fixture=fixture, output_dir=output)
                    self.assertEqual(replay['status'], 'verified_synthetic_replay_only')
                    self.assertEqual(replay['view_sha256'], preview['view_sha256'])
                    self.assertNotIn(f'"case_id": "{fixture}"', (output/'minimised-view.json').read_text())

    def test_fixed_cohort_roundtrip_and_no_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'cohort'
            preview = api.invoke('cohort_preview', output_dir=output)
            self.assertEqual(preview['status'], 'fixed_synthetic_cohort_preview_written')
            self.assertEqual(cli('cohort_verify', output_dir=output)[1],
                             api.invoke('cohort_verify', output_dir=output))
            self.assertEqual(api.invoke('cohort_verify', output_dir=output)['summary_sha256'],
                             preview['summary_sha256'])
            invalid = api.invoke('cohort_preview', fixture='L1', output_dir=Path(tmp)/'subset')
            self.assertEqual(invalid['reason'], 'subset_or_profile_selection_forbidden')
            self.assertFalse((Path(tmp)/'subset').exists())

    def test_no_overwrites_and_missing_verification_outputs_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'once'
            first = api.invoke('privacy_preview', fixture='c21-demo',
                               profile='public_story_preview', output_dir=output)
            self.assertEqual(first['status'], 'synthetic_preview_written')
            before = (output/'privacy-receipt.json').read_bytes()
            second = api.invoke('privacy_preview', fixture='c21-demo',
                                profile='public_story_preview', output_dir=output)
            self.assertEqual(second['reason'], 'output_directory_already_exists')
            self.assertEqual(before, (output/'privacy-receipt.json').read_bytes())
            missing = api.invoke('privacy_verify', fixture='c21-demo',
                                 profile='public_story_preview', output_dir=Path(tmp)/'missing')
            self.assertEqual(missing['status'], 'blocked')

    def test_reject_non_enrolled_and_unknown_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = {'output_dir': Path(tmp)/'new'}
            blocked = (
                api.invoke('privacy_preview', fixture='../private.json', profile='public_story_preview', **args),
                api.invoke('c17_feedback_preview', fixture='L9', **args),
                api.invoke('privacy_preview', fixture='c21-demo', profile='c17_feedback_preview', **args),
                api.invoke('other_op', fixture='c21-demo', **args),
                api.invoke('cohort_preview', profile='public_story_preview', **args),
                api.invoke('capabilities', fixture='L1'),
            )
            self.assertTrue(all(x['status']=='blocked' for x in blocked))
            self.assertTrue(all(not x['private_data_enabled'] for x in blocked))
            self.assertFalse((Path(tmp)/'new').exists())

    def test_path_safety(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            new=base/'new'
            args = {'fixture':'c21-demo','profile':'public_story_preview'}
            self.assertEqual(api.invoke('privacy_preview', output_dir='relative/path',**args)['reason'],
                             'absolute_output_dir_required')
            self.assertEqual(api.invoke('privacy_preview', output_dir=ROOT/'bad',**args)['reason'],
                             'output_inside_skill_forbidden')
            # Normalized '..' never reaches the engine; no unintended writes.
            self.assertEqual(api.invoke('privacy_preview', output_dir=str(base/'new'/'..'/'new'),**args)['reason'],
                             'unsafe_output_path')
            (base/'alias').symlink_to(base, target_is_directory=True)
            self.assertEqual(api.invoke('privacy_preview', output_dir=base/'alias'/'bad',**args)['reason'],
                             'symlink_output_path_forbidden')
            self.assertFalse(new.exists())

    def test_engine_rejection_is_not_raw_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'view'
            api.invoke('privacy_preview',fixture='c21-demo',profile='public_story_preview',output_dir=output)
            (output/'minimised-view.json').write_text('{}')
            replay=api.invoke('privacy_verify',fixture='c21-demo',profile='public_story_preview',output_dir=output)
            self.assertEqual(replay['status'],'blocked')
            self.assertEqual(replay['reason'],'engine_rejected_or_failed')
            self.assertNotIn(str(output),json.dumps(replay))

    def test_core_execution_has_no_country_or_plugin_dependency(self):
        # No imports of country modules, MCP frameworks or plugin scaffolding.
        script = CLI.read_text(encoding='utf-8')
        self.assertNotIn('import fastmcp',script)
        self.assertNotIn('import mcp',script)
        self.assertNotIn('import eudirective_ms_sweden',script)
        self.assertNotIn('requests.post',script)
        self.assertTrue((compatibility_root()/'core-source-pack-manifest-0.6.1.json').is_file())

    def test_transport_schema_and_adapter_reject_freeform_data(self):
        schema=json.loads((ROOT/'references/contracts/c22-transport-request.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema)
        valid={
            'interface_version':api.INTERFACE_VERSION,
            'operation':'privacy_preview',
            'fixture':'c21-demo',
            'profile':'public_story_preview',
        }
        self.assertTrue(validator.is_valid(valid))
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'adapter'
            direct=api.invoke_request(valid,output_dir=target)
            self.assertEqual(direct['status'],'synthetic_preview_written')
            self.safe(direct)
        for invalid in (
            {**valid,'document_text':'private applicant file'},
            {**valid,'operation':'source_audit'},
            {**valid,'fixture':'L1'},
            {**valid,'profile':'c17_feedback_preview'},
            {'interface_version':'0.1.0','operation':'source_audit','fixture':None},
            {**valid,'interface_version':'0.0.9'},
            {'interface_version':'0.1.0','operation':'cohort_preview','fixture':'L1'},
            {'interface_version':'0.1.0','operation':'capabilities','profile':'public_story_preview'},
        ):
            self.assertFalse(validator.is_valid(invalid))
            blocked=api.invoke_request(invalid)
            self.assertEqual(blocked['status'],'blocked')
            self.assertNotIn('private applicant file',json.dumps(blocked))
            self.safe(blocked)

    def test_facade_file_bytes_match_original_c21_engine(self):
        # Stronger than labels: direct engine and facade write exact same bytes.
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            a=base/'facade'
            b=base/'original'
            self.assertEqual(api.invoke('privacy_preview',fixture='c21-demo',
                  profile='public_story_preview',output_dir=a)['status'],'synthetic_preview_written')
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/c21_privacy.py'),'preview',
                  '--input',str(ROOT/'references/fixtures/c21/fictional-private-looking.json'),
                  '--profile','public_story_preview','--output-dir',str(b)],
                  capture_output=True,text=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stderr)
            for name in ('minimised-view.json','privacy-receipt.json'):
                self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())

    def test_facade_c17_bytes_match_original_engine(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            a=base/'facade'
            b=base/'original'
            self.assertEqual(api.invoke('c17_feedback_preview',fixture='L1',
                                  output_dir=a)['status'],'synthetic_preview_written')
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/c21_privacy.py'),
                                 'c17-preview','--plan',str(ROOT/'references/fixtures/c21/fictional-c17-plan-L1.json'),
                                 '--output-dir',str(b)],capture_output=True,text=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stderr)
            for name in ('minimised-view.json','privacy-receipt.json'):
                self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())

    def test_facade_cohort_bytes_match_original_engine(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            a=base/'facade'
            b=base/'original'
            self.assertEqual(api.invoke('cohort_preview',output_dir=a)['status'],
                             'fixed_synthetic_cohort_preview_written')
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/c21_cohort.py'),'preview',
                                 '--output-dir',str(b)],capture_output=True,text=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stderr)
            for name in ('cohort-summary.json','cohort-receipt.json'):
                self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())

    def test_expected_backend_failure_is_blocked(self):
        with patch.object(api.c18, 'audit', side_effect=ValueError('raw secret example')):
            res=api.invoke('source_audit')
            self.assertEqual(res['status'],'blocked')
            self.assertEqual(res['reason'],'engine_rejected_or_failed')
            self.assertNotIn('raw secret example', json.dumps(res))


if __name__=='__main__':
    unittest.main(verbosity=2)
