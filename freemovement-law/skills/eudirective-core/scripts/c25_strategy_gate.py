#!/usr/bin/env python3
"""C25/C26 synthetic-only categorical applicant-strategy review gate.

DO NOT submit personal narratives, names, locations, dates or real-case records.
All classifications are reviewer supplied; this helper cannot verify source-span
attribution, legal correctness, model compliance, privacy or remedy prospects.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import c24_fact_rule_trace as c24

SCHEMA = 'c25-abstract-strategy/0.3.0'
OUTPUT_SCHEMA = 'c25-abstract-strategy-review/0.3.0'
EVENTS = {
    'ordinary_document_demand': 'visa_supporting_document_grievance',
    'direct_lodgement_denied': 'lodgement_access_grievance',
    'no_procedural_receipt': 'procedural_status_grievance',
    'reported_staff_intimidation': 'staff_treatment_grievance',
    'physical_removal': 'staff_treatment_grievance',
    'documented_delay': 'delay_grievance',
    'digital_only_access': 'digital_access_grievance',
    'record_access_denied': 'records_access_grievance',
    'other_conduct': 'other_grievance_requires_review',
}
GRIEVANCES = frozenset(EVENTS.values())
DISPOSITIONS = frozenset(('candidate_for_complaint', 'needs_decisive_fact',
                          'evidence_or_preservation_only', 'reasoned_exclusion'))
PRIORITIES = frozenset(('urgent_evidence', 'deadline_sensitive',
                        'substantive_redress', 'routine_followup'))
REMEDY_ROUTES = frozenset(('formal_review_pending_source', 'visa_process_complaint',
                           'conduct_complaint', 'written_status_request',
                           'administrative_records_request', 'none'))
DEFENSES = frozenset(('territorial_competence', 'family_scope',
                      'application_not_lodged', 'documents_missing',
                      'other_potential_objection'))
POSITIONS = frozenset(('expressly_invoked', 'indicated_unconfirmed',
                       'not_invoked', 'unknown'))
KNOWLEDGE = frozenset(('acknowledged', 'disclosed_unacknowledged',
                       'not_shown', 'unknown'))
ROLES = frozenset(('threshold_to_requested_relief', 'potential_defense', 'peripheral'))
HANDLING = frozenset(('lead_complaint', 'respond_to_invocation', 'contingency_only',
                      'request_clarification', 'legally_required_disclosure'))
ATTRIBUTION = frozenset(('written_authority_statement',
                         'reported_oral_authority_statement',
                         'authority_case_record', 'indirect_authority_hint',
                         'applicant_disclosure_only', 'none'))
DIRECT_ATTRIBUTION = frozenset(('written_authority_statement',
                                'reported_oral_authority_statement',
                                'authority_case_record'))
RECORDS = frozenset(('emails', 'email_access_metadata', 'appointment_records',
                     'visa_case_notes', 'cctv', 'incident_report',
                     'security_log', 'system_access_log'))
EVIDENCE_ACTIONS = frozenset(('gdpr_access_considered',
                              'urgent_preservation_considered',
                              'national_file_access_considered',
                              'complaint_investigation_considered',
                              'formal_disclosure_considered'))
EVIDENCE_ROUTES = frozenset(('gdpr_article15', 'urgent_preservation',
                             'national_file_access', 'conduct_investigation'))
PLAN_DECISIONS = frozenset(('recommend_now', 'conditional_controller_check',
                            'reasoned_not_appropriate'))
CONTROLLER_STATUSES = frozenset(('identified_needs_source_review',
                                 'needs_verification', 'multiple_possible',
                                 'not_applicable'))
NEXT_STEPS = frozenset(('targeted_personal_data_request',
                        'identify_controller_then_request',
                        'request_preservation_where_lawful',
                        'request_file_access_where_available',
                        'request_conduct_investigation', 'none'))
PLAN_LIMITS = frozenset(('personal_data_only', 'not_whole_files',
                         'third_party_or_security_limits',
                         'gdpr_request_not_preservation',
                         'no_automatic_record_retention',
                         'controller_must_be_verified',
                         'no_visa_deadline_suspension',
                         'sector_specific_access_may_apply'))
ROUTE_NEXT_STEPS = {
    'gdpr_article15': {'targeted_personal_data_request', 'identify_controller_then_request'},
    'urgent_preservation': {'request_preservation_where_lawful'},
    'national_file_access': {'request_file_access_where_available'},
    'conduct_investigation': {'request_conduct_investigation'},
}
QUESTIONS = frozenset(('lodgement_status', 'decision_service_date',
                       'actor_or_employer', 'actual_objection_invoked',
                       'available_cctv', 'desired_remedy', 'movement_or_family_scope'))
QUESTION_IMPACTS = frozenset(('changes_relief', 'changes_deadline',
                              'changes_competence', 'changes_evidence_urgency',
                              'changes_legal_regime'))


class C25Error(ValueError):
    pass


def _object(obj, keys, label):
    if type(obj) is not dict or set(obj) != keys:
        raise C25Error('invalid_' + label + '_shape')


def _codes(seq, allowed, label, maximum=15):
    if type(seq) is not list or len(seq) > maximum:
        raise C25Error('invalid_' + label)
    if (any(type(x) is not str or x not in allowed for x in seq) or
            len(seq) != len(set(seq))):
        raise C25Error('invalid_' + label)


def _grievance(item, keys, label):
    _object(item, keys, label)
    return (type(item['issue']) is str and item['issue'] in GRIEVANCES and
            type(item['disposition']) is str and item['disposition'] in DISPOSITIONS and
            type(item['route']) is str and item['route'] in REMEDY_ROUTES and
            type(item['priority']) is str and item['priority'] in PRIORITIES)


def validate(p):
    _object(p, {'schema', 'mode', 'reported_events', 'event_reviews', 'grievances',
                'defenses', 'available_records', 'evidence_actions',
                'evidence_plans', 'questions'}, 'payload')
    if p['schema'] != SCHEMA or p['mode'] != 'synthetic_abstract_review':
        raise C25Error('unsupported_schema_or_mode')
    _codes(p['reported_events'], EVENTS, 'reported_events')
    if not p['reported_events']:
        raise C25Error('no_reported_events')
    _codes(p['available_records'], RECORDS, 'available_records')
    _codes(p['evidence_actions'], EVIDENCE_ACTIONS, 'evidence_actions')
    if type(p['grievances']) is not list or len(p['grievances']) > len(GRIEVANCES):
        raise C25Error('invalid_grievances')
    seen = set()
    for g in p['grievances']:
        if (not _grievance(g, {'issue', 'disposition', 'route', 'priority'}, 'grievance') or
                g['issue'] in seen):
            raise C25Error('invalid_grievance_classification')
        seen.add(g['issue'])
    if type(p['event_reviews']) is not list or len(p['event_reviews']) > len(EVENTS):
        raise C25Error('invalid_event_reviews')
    seen = set()
    for item in p['event_reviews']:
        if not _grievance(item, {'event', 'issue', 'disposition', 'route', 'priority'}, 'event_review'):
            raise C25Error('invalid_event_review_classification')
        event = item['event']
        if (type(event) is not str or event not in p['reported_events'] or
                event in seen or item['issue'] != EVENTS[event]):
            raise C25Error('invalid_event_review_mapping')
        seen.add(event)
    if type(p['defenses']) is not list or len(p['defenses']) > len(DEFENSES):
        raise C25Error('invalid_defenses')
    seen = set()
    defense_keys = {'issue', 'authority_position', 'authority_knowledge',
                    'role', 'handling', 'attribution_basis'}
    for d in p['defenses']:
        _object(d, defense_keys, 'defense')
        if (type(d['issue']) is not str or d['issue'] not in DEFENSES or d['issue'] in seen or
                any(type(d[k]) is not str for k in defense_keys) or
                d['authority_position'] not in POSITIONS or
                d['authority_knowledge'] not in KNOWLEDGE or
                d['role'] not in ROLES or d['handling'] not in HANDLING or
                d['attribution_basis'] not in ATTRIBUTION):
            raise C25Error('invalid_defense_classification')
        seen.add(d['issue'])
    if type(p['evidence_plans']) is not list or len(p['evidence_plans']) > len(EVIDENCE_ROUTES):
        raise C25Error('invalid_evidence_plans')
    seen = set()
    plan_keys = {'route', 'decision', 'controller_status', 'records', 'next_step', 'limits'}
    for item in p['evidence_plans']:
        _object(item, plan_keys, 'evidence_plan')
        if (type(item['route']) is not str or item['route'] not in EVIDENCE_ROUTES or
                item['route'] in seen or type(item['decision']) is not str or
                item['decision'] not in PLAN_DECISIONS or
                type(item['controller_status']) is not str or
                item['controller_status'] not in CONTROLLER_STATUSES or
                type(item['next_step']) is not str or item['next_step'] not in NEXT_STEPS):
            raise C25Error('invalid_evidence_plan_classification')
        _codes(item['records'], RECORDS, 'evidence_plan_records', maximum=len(RECORDS))
        _codes(item['limits'], PLAN_LIMITS, 'evidence_plan_limits', maximum=len(PLAN_LIMITS))
        seen.add(item['route'])
    if type(p['questions']) is not list or len(p['questions']) > 3:
        raise C25Error('invalid_question_count')
    seen = set()
    for item in p['questions']:
        _object(item, {'question', 'impact'}, 'question')
        if (type(item['question']) is not str or item['question'] not in QUESTIONS or
                item['question'] in seen or type(item['impact']) is not str or
                item['impact'] not in QUESTION_IMPACTS):
            raise C25Error('invalid_question_classification')
        seen.add(item['question'])
    # C24's source-integrity boundary verifies local byte identities, NOT legal conclusions.
    c24._source_gate()


def assess(p):
    validate(p)
    expected_issues = sorted({EVENTS[e] for e in p['reported_events']})
    grievances = {g['issue']: g for g in p['grievances']}
    events = set(p['reported_events'])
    event_reviews = {r['event']: r for r in p['event_reviews']}
    records = set(p['available_records'])
    acts = set(p['evidence_actions'])
    plans = {r['route']: r for r in p['evidence_plans']}
    flags = []

    def flag(code, issue):
        flags.append({'code': code, 'issue': issue})

    missing_issues = sorted(set(expected_issues) - set(grievances))
    missing_events = sorted(events - set(event_reviews))
    for issue in missing_issues:
        flag('unaddressed_reported_grievance', issue)
    for event in missing_events:
        flag('unaddressed_reported_event', event)
    for event, g in event_reviews.items():
        if g['disposition'] == 'candidate_for_complaint' and g['route'] == 'none':
            flag('event_candidate_without_remedy_route', event)
        if g['disposition'] == 'reasoned_exclusion':
            flag('event_exclusion_needs_human_review', event)
        if event in ('reported_staff_intimidation', 'physical_removal') and g['route'] == 'none':
            flag('event_conduct_route_unaddressed', event)
        if event == 'physical_removal' and g['priority'] == 'routine_followup':
            flag('event_evidence_urgency_underweighted', event)
        if g['issue'] not in grievances:
            flag('event_without_grievance_summary', event)
        elif (g['disposition'] == 'candidate_for_complaint' and
              grievances[g['issue']]['disposition'] == 'reasoned_exclusion'):
            flag('event_summary_disposition_conflict', event)
    for issue, g in grievances.items():
        if g['disposition'] == 'candidate_for_complaint' and g['route'] == 'none':
            flag('candidate_without_remedy_route', issue)
        if g['disposition'] == 'reasoned_exclusion':
            flag('reasoned_exclusion_requires_human_review', issue)
        if ('physical_removal' in events and issue == 'staff_treatment_grievance' and
                g['priority'] == 'routine_followup'):
            flag('evidence_urgency_may_be_underweighted', issue)
        if issue == 'staff_treatment_grievance' and g['route'] == 'none':
            flag('conduct_route_unaddressed', issue)
    for d in p['defenses']:
        issue = d['issue']
        if d['authority_position'] == 'not_invoked' and d['handling'] in ('lead_complaint', 'respond_to_invocation'):
            flag('uninvoked_defense_promoted_to_actual_ground', issue)
        if d['authority_position'] == 'expressly_invoked' and d['handling'] == 'contingency_only':
            flag('invoked_ground_lacks_response', issue)
        if d['role'] == 'threshold_to_requested_relief' and d['handling'] == 'contingency_only':
            flag('threshold_requires_internal_merits_review', issue)
        if d['authority_knowledge'] == 'disclosed_unacknowledged' and d['handling'] == 'lead_complaint':
            flag('disclosure_not_proof_of_consideration_or_waiver', issue)
        if d['authority_position'] == 'expressly_invoked' and d['attribution_basis'] not in DIRECT_ATTRIBUTION:
            flag('express_invocation_without_authority_statement_basis', issue)
        if d['authority_position'] == 'not_invoked' and d['attribution_basis'] in DIRECT_ATTRIBUTION:
            flag('source_kind_conflicts_uninvoked_label', issue)
        if d['authority_position'] == 'indicated_unconfirmed' and d['attribution_basis'] in ('none', 'applicant_disclosure_only'):
            flag('authority_indication_needs_source_support', issue)
        if d['authority_knowledge'] == 'acknowledged' and d['attribution_basis'] == 'applicant_disclosure_only':
            flag('disclosure_not_evidence_of_acknowledgment', issue)

    need_gdpr = bool(records or events & {'ordinary_document_demand', 'no_procedural_receipt',
                                           'reported_staff_intimidation', 'physical_removal',
                                           'record_access_denied'})
    need_preservation = bool('cctv' in records or events & {'physical_removal', 'reported_staff_intimidation'})
    if need_gdpr and 'gdpr_access_considered' not in acts:
        flag('consider_data_subject_access', 'authority_held_personal_data')
    if need_preservation and 'urgent_preservation_considered' not in acts:
        flag('consider_urgent_preservation', 'potentially_ephemeral_records')
    if need_preservation and 'complaint_investigation_considered' not in acts:
        flag('consider_separate_conduct_investigation', 'staff_treatment_grievance')
    if 'no_procedural_receipt' in events and 'national_file_access_considered' not in acts:
        flag('consider_procedural_file_access', 'procedural_status_grievance')
    route_tags = {
        'gdpr_article15': 'gdpr_access_considered',
        'urgent_preservation': 'urgent_preservation_considered',
        'national_file_access': 'national_file_access_considered',
        'conduct_investigation': 'complaint_investigation_considered',
    }
    for route, tag in route_tags.items():
        if tag in acts and route not in plans:
            flag('consideration_without_evidence_plan', route)
    for route, plan in plans.items():
        if plan['decision'] == 'reasoned_not_appropriate':
            flag('evidence_route_exclusion_needs_human_review', route)
            if plan['next_step'] != 'none':
                flag('inconsistent_evidence_exclusion', route)
            continue
        if plan['next_step'] not in ROUTE_NEXT_STEPS[route] or not plan['records']:
            flag('evidence_plan_lacks_action_or_record_targets', route)
        if route == 'gdpr_article15':
            if 'personal_data_only' not in plan['limits']:
                flag('gdpr_personal_data_scope_not_checked', route)
            if 'gdpr_request_not_preservation' not in plan['limits']:
                flag('gdpr_access_vs_preservation_not_separated', route)
            if ('cctv' in plan['records'] and
                    'third_party_or_security_limits' not in plan['limits']):
                flag('gdpr_cctv_exemptions_not_checked', route)
            if (plan['controller_status'] in ('needs_verification', 'multiple_possible') and
                    plan['next_step'] != 'identify_controller_then_request'):
                flag('gdpr_controller_uncertainty_unaddressed', route)
        if route == 'urgent_preservation':
            if 'no_automatic_record_retention' not in plan['limits']:
                flag('preservation_not_automatic_guardrail_missing', route)
            if plan['decision'] == 'conditional_controller_check':
                flag('urgent_preservation_may_be_delayed', route)
    if need_gdpr and 'gdpr_article15' not in plans:
        flag('gdpr_review_without_actionable_route', 'authority_held_personal_data')
    if need_preservation and 'urgent_preservation' not in plans:
        flag('preservation_review_without_separate_request', 'potentially_ephemeral_records')
    if need_preservation and 'conduct_investigation' not in plans:
        flag('conduct_investigation_without_plan', 'staff_treatment_grievance')
    flags.sort(key=lambda x: (x['code'], x['issue']))
    return {
        'schema': OUTPUT_SCHEMA,
        'status': 'human_review_required',
        'reported_event_count': len(p['reported_events']),
        'event_review_count': len(p['event_reviews']),
        'expected_grievance_codes': expected_issues,
        'missing_grievance_codes': missing_issues,
        'missing_reported_event_codes': missing_events,
        'evidence_plan_route_codes': sorted(plans),
        'review_flags': flags,
        'limitations': [
            'synthetic_feature_labels_are_not_anonymisation',
            'no_narrative_extraction_or_independent_source_span_verification',
            'no_legal_merits_or_national_authority_verification',
            'no_proof_model_recommended_any_plan_to_applicant',
            'no_gdpr_scope_certification_or_record_preservation',
            'no_automated_external_actions',
        ],
        'private_data_enabled': False,
        'external_disclosure_authorized': False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('operation', choices=('preview',))
    ap.add_argument('--input', required=True, help='Fictional abstract JSON path only')
    args = ap.parse_args(argv)
    try:
        data = json.loads(Path(args.input).read_text(encoding='utf-8'))
        result = assess(data)
    except (ValueError, TypeError, OSError, RecursionError) as exc:
        message = str(exc) if isinstance(exc, C25Error) else 'invalid_or_unavailable_input'
        print(json.dumps({'error': message}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
