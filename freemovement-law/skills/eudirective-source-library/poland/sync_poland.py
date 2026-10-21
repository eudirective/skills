#!/usr/bin/env python3
"""Capture Polish candidate texts from ELI and official source pages."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "source-library"
PACK = LIBRARY / "poland"
MANIFEST_PATH = PACK / "references/candidate-manifest.json"
RESULTS_PATH = PACK / "references/poland-capture-results.json"
MAX_BYTES = 24 * 1024 * 1024
TIMEOUT = 25
DELAY = 1.0
USER_AGENT = "eudirective-source-library/1.0 (public-source review; eudirective@proton.me)"

sys.path.insert(0, str(LIBRARY))
import sync_candidate_pages as common  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, hosts: set[str], accept: str) -> tuple[bytes, str, str]:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in hosts:
        raise ValueError("request URL is outside the HTTPS host allowlist")

    class CheckedRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            target = urllib.parse.urlparse(newurl)
            target_host = (target.hostname or "").lower()
            if target.scheme != "https" or target_host not in hosts:
                raise ValueError("redirect is outside the HTTPS host allowlist")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(CheckedRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with opener.open(request, timeout=TIMEOUT) as response:
        resolved = response.geturl()
        target = urllib.parse.urlparse(resolved)
        if target.scheme != "https" or (target.hostname or "").lower() not in hosts:
            raise ValueError("final URL is outside the HTTPS host allowlist")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeded 24 MiB limit")
        if not raw:
            return raw, resolved, response.headers.get_content_type().lower()
        return raw, resolved, response.headers.get_content_type().lower()


def save(relative: str, data: bytes) -> None:
    path = common.inside(relative)
    if not path.exists():
        common.atomic(path, data)


def eli_api_urls(entry: dict) -> tuple[str, str, str, int, int] | None:
    match = re.fullmatch(r"/eli/([A-Z]+)/([0-9]{4})/([0-9]+)/ogl", urllib.parse.urlparse(entry["url"]).path)
    if not match or urllib.parse.urlparse(entry["url"]).hostname != "eli.gov.pl":
        return None
    publisher, year_text, position_text = match.groups()
    year, position = int(year_text), int(position_text)
    metadata_url = f"https://api.sejm.gov.pl/eli/acts/{publisher}/{year}/{position}"
    return metadata_url, publisher, year_text, position, year


def capture_eli(entry: dict, hosts: set[str], stamp: str, prior: dict | None) -> dict:
    parsed = eli_api_urls(entry)
    if parsed is None:
        raise ValueError("candidate is not a supported Polish ELI publication URI")
    metadata_url, publisher, year_text, position, year = parsed
    metadata_raw, metadata_resolved, metadata_type = fetch(
        metadata_url, hosts, "application/json"
    )
    if metadata_type != "application/json":
        raise ValueError(f"unexpected ELI metadata media type: {metadata_type}")
    metadata = json.loads(metadata_raw)
    if metadata.get("publisher") != publisher or metadata.get("year") != year or metadata.get("pos") != position:
        raise ValueError("ELI metadata does not match the candidate's official publication identifier")
    if not metadata.get("title"):
        raise ValueError("ELI metadata has no official title")
    if "DU/" + year_text + "/" + str(position) in str(metadata.get("ELI", "")):
        pass
    elif metadata.get("ELI"):
        raise ValueError("ELI metadata URI does not match the candidate identifier")

    metadata_hash = sha(metadata_raw)
    metadata_rel = f"temp/poland/metadata/{common.slug(entry['id'])}-{metadata_hash}.json"
    save(metadata_rel, metadata_raw)
    formats = []
    if metadata.get("textHTML"):
        formats.append(("text.html", "text/html"))
    if metadata.get("textPDF"):
        formats.append(("text.pdf", "application/pdf"))
    if not formats:
        raise ValueError("official ELI metadata advertises no text format")

    raw = b""
    resolved = ""
    content_type = ""
    request_url = ""
    for suffix, accept in formats:
        request_url = metadata_url + "/" + suffix
        raw, resolved, content_type = fetch(request_url, hosts, accept)
        if raw:
            break
        time.sleep(DELAY)
    if not raw:
        raise ValueError("ELI metadata advertises a text format, but all advertised text endpoints were empty")

    source_hash = sha(raw)
    is_pdf = content_type == "application/pdf" and raw.startswith(b"%PDF-")
    raw_ext = "pdf" if is_pdf else "html"
    raw_rel = f"temp/poland/raw/{common.slug(entry['id'])}-{source_hash}.{raw_ext}"
    save(raw_rel, raw)
    pdf_rel = None
    if is_pdf:
        pdf_rel = f"temp/poland/pdf/{common.slug(entry['id'])}-{source_hash}.pdf"
        save(pdf_rel, raw)

    if content_type in {"text/html", "application/xhtml+xml"}:
        parser = common.Region()
        parser.feed(raw.decode("utf-8", "replace"))
        body = parser.text()
        selector = parser.selector or "no primary region"
        if len(body) < 100:
            raise ValueError("ELI HTML text is too short to be a legal text")
    elif is_pdf:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(raw))
        body = "\n\n".join(
            f"<!-- page {number} -->\n" + (page.extract_text() or "")
            for number, page in enumerate(reader.pages, 1)
        ).strip()
        selector = f"PDF text extraction; {len(reader.pages)} pages"
        if len(body) < 100:
            raise ValueError("ELI PDF text extraction returned no substantial text")
    else:
        raise ValueError(f"unexpected ELI text media type: {content_type}")

    changed = bool(
        not entry.get("replace_prior_capture", False)
        and prior
        and (
            prior.get("review_state") == "changed_pending_review"
            or (prior.get("source_sha256") and prior["source_sha256"] != source_hash)
        )
    )
    output = f"source-library/poland/candidates/{common.slug(entry['id'])}.md"
    status = "converted_review_candidate"
    if changed:
        output = f"temp/poland/pending/{common.slug(entry['id'])}-{source_hash[:16]}.md"
        status = "changed_review_candidate"
    rendered = common.render(
        entry, "poland", stamp, resolved, content_type, source_hash, selector, body
    )
    common.atomic(common.inside(output), rendered)
    result = {
        "candidate_id": entry["id"],
        "source_url": entry["url"],
        "request_url": request_url,
        "resolved_url": resolved,
        "retrieved_at": stamp,
        "source_content_type": content_type,
        "source_bytes": len(raw),
        "source_sha256": source_hash,
        "raw_path": raw_rel,
        "candidate_text_path": output,
        "converted_sha256": sha(rendered),
        "converted_bytes": len(rendered),
        "content_selector": selector,
        "retrieval_status": status,
        "review_state": "changed_pending_review" if changed else "review_candidate",
        "accepted": False,
        "candidate_source_path": pdf_rel,
        "conversion_engine": "pypdf 6.21.1" if is_pdf else "source-library/sync_candidate_pages.py HTML parser",
        "eli_metadata_url": metadata_url,
        "eli_metadata_resolved_url": metadata_resolved,
        "eli_metadata_path": metadata_rel,
        "eli_metadata_sha256": metadata_hash,
        "eli_metadata_bytes": len(metadata_raw),
        "eli_published_title": metadata["title"],
        "eli_published_status": metadata.get("status"),
        "eli_textHTML": bool(metadata.get("textHTML")),
        "eli_textPDF": bool(metadata.get("textPDF")),
        "eli_identifier": metadata.get("ELI") or f"{publisher}/{year_text}/{position}",
    }
    return result


def sync(selected_ids: set[str] | None = None) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    all_entries = manifest["sources"]
    entries = [entry for entry in all_entries if selected_ids is None or entry["id"] in selected_ids]
    unknown = (selected_ids or set()) - {entry["id"] for entry in entries}
    if unknown:
        raise SystemExit("unknown candidate ID(s): " + ", ".join(sorted(unknown)))
    old = json.loads(RESULTS_PATH.read_text(encoding="utf-8")) if RESULTS_PATH.exists() else {"records": []}
    old_by_id = {record["candidate_id"]: record for record in old.get("records", [])}
    hosts = {str(host).lower() for host in manifest.get("official_hosts", [])}
    hosts.add("api.sejm.gov.pl")
    for entry in entries:
        host = urllib.parse.urlparse(entry["url"]).hostname
        if host:
            hosts.add(host.lower())

    records_by_id = dict(old_by_id)
    for index, entry in enumerate(entries):
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            if eli_api_urls(entry):
                record = capture_eli(entry, hosts, stamp, old_by_id.get(entry["id"]))
            else:
                record = common.capture("poland", entry, hosts, old_by_id.get(entry["id"]))
        except Exception as exc:
            record = {
                "candidate_id": entry["id"],
                "source_url": entry.get("url"),
                "retrieval_status": "retrieval_or_conversion_error",
                "retrieval_note": f"{type(exc).__name__}: {exc}",
                "accepted": False,
            }
        records_by_id[entry["id"]] = record
        print(entry["id"], record["retrieval_status"], record.get("candidate_text_path", record.get("retrieval_note", "")), flush=True)
        if index < len(entries) - 1:
            time.sleep(DELAY)

    records = [records_by_id[entry["id"]] for entry in all_entries if entry["id"] in records_by_id]
    by_id = {record["candidate_id"]: record for record in records}
    for entry in all_entries:
        if entry["id"] not in selected_ids and selected_ids is not None:
            continue
        record = by_id[entry["id"]]
        entry["retrieved"] = bool(record.get("source_sha256"))
        entry["accepted"] = False
        entry["retrieval_status"] = record["retrieval_status"]
        for key in (
            "candidate_text_path", "candidate_source_path", "source_sha256", "converted_sha256",
            "source_bytes", "source_content_type", "raw_path", "request_url", "resolved_url",
            "converted_bytes", "content_selector", "conversion_engine", "review_state",
            "retrieval_note", "eli_metadata_url", "eli_metadata_path", "eli_metadata_sha256",
            "eli_published_title", "eli_published_status", "eli_identifier", "eli_textHTML", "eli_textPDF",
        ):
            if key in record and record[key] is not None:
                entry[key] = record[key]
            elif key == "retrieval_note":
                entry.pop(key, None)

        if record.get("candidate_text_path"):
            entry["retrieval_shape"] = (
                f"Exact {record.get('source_content_type', 'source')} response saved at `{record['raw_path']}` "
                f"({record.get('source_bytes', 0)} bytes; SHA-256 `{record['source_sha256']}`) and converted to "
                f"`{record['candidate_text_path']}` as an unaccepted review candidate."
            )
        elif record.get("source_sha256"):
            entry["retrieval_shape"] = (
                f"Exact {record.get('source_content_type', 'source')} response saved at `{record['raw_path']}`, "
                "but the page contained no sufficiently long extractable source body; retain as a discovery surface."
            )
        elif record.get("retrieval_note"):
            entry["retrieval_shape"] = (
                "Bounded HTTPS capture did not retrieve source bytes: " + record["retrieval_note"]
                + ". No authentication or certificate bypass was attempted."
            )

    counts: dict[str, int] = {}
    for record in records:
        state = record["retrieval_status"]
        counts[state] = counts.get(state, 0) + 1
    retrieved = sum(bool(record.get("source_sha256")) for record in records)
    converted = sum(bool(record.get("candidate_text_path")) for record in records)
    manifest["capture_status"] = "local_capture_candidates_updated"
    manifest["retrieved_review_candidate_count"] = retrieved
    manifest["converted_review_candidate_count"] = converted
    manifest["accepted_source_count"] = 0
    manifest["accepted_local_copy_count"] = 0
    manifest["acceptance_count_note"] = (
        "accepted_source_count and accepted_local_copy_count count retained local copies only. "
        "accepted_external_reference_count separately counts official links accepted within their recorded scope."
    )
    manifest["retrieval_status"] = (
        f"Local capture run: {converted} of {len(all_entries)} candidate records converted; {retrieved} exact source responses saved; "
        f"{counts.get('official_pdf_preserved_text_extraction_unavailable', 0)} PDFs preserved without text; "
        f"{counts.get('discovery_surface_no_text', 0)} pages had no extractable body; "
        f"{counts.get('retrieval_or_conversion_error', 0)} retrieval/conversion errors. No local copy is accepted by capture; "
        "official-link decisions are recorded separately in source-acceptance.json and source-review-manifest.json."
    )
    results = {
        "jurisdiction": "Poland",
        "as_of_date": datetime.now(timezone.utc).date().isoformat(),
        "method": "Polish ELI legal texts use the public Sejm API metadata and advertised HTML/PDF manifestation; other candidates use bounded ordinary HTTPS GET from their listed publisher/discovery URL. Exact bytes are hashed, conversions are review-only, and no authentication or challenge bypass is attempted.",
        "request_policy": {"timeout_seconds": TIMEOUT, "max_response_bytes": MAX_BYTES, "delay_seconds": DELAY},
        "records": records,
        "accepted_source_count": 0,
        "accepted_local_copy_count": 0,
        "acceptance_count_note": "accepted_source_count and accepted_local_copy_count count retained local copies only. Link acceptance is tracked separately in source-acceptance.json and source-review-manifest.json.",
    }
    common.atomic(MANIFEST_PATH, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode())
    common.atomic(RESULTS_PATH, (json.dumps(results, ensure_ascii=False, indent=2) + "\n").encode())


def verify() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    common.verify("poland")
    errors = []
    for record in results.get("records", []):
        if not record.get("eli_metadata_path"):
            continue
        try:
            metadata_raw = common.inside(record["eli_metadata_path"]).read_bytes()
            if sha(metadata_raw) != record["eli_metadata_sha256"]:
                raise ValueError("ELI metadata hash mismatch")
            metadata = json.loads(metadata_raw)
            entry = next(item for item in manifest["sources"] if item["id"] == record["candidate_id"])
            parsed = eli_api_urls(entry)
            if not parsed or metadata.get("publisher") != parsed[1] or metadata.get("year") != parsed[4] or metadata.get("pos") != parsed[3]:
                raise ValueError("ELI metadata no longer matches the recorded publication identifier")
            if metadata.get("title") != record["eli_published_title"] or metadata.get("status") != record.get("eli_published_status"):
                raise ValueError("ELI metadata title/status mismatch")
            print("verified ELI metadata", record["candidate_id"])
        except Exception as exc:
            errors.append(f"{record.get('candidate_id')}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"sync", "verify"}:
        raise SystemExit("usage: python source-library/poland/sync_poland.py sync [CANDIDATE_ID ...]|verify")
    if sys.argv[1] == "sync":
        sync(set(sys.argv[2:]) if len(sys.argv) > 2 else None)
    else:
        verify()


if __name__ == "__main__":
    main()
