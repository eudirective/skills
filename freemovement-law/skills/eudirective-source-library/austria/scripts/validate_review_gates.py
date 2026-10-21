#!/usr/bin/env python3
"""Validate Austria's source-acceptance, dependency, and coverage gates offline."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
REPO = PACK.parents[1]
MANIFEST = PACK / "references" / "candidate-manifest.json"
LEDGER = PACK / "references" / "capture-ledger.json"
ACCEPTANCE = PACK / "references" / "source-acceptance.json"
DEPENDENCIES = PACK / "references" / "source-dependencies.json"
COVERAGE = PACK / "references" / "coverage-model.json"
RULES = PACK / "references" / "source-rules.json"
OPERATIONS = PACK / "references" / "operational-discovery.json"
CASE_LAW = PACK / "references" / "case-law-discovery.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def path_for(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    if value.startswith("captures/"):
        return PACK / candidate
    direct = REPO / candidate
    if direct.exists():
        return direct
    if value.startswith("source-library/austria/"):
        bundled = PACK / value.removeprefix("source-library/austria/")
        if bundled.exists():
            return bundled
    if value.startswith("temp/austria/raw/"):
        bundled = PACK / "captures" / "2026-10-19" / Path(value).name
        if bundled.exists():
            return bundled
    return direct


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def usable_official_reference(source_id: str, acceptance: dict) -> bool:
    """A reviewed official link may support coverage without accepting a local copy."""
    review = acceptance.get("official_reference_reviews", {}).get(source_id, {})
    if review.get("status") != "usable_official_reference":
        return False
    required = ("publisher", "url", "checked_on", "language", "version_or_cutoff", "scope", "reviewed_content", "limitations")
    if not all(review.get(key) for key in required):
        return False
    return str(review["url"]).startswith("https://")


def gate_state(data: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    manifest = load(MANIFEST)
    ledger = load(LEDGER)
    acceptance = load(ACCEPTANCE)
    deps = load(DEPENDENCIES)
    coverage = load(COVERAGE)
    rules = load(RULES)
    case_law = load(CASE_LAW)
    docs = {r["id"]: r for r in manifest.get("documents", [])}
    decisions = acceptance.get("records", {})
    if len(docs) != len(manifest.get("documents", [])):
        errors.append("manifest contains duplicate source IDs")
    missing = sorted(set(docs) - set(decisions))
    extra = sorted(set(decisions) - set(docs))
    if missing:
        errors.append(f"acceptance register missing source IDs: {', '.join(missing)}")
    if extra:
        errors.append(f"acceptance register includes unknown source IDs: {', '.join(extra)}")

    rule_ids = {sid for rule in rules.get("rules", []) for sid in rule.get("source_ids", [])}
    uncovered_rules = sorted(set(docs) - rule_ids)
    if uncovered_rules:
        errors.append(f"manifest records without a retrieval/conversion rule: {', '.join(uncovered_rules)}")

    ledger_rows = {r.get("candidate_id"): r for r in ledger.get("records", [])}
    accept_ready: list[str] = []
    accepted_count = 0
    blocked_sources: dict[str, list[str]] = {}
    required = acceptance.get("required_checks", [])
    allowed = {"pass", "pending", "fail", "not_applicable"}
    for source_id, row in docs.items():
        review = decisions.get(source_id, {})
        failed: list[str] = []
        checks = review.get("checks", {})
        native_path = row.get("native_source_path")
        if native_path:
            native_file = path_for(native_path)
            if not native_file.is_file():
                errors.append(f"{source_id} native source representation is missing")
            elif row.get("source_sha256") and sha(native_file.read_bytes()) != row["source_sha256"]:
                errors.append(f"{source_id} native source does not match the recorded source hash")
        for name in required:
            check = checks.get(name, {})
            state = check.get("status")
            if state not in allowed:
                failed.append(f"{name}:missing_or_invalid")
                continue
            if state == "not_applicable" and not check.get("reason"):
                failed.append(f"{name}:missing_not_applicable_reason")
            if state in {"pending", "fail"}:
                failed.append(f"{name}:{state}")
            if state == "pass" and not check.get("evidence"):
                failed.append(f"{name}:missing_evidence")
        if review.get("status") == "accepted" and failed:
            errors.append(f"{source_id} marked accepted while gate checks are open: {', '.join(failed)}")
        if review.get("status") == "ready_to_accept" and not failed and review.get("semantic_review", {}).get("status") == "passed":
            accept_ready.append(source_id)
        if review.get("status") == "accepted":
            accepted_count += 1
            native_path = row.get("native_source_path")
            content_path = row.get("source_text_path") or row.get("candidate_text_path") or native_path
            if not content_path or not path_for(content_path).is_file():
                errors.append(f"{source_id} accepted but its source representation is missing")
            elif native_path and row.get("source_sha256") and sha(path_for(native_path).read_bytes()) != row["source_sha256"]:
                errors.append(f"{source_id} native source does not match the recorded source hash")
            elif not native_path and row.get("converted_sha256") and sha(path_for(content_path).read_bytes()) != row["converted_sha256"]:
                errors.append(f"{source_id} accepted text does not match the recorded conversion hash")
            selector = str(row.get("content_selector") or "").strip().lower()
            valid_native_review = bool(native_path and row.get("conversion_rule_id") == "native-pdf-retention-v1")
            if row.get("source_type") != "official_guidance_directory" and not valid_native_review and selector in {"body", "body (filtered fallback)", ""}:
                errors.append(f"{source_id} accepted with an unvalidated or missing extraction selector")
            if row.get("source_sha256"):
                capture = ledger_rows.get(source_id, {})
                payload = capture.get("linked_payload") if native_path else None
                raw_rel = payload.get("raw_path") if payload else capture.get("raw_path")
                expected_source_hash = payload.get("source_sha256") if payload else row["source_sha256"]
                if raw_rel and path_for(raw_rel).is_file():
                    if sha(path_for(raw_rel).read_bytes()) != expected_source_hash:
                        errors.append(f"{source_id} raw source hash does not match the manifest/linked payload")
                elif not review.get("raw_capture_evidence"):
                    errors.append(f"{source_id} accepted without an available raw capture or replayable evidence")
        elif failed:
            blocked_sources[source_id] = failed
        if review.get("semantic_review", {}).get("status") == "passed" and not review.get("semantic_review", {}).get("method"):
            errors.append(f"{source_id} semantic review has no recorded method")

    dependency_errors: list[str] = []
    dep_rows = deps.get("dependencies", [])
    dep_by_id = {x.get("id"): x for x in dep_rows}
    for dep in dep_rows:
        src = dep.get("source_id")
        for sid in dep.get("source_ids", []):
            if sid not in docs:
                dependency_errors.append(f"{dep.get('id')} references unknown source {sid}")
        if src and src not in docs:
            dependency_errors.append(f"{dep.get('id')} references unknown source {src}")
        status = dep.get("dependency_review_status")
        if status in {"unresolved", "review_required_by_article_map", "unknown"}:
            dependency_errors.append(f"{dep.get('id')} remains {status}")
        elif status and not dep.get("evidence"):
            dependency_errors.append(f"{dep.get('id')} is {status} without evidence")

    article_map = deps.get("directive_article_map", [])
    required_articles = deps.get("required_directive_articles", [])
    mapped_articles = {str(row.get("article")) for row in article_map}
    for article in required_articles:
        if str(article) not in mapped_articles:
            dependency_errors.append(f"Directive 2004/38 Article {article} has no mapping or explicit gap record")
    for row in article_map:
        article = row.get("article")
        if row.get("mapping_status") != "mapped":
            dependency_errors.append(f"Directive 2004/38 Article {article} remains {row.get('mapping_status', 'unresolved')}")
        for sid in row.get("source_ids", []):
            if sid not in docs:
                dependency_errors.append(f"Directive article {article} references unknown source {sid}")
            elif row.get("mapping_status") == "mapped" and decisions.get(sid, {}).get("status") != "accepted" and not usable_official_reference(sid, acceptance):
                dependency_errors.append(f"Directive article {article} maps to neither an accepted local artifact nor a usable official reference: {sid}")

    uncovered: list[str] = []
    topic_rows = coverage.get("topics", [])
    topic_by_id = {topic.get("id"): topic for topic in topic_rows}
    for topic_id in coverage.get("required_topic_ids", []):
        if topic_id not in topic_by_id:
            uncovered.append(f"{topic_id}:required_topic_missing")
    for topic in topic_rows:
        for layer_name in coverage.get("required_layers", []):
            layer = topic.get("layers", {}).get(layer_name)
            if not layer:
                uncovered.append(f"{topic.get('id')}/{layer_name}:missing")
                continue
            status = layer.get("status")
            if status not in {"covered", "not_applicable"}:
                uncovered.append(f"{topic.get('id')}/{layer_name}:{status or 'missing'}")
            if status == "covered" and not layer.get("source_ids"):
                uncovered.append(f"{topic.get('id')}/{layer_name}:covered_without_evidence_sources")
            if status == "not_applicable" and not layer.get("reason"):
                errors.append(f"{topic.get('id')}/{layer_name} is not applicable without a reason")
            for sid in layer.get("source_ids", []):
                if sid not in docs:
                    errors.append(f"{topic.get('id')}/{layer_name} references unknown source {sid}")
                elif status == "covered" and decisions.get(sid, {}).get("status") != "accepted" and not usable_official_reference(sid, acceptance):
                    uncovered.append(f"{topic.get('id')}/{layer_name}:no_accepted_local_artifact_or_usable_reference:{sid}")
            if status in {"gap", "unresolved", "located_not_captured"} and not topic.get("open_issues"):
                errors.append(f"{topic.get('id')}/{layer_name} is open without an issue record")

    case_law_report = {"status": "incomplete", "planned_tasks": 0, "court_collections": 0, "complete_batches": 0, "covered_task_ids": 0, "open_task_ids": [], "errors": []}
    planned = case_law.get("planned_search_tasks", [])
    expected_task_ids = {row.get("task_id") for row in planned if row.get("task_id")}
    case_law_report["planned_tasks"] = len(planned)
    case_law_report["court_collections"] = len(case_law.get("court_collections", []))
    if len(expected_task_ids) != len(planned) or len(planned) != 55:
        case_law_report["errors"].append("case-law plan must contain 55 unique court/query tasks")
    if len(case_law.get("court_collections", [])) != 11:
        case_law_report["errors"].append("case-law plan must cover VwGH, BVwG and all nine LVwG collections")
    covered_task_ids: set[str] = set()
    complete_batches = 0
    sys.path.insert(0, str(PACK / "scripts"))
    from case_law_discovery import validate_batch as validate_case_law_batch
    for batch in case_law.get("runs", []):
        if batch.get("status") != "complete":
            continue
        task_ids = [row.get("task_id") for row in batch.get("tasks", [])]
        task_id_set = set(task_ids)
        batch_errors = validate_case_law_batch(batch, case_law)
        if batch_errors:
            case_law_report["errors"].extend(f"{batch.get('batch_id', 'unnamed batch')}: {error}" for error in batch_errors)
        else:
            complete_batches += 1
            covered_task_ids.update(task_id_set)
    case_law_report["complete_batches"] = complete_batches
    case_law_report["covered_task_ids"] = len(covered_task_ids)
    case_law_report["open_task_ids"] = sorted(expected_task_ids - covered_task_ids)
    if not case_law_report["errors"] and not case_law_report["open_task_ids"]:
        case_law_report["status"] = "pass"

    operations_report = {"status": "incomplete", "regional_tasks": 0, "mission_tasks": 0, "open_regional_tasks": 0, "open_mission_tasks": 0, "resolved_tasks_missing_evidence_count": 0, "resolved_tasks_evidence_error_count": 0, "errors": []}
    if not OPERATIONS.is_file():
        operations_report["errors"].append("operational discovery queue is missing")
    else:
        operations = load(OPERATIONS)
        regional = operations.get("regional_tasks", [])
        missions = operations.get("mission_tasks", [])
        regional_done = {"reviewed_and_accepted", "not_applicable_with_evidence", "no_source_found_after_recorded_search"}
        mission_done = regional_done
        operations_report.update({
            "regional_tasks": len(regional), "mission_tasks": len(missions),
            "open_regional_tasks": sum(1 for row in regional if row.get("status") not in regional_done),
            "open_mission_tasks": sum(1 for row in missions if row.get("status") not in mission_done),
        })
        sys.path.insert(0, str(PACK / "scripts"))
        from operational_discovery import validate as validate_operations
        operations_detail = validate_operations(operations)
        operations_report["resolved_tasks_missing_evidence_count"] = operations_detail.get("resolved_tasks_missing_evidence_count", 0)
        operations_report["resolved_tasks_evidence_error_count"] = operations_detail.get("resolved_tasks_evidence_error_count", 0)
        operations_report["errors"].extend(operations_detail.get("errors", []))
        if operations_detail.get("resolved_tasks_missing_evidence_count"):
            operations_report["errors"].append(f"{operations_detail['resolved_tasks_missing_evidence_count']} resolved operational fields lack evidence")
        if operations_report["resolved_tasks_evidence_error_count"]:
            operations_report["errors"].append(f"{operations_report['resolved_tasks_evidence_error_count']} resolved operational fields have invalid evidence or search provenance")
        if len(regional) != 9 or len({row.get("land") for row in regional}) != 9:
            operations_report["errors"].append("regional discovery queue must cover each of the nine Länder exactly once")
        if len(missions) != len({row.get("source_record_id") for row in missions}):
            operations_report["errors"].append("mission discovery queue has duplicate representation IDs")
        if len(missions) != 524:
            operations_report["errors"].append(f"mission discovery queue has {len(missions)} tasks; expected 524 from the reviewed BMEIA directory")
        if operations_report["errors"]:
            operations_report["status"] = "invalid"
        elif operations_report["open_regional_tasks"] or operations_report["open_mission_tasks"]:
            operations_report["status"] = "incomplete"
        else:
            operations_report["status"] = "pass"

    source_pending = sorted(source_id for source_id, row in decisions.items() if row.get("status") not in {"accepted", "discovery_only"})
    source_acceptance_status = "pass" if not source_pending and not blocked_sources else "incomplete"
    # Local-copy acceptance is reported separately and is not a prerequisite for
    # topic or country completion when the official source itself was reviewed.
    complete = not uncovered and not dependency_errors and not errors and case_law_report["status"] == "pass" and operations_report["status"] == "pass"
    if coverage.get("country_review_status") == "complete" and not complete:
        errors.append("country review is marked complete while one or more mandatory gates are open")
    return {
        "jurisdiction": "AT",
        "source_acceptance": {"status": source_acceptance_status, "accepted": accepted_count, "total": len(docs), "discovery_only": sum(1 for row in decisions.values() if row.get("status") == "discovery_only"), "pending": source_pending, "ready_to_accept": sorted(accept_ready), "blocked": blocked_sources},
        "dependency_gate": {"status": "pass" if not dependency_errors else "incomplete", "open": dependency_errors},
        "coverage_gate": {"status": "pass" if not uncovered else "incomplete", "uncovered_layers": uncovered},
        "case_law_discovery_gate": case_law_report,
        "operational_discovery_gate": operations_report,
        "country_review": "complete" if complete else "incomplete",
        "errors": errors
    }, errors


def promote() -> int:
    gate_report, errors = gate_state({})
    if errors:
        print(json.dumps({"promoted": [], "count": 0, "errors": errors}, ensure_ascii=False, indent=2))
        return 2
    manifest = load(MANIFEST)
    ledger = load(LEDGER)
    acceptance = load(ACCEPTANCE)
    rows = {r["id"]: r for r in manifest["documents"]}
    ledger_rows = {r["candidate_id"]: r for r in ledger.get("records", [])}
    promoted: list[str] = []
    for source_id, review in acceptance.get("records", {}).items():
        checks = review.get("checks", {})
        required = acceptance.get("required_checks", [])
        checks_pass = all(checks.get(name, {}).get("status") in {"pass", "not_applicable"} and (checks.get(name, {}).get("status") != "not_applicable" or checks.get(name, {}).get("reason")) for name in required)
        if review.get("status") not in {"accepted", "ready_to_accept"} or review.get("semantic_review", {}).get("status") != "passed" or not checks_pass:
            continue
        record = rows[source_id]
        native_path_value = record.get("native_source_path")
        source_path_value = record.get("source_text_path") or record.get("candidate_text_path") or native_path_value
        if not source_path_value:
            continue
        native_only = bool(native_path_value and not (record.get("source_text_path") or record.get("candidate_text_path")))
        source_path = path_for(source_path_value)
        if not source_path.is_file():
            continue
        was_ready = review.get("status") == "ready_to_accept"
        review["status"] = "accepted"
        record["accepted"] = True
        record["review_state"] = "accepted"
        record["source_status"] = "accepted"
        record["retrieval_status"] = "accepted_source"
        if source_path_value.startswith("source-library/austria/candidates/"):
            target_value = source_path_value.replace("source-library/austria/candidates/", "source-library/austria/documents/", 1)
            target_path = path_for(target_value)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(target_path))
        else:
            target_value = source_path_value
            target_path = source_path
        ledger_row = ledger_rows.get(source_id)
        if was_ready and not native_only:
            sys.path.insert(0, str(PACK / "scripts"))
            from convert_ris_capture import digest as converted_digest, extract_text, render_candidate
            raw_path = path_for(ledger_row.get("raw_path", "") if ledger_row else "")
            if not ledger_row or not raw_path.is_file():
                raise ValueError(f"{source_id} is ready to accept but its raw capture is missing")
            text, _ = extract_text(raw_path.read_bytes())
            rendered = render_candidate(record, ledger_row, text)
            target_path.write_bytes(rendered)
            record["converted_sha256"] = converted_digest(rendered)
            record["converted_bytes"] = len(rendered)
            ledger_row["converted_sha256"] = record["converted_sha256"]
            ledger_row["converted_bytes"] = record["converted_bytes"]
            promoted.append(source_id)
        if native_only:
            record["native_source_path"] = target_value
            record["candidate_path"] = target_value
            record.pop("source_text_path", None)
            record.pop("candidate_text_path", None)
        else:
            record["source_text_path"] = target_value
            record["candidate_text_path"] = target_value
        record["accepted"] = True
        record["review_state"] = "accepted"
        record["source_status"] = "accepted"
        record["retrieval_status"] = "accepted_source"
        if ledger_row is not None:
            if native_only:
                ledger_row["native_source_path"] = target_value
                if ledger_row.get("linked_payload"):
                    ledger_row["linked_payload"]["candidate_path"] = target_value
                ledger_row.pop("candidate_text_path", None)
                ledger_row.pop("source_text_path", None)
            else:
                ledger_row["candidate_text_path"] = target_value
                ledger_row["source_text_path"] = target_value
            ledger_row["accepted"] = True
            ledger_row["review_state"] = "accepted"
            ledger_row["retrieval_status"] = "accepted_source"
    manifest["accepted_source_count"] = sum(1 for r in manifest["documents"] if r.get("accepted"))
    manifest["candidate_source_count"] = sum(1 for r in manifest["documents"] if not r.get("accepted") and r.get("retrieved") and r.get("review_state") != "discovery_only")
    manifest["located_not_captured_count"] = sum(1 for r in manifest["documents"] if not r.get("retrieved"))
    manifest["discovery_only_count"] = sum(1 for r in manifest["documents"] if r.get("review_state") == "discovery_only")
    manifest["retrieved_review_candidate_count"] = manifest["candidate_source_count"]
    manifest["converted_review_candidate_count"] = sum(
        1 for r in manifest["documents"]
        if r.get("retrieved") and not r.get("accepted") and r.get("review_state") != "discovery_only"
        and (r.get("source_text_path") or r.get("candidate_text_path"))
        and not r.get("native_source_path") and r.get("source_type") != "official_form"
    )
    manifest["native_pdf_source_count"] = sum(1 for r in manifest["documents"] if r.get("native_source_path"))
    manifest["native_pdf_review_candidate_count"] = sum(1 for r in manifest["documents"] if r.get("native_source_path") and not r.get("accepted"))
    manifest["status"] = "source_acceptance_complete_country_coverage_incomplete" if manifest["candidate_source_count"] == 0 else "source_acceptance_in_progress_country_coverage_incomplete"
    manifest["retrieval_status"] = f"{manifest['accepted_source_count']} accepted; {manifest['candidate_source_count']} captured and pending review; {manifest['discovery_only_count']} discovery-only; {manifest['located_not_captured_count']} located but not captured"
    ledger["accepted_source_count"] = manifest["accepted_source_count"]
    ledger["converted_review_candidate_count"] = manifest["converted_review_candidate_count"]
    ledger["native_pdf_review_candidate_count"] = manifest.get("native_pdf_review_candidate_count", 0)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ACCEPTANCE.write_text(json.dumps(acceptance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"promoted": promoted, "count": len(promoted), "country_review": gate_report["country_review"]}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("review", "promote"))
    parser.add_argument("--strict", action="store_true", help="return nonzero while any mandatory gate is incomplete")
    args = parser.parse_args()
    if args.action == "promote":
        return promote()
    state, errors = gate_state({})
    print(json.dumps(state, ensure_ascii=False, indent=2))
    if errors:
        return 2
    return 1 if args.strict and state["country_review"] != "complete" else 0


if __name__ == "__main__":
    raise SystemExit(main())
