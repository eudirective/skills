#!/usr/bin/env python3
"""Capture official Liechtenstein source candidates without bypassing publisher controls."""
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
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
REFS = PACK / "references"
MANIFEST = REFS / "candidate-manifest.json"
CAPTURES = REFS / "liechtenstein-captures.json"
MAX_BYTES = 24 * 1024 * 1024
TIMEOUT = 20
DELAY = 1.0
UA = "eudirective-source-library/1.0 (public-source review; eudirective@proton.me)"
STAGING_IDS = {"li-25", "li-26", "li-34", "li-35"}
INTERACTIVE_IDS = {"li-27"}
APP_SHELL_IDS = {"li-33"}
PDF_IDS = {"li-05", "li-13", "li-28", "li-29"}
PDF_CONVERSION_VERSION = "liechtenstein-pdf-text-v1"
PDF_LIBRARY_VERSION = "6.21.1"
SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "form"}
BLOCK_TAGS = {"address", "article", "br", "dd", "div", "dl", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "section", "table", "td", "th", "tr", "ul"}
SELECTORS = {
    "gesetze.li": [("class", "content"), ("tag", "body")],
    "www.gesetze.li": [("class", "content"), ("tag", "body")],
    "www.datenschutzstelle.li": [("tag", "main"), ("tag", "body")],
    "datenschutzstelle.li": [("tag", "main"), ("tag", "body")],
    "www.gerichte.li": [("tag", "main"), ("tag", "body")],
    "gerichte.li": [("tag", "main"), ("tag", "body")],
    "www.gerichtsentscheidungen.li": [("tag", "main"), ("tag", "body")],
    "gerichtsentscheidungen.li": [("tag", "main"), ("tag", "body")],
    "opendata.li": [("tag", "main"), ("tag", "body")],
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def comparison_hash(data: bytes) -> str:
    stable = re.sub(rb"<script\b[^>]*>.*?</script\s*>", b"", data, flags=re.I | re.S)
    stable = re.sub(rb"js-view-dom-id-[a-f0-9]{40,}", b"js-view-dom-id-{volatile}", stable, flags=re.I)
    # Observed SiteImprove bot-detection form tokens rotate on every GET.
    stable = re.sub(
        rb"(<input\b[^>]*\bname\s*=\s*['\"]as_sfid['\"][^>]*\bvalue\s*=\s*['\"])[^'\"]*(['\"])",
        rb"\1{volatile}\2", stable, flags=re.I,
    )
    stable = re.sub(
        rb"(<input\b[^>]*\bname\s*=\s*['\"]as_fid['\"][^>]*\bvalue\s*=\s*['\"])[^'\"]*(['\"])",
        rb"\1{volatile}\2", stable, flags=re.I,
    )
    # Concrete pages showed a timestamp-only cache buster on the same CSS asset.
    stable = re.sub(rb"(swSkin\.css\?ts=)\d+", rb"\1{cache_timestamp}", stable, flags=re.I)
    # The LLV contact widget obfuscates the same mail address with a rotating
    # Cloudflare fragment; the stable mailto path is present in the same link.
    stable = re.sub(rb"(/cdn-cgi/l/email-protection#)[0-9a-f]+", rb"\1{volatile}", stable, flags=re.I)
    def csrf(match: re.Match[bytes]) -> bytes:
        return re.sub(rb"(\bcontent\s*=\s*['\"])[^'\"]*(['\"])", rb"\1{csrf}\2", match.group(0), count=1, flags=re.I)
    stable = re.sub(rb"<meta\b[^>]*\bname\s*=\s*['\"]csrf-token['\"][^>]*>", csrf, stable, flags=re.I)
    return sha256(stable)


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


def write_raw(relative: str, data: bytes) -> None:
    path = inside_root(relative)
    if not path.exists():
        atomic_write(path, data)


def allowed_hosts(manifest: dict) -> set[str]:
    hosts = {str(host).lower() for host in manifest.get("official_hosts", [])}
    for item in manifest.get("sources", []):
        host = urllib.parse.urlparse(item["url"]).hostname
        if host:
            hosts.add(host.lower())
    return hosts


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts: set[str]):
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or host not in self.hosts:
            raise ValueError(f"refused redirect outside official-host allowlist: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, hosts: set[str]) -> tuple[bytes, str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in hosts:
        raise ValueError(f"refused non-allowlisted official URL: {url}")
    opener = urllib.request.build_opener(SafeRedirect(hosts))
    request = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    })
    with opener.open(request, timeout=TIMEOUT) as response:
        final = response.geturl()
        parsed_final = urllib.parse.urlparse(final)
        if parsed_final.scheme != "https" or (parsed_final.hostname or "").lower() not in hosts:
            raise ValueError(f"refused final URL outside official-host allowlist: {final}")
        content_type = response.headers.get_content_type().lower()
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError(f"response exceeds {MAX_BYTES} byte cap")
        if not data:
            raise ValueError("publisher returned an empty response")
        return data, final, content_type


class TextRegion(HTMLParser):
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
        classes = set((dict(attrs).get("class") or "").split())
        if tag in SKIP_TAGS or classes.intersection({"sidebar", "header-and-nav", "modal"}):
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
        del self.stack[idx:]
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.found and self.stack and not self.skip_stack and data.strip():
            self.parts.append(data)

    def result(self) -> str:
        raw = "".join(self.parts).replace("\xa0", " ").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", part).strip() for part in raw.splitlines()]
        compact: list[str] = []
        for line in lines:
            if line or (compact and compact[-1]):
                compact.append(line)
        return "\n".join(compact).strip()


class IframeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.src: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "iframe" and self.src is None:
            self.src = dict(attrs).get("src")


def extract_text(raw: bytes, host: str, forced: tuple[str, str] | None = None) -> tuple[str, str]:
    source = raw.decode("utf-8", "replace")
    selectors = [forced] if forced else SELECTORS.get(host, [("tag", "main"), ("tag", "body")])
    for selector in selectors:
        parser = TextRegion(selector)
        parser.feed(source)
        body = parser.result()
        if body:
            return body, f"{selector[0]}={selector[1]}"
    return "", "no supported primary-content selector found"


def extract_pdf(raw: bytes) -> list[str]:
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
    return pages


def pdf_markdown(source: dict, record: dict, raw: bytes) -> tuple[bytes, int]:
    pages = extract_pdf(raw)
    text_body = "\n\n".join(f"<!-- page {number} -->\n{text}" for number, text in enumerate(pages, start=1))
    lines = [
        f"# {source['title']}",
        "",
        "- Jurisdiction: Liechtenstein",
        f"- Candidate ID: `{source['id']}`",
        f"- Source type: `{source.get('class', 'official_source_candidate')}`",
        f"- Official source page: {record.get('source_url', source.get('url', ''))}",
        f"- Retrieved PDF URL: {record.get('resolved_url', record.get('source_url', source.get('url', '')))}",
        f"- Retrieved: {record.get('retrieved_at', 'date not recorded')}",
        f"- Original PDF path: `{record.get('candidate_source_path', record.get('raw_path', ''))}`",
        f"- Original PDF SHA-256: `{record['source_sha256']}`",
        f"- Original PDF bytes: {record['source_bytes']}",
        f"- Conversion rule: `{PDF_CONVERSION_VERSION}` using `pypdf=={PDF_LIBRARY_VERSION}`",
        f"- Pages: {len(pages)}",
        "- Status: unaccepted review candidate",
        "",
        "> **Review candidate.** Page-wise text extraction is for search and review. The original PDF remains the source artifact; layout is not recreated, and PDF signatures are not cryptographically validated.",
        "",
        "## Text extracted by page",
        "",
        text_body,
        "",
    ]
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8"), len(pages)


def title_from(raw: bytes) -> str:
    source = raw.decode("utf-8", "replace")
    for pattern in (r"<title[^>]*>(.*?)</title>", r"<h1[^>]*>(.*?)</h1>", r'<meta[^>]+name=[\"\']description[\"\'][^>]+content=[\"\']([^\"\']+)'):
        match = re.search(pattern, source, re.I | re.S)
        if match:
            value = html.unescape(re.sub(r"<[^>]+>", " ", match.group(1)))
            value = re.sub(r"\s+", " ", value).strip()
            if value and not any(x in value.lower() for x in ("captcha", "access denied", "error page")):
                return value
    raise ValueError("official page lacks a usable title")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def markdown(source: dict, title: str, resolved: str, retrieved: str, version: str,
             source_hash: str, shell_hash: str | None, selector: str, body: str) -> bytes:
    lines = [
        f"# {source['title']}", "",
        "- Jurisdiction: Liechtenstein",
        f"- Candidate ID: `{source['id']}`",
        f"- Source class: `{source.get('class', 'official_source')}`",
        f"- Official page title: {title}",
        f"- Publisher: {source.get('publisher', '')}",
        f"- Candidate source URL: {source['url']}",
        f"- Resolved text URL: {resolved}",
        f"- Retrieved: {retrieved}",
        f"- Publisher/version evidence: {version}",
        f"- Extraction region: `{selector}`",
        f"- Text response SHA-256: `{source_hash}`",
    ]
    if shell_hash:
        lines.append(f"- Current-version shell SHA-256: `{shell_hash}`")
    lines += [
        "",
        f"> **Review candidate.** Not accepted into the trusted source corpus. Relationship: {source.get('relationship', 'unreviewed source lead')}",
        "> Check exact legal identity, version, language, scope, authority, links and reuse conditions before reliance.",
        "",
        "## Official source text", "", body, "",
    ]
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def previous_record(previous: dict, item_id: str) -> dict | None:
    return next((item for item in previous.get("records", []) if item.get("candidate_id") == item_id), None)


def prior_html_digest(source: dict, prior: dict | None) -> str | None:
    if not prior:
        return None
    # Rebuild the previous digest from immutable raw captures. This lets a
    # refined comparison rule take effect without inventing a source change.
    candidate_path = prior.get("previous_candidate_text_path") or prior.get("candidate_text_path")
    if candidate_path:
        path = inside_root(candidate_path)
        if path.exists():
            text = path.read_text(encoding="utf-8")
            def metadata(name: str) -> str | None:
                match = re.search(r"^- " + re.escape(name) + r": `([^`]+)`$", text, re.M)
                return match.group(1) if match else None
            text_digest = metadata("Text response SHA-256")
            shell_digest = metadata("Current-version shell SHA-256")
            def raw_for(source_digest: str | None) -> Path | None:
                if not source_digest:
                    return None
                matches = sorted((ROOT / "temp/liechtenstein/raw").glob(f"{slug(source['id'])}-{source_digest}.html"))
                return matches[0] if matches else None
            text_raw = raw_for(text_digest)
            shell_raw = raw_for(shell_digest) if shell_digest else None
            if text_raw and (not shell_digest or shell_raw):
                shell_cmp = comparison_hash(shell_raw.read_bytes()) if shell_raw else ""
                text_cmp = comparison_hash(text_raw.read_bytes())
                return sha256((shell_cmp + text_cmp).encode())
    return prior.get("change_detection_sha256")


def output_path(source: dict, digest: str, prior: dict | None, kind: str,
                comparison_digest: str | None = None) -> tuple[str, str, str | None]:
    prior_digest = prior_html_digest(source, prior) if kind == "html" else (prior.get("source_sha256") if prior else None)
    current_digest = comparison_digest if kind == "html" else digest
    if prior_digest and current_digest and prior_digest != current_digest:
        previous_path = prior.get("candidate_text_path") if kind == "html" else prior.get("candidate_source_path")
        extension = "md" if kind == "html" else "pdf"
        path = f"temp/liechtenstein/pending/{slug(source['id'])}-{digest[:16]}.{extension}"
        return path, "changed_review_candidate", previous_path
    extension = "md" if kind == "html" else "pdf"
    path = f"source-library/liechtenstein/candidates/{slug(source['id'])}.{extension}"
    status = "converted_review_candidate" if kind == "html" else "source_pdf_review_candidate_not_text_extracted"
    return path, status, None


def capture_pdf(source: dict, hosts: set[str], prior: dict | None, retrieved: str) -> dict:
    raw, resolved, content_type = fetch(source["url"], hosts)
    if content_type != "application/pdf" or not raw.startswith(b"%PDF-"):
        raise ValueError(f"expected official PDF, received {content_type}")
    digest = sha256(raw)
    name = slug(source["id"])
    raw_path = f"temp/liechtenstein/raw/{name}-{digest}.pdf"
    write_raw(raw_path, raw)
    path, status, previous_path = output_path(source, digest, prior, "pdf")
    staged = f"temp/liechtenstein/staging/{name}-{digest}.pdf"
    write_raw(staged, raw)
    result = {
        "candidate_id": source["id"], "source_url": source["url"], "resolved_url": resolved,
        "title": source["title"], "as_of_date": date.today().isoformat(), "retrieved_at": retrieved,
        "source_content_type": content_type, "source_bytes": len(raw), "source_sha256": digest,
        "raw_path": raw_path, "candidate_source_path": path, "staged_source_path": staged,
        "retrieval_status": status, "review_state": "changed_pending_review" if status == "changed_review_candidate" else "review_candidate",
        "accepted": False,
    }
    if previous_path:
        result["previous_candidate_source_path"] = previous_path
    return result


def capture_one(source: dict, hosts: set[str], prior: dict | None) -> dict:
    item_id = source["id"]
    if item_id in STAGING_IDS:
        return {"candidate_id": item_id, "source_url": source["url"], "title": source["title"],
                "retrieval_status": "nonproduction_staging_route_not_fetched", "retrieval_note": "Staging host is not a production source; locate a verified production URL before capturing.", "accepted": False}
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if item_id in PDF_IDS:
        return capture_pdf(source, hosts, prior, retrieved)

    raw, resolved, content_type = fetch(source["url"], hosts)
    name = slug(item_id)
    source_hash = sha256(raw)
    extension = "pdf" if content_type == "application/pdf" else "html"
    raw_path = f"temp/liechtenstein/raw/{name}-{source_hash}.{extension}"
    write_raw(raw_path, raw)
    if content_type == "application/pdf" and raw.startswith(b"%PDF-"):
        path, status, previous_path = output_path(source, source_hash, prior, "pdf")
        staged = f"temp/liechtenstein/staging/{name}-{source_hash}.pdf"
        write_raw(staged, raw)
        return {"candidate_id": item_id, "source_url": source["url"], "resolved_url": resolved,
                "title": source["title"], "retrieved_at": retrieved, "source_content_type": content_type,
                "source_bytes": len(raw), "source_sha256": source_hash, "raw_path": raw_path,
                "candidate_source_path": path, "staged_source_path": staged, "retrieval_status": status,
                "review_state": "review_candidate", "accepted": False}

    if content_type not in {"text/html", "application/xhtml+xml", "application/octet-stream"}:
        raise ValueError(f"expected HTML or PDF, received {content_type}")
    if not raw.lstrip().lower().startswith((b"<!doctype html", b"<html", b"<!--")):
        raise ValueError("publisher response is not recognizable HTML")
    shell_hash = None
    text_raw = raw
    text_resolved = resolved
    source_path = urllib.parse.urlparse(source["url"]).path
    if urllib.parse.urlparse(source["url"]).hostname in {"www.gesetze.li", "gesetze.li"} and re.fullmatch(r"/konso/\d+", source_path):
        parser = IframeParser()
        parser.feed(raw.decode("utf-8", "replace"))
        if not parser.src:
            raise ValueError("Gesetze.li record did not expose its current-text iframe")
        frame_url = urllib.parse.urljoin(resolved, html.unescape(parser.src))
        frame_parsed = urllib.parse.urlparse(frame_url)
        if frame_parsed.hostname not in hosts or not frame_parsed.path.startswith("/konso/html/"):
            raise ValueError(f"refused unexpected Gesetze.li text frame: {frame_url}")
        time.sleep(DELAY)
        text_raw, text_resolved, frame_type = fetch(frame_url, hosts)
        if frame_type not in {"text/html", "application/xhtml+xml", "application/octet-stream"} or not text_raw.lstrip().lower().startswith(b"<html"):
            raise ValueError(f"Gesetze.li current text frame is not HTML ({frame_type})")
        shell_hash = source_hash
        frame_hash = sha256(text_raw)
        frame_path = f"temp/liechtenstein/raw/{name}-{frame_hash}.html"
        write_raw(frame_path, text_raw)
    else:
        frame_hash = source_hash
        frame_path = raw_path

    host = (urllib.parse.urlparse(text_resolved).hostname or "").lower()
    forced = ("tag", "body") if "/konso/html/" in urllib.parse.urlparse(text_resolved).path else None
    body, selector = extract_text(text_raw, host, forced)
    if item_id in INTERACTIVE_IDS:
        return {"candidate_id": item_id, "source_url": source["url"], "resolved_url": resolved,
                "title": source["title"], "retrieved_at": retrieved, "source_content_type": content_type,
                "source_bytes": len(raw), "source_sha256": source_hash, "raw_path": raw_path,
                "retrieval_status": "interactive_form_initial_step_only", "retrieval_note": "Only the public initial GET was captured; this multi-step application is not a complete static source text and no form was submitted.", "accepted": False}
    if item_id in APP_SHELL_IDS:
        return {"candidate_id": item_id, "source_url": source["url"], "resolved_url": resolved,
                "title": source["title"], "retrieved_at": retrieved, "source_content_type": content_type,
                "source_bytes": len(raw), "source_sha256": source_hash, "raw_path": raw_path,
                "retrieval_status": "decision_search_app_shell_only", "retrieval_note": "The portal returned a JavaScript application shell without extractable decision text. No individual judgment was identified or downloaded.", "accepted": False}
    if len(body) < 40:
        raise ValueError(f"primary content unexpectedly short ({len(body)} characters; {selector})")

    shell_comparison_hash = comparison_hash(raw) if shell_hash else ""
    frame_comparison_hash = comparison_hash(text_raw)
    combined_hash = sha256((shell_comparison_hash + frame_comparison_hash).encode())
    path, status, previous_path = output_path(source, combined_hash, prior, "html", combined_hash)
    version = source.get("version_evidence", "No publisher version evidence recorded in inventory.")
    if shell_hash:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(text_resolved).query)
        selected = query.get("version", ["unspecified"])[0]
        version = f"Gesetze.li current-text frame version={selected}; inventory note: {version}"
    page_title = title_from(raw) if not shell_hash else title_from(raw)
    converted = markdown(source, page_title, text_resolved, retrieved, version, frame_hash, shell_hash, selector, body)
    converted_hash = sha256(converted)
    staged = f"temp/liechtenstein/staging/{name}-{converted_hash}.md"
    write_raw(staged, converted)
    result = {
        "candidate_id": item_id, "source_url": source["url"], "resolved_url": resolved,
        "text_url": text_resolved, "title": source["title"], "official_page_title": page_title,
        "as_of_date": date.today().isoformat(), "retrieved_at": retrieved,
        "source_content_type": content_type, "source_bytes": len(raw), "source_sha256": source_hash,
        "raw_path": raw_path, "text_raw_path": frame_path, "text_source_bytes": len(text_raw),
        "text_source_sha256": frame_hash, "change_detection_sha256": combined_hash,
        "publisher_shell_sha256": shell_hash, "content_selector": selector,
        "publisher_version_evidence": version, "candidate_text_path": path,
        "staged_text_path": staged, "converted_bytes": len(converted),
        "converted_sha256": converted_hash, "retrieval_status": status,
        "review_state": "changed_pending_review" if status == "changed_review_candidate" else "review_candidate",
        "accepted": False,
    }
    if previous_path:
        result["previous_candidate_text_path"] = previous_path
    return result


def finalize(results: list[dict]) -> None:
    for result in results:
        for stage_key, output_key, hash_key in (("staged_text_path", "candidate_text_path", "converted_sha256"), ("staged_source_path", "candidate_source_path", "source_sha256")):
            if stage_key not in result:
                continue
            data = inside_root(result[stage_key]).read_bytes()
            if sha256(data) != result[hash_key]:
                raise ValueError(f"staged hash mismatch for {result['candidate_id']}")
            atomic_write(inside_root(result[output_key]), data)
            inside_root(result[stage_key]).unlink(missing_ok=True)
            result.pop(stage_key, None)


def convert_pdf_records(manifest: dict, records: list[dict]) -> None:
    sources = {item["id"]: item for item in manifest.get("sources", [])}
    for record in records:
        if record.get("source_content_type") != "application/pdf" or not record.get("candidate_source_path"):
            continue
        raw = inside_root(record["raw_path"]).read_bytes()
        if sha256(raw) != record.get("source_sha256"):
            raise ValueError(f"raw PDF hash mismatch for {record['candidate_id']}")
        source_copy = inside_root(record["candidate_source_path"]).read_bytes()
        if sha256(source_copy) != record["source_sha256"]:
            raise ValueError(f"preserved PDF hash mismatch for {record['candidate_id']}")
        content, page_count = pdf_markdown(sources[record["candidate_id"]], record, raw)
        output_path = record.get("candidate_text_path") or str(Path(record["candidate_source_path"]).with_suffix(".md"))
        atomic_write(inside_root(output_path), content)
        digest = sha256(content)
        changed = record.get("retrieval_status") == "changed_review_candidate"
        record.update({
            "candidate_text_path": output_path,
            "content_selector": f"PDF text extraction; {page_count} pages",
            "conversion_rule_version": PDF_CONVERSION_VERSION,
            "page_count": page_count,
            "converted_bytes": len(content),
            "converted_sha256": digest,
            "retrieval_status": "changed_review_candidate" if changed else "converted_review_candidate",
            "review_state": "changed_pending_review" if changed else "review_candidate",
            "accepted": False,
        })
        print(f"converted PDF {record['candidate_id']} to {output_path}")


def convert_pdfs() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    capture = json.loads(CAPTURES.read_text(encoding="utf-8"))
    records = capture.get("records", [])
    convert_pdf_records(manifest, records)
    update_manifest(manifest, records)
    capture["pdf_conversion_rule"] = PDF_CONVERSION_VERSION
    capture["pdf_conversion_library"] = f"pypdf=={PDF_LIBRARY_VERSION}"
    capture["method"] = "Allowlisted ordinary HTTPS GET only; no login, API registration, challenge bypass, or form submission. Gesetze.li law pages are read through their current-version iframe. Official PDF originals are preserved byte-for-byte and page-wise text is extracted with pinned pypdf."
    atomic_write(MANIFEST, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    atomic_write(CAPTURES, (json.dumps(capture, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def update_manifest(manifest: dict, results: list[dict]) -> None:
    sources = {item["id"]: item for item in manifest.get("sources", [])}
    for result in results:
        source = sources[result["candidate_id"]]
        source["retrieved"] = bool(result.get("source_sha256"))
        source["retrieval_status"] = result["retrieval_status"]
        source["accepted"] = False
        for key in ("candidate_text_path", "previous_candidate_text_path", "candidate_source_path", "previous_candidate_source_path", "resolved_url", "text_url", "source_content_type", "source_sha256", "text_source_sha256", "change_detection_sha256", "converted_sha256", "publisher_version_evidence", "content_selector", "retrieval_note", "source_bytes", "converted_bytes", "conversion_rule_version", "page_count"):
            if key in result:
                source[key] = result[key]
    counts = {}
    for item in sources.values():
        counts[item.get("retrieval_status", "discovery_only")] = counts.get(item.get("retrieval_status", "discovery_only"), 0) + 1
    converted = sum(v for k, v in counts.items() if k in {"converted_review_candidate", "changed_review_candidate"})
    html_converted = sum(1 for item in results if item.get("candidate_text_path") and item.get("source_content_type") != "application/pdf")
    pdf_converted = sum(1 for item in results if item.get("candidate_text_path") and item.get("source_content_type") == "application/pdf")
    pdfs = counts.get("source_pdf_review_candidate_not_text_extracted", 0)
    retrieved = sum(bool(x.get("retrieved")) for x in sources.values())
    manifest["status"] = "partially_retrieved_review_candidates"
    manifest["retrieval_status"] = f"{converted} texts converted ({html_converted} HTML, {pdf_converted} PDF); {pdfs} official PDFs remain without text extraction; LLV 403, staging and interactive routes are separately identified; no source accepted"
    manifest["accepted_source_count"] = 0
    manifest["retrieved_review_candidate_count"] = retrieved
    manifest["converted_review_candidate_count"] = converted
    manifest["converted_pdf_candidate_count"] = pdf_converted
    manifest["preserved_pdf_candidate_count"] = sum(bool(x.get("candidate_source_path")) for x in results)


def sync() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hosts = allowed_hosts(manifest)
    previous = json.loads(CAPTURES.read_text(encoding="utf-8")) if CAPTURES.exists() else {"records": []}
    results = []
    items = manifest.get("sources", [])
    for index, source in enumerate(items):
        prior = previous_record(previous, source["id"])
        try:
            print(f"retrieving {source['id']}", flush=True)
            results.append(capture_one(source, hosts, prior))
        except Exception as exc:
            note = f"{type(exc).__name__}: {exc}"
            print(f"review {source['id']}: {note}", flush=True)
            results.append({"candidate_id": source["id"], "source_url": source["url"], "title": source["title"],
                            "retrieval_status": "retrieval_or_conversion_error", "retrieval_note": note, "accepted": False})
        if index < len(items) - 1:
            time.sleep(DELAY)
    finalize(results)
    convert_pdf_records(manifest, results)
    update_manifest(manifest, results)
    capture = {
        "manifest_version": 1, "jurisdiction": "Liechtenstein", "as_of_date": date.today().isoformat(),
        "method": "Allowlisted ordinary HTTPS GET only; no login, API registration, challenge bypass, or form submission. Gesetze.li law pages are read through their current-version iframe. Official PDF originals are preserved byte-for-byte and page-wise text is extracted with pinned pypdf.",
        "pdf_conversion_rule": PDF_CONVERSION_VERSION,
        "pdf_conversion_library": f"pypdf=={PDF_LIBRARY_VERSION}",
        "request_policy": {"timeout_seconds": TIMEOUT, "max_response_bytes": MAX_BYTES, "delay_seconds": DELAY},
        "change_detection": "Exact response bytes are hashed. HTML comparison digest ignores script, CSRF and Drupal view-id transport tokens only. Changed sources are staged under temp/liechtenstein/pending and never accepted automatically. PDFs use exact-byte hashes.",
        "publisher_terms": "The 2026 public-sector reuse framework and database/publisher terms are not reconciled for every source. All outputs remain review candidates pending source-specific reuse confirmation.",
        "records": results, "accepted_source_count": 0,
    }
    atomic_write(MANIFEST, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    atomic_write(CAPTURES, (json.dumps(capture, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def verify() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    capture = json.loads(CAPTURES.read_text(encoding="utf-8"))
    sources = {item["id"]: item for item in manifest.get("sources", [])}
    errors = []
    for record in capture.get("records", []):
        try:
            if record.get("raw_path"):
                raw = inside_root(record["raw_path"]).read_bytes()
                if sha256(raw) != record["source_sha256"]:
                    raise ValueError("source response hash mismatch")
            if record.get("text_raw_path") and record["text_raw_path"] != record.get("raw_path"):
                text_raw = inside_root(record["text_raw_path"]).read_bytes()
                if sha256(text_raw) != record["text_source_sha256"]:
                    raise ValueError("current-text frame hash mismatch")
            else:
                text_raw = inside_root(record["raw_path"]).read_bytes() if record.get("raw_path") else b""
            if record.get("change_detection_sha256"):
                shell_cmp = comparison_hash(inside_root(record["raw_path"]).read_bytes()) if record.get("publisher_shell_sha256") else ""
                text_cmp = comparison_hash(text_raw)
                if sha256((shell_cmp + text_cmp).encode()) != record["change_detection_sha256"]:
                    raise ValueError("normalized source change-detection hash mismatch")
            if record.get("candidate_text_path"):
                source = sources[record["candidate_id"]]
                if record.get("source_content_type") == "application/pdf":
                    rebuilt, page_count = pdf_markdown(source, record, text_raw)
                    selector = f"PDF text extraction; {page_count} pages"
                    if record.get("conversion_rule_version") != PDF_CONVERSION_VERSION or page_count != record.get("page_count"):
                        raise ValueError("PDF conversion rule or page-count mismatch")
                else:
                    host = (urllib.parse.urlparse(record.get("text_url", record["resolved_url"])).hostname or "").lower()
                    forced = ("tag", "body") if "/konso/html/" in urllib.parse.urlparse(record.get("text_url", "")).path else None
                    body, selector = extract_text(text_raw, host, forced)
                    version = record["publisher_version_evidence"]
                    rebuilt = markdown(source, record["official_page_title"], record.get("text_url", record["resolved_url"]),
                                       record["retrieved_at"], version, record["text_source_sha256"],
                                       record.get("publisher_shell_sha256"), selector, body)
                if selector != record["content_selector"] or sha256(rebuilt) != record["converted_sha256"]:
                    raise ValueError("deterministic HTML extraction replay mismatch")
                if sha256(inside_root(record["candidate_text_path"]).read_bytes()) != record["converted_sha256"]:
                    raise ValueError("candidate text hash mismatch")
                print(f"verified {record['candidate_id']}")
            elif record.get("candidate_source_path"):
                if sha256(inside_root(record["candidate_source_path"]).read_bytes()) != record["source_sha256"]:
                    raise ValueError("preserved PDF hash mismatch")
                print(f"verified {record['candidate_id']} (PDF preserved)")
        except Exception as exc:
            errors.append(f"{record.get('candidate_id', 'unknown')}: {type(exc).__name__}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "sync":
        sync()
    elif mode == "convert-pdfs":
        convert_pdfs()
    elif mode == "verify":
        verify()
    else:
        raise SystemExit("usage: sync_liechtenstein.py [sync|convert-pdfs|verify]")


if __name__ == "__main__":
    main()
