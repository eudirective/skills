#!/usr/bin/env python3
"""C21 adversarial synthetic-only privacy tests. NOT independent anonymity testing."""
from __future__ import annotations
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import c21_privacy as c21
from contract_validate import digest_obj

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT/'references/fixtures/c21/fictional-private-looking.json'
PLAN = ROOT/'references/fixtures/c21/fictional-c17-plan-L1.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


class C21PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.data = load(FIX)
        self.policy = c21.policy()

    def assert_blocked(self, fn, expected):
        with self.assertRaises(c21.PrivacyError) as e:
            fn()
        self.assertEqual(str(e.exception), expected)
        self.assertNotIn('Ada Sample', str(e.exception))

    def test_policy_is_pinned_and_constrains_profiles(self):
        self.assertEqual(len(self.policy['profiles']), 4)
        expected={'internal_review_preview','public_story_preview','feedback_aggregate_preview','c17_feedback_preview'}
        self.assertEqual({p['name'] for p in self.policy['profiles']},expected)
        self.assertEqual(c21.policy(), self.policy)
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/'policy.json'
            fake.write_text((c21.POLICY_PATH).read_text()+'\n')
            original=c21.POLICY_PATH
            try:
                c21.POLICY_PATH=fake
                self.assert_blocked(c21.policy,'modified_policy_not_bound_to_engine')
            finally:
                c21.POLICY_PATH=original

    def test_three_profiles_drop_or_transform(self):
        for name in ('internal_review_preview','public_story_preview','feedback_aggregate_preview'):
            with self.subTest(profile=name):
                result=c21.build(self.data,self.policy,name)
                self.assertFalse(result['external_disclosure_authorized'])
                self.assertFalse(result['private_data_enabled'])
                self.assertTrue(result['human_review_required'])
                self.assertNotIn('case_ref',result)
                self.assertEqual(result['minimisation']['input_fields'],9)
                self.assertEqual(result['minimisation']['retained_fields']+result['minimisation']['dropped_fields'],9)
                self.assertEqual(c21.build(self.data,self.policy,name),result)
                self.assertEqual(c21.receipt_for(result,self.policy)['view_sha256'],digest_obj(result))
        self.assertNotIn('narrative',c21.build(self.data,self.policy,'feedback_aggregate_preview')['fields'])
        self.assertEqual(c21.build(self.data,self.policy,'internal_review_preview')['fields']['event_date'],'2026')

    def test_all_declared_identifiers_scrubbed(self):
        result=c21.build(self.data,self.policy,'internal_review_preview')
        text=result['fields']['narrative']
        self.assertIn('[APPLICANT]',text)
        self.assertIn('[PLACE]',text)
        self.assertIn('[DATE]',text)
        for phrase in ('Ada Sample','Pinehaven','ada.sample@example.invalid','TR-VISA-927443','2026-10-07','SYN-C21-ONE'):
            self.assertNotIn(phrase,json.dumps(result,ensure_ascii=False))
            self.assertNotIn(phrase,json.dumps(c21.receipt_for(result,self.policy)))

    def test_potential_extra_identifier_patterns(self):
        val=('Applicant Ava Fiction used ava@example.invalid and https://example.invalid/a?user=ava. '
             'Bank DE89370400440532013000; telephone +90 555 123 4567; '
             'dates 2026-10-07, 07/10/2026 and 7 October 2026; '
             'the IP was 198.51.100.42 and reference number AB-654321. '
             '“This is a deliberately long exact statement that might be searchable online.”')
        v=c21.scrub(val,[('Ava Fiction','APPLICANT')])
        for phrase in ('ava@example.invalid','https://example.invalid','DE89370400440532013000',
                       '+90 555 123 4567','2026-10-07','07/10/2026','7 October 2026','198.51.100.42','AB-654321'):
            self.assertNotIn(phrase,v)
        self.assertIn('[APPLICANT]',v)
        self.assertIn('[REMOVED_QUOTE]',v)
        self.assertIn('[FINANCIAL_ID]',v)

    def test_repetition_longer_first_case_independent(self):
        a=c21.scrub('Anna Sam and Anna met ANNA SAM', [('Anna','OTHER_PERSON'),('Anna Sam','APPLICANT')])
        self.assertEqual(a,'[APPLICANT] and [OTHER_PERSON] met [APPLICANT]')
        b=c21.scrub('Anna Sam and Anna met ANNA SAM', [('Anna','OTHER_PERSON'),('Anna Sam','APPLICANT')])
        self.assertEqual(a,b)
        self.assertNotIn('Anna',a)

    def test_ambiguous_alias_is_blocked(self):
        self.data['redaction_terms'].append({'value':'ADA SAMPLE','role':'OFFICIAL'})
        self.assert_blocked(lambda:c21.build(self.data,self.policy,'public_story_preview'),'ambiguous_redaction_alias')

    def test_raw_classification_cannot_keep_identifying_enum(self):
        self.data['fields'][0]['classification']='direct_identifier'
        self.assert_blocked(lambda:c21.build(self.data,self.policy,'feedback_aggregate_preview'),
                            'unsafe_or_non_whitelisted_enum_issue_category')
        self.data['fields'][0]['classification']='sensitive'
        self.assert_blocked(lambda:c21.build(self.data,self.policy,'feedback_aggregate_preview'),
                            'unsafe_or_non_whitelisted_enum_issue_category')

    def test_enum_is_closed(self):
        self.data['fields'][0]['value']='give_me_everything'
        self.assert_blocked(lambda:c21.build(self.data,self.policy,'feedback_aggregate_preview'),
                            'unsafe_or_non_whitelisted_enum_issue_category')

    def test_build_is_offline_even_when_socket_is_blocked(self):
        from unittest.mock import patch
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            for profile in ('internal_review_preview','public_story_preview','feedback_aggregate_preview'):
                view=c21.build(self.data,self.policy,profile)
                self.assertFalse(view['external_disclosure_authorized'])

    def test_only_real_iso_dates_are_generalised(self):
        for bad in ('2026-02-31','2026-13-01','junk-2026-10','10/07/2026','2026-10'):
            test=copy.deepcopy(self.data)
            test['fields'][2]['value']=bad
            with self.subTest(value=bad):
                self.assert_blocked(lambda:c21.build(test,self.policy,'internal_review_preview'),
                                    'invalid_date_event_date')
        self.data['fields'][2]['classification']='direct_identifier'
        self.assert_blocked(lambda:c21.build(self.data,self.policy,'internal_review_preview'),
                            'invalid_date_classification_event_date')

    def test_no_unknown_fields_or_sensitive_field_names(self):
        self.data['fields'].append({'field_id':'surprise_personal_secret','classification':'sensitive',
                                   'value':'PRIVATE-CANARY-001','risk_tags':['public_searchable_quote']})
        result=c21.build(self.data,self.policy,'feedback_aggregate_preview')
        serialized=json.dumps(result)
        self.assertNotIn('surprise_personal_secret',serialized)
        self.assertNotIn('PRIVATE-CANARY-001',serialized)
        self.assertEqual(result['minimisation']['dropped_fields'],8)
        self.assertIn('cohort_aggregation_not_performed',result['risk_flags'])

    def test_unknown_names_not_declared_safe(self):
        self.data['fields'][-1]['value']='I met Mysterious Faraway Person.'
        self.data['fields'][7]['risk_tags']=[]  # Low-linkability synthetic branch.
        result=c21.build(self.data,self.policy,'public_story_preview')
        self.assertIn('Mysterious Faraway Person',result['fields']['narrative'])
        self.assertIn('free_text_can_contain_undetected_identifiers',result['risk_flags'])
        self.assertFalse(result['external_disclosure_authorized'])

    def test_dropped_high_linkability_field_suppresses_public_narrative(self):
        # Pinehaven has a high-linkability tag even though the field is dropped.
        # The retained narrative may paraphrase that place or its rarity.
        preview=c21.build(self.data,self.policy,'public_story_preview')
        self.assertEqual(set(preview['fields']), {'issue_category'})
        self.assertIn('narrative_suppressed_due_to_cross_field_linkability',preview['risk_flags'])
        self.assertFalse(preview['external_disclosure_authorized'])
        review=c21.build(self.data,self.policy,'internal_review_preview')
        self.assertIn('narrative',review['fields'])

    def test_all_eight_enrolled_c17_plan_fixtures_replay(self):
        registry=c21.enrolled_registry()['c17_plans']
        for i in range(1,9):
            with self.subTest(case=i):
                name='L'+str(i)
                plan=load(ROOT/f'references/fixtures/c21/fictional-c17-plan-{name}.json')
                self.assertEqual(plan['case_id'],name)
                self.assertIn(digest_obj(plan),registry[name])
                typed=c21.from_c17_plan(plan)
                output=c21.build(typed,self.policy,'c17_feedback_preview')
                self.assertFalse(output['external_disclosure_authorized'])
                self.assertNotIn(name,json.dumps(output))

    def test_rare_searchable_story_is_blocked(self):
        self.data['fields'][-1]['risk_tags']=['unique_topology']
        self.assert_blocked(lambda:c21.build(self.data,self.policy,'public_story_preview'),
                            'high_linkability_story_requires_redesign')
        review=c21.build(self.data,self.policy,'internal_review_preview')
        self.assertIn('case_context_linkability_requires_review',review['risk_flags'])

    def test_wrong_text_classification_is_blocked(self):
        self.data['fields'][-1]['classification']='direct_identifier'
        self.assert_blocked(lambda:c21.build(self.data,self.policy,'public_story_preview'),
                            'unsafe_text_classification_narrative')

    def test_real_or_public_person_input_rejected(self):
        for label in ('private','public'):
            with tempfile.TemporaryDirectory() as tmp:
                obj=copy.deepcopy(self.data);obj['data_class']=label
                p=Path(tmp)/'not-private-data.json';p.write_text(json.dumps(obj))
                self.assert_blocked(lambda:c21.vetted_input(p),'real_or_public_person_data_not_authorized')

    def test_declared_synthetic_but_unenrolled_input_is_denied_at_cli_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            td=Path(tmp);x=copy.deepcopy(self.data)
            x['fields'][0]['value']='visa_delay'  # still a legal enum, but not enrolled.
            p=td/'uninventoried.json';p.write_text(json.dumps(x))
            self.assert_blocked(lambda:c21.vetted_input(p),'unapproved_synthetic_fixture')
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/c21_privacy.py'),'preview',
                '--input',str(p),'--profile','public_story_preview','--output-dir',str(td/'new')],
                capture_output=True,text=True)
            self.assertEqual(proc.returncode,2)
            self.assertIn('unapproved_synthetic_fixture',proc.stderr)
            self.assertFalse((td/'new').exists())

    def test_unenrolled_but_structurally_safe_c17_plan_is_blocked(self):
        p=load(PLAN)
        p['parallelism_warnings'][0] += ' (fictional edited edition)'
        self.assert_blocked(lambda:c21.from_c17_plan(p),'unenrolled_c17_plan')

    def test_fixture_registry_hash_tamper_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/'registry.json'
            fake.write_text(c21.REGISTRY_PATH.read_text()+'\n')
            original=c21.REGISTRY_PATH
            try:
                c21.REGISTRY_PATH=fake
                self.assert_blocked(c21.enrolled_registry,'modified_fixture_registry_not_bound_to_engine')
            finally:
                c21.REGISTRY_PATH=original

    def test_duplicate_facts_and_unknown_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            x=copy.deepcopy(self.data)
            x['fields'].append(copy.deepcopy(x['fields'][0]))
            p=Path(tmp)/'duplicate.json';p.write_text(json.dumps(x))
            self.assert_blocked(lambda:c21.vetted_input(p),'duplicate_field_id')
            x=copy.deepcopy(self.data);x['fields'][0]['unexpected_value']='unknown'
            p.write_text(json.dumps(x))
            self.assert_blocked(lambda:c21.vetted_input(p),'invalid_or_unsafe_fixture')
            p.write_text('{"case_ref":"SYN", "case_ref":"OTHER"}')
            self.assert_blocked(lambda:c21.vetted_input(p),'invalid_or_unsafe_fixture')
            x=copy.deepcopy(self.data);x['shell']='rm -rf /'
            p.write_text(json.dumps(x))
            self.assert_blocked(lambda:c21.vetted_input(p),'invalid_or_unsafe_fixture')

    def test_deterministic_outputs_no_overwrites_no_case_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            td=Path(tmp);view=c21.build(self.data,self.policy,'public_story_preview')
            receipt=c21.receipt_for(view,self.policy)
            c21.write_preview(td/'one',view,receipt)
            c21.write_preview(td/'two',view,receipt)
            for name in ('minimised-view.json','privacy-receipt.json'):
                self.assertEqual((td/'one'/name).read_bytes(),(td/'two'/name).read_bytes())
            self.assertEqual((td/'one').stat().st_mode & 0o777,0o700)
            self.assertEqual((td/'one'/'minimised-view.json').stat().st_mode & 0o777,0o600)
            self.assert_blocked(lambda:c21.write_preview(td/'one',view,receipt),'output_directory_must_be_new')
            serial=(td/'one'/'minimised-view.json').read_text()+(td/'one'/'privacy-receipt.json').read_text()
            self.assertNotIn('SYN-C21-ONE',serial)
            self.assertNotIn('Ada Sample',serial)
            self.assertNotIn('source_sha256',serial)

    def test_directory_symlink_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            td=Path(tmp)
            (td/'real').mkdir()
            (td/'link').symlink_to(td/'real',target_is_directory=True)
            x=c21.build(self.data,self.policy,'public_story_preview')
            self.assert_blocked(lambda:c21.write_preview(td/'link',x,c21.receipt_for(x,self.policy)),
                                'output_directory_must_be_new')

    def test_c17_plan_adapter_is_purpose_bounded(self):
        p=load(PLAN)
        typed=c21.from_c17_plan(p)
        self.assertEqual(typed['data_class'],'synthetic')
        self.assertEqual({x['field_id'] for x in typed['fields']},{'plan_kind','route_presence'})
        result=c21.build(typed,self.policy,'c17_feedback_preview')
        text=json.dumps(result,ensure_ascii=False)
        self.assertNotIn('L1',text)
        self.assertNotIn('input_digests',text)
        self.assertNotIn('correspondence_drafts',text)
        self.assertNotIn('source_refs',text)
        self.assertFalse(result['external_disclosure_authorized'])
        self.assertIn('cohort_aggregation_not_performed',result['risk_flags'])

    def test_c17_send_or_merits_promotion_rejected(self):
        p=load(PLAN)
        for case in ('send_authorized','verified_legal_merits'):
            x=copy.deepcopy(p);x[case]=True
            self.assert_blocked(lambda:c21.from_c17_plan(x),'invalid_c17_plan')
        x=copy.deepcopy(p);x['correspondence_drafts'][0]['send_authorized']=True
        self.assert_blocked(lambda:c21.from_c17_plan(x),'invalid_c17_plan')
        x=copy.deepcopy(p);x['decision_gate']='authorized_to_send'
        self.assert_blocked(lambda:c21.from_c17_plan(x),'invalid_c17_plan')

    def test_c17_unsupported_case_rejected(self):
        p=load(PLAN);p['case_id']='L9'
        self.assert_blocked(lambda:c21.from_c17_plan(p),'invalid_c17_plan')

    def test_cli_replay_and_tamper_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            td=Path(tmp)
            def cmd(*args):
                return subprocess.run([sys.executable,str(ROOT/'scripts/c21_privacy.py'),*args],
                                      capture_output=True,text=True,check=False)
            out=td/'render'
            args=('--input',str(FIX),'--profile','public_story_preview','--output-dir',str(out))
            p=cmd('preview',*args);self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('Ada Sample',p.stdout+p.stderr)
            p=cmd('verify',*args);self.assertEqual(p.returncode,0,p.stderr)
            p=cmd('preview',*args);self.assertEqual(p.returncode,2)
            self.assertIn('output_directory_must_be_new',p.stderr)
            view=out/'minimised-view.json';d=load(view);d['fields']['narrative']='tampered';view.write_text(json.dumps(d))
            p=cmd('verify',*args);self.assertEqual(p.returncode,2)
            self.assertIn('replay_or_digest_mismatch',p.stderr)

    def test_cli_c17_adapter_and_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            td=Path(tmp);out=td/'plan'
            def cmd(*args):
                return subprocess.run([sys.executable,str(ROOT/'scripts/c21_privacy.py'),*args],
                                      capture_output=True,text=True,check=False)
            p=cmd('c17-preview','--plan',str(PLAN),'--output-dir',str(out))
            self.assertEqual(p.returncode,0,p.stderr)
            p=cmd('verify','--plan',str(PLAN),'--profile','c17_feedback_preview','--output-dir',str(out))
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('L1', (out/'minimised-view.json').read_text())

    def test_c17_adapter_cannot_be_bypassed_via_generic_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            td=Path(tmp)
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/c21_privacy.py'),'verify',
                '--input',str(FIX),'--profile','c17_feedback_preview',
                '--output-dir',str(td/'missing')],capture_output=True,text=True)
            self.assertEqual(proc.returncode,2)
            self.assertIn('c17_profile_requires_validated_plan',proc.stderr)

    def test_failure_logs_never_reflect_personal_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            td=Path(tmp)
            p=td/'bad.json';inp=copy.deepcopy(self.data)
            inp['fields'][0]['value']='SECRET-APPLICANT-CANARY'
            p.write_text(json.dumps(inp))
            out=td/'out'
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/c21_privacy.py'),'preview',
                '--input',str(p),'--profile','feedback_aggregate_preview','--output-dir',str(out)],
                capture_output=True,text=True)
            self.assertEqual(proc.returncode,2)
            self.assertNotIn('SECRET-APPLICANT-CANARY',proc.stdout+proc.stderr)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
