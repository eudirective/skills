#!/usr/bin/env python3
"""Check the Cyprus inventory's cross-register completeness before review or sync."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"


def read_json(name: str) -> dict[str, Any]:
    path = REFERENCES / name
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    manifest = read_json("candidate-manifest.json")
    rules_doc = read_json("source-rules.json")
    acceptance = read_json("source-acceptance.json")
    dependencies = read_json("source-dependencies.json")
    coverage = read_json("coverage-model.json")

    documents = manifest.get("documents", [])
    doc_ids = [item.get("id") for item in documents if isinstance(item, dict)]
    known_ids = {item for item in doc_ids if isinstance(item, str) and item}
    require(len(doc_ids) == len(documents), "manifest contains a non-object record", errors)
    require(len(doc_ids) == len(known_ids), "manifest record IDs are missing or duplicated", errors)

    rules = rules_doc.get("rules", [])
    rule_ids = [item.get("rule_id") for item in rules if isinstance(item, dict)]
    require(len(rule_ids) == len(rules), "source-rules contains a non-object rule", errors)
    require(all(isinstance(item, str) and item for item in rule_ids), "source-rule ID is missing", errors)
    require(len(rule_ids) == len(set(rule_ids)), "source-rule IDs are duplicated", errors)
    rule_memberships: Counter[str] = Counter()
    member_rule: dict[str, str] = {}
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rid = rule.get("rule_id")
        require(bool(rule.get("retrieval")), f"{rid}: retrieval rule is missing", errors)
        require(bool(rule.get("conversion")), f"{rid}: conversion rule is missing", errors)
        require(bool(rule.get("semantic_checks")), f"{rid}: semantic checks are missing", errors)
        for source_id in rule.get("source_ids", []):
            if isinstance(source_id, str):
                rule_memberships[source_id] += 1
                member_rule[source_id] = str(rid)
    for source_id in sorted(known_ids):
        count = rule_memberships[source_id]
        require(count == 1, f"{source_id}: expected exactly one retrieval/conversion rule, found {count}", errors)
        record = next((item for item in documents if item.get("id") == source_id), {})
        require(record.get("source_rule_id") == member_rule.get(source_id),
                f"{source_id}: manifest source_rule_id does not match its rule mapping", errors)
    for source_id in sorted(set(rule_memberships) - known_ids):
        require(False, f"source-rules references unknown manifest record {source_id}", errors)

    source_list = (REFERENCES / "source-list.md").read_text(encoding="utf-8")
    listed_ids = set(re.findall(r"^\|\s*`(cy-[a-z0-9-]+)`\s*\|", source_list, re.MULTILINE))
    require(listed_ids == known_ids,
            f"source-list/manifest mismatch: {len(known_ids-listed_ids)} missing rows, {len(listed_ids-known_ids)} extra rows",
            errors)

    for key in ("accepted_source_count", "accepted_current_law_source_count",
                "accepted_derived_text_count", "accepted_derived_passage_count", "accepted_external_reference_count"):
        require(manifest.get(key) == acceptance.get(key),
                f"manifest and source-acceptance disagree on {key}", errors)
    manifest_counts = manifest.get("library_disposition_counts", {})
    for state_name in ("external_reference_status_counts", "local_copy_status_counts"):
        require(manifest_counts.get(state_name) == acceptance.get(state_name),
                f"manifest and source-acceptance disagree on {state_name}", errors)

    dependency_rows = dependencies.get("dependencies", [])
    dependency_ids = {item.get("id") for item in dependency_rows if isinstance(item, dict)}
    require(all(isinstance(item, str) and item for item in dependency_ids), "dependency ID is missing", errors)
    require(len(dependency_ids) == len(dependency_rows), "dependency IDs are missing or duplicated", errors)
    for dependency in dependency_rows:
        if not isinstance(dependency, dict):
            continue
        require(bool(dependency.get("relationship")), f"{dependency.get('id')}: relationship is missing", errors)
        require(bool(dependency.get("status")), f"{dependency.get('id')}: currentness/review status is missing", errors)
        require(bool(dependency.get("instrument") or dependency.get("instruments")),
                f"{dependency.get('id')}: instrument is missing", errors)
        for source_id in dependency.get("source_ids", []):
            require(source_id in known_ids,
                    f"{dependency.get('id')}: references unknown source {source_id}", errors)

    gap_rows = coverage.get("unresolved_source_gaps", [])
    gap_ids = {item.get("gap_id") for item in gap_rows if isinstance(item, dict)}
    topic_rows = coverage.get("topics", [])
    topic_ids = {item.get("topic_id") for item in topic_rows if isinstance(item, dict)}
    require(all(isinstance(item, str) and item for item in topic_ids), "coverage topic ID is missing", errors)
    require(len(topic_ids) == len(topic_rows), "coverage topic IDs are missing or duplicated", errors)
    referenced_dependency_ids: set[str] = set()
    for topic in topic_rows:
        if not isinstance(topic, dict):
            continue
        tid = topic.get("topic_id")
        require(bool(topic.get("required_layers")), f"{tid}: required legal layers are not specified", errors)
        require(bool(topic.get("source_ids")), f"{tid}: no sources are mapped to the topic", errors)
        for source_id in topic.get("source_ids", []):
            require(source_id in known_ids, f"{tid}: references unknown source {source_id}", errors)
        for dependency_id in topic.get("dependency_ids", []):
            referenced_dependency_ids.add(dependency_id)
            require(dependency_id in dependency_ids, f"{tid}: references unknown dependency {dependency_id}", errors)
        for gap_id in topic.get("source_gap_ids", []):
            require(gap_id in gap_ids, f"{tid}: references unknown source gap {gap_id}", errors)
        if "incomplete" in str(topic.get("status", "")).lower():
            require(bool(topic.get("unresolved_instruments") or topic.get("source_gap_ids")),
                    f"{tid}: incomplete topic lacks a recorded unresolved source", errors)
    require(referenced_dependency_ids == dependency_ids,
            "coverage/dependency mismatch: every dependency must be linked from at least one topic",
            errors)

    for key in ("accepted_source_count", "accepted_current_law_source_count", "accepted_topic_count"):
        if key in coverage:
            require(coverage.get(key) == acceptance.get(key),
                    f"coverage model and source-acceptance disagree on {key}", errors)
    require(coverage.get("country_review_complete") == acceptance.get("country_review_complete"),
            "coverage model and source-acceptance disagree on country_review_complete", errors)

    if coverage.get("country_review_complete"):
        require(not gap_rows, "country review is complete while source gaps remain", errors)
        require(all(str(item.get("status", "")).lower() in {"adequate", "complete"} for item in topic_rows),
                "country review is complete while a topic is not marked adequate/complete", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAILED: {len(errors)} inventory consistency issue(s)", file=sys.stderr)
        return 1

    print(json.dumps({
        "ok": True,
        "source_records": len(known_ids),
        "retrieval_conversion_rules": len(rule_ids),
        "dependency_records": len(dependency_ids),
        "coverage_topics": len(topic_ids),
        "source_list_rows": len(listed_ids),
        "accepted_current_law_sources": manifest.get("accepted_current_law_source_count", 0),
        "accepted_derived_passages": manifest.get("accepted_derived_passage_count", 0),
        "country_review_complete": coverage.get("country_review_complete", False),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
