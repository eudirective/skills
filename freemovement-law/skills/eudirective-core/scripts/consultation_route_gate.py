#!/usr/bin/env python3
"""Structurally check a privacy-minimised consultation route receipt.

This is a portable pre-release check for a host that chooses to call it. It
cannot establish that the model selected every relevant conditional workflow,
that a model-led review actually happened, or that referenced evidence is
truthful. It accepts no applicant narrative or jurisdiction values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from c27_case_state import (
    ADMINISTRATIVE_OUTCOMES, POST_ISSUANCE_EVENTS, PROCEDURE_TYPES,
    StateError, load_registry, validate_route_check_record,
)
from contract_validate import ContractError, validate_obj
from module_conformance import ConformanceError, validate_paths
from research_gate import ResearchGateError, validate_research
from issue_source_preflight import SourcePreflightError, validate_source_preflight
from consultation_dashboard import DashboardError, render_dashboard, validate_dashboard_receipt
from consultation_issue_selection import (
    SelectionError as IssueSelectionError,
    load_json as load_issue_json,
    select_issue_requirements,
    validate_source_class_policy,
)

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT.parents[1]
REQUIRED_OPERATIONS = {
    "applicant_guidance": (
        "route_classification",
        "c23_guidance",
        "c27_reconciliation",
        "attack_angle_screen",
        "requested_output",
    ),
    "source_research": (
        "route_classification",
        "research_gate",
        "source_preflight",
        "requested_output",
    ),
    "no_case_assessment": ("route_classification", "requested_output"),
}
OPERATION_EVIDENCE_KINDS = {
    "route_classification": {"conversation_record"},
    "c23_guidance": {"conversation_record", "source_record", "local_artifact"},
    "c27_reconciliation": {"conversation_record", "local_artifact"},
    "attack_angle_screen": {"conversation_record", "local_artifact"},
    "requested_output": {"conversation_record"},
    "c3_module_pair_conformance": {"module_conformance"},
    "c3_case_geography_match": {"conversation_record"},
    "research_gate": {"research_gate"},
    "source_preflight": {"source_preflight"},
}
CLOSED_C27_STATUSES = {"assessed", "not_applicable"}
ISSUE_MATRIX_PATH = ROOT / "references" / "consultation-issue-routing.json"
ISSUE_REGISTRY_PATH = ROOT / "references" / "state-engine" / "check-registry.json"
ROUTE_GATE_VERSION = "0.7.0"
TYPED_RECEIPT_SCHEMAS = {"0.6.0", "0.7.0"}
INFORMATIONAL_ROUTE_SCOPE_STATUSES = {
    "not_selected_outcome_mismatch", "not_selected_no_formal_outcome",
    "not_selected_outcome_unverified", "not_selected_signal_missing",
}


class RouteGateError(ValueError):
    pass


STRATEGY_TRIGGER_IDS = {
    "adverse_decision_or_denial",
    "urgent_deadline_or_clock",
    "procedural_access_or_lodgement_problem",
    "source_supported_preventive_opportunity",
    "user_requested_strategy",
}
STRATEGY_TRIGGER_SIGNALS = {
    "adverse_decision_or_denial": {
        "formal_refusal_issued", "outcome_article18_not_competent",
        "outcome_article19_inadmissible", "outcome_article32_substantive_refusal",
        "prior_refusal_or_status_change",
    },
    "urgent_deadline_or_clock": {
        "appeal_deadline_risk", "processing_delay_or_deadline_question",
    },
    "procedural_access_or_lodgement_problem": {
        "pre_lodgement_access_obstruction", "appointment_delay", "lodgement_disputed",
        "physical_exclusion_or_staff_treatment", "digital_only_access_requirement",
        "mandatory_provider_pre_screening",
    },
    "user_requested_strategy": {"preventive_strategy_requested"},
}
GENERIC_STRATEGY_TEXT = {
    "unknown", "unclear", "not enough information", "not enough info",
    "more information is needed", "more research is needed", "cannot determine",
    "unable to assess", "n/a", "not applicable",
}


def _require_specific_strategy_text(value: str, label: str) -> None:
    normalized = " ".join(value.casefold().split()).strip(" .;:")
    if normalized in GENERIC_STRATEGY_TEXT or len(set(re.findall(r"[a-z0-9]+", normalized))) < 5:
        raise RouteGateError(f"strategy_{label}_too_generic")
    if any(phrase in normalized for phrase in (
        "more information is needed", "more research is needed", "not enough information",
        "not enough info", "cannot determine from the information provided",
    )):
        raise RouteGateError(f"strategy_{label}_too_generic")


def check_strategy_assessment(route: dict, evidence_index: dict[str, dict], gaps: list[str]) -> str | None:
    """Check the consultation strategy screen against the shared issue/evidence record."""
    if route.get("schema_version") != "0.7.0":
        return None
    strategy = route.get("strategy_assessment")
    if not isinstance(strategy, dict):
        raise RouteGateError("strategy_assessment_missing")

    reviews = strategy["trigger_reviews"]
    by_id = {item["trigger_id"]: item for item in reviews}
    if len(by_id) != len(reviews) or set(by_id) != STRATEGY_TRIGGER_IDS:
        raise RouteGateError("strategy_trigger_review_set_incomplete_or_duplicate")
    signal_evidence: dict[str, set[str]] = {trigger: set() for trigger in STRATEGY_TRIGGER_IDS}
    declared_signals: set[str] = set()
    for issue in route.get("issues", []):
        issue_signals = set(issue.get("signal_ids", []))
        declared_signals.update(issue_signals)
        for trigger_id, signal_ids in STRATEGY_TRIGGER_SIGNALS.items():
            if signal_ids.intersection(issue_signals):
                signal_evidence[trigger_id].add(issue["evidence_ref"])

    for trigger_id, review in by_id.items():
        _require_specific_strategy_text(review["reason"], f"trigger_reason:{trigger_id}")
        refs = review["evidence_refs"]
        if any(ref not in evidence_index for ref in refs):
            raise RouteGateError(f"strategy_trigger_evidence_dangling:{trigger_id}")
        required_refs = signal_evidence[trigger_id]
        if required_refs and review["status"] != "triggered":
            raise RouteGateError(f"strategy_trigger_signal_not_screened_as_triggered:{trigger_id}")
        if required_refs and not required_refs.issubset(set(refs)):
            raise RouteGateError(f"strategy_trigger_signal_evidence_missing:{trigger_id}")
        if review["status"] == "triggered" and not refs:
            raise RouteGateError(f"strategy_trigger_evidence_missing:{trigger_id}")
        if trigger_id == "source_supported_preventive_opportunity" and review["status"] == "triggered":
            if not any(evidence_index[ref].get("kind") == "source_record" for ref in refs):
                raise RouteGateError("strategy_source_supported_trigger_requires_source_evidence")
        if trigger_id == "user_requested_strategy" and "preventive_strategy_requested" in declared_signals:
            if not any(evidence_index[ref].get("kind") == "conversation_record" for ref in refs):
                raise RouteGateError("strategy_user_request_requires_conversation_evidence")

    mode = strategy["mode"]
    statuses = {item["status"] for item in reviews}
    triggered = any(item["status"] == "triggered" for item in reviews)
    unknown = any(item["status"] == "unknown" for item in reviews)
    if route["request_kind"] == "source_research":
        if mode != "not_applicable" or statuses != {"not_applicable"}:
            raise RouteGateError("strategy_not_applicable_required_for_source_research")
        _require_specific_strategy_text(strategy["summary"], "summary")
        _require_specific_strategy_text(strategy["not_applicable_reason"], "not_applicable_reason")
        return mode
    if mode == "not_applicable":
        raise RouteGateError("strategy_not_applicable_for_applicant_guidance")

    action_fields = ("first_step", "purpose", "reassess_when")
    if triggered:
        if mode not in {"full", "limited"}:
            raise RouteGateError("strategy_triggered_without_actionable_mode")
        for field in action_fields:
            value = strategy.get(field)
            if not isinstance(value, str):
                raise RouteGateError(f"strategy_action_field_missing:{field}")
            _require_specific_strategy_text(value, field)
        if len(strategy["alternatives_considered"]) < 2:
            raise RouteGateError("strategy_action_alternatives_insufficient")
    if unknown and mode != "limited":
        raise RouteGateError("strategy_unknown_trigger_requires_limited_mode")
    if mode == "full" and (not triggered or unknown or "limitation" in strategy):
        raise RouteGateError("strategy_full_mode_inconsistent_with_trigger_review")
    if mode == "not_triggered":
        if triggered or unknown or statuses - {"not_triggered", "not_applicable"}:
            raise RouteGateError("strategy_not_triggered_mode_inconsistent_with_trigger_review")
        _require_specific_strategy_text(strategy["no_trigger_reason"], "no_trigger_reason")
    if mode == "limited":
        if not (triggered or unknown):
            raise RouteGateError("strategy_limited_mode_without_open_trigger")
        limitation = strategy["limitation"]
        for field in ("missing", "effect"):
            _require_specific_strategy_text(limitation[field], f"limitation_{field}")
        if any(ref not in evidence_index for ref in limitation["evidence_refs"]):
            raise RouteGateError("strategy_limitation_evidence_dangling")
        gaps.append(f"strategy_assessment:limited:{limitation['reason_code']}")
    _require_specific_strategy_text(strategy["summary"], "summary")
    return mode


def required_operations_for(route: dict) -> tuple[str, ...]:
    required = list(REQUIRED_OPERATIONS[route["request_kind"]])
    if route.get("schema_version") in {"0.4.0", "0.5.0", "0.6.0", "0.7.0"} and route["request_kind"] in {
        "applicant_guidance", "source_research",
    }:
        for operation_id in ("research_gate", "source_preflight", "attack_angle_screen"):
            if operation_id not in required:
                required.append(operation_id)
    return tuple(required)


def safe_relative_file(base: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise RouteGateError(f"{label}:absolute_path_not_allowed")
    if any(part in {"..", ""} for part in candidate.parts):
        raise RouteGateError(f"{label}:path_component_not_allowed")
    cursor = base
    for part in candidate.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RouteGateError(f"{label}:symlink_not_allowed")
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as error:
        raise RouteGateError(f"{label}:path_outside_allowed_root") from error
    if not resolved.is_file():
        raise RouteGateError(f"{label}:file_not_found")
    return resolved


def strict_receipt(route: dict) -> bool:
    return route.get("schema_version") in {"0.5.0", "0.6.0", "0.7.0"}


def check_c27_records(route: dict, registry: dict, gaps: list[str]) -> int:
    if route["request_kind"] == "no_case_assessment":
        if route["c27_checks"] or route.get("issues"):
            raise RouteGateError("non_consultation_receipt_contains_case_assessment")
        return 0
    strict = strict_receipt(route)
    typed_scopes = {
        item["scope_ref"]: item
        for item in route.get("proceedings", [])
    } if route.get("schema_version") in TYPED_RECEIPT_SCHEMAS else {}
    check_specs = {item["check_id"]: item for item in registry["checks"]}
    procedure_scopes = {
        item["scope_id"]: set(item["procedure_types"])
        for item in registry.get("procedure_scopes", [])
    }
    seen: set[tuple[str, str]] = set()
    seen_assessments: set[str] = set()
    seen_occurrences: set[tuple[str, str, str]] = set()
    for item in route["c27_checks"]:
        record = item["record"]
        validate_route_check_record(record, registry)
        check_id = record["check_id"]
        check_scope_id = check_specs[check_id].get("procedure_scope_id")
        if check_scope_id and route.get("schema_version") not in TYPED_RECEIPT_SCHEMAS:
            raise RouteGateError("c27_procedure_scope_requires_receipt_0_6")
        if route.get("schema_version") in TYPED_RECEIPT_SCHEMAS:
            scope_ref = item["scope_ref"]
            context = typed_scopes.get(scope_ref)
            if context is None:
                raise RouteGateError("c27_scope_not_declared_as_proceeding")
            if (check_scope_id
                    and context["procedure_type"] not in procedure_scopes[check_scope_id]):
                if (record["status"] != "not_applicable"
                        or record.get("scope_exclusion") != "procedure_outside_scope"):
                    raise RouteGateError("c27_procedure_scoped_check_used_outside_scope")
        if strict:
            assessment_ref = item["assessment_ref"]
            if assessment_ref in seen_assessments:
                raise RouteGateError(f"c27_assessment_duplicate:{assessment_ref}")
            seen_assessments.add(assessment_ref)
            binding_kind = item.get("binding_kind")
            bound_issue_refs = item.get("bound_issue_refs")
            if not isinstance(bound_issue_refs, list):
                raise RouteGateError("c27_assessment_issue_bindings_invalid")
            if binding_kind == "issue_specific" and len(bound_issue_refs) != 1:
                raise RouteGateError("c27_issue_specific_binding_cardinality_invalid")
            if binding_kind == "proceeding_shared" and len(bound_issue_refs) < 2:
                raise RouteGateError("c27_shared_binding_cardinality_invalid")
            if binding_kind not in {"issue_specific", "proceeding_shared"}:
                raise RouteGateError("c27_binding_kind_invalid")
            for issue_ref in bound_issue_refs:
                occurrence = (item["scope_ref"], check_id, issue_ref)
                if occurrence in seen_occurrences:
                    raise RouteGateError(
                        "c27_assessment_occurrence_duplicate:"
                        f"{item['scope_ref']}:{check_id}:{issue_ref}"
                    )
                seen_occurrences.add(occurrence)
        else:
            key = (item["scope_ref"], check_id)
            if key in seen:
                raise RouteGateError(f"c27_check_duplicate:{item['scope_ref']}:{check_id}")
            seen.add(key)
        if record["status"] not in CLOSED_C27_STATUSES:
            gaps.append(f"c27:{item['scope_ref']}:{check_id}:{record['status']}")
    if route["request_kind"] == "applicant_guidance" and not route["c27_checks"]:
        gaps.append("c27:no_selected_checks_recorded")
    return len(seen_assessments) if strict else len(seen)


def validate_issue_c27_bindings(route: dict) -> dict[str, set[str]]:
    """Return checks bound to each issue after validating exact receipt links.

    A shared proceeding fact may bind one assessment to several issues, but
    issue-specific assessments cannot be borrowed across those issue records.
    """
    if not strict_receipt(route):
        return {}
    issues = route.get("issues")
    checks = route.get("c27_checks")
    if not isinstance(issues, list) or not isinstance(checks, list):
        raise RouteGateError("c27_issue_binding_records_missing")
    issue_by_ref = {item["issue_ref"]: item for item in issues}
    if len(issue_by_ref) != len(issues):
        raise RouteGateError("issue_duplicate")
    check_by_ref: dict[str, dict] = {}
    for check in checks:
        assessment_ref = check["assessment_ref"]
        if assessment_ref in check_by_ref:
            raise RouteGateError(f"c27_assessment_duplicate:{assessment_ref}")
        check_by_ref[assessment_ref] = check

    actual_by_issue: dict[str, set[str]] = {issue_ref: set() for issue_ref in issue_by_ref}
    for check in checks:
        assessment_ref = check["assessment_ref"]
        scope_ref = check["scope_ref"]
        bound_refs = check["bound_issue_refs"]
        if check["binding_kind"] == "proceeding_shared":
            if not isinstance(check.get("shared_basis"), dict):
                raise RouteGateError("c27_shared_assessment_basis_missing")
        elif check.get("shared_basis") is not None:
            raise RouteGateError("c27_issue_specific_shared_basis_not_allowed")
        for issue_ref in bound_refs:
            issue = issue_by_ref.get(issue_ref)
            if issue is None:
                raise RouteGateError("c27_assessment_issue_reference_dangling")
            if issue["scope_ref"] != scope_ref:
                raise RouteGateError("c27_assessment_scope_mismatch")
            if assessment_ref not in issue["c27_assessment_refs"]:
                raise RouteGateError("c27_assessment_binding_asymmetry")
            actual_by_issue[issue_ref].add(check["record"]["check_id"])

    for issue_ref, issue in issue_by_ref.items():
        refs = issue["c27_assessment_refs"]
        if len(refs) != len(set(refs)):
            raise RouteGateError(f"c27_assessment_reference_duplicate:{issue_ref}")
        for assessment_ref in refs:
            check = check_by_ref.get(assessment_ref)
            if check is None:
                raise RouteGateError("c27_assessment_reference_dangling")
            if issue_ref not in check["bound_issue_refs"]:
                raise RouteGateError("c27_assessment_binding_asymmetry")
            if issue["scope_ref"] != check["scope_ref"]:
                raise RouteGateError("c27_assessment_scope_mismatch")
    return actual_by_issue


def issue_c27_statuses(route: dict) -> dict[str, dict[str, str]]:
    """Map each bound atomic check to its recorded status for each issue."""
    result: dict[str, dict[str, str]] = {}
    for check in route.get("c27_checks", []):
        check_id = check["record"]["check_id"]
        status = check["record"]["status"]
        for issue_ref in check.get("bound_issue_refs", []):
            result.setdefault(issue_ref, {})[check_id] = status
    return result


def record_issue_c27_gaps(
    issue_ref: str, required_check_ids: list[str], actual_check_ids: set[str],
    check_statuses: dict[str, str], gaps: list[str],
) -> list[str]:
    """Record missing/open required checks with issue-specific provenance."""
    missing = sorted(set(required_check_ids) - actual_check_ids)
    for check_id in missing:
        gaps.append(f"issue:{issue_ref}:c27_required_check_missing:{check_id}")
    open_checks = []
    for check_id in sorted(set(required_check_ids) & actual_check_ids):
        status = check_statuses.get(check_id, "missing")
        if status not in CLOSED_C27_STATUSES:
            open_checks.append(check_id)
            gaps.append(f"issue:{issue_ref}:c27_check_open:{check_id}:{status}")
    return open_checks


def check_evidence_index(route: dict, receipt_dir: Path,
                         module_reports: list[dict], research_reports: list[dict],
                         source_preflight_reports: list[dict]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for item in route["evidence"]:
        ref = item["evidence_ref"]
        if ref in index:
            raise RouteGateError(f"evidence_duplicate:{ref}")
        index[ref] = item
        if item["kind"] == "local_artifact":
            artifact = safe_relative_file(receipt_dir, item["artifact_path"], "evidence_artifact")
            actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if actual != item["sha256"]:
                raise RouteGateError(f"evidence_digest_mismatch:{ref}")

    module_results = {item["pair_ref"]: item for item in module_reports}
    research_results = {
        item.get("research_ref"): report
        for item, report in zip(route["research_artifacts"], research_reports)
        if item.get("research_ref")
    }
    preflight_results = {item.get("preflight_id"): item for item in source_preflight_reports
                         if item.get("preflight_id")}
    for item in index.values():
        if item["kind"] == "module_conformance":
            report = module_results.get(item["subject_ref"])
            if report is None or report.get("status") != "conformant":
                raise RouteGateError(f"evidence_module_report_unverified:{item['evidence_ref']}")
        elif item["kind"] == "research_gate":
            report = research_results.get(item["subject_ref"])
            if report is None or report.get("status") != "valid":
                raise RouteGateError(f"evidence_research_report_unverified:{item['evidence_ref']}")
        elif item["kind"] == "source_preflight":
            report = preflight_results.get(item["subject_ref"])
            if report is None or report.get("validation_status") != "valid":
                raise RouteGateError(f"evidence_source_preflight_unverified:{item['evidence_ref']}")

    def require_ref(ref: str, allowed: set[str] | None = None) -> dict:
        item = index.get(ref)
        if item is None:
            raise RouteGateError(f"evidence_reference_dangling:{ref}")
        if allowed is not None and item["kind"] not in allowed:
            raise RouteGateError(f"evidence_reference_wrong_kind:{ref}")
        return item

    for value in route["classification"].values():
        require_ref(value["evidence_ref"], {"conversation_record"})
    require_ref(route["conditional_review"]["evidence_ref"], {"conversation_record"})
    for operation in route["operations"]:
        for ref in operation["evidence_refs"]:
            require_ref(ref)
    for item in route["c27_checks"]:
        record = item["record"]
        for ref in record["evidence_refs"]:
            require_ref(ref, {"conversation_record", "local_artifact"})
        for ref in record["source_refs"]:
            require_ref(ref, {"source_record", "local_artifact"})
        if strict_receipt(route) and item.get("binding_kind") == "proceeding_shared":
            require_ref(item["shared_basis"]["evidence_ref"], {"conversation_record", "local_artifact"})
    if strict_receipt(route):
        for issue in route.get("issues", []):
            require_ref(issue["evidence_ref"], {"conversation_record"})
            for ref in issue["conditional_closure"]["evidence_refs"]:
                require_ref(ref, {"conversation_record", "source_record", "local_artifact", "source_preflight"})
            for exclusion in issue["source_owner_exclusions"]:
                require_ref(exclusion["evidence_ref"], {"conversation_record"})
            for obligation in issue["source_obligations"]:
                require_ref(obligation["evidence_ref"], {"conversation_record", "source_preflight"})
            for topic in issue["attack_angle_reviews"]:
                require_ref(topic["evidence_ref"], {"conversation_record"})
                for state in topic["screening"]["predicate_states"]:
                    require_ref(state["evidence_ref"], {"conversation_record"})
    for pair in route["module_pairs"]:
        if not any(item["kind"] == "module_conformance" and
                   item.get("subject_ref") == pair["pair_ref"]
                   for item in index.values()):
            raise RouteGateError(f"module_pair_evidence_missing:{pair['pair_ref']}")
    for artifact in route["research_artifacts"]:
        if not any(item["kind"] == "research_gate" and
                   item.get("subject_ref") == artifact["research_ref"]
                   for item in index.values()):
            raise RouteGateError(f"research_artifact_evidence_missing:{artifact['research_ref']}")
        if artifact.get("preflight_ref") and not any(
            item["kind"] == "source_preflight" and item.get("subject_ref") == artifact["preflight_ref"]
            for item in index.values()
        ):
            raise RouteGateError(f"source_preflight_evidence_missing:{artifact['preflight_ref']}")
    return index


def validate_attack_angle_screen(
    issue: dict, topic: dict, expected_topic: dict, evidence_index: dict[str, dict],
) -> None:
    """Validate route selection separately from adverse-topic screening.

    Route signals select work for review. They do not establish the adverse
    condition under review. Candidate outcomes therefore require a separately
    bound topic-specific adverse predicate. Generic topics without such a
    mapping remain unresolved and block a comprehensive claim.
    """
    issue_ref = issue["issue_ref"]
    route_id = topic["route_id"]
    evidence = evidence_index.get(topic["evidence_ref"])
    if not evidence or evidence["kind"] != "conversation_record":
        raise RouteGateError(f"issue_attack_review_evidence_invalid:{issue_ref}:{route_id}")
    for key in ("trigger_any_signal_ids", "trigger_all_signal_ids"):
        expected = sorted(expected_topic.get(key, []))
        actual = topic.get(key)
        if not isinstance(actual, list) or sorted(actual) != expected:
            raise RouteGateError(f"issue_attack_screen_predicate_binding_mismatch:{issue_ref}:{route_id}:{key}")
    expected_any = expected_topic.get("trigger_any_signal_ids", [])
    expected_all = expected_topic.get("trigger_all_signal_ids", [])
    if not expected_any and not expected_all:
        raise RouteGateError(f"issue_attack_screen_predicate_binding_empty:{issue_ref}:{route_id}")
    screening = topic.get("screening")
    if not isinstance(screening, dict):
        raise RouteGateError(f"issue_attack_screen_missing:{issue_ref}:{route_id}")
    states: dict[str, str] = {}
    for state_record in screening["predicate_states"]:
        signal_id = state_record["signal_id"]
        if signal_id in states:
            raise RouteGateError(f"issue_attack_screen_predicate_duplicate:{issue_ref}:{route_id}")
        states[signal_id] = state_record["state"]
        predicate_evidence = evidence_index.get(state_record["evidence_ref"])
        if not predicate_evidence or predicate_evidence["kind"] != "conversation_record":
            raise RouteGateError(f"issue_attack_screen_evidence_invalid:{issue_ref}:{route_id}")
    expected_trigger_ids = set(expected_any) | set(expected_all)
    if set(states) != expected_trigger_ids:
        raise RouteGateError(f"issue_attack_screen_predicate_binding_mismatch:{issue_ref}:{route_id}:states")
    issue_signals = set(issue["signal_ids"])
    if any(
        (signal_id in issue_signals and state != "present")
        or (signal_id not in issue_signals and state == "present")
        for signal_id, state in states.items()
    ):
        raise RouteGateError(f"issue_attack_route_trigger_state_conflicts_with_issue:{issue_ref}:{route_id}")

    def evaluate(states_by_id: dict[str, str], predicate_ids: list[str]) -> bool | None:
        """All declared topic predicates must be present to support a candidate."""
        if not predicate_ids:
            return None
        values = [states_by_id[predicate_id] for predicate_id in predicate_ids]
        if "absent" in values:
            return False
        if "unknown" in values:
            return None
        return True

    expected_adverse_ids = sorted(expected_topic.get("adverse_predicate_ids", []))
    if sorted(topic.get("adverse_predicate_ids", [])) != expected_adverse_ids:
        raise RouteGateError(f"issue_attack_adverse_predicate_binding_mismatch:{issue_ref}:{route_id}")
    raw_adverse_states = screening.get("adverse_predicate_states")
    if not isinstance(raw_adverse_states, list):
        raise RouteGateError(f"issue_attack_adverse_predicate_states_missing:{issue_ref}:{route_id}")
    adverse_states: dict[str, str] = {}
    for state_record in raw_adverse_states:
        predicate_id = state_record["predicate_id"]
        if predicate_id in adverse_states:
            raise RouteGateError(f"issue_attack_adverse_predicate_duplicate:{issue_ref}:{route_id}")
        adverse_states[predicate_id] = state_record["state"]
        predicate_evidence = evidence_index.get(state_record["evidence_ref"])
        if not predicate_evidence or predicate_evidence["kind"] != "conversation_record":
            raise RouteGateError(f"issue_attack_adverse_predicate_evidence_invalid:{issue_ref}:{route_id}")
    if set(adverse_states) != set(expected_adverse_ids):
        raise RouteGateError(f"issue_attack_adverse_predicate_binding_mismatch:{issue_ref}:{route_id}")

    predicate_result = evaluate(adverse_states, expected_adverse_ids)
    outcome = topic["outcome"]
    if outcome == "candidate_issue_linked":
        linked_issue_ref = topic.get("linked_issue_ref")
        if not linked_issue_ref:
            raise RouteGateError(f"issue_attack_candidate_link_missing:{issue_ref}:{route_id}")
        if linked_issue_ref == issue_ref:
            raise RouteGateError(f"issue_attack_candidate_self_link:{issue_ref}:{route_id}")
    reason = screening["reason_code"]
    if not expected_adverse_ids:
        if outcome != "unresolved" or reason != "predicate_unmapped":
            raise RouteGateError(f"issue_attack_unmapped_predicate_must_remain_unresolved:{issue_ref}:{route_id}")
        return

    if outcome == "no_signal_identified":
        if (reason not in {"no_adverse_signal", "predicate_contradicted"}
                or predicate_result is not False):
            raise RouteGateError(f"issue_attack_negative_screen_unsupported:{issue_ref}:{route_id}")
    elif outcome == "unresolved":
        if reason not in {"evidence_missing", "scope_unclear"} or predicate_result is not None:
            raise RouteGateError(f"issue_attack_unresolved_screen_unsupported:{issue_ref}:{route_id}")
    elif outcome in {"candidate_issue_linked", "candidate_same_issue"}:
        if reason != "candidate_assessed" or predicate_result is not True:
            raise RouteGateError(f"issue_attack_candidate_screen_unsupported:{issue_ref}:{route_id}")


def validate_linked_attack_candidates(
    route: dict, issue_c27_actual: dict[str, set[str]],
    issue_c27_statuses: dict[str, dict[str, str]], gaps: list[str],
) -> None:
    """Require a separate declared issue and its own routed assessment trace."""
    issue_by_ref = {item["issue_ref"]: item for item in route.get("issues", [])}
    for issue in route.get("issues", []):
        for topic in issue.get("attack_angle_reviews", []):
            if topic.get("outcome") != "candidate_issue_linked":
                continue
            linked_ref = topic.get("linked_issue_ref")
            route_id = topic["route_id"]
            linked = issue_by_ref.get(linked_ref)
            if linked is None:
                gaps.append(f"issue:{issue['issue_ref']}:attack_angle_linked_issue_missing:{route_id}")
                continue
            if linked_ref == issue["issue_ref"]:
                raise RouteGateError(f"issue_attack_candidate_self_link:{issue['issue_ref']}:{route_id}")
            try:
                required = set(select_issue_requirements(linked["signal_ids"])["check_ids"])
            except IssueSelectionError as error:
                raise RouteGateError(f"issue_attack_linked_issue_invalid:{linked_ref}") from error
            actual = issue_c27_actual.get(linked_ref, set())
            statuses = issue_c27_statuses.get(linked_ref, {})
            required_closed = all(
                statuses.get(check_id) in CLOSED_C27_STATUSES
                for check_id in required
            )
            if not linked.get("c27_assessment_refs") or not required <= actual or not required_closed:
                gaps.append(
                    f"issue:{issue['issue_ref']}:attack_angle_linked_issue_assessment_missing:{route_id}"
                )


def validate_source_class_obligation(
    issue_ref: str, owner_id: str, obligation: dict,
    policy_requirement: dict, gaps: list[str],
) -> None:
    """Compare declared classes with the route/signal-derived minimum."""
    declared = set(obligation["required_source_classes"])
    required = set(policy_requirement.get("required_classes", []))
    excluded = set(policy_requirement.get("excluded_classes", []))
    if not required <= declared:
        gaps.append(
            f"issue:{issue_ref}:source_class_policy_required_missing:{owner_id}:"
            + ",".join(sorted(required - declared))
        )
    if declared & excluded:
        raise RouteGateError(f"issue_source_class_policy_exclusion_violated:{issue_ref}:{owner_id}")
    if sorted(obligation["policy_excluded_source_classes"]) != sorted(excluded):
        raise RouteGateError(f"issue_source_class_exclusion_record_mismatch:{issue_ref}:{owner_id}")


def check_operation_evidence(route: dict, evidence_index: dict[str, dict],
                             gaps: list[str]) -> None:
    for operation in route["operations"]:
        allowed = OPERATION_EVIDENCE_KINDS.get(operation["operation_id"])
        if allowed is None:
            continue
        for ref in operation["evidence_refs"]:
            item = evidence_index[ref]
            if item["kind"] not in allowed:
                gaps.append(
                    f"operation:{operation['operation_id']}:"
                    f"evidence_kind_not_acceptable:{ref}"
                )


def _abstract_issue_map(state: dict, signal_ids: set[str]) -> dict[str, dict]:
    if state.get("manifest_version") != "0.1.0":
        raise RouteGateError("abstract_state_version_unsupported")
    result: dict[str, dict] = {}
    for item in state.get("issues", []):
        issue_ref = item["issue_ref"]
        if issue_ref in result:
            raise RouteGateError("abstract_state_issue_duplicate")
        signal_states: dict[str, str] = {}
        for signal in item["signal_states"]:
            signal_id = signal["signal_id"]
            if signal_id not in signal_ids:
                raise RouteGateError("abstract_state_signal_unknown")
            if signal_id in signal_states:
                raise RouteGateError("abstract_state_signal_duplicate")
            if signal["state"] not in {"present", "absent", "unknown"}:
                raise RouteGateError("abstract_state_signal_state_invalid")
            signal_states[signal_id] = signal["state"]
        if not signal_states:
            raise RouteGateError("abstract_state_signal_states_missing")
        result[issue_ref] = {
            "scope_ref": item["scope_ref"],
            "signal_ids": sorted(
                signal_id for signal_id, value in signal_states.items() if value == "present"
            ),
            "signal_states": sorted(signal_states.items()),
        }
        for key in (
            "procedure_type", "administrative_outcome_classification",
            "administrative_outcome_source", "post_issuance_event_type",
            "post_issuance_event_source",
        ):
            if key in item:
                result[issue_ref][key] = item[key]
    return result


def validate_abstract_revision(route: dict, gaps: list[str]) -> set[str]:
    """Derive deltas from opaque issue/scope/signal snapshots, not a flag."""
    if not strict_receipt(route):
        return set()
    revision = route["revision_control"]
    try:
        matrix = load_issue_json(ISSUE_MATRIX_PATH)
        signal_defs = {
            item["signal_id"] for item in matrix["signal_catalog"]
        }
    except (IssueSelectionError, KeyError, TypeError) as error:
        raise RouteGateError("abstract_revision_catalogue_unavailable") from error

    current = _abstract_issue_map(revision["current_abstract_state"], signal_defs)
    declared = {}
    typed_scopes = {
        item["scope_ref"]: item for item in route.get("proceedings", [])
    } if route.get("schema_version") in TYPED_RECEIPT_SCHEMAS else {}
    for issue in route["issues"]:
        item = {
            "scope_ref": issue["scope_ref"],
            "signal_ids": sorted(issue["signal_ids"]),
        }
        if route.get("schema_version") in TYPED_RECEIPT_SCHEMAS:
            context = typed_scopes.get(issue["scope_ref"])
            if context is None:
                raise RouteGateError("abstract_state_issue_scope_undeclared")
            item["procedure_type"] = context["procedure_type"]
            outcome = issue.get("administrative_outcome")
            if outcome:
                item["administrative_outcome_classification"] = outcome["classification"]
                item["administrative_outcome_source"] = outcome["source"]
            event = issue.get("post_issuance_event")
            if event:
                item["post_issuance_event_type"] = event["event_type"]
                item["post_issuance_event_source"] = event["source"]
        declared[issue["issue_ref"]] = item
    declared_current = {
        issue_ref: {
            key: value for key, value in item.items()
            if key in {
                "scope_ref", "signal_ids", "procedure_type",
                "administrative_outcome_classification", "administrative_outcome_source",
                "post_issuance_event_type", "post_issuance_event_source",
            }
        }
        for issue_ref, item in current.items()
    }
    if declared_current != declared:
        raise RouteGateError("abstract_state_differs_from_declared_issue_records")

    previous_state = revision["previous_abstract_state"]
    if previous_state is None:
        if revision["change_detection_status"] != "previous_state_unavailable":
            raise RouteGateError("abstract_revision_status_mismatch")
        if route["invocation"].get("material_change") is not True:
            raise RouteGateError("abstract_revision_unavailable_must_remain_open")
        if any(revision.get(key) for key in (
            "added_issue_refs", "removed_issue_refs", "changed_issue_refs",
            "affected_scope_refs", "reassessed_scope_refs",
        )):
            raise RouteGateError("abstract_revision_delta_without_previous_state")
        if revision.get("removed_issue_reviews"):
            raise RouteGateError("abstract_revision_removal_without_previous_state")
        gaps.append("abstract_revision_comparison_unavailable")
        return set()

    if revision["change_detection_status"] != "compared":
        raise RouteGateError("abstract_revision_status_mismatch")
    previous = _abstract_issue_map(previous_state, signal_defs)
    added = set(current) - set(previous)
    removed = set(previous) - set(current)
    changed = {ref for ref in set(current) & set(previous) if current[ref] != previous[ref]}
    expected_added = sorted(added)
    expected_removed = sorted(removed)
    expected_changed = sorted(changed)
    for key, expected in (
        ("added_issue_refs", expected_added),
        ("removed_issue_refs", expected_removed),
        ("changed_issue_refs", expected_changed),
    ):
        if revision[key] != expected:
            raise RouteGateError(f"abstract_revision_{key}_mismatch")
    changed_any = bool(added or removed or changed)
    if route["invocation"].get("material_change") is not changed_any:
        raise RouteGateError("material_change_declaration_mismatch")

    affected: set[str] = set()
    for issue_ref in added | changed:
        affected.add(current[issue_ref]["scope_ref"])
    for issue_ref in removed | changed:
        affected.add(previous[issue_ref]["scope_ref"])
    if revision["affected_scope_refs"] != sorted(affected):
        raise RouteGateError("abstract_revision_affected_scope_mismatch")

    reassessed = set(revision["reassessed_scope_refs"])
    if not reassessed <= affected:
        raise RouteGateError("material_change_reassessed_scope_not_affected")
    for scope_ref in sorted(affected - reassessed):
        gaps.append(f"material_change_scope_reassessment_pending:{scope_ref}")

    removal_records = revision["removed_issue_reviews"]
    if {item["issue_ref"] for item in removal_records} != removed:
        raise RouteGateError("abstract_revision_removed_issue_review_mismatch")
    for item in removal_records:
        if item["scope_ref"] != previous[item["issue_ref"]]["scope_ref"]:
            raise RouteGateError("abstract_revision_removed_issue_scope_mismatch")
        evidence = next((e for e in route["evidence"] if e["evidence_ref"] == item["evidence_ref"]), None)
        if not evidence or evidence["kind"] != "conversation_record" or evidence.get("record_scope") != "current_response":
            gaps.append(f"removed_issue_review_not_current:{item['issue_ref']}")
        if item["disposition"] == "merged_into_current_issue" and item["merged_into_issue_ref"] not in current:
            raise RouteGateError("abstract_revision_merge_target_missing")
    return affected


_PRIVACY_TEXT_KEYS = {
    "title", "missing", "effect", "reason", "scope_note", "exceptions_note",
    "question", "response_read_evidence", "conversation_read_evidence",
}
_PII_PATTERNS = (
    ("email_like_value", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("long_numeric_identifier", re.compile(r"(?<!\d)(?:\d[ -]?){8,}(?!\d)")),
    ("exact_date", re.compile(r"\b(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])\b")),
    ("travel_document_identifier", re.compile(r"\b[A-Z]{1,3}\d{6,10}\b", re.I)),
)


def validate_privacy_minimisation(route: dict) -> None:
    """Reject a small set of obvious identifiers in strict free-text fields."""
    if not strict_receipt(route):
        return
    def walk(value, path=()):
        if isinstance(value, dict):
            for key, child in value.items():
                yield from walk(child, path + (key,))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from walk(child, path + (str(index),))
        elif isinstance(value, str) and path and path[-1] in _PRIVACY_TEXT_KEYS:
            for label, pattern in _PII_PATTERNS:
                if pattern.search(value):
                    raise RouteGateError(
                        "privacy_minimisation_failed:" + ".".join(path) + ":" + label
                    )
    for _ in walk(route):
        pass


def check_declared_issues(route: dict, evidence_index: dict[str, dict],
                          source_preflight_reports: list[dict], gaps: list[str]) -> list[dict]:
    """Reconcile issue signals to C27, owner-specific sources and attack topics.

    Earlier receipts may omit issues. Strict version 0.5.0 checks per-issue
    C27 occurrence bindings, policy-derived source classes and linked attack
    records, but it still cannot discover an omitted issue or validate whether
    the selected signal set is legally complete.
    """
    issues = route.get("issues")
    if issues is None:
        return []
    try:
        matrix = load_issue_json(ISSUE_MATRIX_PATH)
        registry_data = load_issue_json(ISSUE_REGISTRY_PATH)
    except IssueSelectionError as error:
        raise RouteGateError("issue_routing_configuration_invalid") from error
    outcome_signal_by_class = {
        item["required_outcome_classification"]: item["when_any_signal"][0]
        for item in matrix.get("routes", [])
        if item.get("required_outcome_classification")
        and len(item.get("when_any_signal", [])) == 1
    }

    version = route.get("schema_version")
    strict = version in {"0.4.0", "0.5.0", "0.6.0", "0.7.0"}
    v05 = version in {"0.5.0", "0.6.0", "0.7.0"}
    if (version == "0.4.0" and route.get("revision_control") is not None
            and route.get("invocation", {}).get("material_change") is not True):
        raise RouteGateError("revision_control_without_material_change")
    if version == "0.4.0" and route.get("invocation", {}).get("material_change") is True:
        revision = route.get("revision_control")
        if not isinstance(revision, dict):
            raise RouteGateError("material_change_revision_control_missing")
        affected_scopes = set(revision["affected_scope_refs"])
        reassessed_scopes = set(revision["reassessed_scope_refs"])
        declared_scopes = {item["scope_ref"] for item in issues}
        if not affected_scopes <= declared_scopes:
            raise RouteGateError("material_change_scope_not_declared")
        if not reassessed_scopes <= affected_scopes:
            raise RouteGateError("material_change_reassessed_scope_not_affected")
        for scope_ref in sorted(affected_scopes - reassessed_scopes):
            gaps.append(f"material_change_scope_reassessment_pending:{scope_ref}")
    seen_issue_refs: set[str] = set()
    actual_by_scope: dict[str, set[str]] = {}
    for item in route["c27_checks"]:
        actual_by_scope.setdefault(item["scope_ref"], set()).add(item["record"]["check_id"])
    issue_by_ref = {item["issue_ref"]: item for item in issues}
    typed_scopes: dict[str, dict] = {}
    if version in TYPED_RECEIPT_SCHEMAS:
        for proceeding in route["proceedings"]:
            scope_ref = proceeding["scope_ref"]
            if scope_ref in typed_scopes:
                raise RouteGateError("proceeding_scope_duplicate")
            if proceeding["procedure_type"] not in PROCEDURE_TYPES:
                raise RouteGateError("proceeding_procedure_type_unknown")
            if proceeding["evidence_ref"] not in evidence_index:
                raise RouteGateError("proceeding_evidence_reference_dangling")
            if evidence_index[proceeding["evidence_ref"]]["kind"] not in {
                "conversation_record", "local_artifact",
            }:
                raise RouteGateError("proceeding_evidence_kind_invalid")
            typed_scopes[scope_ref] = proceeding
        for proceeding in typed_scopes.values():
            parent_ref = proceeding.get("parent_scope_ref")
            if parent_ref is not None and parent_ref not in typed_scopes:
                raise RouteGateError("proceeding_parent_scope_unknown")
            if parent_ref == proceeding["scope_ref"]:
                raise RouteGateError("proceeding_parent_scope_self_link")
            if proceeding["procedure_type"] == "visa_appeal" and not parent_ref:
                gaps.append(
                    f"proceeding:{proceeding['scope_ref']}:underlying_application_proceeding_unlinked"
                )
            elif (proceeding["procedure_type"] == "visa_appeal"
                  and typed_scopes[parent_ref]["procedure_type"] not in {
                      "ordinary_short_stay_visa", "eu_family_entry_visa",
                      "national_long_stay_visa",
                  }):
                gaps.append(
                    f"proceeding:{proceeding['scope_ref']}:parent_is_not_a_visa_application"
                )
        if any(item["scope_ref"] not in typed_scopes for item in issues):
            raise RouteGateError("issue_scope_not_declared_as_proceeding")
    issue_c27_actual = validate_issue_c27_bindings(route) if v05 else {}
    issue_c27_status_by_issue = issue_c27_statuses(route) if v05 else {}
    if v05:
        for check in route["c27_checks"]:
            if check["binding_kind"] == "proceeding_shared":
                basis = check["shared_basis"]
                evidence = evidence_index.get(basis["evidence_ref"])
                if not evidence or evidence["kind"] not in {"conversation_record", "local_artifact"}:
                    raise RouteGateError("c27_shared_assessment_basis_invalid")
    preflight_by_id = {
        report.get("preflight_id"): report
        for report in source_preflight_reports
        if report.get("preflight_id")
    }
    declared_issue_refs = {item["issue_ref"] for item in issues}
    all_source_owners = set((matrix.get("source_owners") or {}).keys())
    issue_reports: list[dict] = []
    scoped_signals = {
        "outcome_article18_not_competent", "outcome_article19_inadmissible",
        "outcome_article32_substantive_refusal", "mandatory_provider_pre_screening",
        "lodgement_disputed", "post_issuance_event", "withdrawal_or_transfer_event",
    }
    if version not in TYPED_RECEIPT_SCHEMAS and any(
        scoped_signals.intersection(item.get("signal_ids", [])) for item in issues
    ):
        raise RouteGateError("outcome_routing_requires_receipt_0_6")

    if version == "0.4.0" and route.get("invocation", {}).get("material_change") is True:
        reassessed_scopes = set(route["revision_control"]["reassessed_scope_refs"])
        for scope_ref in sorted(reassessed_scopes):
            scoped_issues = [item for item in issues if item["scope_ref"] == scope_ref]
            for issue in scoped_issues:
                issue_evidence = evidence_index[issue["evidence_ref"]]
                if issue_evidence.get("record_scope") != "current_response":
                    gaps.append(f"material_change_issue_evidence_not_current:{issue['issue_ref']}")
                for obligation in issue["source_obligations"]:
                    obligation_evidence = evidence_index[obligation["evidence_ref"]]
                    if obligation_evidence.get("record_scope") != "current_response":
                        gaps.append(
                            f"material_change_source_evidence_not_current:{issue['issue_ref']}:"
                            f"{obligation['owner_id']}"
                        )
                for topic in issue["attack_angle_reviews"]:
                    topic_evidence = evidence_index[topic["evidence_ref"]]
                    if topic_evidence.get("record_scope") != "current_response":
                        gaps.append(
                            f"material_change_attack_evidence_not_current:{issue['issue_ref']}:"
                            f"{topic['route_id']}"
                        )
            for check in route["c27_checks"]:
                if check["scope_ref"] != scope_ref:
                    continue
                refs = check["record"]["evidence_refs"] + check["record"]["source_refs"]
                if not any(
                    evidence_index[ref].get("record_scope") == "current_response"
                    for ref in refs
                ):
                    gaps.append(
                        f"material_change_c27_evidence_not_current:{scope_ref}:"
                        f"{check['record']['check_id']}"
                    )
    elif v05 and route["invocation"].get("material_change") is True:
        revision = route["revision_control"]
        reassessed_scopes = set(revision["reassessed_scope_refs"])
        for scope_ref in sorted(reassessed_scopes):
            scoped_issues = [item for item in issues if item["scope_ref"] == scope_ref]
            for issue in scoped_issues:
                evidence_refs = [issue["evidence_ref"]]
                evidence_refs.extend(item["evidence_ref"] for item in issue["source_obligations"])
                evidence_refs.extend(item["evidence_ref"] for item in issue["source_owner_exclusions"])
                evidence_refs.extend(item["evidence_ref"] for item in issue["attack_angle_reviews"])
                evidence_refs.extend(
                    ref for ref in issue["conditional_closure"]["evidence_refs"]
                )
                if any(evidence_index[ref].get("record_scope") != "current_response" for ref in evidence_refs):
                    gaps.append(f"material_change_issue_evidence_not_current:{issue['issue_ref']}")
            for check in route["c27_checks"]:
                if check["scope_ref"] != scope_ref:
                    continue
                refs = check["record"]["evidence_refs"] + check["record"]["source_refs"]
                if not any(evidence_index[ref].get("record_scope") == "current_response" for ref in refs):
                    gaps.append(
                        f"material_change_c27_evidence_not_current:{scope_ref}:"
                        f"{check['record']['check_id']}"
                    )

    for issue in issues:
        issue_ref = issue["issue_ref"]
        scope_ref = issue["scope_ref"]
        if issue_ref in seen_issue_refs:
            raise RouteGateError(f"issue_duplicate:{issue_ref}")
        seen_issue_refs.add(issue_ref)
        evidence = evidence_index.get(issue["evidence_ref"])
        if evidence is None:
            raise RouteGateError(f"issue_evidence_reference_dangling:{issue_ref}")
        if evidence["kind"] != "conversation_record":
            raise RouteGateError(f"issue_evidence_wrong_kind:{issue_ref}")
        try:
            procedure_type = typed_scopes.get(scope_ref, {}).get("procedure_type")
            outcome_record = issue.get("administrative_outcome") or {}
            outcome_classification = outcome_record.get("classification")
            outcome_evidence = evidence_index.get(outcome_record.get("evidence_ref"))
            if outcome_record:
                if outcome_classification not in ADMINISTRATIVE_OUTCOMES:
                    raise RouteGateError(f"issue_outcome_classification_invalid:{issue_ref}")
                if outcome_evidence is None:
                    raise RouteGateError(f"issue_outcome_evidence_dangling:{issue_ref}")
                if outcome_classification == "other":
                    gaps.append(
                        f"issue:{issue_ref}:administrative_outcome_other_requires_manual_route_review"
                    )
                elif outcome_classification == "undetermined":
                    gaps.append(
                        f"issue:{issue_ref}:administrative_outcome_undetermined"
                    )
                formal_outcomes = {
                    "article18_not_competent", "article19_inadmissible",
                    "article32_substantive_refusal", "visa_issued",
                }
                if outcome_classification in formal_outcomes:
                    if outcome_record["source"] not in {
                        "document_seen", "authority_record_seen",
                    } or outcome_evidence["kind"] != "local_artifact":
                        gaps.append(
                            f"issue:{issue_ref}:administrative_outcome_official_record_unverified"
                        )
                        outcome_classification = None
            post_event = issue.get("post_issuance_event") or {}
            post_event_type = post_event.get("event_type")
            if post_event:
                if post_event_type not in POST_ISSUANCE_EVENTS:
                    raise RouteGateError(f"issue_post_issuance_event_type_invalid:{issue_ref}")
                post_evidence = evidence_index.get(post_event.get("evidence_ref"))
                if post_evidence is None:
                    raise RouteGateError(f"issue_post_issuance_evidence_dangling:{issue_ref}")
                if (post_event["source"] not in {"document_seen", "authority_record_seen"}
                        or post_evidence["kind"] != "local_artifact"):
                    gaps.append(f"issue:{issue_ref}:post_issuance_event_official_record_unverified")
                    post_event_type = None
            requirements = select_issue_requirements(
                issue["signal_ids"], matrix=matrix, registry=registry_data,
                procedure_type=procedure_type,
                administrative_outcome_classification=outcome_classification,
                post_issuance_event_type=post_event_type,
            )
        except IssueSelectionError as error:
            raise RouteGateError(f"issue_signal_selection_invalid:{issue_ref}:{error}") from error
        expected_outcome_signal = outcome_signal_by_class.get(outcome_classification)
        if (expected_outcome_signal
                and expected_outcome_signal not in issue["signal_ids"]):
            gaps.append(
                f"issue:{issue_ref}:administrative_outcome_signal_missing:{expected_outcome_signal}"
            )
        if v05:
            for status in requirements["route_scope_statuses"]:
                if (status["status"] != "applicable"
                        and status["status"] not in INFORMATIONAL_ROUTE_SCOPE_STATUSES):
                    gaps.append(
                        f"issue:{issue_ref}:route_scope:{status['route_id']}:{status['status']}"
                    )
            actual = issue_c27_actual.get(issue_ref, set())
            bound_statuses = issue_c27_status_by_issue.get(issue_ref, {})
        else:
            actual = actual_by_scope.get(scope_ref, set())
            bound_statuses = {}
        if v05:
            procedure_scoped_check_ids = {
                item["check_id"] for item in registry_data.get("checks", [])
                if item.get("procedure_scope_id")
            }
            misrouted_scoped_checks = sorted(
                check_id for check_id in (
                    (set(actual) & procedure_scoped_check_ids)
                    - set(requirements["check_ids"])
                )
                if bound_statuses.get(check_id) in {"assessed", "partial"}
            )
            if misrouted_scoped_checks:
                raise RouteGateError(
                    f"issue_procedure_scoped_check_not_selected:{issue_ref}:"
                    f"{misrouted_scoped_checks[0]}"
                )
            open_issue_check_ids = record_issue_c27_gaps(
                issue_ref, requirements["check_ids"], actual, bound_statuses, gaps
            )
        else:
            open_issue_check_ids = []
            for check_id in sorted(set(requirements["check_ids"]) - actual):
                gaps.append(f"issue:{issue_ref}:c27_required_check_missing:{check_id}")
        if issue["disposition"] in {"source_missing", "fact_missing"}:
            gaps.append(f"issue:{issue_ref}:disposition:{issue['disposition']}")
        if v05:
            closure = issue["conditional_closure"]
            for ref in closure["evidence_refs"]:
                if ref not in evidence_index:
                    raise RouteGateError(f"issue_conditional_evidence_dangling:{issue_ref}")
            if closure["status"] == "predicate_open":
                gaps.append(f"issue:{issue_ref}:conditional_predicate_open")
            if issue["disposition"] == "answered_conditionally" and closure["status"] not in {
                "evidence_resolved", "qualified_condition",
            }:
                gaps.append(f"issue:{issue_ref}:conditional_answer_closure_missing")
            if closure["status"] == "qualified_condition" and not closure["evidence_refs"]:
                raise RouteGateError(f"issue_conditional_closure_evidence_missing:{issue_ref}")

        issue_report = {
            "issue_ref": issue_ref,
            "scope_ref": scope_ref,
            "route_ids": requirements["route_ids"],
            "route_scope_statuses": requirements["route_scope_statuses"],
            "required_check_ids": requirements["check_ids"],
            "required_source_owner_ids": requirements["source_owner_ids"],
            "attack_angle_topic_count": len(requirements["attack_angle_topics"]),
            "attack_angle_topics": requirements["attack_angle_topics"],
        }
        if version in TYPED_RECEIPT_SCHEMAS:
            issue_report["procedure_type"] = procedure_type
            raw_outcome = issue.get("administrative_outcome") or {}
            issue_report["administrative_outcome_classification"] = raw_outcome.get("classification")
            issue_report["administrative_outcome_source"] = raw_outcome.get("source")
            issue_report["administrative_outcome_missing_evidence_reason"] = raw_outcome.get(
                "missing_evidence_reason"
            )
            issue_report["administrative_outcome_evidence_reference_recorded"] = bool(
                raw_outcome.get("evidence_ref")
            )
            issue_report["administrative_outcome_routing_classification"] = outcome_classification
            if not raw_outcome:
                outcome_routing_status = "not_recorded"
            elif raw_outcome.get("classification") == "undetermined":
                outcome_routing_status = "outcome_undetermined"
            elif raw_outcome.get("classification") == "other":
                outcome_routing_status = "other_outcome_requires_manual_route_review"
            elif outcome_classification is not None:
                outcome_routing_status = "available_for_routing"
            else:
                outcome_routing_status = "official_record_unverified"
            issue_report["administrative_outcome_routing_status"] = outcome_routing_status
            raw_post_event = issue.get("post_issuance_event") or {}
            issue_report["post_issuance_event_type"] = raw_post_event.get("event_type")
            issue_report["post_issuance_event_source"] = raw_post_event.get("source")
            issue_report["post_issuance_event_routing_type"] = post_event_type
            issue_report["post_issuance_event_routing_status"] = (
                "not_recorded" if not raw_post_event
                else "available_for_routing" if post_event_type is not None
                else "official_record_unverified"
            )
        if v05:
            issue_report["c27_check_statuses"] = {
                check_id: bound_statuses.get(check_id, "missing")
                for check_id in requirements["check_ids"]
            }
            issue_report["open_c27_check_ids"] = sorted(
                set(requirements["check_ids"]) - actual | set(open_issue_check_ids)
            )
        if strict:
            if not requirements["route_ids"]:
                gaps.append(f"issue:{issue_ref}:no_registered_route_for_declared_signals")
            if requirements["routing_review_status"] != "reviewed":
                gaps.append(f"issue:{issue_ref}:routing_metadata_independent_review_pending")

            obligation_by_owner: dict[str, dict] = {}
            for obligation in issue["source_obligations"]:
                owner_id = obligation["owner_id"]
                if owner_id in obligation_by_owner:
                    raise RouteGateError(f"issue_source_owner_duplicate:{issue_ref}:{owner_id}")
                if owner_id not in all_source_owners:
                    raise RouteGateError(f"issue_source_owner_unknown:{issue_ref}:{owner_id}")
                obligation_by_owner[owner_id] = obligation
            required_owner_ids = (
                requirements["strict_source_owner_ids"] if v05
                else requirements["source_owner_ids"]
            )
            missing_owners = sorted(set(required_owner_ids) - set(obligation_by_owner))
            for owner_id in missing_owners:
                gaps.append(f"issue:{issue_ref}:source_owner_obligation_missing:{owner_id}")

            if v05:
                if requirements["source_class_policy_review_status"] != "reviewed":
                    gaps.append(f"issue:{issue_ref}:source_class_policy_independent_review_pending")
                declared_exclusions = issue["source_owner_exclusions"]
                exclusion_by_owner = {}
                for exclusion in declared_exclusions:
                    owner_id = exclusion["owner_id"]
                    if owner_id in exclusion_by_owner:
                        raise RouteGateError(f"issue_source_owner_exclusion_duplicate:{issue_ref}")
                    exclusion_by_owner[owner_id] = exclusion
                    if exclusion["reason_code"] != "no_source_class_predicate_triggered":
                        raise RouteGateError(f"issue_source_owner_exclusion_reason_invalid:{issue_ref}")
                    if exclusion["evidence_ref"] != issue["evidence_ref"]:
                        raise RouteGateError(f"issue_source_owner_exclusion_evidence_mismatch:{issue_ref}")
                expected_exclusions = set(requirements["source_owner_exclusions"])
                if set(exclusion_by_owner) != expected_exclusions:
                    raise RouteGateError(f"issue_source_owner_exclusion_policy_mismatch:{issue_ref}")
                if set(obligation_by_owner) != set(required_owner_ids):
                    extra = set(obligation_by_owner) - set(required_owner_ids)
                    if extra:
                        raise RouteGateError(f"issue_source_owner_not_required_by_policy:{issue_ref}")
                    gaps.append(f"issue:{issue_ref}:source_owner_obligation_missing")
                issue_report["required_source_owner_ids"] = sorted(required_owner_ids)
                issue_report["source_owner_exclusions"] = sorted(expected_exclusions)
                issue_report["source_class_requirements"] = requirements["source_class_requirements"]

            for owner_id, obligation in obligation_by_owner.items():
                source_policy = requirements["source_class_requirements"].get(owner_id, {}) if v05 else {}
                if v05:
                    validate_source_class_obligation(
                        issue_ref, owner_id, obligation, source_policy, gaps
                    )
                evidence = evidence_index.get(obligation["evidence_ref"])
                if evidence is None:
                    raise RouteGateError(f"issue_source_evidence_dangling:{issue_ref}:{owner_id}")
                preflight_ref = obligation.get("preflight_ref")
                preflight = preflight_by_id.get(preflight_ref)
                if obligation["status"] == "reviewed":
                    if evidence["kind"] != "source_preflight" or evidence.get("subject_ref") != preflight_ref:
                        raise RouteGateError(f"issue_source_review_evidence_mismatch:{issue_ref}:{owner_id}")
                elif evidence["kind"] not in {"conversation_record", "source_preflight"}:
                    raise RouteGateError(f"issue_source_open_evidence_kind_invalid:{issue_ref}:{owner_id}")

                if obligation["status"] != "reviewed":
                    gaps.append(
                        f"issue:{issue_ref}:source_owner_status:{owner_id}:"
                        f"{obligation['status']}:{obligation['reason_code']}"
                    )
                if preflight_ref is None:
                    if obligation["status"] == "reviewed":
                        raise RouteGateError(f"issue_source_preflight_ref_missing:{issue_ref}:{owner_id}")
                    continue
                if preflight is None:
                    gaps.append(f"issue:{issue_ref}:source_preflight_unavailable:{owner_id}")
                    continue
                if preflight.get("contract_version") != "0.3.0":
                    gaps.append(f"issue:{issue_ref}:source_preflight_legacy_contract:{owner_id}")
                    continue
                matches = [
                    item for item in preflight.get("issues", [])
                    if item.get("consultation_issue_ref") == issue_ref
                    and item.get("consultation_scope_ref") == scope_ref
                    and item.get("owner_id") == owner_id
                ]
                if len(matches) != 1:
                    gaps.append(f"issue:{issue_ref}:source_preflight_issue_binding_missing:{owner_id}")
                    continue
                match = matches[0]
                if sorted(obligation["required_source_classes"]) != match.get("required_source_classes"):
                    raise RouteGateError(f"issue_source_classes_do_not_match_preflight:{issue_ref}:{owner_id}")
                if match.get("status") != "accounted_for_review" or match.get("outstanding"):
                    open_items = match.get("outstanding") or ["source_review_not_accounted"]
                    gaps.extend(
                        f"issue:{issue_ref}:source_preflight:{owner_id}:{item}"
                        for item in open_items
                    )
                if obligation["status"] == "reviewed" and match.get("status") != "accounted_for_review":
                    gaps.append(f"issue:{issue_ref}:source_owner_claim_exceeds_preflight:{owner_id}")

            actual_topics: dict[tuple[str, str], dict] = {}
            for topic_record in issue["attack_angle_reviews"]:
                key = (topic_record["route_id"], topic_record["topic"])
                if key in actual_topics:
                    raise RouteGateError(f"issue_attack_topic_duplicate:{issue_ref}:{key[0]}")
                actual_topics[key] = topic_record
                topic_evidence = evidence_index.get(topic_record["evidence_ref"])
                if topic_evidence is None or topic_evidence["kind"] != "conversation_record":
                    raise RouteGateError(f"issue_attack_review_evidence_invalid:{issue_ref}:{key[0]}")
                if topic_record["outcome"] == "unresolved":
                    gaps.append(f"issue:{issue_ref}:attack_angle_topic_unresolved:{key[0]}")
                    if (topic_record.get("screening", {}).get("reason_code") == "predicate_unmapped"):
                        gaps.append(f"issue:{issue_ref}:attack_angle_predicate_unmapped:{key[0]}")
                linked_issue = topic_record.get("linked_issue_ref")
                if topic_record["outcome"] == "candidate_issue_linked" and linked_issue not in declared_issue_refs:
                    gaps.append(f"issue:{issue_ref}:attack_angle_linked_issue_missing:{key[0]}")
                if topic_record["outcome"] == "candidate_issue_linked" and linked_issue == issue_ref:
                    raise RouteGateError(f"issue_attack_candidate_self_link:{issue_ref}:{key[0]}")
            expected_topics = {
                (item["route_id"], item["topic"])
                for item in requirements["attack_angle_topics"]
            }
            expected_topic_records = {
                (item["route_id"], item["topic"]): item
                for item in requirements["attack_angle_topics"]
            }
            missing_topics = sorted(expected_topics - set(actual_topics))
            extra_topics = sorted(set(actual_topics) - expected_topics)
            for route_id, _topic in missing_topics:
                gaps.append(f"issue:{issue_ref}:attack_angle_topic_missing:{route_id}")
            if extra_topics:
                raise RouteGateError(
                    f"issue_attack_topic_not_in_routing_catalog:{issue_ref}:{extra_topics[0][0]}"
                )
            for key, expected_topic in expected_topic_records.items():
                actual_topic = actual_topics.get(key)
                if actual_topic is None:
                    continue
                if v05:
                    validate_attack_angle_screen(issue, actual_topic, expected_topic, evidence_index)
                for field in (
                    "pathway_id", "trigger_route_id", "coverage_pattern_ids", "c27_check_ids",
                ):
                    expected_value = expected_topic.get(field)
                    actual_value = actual_topic.get(field)
                    if expected_value is None and actual_value is None:
                        continue
                    if isinstance(expected_value, list) and isinstance(actual_value, list):
                        binding_mismatch = sorted(expected_value) != sorted(actual_value)
                    else:
                        binding_mismatch = expected_value != actual_value
                    if binding_mismatch:
                        raise RouteGateError(
                            f"issue_attack_pathway_binding_mismatch:{issue_ref}:{key[0]}:{field}"
                        )
                if expected_topic.get("pathway_id") and requirements["pathway_review_status"] != "reviewed":
                    gaps.append(
                        f"issue:{issue_ref}:attack_pathway_metadata_independent_review_pending:"
                        f"{expected_topic['pathway_id']}"
                    )

        issue_reports.append(issue_report)
    if v05:
        validate_linked_attack_candidates(
            route, issue_c27_actual, issue_c27_status_by_issue, gaps
        )
        for issue in issues:
            for topic in issue["attack_angle_reviews"]:
                if topic["outcome"] != "candidate_issue_linked":
                    continue
                linked_ref = topic["linked_issue_ref"]
                linked = issue_by_ref.get(linked_ref)
                if linked is None:
                    raise RouteGateError(f"issue_attack_link_target_missing:{issue['issue_ref']}")
                linked_disposition = linked["disposition"]
                linked_closure = linked["conditional_closure"]["status"]
                linked_closed = (
                    linked_disposition == "answered_supported"
                    or (linked_disposition == "answered_conditionally" and linked_closure in {
                        "evidence_resolved", "qualified_condition",
                    })
                )
                linked_gaps = any(item.startswith(f"issue:{linked_ref}:") for item in gaps)
                if not linked_closed or linked_gaps:
                    gaps.append(
                        f"issue:{issue['issue_ref']}:attack_linked_candidate_not_closed:{topic['route_id']}"
                    )
    return issue_reports


def check_operations(route: dict, gaps: list[str],
                     required_operation_ids: tuple[str, ...]) -> dict[str, dict]:
    operations: dict[str, dict] = {}
    for item in route["operations"]:
        key = item["operation_id"]
        if key in operations:
            raise RouteGateError(f"operation_duplicate:{key}")
        operations[key] = item
        applies = item["applicability"] in {"required", "triggered"}
        if applies and item["status"] != "completed":
            gaps.append(f"operation:{key}:{item['status']}")
        if applies and not item["evidence_refs"]:
            gaps.append(f"operation:{key}:evidence_reference_missing")
        if item["applicability"] == "not_triggered" and item["status"] != "not_applicable":
            gaps.append(f"operation:{key}:not_triggered_without_not_applicable")
    for operation_id in required_operation_ids:
        operation = operations.get(operation_id)
        if operation is None:
            gaps.append(f"required_operation_missing:{operation_id}")
        elif operation["applicability"] != "required":
            gaps.append(f"required_operation_misclassified:{operation_id}")
    return operations


def check_module_pairs(route: dict, operations: dict[str, dict], gaps: list[str]) -> list[dict]:
    reports = []
    seen: set[str] = set()
    for pair in route["module_pairs"]:
        pair_ref = pair["pair_ref"]
        if pair_ref in seen:
            raise RouteGateError(f"module_pair_duplicate:{pair_ref}")
        seen.add(pair_ref)
        try:
            manifest = safe_relative_file(PLUGIN_ROOT, pair["manifest_path"], "module_manifest")
            export = safe_relative_file(PLUGIN_ROOT, pair["export_path"], "module_export")
            report = validate_paths(manifest, export)
            reports.append({"pair_ref": pair_ref, **report})
        except (ConformanceError, ContractError, OSError, RouteGateError) as error:
            gaps.append(f"module_pair:{pair_ref}:unavailable_or_nonconformant")
            reports.append({"pair_ref": pair_ref, "status": "rejected", "reason": str(error)})
    if route["module_pairs"]:
        op = operations.get("c3_module_pair_conformance")
        if op is None or op["applicability"] not in {"required", "triggered"}:
            gaps.append("c3_module_pair_conformance:operation_not_declared")
        elif op["status"] != "completed":
            gaps.append(f"c3_module_pair_conformance:{op['status']}")
        # The packaged case controller accepts only synthetic case records.
        # A model declaration cannot turn it into an approved real-case check.
        if route["request_kind"] == "applicant_guidance":
            match = operations.get("c3_case_geography_match")
            if match is None:
                gaps.append("c3_case_geography_match:not_recorded_for_selected_module")
            elif match["status"] != "unavailable":
                gaps.append("c3_case_geography_match:ordinary_case_execution_not_supported")
            elif match.get("reason_code") != "restricted_synthetic_input":
                gaps.append("c3_case_geography_match:restricted_input_reason_missing")
            else:
                gaps.append("c3_case_geography_match:required_check_unavailable")
    return reports


def check_research(route: dict, operations: dict[str, dict], gaps: list[str], receipt_dir: Path) -> list[dict]:
    reports = []
    op = operations.get("research_gate")
    if route["research_artifacts"] and (op is None or op["applicability"] not in {"required", "triggered"}):
        gaps.append("research_gate:operation_not_declared")
    if op and op["applicability"] in {"required", "triggered"} and not route["research_artifacts"]:
        gaps.append("research_gate:artifacts_missing")
    for index, artifact in enumerate(route["research_artifacts"], start=1):
        try:
            plan = safe_relative_file(receipt_dir, artifact["plan_path"], "research_plan")
            bundle = safe_relative_file(receipt_dir, artifact["bundle_path"], "research_bundle")
            report = validate_research(plan, bundle)
            report["research_ref"] = artifact["research_ref"]
            reports.append(report)
            if not report["research_complete"]:
                gaps.append(f"research_artifact:{index}:coverage_incomplete")
        except (ContractError, ResearchGateError, OSError, RouteGateError) as error:
            gaps.append(f"research_artifact:{index}:invalid_or_unavailable")
            reports.append({"status": "invalid", "reason": str(error)})
    if op and op["applicability"] in {"required", "triggered"} and op["status"] != "completed":
        gaps.append(f"research_gate:{op['status']}")
    return reports


def check_source_preflights(route: dict, operations: dict[str, dict], gaps: list[str],
                            receipt_dir: Path, research_reports: list[dict]) -> list[dict]:
    reports = []
    research_status = {item.get("research_ref"): item for item in research_reports
                       if item.get("research_ref")}
    operation = operations.get("source_preflight")
    if operation and operation["applicability"] in {"required", "triggered"} and not any(
        item.get("preflight_path") for item in route["research_artifacts"]
    ):
        gaps.append("source_preflight:artifacts_missing")
    for artifact in route["research_artifacts"]:
        if not artifact.get("preflight_path"):
            if route["request_kind"] == "source_research":
                gaps.append(f"source_preflight:missing_for_research:{artifact['research_ref']}")
            continue
        if research_status.get(artifact["research_ref"], {}).get("status") != "valid":
            gaps.append(f"source_preflight:research_not_valid:{artifact['research_ref']}")
            reports.append({"preflight_id": artifact["preflight_ref"],
                            "validation_status": "invalid", "status": "invalid",
                            "outstanding": ["research_artifact_not_valid"]})
            continue
        try:
            preflight_path = safe_relative_file(receipt_dir, artifact["preflight_path"], "source_preflight")
            plan = safe_relative_file(receipt_dir, artifact["plan_path"], "research_plan")
            bundle = safe_relative_file(receipt_dir, artifact["bundle_path"], "research_bundle")
            report = validate_source_preflight(preflight_path, plan, bundle)
            if report["preflight_id"] != artifact["preflight_ref"]:
                raise RouteGateError("source_preflight_reference_mismatch")
            reports.append(report)
            gaps.extend(f"source_preflight:{artifact['research_ref']}:{item}"
                        for item in report["outstanding"])
        except (ContractError, SourcePreflightError, ResearchGateError, OSError,
                RouteGateError, KeyError, TypeError) as error:
            gaps.append(f"source_preflight:{artifact['research_ref']}:invalid_or_unavailable")
            reports.append({"preflight_id": artifact["preflight_ref"],
                            "validation_status": "invalid", "status": "invalid",
                            "reason": str(error), "outstanding": []})
    return reports


def validate_route(path: Path) -> dict:
    receipt_bytes = path.read_bytes()
    try:
        route = json.loads(receipt_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RouteGateError("receipt_json_invalid") from error
    validate_obj("consultation-route-receipt", route)
    gaps: list[str] = []
    validate_privacy_minimisation(route)
    if strict_receipt(route) and route["request_kind"] != "no_case_assessment":
        validate_abstract_revision(route, gaps)
    required_operation_ids = required_operations_for(route)
    registry = load_registry()
    check_c27_records(route, registry, gaps)
    operations = check_operations(route, gaps, required_operation_ids)

    for name, value in route["classification"].items():
        if value["state"] == "unknown":
            gaps.append(f"classification:{name}:unknown")

    if route["conditional_review"]["status"] != "reviewed":
        gaps.append("conditional_workflow_review:incomplete")

    module_reports = check_module_pairs(route, operations, gaps)
    research_reports = check_research(route, operations, gaps, path.resolve().parent)
    source_preflight_reports = check_source_preflights(
        route, operations, gaps, path.resolve().parent, research_reports)
    evidence_index = check_evidence_index(
        route, path.resolve().parent, module_reports, research_reports, source_preflight_reports)
    check_operation_evidence(route, evidence_index, gaps)
    issue_routing_reports = check_declared_issues(
        route, evidence_index, source_preflight_reports, gaps)
    strategy_mode = check_strategy_assessment(route, evidence_index, gaps)

    try:
        dashboard_report = validate_dashboard_receipt(
            route, evidence_index, gaps, module_reports, required_operation_ids
        )
    except DashboardError as error:
        raise RouteGateError(f"dashboard:{error}") from error

    if route["coverage_claim"] == "comprehensive" and gaps:
        status = "rejected_comprehensive_claim"
    elif gaps:
        status = "valid_partial_route"
    else:
        status = "structurally_closed_declared_plan"

    outstanding = sorted(set(gaps))
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    validation_record = {
        "validator": "consultation_route_gate.py",
        "validator_version": ROUTE_GATE_VERSION,
        "receipt_sha256": receipt_sha256,
        "result": status,
        "outstanding_count": len(outstanding),
    }
    dashboard_preview = None
    if dashboard_report["required"]:
        dashboard_preview = render_dashboard(
            route,
            dashboard_report.get("render_metrics") or {"response": {}, "conversation": {}},
            outstanding,
            required_operation_ids,
            validation_record=validation_record,
            validator_reports={
                "c27_check_count": len(route["c27_checks"]),
                "issue_records_declared": route.get("issues") is not None,
                "issue_record_count": len(route.get("issues", [])),
                "issue_routing": issue_routing_reports,
                "source_ledger_validated": dashboard_report.get("source_metrics") is not None,
                "dashboard_consistency_validated": True,
                "module_pairs": module_reports,
                "research": research_reports,
                "source_preflight": source_preflight_reports,
            },
        )

    return {
        "status": status,
        "route_ref": route["route_ref"],
        "coverage_claim": route["coverage_claim"],
        "declared_plan_has_no_outstanding_gaps": not gaps,
        "outstanding": outstanding,
        "validation_record": validation_record,
        "module_pair_reports": module_reports,
        "research_reports": research_reports,
        "source_preflight_reports": source_preflight_reports,
        "issue_routing_reports": issue_routing_reports,
        "strategy_mode": strategy_mode,
        "dashboard_required": dashboard_report["required"],
        "dashboard_preview": dashboard_preview,
        "source_metrics": dashboard_report["source_metrics"],
        "source_origin_metrics": dashboard_report.get("source_origin_metrics"),
        "assurance": "model_declared_plan_and_references_only; routing_is_checked_only_for_declared_issues_and_signals; omitted_issues_source_class_selection_conditional_trigger_semantics_and_evidence_truth_not_verified",
        "host_release_enforcement": "requires_host_to_call_this_gate_and_enforce_its_result",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route_receipt", type=Path)
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="write the validated Markdown dashboard to stdout without the surrounding JSON report",
    )
    args = parser.parse_args(argv)
    try:
        result = validate_route(args.route_receipt)
        if args.dashboard_only:
            preview = result.get("dashboard_preview")
            if not isinstance(preview, str):
                raise RouteGateError("dashboard_not_required_or_not_rendered")
            sys.stdout.write(preview)
        else:
            print(json.dumps(result, sort_keys=True))
        if result["status"] == "rejected_comprehensive_claim":
            return 3
        return 0
    except (ContractError, RouteGateError, StateError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
