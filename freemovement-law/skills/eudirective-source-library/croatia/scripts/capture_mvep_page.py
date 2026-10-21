#!/usr/bin/env python3
"""Fetch one public MVEP page and extract its main article without the page shell.

No source text or raw HTML is written to disk. The optional text output is meant
for a reviewer to compare with the live official page; the JSON ledger contains
only URL, hash, selector, size, and HTTP date metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen


HOST = "mvep.gov.hr"
SELECTOR = "div#content .page_content"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BREAKS = {"address", "article", "blockquote", "br", "dd", "div", "dl", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "section", "ul"}


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, dict[str, str]]] = []
        self.article_depth: int | None = None
        self.article_matches = 0
        self.title_depth: int | None = None
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        in_content = any(name == "div" and node.get("id") == "content" for name, node in self.stack)
        if tag == "h1" and in_content and self.title_depth is None:
            self.title_depth = len(self.stack) + 1
        if tag == "div" and in_content and "page_content" in values.get("class", "").split():
            self.article_matches += 1
            if self.article_depth is None:
                self.article_depth = len(self.stack) + 1
        if self.article_depth is not None and len(self.stack) + 1 >= self.article_depth and tag in BREAKS:
            self.text_parts.append("\n")
        self.stack.append((tag, values))
        if tag in VOID:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        depth = len(self.stack)
        if self.title_depth == depth and tag == "h1":
            self.title_depth = None
        if self.article_depth is not None and depth == self.article_depth and tag == "div":
            self.article_depth = None
        for index in range(depth - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break
        if self.article_depth is not None and tag in BREAKS:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.title_depth is not None and data.strip():
            self.title_parts.append(data.strip())
        if self.article_depth is not None and data.strip():
            self.text_parts.append(data.strip())

    def result(self) -> tuple[str, str]:
        title = re.sub(r"\s+", " ", " ".join(self.title_parts)).strip()
        lines = [re.sub(r"\s+", " ", part).strip() for part in self.text_parts]
        text = "\n".join(line for line in lines if line)
        return title, text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public English or Croatian page on mvep.gov.hr")
    parser.add_argument("--expected-title", required=True, help="Expected article heading; fails if the target page changed")
    parser.add_argument("--emit-text", action="store_true", help="Print extracted article text after the JSON ledger")
    args = parser.parse_args()

    requested = urlparse(args.url)
    if requested.scheme != "https" or requested.hostname != HOST:
        parser.error(f"URL must use https://{HOST}/")

    request = Request(args.url, headers={"User-Agent": "eudirective-source-review/1.0"})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
        resolved_url = response.geturl()
        status = response.status
        content_type = response.headers.get("Content-Type", "")
        last_modified = response.headers.get("Last-Modified")
        etag = response.headers.get("ETag")

    resolved = urlparse(resolved_url)
    if resolved.scheme != "https" or resolved.hostname != HOST:
        raise SystemExit(f"Refusing cross-domain redirect: {resolved_url}")
    if status != 200 or "html" not in content_type.lower():
        raise SystemExit(f"Unexpected response: status={status}, content_type={content_type}")

    extractor = ArticleParser()
    extractor.feed(raw.decode("utf-8", "replace"))
    title, article = extractor.result()
    if extractor.article_matches != 1:
        raise SystemExit(f"Expected one {SELECTOR} element; found {extractor.article_matches}")
    if title != args.expected_title:
        raise SystemExit(f"Page title changed: expected {args.expected_title!r}, received {title!r}")
    if not article:
        raise SystemExit("The source-specific article selector returned no text")

    result = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_url": args.url,
        "resolved_url": resolved_url,
        "http_status": status,
        "content_type": content_type,
        "last_modified": last_modified,
        "etag": etag,
        "page_title": title,
        "selector": SELECTOR,
        "selector_matches": extractor.article_matches,
        "raw_response_bytes": len(raw),
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
        "article_characters": len(article),
        "article_sha256": hashlib.sha256(article.encode("utf-8")).hexdigest(),
        "retention": "No HTML or extracted source text is persisted by this script.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.emit_text:
        print("\n--- extracted article for review; not saved ---\n")
        print(article)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        raise SystemExit(130)
