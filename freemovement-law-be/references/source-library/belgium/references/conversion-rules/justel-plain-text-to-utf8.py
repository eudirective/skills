#!/usr/bin/env python3
"""Extract the visible body from a Justel legal-text HTML page."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re


class PlainTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and attrs.get("id") == "list-title-3":
            self.active = True
            self.depth = 1
            return
        if not self.active:
            return
        if tag == "div":
            self.depth += 1
        elif tag in ("br", "p"):
            self.parts.append("\n")
        elif tag == "sup":
            self.parts.append("[")

    def handle_endtag(self, tag):
        if not self.active:
            return
        if tag == "sup":
            self.parts.append("]")
        elif tag == "div":
            self.depth -= 1
            if self.depth == 0:
                self.active = False

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)


def convert(data: bytes, encoding: str) -> str:
    parser = PlainTextExtractor()
    parser.feed(data.decode(encoding))
    if parser.active or not parser.parts:
        raise ValueError("Could not isolate Justel div#list-title-3.box.plain-text")
    text = "".join(parser.parts).replace("\xa0", " ")
    lines = []
    for original in text.splitlines():
        line = re.sub(r"\s+", " ", original).strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        lines.append(line)
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    if lines and lines[0].casefold() == "texte":
        lines.pop(0)
        while lines and lines[0] == "":
            lines.pop(0)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_html", type=Path)
    parser.add_argument("output_text", type=Path)
    parser.add_argument("--encoding", default="iso-8859-1")
    args = parser.parse_args()
    output = convert(args.input_html.read_bytes(), args.encoding)
    args.output_text.write_text(output, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
