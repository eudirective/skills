#!/usr/bin/env python3
"""Synthetic regression cases for receipt 0.9 and controlled board release."""
import copy
import json
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
from test_consultation_route_gate import make_strict_controlled_receipt
from test_consultation_p0_integrated import make_research_records, RESEARCH_REF, PREFLIGHT_REF
from consultation_route_gate import validate_route, check_strategy_assessment, RouteGateError
from consultation_release_gate import repair_dashboard_once, controlled_release, ReleaseBindingError
from migrate_consultation_receipt import migrate_08_to_09, MigrationError
from contract_validate import validate_obj, ContractError

TRIGGERS = (
    "adverse_decision_or_denial",
    "urgent_deadline_or_clock",
    "procedural_access_or_lodgement_problem",
    "source_supported_preventive_opportunity",
    "user_requested_strategy",
)


def v08_receipt(*, mode: str = "full") -> dict:
    route = make_strict_controlled_receipt(
        coverage="partial", signal_id="pre_lodgement_access_obstruction"
    )
    issue = route["issues"][0]
    issue_ref = issue["issue_ref"]
    evidence_ref = issue["evidence_ref"]
    route["schema_version"] = "0.8.0"
    route["consultation_mode"] = mode
    route["dashboard"].pop("mode", None)
    scope_ref = issue["scope_ref"]
    route["proceedings"] = [{
        "scope_ref": scope_ref,
        "procedure_type": "ordinary_short_stay_visa",
        "evidence_ref": evidence_ref,
    }]
    for state_name in ("current_abstract_state", "previous_abstract_state"):
        for state_issue in route["revision_control"][state_name]["issues"]:
            state_issue["procedure_type"] = "ordinary_short_stay_visa"
    reviews = []
    for trigger_id in TRIGGERS:
        triggered = trigger_id == "procedural_access_or_lodgement_problem"
        reviews.append({
            "trigger_id": trigger_id,
            "status": "triggered" if triggered else "not_triggered",
            "reason": (
                "The recorded access obstruction supports an issue-specific procedural strategy review."
                if triggered else
                f"The recorded issues do not establish the {trigger_id.replace('_', ' ')} trigger."
            ),
            "evidence_refs": [evidence_ref] if triggered else [],
            "issue_refs": [issue_ref] if triggered else [],
        })
    route["strategy_assessment"] = {
        "mode": "full",
        "summary": "A targeted procedural step is supported by the recorded access obstruction and its evidence.",
        "trigger_reviews": reviews,
        "issue_refs": [issue_ref],
        "first_step": "Preserve the appointment record and ask the authority to confirm the available direct filing route.",
        "purpose": "This establishes whether the applicant can lodge directly and records any continuing barrier.",
        "reassess_when": "Reassess if the authority refuses direct filing, supplies a different route, or issues a written decision.",
        "alternatives_considered": ["targeted_clarification", "wait_or_no_extra_action"],
    }
    route["operations"].append({
        "operation_id": "consultation_finalisation",
        "applicability": "required",
        "status": "completed",
        "evidence_refs": [evidence_ref],
    })
    return route


class V09Tests(unittest.TestCase):
    def route(self):
        route = v08_receipt()
        route["schema_version"] = "0.9.0"
        route["strategy_assessment"].update(disposition="action", objective="Obtain effective access to lodging while preserving the applicant's procedural position.")
        names = {"research_gate": "research_review", "source_preflight": "source_review"}
        route["workflow_reviews"] = [{"review_id": names.get(item["operation_id"], item["operation_id"]), "status": "completed", "evidence_refs": [route["issues"][0]["evidence_ref"]]} for item in route["operations"]]
        for review in route["workflow_reviews"]:
            if review["review_id"] in {"research_review", "source_review"}:
                review.update(source_outcome="no_source_available", reason="The relevant official source could not be retrieved during this fictional review.")
        return route

    def validate(self, route, with_artifacts=False):
        with tempfile.TemporaryDirectory() as tmp:
            if with_artifacts:
                for filename, value in zip(("plan.json", "bundle.json", "preflight.json"), make_research_records()):
                    (Path(tmp) / filename).write_text(json.dumps(value))
            path = Path(tmp) / "receipt.json"
            path.write_text(json.dumps(route))
            return validate_route(path)

    def complete_workflow(self, route):
        for operation in route["operations"]:
            if operation["operation_id"] in {"research_gate", "source_preflight"}:
                evidence_ref = "r_0000000000000106" if operation["operation_id"] == "research_gate" else "r_0000000000000107"
                operation.update(status="completed", evidence_refs=[evidence_ref])
                operation.pop("reason_code", None)
        route["evidence"] += [
            {"evidence_ref": "r_0000000000000106", "kind": "research_gate", "subject_ref": RESEARCH_REF},
            {"evidence_ref": "r_0000000000000107", "kind": "source_preflight", "subject_ref": PREFLIGHT_REF},
        ]
        route["research_artifacts"] = [{"research_ref": RESEARCH_REF, "plan_path": "plan.json", "bundle_path": "bundle.json", "preflight_ref": PREFLIGHT_REF, "preflight_path": "preflight.json"}]

    def test_full_review_with_partial_coverage_and_real_synthetic_artifacts(self):
        route = self.route(); self.complete_workflow(route)
        result = self.validate(route, with_artifacts=True)
        self.assertEqual(result["consultation_mode"], "full")
        self.assertEqual(result["coverage_claim"], "partial")
        self.assertIn("Full consultation review", result["dashboard_preview"])
        self.assertIn("PARTIAL", result["dashboard_preview"])

    def test_limited_mode_reports_missing_work_and_effect(self):
        route = self.route(); route["consultation_mode"] = "limited"
        issue = route["issues"][0]
        for review in route["workflow_reviews"]:
            if review["review_id"] in {"research_review", "source_review"}:
                review.update(status="not_checked", reason="The structured research review step was not performed for this fictional case.")
        route["consultation_limitation"] = {"reason_code": "required_workflow_unperformed", "missing": "The structured research and source review were not performed.", "effect": "The relevant source coverage remains unverified for this assessment.", "issue_refs": [issue["issue_ref"]], "evidence_refs": [issue["evidence_ref"]], "review_ids": ["research_review", "source_review"]}
        result = self.validate(route)
        self.assertIn(route["consultation_limitation"]["missing"], result["dashboard_preview"])
        self.assertIn(route["consultation_limitation"]["effect"], result["dashboard_preview"])
        route["consultation_limitation"]["review_ids"] = ["research_review"]
        with self.assertRaisesRegex(RouteGateError, "missing_required_reviews"): self.validate(route)
        route["consultation_limitation"]["review_ids"] = ["research_review", "source_review"]
        route["consultation_limitation"]["missing"] = "More information is needed."
        with self.assertRaisesRegex(RouteGateError, "too_generic"): self.validate(route)

    def test_legacy_migration_preserves_source_and_requires_operator_input(self):
        original = v08_receipt(); snapshot = copy.deepcopy(original)
        reviews = self.route()["workflow_reviews"]
        migrated = migrate_08_to_09(original, "full", workflow_reviews=reviews, strategy_update={"disposition":"action", "objective":"Obtain effective access to lodging while preserving the applicant procedural position."})
        self.assertEqual(original, snapshot)
        self.assertEqual(migrated["schema_version"], "0.9.0")
        self.assertTrue(validate_obj("consultation-route-receipt", original))
        with self.assertRaises(MigrationError): migrate_08_to_09(original, "limited")

    def test_unknown_trigger_can_have_full_conditional_strategy(self):
        route = self.route()
        item = route["strategy_assessment"]["trigger_reviews"][1]
        item.update(status="unknown", issue_refs=[route["issues"][0]["issue_ref"]], evidence_refs=[route["issues"][0]["evidence_ref"]])
        evidence = {item["evidence_ref"]: item for item in route["evidence"]}
        self.assertEqual(check_strategy_assessment(route, evidence, []), "full")
        route["schema_version"] = "0.8.0"
        with self.assertRaisesRegex(RouteGateError, "unknown_trigger_requires_limited"):
            check_strategy_assessment(route, evidence, [])

    def test_limited_requires_explicit_explanation(self):
        route = self.route(); route["consultation_mode"] = "limited"
        with self.assertRaises(ContractError): validate_obj("consultation-route-receipt", route)
        with self.assertRaises(MigrationError): migrate_08_to_09(v08_receipt(), "limited")

    def test_full_refuses_unperformed_finalisation(self):
        route = self.route()
        final = next(item for item in route["workflow_reviews"] if item["review_id"] == "consultation_finalisation")
        final.update(status="not_checked", reason="The final consultation workflow reconciliation was not performed.", evidence_refs=[])
        with self.assertRaisesRegex(RouteGateError, "full_consultation_with_unperformed_required_work"):
            self.validate(route)

    def test_limited_strategy_requires_issue_evidence_and_specific_effect(self):
        route = self.route()
        strategy = route["strategy_assessment"]
        strategy["mode"] = "limited"
        issue = route["issues"][0]
        strategy["limitation"] = {"reason_code": "urgent_route_unverified", "missing": "The urgent judicial route has not been identified in an official source.", "effect": "The reviewer cannot assess whether an urgent remedy is available or timely.", "evidence_refs": [issue["evidence_ref"]], "issue_refs": [issue["issue_ref"]]}
        evidence = {item["evidence_ref"]: item for item in route["evidence"]}
        self.assertEqual(check_strategy_assessment(route, evidence, []), "limited")
        strategy["limitation"]["evidence_refs"] = []
        with self.assertRaisesRegex(RouteGateError, "issue_evidence_mismatch"): check_strategy_assessment(route, evidence, [])

    def test_unavailable_validators_do_not_erase_completed_model_review(self):
        route = self.route()
        result = self.validate(route)
        self.assertEqual(result["consultation_mode"], "full")
        self.assertIn("research_gate:not_checked", result["outstanding"])
        self.assertIn("Model-led workflow reviews", result["dashboard_preview"])

    def test_triggered_operation_requires_corresponding_model_review(self):
        route = self.route()
        route["operations"].append({"operation_id":"c3_case_geography_match", "applicability":"triggered", "status":"not_checked", "reason_code":"not_attempted", "evidence_refs":[]})
        with self.assertRaisesRegex(RouteGateError, "full_consultation_with_unperformed_required_work:c3_case_geography_match"): self.validate(route)
        route["workflow_reviews"].append({"review_id":"c3_case_geography_match", "status":"completed", "evidence_refs":[route["issues"][0]["evidence_ref"]]})
        self.assertEqual(self.validate(route)["consultation_mode"], "full")

    def test_unacceptable_model_review_evidence_is_rejected(self):
        route = self.route(); self.complete_workflow(route)
        route["workflow_reviews"][0]["evidence_refs"] = ["r_0000000000000106"]
        with self.assertRaisesRegex(RouteGateError, "workflow_review_evidence_kind_invalid"):
            self.validate(route, with_artifacts=True)

    def test_full_no_action_requires_rationale(self):
        route = self.route(); strategy = route["strategy_assessment"]
        strategy.update(mode="full", disposition="no_action", no_action_reason="Ordinary cooperation is sufficient because no additional procedural action is presently warranted.", issue_refs=[])
        for review in strategy["trigger_reviews"]: review.update(status="not_triggered", issue_refs=[], evidence_refs=[])
        route["issues"][0]["signal_ids"] = []
        for name in ("objective", "first_step", "purpose", "reassess_when", "alternatives_considered"): strategy.pop(name, None)
        self.assertEqual(check_strategy_assessment(route, {item["evidence_ref"]:item for item in route["evidence"]}, []), "full")
        triggered = self.route()
        triggered_strategy = triggered["strategy_assessment"]
        triggered_strategy.update(mode="full", disposition="no_action", no_action_reason="Ordinary cooperation remains appropriate because an additional step would add unnecessary burden.")
        for field in ("objective", "first_step", "purpose", "reassess_when", "alternatives_considered"): triggered_strategy.pop(field, None)
        self.assertTrue(validate_obj("consultation-route-receipt", triggered))
        self.assertEqual(check_strategy_assessment(triggered, {item["evidence_ref"]:item for item in triggered["evidence"]}, []), "full")
        strategy["no_action_reason"] = "More information is needed."
        with self.assertRaisesRegex(RouteGateError, "too_generic"): check_strategy_assessment(route, {item["evidence_ref"]:item for item in route["evidence"]}, [])

    def test_source_review_requires_real_source_or_explicit_unavailability(self):
        route = self.route()
        review = next(item for item in route["workflow_reviews"] if item["review_id"] == "source_review")
        review["source_outcome"] = "reviewed"
        with self.assertRaisesRegex(RouteGateError, "workflow_source_review_evidence_missing"): self.validate(route)
        review["source_outcome"] = "no_source_available"; review.pop("reason")
        with self.assertRaisesRegex(RouteGateError, "workflow_source_unavailability_reason_missing"): self.validate(route)

    def test_unperformed_c27_check_cannot_be_presented_as_full(self):
        route = self.route()
        record = route["c27_checks"][0]["record"]
        record.update(status="not_checked", method="none", reason="not_attempted", evidence_refs=[], source_refs=[])
        with self.assertRaisesRegex(RouteGateError, "workflow_review_c27_conflicts"): self.validate(route)

    def test_v09_strategy_mode_and_disposition_cannot_bypass_review(self):
        for mode, disposition in (("full", "not_applicable"), ("not_triggered", "no_action")):
            route = self.route(); route["strategy_assessment"].update(mode=mode, disposition=disposition)
            with self.subTest(mode=mode, disposition=disposition), self.assertRaises(ContractError): validate_obj("consultation-route-receipt", route)

    def test_v09_strategy_text_rejects_obvious_identifiers(self):
        route = self.route(); route["strategy_assessment"]["objective"] = "Contact fictional-person@example.invalid about the procedural objective."
        with self.assertRaisesRegex(RouteGateError, "privacy_minimisation_failed.*objective"): self.validate(route)

    def test_migration_reports_missing_finalisation_without_crash(self):
        legacy = v08_receipt(); legacy["operations"] = [item for item in legacy["operations"] if item["operation_id"] != "consultation_finalisation"]
        strategy_update = {"disposition":"action", "objective":"Obtain effective access to lodging while preserving the applicant procedural position."}
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); input_path = base/"input.json"; output_path = base/"output.json"; review_path = base/"reviews.json"; strategy_path = base/"strategy.json"
            input_path.write_text(json.dumps(legacy)); review_path.write_text(json.dumps(self.route()["workflow_reviews"])); strategy_path.write_text(json.dumps(strategy_update))
            command = [sys.executable, str(Path(__file__).with_name("migrate_consultation_receipt.py")), "--input", str(input_path), "--output", str(output_path), "--consultation-mode", "full", "--target-version", "0.9.0", "--workflow-reviews-json", str(review_path), "--strategy-update-json", str(strategy_path)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["finalisation_status"], "missing")
            self.assertTrue(output_path.is_file())
            output_path.unlink(); legacy["request_kind"] = "no_case_assessment"; input_path.write_text(json.dumps(legacy))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_path.exists())

    def test_partial_c27_assessment_allows_full_review(self):
        route = self.route(); route["c27_checks"][0]["record"]["status"] = "partial"
        self.assertEqual(self.validate(route)["consultation_mode"], "full")

    def test_missing_c27_requires_limited_review_and_is_visible(self):
        route = self.route(); check = route["c27_checks"].pop(0)
        issue = route["issues"][0]; issue["c27_assessment_refs"].remove(check["assessment_ref"])
        review = next(item for item in route["workflow_reviews"] if item["review_id"] == "c27_reconciliation")
        review.update(status="partial", reason="The required C27 check was not assessed for this fictional issue.")
        route["consultation_mode"] = "limited"
        route["consultation_limitation"] = {"reason_code":"required_workflow_unperformed", "missing":"The required C27 check for the issue has not been assessed.", "effect":"The corresponding procedural question cannot be treated as reviewed.", "issue_refs":[issue["issue_ref"]], "evidence_refs":[issue["evidence_ref"]], "review_ids":["c27_reconciliation"]}
        result = self.validate(route)
        self.assertIn("c27_required_check_missing:" + check["record"]["check_id"], " ".join(result["outstanding"]))
        self.assertIn(check["record"]["check_id"], result["dashboard_preview"])

    def test_legacy_schema_cannot_accept_v09_only_fields(self):
        old = v08_receipt(); old["consultation_limitation"] = {}
        with self.assertRaises(ContractError): validate_obj("consultation-route-receipt", old)
        old = v08_receipt(); old["strategy_assessment"]["disposition"] = "action"
        with self.assertRaises(ContractError): validate_obj("consultation-route-receipt", old)

    def test_nested_schema_requires_c27_binding_fields(self):
        route = self.route(); route["c27_checks"][0].pop("assessment_ref")
        with self.assertRaises(ContractError): validate_obj("consultation-route-receipt", route)

    def test_v09_controlled_release_exact_bytes_and_rejection_are_read_only(self):
        route = self.route()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); receipt = root/"receipt.json"; answer = root/"answer.md"
            receipt.write_text(json.dumps(route)); receipt_before = receipt.read_bytes()
            preview = validate_route(receipt)["dashboard_preview"]
            valid = ("Fictional answer.\n\n" + preview).encode()
            answer.write_bytes(valid)
            self.assertEqual(controlled_release(receipt, answer), valid)
            self.assertEqual(receipt.read_bytes(), receipt_before)
            self.assertEqual(answer.read_bytes(), valid)
            malformed = ("Fictional answer.\n\n### Consultation dashboard\nTruncated").encode()
            answer.write_bytes(malformed)
            with self.assertRaises(ReleaseBindingError): controlled_release(receipt, answer)
            self.assertEqual(receipt.read_bytes(), receipt_before)
            self.assertEqual(answer.read_bytes(), malformed)

    def test_dashboard_rejects_unsafe_generated_content_and_malformed_table(self):
        validation = {"receipt_sha256":"abc", "result":"valid_partial_route"}
        for content in ("<script>bad</script>", "```\nhidden", "| broken | table |"):
            preview = "## freemovement-law — Consultation Review\n\n`abc` valid partial route\n" + content
            result = {"dashboard_required":True, "dashboard_preview":preview, "validation_record":validation}
            with self.subTest(content=content), self.assertRaises(ReleaseBindingError): repair_dashboard_once(result, preview.encode())

    def test_bad_existing_board_and_duplicates_are_rejected(self):
        preview = "## freemovement-law — Consultation Review\n\n`abc` valid partial route"
        result = {"dashboard_required": True, "dashboard_preview": preview, "validation_record": {"receipt_sha256":"abc", "result":"valid_partial_route"}}
        original = b"Answer  \n\n"
        repaired, changed = repair_dashboard_once(result, original)
        self.assertTrue(repaired.startswith(original))
        self.assertTrue(changed)
        self.assertFalse(repair_dashboard_once(result, repaired)[1])
        for prefix, error in (("```\n", "unclosed_code_fence"), ("> ```\n", "unclosed_code_fence"), ("<!--\n", "unclosed_html_comment"), ("<pre>\n", "unclosed_html_block"), ("<script>\n", "unclosed_html_block")):
            with self.subTest(prefix=prefix), self.assertRaisesRegex(ReleaseBindingError, error): repair_dashboard_once(result, (prefix + preview).encode())
        for text in ("## freemovement-law — Case Review\ntruncated", "## Consultation dashboard\ntruncated", "## 6. C27 case-state dashboard\ntruncated", "### Consultation dashboard\ntruncated", preview + "\n\n" + preview):
            with self.subTest(text=text), self.assertRaises(ReleaseBindingError): repair_dashboard_once(result, text.encode())

if __name__ == "__main__": unittest.main()
