#!/usr/bin/env python3
"""Select C27 discovery checks from synthetic abstract consultation signals.

This utility does not accept case narratives, jurisdictions, identities, dates,
documents, or arbitrary case facts. It validates declared signal IDs against a
static routing matrix and check IDs against the existing C27 registry. A
selection is a routing test result, not legal analysis or evidence of execution.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "references" / "consultation-issue-routing.json"
REGISTRY_PATH = ROOT / "references" / "state-engine" / "check-registry.json"
FIXTURE_KIND = "synthetic_abstract"
PROCEEDING_ID_PATTERN = re.compile(r"^p_[1-9][0-9]{0,2}$")


class SelectionError(ValueError):
    """Invalid synthetic fixture or inconsistent routing metadata."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SelectionError(f"cannot_read_json:{path.name}") from error
    if not isinstance(value, dict):
        raise SelectionError(f"json_root_must_be_object:{path.name}")
    return value


def registry_check_ids(registry: dict[str, Any]) -> set[str]:
    checks = registry.get("checks")
    if not isinstance(checks, list):
        raise SelectionError("registry_checks_missing")
    result: set[str] = set()
    for item in checks:
        if not isinstance(item, dict) or not isinstance(item.get("check_id"), str):
            raise SelectionError("registry_check_invalid")
        check_id = item["check_id"]
        if check_id in result:
            raise SelectionError(f"registry_check_duplicate:{check_id}")
        result.add(check_id)
    return result


def signal_catalog(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = matrix.get("signal_catalog")
    if not isinstance(raw, list):
        raise SelectionError("signal_catalog_missing")
    result: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise SelectionError("signal_definition_invalid")
        signal_id = item.get("signal_id")
        description = item.get("neutral_description")
        if not isinstance(signal_id, str) or not signal_id:
            raise SelectionError("signal_id_invalid")
        if not isinstance(description, str) or not description:
            raise SelectionError(f"signal_description_missing:{signal_id}")
        if signal_id in result:
            raise SelectionError(f"signal_duplicate:{signal_id}")
        result[signal_id] = item
    return result


def _as_id_list(value: Any, label: str, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise SelectionError(f"{label}_must_be_array")
    if not allow_empty and not value:
        raise SelectionError(f"{label}_must_not_be_empty")
    if any(not isinstance(item, str) or not item for item in value):
        raise SelectionError(f"{label}_contains_invalid_id")
    if len(value) != len(set(value)):
        raise SelectionError(f"{label}_contains_duplicate_id")
    return value


def validate_configuration(
    matrix: dict[str, Any],
    registry: dict[str, Any],
    root: Path = ROOT,
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    """Validate every matrix check ID and every owned core reference path."""
    if matrix.get("schema") != "freemovement-consultation-issue-routing/0.1.0":
        raise SelectionError("unsupported_matrix_schema")
    signal_defs = signal_catalog(matrix)
    valid_checks = registry_check_ids(registry)

    owners = matrix.get("source_owners")
    if not isinstance(owners, dict) or not owners:
        raise SelectionError("source_owners_missing")
    for owner_id, owner in owners.items():
        if not isinstance(owner_id, str) or not isinstance(owner, dict):
            raise SelectionError("source_owner_invalid")
        refs = owner.get("core_references", [])
        if not isinstance(refs, list):
            raise SelectionError(f"source_references_must_be_array:{owner_id}")
        for ref in refs:
            if not isinstance(ref, str) or not ref:
                raise SelectionError(f"source_reference_invalid:{owner_id}")
            candidate = (root / ref).resolve()
            allowed_root = root.resolve().parent
            try:
                candidate.relative_to(allowed_root)
            except ValueError as error:
                raise SelectionError(f"source_reference_outside_skills_tree:{owner_id}") from error
            if not candidate.is_file():
                raise SelectionError(f"source_reference_missing:{owner_id}:{ref}")

    routes = matrix.get("routes")
    if not isinstance(routes, list) or not routes:
        raise SelectionError("routes_missing")
    route_ids: set[str] = set()
    for route in routes:
        if not isinstance(route, dict):
            raise SelectionError("route_invalid")
        route_id = route.get("route_id")
        if not isinstance(route_id, str) or not route_id:
            raise SelectionError("route_id_invalid")
        if route_id in route_ids:
            raise SelectionError(f"route_duplicate:{route_id}")
        route_ids.add(route_id)

        activation = _as_id_list(route.get("when_any_signal"), f"{route_id}.when_any_signal", False)
        for signal_id in activation:
            if signal_id not in signal_defs:
                raise SelectionError(f"route_signal_unknown:{route_id}:{signal_id}")
        mandatory = _as_id_list(route.get("mandatory_checks"), f"{route_id}.mandatory_checks", False)
        for check_id in mandatory:
            if check_id not in valid_checks:
                raise SelectionError(f"check_id_unknown:{route_id}:{check_id}")

        owner_ids = _as_id_list(route.get("source_owner_ids"), f"{route_id}.source_owner_ids", False)
        for owner_id in owner_ids:
            if owner_id not in owners:
                raise SelectionError(f"source_owner_unknown:{route_id}:{owner_id}")
        conditional_owners = route.get("conditional_source_owner_ids", [])
        if not isinstance(conditional_owners, list):
            raise SelectionError(f"conditional_source_owners_must_be_array:{route_id}")
        for owner_condition in conditional_owners:
            if not isinstance(owner_condition, dict):
                raise SelectionError(f"conditional_source_owner_invalid:{route_id}")
            owner_signals = _as_id_list(
                owner_condition.get("when_any_signal"),
                f"{route_id}.conditional_source_owner_signals",
                False,
            )
            for signal_id in owner_signals:
                if signal_id not in signal_defs:
                    raise SelectionError(f"conditional_signal_unknown:{route_id}:{signal_id}")
            conditional_owner_ids = _as_id_list(
                owner_condition.get("source_owner_ids"),
                f"{route_id}.conditional_source_owner_ids",
                False,
            )
            for owner_id in conditional_owner_ids:
                if owner_id not in owners:
                    raise SelectionError(f"source_owner_unknown:{route_id}:{owner_id}")
        for section in ("triggering_conditions", "source_references", "negative_applicability", "related_independent_issues"):
            if not isinstance(route.get(section, []), list):
                raise SelectionError(f"route_section_must_be_array:{route_id}:{section}")
        for section in ("triggering_conditions", "source_references"):
            values = route.get(section, [])
            if not values or any(not isinstance(value, str) or not value.strip() for value in values):
                raise SelectionError(f"route_section_has_invalid_entry:{route_id}:{section}")
        related = route.get("related_independent_issues", [])
        if any(not isinstance(value, str) or not value for value in related):
            raise SelectionError(f"related_issue_invalid:{route_id}")
        angle_review = route.get("potential_attack_angle_review")
        if not isinstance(angle_review, dict) or angle_review.get("required") is not True:
            raise SelectionError(f"attack_angle_review_required:{route_id}")
        if not isinstance(angle_review.get("review_topics"), list) or not angle_review["review_topics"]:
            raise SelectionError(f"attack_angle_topics_missing:{route_id}")

        conditional = route.get("conditional_checks")
        if not isinstance(conditional, list):
            raise SelectionError(f"conditional_checks_must_be_array:{route_id}")
        for condition in conditional:
            if not isinstance(condition, dict):
                raise SelectionError(f"conditional_check_invalid:{route_id}")
            if not isinstance(condition.get("reason"), str) or not condition["reason"].strip():
                raise SelectionError(f"conditional_reason_missing:{route_id}")
            when = _as_id_list(condition.get("when_any_signal"), f"{route_id}.conditional_signal", False)
            unless = _as_id_list(condition.get("unless_any_signal", []), f"{route_id}.conditional_exclusion")
            for signal_id in when + unless:
                if signal_id not in signal_defs:
                    raise SelectionError(f"conditional_signal_unknown:{route_id}:{signal_id}")
            check_ids = _as_id_list(condition.get("check_ids"), f"{route_id}.conditional_check_ids", False)
            for check_id in check_ids:
                if check_id not in valid_checks:
                    raise SelectionError(f"check_id_unknown:{route_id}:{check_id}")

        for exclusion in route.get("negative_applicability", []):
            if not isinstance(exclusion, dict):
                continue
            signal_id = exclusion.get("signal_id")
            opposite = exclusion.get("opposes_signal_id")
            if signal_id not in signal_defs or opposite not in signal_defs:
                raise SelectionError(f"negative_signal_unknown:{route_id}")
            if signal_defs[signal_id].get("polarity") != "negative":
                raise SelectionError(f"negative_signal_polarity_missing:{route_id}:{signal_id}")
            if signal_defs[signal_id].get("opposes_signal_id") != opposite:
                raise SelectionError(f"negative_signal_pair_mismatch:{route_id}:{signal_id}")
            for check_id in _as_id_list(
                exclusion.get("excluded_check_ids"), f"{route_id}.excluded_check_ids", False
            ):
                if check_id not in valid_checks:
                    raise SelectionError(f"check_id_unknown:{route_id}:{check_id}")

    for route in routes:
        for related_route_id in route.get("related_independent_issues", []):
            if related_route_id not in route_ids:
                raise SelectionError(f"related_issue_route_unknown:{route['route_id']}:{related_route_id}")

    return signal_defs, valid_checks


def validate_fixture(
    fixture: dict[str, Any],
    signal_defs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if set(fixture) != {"fixture_kind", "proceedings"}:
        raise SelectionError("fixture_fields_not_allowed")
    if fixture.get("fixture_kind") != FIXTURE_KIND:
        raise SelectionError("fixture_must_be_synthetic_abstract")
    proceedings = fixture.get("proceedings")
    if not isinstance(proceedings, list) or not proceedings:
        raise SelectionError("proceedings_must_be_nonempty_array")
    seen_proceedings: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in proceedings:
        if not isinstance(item, dict) or set(item) != {"proceeding_id", "signal_ids"}:
            raise SelectionError("proceeding_fields_not_allowed")
        proceeding_id = item.get("proceeding_id")
        if not isinstance(proceeding_id, str) or not PROCEEDING_ID_PATTERN.fullmatch(proceeding_id):
                raise SelectionError("proceeding_id_must_be_synthetic_sequence_id")
        if proceeding_id in seen_proceedings:
            raise SelectionError(f"proceeding_duplicate:{proceeding_id}")
        seen_proceedings.add(proceeding_id)
        signal_ids = _as_id_list(item.get("signal_ids"), f"{proceeding_id}.signal_ids")
        for signal_id in signal_ids:
            if signal_id not in signal_defs:
                raise SelectionError(f"signal_unknown:{signal_id}")
        signal_set = set(signal_ids)
        for signal_id in signal_ids:
            opposite = signal_defs[signal_id].get("opposes_signal_id")
            if opposite and opposite in signal_set:
                raise SelectionError(f"contradictory_signals:{signal_id}:{opposite}")
        normalized.append(
            {
                "proceeding_id": proceeding_id,
                "signal_ids": sorted(signal_ids),
            }
        )
    return sorted(normalized, key=lambda item: item["proceeding_id"])


def select_check_ids(
    signal_ids: list[str],
    matrix: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    root: Path = ROOT,
) -> list[str]:
    """Return sorted selected C27 IDs for one opaque synthetic signal set.

    The caller supplies signal IDs only. No issue text, jurisdiction, fact,
    applicant narrative, or proceeding history is accepted.
    """
    matrix = matrix or load_json(MATRIX_PATH)
    registry = registry or load_json(REGISTRY_PATH)
    signal_defs, valid_checks = validate_configuration(matrix, registry, root)
    normalized = _as_id_list(signal_ids, "signal_ids")
    unknown = sorted(set(normalized) - set(signal_defs))
    if unknown:
        raise SelectionError(f"signal_unknown:{unknown[0]}")
    signals = set(normalized)
    for signal_id in normalized:
        opposite = signal_defs[signal_id].get("opposes_signal_id")
        if opposite and opposite in signals:
            raise SelectionError(f"contradictory_signals:{signal_id}:{opposite}")

    selected: set[str] = set()
    for route in matrix["routes"]:
        if not set(route["when_any_signal"]) & signals:
            continue
        selected.update(route["mandatory_checks"])
        for condition in route["conditional_checks"]:
            matched = set(condition["when_any_signal"]) & signals
            excluded = set(condition.get("unless_any_signal", [])) & signals
            if matched and not excluded:
                selected.update(condition["check_ids"])
    invalid = sorted(selected - valid_checks)
    if invalid:
        raise SelectionError(f"check_id_unknown:selected:{invalid[0]}")
    return sorted(selected)


def select_checks(
    fixture: dict[str, Any],
    matrix: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    matrix = matrix or load_json(MATRIX_PATH)
    registry = registry or load_json(REGISTRY_PATH)
    signal_defs, _ = validate_configuration(matrix, registry, root)
    proceedings = validate_fixture(fixture, signal_defs)
    routes = matrix["routes"]
    selected_proceedings = []
    for proceeding in proceedings:
        signal_set = set(proceeding["signal_ids"])
        issue_routes = []
        combined: dict[str, set[str]] = {}
        for route in routes:
            matched = sorted(set(route["when_any_signal"]) & signal_set)
            if not matched:
                continue
            route_checks: dict[str, set[str]] = {}
            for check_id in route["mandatory_checks"]:
                route_checks.setdefault(check_id, set()).add(
                    "mandatory_for:" + ",".join(matched)
                )
            for condition in route["conditional_checks"]:
                condition_matches = sorted(set(condition["when_any_signal"]) & signal_set)
                exclusions = set(condition.get("unless_any_signal", [])) & signal_set
                if condition_matches and not exclusions:
                    reason = "conditional:" + ",".join(condition_matches)
                    for check_id in condition["check_ids"]:
                        route_checks.setdefault(check_id, set()).add(reason)
            route_check_ids = sorted(route_checks)
            issue_routes.append(
                {
                    "route_id": route["route_id"],
                    "trigger_signal_ids": matched,
                    "check_ids": route_check_ids,
                }
            )
            for check_id, reasons in route_checks.items():
                combined.setdefault(check_id, set()).add(route["route_id"] + ":" + ",".join(sorted(reasons)))
        selected_proceedings.append(
            {
                "proceeding_id": proceeding["proceeding_id"],
                "declared_signal_ids": proceeding["signal_ids"],
                "issue_routes": sorted(issue_routes, key=lambda item: item["route_id"]),
                "selected_checks": [
                    {"check_id": check_id, "selection_reasons": sorted(combined[check_id])}
                    for check_id in sorted(combined)
                ],
            }
        )
    return {
        "schema": "freemovement-synthetic-issue-selection/0.1.0",
        "fixture_kind": FIXTURE_KIND,
        "selection_limit": "Declared abstract signals only; not issue extraction, legal assessment, source verification, or proof of engine execution.",
        "proceedings": selected_proceedings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="synthetic abstract JSON fixture")
    args = parser.parse_args()
    try:
        result = select_checks(load_json(args.fixture))
    except SelectionError as error:
        print(json.dumps({"status": "rejected", "reason": str(error)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
