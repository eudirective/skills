#!/usr/bin/env python3
"""Fail-first structural regressions for strict consultation receipts.

Fixtures contain opaque references and registered signal/check IDs only. They
must never be expanded with applicant facts or production case material.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import consultation_dashboard as dashboard
import consultation_issue_selection as selector
import consultation_route_gate as route_gate


ISSUE_A = "r_0000000000000001"
ISSUE_B = "r_0000000000000002"
SCOPE = "r_0000000000000003"
EVIDENCE = "r_0000000000000004"
SCOPE_B = "r_0000000000000005"


def shared_scope_route(version: str) -> dict:
    signal_sets = [
        (ISSUE_A, ["external_service_provider_used"]),
        (ISSUE_B, ["digital_only_access_requirement"]),
    ]
    requirements = {
        issue_ref: selector.select_issue_requirements(signal_ids)
        for issue_ref, signal_ids in signal_sets
    }
    c27_checks = []
    issues = []
    assessment_number = 0x100
    for issue_ref, signal_ids in signal_sets:
        selected = requirements[issue_ref]
        assessment_refs = []
        if version == "0.4.0":
            owners = selected["source_owner_ids"]
        else:
            owners = selected["strict_source_owner_ids"]
        obligations = []
        for owner_id in owners:
            classes = (
                selected["source_class_requirements"][owner_id]["required_classes"]
                if version == "0.5.0" else ["procedural_rule"]
            )
            obligations.append({
                "owner_id": owner_id,
                "required_source_classes": classes or ["procedural_rule"],
                "status": "unavailable", "evidence_ref": EVIDENCE,
                "reason_code": "source_unavailable",
                **({
                    "policy_excluded_source_classes":
                        selected["source_class_requirements"][owner_id]["excluded_classes"]
                } if version == "0.5.0" else {}),
            })
        attack_reviews = []
        for topic in selected["attack_angle_topics"]:
            trigger_ids = sorted(set(topic["trigger_any_signal_ids"]) | set(topic["trigger_all_signal_ids"]))
            attack_reviews.append({
                **topic, "outcome": "unresolved", "evidence_ref": EVIDENCE,
                **({
                    "screening": {
                        "reason_code": "evidence_missing" if topic["adverse_predicate_ids"] else "predicate_unmapped",
                        "predicate_states": [{
                            "signal_id": signal_id,
                            "state": "present" if signal_id in signal_ids else "absent",
                            "evidence_ref": EVIDENCE,
                        } for signal_id in trigger_ids],
                        "adverse_predicate_states": [{
                            "predicate_id": predicate_id, "state": "unknown",
                            "evidence_ref": EVIDENCE,
                        } for predicate_id in topic["adverse_predicate_ids"]],
                    }
                } if version == "0.5.0" else {}),
            })
        issue = {
            "issue_ref": issue_ref, "scope_ref": SCOPE,
            "signal_ids": signal_ids, "disposition": "answered_supported",
            "evidence_ref": EVIDENCE,
            "source_obligations": obligations,
            "attack_angle_reviews": attack_reviews,
            **({
                "c27_assessment_refs": [],
                "conditional_closure": {"status": "not_conditional", "evidence_refs": []},
                "source_owner_exclusions": [{
                    "owner_id": owner_id,
                    "reason_code": "no_source_class_predicate_triggered",
                    "evidence_ref": EVIDENCE,
                } for owner_id in selected["source_owner_exclusions"]],
            } if version == "0.5.0" else {}),
        }
        issues.append(issue)
        for check_id in selected["check_ids"]:
            if version == "0.5.0" and issue_ref == ISSUE_B:
                # Deliberately omit the second issue's assessments to expose
                # any accidental borrowing from its shared proceeding scope.
                continue
            c27_item = {
                "scope_ref": SCOPE,
                "record": {
                    "check_id": check_id, "status": "assessed",
                    "method": "model_review", "reason": "scope_reviewed",
                    "evidence_refs": [EVIDENCE], "source_refs": [],
                },
            }
            if version == "0.5.0":
                assessment_ref = f"r_{assessment_number:016x}"
                assessment_number += 1
                assessment_refs.append(assessment_ref)
                c27_item.update({
                    "assessment_ref": assessment_ref,
                    "binding_kind": "issue_specific",
                    "bound_issue_refs": [issue_ref],
                })
            c27_checks.append(c27_item)
        if version == "0.5.0":
            issue["c27_assessment_refs"] = assessment_refs
    if version == "0.4.0":
        union_ids = sorted(
            set(requirements[ISSUE_A]["check_ids"]) |
            set(requirements[ISSUE_B]["check_ids"])
        )
        c27_checks = [{
            "scope_ref": SCOPE,
            "record": {
                "check_id": check_id, "status": "assessed",
                "method": "model_review", "reason": "scope_reviewed",
                "evidence_refs": [EVIDENCE], "source_refs": [],
            },
        } for check_id in union_ids]
    return {
        "schema_version": version,
        "request_kind": "applicant_guidance",
        "invocation": {"material_change": False},
        "issues": issues,
        "c27_checks": c27_checks,
    }


class ConsultationP0RegressionTests(unittest.TestCase):
    def test_legacy_scope_aggregation_covers_two_issues_but_strict_receipt_keeps_missing_checks_open(self):
        evidence = {EVIDENCE: {"kind": "conversation_record"}}
        legacy_gaps = []
        route_gate.check_declared_issues(
            shared_scope_route("0.4.0"), evidence, [], legacy_gaps
        )
        self.assertFalse(any(
            gap.startswith(f"issue:{ISSUE_B}:c27_required_check_missing:")
            for gap in legacy_gaps
        ))

        if not hasattr(route_gate, "validate_issue_c27_bindings"):
            self.skipTest("strict issue-to-C27 occurrence binding is absent on the recorded base")
        strict_gaps = []
        route_gate.check_declared_issues(
            shared_scope_route("0.5.0"), evidence, [], strict_gaps
        )
        self.assertTrue(any(
            gap.startswith(f"issue:{ISSUE_B}:c27_required_check_missing:")
            for gap in strict_gaps
        ))

    def test_same_scope_does_not_let_one_issue_borrow_another_issues_c27_check(self):
        req_a = selector.select_issue_requirements(["external_service_provider_used"])
        req_b = selector.select_issue_requirements(["digital_only_access_requirement"])
        unique_b = sorted(set(req_b["check_ids"]) - set(req_a["check_ids"]))
        self.assertTrue(unique_b)
        route = {
            "schema_version": "0.5.0",
            "issues": [
                {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                 "signal_ids": ["external_service_provider_used"],
                 "c27_assessment_refs": ["r_0000000000000010"]},
                {"issue_ref": ISSUE_B, "scope_ref": SCOPE,
                 "signal_ids": ["digital_only_access_requirement"],
                 "c27_assessment_refs": []},
            ],
            "c27_checks": [{
                "scope_ref": SCOPE,
                "assessment_ref": "r_0000000000000010",
                "binding_kind": "issue_specific",
                "bound_issue_refs": [ISSUE_A],
                "record": {
                    "check_id": req_a["check_ids"][0],
                    "status": "assessed", "method": "model_review",
                    "reason": "synthetic regression", "evidence_refs": [EVIDENCE],
                    "source_refs": [],
                },
            }],
        }
        actual = route_gate.validate_issue_c27_bindings(route)
        self.assertEqual(actual[ISSUE_A], {req_a["check_ids"][0]})
        self.assertTrue(set(req_b["check_ids"]) - actual[ISSUE_B])

    def test_distinct_assessment_refs_do_not_duplicate_one_atomic_c27_occurrence(self):
        record = {
            "check_id": "case_intake.proceedings_identified",
            "status": "assessed", "method": "model_review",
            "reason": "scope_reviewed", "evidence_refs": [EVIDENCE],
            "source_refs": [],
        }
        first = {
            "scope_ref": SCOPE, "assessment_ref": "r_0000000000000010",
            "binding_kind": "issue_specific", "bound_issue_refs": [ISSUE_A],
            "record": record,
        }
        second = {
            "scope_ref": SCOPE, "assessment_ref": "r_0000000000000011",
            "binding_kind": "issue_specific", "bound_issue_refs": [ISSUE_A],
            "record": dict(record),
        }
        with self.assertRaisesRegex(route_gate.RouteGateError, "c27_assessment_occurrence_duplicate"):
            route_gate.check_c27_records(
                {"schema_version": "0.5.0", "request_kind": "applicant_guidance",
                 "c27_checks": [first, second]},
                selector.load_json(selector.REGISTRY_PATH), [],
            )

    def test_resolved_qualified_conditional_answer_is_not_counted_as_open_work(self):
        route = {
            "schema_version": "0.5.0",
            "issues": [
                {"issue_ref": ISSUE_A, "disposition": "answered_conditionally",
                 "conditional_closure": {"status": "qualified_condition", "evidence_refs": [EVIDENCE]}},
                {"issue_ref": ISSUE_B, "disposition": "answered_conditionally",
                 "conditional_closure": {"status": "predicate_open", "evidence_refs": [EVIDENCE]}},
            ],
        }
        self.assertEqual(dashboard.unresolved_issue_refs(route), {ISSUE_B})

    def test_route_derived_source_classes_do_not_force_national_law_without_a_trigger(self):
        eu_only = selector.select_issue_requirements(["directive_scope_question"])
        self.assertEqual(eu_only["strict_source_owner_ids"], ["eu_common_core"])
        self.assertIn("member_state_law", eu_only["source_owner_exclusions"])
        triggered = selector.select_issue_requirements(["digital_only_access_requirement"])
        self.assertIn("member_state_law", triggered["strict_source_owner_ids"])
        self.assertIn(
            "national_binding_law",
            triggered["source_class_requirements"]["member_state_law"]["required_classes"],
        )

    def test_owner_cannot_omit_a_policy_required_source_class(self):
        obligation = {
            "required_source_classes": ["procedural_rule"],
            "policy_excluded_source_classes": ["eu_binding_law"],
        }
        gaps = []
        route_gate.validate_source_class_obligation(
            ISSUE_A, "member_state_law", obligation,
            {"required_classes": ["national_binding_law", "procedural_rule"],
             "excluded_classes": ["eu_binding_law"]},
            gaps,
        )
        self.assertEqual(
            gaps,
            ["issue:r_0000000000000001:source_class_policy_required_missing:"
             "member_state_law:national_binding_law"],
        )

    def test_candidate_attack_self_link_and_negative_screen_are_rejected(self):
        expected = next(
            item for item in selector.select_issue_requirements(
                ["digital_only_access_requirement"]
            )["attack_angle_topics"]
            if item.get("pathway_id") == "digital_only_access"
        )
        trigger_ids = sorted(set(expected["trigger_any_signal_ids"]) | set(expected["trigger_all_signal_ids"]))
        issue = {
            "issue_ref": ISSUE_A,
            "signal_ids": ["digital_only_access_requirement"],
            "attack_angle_reviews": [{
                **expected,
                "outcome": "candidate_issue_linked", "linked_issue_ref": ISSUE_A,
                "screening": {
                    "reason_code": "candidate_assessed",
                    "predicate_states": [{
                        "signal_id": signal_id,
                        "state": "present" if signal_id == "digital_only_access_requirement" else "absent",
                        "evidence_ref": EVIDENCE,
                    } for signal_id in trigger_ids],
                    "adverse_predicate_states": [{
                        "predicate_id": predicate_id, "state": "present",
                        "evidence_ref": EVIDENCE,
                    } for predicate_id in expected["adverse_predicate_ids"]],
                },
                "evidence_ref": EVIDENCE,
            }],
        }
        evidence = {EVIDENCE: {"kind": "conversation_record"}}
        with self.assertRaisesRegex(route_gate.RouteGateError, "issue_attack_candidate_self_link"):
            route_gate.validate_attack_angle_screen(
                issue, issue["attack_angle_reviews"][0], expected, evidence
            )

        issue["attack_angle_reviews"][0].update(
            outcome="no_signal_identified", linked_issue_ref=None,
        )
        issue["attack_angle_reviews"][0]["screening"].update(
            reason_code="no_adverse_signal",
            predicate_states=[{"signal_id": signal_id,
                              "state": "present" if signal_id == "digital_only_access_requirement" else "absent",
                              "evidence_ref": EVIDENCE} for signal_id in trigger_ids],
            adverse_predicate_states=[{"predicate_id": predicate_id,
                                       "state": "unknown", "evidence_ref": EVIDENCE}
                                      for predicate_id in expected["adverse_predicate_ids"]],
        )
        with self.assertRaisesRegex(route_gate.RouteGateError, "issue_attack_negative_screen_unsupported"):
            # A neutral route trigger cannot be substituted for an unknown
            # topic-specific adverse predicate.
            route_gate.validate_attack_angle_screen(
                issue, issue["attack_angle_reviews"][0], expected, evidence
            )

    def test_attack_screen_rejects_unrelated_absent_or_present_signals(self):
        expected = selector.select_issue_requirements(["directive_scope_question"])["attack_angle_topics"][0]
        issue = {"issue_ref": ISSUE_A, "signal_ids": ["directive_scope_question"]}
        topic = {
            **expected, "outcome": "no_signal_identified", "evidence_ref": EVIDENCE,
            "screening": {"reason_code": "no_adverse_signal", "predicate_states": [{
                "signal_id": "formal_refusal_issued", "state": "absent",
                "evidence_ref": EVIDENCE,
            }]},
        }
        evidence = {EVIDENCE: {"kind": "conversation_record"}}
        with self.assertRaisesRegex(route_gate.RouteGateError, "issue_attack_screen_predicate_binding_mismatch"):
            route_gate.validate_attack_angle_screen(issue, topic, expected, evidence)

        topic["outcome"] = "candidate_same_issue"
        topic["screening"] = {
            "reason_code": "candidate_assessed",
            "predicate_states": [{
                "signal_id": signal_id, "state": "present", "evidence_ref": EVIDENCE,
            } for signal_id in expected["trigger_any_signal_ids"]],
            "adverse_predicate_states": [],
        }
        with self.assertRaisesRegex(route_gate.RouteGateError, "issue_attack_unmapped_predicate_must_remain_unresolved"):
            route_gate.validate_attack_angle_screen(issue, topic, expected, evidence)

    def test_pathway_all_predicates_control_negative_unresolved_and_candidate_outcomes(self):
        signal_ids = ["pre_lodgement_access_obstruction", "appointment_delay"]
        expected = next(
            item for item in selector.select_issue_requirements(signal_ids)["attack_angle_topics"]
            if item.get("trigger_all_signal_ids")
        )
        self.assertEqual(expected["trigger_any_signal_ids"], [])
        self.assertEqual(set(expected["trigger_all_signal_ids"]), set(signal_ids))
        issue = {"issue_ref": ISSUE_A, "signal_ids": signal_ids}
        evidence = {EVIDENCE: {"kind": "conversation_record"}}

        def topic_for(outcome: str, reason: str, values: dict[str, str]) -> dict:
            return {
                **expected, "outcome": outcome, "evidence_ref": EVIDENCE,
                "screening": {
                    "reason_code": reason,
                    "predicate_states": [
                        {"signal_id": signal_id, "state": "present", "evidence_ref": EVIDENCE}
                        for signal_id in signal_ids
                    ],
                    "adverse_predicate_states": [
                        {"predicate_id": predicate_id,
                         "state": values.get(predicate_id, "unknown"),
                         "evidence_ref": EVIDENCE}
                        for predicate_id in expected["adverse_predicate_ids"]
                    ],
                },
            }

        route_gate.validate_attack_angle_screen(
            issue, topic_for("unresolved", "evidence_missing", {expected["adverse_predicate_ids"][0]: "unknown"}),
            expected, evidence,
        )
        route_gate.validate_attack_angle_screen(
            issue, topic_for("candidate_same_issue", "candidate_assessed", {expected["adverse_predicate_ids"][0]: "present"}),
            expected, evidence,
        )
        route_gate.validate_attack_angle_screen(
            issue, topic_for("no_signal_identified", "no_adverse_signal", {expected["adverse_predicate_ids"][0]: "absent"}),
            expected, evidence,
        )

    def test_linked_candidate_remains_open_when_bound_required_c27_check_is_partial(self):
        linked_requirements = selector.select_issue_requirements(["digital_only_access_requirement"])
        required = linked_requirements["check_ids"]
        statuses = {check_id: "assessed" for check_id in required}
        statuses[required[0]] = "partial"
        linked = {
            "issue_ref": ISSUE_B, "scope_ref": SCOPE,
            "signal_ids": ["digital_only_access_requirement"],
            "disposition": "answered_supported",
            "c27_assessment_refs": [EVIDENCE],
            "conditional_closure": {"status": "not_conditional", "evidence_refs": []},
        }
        source = {
            "issue_ref": ISSUE_A,
            "attack_angle_reviews": [{
                "route_id": "candidate_topic", "outcome": "candidate_issue_linked",
                "linked_issue_ref": ISSUE_B,
            }],
        }
        gaps = []
        route_gate.validate_linked_attack_candidates(
            {"issues": [source, linked]},
            {ISSUE_B: set(required)},
            {ISSUE_B: statuses},
            gaps,
        )
        self.assertTrue(any(
            gap.startswith(f"issue:{ISSUE_A}:attack_angle_linked_issue_assessment_missing:")
            for gap in gaps
        ))
        issue_gaps = []
        open_ids = route_gate.record_issue_c27_gaps(
            ISSUE_B, required, set(required), statuses, issue_gaps
        )
        self.assertEqual(open_ids, [required[0]])
        self.assertIn(f"issue:{ISSUE_B}:c27_check_open:{required[0]}:partial", issue_gaps)

    def test_material_signal_change_cannot_be_hidden_by_false_material_change(self):
        route = {
            "schema_version": "0.5.0",
            "invocation": {"material_change": False},
            "issues": [{"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                        "signal_ids": ["formal_refusal_issued"]}],
            "revision_control": {
                "change_detection_status": "compared",
                "previous_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "directive_scope_question", "state": "present"}]},
                ]},
                "current_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "formal_refusal_issued", "state": "present"}]},
                ]},
                "added_issue_refs": [], "removed_issue_refs": [],
                "changed_issue_refs": [ISSUE_A], "affected_scope_refs": [SCOPE],
                "reassessed_scope_refs": [], "removed_issue_reviews": [],
            },
        }
        with self.assertRaisesRegex(route_gate.RouteGateError, "material_change_declaration_mismatch"):
            route_gate.validate_abstract_revision(route, [])

    def test_unknown_to_present_signal_transition_is_detected_as_material(self):
        route = {
            "schema_version": "0.5.0",
            "invocation": {"material_change": False},
            "issues": [{"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                        "signal_ids": ["digital_only_access_requirement"]}],
            "revision_control": {
                "change_detection_status": "compared",
                "previous_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "digital_only_access_requirement", "state": "unknown"}]},
                ]},
                "current_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "digital_only_access_requirement", "state": "present"}]},
                ]},
                "added_issue_refs": [], "removed_issue_refs": [],
                "changed_issue_refs": [ISSUE_A], "affected_scope_refs": [SCOPE],
                "reassessed_scope_refs": [], "removed_issue_reviews": [],
            },
        }
        with self.assertRaisesRegex(route_gate.RouteGateError, "material_change_declaration_mismatch"):
            route_gate.validate_abstract_revision(route, [])

    def test_abstract_revision_records_added_issue_and_affected_scope(self):
        route = {
            "schema_version": "0.5.0",
            "invocation": {"material_change": True},
            "issues": [
                {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                 "signal_ids": ["directive_scope_question"]},
                {"issue_ref": ISSUE_B, "scope_ref": SCOPE_B,
                 "signal_ids": ["digital_only_access_requirement"]},
            ],
            "revision_control": {
                "change_detection_status": "compared",
                "previous_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "directive_scope_question", "state": "present"}]},
                ]},
                "current_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "directive_scope_question", "state": "present"}]},
                    {"issue_ref": ISSUE_B, "scope_ref": SCOPE_B,
                     "signal_states": [{"signal_id": "digital_only_access_requirement", "state": "present"}]},
                ]},
                "added_issue_refs": [ISSUE_B], "removed_issue_refs": [],
                "changed_issue_refs": [], "affected_scope_refs": [SCOPE_B],
                "reassessed_scope_refs": [], "removed_issue_reviews": [],
            },
        }
        gaps = []
        self.assertEqual(route_gate.validate_abstract_revision(route, gaps), {SCOPE_B})
        self.assertEqual(gaps, [f"material_change_scope_reassessment_pending:{SCOPE_B}"])

    def test_removed_issue_requires_current_response_evidence_and_reassessment(self):
        route = {
            "schema_version": "0.5.0",
            "invocation": {"material_change": True},
            "issues": [{"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                        "signal_ids": ["directive_scope_question"]}],
            "evidence": [{"evidence_ref": EVIDENCE, "kind": "conversation_record",
                          "record_scope": "prior_conversation"}],
            "revision_control": {
                "change_detection_status": "compared",
                "previous_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "directive_scope_question", "state": "present"}]},
                    {"issue_ref": ISSUE_B, "scope_ref": SCOPE_B,
                     "signal_states": [{"signal_id": "digital_only_access_requirement", "state": "present"}]},
                ]},
                "current_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "directive_scope_question", "state": "present"}]},
                ]},
                "added_issue_refs": [], "removed_issue_refs": [ISSUE_B],
                "changed_issue_refs": [], "affected_scope_refs": [SCOPE_B],
                "reassessed_scope_refs": [SCOPE_B],
                "removed_issue_reviews": [{
                    "issue_ref": ISSUE_B, "scope_ref": SCOPE_B,
                    "disposition": "no_longer_in_scope", "evidence_ref": EVIDENCE,
                }],
            },
        }
        gaps = []
        route_gate.validate_abstract_revision(route, gaps)
        self.assertIn(f"removed_issue_review_not_current:{ISSUE_B}", gaps)

        route["evidence"][0]["record_scope"] = "current_response"
        gaps = []
        route_gate.validate_abstract_revision(route, gaps)
        self.assertEqual(gaps, [])

    def test_removed_issue_merge_target_must_exist_in_current_manifest(self):
        route = {
            "schema_version": "0.5.0",
            "invocation": {"material_change": True},
            "issues": [{"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                        "signal_ids": ["directive_scope_question"]}],
            "evidence": [{"evidence_ref": EVIDENCE, "kind": "conversation_record",
                          "record_scope": "current_response"}],
            "revision_control": {
                "change_detection_status": "compared",
                "previous_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "directive_scope_question", "state": "present"}]},
                    {"issue_ref": ISSUE_B, "scope_ref": SCOPE_B,
                     "signal_states": [{"signal_id": "digital_only_access_requirement", "state": "present"}]},
                ]},
                "current_abstract_state": {"manifest_version": "0.1.0", "issues": [
                    {"issue_ref": ISSUE_A, "scope_ref": SCOPE,
                     "signal_states": [{"signal_id": "directive_scope_question", "state": "present"}]},
                ]},
                "added_issue_refs": [], "removed_issue_refs": [ISSUE_B],
                "changed_issue_refs": [], "affected_scope_refs": [SCOPE_B],
                "reassessed_scope_refs": [SCOPE_B],
                "removed_issue_reviews": [{
                    "issue_ref": ISSUE_B, "scope_ref": SCOPE_B,
                    "disposition": "merged_into_current_issue", "evidence_ref": EVIDENCE,
                    "merged_into_issue_ref": ISSUE_B,
                }],
            },
        }
        with self.assertRaisesRegex(route_gate.RouteGateError, "abstract_revision_merge_target_missing"):
            route_gate.validate_abstract_revision(route, [])
        route["revision_control"]["removed_issue_reviews"][0]["merged_into_issue_ref"] = ISSUE_A
        gaps = []
        route_gate.validate_abstract_revision(route, gaps)
        self.assertEqual(gaps, [])

    def test_strict_provenance_requires_discovery_methods(self):
        ledger = {"response_tracking": "unavailable", "conversation_tracking": "unavailable",
                  "sources": [{
                      "logical_source_id": "synthetic-source-1", "source_id": "eu:synthetic",
                      "title": "Synthetic source", "section": "EU core", "jurisdiction": "EU",
                      "category": "eu_legislation", "origin": "bundled_library",
                      "official_url": None, "version_or_edition": None,
                      "representation_ids": [], "pinpoints": [], "currentness": "unknown",
                      "library_state": "not_recorded", "response_use": "not_referenced",
                      "conversation_use": "not_referenced", "response_provenance": "none",
                      "conversation_provenance": "none", "response_read_evidence": None,
                      "conversation_read_evidence": None, "response_evidence_ref": None,
                      "conversation_evidence_ref": None,
                  }]}
        with self.assertRaisesRegex(dashboard.DashboardError, "source_discovery_method_missing"):
            dashboard.validate_strict_source_provenance(ledger)

    def test_obvious_identifiers_are_rejected_from_strict_receipt_text(self):
        with self.assertRaisesRegex(route_gate.RouteGateError, "privacy_minimisation_failed"):
            route_gate.validate_privacy_minimisation({
                "schema_version": "0.5.0",
                "dashboard": {"issue_summaries": [{"title": "Synthetic contact person@example.invalid"}]},
            })


if __name__ == "__main__":
    unittest.main(verbosity=2)
