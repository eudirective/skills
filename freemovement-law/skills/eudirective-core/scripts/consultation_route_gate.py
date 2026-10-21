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
from contract_validate import ContractError, load_json, validate_obj
from module_conformance import ConformanceError, validate_paths
from research_gate import ResearchGateError, validate_research
from issue_source_preflight import SourcePreflightError, validate_source_preflight
from consultation_dashboard import DashboardError, validate_dashboard_receipt
from consultation_issue_selection import (
    SelectionError as IssueSelectionError,
    load_json as load_issue_json,
    select_check_ids,
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


class RouteGateError(ValueError):
    pass


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
                          gaps: list[str]) -> None:
    """Reconcile optional declared issues with routed C27 checks by scope.

    Legacy receipts may omit ``issues``. When present, this validates only
    declared issue signals and cannot discover an omitted issue.
    """
    issues = route.get("issues")
    if issues is None:
        return
    try:
        matrix = load_issue_json(ISSUE_MATRIX_PATH)
        registry_data = load_issue_json(ISSUE_REGISTRY_PATH)
    except IssueSelectionError as error:
        raise RouteGateError("issue_routing_configuration_invalid") from error
    seen_issue_refs: set[str] = set()
    actual_by_scope: dict[str, set[str]] = {}
    for item in route["c27_checks"]:
        actual_by_scope.setdefault(item["scope_ref"], set()).add(item["record"]["check_id"])

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
            required = select_check_ids(
                issue["signal_ids"], matrix=matrix, registry=registry_data
            )
        except IssueSelectionError as error:
            raise RouteGateError(f"issue_signal_selection_invalid:{issue_ref}:{error}") from error
        actual = actual_by_scope.get(scope_ref, set())
        for check_id in sorted(set(required) - actual):
            gaps.append(f"issue:{issue_ref}:c27_required_check_missing:{check_id}")
        if issue["disposition"] in {"source_missing", "fact_missing"}:
            gaps.append(f"issue:{issue_ref}:disposition:{issue['disposition']}")


def check_operations(route: dict, gaps: list[str]) -> dict[str, dict]:
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
    for operation_id in REQUIRED_OPERATIONS[route["request_kind"]]:
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
    route = load_json(path)
    validate_obj("consultation-route-receipt", route)
    gaps: list[str] = []
    registry = load_registry()
    check_c27_records(route, registry, gaps)
    operations = check_operations(route, gaps)

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
    check_declared_issues(route, evidence_index, gaps)

    try:
        dashboard_report = validate_dashboard_receipt(
            route, evidence_index, gaps, module_reports, REQUIRED_OPERATIONS[route["request_kind"]]
        )
    except DashboardError as error:
        raise RouteGateError(f"dashboard:{error}") from error

    if route["coverage_claim"] == "comprehensive" and gaps:
        status = "rejected_comprehensive_claim"
    elif gaps:
        status = "valid_partial_route"
    else:
        status = "structurally_closed_declared_plan"

    return {
        "status": status,
        "route_ref": route["route_ref"],
        "coverage_claim": route["coverage_claim"],
        "declared_plan_has_no_outstanding_gaps": not gaps,
        "outstanding": sorted(set(gaps)),
        "module_pair_reports": module_reports,
        "research_reports": research_reports,
        "source_preflight_reports": source_preflight_reports,
        "dashboard_required": dashboard_report["required"],
        "dashboard_preview": dashboard_report["preview"],
        "source_metrics": dashboard_report["source_metrics"],
        "assurance": "model_declared_plan_and_references_only; issue_signal_routing_is_checked_only_for_declared_issues; omitted_issues_conditional_trigger_semantics_and_evidence_truth_not_verified",
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
