#!/usr/bin/env python3
"""Check cross-artifact integrity and research coverage for core research records."""
import argparse
import json
import sys
from pathlib import Path

from contract_validate import ContractError, digest_obj, load_json, validate_obj


class ResearchGateError(Exception):
    pass


TEXT_INSPECTION_STATUSES = {"publisher_text_inspected", "bundled_text_inspected"}


def _index_unique(items, key, label):
    result = {}
    for item in items:
        value = item[key]
        if value in result:
            raise ResearchGateError(f"duplicate {label}: {value}")
        result[value] = item
    return result


def _require_refs(values, allowed, label):
    missing = sorted(set(values) - set(allowed))
    if missing:
        raise ResearchGateError(f"{label} reference missing: {', '.join(missing)}")


def _has_reviewed_content(item, plan):
    status = item.get("inspection_status", "not_recorded")
    if status in TEXT_INSPECTION_STATUSES:
        return True
    return status == "synthetic_fixture_only" and plan["purpose"] == "synthetic_issue_followup"


def _require_reviewed_evidence(items, plan, label):
    if not items or any(not _has_reviewed_content(item, plan) for item in items):
        raise ResearchGateError(
            f"{label} links evidence without inspected source text; a search result, opened page, or unrecorded inspection cannot support it"
        )


def _validate_source_access(item, plan, contract_version):
    access = item.get("source_access")
    if contract_version == "0.4.0" and not isinstance(access, dict):
        raise ResearchGateError(f"evidence {item['evidence_id']} is missing source access status")
    if access is None:
        return

    channel = access["channel"]
    status = access["status"]
    inspection = item.get("inspection_status", "not_recorded")
    relation = item["relation"]
    if channel == "synthetic_fixture":
        if plan["purpose"] != "synthetic_issue_followup" or inspection != "synthetic_fixture_only":
            raise ResearchGateError("synthetic source access requires a synthetic fixture and inspection status")
    if inspection == "synthetic_fixture_only" and plan["purpose"] != "synthetic_issue_followup":
        raise ResearchGateError("synthetic fixture inspection is not allowed for a non-synthetic plan")
    if status != "accessible":
        if relation in {"supports", "contradicts"}:
            raise ResearchGateError(
                f"evidence {item['evidence_id']} with source access {status} cannot support or contradict a finding"
            )
        if inspection != "not_recorded":
            raise ResearchGateError(
                f"evidence {item['evidence_id']} has inspected content despite source access {status}"
            )
    if inspection == "publisher_text_inspected" and (status != "accessible" or channel != "official_publisher"):
        raise ResearchGateError("publisher text inspection must use accessible official-publisher access")
    if inspection == "bundled_text_inspected" and (
        status != "accessible" or channel not in {"bundled_runtime", "local_package"}
    ):
        raise ResearchGateError("bundled text inspection must use accessible bundled source access")
    if channel == "official_publisher" and item["source"]["record_kind"] != "official_reference":
        raise ResearchGateError("official-publisher fallback must be recorded as an official_reference")


def validate_research(plan_path: Path, bundle_path: Path):
    plan = load_json(plan_path)
    bundle = load_json(bundle_path)
    validate_obj("research-plan", plan)
    validate_obj("research-evidence-bundle", bundle)

    if plan["research_id"] != bundle["research_id"]:
        raise ResearchGateError("plan and evidence bundle research_id differ")
    if plan["mode"] != bundle["mode"]:
        raise ResearchGateError("plan and evidence bundle mode differ")
    expected_plan_hash = digest_obj(plan)
    if bundle["plan_sha256"] != expected_plan_hash:
        raise ResearchGateError("evidence bundle does not bind the exact plan digest")

    plan_tasks = _index_unique(plan["tasks"], "task_id", "plan task_id")
    results = _index_unique(bundle["tasks"], "task_id", "bundle task_id")
    if set(plan_tasks) != set(results):
        raise ResearchGateError("plan and bundle task_id sets differ")

    findings = _index_unique(bundle["findings"], "finding_id", "finding_id")
    evidence = _index_unique(bundle["evidence"], "evidence_id", "evidence_id")
    claims = _index_unique(bundle["claims"], "claim_id", "claim_id")

    findings_by_task = {task_id: set() for task_id in plan_tasks}
    evidence_by_task = {task_id: set() for task_id in plan_tasks}
    for finding in findings.values():
        task_id = finding["task_id"]
        if task_id not in plan_tasks:
            raise ResearchGateError(f"finding {finding['finding_id']} refers to an unknown task")
        findings_by_task[task_id].add(finding["finding_id"])
        _require_refs(finding["evidence_ids"], evidence, f"finding {finding['finding_id']} evidence")
        _require_refs(finding["counterevidence_ids"], evidence, f"finding {finding['finding_id']} counterevidence")
        if finding["disposition"] == "supported_for_review" and not any(
            evidence[evidence_id]["relation"] == "supports"
            for evidence_id in finding["evidence_ids"]
        ):
            raise ResearchGateError(
                f"finding {finding['finding_id']} is supported_for_review without supporting evidence"
            )
        if finding["disposition"] == "supported_for_review":
            supporting = [evidence[evidence_id] for evidence_id in finding["evidence_ids"]
                          if evidence[evidence_id]["relation"] == "supports"]
            _require_reviewed_evidence(supporting, plan, f"finding {finding['finding_id']}")
        elif finding["disposition"] == "contested":
            supporting = [evidence[evidence_id] for evidence_id in finding["evidence_ids"]
                          if evidence[evidence_id]["relation"] == "supports"]
            if supporting:
                _require_reviewed_evidence(supporting, plan, f"finding {finding['finding_id']} supporting evidence")
        if finding["disposition"] == "contested" and not any(
            evidence[evidence_id]["relation"] == "contradicts"
            for evidence_id in finding["counterevidence_ids"]
        ):
            raise ResearchGateError(
                f"finding {finding['finding_id']} is contested without contradictory counterevidence"
            )
        if finding["disposition"] == "contested":
            contradictory = [evidence[evidence_id] for evidence_id in finding["counterevidence_ids"]
                             if evidence[evidence_id]["relation"] == "contradicts"]
            _require_reviewed_evidence(contradictory, plan, f"finding {finding['finding_id']} counterevidence")
        for evidence_id in set(finding["evidence_ids"] + finding["counterevidence_ids"]):
            item = evidence[evidence_id]
            if item["task_id"] != task_id:
                raise ResearchGateError(f"finding {finding['finding_id']} links evidence from a different task")

    for item in evidence.values():
        task_id = item["task_id"]
        if task_id not in plan_tasks:
            raise ResearchGateError(f"evidence {item['evidence_id']} refers to an unknown task")
        evidence_by_task[task_id].add(item["evidence_id"])
        _validate_source_access(item, plan, bundle["contract_version"])
        task = plan_tasks[task_id]
        expected_owner = task["owner"]
        if item["source"]["owner"] != expected_owner:
            raise ResearchGateError(f"evidence {item['evidence_id']} owner differs from its plan task owner")
        if (expected_owner["family"] == "source_library_national"
                and expected_owner["owner_id"].startswith("unregistered:")):
            if item["source"]["record_kind"] == "registered_source":
                raise ResearchGateError(
                    f"evidence {item['evidence_id']} cannot claim a registered source for an unregistered national owner"
                )
            if item["relation"] in {"supports", "contradicts"}:
                if item["source"]["record_kind"] != "official_reference":
                    raise ResearchGateError(
                        f"evidence {item['evidence_id']} must use an official reference for an unregistered national source"
                    )
                if (item.get("inspection_status") != "publisher_text_inspected"
                        and not (plan["purpose"] == "synthetic_issue_followup"
                                 and item.get("inspection_status") == "synthetic_fixture_only")):
                    raise ResearchGateError(
                        f"evidence {item['evidence_id']} must record inspected publisher text for an unregistered national source"
                    )

    used_evidence = set()
    for finding in findings.values():
        used_evidence.update(finding["evidence_ids"])
        used_evidence.update(finding["counterevidence_ids"])

    used_findings = set()
    for claim in claims.values():
        _require_refs(claim["finding_ids"], findings, f"claim {claim['claim_id']} finding")
        _require_refs(claim["counterevidence_ids"], evidence, f"claim {claim['claim_id']} counterevidence")
        if any(evidence[eid]["relation"] != "contradicts" for eid in claim["counterevidence_ids"]):
            raise ResearchGateError(f"claim {claim['claim_id']} counterevidence is not marked contradictory")
        used_findings.update(claim["finding_ids"])
        used_evidence.update(claim["counterevidence_ids"])
        linked = [findings[finding_id] for finding_id in claim["finding_ids"]]
        if claim["disposition"] == "supported_for_review":
            if not linked or any(item["disposition"] != "supported_for_review" for item in linked):
                raise ResearchGateError(f"claim {claim['claim_id']} overstates a linked finding")
            supporting_ids = {eid for item in linked for eid in item["evidence_ids"]}
            if not any(evidence[eid]["relation"] == "supports" for eid in supporting_ids):
                raise ResearchGateError(f"claim {claim['claim_id']} has no supporting evidence")
            _require_reviewed_evidence(
                [evidence[eid] for eid in supporting_ids if evidence[eid]["relation"] == "supports"],
                plan, f"claim {claim['claim_id']}"
            )
            if claim["falsifier_review"]["result"] == "unresolved" or any(item["falsifier_review"]["result"] == "unresolved" for item in linked):
                raise ResearchGateError(f"claim {claim['claim_id']} has unresolved falsifier review")
        elif claim["disposition"] == "contested":
            if not any(evidence[eid]["relation"] == "contradicts" for eid in claim["counterevidence_ids"]):
                raise ResearchGateError(f"claim {claim['claim_id']} is contested without linked counterevidence")
            _require_reviewed_evidence(
                [evidence[eid] for eid in claim["counterevidence_ids"]], plan,
                f"claim {claim['claim_id']} counterevidence"
            )
        elif claim["disposition"] == "context_only":
            if not linked or any(item["disposition"] != "context_only" for item in linked):
                raise ResearchGateError(f"claim {claim['claim_id']} is not limited to contextual findings")

    for finding in findings.values():
        for evidence_id in finding["counterevidence_ids"]:
            if evidence[evidence_id]["relation"] != "contradicts":
                raise ResearchGateError(f"finding {finding['finding_id']} counterevidence is not marked contradictory")

    if set(findings) != used_findings:
        raise ResearchGateError("every finding must be mapped to at least one output claim")
    if set(evidence) != used_evidence:
        raise ResearchGateError("every evidence record must be linked to a finding or claim")

    finished = {"complete", "not_applicable"}
    for task_id, result in results.items():
        if set(result["finding_ids"]) != findings_by_task[task_id]:
            raise ResearchGateError(f"task {task_id} finding_ids do not match the bundle findings")
        if set(result["evidence_ids"]) != evidence_by_task[task_id]:
            raise ResearchGateError(f"task {task_id} evidence_ids do not match the bundle evidence")
        if result["status"] in finished and not result["limitations"]:
            raise ResearchGateError(f"closed task {task_id} needs a limitation/reason record")
        if result["status"] == "complete" and (not findings_by_task[task_id] or not evidence_by_task[task_id]):
            raise ResearchGateError(f"complete task {task_id} needs findings and evidence")

    all_tasks_finished = all(item["status"] in finished for item in results.values())
    has_unresolved_falsifier = any(
        item["falsifier_review"]["result"] == "unresolved"
        for item in list(findings.values()) + list(claims.values())
    )
    if all_tasks_finished and has_unresolved_falsifier:
        raise ResearchGateError("coverage cannot be complete while a material falsifier remains unresolved")
    if (bundle["coverage_status"] == "complete") != all_tasks_finished:
        raise ResearchGateError("coverage_status must be complete exactly when all tasks are complete or not_applicable")

    report = {
        "status": "valid",
        "research_id": plan["research_id"],
        "mode": plan["mode"],
        "coverage_status": bundle["coverage_status"],
        "research_complete": all_tasks_finished,
        "plan_sha256": expected_plan_hash,
        "task_count": len(plan_tasks),
        "finding_count": len(findings),
        "evidence_count": len(evidence),
        "claim_count": len(claims),
        "inspection_provenance": "model_declared_not_authenticated",
        "supported_findings_require_inspected_text": True,
        "source_access_provenance": "caller_declared_not_authenticated",
        "source_access_evidence_count": sum("source_access" in item for item in evidence.values()),
        "inaccessible_source_access_count": sum(
            item.get("source_access", {}).get("status") == "inaccessible"
            for item in evidence.values()
        ),
        "legal_merits_status": "not_determined",
        "downstream_status": "research_only",
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="Check a freemovement-law research plan/evidence bundle pair")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--require-complete", action="store_true", help="return exit code 3 unless all research tasks are complete or not applicable")
    args = parser.parse_args()
    try:
        report = validate_research(args.plan, args.bundle)
        print(json.dumps(report, sort_keys=True))
        if args.require_complete and not report["research_complete"]:
            return 3
        return 0
    except (ContractError, ResearchGateError, OSError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
