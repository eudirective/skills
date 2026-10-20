#!/usr/bin/env python3
"""Retrieve current Italian statutes through public Normattiva URN pages."""
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
import http.cookiejar
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
REFS = PACK / "references"
CANDIDATES = REFS / "candidate-manifest.json"
CAPTURES = REFS / "normattiva-captures.json"
RETRIEVAL = REFS / "normattiva-retrieval-manifest.json"
HOST = "www.normattiva.it"
UA = "eudirective-source-library/1.0 (public official law text retrieval; eudirective@proton.me)"
MAX_BYTES = 16 * 1024 * 1024
TIMEOUT = 30
REQUEST_DELAY_SECONDS = 0.25
TARGET_IDS = {
    "it-01-legislative-decree-no.-30-2007-implementing-free-movement-and-residence-rig",
    "it-02-law-no.-218-1995-reforming-italian-private-international-law",
    "it-03-law-no.-184-1983-on-adoption-and-foster-care",
}
EXPECTED = {
    "it-01-legislative-decree-no.-30-2007-implementing-free-movement-and-residence-rig": ("30", "DECRETO LEGISLATIVO"),
    "it-02-law-no.-218-1995-reforming-italian-private-international-law": ("218", "LEGGE"),
    "it-03-law-no.-184-1983-on-adoption-and-foster-care": ("184", "LEGGE"),
}


class LegalText(HTMLParser):
    """Extract only the first Normattiva article-text container."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.stack: list[tuple[str, bool]] = []
        self.parts: list[str] = []
        self.found = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        target = tag == "div" and "bodyTesto" in (attrs_dict.get("class") or "").split()
        if target and self.depth == 0 and not self.found:
            self.depth = 1
            self.found = True
            self.stack.append((tag, True))
            return
        if self.depth == 0:
            if tag not in self.VOID:
                self.stack.append((tag, False))
            return
        if tag in self.VOID:
            if tag == "br":
                self.parts.append("\n")
            return
        self.depth += 1
        self.stack.append((tag, False))
        if tag in {"p", "div", "section", "h1", "h2", "h3", "h4", "ul", "ol", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        idx = len(self.stack) - 1
        while idx >= 0 and self.stack[idx][0] != tag:
            idx -= 1
        if idx < 0:
            return
        matched = self.stack[idx:]
        del self.stack[idx:]
        if self.depth == 0:
            return
        if matched[0][1]:
            self.depth = 0
        else:
            if tag in {"p", "div", "section", "h1", "h2", "h3", "h4", "ul", "ol", "li"}:
                self.parts.append("\n")
            self.depth = max(1, self.depth - len(matched))

    def handle_data(self, data: str) -> None:
        if self.depth and data.strip():
            self.parts.append(data)

    def result(self) -> str:
        raw = "".join(self.parts).replace("\xa0", " ").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
        compact: list[str] = []
        for line in lines:
            if line or (compact and compact[-1]):
                compact.append(line)
        return "\n".join(compact).strip()


class ArticleLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key.lower() == "onclick" and value:
                match = re.search(r"showArticle\(\s*'([^']+)'", value)
                if match:
                    self.links.append(html.unescape(match.group(1)))


def sha256(data: bytes) -> str:
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


def validate_url(url: str, article: bool = False) -> None:
    p = urllib.parse.urlparse(url)
    allowed_path = p.path == "/atto/caricaArticolo" if article else p.path.startswith("/uri-res/N2Ls")
    if p.scheme != "https" or (p.hostname or "").lower() != HOST or not allowed_path:
        raise ValueError(f"refused non-allowlisted Normattiva URL: {url}")


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        if p.scheme != "https" or (p.hostname or "").lower() != HOST:
            raise ValueError(f"refused cross-host Normattiva redirect: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def new_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), SameHostRedirect())


def fetch(url: str, opener: urllib.request.OpenerDirector, referer: str | None = None, xhr: bool = False) -> tuple[bytes, str, str]:
    is_article = urllib.parse.urlparse(url).path == "/atto/caricaArticolo"
    validate_url(url, article=is_article)
    headers = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    if referer:
        headers["Referer"] = referer
    if xhr:
        headers["X-Requested-With"] = "XMLHttpRequest"
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=TIMEOUT) as response:
        final = response.geturl()
        validate_url(final, article=urllib.parse.urlparse(final).path == "/atto/caricaArticolo")
        content_type = response.headers.get_content_type().lower()
        if content_type not in {"text/html", "application/xhtml+xml", "application/xml", "text/xml"}:
            raise ValueError(f"expected HTML/XML; got {content_type}")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError(f"response exceeds {MAX_BYTES} byte cap")
        if not raw.strip():
            raise ValueError("publisher returned an empty response")
        return raw, final, content_type


def page_title_version(raw: bytes, record: dict, as_of: str) -> tuple[str, str]:
    source = raw.decode("utf-8", "replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", source, re.I | re.S)
    if not title_match:
        raise ValueError("Normattiva response lacks a title")
    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", title_match.group(1))).strip()
    if "normattiva - errore" in title.lower():
        raise ValueError("publisher returned its error page, not the legal text")
    number, kind = EXPECTED[record["id"]]
    if number not in title or kind not in title.upper():
        raise ValueError(f"page title does not identify expected {kind} {number}: {title}")
    version_meta = re.search(r'property=["\']eli:version_date["\'][^>]*content=["\']([^"\']+)', source, re.I)
    if not version_meta:
        version_meta = re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']eli:version_date["\']', source, re.I)
    version = version_meta.group(1) if version_meta else ""
    if version and version > as_of:
        raise ValueError(f"publisher version date {version} is after requested date {as_of}")
    if not version:
        version = "In-force URN selector in the official link; publisher ELI version date not present in this page"
    return title, version


def article_links(raw: bytes, landing_url: str) -> list[dict]:
    parser = ArticleLinkParser()
    parser.feed(raw.decode("utf-8", "replace"))
    result: list[dict] = []
    seen: set[tuple[str, ...]] = set()
    keys = ("art.idGruppo", "art.flagTipoArticolo", "art.codiceRedazionale", "art.idArticolo", "art.idSottoArticolo", "art.idSottoArticolo1", "art.progressivo")
    for relative in parser.links:
        url = urllib.parse.urljoin(landing_url, relative)
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query, keep_blank_values=True)
        if query.get("art.imUpdate", [""])[0].lower() == "true":
            continue
        if urllib.parse.urlparse(url).path != "/atto/caricaArticolo":
            continue
        validate_url(url, article=True)
        key = tuple(query.get(k, [""])[0] for k in keys)
        if not query.get("art.idArticolo") or key in seen:
            continue
        seen.add(key)
        result.append({
            "url": url,
            "article_id": query["art.idArticolo"][0],
            "subarticle": query.get("art.idSottoArticolo", [""])[0],
            "subarticle1": query.get("art.idSottoArticolo1", [""])[0],
            "group": query.get("art.idGruppo", [""])[0],
            "version": query.get("art.versione", [""])[0],
            "redactional_code": query.get("art.codiceRedazionale", [""])[0],
        })
    if not result:
        raise ValueError("current Normattiva page exposes no article links")
    return result


def parse_article(raw: bytes, link: dict) -> tuple[str, str]:
    source = raw.decode("utf-8", "replace")
    if "<div class=\"bodyTesto\"" not in source and "<div class='bodyTesto'" not in source:
        raise ValueError(f"article {link['article_id']} response lacks its legal-text container")
    parser = LegalText()
    parser.feed(source)
    text = parser.result()
    number = re.escape(link["article_id"])
    if not re.search(rf"(?m)^Art\.\s*{number}(?!\d)", text):
        raise ValueError(f"article response does not identify Art. {link['article_id']}")
    if len(text) < 20:
        raise ValueError(f"article {link['article_id']} text is unexpectedly short ({len(text)} characters)")
    in_force = re.search(r'id=["\']artInizio["\'][^>]*>(.*?)</span>', source, re.I | re.S)
    evidence = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", in_force.group(1))).strip() if in_force else "Not shown in article response"
    return text, evidence


def bundle_digest(landing_sha: str, articles: list[dict]) -> str:
    bundle = {"landing_sha256": landing_sha, "articles": [{"url": x["url"], "sha256": x["source_sha256"]} for x in articles]}
    return sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def initial_preamble(raw: bytes) -> str:
    parser = LegalText()
    parser.feed(raw.decode("utf-8", "replace"))
    text = parser.result()
    match = re.search(r"(?m)^Art\.\s*1(?:\b|[-])", text)
    return text[:match.start()].strip() if match else ""


def markdown_content(record: dict, title: str, resolved_url: str, as_of: str, version: str, retrieved_at: str,
                     content_type: str, source_sha: str, landing_sha: str, articles: list[dict], preamble: str) -> bytes:
    lines = [
        f"# {record['title']}", "",
        "- Jurisdiction: Italy",
        f"- Candidate ID: `{record['id']}`",
        f"- Official act title: {title}",
        "- Publisher: Normattiva / Istituto Poligrafico e Zecca dello Stato",
        f"- Candidate source URL: {record['url']}",
        f"- Resolved source URL: {resolved_url}",
        f"- As-of date: {as_of}",
        f"- Publisher version evidence: {version}",
        f"- Retrieved: {retrieved_at}",
        f"- Landing content type: {content_type}",
        f"- Source bundle SHA-256: `{source_sha}`",
        f"- Landing page SHA-256: `{landing_sha}`",
        f"- Article count: {len(articles)}",
        "",
        "> **Review candidate.** This current-text capture has not been accepted into the trusted legal corpus. Verify scope, amendments, commencement and source attribution before reliance.",
        "> **Attribution:** Normattiva, Istituto Poligrafico e Zecca dello Stato.",
        "",
        "## Official current statutory text (Italian)", "",
    ]
    if preamble:
        lines.extend(["### Preamble", "", preamble, ""])
    for index, article in enumerate(articles, 1):
        lines.extend([
            f"### Article record {index}: Art. {article['article_id']}", "",
            f"- Official article URL: {article['resolved_url']}",
            f"- Normattiva article version selector: `{article['version']}`",
            f"- Effective-from evidence shown on page: {article['in_force_from']}",
            f"- Article source SHA-256: `{article['source_sha256']}`",
            "",
            article["text"], "",
        ])
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def relative_capture_path(slug: str, digest: str, ext: str) -> str:
    return f"temp/italy/raw/{slug}-{digest}.{ext}"


def store_capture(path_rel: str, raw: bytes) -> None:
    path = (ROOT / path_rel).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("refused capture path outside repository root")
    if not path.exists():
        atomic_write(path, raw)


def capture_record(record: dict, as_of: str, previous: dict | None = None) -> dict:
    opener = new_opener()
    landing_raw, landing_url, content_type = fetch(record["url"], opener)
    title, version = page_title_version(landing_raw, record, as_of)
    landing_sha = sha256(landing_raw)
    slug = re.sub(r"[^a-z0-9]+", "-", record["id"].lower()).strip("-")
    landing_path = relative_capture_path(slug, landing_sha, "html")
    store_capture(landing_path, landing_raw)
    links = article_links(landing_raw, landing_url)
    article_records: list[dict] = []
    for i, link in enumerate(links, 1):
        raw, final, article_type = fetch(link["url"], opener, referer=landing_url, xhr=True)
        text, in_force = parse_article(raw, link)
        digest = sha256(raw)
        raw_path = relative_capture_path(f"{slug}-article-{i:03d}-art-{link['article_id']}", digest, "html")
        store_capture(raw_path, raw)
        article_records.append({
            **link, "resolved_url": final, "content_type": article_type,
            "source_bytes": len(raw), "source_sha256": digest, "raw_path": raw_path,
            "converted_characters": len(text), "text": text, "in_force_from": in_force,
        })
        if i < len(links):
            time.sleep(REQUEST_DELAY_SECONDS)
        if i % 20 == 0 or i == len(links):
            print(f"  {record['id']}: captured {i}/{len(links)} article records", flush=True)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_sha = bundle_digest(landing_sha, article_records)
    prior_pending = bool(previous and previous.get("review_state") == "changed_pending_review")
    source_changed = bool(previous and previous.get("source_sha256") and previous["source_sha256"] != source_sha)
    review_state = "changed_pending_review" if prior_pending or source_changed else "current_review_candidate"
    previous_candidate_path = previous.get("previous_candidate_text_path") or previous.get("candidate_text_path") if previous else None
    if review_state == "changed_pending_review":
        if prior_pending and not source_changed:
            out_path = previous["candidate_text_path"]
        else:
            out_path = f"temp/italy/pending/{slug}-{source_sha[:16]}.md"
    else:
        out_path = f"source-library/italy/candidates/{slug}.md"
    content = markdown_content(record, title, landing_url, as_of, version, retrieved_at, content_type,
                               source_sha, landing_sha, article_records, initial_preamble(landing_raw))
    converted_sha = sha256(content)
    staged_path = f"temp/italy/staging/{slug}-{converted_sha}.md"
    store_capture(staged_path, content)
    saved_articles = [{key: value for key, value in article.items() if key != "text"} for article in article_records]
    return {
        "candidate_id": record["id"], "title": record["title"], "source_url": record["url"],
        "resolved_url": landing_url, "publisher_version_evidence": version, "as_of_date": as_of,
        "retrieved_at": retrieved_at, "content_type": content_type, "source_bytes": len(landing_raw),
        "source_sha256": source_sha, "landing_source_sha256": landing_sha,
        "landing_raw_path": landing_path, "article_count": len(article_records), "articles": saved_articles,
        "candidate_text_path": out_path, "staged_text_path": staged_path,
        "converted_bytes": len(content), "converted_sha256": converted_sha,
        "retrieval_status": "changed_review_candidate" if review_state == "changed_pending_review" else "converted_review_candidate",
        "review_state": review_state, "accepted": bool(record.get("accepted", False)),
        **({"previous_candidate_text_path": previous_candidate_path} if review_state == "changed_pending_review" and previous_candidate_path else {}),
    }


def update_manifest(results: list[dict]) -> None:
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    by_id = {x["id"]: x for x in manifest.get("documents", [])}
    for rec in results:
        item = by_id[rec["candidate_id"]]
        status = rec["retrieval_status"]
        item.update({
            "retrieved": status in {"converted_review_candidate", "changed_review_candidate", "converted_review_candidate_currentness_unverified"},
            "retrieval_status": status,
        })
        for key in ("candidate_text_path", "previous_candidate_text_path", "resolved_url", "browser_view_url", "alternate_language_url", "retrieval_checked_at", "source_sha256", "converted_sha256", "publisher_version_evidence", "retrieval_note", "article_count"):
            if key in rec:
                item[key] = rec[key]
    count = sum(x.get("retrieval_status") in {"converted_review_candidate", "changed_review_candidate", "converted_review_candidate_currentness_unverified"} for x in by_id.values())
    manifest["candidate_source_count"] = len(manifest.get("documents", []))
    manifest["accepted_source_count"] = 0
    manifest["retrieved_review_candidate_count"] = count
    manifest["status"] = "partially_retrieved_review_candidates"
    manifest["retrieval_status"] = "Three current Normattiva statutes captured article by article; any later changed source bundle is staged for review; one earlier MAECI candidate has unverified currentness; a second guidance page returned a publisher security challenge; no source accepted"
    atomic_write(CANDIDATES, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def finalize_staged_documents(results: list[dict]) -> None:
    staged: list[tuple[dict, bytes]] = []
    for rec in results:
        path_rel = rec.get("staged_text_path")
        if not path_rel:
            continue
        source = (ROOT / path_rel).resolve()
        target = (ROOT / rec["candidate_text_path"]).resolve()
        if not source.is_relative_to(ROOT) or not target.is_relative_to(ROOT):
            raise ValueError("refused staged conversion path outside repository root")
        content = source.read_bytes()
        if sha256(content) != rec["converted_sha256"]:
            raise ValueError(f"staged conversion hash mismatch for {rec['candidate_id']}")
        staged.append((rec, content))
    for rec, content in staged:
        atomic_write(ROOT / rec["candidate_text_path"], content)
        (ROOT / rec["staged_text_path"]).unlink(missing_ok=True)
        rec.pop("staged_text_path", None)


def sync() -> None:
    as_of = date.today().isoformat()
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    prior_capture = json.loads(CAPTURES.read_text(encoding="utf-8")) if CAPTURES.exists() else {"records": []}
    previous_by_id = {x["candidate_id"]: x for x in prior_capture.get("records", []) if x.get("articles")}
    results: list[dict] = []
    for record in manifest.get("documents", []):
        if record["id"] in TARGET_IDS:
            print(f"retrieving {record['id']}", flush=True)
            results.append(capture_record(record, as_of, previous_by_id.get(record["id"])))
    prior_maeci = next((x for x in manifest.get("documents", []) if x["id"].startswith("it-05-")), None)
    if prior_maeci:
        results.append({
            "candidate_id": prior_maeci["id"], "title": prior_maeci["title"], "source_url": prior_maeci["url"],
            "resolved_url": "https://validate.perfdrive.com/ (official host redirects to publisher security challenge)",
            "retrieval_status": "converted_review_candidate_currentness_unverified", "accepted": False,
            "browser_view_url": prior_maeci.get("browser_view_url", prior_maeci["url"]),
            "alternate_language_url": prior_maeci.get("alternate_language_url"),
            "retrieval_checked_at": as_of,
            "retrieval_note": "Prior 15 October 2026 English review candidate retained without raw HTML for replay. Current page is visible in the standard web view, but direct HTTP retrieval returns a publisher security challenge and no dependable version date is exposed; currentness remains unverified. No challenge bypass was attempted.",
        })
    guidance = next((x for x in manifest.get("documents", []) if x["id"].startswith("it-04-")), None)
    if guidance:
        results.append({
            "candidate_id": guidance["id"], "title": guidance["title"], "source_url": guidance["url"],
            "resolved_url": "https://validate.perfdrive.com/ (official host redirects to publisher security challenge)",
            "retrieval_status": "publisher_security_challenge", "accepted": False,
            "browser_view_url": guidance.get("browser_view_url", guidance["url"]),
            "retrieval_checked_at": as_of,
            "retrieval_note": "The current official page is visible in the standard web view, but direct HTTP retrieval returned the publisher security challenge, so no local raw capture or conversion is available. No challenge bypass was attempted. Official embassy pages also publish related guidance, but their local scope differs.",
        })
    retrieval = {
        "manifest_version": 2, "jurisdiction": "Italy", "as_of_date": as_of,
        "method": "For three Normattiva acts, use each stable URN page with its current-text selector, retain the session cookie from that public page, collect the article links published by the page, and request each linked article through the site's own XHR page flow. The site states in its page markup that article content is loaded dynamically. This requires no account or email registration, but the article endpoint is an undocumented page interface and is rated fragile. The two MAECI pages are readable in the standard web view but redirect direct HTTP requests to the publisher's security challenge; no challenge bypass is used.",
        "open_data_documentation": "https://dati.normattiva.it/Come-scaricare-i-dati",
        "normattiva_versioning_documentation": "https://www.normattiva.it/staticPage/utilita",
        "article_endpoint_note": "The article URLs are extracted from the current official HTML page's showArticle links. Requests are limited to the allowlisted Normattiva host and article path, reuse the page session, include the page as Referer and the X-Requested-With header, and are spaced by 0.25 seconds.",
        "change_detection": "Compare the bundle hash over the landing page and ordered article responses with the last capture. If changed, save the new conversion under temp/italy/pending and mark changed_review_candidate; do not overwrite the prior candidate. Repeated syncs keep the pending review state until a reviewer resolves it.",
        "maeci_access_note": "Direct HTTP requests to canonical Italian and English MAECI pages returned Radware security challenge content. The pages are readable in the standard web view, but no raw response was available for offline replay. No challenge bypass was attempted.",
        "accepted_source_count": 0, "records": results,
    }
    finalize_staged_documents(results)
    atomic_write(CAPTURES, (json.dumps(retrieval, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    atomic_write(RETRIEVAL, (json.dumps(retrieval, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    update_manifest(results)


def verify() -> None:
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    documents = {x["id"]: x for x in json.loads(CANDIDATES.read_text(encoding="utf-8"))["documents"]}
    errors: list[str] = []
    for rec in (x for x in captures.get("records", []) if x.get("articles")):
        try:
            landing = (ROOT / rec["landing_raw_path"]).read_bytes()
            if sha256(landing) != rec["landing_source_sha256"]:
                raise ValueError("landing-page source hash mismatch")
            title, version = page_title_version(landing, documents[rec["candidate_id"]], rec["as_of_date"])
            links = article_links(landing, rec["resolved_url"])
            if len(links) != rec["article_count"] or len(links) != len(rec["articles"]):
                raise ValueError("article-link inventory count differs from saved capture")
            replay_articles: list[dict] = []
            for link, saved in zip(links, rec["articles"], strict=True):
                if link["url"] != saved["url"]:
                    raise ValueError("article URL order differs from official page")
                raw = (ROOT / saved["raw_path"]).read_bytes()
                if sha256(raw) != saved["source_sha256"]:
                    raise ValueError(f"article {link['article_id']} source hash mismatch")
                text, in_force = parse_article(raw, link)
                if len(text) != saved["converted_characters"] or in_force != saved["in_force_from"]:
                    raise ValueError(f"article {link['article_id']} extraction replay differs")
                replay_articles.append({**saved, "text": text, "in_force_from": in_force})
            source_sha = bundle_digest(rec["landing_source_sha256"], replay_articles)
            if source_sha != rec["source_sha256"]:
                raise ValueError("source bundle hash mismatch")
            content = markdown_content(documents[rec["candidate_id"]], title, rec["resolved_url"], rec["as_of_date"], version,
                                       rec["retrieved_at"], rec["content_type"], source_sha, rec["landing_source_sha256"],
                                       replay_articles, initial_preamble(landing))
            if sha256(content) != rec["converted_sha256"]:
                raise ValueError("deterministic conversion hash mismatch")
            if sha256((ROOT / rec["candidate_text_path"]).read_bytes()) != rec["converted_sha256"]:
                raise ValueError("saved Markdown differs from replay")
            print(f"verified {rec['candidate_id']}: {rec['article_count']} articles")
        except Exception as exc:
            errors.append(f"{rec.get('candidate_id', 'unknown')}: {type(exc).__name__}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "sync":
        sync()
    elif mode == "verify":
        verify()
    else:
        raise SystemExit("usage: sync_italy.py [sync|verify]")


if __name__ == "__main__":
    main()
