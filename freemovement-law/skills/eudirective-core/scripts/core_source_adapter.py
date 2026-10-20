#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import sys

from contract_validate import ContractError, canonical_bytes, load_json, validate_obj

CONTRACT_VERSION = "0.2.0"
MODULE_ID = "eudirective-core-source"
MODULE_VERSION = "0.18.0"
JURISDICTION = "EU"


class AdapterError(Exception):
    pass


def logical_digest(representations):
    payload = [
        {"language": r["language"], "sha256": r["sha256"]}
        for r in sorted(representations, key=lambda x: (x["language"], x["relative_path"]))
    ]
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def map_freshness(states):
    states = set(states)
    if states and states <= {"current", "fixed_verified"}:
        return "current"
    if states and states <= {"current", "fixed_verified", "baseline_verified_not_live_rechecked"} and "baseline_verified_not_live_rechecked" in states:
        return "baseline_verified_not_live_rechecked"
    if "stale" in states:
        return "stale"
    return "unknown"


def verified_bundled_reps(src):
    return [r for r in src.get("representations", []) if r.get("kind") == "bundled_text" and r.get("authenticity_state") == "verified_official"]

def verified_note_reps(src):
    return [r for r in src.get("representations", []) if r.get("kind") == "verified_source_note" and r.get("authenticity_state") == "verified_identity_version"]

def usable_reps(src):
    return verified_bundled_reps(src) + verified_note_reps(src)


def select_export_reps(src):
    bundled = verified_bundled_reps(src)
    if bundled:
        return bundled, "authoritative_bundled_text", "verified_official"
    notes = verified_note_reps(src)
    if notes:
        return notes, "verified_source_note", "verified_identity_version"
    refs = [r for r in src.get("representations", []) if r.get("kind") == "curated_reference_note"]
    if refs:
        return refs, "curated_reference_note", "reference_only"
    candidates = [r for r in src.get("representations", []) if r.get("kind") == "candidate_text"]
    if candidates:
        return candidates, "unverified_candidate", "unverified_candidate"
    raise AdapterError(f"source has no exportable representation: {src.get('source_id')}")


def build_objects(pack_manifest):
    validate_obj("core-source-pack", pack_manifest)
    freshness = map_freshness(src["freshness_state"] for src in pack_manifest["sources"])
    blocked_sources = [src for src in pack_manifest.get("sources", []) if not usable_reps(src)]
    known_gaps = []
    if pack_manifest.get("completion_status") not in {"c1_source_representation_complete", "c1_source_text_complete"} or blocked_sources:
        known_gaps.append("c1_source_representation_pending")
    if freshness == "baseline_verified_not_live_rechecked":
        known_gaps.append("live_source_freshness_not_rechecked")
    elif freshness == "stale":
        known_gaps.append("one_or_more_sources_stale")
    elif freshness == "unknown":
        known_gaps.append("source_freshness_unknown")

    source_records = []
    for src in pack_manifest["sources"]:
        reps, content_kind, authenticity_state = select_export_reps(src)
        languages = sorted({r["language"] for r in reps})
        usable = content_kind in {"authoritative_bundled_text", "verified_source_note"}
        if usable:
            record_status = "current" if src["freshness_state"] == "fixed_verified" else src["freshness_state"]
            scope = "EU/common source substrate" if content_kind == "authoritative_bundled_text" else "EU/common source substrate; identity/version-verified normalized representation; exact wording and pinpoints require official source"
        else:
            record_status = "unknown"
            scope = "EU/common source substrate; unverified metadata/reference only"
        source_records.append({
            "source_id": src["source_id"],
            "title": src["title"],
            "authority": src["issuing_authority"],
            "source_type": src["source_type"],
            "scope": scope,
            "language": languages[0] if len(languages) == 1 else "MULTI",
            "verified_at": f"{src.get('verification_date', src.get('baseline_date'))[:10]}T00:00:00Z",
            "effective_from": None,
            "effective_to": None,
            "locator": src["canonical_url"],
            "content_sha256": reps[0]["sha256"] if len(reps) == 1 else logical_digest(reps),
            "status": record_status,
            "content_kind": content_kind,
            "authenticity_state": authenticity_state,
        })

    manifest = {
        "contract_version": CONTRACT_VERSION,
        "module_family": "core_source",
        "module_id": MODULE_ID,
        "id_namespace": "eu",
        "jurisdiction": JURISDICTION,
        "module_version": MODULE_VERSION,
        "pack_version": pack_manifest["pack_version"],
        "freshness_state": freshness,
        "known_gap_ids": [f"eu:gap:{gap}" for gap in known_gaps] + [f"eu:gap:source_representation:{src['source_id'].replace(':', '_')}" for src in blocked_sources],
        "supported_domains": sorted({src["source_type"] for src in pack_manifest["sources"]}),
        "supported_roles": ["common_eu"],
        "compatibility": {"conformance_profile_version":"0.2.0","controller_protocol_versions":["0.3.0"],"element_model_versions":["0.2.0"]},
        "data_classification": "reusable_non_case",
        "dataset_versions": {
            "sources": pack_manifest["pack_version"],
            "rules": "none",
            "authorities": "none",
            "deadlines": "none",
            "routes": "none",
            "operations": "none",
            "attack_angles": "none",
        },
    }
    gap_records = []
    for gap in known_gaps:
        area = "source_completeness" if gap == "c1_source_representation_pending" else "source_freshness"
        gap_records.append({"gap_id": f"eu:gap:{gap}", "area": area, "scope": "sources", "impact": "blocking" if gap == "c1_source_representation_pending" else "degrading", "status": "known_gap", "detail": gap})
    for src in blocked_sources:
        gap_records.append({
            "gap_id": f"eu:gap:source_representation:{src['source_id'].replace(':', '_')}",
            "area": "source_completeness",
            "scope": "sources",
            "impact": "blocking",
            "status": "known_gap",
            "detail": f"{src['source_id']} lacks a verified usable source representation.",
        })
    export = {
        "contract_version": CONTRACT_VERSION,
        "module_family": "core_source",
        "module_id": MODULE_ID,
        "id_namespace": "eu",
        "jurisdiction": JURISDICTION,
        "module_version": MODULE_VERSION,
        "pack_version": pack_manifest["pack_version"],
        "source_records": source_records,
        "rule_records": [],
        "authority_records": [],
        "gap_records": gap_records,
        "operational_records": [],
        "deadline_records": [],
        "route_records": [],
        "attack_angle_records": [],
    }
    validate_obj("module-manifest", manifest)
    validate_obj("module-export", export)
    return manifest, export


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Adapt eudirective-core source-pack manifest into C3 contract 0.2.0 controller module files")
    ap.add_argument("pack_manifest")
    ap.add_argument("output_dir")
    args = ap.parse_args()
    try:
        pack = load_json(Path(args.pack_manifest))
        manifest, export = build_objects(pack)
        out = Path(args.output_dir)
        mp = out / "core-source-module-manifest.json"
        ep = out / "core-source-module-export.json"
        write_json(mp, manifest)
        write_json(ep, export)
        print(json.dumps({
            "status": "adapted",
            "manifest": str(mp),
            "export": str(ep),
            "freshness_state": manifest["freshness_state"],
            "source_count": len(export["source_records"]),
        }, sort_keys=True))
        return 0
    except (AdapterError, ContractError, OSError, json.JSONDecodeError) as e:
        print(json.dumps({"status": "rejected", "error": str(e)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
