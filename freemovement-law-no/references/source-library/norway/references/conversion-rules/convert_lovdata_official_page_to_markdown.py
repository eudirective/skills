#!/usr/bin/env python3
"""Convert one Lovdata current-law page into a hash-validated Markdown copy.

Input is JSON on stdin: content, sha256, archive_path, source_id, retrieved_on,
license, attribution, and language. The official page is parsed with the pinned
standard-library tree parser. Only #documentBody is retained; its statutory
section containers are adapted to the shared source-preserving renderer.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_lovdata_html_to_markdown import BLOCK_TAGS, Node, TreeParser, normalize, render, walk

CONVERTER_VERSION = "1.0.0"
RULE_ID = "NO-LOVDATA-OFFICIAL-LAW-PAGE-001"
RULE_VERSION = "1.0.0"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP_CLASSES = {"share-paragraf", "share-dokument"}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def classes(node: Node) -> set[str]:
    return set((node.attrs.get("class") or "").split())


def safe_attrs(attrs: dict[str, str | None]) -> str:
    allowed = {"id", "class", "href", "title", "type", "start", "value", "scope", "colspan", "rowspan", "lang", "dir", "target", "rel", "alt", "width", "height"}
    parts = []
    for key in sorted(attrs):
        value = attrs[key]
        if value is None or key.lower().startswith("on"):
            continue
        if key in allowed or key.startswith("data-") or key.startswith("aria-"):
            parts.append(f'{key}="{html.escape(value, quote=True)}"')
    return (" " + " ".join(parts)) if parts else ""


def text_of(node: Node | str) -> str:
    if isinstance(node, str):
        return node
    return "".join(text_of(child) for child in node.children)


def visible_text(node: Node | str, *, omit_title: bool = False) -> str:
    if isinstance(node, str):
        return node
    node_classes = classes(node)
    if node_classes & SKIP_CLASSES or (omit_title and "publisherDocumentTitle" in node_classes):
        return ""
    pieces = [" "] if node.tag in BLOCK_TAGS or node.tag == "br" else []
    pieces.extend(visible_text(child, omit_title=omit_title) for child in node.children)
    if node.tag in BLOCK_TAGS or node.tag == "br":
        pieces.append(" ")
    return "".join(pieces)


def serialize_document_body(node: Node, document_path: str) -> str:
    if node.tag in {"script", "style", "noscript"} or classes(node) & SKIP_CLASSES:
        return ""
    tag = node.tag
    attrs = dict(node.attrs)
    ident = str(attrs.get("id") or "")
    if ident == "documentBody":
        attrs["class"] = "documentBody"
        attrs["data-lovdata-url"] = document_path
    elif re.fullmatch(r"PARAGRAF_\d+", ident):
        section = ident.rsplit("_", 1)[1]
        tag = "article"
        attrs["class"] = " ".join(sorted(classes(node) | {"legalArticle"}))
        attrs["data-name"] = f"§{section}"
    elif re.fullmatch(r"ARTIKKEL_\d+", ident):
        article = ident.rsplit("_", 1)[1]
        tag = "article"
        attrs["class"] = " ".join(sorted(classes(node) | {"legalArticle"}))
        attrs["data-name"] = f"a{article}"
    if "paragrafHeader" in classes(node):
        attrs["class"] = " ".join(sorted(classes(node) | {"legalArticleHeader"}))
    inner = "".join(serialize_document_body(child, document_path) if isinstance(child, Node) else html.escape(child, quote=False) for child in node.children)
    if tag in VOID:
        return f"<{tag}{safe_attrs(attrs)} />"
    return f"<{tag}{safe_attrs(attrs)}>{inner}</{tag}>"


def metadata_value(nodes: list[Node], element_id: str) -> str:
    matches = [node for node in nodes if node.attrs.get("id") == element_id]
    return normalize(text_of(matches[0])) if len(matches) == 1 else ""


def convert(record: dict) -> dict:
    page = record.get("content")
    expected = record.get("sha256")
    archive_path = record.get("archive_path")
    if not isinstance(page, str) or not isinstance(expected, str) or not archive_path:
        raise ValueError("input requires content, sha256, and archive_path")
    actual = digest(page)
    if actual != expected:
        raise ValueError(f"official page byte hash mismatch: expected {expected}, got {actual}")
    parser = TreeParser()
    parser.feed(page)
    parser.close()
    nodes = list(walk(parser.root))
    body_nodes = [node for node in nodes if node.attrs.get("id") == "documentBody"]
    if len(body_nodes) != 1:
        raise ValueError(f"expected one official #documentBody, found {len(body_nodes)}")
    meta_nodes = [node for node in nodes if node.attrs.get("id", "").startswith("metaField_")]
    # Lovdata's displayed title is the h1 inside the unique documentMeta panel.
    meta_panel = [node for node in nodes if node.attrs.get("id") == "documentMeta"]
    if len(meta_panel) != 1:
        raise ValueError(f"expected one official #documentMeta, found {len(meta_panel)}")
    title_matches = [node for node in walk(meta_panel[0]) if node.tag == "h1"]
    if len(title_matches) != 1:
        raise ValueError(f"expected one title h1 in #documentMeta, found {len(title_matches)}")
    title = normalize(text_of(title_matches[0]))
    identifier = metadata_value(meta_nodes, "metaField_dato")
    changed_nodes = [node for node in meta_nodes if node.attrs.get("id") == "metaField_endret"]
    changed_by = ""
    if len(changed_nodes) == 1:
        links = [node for node in walk(changed_nodes[0]) if node.tag == "a"]
        changed_by = str((links[0].attrs.get("data-id") or text_of(links[0])) if links else text_of(changed_nodes[0])).strip()
    short_title = metadata_value(meta_nodes, "metaField_korttittel")
    corrected = metadata_value(meta_nodes, "metaField_rettet")
    published = metadata_value(meta_nodes, "metaField_kunngjort")
    doc_path_match = re.search(r"\bdocumentURL\s*=\s*[\"'](/dokument/([^\"']+))[\"']", page)
    if not doc_path_match:
        raise ValueError("official page does not expose a Lovdata documentURL")
    document_path = doc_path_match.group(2)
    comparable_identifier = re.sub(r"^(?:LOV|FOR)-", "", identifier, flags=re.IGNORECASE)
    if identifier and comparable_identifier not in document_path:
        raise ValueError("official page identifier and documentURL disagree")
    language = str(record.get("language") or "no")
    metadata = {
        "refid": document_path.split("/", 1)[-1],
        "dokid": document_path,
        "title": title,
        "titleShort": short_title,
        "lastChangedBy": changed_by,
        "lastupdated": corrected,
        "dateOfPublication": published,
    }
    last_change_in_force = str(record.get("last_change_in_force") or "").strip()
    if last_change_in_force:
        metadata["lastChangeInForce"] = last_change_in_force
    metadata_html = "<dl>" + "".join(
        f"<dt class=\"{html.escape(key, quote=True)}\">{html.escape(key)}</dt><dd>{html.escape(value)}</dd>"
        for key, value in metadata.items() if value
    ) + "</dl>"
    title_html = f'<h1 class="publisherDocumentTitle">{html.escape(title)}</h1>'
    transformed_body = serialize_document_body(body_nodes[0], document_path)
    synthetic = f'<html lang="{html.escape(language, quote=True)}"><body>{metadata_html}{transformed_body}</body></html>'
    # The title belongs inside the adapted document body so the retained copy is self-identifying.
    body_open = re.search(r'<div\b(?=[^>]*\bclass="documentBody")(?=[^>]*\bdata-lovdata-url="' + re.escape(html.escape(document_path, quote=True)) + r'")[^>]*>', synthetic)
    if not body_open:
        raise ValueError("failed to locate adapted documentBody opening tag")
    synthetic = synthetic[:body_open.end()] + title_html + synthetic[body_open.end():]
    adapted_parser = TreeParser()
    adapted_parser.feed(synthetic)
    adapted_parser.close()
    adapted_bodies = [node for node in walk(adapted_parser.root) if "documentBody" in classes(node)]
    if len(adapted_bodies) != 1:
        raise ValueError(f"expected one adapted documentBody, found {len(adapted_bodies)}")
    original_visible = normalize(visible_text(body_nodes[0]))
    adapted_visible = normalize(visible_text(adapted_bodies[0], omit_title=True))
    if original_visible != adapted_visible:
        raise ValueError("adapted official documentBody differs from the captured page's visible legal text")
    rendered = render({
        "content": synthetic,
        "sha256": digest(synthetic),
        "archive_path": record.get("derived_archive_path") or archive_path,
        "source_id": record.get("source_id") or "unassigned",
        "publisher": "Lovdata",
        "retrieved_on": record.get("retrieved_on") or "",
        "licence": record.get("license") or record.get("licence") or "NLOD 2.0",
        "attribution": record.get("attribution") or "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Lovdata",
    })
    markdown = rendered["markdown"]
    markdown = markdown.replace('conversion_rule_id: "NO-LOVDATA-CURRENT-LAW-HTML-001"', f'conversion_rule_id: "{RULE_ID}"', 1)
    markdown = markdown.replace('conversion_rule_version: "0.5.0"', f'conversion_rule_version: "{RULE_VERSION}"', 1)
    markdown = markdown.replace('converter_version: "0.4.0"', f'converter_version: "{CONVERTER_VERSION}"', 1)
    markdown = markdown.replace('license: "NLOD 2.0"\n', 'license: "NLOD 2.0"\nlicense_url: "https://data.norge.no/nlod/en/2.0"\n', 1)
    shared_renderer_output_sha256 = rendered["output_sha256"]
    rendered["output_sha256"] = digest(markdown)
    rendered.update({
        "page_converter_version": CONVERTER_VERSION,
        "conversion_rule_id": RULE_ID,
        "conversion_rule_version": RULE_VERSION,
        "official_page_archive_path": archive_path,
        "official_page_sha256": actual,
        "official_page_bytes": len(page.encode("utf-8")),
        "official_identifier": identifier,
        "official_last_changed_by": changed_by,
        "official_title": title,
        "official_short_title": short_title,
        "official_correction": corrected,
        "official_publication_metadata": published,
        "official_last_change_in_force": last_change_in_force,
        "source_page_visible_body_sha256": digest(original_visible),
        "adapted_document_body_visible_sha256": digest(adapted_visible),
        "source_page_visible_body_equal": original_visible == adapted_visible,
        "derived_input_sha256": digest(synthetic),
        "derived_input_bytes": len(synthetic.encode("utf-8")),
        "shared_renderer_output_sha256": shared_renderer_output_sha256,
        "derived_input_html": synthetic,
        "markdown": markdown,
    })
    return rendered


def main() -> int:
    try:
        result = convert(json.load(sys.stdin))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
