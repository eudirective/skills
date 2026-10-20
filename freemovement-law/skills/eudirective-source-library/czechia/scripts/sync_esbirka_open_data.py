#!/usr/bin/env python3
"""Capture current Czech legal text from e-Sbírka's public page data service.

The route is the same read-only, unauthenticated service used by the public
e-Sbírka page. It resolves the current version from a stable act URL, then
returns that version's ordered text fragments as JSON. This does not use the
registration-gated REST API or claim the consolidated text is authentic
promulgation.
"""
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
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
ROOT = PACK.parents[1]
PROJECT_TEMP = ROOT / "temp"
REFERENCES = PACK / "references"
SOURCE_MANIFEST = REFERENCES / "candidate-manifest.json"
CAPTURE_MANIFEST = REFERENCES / "esbirka-open-data-captures.json"
HOST = "e-sbirka.gov.cz"
BASE = f"https://{HOST}/sbr-externi"
USER_AGENT = "eudirective-source-library/1.0 (bounded official text retrieval; eudirective@proton.me)"
TIMEOUT = 30
MAX_RESPONSE_BYTES = 24 * 1024 * 1024
REQUEST_DELAY = 0.2


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inside_pack(relative: str) -> Path:
    path = (PACK / relative).resolve()
    if not path.is_relative_to(PACK.resolve()):
        raise ValueError(f"unsafe pack path: {relative}")
    return path


def in_project_temp(relative: str) -> Path:
    """Resolve operational work paths in the project temp tree, not the pack."""
    path = inside_pack(relative)
    if not relative.replace("\\", "/").startswith("work/"):
        raise ValueError(f"expected a work path: {relative}")
    return (PROJECT_TEMP / path.relative_to(ROOT)).resolve()


def artifact_path(relative: str) -> Path:
    """Candidates are library artifacts; raw and pending files are temporary."""
    portable = relative.replace("\\", "/")
    if portable.startswith(("work/raw/", "work/pending/")):
        return in_project_temp(portable)
    return inside_pack(portable)


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


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != HOST:
            raise ValueError(f"refused redirect outside official e-Sbírka host: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_json(url: str) -> tuple[bytes, dict]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != HOST:
        raise ValueError(f"refused non-allowlisted e-Sbírka URL: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    opener = urllib.request.build_opener(SameHostRedirect())
    with opener.open(request, timeout=TIMEOUT) as response:
        final = urllib.parse.urlparse(response.geturl())
        if final.scheme != "https" or (final.hostname or "").lower() != HOST:
            raise ValueError(f"refused final URL outside official e-Sbírka host: {response.geturl()}")
        if response.headers.get_content_type().lower() != "application/json":
            raise ValueError(f"unexpected media type {response.headers.get_content_type()} from {url}")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError(f"response exceeds {MAX_RESPONSE_BYTES} byte cap")
        if not raw:
            raise ValueError(f"empty response from {url}")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON response from {url}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object from {url}")
    return raw, value


class PlainText(HTMLParser):
    """Extract visible inline text from e-Sbírka's fragment XHTML."""

    BLOCKS = {"br", "p", "div", "li", "ul", "ol", "table", "tr", "td", "th"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        value = "".join(self.parts).replace("\xa0", " ").replace("\r", "\n")
        lines = [re.sub(r"[\t ]+", " ", line).strip() for line in value.splitlines()]
        result: list[str] = []
        for line in lines:
            if line or (result and result[-1]):
                result.append(line)
        return "\n".join(result).strip()


def fragment_text(fragment: dict) -> str:
    source = fragment.get("xhtml")
    if not isinstance(source, str) or not source.strip():
        return ""
    parser = PlainText()
    parser.feed(source)
    parser.close()
    return parser.text()


def render_markdown(entry: dict, metadata: dict, fragments: list[dict], capture: dict) -> bytes:
    title = entry.get("title", entry["id"])
    current_url = f"https://{HOST}{metadata['staleUrl']}"
    lines = [
        f"# {title}",
        "",
        f"- Jurisdiction: Czechia",
        f"- Candidate ID: `{entry['id']}`",
        f"- Source type: `{entry.get('source_type', 'national_legislation')}`",
        f"- Official stable record: {entry['url']}",
        f"- Current version text: {current_url}",
        f"- Publisher citation: {metadata.get('uplnaCitace', metadata.get('zkracenaCitace', ''))}",
        f"- Publisher version type: `{metadata.get('typZneni', 'unknown')}`",
        f"- Version effective from: `{metadata['datumUcinnostiZneniOd']}`",
        f"- Source retrieval: public e-Sbírka page-data route; no account or API key used",
        f"- Exact response set SHA-256: `{capture['source_sha256']}`",
        f"- Fragment pages: {capture['page_count']}; text fragments: {capture['text_fragment_count']}",
        "",
        "> **Review candidate.** Use this official e-Sbírka consolidated text as a dated working version and retain its informational status. Check a known later change or commencement issue only when relevant; no full Gazette history is required.",
        "",
        "## Official text",
        "",
    ]
    in_footnotes = False
    heading_kinds = {
        "Cast": 2,
        "Hlava": 3,
        "Dil": 3,
        "Díl": 3,
        "Oddil": 4,
        "Oddíl": 4,
        "Pododdil": 5,
        "Pododdíl": 5,
        "Paragraf": 4,
        "Clanek": 4,
        "Článek": 4,
        "Nadpis_pod": 5,
    }
    for fragment in fragments:
        text = fragment_text(fragment)
        if not text:
            continue
        kind = str(fragment.get("kodTypuFragmentu", ""))
        if kind in {"PPC", "Virtual_PPC"} and not in_footnotes:
            lines.extend(["", "## Poznámky pod čarou", ""])
            in_footnotes = True
        heading = heading_kinds.get(kind)
        if heading:
            lines.append("#" * heading + " " + text.replace("\n", " "))
            lines.append("")
        else:
            depth = fragment.get("hloubka", 0)
            indent = "  " * max(0, min(int(depth or 0) - 4, 4))
            lines.extend(indent + part for part in text.splitlines())
            lines.append("")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def legal_entries(manifest: dict) -> list[dict]:
    return [
        item for item in manifest.get("documents", [])
        if item.get("id", "").startswith("cz-esbirka-")
    ]


def record_url(entry: dict) -> tuple[int, int, str]:
    parsed = urllib.parse.urlparse(entry["url"])
    if (parsed.hostname or "").lower() not in {HOST, "www.e-sbirka.cz"}:
        raise ValueError("candidate record is not hosted by e-Sbírka")
    match = re.fullmatch(r"/sb/(\d{4})/(\d+)", parsed.path)
    if not match:
        raise ValueError(f"unexpected e-Sbírka stable record path: {parsed.path}")
    year, number = int(match.group(1)), int(match.group(2))
    return year, number, f"/sb/{year}/{number}"


def current_metadata(stable_path: str, year: int, number: int) -> tuple[bytes, dict]:
    url = BASE + "/dokumenty-sbirky/" + urllib.parse.quote(stable_path, safe="")
    raw, data = fetch_json(url)
    if data.get("typZneni") != "AKTUALNI":
        raise ValueError(f"e-Sbírka did not resolve an active current version: {data.get('typZneni')}")
    citation = str(data.get("kodDokumentuSbirky", ""))
    if citation != f"{number}/{year} Sb.":
        raise ValueError(f"act identity mismatch: expected {number}/{year} Sb., received {citation!r}")
    current_path = data.get("staleUrl")
    if not isinstance(current_path, str) or not re.fullmatch(rf"/sb/{year}/{number}/\d{{4}}-\d{{2}}-\d{{2}}", current_path):
        raise ValueError(f"unexpected current-version URL: {current_path!r}")
    date = data.get("datumUcinnostiZneniOd")
    if date != current_path.rsplit("/", 1)[-1]:
        raise ValueError("effective date does not match the current-version URL")
    return raw, data


def capture_entry(entry: dict, previous: dict | None) -> tuple[dict, bytes]:
    year, number, stable_path = record_url(entry)
    metadata_bytes, metadata = current_metadata(stable_path, year, number)
    current_path = metadata["staleUrl"]
    page_count: int | None = None
    fragments: list[dict] = []
    page_records: list[dict] = []
    fragment_ids: set[str] = set()
    for page_number in range(100):
        page_url = BASE + "/dokumenty-sbirky/" + urllib.parse.quote(current_path, safe="") + "/fragmenty?cisloStranky=" + str(page_number)
        raw_page, page = fetch_json(page_url)
        if page_count is None:
            page_count = page.get("pocetStranek")
            if not isinstance(page_count, int) or not (1 <= page_count <= 100):
                raise ValueError(f"invalid fragment page count: {page_count!r}")
        elif page.get("pocetStranek") != page_count:
            raise ValueError("fragment page count changed during retrieval")
        page_fragments = page.get("seznam")
        if not isinstance(page_fragments, list):
            raise ValueError(f"fragment page {page_number} has no fragment list")
        if not page_fragments:
            raise ValueError(f"empty fragment page {page_number}")
        for fragment in page_fragments:
            if not isinstance(fragment, dict):
                raise ValueError(f"invalid fragment record on page {page_number}")
            fragment_stale_url = str(fragment.get("staleUrl", "")).split("#", 1)[0]
            fragment_eli = str(fragment.get("eli", ""))
            current_eli = str(metadata.get("eli", ""))
            if fragment_stale_url:
                if fragment_stale_url != current_path:
                    raise ValueError(f"fragment belongs to a different version: {fragment.get('staleUrl')}")
            elif not current_eli or not fragment_eli.startswith(current_eli):
                raise ValueError(f"fragment has no matching current-version identity: {fragment_eli!r}")
            fragment_id = str(fragment.get("eli", ""))
            if not fragment_id or fragment_id in fragment_ids:
                raise ValueError(f"missing or duplicate fragment identifier: {fragment_id!r}")
            fragment_ids.add(fragment_id)
            fragments.append(fragment)
        digest = sha256(raw_page)
        rel = f"work/raw/esbirka-open-data/{entry['id']}/{metadata['datumUcinnostiZneniOd']}/page-{page_number:03d}-{digest}.json"
        atomic_write(in_project_temp(rel), raw_page)
        page_records.append({
            "page_number": page_number,
            "raw_path": rel,
            "source_sha256": digest,
            "source_bytes": len(raw_page),
            "fragment_count": len(page_fragments),
        })
        time.sleep(REQUEST_DELAY)
        if page_number + 1 >= page_count:
            break
    else:
        raise ValueError("fragment page limit exceeded")
    if page_count is None or len(page_records) != page_count:
        raise ValueError("not all fragment pages were captured")
    text_fragment_count = sum(bool(fragment_text(fragment)) for fragment in fragments)
    if text_fragment_count < 10:
        raise ValueError(f"too few text-bearing fragments: {text_fragment_count}")
    source_digest = hashlib.sha256()
    source_digest.update(len(metadata_bytes).to_bytes(8, "big"))
    source_digest.update(metadata_bytes)
    for record in page_records:
        raw = in_project_temp(record["raw_path"]).read_bytes()
        source_digest.update(len(raw).to_bytes(8, "big"))
        source_digest.update(raw)
    source_hash = source_digest.hexdigest()
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    metadata_rel = f"work/raw/esbirka-open-data/{entry['id']}/{metadata['datumUcinnostiZneniOd']}/metadata-{sha256(metadata_bytes)}.json"
    atomic_write(in_project_temp(metadata_rel), metadata_bytes)
    rec = {
        "candidate_id": entry["id"],
        "source_url": entry["url"],
        "request_url": BASE + "/dokumenty-sbirky/" + urllib.parse.quote(stable_path, safe=""),
        "resolved_url": f"https://{HOST}{current_path}",
        "publisher_citation": metadata.get("uplnaCitace", metadata.get("zkracenaCitace")),
        "publisher_code": metadata.get("kodDokumentuSbirky"),
        "version_type": metadata.get("typZneni"),
        "version_effective_from": metadata["datumUcinnostiZneniOd"],
        "eli": metadata.get("eli"),
        "retrieved_at": retrieved_at,
        "metadata_raw_path": metadata_rel,
        "metadata_sha256": sha256(metadata_bytes),
        "pages": page_records,
        "page_count": page_count,
        "fragment_count": len(fragments),
        "text_fragment_count": text_fragment_count,
        "source_sha256": source_hash,
        "accepted": False,
    }
    markdown = render_markdown(entry, metadata, fragments, rec)
    rec["converted_sha256"] = sha256(markdown)
    rec["converted_bytes"] = len(markdown)
    if previous and previous.get("source_sha256") == source_hash:
        target = previous.get("candidate_text_path")
        previous_path = artifact_path(target) if isinstance(target, str) else None
        if previous_path and previous_path.is_file() and sha256(previous_path.read_bytes()) == previous.get("converted_sha256"):
            rec["candidate_text_path"] = target
            rec["retrieval_status"] = "converted_review_candidate"
            rec["review_state"] = "review_candidate"
            return rec, markdown
    changed = bool(previous and previous.get("source_sha256") and previous.get("source_sha256") != source_hash)
    normal_rel = f"candidates/legislation/{entry['id']}.md"
    normal_path = inside_pack(normal_rel)
    if changed or (normal_path.exists() and sha256(normal_path.read_bytes()) != sha256(markdown)):
        target = f"work/pending/{entry['id']}-{metadata['datumUcinnostiZneniOd']}-{source_hash[:16]}.md"
        rec["retrieval_status"] = "changed_review_candidate"
        rec["review_state"] = "changed_pending_review"
    else:
        target = normal_rel
        rec["retrieval_status"] = "converted_review_candidate"
        rec["review_state"] = "review_candidate"
    atomic_write(artifact_path(target), markdown)
    rec["candidate_text_path"] = target
    return rec, markdown


def update_manifests(manifest: dict, capture: dict) -> None:
    documents = {item["id"]: item for item in manifest.get("documents", [])}
    for rec in capture.get("records", []):
        item = documents.get(rec["candidate_id"])
        if not item:
            continue
        item["retrieved"] = bool(rec.get("source_sha256"))
        item["accepted"] = False
        item["retrieval_status"] = rec.get("retrieval_status", "retrieval_or_conversion_error")
        item["retrieval_method"] = "esbirka_public_current_version_fragment_service"
        for key in ("candidate_text_path", "source_sha256", "converted_sha256", "resolved_url", "version_effective_from", "publisher_citation", "retrieval_note"):
            if key in rec:
                item[key] = rec[key]
            else:
                item.pop(key, None)
    entries = legal_entries(manifest)
    all_documents = manifest.get("documents", [])
    legal_retrieved = sum(bool(item.get("retrieved")) for item in entries)
    legal_converted = sum(item.get("retrieval_status") in {"converted_review_candidate", "changed_review_candidate"} for item in entries)
    legal_blocked = sum(item.get("retrieval_status") == "retrieval_or_conversion_error" for item in entries)
    manifest["accepted_source_count"] = 0
    manifest["retrieved_source_count"] = sum(bool(item.get("retrieved")) for item in all_documents)
    manifest["retrieved_review_candidate_count"] = manifest["retrieved_source_count"]
    manifest["converted_review_candidate_count"] = sum(item.get("retrieval_status") in {"converted_review_candidate", "changed_review_candidate"} for item in all_documents)
    manifest["blocked_source_count"] = sum(item.get("retrieval_status") == "retrieval_or_conversion_error" for item in all_documents)
    guidance_count = sum(item.get("retrieval_method") == "czech_official_guidance_html_adapter" for item in all_documents)
    monitor_count = sum(item.get("retrieval_method") == "bounded_official_https_capture" for item in all_documents)
    manifest["legal_retrieval"] = {
        "publisher": "e-Sbírka",
        "route": "Public read-only page-data service at /sbr-externi/dokumenty-sbirky/{encoded-current-stable-url}; resolves current version and exposes ordered fragment pages",
        "registration": "No account or API key was required for the tested public page-data requests; the separately documented registration-gated REST API is not used",
        "version_evidence": "Publisher response fields typZneni=AKTUALNI, staleUrl, datumUcinnostiZneniOd, and citation are captured for each act",
        "retrieved_source_count": legal_retrieved,
        "converted_review_candidate_count": legal_converted,
        "blocked_source_count": legal_blocked,
        "status": f"{legal_converted} current Czech legal texts converted as review candidates; {legal_blocked} retrieval failures; none accepted",
        "capture_manifest": "references/esbirka-open-data-captures.json",
    }
    manifest["guidance_retrieval"] = {
        "captured_count": guidance_count,
                "method": "Official-page HTML adapter, exact response and conversion hashes retained in project temp storage and references; all remain review-only candidates.",
    }
    manifest["monitor_capture"] = {
        "captured_count": monitor_count,
        "method": "Bounded allowlisted official HTTPS capture; exact response hashes and deterministic conversions are replay-verified. Parent-index/currentness review remains required for forms and mission/court/oversight discovery pages.",
        "capture_manifest": "references/monitor-pass-2026-10-19-capture-results.json",
    }
    manifest["retrieval_status"] = (
        f"{legal_converted} current Czech legal texts, {guidance_count} official guidance/index pages, and "
        f"{monitor_count} monitor/discovery pages converted as review candidates; "
        f"{manifest['blocked_source_count']} retrieval failures; none accepted"
    )


def sync(selected_ids: set[str] | None = None) -> None:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    old_capture = json.loads(CAPTURE_MANIFEST.read_text(encoding="utf-8")) if CAPTURE_MANIFEST.exists() else {"records": []}
    previous = {record.get("candidate_id"): record for record in old_capture.get("records", [])}
    records = []
    targets = [item for item in legal_entries(manifest) if selected_ids is None or item["id"] in selected_ids]
    unknown = (selected_ids or set()) - {item["id"] for item in legal_entries(manifest)}
    if unknown:
        raise SystemExit(f"unknown Czech candidate IDs: {', '.join(sorted(unknown))}")
    for index, entry in enumerate(targets):
        print(f"retrieving {entry['id']}", flush=True)
        try:
            record, markdown = capture_entry(entry, previous.get(entry["id"]))
            records.append(record)
            print(f"{record['retrieval_status']} {record['version_effective_from']} {record['fragment_count']} fragments", flush=True)
        except Exception as exc:
            records.append({
                "candidate_id": entry["id"],
                "source_url": entry.get("url"),
                "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "retrieval_status": "retrieval_or_conversion_error",
                "retrieval_note": f"{type(exc).__name__}: {exc}",
                "accepted": False,
            })
            print(f"review {entry['id']}: {type(exc).__name__}: {exc}", flush=True)
        if index + 1 < len(targets):
            time.sleep(REQUEST_DELAY)
    if selected_ids is not None:
        refreshed = {record.get("candidate_id"): record for record in records}
        for candidate_id, record in previous.items():
            if candidate_id not in selected_ids:
                refreshed[candidate_id] = record
        records = [refreshed[entry["id"]] for entry in legal_entries(manifest) if entry["id"] in refreshed]
    capture = {
        "jurisdiction": "czechia",
        "as_of_date": datetime.now(timezone.utc).date().isoformat(),
        "method": "Ordinary unauthenticated HTTPS requests to the public e-Sbírka page-data route; no account, API key, challenge bypass, or form submission. Current-version metadata and each exact JSON fragment-page response are saved and hash-pinned. All outputs remain unaccepted review candidates.",
        "request_policy": {"timeout_seconds": TIMEOUT, "max_response_bytes": MAX_RESPONSE_BYTES, "delay_seconds": REQUEST_DELAY, "official_host": HOST},
        "records": records,
        "accepted_source_count": 0,
    }
    update_manifests(manifest, capture)
    atomic_write(CAPTURE_MANIFEST, (json.dumps(capture, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    atomic_write(SOURCE_MANIFEST, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"captured {sum(bool(r.get('candidate_text_path')) for r in records)}/{len(records)} current Czech texts; accepted 0", flush=True)


def verify() -> None:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    entries = {entry["id"]: entry for entry in legal_entries(manifest)}
    capture = json.loads(CAPTURE_MANIFEST.read_text(encoding="utf-8"))
    errors: list[str] = []
    for record in capture.get("records", []):
        candidate_id = record.get("candidate_id", "unknown")
        try:
            if record.get("retrieval_status") not in {"converted_review_candidate", "changed_review_candidate"}:
                continue
            entry = entries[candidate_id]
            meta_raw = in_project_temp(record["metadata_raw_path"]).read_bytes()
            if sha256(meta_raw) != record["metadata_sha256"]:
                raise ValueError("metadata hash mismatch")
            metadata = json.loads(meta_raw)
            all_fragments: list[dict] = []
            aggregate = hashlib.sha256()
            aggregate.update(len(meta_raw).to_bytes(8, "big")); aggregate.update(meta_raw)
            for page in record["pages"]:
                raw_page = in_project_temp(page["raw_path"]).read_bytes()
                if sha256(raw_page) != page["source_sha256"]:
                    raise ValueError(f"page {page['page_number']} hash mismatch")
                aggregate.update(len(raw_page).to_bytes(8, "big")); aggregate.update(raw_page)
                data = json.loads(raw_page)
                if data.get("pocetStranek") != record["page_count"]:
                    raise ValueError("page count mismatch in saved response")
                all_fragments.extend(data["seznam"])
            if aggregate.hexdigest() != record["source_sha256"]:
                raise ValueError("aggregate source hash mismatch")
            if len(all_fragments) != record["fragment_count"]:
                raise ValueError("fragment count mismatch")
            markdown = render_markdown(entry, metadata, all_fragments, record)
            if sha256(markdown) != record["converted_sha256"]:
                raise ValueError("offline conversion replay mismatch")
            candidate = artifact_path(record["candidate_text_path"]).read_bytes()
            if sha256(candidate) != record["converted_sha256"]:
                raise ValueError("saved candidate hash mismatch")
            print(f"verified {candidate_id}: {record['version_effective_from']}, {record['fragment_count']} fragments", flush=True)
        except Exception as exc:
            errors.append(f"{candidate_id}: {type(exc).__name__}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"sync", "verify"} or (sys.argv[1] == "verify" and len(sys.argv) != 2):
        raise SystemExit("usage: python source-library/czechia/scripts/sync_esbirka_open_data.py sync [candidate-id ...] | verify")
    if sys.argv[1] == "sync":
        sync(set(sys.argv[2:]) if len(sys.argv) > 2 else None)
    else:
        verify()


if __name__ == "__main__":
    main()
