#!/usr/bin/env python3
"""Deterministic national sidecar source and authority ownership checks.

Checks local data-only integrity, never legal accuracy or official currency.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT/'references'


def load(name):
    return json.loads((REF/name).read_text(encoding='utf-8'))


def errors(manifest, export, extension, catalog):
    problems = []
    module_id = manifest['module_id']
    prefix = export['id_namespace']
    if any(obj['module_id'] != module_id for obj in (export,)):
        problems.append('export_owner_mismatch')
    if extension['producer_module_id'] != module_id or catalog['owner_module_id'] != module_id:
        problems.append('sidecar_owner_mismatch')
    if (export['jurisdiction'] != manifest['jurisdiction'] or
        extension['jurisdiction'] != manifest['jurisdiction'] or
        catalog['jurisdiction'] != manifest['jurisdiction']):
        problems.append('jurisdiction_mismatch')
    if extension['bound_export_sha256'] != hashlib.sha256(json.dumps(
        export,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest():
        problems.append('export_binding_mismatch')
    rule_ids = {r['rule_id'] for r in extension['rules']}
    sources = {r['source_id'] for r in export['source_records']}
    authorities = {r['authority_id'] for r in export['authority_records']}
    if len(rule_ids)!=len(extension['rules']):
        problems.append('duplicate_rules')
    if len(sources)!=len(export['source_records']):
        problems.append('duplicate_sources')
    if len(authorities)!=len(export['authority_records']):
        problems.append('duplicate_authorities')
    for remedy in catalog['remedies']:
        if not (remedy['remedy_id'].startswith(prefix) and
                set(remedy['trigger_rule_ids']) <= rule_ids and
                set(remedy['source_refs']) <= sources and
                remedy['authority_ref'] in authorities):
            problems.append('foreign_or_unknown_remedy_references')
        if (remedy['send_authorized'] is not False or
            remedy['requires_human_review'] is not True or
            remedy['legal_violation_status'] != 'not_determined'):
            problems.append('unsafe_remedy_gate')
    for rule in extension['rules']:
        if not rule['rule_id'].startswith(prefix):
            problems.append('foreign_rule_prefix')
    return sorted(set(problems))


class SidecarIntegrity(unittest.TestCase):
    def setUp(self):
        self.m=load('module-manifest.json')
        self.e=load('module-export.json')
        self.x=load('c12-rule-extension.json')
        self.c=load('c17-remedy-catalog.json')

    def test_source_ownership_and_review_gates(self):
        self.assertEqual(errors(self.m,self.e,self.x,self.c),[])

    def test_tampered_export_binding_detected(self):
        altered=json.loads(json.dumps(self.e))
        altered['pack_version']='malicious'
        self.assertIn('export_binding_mismatch',errors(self.m,altered,self.x,self.c))

    def test_cross_country_source_or_rule_detected(self):
        altered=json.loads(json.dumps(self.c))
        altered['remedies'][0]['source_refs']=['foreign:src:dummy']
        self.assertIn('foreign_or_unknown_remedy_references',errors(self.m,self.e,self.x,altered))
        altered=json.loads(json.dumps(self.c))
        altered['remedies'][0]['trigger_rule_ids']=['foreign:c12:not-in-module']
        self.assertIn('foreign_or_unknown_remedy_references',errors(self.m,self.e,self.x,altered))

    def test_forbidden_approval_detected(self):
        altered=json.loads(json.dumps(self.c))
        altered['remedies'][0]['send_authorized']=True
        self.assertIn('unsafe_remedy_gate',errors(self.m,self.e,self.x,altered))

    def test_wrong_jurisdiction_and_owner_detected(self):
        altered=json.loads(json.dumps(self.c))
        altered['owner_module_id']='unrelated'
        self.assertIn('sidecar_owner_mismatch',errors(self.m,self.e,self.x,altered))
        altered=json.loads(json.dumps(self.c))
        altered['jurisdiction']='X'
        self.assertIn('jurisdiction_mismatch',errors(self.m,self.e,self.x,altered))


if __name__ == '__main__':
    unittest.main(verbosity=2)
