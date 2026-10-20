#!/usr/bin/env python3
"""C23: narrow, advisory EU-family/ordinary-checklist scope contrast.

Input is a STRICT, non-identifying feature vector. It does not process a
private case narrative, decide legal merits, authenticate documents or send.
The reviewing model/person must map case facts to the three scope predicates;
that semantic mapping is outside this deterministic function's proof scope.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import verify_bundled_source_pack as source_gate
from source_library_paths import compatibility_sources_root

VERSION = '0.1.0'
CODES = frozenset({
    'bank_statements', 'financial_means', 'accommodation_booking',
    'flight_reservation', 'travel_medical_insurance', 'local_residence_status',
    'family_link_evidence', 'eu_citizen_identity', 'applicant_passport',
    'eu_travel_confirmation', 'other'
})
PURPOSES = frozenset({'visa_entitlement', 'consular_territorial_competence', 'unknown'})
PREDICATES = ('eu_citizen_moving_to_other_member_state', 'non_eu_direct_family_member',
              'accompany_or_join')
NORMAL = frozenset({'bank_statements', 'financial_means', 'accommodation_booking',
                    'flight_reservation', 'travel_medical_insurance'})
EVIDENCE = frozenset({'family_link_evidence', 'eu_citizen_identity', 'applicant_passport'})
SOURCE = 'Visa_Code_Handbook_I_2024_EN_Annex_2024.md'


class ScopeError(ValueError):
    pass


def _enum(value, allowed, name):
    if not isinstance(value, str) or value not in allowed:
        raise ScopeError('invalid_' + name)


def _scope(rec: dict) -> tuple[str, list[str]]:
    if not isinstance(rec, dict) or set(rec) != set(PREDICATES):
        raise ScopeError('invalid_scope_predicates')
    for k in PREDICATES:
        _enum(rec[k], {'yes', 'no', 'unknown'}, k)
    if any(rec[k] == 'no' for k in PREDICATES):
        return 'outside_directive_family_pattern_on_supplied_features', []
    gaps = [k for k in PREDICATES if rec[k] == 'unknown']
    return ('potential_beneficiary_needs_specific_fact' if gaps else
            'directive_family_scope_assumed_from_reviewer_features'), gaps


def _verify_local_basis() -> None:
    # Reuse pinned C18 source identity/byte gate, never a filename-only test.
    proof = source_gate.inspect()
    if proof['source_pack_version'] != '0.6.1':
        raise ScopeError('stale_source_pack')
    path = compatibility_sources_root() / 'eu' / SOURCE
    txt = path.read_text(encoding='utf-8')
    required = (
        'harmonised lists of supporting documents, as drawn up in local Schengen cooperation, cannot',
        '## 3.   TERRITORIAL COMPETENCE',
        '### 4.7.2',
        '#### 4.7.3',
    )
    # Do not require arbitrary case normalization or language-model extraction.
    for expected in required:
        if expected not in txt:
            raise ScopeError('pinned_handbook_required_passage_missing')


def assess(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) != {'scope', 'demands', 'mode'}:
        raise ScopeError('invalid_contract_or_extra_keys')
    _enum(data['mode'], {'abstract_read_only_advisory'}, 'mode')
    scope, gaps = _scope(data['scope'])
    demands = data['demands']
    if not isinstance(demands, list) or not (1 <= len(demands) <= 15):
        raise ScopeError('invalid_demands')
    _verify_local_basis()
    items = []
    for d in demands:
        if not isinstance(d, dict) or set(d) != {'item', 'purpose', 'mandatory'}:
            raise ScopeError('invalid_demand_record')
        _enum(d['item'], CODES, 'item')
        _enum(d['purpose'], PURPOSES, 'purpose')
        if type(d['mandatory']) is not bool:
            raise ScopeError('invalid_mandatory_flag')
        code = d['item']
        purpose = d['purpose']
        if not d['mandatory']:
            finding = 'no_mandatory_demand_claimed'
        elif scope == 'outside_directive_family_pattern_on_supplied_features':
            finding = 'family_exception_not_established_on_features'
        elif scope == 'potential_beneficiary_needs_specific_fact':
            finding = 'conditional_until_family_scope_fact_answered'
        elif code in NORMAL and purpose == 'visa_entitlement':
            finding = 'ordinary_list_item_inapplicable_as_eu_family_visa_requirement'
        elif code in NORMAL and purpose == 'unknown':
            finding = 'inapplicable_as_routine_eu_family_support;ask_for_claimed_purpose'
        elif code in NORMAL and purpose == 'consular_territorial_competence':
            finding = 'not_a_routine_family_visa_condition;requires_specific_competence_basis'
        elif code == 'local_residence_status':
            finding = 'potentially_relevant_to_consular_territorial_competence_only'
        elif code in EVIDENCE:
            finding = 'relevant_to_family_beneficiary_proof'
        elif code == 'eu_travel_confirmation':
            finding = 'relevant_to_accompany_or_join_confirmation_no_paid_booking_required'
        else:
            finding = 'manual_source_and_purpose_review_needed'
        items.append({'item': code, 'purpose': purpose, 'mandatory_claimed': d['mandatory'],
                      'scope_finding': finding})
    return {
        'contract_version': VERSION,
        'status': 'abstract_rule_scope_review_not_legal_merits_adjudication',
        'scope_assessment': scope,
        'material_scope_gaps': gaps,
        'source_binding': {
            'core_source_pack': '0.6.1',
            'handbook': SOURCE,
            'handbook_parts': ['III 3.1', 'III 4.7.2', 'III 4.7.3(4)-(6)'],
            'assurance': 'locally_pinned_bytes_not_fresh_legal_validation',
        },
        'demands': items,
        'legal_violation_status': 'not_determined',
        'external_disclosure_authorized': False,
        'contains_private_case_narrative': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='Strict abstract JSON file, or - for stdin.')
    args = parser.parse_args()
    try:
        if args.input == '-':
            txt = sys.stdin.read(12001)
            if len(txt) > 12000:
                raise ScopeError('oversized_input')
            data = json.loads(txt)
        else:
            path = Path(args.input)
            if path.stat().st_size > 12000:
                raise ScopeError('oversized_input')
            data = json.loads(path.read_text(encoding='utf-8'))
        result = assess(data)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ScopeError, ValueError, OSError, KeyError) as ex:
        code = str(ex) if isinstance(ex, ScopeError) else 'invalid_input_or_local_source'
        print(json.dumps({'status': 'blocked', 'reason': code}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
