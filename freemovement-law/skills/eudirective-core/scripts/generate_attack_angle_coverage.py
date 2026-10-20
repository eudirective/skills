#!/usr/bin/env python3
"""Generate a deterministic inventory of screening coverage and boundaries."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from attack_angle_synthesis import SUPPORTED_SIGNAL_KINDS
from contract_validate import ContractError, digest_obj, load_json, validate_obj
from module_conformance import ConformanceError, validate_paths
from source_library_paths import compatibility_root

CORE_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = CORE_ROOT.parents[1]
MODULES = (
    PLUGIN_ROOT / "skills" / "eudirective-ms-sweden",
    PLUGIN_ROOT / "skills" / "eudirective-ac-turkiye",
)
ALLOWED_CAPABILITIES = {"deterministic", "model_led", "synthetic_only", "not_implemented", "unavailable"}


class InventoryError(ValueError):
    pass


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return load_json(path)


def source_record(path: Path) -> dict:
    return {"path": path.relative_to(PLUGIN_ROOT).as_posix(), "sha256": file_sha(path)}


def source_pack_index() -> dict:
    path = compatibility_root() / "core-source-pack-manifest-0.6.1.json"
    manifest = read_json(path)
    return {item["source_id"]: item for item in manifest["sources"]}


def validate_inventory(inventory: dict) -> None:
    record_ids = [item["record_id"] for item in inventory["records"]]
    if len(record_ids) != len(set(record_ids)):
        raise InventoryError("duplicate_coverage_record_id")
    for item in inventory["records"]:
        if item["capability"] not in ALLOWED_CAPABILITIES:
            raise InventoryError(f"unknown_capability:{item['record_id']}:{item['capability']}")
        kind = item["record_type"]
        if kind == "c27_atomic_prompt":
            if item["capability"] == "model_led" and (
                item["c5d_predicate_status"] != "not_a_C5d_predicate" or
                item["legal_violation_claim_allowed"] is not False
            ):
                raise InventoryError(f"model_guidance_misreported_as_c5d_execution:{item['record_id']}")
        elif kind == "core_c5d_pattern" and item["legal_violation_status"] != "not_determined":
            raise InventoryError(f"c5d_legal_status_overclaim:{item['record_id']}")
        elif kind == "core_c5d_pattern" and item["capability"] == "deterministic" and (
            item["implementation_scope"] != "deterministic_synthetic_predicate" or
            item["execution_boundary"] != "synthetic_only"
        ):
            raise InventoryError(f"c5d_execution_boundary_missing:{item['record_id']}")
        elif kind == "adapted_strategy_heuristic" and item["not_a_legal_attack_angle"] is not True:
            raise InventoryError(f"adapted_strategy_mislabelled_as_legal_angle:{item['record_id']}")


def validate_module_references(export: dict, sidecar: dict) -> tuple[set[str], set[str], set[str], dict[str, dict]]:
    namespace = export["id_namespace"]
    module_sources = {item["source_id"] for item in export["source_records"]}
    module_attacks = {item["attack_angle_id"]: item for item in export["attack_angle_records"]}
    module_authorities = {item["authority_id"] for item in export["authority_records"]}
    module_routes = {item["route_id"] for item in export["route_records"]}
    if len(module_attacks) != len(export["attack_angle_records"]):
        raise InventoryError(f"duplicate_module_attack_id:{export['module_id']}")
    for attack_id, attack in module_attacks.items():
        if not attack_id.startswith(namespace + ":attack:"):
            raise InventoryError(f"module_attack_namespace_mismatch:{attack_id}")
        if (not set(attack["source_refs"]) <= module_sources or
            not set(attack["authority_refs"]) <= module_authorities or
            not set(attack["route_refs"]) <= module_routes):
            raise InventoryError(f"module_attack_orphan_reference:{attack_id}")
    if sidecar["producer_module_id"] != export["module_id"]:
        raise InventoryError(f"sidecar_module_owner_mismatch:{export['module_id']}")
    if sidecar["jurisdiction"] != export["jurisdiction"]:
        raise InventoryError(f"sidecar_jurisdiction_mismatch:{export['module_id']}")
    if sidecar["bound_export_sha256"] != digest_obj(export):
        raise InventoryError(f"sidecar_export_binding_mismatch:{export['module_id']}")
    seen: set[str] = set()
    for rule in sidecar["rules"]:
        rule_id = rule["rule_id"]
        if rule_id in seen or not rule_id.startswith(namespace + ":"):
            raise InventoryError(f"sidecar_rule_namespace_or_duplicate:{rule_id}")
        seen.add(rule_id)
        if rule.get("attack_angle_id") and rule["attack_angle_id"] not in module_attacks:
            raise InventoryError(f"sidecar_attack_reference_missing:{rule_id}")
        cited_sources = {item["source_id"] for item in rule.get("source_citations", [])}
        if not cited_sources <= module_sources:
            raise InventoryError(f"sidecar_source_reference_missing:{rule_id}")
    return module_sources, module_authorities, module_routes, module_attacks


def load_inputs() -> tuple[dict, list[dict]]:
    registry_path = CORE_ROOT / "references/state-engine/check-registry.json"
    catalog_path = CORE_ROOT / "references/attack-angles/core-attack-angle-catalog.json"
    stratagem_path = CORE_ROOT / "references/stratagems/adapted-stratagem-catalog.json"
    topic_path = CORE_ROOT / "references/attack-angles/consultation-topic-review-pathways.json"
    registry, catalog, stratagems, topic_catalog = (
        read_json(registry_path), read_json(catalog_path), read_json(stratagem_path), read_json(topic_path))
    if not isinstance(registry.get("checks"), list) or not isinstance(catalog.get("patterns"), list):
        raise InventoryError("registry_or_core_catalog_malformed")
    pack_sources = source_pack_index()

    family_ids = {item["family_id"] for item in registry["families"]}
    c27_family_ids = family_ids
    check_ids: set[str] = set()
    records: list[dict] = []
    for check in registry["checks"]:
        check_id = check["check_id"]
        if check_id in check_ids:
            raise InventoryError(f"duplicate_c27_check_id:{check_id}")
        check_ids.add(check_id)
        family = check["family"]
        if family not in family_ids or not check_id.startswith(family + "."):
            raise InventoryError(f"c27_namespace_or_family_mismatch:{check_id}")
        capability = {
            "model_guidance": "model_led",
            "synthetic_only": "synthetic_only",
            "not_implemented": "not_implemented",
        }.get(check["capability"], "unavailable")
        ref = check["reference"]
        ref_path = (CORE_ROOT / ref).resolve()
        try:
            ref_path.relative_to(CORE_ROOT.resolve())
        except ValueError as error:
            raise InventoryError(f"c27_reference_escapes_core:{check_id}") from error
        if not ref_path.is_file():
            raise InventoryError(f"c27_reference_missing:{check_id}:{ref}")
        records.append({
            "record_id": check_id,
            "record_type": "c27_atomic_prompt",
            "owner": {"family": "core", "jurisdiction": "EU", "role": "shared_consultation_guidance"},
            "capability": capability,
            "implementation_scope": "model_guidance_only" if capability == "model_led" else capability,
            "c5d_predicate_status": "not_a_C5d_predicate",
            "legal_violation_claim_allowed": False,
            "evidence_preconditions": [ref],
            "family": family,
            "triggers_any": check["triggers_any"],
            "priority": check["priority"],
        })

    pattern_ids: set[str] = set()
    for pattern in catalog["patterns"]:
        pattern_id = pattern["attack_angle_id"]
        if pattern_id in pattern_ids or not pattern_id.startswith("core:attack:"):
            raise InventoryError(f"core_attack_angle_id_or_namespace_invalid:{pattern_id}")
        pattern_ids.add(pattern_id)
        missing_sources = sorted(set(pattern["source_refs"]) - set(pack_sources))
        if missing_sources:
            raise InventoryError(f"core_attack_pattern_orphan_source:{pattern_id}:{','.join(missing_sources)}")
        supported = pattern["signal_kind"] in SUPPORTED_SIGNAL_KINDS
        records.append({
            "record_id": pattern_id,
            "record_type": "core_c5d_pattern",
            "owner": {"family": "core", "jurisdiction": "EU", "role": "common_eu"},
            "capability": "deterministic" if supported else "not_implemented",
            "implementation_scope": "deterministic_synthetic_predicate" if supported else "signal_handler_missing",
            "execution_boundary": "synthetic_only",
            "signal_kind": pattern["signal_kind"],
            "evidence_preconditions": pattern["evidence_needs"],
            "source_refs": pattern["source_refs"],
            "false_positive_risks": pattern["false_positive_risks"],
            "legal_violation_status": "not_determined",
            "review_required": True,
        })

    topic_ids: set[str] = set()
    for topic in topic_catalog["topics"]:
        topic_id = topic["topic_id"]
        if topic_id in topic_ids:
            raise InventoryError(f"duplicate_priority_topic:{topic_id}")
        topic_ids.add(topic_id)
        if not set(topic["c27_families"]) <= c27_family_ids:
            raise InventoryError(f"priority_topic_unknown_c27_family:{topic_id}")
        for coverage_ref in topic["coverage"].split(";"):
            if coverage_ref.startswith("core:attack:") and coverage_ref not in pattern_ids:
                raise InventoryError(f"priority_topic_attack_reference_missing:{topic_id}:{coverage_ref}")
        records.append({
            "record_id": "topic:" + topic_id,
            "record_type": "priority_topic_review_path",
            "owner": {"family": "core", "jurisdiction": "EU", "role": "cross_owner_review_path"},
            "capability": "model_led",
            "implementation_scope": "source_qualified_review_metadata_not_legal_rule",
            "c27_families": topic["c27_families"],
            "attack_angle_coverage": topic["coverage"],
            "source_refs": [item["source_ref"] for item in topic["sources"]],
            "evidence_preconditions": topic["records_to_seek"],
            "counterarguments_and_exceptions": topic["counterarguments_and_exceptions"],
            "legal_violation_status": "not_determined",
            "remedy_competence_and_limits": topic["remedy_competence_and_limits"],
        })

    module_outputs = []
    module_files: list[Path] = [registry_path, catalog_path, stratagem_path,
                                compatibility_root() / "core-source-pack-manifest-0.6.1.json"]
    for module_root in MODULES:
        manifest_path = module_root / "references/module-manifest.json"
        export_path = module_root / "references/module-export.json"
        sidecar_path = module_root / "references/c12-rule-extension.json"
        manifest, export, sidecar = read_json(manifest_path), read_json(export_path), read_json(sidecar_path)
        try:
            conformance = validate_paths(manifest_path, export_path)
        except (ConformanceError, ContractError) as error:
            raise InventoryError(f"module_pair_nonconformant:{manifest.get('module_id')}:{error}") from error
        validate_obj("c12-rule-extension", sidecar)
        module_sources, module_authorities, module_routes, module_attacks = validate_module_references(export, sidecar)
        for attack_id, attack in module_attacks.items():
            capability = "not_implemented" if attack.get("support_status") == "unsupported_automation" else "model_led"
            records.append({
                "record_id": attack_id,
                "record_type": "country_module_review_hypothesis",
                "owner": {"module_id": export["module_id"], "family": export["module_family"],
                          "jurisdiction": export["jurisdiction"], "role": "module_owned"},
                "capability": capability,
                "implementation_scope": "review_candidate_only",
                "support_status": attack.get("support_status", "candidate"),
                "issue_type": attack["issue_type"],
                "evidence_preconditions": attack["evidence_needs"],
                "prerequisite_element_ids": attack["prerequisite_element_ids"],
                "required_completeness_ids": attack["required_completeness_ids"],
                "source_refs": attack["source_refs"],
                "legal_violation_status": "not_determined",
            })

        sidecar_rule_ids: set[str] = set()
        for rule in sidecar["rules"]:
            rule_id = rule["rule_id"]
            sidecar_rule_ids.add(rule_id)
            cited_sources = {item["source_id"] for item in rule.get("source_citations", [])}
            records.append({
                "record_id": rule_id,
                "record_type": "country_owned_typed_predicate" if rule.get("attack_angle_id") else "country_owned_typed_review_rule",
                "owner": {"module_id": export["module_id"], "family": export["module_family"],
                          "jurisdiction": export["jurisdiction"], "role": "module_owned"},
                "capability": "synthetic_only",
                "implementation_scope": "deterministic_typed_predicate_in_synthetic_lane",
                "attack_angle_id": rule.get("attack_angle_id"),
                "conditions": rule["conditions"],
                "exception_questions": rule["exception_questions"],
                "source_refs": sorted(cited_sources),
                "limitations": rule["limitations"],
            })

        module_outputs.append({
            "module_id": export["module_id"], "family": export["module_family"],
            "jurisdiction": export["jurisdiction"], "pair_status": conformance["status"],
            "attack_angle_count": len(export["attack_angle_records"]),
            "sidecar_rule_count": len(sidecar["rules"]),
        })
        module_files.extend([manifest_path, export_path, sidecar_path])

    stratagem_ids: set[str] = set()
    for item in stratagems["patterns"]:
        stratagem_id = item["stratagem_id"]
        if stratagem_id in stratagem_ids or not stratagem_id.startswith("adapted:"):
            raise InventoryError(f"adapted_stratagem_namespace_or_duplicate:{stratagem_id}")
        stratagem_ids.add(stratagem_id)
        records.append({
            "record_id": stratagem_id,
            "record_type": "adapted_strategy_heuristic",
            "owner": {"family": "core", "jurisdiction": "EU", "role": "strategy_catalog"},
            "capability": "synthetic_only",
            "implementation_scope": "strategic_candidate_generation_not_legal_screening",
            "not_a_legal_attack_angle": True,
            "evidence_preconditions": item["constraints"],
            "tags": item["tags"],
        })

    input_paths = [registry_path, catalog_path, stratagem_path, topic_path,
                   compatibility_root() / "core-source-pack-manifest-0.6.1.json", *module_files[4:]]
    source_files = [source_record(path) for path in sorted(set(input_paths))]
    summary: dict[str, int] = {}
    for item in records:
        summary[item["capability"]] = summary.get(item["capability"], 0) + 1
    inventory = {
        "schema_version": "0.1.0",
        "inventory_scope": "declared screening inventory; does not assert consultation execution",
        "counts": {
            "c27_atomic_checks": len(registry["checks"]),
            "core_c5d_patterns": len(catalog["patterns"]),
            "country_attack_angle_records": sum(item["attack_angle_count"] for item in module_outputs),
            "country_typed_sidecar_rules": sum(item["sidecar_rule_count"] for item in module_outputs),
            "adapted_strategy_heuristics": len(stratagems["patterns"]),
            "priority_topic_review_paths": len(topic_catalog["topics"]),
            "coverage_records": len(records),
        },
        "capability_counts": dict(sorted(summary.items())),
        "modules": module_outputs,
        "source_files": source_files,
        "records": records,
        "assurance": {
            "model_led_checks_are_not_execution_receipts": True,
            "c27_model_guidance_is_not_a_c5d_predicate": True,
            "country_attack_records_are_review_hypotheses": True,
            "adapted_strategies_are_not_legal_attack_angles": True,
            "c5d_legal_violation_status": "not_determined",
            "host_release_enforcement": "not_implemented",
        },
    }
    validate_inventory(inventory)
    return inventory


def markdown(inventory: dict) -> str:
    lines = [
        "# Generated screening coverage inventory",
        "",
        "This is an inventory of declared prompts, hypotheses and synthetic predicates. It does not say that any were executed in a consultation.",
        "",
        "## Counts",
        "",
        "| Inventory | Count |",
        "| --- | ---: |",
    ]
    for key, value in inventory["counts"].items():
        lines.append(f"| {key.replace('_', ' ')} | {value} |")
    lines.extend(["", "## Capability counts", "", "| Capability | Records |", "| --- | ---: |"])
    for key, value in inventory["capability_counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Country module coverage", "", "| Module | Owner family | Jurisdiction | Attack hypotheses | Typed sidecar rules | Conformance |", "| --- | --- | --- | ---: | ---: | --- |"])
    for module in inventory["modules"]:
        lines.append(f"| {module['module_id']} | {module['family']} | {module['jurisdiction']} | {module['attack_angle_count']} | {module['sidecar_rule_count']} | {module['pair_status']} |")
    lines.extend(["", "## Interpretation limits", "", "- C27 model-guidance prompts are not C5d predicates or execution receipts.", "- Core C5d patterns execute only within the synthetic lane and leave legal violation status undetermined.", "- Country module records are review hypotheses whose owner, jurisdiction and source references remain module-specific.", "- Priority topic records are review pathways. Their source lists still require issue-specific currentness and owner checks.", "- Adapted-stratagem rows are strategic heuristics, not legal attack angles.", "- Host release enforcement is not implemented.", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)
    try:
        inventory = load_inputs()
        encoded = json.dumps(inventory, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        rendered = markdown(inventory)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(encoded, encoding="utf-8")
        if args.markdown_output:
            args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_output.write_text(rendered, encoding="utf-8")
        if not args.json_output and not args.markdown_output:
            print(encoded, end="")
        else:
            print(json.dumps({"status": "generated", "counts": inventory["counts"],
                              "capability_counts": inventory["capability_counts"]}, sort_keys=True))
        return 0
    except (ContractError, InventoryError, ConformanceError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
