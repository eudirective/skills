#!/usr/bin/env python3
"""Convert one hash-verified Lovdata current-law HTML member to Markdown.

The input is a JSON object on stdin containing archive metadata and the exact
UTF-8 member text. The output is a JSON object with Markdown, source/output
hashes, publisher metadata, and fail-closed conversion validation. This tool
creates a derived review copy only; it does not accept or publish a source.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import unicodedata
from collections import Counter
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin


CONVERTER_VERSION = "0.4.0"
RULE_ID = "NO-LOVDATA-CURRENT-LAW-HTML-001"
RULE_VERSION = "0.5.0"
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
BLOCK_TAGS = {
    "address", "article", "blockquote", "dd", "div", "dl", "dt", "footer",
    "h1", "h2", "h3", "h4", "h5", "h6", "header", "li", "ol", "p",
    "section", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
}
INLINE_SEMANTIC_TAGS = {
    "b", "cite", "code", "del", "em", "i", "ins", "mark", "q", "s", "small",
    "span", "strong", "sub", "sup", "u",
}
METADATA_CLASSES = {
    "dokid", "refid", "dateInForce", "lastChangeInForce", "lastChangedBy",
    "dateOfPublication", "lastupdated", "titleShort", "title", "eli",
}


class Node:
    def __init__(self, tag: str, attrs: dict[str, str | None] | None = None):
        self.tag = tag.lower()
        self.attrs = attrs or {}
        self.children: list[Node | str] = []

    @property
    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())


class TreeParser(HTMLParser):
    """Small tolerant HTML tree builder for Lovdata's captured documents."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag.lower() not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].children.append(Node(tag, dict(attrs)))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)


def walk(node: Node):
    for child in node.children:
        if isinstance(child, Node):
            yield child
            yield from walk(child)


def find_nodes(node: Node, predicate):
    return [candidate for candidate in walk(node) if predicate(candidate)]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFC", value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def node_text(
    node: Node | str,
    *,
    omit_article_header: bool = False,
    omit_footnotes: bool = False,
    omit_change_history: bool = False,
    omit_nested_legal_articles: bool = False,
    root: bool = True,
) -> str:
    if isinstance(node, str):
        return node
    if omit_article_header and "legalArticleHeader" in node.classes:
        return ""
    if omit_footnotes and (node.tag == "footer" or node.classes & {"footnotes", "footnote", "footnotereference"}):
        return ""
    if omit_change_history and "changesToParent" in node.classes:
        return ""
    if omit_nested_legal_articles and not root and node.tag == "article" and "legalArticle" in node.classes:
        return ""

    pieces: list[str] = []
    if node.tag in BLOCK_TAGS or node.tag == "br":
        pieces.append(" ")
    for child in node.children:
        pieces.append(
            node_text(
                child,
                omit_article_header=omit_article_header,
                omit_footnotes=omit_footnotes,
                omit_change_history=omit_change_history,
                omit_nested_legal_articles=omit_nested_legal_articles,
                root=False,
            )
        )
    if node.tag in BLOCK_TAGS or node.tag == "br":
        pieces.append(" ")
    return "".join(pieces)


def attributes_html(attrs: dict[str, str | None], *, omit: set[str] | None = None) -> str:
    omitted = omit or set()
    safe: list[str] = []
    for key in sorted(attrs):
        value = attrs[key]
        if key in omitted or value is None or key.lower().startswith("on"):
            continue
        if not (
            key in {"id", "class", "href", "title", "type", "start", "value", "scope", "colspan", "rowspan", "lang", "dir", "target", "rel", "alt", "width", "height"}
            or key.startswith("data-")
            or key.startswith("aria-")
        ):
            continue
        safe.append(f'{key}="{html.escape(value, quote=True)}"')
    return (" " + " ".join(safe)) if safe else ""


def resolved_href(href: str, source_base: str) -> str:
    if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return href
    return urljoin(source_base, href)


def source_anchor(node: Node, output_id: str | None = None) -> str:
    source_id = node.attrs.get("id")
    anchor_id = output_id or source_id
    if not anchor_id:
        return ""
    attrs = {"id": anchor_id}
    if node.attrs.get("data-name"):
        attrs["data-name"] = node.attrs["data-name"]
    if node.attrs.get("data-lovdata-url"):
        attrs["data-lovdata-url"] = node.attrs["data-lovdata-url"]
    if node.attrs.get("class"):
        attrs["data-source-class"] = node.attrs["class"]
    return f"<a{attributes_html(attrs)}></a>"


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-").lower()
    return value or "source"


def find_document_body(root: Node) -> Node:
    bodies = find_nodes(root, lambda node: "documentBody" in node.classes)
    if len(bodies) != 1:
        raise ValueError(f"expected one documentBody, found {len(bodies)}")
    return bodies[0]


def extract_metadata(root: Node, document_body: Node) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for parent in walk(root):
        children = [child for child in parent.children if isinstance(child, Node)]
        for index, child in enumerate(children[:-1]):
            if child.tag != "dt" or not (child.classes & METADATA_CLASSES):
                continue
            next_node = children[index + 1]
            if next_node.tag != "dd":
                continue
            key = next(iter(child.classes & METADATA_CLASSES))
            metadata[key] = normalize(node_text(next_node))
    title_nodes = find_nodes(document_body, lambda node: node.tag == "h1")
    if title_nodes:
        metadata["document_title"] = normalize(node_text(title_nodes[0]))
    metadata["document_url_path"] = document_body.attrs.get("data-lovdata-url", "") or ""
    html_nodes = find_nodes(root, lambda node: node.tag == "html")
    if html_nodes and html_nodes[0].attrs.get("lang"):
        metadata["language"] = str(html_nodes[0].attrs["lang"])
    return metadata


def render(input_record: dict[str, Any]) -> dict[str, Any]:
    content = input_record.get("content")
    expected_hash = input_record.get("sha256") or input_record.get("input_sha256")
    archive_path = input_record.get("archive_path") or input_record.get("input_archive_path")
    if not isinstance(content, str) or not isinstance(expected_hash, str) or not archive_path:
        raise ValueError("input requires content, archive_path, and sha256")
    actual_hash = sha256_text(content)
    if actual_hash != expected_hash:
        raise ValueError(f"input byte hash mismatch: expected {expected_hash}, got {actual_hash}")

    parser = TreeParser()
    parser.feed(content)
    parser.close()
    body = find_document_body(parser.root)
    metadata = extract_metadata(parser.root, body)
    root_attrs = parser.root.children[0].attrs if parser.root.children and isinstance(parser.root.children[0], Node) else {}
    language = str(root_attrs.get("lang") or metadata.get("language") or "no")
    source_id = str(input_record.get("source_id") or "unassigned")
    publisher = str(input_record.get("publisher") or "Lovdata")
    retrieved_on = str(input_record.get("retrieved_on") or "")
    licence = str(input_record.get("licence") or input_record.get("license") or "NLOD 2.0")
    attribution = str(input_record.get("attribution") or "Lovdata")
    document_path = metadata.get("document_url_path", "")
    source_url = f"https://lovdata.no/dokument/{document_path}" if document_path else ""
    # Lovdata member links are rooted at /dokument/NL/, not relative to the
    # current law's own URL. Retain both this resolved target and the raw href.
    source_base = "https://lovdata.no/dokument/NL/"

    stats: dict[str, Any] = {
        "emitted_ids": [],
        "internal_links": [],
        "footnote_references": [],
        "footnote_notes": [],
        "change_history_nodes": [],
        "article_body_checks": [],
        "table_nodes": 0,
        "warnings": [],
    }

    recorded_node_ids: set[int] = set()

    def record_id(node: Node) -> None:
        identity = id(node)
        if node.attrs.get("id") and identity not in recorded_node_ids:
            stats["emitted_ids"].append(str(node.attrs["id"]))
            recorded_node_ids.add(identity)

    def output_anchor(node: Node, generated_id: str | None = None) -> str:
        record_id(node)
        if not node.attrs.get("id") and not generated_id:
            return ""
        return source_anchor(node, generated_id)

    def render_children(children: list[Node | str], context: dict[str, Any]) -> tuple[str, str]:
        rendered: list[str] = []
        visible: list[str] = []
        for child in children:
            if isinstance(child, Node) and child.tag in BLOCK_TAGS:
                rendered.append("\n\n")
                visible.append(" ")
            child_md, child_visible = render_node(child, context)
            rendered.append(child_md)
            visible.append(child_visible)
            if isinstance(child, Node) and child.tag in BLOCK_TAGS:
                rendered.append("\n\n")
                visible.append(" ")
        return "".join(rendered), "".join(visible)

    def inline_children(children: list[Node | str], context: dict[str, Any]) -> tuple[str, str]:
        rendered: list[str] = []
        visible: list[str] = []
        for child in children:
            if isinstance(child, Node) and child.tag in BLOCK_TAGS and child.tag not in {"p"}:
                child_md, child_visible = render_node(child, context)
                rendered.extend(["\n", child_md, "\n"])
                visible.extend([" ", child_visible, " "])
            else:
                child_md, child_visible = render_node(child, context)
                rendered.append(child_md)
                visible.append(child_visible)
        return "".join(rendered), "".join(visible)

    def generic_attributes(node: Node, extra: dict[str, str] | None = None) -> str:
        attrs = dict(node.attrs)
        if extra:
            attrs.update(extra)
        if attrs.get("id"):
            record_id(node)
        return attributes_html(attrs)

    def _render_node_impl(value: Node | str, context: dict[str, Any]) -> tuple[str, str]:
        if isinstance(value, str):
            return html.escape(value, quote=False), value

        classes = value.classes
        tag = value.tag
        if tag == "article" and "legalArticle" in classes:
            article_id = str(value.attrs.get("id") or value.attrs.get("data-name") or "article")
            article_context = dict(context)
            article_context["article_id"] = article_id
            article_context["article_slug"] = slug(article_id)
            article_context["reference_counts"] = Counter()
            article_context["_article_body_capture"] = []
            article_context["_article_body_ignored"] = False
            article_context["note_labels"] = {
                str(note.attrs.get("data-name") or "")
                for note in find_nodes(value, lambda node: "footnote" in node.classes)
            }
            child_md, child_visible = render_children(value.children, article_context)
            source_body = normalize(
                node_text(
                    value,
                    omit_article_header=True,
                    omit_footnotes=True,
                    omit_change_history=True,
                    omit_nested_legal_articles=True,
                )
            )
            converted_body = normalize("".join(article_context["_article_body_capture"]))
            stats["article_body_checks"].append({
                "data_name": value.attrs.get("data-name"),
                "element_id": value.attrs.get("id"),
                "source_body_characters": len(source_body),
                "source_body_sha256": sha256_text(source_body),
                "converted_body_characters": len(converted_body),
                "converted_body_sha256": sha256_text(converted_body),
                "body_equal": source_body == converted_body,
            })
            attrs = generic_attributes(value)
            return f"<article{attrs}>\n{child_md}\n</article>", child_visible

        if tag == "section" and "section" in classes:
            child_md, child_visible = render_children(value.children, context)
            attrs = generic_attributes(value)
            return f"<section{attrs}>\n{child_md}\n</section>", child_visible

        if "footnotereference" in classes:
            label = str(value.attrs.get("data-footnotereferencevalue") or normalize(node_text(value)))
            article_id = str(context.get("article_id") or context.get("scope_id") or "document")
            article_slug = slug(article_id)
            counts = context.setdefault("reference_counts", Counter())
            counts[label] += 1
            ref_id = f"ref-{article_slug}-{slug(label)}-{counts[label]}"
            note_id = f"fn-{article_slug}-{slug(label)}"
            source_label = normalize(node_text(value)) or label
            stats["footnote_references"].append({"article_id": article_id, "label": label})
            if label in context.get("note_labels", set()):
                return (
                    f'<sup id="{html.escape(ref_id, quote=True)}" data-footnote-referencevalue="{html.escape(label, quote=True)}"><a href="#{html.escape(note_id, quote=True)}">{html.escape(source_label)}</a></sup>',
                    source_label,
                )
            return (
                f'<sup id="{html.escape(ref_id, quote=True)}" data-footnote-referencevalue="{html.escape(label, quote=True)}">{html.escape(source_label)}</sup>',
                source_label,
            )

        if tag == "article" and "footnote" in classes:
            label = str(value.attrs.get("data-name") or "")
            article_id = str(context.get("article_id") or context.get("scope_id") or "document")
            article_slug = slug(article_id)
            note_id = f"fn-{article_slug}-{slug(label)}"
            stats["footnote_notes"].append({"article_id": article_id, "label": label})
            content_md, content_visible = render_children(value.children, context)
            source_id = value.attrs.get("id")
            if source_id:
                record_id(value)
            extra = f' id="{html.escape(note_id, quote=True)}" data-footnote-label="{html.escape(label, quote=True)}"'
            if source_id:
                extra += f' data-source-id="{html.escape(str(source_id), quote=True)}"'
            return f"<div class=\"lovdata-footnote\"{extra}>{content_md}</div>", content_visible

        if tag == "footer" and "footnotes" in classes:
            child_md, child_visible = render_children(value.children, context)
            attrs = generic_attributes(value, {"class": "lovdata-footnotes"})
            return f"<div{attrs}>\n{child_md}\n</div>", child_visible

        if tag == "article" and "changesToParent" in classes:
            child_md, child_visible = inline_children(value.children, context)
            stats["change_history_nodes"].append({"article_id": context.get("article_id"), "characters": len(normalize(child_visible)), "sha256": sha256_text(normalize(child_visible))})
            attrs = generic_attributes(value, {"class": "publisher-change-history", "data-source-class": "changesToParent"})
            return f"<aside{attrs}>{child_md}</aside>", child_visible

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            child_md, child_visible = inline_children(value.children, context)
            attrs = generic_attributes(value)
            return f"<{tag}{attrs}>{child_md}</{tag}>", child_visible

        if tag == "a":
            child_md, child_visible = inline_children(value.children, context)
            raw_href = value.attrs.get("href")
            if raw_href:
                absolute = resolved_href(raw_href, source_base)
                stats["internal_links"].append({"source_href": raw_href, "resolved_href": absolute})
                attrs = {"href": absolute, "data-source-href": raw_href}
                if value.attrs.get("id"):
                    attrs["id"] = value.attrs["id"]
                    record_id(value)
                if value.attrs.get("title"):
                    attrs["title"] = value.attrs["title"]
                return f"<a{attributes_html(attrs)}>{child_md}</a>", child_visible
            attrs = generic_attributes(value)
            return f"<a{attrs}>{child_md}</a>", child_visible

        if tag == "br":
            return "<br />", " "

        if tag in {"ol", "ul", "li", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "blockquote", "p", "div", "dl", "dt", "dd", "header", "address"}:
            child_md, child_visible = render_children(value.children, context)
            attrs = generic_attributes(value)
            if tag == "table":
                stats["table_nodes"] += 1
            if tag in {"ol", "ul", "li", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "blockquote", "p", "div", "dl", "dt", "dd", "header", "address"}:
                return f"<{tag}{attrs}>{child_md}</{tag}>", child_visible

        if tag == "article":
            child_md, child_visible = render_children(value.children, context)
            attrs = generic_attributes(value)
            return f"<article{attrs}>{child_md}</article>", child_visible

        if tag in INLINE_SEMANTIC_TAGS:
            child_md, child_visible = inline_children(value.children, context)
            attrs = generic_attributes(value)
            return f"<{tag}{attrs}>{child_md}</{tag}>", child_visible

        child_md, child_visible = inline_children(value.children, context)
        attrs = generic_attributes(value)
        if tag in VOID_TAGS:
            return f"<{tag}{attrs} />", child_visible
        if tag not in {"html", "head", "body", "document", "documentheader", "nav"}:
            warning = f"preserved unclassified tag <{tag}> classes={','.join(sorted(classes))}"
            if warning not in stats["warnings"]:
                stats["warnings"].append(warning)
            return f"<{tag}{attrs}>{child_md}</{tag}>", child_visible
        return child_md, child_visible

    def render_node(value: Node | str, context: dict[str, Any]) -> tuple[str, str]:
        if isinstance(value, Node):
            record_id(value)
        capture = context.get("_article_body_capture")
        previously_ignored = bool(context.get("_article_body_ignored", False))
        changed_ignored = False
        add_block_spacing = False
        if capture is not None and not previously_ignored:
            if isinstance(value, str):
                capture.append(value)
            elif (
                "legalArticleHeader" in value.classes
                or "changesToParent" in value.classes
                or "footnotes" in value.classes
                or "footnote" in value.classes
                or "footnotereference" in value.classes
                or (value.tag == "article" and "legalArticle" in value.classes)
            ):
                context["_article_body_ignored"] = True
                changed_ignored = True
            elif value.tag in BLOCK_TAGS or value.tag == "br":
                capture.append(" ")
                add_block_spacing = True
        try:
            return _render_node_impl(value, context)
        finally:
            if add_block_spacing:
                capture.append(" ")
            if changed_ignored:
                context["_article_body_ignored"] = previously_ignored

    initial_context: dict[str, Any] = {"scope_id": "document", "reference_counts": Counter()}
    markdown_parts: list[str] = []
    rendered_visible_parts: list[str] = []
    for child in body.children:
        if isinstance(child, Node) and child.tag in BLOCK_TAGS:
            markdown_parts.append("\n\n")
            rendered_visible_parts.append(" ")
        part_md, part_visible = render_node(child, initial_context)
        markdown_parts.append(part_md)
        rendered_visible_parts.append(part_visible)
        if isinstance(child, Node) and child.tag in BLOCK_TAGS:
            markdown_parts.append("\n\n")
            rendered_visible_parts.append(" ")
    body_markdown = "".join(markdown_parts).strip()
    source_visible = normalize(node_text(body))
    converted_visible = normalize("".join(rendered_visible_parts))

    all_nodes = list(walk(body))
    source_ids = [str(node.attrs["id"]) for node in all_nodes if node.attrs.get("id")]
    emitted_ids = [str(value) for value in stats["emitted_ids"]]
    legal_articles = [node for node in all_nodes if node.tag == "article" and "legalArticle" in node.classes]
    article_rows: list[dict[str, Any]] = []
    for article, body_check in zip(legal_articles, stats["article_body_checks"]):
        source_body = normalize(
            node_text(
                article,
                omit_article_header=True,
                omit_footnotes=True,
                omit_change_history=True,
                omit_nested_legal_articles=True,
            )
        )
        article_rows.append(
            {
                "data_name": article.attrs.get("data-name"),
                "element_id": article.attrs.get("id"),
                "heading": next(
                    (normalize(node_text(child)) for child in article.children if isinstance(child, Node) and "legalArticleHeader" in child.classes),
                    "",
                ),
                "source_body_characters": len(source_body),
                "source_body_sha256": sha256_text(source_body),
                "converted_body_characters": body_check["converted_body_characters"],
                "converted_body_sha256": body_check["converted_body_sha256"],
                "body_equal": body_check["body_equal"],
                "body_nonempty": bool(source_body),
            }
        )

    duplicate_source_ids = [key for key, count in Counter(source_ids).items() if count > 1]
    duplicate_emitted_ids = [key for key, count in Counter(emitted_ids).items() if count > 1]
    missing_ids = sorted(set(source_ids) - set(emitted_ids))
    unexpected_ids = sorted(set(emitted_ids) - set(source_ids))
    reference_pairs = Counter((str(row.get("article_id")), str(row["label"])) for row in stats["footnote_references"])
    note_pairs = Counter((str(row.get("article_id")), str(row["label"])) for row in stats["footnote_notes"])
    unmatched_refs = [
        {"article_id": article_id, "label": label, "count": count, "note_count": note_pairs[(article_id, label)]}
        for (article_id, label), count in reference_pairs.items()
        if note_pairs[(article_id, label)] == 0
    ]
    if unmatched_refs:
        stats["warnings"].append(
            f"{sum(row['count'] for row in unmatched_refs)} footnote reference(s) have no note in the same legal article; see unmatched_footnote_references"
        )
    article_body_empty = [
        row["data_name"]
        for row in article_rows
        if row["body_nonempty"] and row["converted_body_characters"] == 0
    ]
    article_body_mismatches = [row["data_name"] for row in article_rows if not row["body_equal"]]
    source_url = source_url or ""
    markdown_metadata = {
        "source_id": source_id,
        "official_identifier": metadata.get("refid", ""),
        "publisher": publisher,
        "title": metadata.get("document_title", ""),
        "short_title": metadata.get("titleShort", ""),
        "publisher_version_last_changed_by": metadata.get("lastChangedBy", ""),
        "publisher_last_change_in_force": metadata.get("lastChangeInForce", ""),
        "publisher_last_correction": metadata.get("lastupdated", ""),
        "language": language,
        "retrieved_on": retrieved_on,
        "official_source_url": source_url,
        "input_archive_path": archive_path,
        "input_sha256": actual_hash,
        "license": licence,
        "attribution": attribution,
        "conversion_rule_id": RULE_ID,
        "conversion_rule_version": RULE_VERSION,
        "converter_version": CONVERTER_VERSION,
        "acceptance_status": "unaccepted_local_review_copy",
    }
    frontmatter = "---\n" + "".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}\n" for key, value in markdown_metadata.items()
    ) + "---\n\n"
    markdown = frontmatter + body_markdown + "\n"
    output_hash = sha256_text(markdown)

    errors: list[str] = []
    if not legal_articles:
        errors.append("document body contains no legalArticle nodes")
    ids_ordered_preserved = source_ids == emitted_ids
    if missing_ids or unexpected_ids or Counter(source_ids) != Counter(emitted_ids) or not ids_ordered_preserved:
        errors.append("source element IDs do not survive conversion exactly once in publisher order")
    if duplicate_source_ids:
        errors.append("source document contains duplicate element IDs")
    if duplicate_emitted_ids:
        errors.append("converted document contains duplicate element IDs")
    if source_visible != converted_visible:
        errors.append("normalized documentBody visible text differs after conversion")
    if article_body_empty:
        errors.append("one or more non-empty legal articles produced an empty converted body")
    if article_body_mismatches:
        errors.append("one or more converted legal-article bodies differ from their official source bodies")

    return {
        "schema_version": "1.0.0",
        "converter_version": CONVERTER_VERSION,
        "conversion_rule_id": RULE_ID,
        "conversion_rule_version": RULE_VERSION,
        "source_id": source_id,
        "input_archive_path": archive_path,
        "input_sha256": actual_hash,
        "output_sha256": output_hash,
        "publisher_metadata": metadata,
        "article_count": len(legal_articles),
        "article_rows": article_rows,
        "article_body_empty": article_body_empty,
        "article_body_mismatches": article_body_mismatches,
        "source_element_id_count": len(source_ids),
        "emitted_element_id_count": len(emitted_ids),
        "source_ids_ordered_preserved": ids_ordered_preserved,
        "footnote_reference_count": len(stats["footnote_references"]),
        "footnote_note_count": len(stats["footnote_notes"]),
        "unmatched_footnote_references": unmatched_refs,
        "change_history_node_count": len(stats["change_history_nodes"]),
        "change_history_rows": stats["change_history_nodes"],
        "internal_link_count": len(stats["internal_links"]),
        "internal_links": stats["internal_links"],
        "table_node_count": stats["table_nodes"],
        "normalized_source_body_sha256": sha256_text(source_visible),
        "normalized_converted_body_sha256": sha256_text(converted_visible),
        "visible_document_body_equal": source_visible == converted_visible,
        "missing_source_ids": missing_ids,
        "unexpected_output_ids": unexpected_ids,
        "duplicate_source_ids": duplicate_source_ids,
        "duplicate_output_ids": duplicate_emitted_ids,
        "warnings": stats["warnings"],
        "errors": errors,
        "valid": not errors,
        "markdown": markdown,
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = render(payload)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
