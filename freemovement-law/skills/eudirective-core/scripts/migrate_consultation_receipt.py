#!/usr/bin/env python3
"""Conservatively migrate a privacy-minimised consultation receipt 0.7.0 to 0.8.0.

The required Full/Limited consultation mode is an explicit operator input. The
migrator never infers it from the older dashboard mode or from coverage.
Ambiguous strategy-to-issue links are rejected, and the new core finalisation
operation is recorded as not checked rather than being fabricated as complete.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from consultation_dashboard import unresolved_issue_refs
from consultation_route_gate import RouteGateError, STRATEGY_TRIGGER_SIGNALS, validate_privacy_minimisation
from contract_validate import ContractError, validate_obj


class MigrationError(ValueError):
    pass


def migrate_receipt(receipt: dict, consultation_mode: str) -> dict:
    if consultation_mode not in {"full", "limited"}:
        raise MigrationError("consultation_mode_must_be_full_or_limited")
    if not isinstance(receipt, dict) or receipt.get("schema_version") != "0.7.0":
        raise MigrationError("migration_requires_receipt_0_7_0")
    if receipt.get("request_kind") not in {"applicant_guidance", "source_research"}:
        raise MigrationError("migration_requires_in_scope_consultation")
    validate_obj("consultation-route-receipt", receipt)
    validate_privacy_minimisation(receipt)

    result = copy.deepcopy(receipt)
    result["schema_version"] = "0.8.0"
    result["consultation_mode"] = consultation_mode
    result["dashboard"].pop("mode", None)

    issues_by_ref = {item["issue_ref"]: item for item in result.get("issues", [])}
    strategy = result["strategy_assessment"]
    linked_refs: set[str] = set()
    for review in strategy["trigger_reviews"]:
        candidates: set[str] = set()
        trigger_id = review["trigger_id"]
        if review["status"] == "triggered":
            signal_ids = STRATEGY_TRIGGER_SIGNALS.get(trigger_id, set())
            if signal_ids:
                candidates = {
                    issue["issue_ref"] for issue in issues_by_ref.values()
                    if signal_ids.intersection(issue.get("signal_ids", []))
                    and issue["evidence_ref"] in review.get("evidence_refs", [])
                }
            else:
                candidates = {
                    issue["issue_ref"] for issue in issues_by_ref.values()
                    if issue["evidence_ref"] in review.get("evidence_refs", [])
                }
            if not candidates:
                raise MigrationError(f"strategy_issue_link_requires_manual_review:{trigger_id}")
        elif review["status"] == "unknown":
            candidates = {
                issue["issue_ref"] for issue in issues_by_ref.values()
                if issue["evidence_ref"] in review.get("evidence_refs", [])
            }
            if not candidates:
                raise MigrationError(f"strategy_issue_link_requires_manual_review:{trigger_id}")
        review["issue_refs"] = sorted(candidates)
        linked_refs.update(candidates)

    strategy["issue_refs"] = sorted(linked_refs)
    if strategy["mode"] == "limited":
        limitation = strategy.get("limitation")
        if not isinstance(limitation, dict):
            raise MigrationError("strategy_limitation_requires_manual_review")
        open_refs = unresolved_issue_refs(result)
        limitation_refs = {
            issue_ref for issue_ref in open_refs
            if issues_by_ref[issue_ref]["evidence_ref"] in limitation.get("evidence_refs", [])
        }
        if not limitation_refs:
            raise MigrationError("strategy_limitation_issue_link_requires_manual_review")
        limitation["issue_refs"] = sorted(limitation_refs)

    if not any(
        item.get("operation_id") == "consultation_finalisation"
        for item in result["operations"]
    ):
        result["operations"].append({
            "operation_id": "consultation_finalisation",
            "applicability": "required",
            "status": "not_checked",
            "reason_code": "not_attempted",
            "evidence_refs": [],
        })

    validate_obj("consultation-route-receipt", result)
    validate_privacy_minimisation(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--consultation-mode", required=True, choices=("full", "limited"))
    args = parser.parse_args(argv)
    try:
        source = args.input.read_bytes()
        if len(source) > 2_000_000:
            raise MigrationError("receipt_too_large")
        receipt = json.loads(source.decode("utf-8"))
        migrated = migrate_receipt(receipt, args.consultation_mode)
        payload = (json.dumps(migrated, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as handle:
            handle.write(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ContractError, MigrationError, RouteGateError) as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "migrated",
        "schema_version": migrated["schema_version"],
        "consultation_mode": migrated["consultation_mode"],
        "finalisation_status": next(
            item["status"] for item in migrated["operations"]
            if item["operation_id"] == "consultation_finalisation"
        ),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
