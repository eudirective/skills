#!/usr/bin/env python3
"""C24: bounded, source-indexed fact-to-rule trace and revision audit.

This tool accepts *only categorical, abstract features*. It NEVER extracts facts
from a user's story, verifies truth, proves a legal conclusion, sends data, or
certifies privacy. The CLI writes only to stdout/stderr. Even a feature vector
can be personal data in context: do not supply case identifiers or raw records.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import c23_scope_contrast as c23
from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'c24-abstract-case-trace/0.1.0'
RESPONSE_SCHEMA = 'c24-abstract-case-trace-result/0.1.0'
FACT_VALUES = frozenset({'yes', 'no', 'unknown'})
ORIGINS = frozenset({'user_account', 'authority_reported_by_user',
                     'supplied_document_described', 'reviewer_inference', 'not_supplied'})
CHANGE_REASONS = frozenset({'user_correction', 'record_clarification',
                            'classification_revision', 'new_answer_to_question'})
SCOPE_KEYS = tuple(c23.PREDICATES)
FACT_KEYS = frozenset((*SCOPE_KEYS, 'potential_returnee',
    'lawful_presence_in_consular_country', 'application_formally_lodged',
    'written_refusal_served', 'service_date_known',
    'authority_demanded_extra_documents', 'appointment_free_lodging_attempted',
    'family_relationship_contested', 'article_10_residence_card_held'))
ISSUES = ('eu_family_regime', 'ordinary_supporting_documents',
          'consular_territorial_competence', 'consular_access',
          'lodgement_and_written_decision', 'formal_remedy_deadline',
          'national_complaint_route')
DEPENDENCIES = {
    'eu_family_regime': (*SCOPE_KEYS, 'potential_returnee'),
    'ordinary_supporting_documents': (*SCOPE_KEYS, 'potential_returnee',
                                     'authority_demanded_extra_documents'),
    'consular_territorial_competence': ('lawful_presence_in_consular_country',),
    'consular_access': ('appointment_free_lodging_attempted',),
    'lodgement_and_written_decision': ('application_formally_lodged',
                                       'written_refusal_served'),
    'formal_remedy_deadline': ('written_refusal_served', 'service_date_known'),
    'national_complaint_route': ('written_refusal_served',),
}
# References are provided for REVIEW, not as proof that each legal proposition is true.
SOURCES = {
    'directive_2004_38_articles_2_3_5': {
        'path': str(compatibility_root() / 'sources/eu/CELEX_02004L0038-20110616_EN_TXT.md'),
        'locator': 'Articles 2, 3, 5', 'kind': 'binding_eu_law_local_copy'},
    'visa_code_article_6': {
        'path': str(compatibility_root() / 'sources/eu/CELEX_02009R0810-20240628_EN_TXT.md'),
        'locator': 'Article 6', 'kind': 'binding_eu_law_local_copy'},
    'visa_code_article_32': {
        'path': str(compatibility_root() / 'sources/eu/CELEX_02009R0810-20240628_EN_TXT.md'),
        'locator': 'Article 32', 'kind': 'binding_eu_law_local_copy'},
    'handbook_part_III_3_1': {
        'path': str(compatibility_root() / 'sources/eu/Visa_Code_Handbook_I_2024_EN_Annex_2024.md'),
        'locator': 'Part III 3.1', 'kind': 'commission_interpretive_guidance'},
    'handbook_part_III_4_7': {
        'path': str(compatibility_root() / 'sources/eu/Visa_Code_Handbook_I_2024_EN_Annex_2024.md'),
        'locator': 'Part III 4.7.2-4.7.3', 'kind': 'commission_interpretive_guidance'},
}
ISSUE_REFERENCES = {
    'eu_family_regime': ('directive_2004_38_articles_2_3_5',),
    'ordinary_supporting_documents': ('directive_2004_38_articles_2_3_5',
                                      'handbook_part_III_4_7'),
    'consular_territorial_competence': ('visa_code_article_6', 'handbook_part_III_3_1'),
    'consular_access': ('directive_2004_38_articles_2_3_5',),
    'lodgement_and_written_decision': ('directive_2004_38_articles_2_3_5',),
    'formal_remedy_deadline': ('visa_code_article_32',),
    'national_complaint_route': (),
}
QUESTION_REASONS = {
    'eu_citizen_moving_to_other_member_state': 'direct_mobility_scope',
    'non_eu_direct_family_member': 'family_member_scope',
    'accompany_or_join': 'movement_connection',
    'potential_returnee': 'possible_returnee_exception',
    'lawful_presence_in_consular_country': 'consular_territorial_competence_only',
    'appointment_free_lodging_attempted': 'access_incident',
    'application_formally_lodged': 'procedural_status',
    'written_refusal_served': 'formal_review_or_written_decision',
    'service_date_known': 'deadline_requires_service_fact',
    'authority_demanded_extra_documents': 'what_was_required',
}

class TraceError(ValueError):
    """Safe short machine-readable error without replay of rejected input."""


def _check_object(obj, required, name):
    if type(obj) is not dict or set(obj) != set(required):
        raise TraceError('invalid_' + name + '_shape')


def _source_gate():
    c23._verify_local_basis()  # fully checks locally bundled C1 representation hashes
    for r in SOURCES.values():
        path = ROOT / r['path']
        if not path.is_file():
            raise TraceError('missing_pinned_rule_representation')


def _validate(payload):
    _check_object(payload, {'schema', 'mode', 'revision', 'facts',
                            'requested_issues', 'document_demands'}, 'case')
    if payload['schema'] != SCHEMA or payload['mode'] != 'abstract_read_only_advisory':
        raise TraceError('unsupported_schema_or_mode')
    if type(payload['revision']) is not int or not 1 <= payload['revision'] <= 999:
        raise TraceError('invalid_revision')
    facts = payload['facts']
    if type(facts) is not dict or not set(facts).issubset(FACT_KEYS):
        raise TraceError('invalid_fact_keys')
    for key, rec in facts.items():
        _check_object(rec, {'value', 'origin', 'change_reason'}, 'fact')
        if rec['value'] not in FACT_VALUES or rec['origin'] not in ORIGINS:
            raise TraceError('invalid_fact_classification')
        if rec['value'] == 'unknown' and rec['origin'] not in ('not_supplied', 'reviewer_inference'):
            raise TraceError('unknown_must_not_claim_evidence')
        if rec['value'] != 'unknown' and rec['origin'] == 'not_supplied':
            raise TraceError('unsupported_fact_provenance')
        if rec['change_reason'] is not None and rec['change_reason'] not in CHANGE_REASONS:
            raise TraceError('invalid_change_reason')
        if payload['revision'] == 1 and rec['change_reason'] is not None:
            raise TraceError('initial_revision_cannot_be_correction')
    issues = payload['requested_issues']
    if type(issues) is not list or not 1 <= len(issues) <= len(ISSUES):
        raise TraceError('invalid_issues')
    if len(issues) != len(set(issues)) or any(i not in ISSUES for i in issues):
        raise TraceError('duplicate_or_unknown_issue')
    demands = payload['document_demands']
    if type(demands) is not list or len(demands) > 15:
        raise TraceError('invalid_demands')
    for item in demands:
        _check_object(item, {'item', 'purpose', 'mandatory'}, 'demand')
        if item['item'] not in c23.CODES or item['purpose'] not in c23.PURPOSES:
            raise TraceError('invalid_demand_code_or_purpose')
        if type(item['mandatory']) is not bool:
            raise TraceError('invalid_demand_mandatory')
    if demands and 'ordinary_supporting_documents' not in issues:
        raise TraceError('document_demands_without_scope_issue')
    if 'ordinary_supporting_documents' in issues and not demands:
        raise TraceError('document_issue_requires_coded_demands')
    _source_gate()


def _fact(payload, key):
    return payload['facts'].get(key, {'value': 'unknown',
                                     'origin': 'not_supplied', 'change_reason': None})


def _issue_status(issue, facts, scope_status, missing):
    """Mechanical triage, not a merits conclusion or authority finding."""
    if issue in ('eu_family_regime', 'ordinary_supporting_documents'):
        if issue == 'ordinary_supporting_documents' and facts['authority_demanded_extra_documents']['value'] == 'no':
            return 'no_mandatory_extra_document_demand_reported'
        if facts['potential_returnee']['value'] == 'yes':
            return 'returnee_or_analogous_regime_requires_separate_legal_review'
        if scope_status == 'directive_family_scope_assumed_from_reviewer_features':
            if issue == 'ordinary_supporting_documents' and \
                    facts['authority_demanded_extra_documents']['value'] == 'unknown':
                return 'reported_demand_needs_clarification'
            return 'conditional_eu_family_scope_for_review'
        if scope_status == 'outside_directive_family_pattern_on_supplied_features':
            return 'ordinary_directive_pattern_not_established_check_exceptions'
        return 'material_scope_question_open'
    if missing:
        return 'material_fact_missing_review_needed'
    if issue == 'formal_remedy_deadline':
        return 'requires_current_national_rule_and_exact_service_details'
    if issue == 'national_complaint_route':
        return 'requires_current_national_authority_and_power_verification'
    return 'fact_pattern_ready_for_source_and_remedy_review'


def assess(payload):
    _validate(payload)
    facts = {k: _fact(payload, k) for k in FACT_KEYS}
    scope_obj = {k: facts[k]['value'] for k in SCOPE_KEYS}
    scope_status, gaps = c23._scope(scope_obj)
    items = []
    if payload['document_demands']:
        items = c23.assess({'mode': 'abstract_read_only_advisory',
                            'scope': scope_obj, 'demands': payload['document_demands']})['demands']
    issues = []
    all_questions = []
    for issue in payload['requested_issues']:
        dependencies = DEPENDENCIES[issue]
        missing = [k for k in dependencies if facts[k]['value'] == 'unknown' and
                   not (k == 'potential_returnee' and
                        facts['eu_citizen_moving_to_other_member_state']['value'] == 'yes')]
        status = _issue_status(issue, facts, scope_status, missing)
        # A separate returnee possibility must never be treated as a definitive
        # direct-Directive disqualification because a three-feature check says no.
        issue_rules = [{'id': r, **SOURCES[r],
                        'source_check': 'local_integrity_only_not_live'}
                       for r in ISSUE_REFERENCES[issue]]
        issues.append({
            'issue': issue,
            'status': status,
            'fact_trace': [{'key': k, 'value': facts[k]['value'],
                            'basis': facts[k]['origin'],
                            'mapping_verification': 'not_independently_verified'}
                           for k in dependencies],
            'rule_references': issue_rules,
            'missing_material_facts': missing,
            'scope_comparator_status': scope_status if issue in ('eu_family_regime',
                                        'ordinary_supporting_documents') else 'not_applicable',
            'rule_scope_findings': items if issue == 'ordinary_supporting_documents'
                                   else [],
            'exceptions_to_review': (['returnee_and_national_scope',
                                       'territorial_competence_separate']
                                     if issue in ('eu_family_regime',
                                                  'ordinary_supporting_documents') else []),
            'remedy_status': 'no_national_remedy_verified',
            'must_not_claim_violation_proved': True,
        })
        for k in missing:
            if k in QUESTION_REASONS and k not in all_questions:
                all_questions.append(k)
    # If no direct cross-border movement, asking about returnee is more important
    # than asking irrelevant ordinary checklist details.
    if facts['eu_citizen_moving_to_other_member_state']['value'] == 'no' and \
            'potential_returnee' not in all_questions and \
            facts['potential_returnee']['value'] == 'unknown' and \
            any(x in ('eu_family_regime', 'ordinary_supporting_documents')
                for x in payload['requested_issues']):
        all_questions.insert(0, 'potential_returnee')
    questions = [{'fact_key': k, 'reason': QUESTION_REASONS[k]}
                 for k in all_questions[:3]]
    return {
        'schema': RESPONSE_SCHEMA, 'revision': payload['revision'],
        'mode': 'abstract_read_only_advisory',
        'source_integrity': 'C1_v0.6.1_locally_pinned_not_live_checked',
        'feature_extraction': 'reviewer_supplied_categorical_not_verified_by_script',
        'scope_status': scope_status, 'scope_missing': gaps,
        'issue_traces': issues, 'priority_question_codes': questions,
        'questions_are_for_model_to_phrase_without_private_data_requests': True,
        'legal_merits': 'not_determined_by_script',
        'national_authority_powers': 'not_verified_by_script',
        'external_disclosure_authorized': False,
        'private_data_isolation_verified': False,
        'contains_raw_case_narrative': False,
        'persistent_case_storage_authorized': False,
    }


def compare(previous, current):
    _validate(previous)
    _validate(current)
    if previous['mode'] != current['mode'] or current['revision'] != previous['revision'] + 1:
        raise TraceError('invalid_revision_chain')
    old = assess(previous)
    new = assess(current)
    changes = []
    for k in sorted(FACT_KEYS):
        before, after = _fact(previous, k), _fact(current, k)
        if before['value'] == after['value'] and before['origin'] == after['origin']:
            if after['change_reason'] is not None:
                raise TraceError('unchanged_fact_cannot_claim_correction')
            continue
        if after['change_reason'] is None:
            raise TraceError('fact_change_needs_explicit_reason')
        if before['value'] in ('yes', 'no') and after['value'] in ('yes', 'no') and \
                before['value'] != after['value'] and \
                after['change_reason'] not in ('user_correction', 'record_clarification',
                                               'classification_revision'):
            raise TraceError('opposing_fact_values_need_reconciliation')
        changes.append({'fact_key': k, 'previous_value': before['value'],
                        'current_value': after['value'],
                        'reason': after['change_reason'],
                        'contradiction_requires_review': before['value'] in ('yes', 'no') and
                                                          after['value'] in ('yes', 'no') and
                                                          before['value'] != after['value']})
    if not changes and previous['requested_issues'] == current['requested_issues'] and \
            previous['document_demands'] == current['document_demands']:
        raise TraceError('no_actual_change_in_revision')
    old_issues = {i['issue']: i for i in old['issue_traces']}
    new_issues = {i['issue']: i for i in new['issue_traces']}
    changed_keys = {c['fact_key'] for c in changes}
    affected = []
    for issue in sorted(set(old_issues) | set(new_issues)):
        is_affected = bool(changed_keys.intersection(DEPENDENCIES[issue])) or \
                      issue not in old_issues or issue not in new_issues or \
                      (issue == 'ordinary_supporting_documents' and
                       previous['document_demands'] != current['document_demands'])
        if is_affected:
            affected.append({
                'issue': issue, 'previous_status': old_issues.get(issue, {}).get('status'),
                'current_status': new_issues.get(issue, {}).get('status'),
                'previous_advice_is_stale': True,
                'must_reassess_sources_actions_and_deadlines': True,
            })
    return {
        'schema': 'c24-abstract-case-revision/0.1.0',
        'from_revision': previous['revision'], 'to_revision': current['revision'],
        'changes': changes, 'affected_issues': affected,
        'updated_trace': new,
        'must_identify_displaced_advice_to_user': bool(affected),
        'contradictions_require_human_reconciliation': any(
            c['contradiction_requires_review'] for c in changes),
        'external_disclosure_authorized': False,
        'legal_merits': 'not_determined_by_script',
    }


def _load(path):
    if path == '-':
        s = sys.stdin.read(15001)
        if len(s) > 15000:
            raise TraceError('oversized_input')
        return json.loads(s)
    p = Path(path)
    if p.stat().st_size > 15000:
        raise TraceError('oversized_input')
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preview', 'compare'])
    parser.add_argument('--input', required=True, help='Feature-only JSON path or - (stdin)')
    parser.add_argument('--previous', help='Previous abstract feature-only JSON for compare')
    args = parser.parse_args()
    try:
        obj = _load(args.input)
        if args.command == 'compare':
            if not args.previous:
                raise TraceError('previous_required_for_comparison')
            result = compare(_load(args.previous), obj)
        else:
            if args.previous:
                raise TraceError('previous_only_for_comparison')
            result = assess(obj)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (TraceError, c23.ScopeError, OSError, ValueError, KeyError, TypeError) as exc:
        reason = str(exc) if isinstance(exc, TraceError) else 'invalid_input_or_source'
        print(json.dumps({'status': 'blocked', 'reason': reason}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
