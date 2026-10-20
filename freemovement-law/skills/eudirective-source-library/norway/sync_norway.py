#!/usr/bin/env python3
"""Replayable capture of Norway candidates using Lovdata's documented public data route."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tarfile
import urllib.parse
import time
from datetime import date, datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
sys.path.insert(0, str(BASE))
import sync_candidate_pages as generic

RAW = ROOT / "temp/norway/raw"
CAPTURE_PATH = BASE / "norway/references/norway-capture-results.json"
LAW_ARCHIVE: Path | None = None
REG_ARCHIVE: Path | None = None
GAZETTE_ARCHIVE: Path | None = None
GAZETTE_FILENAME: str | None = None
API_LIST = "https://api.lovdata.no/v1/publicData/list"
API_SPEC = "https://api.lovdata.no/swagger/api.json"
API_GET = "https://api.lovdata.no/v1/publicData/get/"
TIMEOUT = generic.TIMEOUT

LEGAL_MEMBERS = {
    "no-06": ("laws", "nl/nl-20080515-035.xml"),
    "no-08": ("laws", "nl/nl-19921127-109.xml"),
    "no-13": ("laws", "nl/nl-19670210-000.xml"),
    "no-14": ("laws", "nl/nl-20060519-016.xml"),
    "no-16": ("laws", "nl/nl-20180615-038.xml"),
    "no-17": ("laws", "nl/nl-20260619-036.xml"),
    "no-48": ("laws", "nl/nl-19800613-035.xml"),
    "no-07": ("regulations", "sf/sf-20091015-1286.xml"),
    "no-15": ("regulations", "sf/sf-20081017-1119.xml"),
    "no-53": ("laws", "nl/nl-20250620-081.xml"),
    "no-54": ("laws", "nl/nl-20121214-081.xml"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def install_package_paths(packages: dict[str, dict]) -> None:
    global LAW_ARCHIVE, REG_ARCHIVE, GAZETTE_ARCHIVE, GAZETTE_FILENAME
    law = packages["gjeldende-lover.tar.bz2"]
    regulations = packages["gjeldende-sentrale-forskrifter.tar.bz2"]
    gazette_names = [n for n in packages if re.fullmatch(r"lovtidend-avd1-\d{4}\.tar\.bz2", n)]
    if not gazette_names:
        raise ValueError("publicData list has no current-year Avdeling I package")
    GAZETTE_FILENAME = max(gazette_names, key=lambda n: int(re.search(r"(\d{4})\.tar\.bz2$", n).group(1)))
    LAW_ARCHIVE = ROOT / law["raw_path"]
    REG_ARCHIVE = ROOT / regulations["raw_path"]
    GAZETTE_ARCHIVE = ROOT / packages[GAZETTE_FILENAME]["raw_path"]


def fetch_public_packages(hosts: set[str]) -> tuple[bytes, dict, dict[str, dict]]:
    """Refresh the no-auth list and only the current package classes used by this inventory."""
    list_raw, list_url, list_type = generic.fetch(API_LIST, hosts)
    if list_type not in {"application/json", "text/json"}:
        raise ValueError(f"publicData list returned unexpected media type: {list_type}")
    listing = json.loads(list_raw)
    if not isinstance(listing, list) or not all(isinstance(row, dict) for row in listing):
        raise ValueError("publicData list has unexpected JSON shape")
    list_digest = sha(list_raw)
    list_rel = f"temp/norway/raw/publicData-list-{list_digest}.json"
    generic.save(list_rel, list_raw)
    by_name = {row.get("filename"): row for row in listing if isinstance(row.get("filename"), str)}
    current_year_name = f"lovtidend-avd1-{date.today().year}.tar.bz2"
    required = ["gjeldende-lover.tar.bz2", "gjeldende-sentrale-forskrifter.tar.bz2", current_year_name]
    missing = [name for name in required if name not in by_name]
    if missing:
        raise ValueError("publicData list lacks required current package(s): " + ", ".join(missing))
    packages: dict[str, dict] = {}
    for name in required:
        row = by_name[name]
        expected_size = int(row.get("sizeBytes", "0"))
        if expected_size <= 0 or expected_size > generic.MAX_BYTES:
            raise ValueError(f"listed package size outside configured cap: {name} ({expected_size} bytes)")
        url = API_GET + urllib.parse.quote(name, safe="")
        data, resolved, content_type = generic.fetch(url, hosts)
        if len(data) != expected_size:
            raise ValueError(f"listed size mismatch for {name}: expected {expected_size}, got {len(data)}")
        if not data.startswith(b"BZh"):
            raise ValueError(f"official package is not bzip2 data: {name}")
        digest = sha(data)
        raw_rel = f"temp/norway/raw/{name}-{digest}.raw"
        generic.save(raw_rel, data)
        packages[name] = {"filename": name, "description": row.get("description"),
                          "listed_size_bytes": expected_size, "actual_size_bytes": len(data),
                          "last_modified": row.get("lastModified"), "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "request_url": url, "resolved_url": resolved, "media_type": content_type,
                          "sha256": digest, "raw_path": raw_rel}
        time.sleep(generic.DELAY)
    install_package_paths(packages)
    list_record = {"request_url": API_LIST, "resolved_url": list_url, "media_type": list_type,
                   "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "source_bytes": len(list_raw), "sha256": list_digest, "raw_path": list_rel,
                   "listed_packages": listing}
    return list_raw, list_record, packages


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def source_entry(manifest: dict, candidate_id: str) -> dict | None:
    return next((e for e in manifest["sources"] if e["id"] == candidate_id), None)


def header_metadata(root: ET.Element) -> list[tuple[str, str]]:
    header = root.find(".//header[@class='documentHeader']")
    if header is None:
        header = root.find(".//header")
    if header is None:
        return []
    dl = header.find(".//dl")
    if dl is None:
        return []
    pairs, pending = [], None
    for node in list(dl):
        tag = node.tag.rsplit("}", 1)[-1].lower()
        value = " ".join("".join(node.itertext()).split())
        if tag == "dt":
            pending = value
        elif tag == "dd" and pending:
            if pending.lower() != "innhold":
                pairs.append((pending, value))
            pending = None
    return pairs


def main_text(root: ET.Element) -> str:
    main = root.find(".//main[@class='documentBody']")
    if main is None:
        main = root.find(".//main")
    if main is None:
        raise ValueError("Lovdata XHTML has no main document body")
    out: list[str] = []
    block_tags = {"article", "div", "p", "section", "ul", "ol", "table", "tr"}
    skip_tags = {"script", "style", "nav", "footer", "header"}

    def add(value: str | None) -> None:
        if value:
            out.append(value)

    def walk(node: ET.Element, suppress_first_block: bool = False) -> bool:
        tag = node.tag.rsplit("}", 1)[-1].lower()
        if tag in skip_tags:
            return False
        is_item = tag == "li"
        is_block = tag in block_tags or tag in {"h1", "h2", "h3", "h4", "h5", "li"}
        if is_item:
            out.append("\n")
            out.append("- ")
        elif is_block and not suppress_first_block:
            out.append("\n")
        if tag in {"h1", "h2", "h3", "h4", "h5"}:
            level = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5}[tag]
            out.append("#" * level + " ")
        elif tag == "br":
            out.append("\n")
        consumed = bool(node.text and node.text.strip())
        add(node.text)
        for child in list(node):
            child_consumed = walk(child, (suppress_first_block or is_item) and not consumed)
            consumed = consumed or child_consumed
            if child.tail and child.tail.strip():
                consumed = True
            add(child.tail)
        if is_block:
            out.append("\n")
        return consumed

    for child in list(main):
        walk(child)
        add(child.tail)
    text = "".join(out).replace("\xa0", " ").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", x).strip() for x in text.splitlines()]
    compact: list[str] = []
    for line in lines:
        if line or (compact and compact[-1]):
            compact.append(line)
    return "\n".join(compact).strip()


def render_law(entry: dict, member: str, archive: Path, raw: bytes, received: str) -> tuple[bytes, str]:
    root = ET.fromstring(raw)
    title_node = root.find(".//head/title")
    title = " ".join("".join(title_node.itertext()).split()) if title_node is not None else entry["title"]
    digest = sha(raw)
    meta = header_metadata(root)
    lines = [f"# {entry['title']}", "", "- Jurisdiction: Norway", f"- Candidate ID: {entry['id']}",
             f"- Candidate URL: {entry['url']}", f"- Lovdata archive member: {member}",
             f"- Archive filename: {archive.name}", f"- Source-text SHA-256: {digest}",
             f"- Captured: {received}", "- Content type: text/html; charset=utf-8 (official Lovdata XHTML)",
             "- Extraction: header definition list plus complete documentBody block structure", "",
             "> Review candidate. Not accepted into the trusted source corpus.", "", "## Publisher metadata", ""]
    lines.extend(f"- {key}: {value}" for key, value in meta)
    lines.extend(["", f"## Official document title", "", title, "", "## Legal text", "", main_text(root), ""])
    return ("\n".join(lines).rstrip() + "\n").encode(), digest


def archive_member(archive: Path, member_name: str) -> bytes:
    with tarfile.open(archive, "r:bz2") as tf:
        for member in tf.getmembers():
            p = Path(member.name)
            if p.is_absolute() or ".." in p.parts or member.issym() or member.islnk():
                raise ValueError(f"unsafe member in official archive: {member.name}")
        member = tf.getmember(member_name)
        if not member.isfile() or member.size > generic.MAX_BYTES:
            raise ValueError(f"unexpected archive member type/size: {member_name}")
        handle = tf.extractfile(member)
        if handle is None:
            raise ValueError(f"cannot read archive member: {member_name}")
        data = handle.read(generic.MAX_BYTES + 1)
        if len(data) != member.size or len(data) > generic.MAX_BYTES:
            raise ValueError(f"archive member byte count mismatch: {member_name}")
        return data


def tar_index_markdown(entry: dict, archive: Path, url: str, received: str) -> tuple[bytes, str, str]:
    archive_bytes = archive.read_bytes()
    with tarfile.open(archive, "r:bz2") as tf:
        members = tf.getmembers()
        rows = []
        for m in members:
            p = Path(m.name)
            if p.is_absolute() or ".." in p.parts or m.issym() or m.islnk():
                raise ValueError(f"unsafe member in official archive: {m.name}")
            if m.isfile():
                rows.append((m.name, m.size))
    digest = sha(archive_bytes)
    lines = [f"# {entry['title']}", "", "- Jurisdiction: Norway", f"- Candidate ID: {entry['id']}",
             f"- Candidate URL: {entry['url']}", f"- Retrieval URL: {url}", f"- Retrieved: {received}",
             f"- Archive filename: {archive.name}", f"- Archive SHA-256: {digest}",
             "- Archive type: bzip2-compressed tar of official XML documents", "- Archive member count: " + str(len(rows)),
             "", "> Review candidate. Archive index only; original promulgations remain separate records.", "",
             "## Archive members", "", "| Path | Bytes |", "|---|---:|"]
    lines.extend(f"| `{name}` | {size} |" for name, size in rows)
    return ("\n".join(lines) + "\n").encode(), digest, f"{len(rows)} safe regular files; all paths checked"


def generic_record(entry: dict, country: str, hosts: set[str], prior: dict | None) -> dict:
    return generic.capture(country, entry, hosts, prior)


def persist_candidate(candidate_id: str, source_digest: str, markdown: bytes, old: dict | None) -> tuple[str, str, str]:
    """Keep changed-source candidates staged until a reviewer handles them."""
    unchanged = bool(old and old.get("source_sha256") == source_digest and old.get("candidate_text_path")
                     and (ROOT / old["candidate_text_path"]).is_file())
    changed = bool(old and old.get("source_sha256") and old["source_sha256"] != source_digest)
    if unchanged:
        out_rel = old["candidate_text_path"]
        status = old.get("retrieval_status", "converted_review_candidate")
        state = old.get("review_state", "review_candidate")
    elif changed:
        out_rel = f"temp/norway/pending/{generic.slug(candidate_id)}-{source_digest[:16]}.md"
        status, state = "changed_review_candidate", "changed_pending_review"
    else:
        out_rel = f"source-library/norway/candidates/{generic.slug(candidate_id)}.md"
        status, state = "converted_review_candidate", "review_candidate"
    generic.atomic(generic.inside(out_rel), markdown)
    return out_rel, status, state


def sync() -> None:
    mp = BASE / "norway/references/candidate-manifest.json"
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    entries = manifest["sources"]
    hosts = {str(h).lower() for h in manifest.get("official_hosts", [])}
    hosts.update({"api.lovdata.no"})
    prior = json.loads(CAPTURE_PATH.read_text(encoding="utf-8")) if CAPTURE_PATH.exists() else {"records": []}
    prior_by_id = {r["candidate_id"]: r for r in prior.get("records", [])}
    results: list[dict] = []
    public_list_bytes, list_record, packages = fetch_public_packages(hosts)
    received = list_record["retrieved_at"]
    api_spec_entry = source_entry(manifest, "no-02")

    # These source rows are represented by Lovdata's documented public data API, never by bulk website pages.
    e01 = source_entry(manifest, "no-01")
    if e01["url"] != API_LIST:
        e01["previous_url"] = e01["url"]
        e01["url"] = API_LIST
    e01["retrieval_url"] = API_LIST
    e01["note"] = "Current public-data package catalogue from Lovdata's documented no-auth API; individual record pages are not scraped."
    e02 = api_spec_entry
    if e02["url"] != API_SPEC:
        e02["previous_url"] = e02["url"]
        e02["url"] = API_SPEC
    e02["retrieval_url"] = API_SPEC
    e02["note"] = "OpenAPI schema for Lovdata routes; structuredRules endpoints require a key, while publicData list/get are documented as unauthenticated."

    for entry in entries:
        cid = entry["id"]
        print("capturing", cid, flush=True)
        try:
            if cid in LEGAL_MEMBERS:
                package_key, member = LEGAL_MEMBERS[cid]
                archive_record = packages["gjeldende-lover.tar.bz2"] if package_key == "laws" else packages["gjeldende-sentrale-forskrifter.tar.bz2"]
                archive = ROOT / archive_record["raw_path"]
                data = archive_member(archive, member)
                digest = sha(data)
                old = prior_by_id.get(cid)
                raw_rel = f"temp/norway/raw/{cid}-{digest}.html"
                generic.save(raw_rel, data)
                captured_at = old["retrieved_at"] if old and old.get("source_sha256") == digest else received
                md, digest = render_law(entry, member, archive, data, captured_at)
                out_rel, status, review_state = persist_candidate(cid, digest, md, old)
                request_url = API_GET + archive_record["filename"]
                result = {"candidate_id": cid, "source_url": entry["url"], "request_url": request_url,
                          "resolved_url": archive_record["resolved_url"], "archive_member": member,
                          "package_filename": archive_record["filename"], "package_archive_sha256": archive_record["sha256"],
                          "package_last_modified": archive_record["last_modified"], "package_raw_path": archive_record["raw_path"],
                          "retrieved_at": captured_at, "source_content_type": "text/html", "source_bytes": len(data),
                          "source_sha256": digest, "raw_path": raw_rel, "candidate_text_path": out_rel,
                          "converted_sha256": sha(md), "converted_bytes": len(md),
                          "content_selector": "Lovdata XHTML metadata and complete legal document body",
                          "retrieval_status": status, "review_state": review_state, "accepted": False}
            elif cid == "no-01":
                old = prior_by_id.get(cid)
                obj = json.loads(public_list_bytes)
                data = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()
                digest = list_record["sha256"]
                raw_rel = list_record["raw_path"]
                captured_at = old["retrieved_at"] if old and old.get("source_sha256") == digest else received
                md = (f"# {entry['title']}\n\n- Jurisdiction: Norway\n- Candidate ID: {cid}\n- Official API: {API_LIST}\n"
                      f"- Captured: {captured_at}\n- Exact response SHA-256: {digest}\n\n> Review candidate. Not accepted.\n\n## Public package list\n\n```json\n" + data.decode() + "```\n").encode()
                out_rel, status, review_state = persist_candidate(cid, digest, md, old)
                result = {"candidate_id": cid, "source_url": entry["url"], "request_url": API_LIST, "resolved_url": API_LIST,
                          "retrieved_at": captured_at, "source_content_type": "application/json", "source_bytes": len(public_list_bytes),
                          "source_sha256": digest, "raw_path": raw_rel, "candidate_text_path": out_rel,
                          "converted_sha256": sha(md), "converted_bytes": len(md), "content_selector": "documented no-auth publicData package list",
                          "retrieval_status": status, "review_state": review_state, "accepted": False}
            elif cid == "no-04":
                old = prior_by_id.get(cid)
                gazette = packages[GAZETTE_FILENAME]
                archive = ROOT / gazette["raw_path"]
                data = archive.read_bytes()
                digest = sha(data)
                raw_rel = gazette["raw_path"]
                url = API_GET + gazette["filename"]
                captured_at = old["retrieved_at"] if old and old.get("source_sha256") == digest else received
                md, digest, check = tar_index_markdown(entry, archive, url, captured_at)
                out_rel, status, review_state = persist_candidate(cid, digest, md, old)
                result = {"candidate_id": cid, "source_url": entry["url"], "request_url": url, "resolved_url": gazette["resolved_url"],
                          "package_filename": gazette["filename"], "package_last_modified": gazette["last_modified"],
                          "package_raw_path": gazette["raw_path"],
                          "retrieved_at": captured_at, "source_content_type": "application/x-bzip2", "source_bytes": len(data),
                          "source_sha256": digest, "raw_path": raw_rel, "candidate_text_path": out_rel,
                          "converted_sha256": sha(md), "converted_bytes": len(md), "content_selector": check,
                          "retrieval_status": status, "review_state": review_state, "accepted": False}
            elif cid == "no-05":
                result = {"candidate_id": cid, "source_url": entry["url"], "retrieval_status": "not_available_in_public_api_catalogue",
                          "retrieval_note": "The documented no-auth package list exposes Avdeling I packages only; no Avdeling II/local-regulation archive was identified. Lovdata website pages were not systematically retrieved under its terms.", "accepted": False}
            elif cid == "no-12":
                # One historical Lovdata item only; the bulk archive omits it because it is repealed.
                entry["retrieval_url"] = "https://lovdata.no/dokument/NLO/lov/1992-11-27-112"
                entry["note"] = "Historical text only; Lovdata identifies it as repealed on 14 December 2012 by LOV-2012-12-14-81."
                result = generic_record(entry, "norway", hosts, prior_by_id.get(cid))
            else:
                result = generic_record(entry, "norway", hosts, prior_by_id.get(cid))
            results.append(result)
            if result.get("source_sha256"):
                print("saved", cid, result.get("retrieval_status"), flush=True)
            else:
                print("review", cid, result.get("retrieval_status"), flush=True)
            if entry is not entries[-1]:
                time.sleep(generic.DELAY)
        except Exception as exc:
            result = {"candidate_id": cid, "source_url": entry.get("url"), "retrieval_status": "retrieval_or_conversion_error",
                      "retrieval_note": f"{type(exc).__name__}: {exc}", "accepted": False}
            results.append(result)
            print("review", cid, result["retrieval_note"], flush=True)

    byid = {r["candidate_id"]: r for r in results}
    for entry in entries:
        r = byid[entry["id"]]
        entry["retrieved"] = bool(r.get("source_sha256"))
        entry["accepted"] = False
        entry["retrieval_status"] = r["retrieval_status"]
        for key in ("candidate_text_path", "source_sha256", "converted_sha256", "source_bytes", "resolved_url", "retrieval_note", "archive_member"):
            if key in r:
                entry[key] = r[key]
    counts: dict[str, int] = {}
    for r in results:
        counts[r["retrieval_status"]] = counts.get(r["retrieval_status"], 0) + 1
    manifest["status"] = "partially_retrieved_review_candidates"
    manifest["accepted_source_count"] = 0
    manifest["retrieved_review_candidate_count"] = sum(bool(r.get("source_sha256")) for r in results)
    manifest["converted_review_candidate_count"] = sum(bool(r.get("candidate_text_path")) for r in results)
    manifest["retrieval_status"] = "; ".join(f"{v} {k}" for k, v in sorted(counts.items())) + "; all outputs are review candidates; no source accepted"
    capture = {"jurisdiction": "norway", "as_of_date": date.today().isoformat(),
               "method": "Each sync refreshes Lovdata's no-auth publicData list and retrieves the listed current-law, central-regulation and current-year Avdeling I packages. Other candidate pages use ordinary allowlisted HTTPS GET. No systematic Lovdata website extraction. Exact bytes are hashed; output changes stage for review; no source is accepted automatically.",
               "request_policy": {"timeout_seconds": TIMEOUT, "archive_member_size_cap_bytes": generic.MAX_BYTES,
                                 "delay_seconds": generic.DELAY, "max_response_bytes": generic.MAX_BYTES,
                                 "lovdata_api_list": API_LIST, "lovdata_api_spec": API_SPEC,
                                 "lovdata_api_get_prefix": API_GET},
               "public_data_list": list_record, "data_packages": packages,
               "records": results, "accepted_source_count": 0}
    atomic(mp, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode())
    atomic(CAPTURE_PATH, (json.dumps(capture, ensure_ascii=False, indent=2) + "\n").encode())
    print("counts", json.dumps(counts, sort_keys=True))


def verify() -> None:
    manifest = json.loads((BASE / "norway/references/candidate-manifest.json").read_text(encoding="utf-8"))
    entries = {e["id"]: e for e in manifest["sources"]}
    capture = json.loads(CAPTURE_PATH.read_text(encoding="utf-8"))
    errors = []
    packages = capture.get("data_packages", {})
    if not packages:
        errors.append("capture results contain no live publicData package metadata")
    else:
        try:
            install_package_paths(packages)
            for name, record in packages.items():
                package_path = (ROOT / record["raw_path"]).resolve()
                if not package_path.is_relative_to(ROOT):
                    raise ValueError(f"package path escapes work root: {name}")
                package_bytes = package_path.read_bytes()
                if len(package_bytes) != record["actual_size_bytes"] or sha(package_bytes) != record["sha256"]:
                    raise ValueError(f"package hash/size mismatch: {name}")
                if not package_bytes.startswith(b"BZh"):
                    raise ValueError(f"package is not bzip2 data: {name}")
                print("verified package", name)
            list_record = capture["public_data_list"]
            list_path = (ROOT / list_record["raw_path"]).resolve()
            if not list_path.is_relative_to(ROOT):
                raise ValueError("publicData list path escapes work root")
            list_bytes = list_path.read_bytes()
            if len(list_bytes) != list_record["source_bytes"] or sha(list_bytes) != list_record["sha256"]:
                raise ValueError("publicData list hash/size mismatch")
            listed = json.loads(list_bytes)
            for name, record in packages.items():
                row = next((x for x in listed if x.get("filename") == name), None)
                if row is None or int(row["sizeBytes"]) != record["listed_size_bytes"] or row.get("lastModified") != record["last_modified"]:
                    raise ValueError(f"current publicData list metadata mismatch: {name}")
            print("verified live publicData list")
        except Exception as exc:
            errors.append(f"publicData packages: {type(exc).__name__}: {exc}")
    for r in capture["records"]:
        try:
            if not r.get("raw_path"):
                continue
            raw_path = (ROOT / r["raw_path"]).resolve()
            if not raw_path.is_relative_to(ROOT):
                raise ValueError("raw path escapes work root")
            raw = raw_path.read_bytes()
            if sha(raw) != r["source_sha256"]:
                raise ValueError("source hash mismatch")
            if r.get("archive_member"):
                archive = ROOT / packages[r["package_filename"]]["raw_path"]
                xml = archive_member(archive, r["archive_member"])
                if sha(xml) != r["source_sha256"]:
                    raise ValueError("archive source member hash mismatch")
                md, _ = render_law(entries[r["candidate_id"]], r["archive_member"], archive, xml, r["retrieved_at"])
            elif r["candidate_id"] == "no-04":
                md, _, _ = tar_index_markdown(entries["no-04"], GAZETTE_ARCHIVE, r["request_url"], r["retrieved_at"])
            elif r["candidate_id"] == "no-01":
                obj = json.loads(raw)
                data = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()
                md = (f"# {entries['no-01']['title']}\n\n- Jurisdiction: Norway\n- Candidate ID: no-01\n- Official API: {API_LIST}\n"
                      f"- Captured: {r['retrieved_at']}\n- Exact response SHA-256: {r['source_sha256']}\n\n> Review candidate. Not accepted.\n\n## Public package list\n\n```json\n" + data.decode() + "```\n").encode()
            else:
                if not r.get("candidate_text_path"):
                    continue
                entry = entries[r["candidate_id"]]
                ctype = r["source_content_type"]
                if ctype in {"application/json", "application/ld+json"}:
                    body = "```json\n" + json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + "\n```"
                    selector = "formatted JSON record"
                elif ctype == "application/pdf":
                    from io import BytesIO
                    from pypdf import PdfReader
                    reader = PdfReader(BytesIO(raw))
                    body = "\n\n".join(f"<!-- page {n} -->\n" + (page.extract_text() or "") for n, page in enumerate(reader.pages, 1)).strip()
                    selector = f"PDF text extraction; {len(reader.pages)} pages"
                else:
                    parser = generic.Region()
                    parser.feed(raw.decode("utf-8", "replace"))
                    body = parser.text()
                    selector = parser.selector or "no primary region"
                md = generic.render(entry, "norway", r["retrieved_at"], r["resolved_url"], ctype,
                                    r["source_sha256"], selector, body)
            candidate = (ROOT / r["candidate_text_path"]).resolve()
            if not candidate.is_relative_to(ROOT) or sha(candidate.read_bytes()) != sha(md):
                raise ValueError("conversion replay mismatch")
            print("verified", r["candidate_id"])
        except Exception as exc:
            errors.append(f"{r.get('candidate_id')}: {type(exc).__name__}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"sync", "verify"}:
        raise SystemExit("usage: sync_norway.py sync|verify")
    if sys.argv[1] == "sync":
        sync()
    else:
        verify()


if __name__ == "__main__":
    main()
