#!/usr/bin/env python3
"""Replay Austria's nine legacy page captures with scoped extractors."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
ROOT = PACK.parents[1]
sys.path.insert(0, str(PACK))
from scripts.local_capture_archive import resolve_capture  # noqa: E402
from sync_austria_sources import ScopedText  # noqa: E402
from scripts.convert_ris_capture import extract_text  # noqa: E402

MANIFEST_PATH = PACK / "references" / "candidate-manifest.json"
LEDGER_PATH = PACK / "references" / "capture-ledger.json"
RULE_VERSION = "at-main-ris-record-aware-v2"
LEGACY_IDS = {
    "at-guidance-family-card",
    "at-guidance-family-index",
    "at-dsb-complaint",
    "at-volksanwaltschaft-complaint",
    "at-lvwg-wien-2022-6086",
    "at-bmeia-visa",
    "at-bmeia-settlement-residence",
    "at-guidance-visa-application",
    "at-bmeia-representation-directory",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack_path(value: str) -> Path:
    archived = resolve_capture(value)
    if archived is not None:
        return archived
    if value.startswith("captures/"):
        return PACK / value
    path = ROOT / value
    if path.exists():
        return path
    prefix = "source-library/austria/"
    if value.startswith(prefix):
        return PACK / value[len(prefix):]
    return path


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


class BMEIADirectoryParser(HTMLParser):
    """Turn the BMEIA HTML table into country/representation records."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.country: dict | None = None
        self.current: dict | None = None
        self.heading_mode: str | None = None
        self.heading_text: list[str] = []
        self.category_text: list[str] = []
        self.in_category = False
        self.country_id = ""
        self.country_rows: list[dict] = []
        self.records: list[dict] = []
        self.countries: list[dict] = []
        self.date_text = ""
        self.table_depth = 0
        self.row: list[dict] | None = None
        self.cell: dict | None = None
        self.active_link: dict | None = None
        self.in_paragraph = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "h2" and (a.get("id") or "").startswith("country-"):
            self._finish_record()
            self._finish_country()
            self.heading_mode = "country"
            self.heading_text = []
            self.country_id = a.get("id") or ""
        elif tag == "h3":
            self._finish_record()
            self.heading_mode = "office"
            self.heading_text = []
            self.category_text = []
            self.in_category = False
            self.current = {"country_id": self.country_id, "country": self.country, "details": {}, "links": []}
        elif tag == "h1":
            self.heading_mode = "page_title"
            self.heading_text = []
        elif tag == "p":
            self.in_paragraph = True
            self.heading_text = []
        elif tag == "span" and self.heading_mode == "office" and "uppercase" in (a.get("class") or "").split():
            self.in_category = True
        elif tag == "table":
            self.table_depth += 1
        elif tag == "tr" and self.current and self.table_depth == 1:
            self.row = []
        elif tag == "td" and self.row is not None and self.table_depth == 1:
            self.cell = {"text": [], "links": []}
        elif tag == "a" and self.cell is not None and a.get("href"):
            self.active_link = {"url": a["href"], "text": []}
            self.cell["links"].append(self.active_link)
        elif tag == "br":
            if self.heading_mode:
                self.heading_text.append(" ")
            if self.cell is not None:
                self.cell["text"].append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self.active_link = None
        elif tag == "span":
            self.in_category = False
        elif tag == "td" and self.cell is not None and self.row is not None:
            self.cell["text"] = clean("".join(self.cell["text"]))
            for link in self.cell["links"]:
                link["text"] = clean("".join(link["text"]))
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.current and self.table_depth == 1 and len(self.row) >= 2:
                key = self.row[0]["text"].rstrip(":")
                value = self.row[1]["text"]
                if key:
                    self.current["details"][key] = value
                elif self.current["details"]:
                    previous = next(reversed(self.current["details"]))
                    self.current["details"][previous] = "; ".join(filter(None, [self.current["details"][previous], value]))
                else:
                    self.current["details"][f"field_{len(self.current['details']) + 1}"] = value
                for cell in self.row:
                    self.current["links"].extend(link for link in cell.get("links", []) if link.get("url"))
            self.row = None
        elif tag == "table" and self.table_depth:
            self.table_depth -= 1
        elif tag == "h2" and self.heading_mode == "country":
            title = clean("".join(self.heading_text))
            self.country = {"country_id": self.country_id, "name": title, "representation_count": 0}
            self.countries.append(self.country)
            self.heading_mode = None
            self.heading_text = []
        elif tag == "h3" and self.heading_mode == "office":
            title = clean("".join(self.heading_text))
            category = clean("".join(self.category_text))
            if self.current is not None:
                self.current["title"] = title
                self.current["category"] = category or None
            self.heading_mode = None
            self.heading_text = []
        elif tag == "h1" and self.heading_mode == "page_title":
            self.heading_mode = None
            self.heading_text = []
        elif tag == "p" and self.in_paragraph:
            text = clean("".join(self.heading_text))
            if re.match(r"^Stand\s", text, re.I):
                self.date_text = text
            self.in_paragraph = False
            if self.heading_mode is None:
                self.heading_text = []

    def handle_data(self, data: str) -> None:
        if self.heading_mode or self.in_paragraph:
            self.heading_text.append(data)
            if self.in_category:
                self.category_text.append(data)
        if self.cell is not None:
            self.cell["text"].append(data)
            if self.active_link is not None:
                self.active_link["text"].append(data)

    def _finish_record(self) -> None:
        if self.current and self.current.get("title"):
            self.current["links"] = list({(x["url"], x["text"]): x for x in self.current["links"]}.values())
            self.current["source_record_id"] = f"{self.current.get('country_id','country-unknown')}-{len(self.records)+1:04d}"
            self.records.append(self.current)
            if self.country is not None:
                self.country["representation_count"] += 1
        self.current = None

    def _finish_country(self) -> None:
        self._finish_record()

    def result(self) -> dict:
        self._finish_record()
        return {
            "schema_version": "1.0.0",
            "publisher": "Austrian Federal Ministry for European and International Affairs (BMEIA)",
            "source_url": "https://www.bmeia.gv.at/reports/oesterreichische-vertretungen-im-ausland",
            "directory_as_of": self.date_text,
            "captured_on": "2026-10-19",
            "country_count": len(self.countries),
            "representation_record_count": len(self.records),
            "record_key": ["country_id", "source_record_id"],
            "countries": self.countries,
            "representations": self.records,
        }


def render_record(record: dict, ledger_row: dict, content: str, structured_path: str | None = None) -> bytes:
    id_label = "Source ID" if record.get("accepted") else "Candidate ID"
    common = [
        f"# {record['title']}", "",
        "- Jurisdiction: Austria",
        f"- {id_label}: `{record['id']}`",
        f"- Source type: `{record.get('source_type')}`",
        f"- Official URL: {record['url']}",
        f"- Retrieved: {ledger_row.get('retrieved_at')}",
        f"- Selector: `{record.get('content_selector')}`",
        f"- Raw capture SHA-256: `{ledger_row.get('source_sha256')}`",
        f"- Replay rule: `{RULE_VERSION}`",
    ]
    if structured_path:
        common.extend([
            f"- Directory reference date: {record.get('directory_as_of')}",
            f"- Structured mission records: `{structured_path}`",
            f"- Country records: {record.get('directory_country_count')}; representation records: {record.get('directory_record_count')}",
        ])
    common.extend(["", "## Replayed source content", "", content, ""])
    return "\n".join(common).encode("utf-8")


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    records = {x["id"]: x for x in manifest["documents"]}
    ledger_rows = {x["candidate_id"]: x for x in ledger["records"]}
    if not LEGACY_IDS.issubset(records.keys() & ledger_rows.keys()):
        raise ValueError("legacy record set does not reconcile with manifest and capture ledger")

    directory_json_path = PACK / "references" / "bmeia-representation-records.json"
    out = []
    directory_counts = None
    for source_id in sorted(LEGACY_IDS):
        record, capture = records[source_id], ledger_rows[source_id]
        raw_path = pack_path(capture["raw_path"])
        raw = raw_path.read_bytes()
        if digest(raw) != capture.get("source_sha256"):
            raise ValueError(f"raw hash mismatch for {source_id}")
        html = raw.decode("utf-8", "replace")
        if source_id == "at-lvwg-wien-2022-6086":
            text, _links = extract_text(raw)
            selector = "div.contentBlock; excludes script/style/noscript and .sr-only accessibility-expanded duplicates"
            if len(text) < 1500:
                raise ValueError(f"replayed RIS decision unexpectedly short for {source_id}: {len(text)}")
            if "VGW-151/094/6086/2022" not in text:
                raise ValueError("replayed Vienna decision lacks its case-number anchor")
            content = text
            record["semantic_review_status"] = "replayed_hidden_accessibility_variants_excluded_case_identity_checked"
        elif source_id == "at-bmeia-representation-directory":
            parser = BMEIADirectoryParser()
            parser.feed(html)
            structured = parser.result()
            if not structured["directory_as_of"].startswith("Stand 19. Oktober 2026"):
                raise ValueError(f"unexpected directory as-of date: {structured['directory_as_of']}")
            if structured["country_count"] < 150 or structured["representation_record_count"] < 400:
                raise ValueError(f"structured directory seems incomplete: {structured['country_count']} countries / {structured['representation_record_count']} records")
            directory_json_path.write_text(json.dumps(structured, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            record["directory_as_of"] = structured["directory_as_of"]
            record["directory_country_count"] = structured["country_count"]
            record["directory_record_count"] = structured["representation_record_count"]
            record["directory_structured_path"] = "source-library/austria/references/bmeia-representation-records.json"
            selector = "h2#country-* / h3 representation heading / table row fields"
            content = (
                f"The official directory is represented as {structured['representation_record_count']} structured representation records across "
                f"{structured['country_count']} country headings. The date shown by the captured official page is **{structured['directory_as_of']}**. "
                "Each record preserves the country heading, representation heading/type, field/value rows, and links. See the linked JSON record set for the complete machine-readable entries."
            )
            directory_counts = (structured["country_count"], structured["representation_record_count"])
            record["semantic_review_status"] = "structured_country_mission_rows_and_page_date_checked"
        else:
            parser = ScopedText(source_id)
            parser.feed(html)
            content, selector = parser.result()
            if len(content) < 100:
                raise ValueError(f"scoped page extraction unexpectedly short for {source_id}")
            record["semantic_review_status"] = "publisher_main_region_replayed_and_heading_checked"

        record["content_selector"] = selector
        record["conversion_rule_version"] = RULE_VERSION
        output_value = record.get("candidate_text_path")
        if not output_value and record.get("retrieval_status") == "discovery_only":
            output_value = f"source-library/austria/documents/discovery/{source_id}.md"
            record["candidate_text_path"] = output_value
        if not output_value:
            raise ValueError(f"candidate path missing for {source_id}")
        output_path = pack_path(output_value)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if source_id == "at-bmeia-representation-directory":
            structured_rel = "source-library/austria/references/bmeia-representation-records.json"
            rendered = render_record(record, capture, content, structured_rel)
        else:
            rendered = render_record(record, capture, content)
        output_path.write_bytes(rendered)
        record["converted_sha256"] = digest(rendered)
        record["converted_bytes"] = len(rendered)
        prior_status = record.get("retrieval_status")
        if prior_status not in {"accepted_source", "discovery_only"}:
            record["retrieval_status"] = "converted_review_candidate"
        record["retrieved"] = True
        capture["candidate_text_path"] = output_value
        capture["converted_sha256"] = digest(rendered)
        capture["converted_bytes"] = len(rendered)
        capture["content_selector"] = selector
        capture["conversion_rule_version"] = RULE_VERSION
        if prior_status not in {"accepted_source", "discovery_only"}:
            capture["retrieval_status"] = "converted_review_candidate"
            capture["review_state"] = "semantic_replay_complete_acceptance_gate_pending"
        capture["semantic_review_status"] = record["semantic_review_status"]
        out.append({"source_id": source_id, "selector": selector, "text_chars": len(content), "output_bytes": len(rendered)})

    manifest["semantic_replay_rule_version"] = RULE_VERSION
    manifest["retrieved_review_candidate_count"] = sum(
        bool(x.get("retrieved")) and not x.get("accepted") and x.get("review_state") != "discovery_only"
        for x in manifest["documents"]
    )
    manifest["converted_review_candidate_count"] = sum(
        bool(x.get("retrieved")) and not x.get("accepted") and x.get("review_state") != "discovery_only"
        and bool(x.get("source_text_path") or x.get("candidate_text_path"))
        and not x.get("native_source_path") and x.get("source_type") != "official_form"
        for x in manifest["documents"]
    )
    ledger["semantic_replay_rule_version"] = RULE_VERSION
    ledger["semantic_replayed_legacy_ids"] = sorted(LEGACY_IDS)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"replayed": out, "directory_counts": directory_counts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
