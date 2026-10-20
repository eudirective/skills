#!/usr/bin/env python3
"""Validate issue-level source accounting against the existing research gate.

This checks declared structure, ownership, registry references, byte hashes
for retained sources, and open-work labels. Human-reviewed official references
can satisfy a source class without registration or a saved-content hash; their
publisher identity and review remain declared evidence. The validator does not
establish current law, source authenticity beyond local pack checks, or legal
entailment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import verify_bundled_source_pack as source_pack_gate
from contract_validate import ContractError, digest_obj, load_json, validate_obj
from module_conformance import ConformanceError, validate_paths
from research_gate import ResearchGateError, validate_research
from source_library_paths import source_library_root
import topology_engine


class SourcePreflightError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _national_candidate_record(source_id: str, evidence_source: dict) -> dict | None:
    """Bind CAND-<CC>-<library-id> references to the inventory; never promote them."""
    owner = evidence_source["owner"]
    if owner["family"] != "source_library_national":
        return None
    owner_id = owner["owner_id"]
    is_unregistered = owner_id == f"unregistered:{owner['jurisdiction']}"
    candidate_prefix = f"CAND-{owner['jurisdiction']}-"
    if not source_id.startswith(candidate_prefix):
        if is_unregistered:
            return None
        raise SourcePreflightError("national_candidate_id_namespace_mismatch")
    library_source_id = source_id[len(candidate_prefix):].casefold()
    if not library_source_id:
        raise SourcePreflightError("national_candidate_id_namespace_mismatch")
    try:
        library_root = source_library_root()
    except FileNotFoundError:
        if is_unregistered:
            return None
        raise SourcePreflightError("national_candidate_library_unavailable")

    manifests = []
    for manifest_path in library_root.glob("*/references/candidate-manifest.json"):
        manifest = load_json(manifest_path)
        manifests.append((manifest_path, manifest))
    if is_unregistered:
        eligible = [(path, manifest) for path, manifest in manifests
                    if topology_engine.same_jurisdiction(
                        owner["jurisdiction"], manifest.get("jurisdiction") or path.parent.parent.name)]
    else:
        eligible = [(path, manifest) for path, manifest in manifests if manifest.get("pack") == owner_id]
        if len(eligible) != 1:
            raise SourcePreflightError("national_candidate_pack_manifest_not_supported")
        path, manifest = eligible[0]
        country = manifest.get("jurisdiction") or path.parent.parent.name
        if not topology_engine.same_jurisdiction(owner["jurisdiction"], country):
            raise SourcePreflightError("national_candidate_pack_jurisdiction_mismatch")
        if owner.get("source_pack_sha256") != sha256(path):
            raise SourcePreflightError("national_candidate_manifest_digest_mismatch")

    matches = []
    for manifest_path, manifest in eligible:
        for records in manifest.values():
            if not isinstance(records, list):
                continue
            matches.extend((manifest_path, manifest, item) for item in records
                           if isinstance(item, dict) and
                           isinstance(item.get("id"), str) and
                           item["id"].casefold() == library_source_id)
    if not matches and is_unregistered:
        # A genuinely unregistered source may be external to the bundled candidate inventory.
        # It remains open and cannot satisfy any required source class.
        return None
    if not matches:
        raise SourcePreflightError("national_candidate_id_not_in_inventory")
    if len(matches) != 1:
        raise SourcePreflightError("national_candidate_id_ambiguous_in_inventory")

    manifest_path, manifest, entry = matches[0]
    if entry.get("accepted") is True:
        raise SourcePreflightError("candidate_record_marked_accepted_in_inventory")

    known_digests = {entry.get(name) for name in
                     ("source_sha256", "converted_sha256", "content_sha256", "sha256")
                     if isinstance(entry.get(name), str)}
    candidate_root = manifest_path.parent.parent
    expected_hash_field = {
        "candidate_text_path": "converted_sha256",
        "document_path": "converted_sha256",
        "raw_source_path": "source_sha256",
        "file": "content_sha256",
    }
    for name, hash_field in expected_hash_field.items():
        relative = entry.get(name)
        if not isinstance(relative, str):
            continue
        candidate_path = Path(relative)
        if candidate_path.is_absolute() or ".." in candidate_path.parts or "\\" in relative:
            raise SourcePreflightError("national_candidate_path_unsafe")
        path = candidate_root / candidate_path
        if path.is_symlink():
            raise SourcePreflightError("national_candidate_path_symlinked")
        if path.is_file():
            if not path.resolve().is_relative_to(candidate_root.resolve()):
                raise SourcePreflightError("national_candidate_path_escapes_inventory")
            local_digest = sha256(path)
            expected_digest = entry.get(hash_field)
            if isinstance(expected_digest, str) and local_digest != expected_digest:
                raise SourcePreflightError("national_candidate_local_content_manifest_digest_mismatch")
            known_digests.add(local_digest)
    supplied_digest = evidence_source.get("content_sha256")
    if known_digests and supplied_digest not in known_digests:
        raise SourcePreflightError("national_candidate_content_digest_mismatch")
    return entry


def _registered_source_record(source_id: str, evidence_source: dict) -> dict:
    owner = evidence_source["owner"]
    if owner["family"] == "core_source":
        manifest_path = source_pack_gate.MANIFEST
        manifest = load_json(manifest_path)
        if owner["owner_id"] != manifest["pack_name"] + "-" + manifest["pack_version"]:
            raise SourcePreflightError("core_source_pack_owner_id_mismatch")
        if owner.get("source_pack_sha256") != sha256(manifest_path):
            raise SourcePreflightError("core_source_pack_manifest_digest_mismatch")
        proof = source_pack_gate.inspect()
        if proof["status"] != "verified_locally_complete":
            raise SourcePreflightError("core_source_pack_integrity_not_verified")
        matches = [item for item in manifest["sources"] if item["source_id"] == source_id]
        if len(matches) != 1:
            raise SourcePreflightError("source_id_not_in_pinned_core_pack")
        entry = matches[0]
        hashes = {item["sha256"] for item in entry["representations"]}
    elif owner["family"] in {"member_state", "applicant_country"}:
        entry = None
        module_skills_root = source_pack_gate.ROOT.parent
        for module_name in ("eudirective-ms-sweden", "eudirective-ac-turkiye"):
            module_root = module_skills_root / module_name
            manifest_path = module_root / "references/module-manifest.json"
            export_path = module_root / "references/module-export.json"
            manifest = load_json(manifest_path)
            export = load_json(export_path)
            try:
                validate_paths(manifest_path, export_path)
            except (ConformanceError, ContractError) as error:
                raise SourcePreflightError(f"module_pair_nonconformant:{owner['owner_id']}") from error
            if export["module_id"] != owner["owner_id"]:
                continue
            if export["module_family"] != owner["family"] or export["jurisdiction"] != owner["jurisdiction"]:
                raise SourcePreflightError("module_source_owner_role_mismatch")
            if digest_obj(manifest) != owner.get("manifest_sha256"):
                raise SourcePreflightError("module_manifest_digest_mismatch")
            if digest_obj(export) != owner.get("export_sha256"):
                raise SourcePreflightError("module_export_digest_mismatch")
            matches = [item for item in export["source_records"] if item["source_id"] == source_id]
            if len(matches) != 1:
                raise SourcePreflightError("source_id_not_in_registered_module_export")
            entry = matches[0]
            break
        if entry is None:
            raise SourcePreflightError("registered_module_owner_not_found")
        hashes = {entry["content_sha256"]}
    else:
        raise SourcePreflightError("registered_national_source_registry_not_implemented")
    if evidence_source["content_sha256"] not in hashes:
        raise SourcePreflightError("registered_source_content_digest_mismatch")
    return entry


def _class_compatible(source_class: str, record: dict, evidence: dict) -> bool:
    if source_class == "contrary_authority":
        return evidence["relation"] == "contradicts"
    if evidence["relation"] not in {"supports", "context_only", "contradicts"}:
        return False
    if source_class == "case_law":
        return record.get("source_type") == "judgment" or record.get("legal_status") == "case_law"
    if source_class == "official_guidance":
        return (record.get("source_type") in {
                    "official_guidance", "official_form", "mission_instruction",
                    "complaint_route", "oversight_material", "official_register",
                    "other_official",
                } or
                "guidance" in record.get("source_type", "") or
                record.get("legal_status") == "official_guidance")
    if source_class == "eu_binding_law":
        return (record.get("jurisdiction") == "EU" and
                (record.get("legal_status") in {"primary_law", "binding_secondary_law"} or
                 record.get("source_type") in {"treaty", "regulation", "directive", "directive_consolidated", "decision"}))
    if source_class == "national_binding_law":
        return (record.get("jurisdiction") != "EU" and
                (record.get("legal_status") in {"primary_law", "binding_secondary_law"} or
                 record.get("source_type") in {"statute", "legislation", "primary_law"}))
    if source_class == "procedural_rule":
        return (record.get("legal_status") == "procedural_rule" or
                record.get("source_type") in {"procedure", "procedural_rule", "complaint_route"})
    return False


def _record_status(record: dict, evidence: dict, source_class: str) -> tuple[bool, str | None]:
    source = evidence["source"]
    if record["record_kind"] == "registered_source":
        expected_ref = source.get("source_id")
    elif record["record_kind"] == "candidate_source":
        expected_ref = source.get("candidate_id")
    else:
        expected_ref = source.get("reference_id")
    if source.get("record_kind") != record["record_kind"] or expected_ref != record["source_ref"]:
        raise SourcePreflightError("source_record_reference_or_kind_mismatch")
    if record["record_kind"] == "candidate_source":
        if source.get("activation_status") != "candidate_not_activated":
            raise SourcePreflightError("candidate_activation_state_invalid")
        _national_candidate_record(record["source_ref"], source)
        return False, "candidate_source_not_accepted"

    if record["record_kind"] == "official_reference":
        if source.get("activation_status") != "reference_only_not_registered":
            raise SourcePreflightError("official_reference_activation_state_invalid")
        if record["currentness"] in {"reviewed_within_cutoff", "reviewed_historical_scope"}:
            if not record.get("source_date"):
                raise SourcePreflightError("official_reference_date_scope_missing")
            declared_date = source.get("published_or_effective_date")
            if declared_date and declared_date != record["source_date"]:
                raise SourcePreflightError("official_reference_date_scope_mismatch")
        metadata = dict(source)
        metadata["jurisdiction"] = source["owner"]["jurisdiction"]
        if not _class_compatible(source_class, metadata, evidence):
            return False, "source_class_not_supported_by_official_reference"
        return True, None

    entry = _registered_source_record(record["source_ref"], source)
    if not _class_compatible(source_class, entry, evidence):
        return False, "source_class_not_supported_by_registry_record"
    return True, None


def validate_source_preflight(preflight_path: Path, plan_path: Path, bundle_path: Path) -> dict:
    report = validate_research(plan_path, bundle_path)
    preflight = load_json(preflight_path)
    validate_obj("issue-source-preflight", preflight)
    plan = load_json(plan_path)
    bundle = load_json(bundle_path)
    if preflight["research_id"] != plan["research_id"]:
        raise SourcePreflightError("preflight_research_id_mismatch")

    tasks = {item["task_id"]: item for item in plan["tasks"]}
    task_results = {item["task_id"]: item for item in bundle["tasks"]}
    findings = {item["finding_id"]: item for item in bundle["findings"]}
    claims = {item["claim_id"]: item for item in bundle["claims"]}
    seen_issues: set[str] = set()
    outstanding: list[str] = []
    issue_reports = []
    for issue in preflight["issues"]:
        issue_id = issue["issue_id"]
        if issue_id in seen_issues:
            raise SourcePreflightError(f"duplicate_issue_id:{issue_id}")
        seen_issues.add(issue_id)
        task = tasks.get(issue["task_id"])
        if task is None:
            raise SourcePreflightError(f"issue_task_unknown:{issue_id}")
        if task["owner"] != issue["owner"]:
            raise SourcePreflightError(f"issue_owner_differs_from_research_task:{issue_id}")

        task_evidence = {item["evidence_id"]: item for item in bundle["evidence"]
                         if item["task_id"] == issue["task_id"]}
        issue_open: list[str] = []
        task_result = task_results[issue["task_id"]]
        if task_result["status"] not in {"complete", "not_applicable"}:
            issue_open.append(f"{issue_id}:research_task_{task_result['status']}")
        traced_evidence: set[str] = set()
        for claim_id in issue["claim_ids"]:
            claim = claims.get(claim_id)
            if claim is None:
                raise SourcePreflightError(f"issue_claim_unknown:{issue_id}:{claim_id}")
            linked = [findings[finding_id] for finding_id in claim["finding_ids"]
                      if finding_id in findings]
            issue_findings = [item for item in linked if item["task_id"] == issue["task_id"]]
            if not issue_findings:
                raise SourcePreflightError(f"issue_claim_not_linked_to_task:{issue_id}:{claim_id}")
            for finding in issue_findings:
                traced_evidence.update(finding["evidence_ids"])
                traced_evidence.update(finding["counterevidence_ids"])
            traced_evidence.update(claim["counterevidence_ids"])
        source_refs: set[str] = set()
        satisfied_classes: set[str] = set()
        for record in issue["sources"]:
            if record["source_ref"] in source_refs:
                raise SourcePreflightError(f"duplicate_source_reference:{issue_id}:{record['source_ref']}")
            source_refs.add(record["source_ref"])
            usable_currentness = {
                "reviewed_current", "reviewed_within_cutoff", "reviewed_historical_scope"
            }
            record_satisfies = (
                record["record_kind"] in {"registered_source", "official_reference"}
                and record["currentness"] in usable_currentness
            )
            if record["currentness"] not in usable_currentness:
                issue_open.append(f"{issue_id}:source_currentness_{record['currentness']}:{record['source_ref']}")
            expected_acceptance = {
                "registered_source": "registered_record",
                "candidate_source": "candidate_unaccepted",
                "official_reference": "reference_usable",
            }[record["record_kind"]]
            if record["acceptance_state"] != expected_acceptance:
                issue_open.append(f"{issue_id}:source_candidate_unaccepted:{record['source_ref']}")
            for evidence_id in record["evidence_ids"]:
                evidence = task_evidence.get(evidence_id)
                if evidence is None:
                    raise SourcePreflightError(f"source_evidence_not_linked_to_task:{issue_id}:{evidence_id}")
                if evidence["source"]["owner"] != issue["owner"]:
                    raise SourcePreflightError(f"source_evidence_owner_mismatch:{issue_id}:{evidence_id}")
                accepted, reason = _record_status(record, evidence, record["source_class"])
                record_satisfies = record_satisfies and accepted
                if reason:
                    issue_open.append(f"{issue_id}:{reason}:{record['source_ref']}")
            if record_satisfies:
                satisfied_classes.add(record["source_class"])

        for source_class in issue["required_source_classes"]:
            if source_class not in satisfied_classes:
                issue_open.append(f"{issue_id}:required_source_class_missing:{source_class}")
        source_evidence_ids = {evidence_id for item in issue["sources"] for evidence_id in item["evidence_ids"]}
        source_evidence_ids.update(issue["counterauthority_evidence_ids"])
        if not source_evidence_ids <= traced_evidence:
            missing_claim_trace = sorted(source_evidence_ids - traced_evidence)
            raise SourcePreflightError(f"issue_claim_source_trace_missing:{issue_id}:{','.join(missing_claim_trace)}")
        if issue["scope_review"] != "reviewed":
            issue_open.append(f"{issue_id}:scope_review_open")
        if issue["exceptions_review"] != "reviewed":
            issue_open.append(f"{issue_id}:exceptions_review_open")
        counter_status = issue["counterauthority_review"]
        if counter_status == "open":
            issue_open.append(f"{issue_id}:counterauthority_review_open")
        elif counter_status == "searched_none_reported":
            if not task_result["search_log"]:
                raise SourcePreflightError(f"counterauthority_search_not_recorded:{issue_id}")
        elif counter_status == "reviewed_with_counterevidence":
            for evidence_id in issue["counterauthority_evidence_ids"]:
                evidence = task_evidence.get(evidence_id)
                if evidence is None or evidence["relation"] != "contradicts":
                    raise SourcePreflightError(f"counterauthority_evidence_invalid:{issue_id}:{evidence_id}")
        if issue["review_provenance"] not in {"source_review", "human_review"}:
            issue_open.append(f"{issue_id}:independent_source_review_not_recorded")
        if issue["gap_disposition"] == "open":
            issue_open.append(f"{issue_id}:declared_open:{issue['gap_reason']}")
        elif issue_open:
            raise SourcePreflightError(
                f"issue_claimed_accounted_with_open_requirements:{issue_id}:" + ",".join(sorted(set(issue_open)))
            )
        issue_reports.append({
            "issue_id": issue_id,
            "task_id": issue["task_id"],
            "owner_role": issue["owner"]["role"],
            "satisfied_source_classes": sorted(satisfied_classes),
            "outstanding": sorted(set(issue_open)),
        })
        outstanding.extend(issue_open)

    if preflight["coverage_claim"] == "accounted_for_review" and outstanding:
        status = "rejected_accounted_claim"
    else:
        status = "valid_open_work" if outstanding else "accounted_for_review"
    return {
        "validation_status": "valid",
        "status": status,
        "preflight_id": preflight["preflight_id"],
        "research_id": preflight["research_id"],
        "research_gate_status": report["status"],
        "source_coverage_accounted_for_review": not outstanding,
        "issues": issue_reports,
        "outstanding": sorted(set(outstanding)),
        "assurance": "structural_source_accounting_only; does_not_verify_current_law_legal_applicability_entailment_or_nationwide_exhaustiveness",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = validate_source_preflight(args.preflight, args.plan, args.bundle)
        print(json.dumps(result, sort_keys=True))
        return 3 if result["status"] == "rejected_accounted_claim" else 0
    except (ContractError, SourcePreflightError, ResearchGateError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
