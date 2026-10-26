#!/usr/bin/env python3
"""Replay accepted Estonian Riigi Teataja legal texts against saved responses."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import convert_riigiteataja as rt

PACK = Path(__file__).resolve().parent
TEMP_ROOT = Path(os.environ.get("PUBLIC_DATA_TEMP_ROOT", "/tmp/public-data"))
TEMP_ESTONIA = TEMP_ROOT / "temp" / "estonia"
MANIFEST = TEMP_ESTONIA / "candidate-manifest.json"
CAPTURES = TEMP_ESTONIA / "retrieval-manifest.json"
HOST = "www.riigiteataja.ee"
MAX_BODY_CHARS = 500

# Current Estonian wording is resolved by exact official title in the dated law
# search. English candidate links remain separate, exact-version captures below.
CURRENT_GROUPS = [
    {"official_title": "Välismaalaste seadus", "candidate_ids": ["ee-aliens-act-current-2026-10", "ee-aliens-act-current"]},
    {"official_title": "Euroopa Liidu kodaniku seadus", "candidate_ids": ["ee-citizen-act-current-2026-10"]},
    {"official_title": "Rahvastikuregistri seadus", "candidate_ids": ["ee-population-register-act"]},
    {"official_title": "Väljasõidukohustuse ja sissesõidukeelu seadus", "candidate_ids": ["ee-leave-entry-ban-act"]},
    {"official_title": "Isikut tõendavate dokumentide seadus", "candidate_ids": ["ee-identity-documents-act"]},
    {"official_title": "Konsulaarseadus", "candidate_ids": ["ee-consular-act"]},
    {"official_title": "Riigilõivuseadus", "candidate_ids": ["ee-state-fees-act"]},
    {"official_title": "Haldusmenetluse seadus", "candidate_ids": ["ee-admin-procedure-act"]},
    {"official_title": "Riigivastutuse seadus", "candidate_ids": ["ee-state-liability-act"]},
    {"official_title": "Halduskohtumenetluse seadustik", "candidate_ids": ["ee-admin-court-code-current"]},
    {"official_title": "Riigi õigusabi seadus", "candidate_ids": ["ee-state-legal-aid-act"]},
    {"official_title": "Isikuandmete kaitse seadus", "candidate_ids": ["ee-personal-data-act"]},
    {"official_title": "Avaliku teabe seadus", "candidate_ids": ["ee-public-information-act"]},
]

# These candidate URLs identify a specific Estonian-language edition rather
# than a current-alias lead. Retrieve that exact ID from the XML endpoint.
EXACT_XML = {
    "ee-citizen-act-et-future": {"source_id": "103062026006", "official_title": "Euroopa Liidu kodaniku seadus"},
    "ee-eu-right-regulation": {"source_id": "125042025013", "official_title": "Euroopa Liidu kodaniku ja tema perekonnaliikme elamisõiguse taotlemise, andmise ning selle pikendamise ja lõpetamise kord"},
    "ee-residence-data-forms-regulation": {"source_id": "108012019012", "official_title": "Elukohaandmete rahvastikuregistrisse kandmise kord, vormid ja nende täitmise juhend"},
}

# Exact document IDs found in the official /en/akt and /en/tolge links. The
# publisher's blob-html API returns the full published English text and its
# edition metadata; it does not imply that the translation is current today.
ENGLISH_IDS = {
    "ee-citizen-act-en-2025": "508092025004",
    "ee-citizen-act-en-2024": "524012024003",
    "ee-population-register-act": "511012023005",
    "ee-aliens-act-current": "510042023008",
    "ee-aliens-act-sept-2026": "501092026001",
    "ee-leave-entry-ban-act": "510072026001",
    "ee-identity-documents-act": "530092025008",
    "ee-consular-act": "512082025004",
    "ee-state-fees-act": "513072017017",
    "ee-admin-procedure-act": "505122023003",
    "ee-state-liability-act": "516052025004",
    "ee-admin-court-code-current": "507012014002",
    "ee-admin-court-code-may-2026": "520052026002",
    "ee-state-legal-aid-act": "520032025008",
    "ee-personal-data-act": "519032026002",
    "ee-public-information-act": "507082025001",
}

BLOCKS = {"address", "article", "br", "dd", "div", "dl", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "section", "table", "td", "th", "tr", "ul"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "noscript", "svg", "form"}
SKIP_CLASSES = {"hover-item-menu", "material-icons"}


class ClassText(HTMLParser):
    """Extract one publisher-marked HTML region while excluding UI controls."""
    def __init__(self, target_class: str):
        super().__init__(convert_charrefs=True)
        self.target_class = target_class
        self.stack: list[tuple[str, bool]] = []
        self.active = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if not self.active:
            if self.target_class not in classes:
                return
            self.active = True
            if tag not in VOID:
                self.stack.append((tag, False))
            return
        inherited_skip = any(skip for _, skip in self.stack)
        skip = inherited_skip or tag in SKIP_TAGS or bool(classes & SKIP_CLASSES)
        if tag == "br" and not skip:
            self.parts.append("\n")
        elif tag in BLOCKS and not skip:
            self.parts.append("\n")
        if tag not in VOID:
            self.stack.append((tag, skip))

    def handle_endtag(self, tag: str) -> None:
        if not self.active:
            return
        index = next((i for i in range(len(self.stack) - 1, -1, -1) if self.stack[i][0] == tag), None)
        if index is None:
            return
        skipped = any(skip for _, skip in self.stack[:index + 1])
        if tag in BLOCKS and not skipped:
            self.parts.append("\n")
        del self.stack[index:]
        if not self.stack:
            self.active = False

    def handle_data(self, data: str) -> None:
        if self.active and self.stack and not any(skip for _, skip in self.stack) and data.strip():
            self.parts.append(data)

    def text(self) -> str:
        raw = "".join(self.parts).replace("\xa0", " ").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
        out: list[str] = []
        for line in lines:
            if line or (out and out[-1]):
                out.append(line)
        return "\n".join(out).strip()


def extract_class(raw: bytes, class_name: str) -> str:
    parser = ClassText(class_name)
    parser.feed(raw.decode("utf-8", "replace"))
    return parser.text()


def entries_by_id(manifest: dict) -> dict[str, dict]:
    return {item["id"]: item for item in manifest.get("documents", [])}


def exact_xml_metadata(raw: bytes, source_id: str, expected_title: str):
    root = rt.ET.fromstring(raw)
    if rt.local_name(root) != "oigusakt":
        raise ValueError(f"unexpected XML root: {rt.local_name(root)}")
    metadata = rt.find_child(root, "metaandmed")
    if metadata is None:
        raise ValueError("XML lacks metadata")
    meta = {rt.local_name(child): rt.text_of(child) for child in metadata}
    if meta.get("globaalID") != source_id:
        raise ValueError(f"exact source ID {source_id} differs from XML global ID {meta.get('globaalID')!r}")
    if meta.get("tekstiliik") not in {"terviktekst", "algtekst-terviktekst"}:
        raise ValueError(f"XML does not contain a consolidated text: {meta.get('tekstiliik')!r}")
    if meta.get("dokumentLiik") not in {"seadus", "määrus"}:
        raise ValueError(f"unexpected legal document type: {meta.get('dokumentLiik')!r}")
    actual = rt.text_of(rt.find_child(root, "aktinimi"))
    if not actual.startswith(expected_title):
        raise ValueError(f"XML title {actual!r} does not match {expected_title!r}")
    body = rt.find_child(root, "sisu")
    if body is None or len(list(body.iter())) < 20:
        raise ValueError("XML lacks a substantial legal-text body")
    return root, meta, actual


def xml_markdown(root, entry: dict, descriptor: dict) -> bytes:
    return rt.render_document(root, {
        **descriptor,
        "candidate_id": entry["id"],
        "title": entry.get("title", entry["id"]),
        "language": "et",
    })


def html_markdown(entry: dict, record: dict, raw: bytes) -> tuple[bytes, str, str]:
    metadata = extract_class(raw, "meta")
    body = extract_class(raw, "akt-sisu")
    if len(body) < MAX_BODY_CHARS:
        raise ValueError(f"official blob-html response has only {len(body)} chars in .akt-sisu")
    text = [
        f"# {entry.get('title', entry['id'])}",
        "",
        "- Jurisdiction: Estonia",
        f"- Candidate ID: `{entry['id']}`",
        f"- Publisher: Riigi Teataja",
        f"- Candidate URL: {entry['url']}",
        f"- Exact text API URL: {record['request_url']}",
        f"- Retrieved: {record['retrieved_at']}",
        f"- Source SHA-256: `{record['source_sha256']}`",
        "- Extraction: official `akt-sisu` article body; publisher `meta` region retained below",
        "",
        "> **Review candidate.** This is the exact published English text returned for the document ID above. Translation and in-force dates below belong to this edition; they do not establish currentness. It has not been accepted into the trusted legal corpus.",
        "",
        "## Publisher version metadata",
        "",
        metadata or "No metadata text was returned.",
        "",
        "## Captured official English text",
        "",
        body,
        "",
    ]
    return ("\n".join(text).rstrip() + "\n").encode("utf-8"), metadata, body


def current_search(as_of: str):
    pages: list[dict] = []
    rows: list[dict] = []
    total = None
    for page in range(1, 10):
        url = rt.search_url(as_of, page)
        raw, final_url, content_type = rt.fetch(url, "application/json")
        if content_type != "application/json":
            raise ValueError(f"dated search returned {content_type}, expected JSON")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload.get("aktid"), list) or not isinstance(payload.get("metaandmed"), dict):
            raise ValueError("dated search response lacks expected act and metadata arrays")
        if payload["metaandmed"].get("leht") != page:
            raise ValueError(f"dated search returned an unexpected page number: {payload['metaandmed'].get('leht')}")
        if total is None:
            total = int(payload["metaandmed"].get("kokku", 0))
        raw_path = rt.save_raw(f"laws-{as_of}-page-{page}", raw, "json")
        pages.append({"page": page, "request_url": url, "resolved_url": final_url, "source_bytes": len(raw), "source_sha256": rt.sha256(raw), "raw_path": raw_path, "row_count": len(payload["aktid"]), "total_count": total})
        rows.extend(payload["aktid"])
        if len(rows) >= total:
            break
        time.sleep(1)
    if total is None or len(rows) < total:
        raise ValueError(f"dated act search incomplete: got {len(rows)} of {total}")
    return pages, rows


def make_record(entry: dict, artifact_type: str, representation: str, request_url: str, resolved_url: str, raw: bytes, raw_path: str, output_path: str, converted: bytes, retrieved_at: str | None = None, **extra) -> dict:
    return {
        "candidate_id": entry["id"],
        "artifact_type": artifact_type,
        "representation": representation,
        "source_url": entry["url"],
        "request_url": request_url,
        "resolved_url": resolved_url,
        "retrieved_at": retrieved_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_content_type": extra.pop("source_content_type", "text/html" if artifact_type == "english_version" else "application/xml"),
        "source_bytes": len(raw),
        "source_sha256": rt.sha256(raw),
        "raw_path": raw_path,
        "candidate_text_path": output_path,
        "converted_bytes": len(converted),
        "converted_sha256": rt.sha256(converted),
        "retrieval_status": "converted_review_candidate",
        "accepted": False,
        **extra,
    }


def sync() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_id = entries_by_id(manifest)
    legacy_capture = json.loads(rt.CAPTURES.read_text(encoding="utf-8")) if rt.CAPTURES.exists() else {"records": []}
    legacy_by_id = {item.get("candidate_id"): item for item in legacy_capture.get("records", [])}
    as_of = datetime.now().date().isoformat()
    search_pages, rows = current_search(as_of)
    records: list[dict] = []
    errors: list[str] = []

    for group in CURRENT_GROUPS:
        title = group["official_title"]
        matches = [row for row in rows if row.get("pealkiri") == title]
        if len(matches) != 1:
            errors.append(f"current {title}: expected one exact title match, got {len(matches)}")
            continue
        row = matches[0]
        try:
            rt.parse_validity(row, as_of)
            act_id = int(row["globaalID"])
            api_url = f"https://{HOST}/public-api/api/v1/akt/{act_id}/xml"
            raw, resolved_url, content_type = rt.fetch(api_url)
            rt.validate_xml(raw, act_id, title, as_of)
            raw_path = rt.save_raw(f"current-{act_id}-{as_of}", raw, "xml")
            for candidate_id in group["candidate_ids"]:
                entry = by_id[candidate_id]
                canonical = candidate_id in {"ee-aliens-act-current-2026-10", "ee-citizen-act-current-2026-10"}
                suffix = "" if canonical else f"-current-et-{as_of}"
                output_path = f"source-library/estonia/candidates/{candidate_id}{suffix}.md"
                prior = legacy_by_id.get(candidate_id, {})
                retrieved_at = prior.get("retrieved_at") if prior.get("source_sha256") == rt.sha256(raw) else None
                retrieved_at = retrieved_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
                descriptor = {
                    "candidate_id": candidate_id,
                    "title": entry.get("title", candidate_id),
                    "language": "et",
                    "as_of_date": as_of,
                    "source_url": f"https://{HOST}/akt/{act_id}",
                    "api_url": resolved_url,
                    "retrieved_at": retrieved_at,
                    "source_sha256": rt.sha256(raw),
                }
                xml_root = rt.ET.fromstring(raw)
                meta = {rt.local_name(child): rt.text_of(child) for child in rt.find_child(xml_root, "metaandmed")}
                descriptor["validity_period"] = meta.get("kehtivus", "")
                converted = rt.render_document(xml_root, descriptor)
                rt.atomic_write(rt.ROOT / output_path, converted)
                record = make_record(entry, "current_xml", "current_estonian", f"{api_url} (title resolved from dated law search)", resolved_url, raw, raw_path, output_path, converted,
                                     retrieved_at=retrieved_at, source_url=descriptor["source_url"], source_content_type=content_type,
                                     as_of_date=as_of, official_title=title, act_id=act_id, validity_period=meta.get("kehtivus"),
                                     retrieval_shape="dated official law search -> exact XML API")
                records.append(record)
                print(f"current {candidate_id}: ID {act_id}, {len(raw)} XML bytes")
        except Exception as exc:
            errors.append(f"current {title}: {type(exc).__name__}: {exc}")

    for candidate_id, target in EXACT_XML.items():
        entry = by_id[candidate_id]
        source_id = target["source_id"]
        api_url = f"https://{HOST}/public-api/api/v1/akt/{source_id}/xml"
        try:
            raw, resolved_url, content_type = rt.fetch(api_url)
            root, meta, actual_title = exact_xml_metadata(raw, source_id, target["official_title"])
            raw_path = rt.save_raw(f"exact-{candidate_id}-{source_id}", raw, "xml")
            output_path = f"source-library/estonia/candidates/{candidate_id}.md"
            retrieval_label = f"Exact published edition ID {source_id}; source validity period {meta.get('kehtivus', '')}"
            review_note = "> **Review candidate.** This is the exact published edition identified by the candidate URL. Its source validity period is retained below; do not treat a future or expired edition as current. It has not been accepted into the trusted legal corpus."
            retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            descriptor = {"candidate_id": candidate_id, "title": entry.get("title", candidate_id), "language": "et", "as_of_date": "exact-published-edition", "retrieval_label": retrieval_label,
                          "source_url": entry["url"], "api_url": resolved_url, "retrieved_at": retrieved_at, "source_sha256": rt.sha256(raw),
                          "review_note": review_note}
            converted = rt.render_document(root, descriptor)
            # The converter's standard paragraph says "effective-date search" only
            # for dated lookup. Exact version records carry a distinct retrieval label.
            rt.atomic_write(rt.ROOT / output_path, converted)
            record = make_record(entry, "exact_xml", "exact_estonian_edition", api_url, resolved_url, raw, raw_path, output_path, converted,
                                 retrieved_at=retrieved_at, source_content_type=content_type,
                                 source_id=source_id, official_title=actual_title, validity_period=meta.get("kehtivus"), text_type=meta.get("tekstiliik"),
                                 document_type=meta.get("dokumentLiik"), retrieval_label=retrieval_label, review_note=review_note,
                                 retrieval_shape="exact published source ID -> official XML API")
            records.append(record)
            print(f"exact {candidate_id}: {source_id}, {len(raw)} XML bytes")
        except Exception as exc:
            errors.append(f"exact {candidate_id}: {type(exc).__name__}: {exc}")

    for candidate_id, source_id in ENGLISH_IDS.items():
        entry = by_id[candidate_id]
        api_url = f"https://{HOST}/public-api/api/v1/en/akt/{source_id}/blob-html"
        try:
            raw, resolved_url, content_type = rt.fetch(api_url, "text/html")
            if content_type not in {"text/html", "application/xhtml+xml"}:
                raise ValueError(f"English text API returned {content_type}")
            metadata = extract_class(raw, "meta")
            body = extract_class(raw, "akt-sisu")
            if len(body) < MAX_BODY_CHARS:
                raise ValueError(f"publisher article body contains only {len(body)} characters")
            raw_path = rt.save_raw(f"english-{candidate_id}-{source_id}", raw, "html")
            output_path = f"source-library/estonia/candidates/{candidate_id}.md"
            record_stub = {"request_url": api_url, "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source_sha256": rt.sha256(raw)}
            converted, metadata, body = html_markdown(entry, record_stub, raw)
            rt.atomic_write(rt.ROOT / output_path, converted)
            meta_lines = [line.strip() for line in metadata.splitlines() if line.strip()]
            version_evidence = "; ".join(meta_lines[:14])
            record = make_record(entry, "english_version", "exact_published_english", api_url, resolved_url, raw, raw_path, output_path, converted,
                                 retrieved_at=record_stub["retrieved_at"], source_content_type=content_type,
                                 source_id=source_id, publisher_metadata=metadata, version_evidence=version_evidence,
                                 retrieval_shape="official English blob-html API -> publisher-marked article body")
            records.append(record)
            print(f"English {candidate_id}: {source_id}, {len(body)} text characters")
        except Exception as exc:
            errors.append(f"English {candidate_id}: {type(exc).__name__}: {exc}")

    old = json.loads(CAPTURES.read_text(encoding="utf-8")) if CAPTURES.exists() else {}
    capture_manifest = {
        "manifest_version": 1,
        "jurisdiction": "Estonia",
        "publisher": "Riigi Teataja",
        "as_of_date": as_of,
        "method": "Current Estonian acts are resolved by exact title from the official date-bound law-search API and retrieved by global ID as XML. Fixed Estonian editions use the exact candidate document ID and the XML API. English editions use the exact candidate document ID and the official blob-html API; edition validity is kept separate from currentness.",
        "search_pages": search_pages,
        "records": records,
        "candidate_text_artifact_count": sum(bool(item.get("candidate_text_path")) for item in records),
        "accepted_source_count": 0,
        "errors": errors,
    }
    rt.atomic_write(CAPTURES, (json.dumps(capture_manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    # Update the inventory without conflating an older English translation with
    # the current Estonian consolidation captured for the same instrument.
    for record in records:
        entry = by_id[record["candidate_id"]]
        entry["retrieved"] = True
        entry["accepted"] = False
        entry["retrieval_status"] = record["retrieval_status"]
        entry["source_sha256"] = record["source_sha256"]
        entry["converted_sha256"] = record["converted_sha256"]
        entry["source_bytes"] = record["source_bytes"]
        entry["candidate_text_path"] = record["candidate_text_path"]
        entry["resolved_url"] = record["resolved_url"]
        entry["retrieval_shape"] = record["retrieval_shape"]
        if record["artifact_type"] == "english_version":
            entry["version_evidence"] = record["version_evidence"]
            entry["exact_english_source_id"] = record["source_id"]
            entry["publisher_metadata"] = record["publisher_metadata"]
    current_by_id = {record["candidate_id"]: record for record in records if record["artifact_type"] == "current_xml"}
    primary_current = {"ee-aliens-act-current-2026-10", "ee-citizen-act-current-2026-10"}
    for candidate_id, record in current_by_id.items():
        entry = by_id[candidate_id]
        if candidate_id in primary_current:
            entry["candidate_text_path"] = record["candidate_text_path"]
            entry["source_sha256"] = record["source_sha256"]
            entry["converted_sha256"] = record["converted_sha256"]
            entry["source_bytes"] = record["source_bytes"]
        else:
            entry["current_estonian_text_path"] = record["candidate_text_path"]
            entry["current_estonian_source_sha256"] = record["source_sha256"]
            entry["current_estonian_converted_sha256"] = record["converted_sha256"]
            entry["current_estonian_as_of_date"] = as_of
            entry["current_estonian_version_evidence"] = f"{record['official_title']}; global ID {record['act_id']}; effective period {record['validity_period']}; resolved for {as_of}."
    manifest["candidate_source_count"] = len(manifest.get("documents", []))
    manifest["accepted_source_count"] = 0
    manifest["retrieved_review_candidate_count"] = sum(bool(item.get("retrieved")) for item in manifest.get("documents", []))
    manifest["converted_review_candidate_count"] = sum(item.get("retrieval_status") == "converted_review_candidate" for item in manifest.get("documents", []))
    manifest["retrieval_status"] = f"{manifest['converted_review_candidate_count']} candidate source texts converted; exact English editions remain distinct from current Estonian texts; no source accepted"
    rt.atomic_write(MANIFEST, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"saved {len(records)} text artifacts; errors={len(errors)}")
    if errors:
        raise SystemExit("\n".join(errors))


def verify() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_id = entries_by_id(manifest)
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    errors: list[str] = []
    capture_ledger = captures.get("legal_text_capture_ledger", captures)
    for record in capture_ledger.get("records", []):
        try:
            raw = (TEMP_ROOT / record["raw_path"]).read_bytes()
            if rt.sha256(raw) != record["source_sha256"]:
                raise ValueError("raw source hash mismatch")
            entry = by_id[record["candidate_id"]]
            if record["artifact_type"] == "english_version":
                converted, metadata, body = html_markdown(entry, record, raw)
                if metadata != record.get("publisher_metadata"):
                    raise ValueError("publisher metadata replay mismatch")
                section = "Captured official English text"
            else:
                root = rt.ET.fromstring(raw)
                if record["artifact_type"] == "current_xml":
                    rt.validate_xml(raw, int(record["act_id"]), record["official_title"], record["as_of_date"])
                else:
                    exact_xml_metadata(raw, record["source_id"], record["official_title"])
                descriptor = {
                    **record,
                    "candidate_id": record["candidate_id"],
                    "title": entry.get("title", record["candidate_id"]),
                    "language": "et",
                    "source_url": record["source_url"],
                    "api_url": record["resolved_url"],
                    "retrieved_at": record["retrieved_at"],
                    "source_sha256": record["source_sha256"],
                    "as_of_date": record.get("as_of_date", "exact-published-edition"),
                }
                for field in ("retrieval_label", "review_note"):
                    if field in record:
                        descriptor[field] = record[field]
                converted = rt.render_document(root, descriptor)
                section = "Consolidated statutory text (Estonian)"
            if rt.sha256(converted) != record["converted_sha256"]:
                raise ValueError("deterministic conversion hash differs from capture ledger")
            saved = (PACK / record["document_path"]).read_bytes()
            if rt.sha256(saved) != record.get("accepted_artifact_sha256"):
                raise ValueError("accepted document hash differs from acceptance register")
            marker = f"## {section}\n"
            replay_body = converted.decode("utf-8").split(marker, 1)[1].strip()
            accepted_body = saved.decode("utf-8").split(marker, 1)[1].strip()
            if replay_body != accepted_body:
                raise ValueError("accepted legal text differs from deterministic replay")
            print(f"verified accepted local copy {record['candidate_id']} ({record['representation']})")
        except Exception as exc:
            errors.append(f"{record.get('candidate_id')} {record.get('representation')}: {type(exc).__name__}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "verify":
        verify()
    elif mode == "sync":
        raise SystemExit("Capture is handled through EU Source Update Monitor local research. The legacy sync mode is retired after promotion.")
    else:
        raise SystemExit("usage: sync_estonia_legal_texts.py sync|verify")
