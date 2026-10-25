#!/usr/bin/env python3
"""Capture and convert current Finlex statute pages carrying text in Next.js RSC."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PACK = Path(__file__).resolve().parent
PROJECT_ROOT = PACK.parents[1]
TEMP_ROOT = Path(os.environ.get("PUBLIC_DATA_TEMP_ROOT", str(PROJECT_ROOT))).resolve()
CAPTURE_LIST = PACK / "references" / "finlex-rsc-captures.json"
OUTPUT_MANIFEST = PACK / "references" / "finlex-rsc-retrieval-manifest.json"
ALLOWED_HOSTS = {"www.finlex.fi", "finlex.fi"}
RSC_REF = re.compile(r"^\$L([0-9a-f]+)$")
ELI_PATTERN = re.compile(r"http://data\.finlex\.fi/eli/sd/(\d{4}/\d+)/ajantasa/(\d{4}-\d{2}-\d{2})/fin(?:\\\\?/|[\"'<>\s])")
SECTION_NUMBER = re.compile(r"^\s*\d+[a-z]?\s*§", re.IGNORECASE)
CHAPTER_NUMBER = re.compile(r"^\s*\d+\s+luku\b", re.IGNORECASE)


def local_path(relative_path: str) -> Path:
    """Resolve source-library files in the checkout and temp files in the configured scratch root."""
    relative = Path(relative_path)
    base = TEMP_ROOT if relative.parts and relative.parts[0] == "temp" else PROJECT_ROOT
    output = (base / relative).resolve()
    if not output.is_relative_to(base.resolve()):
        raise ValueError(f"refused path outside its root: {relative_path}")
    return output


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


class RSCParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.payloads: list[str] = []

    def handle_data(self, data: str) -> None:
        if "self.__next_f.push(" in data:
            self.payloads.append(data)


def rsc_chunks(raw_html: bytes) -> dict[str, object]:
    parser = RSCParser()
    parser.feed(raw_html.decode("utf-8"))
    stream_parts: list[str] = []
    for payload in parser.payloads:
        match = re.search(r"self\.__next_f\.push\((.*)\)", payload, flags=re.DOTALL)
        if not match:
            continue
        try:
            values = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if len(values) > 1 and isinstance(values[1], str):
            stream_parts.append(values[1])
    if len(stream_parts) < 10:
        raise ValueError("Finlex page did not contain a complete Next.js RSC stream")
    chunks: dict[str, object] = {}
    for line in "".join(stream_parts).splitlines():
        key, separator, value = line.partition(":")
        if not separator or not re.fullmatch(r"[0-9a-f]+", key):
            continue
        try:
            chunks[key] = json.loads(value)
        except json.JSONDecodeError:
            continue
    if len(chunks) < 100:
        raise ValueError("Finlex RSC stream was too small to contain a statute body")
    return chunks


def resolve_ref(value: object, chunks: dict[str, object], stack: frozenset[str]) -> object:
    if not isinstance(value, str):
        return value
    match = RSC_REF.fullmatch(value)
    if not match:
        return value
    key = match.group(1)
    if key in stack:
        return None
    target = chunks.get(key)
    # Client-module and error records are not text nodes.
    if isinstance(target, list) and target and isinstance(target[0], str) and target[0] in {"I", "E", "T"}:
        return None
    return target


def walk_find_finnish_section(value: object, chunks: dict[str, object], stack: frozenset[str], seen_chunks: set[str], seen_objects: set[int], found: list[dict]) -> None:
    if isinstance(value, str):
        match = RSC_REF.fullmatch(value)
        if match:
            key = match.group(1)
            if key not in stack and key not in seen_chunks:
                seen_chunks.add(key)
                walk_find_finnish_section(chunks.get(key), chunks, stack | {key}, seen_chunks, seen_objects, found)
        return
    if isinstance(value, list):
        if len(value) >= 4 and value[0] == "$" and isinstance(value[3], dict):
            props = value[3]
            if value[1] == "section" and props.get("lang") == "fi" and "akomaNtoso" in props.get("className", ""):
                if id(props) not in seen_objects:
                    seen_objects.add(id(props))
                    found.append(props)
            for child in props.values():
                walk_find_finnish_section(child, chunks, stack, seen_chunks, seen_objects, found)
        else:
            for child in value:
                walk_find_finnish_section(child, chunks, stack, seen_chunks, seen_objects, found)
        return
    if isinstance(value, dict):
        for child in value.values():
            walk_find_finnish_section(child, chunks, stack, seen_chunks, seen_objects, found)


def finnish_body_section(chunks: dict[str, object]) -> dict:
    found: list[dict] = []
    seen_chunks: set[str] = set()
    seen_objects: set[int] = set()
    for chunk in chunks.values():
        walk_find_finnish_section(chunk, chunks, frozenset(), seen_chunks, seen_objects, found)
    if len(found) != 1:
        raise ValueError(f"expected one Finnish Akoma Ntoso text section, found {len(found)}")
    return found[0]


def children_text(value: object, chunks: dict[str, object], stack: frozenset[str] = frozenset()) -> str:
    if isinstance(value, str):
        match = RSC_REF.fullmatch(value)
        if match:
            key = match.group(1)
            if key in stack:
                return ""
            resolved = resolve_ref(value, chunks, stack)
            return children_text(resolved, chunks, stack | {key})
        return "" if value.startswith("$") else value
    if isinstance(value, list):
        if len(value) >= 4 and value[0] == "$" and isinstance(value[3], dict):
            return children_text(value[3].get("children", ""), chunks, stack)
        return "".join(children_text(child, chunks, stack) for child in value)
    if isinstance(value, dict):
        return children_text(value.get("children", ""), chunks, stack)
    return ""


def normalized_text(value: object, chunks: dict[str, object]) -> str:
    text = children_text(value, chunks)
    text = html.unescape(text).replace("\u00a0", " ").replace("\u2009", " ")
    return re.sub(r"\s+", " ", text).strip()


def format_heading(text: str) -> tuple[str, str]:
    display = re.sub(
        r"^(\d+\s+(?:[a-z]\s+)?(?:luku|§))(?=\S)",
        r"\1 — ",
        text,
        flags=re.IGNORECASE,
    )
    display = re.sub(r"\)(?=\S)", ") — ", display)
    if CHAPTER_NUMBER.match(display):
        return "##", display
    if SECTION_NUMBER.match(display):
        return "###", display
    return "####", display


def extract_nodes(value: object, chunks: dict[str, object], stack: frozenset[str] = frozenset(), output: list[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
    if output is None:
        output = []
    if isinstance(value, str):
        match = RSC_REF.fullmatch(value)
        if match:
            key = match.group(1)
            if key not in stack:
                resolved = resolve_ref(value, chunks, stack)
                extract_nodes(resolved, chunks, stack | {key}, output)
        return output
    if isinstance(value, list):
        if len(value) >= 4 and value[0] == "$" and isinstance(value[3], dict):
            tag = value[1]
            props = value[3]
            class_name = props.get("className", "")
            text = normalized_text(props.get("children", ""), chunks)
            if tag in {"h2", "h3", "h4", "h5", "h6"} and text and "sectionTitle" in class_name:
                output.append(("heading", text))
                return output
            if tag == "p" and "bodyText" in class_name and text:
                output.append(("paragraph", text))
                return output
            extract_nodes(props.get("children", ""), chunks, stack, output)
        else:
            for child in value:
                extract_nodes(child, chunks, stack, output)
        return output
    if isinstance(value, dict):
        extract_nodes(value.get("children", ""), chunks, stack, output)
    return output


def render(record: dict, raw_html: bytes) -> tuple[bytes, dict]:
    html_text = raw_html.decode("utf-8")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    page_title = html.unescape(re.sub(r"\s+", " ", title_match.group(1))).strip() if title_match else ""
    if record["expected_page_title"] not in page_title or record["act_number"] not in page_title:
        raise ValueError(f"Finlex HTML title does not match expected statute: {page_title!r}")
    eli_matches = re.findall(
        rf"http://data\.finlex\.fi/eli/sd/{re.escape(record['eli_work'])}/ajantasa/(\d{{4}}-\d{{2}}-\d{{2}})/fin",
        html_text,
    )
    if not eli_matches:
        raise ValueError("Finlex page has no current Finnish ELI identifier")
    current_date = eli_matches[0]
    chunks = rsc_chunks(raw_html)
    section = finnish_body_section(chunks)
    nodes = extract_nodes(section.get("children", ""), chunks)
    if len(nodes) < record["min_body_paragraphs"]:
        raise ValueError(f"Finlex RSC body has too few text blocks: {len(nodes)}")
    paragraphs = [text for kind, text in nodes if kind == "paragraph"]
    headings = [text for kind, text in nodes if kind == "heading"]
    section_headings = [text for text in headings if SECTION_NUMBER.match(text)]
    if len(section_headings) < record["min_section_headings"]:
        raise ValueError(f"Finlex RSC body has too few section headings: {len(section_headings)}")
    body_parts = []
    for kind, text in nodes:
        if kind == "heading":
            level, display = format_heading(text)
            body_parts.append(level + " " + display)
        else:
            body_parts.append(text)
    body = "\n\n".join(body_parts)
    if len(body) < record["min_body_chars"]:
        raise ValueError(f"Finlex RSC body is unexpectedly short: {len(body)} characters")
    if record["body_marker"] not in body:
        raise ValueError(f"expected body identity marker was not found: {record['body_marker']!r}")
    if "Eduskunnan päätöksen mukaisesti säädetään" not in body:
        raise ValueError("Finlex page is missing the expected Finnish enacting formula")
    retrieved_at = record.get("retrieved_at")
    if not retrieved_at:
        raise ValueError("capture descriptor must pin retrieved_at for reproducible conversion")
    markdown = (
        f"# {record['title']}\n\n"
        f"- Jurisdiction: Finland\n"
        f"- Publisher: Finlex, Legal Register Centre\n"
        f"- Act: `{record['act_number']}` (Finnish)\n"
        f"- Official current-text page: {record['page_url']}\n"
        f"- Current ELI version shown by Finlex: http://data.finlex.fi/eli/sd/{record['eli_work']}/ajantasa/{current_date}/fin\n"
        f"- Retrieved: {retrieved_at}\n"
        f"- Captured page title: {page_title}\n"
        f"- Conversion: Finnish `section[lang=fi]` extracted from the Finlex Next.js React Server Component stream; headings and paragraph blocks retained in publisher order\n"
        f"- Extracted headings: {len(headings)}; numbered sections: {len(section_headings)}; text paragraphs: {len(paragraphs)}; body characters: {len(body)}\n\n"
        f"> **Review candidate.** Finlex identifies this as an up-to-date Finnish text and displays the ELI version above. Its HTML/RSC conversion is a page-specific fallback, so a later publisher redesign must fail closed and be reviewed. This capture is not accepted into the trusted legal corpus.\n>\n"
        f"> **Attribution:** Based on Finlex open data, made available under CC BY 4.0.\n\n"
        f"## Current Finnish statutory text\n\n{body}\n"
    ).encode("utf-8")
    metadata = {
        **record,
        "page_title": page_title,
        "current_eli": f"http://data.finlex.fi/eli/sd/{record['eli_work']}/ajantasa/{current_date}/fin",
        "retrieved_at": retrieved_at,
        "raw_html_sha256": sha256(raw_html),
        "raw_html_bytes": len(raw_html),
        "rsc_chunk_count": len(chunks),
        "heading_count": len(headings),
        "section_heading_count": len(section_headings),
        "paragraph_count": len(paragraphs),
        "body_chars": len(body),
        "converted_sha256": sha256(markdown),
        "converted_bytes": len(markdown),
        "retrieval_status": "converted_review_candidate",
        "accepted": False,
    }
    return markdown, metadata


def update_inventories(record: dict) -> None:
    for path in (PACK / "references" / "candidate-manifest.json", PACK / "references" / "source-catalog.json"):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("documents", data.get("sources", []))
        for item in entries:
            if item.get("id") != record["id"]:
                continue
            item["retrieved"] = True
            if not item.get("local_copy_accepted"):
                item["accepted"] = False
                item["retrieval_status"] = "converted_review_candidate"
            item["retrieval_shape"] = "Finlex current-text HTML page with full Finnish law body embedded in a Next.js RSC stream"
            item["publisher_identifier"]["record"] = f"{record['act_number']}; current ELI: {record['current_eli']}"
            if not item.get("local_copy_accepted"):
                item["verification_status"] = "Official current Finlex page, exact act title, Finnish ELI date, enacting formula, section headings, paragraph count and full-body threshold validated; conversion remains a review candidate."
            item["latest_conversion_candidate_path"] = record["output_path"]
            if record.get("monitor_archive_path"):
                item["monitor_archive_path"] = record["monitor_archive_path"]
            item["raw_capture_path"] = record["raw_html_path"]
            break
        accepted_local = sum(bool(item.get("local_copy_accepted")) for item in entries)
        data["accepted_source_count"] = accepted_local
        data["accepted_local_copy_count"] = accepted_local
        data["retrieved_review_candidate_count"] = sum("review_candidate" in x.get("retrieval_status", "") for x in entries)
        data["converted_review_candidate_count"] = data["retrieved_review_candidate_count"]
        atomic_write(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sync() -> None:
    captures = json.loads(CAPTURE_LIST.read_text(encoding="utf-8"))
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    errors = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for index, record in enumerate(captures["records"]):
        parsed = urllib.parse.urlsplit(record["page_url"])
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            errors.append(f"{record['id']}: page URL is outside Finlex HTTPS allowlist")
            continue
        if index:
            time.sleep(1)
        request = urllib.request.Request(record["page_url"], headers={
            "User-Agent": "eudirective-public-data/1.0 (Finlex current-text capture)",
            "Accept": "text/html",
        })
        try:
            with opener.open(request, timeout=30) as response:
                final = urllib.parse.urlsplit(response.geturl())
                content_type = response.headers.get("Content-Type", "")
                if response.status != 200 or final.scheme != "https" or final.hostname not in ALLOWED_HOSTS:
                    raise ValueError(f"unexpected response: HTTP {response.status} {response.geturl()}")
                if "text/html" not in content_type.lower():
                    raise ValueError(f"unexpected content type: {content_type or '(missing)'}")
                body = response.read(12 * 1024 * 1024 + 1)
                if len(body) > 12 * 1024 * 1024:
                    raise ValueError("response exceeds 12 MiB cap")
                if not body:
                    raise ValueError("empty response")
                digest = sha256(body)
                path = f"temp/finland/raw/{record['id']}-{digest}.html"
                output = local_path(path)
                if output.exists() and sha256(output.read_bytes()) != digest:
                    raise ValueError("hash-named raw snapshot has conflicting content")
                if not output.exists():
                    atomic_write(output, body)
                record.update({
                    "retrieved_at": now,
                    "raw_html_path": path,
                    "raw_html_sha256": digest,
                    "raw_html_bytes": len(body),
                    "response_url": response.geturl(),
                    "response_content_type": content_type,
                    "last_checked_at": now,
                })
                print(f"saved {record['id']} {digest} ({len(body)} bytes)")
        except Exception as exc:
            errors.append(f"{record['id']}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))
    atomic_write(CAPTURE_LIST, (json.dumps(captures, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def run(mode: str) -> None:
    captures = json.loads(CAPTURE_LIST.read_text(encoding="utf-8"))
    previous = json.loads(OUTPUT_MANIFEST.read_text(encoding="utf-8")) if OUTPUT_MANIFEST.exists() else {"records": []}
    old_by_id = {item["id"]: item for item in previous.get("records", [])}
    results = []
    errors = []
    for record in captures["records"]:
        try:
            raw_path = local_path(record["raw_html_path"])
            raw_html = raw_path.read_bytes()
            markdown, metadata = render(record, raw_html)
            out_path = local_path(record["output_path"])
            if mode == "verify":
                expected = old_by_id.get(record["id"])
                if not expected:
                    raise ValueError("record is absent from retrieval manifest")
                checks = {
                    "raw HTML": (sha256(raw_html), expected.get("raw_html_sha256")),
                    "converted Markdown replay": (sha256(markdown), expected.get("converted_sha256")),
                    "saved Markdown": (sha256(out_path.read_bytes()), expected.get("converted_sha256")),
                }
                failed = [name for name, (actual, want) in checks.items() if actual != want]
                if failed:
                    raise ValueError("hash/replay mismatch: " + ", ".join(failed))
                print(f"verified {record['id']} (official page hash and conversion replay)")
            else:
                atomic_write(out_path, markdown)
                metadata["output_path"] = record["output_path"]
                metadata["raw_html_path"] = record["raw_html_path"]
                metadata["response_url"] = record.get("response_url", record["page_url"])
                if record.get("monitor_archive_path"):
                    metadata["monitor_archive_path"] = record["monitor_archive_path"]
                results.append(metadata)
                update_inventories(metadata)
                print(f"converted {record['id']} -> {record['output_path']}")
        except Exception as exc:
            errors.append(f"{record.get('id', '<unknown>')}: {exc}")
    if mode != "verify" and not errors:
        manifest = {
            "manifest_version": 1,
            "publisher": "Finlex / Legal Register Centre",
            "retrieval_method": "Official current-text page HTML, with law text extracted from the Finnish Next.js RSC subtree; hash-pinned raw snapshots and offline deterministic replay.",
            "review_status": "All outputs are unaccepted review candidates.",
            "records": results,
            "accepted_source_count": 0,
        }
        atomic_write(OUTPUT_MANIFEST, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if mode == "verify":
        extra = set(old_by_id) - {record["id"] for record in captures["records"]}
        if extra:
            errors.append("retrieval manifest contains records absent from capture list: " + ", ".join(sorted(extra)))
    if errors:
        raise SystemExit("\n".join(errors))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "convert"
    if mode == "sync":
        sync()
    elif mode in {"convert", "verify"}:
        run(mode)
    else:
        raise SystemExit("usage: convert_finlex_rsc_capture.py [sync|convert|verify]")
