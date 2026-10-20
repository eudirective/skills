#!/usr/bin/env python3
"""Retrieve and convert the identified federal statutes from Gesetze im Internet."""
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
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
REFS = PACK / "references"
CANDIDATES = REFS / "candidate-manifest.json"
CAPTURES = REFS / "gii-captures.json"
RETRIEVAL = REFS / "gii-retrieval-manifest.json"
HOST = "www.gesetze-im-internet.de"
UA = "eudirective-source-library/1.0 (bounded public-law retrieval; eudirective@proton.me)"
MAX_BYTES = 64 * 1024 * 1024
TIMEOUT = 35


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.label: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.label = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.label.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.href is not None:
            self.links.append((self.href, " ".join(" ".join(self.label).split())))
            self.href = None
            self.label = []


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


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def family_dir(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    if path.lower().endswith(".html"):
        return path.rsplit("/", 1)[0] + "/"
    return path if path.endswith("/") else path + "/"


def validate_url(url: str) -> None:
    p = urllib.parse.urlparse(url)
    if p.scheme != "https" or (p.hostname or "").lower() != HOST:
        raise ValueError(f"refused non-allowlisted Gesetze im Internet URL: {url}")


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, accept: str) -> tuple[bytes, str, str]:
    validate_url(url)
    opener = urllib.request.build_opener(SameHostRedirect())
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with opener.open(req, timeout=TIMEOUT) as response:
        final = response.geturl()
        validate_url(final)
        ctype = response.headers.get_content_type().lower()
        chunks: list[bytes] = []
        total = 0
        while True:
            part = response.read(min(64 * 1024, MAX_BYTES + 1 - total))
            if not part:
                break
            total += len(part)
            if total > MAX_BYTES:
                raise ValueError(f"response exceeds {MAX_BYTES} byte cap")
            chunks.append(part)
        return b"".join(chunks), final, ctype


def save_raw(stem: str, data: bytes, suffix: str) -> str:
    digest = sha256(data)
    rel = f"temp/germany/raw/{stem}-{digest}.{suffix}"
    out = (ROOT / rel).resolve()
    if not out.is_relative_to(ROOT):
        raise ValueError("refused capture path outside repository root")
    if out.exists() and sha256(out.read_bytes()) != digest:
        raise ValueError(f"hash-addressed path conflict: {rel}")
    if not out.exists():
        atomic_write(out, data)
    return rel


def text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return normalized(" ".join(node.itertext()))


def child(node: ET.Element, name: str) -> ET.Element | None:
    return next((x for x in node if x.tag.rsplit("}", 1)[-1] == name), None)


def metadata(norm: ET.Element) -> dict[str, str]:
    m = child(norm, "metadaten")
    if m is None:
        return {}
    return {x.tag.rsplit("}", 1)[-1]: text(x) for x in m}


def inline_text(node: ET.Element) -> str:
    """Read inline statutory XML without losing text around inline tags."""
    pieces = [node.text or ""]
    for item in node:
        tag = item.tag.rsplit("}", 1)[-1]
        if tag != "DL":
            pieces.append("\n" if tag == "BR" else inline_text(item))
        pieces.append(item.tail or "")
    return normalized("".join(pieces))


def render_dl(node: ET.Element, depth: int = 0) -> list[str]:
    rows: list[str] = []
    label = ""
    indent = "  " * min(depth, 3)
    for item in node:
        tag = item.tag.rsplit("}", 1)[-1]
        if tag == "DT":
            label = inline_text(item)
        elif tag == "DD":
            body, nested = inline_and_nested(item, depth + 1)
            rows.append(f"{indent}- {label} {body}".rstrip())
            rows.extend(nested)
            label = ""
        if item.tail and item.tail.strip():
            rows.append(indent + item.tail.strip())
    return rows


def inline_and_nested(node: ET.Element, depth: int) -> tuple[str, list[str]]:
    pieces = [node.text or ""]
    nested: list[str] = []
    for item in node:
        tag = item.tag.rsplit("}", 1)[-1]
        if tag == "DL":
            nested.extend(render_dl(item, depth))
        else:
            body, child_lists = inline_and_nested(item, depth)
            pieces.append(body)
            nested.extend(child_lists)
        pieces.append(item.tail or "")
    return normalized("".join(pieces)), nested


def render_xml_content(node: ET.Element) -> str:
    """Render GII paragraph and definition-list nodes with readable breaks."""
    paragraphs: list[str] = []

    def visit(current: ET.Element) -> None:
        tag = current.tag.rsplit("}", 1)[-1]
        if tag == "DL":
            paragraphs.extend(render_dl(current))
            return
        if tag == "P":
            pieces: list[str] = []
            if current.text and current.text.strip():
                pieces.append(current.text.strip())
            for child_node in current:
                child_tag = child_node.tag.rsplit("}", 1)[-1]
                if child_tag == "DL":
                    if pieces:
                        paragraphs.append(normalized(" ".join(pieces)))
                        pieces = []
                    paragraphs.extend(render_dl(child_node))
                elif child_tag == "BR":
                    pieces.append(" ")
                else:
                    pieces.append(inline_text(child_node))
                if child_node.tail and child_node.tail.strip():
                    pieces.append(child_node.tail.strip())
            if pieces:
                paragraphs.append(normalized(" ".join(pieces)))
            return
        if current.text and current.text.strip():
            paragraphs.append(current.text.strip())
        for child_node in current:
            visit(child_node)
            if child_node.tail and child_node.tail.strip():
                paragraphs.append(child_node.tail.strip())

    visit(node)
    return "\n\n".join(x for x in paragraphs if x)


def extract_main_norm(data: bytes) -> tuple[ET.Element, list[ET.Element]]:
    # The publisher's public DTD is intentionally not fetched at runtime.
    parser = ET.XMLParser()
    root = ET.fromstring(data, parser=parser)
    if root.tag.rsplit("}", 1)[-1] != "dokumente":
        raise ValueError("unexpected XML root; expected dokumente")
    norms = [x for x in root if x.tag.rsplit("}", 1)[-1] == "norm"]
    if not norms:
        raise ValueError("XML package contains no legal norms")
    return norms[0], norms


def extract_targets() -> list[dict]:
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    return [x for x in manifest.get("documents", []) if x.get("source_type") == "national_legislation"]


def expected_alias(record: dict) -> str:
    return {
        "de-06": "FreizügG/EU", "de-08": "AufenthG", "de-09": "AufenthV",
        "de-10": "AufenthV", "de-11": "GAD", "de-12": "KonsG", "de-13": "VwVfG",
        "de-14": "IFG", "de-15": "VwGO", "de-16": "AABGebV", "de-17": "AZRG",
        "de-18": "PStG", "de-19": "PStV", "de-20": "AdWirkG", "de-21": "AdVermiG",
        "de-22": "AdÜbAG", "de-23": "BGBEG", "de-24": "FamFG",
    }[record["id"]]


def target_section(record: dict) -> str | None:
    return {"de-10": "§ 28", "de-13": "§ 2", "de-18": "§ 34"}.get(record["id"])


def validate_norms(meta_norm: ET.Element, norms: list[ET.Element], record: dict) -> None:
    m = metadata(meta_norm)
    identifiers = " ".join(m.values())
    alias = expected_alias(record)
    if alias not in identifiers and alias.replace("ü", "ue") not in identifiers:
        raise ValueError(f"XML metadata does not identify {alias}: {identifiers[:240]}")
    if len(norms) < 2:
        raise ValueError("XML package lacks text norms")
    target = target_section(record)
    if target:
        if not any(metadata(n).get("enbez", "") == target for n in norms):
            raise ValueError(f"expected section {target} not found in XML package")


def render_zip(raw_zip: bytes, record: dict, descriptor: dict) -> bytes:
    with zipfile.ZipFile(BytesIO(raw_zip)) as archive:
        xml_names = [n for n in archive.namelist() if n.lower().endswith(".xml") and not n.startswith("__MACOSX/")]
        if len(xml_names) != 1:
            raise ValueError(f"expected one XML document in publisher ZIP; found {xml_names}")
        xml_bytes = archive.read(xml_names[0])
    meta_norm, norms = extract_main_norm(xml_bytes)
    validate_norms(meta_norm, norms, record)
    meta = metadata(meta_norm)
    meta_node = child(meta_norm, "metadaten")
    consolidation_notes = "; ".join(
        text(x) for x in (list(meta_node) if meta_node is not None else [])
        if x.tag.rsplit("}", 1)[-1] == "standangabe"
    )
    if target_section(record):
        norms = [n for n in norms if metadata(n).get("enbez", "") == target_section(record)]
    alias = expected_alias(record)
    title = record["title"]
    out = [
        f"# {title}", "",
        "- Jurisdiction: Germany (federal law)",
        f"- Candidate ID: `{record['id']}`",
        f"- Official act abbreviation: `{alias}`",
        f"- Publisher: Federal Ministry of Justice / Federal Office of Justice, Gesetze im Internet",
        f"- Publisher norm ID: `{meta_norm.attrib.get('doknr', '')}`",
        f"- Consolidated source build date: `{meta_norm.attrib.get('builddate', '')}`",
        f"- Consolidation note: `{consolidation_notes}`",
        f"- Official XML package: {descriptor['xml_url']}",
        f"- Official page: {record['url']}",
        f"- Retrieved: {descriptor['retrieved_at']}",
        f"- Source ZIP SHA-256: `{descriptor['source_sha256']}`",
        "",
        "> **Review candidate.** The publisher describes this as a consolidated law text; the published Bundesgesetzblatt remains the authoritative promulgation record. This conversion is not accepted into the trusted legal corpus.",
        "> **Attribution:** Federal Ministry of Justice / Federal Office of Justice, Gesetze im Internet. The publisher states German legal norms are available for free use and reuse.",
        "",
        "## Consolidated statutory text (German)", "",
    ]
    for norm in norms:
        m = metadata(norm)
        number = m.get("enbez", "").strip()
        titlepart = m.get("titel", "").strip()
        if number or titlepart:
            out.extend([f"### {' '.join(x for x in (number, titlepart) if x)}", ""])
        body = child(norm, "textdaten")
        if body is None:
            continue
        rendered = render_xml_content(body)
        if rendered:
            out.extend([rendered, ""])
    while out and not out[-1]:
        out.pop()
    return ("\n".join(out) + "\n").encode("utf-8")


def update_catalog(records: list[dict]) -> None:
    data = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    by_id = {x["id"]: x for x in data.get("documents", [])}
    for rec in records:
        item = by_id[rec["candidate_id"]]
        item.update({
            "retrieval_status": rec["retrieval_status"],
            "retrieved": rec["retrieval_status"] == "converted_review_candidate",
            "accepted": False,
        })
        for key in ("candidate_text_path", "source_sha256", "converted_sha256", "raw_path", "xml_url", "publisher_build_date"):
            if key in rec:
                item[key] = rec[key]
    data["candidate_source_count"] = len(data.get("documents", []))
    data["accepted_source_count"] = 0
    data["status"] = "partially_retrieved_review_candidates"
    count = sum(1 for x in by_id.values() if x.get("retrieval_status") == "converted_review_candidate")
    data["retrieval_status"] = f"{count} federal-law conversions saved as review candidates; non-law sources remain pending or discovery-only"
    atomic_write(CANDIDATES, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sync() -> None:
    targets = extract_targets()
    families: dict[str, list[dict]] = {}
    for rec in targets:
        families.setdefault(family_dir(rec["url"]), []).append(rec)
    prior = json.loads(CAPTURES.read_text(encoding="utf-8")) if CAPTURES.exists() else {"families": {}}
    results: list[dict] = []
    errors: list[str] = []
    for path, records in families.items():
        index_url = urllib.parse.urljoin(f"https://{HOST}", path + "index.html")
        family_id = path.strip("/").split("/")[-1]
        previous = prior.get("families", {}).get(family_id, {})
        try:
            page, page_final, page_type = fetch(index_url, "text/html")
            if page_type != "text/html":
                raise ValueError(f"index returned {page_type}, expected text/html")
            parser = Links()
            parser.feed(page.decode("utf-8", "replace"))
            xml_hrefs = [h for h, label in parser.links if "xml.zip" in h.lower() or ("xml" in label.lower() and h.lower().endswith(".zip"))]
            if len(xml_hrefs) != 1:
                raise ValueError(f"expected one official XML ZIP link on law index; found {xml_hrefs}")
            xml_url = urllib.parse.urljoin(page_final, xml_hrefs[0])
            validate_url(xml_url)
            raw_zip, zip_final, zip_type = fetch(xml_url, "application/zip,application/octet-stream")
            if not zipfile.is_zipfile(BytesIO(raw_zip)):
                raise ValueError("publisher XML package is not a valid ZIP archive")
            # Validate the package against every candidate mapped to this law before saving it.
            with zipfile.ZipFile(BytesIO(raw_zip)) as zf:
                xml_names = [n for n in zf.namelist() if n.lower().endswith(".xml") and not n.startswith("__MACOSX/")]
                if len(xml_names) != 1:
                    raise ValueError(f"expected one XML file in package; found {xml_names}")
                xml_bytes = zf.read(xml_names[0])
            for rec in records:
                top, norms = extract_main_norm(xml_bytes)
                validate_norms(top, norms, rec)
            digest = sha256(raw_zip)
            raw_path = save_raw(family_id, raw_zip, "zip")
            descriptor = {
                "family_id": family_id,
                "index_url": index_url,
                "index_final_url": page_final,
                "index_sha256": sha256(page),
                "xml_url": zip_final,
                "content_type": zip_type,
                "bytes": len(raw_zip),
                "source_sha256": digest,
                "raw_path": raw_path,
                "publisher_build_date": extract_main_norm(xml_bytes)[0].attrib.get("builddate"),
                "retrieved_at": previous.get("retrieved_at") if previous.get("source_sha256") == digest else datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "record_ids": [x["id"] for x in records],
                "retrieval_status": "official_current_consolidation_xml_downloaded",
            }
            prior.setdefault("families", {})[family_id] = descriptor
            print(f"downloaded {family_id}: {len(records)} target record(s), {len(raw_zip)} bytes")
            for rec in records:
                content = render_zip(raw_zip, rec, descriptor)
                out_path = f"source-library/germany/candidates/{rec['id']}.md"
                out = ROOT / out_path
                atomic_write(out, content)
                results.append({
                    "candidate_id": rec["id"], "family_id": family_id,
                    "title": rec["title"], "official_url": rec["url"],
                    "xml_url": zip_final, "publisher_norm_id": extract_main_norm(xml_bytes)[0].attrib.get("doknr"),
                    "publisher_build_date": descriptor["publisher_build_date"],
                    "retrieved_at": descriptor["retrieved_at"], "checked_at": descriptor["checked_at"],
                    "content_type": zip_type, "bytes": len(raw_zip), "source_sha256": digest,
                    "raw_path": raw_path, "candidate_text_path": out_path,
                    "converted_sha256": sha256(content), "retrieval_status": "converted_review_candidate",
                    "accepted": False,
                })
            time.sleep(0.5)
        except Exception as exc:
            errors.append(f"{family_id}: {type(exc).__name__}: {exc}")
            print(f"review {family_id}: {type(exc).__name__}: {exc}")
    prior["publisher"] = "Federal Ministry of Justice / Federal Office of Justice, Gesetze im Internet"
    prior["retrieved_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    atomic_write(CAPTURES, (json.dumps(prior, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    retrieval = {
        "manifest_version": 1,
        "jurisdiction": "Germany (federal)",
        "publisher": "Gesetze im Internet",
        "retrieval_method": "For each candidate law family, read the official act index, follow its XML ZIP link, validate the archive and legal abbreviation, then convert the official XML package. The official portal states that German legal norms are free to use and reuse.",
        "documentation": "https://www.gesetze-im-internet.de/hinweise.html",
        "status_page": "https://www.gesetze-im-internet.de/aktuDienst.html",
        "candidate_count": len(results),
        "accepted_source_count": 0,
        "families": prior.get("families", {}),
        "records": results,
    }
    atomic_write(RETRIEVAL, (json.dumps(retrieval, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    update_catalog(results)
    if errors:
        raise SystemExit("\n".join(errors))


def verify() -> None:
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    retrieval = json.loads(RETRIEVAL.read_text(encoding="utf-8"))
    candidates = {x["id"]: x for x in json.loads(CANDIDATES.read_text(encoding="utf-8"))["documents"]}
    errors: list[str] = []
    for rec in retrieval.get("records", []):
        try:
            family = captures["families"][rec["family_id"]]
            raw = (ROOT / family["raw_path"]).read_bytes()
            if sha256(raw) != family["source_sha256"] or sha256(raw) != rec["source_sha256"]:
                raise ValueError("official ZIP hash mismatch")
            content = render_zip(raw, candidates[rec["candidate_id"]], family)
            if sha256(content) != rec["converted_sha256"]:
                raise ValueError("deterministic conversion hash mismatch")
            path = ROOT / rec["candidate_text_path"]
            if sha256(path.read_bytes()) != rec["converted_sha256"]:
                raise ValueError("saved Markdown differs from deterministic replay")
            print(f"verified {rec['candidate_id']} ({family['publisher_build_date']})")
        except Exception as exc:
            errors.append(f"{rec.get('candidate_id')}: {type(exc).__name__}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))


def convert() -> None:
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    retrieval = json.loads(RETRIEVAL.read_text(encoding="utf-8"))
    candidates = {x["id"]: x for x in json.loads(CANDIDATES.read_text(encoding="utf-8"))["documents"]}
    for rec in retrieval.get("records", []):
        family = captures["families"][rec["family_id"]]
        raw = (ROOT / family["raw_path"]).read_bytes()
        content = render_zip(raw, candidates[rec["candidate_id"]], family)
        atomic_write(ROOT / rec["candidate_text_path"], content)
        rec["converted_sha256"] = sha256(content)
        rec["converted_bytes"] = len(content)
        rec["retrieval_status"] = "converted_review_candidate"
        rec["accepted"] = False
    atomic_write(RETRIEVAL, (json.dumps(retrieval, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    update_catalog(retrieval.get("records", []))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "sync":
        sync()
    elif mode == "convert":
        convert()
    elif mode == "verify":
        verify()
    else:
        raise SystemExit("usage: sync_germany.py [sync|convert|verify]")


if __name__ == "__main__":
    main()
