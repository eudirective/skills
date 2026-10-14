#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

PACK_VERSION = "0.1.0"
BASELINE_DATE = "2026-10-03"
PACK_NAME = "eudirective-core-source-pack"

TYPE_MAP = {
    "32004L0038": ("directive_consolidated", "binding_secondary_law"),
    "32009R0810": ("regulation_consolidated", "binding_secondary_law"),
    "32016L0680": ("directive_consolidated", "binding_secondary_law"),
    "32016R0399": ("regulation_consolidated", "binding_secondary_law"),
    "32016R0679": ("regulation_consolidated", "binding_secondary_law"),
    "32018R1806": ("regulation_consolidated", "binding_secondary_law"),
    "12012P": ("charter", "primary_law"),
    "52014SC0284": ("commission_staff_working_document", "non_binding_official_material"),
    "C:2023:1392": ("commission_notice", "non_binding_official_guidance"),
    "32013H0461": ("commission_recommendation", "non_binding_soft_law"),
}

TITLE_OVERRIDES = {
    "32004L0038": "Directive 2004/38/EC on free movement and residence",
    "32009R0810": "Regulation (EC) No 810/2009 establishing a Community Code on Visas (Visa Code)",
    "32016L0680": "Directive (EU) 2016/680 on law-enforcement data protection",
    "32016R0399": "Regulation (EU) 2016/399 (Schengen Borders Code)",
    "32016R0679": "Regulation (EU) 2016/679 (General Data Protection Regulation)",
    "32018R1806": "Regulation (EU) 2018/1806 on visa requirements and exemptions",
    "12012P": "Charter of Fundamental Rights of the European Union",
    "52014SC0284": "Commission staff working document SWD(2014) 284",
    "C:2023:1392": "Commission Notice C/2023/1392 — Guidance on the right of free movement of EU citizens and their families",
    "32013H0461": "Commission Recommendation 2013/461/EU on the principles governing SOLVIT",
    "visa-code-handbook-i-2024": "European Commission Visa Code Handbook I (2024)",
}

HANDBOOK_URL = "https://home-affairs.ec.europa.eu/document/download/1d79f44d-49ba-4847-951e-129f924b1051_en"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def celex_from_record(rec: dict) -> str | None:
    if rec.get("exact_celex"):
        return rec["exact_celex"]
    rid = rec.get("id", "")
    if rid.startswith("eu-live:"):
        return rid.split(":", 1)[1]
    return None


def logical_key(rec: dict) -> str:
    celex = celex_from_record(rec)
    if celex:
        return celex
    if rec.get("id") == "eu-guidance:visa-code-handbook-i":
        return "visa-code-handbook-i-2024"
    raise ValueError(f"cannot derive logical key for {rec.get('path')}")


def canonical_url(key: str, rec: dict) -> str:
    if key == "visa-code-handbook-i-2024":
        return HANDBOOK_URL
    return f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{key}"


def source_type_and_status(key: str) -> tuple[str, str]:
    if key.startswith("6") and "CJ" in key:
        return "cjeu_judgment", "binding_judicial_interpretation"
    if key == "visa-code-handbook-i-2024":
        return "commission_handbook", "non_binding_official_guidance"
    return TYPE_MAP.get(key, ("eu_official_material", "official_material"))


def display_title(key: str, records: list[dict]) -> str:
    if key in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[key]
    hint = records[0].get("title_hint") or key
    hint = " ".join(str(hint).replace("**", "").split())
    return hint[:1000]


def output_relpath(key: str, rec: dict) -> str:
    src_name = Path(rec["path"]).name
    if key.startswith("6") and "CJ" in key:
        return f"sources/case_law/{src_name}"
    return f"sources/eu/{src_name}"


def selected_records(update_manifest: dict) -> list[dict]:
    return [
        rec for rec in update_manifest.get("documents", [])
        if rec.get("source_family") in {"eu_legal_material", "commission_home_affairs"}
    ]


def build(source_root: Path, output_dir: Path) -> dict:
    update_path = source_root / "update_manifest.json"
    manifest_in = json.loads(update_path.read_text(encoding="utf-8"))
    records = selected_records(manifest_in)
    if not records:
        raise ValueError("no EU/common source records found")

    by_key: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_key[logical_key(rec)].append(rec)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    sources = []
    representations = 0
    for key in sorted(by_key):
        recs = sorted(by_key[key], key=lambda r: (r.get("language", ""), r["path"]))
        source_type, legal_status = source_type_and_status(key)
        reps = []
        for rec in recs:
            src = source_root / "legal_pack" / rec["path"]
            if not src.exists():
                raise FileNotFoundError(src)
            actual_hash = sha256(src)
            expected_hash = rec.get("baseline_sha256")
            if expected_hash and actual_hash != expected_hash:
                raise ValueError(f"baseline hash mismatch for {rec['path']}")
            rel = output_relpath(key, rec)
            dest = output_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            reps.append({
                "language": rec.get("language", "und"),
                "relative_path": rel,
                "sha256": actual_hash,
                "bytes": dest.stat().st_size,
                "source_policy": rec.get("source_policy"),
                "update_intent": rec.get("update_intent"),
                "original_combined_pack_path": f"legal_pack/{rec['path']}",
            })
            representations += 1

        authority = "Court of Justice of the European Union" if source_type == "cjeu_judgment" else (
            "European Commission" if source_type in {"commission_handbook", "commission_staff_working_document", "commission_notice", "commission_recommendation"} else "European Union"
        )
        source_id = f"eu:{key.lower().replace(':','-')}"
        sources.append({
            "source_id": source_id,
            "identity": key,
            "title": display_title(key, recs),
            "canonical_owner_family": "core",
            "authority_level": "eu",
            "issuing_authority": authority,
            "jurisdiction": "EU",
            "source_type": source_type,
            "legal_status": legal_status,
            "canonical_url": canonical_url(key, recs[0]),
            "baseline_date": BASELINE_DATE,
            "freshness_state": "baseline_verified_not_live_rechecked",
            "representations": reps,
        })

    manifest = {
        "manifest_version": "0.1.0",
        "pack_name": PACK_NAME,
        "pack_version": PACK_VERSION,
        "baseline_date": BASELINE_DATE,
        "source_pool": {
            "pack_name": manifest_in.get("pack_name"),
            "pack_version": manifest_in.get("pack_version"),
            "baseline_date": manifest_in.get("baseline_date"),
        },
        "ownership_rule": "EU institutions/CJEU/common EU material belongs to core regardless of legacy folder or country names",
        "freshness_claim": "baseline bytes verified against the supplied combined pack; live-source freshness is not asserted",
        "logical_source_count": len(sources),
        "representation_count": representations,
        "sources": sources,
    }
    (output_dir / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = []
    for p in sorted(output_dir.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            lines.append(f"{sha256(p)}  {p.relative_to(output_dir).as_posix()}")
    (output_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    metadata = {
        "pack_name": PACK_NAME,
        "pack_version": PACK_VERSION,
        "baseline_date": BASELINE_DATE,
        "logical_source_count": len(sources),
        "representation_count": representations,
        "status": "core/common baseline extracted deterministically from supplied combined Sweden/EU pack",
        "live_freshness_verified": False,
    }
    (output_dir / "PACK_METADATA.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return manifest


def validate(pack_dir: Path) -> dict:
    manifest = json.loads((pack_dir / "source_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("pack_name") != PACK_NAME:
        raise ValueError("wrong pack_name")
    if manifest.get("pack_version") != PACK_VERSION:
        raise ValueError("wrong pack_version")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources missing")
    seen_sources = set()
    rep_count = 0
    languages_for_solvit = set()
    for src in sources:
        sid = src.get("source_id")
        if not sid or sid in seen_sources:
            raise ValueError(f"duplicate/missing source_id:{sid}")
        seen_sources.add(sid)
        if src.get("canonical_owner_family") != "core" or src.get("authority_level") != "eu" or src.get("jurisdiction") != "EU":
            raise ValueError(f"ownership_error:{sid}")
        if src.get("freshness_state") != "baseline_verified_not_live_rechecked":
            raise ValueError(f"freshness_claim_error:{sid}")
        reps = src.get("representations")
        if not isinstance(reps, list) or not reps:
            raise ValueError(f"representations_missing:{sid}")
        for rep in reps:
            rel = rep.get("relative_path", "")
            if not rel.startswith("sources/") or "swedish_laws" in rel.lower():
                raise ValueError(f"bad_output_path:{sid}:{rel}")
            p = pack_dir / rel
            if not p.is_file():
                raise ValueError(f"missing_file:{rel}")
            if sha256(p) != rep.get("sha256"):
                raise ValueError(f"hash_mismatch:{rel}")
            rep_count += 1
            if src.get("identity") == "32013H0461":
                languages_for_solvit.add(rep.get("language"))
    if len(sources) != manifest.get("logical_source_count"):
        raise ValueError("logical_source_count_mismatch")
    if rep_count != manifest.get("representation_count"):
        raise ValueError("representation_count_mismatch")
    if languages_for_solvit != {"EN", "SV"}:
        raise ValueError(f"solvit_language_grouping_error:{sorted(languages_for_solvit)}")
    return {
        "status": "valid",
        "pack_name": PACK_NAME,
        "pack_version": PACK_VERSION,
        "logical_source_count": len(sources),
        "representation_count": rep_count,
        "manifest_sha256": sha256(pack_dir / "source_manifest.json"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build or validate the EU/common sibling source pack")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("source_root")
    b.add_argument("output_dir")
    v = sub.add_parser("validate")
    v.add_argument("pack_dir")
    args = ap.parse_args()
    try:
        if args.cmd == "build":
            out = build(Path(args.source_root), Path(args.output_dir))
            result = {"status":"built","logical_source_count":out["logical_source_count"],"representation_count":out["representation_count"]}
        else:
            result = validate(Path(args.pack_dir))
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status":"invalid","error":str(exc)}, sort_keys=True), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
