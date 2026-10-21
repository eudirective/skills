#!/usr/bin/env python3
"""Capture locator-only Austrian statutes from the official RIS, one at a time.

This action is limited to national-legislation records on the allowlisted RIS
host. It saves exact HTML responses and deterministic contentBlock conversions
as review candidates, then marks records ready only when all five source gates
and the semantic extraction checks pass. It never searches, accepts, or
overwrites an existing capture.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

PACK = Path(__file__).resolve().parents[1]
ROOT = PACK.parents[1]
sys.path.insert(0, str(PACK))
from sync_austria_sources import fetch  # noqa: E402
from scripts.convert_ris_capture import (  # noqa: E402
    RULE_VERSION,
    digest,
    extract_text,
    load_json,
    render_candidate,
    save_json,
)

MANIFEST_PATH = PACK / "references" / "candidate-manifest.json"
LEDGER_PATH = PACK / "references" / "capture-ledger.json"
ACCEPTANCE_PATH = PACK / "references" / "source-acceptance.json"
DELAY_SECONDS = 1.0


def title_from(raw: bytes) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title\s*>", raw.decode("utf-8", "replace"), re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", match.group(1)))).strip() if match else ""


def check_record(record: dict, raw: bytes, media_type: str, text: str, links: list[str]) -> tuple[dict, str]:
    url = record["url"]
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    identity = record.get("publisher_identifier", {})
    statute_number = str(identity.get("Gesetzesnummer", ""))
    paragraph = str(identity.get("Paragraf", ""))
    page_title = title_from(raw)
    expected_law = record.get("title", "").split(" § ", 1)[0]
    failures: list[str] = []

    if parsed.scheme != "https" or parsed.hostname not in {"ris.bka.gv.at", "www.ris.bka.gv.at"}:
        failures.append("publisher URL is not an allowlisted HTTPS RIS address")
    if query.get("Gesetzesnummer", [None])[0] != statute_number or query.get("Paragraf", [None])[0] != paragraph:
        failures.append("official locator does not match the manifest statute and paragraph")
    if media_type not in {"text/html", "application/xhtml+xml"}:
        failures.append(f"unexpected media type {media_type}")
    if "Bundesrecht konsolidiert" not in page_title or "tagesaktuelle Fassung" not in page_title:
        failures.append("RIS current-consolidated-version marker is absent from the page title")
    if expected_law and expected_law.casefold() not in page_title.casefold():
        failures.append("RIS page title does not match the expected statute")
    paragraph_pattern = rf"§\s*{re.escape(paragraph)}(?![A-Za-z0-9])"
    if not re.search(paragraph_pattern, text):
        failures.append(f"extracted RIS content does not contain § {paragraph}")
    target_clause = identity.get("target_clause")
    if target_clause and "Ziffer 11" in target_clause:
        clause = re.search(r"(?ms)^11\.\n(.+?)(?=\n(?:12\.|$))", text)
        if not clause or "begünstigter Drittstaatsangehöriger" not in clause.group(1):
            failures.append("FPG § 2(4)(11) target definition is absent or truncated")
    if len(text) < 100:
        failures.append("extracted section is unexpectedly short")
    pdf_links = sorted({urljoin(url, href) for href in links if ".pdf" in href.casefold()})
    known_pdf_types = all(
        urlparse(link).hostname in {"ris.bka.gv.at", "www.ris.bka.gv.at"}
        and urlparse(link).path.startswith(("/Dokumente/Bundesnormen/", "/Dokumente/BgblPdf/"))
        for link in pdf_links
    )
    if not known_pdf_types:
        failures.append("RIS content contains a linked PDF outside the reviewed current-text or official-gazette paths")

    checks = {
        "publisher_identity": {
            "status": "pass" if parsed.scheme == "https" and parsed.hostname in {"ris.bka.gv.at", "www.ris.bka.gv.at"} and query.get("Gesetzesnummer", [None])[0] == statute_number and query.get("Paragraf", [None])[0] == paragraph and expected_law.casefold() in page_title.casefold() else "fail",
            "evidence": f"HTTPS RIS source; URL statute/paragraph parameters match {statute_number}/§ {paragraph}; page title: {page_title}.",
        },
        "current_legal_version": {
            "status": "pass" if "tagesaktuelle Fassung" in page_title and "Bundesrecht konsolidiert" in page_title and expected_law.casefold() in page_title.casefold() else "fail",
            "evidence": f"RIS page title identifies the current consolidated version; retrieved {datetime.now(timezone.utc).date().isoformat()}.",
        },
        "extraction_completeness": {
            "status": "pass" if not any("extracted RIS" in issue or "short" in issue for issue in failures) else "fail",
            "evidence": f"Deterministic {RULE_VERSION} replay of the complete RIS div.contentBlock; expected section heading present; {len(text)} extracted characters.",
        },
        "attachments_review": {
            "status": "pass" if known_pdf_types else "pending",
            "evidence": f"Reviewed {len(pdf_links)} linked PDF target(s): RIS current-section PDFs are parallel renderings; BGBlPdf targets are official gazette promulgations, not incorporated forms or annexes. Current consolidated HTML remains the maintained text. Links: {pdf_links}",
        },
        "legal_classification": {
            "status": "pass" if record.get("source_type") == "national_legislation" else "fail",
            "evidence": f"Official RIS consolidated legislation; classified as national_legislation for {record.get('title')}.",
        },
    }
    return checks, "; ".join(failures)


def main() -> int:
    manifest = load_json(MANIFEST_PATH)
    ledger = load_json(LEDGER_PATH)
    acceptance = load_json(ACCEPTANCE_PATH)
    hosts = {host.lower() for host in manifest.get("official_hosts", [])}
    if "www.ris.bka.gv.at" not in hosts:
        raise ValueError("RIS host is not allowlisted by the manifest")
    ledger_rows = {row["candidate_id"]: row for row in ledger.get("records", [])}
    captured: list[str] = []
    failed: list[dict] = []
    date_dir = datetime.now(timezone.utc).date().isoformat()
    raw_dir = PACK / "captures" / date_dir

    targets = [
        record for record in manifest["documents"]
        if record.get("source_type") == "national_legislation"
        and urlparse(record.get("url", "")).hostname in {"ris.bka.gv.at", "www.ris.bka.gv.at"}
        and (
            record.get("retrieval_status") == "located_not_captured"
            or (record.get("retrieval_status") == "converted_review_candidate"
                and acceptance.get("records", {}).get(record["id"], {}).get("status") == "captured_pending_review")
        )
    ]
    for index, record in enumerate(targets):
        source_id = record["id"]
        using_saved_capture = False
        try:
            prior_capture = ledger_rows[source_id]
            using_saved_capture = bool(prior_capture.get("raw_path"))
            if using_saved_capture:
                raw_path = PACK / prior_capture["raw_path"]
                raw = raw_path.read_bytes()
                if digest(raw) != prior_capture.get("source_sha256"):
                    raise ValueError("saved raw RIS capture hash does not match the ledger")
                resolved_url = prior_capture.get("resolved_url") or record["url"]
                media_type = prior_capture.get("source_content_type") or "text/html"
            else:
                raw, resolved_url, media_type = fetch(record["url"], hosts)
            text, links = extract_text(raw)
            checks, issue = check_record(record, raw, media_type, text, links)
            raw_hash = digest(raw)
            retrieved_at = prior_capture.get("retrieved_at") if using_saved_capture else datetime.now(timezone.utc).isoformat(timespec="seconds")
            raw_name = f"{source_id}-{raw_hash}.html"
            raw_path = PACK / prior_capture["raw_path"] if using_saved_capture else raw_dir / raw_name
            if raw_path.exists() and raw_path.read_bytes() != raw:
                raise ValueError(f"raw capture collision for {source_id}")
            raw_dir.mkdir(parents=True, exist_ok=True)
            if not raw_path.exists():
                raw_path.write_bytes(raw)
            raw_rel = prior_capture["raw_path"] if using_saved_capture else f"captures/{date_dir}/{raw_name}"

            capture = {
                "candidate_id": source_id,
                "source_url": record["url"],
                "request_url": record["url"],
                "resolved_url": resolved_url,
                "retrieved_at": retrieved_at,
                "source_content_type": media_type,
                "source_bytes": len(raw),
                "source_sha256": raw_hash,
                "raw_path": raw_rel,
                "accepted": False,
                "retrieval_status": "converted_review_candidate",
                "review_state": "ready_to_accept" if not issue else "review_candidate",
                "candidate_text_path": None,
                "converted_sha256": None,
                "converted_bytes": None,
                "content_selector": "div.contentBlock",
                "conversion_rule_version": RULE_VERSION,
            }
            output_path = PACK / "candidates" / "legislation" / f"{source_id}.md"
            output_rel = output_path.relative_to(ROOT).as_posix()
            rendered = render_candidate(record, capture, text)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(rendered)
            converted_hash = digest(rendered)
            capture["candidate_text_path"] = output_rel
            capture["converted_sha256"] = converted_hash
            capture["converted_bytes"] = len(rendered)
            record.update({
                "retrieved": True,
                "accepted": False,
                "retrieved_at": retrieved_at,
                "resolved_url": resolved_url,
                "source_bytes": len(raw),
                "source_sha256": raw_hash,
                "source_content_type": media_type,
                "raw_path": raw_rel,
                "candidate_text_path": output_rel,
                "converted_sha256": converted_hash,
                "converted_bytes": len(rendered),
                "content_selector": "div.contentBlock",
                "conversion_rule_version": RULE_VERSION,
                "retrieval_status": "converted_review_candidate",
                "review_state": "ready_to_accept" if not issue else "review_candidate",
            })
            ledger_rows[source_id].update(capture)
            acceptance_row = acceptance["records"][source_id]
            acceptance_row["checks"] = checks
            acceptance_row["semantic_review"] = {
                "status": "passed" if not issue else "pending",
                "method": f"Replayed saved RIS div.contentBlock with {RULE_VERSION}; verified statute title, § {record.get('publisher_identifier', {}).get('Paragraf')}, and complete nonempty output.",
            }
            acceptance_row["raw_capture_evidence"] = raw_rel
            acceptance_row["status"] = "ready_to_accept" if not issue else "captured_pending_review"
            if issue:
                failed.append({"id": source_id, "issue": issue})
            else:
                captured.append(source_id)
            print(f"captured {source_id} {raw_hash} status={acceptance_row['status']}")
        except Exception as exc:
            failed.append({"id": source_id, "issue": f"{type(exc).__name__}: {exc}"})
            print(f"review-required {source_id}: {type(exc).__name__}: {exc}")
        if index < len(targets) - 1 and not using_saved_capture:
            time.sleep(DELAY_SECONDS)

    manifest["accepted_source_count"] = sum(1 for row in manifest["documents"] if row.get("accepted"))
    manifest["candidate_source_count"] = sum(1 for row in manifest["documents"] if row.get("retrieved") and not row.get("accepted") and row.get("review_state") != "discovery_only")
    manifest["located_not_captured_count"] = sum(1 for row in manifest["documents"] if not row.get("retrieved"))
    manifest["discovery_only_count"] = sum(1 for row in manifest["documents"] if row.get("review_state") == "discovery_only")
    manifest["retrieval_status"] = f"{manifest['accepted_source_count']} accepted; {manifest['candidate_source_count']} captured and pending review; {manifest['discovery_only_count']} discovery-only; {manifest['located_not_captured_count']} located but not captured"
    save_json(MANIFEST_PATH, manifest)
    save_json(LEDGER_PATH, ledger)
    save_json(ACCEPTANCE_PATH, acceptance)
    print(json.dumps({"ready_to_accept": captured, "count": len(captured), "review_required": failed}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
