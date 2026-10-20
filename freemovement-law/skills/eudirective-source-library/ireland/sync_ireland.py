#!/usr/bin/env python3
"""Acquire and convert the bounded Ireland source-candidate register."""
from __future__ import annotations

import hashlib
import html
import json
import re
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
REFS = PACK / "references"
CANDIDATES = REFS / "candidate-manifest.json"
RETRIEVAL = REFS / "ireland-retrieval-manifest.json"
USER_AGENT = "eudirective-source-library/1.0 (bounded legal-source retrieval; eudirective@proton.me)"
MAX_BYTES = 32 * 1024 * 1024
TIMEOUT = 30
PARENT_IDS = {"ie-20": "ie-18", "ie-21": "ie-18", "ie-32": "ie-19", "ie-40": "ie-39", "ie-45": "ie-44"}
SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "form", "iframe"}
STOP = {"and", "or", "the", "of", "for", "in", "on", "to", "a", "an", "by", "with", "from", "your", "official", "guidance", "page", "index", "source", "candidate", "ireland"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with open(fd, "wb", closefd=True) as stream:
            stream.write(data)
            stream.flush()
        Path(name).replace(path)
    finally:
        Path(name).unlink(missing_ok=True)


def load_candidates() -> tuple[dict, list[dict]]:
    obj = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    return obj, obj.get("documents", obj.get("sources", []))


def allowed_hosts(catalog: dict) -> set[str]:
    hosts = set(catalog.get("official_hosts", []))
    hosts.update(urllib.parse.urlparse(item.get("url", "")).hostname for item in catalog.get("documents", catalog.get("sources", [])))
    return {host.lower() for host in hosts if host}


class CaptureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.main_depth: int | None = None
        self.article_depth: int | None = None
        self.body_depth: int | None = None
        self.skip = 0
        self.title = []
        self.in_title = False
        self.lines: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.current_link: dict | None = None
        self.link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.depth += 1
        attrs_map = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "body" and self.body_depth is None:
            self.body_depth = self.depth
        if tag == "main" and self.main_depth is None:
            self.main_depth = self.depth
        if tag == "article" and self.article_depth is None:
            self.article_depth = self.depth
        if tag in SKIP_TAGS:
            self.skip += 1
        if tag == "a" and not self.skip:
            self.current_link = {"href": attrs_map.get("href", "") or ""}
            self.link_text = []
        if not self.skip and tag in {"p", "div", "section", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "br", "dt", "dd", "blockquote"}:
            self.lines.append("\n")
        if not self.skip and tag in {"td", "th"}:
            self.lines.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        if tag == "a" and self.current_link is not None:
            label = re.sub(r"\s+", " ", " ".join(self.link_text)).strip()
            if label:
                self.links.append((label, self.current_link["href"]))
            self.current_link = None
            self.link_text = []
        if not self.skip and tag in {"p", "div", "section", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "dt", "dd", "blockquote"}:
            self.lines.append("\n")
        if not self.skip and tag in {"td", "th"}:
            self.lines.append(" | ")
        if tag == "main" and self.main_depth == self.depth:
            self.main_depth = None
        if tag == "article" and self.article_depth == self.depth:
            self.article_depth = None
        if tag == "body" and self.body_depth == self.depth:
            self.body_depth = None
        self.depth = max(0, self.depth - 1)

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title.append(data)
        in_main = self.main_depth is not None
        in_article = self.article_depth is not None
        in_body = self.body_depth is not None
        if self.skip or not (in_main or in_article or in_body):
            return
        value = re.sub(r"\s+", " ", data).strip()
        if value:
            self.lines.append(value + " ")
            if self.current_link is not None:
                self.link_text.append(value)

    def text(self) -> str:
        text = "".join(self.lines)
        text = html.unescape(text).replace("\xa0", " ")
        lines = []
        for line in text.splitlines():
            line = re.sub(r"(?:\s*\|\s*){2,}", " | ", line)
            line = re.sub(r"[ \t]+", " ", line).strip().strip("|").strip()
            lines.append(line)
        output: list[str] = []
        for line in lines:
            if line and (not output or output[-1] != line):
                output.append(line)
            elif not line and output and output[-1] != "":
                output.append("")
        return "\n".join(output).strip() + "\n"


def validate_url(url: str, hosts: set[str]) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in hosts:
        raise ValueError(f"refused non-allowlisted URL: {url}")


def fetch(url: str, hosts: set[str]) -> tuple[bytes, str, str]:
    validate_url(url, hosts)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,application/octet-stream;q=0.8"})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as response:
        final_url = response.geturl()
        validate_url(final_url, hosts)
        content_type = response.headers.get_content_type().lower()
        parts: list[bytes] = []
        size = 0
        while True:
            chunk = response.read(min(64 * 1024, MAX_BYTES + 1 - size))
            if not chunk:
                break
            parts.append(chunk)
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError(f"response exceeds {MAX_BYTES} byte cap")
        return b"".join(parts), final_url, content_type


def discover_parent_pdf(record: dict, captures_by_id: dict[str, dict], records_by_id: dict[str, dict]) -> tuple[str, str]:
    parent_id = PARENT_IDS.get(record.get("id"))
    if not parent_id or parent_id not in captures_by_id:
        return record["url"], "no_parent_capture_used_manifest_url"
    parent = captures_by_id[parent_id]
    raw_path = ROOT / parent["raw_path"]
    parser = CaptureParser()
    try:
        parser.feed(raw_path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return record["url"], "parent_capture_unparseable_used_manifest_url"
    direct = urllib.parse.urlparse(record["url"])
    name = Path(urllib.parse.unquote(direct.path)).name.lower()
    keywords = [w for w in re.findall(r"[a-z0-9]+", record.get("title", "").lower()) if len(w) > 4 and w not in STOP]
    candidates = []
    for label, href in parser.links:
        absolute = urllib.parse.urljoin(parent.get("final_url", records_by_id[parent_id]["url"]), href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme != "https" or not parsed.path.lower().endswith(".pdf"):
            continue
        label_norm = (label + " " + parsed.path).lower()
        score = sum(1 for word in keywords if word in label_norm)
        if name and Path(parsed.path).name.lower() == name:
            score += 10
        candidates.append((score, absolute))
    if candidates:
        candidates.sort(reverse=True)
        if candidates[0][0] >= 2 and (len(candidates) == 1 or candidates[0][0] > candidates[1][0]):
            return candidates[0][1], f"rediscovered_from_parent_{parent_id}"
    return record["url"], f"parent_{parent_id}_did_not_expose_confident_pdf_link_used_manifest_url"


def significant_tokens(value: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", value.lower()) if len(w) >= 3 and w not in STOP}


def content_identity(record: dict, title: str, text: str) -> str:
    source_id = str(record.get("id", ""))
    combined = (title + "\n" + text).lower()
    required = {
        "ie-05": ["eli", "schema"],
        "ie-08": ["548", "2015"],
        "ie-09": ["445", "2021"],
        "ie-10": ["398", "2025"],
        "ie-13": ["41", "2001", "swiss"],
        "ie-14": ["728", "2020", "withdrawal agreement"],
        "ie-15": ["421", "2025"],
        "ie-20": ["eutr1", "eutr1a"],
        "ie-21": ["eutr1"],
        "ie-32": ["short-stay", "visa"],
        "ie-40": ["family reunification", "residency", "visas"],
        "ie-45": ["international protection", "legal aid"],
    }.get(source_id, [])
    missing = [marker for marker in required if marker.lower() not in combined]
    if missing:
        raise ValueError(f"candidate-specific content markers absent: {', '.join(missing)}")
    if required:
        return "candidate-specific content markers"
    tokens = significant_tokens(record.get("title", ""))
    overlap = tokens.intersection(significant_tokens(combined))
    if tokens and len(overlap) / len(tokens) >= 0.25:
        return "candidate-title token overlap"
    # ELI records frequently use punctuation/abbreviations that differ from the register title.
    identifiers = re.findall(r"(?:SI|S\.I\.?|Act|Order|HC)\s*(?:No\.?\s*)?(\d{1,4})\s*(?:/|of\s+)?\s*(\d{4})", record.get("title", ""), re.I)
    for number, year in identifiers:
        if number in combined and year in combined:
            return "instrument number and year"
    if len(text.strip()) < 60:
        raise ValueError("extracted text is too short to represent the candidate")
    if tokens and not overlap:
        raise ValueError(f"candidate title identity check failed for {source_id}: {record.get('title')}")
    return "candidate title partially corroborated"


def extract_payload(raw: bytes, content_type: str) -> tuple[str, str, dict]:
    if raw.startswith(b"%PDF-") or content_type == "application/pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF conversion requires pypdf; install source-library/ireland/requirements.txt") from exc
        reader = PdfReader(__import__("io").BytesIO(raw), strict=False)
        pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
        text = "\n\n".join(pages).strip() + "\n"
        return "pdf", text, {"page_count": len(reader.pages), "extracted_text_sha256": digest(text.encode("utf-8"))}
    decoded = raw.decode("utf-8", errors="replace")
    parser = CaptureParser()
    parser.feed(decoded)
    text = parser.text()
    if len(text.strip()) < 40:
        raise ValueError("HTML extraction produced too little body text")
    return "html", text, {"html_title": re.sub(r"\s+", " ", " ".join(parser.title)).strip(), "links_seen": len(parser.links)}


def sync() -> None:
    catalog, records = load_candidates()
    hosts = allowed_hosts(catalog)
    previous = json.loads(RETRIEVAL.read_text(encoding="utf-8")) if RETRIEVAL.exists() else {"records": []}
    prior = {item["id"]: item for item in previous.get("records", [])}
    results: list[dict] = []
    captures_by_id: dict[str, dict] = {}
    records_by_id = {item["id"]: item for item in records}
    for index, record in enumerate(records):
        item = dict(prior.get(record["id"], {}))
        item.update({"id": record["id"], "title": record["title"], "source_type": record.get("source_type"), "requested_url": record["url"], "accepted": False})
        try:
            url, rediscovery = discover_parent_pdf(record, captures_by_id, records_by_id) if record["url"].lower().endswith(".pdf") else (record["url"], "stable_record_url")
            raw, final_url, content_type = fetch(url, hosts)
            fmt, text, extract_meta = extract_payload(raw, content_type)
            identity = content_identity(record, extract_meta.get("html_title", ""), text)
            source_hash = digest(raw)
            stem = re.sub(r"[^a-z0-9]+", "-", record["id"].lower()).strip("-")
            relative = f"temp/ireland/raw/{stem}-{source_hash}.{'pdf' if fmt == 'pdf' else 'html'}"
            output = (ROOT / relative).resolve()
            if not output.is_relative_to(ROOT):
                raise ValueError("refused capture path outside project root")
            if not output.exists():
                atomic_write(output, raw)
            saved_time = item.get("retrieved_at") if item.get("source_sha256") == source_hash else datetime.now(timezone.utc).isoformat(timespec="seconds")
            item.update({
                "requested_url": url, "final_url": final_url, "link_rediscovery": rediscovery,
                "retrieved_at": saved_time, "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "http_status": 200, "content_type": content_type, "format": fmt,
                "bytes": len(raw), "source_sha256": source_hash, "raw_path": relative,
                "identity_check": identity, "extraction": extract_meta,
                "retrieval_status": "downloaded_ready_for_conversion", "error": None,
            })
            captures_by_id[record["id"]] = item
            print(f"downloaded {record['id']} {fmt} sha256={source_hash[:12]} ({len(raw)} bytes)")
        except urllib.error.HTTPError as exc:
            item.update({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "last_check_http_status": exc.code, "last_check_error": str(exc)})
            if item.get("converted_sha256") and item.get("raw_path"):
                item["retrieval_status"] = "converted_review_candidate"
                item["error"] = None
                print(f"retained prior capture {record['id']} after HTTP {exc.code}")
            else:
                item.update({"http_status": exc.code, "retrieval_status": "publisher_blocked_or_not_found", "error": str(exc)})
                print(f"unavailable {record['id']} HTTP {exc.code}")
        except Exception as exc:
            item.update({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "last_check_error": f"{type(exc).__name__}: {exc}"})
            if item.get("converted_sha256") and item.get("raw_path"):
                item["retrieval_status"] = "converted_review_candidate"
                print(f"retained prior capture {record['id']} after check error: {type(exc).__name__}: {exc}")
            else:
                item["retrieval_status"] = "retrieval_or_identity_review_required"
                item["error"] = f"{type(exc).__name__}: {exc}"
                print(f"review {record['id']}: {type(exc).__name__}: {exc}")
        results.append(item)
        if index + 1 < len(records):
            time.sleep(0.8)
    manifest = {
        "manifest_version": 1,
        "jurisdiction": "Ireland",
        "publisher_scope": "Per-record first-party URLs and redirect hosts allowlisted from the candidate manifest; candidate pages/PDFs only.",
        "reuse_terms": "https://www.irishstatutebook.ie/open-data.html (eISB PSI Open Data licence incorporating CC BY 4.0; other publishers retain their own terms)",
        "candidate_count": len(records),
        "accepted_source_count": 0,
        "records": results,
    }
    atomic_write(RETRIEVAL, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def convert_one(record: dict, capture: dict) -> tuple[bytes, dict]:
    raw = (ROOT / capture["raw_path"]).read_bytes()
    fmt, text, extract_meta = extract_payload(raw, capture["content_type"])
    identity = content_identity(record, extract_meta.get("html_title", ""), text)
    body = text.rstrip()
    warning = "The captured material is a source candidate. Record the official publisher, version date/cutoff, scope, and publisher terms; check only a known material later change relevant to the question. Do not reconstruct a complete amendment chain."
    if record.get("source_type") in {"national_legislation", "amending_legislation", "treaty_implementation_legislation", "withdrawal_agreement_legislation", "fee_legislation", "administrative_procedure_legislation", "privacy_legislation", "court_procedure_rules", "court_practice_direction"}:
        warning += " For legislation, use the latest government-published consolidated text where available. If this is the closest dated text, retain its cutoff and check only a specifically relevant later amendment or commencement."
    markdown = (
        f"# {record['title']}\n\n"
        f"- Jurisdiction: Ireland\n- Candidate ID: `{record['id']}`\n"
        f"- Source type: `{record.get('source_type', 'unspecified')}`\n"
        f"- Publisher URL: {record['url']}\n- Retrieved URL: {capture['final_url']}\n"
        f"- Retrieved: {capture['retrieved_at']}\n- Format: {fmt}; publisher content type `{capture['content_type']}`\n"
        f"- Source SHA-256: `{capture['source_sha256']}`\n- Identity check: {identity}\n"
        f"- PDF link discovery: {capture.get('link_rediscovery', 'not applicable')}\n\n"
        f"> **Review candidate.** {warning}\n\n"
        f"## Extracted source text\n\n{body}\n"
    ).encode("utf-8")
    metadata = {"id": record["id"], "output_path": f"source-library/ireland/candidates/{record['id']}.md", "converted_sha256": digest(markdown), "converted_bytes": len(markdown), "source_sha256": capture["source_sha256"], "identity_check": identity, "extraction": extract_meta, "retrieval_status": "converted_review_candidate", "accepted": False}
    return markdown, metadata


def process(mode: str) -> None:
    _, records = load_candidates()
    current = json.loads(RETRIEVAL.read_text(encoding="utf-8"))
    captured = {item["id"]: item for item in current.get("records", [])}
    outputs: list[dict] = []
    errors = []
    for record in records:
        item = captured.get(record["id"], {})
        if item.get("retrieval_status") not in {"downloaded_ready_for_conversion", "converted_review_candidate"}:
            continue
        try:
            markdown, result = convert_one(record, item)
            path = ROOT / result["output_path"]
            if mode == "verify":
                if item.get("converted_sha256") != result["converted_sha256"]:
                    raise ValueError("retrieval manifest conversion hash differs from deterministic replay")
                if digest(path.read_bytes()) != result["converted_sha256"]:
                    raise ValueError("saved Markdown differs from deterministic replay")
                if digest((ROOT / item["raw_path"]).read_bytes()) != item["source_sha256"]:
                    raise ValueError("saved raw source hash mismatch")
                print(f"verified {record['id']} source hash and conversion replay")
            else:
                atomic_write(path, markdown)
                item.update(result)
                outputs.append(item)
                print(f"converted {record['id']} -> {result['output_path']}")
        except Exception as exc:
            errors.append(f"{record['id']}: {type(exc).__name__}: {exc}")
    if mode == "convert":
        current["records"] = [captured.get(r["id"], {"id": r["id"], "title": r["title"], "retrieval_status": "not_downloaded"}) for r in records]
        current["converted_candidate_count"] = sum(1 for item in current["records"] if item.get("retrieval_status") == "converted_review_candidate")
        current["accepted_source_count"] = 0
        atomic_write(RETRIEVAL, (json.dumps(current, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        catalog, catalog_records = load_candidates()
        by_id = {item["id"]: item for item in current["records"]}
        for record in catalog_records:
            result = by_id.get(record["id"], {})
            record["retrieval_status"] = result.get("retrieval_status", "not_downloaded")
            record["retrieved"] = result.get("retrieval_status") == "converted_review_candidate"
            record["accepted"] = False
            if result.get("retrieval_status") == "converted_review_candidate":
                record["candidate_text_path"] = result["output_path"]
                record["source_sha256"] = result["source_sha256"]
                record["converted_sha256"] = result["converted_sha256"]
            else:
                record.pop("candidate_text_path", None)
                record.pop("source_sha256", None)
                record.pop("converted_sha256", None)
        catalog["status"] = "partial_retrieval_review_candidates"
        catalog["retrieval_status"] = f"{current['converted_candidate_count']} of {len(catalog_records)} candidate records downloaded and converted; others pending or retrieval-blocked"
        catalog["retrieved_candidate_count"] = current["converted_candidate_count"]
        catalog["accepted_source_count"] = 0
        atomic_write(CANDIDATES, (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "sync":
        sync()
    elif mode in {"convert", "verify"}:
        process(mode)
    else:
        raise SystemExit("usage: sync_ireland.py [sync|convert|verify]")


if __name__ == "__main__":
    main()
