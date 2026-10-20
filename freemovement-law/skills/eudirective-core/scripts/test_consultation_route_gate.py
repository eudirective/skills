#!/usr/bin/env python3
"""Synthetic regression tests for the route gate and local binding wrapper."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parents[2]
ROUTE_GATE = HERE / "consultation_route_gate.py"
RELEASE_GATE = HERE / "consultation_release_gate.py"


def make_receipt(*, coverage="comprehensive"):
    ref = "r_0000000000000001"
    operations = [
        {"operation_id": operation, "applicability": "required", "status": "completed", "evidence_refs": [ref]}
        for operation in (
            "route_classification", "c23_guidance", "c27_reconciliation",
            "attack_angle_screen", "requested_output",
        )
    ]
    return {
        "schema_version": "0.1.0",
        "route_ref": "r_0000000000000002",
        "request_kind": "applicant_guidance",
        "classification": {
            name: {"state": "recorded", "evidence_ref": ref}
            for name in ("jurisdictions_by_role", "proceedings_and_stages", "legal_questions", "urgency", "requested_output")
        },
        "conditional_review": {"status": "reviewed", "evidence_ref": ref},
        "operations": operations,
        "c27_checks": [{
            "scope_ref": "r_0000000000000003",
            "record": {
                "check_id": "case_intake.proceedings_identified",
                "status": "assessed",
                "method": "model_review",
                "reason": "scope_reviewed",
                "evidence_refs": [ref],
                "source_refs": [],
            },
        }],
        "evidence": [{"evidence_ref": ref, "kind": "conversation_record"}],
        "research_artifacts": [],
        "module_pairs": [],
        "coverage_claim": coverage,
    }


def add_declared_issue(receipt, *, disposition="answered_supported", routed_checks=False):
    scope_ref = receipt["c27_checks"][0]["scope_ref"]
    evidence_ref = receipt["evidence"][0]["evidence_ref"]
    receipt["issues"] = [{
        "issue_ref": "r_0000000000000008",
        "scope_ref": scope_ref,
        "signal_ids": ["external_service_provider_used"],
        "disposition": disposition,
        "evidence_ref": evidence_ref,
    }]
    if routed_checks:
        template = receipt["c27_checks"][0]
        for check_id in (
            "access.service_provider_accountability",
            "access.direct_access",
            "authority.staff_responsibility",
        ):
            record = json.loads(json.dumps(template))
            record["record"]["check_id"] = check_id
            receipt["c27_checks"].append(record)


class RouteGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fm-route-test-")
        self.root = Path(self.temp.name)
        self.receipt_path = self.root / "receipt.json"
        self.write_receipt(make_receipt())

    def tearDown(self):
        self.temp.cleanup()

    def write_receipt(self, receipt):
        self.receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")

    def run_gate(self, path=None):
        return subprocess.run(
            [sys.executable, str(ROUTE_GATE), str(path or self.receipt_path)],
            cwd=PLUGIN_ROOT, capture_output=True, text=True, check=False,
        )

    def run_release(self, command, receipt=None, answer=None, binding=None):
        return subprocess.run(
            [sys.executable, str(RELEASE_GATE), command,
             "--receipt", str(receipt or self.receipt_path),
             "--answer", str(answer), "--binding", str(binding)],
            cwd=PLUGIN_ROOT, capture_output=True, check=False,
        )

    def test_complete_synthetic_declared_plan_is_structurally_closed(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "structurally_closed_declared_plan")

    def test_open_operation_is_reported_for_partial_and_rejects_comprehensive(self):
        receipt = make_receipt(coverage="partial")
        receipt["operations"][1].update(status="partial", reason_code="other_recorded")
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "valid_partial_route")
        self.assertTrue(any("operation:c23_guidance:partial" in item for item in report["outstanding"]))

        receipt["coverage_claim"] = "comprehensive"
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["status"], "rejected_comprehensive_claim")

    def test_missing_mandatory_operation_blocks_comprehensive_claim(self):
        receipt = make_receipt()
        receipt["operations"] = [item for item in receipt["operations"] if item["operation_id"] != "attack_angle_screen"]
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("required_operation_missing:attack_angle_screen", json.loads(result.stdout)["outstanding"])

    def test_declared_issue_requires_routed_checks_in_its_scope(self):
        receipt = make_receipt()
        add_declared_issue(receipt)
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 3, result.stderr)
        outstanding = json.loads(result.stdout)["outstanding"]
        self.assertIn(
            "issue:r_0000000000000008:c27_required_check_missing:access.direct_access",
            outstanding,
        )

    def test_declared_issue_with_routed_checks_is_structurally_closed(self):
        receipt = make_receipt()
        add_declared_issue(receipt, routed_checks=True)
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "structurally_closed_declared_plan")

    def test_source_or_fact_missing_issue_blocks_comprehensive_claim(self):
        receipt = make_receipt()
        add_declared_issue(receipt, disposition="source_missing", routed_checks=True)
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn(
            "issue:r_0000000000000008:disposition:source_missing",
            json.loads(result.stdout)["outstanding"],
        )

    def test_legacy_receipt_without_issue_records_remains_valid(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "structurally_closed_declared_plan")

    def test_unknown_c27_check_id_is_rejected(self):
        receipt = make_receipt()
        receipt["c27_checks"][0]["record"]["check_id"] = "made_up.check"
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown_check", result.stderr)

    def test_unsupported_c27_status_method_pair_is_rejected(self):
        receipt = make_receipt()
        receipt["c27_checks"][0]["record"].update(status="assessed", method="none")
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("assessed_without_method", result.stderr)

    def test_duplicate_c27_check_record_is_rejected(self):
        receipt = make_receipt()
        receipt["c27_checks"].append(json.loads(json.dumps(receipt["c27_checks"][0])))
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("c27_check_duplicate", result.stderr)

    def test_missing_evidence_index_entry_is_rejected(self):
        receipt = make_receipt()
        receipt["operations"][0]["evidence_refs"] = ["r_0000000000000099"]
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("evidence_reference_dangling", result.stderr)

    def test_artifact_escape_and_changed_digest_are_rejected(self):
        artifact = self.root / "artifact.txt"
        artifact.write_text("synthetic artifact", encoding="utf-8")
        ref = "r_0000000000000010"
        receipt = make_receipt(coverage="partial")
        receipt["evidence"].append({
            "evidence_ref": ref, "kind": "local_artifact", "artifact_path": "artifact.txt",
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        })
        self.write_receipt(receipt)
        artifact.write_text("changed", encoding="utf-8")
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("evidence_digest_mismatch", result.stderr)

        receipt["evidence"][-1]["artifact_path"] = "../outside.txt"
        self.write_receipt(receipt)
        artifact.write_text("synthetic artifact", encoding="utf-8")
        receipt["evidence"][-1]["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("path_outside_allowed_root", result.stderr)

    def test_failed_research_validator_cannot_be_declared_verified(self):
        receipt = make_receipt()
        receipt["request_kind"] = "source_research"
        receipt["operations"] = [
            {"operation_id": "route_classification", "applicability": "required", "status": "completed", "evidence_refs": ["r_0000000000000001"]},
            {"operation_id": "research_gate", "applicability": "required", "status": "completed", "evidence_refs": ["r_0000000000000004"]},
            {"operation_id": "requested_output", "applicability": "required", "status": "completed", "evidence_refs": ["r_0000000000000001"]},
        ]
        receipt["research_artifacts"] = [{"research_ref": "r_0000000000000005", "plan_path": "plan.json", "bundle_path": "bundle.json"}]
        receipt["evidence"].append({"evidence_ref": "r_0000000000000004", "kind": "research_gate", "subject_ref": "r_0000000000000005"})
        (self.root / "plan.json").write_text("{}", encoding="utf-8")
        (self.root / "bundle.json").write_text("{}", encoding="utf-8")
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("evidence_research_report_unverified", result.stderr)

    def test_nonconformant_module_pair_is_not_accepted_as_evidence(self):
        receipt = make_receipt()
        pair_ref = "r_0000000000000006"
        receipt["module_pairs"] = [{
            "pair_ref": pair_ref,
            "manifest_path": "skills/eudirective-core/README.md",
            "export_path": "skills/eudirective-core/README.md",
        }]
        receipt["operations"].append({
            "operation_id": "c3_module_pair_conformance", "applicability": "required",
            "status": "completed", "evidence_refs": ["r_0000000000000007"],
        })
        receipt["evidence"].append({
            "evidence_ref": "r_0000000000000007", "kind": "module_conformance", "subject_ref": pair_ref,
        })
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("evidence_module_report_unverified", result.stderr)

    def test_failed_conditional_review_blocks_comprehensive_claim(self):
        receipt = make_receipt()
        receipt["conditional_review"]["status"] = "incomplete"
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 3)
        self.assertIn("conditional_workflow_review:incomplete", json.loads(result.stdout)["outstanding"])

    def test_changed_local_answer_and_receipt_cannot_reuse_binding(self):
        receipt = make_receipt(coverage="partial")
        receipt["operations"][1].update(status="partial", reason_code="other_recorded")
        self.write_receipt(receipt)
        answer = self.root / "answer.md"
        answer.write_bytes(b"Synthetic answer\n")
        binding = self.root / "binding.json"

        prepared = self.run_release("prepare", answer=answer, binding=binding)
        self.assertEqual(prepared.returncode, 0, prepared.stderr.decode())
        released = self.run_release("release", answer=answer, binding=binding)
        self.assertEqual(released.returncode, 0, released.stderr.decode())
        self.assertEqual(released.stdout, b"Synthetic answer\n")

        answer.write_bytes(b"Changed synthetic answer\n")
        changed_answer = self.run_release("release", answer=answer, binding=binding)
        self.assertEqual(changed_answer.returncode, 2)
        self.assertEqual(changed_answer.stdout, b"")

        answer.write_bytes(b"Synthetic answer\n")
        receipt["classification"]["urgency"]["state"] = "unknown"
        self.write_receipt(receipt)
        changed_receipt = self.run_release("release", answer=answer, binding=binding)
        self.assertEqual(changed_receipt.returncode, 2)
        self.assertEqual(changed_receipt.stdout, b"")


if __name__ == "__main__":
    unittest.main(verbosity=2)
