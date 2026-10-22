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
import sys
from pathlib import Path

from c27_case_state import StateError, load_registry, validate_route_check_record
from contract_validate import ContractError, validate_obj
from module_conformance import ConformanceError, validate_paths
from research_gate import ResearchGateError, validate_research
from issue_source_preflight import SourcePreflightError, validate_source_preflight
from consultation_dashboard import DashboardError, render_dashboard, validate_dashboard_receipt
from consultation_issue_selection import (
    SelectionError as IssueSelectionError,
    load_json as load_issue_json,
    select_issue_requirements,
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
ROUTE_GATE_VERSION = "0.3.0"


class RouteGateError(ValueError):
    pass


def required_operations_for(route: dict) -> tuple[str, ...]:
    required = list(REQUIRED_OPERATIONS[route["request_kind"]])
    if route.get("schema_version") == "0.4.0" and route["request_kind"] in {
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
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as error:
        raise RouteGateError(f"{label}:path_outside_allowed_root") from error
    if not resolved.is_file():
        raise RouteGateError(f"{label}:file_not_found")
    return resolved


def check_c27_records(route: dict, registry: dict, gaps: list[str]) -> int:
    if route["request_kind"] == "no_case_assessment":
        if route["c27_checks"] or route.get("issues"):
            raise RouteGateError("non_consultation_receipt_contains_case_assessment")
        return 0
    seen: set[tuple[str, str]] = set()
    for item in route["c27_checks"]:
        record = item["record"]
        validate_route_check_record(record, registry)
        check_id = record["check_id"]
        key = (item["scope_ref"], check_id)
        if key in seen:
            raise RouteGateError(f"c27_check_duplicate:{item['scope_ref']}:{check_id}")
        seen.add(key)
        if record["status"] not in CLOSED_C27_STATUSES:
            gaps.append(f"c27:{item['scope_ref']}:{check_id}:{record['status']}")
    if route["request_kind"] == "applicant_guidance" and not route["c27_checks"]:
        gaps.append("c27:no_selected_checks_recorded")
    return len(seen)


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


def check_declared_issues(route: dict, evidence_index: dict[str, dict],
                          source_preflight_reports: list[dict], gaps: list[str]) -> list[dict]:
    """Reconcile issue signals to C27, owner-specific sources and attack topics.

    Earlier receipts may omit issues. Version 0.4.0 checks per-issue source and
    attack records, but it still cannot discover an omitted issue or validate
    whether the selected signal set is legally complete.
    """
    issues = route.get("issues")
    if issues is None:
        return []
    try:
        matrix = load_issue_json(ISSUE_MATRIX_PATH)
        registry_data = load_issue_json(ISSUE_REGISTRY_PATH)
    except IssueSelectionError as error:
        raise RouteGateError("issue_routing_configuration_invalid") from error

    strict = route.get("schema_version") == "0.4.0"
    if (strict and route.get("revision_control") is not None
            and route.get("invocation", {}).get("material_change") is not True):
        raise RouteGateError("revision_control_without_material_change")
    if strict and route.get("invocation", {}).get("material_change") is True:
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
    preflight_by_id = {
        report.get("preflight_id"): report
        for report in source_preflight_reports
        if report.get("preflight_id")
    }
    declared_issue_refs = {item["issue_ref"] for item in issues}
    all_source_owners = set((matrix.get("source_owners") or {}).keys())
    issue_reports: list[dict] = []

    if strict and route.get("invocation", {}).get("material_change") is True:
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
            requirements = select_issue_requirements(
                issue["signal_ids"], matrix=matrix, registry=registry_data
            )
        except IssueSelectionError as error:
            raise RouteGateError(f"issue_signal_selection_invalid:{issue_ref}:{error}") from error
        actual = actual_by_scope.get(scope_ref, set())
        for check_id in sorted(set(requirements["check_ids"]) - actual):
            gaps.append(f"issue:{issue_ref}:c27_required_check_missing:{check_id}")
        if issue["disposition"] in {"source_missing", "fact_missing"}:
            gaps.append(f"issue:{issue_ref}:disposition:{issue['disposition']}")

        issue_report = {
            "issue_ref": issue_ref,
            "scope_ref": scope_ref,
            "route_ids": requirements["route_ids"],
            "required_check_ids": requirements["check_ids"],
            "required_source_owner_ids": requirements["source_owner_ids"],
            "attack_angle_topic_count": len(requirements["attack_angle_topics"]),
            "attack_angle_topics": requirements["attack_angle_topics"],
        }
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
            missing_owners = sorted(set(requirements["source_owner_ids"]) - set(obligation_by_owner))
            for owner_id in missing_owners:
                gaps.append(f"issue:{issue_ref}:source_owner_obligation_missing:{owner_id}")

            for owner_id, obligation in obligation_by_owner.items():
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
                linked_issue = topic_record.get("linked_issue_ref")
                if topic_record["outcome"] == "candidate_issue_linked" and linked_issue not in declared_issue_refs:
                    gaps.append(f"issue:{issue_ref}:attack_angle_linked_issue_missing:{key[0]}")

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
    args = parser.parse_args(argv)
    try:
        result = validate_route(args.route_receipt)
        print(json.dumps(result, sort_keys=True))
        if result["status"] == "rejected_comprehensive_claim":
            return 3
        return 0
    except (ContractError, RouteGateError, StateError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
