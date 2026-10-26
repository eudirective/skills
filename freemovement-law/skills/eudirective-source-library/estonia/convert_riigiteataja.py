#!/usr/bin/env python3
"""Resolve date-valid Estonian legislation, retrieve official XML, and convert it."""
from __future__ import annotations

import hashlib
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
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
REFS = PACK / "references"
TEMP_ROOT = Path(os.environ.get("PUBLIC_DATA_TEMP_ROOT", "/tmp/public-data"))
TEMP_ESTONIA = TEMP_ROOT / "temp" / "estonia"
CANDIDATES = TEMP_ESTONIA / "candidate-manifest.json"
CAPTURES = TEMP_ESTONIA / "capture-manifest.json"
RETRIEVAL = TEMP_ESTONIA / "retrieval-manifest.json"
HOST = "www.riigiteataja.ee"
USER_AGENT = "eudirective-source-library/1.0 (bounded official law retrieval; eudirective@proton.me)"
MAX_BYTES = 16 * 1024 * 1024
TIMEOUT = 35
PAGE_SIZE = 500
TARGETS = [
    {
        "id": "ee-aliens-act-current-2026-10",
        "candidate_id": "ee-aliens-act-current-2026-10",
        "title": "Aliens Act",
        "official_title": "Välismaalaste seadus",
        "language": "et",
        "source_type": "national_act_current_consolidation",
        "functional_relationship": "related_source",
    },
    {
        "id": "ee-citizen-act-current-2026-10",
        "candidate_id": "ee-citizen-act-current-2026-10",
        "title": "Citizen of the European Union Act",
        "official_title": "Euroopa Liidu kodaniku seadus",
        "language": "et",
        "source_type": "national_act_current_consolidation",
        "functional_relationship": "close_functional_match",
    },
]


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


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def find_child(element: ET.Element, name: str) -> ET.Element | None:
    return next((child for child in element if local_name(child) == name), None)


def text_of(element: ET.Element | None) -> str:
    return normalized("".join(element.itertext())) if element is not None else ""


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != HOST:
        raise ValueError(f"refused non-allowlisted URL: {url}")


def fetch(url: str, accept: str | None = None) -> tuple[bytes, str, str]:
    validate_url(url)
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as response:
        final_url = response.geturl()
        validate_url(final_url)
        content_type = response.headers.get_content_type().lower()
        chunks: list[bytes] = []
        total = 0
        while True:
            part = response.read(min(64 * 1024, MAX_BYTES + 1 - total))
            if not part:
                break
            chunks.append(part)
            total += len(part)
            if total > MAX_BYTES:
                raise ValueError(f"response exceeds {MAX_BYTES} byte cap")
        return b"".join(chunks), final_url, content_type


def save_raw(stem: str, data: bytes, suffix: str) -> str:
    digest = sha256(data)
    relative = f"temp/estonia/raw/{stem}-{digest}.{suffix}"
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("refused capture output outside repository root")
    if path.exists() and sha256(path.read_bytes()) != digest:
        raise ValueError(f"hash-addressed capture path conflicts: {relative}")
    if not path.exists():
        atomic_write(path, data)
    return relative


def search_url(as_of: str, page: int) -> str:
    query = urllib.parse.urlencode({
        "leht": page,
        "limiit": PAGE_SIZE,
        "dokument": "seadus",
        "kehtiv": as_of,
        "kehtivKehtetus": "false",
        "mitteJoustunud": "false",
    })
    return f"https://{HOST}/api/oigusakt_otsing/1/otsi?{query}"


def parse_validity(value: dict, as_of: str) -> None:
    period = value.get("kehtivus") or {}
    start, end = period.get("algus"), period.get("lopp")
    if not start or start > as_of or (end and end < as_of):
        raise ValueError(f"record is not in force on {as_of}: {period}")
    if value.get("kehtivKehtetus") or value.get("mitteJoustunud"):
        raise ValueError("dated search returned a repealed or not-yet-effective version")


def validate_xml(raw: bytes, act_id: int, title: str, as_of: str) -> tuple[ET.Element, dict]:
    root = ET.fromstring(raw)
    if local_name(root) != "oigusakt":
        raise ValueError(f"unexpected XML root element: {local_name(root)}")
    metadata = find_child(root, "metaandmed")
    if metadata is None:
        raise ValueError("XML response lacks legal-act metadata")
    meta = {local_name(child): text_of(child) for child in metadata}
    if meta.get("globaalID") != str(act_id):
        raise ValueError(f"XML global ID {meta.get('globaalID')!r} does not match search result {act_id}")
    if meta.get("tekstiliik") not in {"terviktekst", "algtekst-terviktekst"}:
        raise ValueError(f"unexpected text type: {meta.get('tekstiliik')!r}")
    if meta.get("dokumentLiik") != "seadus":
        raise ValueError(f"unexpected document type: {meta.get('dokumentLiik')!r}")
    period = meta.get("kehtivus", "").split()
    if len(period) < 1 or period[0] > as_of or (len(period) > 1 and period[1] and period[1] < as_of):
        raise ValueError(f"XML validity interval {meta.get('kehtivus')!r} does not cover {as_of}")
    act_title = text_of(find_child(root, "aktinimi"))
    if not act_title.startswith(title):
        raise ValueError(f"XML act title {act_title!r} does not match expected {title!r}")
    body = find_child(root, "sisu")
    if body is None or len(list(body.iter())) < 20:
        raise ValueError("XML has no substantial consolidated act body")
    return root, {**meta, "actual_title": act_title}


def metadata_note(element: ET.Element) -> str:
    return text_of(element)


def render_document(root: ET.Element, descriptor: dict) -> bytes:
    meta_node = find_child(root, "metaandmed")
    meta = {local_name(child): text_of(child) for child in meta_node} if meta_node is not None else {}
    act_title = text_of(find_child(root, "aktinimi"))
    body = find_child(root, "sisu")
    out: list[str] = [
        f"# {descriptor['title']} ({act_title})",
        "",
        f"- Jurisdiction: Estonia",
        f"- Candidate ID: `{descriptor['candidate_id']}`",
        f"- Official title: `{act_title}`",
        f"- Language: {descriptor['language']} (Estonian; source text is authoritative in Estonian)",
        f"- Publisher: Riigi Teataja, Riigikogu / State Gazette",
        f"- {descriptor.get('retrieval_label') or ('Exact effective-date search: ' + descriptor['as_of_date'])}",
        f"- Official consolidation ID: `{meta.get('globaalID')}`",
        f"- Effective period in source metadata: `{meta.get('kehtivus')}`",
        f"- Source URL: {descriptor['source_url']}",
        f"- XML API URL: {descriptor['api_url']}",
        f"- Retrieved: {descriptor['retrieved_at']}",
        f"- Source SHA-256: `{descriptor['source_sha256']}`",
        "",
        descriptor.get("review_note", "> **Review candidate.** This is the official consolidated text returned for the effective date above. It has not been accepted into the trusted legal corpus; compare scope, commencement, translations and any subsequent version before relying on it."),
        "> **Attribution:** Based on Riigi Teataja public legal text. The Gazette documents XML download of published acts; source URL and exact version ID are retained.",
        "",
        "## Consolidated statutory text (Estonian)",
        "",
    ]

    def heading(node: ET.Element, num_name: str, title_name: str, level: int) -> None:
        number = text_of(find_child(node, num_name))
        title = text_of(find_child(node, title_name))
        label = " — ".join(x for x in (number, title) if x)
        if label:
            out.extend(["#" * level + " " + label, ""])

    def note(node: ET.Element) -> None:
        for child in node:
            if local_name(child) == "muutmismarge":
                value = metadata_note(child)
                if value:
                    out.extend([f"> Version note: {value}", ""])

    def walk(node: ET.Element, depth: int = 0) -> None:
        for child in node:
            tag = local_name(child)
            if tag == "peatykk":
                heading(child, "peatykkNr", "peatykkPealkiri", 2)
                walk(child, depth + 1)
            elif tag == "jagu":
                heading(child, "jaguNr", "jaguPealkiri", 3)
                walk(child, depth + 1)
            elif tag in {"jaotis", "alljaotis"}:
                heading(child, tag + "Nr", tag + "Pealkiri", min(4, 3 + depth))
                walk(child, depth + 1)
            elif tag == "paragrahv":
                visible = text_of(find_child(child, "kuvatavNr"))
                title = text_of(find_child(child, "paragrahvPealkiri"))
                label = " ".join(x for x in (visible, title) if x)
                if label:
                    out.extend([f"#### {label}", ""])
                for part in child:
                    ptag = local_name(part)
                    if ptag == "loige":
                        render_clause(part, 0)
                    elif ptag == "sisuTekst":
                        value = text_of(part)
                        if value:
                            out.extend([value, ""])
                    elif ptag not in {"kuvatavNr", "paragrahvNr", "paragrahvPealkiri"}:
                        render_misc(part, depth + 1)
                note(child)
            elif tag in {"loige", "alampunkt"}:
                render_clause(child, 0)
            elif tag in {"muutmismarge", "kuvatavNr", "peatykkNr", "peatykkPealkiri", "jaguNr", "jaguPealkiri", "jaotisNr", "jaotisPealkiri", "alljaotisNr", "alljaotisPealkiri"}:
                continue
            elif tag in {"reavahetus"}:
                out.append("")
            else:
                render_misc(child, depth)

    def render_clause(node: ET.Element, list_depth: int) -> None:
        visible = text_of(find_child(node, "kuvatavNr")) or text_of(find_child(node, "loigeNr"))
        body_text = text_of(find_child(node, "sisuTekst"))
        if body_text:
            prefix = (visible + " ") if visible else ""
            indent = "  " * min(list_depth, 1)
            out.extend([indent + prefix + body_text, ""])
        for child in node:
            tag = local_name(child)
            if tag in {"alampunkt", "punkt", "loeteluPunkt"}:
                render_clause(child, list_depth + 1)
            elif tag == "muutmismarge":
                value = metadata_note(child)
                if value:
                    out.extend([f"> Version note: {value}", ""])
            elif tag not in {"kuvatavNr", "loigeNr", "sisuTekst"}:
                render_misc(child, list_depth + 1)

    def render_misc(node: ET.Element, depth: int) -> None:
        tag = local_name(node)
        # Riigi Teataja may wrap all article and chapter nodes in an ``osa``
        # element. Keep those legal headings by sending structural containers
        # back through the document walker instead of flattening them as text.
        if tag in {"osa", "peatykk", "jagu", "jaotis", "alljaotis", "paragrahv"}:
            walk(node, depth)
            return
        if tag in {"sisuTekst", "tavatekst"}:
            value = text_of(node)
            if value:
                out.extend([("  " * max(0, depth - 1)) + value, ""])
            return
        if tag in {"alampunkt", "punkt", "loeteluPunkt"}:
            render_clause(node, depth)
            return
        if tag == "muutmismarge":
            value = metadata_note(node)
            if value:
                out.extend([f"> Version note: {value}", ""])
            return
        for child in node:
            render_misc(child, depth)

    walk(body)
    while out and not out[-1]:
        out.pop()
    return ("\n".join(out) + "\n").encode("utf-8")


def update_catalog(records: list[dict]) -> None:
    catalog = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    existing = {item["id"]: item for item in catalog.get("documents", [])}
    for descriptor in records:
        rec = existing.get(descriptor["candidate_id"])
        if rec is None:
            rec = {
                "id": descriptor["candidate_id"],
                "title": descriptor["title"],
                "source_type": descriptor["source_type"],
                "language": "et",
                "url": descriptor["source_url"],
                "publisher_identifier": {"system": "Riigi Teataja", "record": str(descriptor["act_id"])},
                "functional_relationship": descriptor["functional_relationship"],
                "verification_status": "Current consolidated text resolved from the official law list for the recorded effective date; XML response identity and validity interval checked.",
                "retrieval_shape": "Official date-filtered law search API -> exact act XML API",
                "retrieved": False,
                "accepted": False,
            }
            catalog.setdefault("documents", []).append(rec)
            existing[rec["id"]] = rec
        rec.update({
            "retrieval_status": descriptor.get("retrieval_status", "resolved_official_current_version"),
            "version_evidence": f"Official list for {descriptor['as_of_date']} resolves global ID {descriptor['act_id']} with in-force period {descriptor['validity_period']}.",
            "retrieved": descriptor.get("retrieval_status") == "converted_review_candidate",
            "accepted": False,
        })
        if descriptor.get("retrieval_status") == "converted_review_candidate":
            rec.update({
                "candidate_text_path": descriptor["output_path"],
                "source_sha256": descriptor["source_sha256"],
                "converted_sha256": descriptor["converted_sha256"],
            })
    catalog["candidate_source_count"] = len(catalog.get("documents", []))
    catalog["accepted_source_count"] = 0
    catalog["status"] = "partial_retrieval_review_candidates"
    catalog["retrieval_status"] = f"{sum(1 for x in existing.values() if x.get('retrieval_status') == 'converted_review_candidate')} current-law conversions saved; other candidate records remain pending or discovery-only"
    atomic_write(CANDIDATES, (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sync() -> None:
    as_of = date.today().isoformat()
    old = json.loads(CAPTURES.read_text(encoding="utf-8")) if CAPTURES.exists() else {"search_pages": [], "records": []}
    searches: list[dict] = []
    all_rows: list[dict] = []
    total: int | None = None
    for page in range(1, 10):
        url = search_url(as_of, page)
        raw, final_url, content_type = fetch(url, "application/json")
        if content_type != "application/json":
            raise ValueError(f"law-list API returned {content_type}, expected JSON")
        response = json.loads(raw.decode("utf-8"))
        if not isinstance(response.get("aktid"), list) or not isinstance(response.get("metaandmed"), dict):
            raise ValueError("law-list API response lacks aktid/metaandmed arrays")
        if total is None:
            total = int(response["metaandmed"].get("kokku", 0))
        if response["metaandmed"].get("leht") != page:
            raise ValueError(f"search API returned page {response['metaandmed'].get('leht')} for requested page {page}")
        rel = save_raw(f"laws-{as_of}-page-{page}", raw, "json")
        searches.append({"page": page, "requested_url": url, "final_url": final_url, "content_type": content_type, "bytes": len(raw), "sha256": sha256(raw), "raw_path": rel, "row_count": len(response["aktid"]), "total_count": total})
        all_rows.extend(response["aktid"])
        if len(all_rows) >= total:
            break
        time.sleep(1.0)
    if total is None or len(all_rows) < total:
        raise ValueError(f"dated search was incomplete: loaded {len(all_rows)} of {total}")
    previous = {item["candidate_id"]: item for item in old.get("records", [])}
    results = []
    errors = []
    for target in TARGETS:
        item = dict(previous.get(target["candidate_id"], {}))
        try:
            matches = [row for row in all_rows if row.get("pealkiri") == target["official_title"]]
            if len(matches) != 1:
                raise ValueError(f"expected one exact title match for {target['official_title']!r}; found {len(matches)}")
            row = matches[0]
            parse_validity(row, as_of)
            act_id = int(row["globaalID"])
            api_url = f"https://{HOST}/public-api/api/v1/akt/{act_id}/xml"
            raw, final_url, content_type = fetch(api_url)
            if not (raw.lstrip().startswith(b"<?xml") or raw.lstrip().startswith(b"<")):
                raise ValueError("XML API payload lacks an XML document signature")
            _, xml_meta = validate_xml(raw, act_id, target["official_title"], as_of)
            rel = save_raw(re.sub(r"[^a-z0-9]+", "-", target["id"].lower()).strip("-"), raw, "xml")
            item.update({
                **target,
                "as_of_date": as_of,
                "act_id": act_id,
                "official_title": row["pealkiri"],
                "validity_period": xml_meta["kehtivus"],
                "current_status": row.get("staatus"),
                "text_type": row.get("tekst"),
                "search_result_url": urllib.parse.urljoin(f"https://{HOST}", row["url"]),
                "source_url": f"https://{HOST}/akt/{act_id}",
                "api_url": final_url,
                "retrieved_at": item.get("retrieved_at") if item.get("source_sha256") == sha256(raw) else datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "content_type": content_type,
                "bytes": len(raw),
                "source_sha256": sha256(raw),
                "raw_path": rel,
                "retrieval_status": "downloaded_ready_for_conversion",
                "accepted": False,
                "error": None,
            })
            print(f"downloaded {target['id']} ID={act_id} validity={xml_meta['kehtivus']} ({len(raw)} bytes)")
        except Exception as exc:
            item.update({**target, "as_of_date": as_of, "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "retrieval_status": "current_version_or_download_review_required", "error": f"{type(exc).__name__}: {exc}", "accepted": False})
            errors.append(f"{target['candidate_id']}: {type(exc).__name__}: {exc}")
            print(f"review {target['candidate_id']}: {type(exc).__name__}: {exc}")
        results.append(item)
        time.sleep(1.0)
    capture_manifest = {"manifest_version": 1, "publisher": "Riigi Teataja", "as_of_date": as_of, "search_pages": searches, "records": results}
    atomic_write(CAPTURES, (json.dumps(capture_manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    retrieval_manifest = {
        "manifest_version": 1,
        "jurisdiction": "Estonia",
        "retrieval_method": "Official effective-date law search API (JSON, 500 records per page) resolves the current consolidated act global ID; exact text is then downloaded from the documented public XML API.",
        "reuse_terms": "https://www.riigiteataja.ee/et/kkk (Open Data section; published acts downloadable as XML individually and in bulk)",
        "as_of_date": as_of,
        "candidate_count": len(results),
        "accepted_source_count": 0,
        "records": results,
    }
    atomic_write(RETRIEVAL, (json.dumps(retrieval_manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    update_catalog(results)
    if errors:
        raise SystemExit("\n".join(errors))


def process(mode: str) -> None:
    captures = json.loads(CAPTURES.read_text(encoding="utf-8"))
    by_id = {item["candidate_id"]: item for item in captures.get("records", [])}
    manifest = json.loads(RETRIEVAL.read_text(encoding="utf-8")) if RETRIEVAL.exists() else {"records": []}
    results = []
    errors = []
    for target in TARGETS:
        item = by_id.get(target["candidate_id"], {})
        if item.get("retrieval_status") not in {"downloaded_ready_for_conversion", "converted_review_candidate"}:
            continue
        try:
            raw = (ROOT / item["raw_path"]).read_bytes()
            root, xml_meta = validate_xml(raw, int(item["act_id"]), item["official_title"], item["as_of_date"])
            content = render_document(root, item)
            result = {**item, "output_path": f"source-library/estonia/candidates/{target['id']}.md", "converted_sha256": sha256(content), "converted_bytes": len(content), "retrieval_status": "converted_review_candidate", "accepted": False}
            out = ROOT / result["output_path"]
            if mode == "verify":
                if sha256(raw) != item["source_sha256"]:
                    raise ValueError("raw XML hash mismatch")
                if item.get("converted_sha256") != result["converted_sha256"]:
                    raise ValueError("manifest conversion hash differs from deterministic replay")
                if sha256(out.read_bytes()) != result["converted_sha256"]:
                    raise ValueError("saved Markdown differs from deterministic replay")
                print(f"verified {target['id']} (official ID, date validity, source hash and conversion replay)")
            else:
                atomic_write(out, content)
                item.update(result)
                results.append(result)
                print(f"converted {target['id']} -> {result['output_path']}")
        except Exception as exc:
            errors.append(f"{target['candidate_id']}: {type(exc).__name__}: {exc}")
    if mode == "convert":
        captures["records"] = [by_id.get(t["candidate_id"], {**t, "retrieval_status": "not_downloaded"}) for t in TARGETS]
        atomic_write(CAPTURES, (json.dumps(captures, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        manifest["records"] = captures["records"]
        manifest["converted_candidate_count"] = sum(1 for item in captures["records"] if item.get("retrieval_status") == "converted_review_candidate")
        manifest["accepted_source_count"] = 0
        atomic_write(RETRIEVAL, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        update_catalog(captures["records"])
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    raise SystemExit(
        "The legacy capture CLI is retired. Use EU Source Update Monitor local research "
        "for new captures, and sync_estonia_legal_texts.py verify for accepted-text replay."
    )


if __name__ == "__main__":
    main()
