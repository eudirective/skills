#!/usr/bin/env python3
"""Check the bounded Austria source list and stage changed review candidates.

Network policy: ordinary, serial HTTPS GETs to manifest allowlisted official
hosts only. No RIS OGD/API, login, challenge bypass, or automatic acceptance.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
MANIFEST = PACK / "references" / "candidate-manifest.json"
MAX_BYTES = 24 * 1024 * 1024
TIMEOUT = 25
DELAY_SECONDS = 1.0
USER_AGENT = "eudirective-source-library/1.0 (public-source review; eudirective@proton.me)"
SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "form", "svg", "button"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCK_TAGS = {"address", "article", "br", "dd", "div", "dl", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "section", "table", "td", "th", "tr", "ul"}

# Publisher-specific headings protect against a valid official host returning
# an unrelated error, search, or interstitial page.
IDENTITY_MARKERS = {
    "at-guidance-family-card": ("Angehörige von EU-Bürgern",),
    "at-guidance-family-index": ("Aufenthalt in Österreich",),
    "at-dsb-complaint": ("Datenschutzbehörde", "Beschwerde"),
    "at-volksanwaltschaft-complaint": ("Beschwerdewegweiser",),
    "at-bmeia-visa": ("Visa",),
    "at-bmeia-settlement-residence": ("Settlement and residence",),
    "at-guidance-visa-application": ("Antrag auf Visum",),
    "at-bmeia-representation-directory": ("Österreichische Vertretungen",),
}


class AllowlistedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts: set[str]) -> None:
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        host = (parsed.hostname or "").lower()
        if host not in self.hosts:
            raise ValueError("redirect outside the official-host allowlist")
        if parsed.scheme == "http":
            parsed = parsed._replace(scheme="https")
            newurl = urllib.parse.urlunparse(parsed)
        if parsed.scheme != "https":
            raise ValueError("redirect is not HTTPS")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, hosts: set[str]) -> tuple[bytes, str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in hosts:
        raise ValueError("URL outside the official-host allowlist")
    opener = urllib.request.build_opener(AllowlistedRedirect(hosts))
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.5"},
    )
    with opener.open(request, timeout=TIMEOUT) as response:
        final = response.geturl()
        final_url = urllib.parse.urlparse(final)
        if final_url.scheme != "https" or (final_url.hostname or "").lower() not in hosts:
            raise ValueError("final URL outside the official-host allowlist")
        payload = response.read(MAX_BYTES + 1)
        if not payload or len(payload) > MAX_BYTES:
            raise ValueError("empty response or response exceeds 24 MiB cap")
        return payload, final, response.headers.get_content_type().lower()


class ScopedText(HTMLParser):
    """Prefer a record-specific main region; keep filtered body as fallback."""

    TARGETS = {
        "at-guidance-family-card": ("main", None),
        "at-guidance-family-index": ("main", None),
        "at-dsb-complaint": ("main", None),
        "at-volksanwaltschaft-complaint": ("main", "page-main-content"),
        "at-bmeia-visa": ("main", "content"),
        "at-bmeia-settlement-residence": ("main", "content"),
        "at-guidance-visa-application": ("main", None),
    }

    def __init__(self, candidate_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.candidate_id = candidate_id
        self.target = self.TARGETS.get(candidate_id)
        self.stack: list[str] = []
        self.skip_stack: list[str] = []
        self.body_seen = False
        self.target_depth: int | None = None
        self.fallback: list[str] = []
        self.selected: list[str] = []
        self.selector = "body (filtered fallback)"

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        classes = set((attrs_map.get("class") or "").split())
        if tag == "body":
            self.body_seen = True
        if self.skip_stack:
            if tag not in VOID_TAGS:
                self.skip_stack.append(tag)
            return
        if tag in SKIP_TAGS or "sr-only" in classes or attrs_map.get("aria-hidden") == "true":
            if tag not in VOID_TAGS:
                self.skip_stack.append(tag)
            return

        target_tag, target_id = self.target or (None, None)
        if self.target_depth is None and target_tag == tag and (target_id is None or attrs_map.get("id") == target_id):
            self.target_depth = len(self.stack) + (0 if tag in VOID_TAGS else 1)
            self.selector = tag + (f"#{target_id}" if target_id else "")
        if tag == "br":
            self.fallback.append("\n")
            if self.target_depth is not None:
                self.selected.append("\n")
        elif tag not in VOID_TAGS:
            self.stack.append(tag)
            if tag in BLOCK_TAGS:
                self.fallback.append("\n")
                if self.target_depth is not None and len(self.stack) >= self.target_depth:
                    self.selected.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if self.skip_stack:
            for index in range(len(self.skip_stack) - 1, -1, -1):
                if self.skip_stack[index] == tag:
                    del self.skip_stack[index:]
                    break
            return
        if tag in BLOCK_TAGS:
            self.fallback.append("\n")
            if self.target_depth is not None and len(self.stack) >= self.target_depth:
                self.selected.append("\n")
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index] == tag:
                del self.stack[index:]
                if self.target_depth is not None and len(self.stack) < self.target_depth:
                    self.target_depth = None
                break

    def handle_data(self, data: str) -> None:
        if self.skip_stack:
            return
        if self.body_seen:
            self.fallback.append(data)
        if self.target_depth is not None and len(self.stack) >= self.target_depth:
            self.selected.append(data)

    @staticmethod
    def clean(parts: list[str]) -> str:
        raw = "".join(parts).replace("\xa0", " ").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
        out: list[str] = []
        for line in lines:
            if line or (out and out[-1]):
                out.append(line)
        return "\n".join(out).strip()

    def result(self) -> tuple[str, str]:
        if self.target and not self.selected:
            raise ValueError(f"expected page selector was not found: {self.target}")
        text = self.clean(self.selected if self.target else self.fallback)
        if len(text) < 100:
            raise ValueError("extracted page text is unexpectedly short")
        return text, self.selector


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(html.unescape(href))


class Headings(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.active: str | None = None
        self.parts: list[str] = []
        self.values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"title", "h1"} and self.active is None:
            self.active = tag
            self.parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == self.active:
            value = re.sub(r"\s+", " ", "".join(self.parts)).strip()
            if value:
                self.values.append(value)
            self.active = None

    def handle_data(self, data: str) -> None:
        if self.active:
            self.parts.append(data)


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")


def repo_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("candidate path escapes the repository")
    return path


def expected_pdf(record: dict, hosts: set[str]) -> tuple[bytes, str, str, bytes]:
    landing, landing_url, media_type = fetch(record["url"], hosts)
    if media_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError("annex landing page did not return HTML")
    identifier = record.get("publisher_identifier", {}).get("Dokumentnummer")
    if not identifier:
        raise ValueError("annex record has no expected RIS Dokumentnummer")
    parser = Links()
    parser.feed(landing.decode("utf-8", "replace"))
    options = [urllib.parse.urljoin(landing_url, href) for href in parser.hrefs]
    selected = [candidate for candidate in options if identifier in candidate and ".pdf" in urllib.parse.urlparse(candidate).path.lower()]
    if len(set(selected)) != 1:
        raise ValueError(f"could not resolve one current PDF for {identifier}")
    annex_number = str(record.get("publisher_identifier", {}).get("Anlage", ""))
    expected_label = {"5": "Anlage_E", "6": "Anlage_F"}.get(annex_number)
    if expected_label and expected_label.lower() not in urllib.parse.urlparse(selected[0]).path.lower():
        raise ValueError(f"current PDF URL does not identify the expected {expected_label} form")
    time.sleep(DELAY_SECONDS)
    payload, resolved, content_type = fetch(selected[0], hosts)
    if content_type != "application/pdf" or not payload.startswith(b"%PDF-"):
        raise ValueError("linked annex is not a valid PDF response")
    return payload, resolved, content_type, landing


def extract(record: dict, raw: bytes, media_type: str, resolved_url: str) -> tuple[bytes, str]:
    candidate_id = record["id"]
    if media_type == "application/pdf":
        body = (
            f"# {record['title']}\n\n"
            f"- Candidate ID: `{candidate_id}`\n"
            f"- Official PDF URL: {record.get('url')}\n"
            f"- Resolved PDF URL: {resolved_url}\n"
            f"- Source SHA-256: `{sha(raw)}`\n"
            "- Status: unaccepted native PDF review candidate\n\n"
            "The official form is retained as a native PDF. Review its visual layout and fields; do not treat text-layer extraction as a substitute.\n"
        ).encode("utf-8")
        return body, "native PDF retention"

    if candidate_id.startswith("at-nag-") or candidate_id.startswith("at-avg-") or candidate_id.startswith("at-vwgvg-") or candidate_id.startswith("at-ifg-"):
        from scripts.convert_ris_capture import extract_text  # type: ignore
        text, _links = extract_text(raw)
        selector = "div.contentBlock"
    elif record.get("source_type") == "official_case_law":
        from scripts.convert_ris_capture import extract_text  # type: ignore
        text, _links = extract_text(raw)
        selector = "div.contentBlock"
    else:
        parser = ScopedText(candidate_id)
        parser.feed(raw.decode("utf-8", "replace"))
        text, selector = parser.result()

    if len(text) < 100:
        raise ValueError("extracted source text is unexpectedly short")
    folded = text.casefold()
    if record.get("source_type") == "national_legislation":
        identity = record.get("publisher_identifier", {})
        paragraph = identity.get("Paragraf")
        if paragraph and not re.search(rf"§\s*{re.escape(str(paragraph))}(?![0-9A-Za-z])", text):
            raise ValueError(f"expected paragraph § {paragraph} is absent from extracted text")
    elif record.get("source_type") == "official_case_law":
        case_number = record.get("publisher_identifier", {}).get("case_number")
        if case_number and case_number.casefold() not in folded:
            raise ValueError(f"expected case number {case_number} is absent")
    else:
        markers = IDENTITY_MARKERS.get(candidate_id, ())
        headings = Headings()
        headings.feed(raw.decode("utf-8", "replace"))
        identity_text = (text + " " + " ".join(headings.values)).casefold()
        if markers and not all(marker.casefold() in identity_text for marker in markers):
            raise ValueError(f"expected page identity marker is absent: {markers}")

    record_url = record["url"]
    raw_hash = sha(raw)
    markdown = (
        f"# {record['title']}\n\n"
        f"- Jurisdiction: Austria\n"
        f"- Candidate ID: `{candidate_id}`\n"
        f"- Source type: `{record.get('source_type', 'official_source')}`\n"
        f"- Candidate URL: {record_url}\n"
        f"- Resolved URL: {resolved_url}\n"
        f"- Media type: `{media_type}`\n"
        f"- Extraction: `{selector}`\n"
        f"- Exact response SHA-256: `{raw_hash}`\n\n"
        "> **Review candidate.** The source changed since the last recorded capture. Confirm identity, current version, scope, linked materials, and extraction quality before promotion.\n\n"
        "## Captured source text\n\n"
        f"{text}\n"
    ).encode("utf-8")
    return markdown, selector


def write_once(path: Path, payload: bytes) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return True


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hosts = {host.lower() for host in manifest.get("official_hosts", [])}
    if not hosts:
        raise ValueError("manifest contains no official host allowlist")
    documents = manifest.get("documents", [])
    errors: list[dict] = []
    changes: list[dict] = []
    created: list[str] = []
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw_dir = PACK / "pending-updates" / "raw"

    for index, record in enumerate(documents):
        candidate_id = record["id"]
        try:
            if record.get("native_source_path"):
                raw, resolved, media_type, landing = expected_pdf(record, hosts)
                raw_hash = sha(raw)
                observed_hash = raw_hash
            else:
                raw, resolved, media_type = fetch(record["url"], hosts)
                landing = None
                raw_hash = sha(raw)
                observed_hash = raw_hash
            prior_hash = record.get("source_sha256")
            if prior_hash and prior_hash == observed_hash:
                print(f"unchanged {candidate_id} {observed_hash}")
            else:
                if media_type == "application/pdf":
                    ext = "pdf"
                    candidate, selector = extract(record, raw, media_type, resolved)
                else:
                    if media_type not in {"text/html", "application/xhtml+xml"}:
                        raise ValueError(f"unexpected media type: {media_type}")
                    candidate, selector = extract(record, raw, media_type, resolved)
                    ext = "md"
                item_name = safe_name(candidate_id)
                pending_rel = f"source-library/austria/pending-updates/{item_name}-{observed_hash[:16]}.{ext}"
                candidate_path = repo_path(pending_rel)
                if write_once(candidate_path, candidate):
                    created.append(pending_rel)
                raw_ext = "pdf" if media_type == "application/pdf" else "html"
                raw_path = raw_dir / f"{item_name}-{observed_hash}.{raw_ext}"
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                if not raw_path.exists():
                    raw_path.write_bytes(raw)
                raw_rel = raw_path.relative_to(ROOT).as_posix()
                if landing is not None:
                    landing_path = raw_dir / f"{item_name}-{observed_hash}-landing.html"
                    if not landing_path.exists():
                        landing_path.write_bytes(landing)
                    landing_rel = landing_path.relative_to(ROOT).as_posix()
                else:
                    landing_rel = None
                changes.append({
                    "candidate_id": candidate_id,
                    "source_url": record["url"],
                    "resolved_url": resolved,
                    "previous_sha256": prior_hash,
                    "observed_sha256": observed_hash,
                    "media_type": media_type,
                    "conversion_selector": selector,
                    "pending_candidate": pending_rel,
                    "raw_capture": raw_rel,
                    "landing_capture": landing_rel,
                    "review_required": True,
                })
                print(f"changed {candidate_id} {prior_hash or 'unrecorded'} -> {observed_hash}; staged {pending_rel}")
        except Exception as exc:  # One broken publisher must not discard other observations.
            error = {"candidate_id": candidate_id, "url": record.get("url"), "error": f"{type(exc).__name__}: {exc}"}
            errors.append(error)
            print(f"review-required {candidate_id}: {error['error']}")
        if index < len(documents) - 1:
            time.sleep(DELAY_SECONDS)

    report = {
        "jurisdiction": "AT",
        "checked_at": checked_at,
        "records_checked": len(documents),
        "changed_records": changes,
        "retrieval_or_identity_failures": errors,
        "accepted_source_count": 0,
        "notes": [
            "Changed captures are staged for human review and never replace prior candidate content automatically.",
            "This run checks only the manifest's fixed records; it does not run broad case-law searches or discover all mission/Land sources.",
            "RIS OGD/API is not used.",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## Austria source monitor\n\n")
            summary.write(f"Checked {len(documents)} manifest records at {checked_at}. Staged {len(changes)} changed records; {len(errors)} retrieval/identity issues. No source was accepted.\n\n")
            for change in changes:
                summary.write(f"- **{change['candidate_id']}**: `{change['previous_sha256'] or 'unrecorded'}` → `{change['observed_sha256']}`; [review candidate](../../{change['pending_candidate']})\n")
            for error in errors:
                summary.write(f"- **Review required — {error['candidate_id']}**: {error['error']}\n")
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"created={'true' if created else 'false'}\n")
            output.write(f"pending={'true' if changes else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(PACK))
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"fatal: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
