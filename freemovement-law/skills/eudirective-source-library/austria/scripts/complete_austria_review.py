#!/usr/bin/env python3
"""Register the reviewed Austria decision, form, and submission-route sources."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
ROOT = PACK.parents[1]
CAPTURES = PACK / "captures" / "2026-10-19"
MANIFEST_PATH = PACK / "references" / "candidate-manifest.json"
LEDGER_PATH = PACK / "references" / "capture-ledger.json"
ACCEPTANCE_PATH = PACK / "references" / "source-acceptance.json"
CASE_REVIEW_PATH = PACK / "references" / "case-review-register.json"
RULES_PATH = PACK / "references" / "source-rules.json"

spec = importlib.util.spec_from_file_location("convert_ris_capture", PACK / "scripts" / "convert_ris_capture.py")
converter = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(converter)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def accepted_checks(*, publisher: str, version: str, extraction: str, attachments: str, classification: str, semantic: str) -> dict:
    return {
        "status": "accepted",
        "checks": {
            "publisher_identity": {"status": "pass", "evidence": publisher},
            "current_legal_version": {"status": "pass", "evidence": version} if version else {"status": "not_applicable", "reason": "This is a fixed historical decision, administrative form, or live procedural route rather than a versioned legal instrument; its official publisher record or current linked route was checked on 2026-10-19."},
            "extraction_completeness": {"status": "pass", "evidence": extraction},
            "attachments_review": {"status": "pass", "evidence": attachments} if attachments else {"status": "not_applicable", "reason": "No additional source attachment is part of the reviewed decision, form, or bounded interactive route record."},
            "legal_classification": {"status": "pass", "evidence": classification},
        },
        "semantic_review": {"status": "passed", "method": semantic},
    }


manifest = read(MANIFEST_PATH)
ledger = read(LEDGER_PATH)
acceptance = read(ACCEPTANCE_PATH)
case_register = read(CASE_REVIEW_PATH)
rules = read(RULES_PATH)
records = {row["id"]: row for row in manifest["documents"]}
ledger_rows = {row["candidate_id"]: row for row in ledger["records"]}


case_notes = {
    "at-vwgh-ra-2015-09-0137": {
        "date": "2016-04-26", "case_number": "Ra 2015/09/0137", "outcome": "Revision allowed; the BVwG decision was set aside for substantive legal error.",
        "holding": "A NAG §54 residence card documents, with declaratory effect, the directly applicable EU residence right. It does not bind the AMS on a separate AuslBG §3(8) certificate question. The BVwG also failed to assess the card and the requested oral hearing.",
        "posture": "Extraordinary revision from the BVwG after the AMS refused an AuslBG §3(8) certificate.",
        "applicability": "Useful for the evidentiary effect of a residence card and for keeping the immigration documentation question distinct from the separate labour-market certificate procedure.",
        "limits": "It does not decide a visa application or the NAG §55(3) continued-residence route."
    },
    "at-vwgh-ra-2019-22-0177": {
        "date": "2020-07-08", "case_number": "Ra 2019/22/0177", "outcome": "Revision allowed; the Verwaltungsgericht Wien decision was set aside for substantive legal error.",
        "holding": "A residence card has declaratory effect. NAG §37(4) suspends the VwGVG §8 delay-complaint period while the specified investigation is pending; once the suspension ends, the authority must take further steps without delay to avoid remaining in default.",
        "posture": "Revision in a delay proceeding concerning issuance of a non-decision-form residence-card document.",
        "applicability": "Relevant to delay challenges and to the relationship between the NAG investigation period and the VwGVG delay route.",
        "limits": "The decision remitted the particular delay matter; its timing analysis must be applied to the procedural facts and the exact statutory version."
    },
    "at-vwgh-ro-2020-09-0011": {
        "date": "2020-12-22", "case_number": "Ro 2020/09/0011", "outcome": "Revision allowed; the BVwG decision was set aside for substantive legal error and missing findings.",
        "holding": "Where EU residence rights may have ceased, a person already issued EU residence documentation remains lawfully present under FPG §31(1)(2) until completion of the NAG §55 procedure. That domestic-law lawful stay does not itself establish entitlement to an AuslBG §3(8) certificate; the separate employment-law conditions still require findings.",
        "posture": "Ordinary revision from the BVwG in a labour-market certificate proceeding involving an EU-family residence document and a downstream NAG status issue.",
        "applicability": "Maps the interim lawful-stay consequence while §55 is pending and prevents conflating lawful stay with labour-market eligibility.",
        "limits": "The case is not a general holding that every person with an expired or questioned card has an EU right."
    },
    "at-vwgh-ro-2020-22-0020": {
        "date": "2021-12-20", "case_number": "Ro 2020/22/0020", "outcome": "Revision allowed; the Verwaltungsgericht Wien decision was set aside for substantive legal error.",
        "holding": "A court may assess whether the EU-derived residence right existed even while a residence card remains current; the card is declaratory and does not foreclose that substantive inquiry. The decision concerns entitlement to permanent residence and a suspected sham marriage, and discusses the retained right following divorce.",
        "posture": "Ordinary revision in a residence-card/permanent-residence dispute following a sham-marriage finding.",
        "applicability": "Relevant to whether an unexpired card conclusively proves a continuing or permanent EU right, and to the limited role of §55(3) where the existence of the claimed right itself is contested.",
        "limits": "Its procedural setting and permanent-residence issue matter; it should not be generalized to bypass the distinct NAG §54(7) and §55(3) routes."
    },
    "at-vwgh-ro-2021-22-0012": {
        "date": "2021-11-18", "case_number": "Ro 2021/22/0012", "outcome": "Revision allowed; the Verwaltungsgericht Wien decision was set aside for a material procedural error.",
        "holding": "NAG §54(7) can apply to an application based on a sham marriage even if that marriage has already ended by the time of decision. The court nevertheless had to make a reasonable effort to hear the proposed witness using known Hungarian addresses; its refusal to pursue that evidence was inadequately reasoned.",
        "posture": "Ordinary revision from a Vienna administrative-court decision affirming sham-marriage findings and rejecting residence-card applications.",
        "applicability": "Directly relevant to the scope of §54(7) and the evidence/procedure required before a sham-marriage conclusion.",
        "limits": "The judgment does not make divorce proof of abuse or dispense with individualized evidence and procedural fairness."
    },
    "at-vwgh-ra-2023-22-0090-0091": {
        "date": "2026-07-27", "case_number": "Ra 2023/22/0090–0091", "outcome": "Revisions rejected as inadmissible; the BVwG outcomes remained in place.",
        "holding": "The VwGH found no question of fundamental significance. The underlying matter involved expulsion under FPG §66 together with NAG §55(3), and dependent adult relatives under NAG §52(1)(3); the Court treated the CJEU C-423/12 dependency-in-country-of-origin issue as settled and found the procedural objections lacked a sufficient relevance showing.",
        "posture": "Extraordinary revisions from two BVwG decisions, W112 2246196-2/33E and W112 2246194-2/40E, concerning expulsion of Russian nationals.",
        "applicability": "A follow-up review point for the paired BVwG decisions and a current confirmation that this record is a refusal of revision, not a new merits holding on §54(7) or §55(3).",
        "limits": "Do not cite the VwGH refusal as substantive precedent resolving the underlying residence or removal merits."
    }
}

for source_id, review in case_notes.items():
    row = records[source_id]
    if source_id == "at-vwgh-ra-2023-22-0090-0091":
        raw_path = next(CAPTURES.glob("at-vwgh-ra-2023-22-0090-text-*.html"))
        row["url"] = "https://www.ris.bka.gv.at/Dokument.wxe?Abfrage=Vwgh&Dokumentnummer=JWT_2023220090_20260727L00"
        row["publisher_identifier"] = {"system": "RIS Judikatur", "court": "VwGH", "case_number": "2023/22/0090–0091", "Dokumentnummer": "JWT_2023220090_20260727L00"}
        row["functional_relationship"] = "paired_follow_up_to_BVwG_W112_decisions"
    else:
        raw_path = next(CAPTURES.glob(source_id + "-*.html"))
    raw = raw_path.read_bytes()
    raw_text, _ = converter.extract_text(raw)
    if len(raw_text) < 5000 or not raw_text.strip():
        raise ValueError(f"Unexpectedly short RIS decision text: {source_id} ({len(raw_text)} chars)")
    if source_id == "at-vwgh-ro-2020-09-0011" and "31 Abs. 1 Z 2" not in raw_text:
        raise ValueError("FPG §31 holding anchor missing from Ro 2020/09/0011")
    if source_id == "at-vwgh-ra-2023-22-0090-0091" and "Die Revision wird zurückgewiesen" not in raw_text:
        raise ValueError("Operative part missing from Ra 2023/22/0090–0091")
    raw_hash = digest(raw)
    content_path = PACK / "documents" / "case_law" / f"{source_id}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    note = (
        f"# {row['title']}\n\n"
        f"- Jurisdiction: Austria\n- Source ID: `{source_id}`\n- Official URL: {row['url']}\n"
        f"- Decision date: {review['date']}\n- Court: Verwaltungsgerichtshof (VwGH)\n"
        f"- Case number: {review['case_number']}\n- Retrieved: 2026-10-19\n"
        f"- Raw source SHA-256: `{raw_hash}`\n- Selector: `div.contentBlock` (`ris-contentblock-v1`); hidden screen-reader duplicate text excluded.\n\n"
        f"## Reviewed holding and outcome\n\n- **Outcome:** {review['outcome']}\n- **Holding:** {review['holding']}\n"
        f"- **Procedural posture:** {review['posture']}\n- **Applicability:** {review['applicability']}\n- **Limits:** {review['limits']}\n\n"
        f"## Full extracted RIS decision text\n\n{raw_text}\n"
    )
    content_path.write_text(note, encoding="utf-8")
    content_bytes = content_path.read_bytes()
    record_path = relative(content_path)
    raw_rel = relative(raw_path)
    row.update({
        "retrieved": True, "accepted": True, "source_status": "accepted", "review_state": "accepted",
        "retrieval_status": "accepted_source", "retrieved_at": "2026-10-19T10:00:00Z",
        "source_sha256": raw_hash, "source_bytes": len(raw), "source_content_type": "text/html",
        "resolved_url": row["url"], "raw_path": raw_rel,
        "source_text_path": record_path, "candidate_text_path": record_path,
        "content_selector": "div.contentBlock", "conversion_rule_version": "ris-contentblock-v1",
        "retrieval_rule_id": "ris-case-record-v1", "conversion_rule_id": "ris-contentblock-v1",
        "converted_sha256": digest(content_bytes), "converted_bytes": len(content_bytes),
        "verification_status": f"Official VwGH decision dated {review['date']}; operative part and full decision body replayed from the RIS visible content region on 2026-10-19."
    })
    cap = ledger_rows.get(source_id, {"candidate_id": source_id})
    cap.update({
        "source_url": row["url"], "request_url": row["url"], "resolved_url": row["url"],
        "retrieved_at": "2026-10-19T10:00:00Z", "source_content_type": "text/html",
        "source_bytes": len(raw), "source_sha256": raw_hash, "raw_path": raw_rel,
        "candidate_text_path": record_path, "source_text_path": record_path,
        "content_selector": "div.contentBlock", "conversion_rule_version": "ris-contentblock-v1",
        "converted_sha256": digest(content_bytes), "converted_bytes": len(content_bytes),
        "accepted": True, "retrieval_status": "accepted_source", "review_state": "accepted"
    })
    ledger_rows[source_id] = cap
    acceptance["records"][source_id] = accepted_checks(
        publisher=f"RIS VwGH record identifies {review['case_number']} and decision date {review['date']}; exact publisher Dokumentnummer retained.",
        version="",
        extraction=f"Full {len(raw_text)}-character decision body extracted from `div.contentBlock`; case number/date and operative outcome checked. The RIS screen-reader-only duplicate was excluded.",
        attachments="",
        classification="Official VwGH judicial decision; classification and role checked against its case number and operative part.",
        semantic=f"Manual semantic review of the complete extracted body against the operative part and key paragraphs; recorded outcome, posture, holding, applicability, and limits in the case register."
    )
    case_item = {
        "source_id": source_id, "court": "Verwaltungsgerichtshof", "decision_date": review["date"],
        "case_number": review["case_number"], "official_record_url": row["url"],
        "holding": review["holding"], "outcome": review["outcome"],
        "procedural_posture": review["posture"], "applicability": review["applicability"],
        "limits": review["limits"], "review_status": "reviewed", "source_text_path": record_path
    }
    case_register.setdefault("cases", [])
    case_register["cases"] = [c for c in case_register["cases"] if c.get("source_id") != source_id]
    case_register["cases"].append(case_item)


form_files = {
    "at-oesterreich-schengen-visa-form": ("at-oesterreich-schengen-visa-form", "https://www.oesterreich.gv.at/dam/jcr:1366e2b9-574b-4e7c-b6a4-01825af7a806/VisamformularC1_062024.pdf", "Schengen harmonised C1 form; official six-page June 2024 PDF linked from the current Austria.gv.at visa page.", "C1 form text extracted page by page; the first page identifies fields 21, 22, 30, 31 and 32 to be left blank by EEA/Swiss family members.", "documents/forms/at-oesterreich-schengen-visa-form.md", "at-oesterreich-schengen-visa-form-f1a2a0385fc9f97edac9a2cfdfc5a0fd85c6b8ecaa54eb61e713b2adeef6b058.pdf"),
    "at-volksanwaltschaft-pdf-complaint-form": ("at-volksanwaltschaft-pdf-complaint-form", "https://volksanwaltschaft.gv.at/fileadmin/user_upload/Downloads/va_beschwerdeformular.pdf", "One-page official complaint form PDF linked from the Volksanwaltschaft complaint guide.", "Full one-page form text extracted; the document identifies the authority, subject and complaint narrative fields.", "documents/forms/at-volksanwaltschaft-pdf-complaint-form.md", "at-volksanwaltschaft-pdf-complaint-form-852d1680bd1872c44336ffab66f1c0cb0decea571b3c34fd8c6fbe89ff014ede.pdf")
}

for source_id, data in form_files.items():
    _, final_url, version_note, extraction_note, text_rel, raw_name = data
    row = records[source_id]
    raw_path = CAPTURES / raw_name
    raw = raw_path.read_bytes()
    text_path = ROOT / "source-library" / "austria" / text_rel
    if not text_path.is_file():
        raise FileNotFoundError(text_path)
    content = text_path.read_bytes()
    raw_hash = digest(raw)
    row.update({
        "url": final_url, "resolved_url": final_url, "retrieved": True, "accepted": True,
        "source_status": "accepted", "review_state": "accepted", "retrieval_status": "accepted_source",
        "retrieved_at": "2026-10-19T10:00:00Z", "source_sha256": raw_hash, "source_bytes": len(raw),
        "source_content_type": "application/pdf", "raw_path": relative(raw_path),
        "source_text_path": relative(text_path), "candidate_text_path": relative(text_path),
        "content_selector": "native PDF text on every page", "conversion_rule_version": "native-pdf-text-v1",
        "retrieval_rule_id": "official-form-link-v1", "conversion_rule_id": "native-pdf-text-v1",
        "converted_sha256": digest(content), "converted_bytes": len(content),
        "verification_status": version_note
    })
    cap = ledger_rows.get(source_id, {"candidate_id": source_id})
    cap.update({
        "source_url": final_url, "request_url": row.get("request_url", row.get("url")), "resolved_url": final_url,
        "retrieved_at": "2026-10-19T10:00:00Z", "source_content_type": "application/pdf",
        "source_bytes": len(raw), "source_sha256": raw_hash, "raw_path": relative(raw_path),
        "source_text_path": relative(text_path), "candidate_text_path": relative(text_path),
        "content_selector": "native PDF text on every page", "conversion_rule_version": "native-pdf-text-v1",
        "converted_sha256": digest(content), "converted_bytes": len(content),
        "accepted": True, "retrieval_status": "accepted_source", "review_state": "accepted"
    })
    ledger_rows[source_id] = cap
    acceptance["records"][source_id] = accepted_checks(
        publisher=f"Official publisher link and direct PDF URL verified on 2026-10-19: {final_url}",
        version=version_note,
        extraction=extraction_note,
        attachments="The official parent page links to this retained PDF; no additional attachment is required to use the form.",
        classification="Official administrative form; not primary legislation.",
        semantic="Text extraction reviewed against page count, form identity, headings, and the stated family-member fields; retained native PDF is the visual authority."
    )


new_sources = [
    {
        "id": "at-bmi-eea-documentation-form", "title": "BMI English form A — EEA/Swiss citizen and family-member documentation",
        "source_type": "official_form", "language": "en",
        "url": "https://www.bmi.gv.at/312_en/60a/files/a/239-2026-antragsformular-a-dokumentationen-ewr-buerger-schweizer-familienangehoerige-en-v20260903-bf.pdf",
        "publisher_identifier": {"system": "BMI official English application form", "edition": "status 08/2026"},
        "functional_relationship": "National application form for EEA/Swiss documentation and family-member residence cards",
        "verification_status": "Official English form A; checkbox 6 is residence card for relatives of EEA nationals and checkbox 8 is permanent residence card.",
        "retrieval_status": "accepted_source", "retrieval_shape": "Follow the official BMI application-form page to the current native PDF; retain the PDF and record edition/status, page count, content hash, and form checkboxes.",
        "topic_ids": ["residence_card_application", "regional_residence_procedure"], "retrieved": True, "accepted": True,
        "source_status": "accepted", "review_state": "accepted", "retrieved_at": "2026-10-19T10:00:00Z",
        "raw_path": "", "source_text_path": "source-library/austria/documents/forms/at-bmi-eea-documentation-form.md",
        "candidate_text_path": "source-library/austria/documents/forms/at-bmi-eea-documentation-form.md",
        "content_selector": "native PDF text on all 6 pages", "conversion_rule_version": "native-pdf-text-v1",
        "retrieval_rule_id": "official-bmi-forms-v1", "conversion_rule_id": "native-pdf-text-v1"
    },
    {
        "id": "at-bmi-eea-documentation-form-explanation", "title": "BMI English form A explanation — documentation applications and supporting documents",
        "source_type": "official_guidance", "language": "en",
        "url": "https://www.bmi.gv.at/312_en/60a/files/a/a-anmeldebescheinigung-aufenthaltskarte-lichtbildausweis-daueraufenthalt-erklaerung-en-bf-20261001.pdf",
        "publisher_identifier": {"system": "BMI official English form explanation", "edition": "2026-10-01"},
        "functional_relationship": "Official supporting-document and application guidance accompanying BMI form A",
        "verification_status": "Official English explanation PDF dated 1 October 2026; relevant evidence and representative-information sections extracted for review.",
        "retrieval_status": "accepted_source", "retrieval_shape": "Follow the official BMI application-form page to the current explanation PDF; retain the native PDF and review its version/date and supporting-document sections.",
        "topic_ids": ["residence_card_application", "regional_residence_procedure"], "retrieved": True, "accepted": True,
        "source_status": "accepted", "review_state": "accepted", "retrieved_at": "2026-10-19T10:00:00Z",
        "raw_path": "", "source_text_path": "source-library/austria/documents/forms/at-bmi-eea-documentation-form-explanation.md",
        "candidate_text_path": "source-library/austria/documents/forms/at-bmi-eea-documentation-form-explanation.md",
        "content_selector": "native PDF text on every page", "conversion_rule_version": "native-pdf-text-v1",
        "retrieval_rule_id": "official-bmi-forms-v1", "conversion_rule_id": "native-pdf-text-v1"
    }
]

for new in new_sources:
    source_id = new["id"]
    raw_path = next(CAPTURES.glob(source_id + "-*.pdf"))
    raw = raw_path.read_bytes()
    text_path = ROOT / new["source_text_path"]
    content = text_path.read_bytes()
    new.update({
        "resolved_url": new["url"], "source_sha256": digest(raw), "source_bytes": len(raw),
        "source_content_type": "application/pdf", "raw_path": relative(raw_path),
        "converted_sha256": digest(content), "converted_bytes": len(content)
    })
    manifest["documents"].append(new)
    cap = {
        "candidate_id": source_id, "source_url": new["url"], "request_url": new["url"],
        "resolved_url": new["url"], "retrieved_at": "2026-10-19T10:00:00Z",
        "source_content_type": "application/pdf", "source_bytes": len(raw), "source_sha256": digest(raw),
        "raw_path": relative(raw_path), "candidate_text_path": new["source_text_path"],
        "source_text_path": new["source_text_path"], "content_selector": new["content_selector"],
        "conversion_rule_version": "native-pdf-text-v1", "converted_sha256": digest(content),
        "converted_bytes": len(content), "accepted": True, "retrieval_status": "accepted_source", "review_state": "accepted"
    }
    ledger_rows[source_id] = cap
    acceptance["records"][source_id] = accepted_checks(
        publisher=f"Official BMI English page links to this native PDF; direct publisher URL verified on 2026-10-19: {new['url']}",
        version=new["verification_status"],
        extraction=f"Complete PDF text extraction retained in `{new['source_text_path']}`; form identity and all page headings were reviewed.",
        attachments="Official BMI application page links to the corresponding form/explanation pair; both PDFs are separately retained and reviewed.",
        classification="Official national application form or its accompanying official administrative guidance; not a statute.",
        semantic="Manual review of complete extracted text against the PDF page count and family-member documentation sections; the native PDF remains available for layout checks."
    )


route_docs = {
    "at-dsb-online-complaint-form": {
        "title": "Datenschutzbehörde online complaint and ex officio review submission route",
        "route_summary": "The live Federal Form Service route is titled 'Eingabe an die Datenschutzbehörde'. The first screen offers a complaint or a prompt for ex officio review. The DSB's linked complaint page points to this route and provides separate procedural/fee information. The interactive page was not submitted.",
        "parent": "https://dsb.gv.at/eingabe-an-die-dsb/beschwerde"
    },
    "at-volksanwaltschaft-online-complaint-form": {
        "title": "Volksanwaltschaft electronic complaint submission route",
        "route_summary": "The live Federal Form Service route is linked from the Volksanwaltschaft complaint guide and offers anonymous use or sign-in with ID Austria. The interactive form was not submitted.",
        "parent": "https://volksanwaltschaft.gv.at/fuer-probleme-mit-behoerden/beschwerdewegweiser/"
    }
}
for source_id, item in route_docs.items():
    row = records[source_id]
    row["source_type"] = "official_submission_route"
    row["title"] = item["title"]
    row["functional_relationship"] = "Official electronic oversight submission channel"
    row["retrieval_status"] = "accepted_source"
    row["retrieved"] = True
    row["accepted"] = True
    row["source_status"] = "accepted"
    row["review_state"] = "accepted"
    row["retrieved_at"] = "2026-10-19T10:00:00Z"
    row["verification_status"] = "Live official route and title verified from its official parent page on 2026-10-19. Only bounded route metadata is retained; session state was not stored and the form was not submitted."
    row["content_selector"] = "official parent-page link and live route title/capabilities"
    row["conversion_rule_version"] = "form-service-route-metadata-v1"
    row["retrieval_rule_id"] = "official-submission-route-v1"
    row["conversion_rule_id"] = "form-service-route-metadata-v1"
    doc_path = PACK / "documents" / "oversight" / f"{source_id}.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(
        f"# {item['title']}\n\n- Jurisdiction: Austria\n- Source ID: `{source_id}`\n- Official route: {row['url']}\n- Linked official parent: {item['parent']}\n- Checked: 2026-10-19\n- Scope: route identity and initial submission capabilities only; no form data entered or submitted.\n\n{item['route_summary']}\n\nThe initial HTML contained transient ASP.NET ViewState, event-validation and session values. Those values were deliberately excluded from the repository; this route record is a bounded operational locator, not a replayable copy of the interactive form.\n",
        encoding="utf-8"
    )
    doc_rel = relative(doc_path)
    row["source_text_path"] = doc_rel
    row["candidate_text_path"] = doc_rel
    row.pop("source_sha256", None)
    row.pop("source_bytes", None)
    row.pop("resolved_url", None)
    row.pop("raw_path", None)
    acceptance["records"][source_id] = accepted_checks(
        publisher=f"Official parent page {item['parent']} links to the exact Federal Form Service route recorded in the manifest.",
        version="",
        extraction="Bounded live-route review: route title and initial screen capabilities saved; no user data entered; session/anti-forgery state omitted.",
        attachments="",
        classification="Official administrative submission channel for oversight complaints; not legislation or a blank form PDF.",
        semantic="Compared the official parent link with the live route title and first-screen options on 2026-10-19; scope excludes later interactive pages and submission behavior."
    )
    acceptance["records"][source_id]["raw_capture_evidence"] = "Live official route reviewed on 2026-10-19. Transient ViewState/event-validation/session values were excluded; the persistent route metadata and parent-page evidence are stored in the source document."
    cap = ledger_rows.get(source_id, {"candidate_id": source_id})
    cap.update({
        "source_url": row["url"], "request_url": row["url"], "resolved_url": row["url"],
        "retrieved_at": "2026-10-19T10:00:00Z", "source_content_type": "interactive HTML route (metadata only)",
        "source_bytes": None, "source_sha256": None, "raw_path": None,
        "source_text_path": doc_rel, "candidate_text_path": doc_rel,
        "content_selector": row["content_selector"], "conversion_rule_version": "form-service-route-metadata-v1",
        "accepted": True, "retrieval_status": "accepted_source", "review_state": "accepted",
        "retrieval_note": "Session HTML deliberately excluded because it contained transient state; persistent official route metadata and parent-page evidence retained."
    })
    ledger_rows[source_id] = cap


# Reconcile ledger in manifest order and keep every source ID represented.
manifest_ids = {row["id"] for row in manifest["documents"]}
ledger["records"] = [ledger_rows[row["id"]] for row in manifest["documents"]]
ledger["record_count"] = len(ledger["records"])
ledger["accepted_source_count"] = sum(1 for row in manifest["documents"] if row.get("accepted"))
ledger["linked_pdf_not_captured_count"] = 0
ledger["native_pdf_source_count"] = sum(1 for row in manifest["documents"] if row.get("native_source_path"))
ledger["native_pdf_review_candidate_count"] = sum(1 for row in manifest["documents"] if row.get("native_source_path") and not row.get("accepted"))
ledger["raw_capture_location"] = "captures/2026-10-19; all persistent raw page/PDF captures are content-hashed and linked in this ledger. Interactive Form Service session-state responses are intentionally excluded; their official route metadata is retained instead."
ledger["raw_captures_tracked_for_replay"] = True
ledger["semantic_replayed_legacy_ids"] = sorted(set(ledger.get("semantic_replayed_legacy_ids", [])))

manifest["official_hosts"] = sorted(set(manifest.get("official_hosts", [])) | {
    "bmi.gv.at", "www.bmi.gv.at", "www.formularservice.gv.at", "www.oesterreich.gv.at", "volksanwaltschaft.gv.at"
})
manifest["accepted_source_count"] = sum(1 for row in manifest["documents"] if row.get("accepted"))
manifest["candidate_source_count"] = sum(1 for row in manifest["documents"] if row.get("retrieved") and not row.get("accepted") and row.get("review_state") != "discovery_only")
manifest["located_not_captured_count"] = sum(1 for row in manifest["documents"] if not row.get("retrieved"))
manifest["discovery_only_count"] = sum(1 for row in manifest["documents"] if row.get("review_state") == "discovery_only")
manifest["total_source_record_count"] = len(manifest["documents"])
manifest["retrieved_review_candidate_count"] = manifest["candidate_source_count"]
manifest["converted_review_candidate_count"] = sum(
    1 for row in manifest["documents"]
    if row.get("retrieved") and not row.get("accepted") and row.get("review_state") != "discovery_only"
    and row.get("source_text_path") and not row.get("native_source_path")
    and row.get("source_type") != "official_form"
)
manifest["native_pdf_source_count"] = sum(1 for row in manifest["documents"] if row.get("native_source_path"))
manifest["native_pdf_review_candidate_count"] = sum(1 for row in manifest["documents"] if row.get("native_source_path") and not row.get("accepted"))
manifest["status"] = "source_acceptance_complete_country_coverage_incomplete" if manifest["candidate_source_count"] == 0 else "source_acceptance_in_progress_country_coverage_incomplete"
manifest["retrieval_status"] = f"{manifest['accepted_source_count']} accepted; {manifest['candidate_source_count']} captured and pending review; {manifest['discovery_only_count']} discovery-only; {manifest['located_not_captured_count']} located but not captured"
manifest["source_rules_file"] = "references/source-rules.json"
manifest["source_acceptance_register"] = "references/source-acceptance.json"
manifest["case_review_register"] = "references/case-review-register.json"
ledger["converted_review_candidate_count"] = manifest["converted_review_candidate_count"]
acceptance["updated"] = "2026-10-19"
case_register["reviewed_at"] = "2026-10-19"
case_register["scope_note"] = "Eleven selected official decision records have individual holding, outcome, procedural posture, applicability, and limitation notes. This selection is not a comprehensive case-law survey; RIS discovery batches remain open."
case_register["cases"] = sorted(case_register["cases"], key=lambda row: (row.get("decision_date", ""), row.get("source_id", "")))

# The two interactive routes are governed by a metadata-only route rule.
rule_rows = {row["id"]: row for row in rules["rules"]}
form_rule = rule_rows.get("official-form-link-v1")
if form_rule:
    form_rule["source_ids"] = sorted(set(form_rule.get("source_ids", [])) - set(route_docs))
    form_rule["conversion"]["selector"] = "Retain the native linked PDF and extracted text for review; route metadata is recorded under a separate rule."
new_rule_rows = [
    {
        "id": "official-bmi-forms-v1", "applies_to": "BMI English application form A and its supporting-document explanation PDF",
        "source_ids": ["at-bmi-eea-documentation-form", "at-bmi-eea-documentation-form-explanation"],
        "retrieval": "Start from the current official BMI application-form page; follow its English A-form and explanation links; record edition/date, resolved PDF URL, bytes, and SHA-256.",
        "conversion": {"method": "retain native PDF and extract text page by page", "selector": "native PDF text on every page", "review": "check page count, headings, form choices, family-member requirements, and attachment links against the retained PDF"},
        "sustainability": {"verdict": "sustainable_with_limits", "limits": "BMI may replace direct PDF paths; resolve from the official index at each refresh. PDF text extraction does not replace visual layout review."}
    },
    {
        "id": "official-submission-route-v1", "applies_to": "Interactive official complaint/submission routes whose HTML includes ephemeral session state",
        "source_ids": sorted(route_docs),
        "retrieval": "Follow a verified official parent-page link and record the exact route, route title, initial capability, checked date, and authentication choices. Never submit; do not retain ViewState, event-validation, cookies, or session tokens.",
        "conversion": {"method": "metadata-only route record", "selector": "official parent-page link and live route title/capabilities", "review": "preserve route identity and bounded initial-screen scope; record that downstream interactive pages were not inspected"},
        "sustainability": {"verdict": "sustainable_with_limits", "limits": "Session pages cannot be replayed deterministically. Re-resolve the official route manually; no submission, authentication, or personal-data entry is automated."}
    }
]
for new_rule in new_rule_rows:
    rules["rules"] = [row for row in rules["rules"] if row.get("id") != new_rule["id"]]
    rules["rules"].append(new_rule)
rules["updated"] = "2026-10-19"
rules["policy"]["scope"] = "The 74-record manifest contains 73 accepted sources, no captured pending-review sources, and one discovery-only index. It is a bounded inventory, not an exhaustive country review. The fixed monitor checks registered records; separate manual discovery plans address missing cases, missions, and Länder practice."
rules["monitor"]["scope"] = "Only fixed records in references/candidate-manifest.json; no broad RIS search, mission-page discovery, or Land-practice discovery. Separate discover and discover-operations actions create repeatable manual research queues; they do not run searches or accept sources."
rules["monitor"]["activation"] = "The workflow file and monthly schedule are present in eudirective/public-data. On 2026-10-19, the GitHub run-list query could not connect to api.github.com; successful execution and Actions enablement therefore remain unverified. Do not describe scheduled monitoring as operational until a successful run is recorded."

write(MANIFEST_PATH, manifest)
write(LEDGER_PATH, ledger)
write(ACCEPTANCE_PATH, acceptance)
write(CASE_REVIEW_PATH, case_register)
write(RULES_PATH, rules)

# Remove only the obsolete/non-replayable or superseded capture files identified in this review.
for pattern in [
    "at-dsb-online-complaint-form-*.html",
    "at-volksanwaltschaft-online-complaint-form-*.html",
    "at-vwgh-ra-2023-22-0090-0091-*.html",
]:
    for stale in CAPTURES.glob(pattern):
        stale.unlink()

print(json.dumps({
    "source_count": len(manifest["documents"]), "accepted": manifest["accepted_source_count"],
    "captured_pending": manifest["candidate_source_count"], "discovery_only": manifest["discovery_only_count"],
    "located_not_captured": manifest["located_not_captured_count"], "case_reviews": len(case_register["cases"]),
    "capture_ledger_rows": len(ledger["records"]), "source_rule_ids": [r["id"] for r in rules["rules"]]
}, ensure_ascii=False, indent=2))
