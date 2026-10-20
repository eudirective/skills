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


def validate_exact_receipt(receipt_path: Path) -> tuple[dict, bytes]:
    before = read_regular_file(receipt_path, "receipt")
    result = validate_route(receipt_path)
    after = read_regular_file(receipt_path, "receipt")
    if before != after:
        raise ReleaseBindingError("receipt_changed_during_validation")
    if result["status"] == "rejected_comprehensive_claim":
        raise ReleaseBindingError("comprehensive_claim_has_outstanding_work")
    return result, before


def prepare(receipt_path: Path, answer_path: Path, binding_path: Path) -> dict:
    result, receipt_bytes = validate_exact_receipt(receipt_path)
    answer_bytes = read_regular_file(answer_path, "answer")
    if binding_path.resolve() in {receipt_path.resolve(), answer_path.resolve()}:
        raise ReleaseBindingError("binding_path_must_be_separate")
    if binding_path.exists() or binding_path.is_symlink():
        raise ReleaseBindingError("binding_path_already_exists")
    binding = {
        "schema_version": "0.1.0",
        "route_ref": result["route_ref"],
        "receipt_sha256": digest(receipt_bytes),
        "answer_sha256": digest(answer_bytes),
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
    actual = {
        "route_ref": result["route_ref"],
        "receipt_sha256": digest(receipt_bytes),
        "answer_sha256": digest(answer_bytes),
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "release"):
        command = sub.add_parser(name)
        command.add_argument("--receipt", required=True, type=Path)
        command.add_argument("--answer", required=True, type=Path)
        command.add_argument("--binding", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.receipt, args.answer, args.binding)
            print(json.dumps({"status": "binding_created", **result}, sort_keys=True))
            return 0
        answer = release(args.receipt, args.answer, args.binding)
        sys.stdout.buffer.write(answer)
        return 0
    except (ContractError, RouteGateError, ReleaseBindingError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
