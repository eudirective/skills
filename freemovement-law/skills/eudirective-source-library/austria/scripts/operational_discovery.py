#!/usr/bin/env python3
"""Build and validate manual discovery queues for Austria's Länder and missions.

This tool never makes network requests. It turns the captured BMEIA directory
and recorded official leads into a stable research queue, then checks that every
known mission and each of the nine Länder has a review record.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

PACK = Path(__file__).resolve().parents[1]
REFERENCES = PACK / "references"
DIRECTORY = REFERENCES / "bmeia-representation-records.json"
QUEUE = REFERENCES / "operational-discovery.json"
ACCEPTANCE = REFERENCES / "source-acceptance.json"
LANDS = [
    "Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich", "Salzburg",
    "Steiermark", "Tirol", "Vorarlberg", "Wien"
]
OPEN_STATUS = {"not_started", "partial_review", "source_lead_only", "in_progress"}
RESOLVED_STATUS = {"reviewed_and_accepted", "not_applicable_with_evidence", "no_source_found_after_recorded_search"}
REGIONAL_REQUIRED_FIELDS = (
    "competent_authority", "territorial_jurisdiction", "current_form",
    "supporting_document_checklist", "appointment_route", "submission_route",
    "family_member_specific_rules", "checked_on",
)
MISSION_REQUIRED_FIELDS = (
    "mission_visa_instructions", "eu_family_member_route", "appointment_route",
    "current_checklists_and_forms", "outsourcing_or_representation",
    "decision_authority", "residence_scope", "checked_on",
)

REGIONAL_SEEDS = {
    "Burgenland": {
        "status": "source_lead_only", "sources": [
            {"url": "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=LrBgld&Anlage=&Artikel=&FassungVom=2026-08-22&Gesetzesnummer=20000368&Paragraf=1&Uebergangsrecht=", "title": "Angelegenheiten des Niederlassungs- und Aufenthaltsgesetzes § 1", "source_state": "official_legal_lead_requires_validation", "evidence": "RIS page is consolidated to 22 August 2026 but reports its last update as 22 September 2011. It delegates first-instance Landeshauptmann decisions involving Aufenthaltstitel and lists registration certificates under NAG §53 and Daueraufenthaltskarten under §54. Current NAG places Daueraufenthaltskarten under §54a and Aufenthaltskarten under §54; the delegated-document list therefore has a material stale cross-reference and does not establish the current ordinary residence-card route."},
            {"url": "https://www.burgenland.at/verwaltung/bezirksverwaltungsbehoerden/", "title": "Bezirksverwaltungsbehörden — Land Burgenland", "source_state": "official_authority_directory_lead", "evidence": "Official directory lists seven political districts and two Freistädte and links to the responsible district authorities; it does not give a residence-card procedure."}
        ],
        "searches_recorded": ["Official Burgenland RIS §1 delegation ordinance inspected (consolidated 22 August 2026; last update 22 September 2011)", "Official Burgenland district-authority directory inspected", "site:bgld.gv.at Aufenthaltskarte Angehörige EWR Bürger Niederlassungsbehörde", "site:burgenland.at Aufenthaltskarte EWR Angehörige Antrag Termin Formular", "site:bgld.gv.at \"Aufenthaltskarte\" EWR Angehörige", "site:burgenland.at \"Aufenthaltskarte\" EWR Angehörige Niederlassung"],
        "note": "Official authority and delegation leads located, but no current card-specific practice page. Treat the RIS delegation text as historically cross-referenced: current NAG numbering assigns the regular residence card to §54 and the permanent card to §54a, while the Burgenland list names the permanent card under §54. Reconcile the delegation scope before asserting the competent route; identify form, appointment and checklist."
    },
    "Kärnten": {
        "status": "source_lead_only", "sources": [
            {"url": "https://www.ktn.gv.at/Verwaltung/Bezirke", "title": "Bezirke — Kärntner Bezirke", "source_state": "official_authority_directory_lead", "evidence": "Official Land page links the eight Bezirkshauptmannschaften; the page is an authority directory, not a residence-card procedure, and the statutory-city routes need separate confirmation."},
            {"url": "https://www.ktn.gv.at/DE/repos/files/ktn.gv.at/Abteilungen/Abt4/Dateien/Sozialratgeber/Sozialratgeber_2025%20.pdf?exp=1629719&fps=5bbeae54187e4b8f00aca890f01c9a2a1c4b8414", "title": "Sozialratgeber Kärnten 2025", "source_state": "official_contextual_lead_not_procedure", "checked_on": "2026-10-19", "evidence": "Official guide mentions an Aufenthaltskarte/Daueraufenthaltskarte as residence evidence and directs readers to the BH or Magistrat with territorial responsibility. It does not explain application procedure, forms, checklist or appointment booking."}
        ],
        "searches_recorded": ["Official Kärnten district directory inspected", "site:ktn.gv.at Aufenthaltskarte EWR Angehörige Niederlassung Termin", "site:ktn.gv.at Aufenthaltskarte Angehörige EWR Antrag Aufenthaltstitel Termin", "site:ktn.gv.at \"Aufenthaltskarte\" Angehörige EWR"],
        "note": "Official district-authority directory lead located. No current card-specific route, competent desk, current form, appointment rule or family checklist has yet been verified; account separately for Klagenfurt and Villach statutory cities."
    },
    "Niederösterreich": {
        "status": "partial_review", "sources": [
            {"url": "https://www.noe.gv.at/noe/Zustaendigkeit_BVB.html", "title": "Zuständigkeit der Bezirksverwaltungsbehörden", "source_state": "official_lead", "evidence": "Identifies the local BH or Magistrat as the authority for EU residence documentation; directs applicants to contact the local authority for documents. Page date shown as 12 May 2021."},
            {"url": "https://noe.gv.at/noe/Neunkirchen/Bezirkshauptmannschaft_Neunkirchen.html", "title": "BH Neunkirchen — contact, appointments and residence-law hours", "source_state": "official_live_local_authority_lead_not_yet_captured_or_accepted", "checked_on": "2026-10-19", "evidence": "Official page updated 16 September 2026. Recommends appointment booking by email, phone or selected online services; gives a residence-law service window, accepts electronic submissions, and specifies the valid office email route. It is not a family-card checklist and does not establish province-wide practice."}
        ], "searches_recorded": ["Official Land authority page reviewed", "site:noe.gv.at Aufenthaltskarte Angehörige EU Bürger Antrag Formular Termin"],
        "note": "Competent-authority route is partly identified; current local checklist, form and appointment rules remain open."
    },
    "Oberösterreich": {
        "status": "partial_review", "sources": [
            {"url": "https://www.land-oberoesterreich.gv.at/51939.htm", "title": "Bezirkshauptmannschaft Perg — EEA/Swiss residence documentation", "source_state": "official_lead", "evidence": "Specific EEA/Swiss and family documentation information; directs applicants to staff for the individual supporting-document list."},
            {"url": "https://www.land-oberoesterreich.gv.at/553513.htm", "title": "BH Linz-Land — Migration and residence", "source_state": "official_live_page_lead_not_yet_captured_or_accepted", "checked_on": "2026-10-19", "evidence": "Official local page lists EEA-family matters, personal application, form and supporting documents; appointment is recommended and office/customer hours are given. The page's form shows a July 2025 status. This is one district, not proof of uniform provincial practice."}
        ], "searches_recorded": ["Official BH Perg EEA-family information page reviewed"],
        "note": "One district lead is identified; it does not establish a uniform nine-district practice or a complete appointment/form/checklist route."
    },
    "Salzburg": {
        "status": "partial_review", "sources": [
            {"url": "https://www.salzburg.gv.at/dienststellen/bezirke/bh-stjohann/niederlassungs-und-aufenthaltsrecht", "title": "BH St Johann — Niederlassungs- und Aufenthaltsrecht", "source_state": "official_lead", "evidence": "Includes EEA/family residence-card matters and states that appointments are required; authority-specific checklist and territorial coverage still need reconciliation."},
            {"url": "https://www.salzburg.gv.at/dienststellen/bezirke/bh-zellamsee/aufenthaltstitel", "title": "BH Zell am See — Aufenthaltstitel", "source_state": "official_live_page_lead_not_yet_captured_or_accepted", "checked_on": "2026-10-19", "evidence": "Official page identifies an online appointment route for EU residence documents, says authority processing is exclusively by appointment and explains originals/copies and grouped appointment slots. It lists Aufenthaltskarte, but a card-specific checklist still needs capture."},
            {"url": "https://www.salzburg.gv.at/dienststellen/bezirke/bh-hallein/aufenthaltstitel", "title": "BH Hallein — Aufenthaltstitel", "source_state": "official_live_page_lead_not_yet_captured_or_accepted", "checked_on": "2026-10-19", "evidence": "Official residence page identified; extract the EEA-family route, appointment rule, checklist and territorial scope before treating it as a resolved procedure."},
            {"url": "https://www.salzburg.gv.at/dienststellen/bezirke/bh-su/bhsu-aufenthaltstitel", "title": "BH Salzburg-Umgebung — Aufenthaltstitel", "source_state": "official_live_page_lead_not_yet_captured_or_accepted", "checked_on": "2026-10-19", "evidence": "Official residence page identified; extract the EEA-family route, appointment rule, checklist and territorial scope before treating it as a resolved procedure."}
        ], "searches_recorded": ["Official BH St Johann residence-law page reviewed"],
        "note": "One district procedure is identified; province-wide authority, current forms, and full family-card checklist remain open."
    },
    "Steiermark": {
        "status": "partial_review", "sources": [
            {"url": "https://www.verwaltung.steiermark.at/cms/beitrag/13019904/127384147/", "title": "Aufenthaltskarte for EEA-family members", "source_state": "official_lead", "evidence": "Describes personal filing and main-residence authority, identifies Graz as a separate route, and links to appointment information."},
            {"url": "https://www.e-government.steiermark.at/cms/beitrag/13020826/95327281/", "title": "Aufenthaltskarte — Styrian e-government procedure", "source_state": "official_live_page_lead_not_yet_captured_or_accepted", "checked_on": "2026-10-19", "evidence": "Official procedure page says applications are personal, identifies the main-residence authority and the distinct Graz route, links the BMI form and checklist, and was updated 30 December 2025. Exact current authority and appointment route still need local validation."}
        ], "searches_recorded": ["Official Styrian residence-card procedure reviewed"],
        "note": "A detailed route is identified; preserve the exact current checklist/form and verify all district and Graz practice."
    },
    "Tirol": {
        "status": "partial_review", "sources": [
            {"url": "https://www.tirol.gv.at/innsbruck/fw-aufenthalt-ewr/", "title": "Tirol — Aufenthalt EWR", "source_state": "official_lead", "evidence": "Official Land page identified as the residence/EWR practice entry point; card-specific appointment, form, and checklist details still need extraction and review."},
            {"url": "https://www.tirol.gv.at/fileadmin/themen/gesellschaft-soziales/diversitaet/TFA/TFA_2024/tirol-fuer-angekommene-de-2024.pdf", "title": "Tirol für Angekommene 2024", "source_state": "official_historical_guidance_lead", "checked_on": "2026-10-19", "evidence": "Official newcomer guide describes residence-card categories but is dated 2024 and does not establish current application practice."},
            {"url": "https://www.tirol.gv.at/fileadmin/themen/gesellschaft-soziales/staatsbuergerschaft/downloads/Informationsblatt_fuer_EWR-BuergerInnen_Deutsch.pdf", "title": "Information sheet for EEA and Swiss citizens and family members", "source_state": "official_historical_guidance_lead", "checked_on": "2026-10-19", "evidence": "Official October 2019 leaflet names the four-month registration/card deadline and directs applicants to the residence-based BH/Magistrat for document requirements. It is historical and does not establish current forms or appointment conditions."}
        ], "searches_recorded": ["Official Tirol EWR residence page identified", "site:tirol.gv.at Aufenthaltskarte EWR Drittstaatsangehörige Karte Antrag Unterlagen"],
        "note": "Lead only; current card-specific authority and application instructions have not been fully reviewed."
    },
    "Vorarlberg": {
        "status": "source_lead_only", "sources": [
            {"url": "https://vorarlberg.at/documents/302033/24301244/Antragsformular%2BAnmeldebescheinigung.pdf/efd0845c-d399-0cd0-7bfb-eb750bf0fe85?t=1683871642328", "title": "Antragsformular Anmeldebescheinigung", "source_state": "historical_form_lead", "checked_on": "2026-10-19", "evidence": "Official combined NAG form explicitly includes the Aufenthaltskarte and Daueraufenthaltskarte options. It is marked NAG Formular 10/2018; currentness, any successor form and current local procedure are unverified."}
        ], "searches_recorded": ["Official Vorarlberg application form lead identified", "site:vorarlberg.at Aufenthaltskarte Angehörige EWR Bürger Antrag Formular Termin"],
        "note": "Do not use the old form as current practice without a current page or direct confirmation."
    },
    "Wien": {
        "status": "partial_review", "sources": [
            {"url": "https://www.wien.gv.at/amtswege/aufenthaltskarte-angehoerige", "title": "Aufenthaltskarte und Daueraufenthaltskarte für Angehörige", "source_state": "official_lead", "evidence": "Requires personal application within four months; Vienna residence registration first; appointment with the EWR section responsible for the applicant's district."}
        ], "searches_recorded": ["Official Vienna card procedure page reviewed"],
        "note": "Card-specific route and appointment system identified; capture the source and verify its checklist, forms, and current district assignment."
    }
}

MISSION_SEEDS = {
    "country-197-0524": {
        "status": "partial_review", "page_urls": ["https://www.bmeia.gv.at/en/austrian-embassy-nicosia/travels-to-austria/entrance-and-residence/how-to-apply"],
        "observed": "EEA/Swiss family members travelling with or joining the citizen are described as visa-exempt; close EU-family appointments can be arranged by phone/email; general C visas are outsourced to VFS; the Embassy continues to decide applications.",
        "open_fields": ["current family-member checklist", "document-specific checklist and versions", "route by applicant residence/nationality"]
    },
    "country-169-0415": {
        "status": "partial_review", "page_urls": ["https://www.bmeia.gv.at/en/austrian-embassy-pretoria/travels-to-austria/entrance-and-residence/how-to-apply/"],
        "observed": "Official mission page publishes visa instructions, an EU/EEA-family C-visa checklist, appointment-system information, and forms.",
        "open_fields": ["family-member route details and fee exemptions", "outsourcing and representation scope", "checklist edition/version", "applicant residence boundaries"]
    },
    "country-200-0023": {
        "status": "partial_review", "page_urls": ["https://www.bmeia.gv.at/en/austrian-embassy-addis-abeba/travel-to-austria/entrance-and-residence/how-to-apply"],
        "observed": "Official mission page identifies visa submission through VFS and appointment rules, with additional submission routes in some countries covered by the Embassy.",
        "open_fields": ["EU-family-specific appointment and checklist rules", "outsourcing/representation by each covered country", "current forms and fees", "route by applicant residence/nationality"]
    }
    ,"country-62-0174": {
        "status": "partial_review", "page_urls": ["https://www.bmeia.gv.at/en/austrian-embassy-jakarta/your-travel-to-austria/entrance-and-residence/how-to-apply"],
        "observed": "Official mission page is a current lead for EEA/Swiss family travel and local visa submission instructions; appointment, checklist version and outsourcing details still need field-by-field capture.",
        "open_fields": ["family-member route and fee exemptions", "appointment route", "current checklists and forms", "outsourcing or representation", "applicant residence boundaries"]
    },
    "country-53-0479": {
        "status": "partial_review", "page_urls": ["https://www.bmeia.gv.at/en/austrian-embassy-london/travelling-to-austria/entry-requirements-visa-and-immigration/schengen-visa-application-requirements/"],
        "observed": "Official mission page is a current lead for accelerated processing and limited supporting documents for EU/EEA/Swiss family members, with a London-specific VFS and Embassy appointment route.",
        "open_fields": ["family-specific checklist and fee rules", "appointment availability and booking route", "current outsourcing scope", "UK residence and consular-district boundaries"]
    }
}

SHARED_SOURCE_LEADS = [
    {
        "url": "https://www.oesterreich.gv.at/de/themen/menschen_aus_anderen_staaten/aufenthalt/1/Seite.120830",
        "title": "Federal procedure: Aufenthaltskarte and Daueraufenthaltskarte",
        "publisher": "oesterreich.gv.at / BMI",
        "source_state": "official_live_page_lead_not_yet_captured_or_accepted",
        "checked_on": "2026-10-19",
        "observed": "Updated 10 August 2026. Identifies competent local Niederlassungsbehörde, personal filing, four-month initial deadline, online/phone/email appointment differences, federal form download, and family-document checklist. It names BH/Magistrat, with MA35 in Vienna and Styrian Government Office in Graz; it does not resolve every local Land route."
    },
    {
        "url": "https://www.bmeia.gv.at/en/entry-and-residence/visa",
        "title": "Federal visa information",
        "publisher": "BMEIA",
        "source_state": "official_live_page_lead_not_yet_captured_or_accepted",
        "checked_on": "2026-10-19",
        "observed": "Central visa entry point for national/Schengen visa categories and EEA/Swiss family-member treatment; does not replace mission-specific instructions."
    }
]

DISCOVERY_LOG = [
    {
        "checked_on": "2026-10-19",
        "method": "web search for official sources; result counts were not exposed by the search interface",
        "queries": [
            "site:ris.bka.gv.at NAG Aufenthaltskarte Landesverwaltungsgericht 2025 VwGH FPG Österreich",
            "site:ris.bka.gv.at \"Aufenthaltskarte\" \"LVwG\" 2025 OR 2026",
            "site:oesterreich.gv.at Aufenthaltskarte EU Bürger Angehörige Antrag Behörde Unterlagen",
            "site:oesterreich.gv.at Niederlassungsbehörde Aufenthaltskarte Länder Österreich"
        ],
        "result_count": None,
        "result_count_note": "Not exposed by the search interface; this is a lead search, not one of the 55 RIS-form tasks.",
        "official_leads": [
            "https://www.oesterreich.gv.at/de/themen/menschen_aus_anderen_staaten/aufenthalt/1/Seite.120830",
            "https://ris.bka.gv.at/Dokumente/Vwgh/JWT_2025180038_20251009L00/JWT_2025180038_20251009L00.html",
            "https://ris.bka.gv.at/Dokumente/Vwgh/JWT_2025220052_20251212L00/JWT_2025220052_20251212L00.html",
            "https://ris.bka.gv.at/Dokumente/Lvwg/LVWGT_NI_20260910_LVwG_AV_1203_001_2025_00/LVWGT_NI_20260910_LVwG_AV_1203_001_2025_00.html"
        ]
    },
    {
        "checked_on": "2026-10-19",
        "method": "Official-domain web searches for Land-level family-card procedures; search result counts were not exposed",
        "queries": [
            "site:burgenland.at Aufenthaltskarte EWR Angehörige Antrag Termin Formular",
            "site:ktn.gv.at Aufenthaltskarte Angehörige EWR Antrag Aufenthaltstitel Termin",
            "site:noe.gv.at Aufenthaltskarte Angehörige EU Bürger Antrag Formular Termin",
            "site:vorarlberg.at Aufenthaltskarte Angehörige EWR Bürger Antrag Formular Termin",
            "site:tirol.gv.at Aufenthaltskarte EWR Drittstaatsangehörige Karte Antrag Unterlagen",
            "site:bgld.gv.at \"Aufenthaltskarte\" EWR Angehörige",
            "site:burgenland.at \"Aufenthaltskarte\" EWR Angehörige Niederlassung",
            "site:ktn.gv.at \"Aufenthaltskarte\" Angehörige EWR"
        ],
        "result_count": None,
        "result_count_note": "Not exposed by the search interface. This is lead discovery, not a complete publisher search or task closure.",
        "screened_results": [
            {"url": "https://noe.gv.at/noe/Neunkirchen/Bezirkshauptmannschaft_Neunkirchen.html", "disposition": "relevant_lead", "reason": "Current local authority contact and appointment route; not card-specific."},
            {"url": "https://www.tirol.gv.at/fileadmin/themen/gesellschaft-soziales/staatsbuergerschaft/downloads/Informationsblatt_fuer_EWR-BuergerInnen_Deutsch.pdf", "disposition": "historical_lead", "reason": "October 2019 leaflet names residence-card timing and local authority; current local steps still need verification."},
            {"url": "https://www.ktn.gv.at/DE/repos/files/ktn.gv.at/Abteilungen/Abt4/Dateien/Sozialratgeber/Sozialratgeber_2025%20.pdf?exp=1629719&fps=5bbeae54187e4b8f00aca890f01c9a2a1c4b8414", "disposition": "contextual_lead", "reason": "Official guide mentions a residence card as a status document and points to local authorities but gives no application practice."},
            {"url": "https://www.burgenland.at/fileadmin/user_upload/Downloads/Abt._2/2024/Antragsformular.pdf", "disposition": "not_relevant", "reason": "Opened PDF is a citizenship application form, not an EU-family residence-card source; exclude it from the source inventory."},
            {"url": "https://vorarlberg.at/documents/302033/24301244/Antragsformular%2BAnmeldebescheinigung.pdf/efd0845c-d399-0cd0-7bfb-eb750bf0fe85?t=1683871642328", "disposition": "historical_form_lead", "reason": "Official NAG form explicitly has an Aufenthaltskarte checkbox but is marked NAG Formular 10/2018; currentness remains unverified."}
        ]
    }
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def initialize() -> dict:
    directory = read_json(DIRECTORY)
    existing = read_json(QUEUE) if QUEUE.exists() else {}
    old_regions = {row["land"]: row for row in existing.get("regional_tasks", [])}
    old_missions = {row["source_record_id"]: row for row in existing.get("mission_tasks", [])}
    regions = []
    for land in LANDS:
        seed = REGIONAL_SEEDS[land]
        prior = old_regions.get(land, {})
        sources_by_url = {row["url"]: row for row in seed["sources"]}
        sources_by_url.update({row["url"]: row for row in prior.get("sources", []) if row.get("url")})
        regions.append({
            "land": land,
            "status": seed["status"] if prior.get("status") in (None, "not_started") else prior["status"],
            "required_fields": list(REGIONAL_REQUIRED_FIELDS),
            "sources": list(sources_by_url.values()),
            "searches_recorded": list(dict.fromkeys(seed["searches_recorded"] + prior.get("searches_recorded", []))),
            "note": prior.get("note") or seed["note"],
            "review": prior.get("review", {})
        })
    missions = []
    for row in directory.get("representations", []):
        old = old_missions.get(row["source_record_id"], {})
        seed = MISSION_SEEDS.get(row["source_record_id"], {})
        page_urls = list(dict.fromkeys(seed.get("page_urls", []) + old.get("page_urls", [])))
        missions.append({
            "source_record_id": row["source_record_id"],
            "country_id": row["country_id"],
            "country": row.get("country", {}).get("name", ""),
            "mission": row.get("title", ""),
            "category": row.get("category", ""),
            "directory_links": row.get("links", []),
            "status": seed.get("status", "not_started") if old.get("status") in (None, "not_started") else old["status"],
            "page_urls": page_urls,
            "required_fields": list(MISSION_REQUIRED_FIELDS),
            "observed": old.get("observed") or seed.get("observed", ""),
            "open_fields": old.get("open_fields") or seed.get("open_fields", ["all required fields"]),
            "review": old.get("review", {})
        })
    prior_leads = {row.get("source_record_id"): row for row in existing.get("mission_page_leads", [])}
    mission_page_leads = [
        {"source_record_id": key, **value, "evidence_state": "official_live_page_lead_not_yet_captured_or_accepted"}
        for key, value in MISSION_SEEDS.items()
    ]
    seeded_ids = {row["source_record_id"] for row in mission_page_leads}
    mission_page_leads.extend(row for key, row in prior_leads.items() if key not in seeded_ids)
    shared_by_url = {row["url"]: row for row in SHARED_SOURCE_LEADS}
    shared_by_url.update({row["url"]: row for row in existing.get("shared_source_leads", []) if row.get("url")})
    discovery_log = list(existing.get("discovery_log", []))
    for row in DISCOVERY_LOG:
        if row not in discovery_log:
            discovery_log.append(row)
    queue = {
        "schema_version": "1.0.0", "jurisdiction": "AT", "updated": "2026-10-19",
        "purpose": "Issue-led discovery for provincial residence-card practice and mission-specific visa operations. This queue is separate from the fixed source monitor; a directory listing is not a reviewed consular instruction.",
        "regional_task_count": len(regions), "mission_task_count": len(missions),
        "mission_directory_source": "references/bmeia-representation-records.json",
        "mission_directory_as_of": directory.get("directory_as_of"),
        "mission_page_leads": mission_page_leads,
        "shared_source_leads": list(shared_by_url.values()),
        "discovery_log": discovery_log,
        "regional_tasks": regions,
        "mission_tasks": missions,
        "completion_rule": "Each Land and each representation must end in reviewed_and_accepted or not_applicable_with_evidence/no_source_found_after_recorded_search. Every required field must be an evidence object with status, value/reason, and source URL or accepted source ID plus checked_on; no-source claims also require exact queries, search scope, search date, numeric result count, and screened results."
    }
    write_json(QUEUE, queue)
    return queue


def summarize(queue: dict, *, full: bool) -> dict:
    regional_counts = Counter(row["status"] for row in queue.get("regional_tasks", []))
    mission_counts = Counter(row["status"] for row in queue.get("mission_tasks", []))
    report = {
        "queue_file": "references/operational-discovery.json",
        "regional_tasks": {"total": len(queue.get("regional_tasks", [])), "by_status": dict(sorted(regional_counts.items())), "open": sum(regional_counts[s] for s in OPEN_STATUS if s in regional_counts)},
        "mission_tasks": {"total": len(queue.get("mission_tasks", [])), "by_status": dict(sorted(mission_counts.items())), "open": sum(mission_counts[s] for s in OPEN_STATUS if s in mission_counts)},
        "mission_page_leads": len(queue.get("mission_page_leads", [])),
        "discovery_complete": all(row.get("status") in RESOLVED_STATUS for row in queue.get("regional_tasks", [])) and all(row.get("status") in RESOLVED_STATUS for row in queue.get("mission_tasks", [])),
        "automation_scope": "queue generation and structural validation only; no web searches or form submissions"
    }
    if full:
        report["regional_tasks_full"] = queue.get("regional_tasks", [])
        report["mission_tasks_full"] = queue.get("mission_tasks", [])
    return report


def validate(queue: dict) -> dict:
    directory = read_json(DIRECTORY)
    accepted_source_ids = {
        source_id for source_id, row in read_json(ACCEPTANCE).get("records", {}).items()
        if row.get("status") == "accepted"
    }
    expected_ids = {row["source_record_id"] for row in directory.get("representations", [])}
    actual_ids = [row.get("source_record_id") for row in queue.get("mission_tasks", [])]
    actual_set = set(actual_ids)
    lands = [row.get("land") for row in queue.get("regional_tasks", [])]
    errors = []
    if len(lands) != 9 or set(lands) != set(LANDS):
        errors.append("regional task register must contain each Austrian Land exactly once")
    if len(actual_ids) != len(actual_set):
        errors.append("mission task register has duplicate representation IDs")
    if actual_set != expected_ids:
        errors.append(f"mission task IDs do not reconcile to BMEIA directory (missing={len(expected_ids-actual_set)}, extra={len(actual_set-expected_ids)})")
    missing_fields = []
    evidence_errors = []

    def valid_date(value: object) -> bool:
        if not isinstance(value, str):
            return False
        try:
            from datetime import date
            date.fromisoformat(value)
            return True
        except ValueError:
            return False

    def check_search_provenance(task_key: str, field: str, review: dict) -> None:
        provenance = review.get("search_provenance")
        if not isinstance(provenance, dict):
            evidence_errors.append(f"{task_key}:{field}:missing_search_provenance")
            return
        if not isinstance(provenance.get("queries"), list) or not provenance["queries"] or not all(isinstance(q, str) and q.strip() for q in provenance["queries"]):
            evidence_errors.append(f"{task_key}:{field}:missing_exact_queries")
        if not provenance.get("searched_scope"):
            evidence_errors.append(f"{task_key}:{field}:missing_searched_scope")
        if not valid_date(provenance.get("checked_on")):
            evidence_errors.append(f"{task_key}:{field}:invalid_search_date")
        if type(provenance.get("result_count")) is not int or provenance["result_count"] < 0:
            evidence_errors.append(f"{task_key}:{field}:result_count_must_be_numeric")
        results = provenance.get("screened_results")
        if not isinstance(results, list):
            evidence_errors.append(f"{task_key}:{field}:missing_screened_results")
        elif type(provenance.get("result_count")) is int and len(results) != provenance["result_count"]:
            evidence_errors.append(f"{task_key}:{field}:not_all_search_results_screened")
        else:
            for result in results:
                if not isinstance(result, dict) or not result.get("url") or result.get("disposition") not in {"relevant", "not_relevant", "unavailable"} or not result.get("reason"):
                    evidence_errors.append(f"{task_key}:{field}:incomplete_screened_result")

    def check_evidence_refs(task_key: str, field: str, refs: object) -> None:
        if not isinstance(refs, list) or not refs:
            evidence_errors.append(f"{task_key}:{field}:evidence_missing")
            return
        for ref in refs:
            if not isinstance(ref, dict) or not valid_date(ref.get("checked_on")):
                evidence_errors.append(f"{task_key}:{field}:evidence_needs_checked_on")
                continue
            url = ref.get("url")
            source_id = ref.get("source_id")
            if source_id and source_id not in accepted_source_ids:
                evidence_errors.append(f"{task_key}:{field}:source_id_not_accepted")
                continue
            if not source_id and not (isinstance(url, str) and urlparse(url).scheme == "https"):
                evidence_errors.append(f"{task_key}:{field}:evidence_needs_https_url_or_accepted_source_id")
                continue
            if url:
                host = urlparse(url).hostname or ""
                if not (host.endswith(".gv.at") or host == "gv.at"):
                    evidence_errors.append(f"{task_key}:{field}:evidence_url_not_an_official_austrian_publisher")

    def check_field(task_key: str, field: str, item: object, row: dict) -> None:
        if not isinstance(item, dict):
            missing_fields.append(f"{task_key}:{field}")
            return
        state = item.get("status")
        if state == "verified":
            if item.get("value") in (None, "", [], {}):
                evidence_errors.append(f"{task_key}:{field}:verified_value_missing")
            check_evidence_refs(task_key, field, item.get("evidence"))
        elif state == "not_applicable":
            if not item.get("reason"):
                evidence_errors.append(f"{task_key}:{field}:not_applicable_reason_missing")
            check_evidence_refs(task_key, field, item.get("evidence"))
        elif state == "no_source_found":
            if not item.get("reason"):
                evidence_errors.append(f"{task_key}:{field}:no_source_reason_missing")
            check_search_provenance(task_key, field, item)
        else:
            evidence_errors.append(f"{task_key}:{field}:invalid_review_status")

    for kind, rows, required_fields in (
        ("regional", queue.get("regional_tasks", []), REGIONAL_REQUIRED_FIELDS),
        ("mission", queue.get("mission_tasks", []), MISSION_REQUIRED_FIELDS),
    ):
        for row in rows:
            status = row.get("status")
            if status not in OPEN_STATUS | RESOLVED_STATUS:
                errors.append(f"{kind} task {row.get('land') or row.get('source_record_id')} has invalid status {status!r}")
            declared_fields = row.get("required_fields")
            if not isinstance(declared_fields, list) or len(declared_fields) != len(required_fields) or set(declared_fields) != set(required_fields):
                errors.append(f"{kind} task {row.get('land') or row.get('source_record_id')} does not declare the canonical required fields")
            if status in RESOLVED_STATUS:
                task_key = row.get("land") or row.get("source_record_id")
                for field in required_fields:
                    check_field(f"{kind}:{task_key}", field, row.get("review", {}).get(field), row)
                if status == "no_source_found_after_recorded_search":
                    provenance = row.get("search_provenance")
                    check_search_provenance(f"{kind}:{task_key}", "task", {"search_provenance": provenance})
    report = summarize(queue, full=False)
    report.update({"queue_structure": "pass" if not errors else "fail", "errors": errors, "resolved_tasks_missing_evidence": missing_fields[:50], "resolved_tasks_missing_evidence_count": len(missing_fields), "resolved_tasks_evidence_errors": evidence_errors[:50], "resolved_tasks_evidence_error_count": len(evidence_errors)})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "plan", "validate"))
    parser.add_argument("--full", action="store_true", help="include all regional and mission task records")
    args = parser.parse_args()
    queue = initialize() if args.action == "init" or not QUEUE.exists() else read_json(QUEUE)
    if args.action == "plan":
        print(json.dumps(summarize(queue, full=args.full), ensure_ascii=False, indent=2))
        return 0
    report = validate(queue)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["errors"] or report["resolved_tasks_missing_evidence_count"] or report["resolved_tasks_evidence_error_count"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
