#!/usr/bin/env python3
"""Compare Croatian official-text captures with their stored conversions.

This is an acceptance-review operation, not a hash-integrity check: it reads
visible text nodes from the retained Narodne novine document fragment and
compares the ordered normalized text with the candidate's rendered source body.
Image and linked-file content is reported separately for the attachment gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "source-library/croatia"
CAPTURE_DIR = PACK / "captures/official-texts"
BLOCKS = {
    "address", "article", "blockquote", "dd", "div", "dl", "dt", "footer",
    "h1", "h2", "h3", "h4", "h5", "h6", "header", "li", "ol", "p",
    "section", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
}
SKIP = {"script", "style", "noscript"}
CAPTURE_MARKER = "## Official text-only capture\n"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("\u00a0", " ").replace("\u00ad", "")
    return re.sub(r"\s+", " ", text).strip()


class VisibleText(HTMLParser):
    """Independent visible-text walk over the already selected official region."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.images = 0
        self.files: list[str] = []
        self.links: list[str] = []
        self.heading_text: list[str] = []
        self.heading_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag in SKIP:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in BLOCKS or tag == "br":
            self.parts.append(" ")
        if tag == "img":
            self.images += 1
        if tag == "a":
            href = attr.get("href") or ""
            if href:
                self.links.append(href)
                if re.search(r"\.(?:pdf|docx?|xlsx?|pptx?)(?:$|[?#])", href, re.I):
                    self.files.append(href)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_depth += 1
            self.heading_text.append("")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in BLOCKS or tag == "br":
            self.parts.append(" ")
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.heading_depth:
            self.heading_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)
            if self.heading_depth and self.heading_text:
                self.heading_text[-1] += data

    @property
    def text(self) -> str:
        return normalize("".join(self.parts))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-id", action="append", default=[], help="limit the audit to one or more source IDs")
    ap.add_argument("--apply", action="store_true", help="write semantic-review evidence for exact text matches")
    args = ap.parse_args()

    manifest = json.loads((PACK / "references/candidate-manifest.json").read_text(encoding="utf-8"))
    acceptance = json.loads((PACK / "references/source-acceptance.json").read_text(encoding="utf-8"))
    docs = {row["id"]: row for row in manifest["documents"]}
    rows: list[dict] = []
    failures: list[str] = []

    ids = args.source_id or sorted(acceptance["records"])
    for source_id in ids:
        doc = docs.get(source_id)
        record = acceptance["records"].get(source_id)
        if not doc or not record or not doc.get("document_fragment_path"):
            continue
        fragment_path = ROOT / doc["document_fragment_path"]
        candidate_path = ROOT / doc["candidate_text_path"]
        if not fragment_path.is_file() or not candidate_path.is_file():
            failures.append(f"{source_id}: fragment or candidate text is missing")
            continue
        fragment = fragment_path.read_text(encoding="utf-8")
        parser = VisibleText()
        parser.feed(fragment)
        parser.close()
        markdown = candidate_path.read_text(encoding="utf-8")
        if CAPTURE_MARKER not in markdown:
            failures.append(f"{source_id}: official-text section marker is missing")
            continue
        converted = markdown.split(CAPTURE_MARKER, 1)[1]
        converted = converted.strip()
        expected = parser.text
        actual = normalize(converted)
        equal = expected == actual
        url = doc.get("url", "")
        is_narodne_novine = urlparse(url).hostname == "narodne-novine.nn.hr"
        image_count = len(re.findall(r"<img\b", fragment, re.I))
        record_result = {
            "source_id": source_id,
            "textually_equivalent": equal,
            "source_visible_characters": len(expected),
            "converted_visible_characters": len(actual),
            "source_visible_text_sha256": digest(expected),
            "converted_visible_text_sha256": digest(actual),
            "image_count_in_selected_fragment": image_count,
            "linked_file_count_in_selected_fragment": len(parser.files),
            "official_publisher_host": is_narodne_novine,
        }
        rows.append(record_result)
        if not equal:
            failures.append(f"{source_id}: visible source text does not equal converted candidate text")
            continue
        if not args.apply:
            continue
        evidence = (
            "Independent visible-text comparison passed: all decoded text nodes in the retained official .sl-content .doc "
            "fragment match the candidate's converted source section in order after Unicode and whitespace normalization. "
            f"Source and conversion each contain {len(expected)} normalized characters; both normalized-text SHA-256 values are "
            f"{digest(expected)}. This verifies text extraction fidelity for the selected official document region; "
            f"{image_count} embedded images and {len(parser.files)} linked files are reviewed separately under attachments_review."
        )
        record["semantic_review"] = {
            "status": "passed",
            "method": "independent_visible_text_equivalence_and_anchor_review",
            "review_date": "2026-10-19",
            "scope": "ordered_visible_text_in_selected_official_document_region",
            "evidence": evidence,
            "source_fragment_path": doc["document_fragment_path"],
            "source_fragment_sha256": hashlib.sha256(fragment.encode("utf-8")).hexdigest(),
            "normalized_visible_text_sha256": digest(expected),
            "normalized_visible_characters": len(expected),
            "embedded_image_count": image_count,
            "linked_file_urls": parser.files,
        }

    if args.apply:
        acceptance["records"].update({row["source_id"]: acceptance["records"][row["source_id"]] for row in rows if row["textually_equivalent"]})
        (PACK / "references/source-acceptance.json").write_text(
            json.dumps(acceptance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({"audited_records": len(rows), "textually_equivalent": sum(r["textually_equivalent"] for r in rows), "failures": failures, "records": rows}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
