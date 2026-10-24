#!/usr/bin/env python3
"""Convert or verify saved Austrian RIS section HTML from its publisher text container.

This helper is deliberately offline. It resolves exact response bytes through
the monitor's indexed local-only archive, verifies their SHA-256, and does not
make network requests or promote sources to the trusted corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from local_capture_archive import resolve_capture


PACK_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PACK_DIR / "references" / "candidate-manifest.json"
CAPTURE_PATH = PACK_DIR / "references" / "capture-ledger.json"
RULE_VERSION = "ris-contentblock-v1"
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "ol", "ul", "br", "div"}


class RISPageParser(HTMLParser):
    """Extract rendered text from RIS's nested ``div.contentBlock`` node."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.content_depth = 0
        self.ignore_stack: list[str] = []
        self.parts: list[str] = []
        self.links: list[str] = []
        self.found_content = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        ignored = tag in {"script", "style", "noscript"} or "sr-only" in classes
        # Ignore an entire inaccessible subtree before changing the content
        # depth. The old order incremented content_depth for hidden divs and
        # could pull accessibility-only expansions into the next visible block.
        # RIS marks visually rendered text aria-hidden when it supplies a
        # separate screen-reader-expanded `.sr-only` equivalent, so retain the
        # visible text and omit only the expanded duplicate.
        if self.ignore_stack:
            if tag not in VOID_TAGS:
                self.ignore_stack.append(tag)
            return
        if ignored:
            if tag not in VOID_TAGS:
                self.ignore_stack.append(tag)
            return

        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"] or "")

        if tag == "div":
            if self.content_depth:
                self.content_depth += 1
            elif "contentBlock" in classes:
                self.content_depth = 1
                self.found_content = True

        if self.content_depth and tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.ignore_stack:
            if self.ignore_stack[-1] == tag:
                self.ignore_stack.pop()
            elif tag in self.ignore_stack:
                while self.ignore_stack and self.ignore_stack[-1] != tag:
                    self.ignore_stack.pop()
                if self.ignore_stack:
                    self.ignore_stack.pop()
            return

        if self.content_depth and tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "div" and self.content_depth:
            self.content_depth -= 1
        elif self.content_depth and tag == "span":
            # RIS sometimes places paragraph numbers and operative text in
            # adjacent spans; preserve their word boundary in plain text.
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self.content_depth and not self.ignore_stack:
            self.parts.append(data)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    archived = resolve_capture(value)
    if archived is not None:
        return archived
    if value.startswith("captures/"):
        return PACK_DIR / path
    repo_root = PACK_DIR.parent.parent
    resolved = repo_root / path
    if resolved.exists():
        return resolved
    prefix = "source-library/austria/"
    if value.startswith(prefix):
        bundled = PACK_DIR / value[len(prefix):]
        if bundled.exists():
            return bundled
    return resolved


def extract_text(raw: bytes) -> tuple[str, list[str]]:
    parser = RISPageParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    parser.close()
    lines = []
    for source_line in "".join(parser.parts).replace("\r", "").replace("\xa0", " ").splitlines():
        line = re.sub(r"\s+", " ", source_line).strip()
        if line:
            lines.append(line)
    # Avoid duplicate blank lines while keeping each legal paragraph/list item
    # on its own line for citation and review.
    return "\n".join(lines).strip(), parser.links


def render_candidate(record: dict, capture: dict, text: str) -> bytes:
    publisher_id = json.dumps(record.get("publisher_identifier", {}), ensure_ascii=False, sort_keys=True)
    verification = record.get("verification_status", "")
    accepted = record.get("accepted") is True
    id_label = "Source ID" if accepted else "Candidate ID"
    status_label = "accepted source; per-source gates passed" if accepted else "unaccepted review candidate"
    body = [
        f"# {record['title']}",
        "",
        f"- Jurisdiction: Austria",
        f"- {id_label}: `{record['id']}`",
        f"- Official URL: {record['url']}",
        f"- Resolved URL: {capture.get('resolved_url') or record['url']}",
        f"- Retrieved: {capture.get('retrieved_at', 'date not recorded')}",
        f"- Publisher identifier: `{publisher_id}`",
        f"- Version evidence: {verification}",
        f"- Media type: `{capture.get('source_content_type', 'text/html')}`",
        f"- Raw source SHA-256: `{capture['source_sha256']}`",
        f"- Conversion rule: `{RULE_VERSION}`; selector `div.contentBlock`",
        f"- Status: {status_label}",
        "",
        "## Captured official text",
        "",
        text,
        "",
    ]
    return "\n".join(body).encode("utf-8")


def candidate_output_path(record: dict) -> Path:
    existing = record.get("candidate_text_path")
    if existing:
        return resolve_repo_path(existing)
    safe_id = re.sub(r"[^a-z0-9-]+", "-", record["id"].lower()).strip("-")
    folder = {
        "national_legislation": "legislation",
        "official_case_law": "case_law",
        "official_guidance": "guidance",
        "official_guidance_directory": "discovery",
    }.get(record.get("source_type"), "discovery")
    return PACK_DIR / "candidates" / folder / f"{safe_id}.md"


def sync_records() -> tuple[dict, dict]:
    manifest = load_json(MANIFEST_PATH)
    capture_ledger = load_json(CAPTURE_PATH)
    manifest_records = {r["id"]: r for r in manifest["documents"]}
    capture_records = {r["candidate_id"]: r for r in capture_ledger["records"]}
    if manifest_records.keys() != capture_records.keys():
        missing_capture = sorted(manifest_records.keys() - capture_records.keys())
        missing_manifest = sorted(capture_records.keys() - manifest_records.keys())
        raise ValueError(f"Candidate IDs do not reconcile: capture missing {missing_capture}; manifest missing {missing_manifest}")
    return manifest, capture_ledger


def convert() -> int:
    manifest, capture_ledger = sync_records()
    manifest_records = {r["id"]: r for r in manifest["documents"]}
    converted = 0
    pending = 0

    for capture in capture_ledger["records"]:
        if capture.get("retrieval_status") != "pending_conversion":
            continue
        pending += 1
        record = manifest_records[capture["candidate_id"]]
        raw_path = resolve_repo_path(capture["raw_path"])
        raw = raw_path.read_bytes()
        actual_hash = digest(raw)
        if actual_hash != capture.get("source_sha256"):
            raise ValueError(f"Raw hash mismatch for {record['id']}: {actual_hash}")

        text, links = extract_text(raw)
        if not text or len(text) < 200:
            raise ValueError(f"RIS text container is empty or unexpectedly short for {record['id']}: {len(text)} characters")

        output = candidate_output_path(record)
        output.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_candidate(record, capture, text)
        output.write_bytes(rendered)
        rel_output = output.relative_to(PACK_DIR.parent.parent).as_posix()
        converted_hash = digest(rendered)

        capture.update({
            "candidate_text_path": rel_output,
            "converted_sha256": converted_hash,
            "converted_bytes": len(rendered),
            "content_selector": "div.contentBlock",
            "conversion_rule_version": RULE_VERSION,
            "retrieval_status": "converted_review_candidate",
            "review_state": "review_candidate",
        })
        capture.pop("retrieval_note", None)
        record.update({
            "candidate_text_path": rel_output,
            "source_sha256": capture["source_sha256"],
            "source_bytes": capture["source_bytes"],
            "resolved_url": capture.get("resolved_url"),
            "converted_sha256": converted_hash,
            "converted_bytes": len(rendered),
            "content_selector": "div.contentBlock",
            "conversion_rule_version": RULE_VERSION,
            "retrieval_status": "converted_review_candidate",
            "retrieved": True,
            "accepted": False,
        })
        record.pop("retrieval_note", None)
        converted += 1

    if pending:
        manifest["retrieved_review_candidate_count"] = sum(
            bool(r.get("retrieved")) and not r.get("accepted") and r.get("review_state") != "discovery_only"
            for r in manifest["documents"]
        )
        manifest["converted_review_candidate_count"] = sum(
            bool(r.get("retrieved")) and not r.get("accepted") and r.get("review_state") != "discovery_only"
            and bool(r.get("source_text_path") or r.get("candidate_text_path"))
            and not r.get("native_source_path") and r.get("source_type") != "official_form"
            for r in manifest["documents"]
        )
        manifest["native_pdf_source_count"] = sum(bool(r.get("native_source_path")) for r in manifest["documents"])
        manifest["native_pdf_review_candidate_count"] = sum(bool(r.get("native_source_path")) and not r.get("accepted") for r in manifest["documents"])
        manifest["accepted_source_count"] = sum(1 for r in manifest["documents"] if r.get("accepted"))
        manifest["candidate_source_count"] = sum(
            1 for r in manifest["documents"]
            if r.get("retrieved") and not r.get("accepted") and r.get("review_state") != "discovery_only"
        )
        manifest["located_not_captured_count"] = sum(1 for r in manifest["documents"] if not r.get("retrieved"))
        manifest["discovery_only_count"] = sum(1 for r in manifest["documents"] if r.get("review_state") == "discovery_only")
        manifest["retrieval_status"] = (
            f"{manifest['accepted_source_count']} accepted; {manifest['candidate_source_count']} captured and pending review; "
            f"{manifest['discovery_only_count']} discovery-only; {manifest['located_not_captured_count']} located but not captured"
        )
        capture_ledger["conversion_rule"] = RULE_VERSION
        capture_ledger["converted_review_candidate_count"] = manifest["converted_review_candidate_count"]
    save_json(MANIFEST_PATH, manifest)
    save_json(CAPTURE_PATH, capture_ledger)
    accepted = sum(1 for r in manifest["documents"] if r.get("accepted"))
    print(f"converted={converted} pending_conversion_records={pending} accepted_source_count={accepted}")
    return 0


def verify() -> int:
    manifest, capture_ledger = sync_records()
    manifest_records = {r["id"]: r for r in manifest["documents"]}
    verified = 0
    for capture in capture_ledger["records"]:
        record = manifest_records[capture["candidate_id"]]
        payload = capture.get("linked_payload")
        if payload:
            candidate_path = resolve_repo_path(payload["candidate_path"])
            if not candidate_path.is_file():
                raise ValueError(f"Native PDF candidate missing for {record['id']}: {candidate_path}")
            candidate = candidate_path.read_bytes()
            if not candidate.startswith(b"%PDF-") or digest(candidate) != payload.get("source_sha256"):
                raise ValueError(f"Native PDF signature or hash mismatch for {record['id']}")
            raw_path = resolve_repo_path(payload.get("raw_path", ""))
            if raw_path.is_file() and digest(raw_path.read_bytes()) != payload.get("source_sha256"):
                raise ValueError(f"Raw PDF response hash mismatch for {record['id']}")
            verified += 1
            continue
        raw_path = resolve_repo_path(capture.get("raw_path") or "")
        raw_present = raw_path.is_file()
        if not raw_present:
            if capture.get("retrieval_status") == "retrieval_or_conversion_error":
                continue
        else:
            raw = raw_path.read_bytes()
            if digest(raw) != capture.get("source_sha256"):
                raise ValueError(f"Raw response hash mismatch for {record['id']}")
        if capture.get("retrieval_status") not in {"converted_review_candidate", "accepted_source"}:
            continue
        output_path = resolve_repo_path(capture.get("source_text_path") or capture.get("candidate_text_path", ""))
        if not output_path.is_file():
            raise ValueError(f"Converted candidate missing for {record['id']}: {output_path}")
        output = output_path.read_bytes()
        if digest(output) != capture.get("converted_sha256"):
            raise ValueError(f"Converted candidate hash mismatch for {record['id']}")
        if raw_present and capture.get("conversion_rule_version") == RULE_VERSION:
            text, _ = extract_text(raw)
            replay = render_candidate(record, capture, text)
            if replay != output:
                raise ValueError(f"Offline replay mismatch for {record['id']}")
        verified += 1
    print(f"verified_records={verified}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("convert", "verify"))
    args = parser.parse_args()
    try:
        return convert() if args.action == "convert" else verify()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
