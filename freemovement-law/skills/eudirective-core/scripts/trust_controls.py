#!/usr/bin/env python3
import argparse
import json
import os
from datetime import date, datetime
import re
from pathlib import Path
import tempfile

from contract_validate import ContractError, digest_obj, load_json, validate_obj

TRUST_PROFILE_VERSION = "0.1.0"
RISK_BASE = {
    "public": 0,
    "case_fact": 1,
    "quasi_identifier": 2,
    "direct_identifier": 5,
    "sensitive": 3,
}
RISK_TAGS = {
    "rare_nationality": 3,
    "exact_timestamp": 3,
    "unusual_family": 3,
    "unique_topology": 4,
    "precise_procedural_event": 2,
    "public_searchable_quote": 4,
    "repeated_pseudonym": 3,
}
TRANSFORM_RISK_REDUCTION = {
    "keep": 0,
    "redact": 100,
    "presence_only": 4,
    "date_to_month": 3,
    "date_to_year": 5,
    "country_only": 3,
    "count_only": 4,
}

DIRECT_IDENTIFIER_SAFE_TRANSFORMS = {
    "drop",
    "redact",
    "presence_only",
    "country_only",
}

ISO_YEAR_RE = re.compile(r"^\d{4}$")
ISO_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T.+$")

class TrustControlError(Exception):
    pass

def atomic_write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def select_profile(policy, purpose, destination_kind, action):
    matches = [p for p in policy["purpose_profiles"] if p["purpose"] == purpose and p["destination_kind"] == destination_kind and p["action"] == action]
    if len(matches) != 1:
        raise TrustControlError(f"purpose_profile_match_count:{len(matches)}")
    return matches[0]

def _iso_temporal_precision(value):
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    if ISO_YEAR_RE.fullmatch(value):
        return "year"
    if ISO_MONTH_RE.fullmatch(value):
        try:
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            return None
        return "month"
    if ISO_DATE_RE.fullmatch(value):
        try:
            date.fromisoformat(value)
        except ValueError:
            return None
        return "day"
    if ISO_DATETIME_RE.fullmatch(value):
        try:
            datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
        except ValueError:
            return None
        return "datetime"
    return None

def validate_transform_compatibility(field, action, allow_direct_identifiers):
    classification = field["classification"]
    field_id = field["field_id"]
    value = field["value"]

    if classification == "direct_identifier" and not allow_direct_identifiers:
        if action not in DIRECT_IDENTIFIER_SAFE_TRANSFORMS:
            raise TrustControlError(f"direct_identifier_transform_forbidden:{field_id}:{action}")

    if action == "date_to_month":
        if _iso_temporal_precision(value) not in {"month", "day", "datetime"}:
            raise TrustControlError(f"date_to_month_requires_iso_temporal:{field_id}")
    elif action == "date_to_year":
        if _iso_temporal_precision(value) not in {"year", "month", "day", "datetime"}:
            raise TrustControlError(f"date_to_year_requires_iso_temporal:{field_id}")
    elif action == "country_only":
        if not isinstance(value, dict) or not isinstance(value.get("country"), str) or not value["country"].strip():
            raise TrustControlError(f"country_only_requires_country_object:{field_id}")
    elif action == "count_only":
        if not isinstance(value, (list, dict, str)):
            raise TrustControlError(f"count_only_requires_sized_value:{field_id}")

def transform_value(action, value):
    if action == "keep":
        return value
    if action == "redact":
        return "[REDACTED]"
    if action == "presence_only":
        return value is not None
    if action == "date_to_month":
        return value[:7]
    if action == "date_to_year":
        return value[:4]
    if action == "country_only":
        return value["country"].strip()
    if action == "count_only":
        return len(value)
    if action == "drop":
        return None
    raise TrustControlError(f"unknown_transform:{action}")

def build_views(data, policy, outbound_id, purpose, destination_kind, destination, action):
    validate_obj("protected-data", data)
    validate_obj("privacy-policy", policy)
    if data["privacy_classification"] == "private":
        raise TrustControlError("private_data_host_enforcement_not_verified")
    profile = select_profile(policy, purpose, destination_kind, action)
    field_ids=[f["field_id"] for f in data["fields"]]
    if len(field_ids) != len(set(field_ids)):
        raise TrustControlError("duplicate_field_id")
    explicit = {x["field_id"]: x["transform"] for x in profile["field_rules"]}
    if len(explicit) != len(profile["field_rules"]):
        raise TrustControlError("duplicate_field_rule")
    defaults = {x["classification"]: x["transform"] for x in profile["classification_defaults"]}
    if len(defaults) != len(profile["classification_defaults"]):
        raise TrustControlError("duplicate_classification_default")

    protected = {
        "trust_profile_version": TRUST_PROFILE_VERSION,
        "case_id": data["case_id"],
        "bound_case_revision": data["bound_case_revision"],
        "privacy_classification": data["privacy_classification"],
        "fields": data["fields"],
    }
    analysis = {
        "trust_profile_version": TRUST_PROFILE_VERSION,
        "case_id": data["case_id"],
        "bound_case_revision": data["bound_case_revision"],
        "fields": [
            {"field_id": f["field_id"], "value": f["value"], "classification": f["classification"]}
            for f in data["fields"] if f["analysis_required"]
        ],
    }

    outbound_fields = []
    dropped = kept = transformed = 0
    score = 0
    risk_flags = set()
    for field in data["fields"]:
        t = explicit.get(field["field_id"], defaults.get(field["classification"], profile["default_transform"]))
        validate_transform_compatibility(field, t, profile["allow_direct_identifiers"])
        if t == "drop":
            dropped += 1
            continue
        out_value = transform_value(t, field["value"])
        outbound_fields.append({"field_id": field["field_id"], "classification": field["classification"], "transform": t, "value": out_value})
        if t == "keep":
            kept += 1
        else:
            transformed += 1
        field_score = RISK_BASE[field["classification"]] + sum(RISK_TAGS[x] for x in field["risk_tags"])
        field_score = max(0, field_score - TRANSFORM_RISK_REDUCTION[t])
        score += field_score
        if field_score:
            risk_flags.add(f"retained:{field['field_id']}")
        for tag in field["risk_tags"]:
            if field_score:
                risk_flags.add(tag)
    eligible = score <= policy["max_linkability_score"]
    limitations = [
        "Deterministic minimisation does not prove anonymity or defeat external auxiliary information.",
        "Private-data processing remains disabled until host/runtime enforcement is independently demonstrated."
    ]
    if not eligible:
        limitations.append("Residual linkability score exceeds the configured outbound threshold.")
    outbound = {
        "trust_profile_version": TRUST_PROFILE_VERSION,
        "outbound_id": outbound_id,
        "case_id": data["case_id"],
        "bound_case_revision": data["bound_case_revision"],
        "policy_id": policy["policy_id"],
        "policy_sha256": digest_obj(policy),
        "purpose": purpose,
        "destination_kind": destination_kind,
        "destination": destination,
        "action": action,
        "max_attempts": profile["max_attempts"],
        "fields": outbound_fields,
        "minimisation_summary": {"input_fields": len(data["fields"]), "kept_fields": kept, "transformed_fields": transformed, "dropped_fields": dropped},
        "linkability_score": score,
        "residual_risk_flags": sorted(risk_flags),
        "eligible": eligible,
        "limitations": limitations,
    }
    validate_obj("outbound-view", outbound)
    return protected, analysis, outbound

def cmd_build_views(args):
    data = load_json(Path(args.input))
    policy = load_json(Path(args.policy))
    protected, analysis, outbound = build_views(data, policy, args.outbound_id, args.purpose, args.destination_kind, args.destination, args.action)
    out = Path(args.output_dir)
    atomic_write_json(out / "protected-view.json", protected)
    atomic_write_json(out / "analysis-view.json", analysis)
    atomic_write_json(out / "outbound-view.json", outbound)
    print(json.dumps({
        "status": "built",
        "trust_profile_version": TRUST_PROFILE_VERSION,
        "protected_sha256": digest_obj(protected),
        "analysis_sha256": digest_obj(analysis),
        "outbound_sha256": digest_obj(outbound),
        "eligible": outbound["eligible"],
        "linkability_score": outbound["linkability_score"],
    }, sort_keys=True))

def main():
    ap = argparse.ArgumentParser(description="Deterministic privacy/minimisation controls for eudirective-core")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build-views")
    p.add_argument("--input", required=True)
    p.add_argument("--policy", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--outbound-id", required=True)
    p.add_argument("--purpose", required=True)
    p.add_argument("--destination-kind", choices=["local_file", "user_visible", "feedback_service", "external_recipient", "publication"], required=True)
    p.add_argument("--destination", required=True)
    p.add_argument("--action", choices=["analyze", "render", "feedback", "send", "publish"], required=True)
    p.set_defaults(fn=cmd_build_views)
    args = ap.parse_args()
    try:
        args.fn(args)
        return 0
    except (TrustControlError, ContractError, OSError, json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"status": "rejected", "error": str(e)}, sort_keys=True), file=os.sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
