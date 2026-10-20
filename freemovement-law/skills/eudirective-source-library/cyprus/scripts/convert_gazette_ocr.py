#!/usr/bin/env python3
"""Convert the saved Acrobat OCR derivative into a replayable review candidate.

This does not OCR the Gazette or validate legal wording. It deterministically
extracts the saved OCR layer and applies only the page-scoped corrections in the
visual-review ledger. The raw OCR derivative remains unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import pypdf
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - environment-specific message
    raise SystemExit("Install the pinned dependency: pip install -r source-library/cyprus/requirements.txt") from exc

PACK = Path(__file__).resolve().parents[1]
OCR_PDF = PACK / "captures/derived/cy-free-movement-gazette-2007-ocr.pdf"
SOURCE_PDF = PACK / "captures/raw/cy-free-movement-gazette-2007-5956804c60b7979588fb7016109ef76e43d927aeeabcc8444e13d49374f30d50.pdf"
OUTPUT = PACK / "candidates/legislation/cy-free-movement-gazette-2007.md"
REVIEW = PACK / "references/gazette-ocr-review.json"
EXPECTED_PYPDF = "6.21.1"
EXPECTED_SOURCE_SHA256 = "5956804c60b7979588fb7016109ef76e43d927aeeabcc8444e13d49374f30d50"
EXPECTED_OCR_SHA256 = "fb105540b4d679811f9769cd9b4ca443f594fd29ce6d4bba3df6d7a1a3ba397e"
FIRST_PDF_PAGE = 16
LAST_PDF_PAGE = 71
FIRST_GAZETTE_PAGE = 112


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_correction_patches() -> list[dict[str, object]]:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    patches = review["semantic_comparison"]["correction_overlay"]["patches"]
    if not patches:
        raise ValueError("The Gazette correction overlay is empty")
    return patches


def apply_page_corrections(text: str, pdf_page: int, patches: list[dict[str, object]]) -> str:
    for patch in patches:
        if patch["source_pdf_page"] != pdf_page:
            continue
        old = str(patch["ocr_text"])
        new = str(patch["visible_text"])
        expected = int(patch["expected_occurrences"])
        actual = text.count(old)
        if actual != expected:
            raise ValueError(
                f"Correction {patch['id']} expected {expected} occurrence(s) on PDF page "
                f"{pdf_page}; found {actual}"
            )
        text = text.replace(old, new)
    return text


def build_candidate() -> tuple[str, list[int]]:
    if pypdf.__version__ != EXPECTED_PYPDF:
        raise ValueError(f"Expected pypdf {EXPECTED_PYPDF}; found {pypdf.__version__}")
    if sha256(SOURCE_PDF) != EXPECTED_SOURCE_SHA256:
        raise ValueError("The preserved original Gazette PDF hash does not match the reviewed source")
    if sha256(OCR_PDF) != EXPECTED_OCR_SHA256:
        raise ValueError("The saved OCR derivative hash does not match the reviewed OCR output")

    reader = PdfReader(str(OCR_PDF))
    if len(reader.pages) != 71:
        raise ValueError(f"Expected a 71-page OCR derivative; found {len(reader.pages)} pages")

    sections: list[str] = []
    empty_pages: list[int] = []
    patches = load_correction_patches()
    replacement_count = sum(int(patch["expected_occurrences"]) for patch in patches)
    for pdf_page in range(FIRST_PDF_PAGE, LAST_PDF_PAGE + 1):
        text = reader.pages[pdf_page - 1].extract_text() or ""
        if not text.strip():
            empty_pages.append(pdf_page)
            continue
        text = apply_page_corrections(text, pdf_page, patches)
        gazette_page = FIRST_GAZETTE_PAGE + (pdf_page - FIRST_PDF_PAGE)
        if not re.search(rf"(?<!\d){gazette_page}(?!\d)", text):
            raise ValueError(f"Printed Gazette page label {gazette_page} is absent from OCR page {pdf_page}")
        sections.append(
            f"### Gazette page {gazette_page} (original PDF page {pdf_page})\n\n{text.rstrip()}"
        )
    if empty_pages:
        raise ValueError(f"OCR text is empty on original PDF pages: {empty_pages}")

    body = "\n\n".join(sections)
    original_hash = sha256(SOURCE_PDF)
    ocr_hash = sha256(OCR_PDF)
    document = f"""# Original promulgation: Law 7(I)/2007

> **OCR review candidate — not accepted.** This text is extracted from the saved OCR derivative with only the page-specific corrections listed in `references/gazette-ocr-review.json` applied. The original OCR PDF is preserved. Other recognition errors may remain; this is not an authoritative or exhaustively validated transcription.

## Source and extraction record

- Publisher: Government Printing Office of the Republic of Cyprus.
- Official source: [Gazette issue 4110, 9 February 2007]({{source_url}})
- Original PDF: `source-library/cyprus/captures/raw/cy-free-movement-gazette-2007-5956804c60b7979588fb7016109ef76e43d927aeeabcc8444e13d49374f30d50.pdf`
- Original PDF SHA-256: `{original_hash}`.
- OCR derivative: `source-library/cyprus/captures/derived/cy-free-movement-gazette-2007-ocr.pdf`.
- OCR derivative SHA-256: `{ocr_hash}`.
- OCR service: Adobe Acrobat PDF OCR, Greek locale (`el-GR`); output tracking ID `3ff01392-1297-4979-8314-7d9f7e8b6b1c-pdf_service-9c4612ed`.
- Markdown extraction: `pypdf {pypdf.__version__}`; replay with `python source-library/cyprus/scripts/convert_gazette_ocr.py --check`.
- Manual correction overlay: `{len(patches)}` page-scoped exact-text rules, `{replacement_count}` replacements, driven by the visual-review ledger in `references/gazette-ocr-review.json`. Replay aborts if any expected text or occurrence count changes.
- Scope: printed Gazette pages 112–167, original issue PDF pages 16–71 (56 pages). The issue's other pages are excluded.
- Review completed: 2026-10-19. Every page in the 56-page run was visually checked for page presence, order, orientation, visible headings and body/form content. The 26 logged discrepancies were corrected with page-scoped rules. This is not an exhaustive word-level or article-by-article validation.
- Status: original source and OCR derivative preserved; the corrected extraction is useful for review and discovery only. Currentness, amendment reconciliation, residual OCR fidelity, legal classification of each annex and reuse review remain open.

## OCR text with recorded manual corrections

{body}
""".replace("{source_url}", "https://www.mof.gov.cy/mof/gpo/gazette.nsf/All/5ECD762847398688C2258728003A22A7/%24file/A.4110%209.2.2007%20P.%20I%20Meros%20I.pdf?OpenElement=")
    return document, list(range(FIRST_PDF_PAGE, LAST_PDF_PAGE + 1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="write the deterministic candidate Markdown")
    action.add_argument("--check", action="store_true", help="verify the candidate matches replay output")
    args = parser.parse_args()

    candidate, pages = build_candidate()
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(candidate, encoding="utf-8")
        print(f"Wrote {OUTPUT.relative_to(PACK.parent.parent)} from {len(pages)} OCR pages")
    else:
        if not OUTPUT.is_file():
            print(f"Missing candidate: {OUTPUT}", file=sys.stderr)
            return 1
        if OUTPUT.read_text(encoding="utf-8") != candidate:
            print("Candidate does not match deterministic OCR replay", file=sys.stderr)
            return 1
        print(f"Replay matches {len(pages)} pages (PDF {FIRST_PDF_PAGE}–{LAST_PDF_PAGE}; Gazette {FIRST_GAZETTE_PAGE}–{FIRST_GAZETTE_PAGE + len(pages) - 1})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
