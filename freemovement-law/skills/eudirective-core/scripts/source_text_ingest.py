#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PDF_TYPES = {"cjeu_judgment"}
HTML_TYPES = {
    "commission_operational_guidance_page",
    "ombudsman_operational_guidance_page",
}
USER_AGENT = "eudirective-core-source-ingest/0.2 (+official-source-maintenance)"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OFFICIAL_HOSTS = {
    "cjeu_judgment": {"eur-lex.europa.eu"},
    "commission_operational_guidance_page": {"commission.europa.eu"},
    "ombudsman_operational_guidance_page": {"www.ombudsman.europa.eu", "ombudsman.europa.eu"},
}
HTML_IDENTITY_MARKERS = {
    "commission_operational_guidance_page": ("report a breach of eu law", "european commission"),
    "ombudsman_operational_guidance_page": ("make a complaint", "european ombudsman"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_date(value: str) -> str:
    if not DATE_RE.fullmatch(value or ""):
        raise ValueError("--verified-date must be an explicit YYYY-MM-DD value")
    return value


def source_download_url(source: dict) -> str:
    identity = source["identity"]
    if source["source_type"] in PDF_TYPES:
        return f"https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:{identity}"
    return source["canonical_url"]


def expected_extension(source: dict) -> str:
    if source["source_type"] in PDF_TYPES:
        return ".pdf"
    if source["source_type"] in HTML_TYPES:
        return ".html"
    raise ValueError(f"unsupported source type for ingestion: {source['source_type']}")


def target_relative_path(source: dict) -> str:
    ext = expected_extension(source)
    if source["source_type"] in PDF_TYPES:
        return f"sources/case_law/CELEX_{source['identity']}_EN_JUDGMENT{ext}"
    safe = source["source_id"].replace(":", "_").replace("/", "_")
    return f"sources/eu/{safe}_official{ext}"


def candidate_relative_path(source: dict) -> str:
    ext = expected_extension(source)
    safe = source["source_id"].replace(":", "_").replace("/", "_")
    return f"sources/candidates/{safe}_unverified{ext}"


def allowed_hosts(source: dict) -> set[str]:
    try:
        return OFFICIAL_HOSTS[source["source_type"]]
    except KeyError as exc:
        raise ValueError(f"no official-host policy for {source['source_type']}") from exc


def validate_official_url(source: dict, url: str, *, initial: bool = False) -> None:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() != "https":
        raise ValueError(f"official source URL must use HTTPS: {url}")
    if host not in allowed_hosts(source):
        raise ValueError(f"untrusted source host for {source['source_id']}: {host}")
    if initial and url != source_download_url(source):
        raise ValueError(f"download URL drift for {source['source_id']}")
    if initial and source["source_type"] in PDF_TYPES:
        uri = urllib.parse.parse_qs(parsed.query).get("uri", [])
        if uri != [f"CELEX:{source['identity']}"]:
            raise ValueError(f"EUR-Lex request is not bound to expected CELEX identity: {source['identity']}")
    if initial and source["source_type"] in HTML_TYPES and url != source["canonical_url"]:
        raise ValueError(f"operational-page request is not the canonical URL for {source['source_id']}")


class RestrictedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, source: dict):
        super().__init__()
        self.source = source

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        validate_official_url(self.source, newurl, initial=False)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_payload(source: dict, data: bytes, content_type: str | None = None) -> None:
    if len(data) < 1000:
        raise ValueError(f"payload too small for {source['source_id']}: {len(data)} bytes")
    if source["source_type"] in PDF_TYPES:
        if content_type and content_type not in {"application/pdf", "application/octet-stream"}:
            raise ValueError(f"unexpected PDF content type for {source['source_id']}: {content_type}")
        if not data.startswith(b"%PDF"):
            prefix = data[:200].decode("utf-8", errors="ignore").lower()
            raise ValueError(f"expected PDF for {source['source_id']}; received {content_type or 'unknown'}: {prefix!r}")
        if b"%%EOF" not in data[-4096:]:
            raise ValueError(f"PDF end marker missing for {source['source_id']}")
        return
    if source["source_type"] in HTML_TYPES:
        if content_type and content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"unexpected HTML content type for {source['source_id']}: {content_type}")
        head = data[:30000].decode("utf-8", errors="ignore").lower()
        if "<html" not in head and "<!doctype html" not in head:
            raise ValueError(f"expected HTML for {source['source_id']}; received {content_type or 'unknown'}")
        robot_markers = ("verify that you're not a robot", "captcha", "access denied")
        if any(marker in head for marker in robot_markers):
            raise ValueError(f"anti-bot/interstitial page received for {source['source_id']}")
        full = data.decode("utf-8", errors="ignore").lower()
        markers = HTML_IDENTITY_MARKERS[source["source_type"]]
        if not all(marker in full for marker in markers):
            raise ValueError(f"official HTML identity markers missing for {source['source_id']}")
        return
    raise ValueError(f"unsupported source type: {source['source_type']}")


def fetch_bytes(source: dict, timeout: int) -> tuple[bytes, str | None, dict]:
    url = source_download_url(source)
    validate_official_url(source, url, initial=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
    opener = urllib.request.build_opener(RestrictedRedirectHandler(source))
    with opener.open(req, timeout=timeout) as resp:
        data = resp.read()
        ctype = resp.headers.get_content_type() if resp.headers else None
        final_url = resp.geturl()
    validate_official_url(source, final_url, initial=False)
    validate_payload(source, data, ctype)
    return data, ctype, {
        "mode": "official_https_fetch",
        "request_url": url,
        "final_url": final_url,
    }


def candidate_names(source: dict) -> list[str]:
    ext = expected_extension(source)
    safe_source = source["source_id"].replace(":", "_").replace("/", "_")
    if source["source_type"] in PDF_TYPES:
        return [
            source["identity"] + ext,
            f"CELEX_{source['identity']}_EN_JUDGMENT{ext}",
            safe_source + ext,
        ]
    return [source["identity"] + ext, safe_source + ext]


def import_bytes(source: dict, import_dir: Path) -> tuple[bytes, str | None, dict]:
    for name in candidate_names(source):
        path = import_dir / name
        if path.is_file():
            data = path.read_bytes()
            ctype = mimetypes.guess_type(path.name)[0]
            validate_payload(source, data, ctype)
            return data, ctype, {"mode": "offline_import", "path": str(path)}
    raise FileNotFoundError(f"no import file found for {source['source_id']}; expected one of: {candidate_names(source)}")


def verified_text_representations(source: dict) -> list[dict]:
    return [r for r in source.get("representations", []) if r.get("kind") == "bundled_text" and r.get("authenticity_state") == "verified_official"]

def verified_note_representations(source: dict) -> list[dict]:
    return [r for r in source.get("representations", []) if r.get("kind") == "verified_source_note" and r.get("authenticity_state") == "verified_identity_version"]

def usable_representations(source: dict) -> list[dict]:
    return verified_text_representations(source) + verified_note_representations(source)

def blocking_sources(manifest: dict) -> list[dict]:
    return [s for s in manifest.get("sources", []) if not usable_representations(s)]


def recompute_text_state(source: dict) -> str:
    if verified_text_representations(source):
        state = "bundled_verified"
    elif verified_note_representations(source):
        state = "verified_source_note"
    elif any(r.get("kind") == "candidate_text" for r in source.get("representations", [])):
        state = "candidate_unverified"
    else:
        state = "reference_only"
    source["text_completeness_state"] = state
    return state


def remove_candidate_representations(pack: Path, source: dict) -> None:
    kept = []
    for rep in source.get("representations", []):
        if rep.get("kind") == "candidate_text":
            path = pack / rep.get("relative_path", "")
            if path.is_file():
                path.unlink()
        else:
            kept.append(rep)
    source["representations"] = kept


def update_ingestion_files(pack: Path, manifest: dict, operation_date: str) -> dict:
    blocked = blocking_sources(manifest)
    items = []
    for src in blocked:
        items.append({
            "source_id": src["source_id"],
            "identity": src["identity"],
            "title": src["title"],
            "canonical_url": src["canonical_url"],
            "download_url": source_download_url(src),
            "issuing_authority": src["issuing_authority"],
            "source_type": src["source_type"],
            "verification_date": src.get("verification_date"),
            "text_completeness_state": src.get("text_completeness_state", "reference_only"),
            "trusted_ingest_sha256": src.get("trusted_ingest_sha256"),
            "required_action": "obtain_verified_usable_source_representation",
            "status": "requires_verified_representation",
            "offline_import_policy": "stage_only_when_no_trusted_digest; promote_only_on_exact_trusted_sha256_match",
            "expected_extension": expected_extension(src),
            "expected_import_names": candidate_names(src),
            "existing_reference_paths": [
                r["relative_path"] for r in src.get("representations", [])
                if r.get("kind") == "curated_reference_note"
            ],
            "candidate_paths": [
                r["relative_path"] for r in src.get("representations", [])
                if r.get("kind") == "candidate_text"
            ],
        })
    ingestion = {
        "ingestion_manifest_version": "0.5.0",
        "pack_name": manifest["pack_name"],
        "pack_version": manifest["pack_version"],
        "generated_date": operation_date,
        "gate": "c1_source_representation_complete",
        "blocked_source_count": len(items),
        "required_reference_only_count": sum(1 for src in blocked if src.get("text_completeness_state") == "reference_only"),
        "status": "blocked" if items else "complete",
        "rule": "C1 requires a verified usable representation. Full bundled text or an identity/version-verified normalized source note qualifies; unverified candidates do not.",
        "sources": items,
    }
    write_json(pack / "SOURCE_TEXT_INGESTION.json", ingestion)

    meta_path = pack / "PACK_METADATA.json"
    meta = load_json(meta_path) if meta_path.exists() else {}
    meta.update({
        "pack_name": manifest["pack_name"],
        "pack_version": manifest["pack_version"],
        "logical_source_count": len(manifest.get("sources", [])),
        "representation_count": sum(len(s.get("representations", [])) for s in manifest.get("sources", [])),
        "completion_status": manifest.get("completion_status"),
        "offline_full_text_complete": all(any(r.get("kind")=="bundled_text" and r.get("authenticity_state")=="verified_official" for r in s.get("representations",[])) for s in manifest.get("sources",[])),
        "reference_only_source_count": sum(1 for s in blocked if s.get("text_completeness_state") == "reference_only"),
        "candidate_unverified_source_count": sum(1 for s in blocked if s.get("text_completeness_state") == "candidate_unverified"),
        "last_ingestion_operation_date": operation_date,
        "status": "C1 source-representation gate complete." if not items else f"C1 source-representation completion pending; {len(items)} source(s) still lack a verified usable representation.",
    })
    write_json(meta_path, meta)
    return ingestion


def regenerate_checksums(pack: Path) -> None:
    lines = []
    for path in sorted(pack.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_file(path)}  {path.relative_to(pack).as_posix()}")
    (pack / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def authoritative_representation(source: dict, rel: str, data: bytes, acquisition: dict, verified_date: str, method: str) -> dict:
    return {
        "kind": "bundled_text",
        "language": "EN",
        "relative_path": rel,
        "sha256": sha256_bytes(data),
        "bytes": len(data),
        "source_policy": "official-source-byte-snapshot",
        "update_intent": "fixed_identity_refresh" if source["source_type"] in PDF_TYPES else "live_currentness_refresh",
        "original_combined_pack_path": None,
        "authenticity_state": "verified_official",
        "verification_method": method,
        "acquisition_url": acquisition.get("request_url") or acquisition.get("path"),
        "final_url": acquisition.get("final_url"),
        "verified_at": verified_date,
    }


def ingest_verified(pack: Path, source: dict, data: bytes, acquisition: dict, verified_date: str, method: str) -> None:
    rel = target_relative_path(source)
    out = pack / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    remove_candidate_representations(pack, source)
    source["representations"] = [r for r in source.get("representations", []) if r.get("relative_path") != rel]
    source.setdefault("representations", []).append(authoritative_representation(source, rel, data, acquisition, verified_date, method))
    source["trusted_ingest_sha256"] = sha256_bytes(data)
    source["verification_date"] = verified_date
    source["text_completeness_state"] = "bundled_verified"
    if source["source_type"] in PDF_TYPES:
        source["freshness_state"] = "fixed_verified"
        source["verification_basis"] = f"official_judgment_pdf_{method}"
    else:
        source["freshness_state"] = "current"
        source["verification_basis"] = f"official_operational_page_{method}"


def stage_candidate(pack: Path, source: dict, data: bytes, acquisition: dict) -> None:
    rel = candidate_relative_path(source)
    out = pack / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    source["representations"] = [r for r in source.get("representations", []) if r.get("kind") != "candidate_text"]
    source.setdefault("representations", []).append({
        "kind": "candidate_text",
        "language": "EN",
        "relative_path": rel,
        "sha256": sha256_bytes(data),
        "bytes": len(data),
        "source_policy": "offline-unverified-candidate",
        "update_intent": "identity_verification_required",
        "original_combined_pack_path": None,
        "authenticity_state": "unverified_candidate",
        "verification_method": "not_applicable",
        "acquisition_url": acquisition.get("path"),
        "final_url": None,
        "verified_at": None,
    })
    source["text_completeness_state"] = "candidate_unverified"


def select_sources(manifest: dict, ids: list[str] | None) -> list[dict]:
    blocked = blocking_sources(manifest)
    if not ids:
        return blocked
    wanted = set(ids)
    selected = [s for s in blocked if s["source_id"] in wanted or s["identity"] in wanted]
    matched = {s["source_id"] for s in selected} | {s["identity"] for s in selected}
    missing = wanted - matched
    if missing:
        raise ValueError(f"requested blocked sources not found: {sorted(missing)}")
    return selected


def execute(pack: Path, mode: str, import_dir: Path | None, source_ids: list[str] | None, verified_date: str, timeout: int, continue_on_error: bool) -> dict:
    verified_date = require_date(verified_date)
    manifest_path = pack / "source_manifest.json"
    manifest = load_json(manifest_path)
    selected = select_sources(manifest, source_ids)
    results = []
    for source in selected:
        try:
            if mode == "fetch":
                data, ctype, acquisition = fetch_bytes(source, timeout)
                ingest_verified(pack, source, data, acquisition, verified_date, "official_https_fetch")
                result_status = "verified_ingested"
            elif mode == "import":
                if import_dir is None:
                    raise ValueError("--import-dir is required for import mode")
                data, ctype, acquisition = import_bytes(source, import_dir)
                digest = sha256_bytes(data)
                trusted = source.get("trusted_ingest_sha256")
                if trusted:
                    if digest != trusted:
                        raise ValueError(f"offline import digest mismatch for {source['source_id']}: expected {trusted}, got {digest}")
                    ingest_verified(pack, source, data, acquisition, verified_date, "pinned_sha256_match")
                    result_status = "verified_ingested"
                else:
                    stage_candidate(pack, source, data, acquisition)
                    result_status = "candidate_staged"
            else:
                raise ValueError(f"unsupported mode: {mode}")
            results.append({
                "source_id": source["source_id"],
                "status": result_status,
                "bytes": len(data),
                "sha256": sha256_bytes(data),
                "content_type": ctype,
                "acquisition": acquisition,
            })
        except Exception as exc:
            results.append({"source_id": source["source_id"], "status": "failed", "error": str(exc)})
            if not continue_on_error:
                break

    for source in manifest.get("sources", []):
        recompute_text_state(source)
    remaining = blocking_sources(manifest)
    manifest["representation_count"] = sum(len(s.get("representations", [])) for s in manifest.get("sources", []))
    manifest["completion_status"] = "c1_source_representation_complete" if not remaining else "c1_source_representation_pending"
    manifest["freshness_claim"] = (
        "Every C1-required logical source has a verified usable representation. Mutable operational pages still require periodic currentness refresh."
        if not remaining else
        "C1 remains incomplete while any logical source lacks either verified full text or an identity/version-verified normalized source note. Unverified candidates never satisfy the gate."
    )
    write_json(manifest_path, manifest)
    ingestion = update_ingestion_files(pack, manifest, verified_date)
    regenerate_checksums(pack)
    verified_count = sum(1 for r in results if r["status"] == "verified_ingested")
    staged_count = sum(1 for r in results if r["status"] == "candidate_staged")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    return {
        "status": "complete" if not remaining else "partial",
        "mode": mode,
        "attempted": len(selected),
        "verified_ingested": verified_count,
        "candidates_staged": staged_count,
        "failed": failed_count,
        "remaining_blockers": len(remaining),
        "results": results,
        "ingestion_manifest_status": ingestion["status"],
    }


def plan(pack: Path) -> dict:
    manifest = load_json(pack / "source_manifest.json")
    rows = []
    for src in blocking_sources(manifest):
        rows.append({
            "source_id": src["source_id"],
            "identity": src["identity"],
            "source_type": src["source_type"],
            "text_completeness_state": src.get("text_completeness_state", "reference_only"),
            "trusted_ingest_sha256": src.get("trusted_ingest_sha256"),
            "download_url": source_download_url(src),
            "target_relative_path": target_relative_path(src),
            "candidate_relative_path": candidate_relative_path(src),
            "expected_import_names": candidate_names(src),
            "offline_import_policy": "promote only on exact trusted_ingest_sha256 match; otherwise stage as unverified candidate",
        })
    return {"status": "blocked" if rows else "complete", "blocked_source_count": len(rows), "sources": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description="Maintain fuller source snapshots for the C1 core-source representation substrate")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan")
    p.add_argument("pack")

    f = sub.add_parser("fetch")
    f.add_argument("pack")
    f.add_argument("--source-id", action="append", dest="source_ids")
    f.add_argument("--verified-date", required=True)
    f.add_argument("--timeout", type=int, default=45)
    f.add_argument("--continue-on-error", action="store_true")

    i = sub.add_parser("import")
    i.add_argument("pack")
    i.add_argument("--import-dir", required=True)
    i.add_argument("--source-id", action="append", dest="source_ids")
    i.add_argument("--verified-date", required=True)
    i.add_argument("--continue-on-error", action="store_true")

    args = ap.parse_args()
    try:
        pack = Path(args.pack)
        if args.cmd == "plan":
            result = plan(pack)
        elif args.cmd == "fetch":
            result = execute(pack, "fetch", None, args.source_ids, args.verified_date, args.timeout, args.continue_on_error)
        else:
            result = execute(pack, "import", Path(args.import_dir), args.source_ids, args.verified_date, 0, args.continue_on_error)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        if args.cmd == "plan":
            return 0
        return 0 if result.get("status") == "complete" else 3 if result.get("status") == "partial" else 2
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
