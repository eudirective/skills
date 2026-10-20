#!/usr/bin/env python3
"""Inventory embedded image annexes and mark genuinely text-only acts."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "source-library/croatia"
CAPTURES = PACK / "captures/official-texts"
REF = PACK / "references"


def read(name: str) -> dict:
    return json.loads((REF / name).read_text(encoding="utf-8"))


def write(name: str, value: dict) -> None:
    (REF / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    manifest = read("candidate-manifest.json")
    acceptance = read("source-acceptance.json")
    register = read("attachment-review.json")
    docs = {row["id"]: row for row in manifest.get("documents", [])}
    known_records = {row["id"]: row for row in register.get("records", [])}
    seen: set[str] = set()
    image_sources: dict[str, list[str]] = {}
    external_files: dict[str, list[str]] = {}
    form_labels: dict[str, list[str]] = {}
    captured_scanned = 0
    text_only_scanned = 0

    for fragment in sorted(CAPTURES.glob("*.html")):
        source_id = fragment.stem
        doc = docs.get(source_id)
        if not doc:
            continue
        captured_scanned += 1
        html = fragment.read_text(encoding="utf-8", errors="replace")
        base = doc.get("url", "")
        urls = [urljoin(base, src) for src in re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']+)", html, re.I)]
        files = [urljoin(base, href) for href in re.findall(r"<a\b[^>]*\bhref=[\"']([^\"']+)", html, re.I)
                 if re.search(r"\.(?:pdf|docx?|xlsx?|png|jpe?g|gif|svg)(?:[?#]|$)", href, re.I)]
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        labels = list(dict.fromkeys(re.findall(r"(?i)\b(?:Obrazac|DODATAK)\s+[0-9]+[A-Z]?(?:\.[A-Z])?", text)))
        if urls or files:
            image_sources[source_id] = urls
            external_files[source_id] = files
            form_labels[source_id] = labels
        else:
            text_only_scanned += 1
            row = acceptance.get("records", {}).get(source_id)
            if row:
                row.setdefault("checks", {})["attachments_review"] = {
                    "status": "pass",
                    "evidence": "Source-specific .sl-content .doc fragment inspected; no embedded image or linked PDF/Office image attachment is present. The source is text-only for the captured official-document body."
                }

    for source_id, urls in image_sources.items():
        hash_hex = hashlib.sha256((CAPTURES / f"{source_id}.html").read_bytes()).hexdigest()
        if source_id == "hr-eea-reg-amend-86-21" and len(urls) == 4:
            for item_id, asset_urls in (
                ("hr-eea-card-specimen-4b", urls[:2]),
                ("hr-eea-card-specimen-11b", urls[2:]),
            ):
                item = known_records.get(item_id)
                if item:
                    item["image_source_urls"] = asset_urls
                    item["image_count"] = len(asset_urls)
                    item["source_fragment_sha256"] = hash_hex
            row_acceptance = acceptance.get("records", {}).get(source_id)
            if row_acceptance:
                row_acceptance.setdefault("checks", {})["attachments_review"] = {
                    "status": "pending",
                    "evidence": "The official fragment contains the Form 4b and Form 11b card specimens (four image pages total). Their two-sided image URLs are assigned to the two specimen records in attachment-review.json; visual and post-transition currentness review remain open."
                }
            continue
        existing = next((row for row in register.get("records", []) if row.get("parent_source_id") == source_id and row.get("id", "").endswith("-embedded-annex-inventory")), None)
        if existing:
            existing.update({
                "image_source_urls": urls,
                "external_file_urls": external_files[source_id],
                "recognized_labels_from_text": form_labels[source_id],
                "image_count": len(urls),
                "source_fragment_sha256": hash_hex,
            })
            continue
        row = {
            "id": f"{source_id}-embedded-annex-inventory",
            "parent_source_id": source_id,
            "title": f"Embedded image annex inventory for {doc_title(docs[source_id])}",
            "official_locator": docs[source_id].get("url"),
            "attachment_locator": "Image files embedded in the official .sl-content .doc fragment; see the enumerated publisher URLs in image_source_urls.",
            "classification": "officially published image annexes/forms; individual function and text content not visually reviewed",
            "recognized_labels_from_text": form_labels[source_id],
            "image_count": len(urls),
            "image_source_urls": urls,
            "external_file_urls": external_files[source_id],
            "source_fragment_sha256": hash_hex,
            "visual_review_status": "not_reviewed",
            "currentness_status": "unresolved",
            "legal_dependencies": ["Parent statutory/regulatory instrument and its latest usable official consolidation, where available; check a specific later act or EU provision only when it may materially affect the issue or annex relied upon."],
            "required_checks": [
                "visually inspect relevant images at readable resolution, and preserve page order, only when relying on their content or classification",
                "confirm a form/specimen function against headings and operative provisions only when relying on that classification",
                "use the latest usable official parent text; check a specific later act only if a material replacement, renumbering, commencement, or other legal-effect issue remains",
                "compare a live form/card only when relying on the annex as evidence of current practice",
                "record limitations that affect the relied-on image or passage"
            ]
        }
        register.setdefault("records", []).append(row)
        known_records[row["id"]] = row
        seen.add(source_id)
        row_acceptance = acceptance.get("records", {}).get(source_id)
        if row_acceptance:
            row_acceptance.setdefault("checks", {})["attachments_review"] = {
                "status": "pending",
                "evidence": f"Inventory found {len(urls)} embedded image(s) in the official document fragment. Exact image URLs and text labels are in attachment-review.json; visual and currentness checks remain open."
            }

    register["policy"] = (
        "Official-document fragments are scanned for embedded image and linked-file references. The inventory identifies candidates only; "
        "it does not establish visual completeness, legal classification, or current use. A source with no embedded image/file references is "
        "marked attachment-not-applicable for that captured document body."
    )
    write("attachment-review.json", register)
    write("source-acceptance.json", acceptance)
    print(f"Embedded annex inventory: {len(image_sources)} source documents with images; {sum(len(x) for x in image_sources.values())} image assets; {len(seen)} new review groups.")
    print(f"Text-only attachment reviews marked not applicable: {text_only_scanned} of {captured_scanned} captured official texts scanned.")
    return 0


def doc_title(row: dict) -> str:
    return row.get("title", row.get("id", "official document"))


if __name__ == "__main__":
    raise SystemExit(main())
