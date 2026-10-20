#!/usr/bin/env python3
"""Retrieve Latvian official pages and preserve current review candidates."""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
REFS = PACK / "references"
CANDIDATES = REFS / "candidate-manifest.json"
CAPTURES = REFS / "latvia-captures.json"
MAX_BYTES = 16 * 1024 * 1024
TIMEOUT = 20
REQUEST_DELAY_SECONDS = 1.0
UA = "eudirective-source-library/1.0 (public official-source review; eudirective@proton.me)"
MONITOR_ONLY = {"lv-01", "lv-42", "lv-43", "lv-44", "lv-45", "lv-46"}
PDF_IDS = {"lv-07", "lv-22"}
PDF_CONVERSION_VERSION = "latvia-pdf-text-v1"
PDF_LIBRARY_VERSION = "6.21.1"
SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer"}
BLOCK_TAGS = {"address", "article", "br", "dd", "div", "dl", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "section", "table", "td", "th", "tr", "ul"}

HOST_SELECTORS: dict[str, list[tuple[str, str]]] = {
    "likumi.lv": [("class", "doc-body"), ("class", "globalContainerCenter"), ("tag", "main"), ("id", "main")],
    "www.pmlp.gov.lv": [("class", "block--system-main"), ("tag", "main"), ("id", "main")],
    "www.mfa.gov.lv": [("class", "block--system-main"), ("tag", "main"), ("id", "main")],
    "www.lv.lv": [("class", "block--system-main"), ("tag", "main"), ("id", "main")],
    "www.rs.gov.lv": [("class", "block--system-main"), ("tag", "main"), ("id", "main")],
    "www.dvi.gov.lv": [("class", "block--system-main"), ("tag", "main"), ("id", "main")],
    "www.tiesas.lv": [("class", "block--system-main"), ("tag", "main"), ("id", "main")],
    "www.ta.gov.lv": [("class", "block--system-main"), ("tag", "main"), ("id", "main")],
    "www.tiesibsargs.lv": [("tag", "main"), ("id", "main"), ("class", "content")],
    "www.at.gov.lv": [("tag", "main"), ("id", "main"), ("class", "content")],
    "www.satversmestiesa.lv": [("tag", "main"), ("id", "main"), ("class", "content")],
    "www.vestnesis.lv": [("class", "docContent"), ("tag", "main"), ("id", "main"), ("class", "content")],
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_pdf(raw: bytes) -> tuple[list[str], dict[str, object]]:
    import pypdf
    from pypdf import PdfReader

    if pypdf.__version__ != PDF_LIBRARY_VERSION:
        raise ValueError(f"PDF conversion requires pypdf=={PDF_LIBRARY_VERSION}; found {pypdf.__version__}")
    reader = PdfReader(BytesIO(raw), strict=False)
    if reader.is_encrypted:
        raise ValueError("encrypted PDF cannot be converted without a password")
    pages: list[str] = []
    for number, page in enumerate(reader.pages, start=1):
        extracted = page.extract_text() or ""
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in extracted.replace("\r", "\n").splitlines()]
        text = "\n".join(line for line in lines if line).strip()
        if not text:
            raise ValueError(f"PDF page {number} has no extractable text; OCR or manual conversion is required")
        pages.append(text)

    fields = reader.get_fields() or {}
    field_types = Counter(str(field.get("/FT") or "unknown") for field in fields.values())
    info = reader.metadata or {}
    metadata_keys = ("/title", "/lv_nr", "/issue_date", "/edition_nr", "/edition_id", "/Creator", "/Producer", "/CreationDate", "/ModDate")
    metadata = {key: str(info[key]) for key in metadata_keys if info.get(key) is not None and isinstance(info.get(key), (str, int, float))}
    signature_fields = sum(1 for field in fields.values() if str(field.get("/FT")) == "/Sig")
    return pages, {
        "page_count": len(reader.pages),
        "interactive_field_count": len(fields),
        "interactive_field_types": dict(sorted(field_types.items())),
        "signature_field_count": signature_fields,
        "pdf_metadata": metadata,
    }


def pdf_markdown(item: dict, record: dict, raw: bytes) -> tuple[bytes, dict[str, object]]:
    pages, info = extract_pdf(raw)
    text_body = "\n\n".join(f"<!-- page {number} -->\n{text}" for number, text in enumerate(pages, start=1))
    page_url = record.get("publisher_page_url") or item.get("url") or record.get("source_url", "")
    lines = [
        f"# {item['title']}",
        "",
        "- Jurisdiction: Latvia",
        f"- Candidate ID: `{item['id']}`",
        f"- Source type: `{item.get('source_type', 'official_source_candidate')}`",
        f"- Official source page: {page_url}",
        f"- PDF URL: {record.get('resolved_url') or record.get('source_url')}",
        f"- Retrieved: {record.get('retrieved_at', 'date not recorded')}",
        f"- Original PDF path: `{record.get('candidate_source_path', record.get('raw_path'))}`",
        f"- Original PDF SHA-256: `{record['source_sha256']}`",
        f"- Original PDF bytes: {record['source_bytes']}",
        f"- Conversion rule: `{PDF_CONVERSION_VERSION}` using `pypdf=={PDF_LIBRARY_VERSION}`",
        f"- Pages: {info['page_count']}",
        f"- Interactive PDF fields: {info['interactive_field_count']} ({json.dumps(info['interactive_field_types'], ensure_ascii=False, sort_keys=True)})",
    ]
    if info["pdf_metadata"]:
        lines.append(f"- PDF metadata: `{json.dumps(info['pdf_metadata'], ensure_ascii=False, sort_keys=True)}`")
    lines += [
        "- Status: unaccepted review candidate",
        "",
        "> **Review candidate.** This page-wise text extraction is for search and review. The original PDF remains the source artifact; layout and fillable fields are not recreated in Markdown.",
    ]
    if info["signature_field_count"]:
        lines.append("> The PDF contains a signature field; its cryptographic signature was not validated by this conversion.")
    lines += ["", "## Text extracted by page", "", text_body, ""]
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8"), info


def html_change_hash(data: bytes) -> str:
    """Ignore identified transport tokens while retaining exact bytes separately."""
    stable = re.sub(rb"<script\b[^>]*>.*?</script\s*>", b"", data, flags=re.I | re.S)
    stable = re.sub(rb"js-view-dom-id-[a-f0-9]{40,}", b"js-view-dom-id-{volatile}", stable, flags=re.I)
    def replace_csrf(match: re.Match[bytes]) -> bytes:
        tag = match.group(0)
        return re.sub(rb"(\bcontent\s*=\s*['\"])[^'\"]*(['\"])", rb"\1{csrf}\2", tag, count=1, flags=re.I)
    stable = re.sub(rb"<meta\b[^>]*\bname\s*=\s*['\"]csrf-token['\"][^>]*>", replace_csrf, stable, flags=re.I)
    return sha256(stable)


def candidate_body(path: str | None) -> str | None:
    if not path:
        return None
    try:
        content = inside_root(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    marker = "## Official source text\n"
    return content.split(marker, 1)[1].strip() if marker in content else None


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


def inside_root(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"refused path outside repository root: {relative}")
    return path


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def allowed_hosts(manifest: dict) -> set[str]:
    hosts = {x.lower() for x in manifest.get("official_hosts", [])}
    for item in manifest.get("documents", []):
        host = urllib.parse.urlparse(item["url"]).hostname
        if host:
            hosts.add(host.lower())
            hosts.add(host.lower().removeprefix("www."))
    return hosts


class AllowlistedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts: set[str]):
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or host not in self.hosts:
            if "perfdrive" in host or "radware" in host:
                raise RuntimeError("publisher_security_challenge")
            raise ValueError(f"refused redirect outside official-host allowlist: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, hosts: set[str]) -> tuple[bytes, str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in hosts:
        raise ValueError(f"refused non-allowlisted official URL: {url}")
    opener = urllib.request.build_opener(AllowlistedRedirect(hosts))
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    })
    with opener.open(req, timeout=TIMEOUT) as response:
        final = response.geturl()
        final_parsed = urllib.parse.urlparse(final)
        if final_parsed.scheme != "https" or (final_parsed.hostname or "").lower() not in hosts:
            raise ValueError(f"refused final URL outside official-host allowlist: {final}")
        content_type = response.headers.get_content_type().lower()
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError(f"response exceeds {MAX_BYTES} byte cap")
        if not raw:
            raise ValueError("publisher returned an empty response")
        return raw, final, content_type


class RegionText(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, selector: tuple[str, str]):
        super().__init__(convert_charrefs=True)
        self.selector = selector
        self.stack: list[str] = []
        self.skip_stack: list[str] = []
        self.parts: list[str] = []
        self.found = False

    def matches(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        kind, value = self.selector
        values = dict(attrs)
        if kind == "tag":
            return tag == value
        if kind == "id":
            return values.get("id") == value
        return value in (values.get("class") or "").split()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())
        if self.skip_stack:
            if tag not in self.VOID:
                self.skip_stack.append(tag)
            return
        if not self.found:
            if self.matches(tag, attrs):
                self.found = True
                if tag not in self.VOID:
                    self.stack.append(tag)
            return
        if tag in SKIP_TAGS or classes.intersection({"panta-doc-npk", "info-icon-wrapper", "court"}):
            if tag not in self.VOID:
                self.skip_stack.append(tag)
            return
        if tag == "br":
            self.parts.append("\n")
        elif tag not in self.VOID:
            self.stack.append(tag)
            if tag in BLOCK_TAGS:
                self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_stack:
            idx = len(self.skip_stack) - 1
            while idx >= 0 and self.skip_stack[idx] != tag:
                idx -= 1
            if idx >= 0:
                del self.skip_stack[idx:]
            return
        if not self.stack:
            return
        idx = len(self.stack) - 1
        while idx >= 0 and self.stack[idx] != tag:
            idx -= 1
        if idx < 0:
            return
        removed = self.stack[idx:]
        del self.stack[idx:]
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if not self.stack:
            self.found = True

    def handle_data(self, data: str) -> None:
        if self.found and self.stack and not self.skip_stack and data.strip():
            self.parts.append(data)

    def result(self) -> str:
        raw = "".join(self.parts).replace("\xa0", " ").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", x).strip() for x in raw.splitlines()]
        compact: list[str] = []
        for line in lines:
            if line or (compact and compact[-1]):
                compact.append(line)
        return "\n".join(compact).strip()


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors: list[tuple[str, str]] = []
        self.current: tuple[str, list[str]] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href") or ""
            self.current = (href, [])

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current is not None:
            self.anchors.append((self.current[0], " ".join(self.current[1])))
            self.current = None


def extract_title(raw: bytes) -> str:
    source = raw.decode("utf-8", "replace")
    match = re.search(r"<title[^>]*>(.*?)</title>", source, re.I | re.S)
    if not match:
        match = re.search(r"<h1[^>]*>(.*?)</h1>", source, re.I | re.S)
    if not match:
        raise ValueError("official page lacks a title")
    title = html.unescape(re.sub(r"<[^>]+>", " ", match.group(1)))
    title = re.sub(r"\s+", " ", title).strip()
    if any(x in title.lower() for x in ("captcha", "access denied", "404 not found", "error page")):
        raise ValueError(f"publisher returned a non-content page: {title}")
    return title


def extract_text(raw: bytes, host: str) -> tuple[str, str]:
    source = raw.decode("utf-8", "replace")
    selectors = HOST_SELECTORS.get(host, [("tag", "main"), ("id", "main")])
    for selector in selectors:
        parser = RegionText(selector)
        parser.feed(source)
        text = parser.result()
        if text:
            return text, f"{selector[0]}={selector[1]}"
    return "", "no supported primary-content selector found"


def version_evidence(record: dict, raw: bytes, as_of: str) -> str:
    source = raw.decode("utf-8", "replace")
    for pattern in (
        r'<meta[^>]+(?:property|name)=["\'](?:article:modified_time|dcterms.modified)["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:article:modified_time|dcterms.modified)["\']',
    ):
        m = re.search(pattern, source, re.I)
        if m:
            return f"Publisher page metadata: {html.unescape(m.group(1))}"
    note = record.get("version_evidence")
    if note:
        return f"Publisher/version note recorded during source review: {note} Captured {as_of}; verify against any later publisher update."
    return f"No machine-readable page-version date found; captured {as_of}. Check any human-readable update date in the saved review text."


def write_raw(relative: str, data: bytes) -> None:
    path = inside_root(relative)
    if not path.exists():
        atomic_write(path, data)


def markdown(record: dict, title: str, resolved: str, as_of: str, retrieved: str,
             version: str, source_hash: str, selector: str, body: str) -> bytes:
    language = "en" if "/ta/en/" in record["url"] else "lv"
    lines = [
        f"# {record['title']}", "",
        f"- Jurisdiction: Latvia",
        f"- Candidate ID: `{record['id']}`",
        f"- Source type: `{record.get('source_type', 'official_source')}`",
        f"- Official page title: {title}",
        f"- Publisher: {urllib.parse.urlparse(record['url']).hostname}",
        f"- Language: `{language}`",
        f"- Candidate source URL: {record['url']}",
        f"- Resolved URL: {resolved}",
        f"- As-of date: {as_of}",
        f"- Retrieved: {retrieved}",
        f"- Publisher version evidence: {version}",
        f"- Extraction region: `{selector}`",
        f"- Source SHA-256: `{source_hash}`",
        "",
        "> **Review candidate.** Not accepted into the trusted source corpus. Check legal identity, version, language, scope, linked documents and publisher terms before reliance.",
        "",
        "## Official source text", "",
        body, "",
    ]
    if record["id"].startswith("lv-") and record["id"] in {"lv-04", "lv-06", "lv-08", "lv-09", "lv-10", "lv-11", "lv-12", "lv-13", "lv-14", "lv-15", "lv-16", "lv-17"}:
        lines.insert(17, "> Likumi.lv describes systematised wording as informational; Latvijas Vēstnesis promulgation prevails if the records conflict.")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def old_record(previous: dict, candidate_id: str) -> dict | None:
    return next((x for x in previous.get("records", []) if x.get("candidate_id") == candidate_id), None)


def changed_output_path(candidate_id: str, source_hash: str, previous: dict | None, kind: str,
                        comparison_hash: str | None = None) -> tuple[str, str, str | None]:
    prior_pending = bool(previous and previous.get("review_state") == "changed_pending_review")
    changed = False
    prior_hash = None
    if previous and previous.get("source_sha256"):
        if kind == "pdf":
            changed = previous["source_sha256"] != source_hash
        else:
            prior_hash = html_change_hash(inside_root(previous["raw_path"]).read_bytes()) if previous.get("raw_path") else previous.get("change_detection_sha256")
            changed = bool(prior_hash and comparison_hash and prior_hash != comparison_hash)
    if prior_pending and kind != "pdf":
        original_path = previous.get("previous_candidate_text_path")
        if original_path and candidate_body(previous.get("candidate_text_path")) == candidate_body(original_path):
            prior_pending = False
            if comparison_hash and previous.get("raw_path"):
                prior_hash = html_change_hash(inside_root(previous["raw_path"]).read_bytes())
                changed = prior_hash != comparison_hash
    if prior_pending or changed:
        previous_path = (previous.get("previous_candidate_source_path") or previous.get("candidate_source_path")) if kind == "pdf" else (previous.get("previous_candidate_text_path") or previous.get("candidate_text_path"))
        if prior_pending and not changed:
            path = previous.get("candidate_source_path") if kind == "pdf" else previous.get("candidate_text_path")
        else:
            suffix = "pdf" if kind == "pdf" else "md"
            path = f"temp/latvia/pending/{slug(candidate_id)}-{source_hash[:16]}.{suffix}"
        return path, "changed_review_candidate", previous_path
    suffix = "pdf" if kind == "pdf" else "md"
    path = f"source-library/latvia/candidates/{slug(candidate_id)}.{suffix}"
    return path, "source_pdf_review_candidate_not_text_extracted" if kind == "pdf" else "converted_review_candidate", None


def capture_pdf(record: dict, url: str, hosts: set[str], as_of: str, previous: dict | None,
                result: dict, content_type_expected: str = "application/pdf") -> dict:
    raw, final, content_type = fetch(url, hosts)
    if content_type != content_type_expected or not raw.startswith(b"%PDF-"):
        raise ValueError(f"expected a PDF from the official publisher; got {content_type}")
    digest = sha256(raw)
    slugged = slug(record["id"])
    raw_path = f"temp/latvia/raw/{slugged}-{digest}.pdf"
    write_raw(raw_path, raw)
    out_path, status, previous_path = changed_output_path(record["id"], digest, previous, "pdf")
    stage_path = f"temp/latvia/staging/{slugged}-{digest}.pdf"
    write_raw(stage_path, raw)
    result.update({
        "candidate_id": record["id"], "title": record["title"], "source_url": url,
        "resolved_url": final, "as_of_date": as_of, "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_content_type": content_type, "source_bytes": len(raw), "source_sha256": digest,
        "raw_path": raw_path, "candidate_source_path": out_path, "staged_source_path": stage_path,
        "retrieval_status": status, "review_state": "changed_pending_review" if status == "changed_review_candidate" else "review_candidate",
        "accepted": bool(record.get("accepted", False)),
    })
    if previous_path:
        result["previous_candidate_source_path"] = previous_path
    return result


def capture_one(record: dict, hosts: set[str], as_of: str, previous: dict | None) -> dict:
    if record["id"] in MONITOR_ONLY:
        return {"candidate_id": record["id"], "source_url": record["url"], "title": record["title"], "retrieval_status": "monitor_only_no_individual_source_text", "accepted": False, "retrieval_note": "Discovery or repository route; no individual text was identified for this record."}
    if record["id"] == "lv-22":
        return capture_pdf(record, record["url"], hosts, as_of, previous, {})
    raw, final, content_type = fetch(record["url"], hosts)
    source_hash = sha256(raw)
    slugged = slug(record["id"])
    raw_ext = "pdf" if content_type == "application/pdf" else "html"
    raw_path = f"temp/latvia/raw/{slugged}-{source_hash}.{raw_ext}"
    write_raw(raw_path, raw)
    if content_type != "text/html" and content_type != "application/xhtml+xml":
        raise ValueError(f"expected HTML page; got {content_type}")
    title = extract_title(raw)
    host = (urllib.parse.urlparse(final).hostname or "").lower()
    body, selector = extract_text(raw, host)
    if len(body) < 80:
        raise ValueError(f"official page text is unexpectedly short ({len(body)} characters; selector {selector})")
    if record["id"] == "lv-07":
        source = raw.decode("utf-8", "replace")
        if "2026/119.1" not in source:
            raise ValueError("Gazette page does not identify OP 2026/119.1")
        links = AnchorParser()
        links.feed(source)
        pdf_link = next((urllib.parse.urljoin(final, href) for href, label in links.anchors if "pdf" in label.lower() and href), None)
        if not pdf_link:
            raise ValueError("Gazette page does not expose its official PDF link")
        time.sleep(REQUEST_DELAY_SECONDS)
        return capture_pdf(record, pdf_link, hosts, as_of, previous, {
            "publisher_page_url": record["url"], "publisher_page_resolved_url": final,
            "publisher_page_sha256": source_hash, "publisher_page_raw_path": raw_path,
        })
    version = version_evidence(record, raw, as_of)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    comparison_hash = html_change_hash(raw)
    output, status, previous_path = changed_output_path(record["id"], source_hash, previous, "md", comparison_hash)
    content = markdown(record, title, final, as_of, retrieved_at, version, source_hash, selector, body)
    converted_hash = sha256(content)
    stage_path = f"temp/latvia/staging/{slugged}-{converted_hash}.md"
    write_raw(stage_path, content)
    result = {
        "candidate_id": record["id"], "title": record["title"], "source_url": record["url"],
        "resolved_url": final, "as_of_date": as_of, "retrieved_at": retrieved_at,
        "source_content_type": content_type, "source_bytes": len(raw), "source_sha256": source_hash,
        "raw_path": raw_path, "candidate_text_path": output, "staged_text_path": stage_path,
        "publisher_version_evidence": version, "content_selector": selector,
        "change_detection_sha256": comparison_hash,
        "raw_source_changed": bool(previous and previous.get("source_sha256") != source_hash),
        "converted_bytes": len(content), "converted_sha256": converted_hash,
        "retrieval_status": status, "review_state": "changed_pending_review" if status == "changed_review_candidate" else "review_candidate",
        "accepted": bool(record.get("accepted", False)),
    }
    if previous_path:
        result["previous_candidate_text_path"] = previous_path
    return result


def finalize(results: list[dict]) -> None:
    staged: list[tuple[dict, str, bytes, str]] = []
    for rec in results:
        for path_key, dest_key, hash_key in (("staged_text_path", "candidate_text_path", "converted_sha256"), ("staged_source_path", "candidate_source_path", "source_sha256")):
            if path_key not in rec:
                continue
            raw = inside_root(rec[path_key]).read_bytes()
            if sha256(raw) != rec[hash_key]:
                raise ValueError(f"staged file hash mismatch for {rec['candidate_id']}")
            staged.append((rec, dest_key, raw, path_key))
    for rec, dest_key, raw, stage_key in staged:
        atomic_write(inside_root(rec[dest_key]), raw)
        inside_root(rec[stage_key]).unlink(missing_ok=True)
        rec.pop(stage_key, None)


def update_manifest(manifest: dict, results: list[dict]) -> None:
    by_id = {x["id"]: x for x in manifest.get("documents", [])}
    for result in results:
        item = by_id[result["candidate_id"]]
        item["retrieved"] = result["retrieval_status"] in {
            "converted_review_candidate", "source_pdf_review_candidate_not_text_extracted", "changed_review_candidate"
        }
        item["retrieval_status"] = result["retrieval_status"]
        item["accepted"] = bool(item.get("accepted", False))
        for key in (
            "candidate_text_path", "previous_candidate_text_path", "candidate_source_path",
            "previous_candidate_source_path", "resolved_url", "source_sha256", "converted_sha256",
            "publisher_version_evidence", "content_selector", "retrieval_note", "source_bytes",
            "converted_bytes", "conversion_rule_version", "page_count", "interactive_field_count",
            "interactive_field_types", "signature_field_count", "pdf_metadata",
            "change_detection_sha256", "raw_source_changed",
        ):
            if key in result:
                item[key] = result[key]
    retrieved = sum(bool(x.get("retrieved")) for x in by_id.values())
    converted = sum(x.get("retrieval_status") in {"converted_review_candidate", "changed_review_candidate"} for x in by_id.values())
    binaries = sum(x.get("retrieval_status") == "source_pdf_review_candidate_not_text_extracted" for x in by_id.values())
    manifest["status"] = "partially_retrieved_review_candidates"
    captures = results
    html_texts = sum(bool(x.get("candidate_text_path")) and x.get("source_content_type") != "application/pdf" for x in captures)
    pdf_texts = sum(bool(x.get("candidate_text_path")) and x.get("source_content_type") == "application/pdf" for x in captures)
    manifest["retrieval_status"] = f"{converted} texts converted ({html_texts} HTML, {pdf_texts} PDF); {binaries} official PDFs remain without text extraction; repository/database leads remain monitor-only; publisher terms and source coverage remain under review"
    manifest["accepted_source_count"] = 0
    manifest["retrieved_review_candidate_count"] = retrieved
    manifest["converted_review_candidate_count"] = converted
    manifest["preserved_pdf_candidate_count"] = sum(bool(x.get("candidate_source_path")) for x in captures)


def sync() -> None:
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    hosts = allowed_hosts(manifest)
    as_of = date.today().isoformat()
    prior = json.loads(CAPTURES.read_text(encoding="utf-8")) if CAPTURES.exists() else {"records": []}
    results: list[dict] = []
    for index, record in enumerate(manifest.get("documents", [])):
        old = old_record(prior, record["id"])
        try:
            print(f"retrieving {record['id']}", flush=True)
            results.append(capture_one(record, hosts, as_of, old))
        except Exception as exc:
            error = "publisher_security_challenge" if "publisher_security_challenge" in str(exc) else f"{type(exc).__name__}: {exc}"
            print(f"review {record['id']}: {error}", flush=True)
            results.append({
                "candidate_id": record["id"], "title": record["title"], "source_url": record["url"],
                "retrieval_status": "publisher_security_challenge" if error == "publisher_security_challenge" else "retrieval_or_conversion_error",
                "retrieval_note": error, "accepted": False,
            })
        if index < len(manifest.get("documents", [])) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)
    finalize(results)
    retrieval = {
        "manifest_version": 1,
        "jurisdiction": "Latvia",
        "as_of_date": as_of,
        "method": "Retrieve candidate pages with ordinary HTTPS GET and no account/API registration. Redirects remain on allowlisted official hosts. Likumi.lv acts are extracted from doc-body; identified Drupal guidance pages use block--system-main; other official pages use their configured main-content container. Official PDFs are retained byte-for-byte and page-text extracted with pinned pypdf 6.21.1; cryptographic signature validation and reconstruction of interactive form behavior are not performed.",
        "request_policy": {"timeout_seconds": TIMEOUT, "max_response_bytes": MAX_BYTES, "delay_seconds": REQUEST_DELAY_SECONDS},
        "change_detection": "Preserve and record the exact response hash. For HTML comparison, ignore script elements, Drupal js-view-dom-id hashes, and the rotating csrf-token value identified in repeated captures; retain all other markup and links in the comparison digest. A remaining response change stages a new review candidate under temp/latvia/pending. PDFs use exact-byte hashes. Prior candidates are preserved for review and no source is automatically accepted.",
        "publisher_terms": "Likumi.lv terms allow reuse of systematised acts only under the information-access laws and applicable fees; the keeper organises reuse. Latvijas Vēstnesis says reuse must be coordinated in writing with the intended purpose and product/service, and its public interface currently supports grouped official-notice reuse. Confirm in writing whether a recurring legal-text monitor is covered and what fee applies; no crawler rate limit was found. All captures remain unaccepted.",
        "records": results,
        "accepted_source_count": 0,
    }
    update_manifest(manifest, results)
    atomic_write(CANDIDATES, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    atomic_write(CAPTURES, (json.dumps(retrieval, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def reconvert() -> None:
    """Rebuild saved HTML and PDF conversions offline from exact captured bytes."""
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    documents = {x["id"]: x for x in manifest.get("documents", [])}
    for record in captures.get("records", []):
        if not record.get("candidate_text_path"):
            continue
        raw = inside_root(record["raw_path"]).read_bytes()
        if sha256(raw) != record["source_sha256"]:
            raise ValueError(f"raw source hash mismatch for {record['candidate_id']}")
        if record.get("source_content_type") == "application/pdf":
            content, info = pdf_markdown(documents[record["candidate_id"]], record, raw)
            digest = sha256(content)
            atomic_write(inside_root(record["candidate_text_path"]), content)
            record.update(info)
            record.update({
                "content_selector": f"PDF text extraction; {info['page_count']} pages",
                "conversion_rule_version": PDF_CONVERSION_VERSION,
                "converted_bytes": len(content),
                "converted_sha256": digest,
            })
            print(f"reconverted PDF {record['candidate_id']}")
            continue
        title = extract_title(raw)
        body, selector = extract_text(raw, (urllib.parse.urlparse(record["resolved_url"]).hostname or "").lower())
        if len(body) < 80:
            raise ValueError(f"source text unexpectedly short for {record['candidate_id']}")
        version = version_evidence(documents[record["candidate_id"]], raw, record["as_of_date"])
        content = markdown(documents[record["candidate_id"]], title, record["resolved_url"],
                           record["as_of_date"], record["retrieved_at"], version,
                           record["source_sha256"], selector, body)
        digest = sha256(content)
        atomic_write(inside_root(record["candidate_text_path"]), content)
        record["publisher_version_evidence"] = version
        record["content_selector"] = selector
        record["converted_bytes"] = len(content)
        record["converted_sha256"] = digest
        print(f"reconverted {record['candidate_id']}")
    update_manifest(manifest, captures.get("records", []))
    atomic_write(CANDIDATES, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    atomic_write(CAPTURES, (json.dumps(captures, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def convert_pdfs() -> None:
    """Convert preserved PDFs without fetching or modifying the source bytes."""
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    documents = {x["id"]: x for x in manifest.get("documents", [])}
    for record in captures.get("records", []):
        if record.get("source_content_type") != "application/pdf" or not record.get("raw_path"):
            continue
        raw = inside_root(record["raw_path"]).read_bytes()
        if sha256(raw) != record.get("source_sha256"):
            raise ValueError(f"raw PDF hash mismatch for {record['candidate_id']}")
        if record.get("candidate_source_path"):
            original_copy = inside_root(record["candidate_source_path"]).read_bytes()
            if sha256(original_copy) != record["source_sha256"]:
                raise ValueError(f"preserved candidate PDF hash mismatch for {record['candidate_id']}")
        item = documents[record["candidate_id"]]
        content, info = pdf_markdown(item, record, raw)
        output_path = record.get("candidate_text_path") or str(Path(record["candidate_source_path"]).with_suffix(".md"))
        digest = sha256(content)
        atomic_write(inside_root(output_path), content)
        record.update(info)
        record.update({
            "candidate_text_path": output_path,
            "content_selector": f"PDF text extraction; {info['page_count']} pages",
            "conversion_rule_version": PDF_CONVERSION_VERSION,
            "converted_bytes": len(content),
            "converted_sha256": digest,
            "retrieval_status": "converted_review_candidate",
            "review_state": "review_candidate",
            "accepted": False,
        })
        item.update({
            "candidate_text_path": output_path,
            "conversion_rule_version": PDF_CONVERSION_VERSION,
            "converted_bytes": len(content),
            "converted_sha256": digest,
            "page_count": info["page_count"],
            "interactive_field_count": info["interactive_field_count"],
            "interactive_field_types": info["interactive_field_types"],
            "signature_field_count": info["signature_field_count"],
            "pdf_metadata": info["pdf_metadata"],
            "retrieval_status": "converted_review_candidate",
            "retrieved": True,
            "accepted": False,
        })
        print(f"converted PDF {record['candidate_id']} to {output_path}")
    captures["pdf_conversion_rule"] = PDF_CONVERSION_VERSION
    captures["pdf_conversion_library"] = f"pypdf=={PDF_LIBRARY_VERSION}"
    update_manifest(manifest, captures.get("records", []))
    atomic_write(CANDIDATES, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    atomic_write(CAPTURES, (json.dumps(captures, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def verify() -> None:
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    documents = {x["id"]: x for x in manifest.get("documents", [])}
    errors: list[str] = []
    for record in captures.get("records", []):
        try:
            if record.get("raw_path"):
                raw = inside_root(record["raw_path"]).read_bytes()
                if sha256(raw) != record["source_sha256"]:
                    raise ValueError("raw source hash mismatch")
                if record.get("change_detection_sha256") and html_change_hash(raw) != record["change_detection_sha256"]:
                    raise ValueError("normalized HTML change-detection hash mismatch")
            if record.get("publisher_page_raw_path"):
                page = inside_root(record["publisher_page_raw_path"]).read_bytes()
                if sha256(page) != record["publisher_page_sha256"]:
                    raise ValueError("publisher page hash mismatch")
            if record.get("candidate_source_path"):
                source_copy = inside_root(record["candidate_source_path"]).read_bytes()
                if sha256(source_copy) != record["source_sha256"]:
                    raise ValueError("candidate PDF hash mismatch")
            if record.get("candidate_text_path"):
                raw = inside_root(record["raw_path"]).read_bytes()
                if record.get("source_content_type") == "application/pdf":
                    content, info = pdf_markdown(documents[record["candidate_id"]], record, raw)
                    selector = f"PDF text extraction; {info['page_count']} pages"
                    if info != {key: record[key] for key in info}:
                        raise ValueError("PDF extraction metadata replay mismatch")
                    if record.get("conversion_rule_version") != PDF_CONVERSION_VERSION:
                        raise ValueError("PDF conversion rule version mismatch")
                else:
                    title = extract_title(raw)
                    body, selector = extract_text(raw, (urllib.parse.urlparse(record["resolved_url"]).hostname or "").lower())
                    version = version_evidence(documents[record["candidate_id"]], raw, record["as_of_date"])
                    content = markdown(documents[record["candidate_id"]], title, record["resolved_url"], record["as_of_date"],
                                       record["retrieved_at"], version, record["source_sha256"], selector, body)
                if selector != record["content_selector"] or sha256(content) != record["converted_sha256"]:
                    raise ValueError("deterministic extraction replay mismatch")
                if sha256(inside_root(record["candidate_text_path"]).read_bytes()) != record["converted_sha256"]:
                    raise ValueError("candidate Markdown hash mismatch")
                print(f"verified {record['candidate_id']}")
            elif record.get("candidate_source_path"):
                print(f"verified {record['candidate_id']} (PDF source preserved)")
        except Exception as exc:
            errors.append(f"{record.get('candidate_id', 'unknown')}: {type(exc).__name__}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "sync":
        sync()
    elif mode == "reconvert":
        reconvert()
    elif mode == "convert-pdfs":
        convert_pdfs()
    elif mode == "verify":
        verify()
    else:
        raise SystemExit("usage: sync_latvia.py [sync|convert-pdfs|reconvert|verify]")


if __name__ == "__main__":
    main()
