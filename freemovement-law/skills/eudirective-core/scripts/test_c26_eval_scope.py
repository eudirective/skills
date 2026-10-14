#!/usr/bin/env python3
"""Static routing-eval checks: not actual skill routing or legal-semantic evidence."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / 'evaluations/eval_suite.json'
CHALLENGES = ROOT / 'evaluations/c25-strategy-challenges.json'


class C26RoutingCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = json.loads(SUITE.read_text(encoding='utf-8'))
        cls.cases = {c['id']: c for c in cls.suite['cases']}
        cls.c25 = json.loads(CHALLENGES.read_text(encoding='utf-8'))['cases']

    def test_target_version(self):
        self.assertEqual(self.suite['skill_version'], '0.39.0')

    def test_unique_suite_case_ids(self):
        self.assertEqual(len(self.cases), len(self.suite['cases']))

    def test_c25_c26_positive_cases_have_free_movement_nexus(self):
        for c in self.suite['cases']:
            if c['id'].startswith(('c25-', 'c26-')) and c['category'] == 'should_trigger':
                with self.subTest(c['id']):
                    self.assertTrue(any(term in c['prompt'].lower() for term in (
                        'eu-family', 'eu citizen', 'eu-citizen', 'eu spouse',
                        'eu-spouse', 'member state', 'eu national')))

    def test_generic_tourism_and_retail_cctv_negative(self):
        for name in ('c26-no-general-tourist-misconduct', 'c26-no-generic-cctv'):
            c = self.cases[name]
            self.assertEqual(c['category'], 'should_not_trigger')
            self.assertIs(False, c['trigger_expectation']['with_skill'])

    def test_c26_positive_cases_have_human_review(self):
        for name in ('c26-event-atomicity', 'c26-actionable-gdpr',
                     'c26-ground-source-fidelity', 'c26-preservation-not-access',
                     'c26-late-ground-revision'):
            c = self.cases[name]
            self.assertTrue(c['checks']['with_skill']['manual_review'])
            self.assertEqual(c['comparison_expectation']['expectation'], 'with_skill_better')

    def test_c25_challenges_do_not_use_unrelated_generic_tourist(self):
        for c in self.c25:
            prompt = c.get('prompt', c.get('first_turn', '')).lower()
            with self.subTest(c['id']):
                self.assertTrue(any(t in prompt for t in (
                    'eu-family', 'eu citizen', 'eu-citizen', 'eu spouse',
                    'eu-citizen spouse', 'another member state', 'other member state')))

    def test_unrun_cases_are_not_presented_as_successes(self):
        for c in self.suite['cases']:
            if c['id'].startswith('c26-'):
                self.assertNotIn('pass', c)
                self.assertNotIn('observed_response', c)


if __name__ == '__main__':
    unittest.main(verbosity=2)
