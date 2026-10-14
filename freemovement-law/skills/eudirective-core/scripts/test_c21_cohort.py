#!/usr/bin/env python3
"""C21 fixed eight-synthetic-plan remedy cohort test; no release safety claim."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import c21_cohort as cohort
import c21_privacy as privacy
from contract_validate import ContractError, digest_obj, load_json, validate_obj

ROOT = Path(__file__).resolve().parents[1]


class C21CohortTests(unittest.TestCase):
    def test_counts_and_minimum_cohort(self):
        view=cohort.view_from_enrolled_fixtures()
        self.assertEqual(view['cohort_size'],8)
        self.assertEqual(view['minimum_visible_cell'],3)
        self.assertTrue(all(3<=v<=8 for v in view['remedy_category_case_counts'].values()))
        # This confirms actual cohort variation, unlike identical single-record previews.
        self.assertGreater(len(set(view['remedy_category_case_counts'].values())),1)
        self.assertFalse(view['external_disclosure_authorized'])
        self.assertTrue(view['human_review_required'])
        self.assertFalse(view['private_data_enabled'])
        validate_obj('c21-cohort-view',view)
        self.assertNotIn('L1',json.dumps(view))
        self.assertNotIn('source_refs',json.dumps(view))
        self.assertNotIn('correspondence_drafts',json.dumps(view))

    def test_no_differencing_subset_or_freeform_input_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/c21_cohort.py'),
                        'preview','--output-dir',str(Path(tmp)/'out'),
                        '--case','L1'],capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertFalse((Path(tmp)/'out').exists())
            self.assertNotIn('L1',proc.stdout)

    def test_altered_enrolled_fixture_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            orig=cohort.FIXTURES
            testdir=Path(td)
            try:
                for name in cohort.CASES:
                    path=orig/f'fictional-c17-plan-{name}.json'
                    (testdir/path.name).write_bytes(path.read_bytes())
                cohort.FIXTURES=testdir
                path=testdir/'fictional-c17-plan-L5.json'
                doc=load_json(path)
                doc['review_facts']=['made-up-canary']
                path.write_text(json.dumps(doc))
                with self.assertRaises(privacy.PrivacyError):
                    cohort.view_from_enrolled_fixtures()
                path.unlink()
                with self.assertRaises(privacy.PrivacyError):
                    cohort.view_from_enrolled_fixtures()
            finally:
                cohort.FIXTURES=orig

    def test_fixed_cohort_independent_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'new'
            cmd=[sys.executable,str(ROOT/'scripts/c21_cohort.py')]
            p=subprocess.run(cmd+['preview','--output-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            p=subprocess.run(cmd+['verify','--output-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            preview=load_json(out/'cohort-summary.json')
            receipt=load_json(out/'cohort-receipt.json')
            self.assertEqual(receipt['summary_sha256'],digest_obj(preview))
            self.assertFalse(preview['external_disclosure_authorized'])
            self.assertNotIn('L1',(out/'cohort-summary.json').read_text())
            d=dict(preview)
            d['remedy_category_case_counts']['supervisory_complaint']=8
            (out/'cohort-summary.json').write_text(json.dumps(d))
            p=subprocess.run(cmd+['verify','--output-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,2)
            self.assertIn('synthetic_cohort_boundary_failure',p.stderr)

    def test_repeat_cohort_outputs_identical(self):
        first=cohort.view_from_enrolled_fixtures()
        second=cohort.view_from_enrolled_fixtures()
        self.assertEqual(first,second)
        self.assertEqual(cohort.receipt_for(first),cohort.receipt_for(second))


if __name__=='__main__':
    unittest.main(verbosity=2)
