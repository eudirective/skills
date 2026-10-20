#!/usr/bin/env python3
"""Convert saved Finlex rendered-text captures into review-candidate Markdown."""
from __future__ import annotations
import hashlib
import io
import json
import logging
import os
import re
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape as html_unescape
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
CAPTURE_LIST = PACK / "references" / "finlex-captures.json"
OUTPUT_MANIFEST = PACK / "references" / "finlex-retrieval-manifest.json"
AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
FINLEX_NS = "http://data.finlex.fi/schema/finlex"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ").replace("\u2009", " ")).strip()


def extract(text: str, record: dict) -> tuple[str, str]:
    lines = text.splitlines()
    eli = next((clean(line) for line in lines if "data.finlex.fi/eli/sd/" in line and "ajantasa/" in line), None)
    if not eli:
        raise ValueError("rendered page has no current ELI identifier")
    if record["eli_work_fragment"] not in eli:
        raise ValueError(f"ELI identifier {eli!r} does not match expected work {record['eli_work_fragment']!r}")
    start = next((i for i, line in enumerate(lines) if clean(line) == record.get("body_start", "Eduskunnan päätöksen mukaisesti säädetään:")), None)
    if start is None:
        raise ValueError("could not find the expected start of the consolidated law text")
    end = next((i for i in range(len(lines) - 1, start, -1) if clean(lines[i]) == "Sivun alkuun"), len(lines))
    body = [clean(line) for line in lines[start:end]]
    while body and not body[-1]:
        body.pop()
    if len(body) < 20 or record["act_number"] not in text:
        raise ValueError("captured page is too short or lacks the expected act number")
    return eli, markdown_body(body)


def markdown_body(lines: list[str]) -> str:
    output: list[str] = []
    i = 0
    chapter = re.compile(r"^\d+(?:\s+[a-z])?\s+luku$", re.IGNORECASE)
    article = re.compile(r"^\d+\s*[a-z]?\s*§$", re.IGNORECASE)
    while i < len(lines):
        line = lines[i]
        if not line:
            if output and output[-1] != "":
                output.append("")
            i += 1
            continue
        if chapter.match(line):
            title = ""
            j = i + 1
            while j < len(lines) and not lines[j]:
                j += 1
            if j < len(lines) and not article.match(lines[j]) and len(lines[j]) < 180:
                title = lines[j]
                i = j
            output.append(f"## {line}" + (f" — {title}" if title else ""))
            output.append("")
        elif article.match(line):
            title = ""
            j = i + 1
            while j < len(lines) and not lines[j]:
                j += 1
            if j < len(lines) and not article.match(lines[j]) and not chapter.match(lines[j]) and len(lines[j]) < 180:
                title = lines[j]
                i = j
            output.append(f"### {line}" + (f" — {title}" if title else ""))
            output.append("")
        else:
            output.append(line)
        i += 1
    while output and not output[-1]:
        output.pop()
    return "\n".join(output) + "\n"


def render(record: dict, html_bytes: bytes, text_bytes: bytes) -> tuple[bytes, dict]:
    text = text_bytes.decode("utf-8")
    eli, body = extract(text, record)
    retrieved_at = record.get("retrieved_at")
    if not retrieved_at:
        raise ValueError(f"{record['id']}: capture descriptor must pin retrieved_at for reproducible conversion")
    content = (
        f"# {record['title']}\n\n"
        f"- Jurisdiction: Finland\n"
        f"- Publisher: Finlex, Legal Register Centre\n"
        f"- Act: `{record['act_number']}` ({record['language']})\n"
        f"- Official current-text page: {record['page_url']}\n"
        f"- Current ELI version shown by Finlex: {eli}\n"
        f"- Retrieved: {retrieved_at}\n"
        f"- Extraction: rendered text from the Finlex `main` landmark; portal navigation and table of contents removed\n"
        f"- Open-data API attempt: {record.get('api_attempt', 'not attempted')}\n\n"
        f"> **Review candidate.** The saved text is the current Finlex consolidation identified by the ELI version above. It has not been accepted into the trusted legal corpus; compare the authoritative publication and assess amendments and effective dates before legal reliance.\n>\n"
        f"> **Attribution:** Based on Finlex data, made available under CC BY 4.0.\n\n"
        f"## Consolidated statutory text\n\n"
        f"{body}"
    )
    converted = content.encode("utf-8")
    metadata = {
        **record,
        "current_eli": eli,
        "retrieved_at": retrieved_at,
        "raw_html_sha256": sha256(html_bytes),
        "raw_html_bytes": len(html_bytes),
        "rendered_text_sha256": sha256(text_bytes),
        "rendered_text_bytes": len(text_bytes),
        "converted_sha256": sha256(converted),
        "converted_bytes": len(converted),
        "retrieval_status": "converted_review_candidate",
        "accepted": False,
    }
    return converted, metadata


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def normalized_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return clean("".join(element.itertext()))


def akn_text_nodes(element: ET.Element) -> list[str]:
    """Convert a bounded, identity-checked Finlex AKN statute body to text."""
    output: list[str] = []
    for child in element:
        tag = local_name(child)
        if tag in {"chapter", "section"}:
            number = normalized_text(child.find(f"{{{AKN_NS}}}num"))
            heading = normalized_text(child.find(f"{{{AKN_NS}}}heading"))
            level = "##" if tag == "chapter" else "###"
            title = f"{number} — {heading}" if number and heading else number or heading
            output.append(f"{level} {title}".rstrip())
            inner = [part for part in akn_text_nodes(child) if part]
            if inner:
                output.extend(["", *inner])
            output.append("")
        elif tag == "paragraph":
            number = normalized_text(child.find(f"{{{AKN_NS}}}num"))
            body = [part for part in akn_text_nodes(child) if part]
            rendered = " ".join(body)
            output.append((f"{number} {rendered}" if number else rendered).strip())
        elif tag == "hcontainer":
            if child.attrib.get("name") != "noteAuthorial":
                raise ValueError(f"unexpected Akoma Ntoso container: {child.attrib.get('name')!r}")
            note = " ".join(part for part in akn_text_nodes(child) if part)
            if note:
                output.extend(["### Finlex editorial note", "", note, ""])
        elif tag in {"num", "heading"}:
            # Consumed with the parent chapter/section/paragraph.
            continue
        elif tag in {"content", "subsection", "intro", "wrapUp", "p", "blockList", "item"}:
            if tag == "p":
                text = normalized_text(child)
                if text:
                    output.append(text)
            else:
                output.extend(akn_text_nodes(child))
        elif tag in {"i", "ref", "b", "u", "span", "br"}:
            text = normalized_text(child)
            if text:
                output.append(text)
        else:
            raise ValueError(f"unsupported Akoma Ntoso element in statute body: {tag}")
    return output


def render_akn(record: dict, xml_bytes: bytes) -> tuple[bytes, dict]:
    root = ET.fromstring(xml_bytes)
    act = root.find(f"{{{AKN_NS}}}act")
    if act is None:
        raise ValueError("Finlex response has no Akoma Ntoso act element")
    work = act.find(f"{{{AKN_NS}}}meta/{{{AKN_NS}}}identification/{{{AKN_NS}}}FRBRWork")
    expression = act.find(f"{{{AKN_NS}}}meta/{{{AKN_NS}}}identification/{{{AKN_NS}}}FRBRExpression")
    manifestation = act.find(f"{{{AKN_NS}}}meta/{{{AKN_NS}}}identification/{{{AKN_NS}}}FRBRManifestation")
    if work is None or expression is None or manifestation is None:
        raise ValueError("Finlex response is missing FRBR work, expression, or manifestation metadata")
    work_data = {child.tag.rsplit("}", 1)[-1]: child.attrib for child in work}
    expression_data = {child.tag.rsplit("}", 1)[-1]: child.attrib for child in expression}
    manifestation_data = {child.tag.rsplit("}", 1)[-1]: child.attrib for child in manifestation}
    number = work_data.get("FRBRnumber", {}).get("value")
    subtype = work_data.get("FRBRsubtype", {}).get("value")
    country = work_data.get("FRBRcountry", {}).get("value")
    language = expression_data.get("FRBRlanguage", {}).get("language")
    expression_uri = expression_data.get("FRBRuri", {}).get("value")
    expression_eli = next((a.attrib["value"] for a in expression.findall(f"{{{AKN_NS}}}FRBRalias") if a.attrib.get("name") == "eli"), "")
    date_consolidated = next((d.attrib["date"] for d in expression.findall(f"{{{AKN_NS}}}FRBRdate") if d.attrib.get("name") == "dateConsolidated"), "")
    date_produced = next((d.attrib["date"] for d in manifestation.findall(f"{{{AKN_NS}}}FRBRdate") if d.attrib.get("name") == "dateProduced"), "")
    doc_number = normalized_text(act.find(f"{{{AKN_NS}}}preface/{{{AKN_NS}}}p/{{{AKN_NS}}}docNumber"))
    doc_title = normalized_text(act.find(f"{{{AKN_NS}}}preface/{{{AKN_NS}}}p/{{{AKN_NS}}}docTitle"))
    in_force = act.find(f"{{{AKN_NS}}}meta/{{{AKN_NS}}}proprietary/{{{FINLEX_NS}}}isInForce")
    expected = record["expected_identity"]
    if (number, subtype, country, language, doc_number) != (
        expected["number"], expected["subtype"], expected["country"], expected["language"], expected["doc_number"]
    ):
        raise ValueError(f"Finlex AKN identity mismatch: {number=}, {subtype=}, {country=}, {language=}, {doc_number=}")
    if expression_uri != expected["expression_uri"]:
        raise ValueError(f"unexpected Finlex expression URI: {expression_uri!r}")
    if not date_consolidated or not date_produced or in_force is None or in_force.attrib.get("value") != "true":
        raise ValueError("Finlex metadata lacks a consolidation date, production date, or in-force confirmation")
    if expected.get("expected_title") and doc_title != expected["expected_title"]:
        raise ValueError(f"Finlex title mismatch: {doc_title!r}")
    wrapper = act.find(f".//{{{AKN_NS}}}hcontainer[@name='statuteProvisionsWrapper']")
    if wrapper is None:
        raise ValueError("Finlex AKN response has no statuteProvisionsWrapper")
    chapters = wrapper.findall(f"{{{AKN_NS}}}chapter")
    sections = wrapper.findall(f".//{{{AKN_NS}}}section")
    if len(chapters) < expected.get("min_chapters", 1) or len(sections) < expected.get("min_sections", 1):
        raise ValueError(f"Finlex AKN body is incomplete: {len(chapters)} chapters, {len(sections)} sections")
    rendered_nodes = [part for part in akn_text_nodes(wrapper) if part]
    body = "\n\n".join(rendered_nodes).strip()
    if len(body) < expected.get("min_body_chars", 10000):
        raise ValueError(f"Finlex AKN body is unexpectedly short: {len(body)} characters")
    preamble = normalized_text(act.find(f"{{{AKN_NS}}}preamble"))
    eli_work = expected.get("eli_work")
    if not eli_work:
        parts = record["act_number"].split("/")
        eli_work = "/".join(reversed(parts)) if len(parts) == 2 else record["act_number"]
    as_of_eli = f"http://data.finlex.fi/eli/sd/{eli_work}/ajantasa/{date_consolidated}/{language}"
    retrieved_at = record["retrieved_at"]
    caution = expected.get("version_caution", "")
    content = (
        f"# {record['title']}\n\n"
        f"- Jurisdiction: Finland\n"
        f"- Publisher: Finlex, Legal Register Centre\n"
        f"- Act: `{doc_number}` ({language})\n"
        f"- Official current-law page: {record['page_url']}\n"
        f"- Official Finlex API record: {record['api_url']}\n"
        f"- Finlex ELI using the API-reported consolidation date: {as_of_eli}\n"
        f"- Expression ELI reported by the API: {expression_eli}\n"
        f"- Consolidation date: {date_consolidated}; XML production date: {date_produced}\n"
        f"- Retrieved: {retrieved_at}\n"
        f"- In force according to Finlex metadata: yes\n"
        f"- Conversion: Finlex Akoma Ntoso XML `statuteProvisionsWrapper`, preserving chapter/section headings and numbered paragraphs\n\n"
        f"> **Review candidate.** This conversion is not accepted into the trusted legal corpus. {caution} Compare the version metadata and amendment chain with the official current-text page before legal reliance.\n>\n"
        f"> **Attribution:** Based on Finlex open data, made available under CC BY 4.0.\n\n"
        f"## Enacting formula\n\n{preamble}\n\n"
        f"## Consolidated statutory text\n\n{body}\n"
    )
    converted = content.encode("utf-8")
    metadata = {
        **record,
        "current_eli": as_of_eli,
        "expression_eli": expression_eli,
        "date_consolidated": date_consolidated,
        "date_produced": date_produced,
        "source_title": doc_title,
        "chapter_count": len(chapters),
        "section_count": len(sections),
        "converted_sha256": sha256(converted),
        "converted_bytes": len(converted),
        "raw_xml_sha256": sha256(xml_bytes),
        "raw_xml_bytes": len(xml_bytes),
        "retrieval_status": "converted_review_candidate",
        "accepted": False,
    }
    return converted, metadata


def render_pdf(record: dict, pdf_bytes: bytes) -> tuple[bytes, dict]:
    try:
        from pypdf import PdfReader, __version__ as pypdf_version
    except ImportError as exc:
        raise RuntimeError("install the pinned PDF converter with `python3 -m pip install -r requirements.txt`") from exc
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("Finlex translation response does not have a PDF signature")
    previous_logging_disable = logging.root.manager.disable
    logging.disable(logging.WARNING)
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes), strict=True)
        expected = record["expected_identity"]
        if len(reader.pages) != expected["page_count"]:
            raise ValueError(f"Finlex translation page count changed: expected {expected['page_count']}, got {len(reader.pages)}")
        pages = [(page.extract_text() or "").replace("\r\n", "\n").replace("\r", "\n").strip() for page in reader.pages]
    finally:
        logging.disable(previous_logging_disable)
    empty_pages = [index + 1 for index, page in enumerate(pages) if not page]
    if empty_pages:
        raise ValueError("PDF text extraction left empty pages; OCR/review required: " + ", ".join(map(str, empty_pages[:20])))
    extracted = "\n\n".join(pages).strip() + "\n"
    normalized = extracted.casefold()
    missing = [marker for marker in expected["markers"] if marker.casefold() not in normalized]
    if missing:
        raise ValueError("Finlex translation identity markers missing: " + "; ".join(missing))
    extracted_bytes = extracted.encode("utf-8")
    completed = record["completed_date"]
    cutoff = record["amendment_cutoff"]
    content = (
        f"# {record['title']}\n\n"
        f"- Jurisdiction: Finland\n"
        f"- Publisher: Finlex; translation published by {record['publisher']}\n"
        f"- Act: `{record['act_number']}`\n"
        f"- Language: English (unofficial translation)\n"
        f"- Official translation-history page: {record['translation_page_url']}\n"
        f"- Official PDF link discovered from that page: {record['pdf_url']}\n"
        f"- Translation completed: {completed}\n"
        f"- Amendments tracked through: {cutoff}\n"
        f"- Retrieved: {record['retrieved_at']}\n"
        f"- PDF pages: {len(pages)}; empty extracted pages: 0\n"
        f"- Converter: pypdf {pypdf_version}; pages retained in publisher order\n"
        f"- Source PDF SHA-256: {sha256(pdf_bytes)}\n"
        f"- Extracted text SHA-256: {sha256(extracted_bytes)}\n\n"
        f"> **Review candidate.** Finlex labels this as an unofficial translation and states that only Finnish and Swedish are legally binding. This English text tracks amendments only through {cutoff}; it is not a current English consolidation.\n>\n"
        f"> **Attribution:** Based on Finlex open data, made available under CC BY 4.0.\n\n"
        f"## English translation text\n\n{extracted}"
    )
    converted = content.encode("utf-8")
    metadata = {
        **record,
        "pypdf_version": pypdf_version,
        "page_count": len(pages),
        "empty_page_count": 0,
        "extracted_text_sha256": sha256(extracted_bytes),
        "extracted_text_bytes": len(extracted_bytes),
        "raw_pdf_sha256": sha256(pdf_bytes),
        "raw_pdf_bytes": len(pdf_bytes),
        "converted_sha256": sha256(converted),
        "converted_bytes": len(converted),
        "retrieval_status": "converted_review_candidate",
        "accepted": False,
    }
    return converted, metadata


def update_inventories(record: dict) -> None:
    paths = [PACK / "references" / "candidate-manifest.json", PACK / "references" / "source-catalog.json"]
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("documents", data.get("sources", []))
        for item in entries:
            if item.get("id") == record["id"]:
                item["retrieved"] = True
                item["accepted"] = False
                item["retrieval_status"] = "converted_review_candidate"
                item["retrieval_shape"] = record.get("retrieval_shape", "Finlex current-text HTML page, rendered main-content capture")
                if record.get("current_eli"):
                    identity = record.get("act_number", "") + "; current ELI: " + record["current_eli"]
                else:
                    identity = record.get("act_number", "") + "; unofficial English translation; amendments through " + record.get("amendment_cutoff", "unknown")
                item["publisher_identifier"]["record"] = identity
                item["verification_status"] = record.get("verification_note", "Official Finlex current-text page captured; Finlex API route returned 404 for this record; stable ELI current-version identity retained.")
                item["document_path"] = "../candidates/" + record["output_path"].split("/")[-1]
                item["raw_capture_path"] = record.get("raw_pdf_path", record.get("raw_xml_path", record.get("rendered_text_path")))
                break
        data["accepted_source_count"] = 0
        data["retrieved_review_candidate_count"] = sum("review_candidate" in item.get("retrieval_status", "") for item in entries)
        atomic_write(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sync_api() -> None:
    captures = json.loads(CAPTURE_LIST.read_text(encoding="utf-8"))
    api_records = [record for record in captures["records"] if record.get("retrieval_method") == "finlex_akn_api"]
    if not api_records:
        raise SystemExit("no Finlex API records are configured")
    allowed_hosts = {"opendata.finlex.fi", "avoindata.finlex.fi"}

    class CheckedRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            target = urllib.parse.urljoin(req.full_url, newurl)
            parsed = urllib.parse.urlsplit(target)
            if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
                raise urllib.error.URLError(f"refused redirect outside Finlex API hosts: {target}")
            return super().redirect_request(req, fp, code, msg, headers, target)

    tls_context = ssl.create_default_context()
    tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=tls_context), CheckedRedirect())
    fetched: list[tuple[dict, bytes, str, str]] = []
    errors: list[str] = []
    for index, record in enumerate(api_records):
        if index:
            time.sleep(1.0)
        parsed = urllib.parse.urlsplit(record["api_url"])
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            errors.append(f"{record['id']}: configured API URL is outside the Finlex host allowlist")
            continue
        request = urllib.request.Request(record["api_url"], headers={
            "User-Agent": "eudirective-public-data/1.0 (Finlex open-data retrieval)",
            "Accept": "application/xml",
        })
        try:
            with opener.open(request, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "")
                if "application/xml" not in content_type.lower() and "text/xml" not in content_type.lower():
                    raise ValueError(f"unexpected content type: {content_type or '(missing)'}")
                declared = response.headers.get("Content-Length")
                if declared and int(declared) > 12 * 1024 * 1024:
                    raise ValueError("response exceeds 12 MiB cap")
                body = response.read(12 * 1024 * 1024 + 1)
                if len(body) > 12 * 1024 * 1024:
                    raise ValueError("response exceeds 12 MiB cap")
                if not body:
                    raise ValueError("empty response")
                render_akn(record, body)  # Fail closed on mismatched work/language or incomplete statutory body.
                fetched.append((record, body, response.geturl(), content_type))
        except urllib.error.HTTPError as exc:
            errors.append(f"{record['id']}: HTTP {exc.code}; no retry was attempted")
        except Exception as exc:
            errors.append(f"{record['id']}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for record, body, response_url, content_type in fetched:
        digest = sha256(body)
        stem = re.sub(r"[^a-z0-9]+", "-", record["id"].lower()).strip("-")
        relative_path = f"temp/finland/raw/{stem}-{digest}.xml"
        output = (ROOT / relative_path).resolve()
        if not output.is_relative_to(ROOT):
            raise SystemExit(f"refused output path outside project root: {relative_path}")
        if output.exists() and sha256(output.read_bytes()) != digest:
            raise SystemExit(f"hash-named raw snapshot has conflicting content: {relative_path}")
        if not output.exists():
            atomic_write(output, body)
        record["raw_xml_path"] = relative_path
        if record.get("raw_xml_sha256") != digest:
            record["retrieved_at"] = now
        record["last_checked_at"] = now
        record["retrieved_bytes"] = len(body)
        record["response_content_type"] = content_type
        record["response_url"] = response_url
        record["raw_xml_sha256"] = digest
        print(f"saved {record['id']} {digest} ({len(body)} bytes)")
    atomic_write(CAPTURE_LIST, (json.dumps(captures, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sync_pdfs() -> None:
    captures = json.loads(CAPTURE_LIST.read_text(encoding="utf-8"))
    pdf_records = [record for record in captures["records"] if record.get("retrieval_method") == "finlex_translation_pdf"]
    if not pdf_records:
        raise SystemExit("no Finlex translation PDFs are configured")
    allowed_hosts = {"www.finlex.fi", "finlex.fi"}

    class CheckedRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            target = urllib.parse.urljoin(req.full_url, newurl)
            parsed = urllib.parse.urlsplit(target)
            if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
                raise urllib.error.URLError(f"refused redirect outside Finlex hosts: {target}")
            return super().redirect_request(req, fp, code, msg, headers, target)

    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context), CheckedRedirect())

    def fetch(url: str, accept: str, max_bytes: int) -> tuple[bytes, str, str]:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            raise ValueError(f"refused non-Finlex HTTPS URL: {url}")
        request = urllib.request.Request(url, headers={
            "User-Agent": "eudirective-public-data/1.0 (Finlex public legal text retrieval)",
            "Accept": accept,
        })
        with opener.open(request, timeout=30) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if response.status != 200 or final.scheme != "https" or final.hostname not in allowed_hosts:
                raise ValueError(f"unexpected final response: HTTP {response.status} {response.geturl()}")
            content_type = response.headers.get("Content-Type", "")
            if accept == "application/pdf" and "application/pdf" not in content_type.lower():
                raise ValueError(f"unexpected PDF content type: {content_type or '(missing)'}")
            if accept == "text/html" and "text/html" not in content_type.lower():
                raise ValueError(f"unexpected HTML content type: {content_type or '(missing)'}")
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                raise ValueError(f"response exceeds {max_bytes}-byte cap")
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError(f"response exceeds {max_bytes}-byte cap")
            if not data:
                raise ValueError("empty response")
            return data, response.geturl(), content_type

    fetched: list[tuple[dict, bytes, str, str, bytes, str, str]] = []
    errors: list[str] = []
    for index, record in enumerate(pdf_records):
        try:
            page_bytes, final_page_url, page_type = fetch(record["translation_page_url"], "text/html", 12 * 1024 * 1024)
            page_text = page_bytes.decode("utf-8")
            visible = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", " ", page_text, flags=re.IGNORECASE)
            visible = re.sub(r"<style\b[^>]*>[\s\S]*?</style>", " ", visible, flags=re.IGNORECASE)
            visible = re.sub(r"\s*/\s*", "/", clean(re.sub(r"<[^>]+>", " ", visible)))
            expected = record["expected_identity"]
            if expected["publisher_title"].casefold() not in visible.casefold():
                raise ValueError("translation parent page title did not match the expected act")
            if expected["amendment_cutoff_display"] not in visible:
                raise ValueError("translation parent page amendment cutoff changed")
            if expected["completion_iso"] not in page_text:
                raise ValueError("translation parent page completion date changed")
            link_matches = re.findall(
                r'href="([^"]*/api/media/statute-foreign-language-translation/\d+/mainPdf/main\.pdf\?timestamp=[^"]+)"',
                page_text,
                flags=re.IGNORECASE,
            )
            link_matches = list(dict.fromkeys(html_unescape(href) for href in link_matches))
            if len(link_matches) != 1:
                raise ValueError(f"expected one current English PDF link on the translation page, found {len(link_matches)}")
            pdf_url = urllib.parse.urljoin(final_page_url, link_matches[0])
            anchor_position = page_text.find(link_matches[0])
            if "English, pdf-file" not in page_text[max(0, anchor_position - 500):anchor_position + 300]:
                raise ValueError("discovered PDF link is not labelled as the English translation")
            if index:
                time.sleep(1.0)
            pdf_bytes, final_pdf_url, pdf_type = fetch(pdf_url, "application/pdf", 30 * 1024 * 1024)
            if not pdf_bytes.startswith(b"%PDF-"):
                raise ValueError("Finlex translation response lacks the PDF signature")
            updated = dict(record)
            updated.update({"pdf_url": final_pdf_url, "translation_page_final_url": final_page_url})
            render_pdf(updated, pdf_bytes)  # Validate title, cutoff, page count, and text before retaining the new file.
            fetched.append((record, page_bytes, final_page_url, page_type, pdf_bytes, final_pdf_url, pdf_type))
            if index + 1 < len(pdf_records):
                time.sleep(1.0)
        except Exception as exc:
            errors.append(f"{record['id']}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for record, page_bytes, final_page_url, page_type, pdf_bytes, final_pdf_url, pdf_type in fetched:
        page_hash, pdf_hash = sha256(page_bytes), sha256(pdf_bytes)
        stem = re.sub(r"[^a-z0-9]+", "-", record["id"].lower()).strip("-")
        page_path = f"temp/finland/raw/{stem}-page-{page_hash}.html"
        pdf_path = f"temp/finland/raw/{stem}-{pdf_hash}.pdf"
        for relative_path, data, digest in ((page_path, page_bytes, page_hash), (pdf_path, pdf_bytes, pdf_hash)):
            output = (ROOT / relative_path).resolve()
            if not output.is_relative_to(ROOT):
                raise SystemExit(f"refused output path outside project root: {relative_path}")
            if output.exists() and sha256(output.read_bytes()) != digest:
                raise SystemExit(f"hash-named raw snapshot has conflicting content: {relative_path}")
            if not output.exists():
                atomic_write(output, data)
        if record.get("raw_pdf_sha256") != pdf_hash:
            record["retrieved_at"] = now
        record.update({
            "translation_page_final_url": final_page_url,
            "translation_page_capture_path": page_path,
            "translation_page_sha256": page_hash,
            "translation_page_bytes": len(page_bytes),
            "translation_page_content_type": page_type,
            "pdf_url": final_pdf_url,
            "pdf_content_type": pdf_type,
            "raw_pdf_path": pdf_path,
            "raw_pdf_sha256": pdf_hash,
            "retrieved_bytes": len(pdf_bytes),
            "last_checked_at": now,
        })
        print(f"saved {record['id']} pdf={pdf_hash} page={page_hash} ({len(pdf_bytes)} bytes)")
    atomic_write(CAPTURE_LIST, (json.dumps(captures, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def run(mode: str) -> None:
    records = json.loads(CAPTURE_LIST.read_text(encoding="utf-8"))["records"]
    previous_manifest = json.loads(OUTPUT_MANIFEST.read_text(encoding="utf-8")) if OUTPUT_MANIFEST.exists() else {"records": []}
    previous_by_id = {item["id"]: item for item in previous_manifest.get("records", [])}
    manifest_records = []
    errors = []
    for record in records:
        try:
            if record.get("retrieval_method") == "finlex_akn_api":
                raw_bytes = (ROOT / record["raw_xml_path"]).read_bytes()
                converted, metadata = render_akn(record, raw_bytes)
            elif record.get("retrieval_method") == "finlex_translation_pdf":
                raw_bytes = (ROOT / record["raw_pdf_path"]).read_bytes()
                converted, metadata = render_pdf(record, raw_bytes)
            else:
                html_bytes = (ROOT / record["raw_html_path"]).read_bytes()
                text_bytes = (ROOT / record["rendered_text_path"]).read_bytes()
                raw_bytes = html_bytes
                converted, metadata = render(record, html_bytes, text_bytes)
            out = ROOT / record["output_path"]
            if mode == "verify":
                expected = previous_by_id.get(record["id"])
                if not expected:
                    raise ValueError("record is absent from retrieval manifest")
                checks = {"converted Markdown": (sha256(converted), expected.get("converted_sha256")),
                          "saved Markdown": (sha256(out.read_bytes()), expected.get("converted_sha256"))}
                if record.get("retrieval_method") == "finlex_akn_api":
                    checks["raw XML"] = (sha256(raw_bytes), expected.get("raw_xml_sha256"))
                elif record.get("retrieval_method") == "finlex_translation_pdf":
                    checks["raw PDF"] = (sha256(raw_bytes), expected.get("raw_pdf_sha256"))
                    checks["extracted text"] = (metadata.get("extracted_text_sha256"), expected.get("extracted_text_sha256"))
                    checks["translation page capture"] = (
                        sha256((ROOT / record["translation_page_capture_path"]).read_bytes()),
                        expected.get("translation_page_sha256"),
                    )
                else:
                    checks["raw HTML"] = (sha256(raw_bytes), expected.get("raw_html_sha256"))
                    checks["rendered text"] = (sha256(text_bytes), expected.get("rendered_text_sha256"))
                failed = [name for name, (actual, wanted) in checks.items() if actual != wanted]
                if failed:
                    raise ValueError("hash/replay mismatch: " + ", ".join(failed))
                print(f"verified {record['id']} (source hashes and conversion replay)")
            else:
                atomic_write(out, converted)
                metadata["output_path"] = record["output_path"]
                manifest_records.append(metadata)
                update_inventories(metadata)
                print(f"converted {record['id']} -> {record['output_path']}")
        except Exception as exc:
            errors.append(f"{record.get('id', '<unknown>')}: {exc}")
    if mode == "verify":
        unknown = set(previous_by_id) - {r.get("id") for r in records}
        if unknown:
            errors.append("retrieval manifest contains records absent from capture list: " + ", ".join(sorted(unknown)))
    elif not errors:
        manifest = {
            "manifest_version": 1,
            "publisher": "Finlex / Legal Register Centre",
            "retrieval_method": "Per-record official Finlex Akoma Ntoso XML API or official current-text page captured through browser-rendered main content; raw responses are retained under project-root temp/.",
            "reuse_terms": "https://www.finlex.fi/en/data-protection",
            "records": manifest_records,
            "accepted_source_count": 0,
        }
        atomic_write(OUTPUT_MANIFEST, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if errors:
        raise SystemExit("\n".join(errors))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "convert"
    if mode not in {"sync-api", "sync-pdfs", "convert", "verify"}:
        raise SystemExit("usage: convert_finlex_capture.py [sync-api|sync-pdfs|convert|verify]")
    if mode == "sync-api":
        sync_api()
    elif mode == "sync-pdfs":
        sync_pdfs()
    else:
        run(mode)
