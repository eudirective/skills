#!/usr/bin/env python3
"""Fiction-only deterministic reviewer question drafts; no send, no legal conclusion."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {f'L{x}' for x in range(1, 9)}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def build(case_id, case, c12, c13):
    if case_id not in ALLOWED or case.get('case_id') != 'CASE-C10-' + case_id or case.get('privacy_classification') != 'synthetic':
        raise ValueError('C17 requires an enrolled fictional case')
    if c12.get('conclusion') != 'not_determined' or c13.get('legal_violation_status') != 'not_determined':
        raise ValueError('legal disposition is forbidden')
    if c13.get('mode') != 'enrolled':
        raise ValueError('passage-grounded C13 enrollment is required')
    by_link = {x['assessment_id']: x for x in c13['rule_links']}
    if len(by_link) != len(c13['rule_links']):
        raise ValueError('duplicate rule links')
    questions = []
    for a in c12['assessments']:
        if a['status'] != 'supported_for_review':
            continue
        rid = a['assessment_id']
        link = by_link.get(rid)
        if not link or link['status'] != 'passage_anchored_for_review':
            continue
        if a.get('legal_violation_status') != 'not_determined' or not a.get('source_citations'):
            raise ValueError('rule lacks neutral status or provenance')
        citations = [{'source_id': c['source_id'], 'pinpoint_hint': c['pinpoint_hint'],
                      'assurance': c['source_assurance']} for c in a['source_citations']]
        questions.append({'rule_id': rid, 'topic': a['label'], 'citations_for_human_check': citations,
                          'factual_items_for_verification': [p['fact_key'] for p in a.get('supported_facts', [])],
                          'exception_questions': a.get('exception_questions', []),
                          'question': 'Please clarify the factual and procedural basis for the matter described as: ' + a['label'] + '.',
                          'legal_violation_status': 'not_determined'})
    unresolved = list(c12.get('unresolved', [])) + list(c13.get('unresolved', []))
    novel = [x for x in c12.get('novel_issues', []) if x.get('status') == 'novel_unassessed']
    artifact = {'milestone': 'C17', 'mode': 'fictional_review_only', 'case_id': case_id,
                'send_authorized': False, 'legal_violation_status': 'not_determined',
                'requires_human_review': True, 'verified_legal_merits': False,
                'source_assurance_warning': 'Local source pins do not prove completeness, currency, authenticity or legal interpretation.',
                'draft_type': 'neutral_authority_clarification_questions', 'questions': questions,
                'unresolved_items': unresolved, 'novel_unassessed': novel,
                'input_digests': {'case': digest(case), 'c12': digest(c12), 'c13': digest(c13)}}
    return artifact


def render(artifact):
    lines = ['# C17 fictional reviewer draft — ' + artifact['case_id'], '',
             '**NOT FOR SENDING. NOT LEGAL ADVICE.** Developer-authored fictional test material only.',
             'Source references and legal questions require independent human checking; no violation is determined.', '',
             '## Clarification questions (review only)', '']
    for idx, q in enumerate(artifact['questions'], 1):
        lines.extend([f'### {idx}. {q["topic"]}', '', q['question'], '',
                      'Rule ID: `' + q['rule_id'] + '`', '', 'Sources to verify:'])
        for cite in q['citations_for_human_check']:
            lines.append('- `' + cite['source_id'] + '` (' + cite['assurance'] + '): ' + cite['pinpoint_hint'])
        lines.append('')
        for exception in q['exception_questions']:
            lines.append('- Open question: ' + exception)
        lines.append('')
    lines += ['## Review blockers', '', f'- Unresolved items: {len(artifact["unresolved_items"])}',
              f'- Novel unassessed issues: {len(artifact["novel_unassessed"])}',
              '- Source currentness, legal merits, procedural remedy, recipient and filing deadlines are not verified.',
              '- Do not submit, send, or use personal applicant data.', '']
    return '\n'.join(lines)


def generate(case_number):
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    import test_c16_coverage as fixtures
    import c6_integration as c6
    import c7_trust_gate as trust
    case, elements, actors, context, pairs, extensions, ledger, documents = fixtures.load_case(case_number)
    trust.require_source_pack(fixtures.SOURCE)
    for role, obj in [('case', case), ('elements', elements), ('actors', actors),
                      ('c12_fact_ledger', ledger), ('c13_evidence_set', documents)]:
        trust.require_approved(role, obj)
    for extension in extensions:
        trust.require_approved('c12_rule_extension', extension)
    stages = c6.stage_outputs(case, elements, actors, None, context, fixtures.SOURCE,
                              pairs, extensions, ledger, documents)
    return build('L'+str(case_number), case, stages['c12'], stages['c13'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-dir', required=True, type=Path)
    ap.add_argument('--case', type=int, choices=range(1, 9), action='append')
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for case in args.case or range(1, 9):
        artifact = generate(case)
        name = 'L'+str(case)
        (args.output_dir / (name+'-c17.json')).write_text(json.dumps(artifact, indent=2, ensure_ascii=False)+'\n')
        (args.output_dir / (name+'-c17.md')).write_text(render(artifact))
        print(name, len(artifact['questions']), 'review questions')

if __name__ == '__main__':
    main()
