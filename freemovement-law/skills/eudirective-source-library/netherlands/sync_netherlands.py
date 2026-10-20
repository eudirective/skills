#!/usr/bin/env python3
"""Retrieve bounded Netherlands law and IND guidance candidates from official pages."""
from __future__ import annotations

import hashlib
import json
import re
import ssl
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
REFS = PACK / "references"
CANDIDATES = REFS / "candidate-manifest.json"
CAPTURES = REFS / "official-page-captures.json"
RETRIEVAL = REFS / "official-page-retrieval-manifest.json"
UA = "eudirective-source-library/1.0 (bounded official source retrieval; eudirective@proton.me)"
MAX_BYTES = 24 * 1024 * 1024
TIMEOUT = 30


class MainText(HTMLParser):
    """Extract the official regeling container or an IND main element."""

    BLOCKS = {"p", "div", "section", "article", "li", "tr", "blockquote", "ul", "ol", "table"}
    HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####"}

    def __init__(self, target: str):
        super().__init__(convert_charrefs=True)
        self.target = target
        self.depth = 0
        self.skip_depth: int | None = None
        self.stack: list[tuple[str, bool, bool]] = []
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        classes = set((a.get("class") or "").lower().split())
        start_target = (
            self.target == "regeling" and tag == "div" and a.get("id") == "regeling"
        ) or (self.target == "main" and tag == "main")
        if start_target and self.depth == 0:
            self.depth = 1
            self.stack.append((tag, True, False))
            return
        if self.depth == 0:
            self.stack.append((tag, False, False))
            return
        self.depth += 1
        skip = self.skip_depth is not None
        if not skip and (
            tag in {"script", "style", "nav", "button", "form"}
            or "visually-hidden" in classes
            or any(c.startswith("action--") for c in classes)
            or "actionblock" in classes
            or "skiplink" in classes
        ):
            self.skip_depth = self.depth
            skip = True
        self.stack.append((tag, False, skip))
        if skip:
            return
        if tag in self.HEADINGS:
            self.parts.extend(["\n\n", self.HEADINGS[tag] + " "])
        elif tag in self.BLOCKS:
            self.parts.append("\n\n")
            if tag == "li":
                self.parts.append("- ")
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "td":
            self.parts.append(" | ")

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
        was_target = matched[0][1]
        if not was_target:
            skip_here = self.skip_depth is not None and self.depth >= self.skip_depth
            if not skip_here and tag in self.BLOCKS | set(self.HEADINGS):
                self.parts.append("\n\n")
            if self.skip_depth is not None and self.depth == self.skip_depth:
                self.skip_depth = None
            self.depth = max(1, self.depth - len(matched))
        else:
            self.depth = 0
            self.skip_depth = None

    def handle_data(self, data: str) -> None:
        if self.depth and self.skip_depth is None and data.strip():
            self.parts.append(data)

    def result(self) -> str:
        out = "".join(self.parts).replace("\xa0", " ")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in out.splitlines()]
        compact: list[str] = []
        for line in lines:
            if line or (compact and compact[-1]):
                compact.append(line)
        return "\n".join(compact).strip()


LAW_IDS = {
    "nl-01-vreemdelingenbesluit-2000-eu-eea-family-provisions-(including-article-8.7)": "BWBR0011825",
    "nl-03-burgerlijk-wetboek-boek-10-foreign-marriage-recognition-provisions": "BWBR0030068",
    "nl-04-burgerlijk-wetboek-boek-1-civil-status-and-parentage-provisions": "BWBR0002656",
    "nl-05-wet-opneming-buitenlandse-kinderen-ter-adoptie": "BWBR0004447",
    "nl-06-vreemdelingenwet-2000": "BWBR0011823",
    "nl-08-algemene-wet-bestuursrecht-(general-administrative-law-act)": "BWBR0005537",
}
GUIDANCE_IDS = {
    "nl-02-ind-procedure:-verification-against-eu-law-for-family-members-of-union-citi",
    "nl-07-ind-guidance-on-objecting-to-or-appealing-an-ind-decision",
}


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


def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-.")


def fetch(url: str) -> tuple[bytes, str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"wetten.overheid.nl", "ind.nl"}:
        raise ValueError(f"refused non-allowlisted official host: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as response:
        final = response.geturl()
        if urllib.parse.urlparse(final).hostname not in {"wetten.overheid.nl", "ind.nl"}:
            raise ValueError(f"redirect left allowlist: {final}")
        content_type = response.headers.get_content_type().lower()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"expected HTML, got {content_type}")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError(f"response exceeds {MAX_BYTES} byte cap")
        return raw, final, content_type


def title_from_html(raw: bytes, selector: str) -> str:
    s = raw.decode("utf-8", "replace")
    if selector == "regeling":
        m = re.search(r'<div\s+id=["\']regeling["\']\s*>\s*<h1[^>]*>(.*?)</h1>', s, re.I | re.S)
    else:
        m = re.search(r'<main\b[^>]*>.*?<h1[^>]*>(.*?)</h1>', s, re.I | re.S)
    if not m:
        raise ValueError(f"could not find expected {selector} title")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip()


def current_alias(record: dict) -> tuple[str, str, str]:
    cid = record["id"]
    if cid in LAW_IDS:
        bid = LAW_IDS[cid]
        return f"https://wetten.overheid.nl/{bid}/", "regeling", bid
    if cid in GUIDANCE_IDS:
        return record["url"], "main", ""
    raise ValueError(f"no retrieval mapping for candidate {cid}")


def date_status(body: str, as_of: str, is_law: bool) -> str:
    if not is_law:
        return ""
    m = re.search(r"Geldend van\s+(\d{2}-\d{2}-\d{4})\s+t/m\s+(heden|\d{2}-\d{2}-\d{4})", body, re.I)
    if not m:
        raise ValueError("current-law page lacks a recognized effective-period marker")
    start = datetime.strptime(m.group(1), "%d-%m-%Y").date()
    end = None if m.group(2).lower() == "heden" else datetime.strptime(m.group(2), "%d-%m-%Y").date()
    requested = date.fromisoformat(as_of)
    if start > requested or (end and end < requested):
        raise ValueError(f"publisher text validity {m.group(0)!r} does not cover {as_of}")
    return m.group(0)


def update_manifest(results: list[dict]) -> None:
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    by_id = {x["id"]: x for x in manifest.get("documents", [])}
    for rec in results:
        item = by_id[rec["candidate_id"]]
        item.update({
            "retrieval_status": "converted_review_candidate",
            "retrieved": True,
            "accepted": False,
            "candidate_text_path": rec["candidate_text_path"],
            "retrieved_source_url": rec["source_url"],
            "resolved_url": rec["resolved_url"],
            "source_sha256": rec["source_sha256"],
            "converted_sha256": rec["converted_sha256"],
            "publisher_version_evidence": rec.get("publisher_version_evidence", ""),
        })
    manifest["candidate_source_count"] = len(manifest.get("documents", []))
    manifest["accepted_source_count"] = 0
    manifest["status"] = "partially_retrieved_review_candidates"
    count = sum(x.get("retrieval_status") == "converted_review_candidate" for x in by_id.values())
    manifest["retrieved_review_candidate_count"] = count
    manifest["retrieval_status"] = f"{count} of {len(by_id)} scoped source-list candidates converted; all remain unaccepted; wider monitor inventory remains discovery-only"
    atomic_write(CANDIDATES, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sync() -> None:
    as_of = date.today().isoformat()
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    old = json.loads(CAPTURES.read_text(encoding="utf-8")) if CAPTURES.exists() else {"records": []}
    previous = {x["candidate_id"]: x for x in old.get("records", [])}
    results: list[dict] = []
    errors: list[str] = []
    for record in manifest.get("documents", []):
        if record["id"] not in LAW_IDS and record["id"] not in GUIDANCE_IDS:
            continue
        try:
            url, selector, publisher_id = current_alias(record)
            raw, final, content_type = fetch(url)
            title = title_from_html(raw, selector)
            body_parser = MainText(selector)
            body_parser.feed(raw.decode("utf-8", "replace"))
            body = body_parser.result()
            if len(body) < 800:
                raise ValueError(f"extracted content is unexpectedly short: {len(body)} characters")
            if selector == "regeling":
                if publisher_id not in final:
                    raise ValueError(f"resolved URL does not identify {publisher_id}: {final}")
                version = date_status(body, as_of, True)
            else:
                version_match = re.search(r"(?:Last updated|Last update|Updated)\s*:?\s*([^\n]+)", body, re.I)
                version = version_match.group(0) if version_match else "No visible update date captured"
            digest = sha256(raw)
            retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            raw_path = f"temp/netherlands/raw/{safe_id(record['id'])}-{digest}.html"
            raw_out = (ROOT / raw_path).resolve()
            if not raw_out.is_relative_to(ROOT):
                raise ValueError("refused capture path outside repository root")
            if not raw_out.exists():
                atomic_write(raw_out, raw)
            out_path = f"source-library/netherlands/candidates/{safe_id(record['id'])}.md"
            output = "\n".join([
                f"# {title}", "",
                "- Jurisdiction: Netherlands",
                f"- Candidate ID: `{record['id']}`",
                f"- Candidate register title: {record['title']}",
                f"- Publisher: {'Wetten.nl / Government of the Netherlands' if selector == 'regeling' else 'Immigration and Naturalisation Service (IND)'}",
                f"- Official source URL: {record['url']}",
                f"- Retrieved from current source route: {final}",
                f"- Publisher version marker: {version}",
                f"- Retrieved: {retrieved_at}",
                f"- Content type: {content_type}",
                f"- Source SHA-256: `{digest}`",
                "",
                "> **Review candidate.** This capture has not been accepted into the trusted legal corpus. Review source scope, language, currentness, and downstream use before relying on it.",
                "",
                body,
                "",
            ]).encode("utf-8")
            atomic_write(ROOT / out_path, output)
            results.append({
                "candidate_id": record["id"], "candidate_title": record["title"],
                "publisher_id": publisher_id, "source_url": record["url"], "resolved_url": final,
                "publisher_version_evidence": version, "content_type": content_type,
                "source_bytes": len(raw), "source_sha256": digest, "raw_path": raw_path,
                "candidate_text_path": out_path, "converted_bytes": len(output),
                "converted_sha256": sha256(output), "retrieved_at": retrieved_at,
                "as_of_date": as_of, "retrieval_status": "converted_review_candidate", "accepted": False,
            })
            print(f"converted {record['id']} ({len(body)} extracted characters)")
        except Exception as exc:
            errors.append(f"{record['id']}: {type(exc).__name__}: {exc}")
            print(f"review {record['id']}: {type(exc).__name__}: {exc}")
    captures = {"jurisdiction": "Netherlands", "as_of_date": as_of, "records": results}
    atomic_write(CAPTURES, (json.dumps(captures, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    retrieval = {
        "manifest_version": 1, "jurisdiction": "Netherlands", "as_of_date": as_of,
        "method": "Current Wetten.nl pages are resolved from the official stable BWBR identifier; the page's exact effective interval, document ID, HTML source and content hash are retained. IND guidance is refreshed only at its identified public page. Extraction is restricted to the official regeling or main element, with no account workflow or personal submissions.",
        "records": results, "accepted_source_count": 0,
    }
    atomic_write(RETRIEVAL, (json.dumps(retrieval, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    update_manifest(results)
    if errors:
        raise SystemExit("\n".join(errors))


def verify() -> None:
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    manifest = {x["id"]: x for x in json.loads(CANDIDATES.read_text(encoding="utf-8"))["documents"]}
    retrieval = json.loads(RETRIEVAL.read_text(encoding="utf-8"))
    errors: list[str] = []
    for rec in retrieval.get("records", []):
        try:
            raw = (ROOT / rec["raw_path"]).read_bytes()
            if sha256(raw) != rec["source_sha256"]:
                raise ValueError("raw HTML hash mismatch")
            selector = "regeling" if rec.get("publisher_id") else "main"
            title = title_from_html(raw, selector)
            parser = MainText(selector)
            parser.feed(raw.decode("utf-8", "replace"))
            body = parser.result()
            if selector == "regeling":
                date_status(body, rec["as_of_date"], True)
            output = "\n".join([
                f"# {title}", "",
                "- Jurisdiction: Netherlands",
                f"- Candidate ID: `{rec['candidate_id']}`",
                f"- Candidate register title: {manifest[rec['candidate_id']]['title']}",
                f"- Publisher: {'Wetten.nl / Government of the Netherlands' if selector == 'regeling' else 'Immigration and Naturalisation Service (IND)'}",
                f"- Official source URL: {rec['source_url']}",
                f"- Retrieved from current source route: {rec['resolved_url']}",
                f"- Publisher version marker: {rec['publisher_version_evidence']}",
                f"- Retrieved: {rec['retrieved_at']}",
                f"- Content type: {rec['content_type']}",
                f"- Source SHA-256: `{rec['source_sha256']}`",
                "",
                "> **Review candidate.** This capture has not been accepted into the trusted legal corpus. Review source scope, language, currentness, and downstream use before relying on it.",
                "", body, "",
            ]).encode("utf-8")
            if sha256(output) != rec["converted_sha256"]:
                raise ValueError("deterministic conversion hash mismatch")
            if sha256((ROOT / rec["candidate_text_path"]).read_bytes()) != rec["converted_sha256"]:
                raise ValueError("saved Markdown differs from replay")
            print(f"verified {rec['candidate_id']}")
        except Exception as exc:
            errors.append(f"{rec['candidate_id']}: {type(exc).__name__}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "sync":
        sync()
    elif mode == "verify":
        verify()
    else:
        raise SystemExit("usage: sync_netherlands.py [sync|verify]")


if __name__ == "__main__":
    main()
