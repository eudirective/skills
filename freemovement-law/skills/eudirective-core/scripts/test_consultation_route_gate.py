#!/usr/bin/env python3
"""Synthetic regression tests for the route gate and local binding wrapper."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parents[2]
ROUTE_GATE = HERE / "consultation_route_gate.py"
RELEASE_GATE = HERE / "consultation_release_gate.py"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import consultation_issue_selection as issue_selector
import consultation_release_gate as release_gate


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


def make_controlled_receipt(*, coverage="partial", signal_id="external_service_provider_used"):
    receipt = make_receipt(coverage=coverage)
    receipt["schema_version"] = "0.4.0"
    receipt["invocation"] = {
        "state": "explicit", "basis": "visible_plugin_marker", "dashboard_requested": True,
    }
    receipt["source_ledger"] = {
        "response_tracking": "unavailable", "conversation_tracking": "unavailable", "sources": [],
    }
    receipt["operations"].extend([
        {
            "operation_id": "research_gate", "applicability": "required", "status": "not_checked",
            "reason_code": "not_attempted", "evidence_refs": [],
        },
        {
            "operation_id": "source_preflight", "applicability": "required", "status": "not_checked",
            "reason_code": "not_attempted", "evidence_refs": [],
        },
    ])
    issue_ref = "r_0000000000000008"
    scope_ref = receipt["c27_checks"][0]["scope_ref"]
    evidence_ref = receipt["evidence"][0]["evidence_ref"]
    requirements = issue_selector.select_issue_requirements([signal_id])
    receipt["issues"] = [{
        "issue_ref": issue_ref,
        "scope_ref": scope_ref,
        "signal_ids": [signal_id],
        "disposition": "answered_conditionally",
        "evidence_ref": evidence_ref,
        "source_obligations": [
            {
                "owner_id": owner_id,
                "required_source_classes": ["procedural_rule"],
                "status": "unavailable",
                "evidence_ref": evidence_ref,
                "reason_code": "source_unavailable",
            }
            for owner_id in requirements["source_owner_ids"]
        ],
        "attack_angle_reviews": [
            {
                **topic,
                "outcome": "unresolved",
                "evidence_ref": evidence_ref,
            }
            for topic in requirements["attack_angle_topics"]
        ],
    }]
    receipt["dashboard"] = {
        "assessment_status": "partial",
        "issue_summaries": [{
            "issue_ref": issue_ref,
            "title": "Provider participation",
            "missing": "Official procedure and scope review",
            "effect": "The answer remains qualified.",
        }],
        "module_use": [{
            "module_id": "eudirective-core", "role": "consultation routing and EU/common legal analysis",
            "availability": "available", "response_use": "used", "conversation_use": "used_earlier",
            "conformance": "not_applicable", "reason": "Core consultation guidance used this response.",
        }],
    }
    return receipt


def make_strict_controlled_receipt(*, coverage="partial", signal_id="external_service_provider_used"):
    """Upgrade a fictional receipt to strict 0.5 with open, explicit evidence states."""
    receipt = make_controlled_receipt(coverage=coverage, signal_id=signal_id)
    receipt["schema_version"] = "0.5.0"
    receipt["invocation"]["material_change"] = False
    issue = receipt["issues"][0]
    requirements = issue_selector.select_issue_requirements(issue["signal_ids"])
    issue["conditional_closure"] = {
        "status": "predicate_open" if issue["disposition"] == "answered_conditionally" else "not_conditional",
        "evidence_refs": [issue["evidence_ref"]] if issue["disposition"] == "answered_conditionally" else [],
    }
    issue["source_owner_exclusions"] = [{
        "owner_id": owner_id,
        "reason_code": "no_source_class_predicate_triggered",
        "evidence_ref": issue["evidence_ref"],
    } for owner_id in requirements["source_owner_exclusions"]]
    issue["source_obligations"] = [{
        "owner_id": owner_id,
        "required_source_classes": requirement["required_classes"],
        "policy_excluded_source_classes": requirement["excluded_classes"],
        "status": "unavailable",
        "evidence_ref": issue["evidence_ref"],
        "reason_code": "source_unavailable",
    } for owner_id, requirement in requirements["source_class_requirements"].items()
        if requirement["required_classes"]]
    issue["attack_angle_reviews"] = [{
        **topic,
        "outcome": "unresolved",
        "evidence_ref": issue["evidence_ref"],
        "screening": {
            "reason_code": "evidence_missing" if topic["adverse_predicate_ids"] else "predicate_unmapped",
            "predicate_states": [{
                "signal_id": signal_id,
                "state": "present" if signal_id in issue["signal_ids"] else "absent",
                "evidence_ref": issue["evidence_ref"],
            } for signal_id in sorted(
                set(topic["trigger_any_signal_ids"]) | set(topic["trigger_all_signal_ids"])
            )],
            "adverse_predicate_states": [{
                "predicate_id": predicate_id,
                "state": "unknown",
                "evidence_ref": issue["evidence_ref"],
            } for predicate_id in topic["adverse_predicate_ids"]],
        },
    } for topic in requirements["attack_angle_topics"]]

    template = receipt["c27_checks"][0]["record"]
    c27_rows = []
    assessment_refs = []
    check_ids = set(requirements["check_ids"])
    check_ids.add(template["check_id"])
    for index, check_id in enumerate(sorted(check_ids), start=1):
        assessment_ref = f"r_{0x1000 + index:016x}"
        assessment_refs.append(assessment_ref)
        c27_rows.append({
            "scope_ref": issue["scope_ref"],
            "assessment_ref": assessment_ref,
            "binding_kind": "issue_specific",
            "bound_issue_refs": [issue["issue_ref"]],
            "record": {**template, "check_id": check_id},
        })
    receipt["c27_checks"] = c27_rows
    issue["c27_assessment_refs"] = assessment_refs
    abstract_state = {
        "manifest_version": "0.1.0",
        "issues": [{
            "issue_ref": issue["issue_ref"],
            "scope_ref": issue["scope_ref"],
            "signal_states": [{
                "signal_id": signal_id, "state": "present",
            } for signal_id in issue["signal_ids"]],
        }],
    }
    receipt["revision_control"] = {
        "change_detection_status": "compared",
        "current_abstract_state": abstract_state,
        "previous_abstract_state": json.loads(json.dumps(abstract_state)),
        "added_issue_refs": [],
        "removed_issue_refs": [],
        "changed_issue_refs": [],
        "affected_scope_refs": [],
        "reassessed_scope_refs": [],
        "removed_issue_reviews": [],
    }
    return receipt


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

    def run_controlled_release(self, receipt=None, answer=None):
        return subprocess.run(
            [sys.executable, str(RELEASE_GATE), "controlled-release",
             "--receipt", str(receipt or self.receipt_path), "--answer", str(answer)],
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

    def test_v04_issue_owner_and_attack_coverage_are_required_for_comprehensive(self):
        receipt = make_controlled_receipt(coverage="comprehensive")
        receipt["source_ledger"].update(
            response_tracking="model_declared", conversation_tracking="model_declared"
        )
        receipt["issues"][0]["source_obligations"] = receipt["issues"][0]["source_obligations"][:-1]
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 3, result.stderr)
        outstanding = json.loads(result.stdout)["outstanding"]
        self.assertTrue(any("source_owner_obligation_missing" in item for item in outstanding))
        self.assertTrue(any("source_owner_status" in item for item in outstanding))
        self.assertTrue(any("attack_angle_topic_unresolved" in item for item in outstanding))

    def test_controlled_release_withholds_comprehensive_answer_with_open_work(self):
        receipt = make_strict_controlled_receipt(coverage="comprehensive")
        receipt["source_ledger"].update(
            response_tracking="model_declared", conversation_tracking="model_declared"
        )
        self.write_receipt(receipt)
        answer = self.root / "answer.md"
        answer.write_text("Synthetic answer that overclaims coverage.\n", encoding="utf-8")

        released = self.run_controlled_release(answer=answer)

        self.assertEqual(released.returncode, 2)
        self.assertEqual(released.stdout, b"")
        self.assertIn(b"comprehensive_claim_has_outstanding_work", released.stderr)

    def test_material_change_invalidates_scope_until_reassessment_is_declared(self):
        receipt = make_controlled_receipt(coverage="partial")
        scope_ref = receipt["issues"][0]["scope_ref"]
        receipt["revision_control"] = {
            "affected_scope_refs": [scope_ref], "reassessed_scope_refs": [],
        }
        self.write_receipt(receipt)
        mismatched = self.run_gate()
        self.assertEqual(mismatched.returncode, 2)
        self.assertIn("revision_control_without_material_change", mismatched.stderr)

        receipt.pop("revision_control")
        receipt["evidence"][0]["record_scope"] = "prior_conversation"
        receipt["invocation"]["material_change"] = True
        self.write_receipt(receipt)
        malformed = self.run_gate()
        self.assertEqual(malformed.returncode, 2)
        self.assertIn("revision_control", malformed.stderr)

        receipt["revision_control"] = {
            "affected_scope_refs": [scope_ref], "reassessed_scope_refs": [],
        }
        self.write_receipt(receipt)
        pending = self.run_gate()
        self.assertEqual(pending.returncode, 0, pending.stderr)
        self.assertIn(
            f"material_change_scope_reassessment_pending:{scope_ref}",
            json.loads(pending.stdout)["outstanding"],
        )

        receipt["revision_control"]["reassessed_scope_refs"] = [scope_ref]
        self.write_receipt(receipt)
        reassessed = self.run_gate()
        self.assertEqual(reassessed.returncode, 0, reassessed.stderr)
        outstanding = json.loads(reassessed.stdout)["outstanding"]
        self.assertNotIn(f"material_change_scope_reassessment_pending:{scope_ref}", outstanding)
        self.assertTrue(any("material_change_issue_evidence_not_current" in item for item in outstanding))

        receipt["evidence"][0]["record_scope"] = "current_response"
        self.write_receipt(receipt)
        refreshed = self.run_gate()
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        self.assertFalse(any(
            item.startswith("material_change_")
            for item in json.loads(refreshed.stdout)["outstanding"]
        ))

    def test_controlled_release_emits_only_the_exact_checked_partial_answer(self):
        receipt = make_strict_controlled_receipt(coverage="partial")
        self.write_receipt(receipt)
        gate = self.run_gate()
        self.assertEqual(gate.returncode, 0, gate.stderr)
        preview = json.loads(gate.stdout)["dashboard_preview"]
        answer = self.root / "answer.md"
        answer.write_text("Synthetic summary\n\n" + preview, encoding="utf-8")
        released = self.run_controlled_release(answer=answer)
        self.assertEqual(released.returncode, 0, released.stderr.decode())
        self.assertEqual(released.stdout, answer.read_bytes())

        answer.write_text("Changed synthetic summary\n", encoding="utf-8")
        rejected = self.run_controlled_release(answer=answer)
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(rejected.stdout, b"")

    def test_controlled_release_detects_answer_change_between_validation_passes(self):
        receipt = make_strict_controlled_receipt(coverage="partial")
        self.write_receipt(receipt)
        gate = self.run_gate()
        self.assertEqual(gate.returncode, 0, gate.stderr)
        preview = json.loads(gate.stdout)["dashboard_preview"]
        answer = self.root / "answer.md"
        answer.write_text("Synthetic summary\n\n" + preview, encoding="utf-8")
        original_validate = release_gate.validate_exact_receipt
        calls = 0

        def change_after_first_read(path):
            nonlocal calls
            calls += 1
            if calls == 2:
                answer.write_text("Changed during validation\n", encoding="utf-8")
            return original_validate(path)

        with patch.object(release_gate, "validate_exact_receipt", side_effect=change_after_first_read):
            with self.assertRaisesRegex(
                release_gate.ReleaseBindingError,
                "controlled_release_artifact_changed_during_validation",
            ):
                release_gate.controlled_release(self.receipt_path, answer)
        self.assertEqual(calls, 2)

    def test_controlled_release_rejects_legacy_receipt(self):
        answer = self.root / "answer.md"
        answer.write_text("Synthetic answer\n", encoding="utf-8")
        rejected = self.run_controlled_release(answer=answer)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn(b"controlled_release_requires_receipt_0_5_0", rejected.stderr)
        self.assertEqual(rejected.stdout, b"")

    def test_priority_pathway_is_bound_to_c27_checks_and_c5d_catalogue(self):
        receipt = make_controlled_receipt(signal_id="digital_only_access_requirement")
        pathway = next(
            item for item in receipt["issues"][0]["attack_angle_reviews"]
            if item.get("pathway_id") == "digital_only_access"
        )
        self.assertIn("access.digital_only", pathway["c27_check_ids"])
        self.assertEqual(pathway["coverage_pattern_ids"], ["core:attack:procedural-access-review"])
        self.write_receipt(receipt)
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn(
            "issue:r_0000000000000008:attack_pathway_metadata_independent_review_pending:digital_only_access",
            report["outstanding"],
        )
        self.assertIn("do not mean a synthetic C5d engine ran", report["dashboard_preview"])

        pathway["c27_check_ids"].remove("access.digital_only")
        self.write_receipt(receipt)
        rejected = self.run_gate()
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("issue_attack_pathway_binding_mismatch", rejected.stderr)

    def test_neutral_route_trigger_cannot_substitute_for_pathway_adverse_predicate(self):
        for adverse_state in ("absent", "unknown"):
            with self.subTest(adverse_state=adverse_state):
                receipt = make_strict_controlled_receipt(
                    signal_id="digital_only_access_requirement"
                )
                topic = next(
                    item for item in receipt["issues"][0]["attack_angle_reviews"]
                    if item.get("pathway_id") == "digital_only_access"
                )
                topic["outcome"] = "candidate_same_issue"
                topic["screening"]["reason_code"] = "candidate_assessed"
                for state in topic["screening"]["predicate_states"]:
                    state["state"] = "present"
                topic["screening"]["adverse_predicate_states"][0]["state"] = adverse_state
                self.write_receipt(receipt)
                rejected = self.run_gate()
                self.assertEqual(rejected.returncode, 2)
                self.assertIn("issue_attack_candidate_screen_unsupported", rejected.stderr)

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
        self.assertIn("path_component_not_allowed", result.stderr)

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
