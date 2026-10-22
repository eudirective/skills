#!/usr/bin/env python3
"""Structural tests for synthetic abstract consultation issue routing."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import consultation_issue_selection as selector


MATRIX = selector.load_json(selector.MATRIX_PATH)
REGISTRY = selector.load_json(selector.REGISTRY_PATH)


def fixture(*proceedings: tuple[str, list[str]]) -> dict:
    return {
        "fixture_kind": "synthetic_abstract",
        "proceedings": [
            {"proceeding_id": proceeding_id, "signal_ids": signal_ids}
            for proceeding_id, signal_ids in proceedings
        ],
    }


def selected_ids(result: dict, proceeding_id: str = "p_1") -> set[str]:
    proceeding = next(item for item in result["proceedings"] if item["proceeding_id"] == proceeding_id)
    return {item["check_id"] for item in proceeding["selected_checks"]}


def route_ids(result: dict, proceeding_id: str = "p_1") -> set[str]:
    proceeding = next(item for item in result["proceedings"] if item["proceeding_id"] == proceeding_id)
    return {item["route_id"] for item in proceeding["issue_routes"]}


class ConsultationIssueSelectionTests(unittest.TestCase):
    def test_all_matrix_check_ids_and_core_source_references_are_valid(self) -> None:
        signal_defs, valid_checks = selector.validate_configuration(MATRIX, REGISTRY)
        self.assertGreaterEqual(len(signal_defs), 10)
        self.assertGreaterEqual(len(valid_checks), 100)

    def test_receipt_schema_signal_enum_matches_routing_catalog(self) -> None:
        schema_path = selector.ROOT / "references/contracts/consultation-route-receipt.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        declared = set(
            schema["$defs"]["declared_issue"]["properties"]["signal_ids"]["items"]["enum"]
        )
        self.assertEqual(
            declared,
            {item["signal_id"] for item in MATRIX["signal_catalog"]},
        )

    def test_each_priority_route_selects_its_mandatory_checks(self) -> None:
        cases = {
            "directive_scope_question": (
                "directive_personal_and_territorial_applicability",
                {"eu_scope.directive_scope", "case_intake.actor_roles", "case_intake.relationship_basis", "case_intake.geographic_roles"},
            ),
            "accompanying_or_joining_question": (
                "eu_citizen_accompanying_or_joining",
                {"eu_scope.directive_scope", "eu_scope.movement_exercised", "eu_scope.accompany_or_join"},
            ),
            "prior_refusal_or_status_change": (
                "prior_refusal_and_legal_status_change",
                {"case_intake.proceedings_identified", "lifecycle.decision_taken", "authority.actual_ground", "eu_scope.directive_scope"},
            ),
            "swiss_free_movement_framework_question": (
                "member_state_versus_eu_swiss_framework",
                {"eu_scope.directive_scope", "country.multiple_jurisdictions", "sources.binding_classification", "sources.official_publisher"},
            ),
            "pre_lodgement_access_obstruction": (
                "pre_lodgement_obstruction_and_appointment_access",
                {"lifecycle.appointment_request", "lifecycle.lodgement_attempted", "access.appointment_wait", "access.refusal_to_lodge"},
            ),
            "external_service_provider_used": (
                "external_service_provider_and_fees",
                {"access.service_provider_accountability", "access.direct_access", "authority.staff_responsibility"},
            ),
            "ordinary_document_list_or_eu_family_document_question": (
                "ordinary_document_list_or_eu_family_requirements",
                {"documents.requested_item", "documents.requested_legal_basis", "documents.ordinary_checklist_scope"},
            ),
            "processing_delay_or_deadline_question": (
                "processing_delay_or_clock_trigger",
                {"timing.clock_start", "timing.lodgement_trigger", "timing.applicable_rule", "timing.pre_lodgement_delay"},
            ),
            "remedy_or_solvit_or_supervisory_complaint": (
                "remedy_or_supervisory_track",
                {"case_intake.linked_proceedings", "lifecycle.challenge_stage", "remedies.remedy_compatibility", "remedies.competent_authority"},
            ),
            "personal_data_processing_question": (
                "personal_data_protection",
                {"gdpr.lawful_basis", "gdpr.controller_identity", "gdpr.data_minimisation"},
            ),
            "ephemeral_evidence_at_risk": (
                "ephemeral_evidence_preservation",
                {"timing.urgent_preservation", "proof.unexamined_records", "strategy.preservation_first"},
            ),
        }
        for signal, (expected_route, required_checks) in cases.items():
            with self.subTest(signal=signal):
                result = selector.select_checks(fixture(("p_1", [signal])))
                self.assertIn(expected_route, route_ids(result))
                self.assertTrue(required_checks.issubset(selected_ids(result)))

    def test_absent_primary_signal_is_a_negative_route_control(self) -> None:
        result = selector.select_checks(
            fixture(
                (
                    "p_1",
                    ["remedy_or_solvit_or_supervisory_complaint"],
                )
            )
        )
        routes = route_ids(result)
        checks = selected_ids(result)
        self.assertEqual(routes, {"remedy_or_supervisory_track"})
        self.assertNotIn("prior_refusal_and_legal_status_change", routes)
        self.assertNotIn("member_state_versus_eu_swiss_framework", routes)
        self.assertNotIn("personal_data_protection", routes)
        self.assertNotIn("ephemeral_evidence_preservation", routes)
        self.assertNotIn("gdpr.lawful_basis", checks)
        self.assertNotIn("eu_scope.directive_scope", checks)

    def test_conditional_routes_require_their_declared_signal(self) -> None:
        provider_only = selector.select_checks(fixture(("p_1", ["external_service_provider_used"])))
        self.assertNotIn("access.outsourcing_fees", selected_ids(provider_only))
        self.assertNotIn("access.fee_waiver", selected_ids(provider_only))

        fee_disputed = selector.select_checks(
            fixture(("p_1", ["external_service_provider_used", "provider_fee_disputed"]))
        )
        self.assertIn("access.outsourcing_fees", selected_ids(fee_disputed))
        self.assertIn("access.fee_waiver", selected_ids(fee_disputed))

    def test_explicit_negative_applicability_suppresses_only_fee_checks(self) -> None:
        result = selector.select_checks(
            fixture(("p_1", ["external_service_provider_used", "provider_fee_not_disputed"]))
        )
        checks = selected_ids(result)
        self.assertIn("access.service_provider_accountability", checks)
        self.assertIn("access.direct_access", checks)
        self.assertNotIn("access.outsourcing_fees", checks)
        self.assertNotIn("access.fee_waiver", checks)

    def test_gdpr_checks_for_ephemeral_records_require_personal_data_signal(self) -> None:
        nonpersonal = selector.select_checks(fixture(("p_1", ["ephemeral_evidence_at_risk"])))
        self.assertIn("timing.urgent_preservation", selected_ids(nonpersonal))
        self.assertNotIn("gdpr.cctv", selected_ids(nonpersonal))
        personal = selector.select_checks(
            fixture(("p_1", ["ephemeral_evidence_at_risk", "evidence_record_contains_personal_data"]))
        )
        self.assertIn("gdpr.cctv", selected_ids(personal))
        self.assertIn("gdpr.preservation_request", selected_ids(personal))

    def test_public_signal_selector_returns_validated_sorted_check_ids(self) -> None:
        signal_ids = [
            "provider_fee_disputed",
            "external_service_provider_used",
        ]
        expected = selector.select_checks(fixture(("p_1", signal_ids)))
        expected_ids = sorted(selected_ids(expected))
        self.assertEqual(selector.select_check_ids(signal_ids), expected_ids)
        with self.assertRaisesRegex(selector.SelectionError, "signal_unknown"):
            selector.select_check_ids(["unknown_signal"])

    def test_issue_requirements_derive_source_owners_and_attack_topics(self) -> None:
        base = selector.select_issue_requirements(["ephemeral_evidence_at_risk"])
        self.assertEqual(base["source_owner_ids"], ["member_state_law"])
        self.assertEqual(
            {item["route_id"] for item in base["attack_angle_topics"]},
            {"ephemeral_evidence_preservation"},
        )
        self.assertGreater(len(base["attack_angle_topics"]), 0)

        personal = selector.select_issue_requirements([
            "ephemeral_evidence_at_risk", "evidence_record_contains_personal_data",
        ])
        self.assertEqual(
            personal["source_owner_ids"], ["eu_data_protection", "member_state_law"]
        )
        self.assertIn("gdpr.preservation_request", personal["check_ids"])

    def test_issue_requirements_reject_unknown_or_contradictory_signals(self) -> None:
        with self.assertRaisesRegex(selector.SelectionError, "signal_unknown"):
            selector.select_issue_requirements(["not_a_registered_signal"])
        with self.assertRaisesRegex(selector.SelectionError, "contradictory_signals"):
            selector.select_issue_requirements([
                "external_service_provider_used", "provider_fee_disputed", "provider_fee_not_disputed",
            ])

    def test_priority_attack_pathways_bind_signals_predicates_and_selected_checks(self) -> None:
        pathways = selector.validate_pathway_bindings(MATRIX, REGISTRY, selector.signal_catalog(MATRIX))
        self.assertEqual(len(pathways), 6)
        for topic_id, topic in pathways.items():
            for binding in topic["consultation_bindings"]:
                signal_ids = sorted(set(binding["when_any_signal"] + binding["when_all_signal"]))
                requirements = selector.select_issue_requirements(signal_ids)
                self.assertIn(binding["route_id"], requirements["route_ids"], topic_id)
                pathway_record = next(
                    item for item in requirements["attack_angle_topics"]
                    if item.get("pathway_id") == topic_id
                )
                self.assertTrue(pathway_record["c27_check_ids"], topic_id)
                self.assertEqual(pathway_record["coverage_pattern_ids"], topic["coverage_pattern_ids"])

        digital = selector.select_issue_requirements(["digital_only_access_requirement"])
        self.assertIn("access.digital_only", digital["check_ids"])
        self.assertEqual(digital["routing_review_status"], "pending_independent_review")
        generic_topics = [
            item for item in digital["attack_angle_topics"] if not item.get("pathway_id")
        ]
        self.assertTrue(generic_topics)
        self.assertTrue(all(item["adverse_predicate_ids"] == [] for item in generic_topics))
        digital_topic = next(
            item for item in digital["attack_angle_topics"]
            if item.get("pathway_id") == "digital_only_access"
        )
        self.assertEqual(
            digital_topic["adverse_predicate_ids"], ["pathway:digital_only_access"]
        )

    def test_pathway_maps_generic_topic_only_on_exact_route_label_and_triggers(self) -> None:
        pathways = selector.load_json(selector.PATHWAY_PATH)
        pathways["topics"].append({
            "topic_id": "synthetic_exact_generic_topic_binding",
            "label": "territorial or personal-scope exception",
            "coverage": "not_implemented_in_C5d_deterministic_predicates",
            "c27_families": ["eu_scope"],
            "consultation_bindings": [{
                "route_id": "directive_personal_and_territorial_applicability",
                "when_any_signal": ["directive_scope_question"],
            }],
            "adverse_signal": "Synthetic test-only predicate.",
        })
        with tempfile.TemporaryDirectory() as temporary:
            pathway_path = Path(temporary) / "pathways.json"
            pathway_path.write_text(json.dumps(pathways), encoding="utf-8")
            with mock.patch.object(selector, "PATHWAY_PATH", pathway_path):
                result = selector.select_issue_requirements(["directive_scope_question"])

        matching = [
            item for item in result["attack_angle_topics"]
            if item["route_id"] == "directive_personal_and_territorial_applicability"
            and item["topic"] == "territorial or personal-scope exception"
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["pathway_id"], "synthetic_exact_generic_topic_binding")
        self.assertEqual(
            matching[0]["adverse_predicate_ids"],
            ["pathway:synthetic_exact_generic_topic_binding"],
        )

    def test_unmatched_pathway_does_not_replace_generic_route_topic(self) -> None:
        pathways = selector.load_json(selector.PATHWAY_PATH)
        pathways["topics"].append({
            "topic_id": "synthetic_unmatched_generic_topic_binding",
            "label": "territorial or personal-scope exception — altered label",
            "coverage": "not_implemented_in_C5d_deterministic_predicates",
            "c27_families": ["eu_scope"],
            "consultation_bindings": [{
                "route_id": "directive_personal_and_territorial_applicability",
                "when_any_signal": ["directive_scope_question"],
            }],
            "adverse_signal": "Synthetic test-only predicate.",
        })
        with tempfile.TemporaryDirectory() as temporary:
            pathway_path = Path(temporary) / "pathways.json"
            pathway_path.write_text(json.dumps(pathways), encoding="utf-8")
            with mock.patch.object(selector, "PATHWAY_PATH", pathway_path):
                result = selector.select_issue_requirements(["directive_scope_question"])

        generic = [
            item for item in result["attack_angle_topics"]
            if item["route_id"] == "directive_personal_and_territorial_applicability"
            and item["topic"] == "territorial or personal-scope exception"
        ]
        separate = [
            item for item in result["attack_angle_topics"]
            if item.get("pathway_id") == "synthetic_unmatched_generic_topic_binding"
        ]
        self.assertEqual(len(generic), 1)
        self.assertEqual(generic[0]["adverse_predicate_ids"], [])
        self.assertEqual(len(separate), 1)

    def test_duplicate_exact_pathway_bindings_are_rejected(self) -> None:
        pathways = selector.load_json(selector.PATHWAY_PATH)
        for topic_id in (
            "synthetic_duplicate_generic_topic_binding_a",
            "synthetic_duplicate_generic_topic_binding_b",
        ):
            pathways["topics"].append({
                "topic_id": topic_id,
                "label": "territorial or personal-scope exception",
                "coverage": "not_implemented_in_C5d_deterministic_predicates",
                "c27_families": ["eu_scope"],
                "consultation_bindings": [{
                    "route_id": "directive_personal_and_territorial_applicability",
                    "when_any_signal": ["directive_scope_question"],
                }],
                "adverse_signal": "Synthetic test-only predicate.",
            })
        with tempfile.TemporaryDirectory() as temporary:
            pathway_path = Path(temporary) / "pathways.json"
            pathway_path.write_text(json.dumps(pathways), encoding="utf-8")
            with mock.patch.object(selector, "PATHWAY_PATH", pathway_path):
                with self.assertRaisesRegex(
                    selector.SelectionError,
                    "attack_topic_pathway_binding_duplicate:directive_personal_and_territorial_applicability:territorial or personal-scope exception",
                ):
                    selector.select_issue_requirements(["directive_scope_question"])

    def test_contradictory_positive_and_negative_signals_are_rejected(self) -> None:
        with self.assertRaisesRegex(selector.SelectionError, "contradictory_signals"):
            selector.select_checks(
                fixture(
                    (
                        "p_1",
                        ["external_service_provider_used", "provider_fee_disputed", "provider_fee_not_disputed"],
                    )
                )
            )

    def test_multiple_routes_combine_without_losing_distinct_issue_routes(self) -> None:
        result = selector.select_checks(
            fixture(
                (
                    "p_1",
                    [
                        "prior_refusal_or_status_change",
                        "pre_lodgement_access_obstruction",
                        "staff_conduct",
                    ],
                )
            )
        )
        routes = route_ids(result)
        self.assertEqual(
            routes,
            {
                "prior_refusal_and_legal_status_change",
                "pre_lodgement_obstruction_and_appointment_access",
            },
        )
        checks = selected_ids(result)
        self.assertIn("lifecycle.decision_taken", checks)
        self.assertIn("access.refusal_to_lodge", checks)
        self.assertIn("conduct.complaint_channel", checks)

    def test_proceeding_histories_do_not_inherit_each_others_checks(self) -> None:
        result = selector.select_checks(
            fixture(
                ("p_1", ["prior_refusal_or_status_change"]),
                ("p_2", ["personal_data_processing_question"]),
            )
        )
        first = selected_ids(result, "p_1")
        second = selected_ids(result, "p_2")
        self.assertIn("lifecycle.decision_taken", first)
        self.assertNotIn("gdpr.lawful_basis", first)
        self.assertIn("gdpr.lawful_basis", second)
        self.assertNotIn("lifecycle.decision_taken", second)

    def test_signal_and_proceeding_order_do_not_change_result(self) -> None:
        first = fixture(
            ("p_2", ["formal_lodgement_confirmed", "processing_delay_or_deadline_question"]),
            ("p_1", ["returnee_context", "directive_scope_question", "movement_or_cross_border_context"]),
        )
        second = fixture(
            ("p_1", ["movement_or_cross_border_context", "directive_scope_question", "returnee_context"]),
            ("p_2", ["processing_delay_or_deadline_question", "formal_lodgement_confirmed"]),
        )
        self.assertEqual(selector.select_checks(first), selector.select_checks(second))

    def test_unknown_check_id_in_matrix_fails_closed(self) -> None:
        matrix = copy.deepcopy(MATRIX)
        matrix["routes"][0]["mandatory_checks"].append("made_up.check")
        with self.assertRaisesRegex(selector.SelectionError, "check_id_unknown"):
            selector.validate_configuration(matrix, REGISTRY)

    def test_unknown_signal_and_free_text_fixture_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(selector.SelectionError, "signal_unknown"):
            selector.select_checks(fixture(("p_1", ["fictional_but_unsupported_signal"])))
        narrative_fixture = fixture(("p_1", ["directive_scope_question"]))
        narrative_fixture["narrative"] = "This field is intentionally forbidden."
        with self.assertRaisesRegex(selector.SelectionError, "fixture_fields_not_allowed"):
            selector.select_checks(narrative_fixture)

    def test_non_synthetic_fixture_kind_and_non_opaque_proceeding_id_are_rejected(self) -> None:
        with self.assertRaisesRegex(selector.SelectionError, "fixture_must_be_synthetic_abstract"):
            selector.select_checks({"fixture_kind": "real_case", "proceedings": []})
        with self.assertRaisesRegex(selector.SelectionError, "proceeding_id_must_be_synthetic_sequence_id"):
            selector.select_checks(fixture(("actual-country-case", ["directive_scope_question"])))


if __name__ == "__main__":
    unittest.main()
