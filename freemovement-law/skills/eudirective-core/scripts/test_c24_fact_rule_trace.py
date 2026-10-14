#!/usr/bin/env python3
"""Tests C24 mechanical trace and revision behavior; never claims legal correctness."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

import c24_fact_rule_trace as c24

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / 'evaluations/fixtures/c24'


def fixture(n):
    return json.loads((FX / ('rev%d.json' % n)).read_text(encoding='utf-8'))


class TraceTests(unittest.TestCase):
    def test_01_trace_of_facts_and_source_rules(self):
        r = c24.assess(fixture(1))
        docs = next(i for i in r['issue_traces'] if i['issue'] == 'ordinary_supporting_documents')
        self.assertEqual(docs['status'], 'conditional_eu_family_scope_for_review')
        self.assertEqual(len(docs['rule_scope_findings']), 2)
        self.assertTrue(all('inapplicable' in it['scope_finding'] for it in docs['rule_scope_findings']))
        self.assertTrue(all(f['basis'] for f in docs['fact_trace']))
        self.assertEqual({ref['kind'] for ref in docs['rule_references']},
                         {'binding_eu_law_local_copy', 'commission_interpretive_guidance'})

    def test_02_missing_competence_and_lodgement_asked_without_blocking_documents(self):
        r = c24.assess(fixture(1))
        self.assertEqual({q['fact_key'] for q in r['priority_question_codes']},
                         {'lawful_presence_in_consular_country', 'application_formally_lodged',
                          'written_refusal_served'})
        self.assertNotIn('lawful_presence_in_consular_country',
                         next(i for i in r['issue_traces'] if i['issue'] == 'ordinary_supporting_documents')['missing_material_facts'])

    def test_03_followup_changes_only_relevant_issues(self):
        r = c24.compare(fixture(1), fixture(2))
        self.assertEqual({i['issue'] for i in r['affected_issues']},
                         {'consular_territorial_competence', 'lodgement_and_written_decision'})
        self.assertFalse(r['contradictions_require_human_reconciliation'])
        self.assertTrue(all(i['previous_advice_is_stale'] for i in r['affected_issues']))

    def test_04_reversal_suppresses_old_scope_conclusion(self):
        r = c24.compare(fixture(2), fixture(3))
        affected = {i['issue']: i for i in r['affected_issues']}
        self.assertEqual(affected['ordinary_supporting_documents']['current_status'],
                         'ordinary_directive_pattern_not_established_check_exceptions')
        self.assertTrue(r['contradictions_require_human_reconciliation'])
        self.assertTrue(r['must_identify_displaced_advice_to_user'])
        self.assertTrue(any(q['fact_key'] == 'potential_returnee' for q in
                            r['updated_trace']['priority_question_codes']))

    def test_05_returnee_does_not_get_ordinary_directive_dismissal(self):
        x = fixture(3)
        x['facts']['potential_returnee'] = {'value':'yes', 'origin':'user_account', 'change_reason': None}
        r = c24.assess(x)
        status = next(i['status'] for i in r['issue_traces'] if i['issue'] == 'ordinary_supporting_documents')
        self.assertEqual(status, 'returnee_or_analogous_regime_requires_separate_legal_review')

    def test_06_inferred_predicate_is_labelled_not_verified(self):
        x = fixture(1)
        x['facts']['non_eu_direct_family_member']['origin'] = 'reviewer_inference'
        res = c24.assess(x)
        rows = [f for issue in res['issue_traces'] for f in issue['fact_trace']]
        self.assertTrue(any(f['basis'] == 'reviewer_inference' for f in rows))
        self.assertTrue(all(f['mapping_verification'] == 'not_independently_verified' for f in rows))

    def test_07_absent_predicates_ask_question(self):
        x = fixture(1)
        del x['facts']['accompany_or_join']
        r = c24.assess(x)
        docs = next(i for i in r['issue_traces'] if i['issue']=='ordinary_supporting_documents')
        self.assertEqual(docs['status'], 'material_scope_question_open')
        self.assertTrue(any(q['fact_key'] == 'accompany_or_join' for q in r['priority_question_codes']))

    def test_08_unlawful_reassignment_requires_reconciliation(self):
        x = fixture(3)
        x['facts']['eu_citizen_moving_to_other_member_state']['change_reason']='new_answer_to_question'
        with self.assertRaises(c24.TraceError):
            c24.compare(fixture(2), x)

    def test_09_changed_fact_without_provenance_blocked(self):
        x = fixture(2)
        x['facts']['lawful_presence_in_consular_country']['change_reason'] = None
        with self.assertRaises(c24.TraceError):
            c24.compare(fixture(1), x)

    def test_10_malformed_fact_or_raw_narrative_blocked(self):
        for extra in ('case_id','passport_number','personal_name','narrative','file_path','url'):
            x = fixture(1)
            x[extra] = 'DO_NOT_ECHO_PRIVATE'
            with self.assertRaises(c24.TraceError):
                c24.assess(x)

    def test_11_extraneous_fact_attr_and_value_blocked(self):
        for attr in ('raw_quote','source_email','actual_nationality','identifier'):
            x = fixture(1)
            x['facts']['non_eu_direct_family_member'][attr] = 'DO_NOT_ECHO_PRIVATE'
            with self.assertRaises(c24.TraceError):
                c24.assess(x)
        x = fixture(1)
        x['facts']['accompany_or_join']['value'] = 'private raw narrative'
        with self.assertRaises(c24.TraceError):
            c24.assess(x)

    def test_12_no_national_remedy_authority_fabrication(self):
        x = fixture(1)
        x['requested_issues'].append('national_complaint_route')
        r = c24.assess(x)
        self.assertEqual(next(i['status'] for i in r['issue_traces'] if i['issue']=='national_complaint_route'),
                         'material_fact_missing_review_needed')
        self.assertEqual(r['national_authority_powers'], 'not_verified_by_script')

    def test_13_formal_deadline_source_not_deadline_claim(self):
        x = fixture(1)
        x['requested_issues'] = ['formal_remedy_deadline']
        x['document_demands'] = []
        x['facts']['written_refusal_served'] = {'value':'yes','origin':'user_account', 'change_reason': None}
        x['facts']['service_date_known'] = {'value':'yes','origin':'user_account', 'change_reason': None}
        r = c24.assess(x)
        self.assertIn('national_rule',r['issue_traces'][0]['status'])
        self.assertIn('Article 32',r['issue_traces'][0]['rule_references'][0]['locator'])

    def test_14_strict_purpose_gate(self):
        x = fixture(1)
        x['document_demands'][0]['purpose'] = 'arbitrary_reason'
        with self.assertRaises(c24.TraceError):
            c24.assess(x)

    def test_15_purpose_change_invalidates_issue(self):
        x = fixture(2)
        y = copy.deepcopy(x)
        y['revision']=3
        for rec in y['facts'].values():
            rec['change_reason']=None
        y['document_demands'][0]['purpose']='consular_territorial_competence'
        d = c24.compare(x,y)
        self.assertEqual([i['issue'] for i in d['affected_issues']], ['ordinary_supporting_documents'])
        self.assertIn('requires_specific_competence_basis',d['updated_trace']['issue_traces'][0]['rule_scope_findings'][0]['scope_finding'])

    def test_16_no_nonchange_revision(self):
        x = fixture(2)
        y = copy.deepcopy(x)
        y['revision']=3
        for rec in y['facts'].values():
            rec['change_reason']=None
        with self.assertRaises(c24.TraceError):
            c24.compare(x,y)

    def test_17_cli_preview_matches_api(self):
        payload = json.dumps(fixture(1))
        p = subprocess.run([sys.executable, str(ROOT/'scripts/c24_fact_rule_trace.py'),
                            'preview', '--input', '-'], input=payload,text=True,
                           capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout), c24.assess(fixture(1)))

    def test_18_cli_rejects_private_input_without_echo(self):
        x = fixture(1)
        x['actual_private_email']='PRIVATE_TOKEN_THAT_MUST_NOT_ECHO'
        p = subprocess.run([sys.executable, str(ROOT/'scripts/c24_fact_rule_trace.py'),
                            'preview', '--input', '-'], input=json.dumps(x),text=True,
                           capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn('PRIVATE_TOKEN_THAT_MUST_NOT_ECHO',p.stdout+p.stderr)

    def test_19_cli_compare_matches_api(self):
        p = subprocess.run([sys.executable, str(ROOT/'scripts/c24_fact_rule_trace.py'),
                            'compare','--input',str(FX/'rev2.json'),'--previous',str(FX/'rev1.json')],
                           text=True, capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout), c24.compare(fixture(1), fixture(2)))

    def test_20_no_source_or_privacy_certification(self):
        r = c24.assess(fixture(1))
        self.assertEqual(r['source_integrity'],'C1_v0.6.1_locally_pinned_not_live_checked')
        self.assertFalse(r['external_disclosure_authorized'])
        self.assertFalse(r['private_data_isolation_verified'])
        self.assertFalse(r['persistent_case_storage_authorized'])
        self.assertEqual(r['legal_merits'],'not_determined_by_script')


if __name__ == '__main__':
    unittest.main(verbosity=2)
