#!/usr/bin/env python3
"""Opt-in local binding check for one consultation receipt and answer artifact.

This wrapper is not a ChatGPT release gate, an authenticated approval system,
or proof that model-declared checks occurred. It is intended for synthetic or
abstract local workflows only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from consultation_route_gate import RouteGateError, validate_route
from contract_validate import ContractError, load_json, validate_obj


class ReleaseBindingError(ValueError):
    pass


def read_regular_file(path: Path, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ReleaseBindingError(f"{label}:not_a_regular_non_symlink_file")
    return path.read_bytes()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validation_digest(record: dict) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return digest(canonical)


def validate_exact_receipt(receipt_path: Path) -> tuple[dict, bytes]:
    before = read_regular_file(receipt_path, "receipt")
    result = validate_route(receipt_path)
    after = read_regular_file(receipt_path, "receipt")
    if before != after:
        raise ReleaseBindingError("receipt_changed_during_validation")
    if result["status"] == "rejected_comprehensive_claim":
        raise ReleaseBindingError("comprehensive_claim_has_outstanding_work")
    if result.get("dashboard_required"):
        record = result.get("validation_record")
        if not isinstance(record, dict):
            raise ReleaseBindingError("mandatory_validation_record_missing")
        if record.get("receipt_sha256") != digest(before):
            raise ReleaseBindingError("validation_record_receipt_digest_mismatch")
        if record.get("result") != result.get("status"):
            raise ReleaseBindingError("validation_record_result_mismatch")
    return result, before


def validate_dashboard_rendered(result: dict, answer_bytes: bytes) -> None:
    if not result.get("dashboard_required"):
        return
    preview = result.get("dashboard_preview")
    if not isinstance(preview, str) or not preview:
        raise ReleaseBindingError("mandatory_dashboard_preview_missing")
    validation_record = result.get("validation_record")
    if not isinstance(validation_record, dict):
        raise ReleaseBindingError("mandatory_validation_record_missing")
    if f"`{validation_record['receipt_sha256']}`" not in preview:
        raise ReleaseBindingError("dashboard_receipt_fingerprint_missing")
    if str(validation_record.get("result", "")).replace("_", " ") not in preview:
        raise ReleaseBindingError("dashboard_validation_result_missing")
    try:
        answer = answer_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ReleaseBindingError("answer_not_utf8_for_dashboard_check") from error
    if not answer.rstrip().endswith(preview):
        raise ReleaseBindingError("mandatory_dashboard_missing_or_not_at_end_of_answer")


def repair_dashboard_once(result: dict, answer_bytes: bytes) -> tuple[bytes, bool]:
    """Append one canonical validated board when the answer omitted it entirely."""
    try:
        validate_dashboard_rendered(result, answer_bytes)
        return answer_bytes, False
    except ReleaseBindingError as error:
        if str(error) != "mandatory_dashboard_missing_or_not_at_end_of_answer":
            raise
    preview = result.get("dashboard_preview")
    if not isinstance(preview, str) or not preview:
        raise ReleaseBindingError("mandatory_dashboard_preview_missing")
    try:
        answer = answer_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ReleaseBindingError("answer_not_utf8_for_dashboard_repair") from error
    marker = "## freemovement-law — Consultation Review"
    if marker in answer:
        raise ReleaseBindingError("dashboard_present_but_invalid_cannot_be_repaired")
    repaired = answer.rstrip().encode("utf-8") + b"\n\n" + preview.encode("utf-8")
    validate_dashboard_rendered(result, repaired)
    return repaired, True


def prepare(receipt_path: Path, answer_path: Path, binding_path: Path) -> dict:
    result, receipt_bytes = validate_exact_receipt(receipt_path)
    answer_bytes = read_regular_file(answer_path, "answer")
    validate_dashboard_rendered(result, answer_bytes)
    if binding_path.resolve() in {receipt_path.resolve(), answer_path.resolve()}:
        raise ReleaseBindingError("binding_path_must_be_separate")
    if binding_path.exists() or binding_path.is_symlink():
        raise ReleaseBindingError("binding_path_already_exists")
    binding = {
        "schema_version": "0.2.0",
        "route_ref": result["route_ref"],
        "receipt_sha256": digest(receipt_bytes),
        "answer_sha256": digest(answer_bytes),
        "validation_sha256": validation_digest(result["validation_record"]),
        "validated_status": result["status"],
        "coverage_claim": result["coverage_claim"],
    }
    validate_obj("consultation-release-binding", binding)
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with binding_path.open("xb") as handle:
            handle.write((json.dumps(binding, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    except FileExistsError as error:
        raise ReleaseBindingError("binding_path_already_exists") from error
    return binding


def release(receipt_path: Path, answer_path: Path, binding_path: Path) -> bytes:
    binding_bytes = read_regular_file(binding_path, "binding")
    binding = load_json(binding_path)
    validate_obj("consultation-release-binding", binding)
    result, receipt_bytes = validate_exact_receipt(receipt_path)
    answer_bytes = read_regular_file(answer_path, "answer")
    validate_dashboard_rendered(result, answer_bytes)
    actual = {
        "route_ref": result["route_ref"],
        "receipt_sha256": digest(receipt_bytes),
        "answer_sha256": digest(answer_bytes),
        "validation_sha256": validation_digest(result["validation_record"]),
        "validated_status": result["status"],
        "coverage_claim": result["coverage_claim"],
    }
    expected = {key: binding[key] for key in actual}
    if actual != expected:
        raise ReleaseBindingError("binding_mismatch:receipt_answer_or_validation_changed")
    if read_regular_file(binding_path, "binding") != binding_bytes:
        raise ReleaseBindingError("binding_changed_during_validation")
    # Emit the exact bytes whose digest was checked above.
    return answer_bytes


def controlled_release(receipt_path: Path, answer_path: Path) -> bytes:
    """Validate and emit one strict-version answer through this local process.

    This is an opt-in local release path for the versioned consultation
    contract. It may append the canonical dashboard once when entirely absent.
    It is not a ChatGPT host veto or an authenticated approval.
    """
    first_result, first_receipt = validate_exact_receipt(receipt_path)
    source_answer = read_regular_file(answer_path, "answer")
    try:
        receipt = json.loads(first_receipt.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseBindingError("receipt_json_invalid") from error
    if receipt.get("schema_version") not in {"0.5.0", "0.6.0", "0.7.0"} or receipt.get("request_kind") not in {
        "applicant_guidance", "source_research",
    }:
        raise ReleaseBindingError("controlled_release_requires_receipt_0_5_or_later")
    if not first_result.get("dashboard_required"):
        raise ReleaseBindingError("controlled_release_requires_validated_dashboard")
    answer, _repaired = repair_dashboard_once(first_result, source_answer)

    # Revalidate and reread immediately before output; only the exact checked
    # receipt, validation result and answer bytes may pass through this call.
    second_result, second_receipt = validate_exact_receipt(receipt_path)
    second_source_answer = read_regular_file(answer_path, "answer")
    second_answer, _second_repaired = repair_dashboard_once(second_result, second_source_answer)
    if (first_receipt != second_receipt or source_answer != second_source_answer or answer != second_answer or
            validation_digest(first_result["validation_record"]) !=
            validation_digest(second_result["validation_record"])):
        raise ReleaseBindingError("controlled_release_artifact_changed_during_validation")
    validate_dashboard_rendered(second_result, second_answer)
    return second_answer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "release"):
        command = sub.add_parser(name)
        command.add_argument("--receipt", required=True, type=Path)
        command.add_argument("--answer", required=True, type=Path)
        command.add_argument("--binding", required=True, type=Path)
    controlled = sub.add_parser("controlled-release")
    controlled.add_argument("--receipt", required=True, type=Path)
    controlled.add_argument("--answer", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.receipt, args.answer, args.binding)
            print(json.dumps({"status": "binding_created", **result}, sort_keys=True))
            return 0
        if args.command == "controlled-release":
            answer = controlled_release(args.receipt, args.answer)
        else:
            answer = release(args.receipt, args.answer, args.binding)
        sys.stdout.buffer.write(answer)
        return 0
    except (ContractError, RouteGateError, ReleaseBindingError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
