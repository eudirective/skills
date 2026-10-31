#!/usr/bin/env python3
"""Synthetic C27, strategy, and exact local-release regression cases."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from consultation_route_gate import RouteGateError, check_strategy_assessment, validate_route
from consultation_release_gate import ReleaseBindingError, controlled_release
from test_consultation_v09 import TRIGGERS, v08_receipt


class C27AndStrategyTests(unittest.TestCase):
    def validate(self, receipt):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            return validate_route(path)

    def test_selected_unassessed_check_stays_open_and_is_displayed(self):
        receipt = v08_receipt()
        check = receipt["c27_checks"][0]["record"]
        check.update(status="not_checked", method="none", reason="not_attempted", evidence_refs=[], source_refs=[])
        result = self.validate(receipt)
        self.assertTrue(any(check["check_id"] in item and item.endswith(":not_checked") for item in result["outstanding"]))
        self.assertTrue(any(f"`{check['check_id']}` · not checked · none" in line for line in result["dashboard_preview"].splitlines()))

    def test_missing_issue_check_is_individually_reported(self):
        receipt = v08_receipt()
        check = receipt["c27_checks"].pop(0)
        receipt["issues"][0]["c27_assessment_refs"].remove(check["assessment_ref"])
        result = self.validate(receipt)
        check_id = check["record"]["check_id"]
        self.assertTrue(any(f"c27_required_check_missing:{check_id}" in item for item in result["outstanding"]))
        self.assertIn(f"Required C27 check for this issue — `{check_id}`:** Missing:", result["dashboard_preview"])

    def test_preventive_strategy_does_not_require_refusal(self):
        receipt = v08_receipt()
        adverse = next(item for item in receipt["strategy_assessment"]["trigger_reviews"] if item["trigger_id"] == "adverse_decision_or_denial")
        self.assertEqual(adverse["status"], "not_triggered")
        evidence = {item["evidence_ref"]: item for item in receipt["evidence"]}
        self.assertEqual(check_strategy_assessment(receipt, evidence, []), "full")
        self.assertTrue(receipt["strategy_assessment"]["first_step"])

    def test_no_action_requires_specific_rationale(self):
        receipt = {
            "schema_version": "0.8.0", "request_kind": "applicant_guidance", "issues": [],
            "strategy_assessment": {
                "mode": "not_triggered", "issue_refs": [],
                "summary": "All five strategy categories were assessed and no additional action is indicated.",
                "no_trigger_reason": "No adverse decision, urgent timing concern, access problem, preventive opportunity or strategy request is recorded.",
                "trigger_reviews": [{"trigger_id": trigger, "status": "not_triggered", "reason": "The available recorded evidence does not support this strategy trigger.", "evidence_refs": [], "issue_refs": []} for trigger in TRIGGERS],
            },
        }
        self.assertEqual(check_strategy_assessment(receipt, {}, []), "not_triggered")
        receipt["strategy_assessment"]["no_trigger_reason"] = "Not enough information."
        with self.assertRaisesRegex(RouteGateError, "no_trigger_reason_too_generic"):
            check_strategy_assessment(receipt, {}, [])


class ControlledReleaseTests(unittest.TestCase):
    def test_exact_output_and_rejection_leave_candidate_files_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path, answer_path = root / "receipt.json", root / "answer.md"
            receipt_path.write_text(json.dumps(v08_receipt()), encoding="utf-8")
            receipt_bytes = receipt_path.read_bytes()
            preview = validate_route(receipt_path)["dashboard_preview"]
            valid = ("Synthetic answer: café.\n\n" + preview).encode("utf-8")
            answer_path.write_bytes(valid)
            self.assertEqual(controlled_release(receipt_path, answer_path), valid)
            self.assertEqual(receipt_path.read_bytes(), receipt_bytes)
            self.assertEqual(answer_path.read_bytes(), valid)
            for answer in (
                "Answer\n\n## freemovement-law — Case Review\n\nTruncated board",
                "Answer\n\n## Consultation dashboard\n\nMalformed table\n| incomplete",
                "Answer\n\n" + preview + "\n\n" + preview,
            ):
                with self.subTest(answer=answer[:50]):
                    source = answer.encode("utf-8")
                    answer_path.write_bytes(source)
                    with self.assertRaises(ReleaseBindingError):
                        controlled_release(receipt_path, answer_path)
                    self.assertEqual(receipt_path.read_bytes(), receipt_bytes)
                    self.assertEqual(answer_path.read_bytes(), source)

    def test_appended_board_preserves_exact_original_answer_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path, answer_path = root / "receipt.json", root / "answer.md"
            receipt_path.write_text(json.dumps(v08_receipt()), encoding="utf-8")
            original = "A synthetic response with spaces.  \n\n".encode("utf-8")
            answer_path.write_bytes(original)
            result = controlled_release(receipt_path, answer_path)
            self.assertTrue(result.startswith(original))
            self.assertEqual(answer_path.read_bytes(), original)
            self.assertIn(b"Consultation Review", result)


if __name__ == "__main__":
    unittest.main()
