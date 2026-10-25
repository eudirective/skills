#!/usr/bin/env python3
"""Verify accepted Spain document artifacts and check registered BOE text APIs.

This utility is read-only: it does not create candidate files, captures, or
retrieval manifests. Changed live responses are observations for a separate
Monitor review and archival step.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

PACK = Path(__file__).resolve().parent
REFERENCES = PACK / "references"
ACCEPTANCE_PATH = REFERENCES / "source-acceptance.json"
API_ROOT = "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id"
USER_AGENT = "EU-Directive source-library maintenance/1.0 (https://github.com/eudirective/public-data)"
TIMEOUT_SECONDS = 30
REQUEST_INTERVAL_SECONDS = 1.0

# BOE API ID, acceptance-register ID. The BOE ID is the stable publisher key.
SOURCES = [
    ("BOE-A-2007-4184", "es-06"),
    ("BOE-A-2024-24099", "es-07"),
    ("BOE-A-2000-544", "es-08"),
    ("BOE-A-2012-9218", "es-09"),
    ("BOE-A-2015-10565", "es-11"),
    ("BOE-A-1998-16718", "es-12"),
    ("BOE-A-2007-19814", "es-13"),
    ("BOE-A-2013-12887", "es-14"),
    ("BOE-A-2011-12628", "es-15"),
    ("BOE-A-2018-16673", "es-16"),
    ("BOE-A-1996-750", "es-17"),
    ("BOE-A-2021-3698", "es-18"),
    ("BOE-A-1981-10325", "es-19"),
    ("BOE-A-2007-22438", "es-03-original"),
    ("BOE-A-1889-4763", "es-04-original"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_acceptance() -> dict:
    return json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))


def review_rows(data: dict) -> dict:
    rows = data.get("official_reference_reviews")
    if not isinstance(rows, dict):
        raise ValueError("source-acceptance.json has no official_reference_reviews object")
    return rows


def verify() -> int:
    rows = review_rows(load_acceptance())
    errors = []
    checked = 0
    seen_paths = set()
    for source_id, row in rows.items():
        relative = row.get("document_path")
        expected = row.get("document_sha256")
        if not relative or not expected:
            errors.append(f"{source_id}: missing final document path or SHA-256")
            continue
        path = (REFERENCES / relative).resolve()
        if not path.is_relative_to(PACK.resolve()):
            errors.append(f"{source_id}: document path escapes the Spain pack")
            continue
        if str(path) in seen_paths:
            errors.append(f"{source_id}: duplicate document path {relative}")
            continue
        seen_paths.add(str(path))
        if not path.is_file():
            errors.append(f"{source_id}: document is missing: {relative}")
            continue
        actual = sha256(path.read_bytes())
        if actual != expected:
            errors.append(f"{source_id}: document hash mismatch: {relative}")
            continue
        checked += 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"verified {checked} accepted-reference document paths and SHA-256 hashes")
    print("source acceptance, topic coverage, and national review status remain separate")
    return 0


def local_expected_hashes(row: dict) -> tuple[str, str]:
    relative = row.get("document_path")
    if not relative:
        raise ValueError("accepted BOE record has no final document_path")
    path = (REFERENCES / relative).resolve()
    if not path.is_relative_to(PACK.resolve()) or not path.is_file():
        raise ValueError(f"accepted BOE document is missing: {relative}")
    text = path.read_text(encoding="utf-8", errors="strict")
    text_match = re.search(r"BOE(?: API)? text response SHA-256:\s*`?([0-9a-f]{64})", text, re.I)
    metadata_match = re.search(r"BOE(?: API)? metadata response SHA-256:\s*`?([0-9a-f]{64})", text, re.I)
    if not text_match or not metadata_match:
        raise ValueError(f"accepted BOE document lacks raw response hashes: {relative}")
    return text_match.group(1).lower(), metadata_match.group(1).lower()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": "application/xml", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise ValueError(f"unexpected HTTP status {response.status}")
        if urlparse(response.geturl()).hostname not in {"www.boe.es", "boe.es"}:
            raise ValueError("response left the official BOE host")
        payload = response.read(25 * 1024 * 1024 + 1)
        if len(payload) > 25 * 1024 * 1024:
            raise ValueError("response exceeded 25 MiB")
        return payload


def validate_response(payload: bytes, source_id: str, expect_text: bool) -> None:
    root = ET.fromstring(payload)
    code = next((e for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "code"), None)
    if code is None or (code.text or "").strip() != "200":
        raise ValueError("BOE API did not return code 200")
    if expect_text:
        text = next((e for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "texto"), None)
        if text is None:
            raise ValueError("BOE API response has no consolidated text")
        ids = {e.attrib.get("id_norma") for e in text.iter() if e.tag.rsplit("}", 1)[-1] == "version"}
        if source_id not in ids:
            raise ValueError(f"BOE response does not identify {source_id}")
        if not any(e.tag.rsplit("}", 1)[-1] == "bloque" for e in text.iter()):
            raise ValueError("BOE response has no text blocks")
    else:
        metadata = next((e for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "metadatos"), None)
        identifier = next((e for e in metadata.iter() if e.tag.rsplit("}", 1)[-1] == "identificador"), None) if metadata is not None else None
        if identifier is None or (identifier.text or "").strip() != source_id:
            raise ValueError(f"BOE metadata does not identify {source_id}")


def check() -> int:
    rows = review_rows(load_acceptance())
    observations = []
    errors = []
    previous_request = 0.0
    for boe_id, source_id in SOURCES:
        try:
            expected_text, expected_metadata = local_expected_hashes(rows[source_id])
            current = {}
            for kind in ("texto", "metadatos"):
                delay = REQUEST_INTERVAL_SECONDS - (time.monotonic() - previous_request)
                if delay > 0:
                    time.sleep(delay)
                payload = fetch(f"{API_ROOT}/{boe_id}/{kind}")
                previous_request = time.monotonic()
                validate_response(payload, boe_id, expect_text=(kind == "texto"))
                current[kind] = sha256(payload)
            observations.append({
                "publisher_id": boe_id,
                "acceptance_id": source_id,
                "text_response": "unchanged" if current["texto"] == expected_text else "changed",
                "metadata_response": "unchanged" if current["metadatos"] == expected_metadata else "changed",
                "current_text_sha256": current["texto"],
                "current_metadata_sha256": current["metadatos"],
            })
        except (KeyError, OSError, TimeoutError, ValueError, ET.ParseError, urllib.error.URLError) as exc:
            errors.append({"publisher_id": boe_id, "acceptance_id": source_id, "error": str(exc)})
    print(json.dumps({"observed_on_utc": time.strftime("%Y-%m-%d", time.gmtime()), "observations": observations, "errors": errors}, ensure_ascii=False, indent=2))
    print("Live observations are not saved or promoted. Archive any changed response with the Source Update Monitor and review it before updating a final document.")
    return 1 if errors else 0


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if command == "verify":
        raise SystemExit(verify())
    if command == "check":
        raise SystemExit(check())
    raise SystemExit("usage: python sync_boe.py [verify|check]")
