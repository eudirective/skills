#!/usr/bin/env python3
"""Synthetic contract and binding tests for issue source preflight."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import contract_validate
import issue_source_preflight as preflight


OWNER = {
    "family": "core_source",
    "owner_id": "eu-source-pack-0.6.1",
    "jurisdiction": "EU",
    "role": "common_eu",
    "source_pack_sha256": "a" * 64,
}


def artifacts():
    plan = {
        "research_id": "RCH-P0-EU",
        "tasks": [{"task_id": "RQT-P0-EU", "owner": copy.deepcopy(OWNER)}],
    }
    bundle = {
        "tasks": [{"task_id": "RQT-P0-EU", "status": "complete", "search_log": [{"query": "abstract query"}]}],
        "findings": [{
            "finding_id": "RFN-P0-EU", "task_id": "RQT-P0-EU",
            "evidence_ids": ["REV-P0-EU"], "counterevidence_ids": [],
        }],
        "evidence": [{
            "evidence_id": "REV-P0-EU", "task_id": "RQT-P0-EU", "relation": "supports",
            "source": {
                "record_kind": "registered_source", "source_id": "eu:32004l0038",
                "owner": copy.deepcopy(OWNER), "content_sha256": "b" * 64,
            },
        }],
        "claims": [{
            "claim_id": "RCL-P0-EU", "finding_ids": ["RFN-P0-EU"],
            "counterevidence_ids": [],
        }],
    }
    issue = {
        "issue_id": "ISS-P0-EU",
        "consultation_issue_ref": "r_aaaaaaaaaaaa0002",
        "consultation_scope_ref": "r_aaaaaaaaaaaa0003",
        "matter_issue_ref": "ISS-MAT-P0-EU",
        "task_id": "RQT-P0-EU",
        "claim_ids": ["RCL-P0-EU"],
        "question": "Abstract EU source applicability",
        "owner": copy.deepcopy(OWNER),
        "required_source_classes": ["eu_binding_law"],
        "sources": [{
            "source_ref": "eu:32004l0038", "record_kind": "registered_source",
            "source_class": "eu_binding_law", "acceptance_state": "registered_record",
            "currentness": "reviewed_current", "source_date": None,
            "evidence_ids": ["REV-P0-EU"], "scope_note": "Abstract scope.",
            "exceptions_note": "Exceptions reviewed.",
        }],
        "scope_review": "reviewed",
        "exceptions_review": "reviewed",
        "counterauthority_review": "searched_none_reported",
        "counterauthority_evidence_ids": [],
        "review_provenance": "human_review",
        "reviewed_at": "2026-10-22T10:00:00Z",
        "gap_disposition": "accounted_for_review",
        "gap_reason": "The required abstract source review was completed.",
    }
    preflight_record = {
        "contract_version": "0.3.0",
        "preflight_id": "r_aaaaaaaaaaaa0001",
        "research_id": "RCH-P0-EU",
        "coverage_claim": "accounted_for_review",
        "issues": [issue],
    }
    return plan, bundle, preflight_record


class IssueSourcePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fm-preflight-test-")
        self.root = Path(self.temp.name)
        self.plan, self.bundle, self.record = artifacts()
        self.plan_path = self.root / "plan.json"
        self.bundle_path = self.root / "bundle.json"
        self.preflight_path = self.root / "preflight.json"
        self.write_artifacts()

    def tearDown(self):
        self.temp.cleanup()

    def write_artifacts(self):
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        self.bundle_path.write_text(json.dumps(self.bundle), encoding="utf-8")
        self.preflight_path.write_text(json.dumps(self.record), encoding="utf-8")

    def validate(self):
        with patch.object(preflight, "validate_research", return_value={"status": "valid"}), \
                patch.object(preflight, "_record_status", return_value=(True, None)):
            return preflight.validate_source_preflight(
                self.preflight_path, self.plan_path, self.bundle_path
            )

    def test_v03_binds_owner_task_and_required_classes_to_consultation_issue(self):
        contract_validate.validate_obj("issue-source-preflight", self.record)
        report = self.validate()
        self.assertEqual(report["status"], "accounted_for_review")
        self.assertEqual(report["contract_version"], "0.3.0")
        self.assertEqual(report["issues"][0]["consultation_issue_ref"], "r_aaaaaaaaaaaa0002")
        self.assertEqual(report["issues"][0]["consultation_scope_ref"], "r_aaaaaaaaaaaa0003")
        self.assertEqual(report["issues"][0]["owner_id"], OWNER["owner_id"])
        self.assertEqual(report["issues"][0]["required_source_classes"], ["eu_binding_law"])

    def test_v03_requires_consultation_issue_and_scope_references(self):
        invalid = copy.deepcopy(self.record)
        del invalid["issues"][0]["consultation_issue_ref"]
        with self.assertRaises(contract_validate.ContractError):
            contract_validate.validate_obj("issue-source-preflight", invalid)

    def test_v03_rejects_empty_required_source_class_list(self):
        invalid = copy.deepcopy(self.record)
        invalid["issues"][0]["required_source_classes"] = []
        with self.assertRaises(contract_validate.ContractError):
            contract_validate.validate_obj("issue-source-preflight", invalid)

    def test_duplicate_consultation_issue_scope_owner_binding_is_rejected(self):
        duplicate = copy.deepcopy(self.record["issues"][0])
        duplicate["issue_id"] = "ISS-P0-EU-DUP"
        self.record["issues"].append(duplicate)
        self.write_artifacts()
        with patch.object(preflight, "validate_research", return_value={"status": "valid"}), \
                patch.object(preflight, "_record_status", return_value=(True, None)):
            with self.assertRaisesRegex(
                preflight.SourcePreflightError,
                "duplicate_consultation_issue_scope_owner_binding",
            ):
                preflight.validate_source_preflight(
                    self.preflight_path, self.plan_path, self.bundle_path
                )

    def test_false_accounted_for_claim_with_missing_source_class_is_rejected(self):
        self.record["issues"][0]["required_source_classes"].append("case_law")
        self.write_artifacts()
        with patch.object(preflight, "validate_research", return_value={"status": "valid"}), \
                patch.object(preflight, "_record_status", return_value=(True, None)):
            with self.assertRaisesRegex(
                preflight.SourcePreflightError,
                "issue_claimed_accounted_with_open_requirements",
            ):
                preflight.validate_source_preflight(
                    self.preflight_path, self.plan_path, self.bundle_path
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
