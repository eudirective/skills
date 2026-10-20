#!/usr/bin/env python3
"""Capture and replay configured Fedlex legal-text manifestations."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "source-library"
PACK = LIBRARY / "switzerland"
MANIFEST_PATH = PACK / "references/candidate-manifest.json"
RESULTS_PATH = PACK / "references/switzerland-capture-results.json"
MAX_BYTES = 24 * 1024 * 1024
TIMEOUT = 25
USER_AGENT = "eudirective-source-library/1.0 (public-source review; eudirective@proton.me)"

sys.path.insert(0, str(LIBRARY))
import sync_candidate_pages as common  # noqa: E402


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request(url: str, accept: str) -> tuple[bytes, str, str]:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host != "fedlex.data.admin.ch":
        raise ValueError("Fedlex request URL is outside the approved HTTPS host")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        final = response.geturl()
        resolved = urllib.parse.urlparse(final)
        if resolved.scheme != "https" or (resolved.hostname or "").lower() != host:
            raise ValueError("Fedlex redirected outside its approved HTTPS host")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Fedlex response exceeded the 24 MiB limit")
        if not data:
            raise ValueError("Fedlex returned an empty response")
        return data, final, response.headers.get_content_type().lower()


def manifest_file_url(metadata: bytes) -> str:
    text = metadata.decode("utf-8", "replace")
    matches = re.findall(r"\bjolux:isExemplifiedBy\b\s*<([^>]+)>", text)
    if not matches:
        matches = re.findall(
            r"<jolux:isExemplifiedBy\s+rdf:resource=[\"']([^\"']+)", text
        )
    public = [
        url for url in matches
        if url.startswith("https://fedlex.data.admin.ch/filestore/")
    ]
    if len(public) != 1:
        raise ValueError(f"expected one public current Fedlex file-store link, found {len(public)}")
    return public[0]


def save(relative: str, data: bytes) -> None:
    path = common.inside(relative)
    if not path.exists():
        common.atomic(path, data)


def validate_text(entry: dict, raw: bytes, content_type: str) -> tuple[str, str]:
    if content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError(f"unexpected Fedlex text media type: {content_type}")
    if not raw.lstrip().lower().startswith((b"<!doctype html", b"<html")):
        raise ValueError("Fedlex file-store response is not an HTML document")
    parser = common.Region()
    parser.feed(raw.decode("utf-8", "replace"))
    body = parser.text()
    if len(body) < 100:
        raise ValueError("Fedlex HTML did not contain a substantial legal-text body")
    folded = body.casefold()
    missing = [m for m in entry.get("validation_markers", []) if m.casefold() not in folded]
    if missing:
        raise ValueError("publisher identity markers missing from text: " + ", ".join(missing))
    return parser.selector or "body", body


def configured_entries(manifest: dict) -> list[dict]:
    return [e for e in manifest.get("sources", []) if e.get("fedlex_manifest_url")]


def direct_entries(manifest: dict) -> list[dict]:
    return [e for e in manifest.get("sources", []) if e.get("direct_capture")]


def capture_fedlex(entry: dict, stamp: str, old: dict | None) -> dict:
    candidate_id = entry["id"]
    metadata, metadata_resolved, metadata_type = request(
        entry["fedlex_manifest_url"], "text/turtle,application/rdf+xml;q=0.9"
    )
    if metadata_type not in {"text/turtle", "application/rdf+xml"}:
        raise ValueError(f"unexpected Fedlex metadata media type: {metadata_type}")
    file_url = manifest_file_url(metadata)
    expected_prefix = (
        f"https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/"
        f"{entry['fedlex_eli_path']}/{entry['version_date']}/{entry['language']}/html/"
    )
    if not file_url.startswith(expected_prefix):
        raise ValueError("Fedlex file-store object does not match the registered ELI version/language")
    metadata_hash = digest(metadata)
    metadata_rel = f"temp/switzerland/raw/{candidate_id}-{metadata_hash}.ttl"
    save(metadata_rel, metadata)

    raw, resolved, content_type = request(file_url, "text/html,application/xhtml+xml;q=0.9")
    selector, body = validate_text(entry, raw, content_type)
    source_hash = digest(raw)
    raw_rel = f"temp/switzerland/raw/{candidate_id}-{source_hash}.html"
    save(raw_rel, raw)

    changed = bool(old and old.get("source_sha256") != source_hash)
    output = f"source-library/switzerland/candidates/{candidate_id}.md"
    state = "review_candidate"
    status = "converted_review_candidate"
    if changed:
        output = f"temp/switzerland/pending/{candidate_id}-{source_hash[:16]}.md"
        state = "changed_pending_review"
        status = "changed_review_candidate"
    converted = common.render(
        entry, "switzerland", stamp, resolved, content_type, source_hash, selector, body
    )
    common.atomic(common.inside(output), converted)
    return {
        "candidate_id": candidate_id,
        "source_url": entry["url"],
        "manifest_url": entry["fedlex_manifest_url"],
        "manifest_resolved_url": metadata_resolved,
        "manifest_content_type": metadata_type,
        "manifest_bytes": len(metadata),
        "manifest_sha256": metadata_hash,
        "manifest_path": metadata_rel,
        "file_url": file_url,
        "request_url": file_url,
        "resolved_url": resolved,
        "retrieved_at": stamp,
        "source_content_type": content_type,
        "source_bytes": len(raw),
        "source_sha256": source_hash,
        "raw_path": raw_rel,
        "candidate_text_path": output,
        "converted_sha256": digest(converted),
        "converted_bytes": len(converted),
        "content_selector": selector,
        "retrieval_status": status,
        "review_state": state,
        "accepted": False,
    }


def sync() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = configured_entries(manifest) + direct_entries(manifest)
    if not entries:
        raise SystemExit("No Swiss candidates have configured Fedlex or direct-page routes.")
    previous = json.loads(RESULTS_PATH.read_text(encoding="utf-8")) if RESULTS_PATH.exists() else {"records": []}
    old_by_id = {r.get("candidate_id"): r for r in previous.get("records", [])}
    records = []

    for index, entry in enumerate(entries):
        candidate_id = entry["id"]
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            if entry.get("fedlex_manifest_url"):
                record = capture_fedlex(entry, stamp, old_by_id.get(candidate_id))
            else:
                hosts = {str(h).lower() for h in manifest.get("official_hosts", [])}
                for url_key in ("url", "retrieval_url"):
                    host = urllib.parse.urlparse(entry.get(url_key, "")).hostname
                    if host:
                        hosts.add(host.lower())
                record = common.capture("switzerland", entry, hosts, old_by_id.get(candidate_id))
        except Exception as exc:
            record = {
                "candidate_id": candidate_id,
                "source_url": entry.get("url"),
                "retrieval_status": "retrieval_or_conversion_error",
                "retrieval_note": f"{type(exc).__name__}: {exc}",
                "accepted": False,
            }
        records.append(record)
        print(candidate_id, record["retrieval_status"], record.get("candidate_text_path", record.get("retrieval_note", "")), flush=True)
        if index < len(entries) - 1:
            time.sleep(1)

    by_id = {r["candidate_id"]: r for r in records}
    for entry in manifest["sources"]:
        record = by_id.get(entry["id"])
        if not record:
            continue
        entry["retrieved"] = bool(record.get("source_sha256"))
        entry["accepted"] = False
        entry["retrieval_status"] = record["retrieval_status"]
        for key in (
            "candidate_text_path", "candidate_source_path", "source_sha256", "converted_sha256",
            "source_bytes", "resolved_url", "retrieval_note", "fedlex_file_url", "manifest_sha256",
        ):
            source_key = "file_url" if key == "fedlex_file_url" else key
            if source_key in record:
                entry[key] = record[source_key]
            elif key == "retrieval_note":
                entry.pop(key, None)

    states = {}
    for record in records:
        state = record["retrieval_status"]
        states[state] = states.get(state, 0) + 1
    manifest["retrieved_review_candidate_count"] = sum(bool(r.get("source_sha256")) for r in records)
    manifest["converted_review_candidate_count"] = sum(bool(r.get("candidate_text_path")) for r in records)
    manifest["accepted_source_count"] = 0
    manifest["retrieval_status"] = (
        f"{manifest['converted_review_candidate_count']} configured texts/pages converted; "
        f"{states.get('retrieval_or_conversion_error', 0)} configured retrieval/conversion errors; "
        "other Swiss candidates remain pending or discovery-only; no source accepted"
    )
    manifest["status"] = "partially_retrieved_review_candidates"
    results = {
        "jurisdiction": "switzerland",
        "as_of_date": datetime.now(timezone.utc).date().isoformat(),
        "method": "Configured Fedlex records use unauthenticated RDF manifestation metadata followed by the public file-store link. Other configured pages use bounded ordinary HTTPS GET only. Exact bytes are hashed and conversions remain review-only.",
        "request_policy": {"timeout_seconds": TIMEOUT, "max_response_bytes": MAX_BYTES, "delay_seconds": 1},
        "records": records,
        "accepted_source_count": 0,
    }
    common.atomic(MANIFEST_PATH, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode())
    common.atomic(RESULTS_PATH, (json.dumps(results, ensure_ascii=False, indent=2) + "\n").encode())


def verify() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    entries = {entry["id"]: entry for entry in manifest.get("sources", [])}
    errors = []
    for record in results.get("records", []):
        try:
            if not record.get("source_sha256"):
                continue
            raw = common.inside(record["raw_path"]).read_bytes()
            if digest(raw) != record["source_sha256"]:
                raise ValueError("source hash mismatch")
            if record.get("candidate_source_path"):
                pdf = common.inside(record["candidate_source_path"]).read_bytes()
                if digest(pdf) != record["source_sha256"]:
                    raise ValueError("preserved PDF hash mismatch")

            if record.get("manifest_url"):
                metadata = common.inside(record["manifest_path"]).read_bytes()
                if digest(metadata) != record["manifest_sha256"]:
                    raise ValueError("Fedlex metadata hash mismatch")
                if manifest_file_url(metadata) != record["file_url"]:
                    raise ValueError("Fedlex metadata does not identify the captured public file object")

            candidate_path = record.get("candidate_text_path")
            if not candidate_path:
                print("verified source and metadata hashes", record["candidate_id"])
                continue
            candidate = common.inside(candidate_path).read_bytes()
            if digest(candidate) != record.get("converted_sha256"):
                raise ValueError("converted text hash mismatch")

            if record.get("conversion_engine") == "Adobe Acrobat PDF-to-Markdown (connected service; not locally replayable)":
                content = candidate.decode("utf-8")
                if record.get("source_content_type") != "application/pdf":
                    raise ValueError("external PDF extraction is recorded for a non-PDF source")
                if record["source_sha256"] not in content or "## Captured source text" not in content:
                    raise ValueError("external extraction provenance is missing from candidate")
                print("verified external extraction snapshot hashes", record["candidate_id"])
                continue

            entry = entries[record["candidate_id"]]
            content_type = record["source_content_type"]
            if record.get("manifest_url"):
                selector, body = validate_text(entry, raw, content_type)
            elif content_type in {"text/html", "application/xhtml+xml", "application/octet-stream"}:
                parser = common.Region()
                parser.feed(raw.decode("utf-8", "replace"))
                selector, body = parser.selector or "no primary region", parser.text()
            elif content_type in {"application/json", "application/ld+json"}:
                body = "```json\n" + json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + "\n```"
                selector = "formatted JSON record"
            else:
                raise ValueError(f"no local replay rule for {content_type}")
            replay = common.render(
                entry, "switzerland", record["retrieved_at"], record["resolved_url"],
                content_type, record["source_sha256"], selector, body,
            )
            if replay != candidate:
                raise ValueError("conversion replay mismatch")
            print("replayed conversion and verified metadata", record["candidate_id"])
        except Exception as exc:
            errors.append(f"{record.get('candidate_id')}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))

def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"sync", "verify"}:
        raise SystemExit("usage: python source-library/switzerland/sync_switzerland.py sync|verify")
    if sys.argv[1] == "sync":
        sync()
    else:
        verify()


if __name__ == "__main__":
    main()
