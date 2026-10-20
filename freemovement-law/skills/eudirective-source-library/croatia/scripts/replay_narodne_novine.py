#!/usr/bin/env python3
"""Replay Croatian official legal text from the Narodne novine document DOM.

The page shell is deliberately excluded. The script stores only the official
document fragment (``.sl-content .doc``) and renders its text into the existing
candidate markdown. A raw full-page response may be used from local ignored
``temp/`` for the first replay; subsequent deterministic replays use the
repository fragment capture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "source-library/croatia"
CAPTURE_DIR = PACK / "captures/official-texts"
FRAGMENT_SELECTOR = ".sl-content .doc"
LEGAL_TYPES = {
    "access_to_information_act", "administrative_remedies_act", "amending_act",
    "amending_regulation", "general_procedure_act", "implementing_regulation",
    "annual_budget_execution_act", "legal_aid_act", "national_act", "oversight_act", "visa_regulation",
}
BLOCKS = {
    "address", "article", "blockquote", "dd", "div", "dl", "dt", "footer",
    "h1", "h2", "h3", "h4", "h5", "h6", "header", "li", "ol", "p",
    "section", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP = {"script", "style", "noscript"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class OfficialFragmentLocator(HTMLParser):
    """Find exactly one .sl-content .doc subtree and return its original bytes."""

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=False)
        self.html = html
        self.line_offsets = [0]
        for match in re.finditer("\n", html):
            self.line_offsets.append(match.end())
        self.open_stack: list[tuple[str, set[str]]] = []
        self.active_start: int | None = None
        self.active_depth = 0
        self.fragments: list[str] = []

    def source_offset(self) -> int:
        line, column = self.getpos()
        return self.line_offsets[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self.source_offset()
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if self.active_start is not None:
            # Track only div nesting inside the selected div.doc subtree.
            # Narodne novine HTML includes legacy markup with omitted closing
            # tags for paragraphs and other inline elements; counting every
            # tag makes an otherwise balanced document fragment look open.
            if tag == "div":
                self.active_depth += 1
        elif tag == "div" and "doc" in classes and any(
            parent_tag == "div" and "sl-content" in parent_classes
            for parent_tag, parent_classes in self.open_stack
        ):
            self.active_start = start
            self.active_depth = 1
        self.open_stack.append((tag, classes))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Self-closing nodes never affect the depth of the containing document.
        return

    def handle_endtag(self, tag: str) -> None:
        start = self.source_offset()
        if self.active_start is not None and tag == "div":
            self.active_depth -= 1
            if self.active_depth == 0:
                end = self.html.find(">", start)
                if end < 0:
                    raise ValueError("unterminated closing tag in document fragment")
                self.fragments.append(self.html[self.active_start:end + 1])
                self.active_start = None
        # Recover the ancestry stack from the last matching tag. Narodne novine
        # documents are well-formed, but this keeps sibling parsing robust.
        for i in range(len(self.open_stack) - 1, -1, -1):
            if self.open_stack[i][0] == tag:
                del self.open_stack[i:]
                break


class TextRenderer(HTMLParser):
    """Render a selected legal-text fragment while preserving block boundaries."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in BLOCKS or tag == "br":
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append("\t")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.skip_depth and (tag in BLOCKS or tag == "br"):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP and self.skip_depth:
            self.skip_depth -= 1
            return
        if not self.skip_depth and (tag in BLOCKS or tag == "br"):
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        source = "".join(self.parts).replace("\xa0", " ").replace("\u00ad", "")
        lines: list[str] = []
        for line in source.splitlines():
            line = re.sub(r"[\t\r\f\v ]+", " ", line).strip()
            if line:
                lines.append(line)
            elif lines and lines[-1] != "":
                lines.append("")
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)


def render_fragment(fragment: str) -> str:
    renderer = TextRenderer()
    renderer.feed(fragment)
    renderer.close()
    text = renderer.text()
    if not text:
        raise ValueError("selected official document fragment rendered empty")
    return text


def extract_fragment(html: str) -> str:
    parser = OfficialFragmentLocator(html)
    parser.feed(html)
    parser.close()
    if len(parser.fragments) != 1:
        raise ValueError(f"expected exactly one {FRAGMENT_SELECTOR} fragment; found {len(parser.fragments)}")
    return parser.fragments[0]


def main() -> int:
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--dry-run", action="store_true", help="report replay results without writing files")
    args = argp.parse_args()

    manifest = read_json(PACK / "references/candidate-manifest.json")
    capture_results = read_json(PACK / "references/croatia-capture-results.json")
    ledger = read_json(PACK / "references/capture-ledger.json")
    acceptance = read_json(PACK / "references/source-acceptance.json")
    rules = read_json(PACK / "references/source-rules.json")
    docs = {row["id"]: row for row in manifest["documents"]}
    captures = {row["candidate_id"]: row for row in capture_results["records"]}
    ledger_records = {row["source_id"]: row for row in ledger["records"]}
    nn_records: list[tuple[str, dict, dict, str, str, str]] = []
    official_text_ids: list[str] = []
    errors: list[str] = []

    for source_id, doc in docs.items():
        if doc.get("source_type") not in LEGAL_TYPES or urlparse(doc.get("url", "")).hostname != "narodne-novine.nn.hr":
            continue
        if "/clanci/sluzbeni/" in urlparse(doc.get("url", "")).path:
            official_text_ids.append(source_id)
        candidate_path = doc.get("candidate_text_path")
        if not candidate_path:
            continue
        capture = captures.get(source_id)
        if not capture:
            errors.append(f"{source_id}: candidate has no capture ledger entry")
            continue
        local_raw = ROOT / capture.get("raw_path", "")
        fragment_path = CAPTURE_DIR / f"{source_id}.html"
        if local_raw.is_file():
            raw_html = local_raw.read_text(encoding="utf-8", errors="replace")
            fragment = extract_fragment(raw_html)
            input_kind = "local_raw_http_response"
            source_response_sha = sha256(local_raw.read_bytes())
            if capture.get("source_sha256") and source_response_sha != capture["source_sha256"]:
                errors.append(f"{source_id}: local raw-response hash differs from the recorded capture hash")
                continue
        elif fragment_path.is_file():
            fragment = fragment_path.read_text(encoding="utf-8")
            input_kind = "repository_document_fragment"
            source_response_sha = capture.get("source_sha256")
            expected_fragment_hash = capture.get("document_fragment_sha256")
            if expected_fragment_hash and sha256(fragment.encode("utf-8")) != expected_fragment_hash:
                errors.append(f"{source_id}: repository document-fragment hash differs from its capture ledger")
                continue
        else:
            errors.append(f"{source_id}: neither ignored raw response nor repository fragment is available")
            continue
        text = render_fragment(fragment)
        article_numbers = list(dict.fromkeys(re.findall(r"(?im)^\s*Članak\s+(\d+)\s*\.?\s*$", text)))
        citation_match = re.search(r"/(\d{4})_\d{2}_(\d{1,3})_(\d+)\.html$", urlparse(doc.get("url", "")).path)
        gazette_citation = f"NN {citation_match.group(2)}/{citation_match.group(1)}" if citation_match else None
        record_number = citation_match.group(3) if citation_match else None
        shell_leaks = [token for token in ("Upute za korištenje", "Elektronička pošta", "Početna stranica") if token in text]
        status = "pass" if text and not shell_leaks and gazette_citation and record_number else "pending"
        if not gazette_citation:
            errors.append(f"{source_id}: official Gazette identifier not extractable from official record URL")
        if shell_leaks:
            errors.append(f"{source_id}: page-shell text remains in selected document text: {shell_leaks}")

        text_hash = sha256(text.encode("utf-8"))
        fragment_bytes = fragment.encode("utf-8")
        fragment_hash = sha256(fragment_bytes)
        nn_records.append((source_id, doc, capture, fragment, text, input_kind))
        capture["content_selector"] = FRAGMENT_SELECTOR
        capture["converted_sha256"] = text_hash
        capture["converted_bytes"] = len(text.encode("utf-8"))
        capture["document_fragment_path"] = str(fragment_path.relative_to(ROOT)).replace("\\", "/")
        capture["document_fragment_sha256"] = fragment_hash
        capture["source_response_sha256_verified"] = source_response_sha
        capture["official_publication_identifier"] = {
            "gazette_citation": gazette_citation,
            "gazette_record_number": record_number,
        }
        capture["source_fragment_input"] = input_kind
        capture["replay_status"] = status
        capture["semantic_structure"] = {
            "gazette_citation": gazette_citation,
            "gazette_record_number": record_number,
            "unique_article_heading_count": len(article_numbers),
            "first_article_heading": article_numbers[0] if article_numbers else None,
            "last_article_heading": article_numbers[-1] if article_numbers else None,
            "page_shell_tokens_absent": not shell_leaks,
            "manual_legal_scope_review": "pending",
            "attachments_and_embedded_media_review": "tracked_in_attachment-review.json",
        }
        doc["content_selector"] = FRAGMENT_SELECTOR
        doc["converted_sha256"] = text_hash
        doc["converted_bytes"] = len(text.encode("utf-8"))
        doc["document_fragment_path"] = str(fragment_path.relative_to(ROOT)).replace("\\", "/")
        acceptance_row = acceptance["records"].get(source_id)
        if acceptance_row:
            previously_accepted = acceptance_row.get("status") == "accepted"
            previous_fragment_hash = acceptance_row.get("semantic_review", {}).get("source_fragment_sha256")
            if previously_accepted and previous_fragment_hash != fragment_hash:
                errors.append(
                    f"{source_id}: accepted source fragment changed; stop replay and run a fresh source-acceptance review"
                )
            acceptance_row.setdefault("checks", {})["extraction_completeness"] = {
                "status": status,
                "evidence": (
                    f"Replayed only the official .sl-content .doc fragment; source fragment SHA-256 {fragment_hash}; "
                    f"converted text SHA-256 {text_hash}; official record URL identifies {gazette_citation}, item {record_number}; "
                    f"{len(article_numbers)} unique Article headings; "
                    f"publisher shell markers absent. Manual legal-scope and attachment reviews remain separate."
                ),
            }
            if not previously_accepted:
                acceptance_row["semantic_review"] = {
                    "status": "partial" if status == "pass" else "not_reviewed",
                    "method": "publisher_dom_fragment_replay_and_structural_checks",
                    "evidence": (
                        "The selector-bound official document fragment was retained and replayed deterministically; "
                        "the Gazette citation and Article headings were inventoried and known page-shell strings were excluded. "
                        "This establishes conversion fidelity to the selected DOM fragment, not current legal effect, issue coverage, "
                        "or visual completeness of annexes."
                    ),
                    "source_fragment_path": str(fragment_path.relative_to(ROOT)).replace("\\", "/"),
                    "source_fragment_sha256": fragment_hash,
                    "converted_text_sha256": text_hash,
                }

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2

    if not args.dry_run:
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        for source_id, doc, capture, fragment, text, input_kind in nn_records:
            fragment_path = CAPTURE_DIR / f"{source_id}.html"
            fragment_path.write_text(fragment, encoding="utf-8")
            candidate_path = ROOT / doc["candidate_text_path"]
            markdown = candidate_path.read_text(encoding="utf-8")
            marker = "## Official text-only capture"
            if marker in markdown:
                markdown = markdown.split(marker, 1)[0].rstrip() + "\n\n"
            markdown = markdown.replace("- Extraction: `body`", f"- Extraction: `{FRAGMENT_SELECTOR}` (official text fragment; page shell excluded)")
            markdown += "## Official text-only capture\n\n" + text + "\n"
            candidate_path.write_text(markdown, encoding="utf-8")

        for source_id, ledger_row in ledger_records.items():
            matching = next((row for row in nn_records if row[0] == source_id), None)
            if not matching:
                continue
            _, _, capture, _, _, _ = matching
            ledger_row["raw_path_local_ignored"] = ledger_row.pop("raw_path", capture.get("raw_path"))
            ledger_row["raw_bytes_available_in_repository"] = False
            ledger_row["deterministic_replay_from_repository"] = True
            ledger_row["replay_fragment_path"] = capture["document_fragment_path"]
            ledger_row["replay_fragment_sha256"] = capture["document_fragment_sha256"]
            ledger_row["selector_used"] = FRAGMENT_SELECTOR
            if ledger_row.get("accepted"):
                ledger_row["state"] = "accepted_reviewed_source"
                ledger_row["note"] = (
                    "Accepted source. The tracked fragment contains only the official document selected from .sl-content .doc; "
                    "the full publisher response and page shell are excluded. Source-acceptance evidence is in "
                    "source-acceptance.json; topic and country completeness remain separate."
                )
            else:
                ledger_row["state"] = "official_text_fragment_captured_replayable"
                ledger_row["note"] = (
                    "The tracked fragment contains only the officially published legal document selected from .sl-content .doc; "
                    "the full publisher response and page shell are excluded. Article 18(3) of Copyright Act NN 111/21 is the "
                    "recorded copyright basis for retaining this official text."
                )

        for rule in rules["rules"]:
            selected = [sid for sid in rule.get("source_ids", []) if sid in official_text_ids]
            if not selected:
                continue
            captured_selected = [sid for sid in selected if any(row[0] == sid for row in nn_records)]
            rule["selector"] = FRAGMENT_SELECTOR
            if captured_selected:
                if all(docs[sid].get("retrieval_status") == "accepted_source" for sid in captured_selected):
                    rule["status"] = "replayable_dom_fragment; source_accepted"
                    rule["acceptance_policy"] = "A human-reviewed official link is usable within its checked scope; this rule governs optional local-copy review only. Check material changes and relied-on attachments, not a full amendment chain by default."
                else:
                    rule["status"] = "replayable_dom_fragment; manual_legal_review_pending"
                    rule["acceptance_policy"] = "A human-reviewed official link is usable within its checked scope; local-copy review is optional and proportionate."
            else:
                rule["status"] = "source_specific_capture_pending"
                rule["acceptance_policy"] = "A human-reviewed official link is usable within its checked scope; capture and conversion are not prerequisites to reference use."
            rule["semantic_checks"] = list(dict.fromkeys(rule.get("semantic_checks", []) + [
                "official text only; publisher shell excluded",
                "if captured, fragment is stored in the repository with a source hash for deterministic replay",
                "current legal effect and legal-topic sufficiency are assessed separately",
            ]))

        reuse_basis = {
            "basis_id": "hr-copyright-act-nn-111-2021-art-18-3",
            "as_of": "2026-10-19",
            "status": "official_text_copyright_basis_verified",
            "basis_url": "https://narodne-novine.nn.hr/clanci/sluzbeni/2021_10_111_1941.html",
            "basis": "Copyright and Related Rights Act NN 111/21, Article 18(3): officially published legal, administrative, and judicial texts (including statutes, regulations, and court decisions) cease to be protected by copyright when published for official public information.",
            "currentness_evidence_url": "https://www.dziv.hr/hr/intelektualno-vlasnistvo/autorsko-pravo/zakonodavstvo/",
            "scope": "Only the text of the individually identified official act published in the Narodne novine official part, after publication for official public information.",
            "retention_rule": "Store a source-bound text fragment from .sl-content .doc. Keep official citation, stable URL, capture date and hashes as factual provenance. Exclude the Narodne novine page shell and unrelated page content.",
            "not_covered": [
                "full publisher HTML responses and page-shell text",
                "website design, navigation, interface text, and publisher-authored explanatory material",
                "third-party materials, non-text attachments, images, and logos unless independently reviewed",
                "bulk extraction or reuse of the database as a whole, including any separate database right or technical conditions"
            ],
            "retrieval_constraints": {
                "individual_official_record_urls": "use the stable Narodne novine/ELI record URL, not the metadata API as a full-text endpoint",
                "automated_request_rate": "maximum three queries per second per the live Narodne novine data-access page",
                "full_page_response_retention": "not in the repository; ignored local response may be used transiently to create the official-text fragment"
            }
        }
        for source_id in official_text_ids:
            row = acceptance["records"].get(source_id)
            if not row:
                continue
            row.setdefault("checks", {})["lawful_reuse"] = {
                "status": "pass",
                "scope": "official_text_only",
                "basis_id": reuse_basis["basis_id"],
                "evidence": (
                    "Copyright and Related Rights Act NN 111/21 Article 18(3) provides that official legislative, administrative, "
                    "and judicial texts cease to be protected by copyright once published for official public information. "
                    "This pass covers only the individual official act text, not the Narodne novine page shell, third-party attachments, "
                    "or database-wide/systematic reuse. Store only a source-specific text fragment and observe the publisher's stated "
                    "maximum three automated queries per second."
                )
            }

        write_json(PACK / "references/reuse-policy.json", {
            "schema_version": "1.0.0",
            "jurisdiction": "HR",
            "as_of": "2026-10-19",
            "policy": reuse_basis,
            "source_ids_with_official_text_basis": sorted(official_text_ids),
        })

        write_json(PACK / "references/croatia-capture-results.json", capture_results)
        write_json(PACK / "references/capture-ledger.json", ledger)
        write_json(PACK / "references/candidate-manifest.json", manifest)
        write_json(PACK / "references/source-acceptance.json", acceptance)
        write_json(PACK / "references/source-rules.json", rules)

    print(f"Narodne novine official texts: {len(nn_records)} replayed; {sum(1 for row in nn_records if row[0] in acceptance['records'] and acceptance['records'][row[0]]['checks']['extraction_completeness']['status']=='pass')} extraction-complete; {len(errors)} errors.")
    print("Full publisher HTML responses remain local/ignored; only selector-bound official text fragments are retained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
