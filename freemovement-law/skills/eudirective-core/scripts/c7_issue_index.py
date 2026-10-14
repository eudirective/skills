#!/usr/bin/env python3
"""Lossless, replayable issue index for the C7 synthetic controlled analysis.

Every C5 unresolved/limitation entry is preserved with its full value, pointer
and stage digest. Registry gaps are enumerated rather than cut off at 16 items.
"""
import json

from contract_validate import digest_obj, validate_obj

INDEX_VERSION = '0.2.0'
STAGE_NAMES = ('topology', 'regimes', 'c5b', 'c5c', 'c5d', 'c11', 'c12', 'c13')


def build(stages, state):
    reference = state['reference_index']
    digests = {name: digest_obj(stages[name]) for name in STAGE_NAMES}
    digests['controller_reference_index'] = digest_obj(reference)
    items = []
    counts = {}

    def add(stage, kind, pointer, value):
        key = stage + ':' + kind
        counts[key] = counts.get(key, 0) + 1
        items.append({
            'issue_id': 'c7:issue:%05d' % (len(items) + 1),
            'stage': stage, 'category': kind, 'pointer': pointer,
            'stage_sha256': digests[stage], 'value_sha256': digest_obj(value),
            'value': value,
        })

    for name in STAGE_NAMES:
        data = stages[name]
        for category in ('unresolved', 'limitations'):
            for i, value in enumerate(data.get(category, [])):
                add(name, category, '/' + category + '/' + str(i), value)

    for i, value in enumerate(stages['c12']['novel_issues']):
        add('c12','novel_unassessed','/novel_issues/'+str(i),value)
    for i,value in enumerate(stages['c12']['unverified_evidence_records']):
        add('c12','unverified_evidence','/unverified_evidence_records/'+str(i),value)
    registry_fields = (
        ('source_refs', 'usable_source_ids'),
        ('rule_refs', 'rule_ids'),
        ('authority_refs', 'authority_ids'),
        ('route_refs', 'route_ids'),
    )
    absent = set()
    for angle in stages['c5d']['attack_angles']:
        if angle['assessment_status'] == 'blocked':
            continue
        for field, inventory in registry_fields:
            absent.update(set(angle[field]) - set(reference[inventory]))
        if angle['attack_angle_id'] not in reference['attack_angle_ids']:
            absent.add(angle['attack_angle_id'])
    for deadline in stages['c5c']['deadline_assessments']:
        absent.update(set(deadline['source_refs']) - set(reference['usable_source_ids']))
    for idx, ref in enumerate(sorted(absent)):
        add('controller_reference_index', 'unregistered_candidate_id', '/unregistered/' + str(idx), ref)

    out = {
        'index_version': INDEX_VERSION, 'case_id': state['case_id'], 'run_id': state['run_id'],
        'purpose': 'Complete synthetic review record; source-grounded legal conclusion not established',
        'source_stage_digests': digests, 'issues': items,
        'counts_by_stage_and_category': counts, 'issue_count': len(items),
    }
    validate_obj('c7-issue-index', out)
    return out


def render(index):
    lines = [
        '# Complete unresolved-issue index (C7)', '',
        'This is an exhaustive, *synthetic-only* index of C5/C11/C12/C13 unresolved/limitation records and controller-unregistered candidate identifiers.',
        'It is not an independent determination that an authority acted unlawfully.', '',
        'Case: `' + index['case_id'] + '`; run: `' + index['run_id'] + '`',
        'Issue count: **' + str(index['issue_count']) + '**', '',
        '## Counts by stage and category', '',
    ]
    if not index['counts_by_stage_and_category']:
        lines.append('No indexed unresolved records were supplied by the stages.')
    else:
        for key, count in sorted(index['counts_by_stage_and_category'].items()):
            lines.append('- `' + key + '`: ' + str(count))
    lines.extend(['', '## Source-stage digests', ''])
    for name, value in sorted(index['source_stage_digests'].items()):
        lines.append('- `' + name + '`: `' + value + '`')
    lines.extend(['', '## Every issue (no truncation)', ''])
    for item in index['issues']:
        lines.extend([
            '### ' + item['issue_id'], '',
            '- Stage: `' + item['stage'] + '`; kind: `' + item['category'] + '`; pointer: `' + item['pointer'] + '`',
            '- Value SHA-256: `' + item['value_sha256'] + '`', '',
            '```json', json.dumps(item['value'], ensure_ascii=False, sort_keys=True, indent=2), '```', '',
        ])
    return ('\n'.join(lines).rstrip() + '\n').encode('utf-8')
