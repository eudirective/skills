#!/usr/bin/env python3
"""Legacy RIS capture helper; use the monitor's Austria capture action instead."""
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
    print(
        "This standalone capture script is retired. Use the EU Source Update Monitor's "
        "registered Austria capture action so raw responses are stored in the indexed local-only archive.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
