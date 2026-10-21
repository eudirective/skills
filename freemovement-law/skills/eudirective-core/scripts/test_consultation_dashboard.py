#!/usr/bin/env python3
"""Synthetic tests for invocation-aware consultation dashboard accounting."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from consultation_dashboard import (  # noqa: E402
    DashboardError,
    COUNTRY_CODES,
    _category,
    _load_catalog,
    validate_dashboard_receipt,
)
from consultation_route_gate import REQUIRED_OPERATIONS  # noqa: E402
from contract_validate import ContractError, validate_obj  # noqa: E402
from source_library_paths import source_library_root  # noqa: E402


def source_record(source_id: str, *, response_use="consulted", conversation_use="consulted",
                  origin="bundled_library", category=None, logical_source_id=None,
                  representation_ids=None, source_type=None):
    metadata = _load_catalog().get(source_id)
    if origin == "bundled_library":
        if metadata is None:
            raise AssertionError(f"test source is not in bundled metadata: {source_id}")
        section = metadata["section"]
        jurisdiction = metadata["jurisdiction"]
        title = metadata["title"]
        category = category or _category(metadata["source_type"], section, title)
        library_state = metadata["library_state"]
        official_url = metadata.get("official_url")
    else:
        section = "External official · Spain"
        jurisdiction = "ES"
        title = "Synthetic official statute"
        source_type = source_type or "national statute"
        category = category or _category(source_type, section)
        library_state = "not_applicable"
        official_url = "https://example.gov/law/1"
    item = {
        "logical_source_id": logical_source_id or source_id,
        "source_id": source_id,
        "title": title,
        "section": section,
        "jurisdiction": jurisdiction,
        "category": category,
        "origin": origin,
        "official_url": official_url,
        "version_or_edition": "synthetic fixture edition",
        "representation_ids": representation_ids or [source_id + ":EN"],
        "pinpoints": ["Article 3", "Article 5"],
        "currentness": "unknown",
        "library_state": library_state,
        "response_use": response_use,
        "conversation_use": conversation_use,
        "response_provenance": "model_declared" if response_use == "consulted" else "none",
        "conversation_provenance": "model_declared" if conversation_use == "consulted" else "none",
        "response_read_evidence": "source text opened at recorded source path" if response_use == "consulted" else None,
        "conversation_read_evidence": "conversation ledger reference" if conversation_use == "consulted" else None,
        "response_evidence_ref": None,
        "conversation_evidence_ref": None,
    }
    if origin == "external_official":
        item["source_type"] = source_type
    return item


def make_route(*, state="explicit", basis="visible_plugin_marker", dashboard_requested=False,
               request_kind="applicant_guidance", coverage="comprehensive", tracking="model_declared",
               sources=None, issue_summaries=None, issues=None, assessment_status=None):
    if request_kind == "no_case_assessment" and coverage == "comprehensive":
        coverage = "preliminary"
    if assessment_status is None:
        assessment_status = (
            "not_verified" if request_kind == "no_case_assessment"
            else "partial" if coverage != "comprehensive" or issues else "reviewed"
        )
    ref = "r_0000000000000001"
    operations = [
        {"operation_id": name, "applicability": "required", "status": "completed", "evidence_refs": [ref]}
        for name in ("route_classification", "c23_guidance", "c27_reconciliation", "attack_angle_screen", "requested_output")
    ]
    if request_kind == "source_research":
        operations = [
            {"operation_id": name, "applicability": "required", "status": "completed", "evidence_refs": [ref]}
            for name in ("route_classification", "research_gate", "source_preflight", "requested_output")
        ]
    if request_kind == "no_case_assessment":
        operations = [
            {"operation_id": name, "applicability": "required", "status": "completed", "evidence_refs": [ref]}
            for name in ("route_classification", "requested_output")
        ]
    route = {
        "schema_version": "0.2.0",
        "route_ref": "r_0000000000000002",
        "request_kind": request_kind,
        "invocation": {"state": state, "basis": basis, "dashboard_requested": dashboard_requested},
        "classification": {
            name: {"state": "recorded", "evidence_ref": ref}
            for name in ("jurisdictions_by_role", "proceedings_and_stages", "legal_questions", "urgency", "requested_output")
        },
        "conditional_review": {"status": "reviewed", "evidence_ref": ref},
        "operations": operations,
        "c27_checks": [] if request_kind == "no_case_assessment" else [{
            "scope_ref": "r_0000000000000003",
            "record": {
                "check_id": "case_intake.proceedings_identified", "status": "assessed",
                "method": "model_review", "reason": "scope_reviewed",
                "evidence_refs": [ref], "source_refs": [],
            },
        }],
        "evidence": [{"evidence_ref": ref, "kind": "conversation_record"}],
        "research_artifacts": [], "module_pairs": [], "coverage_claim": coverage,
    }
    if issues is not None:
        route["issues"] = issues
    if request_kind != "no_case_assessment":
        route["source_ledger"] = {
            "response_tracking": tracking,
            "conversation_tracking": "model_declared" if tracking != "unavailable" else "unavailable",
            "sources": sources or [],
        }
    if state == "explicit" or dashboard_requested:
        module_use = [] if request_kind == "no_case_assessment" else [{
            "module_id": "eudirective-core", "role": "consultation routing and EU/common legal analysis",
            "availability": "available", "response_use": "used", "conversation_use": "used_earlier",
            "conformance": "not_applicable", "reason": "Core consultation guidance used this response.",
        }]
        route["dashboard"] = {
            "assessment_status": assessment_status,
            "issue_summaries": issue_summaries or [],
            "module_use": module_use,
        }
    return route


class ConsultationDashboardTests(unittest.TestCase):
    def report(self, route, gaps=None):
        return validate_dashboard_receipt(
            route, {"r_0000000000000001": {"kind": "conversation_record"}}, gaps or [],
            required_operation_ids=REQUIRED_OPERATIONS[route["request_kind"]],
        )

    def test_first_and_repeated_explicit_invocations_require_fresh_dashboard(self):
        first = make_route()
        second = make_route()
        for invocation_number, route in enumerate((first, second), start=1):
            validate_obj("consultation-route-receipt", route)
            self.assertTrue(self.report(route)["required"], f"invocation {invocation_number}")
            route.pop("dashboard")
            with self.assertRaisesRegex(ContractError, "dashboard"):
                validate_obj("consultation-route-receipt", route)

    def test_implicit_continuation_does_not_require_dashboard(self):
        route = make_route(state="implicit", basis="continuation_after_explicit_invocation")
        route.pop("dashboard", None)
        validate_obj("consultation-route-receipt", route)
        self.assertFalse(self.report(route)["required"])

    def test_explicit_dashboard_request_is_mandatory_even_when_invocation_unknown(self):
        route = make_route(state="unknown", basis="unavailable", dashboard_requested=True)
        validate_obj("consultation-route-receipt", route)
        self.assertTrue(self.report(route)["required"])
        route.pop("dashboard")
        with self.assertRaises(ContractError):
            validate_obj("consultation-route-receipt", route)

    def test_ordinary_mention_does_not_create_invocation_trigger(self):
        route = make_route(state="unknown", basis="unavailable")
        route.pop("dashboard", None)
        validate_obj("consultation-route-receipt", route)
        self.assertFalse(self.report(route)["required"])

    def test_non_consultation_invocation_renders_minimal_dashboard(self):
        route = make_route(request_kind="no_case_assessment")
        report = self.report(route, ["classification:urgency:unknown"])
        self.assertIn("Not verified", report["preview"])
        self.assertIn("No case assessment was performed", report["preview"])
        self.assertNotIn("Legal texts this response", report["preview"])

    def test_verified_empty_source_ledger_can_report_zero(self):
        route = make_route(sources=[])
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 0)
        self.assertIn("0 (model-reported)", report["preview"])

    def test_unavailable_source_tracking_reports_unknown_not_zero(self):
        route = make_route(tracking="unavailable", coverage="partial", assessment_status="partial")
        report = self.report(route)
        self.assertIsNone(report["source_metrics"]["response"]["count"])
        self.assertIn("Legal texts this response: unknown", report["preview"])
        self.assertNotIn("Legal texts this response: 0", report["preview"])

    def test_conversation_tracking_can_be_unknown_while_response_is_counted(self):
        route = make_route(sources=[source_record("eu:32004l0038")])
        route["source_ledger"]["conversation_tracking"] = "unavailable"
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 1)
        self.assertIsNone(report["source_metrics"]["conversation"]["count"])
        self.assertIn("Conversation total: unknown", report["preview"])

    def test_repeated_read_and_multiple_pinpoints_count_one_logical_text(self):
        item = source_record("eu:32004l0038")
        item["pinpoints"] = ["Article 2", "Article 3", "Article 5"]
        route = make_route(sources=[item])
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 1)
        self.assertIn("Article 2, Article 3, Article 5", report["preview"])

    def test_language_representations_do_not_inflate_count(self):
        item = source_record("eu:32004l0038", representation_ids=["Directive-EN", "Directive-SV"])
        route = make_route(sources=[item])
        self.assertEqual(self.report(route)["source_metrics"]["response"]["count"], 1)
        route["source_ledger"]["sources"].append(copy.deepcopy(item))
        with self.assertRaisesRegex(DashboardError, "duplicate_logical_source"):
            self.report(route)

    def test_national_library_sections_are_grouped_from_manifests(self):
        ids = [
            "it-01-legislative-decree-no.-30-2007-implementing-free-movement-and-residence-rig",
            "ch-04",
            "fi-aliens-act-fi",
        ]
        route = make_route(sources=[source_record(source_id) for source_id in ids])
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 3)
        self.assertEqual(report["source_metrics"]["response"]["sections"], {
            "Italy": 1, "Switzerland": 1, "Finland": 1,
        })
        for country in ("Italy", "Switzerland", "Finland"):
            self.assertIn(country, report["preview"])

    def test_candidate_source_read_is_counted_and_labelled_unaccepted(self):
        item = source_record("it-01-legislative-decree-no.-30-2007-implementing-free-movement-and-residence-rig")
        route = make_route(sources=[item])
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 1)
        self.assertIn("candidate; not accepted", report["preview"])

    def test_core_manifest_acceptance_overrides_retrieval_index_candidate_label(self):
        accepted = source_record("eu:32004l0038")
        unaccepted = source_record("eu:32008r0767")
        self.assertEqual(accepted["library_state"], "registered_record")
        self.assertEqual(unaccepted["library_state"], "candidate_unaccepted")
        report = self.report(make_route(sources=[accepted, unaccepted]))
        self.assertIn("Directive 2004/38/EC", report["preview"])
        self.assertEqual(report["preview"].count("candidate; not accepted"), 1)

    def test_national_manifest_acceptance_overrides_unrecorded_index_state(self):
        item = source_record("fi-migri-family-residence-card")
        self.assertEqual(item["library_state"], "candidate_unaccepted")
        preview = self.report(make_route(sources=[item]))["preview"]
        self.assertIn("candidate; not accepted", preview)

    def test_all_owner_matched_manifest_acceptance_states_reconcile(self):
        catalog = _load_catalog()
        checked = 0
        for manifest_path in source_library_root().glob("*/**/*manifest*.json"):
            if any(token in manifest_path.name for token in ("capture-results", "monitor-candidate")):
                continue
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            country = manifest_path.relative_to(source_library_root()).parts[0].casefold()
            jurisdiction = (
                "EU" if country == "references" and data.get("pack") == "eu-guidance"
                else COUNTRY_CODES.get(country, country.upper())
            )
            records = []
            for key in ("sources", "documents", "source_records", "entries"):
                if isinstance(data, dict) and isinstance(data.get(key), list):
                    records.extend(data[key])
            for item in records:
                if not isinstance(item, dict) or not isinstance(item.get("accepted"), bool):
                    continue
                source_id = item.get("source_id") or item.get("id")
                metadata = catalog.get(source_id)
                if not metadata or metadata["jurisdiction"] != jurisdiction:
                    continue
                expected = "registered_record" if item["accepted"] else "candidate_unaccepted"
                self.assertEqual(metadata["library_state"], expected, source_id)
                checked += 1
        self.assertGreater(checked, 1000)

    def test_eu_guidance_manifest_uses_eu_core_ownership_and_guidance_category(self):
        source = _load_catalog()["eu-edpb-guidelines-01-2022-access"]
        self.assertEqual(source["section"], "EU core")
        self.assertEqual(source["jurisdiction"], "EU")
        self.assertEqual(_category(source["source_type"], source["section"], source["title"]), "official_guidance")
        preview = self.report(make_route(sources=[source_record("eu-edpb-guidelines-01-2022-access")]))["preview"]
        self.assertIn("EU core · Official guidance", preview)

    def test_title_fallback_classifies_manifest_guidance_and_procedure(self):
        catalog = _load_catalog()
        guidance = catalog["dk-omb-02"]
        visa_guidance = catalog["dk-nyidanmark-visa-after-eu-rules"]
        appeal = catalog["dk-nyidanmark-no-visa"]
        procedure = catalog["se-jo-complaint-form"]
        self.assertEqual(_category(guidance["source_type"], guidance["section"], guidance["title"]), "official_guidance")
        self.assertEqual(_category(visa_guidance["source_type"], visa_guidance["section"], visa_guidance["title"]), "official_guidance")
        self.assertEqual(_category(appeal["source_type"], appeal["section"], appeal["title"]), "procedural_rule")
        self.assertEqual(_category(procedure["source_type"], procedure["section"], procedure["title"]), "procedural_rule")

    def test_title_fallback_classifies_remaining_guidance_and_access_procedures(self):
        catalog = _load_catalog()
        guidance_ids = ("ro-eviza-faq-ro", "se-lifos-rs-030-2021-v5", "se-lifos-rs-008-2022-v6")
        procedure_ids = (
            "ro-igi-petitions", "ro-igi-central-administration", "se-mig-public-documents",
            "se-mig-own-case-documents",
        )
        for source_id in guidance_ids:
            item = catalog[source_id]
            self.assertEqual(_category(item["source_type"], item["section"], item["title"]), "official_guidance")
        for source_id in procedure_ids:
            item = catalog[source_id]
            self.assertEqual(_category(item["source_type"], item["section"], item["title"]), "procedural_rule")

    def test_source_type_taxonomy_keeps_nonlegal_records_out_of_legal_text_categories(self):
        expected = {
            "mission_directory": "publisher_portal",
            "publisher_retrieval_documentation": "source_note",
            "api_access_documentation": "source_note",
            "national_act": "national_legislation",
            "national_act_current_consolidation": "national_legislation",
            "court-case": "case_law",
            "primary_judicial_decision": "case_law",
            "commission_notice": "commission_guidance",
            "not_a_known_source_type": "other_reference",
        }
        for source_type, category in expected.items():
            with self.subTest(source_type=source_type):
                self.assertEqual(_category(source_type, "Italy"), category)

    def test_canonical_problem_records_have_independently_expected_categories(self):
        catalog = _load_catalog()
        expected = {
            "ie-31": "publisher_portal",
            "ie-05": "source_note",
            "bg-eu-free-movement-act": "national_legislation",
            "mig:UM-7584-08": "case_law",
            "eu:c-2023-1392": "commission_guidance",
            "fi-finlex-integration-guide": "source_note",
        }
        for source_id, category in expected.items():
            with self.subTest(source_id=source_id):
                metadata = catalog[source_id]
                self.assertEqual(
                    _category(metadata["source_type"], metadata["section"], metadata["title"]),
                    category,
                )

    def test_mission_directory_and_retrieval_documentation_are_not_counted_as_legal_texts(self):
        records = [
            source_record("https://example.gov/mission", origin="external_official",
                          source_type="mission_directory"),
            source_record("https://example.gov/retrieval", origin="external_official",
                          source_type="publisher_retrieval_documentation"),
        ]
        report = self.report(make_route(sources=records))
        self.assertEqual(report["source_metrics"]["response"]["count"], 0)
        self.assertIn("References or unclassified materials read", report["preview"])

    def test_generic_local_artifact_cannot_claim_runtime_source_reads(self):
        item = source_record("eu:32004l0038")
        route = make_route(tracking="model_declared", sources=[item])
        route["source_ledger"]["sources"][0]["response_provenance"] = "runtime_recorded"
        route["source_ledger"]["sources"][0]["response_evidence_ref"] = "r_0000000000000004"
        with self.assertRaisesRegex(
            DashboardError, "runtime_read_events_not_supported_without_host_attestation"
        ):
            validate_dashboard_receipt(
                route,
                {
                    "r_0000000000000001": {"kind": "conversation_record"},
                    "r_0000000000000004": {
                        "kind": "local_artifact", "artifact_path": "read-event.json",
                        "sha256": "0" * 64,
                    },
                },
                [],
                required_operation_ids=REQUIRED_OPERATIONS[route["request_kind"]],
            )
        route = make_route(tracking="runtime_recorded", sources=[item])
        with self.assertRaisesRegex(
            DashboardError, "runtime_read_events_not_supported_without_host_attestation"
        ):
            self.report(route)

    def test_external_official_text_is_separate_from_library_sections(self):
        item = source_record("https://example.gov/law/1", origin="external_official")
        route = make_route(sources=[item])
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 1)
        self.assertEqual(report["source_metrics"]["response"]["sections"], {})
        self.assertIn("External official", report["preview"])

    def test_external_eu_legislation_is_classified_as_eu_law(self):
        item = source_record("https://eur-lex.europa.eu/example", origin="external_official",
                             source_type="EU directive")
        item["section"] = "External official · EU core"
        item["jurisdiction"] = "EU"
        item["official_url"] = "https://eur-lex.europa.eu/example"
        item["category"] = _category(item["source_type"], item["section"])
        route = make_route(sources=[item])
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 1)
        self.assertIn("EU core · EU law", report["preview"])

    def test_reference_material_does_not_inflate_legal_text_total(self):
        portal = source_record(
            "https://example.gov/portal", origin="external_official",
            response_use="consulted", conversation_use="consulted", source_type="publisher portal",
        )
        route = make_route(sources=[portal])
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 0)
        self.assertIn("References or unclassified materials read", report["preview"])

    def test_external_category_must_match_declared_source_type(self):
        item = source_record("https://example.gov/law/1", origin="external_official")
        item["category"] = "case_law"
        route = make_route(sources=[item])
        with self.assertRaisesRegex(DashboardError, "external_source_category_mismatch"):
            self.report(route)

    def test_external_section_must_match_jurisdiction_owner(self):
        item = source_record("https://example.gov/law/1", origin="external_official")
        item["jurisdiction"] = "IT"
        route = make_route(sources=[item])
        with self.assertRaisesRegex(DashboardError, "external_source_owner_mismatch"):
            self.report(route)

    def test_same_representation_cannot_be_counted_as_two_logical_texts(self):
        first = source_record("eu:32004l0038", representation_ids=["same-representation"])
        second = source_record("eu:32013h0461", representation_ids=["same-representation"])
        route = make_route(sources=[first, second])
        with self.assertRaisesRegex(DashboardError, "representation_counted_as_multiple_texts"):
            self.report(route)

    def test_unread_and_memory_cited_sources_are_not_counted_as_consulted(self):
        identified = source_record("eu:32004l0038", response_use="identified_not_read", conversation_use="identified_not_read")
        memory = source_record("eu:32009r0810", response_use="cited_from_memory", conversation_use="cited_from_memory")
        route = make_route(sources=[identified, memory])
        report = self.report(route)
        self.assertEqual(report["source_metrics"]["response"]["count"], 0)
        self.assertIn("Identified but not read", report["preview"])
        self.assertIn("Cited without a new read", report["preview"])

    def test_unexecuted_checks_cannot_be_called_reviewed(self):
        route = make_route(assessment_status="reviewed")
        with self.assertRaisesRegex(DashboardError, "assessment_status_mismatch"):
            self.report(route, ["operation:c23_guidance:not_checked"])

    def test_missing_required_operation_is_named_on_dashboard(self):
        route = make_route()
        route["operations"] = [item for item in route["operations"] if item["operation_id"] != "c23_guidance"]
        route["dashboard"]["assessment_status"] = "partial"
        route["coverage_claim"] = "partial"
        preview = self.report(route, ["required_operation_missing:c23_guidance"])["preview"]
        self.assertIn("4/5 required or triggered operations recorded complete", preview)
        self.assertIn("**Applicant guidance** · not recorded", preview)
        self.assertIn("Still missing — checks and execution", preview)
        self.assertIn("Applicant guidance", preview)
        self.assertIn("Its findings are absent", preview)

    def test_execution_summary_uses_recorded_operation_statuses(self):
        route = make_route()
        route["operations"][1]["status"] = "not_checked"
        route["operations"][1]["reason_code"] = "not_attempted"
        route["dashboard"]["assessment_status"] = "partial"
        route["coverage_claim"] = "partial"
        preview = self.report(route, ["operation:c23_guidance:not_checked"])["preview"]
        self.assertIn("4/5 required or triggered operations recorded complete", preview)
        self.assertIn("**Applicant guidance** · not checked", preview)

    def test_partial_issue_must_match_dashboard_and_name_effect(self):
        ref = "r_0000000000000008"
        issue = {"issue_ref": ref, "scope_ref": "r_0000000000000003", "signal_ids": ["formal_refusal_issued"],
                 "disposition": "source_missing", "evidence_ref": "r_0000000000000001"}
        summary = {"issue_ref": ref, "title": "Refusal decision", "missing": "Decision notice not inspected",
                   "effect": "The authority's verified grounds remain unknown."}
        route = make_route(coverage="partial", assessment_status="partial", issues=[issue], issue_summaries=[summary])
        self.assertIn("Decision notice not inspected", self.report(route, ["source_preflight:missing"])["preview"])
        route["dashboard"]["issue_summaries"] = []
        with self.assertRaisesRegex(DashboardError, "outstanding_issues_mismatch"):
            self.report(route, ["source_preflight:missing"])

    def test_module_board_distinguishes_current_and_prior_use(self):
        route = make_route()
        route["dashboard"]["module_use"].extend([
            {"module_id": "eudirective-ms-spain", "role": "residence procedure",
             "availability": "available", "response_use": "used", "conversation_use": "used_earlier",
             "conformance": "not_checked", "reason": "Source review only; no C3 pair check was recorded."},
            {"module_id": "eudirective-ac-turkiye", "role": "applicant-country operations",
             "availability": "available", "response_use": "not_used", "conversation_use": "not_used",
             "conformance": "not_applicable", "reason": "No Türkiye mission procedure is implicated."},
        ])
        validate_obj("consultation-route-receipt", route)
        preview = self.report(route)["preview"]
        self.assertIn("used this response; used earlier in this chat", preview)
        self.assertIn("not used this response; not used earlier in this chat", preview)
        self.assertIn("no C3 pair check was recorded", preview)

    def test_compact_dashboard_caps_source_and_module_details_with_overflow_counts(self):
        records = []
        countries = [
            ("Spain", "ES"), ("Italy", "IT"), ("Sweden", "SE"),
            ("Finland", "FI"), ("Germany", "DE"), ("France", "FR"),
            ("Austria", "AT"), ("Belgium", "BE"), ("Netherlands", "NL"),
            ("Poland", "PL"), ("Romania", "RO"),
        ]
        for index in range(20):
            item = source_record(
                f"https://example.gov/law/{index}", origin="external_official",
                source_type="national statute",
            )
            item["title"] = f"Synthetic statute {index}"
            country, country_code = countries[index] if index < len(countries) else countries[0]
            item["section"] = f"External official · {country}"
            item["jurisdiction"] = country_code
            records.append(item)
        route = make_route(sources=records)
        route["dashboard"]["module_use"].extend([
            {
                "module_id": f"review-module-{index}", "role": f"support role {index}",
                "availability": "available", "response_use": "not_used",
                "conversation_use": "not_used", "conformance": "not_applicable",
                "reason": "Not selected for this consultation.",
            }
            for index in range(11)
        ])
        preview = self.report(route)["preview"]
        self.assertIn("Legal texts this response: 20 (model-reported)", preview)
        self.assertEqual(preview.count("Synthetic statute"), 12)
        self.assertIn("Compact view omits 8 source details across 1 additional group", preview)
        self.assertIn("2 additional module-use records are retained in the expanded audit", preview)

    def test_compact_gap_summary_shows_three_items_and_counts_remaining_work(self):
        route = make_route(coverage="partial", assessment_status="partial")
        route["issues"] = []
        route["dashboard"]["issue_summaries"] = []
        gaps = [f"unclassified_gap:{index}" for index in range(5)]
        preview = self.report(route, gaps)["preview"]
        self.assertEqual(preview.count("remains unresolved."), 3)
        self.assertIn("2 additional recorded issues or checks remain", preview)
        self.assertIn("request the expanded audit", preview)

    def test_module_cannot_be_claimed_conformant_without_validator_output(self):
        route = make_route()
        pair_ref = "r_0000000000000009"
        route["module_pairs"] = [{"pair_ref": pair_ref, "manifest_path": "module/manifest.json",
                                  "export_path": "module/export.json"}]
        route["dashboard"]["module_use"] = [{
            "module_id": "eudirective-ms-sweden", "role": "deciding Member State",
            "availability": "available", "response_use": "used", "conversation_use": "not_used",
            "conformance": "conformant", "reason": "Pair validator passed.", "pair_ref": pair_ref,
        }]
        validate_obj("consultation-route-receipt", route)
        with self.assertRaisesRegex(DashboardError, "module_conformance_claim_unverified"):
            validate_dashboard_receipt(
                route, {"r_0000000000000001": {"kind": "conversation_record"}}, [], []
            )

    def test_substantive_dashboard_must_show_core_module_use(self):
        route = make_route()
        route["dashboard"]["module_use"] = []
        with self.assertRaisesRegex(DashboardError, "core_module_use_missing_or_inaccurate"):
            self.report(route)

    def test_module_pair_must_match_a_dashboard_module_entry(self):
        route = make_route()
        pair_ref = "r_0000000000000009"
        route["module_pairs"] = [{"pair_ref": pair_ref, "manifest_path": "module/manifest.json",
                                  "export_path": "module/export.json"}]
        with self.assertRaisesRegex(DashboardError, "module_pair_use_reconciliation_mismatch"):
            self.report(route)

    def test_conformant_pair_identity_and_supported_role_must_match_dashboard(self):
        route = make_route()
        pair_ref = "r_0000000000000009"
        route["module_pairs"] = [{"pair_ref": pair_ref, "manifest_path": "module/manifest.json",
                                  "export_path": "module/export.json"}]
        route["dashboard"]["module_use"].append({
            "module_id": "eudirective-ms-spain", "role": "deciding Member State",
            "availability": "available", "response_use": "used", "conversation_use": "not_used",
            "conformance": "conformant", "reason": "C3 pair validator passed.", "pair_ref": pair_ref,
        })
        report = {"pair_ref": pair_ref, "status": "conformant", "module_id": "eudirective-ms-sweden",
                  "supported_roles": ["deciding_member_state"]}
        with self.assertRaisesRegex(DashboardError, "module_pair_identity_mismatch"):
            validate_dashboard_receipt(
                route, {"r_0000000000000001": {"kind": "conversation_record"}}, [], [report]
            )
        route["dashboard"]["module_use"][-1]["module_id"] = "eudirective-ms-sweden"
        with self.assertRaisesRegex(DashboardError, "module_pair_role_mismatch"):
            validate_dashboard_receipt(
                route, {"r_0000000000000001": {"kind": "conversation_record"}}, [], [report]
            )

    def test_valid_pair_uses_manifest_identity_with_readable_display_labels(self):
        route = make_route()
        pair_ref = "r_0000000000000009"
        route["module_pairs"] = [{"pair_ref": pair_ref, "manifest_path": "module/manifest.json",
                                  "export_path": "module/export.json"}]
        route["dashboard"]["module_use"].append({
            "module_id": "member-state-se-source-pilot", "display_name": "eudirective-ms-sweden",
            "role": "deciding_state", "role_label": "deciding Member State",
            "availability": "available", "response_use": "used", "conversation_use": "not_used",
            "conformance": "conformant", "reason": "C3 pair validator passed.", "pair_ref": pair_ref,
        })
        validate_obj("consultation-route-receipt", route)
        report = {"pair_ref": pair_ref, "status": "conformant",
                  "module_id": "member-state-se-source-pilot", "supported_roles": ["deciding_state"]}
        preview = validate_dashboard_receipt(
            route, {"r_0000000000000001": {"kind": "conversation_record"}}, [], [report]
        )["preview"]
        self.assertIn("**eudirective-ms-sweden** · deciding Member State", preview)
        self.assertIn("C3 conformant", preview)

    def test_pair_reference_cannot_be_reused_by_two_dashboard_modules(self):
        route = make_route()
        pair_ref = "r_0000000000000009"
        route["module_pairs"] = [{"pair_ref": pair_ref, "manifest_path": "module/manifest.json",
                                  "export_path": "module/export.json"}]
        for module_id in ("eudirective-ms-spain", "eudirective-ms-sweden"):
            route["dashboard"]["module_use"].append({
                "module_id": module_id, "role": "deciding_member_state",
                "availability": "available", "response_use": "used", "conversation_use": "not_used",
                "conformance": "not_checked", "reason": "Pair reference reused.", "pair_ref": pair_ref,
            })
        with self.assertRaisesRegex(DashboardError, "duplicate_module_pair_use_reference"):
            self.report(route)

    def test_partial_assessment_must_name_open_work(self):
        route = make_route(coverage="partial", assessment_status="partial")
        with self.assertRaisesRegex(DashboardError, "partial_assessment_without_explained_open_work"):
            self.report(route)

    def test_compact_dashboard_bounds_partial_issue_details_and_counts_the_rest(self):
        issues = []
        summaries = []
        for index in range(1, 5):
            issue_ref = f"r_{index:016x}"
            issues.append({"issue_ref": issue_ref, "scope_ref": "r_0000000000000003",
                           "signal_ids": ["formal_refusal_issued"], "disposition": "fact_missing",
                           "evidence_ref": "r_0000000000000001"})
            summaries.append({"issue_ref": issue_ref, "title": f"Issue {index}",
                              "missing": f"Fact {index} is not confirmed", "effect": f"Effect {index} remains uncertain."})
        route = make_route(coverage="partial", assessment_status="partial", issues=issues,
                           issue_summaries=summaries)
        preview = self.report(route)["preview"]
        self.assertIn("Fact 1 is not confirmed", preview)
        self.assertIn("Fact 3 is not confirmed", preview)
        self.assertNotIn("Fact 4 is not confirmed", preview)
        self.assertIn("1 additional recorded issue or check remains", preview)
        self.assertEqual(len(route["dashboard"]["issue_summaries"]), 4)

    def test_release_binding_requires_exact_dashboard_at_answer_end(self):
        route = make_route()
        with tempfile.TemporaryDirectory(prefix="fm-dashboard-release-") as temp:
            root = Path(temp)
            receipt = root / "receipt.json"
            answer = root / "answer.md"
            binding = root / "binding.json"
            receipt.write_text(json.dumps(route), encoding="utf-8")
            gate = HERE / "consultation_route_gate.py"
            released = HERE / "consultation_release_gate.py"
            checked = subprocess.run([sys.executable, str(gate), str(receipt)], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            preview = json.loads(checked.stdout)["dashboard_preview"]
            answer.write_text("The substantive answer.\n\n" + preview + "\n", encoding="utf-8")
            prepared = subprocess.run([
                sys.executable, str(released), "prepare", "--receipt", str(receipt),
                "--answer", str(answer), "--binding", str(binding),
            ], capture_output=True, text=True)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            answer.write_text("The substantive answer only.\n", encoding="utf-8")
            blocked = subprocess.run([
                sys.executable, str(released), "prepare", "--receipt", str(receipt),
                "--answer", str(answer), "--binding", str(root / "missing-dashboard-binding.json"),
            ], capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("mandatory_dashboard_missing", blocked.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
