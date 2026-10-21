#!/usr/bin/env python3
"""Validate and render the model-declared consultation dashboard receipt.

This module reuses the bundled source library as a metadata index. It does not
record model reads, authenticate source retrieval, or enforce ChatGPT release.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from source_library_paths import source_library_root


class DashboardError(ValueError):
    pass


READ_STATES = {"consulted", "identified_not_read", "cited_from_memory", "not_referenced"}
READ_PROVENANCE = {"runtime_recorded", "model_declared", "none"}
TRACKING_STATES = {"runtime_recorded", "model_declared", "unavailable"}
CURRENTNESS = {
    "reviewed_current", "reviewed_within_cutoff", "reviewed_historical_scope",
    "unknown", "stale",
}
LIBRARY_STATES = {
    "registered_record", "candidate_unaccepted", "source_note_only",
    "not_recorded", "not_applicable",
}
NON_TEXT_CATEGORIES = {"publisher_portal", "source_note", "other_reference"}
LEGAL_CATEGORIES = {
    "eu_legislation", "national_legislation", "case_law", "commission_guidance",
    "official_guidance", "procedural_rule", "other_legal_text",
}
UNRESOLVED_ISSUES = {"answered_conditionally", "source_missing", "fact_missing"}
OPAQUE_REF = re.compile(r"^r_[a-f0-9]{12,32}$")
SECTION_LABELS = {
    "eu": "EU core", "at": "Austria", "be": "Belgium", "bg": "Bulgaria",
    "ch": "Switzerland", "cy": "Cyprus", "cz": "Czechia", "de": "Germany",
    "dk": "Denmark", "ee": "Estonia", "es": "Spain", "fi": "Finland",
    "fr": "France", "gr": "Greece", "hr": "Croatia", "hu": "Hungary",
    "ie": "Ireland", "is": "Iceland", "it": "Italy", "li": "Liechtenstein",
    "lt": "Lithuania", "lu": "Luxembourg", "lv": "Latvia", "mt": "Malta",
    "nl": "Netherlands", "no": "Norway", "pl": "Poland", "pt": "Portugal",
    "ro": "Romania", "se": "Sweden", "si": "Slovenia", "sk": "Slovakia",
    "tr": "Türkiye",
}
COUNTRY_CODES = {
    "austria": "AT", "belgium": "BE", "bulgaria": "BG", "croatia": "HR",
    "cyprus": "CY", "czechia": "CZ", "denmark": "DK", "estonia": "EE",
    "finland": "FI", "france": "FR", "germany": "DE", "greece": "GR",
    "hungary": "HU", "iceland": "IS", "ireland": "IE", "italy": "IT",
    "latvia": "LV", "liechtenstein": "LI", "lithuania": "LT", "luxembourg": "LU",
    "malta": "MT", "netherlands": "NL", "norway": "NO", "poland": "PL",
    "portugal": "PT", "romania": "RO", "slovakia": "SK", "slovenia": "SI",
    "spain": "ES", "sweden": "SE", "switzerland": "CH", "turkiye": "TR",
}


def _load_catalog() -> dict[str, dict]:
    """Resolve IDs from existing index/manifests; never creates source records."""
    root = source_library_root()
    catalog: dict[str, dict] = {}
    index_path = root / "retrieval-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else []
    for item in index if isinstance(index, list) else []:
        source_id = item.get("source_id")
        if not isinstance(source_id, str):
            continue
        country = source_id.split(":", 1)[0].casefold()
        catalog.setdefault(source_id, {
            "title": item.get("title", ""),
            "section": "EU core" if country == "eu" else SECTION_LABELS.get(country, country.upper()),
            "jurisdiction": "EU" if country == "eu" else COUNTRY_CODES.get(country, country.upper()),
            "source_type": "",
            "official_url": item.get("official_source"),
            "library_state": "candidate_unaccepted"
            if "candidate" in str(item.get("library_content_state", "")) else "not_recorded",
        })

    for manifest_path in sorted(root.glob("core-source-pack-manifest-*.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in data.get("sources", []):
            source_id = item.get("source_id")
            if isinstance(source_id, str):
                current = catalog.setdefault(source_id, {})
                completeness = item.get("text_completeness_state")
                if completeness == "verified_source_note":
                    library_state = "source_note_only"
                elif completeness == "bundled_verified":
                    library_state = "registered_record"
                elif completeness == "retrieved_full_text_candidate_not_trust_promoted":
                    library_state = "candidate_unaccepted"
                elif completeness == "candidate_unverified":
                    library_state = "candidate_unaccepted"
                elif completeness == "reference_only":
                    library_state = "not_recorded"
                else:
                    library_state = current.get("library_state", "not_recorded")
                current.update({
                    "title": item.get("title", current.get("title", "")),
                    "section": "EU core",
                    "jurisdiction": "EU",
                    "source_type": item.get("source_type", ""),
                    "official_url": item.get("canonical_url", current.get("official_url")),
                    # The core manifest's explicit completeness/acceptance
                    # state is more specific than the retrieval index's older
                    # discovery state. Do not let an index candidate label
                    # override a bundled_verified core record.
                    "library_state": library_state,
                })

    # National manifests deliberately have different formats. Read only their
    # existing source/document records and derive the section from their path.
    for manifest_path in sorted(root.glob("*/**/*manifest*.json")):
        country = manifest_path.relative_to(root).parts[0].casefold()
        country_code = COUNTRY_CODES.get(country)
        if country in {"core", "templates", "visa-code-handbook-i-2020"}:
            continue
        if any(token in manifest_path.name for token in ("capture-results", "monitor-candidate")):
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        eu_guidance_pack = country == "references" and isinstance(data, dict) and data.get("pack") == "eu-guidance"
        section_label = (
            "EU core" if eu_guidance_pack
            else SECTION_LABELS.get(country_code.casefold(), country.title()) if country_code
            else country.title()
        )
        records = []
        if isinstance(data, dict):
            for key in ("sources", "documents", "source_records", "entries"):
                if isinstance(data.get(key), list):
                    records.extend(data[key])
        for item in records:
            if not isinstance(item, dict):
                continue
            source_id = item.get("source_id") or item.get("id")
            title = item.get("title") or item.get("label")
            if not isinstance(source_id, str) or not isinstance(title, str):
                continue
            state = (
                "registered_record" if item.get("accepted") is True
                else "candidate_unaccepted" if item.get("accepted") is False
                else "not_recorded"
            )
            jurisdiction = "EU" if eu_guidance_pack else COUNTRY_CODES.get(country, country.upper())
            source_type = str(item.get("source_type") or item.get("type") or item.get("class") or "")
            if not source_type and eu_guidance_pack:
                source_type = "official_guidance"
            if source_id in catalog:
                # Keep the index's canonical title and ownership when language
                # or path representations repeat a source, but allow an
                # owner-matched manifest to fill acceptance/type metadata.
                current = catalog[source_id]
                if current.get("jurisdiction") == jurisdiction:
                    if isinstance(item.get("accepted"), bool):
                        current["library_state"] = state
                    if not current.get("source_type") and source_type:
                        current["source_type"] = source_type
                    if not current.get("official_url") and (item.get("url") or item.get("official_url")):
                        current["official_url"] = item.get("url") or item.get("official_url")
                continue
            catalog[source_id] = {
                "title": title,
                "section": section_label,
                "jurisdiction": jurisdiction,
                "source_type": source_type,
                "official_url": item.get("url") or item.get("official_url"),
                "library_state": state,
            }
    return catalog


def _category(source_type: str, section: str, title: str = "") -> str:
    """Map recognized source metadata to a category; unknown metadata stays uncounted."""
    raw = source_type.casefold().replace("-", "_").replace(" ", "_").strip("`")
    title_raw = title.casefold().replace("-", "_").replace(" ", "_")
    if not raw:
        # Some existing national manifests provide only an official title.
        # Infer a conservative category from that title; leave unknown items as
        # references rather than counting them as legal texts.
        raw = title_raw
    # Metadata labels that describe discovery or publishing infrastructure are
    # references, even when they include words such as "case law" or
    # "legislation". They are not themselves the legal text being counted.
    if any(token in raw for token in (
        "api", "archive", "catalog", "catalogue", "checklist", "coverage_statement",
        "database", "directory", "discovery", "documentation", "feed",
        "index", "platform", "portal", "repository", "retrieval", "search",
        "status_page", "terms", "dataset",
    )):
        return "source_note" if any(token in raw for token in (
            "index", "documentation", "retrieval", "coverage_statement",
        )) else "publisher_portal"
    if any(token in raw for token in (
        "judgment", "case_law", "court_decision", "court_case", "primary_judicial_decision",
    )):
        return "case_law"
    if "commission" in raw and any(token in raw for token in (
        "guidance", "recommendation", "working_document", "handbook", "notice",
    )):
        return "commission_guidance"
    if any(token in raw for token in ("source_note", "summary", "index")):
        return "source_note"
    if any(token in raw for token in (
        "procedur", "complaint_route", "complaint", "mission_instruction", "instruction",
        "appeal", "application", "request", "form", "how_to", "petition", "central_administration",
        "document_access", "public_documents", "official_documents", "own_case_documents", "order_documents", "escalation",
        "practice_direction", "practice_rule",
    )):
        return "procedural_rule"
    if any(token in raw for token in (
        "guidance", "guideline", "recommendation", "handbook", "official_register", "oversight",
        "frequently_asked_questions", "evidence_standard", "article_8",
    )):
        return "official_guidance"
    if raw == "act" or raw.endswith("_act") or any(token in raw for token in (
        "directive", "regulation", "treaty", "statute", "legislation", "law", "decree",
        "ordinance", "primary_law", "sfs", "national_act", "amending_act", "consolidated_act",
        "charter", "national_code", "consolidated_text", "consolidated_translation",
        "constitutional_text", "coordinated_legal_text", "legal_text",
    )):
        is_eu = section == "EU core" or section.casefold().startswith("external official · eu")
        return "eu_legislation" if is_eu else "national_legislation"
    if not source_type and any(token in raw for token in (
        "visa", "residence", "family_member", "ombudsman", "information", "faq", "how_to",
    )):
        return "official_guidance"
    # Unknown non-empty metadata is not enough to assert that an item is a
    # legal text. Keep it out of the legal-text total until classified.
    return "other_reference"


def _valid_http_url(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_source_ledger(ledger: dict) -> dict:
    if ledger.get("response_tracking") not in TRACKING_STATES:
        raise DashboardError("source_ledger_response_tracking_invalid")
    if ledger.get("conversation_tracking") not in TRACKING_STATES:
        raise DashboardError("source_ledger_conversation_tracking_invalid")
    if "runtime_recorded" in {ledger.get("response_tracking"), ledger.get("conversation_tracking")}:
        raise DashboardError("runtime_read_events_not_supported_without_host_attestation")
    entries = ledger.get("sources")
    if not isinstance(entries, list):
        raise DashboardError("source_ledger_sources_missing")
    catalog = _load_catalog()
    seen: set[str] = set()
    seen_representations: dict[str, str] = {}
    for item in entries:
        logical_id = item.get("logical_source_id")
        if not isinstance(logical_id, str) or not logical_id.strip():
            raise DashboardError("logical_source_id_missing")
        if logical_id in seen:
            raise DashboardError(f"duplicate_logical_source:{logical_id}")
        seen.add(logical_id)
        if item.get("currentness") not in CURRENTNESS:
            raise DashboardError(f"currentness_invalid:{logical_id}")
        if item.get("library_state") not in LIBRARY_STATES:
            raise DashboardError(f"library_state_invalid:{logical_id}")
        if item.get("response_use") not in READ_STATES or item.get("conversation_use") not in READ_STATES:
            raise DashboardError(f"source_use_state_invalid:{logical_id}")
        if item.get("response_provenance") not in READ_PROVENANCE or item.get("conversation_provenance") not in READ_PROVENANCE:
            raise DashboardError(f"source_read_provenance_invalid:{logical_id}")

        bundled = item.get("origin") == "bundled_library"
        external = item.get("origin") == "external_official"
        if not bundled and not external:
            raise DashboardError(f"source_origin_invalid:{logical_id}")
        if bundled:
            source_id = item.get("source_id")
            metadata = catalog.get(source_id)
            if metadata is None:
                raise DashboardError(f"bundled_source_id_not_in_library:{logical_id}")
            if logical_id != source_id:
                raise DashboardError(f"bundled_logical_identity_mismatch:{logical_id}")
            if item.get("title") != metadata.get("title"):
                raise DashboardError(f"bundled_source_title_mismatch:{logical_id}")
            if item.get("section") != metadata.get("section") or item.get("jurisdiction") != metadata.get("jurisdiction"):
                raise DashboardError(f"bundled_source_owner_mismatch:{logical_id}")
            expected_category = (
                "source_note" if metadata.get("library_state") == "source_note_only"
                else _category(metadata.get("source_type", ""), metadata.get("section", ""), metadata.get("title", ""))
            )
            if item.get("category") != expected_category:
                raise DashboardError(f"bundled_source_category_mismatch:{logical_id}")
            if item.get("library_state") != metadata.get("library_state"):
                raise DashboardError(f"bundled_library_state_mismatch:{logical_id}")
            if item.get("source_type") is not None and item["source_type"] != metadata.get("source_type"):
                raise DashboardError(f"bundled_source_type_mismatch:{logical_id}")
            if metadata.get("official_url") and item.get("official_url") != metadata.get("official_url"):
                raise DashboardError(f"bundled_official_url_mismatch:{logical_id}")
        else:
            if item.get("section") != "External official" and not str(item.get("section", "")).startswith("External official · "):
                raise DashboardError(f"external_source_section_invalid:{logical_id}")
            if not _valid_http_url(item.get("official_url")):
                raise DashboardError(f"external_official_url_invalid:{logical_id}")
            if item.get("category") not in LEGAL_CATEGORIES | NON_TEXT_CATEGORIES:
                raise DashboardError(f"external_source_category_invalid:{logical_id}")
            if item.get("category") != _category(item.get("source_type", ""), item.get("section", "")):
                raise DashboardError(f"external_source_category_mismatch:{logical_id}")
            section = item.get("section", "")
            if section.startswith("External official · "):
                label = section.removeprefix("External official · ").casefold()
                expected_jurisdiction = "EU" if label == "eu core" else COUNTRY_CODES.get(label)
                if expected_jurisdiction and item.get("jurisdiction") != expected_jurisdiction:
                    raise DashboardError(f"external_source_owner_mismatch:{logical_id}")

        for representation_id in item.get("representation_ids", []):
            prior_logical_id = seen_representations.get(representation_id)
            if prior_logical_id and prior_logical_id != logical_id:
                raise DashboardError(f"representation_counted_as_multiple_texts:{representation_id}")
            seen_representations[representation_id] = logical_id

        pinpoints = item.get("pinpoints")
        if not isinstance(pinpoints, list) or len(pinpoints) != len(set(pinpoints)):
            raise DashboardError(f"source_pinpoints_invalid:{logical_id}")
        for scope in ("response", "conversation"):
            use = item[f"{scope}_use"]
            provenance = item[f"{scope}_provenance"]
            evidence_ref = item.get(f"{scope}_evidence_ref")
            read_evidence = item.get(f"{scope}_read_evidence")
            if use == "consulted":
                if provenance == "none" or not isinstance(read_evidence, str) or not read_evidence.strip():
                    raise DashboardError(f"consulted_source_without_read_evidence:{scope}:{logical_id}")
                if provenance == "runtime_recorded":
                    raise DashboardError("runtime_read_events_not_supported_without_host_attestation")
            elif provenance != "none" or evidence_ref is not None:
                raise DashboardError(f"unread_source_has_read_provenance:{scope}:{logical_id}")
            if use == "cited_from_memory" and read_evidence:
                raise DashboardError(f"memory_citation_mislabelled_as_read:{scope}:{logical_id}")
        if item["currentness"] not in {"unknown", "stale"}:
            if not item.get("version_or_edition") or not any(
                item.get(f"{scope}_use") == "consulted" and item.get(f"{scope}_read_evidence")
                for scope in ("response", "conversation")
            ):
                raise DashboardError(f"currentness_without_version_or_read_evidence:{logical_id}")

    response = _count_for_scope(entries, "response", ledger["response_tracking"])
    conversation = _count_for_scope(entries, "conversation", ledger["conversation_tracking"])
    return {"response": response, "conversation": conversation, "catalog": catalog}


def _count_for_scope(entries: list[dict], scope: str, tracking: str) -> dict:
    if tracking == "unavailable":
        recorded = [item for item in entries if item[f"{scope}_use"] == "consulted"
                    and item["category"] not in NON_TEXT_CATEGORIES]
        sections: dict[str, int] = {}
        for item in recorded:
            if item["origin"] == "bundled_library":
                sections[item["section"]] = sections.get(item["section"], 0) + 1
        return {"status": "unknown", "count": None, "sources": recorded, "sections": sections}
    consulted = [item for item in entries if item[f"{scope}_use"] == "consulted"]
    legal = [item for item in consulted if item["category"] not in NON_TEXT_CATEGORIES]
    sections: dict[str, int] = {}
    for item in legal:
        if item["origin"] != "bundled_library":
            continue
        section = item["section"]
        sections[section] = sections.get(section, 0) + 1
    return {
        "status": "model_declared",
        "count": len(legal),
        "sources": legal,
        "sections": sections,
    }


OPERATION_LABELS = {
    "route_classification": "Route classification",
    "c23_guidance": "Applicant guidance",
    "c27_reconciliation": "C27 case-state checks",
    "attack_angle_screen": "Alternative-risk screening",
    "requested_output": "Requested answer",
    "research_gate": "Research-plan validation",
    "source_preflight": "Source-coverage check",
    "c3_module_pair_conformance": "Country-module conformance",
    "c3_case_geography_match": "Country-to-case match",
}
CLASSIFICATION_LABELS = {
    "jurisdictions_by_role": "Jurisdiction roles",
    "proceedings_and_stages": "Proceedings and stages",
    "legal_questions": "Legal questions",
    "urgency": "Urgency",
    "requested_output": "Requested output",
}
CATEGORY_LABELS = {
    "eu_legislation": "EU law",
    "national_legislation": "National law",
    "case_law": "Case law",
    "commission_guidance": "Commission guidance",
    "official_guidance": "Official guidance",
    "procedural_rule": "Procedure",
    "other_legal_text": "Other legal text",
    "publisher_portal": "Publisher portal",
    "source_note": "Source note",
    "other_reference": "Reference / unclassified",
}


def _humanize(value: str) -> str:
    return value.replace("_", " ").replace(".", " / ")


def _gap_work(gap: str) -> dict | None:
    """Turn a structural gap into a concise, user-facing missing/effect item."""
    # The unresolved issue summary already explains this disposition.
    if gap.startswith("issue:") and ":disposition:" in gap:
        return None
    if gap == "c27:no_selected_checks_recorded":
        return {
            "title": "Case-state checks",
            "missing": "No relevant C27 checks were selected and recorded.",
            "effect": "The case-state review remains incomplete.",
        }
    if gap.startswith("c27:"):
        parts = gap.split(":")
        if len(parts) >= 4:
            check_id, state = parts[-2], parts[-1]
            return {
                "title": f"Case-state check: {_humanize(check_id)}",
                "missing": f"This check is {state.replace('_', ' ')}; the recorded evidence does not close it.",
                "effect": "Any conclusion depending on this point remains unresolved.",
            }
    if gap.startswith("issue:") and ":c27_required_check_missing:" in gap:
        check_id = gap.rsplit(":", 1)[-1]
        return {
            "title": f"Issue-linked case-state check: {_humanize(check_id)}",
            "missing": "The required C27 check was not recorded for this issue.",
            "effect": "That issue cannot be treated as fully reconciled.",
        }
    if gap.startswith("classification:"):
        _, name, _state = gap.split(":", 2)
        label = CLASSIFICATION_LABELS.get(name, _humanize(name).title())
        return {
            "title": label,
            "missing": f"The {label.casefold()} could not be established from the recorded facts.",
            "effect": "The applicable route or scope may change once this is clarified.",
        }
    if gap == "conditional_workflow_review:incomplete":
        return {
            "title": "Conditional checks",
            "missing": "The review of fact-triggered workflows is incomplete.",
            "effect": "A required line of analysis may not yet be covered.",
        }
    if gap.startswith("required_operation_missing:"):
        operation = gap.split(":", 1)[1]
        label = OPERATION_LABELS.get(operation, _humanize(operation).title())
        return {
            "title": label,
            "missing": "No execution record was supplied for this required step.",
            "effect": "Its findings are absent, so related conclusions remain provisional.",
        }
    if gap.startswith("required_operation_misclassified:"):
        operation = gap.split(":", 1)[1]
        label = OPERATION_LABELS.get(operation, _humanize(operation).title())
        return {
            "title": label,
            "missing": "The required step was not recorded as required.",
            "effect": "The route cannot confirm that this required work was covered.",
        }
    if gap.startswith("operation:"):
        _, operation, state = gap.split(":", 2)
        label = OPERATION_LABELS.get(operation, _humanize(operation).title())
        if state == "evidence_reference_missing":
            missing = "The operation has no linked evidence or result."
            effect = "Completion cannot be verified from this receipt."
        elif state == "not_triggered_without_not_applicable":
            missing = "The operation is marked not triggered without a not-applicable finding."
            effect = "The receipt does not explain why this workflow was excluded."
        else:
            missing = f"The recorded status is {state.replace('_', ' ')}."
            effect = "This step's findings are not available, so related conclusions remain provisional."
        return {"title": label, "missing": missing, "effect": effect}
    if gap.startswith("module_pair:") or gap.startswith("c3_module_pair_conformance:"):
        return {
            "title": "Country-module conformance",
            "missing": "The selected module pair is unavailable or did not pass the conformance check.",
            "effect": "The module's country-specific information cannot be relied on as validated.",
        }
    if gap.startswith("c3_case_geography_match:"):
        return {
            "title": "Country-to-case match",
            "missing": "The real-case geography match is not supported by the synthetic-only controller.",
            "effect": "The selected module's fit to the case remains unverified.",
        }
    if gap.startswith("research_gate:") or gap.startswith("research_artifact:"):
        return {
            "title": "Source research",
            "missing": "The research plan or evidence bundle is missing, incomplete, or did not pass validation.",
            "effect": "Source coverage for the affected question remains unverified.",
        }
    if gap.startswith("source_preflight:"):
        return {
            "title": "Source coverage",
            "missing": "The required official-source preflight is missing or reports an unresolved source gap.",
            "effect": "The affected legal conclusion remains provisional until the source gap is resolved.",
        }
    if gap == "source_use_tracking:current_response_unavailable":
        return {
            "title": "Sources consulted in this response",
            "missing": "Response-level source tracking is unavailable.",
            "effect": "The dashboard reports an unknown total and cannot confirm complete source accounting.",
        }
    return {
        "title": "Open validation item",
        "missing": f"{_humanize(gap).capitalize()} remains unresolved.",
        "effect": "The related part of the assessment remains provisional.",
    }


def _open_work(route_gaps: list[str]) -> list[dict]:
    seen: set[str] = set()
    result = []
    for gap in route_gaps:
        if gap in seen:
            continue
        seen.add(gap)
        item = _gap_work(gap)
        if item is not None:
            result.append(item)
    return result


def render_dashboard(route: dict, source_report: dict, route_gaps: list[str],
                     required_operation_ids: tuple[str, ...] = (),
                     validation_record: dict | None = None,
                     validator_reports: dict | None = None) -> str | None:
    dashboard = route.get("dashboard")
    if dashboard is None:
        return None
    invocation = route.get("invocation", {})
    state = invocation.get("state", "not recorded")
    basis = invocation.get("basis", "not recorded")
    validation = validation_record or {
        "result": "not run by standalone dashboard renderer",
        "validator": "consultation_route_gate.py",
        "receipt_sha256": "not available",
        "outstanding_count": len(set(route_gaps)),
    }
    reports = validator_reports or {}
    lines = ["## FreeMovement — Consultation Review", ""]

    if route["request_kind"] == "no_case_assessment":
        lines.extend([
            "**Not verified** · No case assessment was performed.",
            "",
            "### Invocation and validation",
            f"- Invocation: {state.replace('_', ' ')}; basis: {basis.replace('_', ' ')}.",
            f"- Receipt check: {validation.get('result', 'not recorded')}.",
            f"- Validator: `{validation.get('validator', 'not recorded')}` v{validation.get('validator_version', 'unknown')}.",
            f"- Receipt fingerprint: `{validation.get('receipt_sha256', 'not available')}`.",
            f"- Outstanding validation items: {validation.get('outstanding_count', len(set(route_gaps)))}.",
            "- Host release control: not available in this plugin; this board does not block ChatGPT output.",
            "",
            "---",
        ])
        return "\n".join(lines)

    metrics = source_report
    response = metrics["response"]
    conversation = metrics["conversation"]
    status = {"reviewed": "Reviewed", "partial": "Partial", "not_verified": "Not verified"}[dashboard["assessment_status"]]
    open_work = _open_work(route_gaps)
    issue_summaries = dashboard["issue_summaries"]
    if validation_record is None:
        overall = "Validation not run by this standalone renderer"
    elif validation.get("result") == "structurally_closed_declared_plan":
        overall = "Structurally closed declared plan"
    elif validation.get("result") == "rejected_comprehensive_claim":
        overall = "Comprehensive claim rejected; declared work remains open"
    else:
        overall = "Partial route; declared work remains open"

    def value_status(value: str) -> str:
        return value.replace("_", " ")

    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")

    def refs(refs: list[str]) -> str:
        if not refs:
            return "none recorded"
        counts: dict[str, int] = {}
        evidence = {item["evidence_ref"]: item for item in route.get("evidence", [])}
        kind_labels = {
            "conversation_record": "conversation record", "source_record": "source record",
            "module_conformance": "module check", "research_gate": "research check",
            "source_preflight": "source coverage check", "local_artifact": "local artifact",
        }
        for ref in refs:
            kind = evidence.get(ref, {}).get("kind", "unresolved reference")
            label = kind_labels.get(kind, kind)
            counts[label] = counts.get(label, 0) + 1
        return "; ".join(
            f"{label} ({count})" for label, count in sorted(counts.items())
        )

    lines.extend([
        f"**{status}** · {overall}",
        "",
        "### Invocation and validation",
        f"- Invocation: {value_status(state)}; basis: {value_status(basis)}.",
        f"- Validation result: **{value_status(validation.get('result', 'not recorded'))}**.",
        f"- Validator: `{validation.get('validator', 'not recorded')}` v{validation.get('validator_version', 'unknown')}.",
        f"- Receipt fingerprint: `{validation.get('receipt_sha256', 'not available')}`.",
        f"- Outstanding validation items: {validation.get('outstanding_count', len(set(route_gaps)))}.",
        "- Validation covers the declared receipt and validator outputs. It does not authenticate model-reported facts, source reads, legal reasoning, or omitted issues.",
        "- Host release control: not available in this plugin; a host must call a controller and enforce its result to block output.",
        "",
        "### At a glance",
        f"- Assessment: **{status}**; requested coverage: **{value_status(route['coverage_claim'])}**.",
        f"- Legal texts this response: **{'unknown' if response['count'] is None else response['count']}** (model-reported).",
        f"- Conversation total: **{'unknown' if conversation['count'] is None else conversation['count']}** (model-reported).",
        f"- Source-library sections this response: **{'unknown' if response['count'] is None else len(response['sections'])}**.",
        f"- Declared material issues: **{len(issue_summaries)}**; outstanding checks and operations: **{len(open_work)}**.",
    ])

    lines.extend(["", "### Task scope"])
    for key, item in route["classification"].items():
        label = CLASSIFICATION_LABELS.get(key, _humanize(key).title())
        lines.append(f"- **{label}:** {value_status(item['state'])} · evidence: {refs([item['evidence_ref']])}.")
    conditional = route["conditional_review"]
    lines.append(
        f"- **Conditional workflow review:** {value_status(conditional['status'])} · "
        f"evidence: {refs([conditional['evidence_ref']])}."
    )

    operations = {item["operation_id"]: item for item in route["operations"]}
    for operation_id in required_operation_ids:
        operations.setdefault(operation_id, {
            "operation_id": operation_id, "applicability": "required", "status": "not_recorded",
            "reason_code": "not_attempted", "evidence_refs": [],
        })
    lines.extend(["", "### Work performed and engine checks"])
    applicable_operations = [
        item for item in operations.values()
        if item["applicability"] in {"required", "triggered"}
    ]
    def operation_has_validation_gap(operation_id: str) -> bool:
        return any(
            gap.startswith(f"operation:{operation_id}:")
            or gap == f"required_operation_missing:{operation_id}"
            or gap == f"required_operation_misclassified:{operation_id}"
            for gap in route_gaps
        )

    completed_operations = sum(
        item["status"] == "completed"
        and bool(item.get("evidence_refs"))
        and not operation_has_validation_gap(item["operation_id"])
        for item in applicable_operations
    )
    lines.append(
        f"{completed_operations}/{len(applicable_operations)} required or triggered operations have completion records with acceptable evidence."
    )
    for operation_id, item in sorted(operations.items(), key=lambda pair: (pair[0] not in required_operation_ids, pair[0])):
        label = OPERATION_LABELS.get(operation_id, _humanize(operation_id).title())
        evidence = refs(item.get("evidence_refs", []))
        applicability = value_status(item["applicability"])
        result = value_status(item["status"])
        if operation_has_validation_gap(operation_id) and item["status"] == "completed":
            result = "completion not verified"
        reason = value_status(item.get("reason_code", "reason not recorded"))
        detail = f" Evidence: {evidence}."
        if item.get("reason_code"):
            detail += f" Reason: {reason}."
        lines.append(f"- **{label}** (`{operation_id}`) — {applicability}; {result}.{detail}")
    lines.append("\nExecution status is receipt-declared unless a named validator report below confirms that its validator ran.")

    lines.extend(["", "### C27 case-state checks"])
    if route.get("c27_checks"):
        issue_summaries_by_ref = {item["issue_ref"]: item for item in dashboard["issue_summaries"]}
        scope_labels = {}
        for issue in route.get("issues", []):
            summary = issue_summaries_by_ref.get(issue["issue_ref"])
            if summary:
                scope_labels.setdefault(issue["scope_ref"], summary["title"])
        for index, entry in enumerate(route["c27_checks"], start=1):
            record = entry["record"]
            evidence_text = f"Evidence: {refs(record['evidence_refs'])}; sources: {refs(record['source_refs'])}"
            scope_label = scope_labels.get(entry["scope_ref"], f"Scope {index}")
            lines.append(f"- **{scope_label} — `{record['check_id']}`**")
            lines.append(
                f"  - Status and method: {value_status(record['status'])} · {value_status(record['method'])}. "
                f"Reason: {record['reason']}"
            )
            lines.append(f"  - {evidence_text}.")
            if record.get("scope_exclusion"):
                lines.append(f"  - Scope exclusion: {record['scope_exclusion']}.")
    else:
        lines.append("No C27 checks were recorded for this request.")

    lines.extend(["", "### Material issues and open work"])
    if issue_summaries:
        issue_by_ref = {item["issue_ref"]: item for item in route.get("issues", [])}
        for index, item in enumerate(issue_summaries, start=1):
            linked = issue_by_ref.get(item["issue_ref"], {})
            signals = ", ".join(_humanize(signal) for signal in linked.get("signal_ids", [])) or "signals not recorded"
            disposition = value_status(linked.get("disposition", "not recorded"))
            lines.append(
                f"- **Issue {index}: {item['title']}** · {disposition}; signals: {signals}. "
                f"Missing: {item['missing']} Effect: {item['effect']}"
            )
    if open_work:
        for item in open_work:
            lines.append(f"- **{item['title']}** · Missing: {item['missing']} Effect: {item['effect']}")
    if not issue_summaries and not open_work:
        lines.append("No outstanding items were reported by the declared route and validators.")

    research_reports = {item.get("research_ref"): item for item in reports.get("research", []) if item.get("research_ref")}
    preflight_reports = {item.get("preflight_id"): item for item in reports.get("source_preflight", []) if item.get("preflight_id")}
    lines.extend(["", "### Deterministic validator results"])
    lines.append("- Route-receipt schema and declared references: passed; this board was returned only after structural validation.")
    lines.append(
        f"- C27 record validation: {reports.get('c27_check_count', 0)} selected checks passed the shared record/status/trace validator."
        if reports.get("c27_check_count", 0)
        else "- C27 record validation: no check records were supplied."
    )
    if reports.get("issue_records_declared"):
        lines.append(
            f"- Issue-to-C27 routing: {reports.get('issue_record_count', 0)} declared issue records checked against the routing matrix."
        )
    else:
        lines.append("- Issue-to-C27 routing: no issue records were declared, so issue-signal selection was not run.")
    lines.append(
        "- Source-ledger consistency: passed; source-use counts remain model-reported."
        if reports.get("source_ledger_validated")
        else "- Source-ledger consistency: no consultation ledger was available for validation."
    )
    lines.append(
        "- Dashboard consistency: passed; issue summaries and module records reconcile with the declared receipt and validator results."
        if reports.get("dashboard_consistency_validated")
        else "- Dashboard consistency: not run."
    )
    lines.extend(["", "### Research and source coverage validation"])
    if route.get("research_artifacts"):
        for artifact in route["research_artifacts"]:
            report = research_reports.get(artifact["research_ref"], {})
            lines.append(
                f"- **Research bundle** — {value_status(report.get('status', 'not validated'))}; "
                f"mode: {value_status(report.get('mode', 'not reported'))}; "
                f"coverage: {value_status(report.get('coverage_status', 'unknown'))}; "
                f"complete: {report.get('research_complete', 'unknown')}."
            )
            lines.append(
                f"  - Plan: `{artifact['plan_path']}`; evidence bundle: `{artifact['bundle_path']}`; "
                f"tasks: {report.get('task_count', 'unknown')}; findings: {report.get('finding_count', 'unknown')}; "
                f"evidence items: {report.get('evidence_count', 'unknown')}; claims: {report.get('claim_count', 'unknown')}."
            )
            if report.get("plan_sha256"):
                lines.append(f"  - Validated plan fingerprint: `{report['plan_sha256']}`.")
            if report.get("reason"):
                lines.append(f"  - Validation reason: {report['reason']}.")
            if report.get("legal_merits_status") or report.get("downstream_status"):
                lines.append(
                    f"  - Legal merits: {value_status(report.get('legal_merits_status', 'not reported'))}; "
                    f"downstream use: {value_status(report.get('downstream_status', 'not reported'))}."
                )
            if artifact.get("preflight_ref"):
                preflight = preflight_reports.get(artifact["preflight_ref"], {})
                lines.append(
                    f"  - Official-source coverage: {value_status(preflight.get('status', 'not validated'))}; "
                    f"validator status: {value_status(preflight.get('validation_status', 'not reported'))}; "
                    f"accounted for review: {preflight.get('source_coverage_accounted_for_review', 'unknown')}; "
                    f"research gate: {value_status(preflight.get('research_gate_status', 'not reported') )}."
                )
                for issue in preflight.get("issues", []):
                    lines.append(
                        f"    - Source issue {issue.get('issue_id', 'unknown')} · {value_status(issue.get('owner_role', 'role unknown'))}; "
                        f"satisfied classes: {', '.join(issue.get('satisfied_source_classes', [])) or 'none'}; "
                        f"open items: {', '.join(issue.get('outstanding', [])) or 'none'}."
                    )
                if preflight.get("outstanding"):
                    lines.append(f"  - Full outstanding source items: {', '.join(preflight['outstanding'])}.")
                if preflight.get("reason"):
                    lines.append(f"  - Preflight validation reason: {preflight['reason']}.")
    else:
        lines.append("No research artifact was supplied. Where research was required, the missing task is listed above.")
    if reports.get("module_pairs"):
        lines.append("- Module-pair validator results:")
        for report in reports["module_pairs"]:
            lines.append(
                f"  - {report.get('module_id', 'module not identified')}: "
                f"{value_status(report.get('status', 'unknown'))}; jurisdiction: {value_status(report.get('jurisdiction', 'not reported'))}; "
                f"contract/profile: {report.get('contract_version', 'unknown')}/{report.get('profile_version', 'unknown')}; "
                f"supported roles: {', '.join(report.get('supported_roles', [])) or 'none reported'}; "
                f"records: {report.get('owned_record_count', 'unknown')} owned, {report.get('usable_source_count', 'unknown')} usable, "
                f"{report.get('full_text_source_count', 'unknown')} full text, {report.get('known_gap_count', 'unknown')} known gaps."
            )
            if report.get("reason"):
                lines.append(f"    - Validation reason: {report['reason']}.")
    if not reports.get("module_pairs"):
        lines.append("- No C3 module-pair validator report was produced.")

    lines.extend(["", "### Source ledger"])
    lines.append(
        f"Response tracking: {value_status(route['source_ledger']['response_tracking'])}; "
        f"conversation tracking: {value_status(route['source_ledger']['conversation_tracking'])}. "
        "Counts are model-reported; unavailable tracking remains unknown."
    )
    ledger = sorted(route["source_ledger"]["sources"], key=lambda item: (item["section"].casefold(), item["title"].casefold(), item["logical_source_id"]))
    if ledger:
        for item in ledger:
            category = CATEGORY_LABELS.get(item["category"], _humanize(item["category"]))
            origin = "external official source" if item["origin"] == "external_official" else "source library"
            edition = item.get("version_or_edition") or "edition not recorded"
            pinpoints = ", ".join(item["pinpoints"]) or "pinpoint not recorded"
            url = item.get("official_url")
            title = f"[{item['title']}]({url})" if url else item["title"]
            source_type = f" · {item['source_type']}" if item.get("source_type") else ""
            lines.append(f"- **{title}** — {item['section']} · {item['jurisdiction']} · {category}{source_type}.")
            lines.append(
                f"  - Identity: source `{item['source_id']}`; logical record `{item['logical_source_id']}`; {origin}."
            )
            lines.append(
                f"  - This answer: {value_status(item['response_use'])}; provenance {value_status(item['response_provenance'])}; "
                f"read note: {cell(item.get('response_read_evidence') or 'none')}; evidence: "
                f"{refs([item['response_evidence_ref']] if item.get('response_evidence_ref') else [])}."
            )
            lines.append(
                f"  - Earlier chat: {value_status(item['conversation_use'])}; provenance {value_status(item['conversation_provenance'])}; "
                f"read note: {cell(item.get('conversation_read_evidence') or 'none')}; evidence: "
                f"{refs([item['conversation_evidence_ref']] if item.get('conversation_evidence_ref') else [])}."
            )
            representations = ", ".join(item["representation_ids"]) or "not recorded"
            lines.append(f"  - Edition/version: {edition}; representations: {representations}; pinpoints: {pinpoints}.")
            lines.append(
                f"  - Currentness: {value_status(item['currentness'])}; library status: "
                f"{value_status(item['library_state'])}."
            )
    else:
        lines.append("No source records were supplied.")

    module_entries = sorted(
        dashboard["module_use"],
        key=lambda item: (item["module_id"].casefold() != "eudirective-core", item["module_id"].casefold(), item["role"].casefold()),
    )
    lines.extend(["", "### Module use in this answer and chat"])
    if module_entries:
        for item in module_entries:
            current = {"used": "used", "not_used": "not used", "not_applicable": "not applicable"}[item["response_use"]]
            earlier = {"used_earlier": "used earlier", "not_used": "not used earlier", "unknown": "unknown"}[item["conversation_use"]]
            display_name = item.get("display_name", item["module_id"])
            role_label = item.get("role_label", _humanize(item["role"]))
            identity = f" (`{item['module_id']}`)" if display_name != item["module_id"] else ""
            lines.append(f"- **{display_name}{identity}** — {role_label}.")
            lines.append(
                f"  - This answer: {current}; earlier in chat: {earlier}; "
                f"availability: {value_status(item['availability'])}; C3: {value_status(item['conformance'])}."
            )
            lines.append(f"  - Reason: {item['reason']}")
    else:
        lines.append("No module-use record was supplied.")

    if route.get("issues"):
        lines.extend(["", "### Issue routing record"])
        for index, issue in enumerate(route["issues"], start=1):
            lines.append(
                f"- Issue {index}: {value_status(issue['disposition'])}; "
                f"signals: {', '.join(_humanize(value) for value in issue['signal_ids'])}; "
                f"scope evidence: {refs([issue['evidence_ref']])}."
            )

    lines.extend([
        "",
        "### What this board can verify",
        "- It lists every source, selected C27 check, declared issue, module record, and required or triggered operation present in the receipt; nothing is omitted for compactness.",
        "- Local validators verify declared structure and selected artifacts. They do not prove the truth of model-reported work or detect omitted issues and triggers.",
        "- This plugin has no ChatGPT host release hook. A local controller can bind this exact answer and receipt when a host actually calls it; it cannot intercept ordinary ChatGPT output by itself.",
        "",
        "---",
    ])
    return "\n".join(lines)


def validate_dashboard_receipt(route: dict, evidence_index: dict[str, dict], route_gaps: list[str],
                               module_reports: list[dict] | None = None,
                               required_operation_ids: tuple[str, ...] = ()) -> dict:
    invocation = route.get("invocation")
    if not isinstance(invocation, dict):
        return {"required": False, "preview": None, "source_metrics": None}
    state = invocation.get("state")
    basis = invocation.get("basis")
    if state not in {"explicit", "implicit", "unknown"}:
        raise DashboardError("invocation_state_invalid")
    if basis not in {
        "host_signal", "visible_plugin_marker", "continuation_after_explicit_invocation", "unavailable",
    }:
        raise DashboardError("invocation_basis_invalid")
    if state == "explicit" and basis not in {"host_signal", "visible_plugin_marker"}:
        raise DashboardError("explicit_invocation_without_reliable_marker")
    if state == "implicit" and basis != "continuation_after_explicit_invocation":
        raise DashboardError("implicit_invocation_basis_invalid")
    if state == "unknown" and basis != "unavailable":
        raise DashboardError("unknown_invocation_basis_invalid")
    dashboard = route.get("dashboard")
    required = (
        state == "explicit"
        or invocation.get("dashboard_requested") is True
        or invocation.get("material_change") is True
        or dashboard is not None
    )
    if required and dashboard is None:
        raise DashboardError("mandatory_dashboard_missing")
    if dashboard is None:
        return {"required": False, "preview": None, "source_metrics": None}
    if route["request_kind"] == "no_case_assessment":
        if (dashboard["assessment_status"] != "not_verified" or dashboard["issue_summaries"]
                or dashboard["module_use"]
                or route["coverage_claim"] == "comprehensive"):
            raise DashboardError("non_consultation_dashboard_must_be_minimal")
        empty_metrics = {"response": {}, "conversation": {}}
        return {
            "required": required,
            "preview": render_dashboard(route, empty_metrics, route_gaps),
            "source_metrics": None,
            "render_metrics": empty_metrics,
        }

    ledger = route.get("source_ledger")
    if not isinstance(ledger, dict):
        raise DashboardError("mandatory_source_ledger_missing")
    metrics = validate_source_ledger(ledger)
    unresolved = {
        item["issue_ref"] for item in route.get("issues", [])
        if item["disposition"] in UNRESOLVED_ISSUES
    }
    noted = {item["issue_ref"] for item in dashboard["issue_summaries"]}
    if unresolved != noted:
        raise DashboardError("dashboard_outstanding_issues_mismatch")
    for item in dashboard["issue_summaries"]:
        if not OPAQUE_REF.fullmatch(item["issue_ref"]):
            raise DashboardError("dashboard_issue_reference_invalid")
    seen_modules: set[tuple[str, str]] = set()
    available_pairs = {
        item.get("pair_ref"): item
        for item in (module_reports or [])
        if item.get("pair_ref")
    }
    declared_pair_refs = {item["pair_ref"] for item in route["module_pairs"]}
    paired_module_entries = [item for item in dashboard["module_use"] if item.get("pair_ref") is not None]
    module_use_by_pair = {item["pair_ref"]: item for item in paired_module_entries}
    if len(module_use_by_pair) != len(paired_module_entries):
        raise DashboardError("duplicate_module_pair_use_reference")
    if set(module_use_by_pair) != declared_pair_refs:
        raise DashboardError("module_pair_use_reconciliation_mismatch")
    for item in dashboard["module_use"]:
        module_key = (item["module_id"].casefold(), item["role"].casefold())
        if module_key in seen_modules:
            raise DashboardError("duplicate_module_use_record")
        seen_modules.add(module_key)
        if item["availability"] == "unavailable" and item["response_use"] == "used":
            raise DashboardError("unavailable_module_marked_used")
        pair_ref = item.get("pair_ref")
        if item["conformance"] == "conformant":
            report = available_pairs.get(pair_ref, {})
            if pair_ref not in declared_pair_refs or report.get("status") != "conformant":
                raise DashboardError("module_conformance_claim_unverified")
            if item["module_id"].casefold() != str(report.get("module_id", "")).casefold():
                raise DashboardError("module_pair_identity_mismatch")
            supported_roles = {str(role).casefold() for role in report.get("supported_roles", [])}
            if item["role"].casefold() not in supported_roles:
                raise DashboardError("module_pair_role_mismatch")
        elif pair_ref is not None:
            report = available_pairs.get(pair_ref)
            if item["conformance"] != "unavailable" or report is None or report.get("status") != "rejected":
                raise DashboardError("module_pair_conformance_status_mismatch")
    if route["request_kind"] in {"applicant_guidance", "source_research"}:
        core_entries = [item for item in dashboard["module_use"]
                        if item["module_id"].casefold() == "eudirective-core"]
        if (len(core_entries) != 1 or core_entries[0]["availability"] != "available"
                or core_entries[0]["response_use"] != "used"):
            raise DashboardError("core_module_use_missing_or_inaccurate")
    if ledger["response_tracking"] == "unavailable":
        if route["coverage_claim"] == "comprehensive":
            raise DashboardError("comprehensive_claim_without_current_response_source_accounting")
        route_gaps.append("source_use_tracking:current_response_unavailable")
    expected_status = (
        "partial" if route_gaps or route["coverage_claim"] != "comprehensive"
        else "reviewed"
    )
    if dashboard["assessment_status"] != expected_status:
        raise DashboardError("dashboard_assessment_status_mismatch")
    if dashboard["assessment_status"] == "partial" and not dashboard["issue_summaries"] and not _open_work(route_gaps):
        raise DashboardError("partial_assessment_without_explained_open_work")
    preview = render_dashboard(route, metrics, route_gaps, required_operation_ids)
    return {
        "required": required,
        "preview": preview,
        "source_metrics": {
            k: {"status": v["status"], "count": v["count"], "sections": v["sections"]}
            for k, v in metrics.items() if k in {"response", "conversation"}
        },
        "render_metrics": metrics,
    }
