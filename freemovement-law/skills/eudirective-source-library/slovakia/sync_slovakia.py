#!/usr/bin/env python3
"""Capture and replay Slov-Lex current, date-bound review candidates.

For each Slov-Lex act, resolve the version effective on the run date from its
official history index, then preserve the official printed HTML, binding PDF,
and linked annex PDFs. The captures remain review candidates and are not
accepted or redistributed by this script.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sync_candidate_pages as common

BASE = Path(__file__).resolve().parent
MANIFEST = BASE / "references" / "candidate-manifest.json"
CAPTURES = BASE / "references" / "slovlex-captures.json"
HOSTS = {"static.slov-lex.sk"}
MAX_ATTACHMENTS = 16


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.stack: list[str] = []
        self.skip: list[str] = []
        self.parts: list[str] = []
        self.found = False
        self.selector = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if self.skip:
            if tag not in common.Region.VOID:
                self.skip.append(tag)
            return
        if not self.found:
            if tag in {"main", "article"} or (tag in {"div", "section"} and a.get("id") in {"main", "content", "main-content"}):
                self.found = True
                self.selector = tag + (("#" + a["id"]) if a.get("id") else "")
                if tag not in common.Region.VOID:
                    self.stack.append(tag)
            elif tag == "body":
                self.found = True
                self.selector = "body"
                self.stack.append(tag)
            return
        if tag in common.SKIP:
            if tag not in common.Region.VOID:
                self.skip.append(tag)
            return
        if tag == "br":
            self.parts.append("\n")
        elif tag not in common.Region.VOID:
            self.stack.append(tag)
            if tag in common.BLOCK:
                self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.skip:
            i = len(self.skip) - 1
            while i >= 0 and self.skip[i] != tag:
                i -= 1
            if i >= 0:
                del self.skip[i:]
            return
        i = len(self.stack) - 1
        while i >= 0 and self.stack[i] != tag:
            i -= 1
        if i >= 0:
            del self.stack[i:]
            if tag in common.BLOCK:
                self.parts.append("\n")

    def handle_data(self, data):
        if self.found and self.stack and not self.skip and data.strip():
            self.parts.append(data)

    def body(self):
        text = "".join(self.parts).replace("\xa0", " ").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        out = []
        for line in lines:
            if line or (out and out[-1]):
                out.append(line)
        return "\n".join(out).strip()


def fetch(url: str):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in HOSTS:
        raise ValueError("URL outside Slov-Lex static host allowlist")
    req = urllib.request.Request(url, headers={"User-Agent": common.UA, "Accept": "text/html,application/pdf,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=common.TIMEOUT) as response:
        final = response.geturl()
        final_parsed = urllib.parse.urlparse(final)
        if final_parsed.scheme != "https" or (final_parsed.hostname or "").lower() not in HOSTS:
            raise ValueError("final URL outside Slov-Lex static host allowlist")
        data = response.read(common.MAX_BYTES + 1)
        if not data:
            raise ValueError("empty response")
        if len(data) > common.MAX_BYTES:
            raise ValueError("response exceeds shared 24 MiB cap")
        return data, final, response.headers.get_content_type().lower()


def date_for(entry: dict, as_of: dt.date) -> tuple[str, str, bytes, str, str]:
    match = re.search(r"/SK/ZZ/(\d{4})/(\d+)(?:/(\d{8}))?/?$", entry["url"])
    if not match:
        raise ValueError("candidate URL is not a Slov-Lex act route")
    year, number, pinned = match.groups()
    history_url = f"https://static.slov-lex.sk/static/SK/ZZ/{year}/{number}/"
    history, history_resolved, history_type = fetch(history_url)
    if history_type != "text/html":
        raise ValueError(f"unexpected history type {history_type}")
    text = history.decode("utf-8", "replace")
    rows = re.findall(
        r'<tr[^>]*class=["\'][^"\']*effectivenessHistoryItem[^"\']*["\'][^>]*data-iri=["\']([^"\']+)["\'][^>]*data-vyhlasene=["\']([^"\']+)["\'][^>]*data-ucinnostod=["\']([^"\']*)["\'][^>]*data-ucinnostdo=["\']([^"\']*)["\'][^>]*>',
        text,
        re.I,
    )
    if pinned:
        effective = dt.datetime.strptime(pinned, "%Y%m%d").date()
    else:
        active = []
        for _iri, _promulgated, start_text, end_text in rows:
            try:
                start = dt.date.fromisoformat(start_text)
                end = dt.date.fromisoformat(end_text) if end_text else None
            except ValueError:
                continue
            if start <= as_of and (end is None or end >= as_of):
                active.append(start)
        if not active:
            raise ValueError("official version history has no effective version for run date")
        effective = max(active)
    page_url = f"https://static.slov-lex.sk/static/SK/ZZ/{year}/{number}/{effective:%Y%m%d}.print.html"
    return year, number, history, history_resolved, page_url


def link_for_pdf(html_url: str, raw: bytes, year: str, number: str) -> tuple[str, list[str]]:
    parser = AnchorParser()
    parser.feed(raw.decode("utf-8", "replace"))
    links = [urllib.parse.urljoin(html_url, html.unescape(link)) for link in parser.links]
    # The published HTML links through /static/pdf/, while the corresponding
    # public PDF endpoint is served from /pdf/ on the same official host.
    links = [u.replace("https://static.slov-lex.sk/static/pdf/", "https://static.slov-lex.sk/pdf/") for u in links]
    prefix = f"https://static.slov-lex.sk/pdf/SK/ZZ/{year}/{number}/"
    main = next((u for u in links if u.startswith(prefix) and u.lower().endswith(".pdf")), None)
    if not main:
        raise ValueError("official print page did not link to its expected binding PDF")
    annexes = []
    for url in links:
        if "/pdf/prilohy/SK/ZZ/" in url and url.lower().endswith(".pdf") and url not in annexes:
            annexes.append(url)
    if len(annexes) > MAX_ATTACHMENTS:
        raise ValueError(f"official print page lists {len(annexes)} PDF attachments; cap is {MAX_ATTACHMENTS}")
    return main, annexes


def sync():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest["documents"]
    old_capture = json.loads(CAPTURES.read_text(encoding="utf-8")) if CAPTURES.exists() else {"records": []}
    old_by_id = {r["candidate_id"]: r for r in old_capture.get("records", [])}
    results = []
    as_of = dt.date.today()
    for entry in entries:
        if not entry["url"].startswith("https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/") or entry["id"] == "sk_01":
            continue
        print("retrieving", entry["id"], flush=True)
        try:
            year, number, history_raw, history_url, page_url = date_for(entry, as_of)
            page_raw, page_resolved, page_type = fetch(page_url)
            if page_type != "text/html":
                raise ValueError(f"unexpected print page type {page_type}")
            parser = AnchorParser()
            parser.feed(page_raw.decode("utf-8", "replace"))
            body = parser.body()
            id_pat = rf"(?<!\d){re.escape(number)}/{re.escape(year)}"
            if not re.search(id_pat, body):
                raise ValueError("printed text does not contain the candidate act identifier")
            date_pat = re.compile(r"Dátum účinnosti od:\s*(\d{2}\.\d{2}\.\d{4})", re.I)
            dates = date_pat.findall(body)
            if dates and dt.datetime.strptime(dates[0], "%d.%m.%Y").date() != dt.datetime.strptime(page_url.split("/")[-1][:8], "%Y%m%d").date():
                raise ValueError("printed text effective date differs from selected date route")
            if len(body) < 200:
                raise ValueError("official print page has no substantial source text")
            pdf_url, annex_urls = link_for_pdf(page_url, page_raw, year, number)
            pdf_raw, pdf_resolved, pdf_type = fetch(pdf_url)
            if pdf_type != "application/pdf" or not pdf_raw.startswith(b"%PDF-"):
                raise ValueError("binding document is not a valid PDF response")
            received = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            history_hash = common.sha(history_raw)
            page_hash = common.sha(page_raw)
            pdf_hash = common.sha(pdf_raw)
            slug = common.slug(entry["id"])
            history_rel = f"temp/slovakia/raw/{slug}-history-{history_hash}.html"
            page_rel = f"temp/slovakia/raw/{slug}-{page_hash}.html"
            pdf_rel = f"temp/slovakia/pdf/{slug}-{pdf_hash}.pdf"
            common.save(history_rel, history_raw)
            common.save(page_rel, page_raw)
            common.save(pdf_rel, pdf_raw)
            ann_records = []
            for i, annex_url in enumerate(annex_urls, 1):
                annex_raw, annex_final, annex_type = fetch(annex_url)
                if annex_type != "application/pdf" or not annex_raw.startswith(b"%PDF-"):
                    raise ValueError(f"attachment {i} is not a valid PDF response")
                annex_hash = common.sha(annex_raw)
                annex_rel = f"temp/slovakia/pdf/{slug}-annex-{i}-{annex_hash}.pdf"
                common.save(annex_rel, annex_raw)
                ann_records.append({"url": annex_url, "resolved_url": annex_final, "sha256": annex_hash, "bytes": len(annex_raw), "path": annex_rel})
            selector = parser.selector or "official print HTML"
            md = common.render(entry, "SK", received, page_resolved, page_type, page_hash, selector, body)
            prior = old_by_id.get(entry["id"], {})
            changed = bool(prior and prior.get("page_sha256") and (
                prior.get("page_sha256") != page_hash
                or prior.get("binding_pdf_sha256") != pdf_hash
                or sorted(a.get("sha256") for a in prior.get("annex_pdfs", [])) != sorted(a.get("sha256") for a in ann_records)
            ))
            out_rel = f"source-library/slovakia/candidates/{slug}.md"
            review_state = "review_candidate"
            if changed:
                out_rel = f"temp/slovakia/pending/{slug}-{page_hash[:16]}.md"
                review_state = "changed_pending_review"
            common.atomic(common.inside(out_rel), md)
            result = {
                "candidate_id": entry["id"], "source_url": entry["url"], "history_url": history_url,
                "history_sha256": history_hash, "history_bytes": len(history_raw), "history_path": history_rel,
                "effective_date": page_url.split("/")[-1][:8], "request_url": page_url,
                "resolved_url": page_resolved, "retrieved_at": received, "source_content_type": page_type,
                "source_bytes": len(page_raw), "page_sha256": page_hash, "raw_path": page_rel,
                "candidate_text_path": out_rel, "converted_sha256": common.sha(md), "converted_bytes": len(md),
                "content_selector": selector, "binding_pdf_url": pdf_url, "binding_pdf_resolved_url": pdf_resolved,
                "binding_pdf_sha256": pdf_hash, "binding_pdf_bytes": len(pdf_raw), "binding_pdf_path": pdf_rel,
                "annex_pdfs": ann_records, "review_state": review_state, "retrieval_status": "date_bound_text_and_binding_pdf_captured",
                "accepted": False,
            }
            results.append(result)
            print("captured", entry["id"], result["effective_date"], "annexes", len(ann_records), flush=True)
        except Exception as exc:
            result = {"candidate_id": entry["id"], "source_url": entry["url"], "retrieval_status": "retrieval_or_validation_error", "retrieval_note": f"{type(exc).__name__}: {exc}", "accepted": False}
            results.append(result)
            print("review", entry["id"], result["retrieval_note"], flush=True)
        time.sleep(common.DELAY)
    result_by_id = {r["candidate_id"]: r for r in results}
    for entry in entries:
        if entry["id"] in result_by_id:
            r = result_by_id[entry["id"]]
            entry["retrieved"] = bool(r.get("page_sha256"))
            entry["accepted"] = False
            entry["retrieval_status"] = r["retrieval_status"]
            for src, dst in (("candidate_text_path", "candidate_text_path"), ("binding_pdf_path", "candidate_source_path"), ("page_sha256", "source_sha256"), ("converted_sha256", "converted_sha256"), ("source_bytes", "source_bytes"), ("resolved_url", "resolved_url"), ("retrieval_note", "retrieval_note"), ("effective_date", "captured_effective_date")):
                if src in r:
                    entry[dst] = r[src]
    counts = {}
    for r in results:
        counts[r["retrieval_status"]] = counts.get(r["retrieval_status"], 0) + 1
    generic_path = BASE / "references" / "slovakia-capture-results.json"
    generic = json.loads(generic_path.read_text(encoding="utf-8")) if generic_path.exists() else {"records": []}
    prior_records = [r for r in generic.get("records", []) if r.get("candidate_id") not in result_by_id]
    CAPTURES.parent.mkdir(parents=True, exist_ok=True)
    CAPTURES.write_text(json.dumps({
        "jurisdiction": "SK", "as_of_date": as_of.isoformat(),
        "method": "Resolve current act edition from the official Slov-Lex per-act history index; fetch date-bound static print HTML, binding PDF, and linked official annex PDFs using ordinary allowlisted HTTPS with TLS validation.",
        "request_policy": {"timeout_seconds": common.TIMEOUT, "max_response_bytes": common.MAX_BYTES, "delay_seconds": common.DELAY, "max_annex_pdfs_per_candidate": MAX_ATTACHMENTS},
        "records": prior_records + results,
        "captured_candidate_count": sum(bool(r.get("page_sha256")) for r in results),
        "binding_pdf_count": sum(bool(r.get("binding_pdf_sha256")) for r in results),
        "accepted_source_count": 0,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    success = sum(bool(r.get("page_sha256")) for r in results)
    pdfs = sum(bool(r.get("binding_pdf_sha256")) for r in results)
    all_records = prior_records + results
    total_retrieved = sum(bool(r.get("source_sha256") or r.get("page_sha256")) for r in all_records)
    total_converted = sum(bool(r.get("candidate_text_path")) for r in all_records)
    manifest["status"] = "partially_retrieved_review_candidates"
    manifest["accepted_source_count"] = 0
    manifest["retrieved_review_candidate_count"] = total_retrieved
    manifest["converted_review_candidate_count"] = total_converted
    manifest["captured_slovlex_text_count"] = success
    manifest["captured_slovlex_binding_pdf_count"] = pdfs
    manifest["retrieval_status"] = f"{total_converted} candidate texts converted ({success} Slov-Lex legal texts via date-bound route); {pdfs} Slov-Lex binding PDFs captured; one Slov-Lex discovery page is a shell; 8 MFA requests failed; no source accepted"
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = {e["id"]: e for e in manifest["documents"]}
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    errors = []
    for record in captures["records"]:
        if record.get("retrieval_status") != "date_bound_text_and_binding_pdf_captured":
            continue
        try:
            page = common.inside(record["raw_path"]).read_bytes()
            if common.sha(page) != record["page_sha256"]:
                raise ValueError("HTML hash mismatch")
            history = common.inside(record["history_path"]).read_bytes()
            if common.sha(history) != record["history_sha256"]:
                raise ValueError("version-history hash mismatch")
            pdf = common.inside(record["binding_pdf_path"]).read_bytes()
            if common.sha(pdf) != record["binding_pdf_sha256"] or not pdf.startswith(b"%PDF-"):
                raise ValueError("binding PDF hash/signature mismatch")
            p = AnchorParser()
            p.feed(page.decode("utf-8", "replace"))
            body = p.body()
            selector = p.selector or "official print HTML"
            entry = entries[record["candidate_id"]]
            md = common.render(entry, "SK", record["retrieved_at"], record["resolved_url"], record["source_content_type"], record["page_sha256"], selector, body)
            if common.sha(md) != record["converted_sha256"] or common.sha(common.inside(record["candidate_text_path"]).read_bytes()) != record["converted_sha256"]:
                raise ValueError("HTML-to-text replay mismatch")
            for annex in record.get("annex_pdfs", []):
                raw = common.inside(annex["path"]).read_bytes()
                if common.sha(raw) != annex["sha256"] or not raw.startswith(b"%PDF-"):
                    raise ValueError("annex PDF hash/signature mismatch")
            print("verified", record["candidate_id"], record["effective_date"])
        except Exception as exc:
            errors.append(f"{record.get('candidate_id')}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"sync", "verify"}:
        raise SystemExit("usage: python sync_slovakia.py sync|verify")
    sync() if sys.argv[1] == "sync" else verify()


if __name__ == "__main__":
    main()
