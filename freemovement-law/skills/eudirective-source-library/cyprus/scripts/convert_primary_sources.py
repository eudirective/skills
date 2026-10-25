#!/usr/bin/env python3
"""Deterministically convert captured Cyprus-related EU texts and primary PDFs."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

from pypdf import PdfReader


HTML_SOURCES = {
    "cy-protocol-no-10",
    "cy-protocol-no-10-el",
}
PDF_PAGES = {
    "cy-green-line-regulation-866-2004": 14,
    "cy-green-line-regulation-866-2004-el": 14,
    "cy-scc-edd-215-19": 13,
    "cy-cap105-amendment-4i-2025": 64,
    "cy-free-movement-amendment-96i-2023": 7,
    "cy-directive-2004-38-original-el-op": 47,
}

class LegalBodyParser(HTMLParser):
    """Extract only the EUR-Lex legal body in div#TexteOnly."""

    BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3"}
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.started = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if not self.started and tag == "div" and attributes.get("id") == "TexteOnly":
            self.started = True
            self.depth = 1
            return
        if not self.started:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")
        if tag not in self.VOID_TAGS:
            self.depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.started and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if not self.started:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")
        self.depth -= 1
        if self.depth <= 0:
            self.depth = 0
            self.started = False

    def handle_data(self, data: str) -> None:
        if self.started:
            self.parts.append(data)


def normalize(text: str) -> str:
    lines = [re.sub(r"[ \t\f\v]+", " ", line).strip() for line in text.splitlines()]
    out: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if out and not blank:
                out.append("")
            blank = True
            continue
        out.append(line)
        blank = False
    return "\n".join(out).strip()


def convert(source_id: str, source: Path) -> str:
    if source_id in HTML_SOURCES:
        raw_html = source.read_text(encoding="utf-8", errors="replace")
        parser = LegalBodyParser()
        parser.feed(raw_html)
        if not parser.parts:
            raise ValueError("EUR-Lex selector div#TexteOnly was not found")
        body = normalize("".join(parser.parts))
        if "12003T/PRO/10" not in raw_html:
            raise ValueError("Protocol No. 10 EUR-Lex identifier is absent from the captured response")
        if not body:
            raise ValueError("selected EUR-Lex legal text is empty")
        expected = ["Article 1", "Article 2", "Article 3", "Article 4"] if source_id == "cy-protocol-no-10" else ["Αρθρο 1", "Αρθρο 2", "Αρθρο 3", "Αρθρο 4"]
        title_marker = "Protocol No 10" if source_id == "cy-protocol-no-10" else "Πρωτόκολλο αριθ. 10"
        if title_marker not in body:
            raise ValueError(f"selected legal text does not identify Protocol No. 10 in the expected language: {title_marker}")
        missing = [marker for marker in expected if marker not in body]
        if missing:
            raise ValueError(f"selected Protocol No. 10 text is missing expected article headings: {missing}")
        return f"# Protocol No. 10 on Cyprus ({'English' if source_id.endswith('no-10') else 'Greek'})\n\nSource: EUR-Lex ELI 12003T/PRO/10.\nSelector: `div#TexteOnly`.\n\n{body}\n"

    expected_pages = PDF_PAGES.get(source_id)
    if expected_pages is None:
        raise ValueError(f"unsupported source ID: {source_id}")
    reader = PdfReader(str(source))
    if len(reader.pages) != expected_pages:
        raise ValueError(f"expected {expected_pages} pages, got {len(reader.pages)}")
    if source_id == "cy-directive-2004-38-original-el-op":
        pages: list[str] = []
        for number, page in enumerate(reader.pages, 1):
            text = normalize(page.extract_text() or "")
            # pypdf's embedded-font map uses compatibility glyphs for three
            # Greek letters in this Official Journal PDF. Correct only those
            # mappings; do not reflow, rewrite, or otherwise normalize text.
            text = text.translate(str.maketrans({"µ": "μ", "∆": "Δ", "Ω": "Ω"}))
            if len(re.findall(r"[A-Za-zΑ-ώ]{2,}", text)) < 2:
                raise ValueError(f"page {number} has no substantive extractable text")
            pages.append(f"## PDF page {number}\n\n{text}")
        body = "\n\n".join(pages)
        for page_number, article_marker, printed_page in (
            (1, "ΟΔΗΓΙΑ 2004/38/ΕΚ", "77"),
            (15, "Άρθρο 5", "91"),
            (22, "Άρθρο 10", "98"),
            (47, "Άρθρο 42", "123"),
        ):
            page_text = pages[page_number - 1]
            if article_marker not in page_text or not re.search(
                rf"(?m)^{re.escape(printed_page)}$", page_text
            ):
                raise ValueError(
                    f"PDF page {page_number} failed its article/printed-page identity check"
                )
        return (
            "# Captured primary text: Directive 2004/38/EC, Greek original edition\n\n"
            "Source: Publications Office catalogue record a1435737-300a-4760-8462-03db75b27caa; official Greek PDF, OJ L 158, 30 April 2004.\n"
            "Scope: Original 47-page Greek publication. This is not a current consolidated text and does not include a review of later amendments or corrigenda.\n"
            "Conversion: pypdf 6.21.1, all 47 pages retained with page boundaries. Only the embedded-font mappings µ→μ, ∆→Δ, and Ω→Ω are corrected. Page identity checks confirm the title and OJ page 77, Article 5 on OJ page 91, Article 10 on OJ page 98, and Article 42 on OJ page 123. This is deterministic extraction, not visual or word-level acceptance.\n\n"
            f"{body}\n"
        )
    if source_id == "cy-free-movement-amendment-96i-2023":
        before = normalize(reader.pages[1].extract_text() or "")
        act = normalize(reader.pages[2].extract_text() or "")
        after = normalize(reader.pages[3].extract_text() or "")
        boundary_markers = {
            "preceding Act 95(I)/2023": "Ν. 95(Ι)/2023" in before,
            "Law 96(I)/2023 heading": "Ν. 96(Ι)/2023" in act and "Αριθμός 96(Ι) του 2023" in act,
            "printed Gazette page 425": act.endswith("425"),
            "following Act 97(I)/2023": "Ν. 97(Ι)/2023" in after,
            "prior-law list through 193(I)/2020": "193(Ι) του 2020" in act,
        }
        missing = [name for name, present in boundary_markers.items() if not present]
        if missing:
            raise ValueError(f"Law 96(I)/2023 page boundary or identity checks failed: {missing}")
        sections = (
            r"(?m)^1\.\s+Ο παρών Νόμος",
            r"(?m)^2\.\s+Το άρθρο 2 του βασικού νόμου",
            r"(?m)^3\.\s+Το άρθρο 3Α του βασικού νόμου",
        )
        if not all(re.search(pattern, act) for pattern in sections):
            raise ValueError("Law 96(I)/2023 page 3 is missing one of its three sections")
        if "2018/994" in act or "12.-" in act:
            raise ValueError("adjacent Act text was misattributed to Law 96(I)/2023")
        split_authority_word = "διαγραφή σ τον ορισμό"
        if act.count(split_authority_word) != 1:
            raise ValueError(
                "Law 96(I)/2023 section 2 no longer has the reviewed text-layer split; "
                "recheck the page before changing this correction"
            )
        act = act.replace(split_authority_word, "διαγραφή στον ορισμό", 1)
        return (
            "# Captured primary text: Law 96(I)/2023\n\n"
            "Source: Official Gazette issue 4960, 20 October 2023; exact GPO PDF capture.\n"
            "Scope: PDF page 3 only (printed Gazette page 425). The captured seven-page issue places Act 95(I)/2023 on PDF page 2 and Act 97(I)/2023 on PDF page 4; those adjacent Acts are excluded.\n"
            "Conversion: pypdf 6.21.1; page identity, printed-page number, prior-law list and sections 1–3 checked. One scoped text-layer correction rejoins the split in section 2, ‘σ τον’, as ‘στον’, as confirmed against the official PDF extraction. The extracted page contains no section 12 or delayed-commencement clause. This is the amending Act only, not a current consolidation of Law 7(I)/2007.\n\n"
            f"## PDF page 3 — Gazette page 425\n\n{act}\n"
        )
    pages: list[str] = []
    for number, page in enumerate(reader.pages, 1):
        text = normalize(page.extract_text() or "")
        if len(re.findall(r"[A-Za-zΑ-ώ]{2,}", text)) < 2:
            raise ValueError(f"page {number} has no substantive extractable text")
        pages.append(f"## PDF page {number}\n\n{text}")
    body = "\n\n".join(pages)
    markers = {
        "cy-green-line-regulation-866-2004": ("COUNCIL REGULATION (EC) No 866/2004", "31.08.2015"),
        "cy-green-line-regulation-866-2004-el": ("ΚΑΝΟΝΙΣΜΟ", "31.08.2015"),
        "cy-scc-edd-215-19": ("215/19", "DESTANOVIC DENIS"),
        "cy-cap105-amendment-4i-2025": ("4(I)/2025", "Ο παρών Νόμος τίθεται σε ισχύ", "γνωστοποίησή του που δημοσιεύεται"),
        "cy-directive-2004-38-original-el-op": ("ΟΔΗΓΙΑ 2004/38/ΕΚ", "Άρθρο 5", "Άρθρο 10", "Άρθρο 42"),
    }[source_id]
    missing = [marker for marker in markers if marker not in body]
    if missing:
        raise ValueError(f"source identity/version markers missing from extracted PDF: {missing}")
    return f"# Captured primary text: {source_id}\n\nConversion: pypdf 6.21.1, every page retained with a page boundary.\n\n{body}\n"


def verify_saved_conversions() -> int:
    """Report that pack-wide replay needs files from the Monitor archive."""
    print(
        "Replay check unsupported from the checkout: source and candidate artifacts "
        "are retained in the EU Source Update Monitor local-only archive. Retrieve "
        "the exact files with local_research_read, then replay one source with "
        "--source-id, --input and --output in the temporary workspace.",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="replay and verify tracked source-specific candidates")
    parser.add_argument("--source-id")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.check:
        if any((args.source_id, args.input, args.output)):
            parser.error("--check cannot be combined with --source-id, --input or --output")
        return verify_saved_conversions()
    if not (args.source_id and args.input and args.output):
        parser.error("conversion requires --source-id, --input and --output")
    try:
        result = convert(args.source_id, args.input)
    except (OSError, ValueError) as exc:
        print(f"conversion failed: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"converted {args.source_id}: {len(result.encode('utf-8'))} bytes -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
