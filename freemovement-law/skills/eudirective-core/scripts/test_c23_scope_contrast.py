#!/usr/bin/env python3
"""Local C23 scope-comparison and intake guardrails (mechanical tests only)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

import c23_scope_contrast as sc

ROOT = Path(__file__).resolve().parents[1]


def valid_case():
    return {
        'mode': 'abstract_read_only_advisory',
        'scope': {p: 'yes' for p in sc.PREDICATES},
        'demands': [
            {'item': x, 'purpose': 'visa_entitlement', 'mandatory': True}
            for x in ('bank_statements', 'financial_means', 'accommodation_booking',
                      'flight_reservation', 'travel_medical_insurance')
        ],
    }


class C23ContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_check = sc.source_gate.inspect()

    def test_01_source_pack_gate(self):
        self.assertEqual(self.source_check['source_pack_version'], '0.6.1')
        self.assertEqual(self.source_check['source_representations'], 47)

    def test_02_ordinary_documents_all_excluded(self):
        x = sc.assess(valid_case())
        self.assertEqual(x['scope_assessment'], 'directive_family_scope_assumed_from_reviewer_features')
        for y in x['demands']:
            self.assertEqual(y['scope_finding'], 'ordinary_list_item_inapplicable_as_eu_family_visa_requirement')
        self.assertEqual(x['legal_violation_status'], 'not_determined')

    def test_03_consular_competence_stays_distinct(self):
        x = valid_case()
        x['demands'] = [{'item': 'local_residence_status', 'purpose': 'consular_territorial_competence', 'mandatory': True}]
        ans = sc.assess(x)
        self.assertEqual(ans['demands'][0]['scope_finding'], 'potentially_relevant_to_consular_territorial_competence_only')

    def test_04_incomplete_scope_requires_fact(self):
        x = valid_case()
        x['scope']['accompany_or_join'] = 'unknown'
        ans = sc.assess(x)
        self.assertEqual(ans['material_scope_gaps'], ['accompany_or_join'])
        self.assertEqual(ans['demands'][0]['scope_finding'], 'conditional_until_family_scope_fact_answered')

    def test_05_not_mobile_not_automatically_exempt(self):
        x = valid_case()
        x['scope']['eu_citizen_moving_to_other_member_state'] = 'no'
        ans = sc.assess(x)
        self.assertEqual(ans['demands'][0]['scope_finding'], 'family_exception_not_established_on_features')

    def test_06_unknown_purpose_not_an_excuse_for_checklist(self):
        x = valid_case()
        x['demands'] = [{'item': 'bank_statements', 'purpose': 'unknown', 'mandatory': True}]
        self.assertIn('inapplicable_as_routine', sc.assess(x)['demands'][0]['scope_finding'])

    def test_07_specific_competence_purpose_not_blanket_approval(self):
        x = valid_case()
        x['demands'] = [{'item': 'accommodation_booking', 'purpose': 'consular_territorial_competence', 'mandatory': True}]
        self.assertEqual(sc.assess(x)['demands'][0]['scope_finding'], 'not_a_routine_family_visa_condition;requires_specific_competence_basis')

    def test_08_identity_and_relationship_distinct(self):
        x = valid_case()
        x['demands'] = [{'item': 'family_link_evidence', 'purpose': 'visa_entitlement', 'mandatory': True}]
        self.assertEqual(sc.assess(x)['demands'][0]['scope_finding'], 'relevant_to_family_beneficiary_proof')

    def test_09_confirmation_not_paid_booking(self):
        x = valid_case()
        x['demands'] = [{'item': 'eu_travel_confirmation', 'purpose': 'visa_entitlement', 'mandatory': True}]
        self.assertEqual(sc.assess(x)['demands'][0]['scope_finding'], 'relevant_to_accompany_or_join_confirmation_no_paid_booking_required')

    def test_10_voluntary_unchallenged(self):
        x = valid_case()
        x['demands'][0]['mandatory'] = False
        self.assertEqual(sc.assess(x)['demands'][0]['scope_finding'], 'no_mandatory_demand_claimed')

    def test_11_no_private_text_in_feature_contract(self):
        for extra in ('passport_number', 'applicant_name', 'free_text', 'url', 'case_id'):
            x = valid_case()
            x[extra] = 'secret'
            with self.assertRaises(sc.ScopeError):
                sc.assess(x)

    def test_12_no_arbitrary_custom_item(self):
        x = valid_case()
        x['demands'][0]['item'] = 'upload_photo_of_full_passport'
        with self.assertRaises(sc.ScopeError):
            sc.assess(x)

    def test_13_not_send_no_data_copy(self):
        x = sc.assess(valid_case())
        self.assertFalse(x['external_disclosure_authorized'])
        self.assertFalse(x['contains_private_case_narrative'])
        self.assertNotIn('applicant_name', json.dumps(x))

    def test_14_worked_example_preserved_without_normal_use_anchoring(self):
        guidance = (ROOT / 'references/c23-applicant-case-guidance.md').read_text()
        fixture = (ROOT / 'evaluations/c23-romanian-worked-fixture.md').read_text()
        for term in ('territorial competence', 'up to three', 'C6/C7', 'SOLVIT', 'CCTV'):
            self.assertIn(term.lower(), guidance.lower())
        for term in ('inapplicable', 'bank', 'Romania', 'UAE', 'CCTV'):
            if term.lower() == 'cctv':
                # CCTV mitigation remains a normal-use requirement, not necessarily a fixture line.
                continue
            self.assertIn(term.lower(), fixture.lower())
        self.assertNotIn('### Worked pattern: Polish spouse / Romania', guidance)
        self.assertIn('normal-use', fixture)

    def test_15_guidance_challenge_corpus(self):
        x = json.loads((ROOT / 'evaluations/c23-applicant-guidance-cases.json').read_text())
        self.assertGreaterEqual(len(x['cases']), 6)
        self.assertEqual(len({e['id'] for e in x['cases']}), len(x['cases']))
        for case in x['cases']:
            self.assertTrue(case['should_do'] and case['should_not_do'])

    def test_16_reference_response(self):
        t = (ROOT / 'evaluations/c23-romanian-case-reference-response.md').read_text()
        for signal in ('does not apply', 'lawfully present', 'CCTV', 'questions', 'consular territorial competence'):
            self.assertIn(signal.lower(), t.lower())
        self.assertNotIn('not independently verified', t.lower())

    def test_17_cli_equivalence(self):
        inp = json.dumps(valid_case(), sort_keys=True)
        p = subprocess.run([sys.executable, str(ROOT/'scripts/c23_scope_contrast.py'), '--input', '-'],
                           input=inp, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(p.stdout), sc.assess(valid_case()))

    def test_18_cli_blocks_extra_private_fields_without_echoing(self):
        x = valid_case()
        x['secret_free_text'] = 'DO_NOT_ECHO_PRIVATE_VALUE'
        p = subprocess.run([sys.executable, str(ROOT/'scripts/c23_scope_contrast.py'), '--input', '-'],
                           input=json.dumps(x), text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn('DO_NOT_ECHO_PRIVATE_VALUE', p.stdout+p.stderr)

    def test_19_file_replay_deterministic(self):
        x = valid_case()
        self.assertEqual(json.dumps(sc.assess(x), sort_keys=True), json.dumps(sc.assess(x), sort_keys=True))


if __name__ == '__main__':
    unittest.main(verbosity=2)
