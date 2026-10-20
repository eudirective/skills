#!/usr/bin/env python3
"""Retrieve and convert identified Spanish BOE consolidated-law candidates."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

PACK = Path(__file__).resolve().parent
REPO_ROOT = PACK.parents[1]
RAW_DIR = REPO_ROOT / "temp" / "spain" / "boe"
OUTPUT_DIR = PACK / "candidates"
MANIFEST_PATH = PACK / "references" / "boe-retrieval-manifest.json"
API_ROOT = "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id"
USER_AGENT = "EU-Directive source-library maintenance/1.0 (https://github.com/eudirective/public-data)"
MAX_RESPONSE_BYTES = 25 * 1024 * 1024
TIMEOUT_SECONDS = 30
REQUEST_INTERVAL_SECONDS = 1.0
AS_OF = "2026-10-19"

SOURCES = [
    ("BOE-A-2007-4184", "Real Decreto 240/2007, EU free movement and residence", "https://www.boe.es/eli/es/rd/2007/02/16/240/con"),
    ("BOE-A-2024-24099", "Real Decreto 1155/2024, immigration regulation", "https://www.boe.es/eli/es/rd/2024/11/19/1155/con"),
    ("BOE-A-2000-544", "Ley Orgánica 4/2000, rights and freedoms of foreign nationals", "https://www.boe.es/eli/es/lo/2000/01/11/4/con"),
    ("BOE-A-2012-9218", "Orden PRE/1490/2012, EU residence-card procedures", "https://www.boe.es/eli/es/o/2012/07/09/pre1490"),
    ("BOE-A-2015-10565", "Ley 39/2015, common administrative procedure", "https://www.boe.es/eli/es/l/2015/10/01/39/con"),
    ("BOE-A-1998-16718", "Ley 29/1998, administrative jurisdiction", "https://www.boe.es/eli/es/l/1998/07/13/29/con"),
    ("BOE-A-2007-19814", "Ley 37/2007, public-sector information reuse", "https://www.boe.es/eli/es/l/2007/11/16/37/con"),
    ("BOE-A-2013-12887", "Ley 19/2013, transparency and access to public information", "https://www.boe.es/eli/es/l/2013/12/09/19/con"),
    ("BOE-A-2011-12628", "Ley 20/2011, Civil Registry", "https://www.boe.es/eli/es/l/2011/07/21/20/con"),
    ("BOE-A-2018-16673", "Ley Orgánica 3/2018, personal-data protection", "https://www.boe.es/eli/es/lo/2018/12/05/3/con"),
    ("BOE-A-1996-750", "Ley 1/1996, free legal aid", "https://www.boe.es/eli/es/l/1996/01/10/1/con"),
    ("BOE-A-2021-3698", "Real Decreto 141/2021, free legal aid regulation", "https://www.boe.es/eli/es/rd/2021/03/09/141/con"),
    ("BOE-A-1981-10325", "Ley Orgánica 3/1981, Defensor del Pueblo", "https://www.boe.es/buscar/act.php?id=BOE-A-1981-10325"),
    ("BOE-A-2007-22438", "Ley 54/2007, international adoption", "https://www.boe.es/eli/es/l/2007/12/28/54/con"),
    ("BOE-A-1889-4763", "Código Civil, civil and private-international-law provisions", "https://www.boe.es/eli/es/rd/1889/07/24/(1)/con"),
]


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def fetch(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/xml", "User-Agent": USER_AGENT},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        final_url = response.geturl()
        if urlparse(final_url).hostname not in {"www.boe.es", "boe.es"}:
            raise ValueError(f"unexpected response host: {urlparse(final_url).hostname}")
        payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ValueError(f"response exceeded {MAX_RESPONSE_BYTES} bytes")
        if response.status != 200:
            raise ValueError(f"unexpected HTTP status {response.status}")
        return payload, final_url


def parse_response(payload: bytes, expected_id: str, require_text: bool) -> ET.Element:
    root = ET.fromstring(payload)
    status = next((e for e in root.iter() if local_name(e.tag) == "code"), None)
    if status is None or (status.text or "").strip() != "200":
        raise ValueError(f"BOE API status is {(status.text if status is not None else 'missing')!r}")
    if require_text:
        text_root = next((e for e in root.iter() if local_name(e.tag) == "texto"), None)
        if text_root is None:
            raise ValueError("response has no consolidated text element")
        ids = {e.attrib.get("id_norma") for e in text_root.iter() if local_name(e.tag) == "version"}
        if expected_id not in ids:
            raise ValueError(f"response does not identify requested source {expected_id}")
        if not any(local_name(e.tag) == "bloque" for e in text_root.iter()):
            raise ValueError("response has no text blocks")
    return root


def element_text(node: ET.Element) -> str:
    out: list[str] = []
    if node.text:
        out.append(node.text)
    for child in list(node):
        tag = local_name(child.tag)
        if tag == "br":
            out.append("\n")
        else:
            out.append(element_text(child))
        if child.tail:
            out.append(child.tail)
    return "".join(out).replace("\u00a0", " ")


def clean_paragraph(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return " ".join(line for line in lines if line).strip()


def version_body(version: ET.Element) -> str:
    paragraphs: list[str] = []
    for child in list(version):
        tag = local_name(child.tag)
        if tag in {"p", "blockquote"}:
            text = clean_paragraph(element_text(child))
            if text:
                paragraphs.append(text)
        elif tag == "br":
            continue
        else:
            text = clean_paragraph(element_text(child))
            if text:
                paragraphs.append(text)
    if not paragraphs:
        return clean_paragraph(element_text(version))
    return "\n\n".join(paragraphs)


def metadata_values(root: ET.Element, expected_id: str) -> dict:
    metadata = next((e for e in root.iter() if local_name(e.tag) == "metadatos"), None)
    if metadata is None:
        raise ValueError("metadata response has no metadata element")
    values = {}
    for e in metadata.iter():
        tag = local_name(e.tag)
        if tag != "metadatos":
            value = clean_paragraph("".join(e.itertext()))
            if value:
                values[tag] = value
    if values.get("identificador") != expected_id:
        raise ValueError(f"metadata identifies {values.get('identificador')!r}, expected {expected_id}")
    return values


def markdown_for(source: tuple[str, str, str], raw: bytes, acquired_at: str, publisher_metadata: dict | None = None) -> tuple[bytes, dict]:
    source_id, title, eli_url = source
    root = parse_response(raw, source_id, require_text=True)
    text_root = next(e for e in root.iter() if local_name(e.tag) == "texto")
    blocks = []
    for block in (e for e in list(text_root) if local_name(e.tag) == "bloque"):
        versions = [e for e in list(block) if local_name(e.tag) == "version"]
        if not versions:
            continue
        selected = versions[-1]
        body = version_body(selected)
        if not body:
            continue
        block_id = block.attrib.get("id", "")
        block_type = block.attrib.get("tipo", "")
        block_title = block.attrib.get("titulo", "").strip()
        heading = block_title or block_id or block_type or "Texto"
        # Source block/version identifiers are retained inline for audit and replay.
        comment = (
            f"<!-- block={block_id!r} type={block_type!r} version={selected.attrib.get('id_norma','')!r} "
            f"publication={selected.attrib.get('fecha_publicacion','')!r} effective={selected.attrib.get('fecha_vigencia','')!r} -->"
        )
        blocks.append(f"{comment}\n\n## {heading}\n\n{body}")
    if not blocks:
        raise ValueError("conversion produced no text blocks")
    content = (
        f"# {title}\n\n"
        f"- Jurisdiction: Spain\n"
        f"- Publisher identifier: `{source_id}`\n"
        f"- Official publisher record: {eli_url}\n"
        f"- BOE API text endpoint: {API_ROOT}/{source_id}/texto\n"
        f"- Retrieved: {acquired_at}\n"
        f"- BOE consolidation status: {(publisher_metadata or {}).get('estado_consolidacion', 'not checked')}\n"
        f"- BOE metadata last updated: {(publisher_metadata or {}).get('fecha_actualizacion', 'not supplied')}\n"
        f"- BOE text effective date in metadata: {(publisher_metadata or {}).get('fecha_vigencia', 'not supplied')}\n"
        f"- Conversion: BOE XML, latest returned version per text block, converted to Markdown\n\n"
        f"> **Informational consolidated text only.** It is not an official authentic publication. Verify legal effect against the relevant BOE Gazette publication before legal reliance.\n>\n"
        f"> **Attribution:** Based on data from the Agencia Estatal Boletín Oficial del Estado.\n\n"
        + "\n\n".join(blocks)
        + "\n"
    )
    return content.encode("utf-8"), {"converted_block_count": len(blocks)}


def consolidation_state(root: ET.Element) -> str | None:
    for e in root.iter():
        if local_name(e.tag).replace("_", "").lower() in {"estadoconsolidacion", "estadodeconsolidacion"}:
            value = clean_paragraph("".join(e.itertext()))
            if value:
                return value
    return None


def candidate_path(source_id: str) -> Path:
    return OUTPUT_DIR / f"{source_id.lower()}-consolidated.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_inventory_status(successful: set[str]) -> None:
    paths = [
        PACK / "references" / "candidate-manifest.json",
        PACK / "references" / "monitor-candidate-manifest-2026-10-18.json",
    ]
    for path in paths:
        if not path.exists():
            continue
        data = load_json(path)
        entries = data.get("documents", data.get("sources", []))
        changed = False
        for item in entries:
            joined = " ".join([
                item.get("url", ""), item.get("title", ""),
                json.dumps(item.get("publisher_identifier", {}), ensure_ascii=False),
            ])
            found = next((source_id for source_id in successful if source_id in joined), None)
            if found:
                item["retrieved"] = True
                item["accepted"] = False
                item["retrieval_status"] = "converted_review_candidate"
                item["document_path"] = f"../candidates/{found.lower()}-consolidated.md"
                changed = True
        if changed:
            review_count = sum(1 for item in entries if "review_candidate" in item.get("retrieval_status", ""))
            if "retrieved_review_candidate_count" in data:
                data["retrieved_review_candidate_count"] = review_count
            if "retrieved_converted_candidate_count" in data:
                data["retrieved_converted_candidate_count"] = review_count
            data["accepted_source_count"] = 0
            atomic_write(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sync() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    failures = []
    successful: set[str] = set()
    previous_request = 0.0
    for source in SOURCES:
        source_id, title, eli_url = source
        text_url = f"{API_ROOT}/{source_id}/texto"
        metadata_url = f"{API_ROOT}/{source_id}/metadatos"
        item = {
            "id": source_id,
            "title": title,
            "official_publisher_url": eli_url,
            "text_api_url": text_url,
            "metadata_api_url": metadata_url,
            "accepted": False,
        }
        try:
            for url, suffix in [(text_url, "text"), (metadata_url, "metadata")]:
                delay = REQUEST_INTERVAL_SECONDS - (time.monotonic() - previous_request)
                if delay > 0:
                    time.sleep(delay)
                payload, final_url = fetch(url)
                previous_request = time.monotonic()
                parse_response(payload, source_id, require_text=(suffix == "text"))
                raw_path = RAW_DIR / f"{source_id.lower()}-{suffix}.xml"
                atomic_write(raw_path, payload)
                item[f"{suffix}_raw_path"] = str(raw_path.relative_to(REPO_ROOT))
                item[f"{suffix}_sha256"] = sha256(payload)
                item[f"{suffix}_bytes"] = len(payload)
                item[f"{suffix}_response_url"] = final_url
                if suffix == "metadata":
                    parsed_metadata = ET.fromstring(payload)
                    item["publisher_metadata"] = metadata_values(parsed_metadata, source_id)
                    item["consolidation_state"] = item["publisher_metadata"].get("estado_consolidacion", "not stated in API response")
            acquired = datetime.now(timezone.utc).isoformat(timespec="seconds")
            converted, conversion_info = markdown_for(
                source,
                (RAW_DIR / f"{source_id.lower()}-text.xml").read_bytes(),
                acquired,
                item.get("publisher_metadata"),
            )
            output_path = candidate_path(source_id)
            atomic_write(output_path, converted)
            item["converted_path"] = str(output_path.relative_to(REPO_ROOT))
            item["converted_sha256"] = sha256(converted)
            item["converted_bytes"] = len(converted)
            item["retrieved_at"] = acquired
            item.update(conversion_info)
            item["retrieval_status"] = "converted_review_candidate"
            successful.add(source_id)
            print(f"converted {source_id} ({len(converted)} bytes)")
        except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError, OSError) as exc:
            item["retrieval_status"] = "retrieval_or_conversion_failed"
            item["error"] = str(exc)
            failures.append(source_id)
            print(f"failed {source_id}: {exc}", file=sys.stderr)
        records.append(item)
    data = {
        "manifest_version": 1,
        "jurisdiction": "Spain",
        "publisher": "Agencia Estatal Boletín Oficial del Estado",
        "retrieval_date": datetime.now(timezone.utc).date().isoformat(),
        "api_documentation": "https://www.boe.es/datosabiertos/api/api.php?lang=es",
        "reuse_terms": "https://www.boe.es/informacion/aviso_legal/index.php",
        "conversion_scope": "The API returns all versions; this converter selects the last returned version in each block, matching the BOE latest-version ordering. Raw XML is retained for replay.",
        "review_notice": "All converted texts are informational review candidates and remain unaccepted. BOE metadata status and Gazette publications must be reviewed before legal reliance.",
        "records": records,
        "failures": failures,
    }
    atomic_write(MANIFEST_PATH, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    save_inventory_status(successful)
    print(f"completed: {len(successful)}/{len(SOURCES)} converted; {len(failures)} failed; none accepted")
    return 1 if failures else 0


def rebuild() -> int:
    """Convert already retained publisher responses without another network request."""
    records = []
    failures = []
    successful: set[str] = set()
    for source in SOURCES:
        source_id, title, eli_url = source
        text_path = RAW_DIR / f"{source_id.lower()}-text.xml"
        metadata_path = RAW_DIR / f"{source_id.lower()}-metadata.xml"
        item = {
            "id": source_id,
            "title": title,
            "official_publisher_url": eli_url,
            "text_api_url": f"{API_ROOT}/{source_id}/texto",
            "metadata_api_url": f"{API_ROOT}/{source_id}/metadatos",
            "accepted": False,
        }
        try:
            raw = text_path.read_bytes()
            metadata_raw = metadata_path.read_bytes()
            metadata_root = parse_response(metadata_raw, source_id, require_text=False)
            publisher_metadata = metadata_values(metadata_root, source_id)
            parse_response(raw, source_id, require_text=True)
            retrieved_at = datetime.fromtimestamp(text_path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
            converted, conversion_info = markdown_for(source, raw, retrieved_at, publisher_metadata)
            output_path = candidate_path(source_id)
            atomic_write(output_path, converted)
            item.update({
                "text_raw_path": str(text_path.relative_to(REPO_ROOT)),
                "text_sha256": sha256(raw),
                "text_bytes": len(raw),
                "metadata_raw_path": str(metadata_path.relative_to(REPO_ROOT)),
                "metadata_sha256": sha256(metadata_raw),
                "metadata_bytes": len(metadata_raw),
                "publisher_metadata": publisher_metadata,
                "consolidation_state": publisher_metadata.get("estado_consolidacion", "not stated in API response"),
                "converted_path": str(output_path.relative_to(REPO_ROOT)),
                "converted_sha256": sha256(converted),
                "converted_bytes": len(converted),
                "retrieved_at": retrieved_at,
                "retrieval_status": "converted_review_candidate",
                **conversion_info,
            })
            successful.add(source_id)
            records.append(item)
        except (ValueError, ET.ParseError, OSError) as exc:
            item["retrieval_status"] = "retrieval_or_conversion_failed"
            item["error"] = str(exc)
            failures.append(source_id)
            records.append(item)
    data = {
        "manifest_version": 1,
        "jurisdiction": "Spain",
        "publisher": "Agencia Estatal Boletín Oficial del Estado",
        "retrieval_date": datetime.now(timezone.utc).date().isoformat(),
        "api_documentation": "https://www.boe.es/datosabiertos/api/api.php?lang=es",
        "reuse_terms": "https://www.boe.es/informacion/aviso_legal/index.php",
        "conversion_scope": "The API returns all versions; this converter selects the last returned version in each block, matching the BOE latest-version ordering. Raw XML is retained for replay.",
        "review_notice": "All converted texts are informational review candidates and remain unaccepted. BOE metadata status and Gazette publications must be reviewed before legal reliance.",
        "records": records,
        "failures": failures,
    }
    atomic_write(MANIFEST_PATH, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    save_inventory_status(successful)
    print(f"rebuilt from retained responses: {len(successful)}/{len(SOURCES)} converted; {len(failures)} failed; none accepted")
    return 1 if failures else 0


def verify() -> int:
    data = load_json(MANIFEST_PATH)
    errors = []
    for item in data.get("records", []):
        if item.get("retrieval_status") != "converted_review_candidate":
            continue
        raw_path = REPO_ROOT / item["text_raw_path"]
        output_path = REPO_ROOT / item["converted_path"]
        if not raw_path.exists() or not output_path.exists():
            errors.append(f"{item['id']}: raw or Markdown file missing")
            continue
        raw = raw_path.read_bytes()
        output = output_path.read_bytes()
        if sha256(raw) != item["text_sha256"]:
            errors.append(f"{item['id']}: raw hash mismatch")
            continue
        if sha256(output) != item["converted_sha256"]:
            errors.append(f"{item['id']}: Markdown hash mismatch")
            continue
        rebuilt, _ = markdown_for(
            (item["id"], item["title"], item["official_publisher_url"]),
            raw,
            item["retrieved_at"],
            item.get("publisher_metadata"),
        )
        if rebuilt != output:
            errors.append(f"{item['id']}: offline conversion replay mismatch")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("offline hash and conversion replay succeeded for all converted review candidates")
    return 0


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if command == "sync":
        raise SystemExit(sync())
    if command == "rebuild":
        raise SystemExit(rebuild())
    if command == "verify":
        raise SystemExit(verify())
    raise SystemExit("usage: python sync_boe.py [sync|rebuild|verify]")
