#!/usr/bin/env python3
"""Contract-level C25 tests. Not ChatGPT legal-semantic or privacy validation."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
import c25_strategy_gate as c25

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'evaluations/fixtures/c25/complete-fictional.json'
BAD = ROOT / 'evaluations/fixtures/c25/missing-grievance-fictional.json'


class C25StrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(FIXTURE.read_text(encoding='utf-8'))
        cls.negative = json.loads(BAD.read_text(encoding='utf-8'))

    def assess_change(self, f):
        x = copy.deepcopy(self.base)
        f(x)
        return c25.assess(x)

    def fails_change(self, f):
        x = copy.deepcopy(self.base)
        f(x)
        with self.assertRaises(c25.C25Error):
            c25.assess(x)

    def flag_codes(self, x):
        return {f['code'] for f in c25.assess(x)['review_flags']}

    def test_complete_fixture_has_no_flags(self):
        r = c25.assess(self.base)
        self.assertEqual(r['review_flags'], [])
        self.assertEqual(r['missing_grievance_codes'], [])
        self.assertEqual(r['status'], 'human_review_required')

    def test_no_private_or_send(self):
        r = c25.assess(self.base)
        self.assertFalse(r['private_data_enabled'])
        self.assertFalse(r['external_disclosure_authorized'])

    def test_missing_conduct_grievance_detected(self):
        r = c25.assess(self.negative)
        self.assertIn('staff_treatment_grievance', r['missing_grievance_codes'])

    def test_promoted_uninvoked_defense_detected(self):
        self.assertIn('uninvoked_defense_promoted_to_actual_ground', self.flag_codes(self.negative))

    def test_missing_gdpr_review_detected(self):
        self.assertIn('consider_data_subject_access', self.flag_codes(self.negative))

    def test_preservation_review_detected(self):
        self.assertIn('consider_urgent_preservation', self.flag_codes(self.negative))

    def test_conduct_investigation_detected(self):
        self.assertIn('consider_separate_conduct_investigation', self.flag_codes(self.negative))

    def test_possible_records_even_when_not_confirmed(self):
        def edit(d):
            d['available_records'] = []
            d['evidence_actions'].remove('gdpr_access_considered')
        self.assertIn('consider_data_subject_access', {
            f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_nested_free_text_type_rejected_without_type_error(self):
        self.fails_change(lambda d: d['grievances'][0].update(route={'free_text': 'unsafe'}))

    def test_targeted_file_access_detected(self):
        r = self.assess_change(lambda d: d['evidence_actions'].remove('national_file_access_considered'))
        self.assertIn('consider_procedural_file_access', {f['code'] for f in r['review_flags']})

    def test_invoked_ground_unanswered_detected(self):
        def edit(d):
            d['defenses'][0]['authority_position'] = 'expressly_invoked'
        # Explicitly invoked + contingency => pending response
        self.assertIn('invoked_ground_lacks_response', {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_threshold_cannot_be_skipped(self):
        self.assertIn('threshold_requires_internal_merits_review', {
            f['code'] for f in self.assess_change(lambda d: d['defenses'][0].update(role='threshold_to_requested_relief'))['review_flags']})

    def test_disclosed_not_proved_waived(self):
        self.assertIn('disclosure_not_proof_of_consideration_or_waiver', self.flag_codes(self.negative))

    def test_routine_priority_for_physical_removal_flagged(self):
        self.assertIn('evidence_urgency_may_be_underweighted', {
            f['code'] for f in self.assess_change(lambda d: d['grievances'][-1].update(priority='routine_followup'))['review_flags']})

    def test_reject_priority_free_text(self):
        self.fails_change(lambda d: d['grievances'][0].update(priority='very very critical'))

    def test_exclusion_requires_review(self):
        self.assertIn('reasoned_exclusion_requires_human_review', {
            f['code'] for f in self.assess_change(lambda d: d['grievances'][0].update(disposition='reasoned_exclusion'))['review_flags']})

    def test_candidate_without_route(self):
        self.assertIn('candidate_without_remedy_route', {
            f['code'] for f in self.assess_change(lambda d: d['grievances'][0].update(route='none'))['review_flags']})

    def test_no_duplicate_events(self):
        self.fails_change(lambda d: d['reported_events'].append('physical_removal'))

    def test_no_duplicate_grievances(self):
        self.fails_change(lambda d: d['grievances'].append(copy.deepcopy(d['grievances'][0])))

    def test_unknown_custom_grievance_not_allowed(self):
        self.fails_change(lambda d: d['grievances'][0].update(issue='security_officer_name'))

    def test_no_free_text_field(self):
        self.fails_change(lambda d: d.update(applicant_name='Fictional Name'))

    def test_reject_unknown_defense(self):
        self.fails_change(lambda d: d['defenses'][0].update(authority_position='someone_once_said'))

    def test_question_cap_three(self):
        self.fails_change(lambda d: d['questions'].extend([
            {'question': 'decision_service_date', 'impact': 'changes_deadline'},
            {'question': 'actual_objection_invoked', 'impact': 'changes_competence'}]))

    def test_no_duplicate_questions(self):
        self.fails_change(lambda d: d['questions'].append(copy.deepcopy(d['questions'][0])))

    def test_reject_real_case_mode(self):
        self.fails_change(lambda d: d.update(mode='real_case'))

    def test_reject_no_events(self):
        self.fails_change(lambda d: d.update(reported_events=[]))

    def test_result_is_deterministic(self):
        self.assertEqual(c25.assess(self.base), c25.assess(copy.deepcopy(self.base)))

    def test_no_copy_of_input_which_could_leak(self):
        r = c25.assess(self.base)
        for k in ('reported_events', 'available_records', 'questions', 'defenses'):
            self.assertNotIn(k, r)

    def test_cli_fixture(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts/c25_strategy_gate.py'),
                            'preview', '--input', str(FIXTURE)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['review_flags'], [])

    def test_cli_rejects_real_case_mode_without_echo(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / 'invalid.json'
            data = copy.deepcopy(self.base)
            data['mode'] = 'real_case'
            path.write_text(json.dumps(data), encoding='utf-8')
            p = subprocess.run([sys.executable, str(ROOT / 'scripts/c25_strategy_gate.py'),
                                'preview', '--input', str(path)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn('unsupported_schema_or_mode', p.stderr)
            self.assertNotIn('territorial_competence', p.stderr)


    def test_individual_physical_removal_cannot_hide_under_staff_category(self):
        def edit(p):
            p['event_reviews'] = [e for e in p['event_reviews'] if e['event'] != 'physical_removal']
        r = self.assess_change(edit)
        self.assertEqual(r['missing_grievance_codes'], [])
        self.assertIn('physical_removal', r['missing_reported_event_codes'])
        self.assertIn('unaddressed_reported_event', {f['code'] for f in r['review_flags']})

    def test_individual_intimidation_cannot_hide_under_removal(self):
        def edit(p):
            p['event_reviews'] = [e for e in p['event_reviews'] if e['event'] != 'reported_staff_intimidation']
        self.assertIn('reported_staff_intimidation',
                      self.assess_change(edit)['missing_reported_event_codes'])

    def test_physical_removal_requires_own_proportionate_action(self):
        def edit(p):
            next(x for x in p['event_reviews'] if x['event'] == 'physical_removal').update(route='none')
        self.assertIn('event_conduct_route_unaddressed',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_physical_removal_urgency_individual(self):
        def edit(p):
            next(x for x in p['event_reviews'] if x['event'] == 'physical_removal').update(priority='routine_followup')
        self.assertIn('event_evidence_urgency_underweighted',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_event_exclusion_is_not_automatic_completion(self):
        def edit(p):
            next(x for x in p['event_reviews'] if x['event'] == 'physical_removal').update(disposition='reasoned_exclusion')
        self.assertIn('event_exclusion_needs_human_review',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_event_candidate_cannot_be_hidden_by_summary_exclusion(self):
        def edit(p):
            next(x for x in p['grievances'] if x['issue'] == 'staff_treatment_grievance').update(disposition='reasoned_exclusion')
        self.assertIn('event_summary_disposition_conflict',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_event_mapping_must_be_canonical(self):
        def edit(p):
            p['event_reviews'][0]['issue'] = 'staff_treatment_grievance'
        self.fails_change(edit)

    def test_no_duplicate_event_review(self):
        self.fails_change(lambda p: p['event_reviews'].append(copy.deepcopy(p['event_reviews'][0])))

    def test_no_fake_event_review(self):
        self.fails_change(lambda p: p['event_reviews'][0].update(event='made_up_action'))

    def test_no_out_of_case_event_review(self):
        def edit(p):
            p['reported_events'].remove('physical_removal')
        self.fails_change(edit)

    def test_gdpr_considered_token_alone_is_not_sufficient(self):
        def edit(p):
            p['evidence_plans'] = [x for x in p['evidence_plans'] if x['route'] != 'gdpr_article15']
        codes = {f['code'] for f in self.assess_change(edit)['review_flags']}
        self.assertIn('consideration_without_evidence_plan', codes)
        self.assertIn('gdpr_review_without_actionable_route', codes)

    def test_gdpr_without_record_targets_detected(self):
        def edit(p):
            next(x for x in p['evidence_plans'] if x['route'] == 'gdpr_article15')['records'] = []
        self.assertIn('evidence_plan_lacks_action_or_record_targets',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_gdpr_without_action_detected(self):
        def edit(p):
            next(x for x in p['evidence_plans'] if x['route'] == 'gdpr_article15')['next_step'] = 'none'
        self.assertIn('evidence_plan_lacks_action_or_record_targets',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_gdpr_controller_uncertainty_cannot_be_ignored(self):
        def edit(p):
            next(x for x in p['evidence_plans'] if x['route'] == 'gdpr_article15')['next_step'] = 'targeted_personal_data_request'
        self.assertIn('gdpr_controller_uncertainty_unaddressed',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_gdpr_requires_personal_data_limit(self):
        def edit(p):
            next(x for x in p['evidence_plans'] if x['route'] == 'gdpr_article15')['limits'].remove('personal_data_only')
        self.assertIn('gdpr_personal_data_scope_not_checked',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_cctv_requires_security_or_third_party_limit(self):
        def edit(p):
            next(x for x in p['evidence_plans'] if x['route'] == 'gdpr_article15')['limits'].remove('third_party_or_security_limits')
        self.assertIn('gdpr_cctv_exemptions_not_checked',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_preservation_is_separate_from_gdpr_and_time_sensitive(self):
        def edit(p):
            p['evidence_plans'] = [x for x in p['evidence_plans'] if x['route'] != 'urgent_preservation']
        self.assertIn('preservation_review_without_separate_request',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_preservation_not_an_automatic_retention_order(self):
        def edit(p):
            next(x for x in p['evidence_plans'] if x['route'] == 'urgent_preservation')['limits'].remove('no_automatic_record_retention')
        self.assertIn('preservation_not_automatic_guardrail_missing',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_preservation_deferred_pending_controller_is_flagged(self):
        def edit(p):
            next(x for x in p['evidence_plans'] if x['route'] == 'urgent_preservation')['decision'] = 'conditional_controller_check'
        self.assertIn('urgent_preservation_may_be_delayed',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_claimed_invoked_ground_without_authority_statement_flagged(self):
        def edit(p):
            p['defenses'][0].update(authority_position='expressly_invoked', handling='respond_to_invocation')
        self.assertIn('express_invocation_without_authority_statement_basis',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_authority_statement_but_not_invoked_requires_reconciliation(self):
        def edit(p):
            p['defenses'][0]['attribution_basis'] = 'written_authority_statement'
        self.assertIn('source_kind_conflicts_uninvoked_label',
                      {f['code'] for f in self.assess_change(edit)['review_flags']})

    def test_no_free_text_in_attribution(self):
        self.fails_change(lambda p: p['defenses'][0].update(attribution_basis='my full email'))

    def test_no_identifying_data_in_evidence_plan(self):
        self.fails_change(lambda p: p['evidence_plans'][0].update(controller_name='Real Person'))

    def test_no_external_url_in_evidence_plan(self):
        self.fails_change(lambda p: p['evidence_plans'][0]['records'].append('https://example.org/record'))

    def test_output_never_includes_raw_event_reviews_or_evidence_plans(self):
        r = c25.assess(self.base)
        self.assertNotIn('event_reviews', r)
        self.assertNotIn('evidence_plans', r)
        self.assertFalse(r['external_disclosure_authorized'])

    def test_old_schema_requires_explicit_migration(self):
        self.fails_change(lambda p: p.update(schema='c25-abstract-strategy/0.2.0'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
