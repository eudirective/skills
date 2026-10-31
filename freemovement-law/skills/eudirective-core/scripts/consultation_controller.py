#!/usr/bin/env python3
"""Synthetic-only parent workflow controller for consultation evidence.

This controller owns state transitions. It does not ingest applicant narratives,
perform legal research, establish legal truth, or replace the C3/C27/research
validators. It consumes C27 route selection and records results from existing
validators as separate evidence.
"""
from __future__ import annotations

import argparse
import copy
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

from contract_validate import ContractError, validate_obj
import consultation_issue_selection as issue_selection
import research_gate as research_validator
import consultation_route_gate as route_validator
import module_conformance as module_validator
import issue_source_preflight as preflight_validator


SCHEMA_VERSION = "0.5.0"
GATES = ("intake", "discovery", "research", "assessment", "strategy", "final_review", "reporting")
GATE_INDEX = {name: index for index, name in enumerate(GATES)}
RESEARCH_MODE_MAX_ATTEMPTS = {"quick": 1, "case": 2, "deep": 3}
RESEARCH_NO_PROGRESS_LIMIT = 2
NATIONAL_ROUTING_PATH = issue_selection.ROOT / "references" / "national-source-routing.json"
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
TERMINAL_OBLIGATIONS = {"satisfied", "conditional", "not_applicable"}
EXECUTED_VALIDATOR_KINDS = {"c27_receipt", "module_conformance", "research_gate", "source_preflight"}
RESEARCH_OWNER_FAMILIES = {
    "eu_common_core": "core_source",
    "eu_data_protection": "core_source",
    "eu_swiss_framework": "core_source",
    "member_state_law": "member_state",
    "applicant_country_operations": "applicant_country",
}
SYNTHETIC_TEXT_KEYS = {
    "title", "reason", "scope_note", "exceptions_note", "question", "statement",
    "response_read_evidence", "conversation_read_evidence", "acceptance_criteria",
    "note", "pinpoint", "query", "result_summary", "authority", "publisher_basis", "limitations",
}


def transactional(function):
    """Restore the caller's state if a transition fails validation."""
    @wraps(function)
    def wrapped(state: dict[str, Any], *args: Any, **kwargs: Any):
        before = copy.deepcopy(state)
        try:
            return function(state, *args, **kwargs)
        except Exception:
            state.clear()
            state.update(before)
            raise
    return wrapped


class ControllerError(ValueError):
    pass


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ControllerError(f"invalid_{label}")
    return value


def _unique(values: list[str], label: str) -> list[str]:
    if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
        raise ControllerError(f"invalid_{label}")
    if len(values) != len(set(values)):
        raise ControllerError(f"duplicate_{label}")
    return values


def _advance_revision(state: dict[str, Any], action: str, affected_refs: list[str]) -> None:
    state["revision"] += 1
    state["history"].append({
        "sequence": len(state["history"]) + 1,
        "action": action,
        "revision": state["revision"],
        "affected_refs": sorted(set(affected_refs)),
    })
    if len(state["history"]) > 512:
        raise ControllerError("history_event_budget_exhausted")


def new_state(consultation_id: str, mode: str = "limited") -> dict[str, Any]:
    _id(consultation_id, "consultation_id")
    if mode not in {"full", "limited"}:
        raise ControllerError("invalid_release_mode")
    state = {
        "schema_version": SCHEMA_VERSION,
        "fixture_kind": "synthetic_abstract",
        "consultation_id": consultation_id,
        "revision": 0,
        "active_gate": "intake",
        "intake": {
            "status": "pending", "actor_roles": [], "jurisdictions_by_role": [],
            "legal_question_signal_ids": [], "objectives": [], "urgency": "unknown",
            "urgency_reason_ref": None, "evidence_refs": [], "requested_output": "other",
        },
        "proceedings": [],
        "gates": {
            gate: {"status": "pending", "reason_ref": None, "evidence_refs": [], "obligation_refs": []}
            for gate in GATES
        },
        "obligations": [],
        "issues": [],
        "research_tasks": [],
        "research_findings": [],
        "findings": [],
        "strategy_dispositions": [],
        "claims": [],
        "evidence": [],
        "history": [],
        "release": {"mode": mode, "status": "not_eligible", "open_item_refs": []},
    }
    _advance_revision(state, "initialize", [consultation_id])
    validate_state(state)
    return state


def _evidence_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["evidence_ref"]: item for item in state["evidence"]}


@transactional
def add_evidence(state: dict[str, Any], record: dict[str, Any]) -> None:
    validate_state(state)
    ref = _id(record.get("evidence_ref"), "evidence_ref")
    if ref in _evidence_map(state):
        raise ControllerError("duplicate_evidence_ref")
    if record.get("kind") not in {"conversation_record", "source_review", "c27_receipt", "module_conformance", "research_gate", "source_preflight", "other"}:
        raise ControllerError("invalid_evidence_kind")
    if record.get("kind") in EXECUTED_VALIDATOR_KINDS:
        raise ControllerError("validator_evidence_must_be_created_by_execution")
    if record.get("status") not in {"observed", "passed", "failed", "not_executed", "unavailable"}:
        raise ControllerError("invalid_evidence_status")
    digest = record.get("digest")
    if digest is not None and (not isinstance(digest, str) or not SHA_RE.fullmatch(digest)):
        raise ControllerError("invalid_evidence_digest")
    provenance = _id(record.get("provenance_ref"), "provenance_ref")
    state["evidence"].append({
        **record, "evidence_ref": ref, "provenance_ref": provenance,
        "validator_id": None, "subject_ref": None, "outcome": None,
        "artifact_digests": [], "check_ids": [], "check_bindings": [],
    })
    _advance_revision(state, "evidence_added", [ref])
    validate_state(state)


def _add_obligation(state: dict[str, Any], obligation_ref: str, gate_id: str, *, required: bool = True,
                    status: str = "pending", reason_ref: str | None = None,
                    evidence_refs: list[str] | None = None, subject_ref: str | None = None,
                    depends_on: list[str] | None = None) -> dict[str, Any]:
    obligation_ref = _id(obligation_ref, "obligation_ref")
    if gate_id not in state["gates"]:
        raise ControllerError("unknown_gate")
    if any(x["obligation_ref"] == obligation_ref for x in state["obligations"]):
        raise ControllerError("duplicate_obligation_ref")
    if status not in {"pending", "satisfied", "conditional", "blocked", "not_applicable", "stale"}:
        raise ControllerError("invalid_obligation_status")
    refs = _unique(evidence_refs or [], "evidence_refs")
    known = _evidence_map(state)
    if any(ref not in known for ref in refs):
        raise ControllerError("unknown_obligation_evidence")
    if status in {"conditional", "not_applicable", "blocked"} and (not reason_ref or not refs):
        raise ControllerError("reason_and_evidence_required_for_nonfinal_obligation")
    dependencies = _unique(depends_on or [], "obligation_dependencies")
    existing = {x["obligation_ref"] for x in state["obligations"]}
    if not set(dependencies) <= existing:
        raise ControllerError("obligation_dependency_unknown")
    obligation = {
        "obligation_ref": obligation_ref,
        "gate_id": gate_id,
        "required": bool(required),
        "depends_on": dependencies,
        "status": status,
        "reason_ref": reason_ref,
        "evidence_refs": refs,
        "subject_ref": subject_ref,
    }
    state["obligations"].append(obligation)
    state["gates"][gate_id]["obligation_refs"].append(obligation_ref)
    return obligation


@transactional
def add_obligation(state: dict[str, Any], obligation_ref: str, gate_id: str, *, required: bool = True,
                   depends_on: list[str] | None = None) -> None:
    validate_state(state)
    _add_obligation(state, obligation_ref, gate_id, required=required, depends_on=depends_on)
    _advance_revision(state, "dependency_changed", [obligation_ref])
    validate_state(state)


def _find_obligation(state: dict[str, Any], ref: str) -> dict[str, Any]:
    for item in state["obligations"]:
        if item["obligation_ref"] == ref:
            return item
    raise ControllerError("unknown_obligation")


@transactional
def record_intake_classification(state: dict[str, Any], *, actor_roles: list[str],
                                 jurisdictions_by_role: list[dict[str, str]],
                                 proceedings: list[dict[str, str]],
                                 legal_question_signal_ids: list[str], objectives: list[str],
                                 urgency: str, urgency_reason_ref: str | None,
                                 evidence_refs: list[str], requested_output: str) -> None:
    """Record bounded C23 intake classifications without storing case narratives."""
    validate_state(state)
    if state["active_gate"] != "intake" or state["gates"]["intake"]["status"] in TERMINAL_OBLIGATIONS:
        raise ControllerError("intake_classification_requires_open_intake_gate")
    if state["issues"] or state["proceedings"]:
        raise ControllerError("initial_intake_classification_already_has_case_records")
    actors = _unique(actor_roles, "actor_roles")
    if not actors or not set(actors) <= {
        "applicant", "union_citizen", "family_member", "authority", "service_provider", "representative", "other"
    }:
        raise ControllerError("intake_actor_roles_invalid")
    jurisdictions: list[dict[str, str]] = []
    jurisdiction_keys: set[tuple[str, str]] = set()
    valid_jurisdiction_roles = {
        "applicant_nationality", "applicant_residence", "union_citizen_nationality",
        "union_citizen_residence", "application_location", "deciding_authority",
        "intended_destination", "applicant_country", "other",
    }
    for item in jurisdictions_by_role:
        if not isinstance(item, dict) or set(item) != {"role", "jurisdiction_code"}:
            raise ControllerError("intake_jurisdiction_record_invalid")
        role, code = item["role"], item["jurisdiction_code"]
        if role not in valid_jurisdiction_roles or not isinstance(code, str) or not re.fullmatch(r"(?:EU|[A-Z]{2})", code):
            raise ControllerError("intake_jurisdiction_record_invalid")
        key = (role, code)
        if key in jurisdiction_keys:
            raise ControllerError("duplicate_intake_jurisdiction")
        jurisdiction_keys.add(key)
        jurisdictions.append({"role": role, "jurisdiction_code": code})
    if not jurisdictions:
        raise ControllerError("intake_jurisdictions_required")
    signals = _unique(legal_question_signal_ids, "legal_question_signal_ids")
    try:
        signal_definitions = issue_selection.signal_catalog(issue_selection.load_json(issue_selection.MATRIX_PATH))
    except issue_selection.SelectionError as error:
        raise ControllerError("consultation_signal_catalog_unavailable") from error
    if not signals or not set(signals) <= set(signal_definitions):
        raise ControllerError("intake_legal_question_signals_invalid")
    objective_values = _unique(objectives, "intake_objectives")
    valid_objectives = {
        "obtain_information", "assess_entitlement", "resolve_procedural_barrier", "challenge_decision",
        "preserve_deadline", "prepare_documents", "draft_communication", "plan_preventive_steps", "other",
    }
    if not objective_values or not set(objective_values) <= valid_objectives:
        raise ControllerError("intake_objectives_invalid")
    if requested_output not in {"explanation", "legal_assessment", "options", "action_plan", "draft", "source_research", "document_review", "other"}:
        raise ControllerError("intake_requested_output_invalid")
    if urgency not in {"urgent", "not_urgent", "unknown"}:
        raise ControllerError("intake_urgency_invalid")
    refs = _unique(evidence_refs, "intake_evidence_refs")
    evidence = _evidence_map(state)
    if not refs or any(ref not in evidence or evidence[ref]["kind"] != "conversation_record" for ref in refs):
        raise ControllerError("intake_requires_conversation_evidence")
    if urgency in {"urgent", "unknown"} and (not urgency_reason_ref or not refs):
        raise ControllerError("intake_urgency_requires_reason_and_evidence")
    if not isinstance(proceedings, list) or not proceedings:
        raise ControllerError("intake_proceedings_required")
    seen_proceedings: set[str] = set()
    normalized_proceedings = []
    stages = {
        "prospective", "enquiry", "appointment", "pre_lodgement", "lodgement", "examination", "decision",
        "notification", "appeal", "complaint", "records_access", "residence", "post_issuance", "closed", "unknown",
    }
    required_proceeding_fields = {
        "proceeding_ref", "procedure_type", "stage", "jurisdiction_code", "status", "signal_ids",
    }
    optional_proceeding_fields = {"administrative_outcome_classification", "post_issuance_event_type"}
    for item in proceedings:
        if (not isinstance(item, dict)
                or not required_proceeding_fields <= set(item)
                or set(item) - required_proceeding_fields - optional_proceeding_fields):
            raise ControllerError("intake_proceeding_record_invalid")
        proceeding_ref = _id(item["proceeding_ref"], "proceeding_ref")
        if proceeding_ref in seen_proceedings:
            raise ControllerError("duplicate_proceeding_ref")
        if item["procedure_type"] not in route_validator.PROCEDURE_TYPES or item["stage"] not in stages:
            raise ControllerError("intake_proceeding_classification_invalid")
        code = item["jurisdiction_code"]
        if code is not None and (not isinstance(code, str) or not re.fullmatch(r"(?:EU|[A-Z]{2})", code)):
            raise ControllerError("intake_proceeding_jurisdiction_invalid")
        if item["status"] not in {"prospective", "current", "historical"}:
            raise ControllerError("intake_proceeding_status_invalid")
        outcome_classification = item.get("administrative_outcome_classification")
        if (outcome_classification is not None
                and outcome_classification not in issue_selection.ADMINISTRATIVE_OUTCOMES):
            raise ControllerError("intake_administrative_outcome_classification_invalid")
        post_issuance_event_type = item.get("post_issuance_event_type")
        if (post_issuance_event_type is not None
                and post_issuance_event_type not in issue_selection.POST_ISSUANCE_EVENTS):
            raise ControllerError("intake_post_issuance_event_type_invalid")
        proceeding_signals = _unique(item["signal_ids"], "proceeding_signal_ids")
        if not proceeding_signals or not set(proceeding_signals) <= set(signals):
            raise ControllerError("intake_proceeding_signals_invalid")
        seen_proceedings.add(proceeding_ref)
        normalized_proceedings.append({
            **item, "signal_ids": proceeding_signals,
            "administrative_outcome_classification": outcome_classification,
            "post_issuance_event_type": post_issuance_event_type,
            "discovered_from_finding_ref": None, "evidence_refs": refs[:],
        })
    if set(signals) != {signal for item in normalized_proceedings for signal in item["signal_ids"]}:
        raise ControllerError("intake_signals_must_be_bound_to_proceedings")
    state["intake"] = {
        "status": "classified", "actor_roles": actors,
        "jurisdictions_by_role": jurisdictions, "legal_question_signal_ids": signals,
        "objectives": objective_values, "urgency": urgency,
        "urgency_reason_ref": urgency_reason_ref, "evidence_refs": refs,
        "requested_output": requested_output,
    }
    state["proceedings"] = normalized_proceedings
    _advance_revision(state, "dependency_changed", ["intake", *sorted(seen_proceedings)])
    validate_state(state)


@transactional
def add_proceeding(state: dict[str, Any], *, proceeding_ref: str, procedure_type: str, stage: str,
                   jurisdiction_code: str | None, status: str, discovered_from_finding_ref: str,
                   evidence_refs: list[str], signal_ids: list[str] | None = None,
                   administrative_outcome_classification: str | None = None,
                   post_issuance_event_type: str | None = None) -> None:
    """Add a newly discovered abstract proceeding and reopen discovery."""
    validate_state(state)
    if state["active_gate"] in {"intake", "reporting", "released"}:
        raise ControllerError("new_proceeding_requires_active_review_stage")
    proceeding_ref = _id(proceeding_ref, "proceeding_ref")
    if any(item["proceeding_ref"] == proceeding_ref for item in state["proceedings"]):
        raise ControllerError("duplicate_proceeding_ref")
    if procedure_type not in route_validator.PROCEDURE_TYPES:
        raise ControllerError("new_proceeding_procedure_type_invalid")
    stages = {
        "prospective", "enquiry", "appointment", "pre_lodgement", "lodgement", "examination", "decision",
        "notification", "appeal", "complaint", "records_access", "residence", "post_issuance", "closed", "unknown",
    }
    if stage not in stages or status not in {"prospective", "current", "historical"}:
        raise ControllerError("new_proceeding_classification_invalid")
    if (administrative_outcome_classification is not None
            and administrative_outcome_classification not in issue_selection.ADMINISTRATIVE_OUTCOMES):
        raise ControllerError("new_proceeding_administrative_outcome_classification_invalid")
    if (post_issuance_event_type is not None
            and post_issuance_event_type not in issue_selection.POST_ISSUANCE_EVENTS):
        raise ControllerError("new_proceeding_post_issuance_event_type_invalid")
    if jurisdiction_code is not None and (
        not isinstance(jurisdiction_code, str) or not re.fullmatch(r"(?:EU|[A-Z]{2})", jurisdiction_code)
    ):
        raise ControllerError("new_proceeding_jurisdiction_invalid")
    signals = _unique(signal_ids or [], "new_proceeding_signal_ids")
    try:
        catalog = set(issue_selection.signal_catalog(issue_selection.load_json(issue_selection.MATRIX_PATH)))
    except issue_selection.SelectionError as error:
        raise ControllerError("consultation_signal_catalog_unavailable") from error
    if not set(signals) <= catalog:
        raise ControllerError("new_proceeding_signals_invalid")
    source_finding = next((item for item in state["research_findings"] + state["findings"]
                           if item["finding_ref"] == discovered_from_finding_ref), None)
    if source_finding is None or source_finding["status"] in {"stale", "unsupported"}:
        raise ControllerError("new_proceeding_finding_reference_invalid")
    refs = _unique(evidence_refs, "new_proceeding_evidence_refs")
    known = _evidence_map(state)
    if not refs or any(ref not in known for ref in refs):
        raise ControllerError("new_proceeding_evidence_required")
    source_refs = set(source_finding.get("evidence_refs", []) + source_finding.get("fact_refs", [])
                      + source_finding.get("source_refs", []) + source_finding.get("counterevidence_refs", []))
    if not set(refs) <= source_refs:
        raise ControllerError("new_proceeding_evidence_not_linked_to_finding")
    state["proceedings"].append({
        "proceeding_ref": proceeding_ref, "procedure_type": procedure_type, "stage": stage,
        "jurisdiction_code": jurisdiction_code, "status": status, "signal_ids": signals,
        "administrative_outcome_classification": administrative_outcome_classification,
        "post_issuance_event_type": post_issuance_event_type,
        "discovered_from_finding_ref": discovered_from_finding_ref, "evidence_refs": refs,
    })
    _reopen_from(state, "discovery")
    _advance_revision(state, "dependency_changed", ["proceeding:" + proceeding_ref, discovered_from_finding_ref])
    validate_state(state)


@transactional
def resolve_obligation(state: dict[str, Any], obligation_ref: str, status: str, *,
                       reason_ref: str | None = None, evidence_refs: list[str] | None = None) -> None:
    validate_state(state)
    obligation = _find_obligation(state, obligation_ref)
    if obligation_ref.startswith(("c27:", "assessment:", "research:", "strategy:", "final_review:")):
        raise ControllerError("derived_obligation_cannot_be_resolved_manually")
    if status not in {"satisfied", "conditional", "blocked", "not_applicable", "pending"}:
        raise ControllerError("invalid_obligation_status")
    refs = _unique(evidence_refs or [], "evidence_refs")
    known = _evidence_map(state)
    if any(ref not in known for ref in refs):
        raise ControllerError("unknown_obligation_evidence")
    if status in {"conditional", "blocked", "not_applicable"} and (not reason_ref or not refs):
        raise ControllerError("reason_and_evidence_required_for_nonfinal_obligation")
    if status == "satisfied" and not refs:
        raise ControllerError("satisfied_obligation_requires_evidence")
    obligation.update(status=status, reason_ref=reason_ref, evidence_refs=refs)
    state["gates"][obligation["gate_id"]]["status"] = "pending"
    _reopen_from(state, obligation["gate_id"])
    _advance_revision(state, "dependency_changed", [obligation_ref])
    validate_state(state)


def _selector_requirement(procedure_type: str, signal_ids: list[str], *,
                          administrative_outcome_classification: str | None = None,
                          post_issuance_event_type: str | None = None) -> dict[str, Any]:
    try:
        return issue_selection.select_issue_requirements(
            signal_ids,
            procedure_type=procedure_type,
            administrative_outcome_classification=administrative_outcome_classification,
            post_issuance_event_type=post_issuance_event_type,
        )
    except (issue_selection.SelectionError, KeyError, TypeError) as error:
        raise ControllerError(f"c27_routing_failed:{type(error).__name__}") from error


def _selected_route_requirement(selection: dict[str, Any], route_id: str) -> dict[str, Any]:
    requirement = next((item for item in selection.get("route_requirements", [])
                        if item.get("route_id") == route_id), None)
    if requirement is None:
        raise ControllerError("issue_route_not_selected_by_signals")
    return requirement


def _national_source_owner(owner_id: str, routing: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Resolve a national source-library owner from the existing country registry."""
    if routing is None:
        try:
            routing = issue_selection.load_json(NATIONAL_ROUTING_PATH)
        except issue_selection.SelectionError as error:
            raise ControllerError("research_owner_routing_unavailable") from error
    countries = routing.get("countries")
    if not isinstance(countries, list):
        raise ControllerError("national_source_registry_invalid")

    unregistered = re.fullmatch(r"unregistered:([A-Z]{2})", owner_id)
    if unregistered:
        jurisdiction = unregistered.group(1)
        registered_rows = [
            row for row in countries
            if isinstance(row, dict)
            and row.get("iso_country_code") == jurisdiction
            and isinstance(row.get("plugin_name"), str)
            and isinstance(row.get("source_library_directory"), str)
            and row.get("verification_profile") == "national_source_review"
        ]
        if registered_rows:
            raise ControllerError("national_source_pack_registered_use_registered_owner")
        return {
            "family": "source_library_national", "owner_id": owner_id,
            "iso_country_code": jurisdiction, "registered": False,
            "route_owner_id": "member_state_law",
        }

    rows = [
        row for row in countries
        if isinstance(row, dict)
        and row.get("plugin_name") == owner_id
        and isinstance(row.get("source_library_directory"), str)
        and row.get("verification_profile") == "national_source_review"
    ]
    if len(rows) > 1:
        raise ControllerError("national_source_owner_ambiguous")
    if not rows:
        return None
    jurisdiction = rows[0].get("iso_country_code")
    if not isinstance(jurisdiction, str) or not re.fullmatch(r"[A-Z]{2}", jurisdiction):
        raise ControllerError("national_source_registry_jurisdiction_invalid")
    return {
        "family": "source_library_national", "owner_id": owner_id,
        "iso_country_code": jurisdiction, "registered": True,
        "route_owner_id": "member_state_law",
    }


def _research_owner_family(owner_id: str) -> str | None:
    family = RESEARCH_OWNER_FAMILIES.get(owner_id)
    if family is not None:
        return family
    national_owner = _national_source_owner(owner_id)
    return "source_library_national" if national_owner is not None else None


def _validate_parent_source_pack_digest(owner_id: str, digest: str | None) -> None:
    national_owner = _national_source_owner(owner_id)
    if national_owner is not None and national_owner["registered"]:
        if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
            raise ControllerError("registered_national_source_digest_required")
    elif digest is not None:
        raise ControllerError("source_pack_digest_not_applicable")


def _validate_research_owner_role(owner_id: str, role: str) -> None:
    family = RESEARCH_OWNER_FAMILIES.get(owner_id)
    if family is None:
        national_owner = _national_source_owner(owner_id)
        if national_owner is None:
            raise ControllerError("research_owner_unknown")
        if role != "national_source":
            raise ControllerError("research_owner_role_not_supported")
        return
    try:
        profile = module_validator.load_profile()
    except (module_validator.ConformanceError, ContractError, OSError, ValueError) as error:
        raise ControllerError("research_owner_profile_unavailable") from error
    policies = profile.get("family_policies", {})
    allowed_roles = policies.get(family, {}).get("allowed_roles", [])
    if role not in allowed_roles:
        raise ControllerError("research_owner_role_not_supported")


def _validate_research_owner_assignment(state: dict[str, Any], issue_refs: list[str], owner_id: str,
                                        jurisdiction_ref: str) -> bool:
    """Bind research owners to existing route and country-module registries.

    Returns False only when the route is known but the responsible national
    jurisdiction is still unresolved. The caller may record that task as
    blocked, but may not mark it complete.
    """
    try:
        matrix = issue_selection.load_json(issue_selection.MATRIX_PATH)
        routing = issue_selection.load_json(NATIONAL_ROUTING_PATH)
    except issue_selection.SelectionError as error:
        raise ControllerError("research_owner_routing_unavailable") from error
    owners = matrix.get("source_owners")
    national_owner = _national_source_owner(owner_id, routing) if owner_id not in RESEARCH_OWNER_FAMILIES else None
    route_owner_id = national_owner["route_owner_id"] if national_owner is not None else owner_id
    if not isinstance(owners, dict) or route_owner_id not in owners:
        raise ControllerError("research_owner_unknown")
    if national_owner is not None and jurisdiction_ref != national_owner["iso_country_code"]:
        raise ControllerError("national_source_owner_jurisdiction_mismatch")
    issue_map = {item["issue_ref"]: item for item in state["issues"]}
    if not issue_refs or any(ref not in issue_map for ref in issue_refs):
        raise ControllerError("research_owner_issue_reference_invalid")
    for issue_ref in issue_refs:
        issue = issue_map[issue_ref]
        proceeding = next(
            item for item in state["proceedings"]
            if item["proceeding_ref"] == issue["scope_ref"]
        )
        selection = _selector_requirement(
            proceeding["procedure_type"], issue["signal_ids"],
            administrative_outcome_classification=proceeding.get("administrative_outcome_classification"),
            post_issuance_event_type=proceeding.get("post_issuance_event_type"),
        )
        try:
            route_requirement = _selected_route_requirement(selection, issue["route_id"])
        except ControllerError as error:
            raise ControllerError("research_issue_route_no_longer_selected") from error
        if route_owner_id not in route_requirement["source_owner_ids"]:
            raise ControllerError("research_owner_not_selected_for_issue_route")

    country_codes = {
        item.get("iso_country_code") for item in routing.get("countries", [])
        if isinstance(item, dict) and isinstance(item.get("iso_country_code"), str)
    }
    if route_owner_id == "member_state_law":
        if jurisdiction_ref in {"unknown", "unresolved"}:
            return False
        if ((national_owner is None or national_owner["registered"])
                and jurisdiction_ref not in country_codes):
            raise ControllerError("member_state_research_jurisdiction_unknown")
        proceeding_map = {item["proceeding_ref"]: item for item in state["proceedings"]}
        proceeding_codes = {
            proceeding_map[issue_map[ref]["scope_ref"]].get("jurisdiction_code")
            for ref in issue_refs if issue_map[ref]["scope_ref"] in proceeding_map
        }
        proceeding_codes.discard(None)
        proceeding_codes.discard("EU")
        if len(proceeding_codes) > 1 or (proceeding_codes and jurisdiction_ref not in proceeding_codes):
            raise ControllerError("member_state_research_jurisdiction_mismatch")
        if not proceeding_codes:
            relevant_declared = {
                item["jurisdiction_code"] for item in state["intake"]["jurisdictions_by_role"]
                if item["role"] in {"deciding_authority", "intended_destination"}
            }
            if jurisdiction_ref not in relevant_declared:
                raise ControllerError("member_state_research_jurisdiction_mismatch")
            if len(relevant_declared) != 1:
                return False
        return True

    if route_owner_id == "applicant_country_operations":
        if jurisdiction_ref in {"unknown", "unresolved"}:
            return False
        application_countries = {
            item["jurisdiction_code"] for item in state["intake"]["jurisdictions_by_role"]
            if item["role"] in {"application_location", "applicant_country"}
        }
        if jurisdiction_ref not in application_countries:
            raise ControllerError("applicant_operations_jurisdiction_mismatch")
        modules = [item for item in routing.get("operational_modules", [])
                   if isinstance(item, dict) and item.get("module_family") == "applicant_country"
                   and item.get("jurisdiction") == jurisdiction_ref]
        if not modules:
            return False
        return True

    if route_owner_id == "eu_swiss_framework":
        if jurisdiction_ref not in {"EU", "CH"}:
            raise ControllerError("eu_swiss_research_owner_requires_eu_or_ch_jurisdiction")
        return True

    if jurisdiction_ref != "EU":
        raise ControllerError("eu_research_owner_requires_eu_jurisdiction")
    return True


def _validate_discovery_route_coverage(state: dict[str, Any]) -> None:
    """Require every route selected for each intake proceeding to exist in the issue ledger."""
    for proceeding in state["proceedings"]:
        if not proceeding["signal_ids"]:
            continue
        selection = _selector_requirement(
            proceeding["procedure_type"], proceeding["signal_ids"],
            administrative_outcome_classification=proceeding.get("administrative_outcome_classification"),
            post_issuance_event_type=proceeding.get("post_issuance_event_type"),
        )
        recorded_routes = {
            issue["route_id"] for issue in state["issues"]
            if issue["scope_ref"] == proceeding["proceeding_ref"]
        }
        missing = sorted(set(selection["route_ids"]) - recorded_routes)
        if missing:
            raise ControllerError(
                "discovery_routes_missing:" + proceeding["proceeding_ref"] + ":" + ",".join(missing)
            )


def _validate_strategy_coverage(state: dict[str, Any]) -> None:
    current = [item for item in state["strategy_dispositions"] if item["validity"] == "current"]
    by_issue = {item["issue_ref"]: item for item in current}
    if len(by_issue) != len(current):
        raise ControllerError("duplicate_current_strategy_disposition")
    missing = sorted(
        issue["issue_ref"] for issue in state["issues"]
        if issue["materiality"] != "nonmaterial"
        and issue["applicability"] != "not_applicable"
        and issue["issue_ref"] not in by_issue
    )
    if missing:
        raise ControllerError("material_issue_strategy_disposition_missing:" + ",".join(missing))


@transactional
def add_issue(state: dict[str, Any], *, issue_ref: str, scope_ref: str, route_id: str,
              procedure_type: str, signal_ids: list[str], materiality: str = "unknown",
              applicability: str = "applicable", applicability_reason_ref: str | None = None,
              applicability_evidence_refs: list[str] | None = None,
              discovered_from_finding_ref: str | None = None,
              depends_on: list[str] | None = None) -> dict[str, Any]:
    """Add an abstract issue and derive its C27 obligations from the existing selector."""
    validate_state(state)
    issue_ref, scope_ref, route_id = (_id(issue_ref, "issue_ref"), _id(scope_ref, "scope_ref"), _id(route_id, "route_id"))
    if any(item["issue_ref"] == issue_ref for item in state["issues"]):
        raise ControllerError("duplicate_issue_ref")
    if materiality not in {"material", "nonmaterial", "unknown"}:
        raise ControllerError("invalid_materiality")
    if state["intake"]["status"] != "classified":
        raise ControllerError("issue_requires_classified_intake")
    proceeding = next((item for item in state["proceedings"] if item["proceeding_ref"] == scope_ref), None)
    if proceeding is None:
        raise ControllerError("issue_proceeding_reference_unknown")
    if proceeding["procedure_type"] != procedure_type:
        raise ControllerError("issue_procedure_type_does_not_match_proceeding")
    if applicability not in {"applicable", "not_applicable", "unresolved"}:
        raise ControllerError("invalid_applicability")
    applicability_refs = _unique(applicability_evidence_refs or [], "applicability_evidence_refs")
    known_evidence = _evidence_map(state)
    if any(ref not in known_evidence for ref in applicability_refs):
        raise ControllerError("applicability_evidence_reference_invalid")
    if applicability == "not_applicable" and (not applicability_reason_ref or not applicability_refs):
        raise ControllerError("not_applicable_requires_reason_and_evidence")
    discovery_dependency = None
    if discovered_from_finding_ref is not None:
        _id(discovered_from_finding_ref, "discovered_from_finding_ref")
        source_finding = next((item for item in state["research_findings"] + state["findings"]
                               if item["finding_ref"] == discovered_from_finding_ref), None)
        if source_finding is None or source_finding["status"] in {"stale", "unsupported"}:
            raise ControllerError("discovery_finding_reference_invalid")
        discovery_dependency = (
            "research-finding:" if any(item["finding_ref"] == discovered_from_finding_ref for item in state["research_findings"])
            else "finding:"
        ) + discovered_from_finding_ref
    signals = _unique(signal_ids, "signal_ids")
    if not set(signals) <= set(proceeding["signal_ids"]) and discovered_from_finding_ref is None:
        raise ControllerError("issue_signal_not_in_intake_or_discovered_by_research")
    route_input_signals = proceeding["signal_ids"] if discovered_from_finding_ref is None else signals
    selection = _selector_requirement(
        procedure_type, route_input_signals,
        administrative_outcome_classification=proceeding.get("administrative_outcome_classification"),
        post_issuance_event_type=proceeding.get("post_issuance_event_type"),
    )
    route_requirement = _selected_route_requirement(selection, route_id)
    if set(signals) != set(route_requirement["relevant_signal_ids"]):
        raise ControllerError("issue_signals_do_not_match_route_conditions")
    checks = [{
        "check_id": check_id,
        "selection": "selected",
        "assessment": "not_applicable" if applicability == "not_applicable" else "not_checked",
        "reason_ref": applicability_reason_ref if applicability == "not_applicable" else None,
        "evidence_refs": applicability_refs if applicability == "not_applicable" else [],
    } for check_id in route_requirement["check_ids"]]
    issue_dependencies = set(_unique(depends_on or [], "issue_dependencies"))
    issue_dependencies.add(f"proceeding:{scope_ref}")
    issue_dependencies.update(f"evidence:{ref}" for ref in proceeding["evidence_refs"] + applicability_refs)
    if discovery_dependency:
        issue_dependencies.add(discovery_dependency)
    issue = {
        "issue_ref": issue_ref,
        "scope_ref": scope_ref,
        "route_id": route_id,
        "procedure_type": procedure_type,
        "signal_ids": signals,
        "materiality": materiality,
        "applicability": applicability,
        "applicability_reason_ref": applicability_reason_ref,
        "applicability_evidence_refs": applicability_refs,
        "discovered_from_finding_ref": discovered_from_finding_ref,
        "c27_check_ids": route_requirement["check_ids"],
        "checks": checks,
        "depends_on": sorted(issue_dependencies),
        "status": "open",
    }
    if applicability == "not_applicable":
        issue["status"] = "closed"
    state["issues"].append(issue)
    issue_status = "not_applicable" if applicability == "not_applicable" else "pending"
    _add_obligation(
        state, f"c27:{issue_ref}", "discovery", status=issue_status,
        reason_ref=applicability_reason_ref if applicability == "not_applicable" else None,
        evidence_refs=applicability_refs if applicability == "not_applicable" else [], subject_ref=issue_ref,
    )
    for check in checks:
        _add_obligation(
            state, f"c27:{issue_ref}:{check['check_id']}", "discovery",
            status="not_applicable" if applicability == "not_applicable" else "pending",
            reason_ref=applicability_reason_ref if applicability == "not_applicable" else None,
            evidence_refs=applicability_refs if applicability == "not_applicable" else [], subject_ref=issue_ref,
        )
    _add_obligation(
        state, f"assessment:{issue_ref}", "assessment", required=materiality != "nonmaterial",
        status="not_applicable" if applicability == "not_applicable" else "pending",
        reason_ref=applicability_reason_ref if applicability == "not_applicable" else None,
        evidence_refs=applicability_refs if applicability == "not_applicable" else [], subject_ref=issue_ref,
    )
    _add_obligation(
        state, f"strategy:{issue_ref}", "strategy", required=materiality != "nonmaterial",
        status="not_applicable" if applicability == "not_applicable" else "pending",
        reason_ref=applicability_reason_ref if applicability == "not_applicable" else None,
        evidence_refs=applicability_refs if applicability == "not_applicable" else [], subject_ref=issue_ref,
    )
    state["gates"]["discovery"]["status"] = "pending"
    _reopen_from(state, "discovery")
    state["active_gate"] = "discovery"
    state["release"]["status"] = "not_eligible"
    _advance_revision(state, "issue_added", [f"issue:{issue_ref}"])
    validate_state(state)
    return copy.deepcopy(issue)


@transactional
def record_check(state: dict[str, Any], issue_ref: str, check_id: str, assessment: str, *,
                 reason_ref: str | None = None, evidence_refs: list[str] | None = None) -> None:
    validate_state(state)
    if state["active_gate"] != "discovery":
        raise ControllerError("c27_check_review_requires_discovery_gate")
    issue = next((x for x in state["issues"] if x["issue_ref"] == issue_ref), None)
    if issue is None:
        raise ControllerError("unknown_issue")
    check = next((x for x in issue["checks"] if x["check_id"] == check_id), None)
    if check is None:
        raise ControllerError("c27_check_not_selected_for_issue")
    allowed = {"not_checked", "assessed", "source_verified", "unavailable", "not_applicable", "stale"}
    if assessment not in allowed:
        raise ControllerError("invalid_check_assessment")
    refs = _unique(evidence_refs or [], "evidence_refs")
    evidence = _evidence_map(state)
    if any(ref not in evidence for ref in refs):
        raise ControllerError("unknown_check_evidence")
    expected_kind = {
        "assessed": {"conversation_record"},
        "source_verified": {"source_review"},
    }
    if assessment in expected_kind and (not refs or any(evidence[ref]["kind"] not in expected_kind[assessment] for ref in refs)):
        raise ControllerError("check_method_evidence_mismatch")
    if assessment in {"unavailable", "not_applicable", "stale"} and (not reason_ref or not refs):
        raise ControllerError("check_reason_and_evidence_required")
    if assessment == "not_checked" and (reason_ref or refs):
        raise ControllerError("not_checked_must_not_claim_review_evidence")
    check.update(assessment=assessment, reason_ref=reason_ref, evidence_refs=refs)
    _refresh_issue_state(state, issue)
    _reopen_from(state, "discovery")
    _advance_revision(state, "dependency_changed", [f"c27:{issue_ref}:{check_id}"])
    validate_state(state)


def _derive_issue_state(issue: dict[str, Any], check_obligations: list[dict[str, Any]]) -> tuple[str, str, str | None, list[str]]:
    """Return issue and parent-obligation states from the current C27 check rows."""
    issue_evidence = sorted({ref for item in check_obligations for ref in item["evidence_refs"]})
    if issue["applicability"] == "not_applicable":
        return "closed", "not_applicable", issue["applicability_reason_ref"], issue["applicability_evidence_refs"]
    if any(item["status"] == "stale" for item in check_obligations):
        return "stale", "stale", None, []
    if any(item["status"] == "blocked" for item in check_obligations):
        blocked = next(item for item in check_obligations if item["status"] == "blocked")
        return "open", "blocked", blocked["reason_ref"], issue_evidence
    if any(item["status"] == "pending" for item in check_obligations):
        return "open", "pending", None, []
    if check_obligations and all(item["status"] in TERMINAL_OBLIGATIONS for item in check_obligations):
        conditional = any(item["status"] in {"conditional", "not_applicable"} for item in check_obligations)
        reason_ref = next((item["reason_ref"] for item in check_obligations if item["reason_ref"]), None)
        return "assessed", "conditional" if conditional else "satisfied", reason_ref, issue_evidence
    return "open", "pending", None, []


def _refresh_issue_state(state: dict[str, Any], issue: dict[str, Any]) -> None:
    """Keep C27 issue/check obligations derived from their recorded assessments."""
    issue_ref = issue["issue_ref"]
    check_obligations = []
    status_by_assessment = {
        "not_checked": "pending", "assessed": "satisfied", "source_verified": "satisfied",
        "unavailable": "blocked", "not_applicable": "not_applicable", "stale": "stale",
    }
    for check in issue["checks"]:
        status = status_by_assessment[check["assessment"]]
        obligation = _find_obligation(state, f"c27:{issue_ref}:{check['check_id']}")
        obligation.update(status=status, reason_ref=check["reason_ref"], evidence_refs=check["evidence_refs"])
        check_obligations.append(obligation)
    issue_status, parent_status, parent_reason, parent_evidence = _derive_issue_state(issue, check_obligations)
    issue["status"] = issue_status
    _find_obligation(state, f"c27:{issue_ref}").update(
        status=parent_status, reason_ref=parent_reason, evidence_refs=parent_evidence,
    )
    if issue_status == "stale":
        _find_obligation(state, f"assessment:{issue_ref}").update(status="stale", reason_ref="c27_check_stale")
    else:
        _refresh_assessment_obligation(state, issue_ref)


@transactional
def add_research_task(state: dict[str, Any], *, task_ref: str, issue_refs: list[str], owner_id: str,
                      jurisdiction_ref: str, role: str, mode: str, mode_reason_ref: str,
                      acceptance_criteria_refs: list[str],
                      depends_on: list[str] | None = None, required: bool = True,
                      research_id: str | None = None, child_task_ids: list[str] | None = None,
                      synthetic_issue_id: str | None = None,
                      research_question_sha256: str | None = None,
                      source_pack_sha256: str | None = None) -> None:
    validate_state(state)
    if state["active_gate"] != "research":
        raise ControllerError("research_task_requires_research_gate")
    task_ref = _id(task_ref, "task_ref")
    if any(t["task_ref"] == task_ref for t in state["research_tasks"]):
        raise ControllerError("duplicate_task_ref")
    issues = _unique(issue_refs, "issue_refs")
    issue_ids = {x["issue_ref"] for x in state["issues"]}
    if not issues or not set(issues) <= issue_ids:
        raise ControllerError("research_task_issue_reference_invalid")
    owner_value = _id(owner_id, "owner_id")
    jurisdiction_value = _id(jurisdiction_ref, "jurisdiction_ref")
    role_value = _id(role, "role")
    if mode not in RESEARCH_MODE_MAX_ATTEMPTS:
        raise ControllerError("research_mode_invalid")
    mode_reason = _id(mode_reason_ref, "mode_reason_ref")
    mode_evidence = _evidence_map(state).get(mode_reason)
    if (mode_evidence is None or mode_evidence["kind"] not in {"conversation_record", "other"}
            or mode_evidence["status"] != "observed"):
        raise ControllerError("research_mode_reason_evidence_invalid")
    _validate_research_owner_role(owner_value, role_value)
    _validate_parent_source_pack_digest(owner_value, source_pack_sha256)
    _validate_research_owner_assignment(state, issues, owner_value, jurisdiction_value)
    criteria = _unique(acceptance_criteria_refs, "acceptance_criteria_refs")
    if not criteria:
        raise ControllerError("research_acceptance_criteria_required")
    child_ids = _unique(child_task_ids or [], "child_task_ids")
    bound = [research_id is not None, bool(child_ids), synthetic_issue_id is not None,
             research_question_sha256 is not None]
    if any(bound) and not all(bound):
        raise ControllerError("research_child_binding_incomplete")
    task_dependencies = set(_unique(depends_on or [], "task_dependencies"))
    task_dependencies.update(f"issue:{ref}" for ref in issues)
    task_dependencies.add(f"evidence:{mode_reason}")
    task = {
        "task_ref": task_ref, "issue_refs": issues, "owner_id": owner_value,
        "jurisdiction_ref": jurisdiction_value, "role": role_value,
        "source_pack_sha256": source_pack_sha256,
        "mode": mode, "mode_reason_ref": mode_reason,
        "max_attempts": RESEARCH_MODE_MAX_ATTEMPTS[mode], "attempt_records": [],
        "no_progress_streak": 0,
        "acceptance_criteria_refs": criteria, "depends_on": sorted(task_dependencies),
        "required": bool(required), "status": "pending", "evidence_refs": [mode_reason],
        "counterevidence_refs": [], "finding_refs": [],
        "research_id": research_id, "child_task_ids": child_ids,
        "synthetic_issue_id": synthetic_issue_id, "research_question_sha256": research_question_sha256,
    }
    state["research_tasks"].append(task)
    _add_obligation(state, f"research:{task_ref}", "research", required=required, subject_ref=task_ref)
    state["active_gate"] = "research"
    _reopen_from(state, "research")
    _advance_revision(state, "dependency_changed", [f"research:{task_ref}"])
    validate_state(state)


@transactional
def record_research_attempt(state: dict[str, Any], *, task_ref: str, attempt_ref: str,
                            result: str, evidence_ref: str, progress_sha256: str | None = None,
                            reason_ref: str | None = None) -> None:
    """Record one bounded research attempt without treating a retry as evidence of success."""
    validate_state(state)
    if state["active_gate"] != "research":
        raise ControllerError("research_attempt_requires_research_gate")
    task = next((item for item in state["research_tasks"] if item["task_ref"] == task_ref), None)
    if task is None:
        raise ControllerError("unknown_research_task")
    if task["status"] not in {"pending", "in_progress", "open"}:
        raise ControllerError("research_attempt_requires_open_task")
    attempt_ref = _id(attempt_ref, "research_attempt_ref")
    if any(attempt["attempt_ref"] == attempt_ref
           for row in state["research_tasks"] for attempt in row["attempt_records"]):
        raise ControllerError("duplicate_research_attempt_ref")
    if len(task["attempt_records"]) >= task["max_attempts"]:
        raise ControllerError("research_attempt_budget_exhausted")
    if result not in {"progress", "no_progress", "blocked"}:
        raise ControllerError("research_attempt_result_invalid")
    evidence = _evidence_map(state).get(evidence_ref)
    if evidence is None or evidence["kind"] not in {"source_review", "other"} or evidence["status"] != "observed":
        raise ControllerError("research_attempt_evidence_invalid")
    if result == "progress":
        if not isinstance(progress_sha256, str) or not SHA_RE.fullmatch(progress_sha256):
            raise ControllerError("research_progress_digest_required")
        if any(attempt["progress_sha256"] == progress_sha256 for attempt in task["attempt_records"]):
            raise ControllerError("research_attempt_repeats_prior_progress")
        if reason_ref is not None:
            _id(reason_ref, "research_attempt_reason_ref")
        task["no_progress_streak"] = 0
    else:
        if progress_sha256 is not None:
            raise ControllerError("nonprogress_attempt_must_not_claim_progress_digest")
        _id(reason_ref, "research_attempt_reason_ref")
        if result == "no_progress":
            task["no_progress_streak"] += 1
        else:
            task["no_progress_streak"] = 0
    task["attempt_records"].append({
        "attempt_ref": attempt_ref,
        "result": result,
        "evidence_ref": evidence_ref,
        "progress_sha256": progress_sha256,
        "reason_ref": reason_ref,
    })
    task["evidence_refs"] = sorted(set(task["evidence_refs"] + [evidence_ref]))
    task["depends_on"] = sorted(set(task["depends_on"]) | {f"evidence:{evidence_ref}"})
    task["status"] = "in_progress"

    attempt_budget_exhausted = len(task["attempt_records"]) >= task["max_attempts"]
    no_progress_exhausted = task["no_progress_streak"] >= RESEARCH_NO_PROGRESS_LIMIT
    if result == "blocked" or attempt_budget_exhausted or no_progress_exhausted:
        task["status"] = "blocked"
        block_reason = reason_ref or "research_attempt_budget_exhausted"
        obligation = _find_obligation(state, f"research:{task_ref}")
        obligation.update(status="blocked", reason_ref=block_reason, evidence_refs=task["evidence_refs"])
    _advance_revision(state, "dependency_changed", [f"research:{task_ref}", f"research-attempt:{attempt_ref}"])
    validate_state(state)


def _validator_evidence(state: dict[str, Any], *, evidence_ref: str, kind: str, status: str,
                        provenance_ref: str, validator_id: str, subject_ref: str,
                        outcome: str, artifact_digests: list[str], check_ids: list[str] | None = None,
                        check_bindings: list[dict[str, str]] | None = None) -> None:
    ref = _id(evidence_ref, "evidence_ref")
    if ref in _evidence_map(state):
        raise ControllerError("duplicate_evidence_ref")
    digest_payload = json.dumps({
        "kind": kind, "status": status, "validator_id": validator_id,
        "subject_ref": subject_ref, "outcome": outcome,
        "artifact_digests": sorted(artifact_digests), "check_ids": sorted(set(check_ids or [])),
        "check_bindings": sorted(check_bindings or [], key=lambda item: (item["scope_ref"], item["check_id"])),
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")
    state["evidence"].append({
        "evidence_ref": ref, "kind": kind, "status": status,
        "digest": hashlib.sha256(digest_payload).hexdigest(),
        "provenance_ref": _id(provenance_ref, "provenance_ref"),
        "validator_id": _id(validator_id, "validator_id"),
        "subject_ref": _id(subject_ref, "subject_ref"), "outcome": outcome,
        "artifact_digests": sorted(artifact_digests), "check_ids": sorted(set(check_ids or [])),
        "check_bindings": sorted(check_bindings or [], key=lambda item: (item["scope_ref"], item["check_id"])),
    })
    _advance_revision(state, "evidence_added", [ref])


def _regular_artifact_bytes(paths: list[Path]) -> list[bytes]:
    values = []
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError
        values.append(path.read_bytes())
    return values


def _check_synthetic_text(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _check_synthetic_text(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_synthetic_text(child, path + (str(index),))
    elif isinstance(value, str) and path and path[-1] in SYNTHETIC_TEXT_KEYS:
        for label, pattern in route_validator._PII_PATTERNS:
            if label != "exact_date" and pattern.search(value):
                raise ControllerError("synthetic_privacy_screen_failed:" + label)


@transactional
def record_module_conformance_validation(state: dict[str, Any], manifest_path: Path, export_path: Path, *,
                                         module_id: str, evidence_ref: str, provenance_ref: str) -> dict[str, Any]:
    """Run the existing C3 module-pair validator and record its output fingerprint."""
    validate_state(state)
    if state["fixture_kind"] != "synthetic_abstract":
        raise ControllerError("module_validator_accepts_synthetic_abstract_inputs_only")
    paths = [manifest_path, export_path]
    try:
        before = _regular_artifact_bytes(paths)
        report = module_validator.validate_paths(*paths)
        if _regular_artifact_bytes(paths) != before:
            raise ControllerError("module_artifact_changed_during_validation")
        outcome = report.get("status", "unknown")
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="module_conformance",
            status="passed" if outcome == "conformant" and report.get("module_id") == module_id else "failed",
            provenance_ref=provenance_ref, validator_id="module_conformance.py", subject_ref=module_id,
            outcome=outcome if report.get("module_id") == module_id else "module_id_mismatch",
            artifact_digests=[hashlib.sha256(data).hexdigest() for data in before],
        )
        validate_state(state)
        return report
    except OSError:
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="module_conformance", status="unavailable",
            provenance_ref=provenance_ref, validator_id="module_conformance.py", subject_ref=module_id,
            outcome="artifact_unavailable", artifact_digests=[],
        )
        validate_state(state)
        return {"status": "unavailable"}
    except (ContractError, module_validator.ConformanceError, ControllerError) as error:
        digests = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.is_file() and not path.is_symlink()]
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="module_conformance", status="failed",
            provenance_ref=provenance_ref, validator_id="module_conformance.py", subject_ref=module_id,
            outcome="validator_rejected", artifact_digests=digests,
        )
        validate_state(state)
        return {"status": "invalid", "error": str(error)}


@transactional
def record_source_preflight_validation(state: dict[str, Any], task_ref: str, preflight_path: Path, plan_path: Path,
                                       bundle_path: Path, *, evidence_ref: str,
                                       provenance_ref: str) -> dict[str, Any]:
    """Run the existing research/source-ownership preflight on synthetic artifacts."""
    validate_state(state)
    if state["fixture_kind"] != "synthetic_abstract":
        raise ControllerError("source_preflight_accepts_synthetic_abstract_inputs_only")
    task = next((item for item in state["research_tasks"] if item["task_ref"] == task_ref), None)
    if task is None:
        raise ControllerError("unknown_research_task")
    paths = [preflight_path, plan_path, bundle_path]
    try:
        before = _regular_artifact_bytes(paths)
        preflight = json.loads(before[0].decode("utf-8"))
        if preflight.get("preflight_id") is None:
            raise ControllerError("source_preflight_id_missing")
        plan = json.loads(before[1].decode("utf-8"))
        bundle = json.loads(before[2].decode("utf-8"))
        if (plan.get("purpose") != "synthetic_issue_followup"
                or "SYNTHETIC" not in str(plan.get("synthetic_binding", {}).get("issue_id", "")).upper()
                or plan.get("mode") != task.get("mode")
                or task.get("research_id") != plan.get("research_id")
                or task.get("synthetic_issue_id") != plan.get("synthetic_binding", {}).get("issue_id")
                or task.get("research_question_sha256") != hashlib.sha256(str(plan.get("question", "")).encode("utf-8")).hexdigest()
                or set(task.get("child_task_ids", [])) != {item.get("task_id") for item in plan.get("tasks", [])}
                or preflight.get("research_id") != plan.get("research_id")):
            raise ControllerError("source_preflight_requires_synthetic_research")
        _check_synthetic_text({"plan": plan, "bundle": bundle})
        parent_issues = {item["issue_ref"]: item for item in state["issues"]}
        preflight_issues = preflight.get("issues", [])
        if any(item.get("consultation_issue_ref") not in task["issue_refs"]
               or item.get("consultation_issue_ref") not in parent_issues
               or item.get("consultation_scope_ref") != parent_issues[item["consultation_issue_ref"]]["scope_ref"]
               or item.get("owner", {}).get("owner_id") != task["owner_id"]
               or item.get("owner", {}).get("jurisdiction") != task["jurisdiction_ref"]
               or item.get("owner", {}).get("role") != task["role"]
               for item in preflight_issues):
            raise ControllerError("source_preflight_parent_issue_binding_invalid")
        report = preflight_validator.validate_source_preflight(preflight_path, plan_path, bundle_path)
        if _regular_artifact_bytes(paths) != before:
            raise ControllerError("source_preflight_artifact_changed_during_validation")
        outcome = report.get("status", "unknown")
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="source_preflight",
            status="failed" if outcome == "rejected_accounted_claim" else "passed",
            provenance_ref=provenance_ref, validator_id="issue_source_preflight.py",
            subject_ref=preflight["preflight_id"], outcome=outcome,
            artifact_digests=[hashlib.sha256(data).hexdigest() for data in before],
        )
        validate_state(state)
        return report
    except OSError:
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="source_preflight", status="unavailable",
            provenance_ref=provenance_ref, validator_id="issue_source_preflight.py",
            subject_ref="preflight_unavailable", outcome="artifact_unavailable", artifact_digests=[],
        )
        validate_state(state)
        return {"status": "unavailable"}
    except (UnicodeDecodeError, json.JSONDecodeError, ContractError, preflight_validator.SourcePreflightError,
            research_validator.ResearchGateError, ControllerError) as error:
        digests = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.is_file() and not path.is_symlink()]
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="source_preflight", status="failed",
            provenance_ref=provenance_ref, validator_id="issue_source_preflight.py",
            subject_ref="preflight_invalid", outcome="validator_rejected", artifact_digests=digests,
        )
        validate_state(state)
        return {"status": "invalid", "error": str(error)}


@transactional
def record_c27_receipt_validation(state: dict[str, Any], receipt_path: Path, *,
                                  evidence_ref: str, provenance_ref: str) -> dict[str, Any]:
    """Run the existing route/C27 receipt validator and bind its exact input hash."""
    validate_state(state)
    if state["fixture_kind"] != "synthetic_abstract":
        raise ControllerError("c27_receipt_validator_accepts_synthetic_abstract_inputs_only")
    if receipt_path.is_symlink() or not receipt_path.is_file():
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="c27_receipt", status="unavailable",
            provenance_ref=provenance_ref, validator_id="consultation_route_gate.py",
            subject_ref="receipt_unavailable", outcome="artifact_unavailable", artifact_digests=[],
        )
        validate_state(state)
        return {"status": "unavailable", "error": "receipt_artifact_unavailable"}
    before = receipt_path.read_bytes()
    try:
        route = json.loads(before.decode("utf-8"))
        result = route_validator.validate_route(receipt_path)
        after = receipt_path.read_bytes()
        if before != after:
            raise ControllerError("c27_receipt_changed_during_validation")
        check_bindings = [
            {
                "check_id": item["record"]["check_id"],
                "scope_ref": item["scope_ref"],
                "receipt_status": item["record"]["status"],
                "method": item["record"]["method"],
            }
            for item in route.get("c27_checks", [])
        ]
        check_ids = sorted({item["check_id"] for item in check_bindings})
        outcome = result["status"]
        execution_status = "failed" if outcome == "rejected_comprehensive_claim" else "passed"
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="c27_receipt", status=execution_status,
            provenance_ref=provenance_ref, validator_id="consultation_route_gate.py",
            subject_ref=result["route_ref"], outcome=outcome,
            artifact_digests=[hashlib.sha256(before).hexdigest()], check_ids=check_ids,
            check_bindings=check_bindings,
        )
        validate_state(state)
        return result
    except (UnicodeDecodeError, json.JSONDecodeError, route_validator.RouteGateError, ContractError, OSError, ControllerError) as error:
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="c27_receipt", status="failed",
            provenance_ref=provenance_ref, validator_id="consultation_route_gate.py",
            subject_ref="receipt_invalid", outcome="validator_rejected",
            artifact_digests=[hashlib.sha256(before).hexdigest()],
        )
        validate_state(state)
        return {"status": "invalid", "error": str(error)}


@transactional
def record_research_validation(state: dict[str, Any], task_ref: str, plan_path: Path, bundle_path: Path, *,
                               evidence_ref: str, provenance_ref: str) -> dict[str, Any]:
    """Run the existing research validator on one explicitly synthetic child task."""
    validate_state(state)
    task = next((item for item in state["research_tasks"] if item["task_ref"] == task_ref), None)
    if task is None:
        raise ControllerError("unknown_research_task")
    artifacts: list[bytes] = []
    try:
        for path in (plan_path, bundle_path):
            if path.is_symlink() or not path.is_file():
                raise FileNotFoundError
            artifacts.append(path.read_bytes())
        plan = json.loads(artifacts[0].decode("utf-8"))
        bundle = json.loads(artifacts[1].decode("utf-8"))
        _check_synthetic_text(plan)
        _check_synthetic_text(bundle)
        if bundle.get("contract_version") != "0.4.0":
            raise ControllerError("research_child_access_contract_required")
        if (plan.get("purpose") != "synthetic_issue_followup"
                or "SYNTHETIC" not in str(plan.get("synthetic_binding", {}).get("issue_id", "")).upper()
                or plan.get("mode") != task.get("mode")
                or task.get("research_id") != plan.get("research_id")
                or task.get("synthetic_issue_id") != plan.get("synthetic_binding", {}).get("issue_id")
                or task.get("research_question_sha256") != hashlib.sha256(str(plan.get("question", "")).encode("utf-8")).hexdigest()
                or set(task.get("child_task_ids", [])) != {item.get("task_id") for item in plan.get("tasks", [])}):
            raise ControllerError("research_child_binding_invalid")
        for planned_task in plan.get("tasks", []):
            owner = planned_task.get("owner", {})
            expected_family = _research_owner_family(task["owner_id"])
            if (owner.get("family") != expected_family
                    or owner.get("owner_id") != task["owner_id"]
                    or owner.get("jurisdiction") != task["jurisdiction_ref"]
                    or owner.get("role") != task["role"]
                    or (expected_family == "source_library_national"
                        and owner.get("source_pack_sha256") != task.get("source_pack_sha256"))):
                raise ControllerError("research_child_owner_mismatch")
        report = research_validator.validate_research(plan_path, bundle_path)
        if [plan_path.read_bytes(), bundle_path.read_bytes()] != artifacts:
            raise ControllerError("research_artifact_changed_during_validation")
        artifact_digests = [hashlib.sha256(data).hexdigest() for data in artifacts]
        outcome = "research_complete" if report.get("research_complete") else "research_incomplete"
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="research_gate", status="passed",
            provenance_ref=provenance_ref, validator_id="research_gate.py", subject_ref=task_ref,
            outcome=outcome, artifact_digests=artifact_digests,
        )
        validate_state(state)
        return report
    except OSError:
        artifact_digests = [hashlib.sha256(data).hexdigest() for data in artifacts]
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="research_gate", status="unavailable",
            provenance_ref=provenance_ref, validator_id="research_gate.py", subject_ref=task_ref,
            outcome="artifact_unavailable", artifact_digests=artifact_digests,
        )
        validate_state(state)
        return {"status": "unavailable", "research_complete": False}
    except (UnicodeDecodeError, json.JSONDecodeError, ContractError, research_validator.ResearchGateError, ControllerError) as error:
        artifact_digests = [hashlib.sha256(data).hexdigest() for data in artifacts]
        _validator_evidence(
            state, evidence_ref=evidence_ref, kind="research_gate", status="failed",
            provenance_ref=provenance_ref, validator_id="research_gate.py", subject_ref=task_ref,
            outcome=("privacy_screen_failed" if str(error).startswith("synthetic_privacy_screen_failed") else
                     "binding_invalid" if str(error) in {"research_child_binding_invalid", "research_child_owner_mismatch",
                                                          "research_child_access_contract_required"}
                     else "artifact_invalid"), artifact_digests=artifact_digests,
        )
        validate_state(state)
        return {"status": "invalid", "research_complete": False, "error": str(error)}


@transactional
def set_research_status(state: dict[str, Any], task_ref: str, status: str, *, evidence_refs: list[str] | None = None,
                        counterevidence_refs: list[str] | None = None, finding_refs: list[str] | None = None,
                        reason_ref: str | None = None) -> None:
    validate_state(state)
    if state["active_gate"] != "research":
        raise ControllerError("research_update_requires_research_gate")
    task = next((t for t in state["research_tasks"] if t["task_ref"] == task_ref), None)
    if task is None:
        raise ControllerError("unknown_research_task")
    if status not in {"complete", "open", "blocked", "no_source_found", "conflict_unresolved", "not_applicable", "stale"}:
        raise ControllerError("invalid_research_status")
    if status == "open" and (
        task["status"] == "blocked"
        or len(task["attempt_records"]) >= task["max_attempts"]
        or task["no_progress_streak"] >= RESEARCH_NO_PROGRESS_LIMIT
    ):
        raise ControllerError("research_retry_budget_exhausted")
    evidence_refs = _unique(evidence_refs or [], "evidence_refs")
    counterevidence_refs = _unique(counterevidence_refs or [], "counterevidence_refs")
    finding_refs = _unique(finding_refs or [], "finding_refs")
    known = _evidence_map(state)
    if any(ref not in known for ref in evidence_refs + counterevidence_refs):
        raise ControllerError("research_evidence_reference_invalid")
    if status == "complete":
        if not task["attempt_records"] or task["attempt_records"][-1]["result"] != "progress":
            raise ControllerError("complete_research_requires_recorded_progress")
        if not _validate_research_owner_assignment(state, task["issue_refs"], task["owner_id"], task["jurisdiction_ref"]):
            raise ControllerError("research_owner_jurisdiction_unresolved")
        if not any(known[ref]["kind"] == "research_gate" and known[ref]["status"] == "passed"
                   and known[ref].get("validator_id") == "research_gate.py"
                   and known[ref].get("subject_ref") == task_ref
                   and known[ref].get("outcome") == "research_complete"
                   for ref in evidence_refs):
            raise ControllerError("complete_research_requires_passed_research_validator")
        if not evidence_refs or not counterevidence_refs or not finding_refs:
            raise ControllerError("complete_research_requires_evidence_counterevidence_and_findings")
    research_findings = {f["finding_ref"]: f for f in state["research_findings"]}
    if any(ref not in research_findings or research_findings[ref]["task_ref"] != task_ref for ref in finding_refs):
        raise ControllerError("research_finding_reference_invalid")
    if status == "complete" and any(research_findings[ref]["status"] not in {"supported", "conditional"} for ref in finding_refs):
        raise ControllerError("complete_research_requires_reviewable_findings")
    if status in {"blocked", "no_source_found", "conflict_unresolved", "not_applicable"} and (not reason_ref or not evidence_refs):
        raise ControllerError("research_gap_requires_reason_and_evidence")
    if status == "stale" and (not reason_ref or not evidence_refs):
        raise ControllerError("stale_research_requires_reason_and_evidence")
    evidence_refs = sorted(set(task["evidence_refs"]) | set(evidence_refs))
    task.update(status=status, evidence_refs=evidence_refs,
                counterevidence_refs=counterevidence_refs, finding_refs=finding_refs)
    task["depends_on"] = sorted(set(task["depends_on"]) | {
        f"evidence:{ref}" for ref in evidence_refs + counterevidence_refs
    })
    obligation = _find_obligation(state, f"research:{task_ref}")
    obligation_status = {
        "complete": "satisfied", "open": "conditional", "no_source_found": "conditional",
        "conflict_unresolved": "conditional", "blocked": "blocked", "not_applicable": "not_applicable", "stale": "stale",
    }[status]
    if obligation_status in {"conditional", "blocked", "not_applicable"} and (not reason_ref or not evidence_refs):
        raise ControllerError("research_noncomplete_state_requires_reason_and_evidence")
    if obligation_status in {"conditional", "blocked", "satisfied", "not_applicable"} and evidence_refs:
        obligation.update(status=obligation_status, reason_ref=reason_ref, evidence_refs=evidence_refs)
    elif status == "complete":
        raise ControllerError("complete_research_requires_validated_evidence")
    elif status == "not_applicable":
        obligation.update(status="not_applicable", reason_ref=reason_ref, evidence_refs=evidence_refs)
    elif status == "stale":
        obligation.update(status="stale", reason_ref=reason_ref, evidence_refs=evidence_refs)
    else:
        obligation.update(status="pending", reason_ref=reason_ref, evidence_refs=evidence_refs)
    _advance_revision(state, "dependency_changed", [f"research:{task_ref}"])
    validate_state(state)


@transactional
def add_research_finding(state: dict[str, Any], *, finding_ref: str, task_ref: str, issue_refs: list[str],
                         evidence_refs: list[str], counterevidence_refs: list[str], status: str) -> None:
    validate_state(state)
    if state["active_gate"] != "research":
        raise ControllerError("research_finding_requires_research_gate")
    task = next((item for item in state["research_tasks"] if item["task_ref"] == task_ref), None)
    if task is None:
        raise ControllerError("unknown_research_task")
    finding_ref = _id(finding_ref, "research_finding_ref")
    if any(item["finding_ref"] == finding_ref for item in state["research_findings"]):
        raise ControllerError("duplicate_research_finding_ref")
    if status not in {"supported", "conditional", "unresolved"}:
        raise ControllerError("invalid_research_finding_status")
    issues = _unique(issue_refs, "research_finding_issue_refs")
    if not issues or not set(issues) <= set(task["issue_refs"]):
        raise ControllerError("research_finding_issue_reference_invalid")
    evidence_refs = _unique(evidence_refs, "research_finding_evidence_refs")
    counterevidence_refs = _unique(counterevidence_refs, "research_finding_counterevidence_refs")
    known = _evidence_map(state)
    if not evidence_refs or not counterevidence_refs or any(ref not in known for ref in evidence_refs + counterevidence_refs):
        raise ControllerError("research_finding_requires_evidence_and_counterevidence")
    if status == "supported" and not any(known[ref]["kind"] == "source_review" and known[ref]["status"] == "observed" for ref in evidence_refs):
        raise ControllerError("supported_research_finding_requires_observed_source_review")
    research_dependencies = {f"research:{task_ref}"}
    research_dependencies.update(f"issue:{ref}" for ref in issues)
    research_dependencies.update(f"evidence:{ref}" for ref in evidence_refs + counterevidence_refs)
    record = {
        "finding_ref": finding_ref, "task_ref": task_ref, "issue_refs": issues,
        "evidence_refs": evidence_refs, "counterevidence_refs": counterevidence_refs,
        "depends_on": sorted(research_dependencies), "status": status,
    }
    state["research_findings"].append(record)
    task["finding_refs"].append(finding_ref)
    _advance_revision(state, "dependency_changed", ["research-finding:" + finding_ref])
    validate_state(state)


@transactional
def add_finding(state: dict[str, Any], *, finding_ref: str, issue_refs: list[str], task_refs: list[str],
                fact_refs: list[str], source_refs: list[str], exception_refs: list[str],
                counterevidence_refs: list[str], status: str, statement: str,
                depends_on: list[str], research_finding_refs: list[str] | None = None,
                condition_refs: list[str] | None = None, uncertainty_refs: list[str] | None = None) -> None:
    validate_state(state)
    if state["active_gate"] != "assessment":
        raise ControllerError("finding_requires_assessment_gate")
    finding_ref = _id(finding_ref, "finding_ref")
    if any(f["finding_ref"] == finding_ref for f in state["findings"]):
        raise ControllerError("duplicate_finding_ref")
    issue_ids = {i["issue_ref"] for i in state["issues"]}
    task_ids = {t["task_ref"] for t in state["research_tasks"]}
    if not issue_refs or not set(issue_refs) <= issue_ids or not set(task_refs) <= task_ids:
        raise ControllerError("finding_issue_or_task_reference_invalid")
    if status not in {"supported", "conditional", "unresolved", "unsupported"}:
        raise ControllerError("invalid_finding_status")
    if status == "supported" and (not source_refs or not counterevidence_refs):
        raise ControllerError("supported_finding_requires_source_and_counterevidence_review")
    if not isinstance(statement, str) or not statement.strip() or len(statement) > 2000:
        raise ControllerError("finding_statement_required")
    _check_synthetic_text({"statement": statement})
    evidence = _evidence_map(state)
    issue_refs = _unique(issue_refs, "finding_issues")
    task_refs = _unique(task_refs, "finding_tasks")
    research_refs = _unique(research_finding_refs or [], "finding_research_findings")
    conditions = _unique(condition_refs or [], "condition_refs")
    uncertainties = _unique(uncertainty_refs or [], "uncertainty_refs")
    research_finding_map = {item["finding_ref"]: item for item in state["research_findings"]}
    if any(ref not in research_finding_map for ref in research_refs):
        raise ControllerError("finding_research_finding_reference_invalid")
    linked_research = [research_finding_map[ref] for ref in research_refs]
    linked_task_refs = {item["task_ref"] for item in linked_research}
    if linked_task_refs != set(task_refs):
        raise ControllerError("finding_task_research_finding_binding_invalid")
    if any(not set(item["issue_refs"]) <= set(issue_refs) for item in linked_research):
        raise ControllerError("finding_research_issue_binding_invalid")
    refs_by_class = (
        (fact_refs, {"conversation_record"}, "finding_fact_evidence_invalid"),
        (source_refs, {"source_review"}, "finding_source_evidence_invalid"),
        (exception_refs, {"source_review"}, "finding_exception_evidence_invalid"),
        (conditions, {"source_review", "conversation_record"}, "finding_condition_evidence_invalid"),
        (counterevidence_refs, {"source_review", "conversation_record"}, "finding_counterevidence_invalid"),
        (uncertainties, {"source_review", "conversation_record", "other"}, "finding_uncertainty_evidence_invalid"),
    )
    for refs, kinds, error_code in refs_by_class:
        if any(ref not in evidence or evidence[ref]["kind"] not in kinds for ref in refs):
            raise ControllerError(error_code)
    if status in {"supported", "conditional"} and (not fact_refs or not source_refs or not counterevidence_refs):
        raise ControllerError("reviewable_finding_requires_facts_sources_and_counterevidence")
    if status in {"supported", "conditional"} and not linked_research:
        raise ControllerError("reviewable_finding_requires_linked_research_findings")
    if status == "supported":
        tasks = {item["task_ref"]: item for item in state["research_tasks"]}
        if any(item["status"] != "supported" for item in linked_research):
            raise ControllerError("supported_finding_requires_supported_research")
        if any(tasks[ref]["status"] != "complete" for ref in task_refs):
            raise ControllerError("supported_finding_requires_complete_research")
        linked_source_refs = {ref for item in linked_research for ref in item["evidence_refs"]}
        if not set(source_refs) <= linked_source_refs:
            raise ControllerError("finding_source_not_bound_to_research_finding")
    if status == "conditional" and any(item["status"] not in {"supported", "conditional"} for item in linked_research):
        raise ControllerError("conditional_finding_requires_reviewable_research")
    if status == "unsupported" and not (fact_refs or source_refs or counterevidence_refs):
        raise ControllerError("unsupported_finding_requires_review_evidence")
    if status == "unresolved" and not uncertainties:
        raise ControllerError("unresolved_finding_requires_uncertainty_evidence")
    if status in {"conditional", "unresolved"} and not uncertainties:
        raise ControllerError("nonfinal_finding_requires_uncertainty_evidence")
    all_refs = set(fact_refs + source_refs + exception_refs + conditions + counterevidence_refs + uncertainties)
    if not all_refs <= evidence.keys():
        raise ControllerError("finding_evidence_reference_invalid")
    dependencies = set(_unique(depends_on, "finding_dependencies"))
    dependencies.update(f"issue:{ref}" for ref in issue_refs)
    dependencies.update(f"research:{ref}" for ref in task_refs)
    dependencies.update(f"research-finding:{ref}" for ref in research_refs)
    dependencies.update(f"evidence:{ref}" for ref in all_refs)
    finding = {
        "finding_ref": finding_ref, "statement": statement.strip(), "issue_refs": _unique(issue_refs, "finding_issues"),
        "task_refs": task_refs, "research_finding_refs": research_refs, "fact_refs": _unique(fact_refs, "fact_refs"),
        "source_refs": _unique(source_refs, "source_refs"), "exception_refs": _unique(exception_refs, "exception_refs"),
        "condition_refs": conditions, "counterevidence_refs": _unique(counterevidence_refs, "counterevidence_refs"),
        "uncertainty_refs": uncertainties,
        "assessment_reason_ref": None if status == "supported" else f"reason_{finding_ref}",
        "status": status,
        "depends_on": sorted(dependencies),
    }
    state["findings"].append(finding)
    if len(issue_refs) != 1:
        raise ControllerError("assessment_finding_must_have_one_issue_scope")
    _reopen_from(state, "assessment")
    _refresh_assessment_obligation(state, issue_refs[0])
    _advance_revision(state, "dependency_changed", [f"finding:{finding_ref}"])
    validate_state(state)


def _refresh_assessment_obligation(state: dict[str, Any], issue_ref: str) -> None:
    all_findings = [item for item in state["findings"] if issue_ref in item["issue_refs"]]
    findings = [item for item in all_findings if item["status"] != "stale"]
    obligation = _find_obligation(state, f"assessment:{issue_ref}")
    if not findings:
        obligation.update(
            status="stale" if all_findings else "pending",
            reason_ref="dependency_changed" if all_findings else None,
            evidence_refs=[],
        )
        return
    evidence_refs = sorted({
        ref for item in findings
        for ref in item["fact_refs"] + item["source_refs"] + item["exception_refs"]
        + item["condition_refs"] + item["counterevidence_refs"] + item["uncertainty_refs"]
    })
    if any(item["status"] in {"conditional", "unresolved"} for item in findings):
        obligation.update(status="conditional", reason_ref="reason_assessment_conditional", evidence_refs=evidence_refs)
    else:
        obligation.update(status="satisfied", reason_ref=None, evidence_refs=evidence_refs)


@transactional
def add_strategy_disposition(state: dict[str, Any], *, issue_ref: str, status: str,
                             action_code: str, urgency: str, finding_refs: list[str],
                             alternative_codes: list[str], rationale_ref: str | None,
                             qualification_ref: str | None, evidence_refs: list[str]) -> None:
    """Record one C25 disposition per issue, bound to assessed findings or a documented gap."""
    validate_state(state)
    if state["active_gate"] != "strategy":
        raise ControllerError("strategy_disposition_requires_strategy_gate")
    issue = next((item for item in state["issues"] if item["issue_ref"] == issue_ref), None)
    if issue is None:
        raise ControllerError("strategy_issue_reference_invalid")
    if status not in {"recommended", "conditional", "no_action", "deferred"}:
        raise ControllerError("strategy_disposition_status_invalid")
    actions = {"clarification_request", "application_lodgement", "deadline_protection", "formal_review",
               "supervisory_complaint", "conduct_complaint", "records_access", "evidence_preservation",
               "seek_qualified_advice", "monitor_response", "other", "none"}
    if action_code not in actions:
        raise ControllerError("strategy_action_code_invalid")
    if urgency not in {"urgent", "time_sensitive", "routine", "none"}:
        raise ControllerError("strategy_urgency_invalid")
    alternatives = _unique(alternative_codes, "strategy_alternative_codes")
    if not set(alternatives) <= actions:
        raise ControllerError("strategy_alternative_code_invalid")
    refs = _unique(finding_refs, "strategy_finding_refs")
    findings = {item["finding_ref"]: item for item in state["findings"]}
    if not refs or any(ref not in findings or issue_ref not in findings[ref]["issue_refs"] for ref in refs):
        if status in {"recommended", "conditional"}:
            raise ControllerError("strategy_recommendation_requires_issue_findings")
        if any(ref not in findings or issue_ref not in findings[ref]["issue_refs"] for ref in refs):
            raise ControllerError("strategy_finding_reference_invalid")
    evidence = _evidence_map(state)
    refs_evidence = _unique(evidence_refs, "strategy_evidence_refs")
    if not refs_evidence or any(ref not in evidence for ref in refs_evidence):
        raise ControllerError("strategy_evidence_required")
    if status == "recommended":
        if action_code == "none" or urgency == "none" or rationale_ref is None:
            raise ControllerError("strategy_recommendation_details_required")
        if any(findings[ref]["status"] != "supported" for ref in refs):
            raise ControllerError("strategy_recommendation_requires_supported_findings")
        finding_evidence = {
            ref for item in (findings[ref] for ref in refs)
            for ref in item["fact_refs"] + item["source_refs"] + item["exception_refs"]
            + item["condition_refs"] + item["counterevidence_refs"] + item["uncertainty_refs"]
        }
        if not set(refs_evidence) <= finding_evidence:
            raise ControllerError("strategy_evidence_not_linked_to_findings")
        if qualification_ref is not None:
            raise ControllerError("unqualified_recommendation_cannot_have_qualification")
    elif status == "conditional":
        if action_code == "none" or urgency == "none" or rationale_ref is None or qualification_ref is None:
            raise ControllerError("conditional_strategy_details_required")
        if any(findings[ref]["status"] not in {"supported", "conditional"} for ref in refs):
            raise ControllerError("conditional_recommendation_requires_reviewable_findings")
        finding_evidence = {
            ref for item in (findings[ref] for ref in refs)
            for ref in item["fact_refs"] + item["source_refs"] + item["exception_refs"]
            + item["condition_refs"] + item["counterevidence_refs"] + item["uncertainty_refs"]
        }
        if not set(refs_evidence) <= finding_evidence:
            raise ControllerError("strategy_evidence_not_linked_to_findings")
    else:
        if action_code != "none" or urgency != "none" or rationale_ref is None:
            raise ControllerError("nonrecommendation_requires_reason")
        if status == "deferred" and qualification_ref is None:
            raise ControllerError("deferred_strategy_requires_qualification")
        if status == "no_action" and qualification_ref is not None:
            raise ControllerError("no_action_cannot_have_qualification")
    strategy = {
        "disposition_ref": "disp_" + hashlib.sha256(
            f"{state['consultation_id']}:{issue_ref}:{state['revision'] + 1}".encode()
        ).hexdigest()[:20],
        "issue_ref": issue_ref, "status": status, "action_code": action_code, "urgency": urgency,
        "finding_refs": refs, "alternative_codes": alternatives,
        "rationale_ref": rationale_ref, "qualification_ref": qualification_ref,
        "evidence_refs": refs_evidence,
        "depends_on": sorted({f"issue:{issue_ref}", *(f"finding:{ref}" for ref in refs), *(f"evidence:{ref}" for ref in refs_evidence)}),
        "validity": "current",
    }
    prior = next((item for item in state["strategy_dispositions"]
                  if item["issue_ref"] == issue_ref and item["validity"] == "current"), None)
    if prior:
        raise ControllerError("strategy_disposition_already_current")
    state["strategy_dispositions"].append(strategy)
    obligation_ref = f"strategy:{issue_ref}"
    try:
        obligation = _find_obligation(state, obligation_ref)
    except ControllerError:
        _add_obligation(state, obligation_ref, "strategy", status="pending", subject_ref=issue_ref)
        obligation = _find_obligation(state, obligation_ref)
    obligation_status = "conditional" if status in {"conditional", "deferred"} else "satisfied"
    obligation.update(
        status=obligation_status,
        reason_ref=rationale_ref if obligation_status == "conditional" else None,
        evidence_refs=refs_evidence,
    )
    _reopen_from(state, "strategy")
    _advance_revision(state, "strategy_disposition_added", [f"strategy:{issue_ref}", *strategy["depends_on"]])
    validate_state(state)


@transactional
def add_claim(state: dict[str, Any], *, claim_ref: str, issue_refs: list[str], finding_refs: list[str],
              evidence_refs: list[str], treatment: str, statement: str,
              depends_on: list[str], qualification_ref: str | None = None,
              qualification_text: str | None = None) -> None:
    validate_state(state)
    if state["active_gate"] != "final_review":
        raise ControllerError("claim_requires_final_review_gate")
    claim_ref = _id(claim_ref, "claim_ref")
    if any(c["claim_ref"] == claim_ref for c in state["claims"]):
        raise ControllerError("duplicate_claim_ref")
    if treatment not in {"established", "qualified", "withheld"}:
        raise ControllerError("invalid_claim_treatment")
    if not isinstance(statement, str) or not statement.strip() or len(statement) > 2000:
        raise ControllerError("claim_statement_required")
    _check_synthetic_text({"statement": statement})
    findings = {f["finding_ref"]: f for f in state["findings"]}
    if any(ref not in findings for ref in finding_refs):
        raise ControllerError("claim_finding_reference_invalid")
    issue_ids = {i["issue_ref"] for i in state["issues"]}
    if not issue_refs or not set(issue_refs) <= issue_ids:
        raise ControllerError("claim_issue_reference_invalid")
    evidence = _evidence_map(state)
    if any(ref not in evidence for ref in evidence_refs):
        raise ControllerError("claim_evidence_reference_invalid")
    if treatment == "established" and (not finding_refs or any(findings[ref]["status"] != "supported" for ref in finding_refs)):
        raise ControllerError("established_claim_requires_supported_findings")
    if treatment == "established":
        tasks = {task["task_ref"]: task for task in state["research_tasks"]}
        required_tasks = {task_ref for ref in finding_refs for task_ref in findings[ref]["task_refs"]}
        if any(tasks[ref]["status"] != "complete" for ref in required_tasks):
            raise ControllerError("established_claim_requires_complete_research_tasks")
    if treatment == "qualified" and (not finding_refs or not qualification_ref):
        raise ControllerError("qualified_claim_requires_finding_and_qualification")
    if treatment in {"qualified", "withheld"} and (not isinstance(qualification_text, str) or not qualification_text.strip()):
        raise ControllerError("qualified_or_withheld_claim_requires_qualification_text")
    if treatment == "established" and qualification_text is not None:
        raise ControllerError("established_claim_must_not_hide_qualification_text")
    if treatment == "qualified" and any(findings[ref]["status"] in {"unsupported", "stale"} for ref in finding_refs):
        raise ControllerError("qualified_claim_requires_reviewable_findings")
    if treatment == "withheld" and not qualification_ref:
        raise ControllerError("withheld_claim_requires_reason")
    if treatment in {"established", "qualified"} and not evidence_refs:
        raise ControllerError("released_claim_requires_evidence")
    if treatment == "withheld" and not evidence_refs:
        raise ControllerError("withheld_claim_requires_evidence")
    if treatment in {"qualified", "withheld"}:
        _check_synthetic_text({"statement": qualification_text})
    if treatment in {"established", "qualified"}:
        allowed_evidence = {
            ref for finding_ref in finding_refs
            for ref in (
                findings[finding_ref]["fact_refs"] + findings[finding_ref]["source_refs"]
                + findings[finding_ref]["exception_refs"] + findings[finding_ref]["condition_refs"]
                + findings[finding_ref]["counterevidence_refs"] + findings[finding_ref]["uncertainty_refs"]
            )
        }
        if not set(evidence_refs) <= allowed_evidence:
            raise ControllerError("claim_evidence_not_bound_to_linked_findings")
    dependencies = set(_unique(depends_on, "claim_dependencies"))
    dependencies.update(f"issue:{ref}" for ref in issue_refs)
    dependencies.update(f"finding:{ref}" for ref in finding_refs)
    dependencies.update(f"evidence:{ref}" for ref in evidence_refs)
    for finding_ref in finding_refs:
        dependencies.update(f"research:{ref}" for ref in findings[finding_ref]["task_refs"])
    state["claims"].append({
        "claim_ref": claim_ref, "statement": statement.strip(), "issue_refs": _unique(issue_refs, "claim_issues"),
        "finding_refs": _unique(finding_refs, "claim_findings"), "evidence_refs": _unique(evidence_refs, "claim_evidence"),
        "treatment": treatment, "qualification_ref": qualification_ref,
        "qualification_text": qualification_text.strip() if qualification_text is not None else None,
        "depends_on": sorted(dependencies), "validity": "current",
    })
    _add_obligation(
        state, f"final_review:{claim_ref}", "final_review",
        status="satisfied" if treatment == "established" else "conditional",
        reason_ref=qualification_ref if treatment != "established" else None,
        evidence_refs=evidence_refs, subject_ref=claim_ref,
    )
    _reopen_from(state, "final_review")
    _advance_revision(state, "dependency_changed", [f"claim:{claim_ref}"])
    validate_state(state)


def _reopen_from(state: dict[str, Any], gate_id: str) -> None:
    start = GATE_INDEX[gate_id]
    for gate in GATES[start:]:
        state["gates"][gate]["status"] = "stale" if gate != gate_id else "pending"
        state["gates"][gate]["reason_ref"] = None
        state["gates"][gate]["evidence_refs"] = []
    state["active_gate"] = gate_id
    state["release"]["status"] = "not_eligible"
    state["release"]["open_item_refs"] = []


def _validate_final_review_coverage(state: dict[str, Any]) -> None:
    """Require a current response disposition for every material issue."""
    current_claims = [claim for claim in state["claims"] if claim["validity"] == "current"]
    covered = {issue_ref for claim in current_claims for issue_ref in claim["issue_refs"]}
    missing = sorted(
        issue["issue_ref"] for issue in state["issues"]
        if issue["materiality"] == "material" and issue["issue_ref"] not in covered
    )
    if missing:
        raise ControllerError("material_issue_claim_disposition_missing:" + ",".join(missing))
    findings = {finding["finding_ref"]: finding for finding in state["findings"]}
    for claim in current_claims:
        linked_issue_refs = {
            issue_ref for finding_ref in claim["finding_refs"]
            for issue_ref in findings[finding_ref]["issue_refs"]
        }
        if claim["finding_refs"] and not set(claim["issue_refs"]) <= linked_issue_refs:
            raise ControllerError("claim_issue_not_supported_by_linked_findings:" + claim["claim_ref"])


@transactional
def complete_gate(state: dict[str, Any], gate_id: str, *, reason_ref: str | None = None,
                  evidence_refs: list[str] | None = None) -> str:
    validate_state(state)
    if gate_id not in GATE_INDEX:
        raise ControllerError("unknown_gate")
    if state["active_gate"] != gate_id:
        raise ControllerError("gate_not_active")
    if gate_id == "intake" and state["intake"]["status"] != "classified":
        raise ControllerError("intake_classification_required")
    if gate_id == "discovery":
        _validate_discovery_route_coverage(state)
    if gate_id == "strategy":
        _validate_strategy_coverage(state)
    if gate_id == "final_review":
        _validate_final_review_coverage(state)
    refs = state["gates"][gate_id]["obligation_refs"]
    obligations = {item["obligation_ref"]: item for item in state["obligations"]}
    items = [obligations[ref] for ref in refs]
    for item in items:
        dependency_items = [obligations[ref] for ref in item["depends_on"]]
        if any(dep["status"] not in TERMINAL_OBLIGATIONS for dep in dependency_items):
            raise ControllerError("obligation_dependency_unresolved:" + item["obligation_ref"])
        if any(dep["status"] == "conditional" for dep in dependency_items) and item["required"] and item["status"] == "satisfied":
            raise ControllerError("conditional_dependency_cannot_be_silently_closed:" + item["obligation_ref"])
    carried_research_blocks = {
        item["obligation_ref"] for item in items
        if gate_id == "research" and item["obligation_ref"].startswith("research:")
        and item["status"] == "blocked"
    }
    pending = [
        item["obligation_ref"] for item in items
        if item["required"] and item["status"] not in TERMINAL_OBLIGATIONS
        and item["obligation_ref"] not in carried_research_blocks
    ]
    if pending:
        raise ControllerError("required_obligations_open:" + ",".join(pending))
    for item in items:
        if item["status"] in {"conditional", "blocked", "not_applicable"} and (not item["reason_ref"] or not item["evidence_refs"]):
            raise ControllerError("obligation_gap_missing_reason_or_evidence:" + item["obligation_ref"])
    if any(item["status"] == "conditional" for item in items) or carried_research_blocks:
        status = "conditional"
    elif items and all(item["status"] == "not_applicable" for item in items):
        status = "not_applicable"
    else:
        status = "satisfied"
    gate_evidence = _unique(evidence_refs or [], "gate_evidence_refs")
    known_evidence = _evidence_map(state)
    if any(ref not in known_evidence for ref in gate_evidence):
        raise ControllerError("unknown_gate_evidence")
    if status in {"conditional", "not_applicable"} and (not reason_ref or not gate_evidence):
        # Obligation-level reasons/evidence alone do not silently become a gate summary.
        raise ControllerError("gate_reason_and_evidence_required")
    if status == "satisfied" and not gate_evidence and items:
        gate_evidence = sorted({ref for item in items for ref in item["evidence_refs"]})
    if not gate_evidence:
        raise ControllerError("gate_completion_requires_evidence")
    state["gates"][gate_id].update(status=status, reason_ref=reason_ref, evidence_refs=gate_evidence)
    if gate_id != "reporting":
        next_gate = GATES[GATE_INDEX[gate_id] + 1]
        state["active_gate"] = next_gate
        if state["gates"][next_gate]["status"] == "stale":
            state["gates"][next_gate]["status"] = "pending"
    else:
        state["active_gate"] = "released"
    _advance_revision(state, "gate_completed", [gate_id])
    validate_state(state)
    return status


@transactional
def invalidate(state: dict[str, Any], changed_ref: str) -> list[str]:
    """Invalidate the transitive dependants of a changed fact, source, stage, or finding."""
    validate_state(state)
    changed_ref = _id(changed_ref, "changed_ref")
    changed = {changed_ref}
    if ":" not in changed_ref:
        changed.update({f"fact:{changed_ref}", f"evidence:{changed_ref}"})
    invalidated: set[str] = set()

    def mark(token: str) -> bool:
        invalidated.add(token)
        before = len(changed)
        changed.add(token)
        return len(changed) != before

    changed_any = True
    while changed_any:
        changed_any = False
        for issue in state["issues"]:
            token = f"issue:{issue['issue_ref']}"
            if issue["status"] == "stale" or not changed.intersection(issue.get("depends_on", [])):
                continue
            issue["status"] = "stale"
            stale_reason = "dependency_changed_" + hashlib.sha256(changed_ref.encode()).hexdigest()[:12]
            for check in issue["checks"]:
                check.update(assessment="stale", reason_ref=stale_reason)
                obligation = _find_obligation(state, f"c27:{issue['issue_ref']}:{check['check_id']}")
                obligation.update(status="stale", reason_ref=stale_reason)
            _find_obligation(state, f"c27:{issue['issue_ref']}").update(status="stale", reason_ref=stale_reason)
            _find_obligation(state, f"assessment:{issue['issue_ref']}").update(status="stale", reason_ref=stale_reason)
            _find_obligation(state, f"strategy:{issue['issue_ref']}").update(status="stale", reason_ref=stale_reason)
            changed_any = mark(token) or changed_any
        for task in state["research_tasks"]:
            token = f"research:{task['task_ref']}"
            if task["status"] == "stale" or not changed.intersection(task.get("depends_on", [])):
                continue
            task["status"] = "stale"
            _find_obligation(state, token).update(status="stale", reason_ref="dependency_changed")
            changed_any = mark(token) or changed_any
        for finding in state["research_findings"]:
            token = f"research-finding:{finding['finding_ref']}"
            if finding["status"] == "stale" or not changed.intersection(finding.get("depends_on", [])):
                continue
            finding["status"] = "stale"
            changed_any = mark(token) or changed_any
        for finding in state["findings"]:
            token = f"finding:{finding['finding_ref']}"
            if finding["status"] == "stale" or not changed.intersection(finding.get("depends_on", [])):
                continue
            finding["status"] = "stale"
            for issue_ref in finding["issue_refs"]:
                _refresh_assessment_obligation(state, issue_ref)
            changed_any = mark(token) or changed_any
        for disposition in state["strategy_dispositions"]:
            token = f"strategy:{disposition['issue_ref']}"
            if disposition["validity"] == "stale" or not changed.intersection(disposition.get("depends_on", [])):
                continue
            disposition.update(status="stale", validity="stale")
            _find_obligation(state, token).update(status="stale", reason_ref="dependency_changed")
            changed_any = mark(token) or changed_any
        for claim in state["claims"]:
            token = f"claim:{claim['claim_ref']}"
            if claim["validity"] == "stale" or not changed.intersection(claim.get("depends_on", [])):
                continue
            claim["validity"] = "stale"
            _find_obligation(state, f"final_review:{claim['claim_ref']}").update(
                status="stale", reason_ref="dependency_changed",
            )
            changed_any = mark(token) or changed_any
        for obligation in state["obligations"]:
            token = f"obligation:{obligation['obligation_ref']}"
            if obligation["status"] == "stale" or not any(
                ref in changed or f"obligation:{ref}" in changed for ref in obligation.get("depends_on", [])
            ):
                continue
            obligation.update(status="stale", reason_ref="dependency_changed")
            changed_any = mark(token) or changed_any

    if not invalidated:
        _advance_revision(state, "dependency_changed", [changed_ref])
        validate_state(state)
        return []
    impacted_gates: list[str] = []
    for token in invalidated:
        prefix, _, ref = token.partition(":")
        if prefix == "issue":
            impacted_gates.append("discovery")
        elif prefix in {"research", "research-finding"}:
            impacted_gates.append("research")
        elif prefix == "finding":
            impacted_gates.append("assessment")
        elif prefix == "strategy":
            impacted_gates.append("strategy")
        elif prefix == "claim":
            impacted_gates.append("final_review")
        elif prefix == "obligation":
            item = next((row for row in state["obligations"] if row["obligation_ref"] == ref), None)
            if item:
                impacted_gates.append(item["gate_id"])
    if not impacted_gates:
        impacted_gates.append("discovery")
    gate = min(impacted_gates, key=GATE_INDEX.get)
    _reopen_from(state, gate)
    _advance_revision(state, "dependency_changed", [changed_ref, *sorted(invalidated)])
    validate_state(state)
    return sorted(invalidated)


@transactional
def evaluate_release(state: dict[str, Any]) -> dict[str, Any]:
    validate_state(state)
    _validate_final_review_coverage(state)
    _validate_strategy_coverage(state)
    open_items: set[str] = set()
    for obligation in state["obligations"]:
        if obligation["required"] and obligation["status"] not in TERMINAL_OBLIGATIONS:
            open_items.add(obligation["obligation_ref"])
    for task in state["research_tasks"]:
        if task["required"] and task["status"] not in {"complete", "not_applicable"}:
            open_items.add("research:" + task["task_ref"])
    for issue in state["issues"]:
        if issue["materiality"] == "material" and issue["status"] not in {"assessed", "closed"}:
            open_items.add("issue:" + issue["issue_ref"])
    findings = {item["finding_ref"]: item for item in state["findings"]}
    for claim in state["claims"]:
        if claim["validity"] != "current":
            open_items.add("claim:" + claim["claim_ref"])
            continue
        if claim["treatment"] == "established" and any(findings[ref]["status"] != "supported" for ref in claim["finding_refs"]):
            raise ControllerError("unsupported_material_claim_cannot_be_established")
    prior_gates = [state["gates"][gate]["status"] for gate in GATES]
    if "blocked" in prior_gates or "pending" in prior_gates or "stale" in prior_gates:
        open_items.update(f"gate:{gate}" for gate in GATES[:-1] if state["gates"][gate]["status"] in {"blocked", "pending", "stale"})
    if state["release"]["mode"] == "full":
        if open_items or any(status != "satisfied" for status in prior_gates):
            status = "not_eligible"
        else:
            status = "eligible_full"
    else:
        # Established claims are eligible when their work is complete. Any material
        # issue with open required work needs an explicit qualified/withheld claim.
        open_issue_refs = {
            issue["issue_ref"] for issue in state["issues"]
            if issue["materiality"] != "nonmaterial" and issue["status"] not in {"assessed", "closed"}
        }
        for task in state["research_tasks"]:
            if task["required"] and task["status"] not in {"complete", "not_applicable"}:
                open_issue_refs.update(
                    issue_ref for issue_ref in task["issue_refs"]
                    if next(row for row in state["issues"] if row["issue_ref"] == issue_ref)["materiality"] != "nonmaterial"
                )
        qualified_covered = {
            ref for claim in state["claims"]
            if claim["validity"] == "current" and claim["treatment"] in {"qualified", "withheld"}
            for ref in claim["issue_refs"]
        }
        uncovered = open_issue_refs - qualified_covered
        open_items.update("issue:" + ref for ref in uncovered)
        if any(state["gates"][gate]["status"] == "blocked" for gate in GATES[:-1]) or uncovered:
            status = "not_eligible"
        elif any(value in {"pending", "stale"} for value in prior_gates):
            status = "not_eligible"
        else:
            status = "eligible_limited"
    state["release"].update(status=status, open_item_refs=sorted(open_items))
    _advance_revision(state, "release_evaluated", sorted(open_items))
    validate_state(state)
    return copy.deepcopy(state["release"])


def validate_state(state: dict[str, Any]) -> None:
    try:
        validate_obj("consultation-controller-state", state)
    except ContractError as error:
        raise ControllerError(str(error)) from error
    if state["fixture_kind"] != "synthetic_abstract":
        raise ControllerError("controller_accepts_synthetic_abstract_inputs_only")
    issue_refs = [item["issue_ref"] for item in state["issues"]]
    task_refs = [item["task_ref"] for item in state["research_tasks"]]
    finding_refs = [item["finding_ref"] for item in state["findings"]]
    research_finding_refs = [item["finding_ref"] for item in state["research_findings"]]
    claim_refs = [item["claim_ref"] for item in state["claims"]]
    obligation_refs = [item["obligation_ref"] for item in state["obligations"]]
    strategy_disposition_refs = [item["disposition_ref"] for item in state["strategy_dispositions"]]
    for label, values in (("issue", issue_refs), ("task", task_refs), ("finding", finding_refs),
                          ("research_finding", research_finding_refs), ("claim", claim_refs),
                          ("obligation", obligation_refs), ("strategy_disposition", strategy_disposition_refs)):
        if len(values) != len(set(values)):
            raise ControllerError(f"duplicate_{label}_reference")
    if set(finding_refs) & set(research_finding_refs):
        raise ControllerError("duplicate_cross_layer_finding_reference")
    evidence_refs = set(_evidence_map(state))
    intake = state["intake"]
    if intake["status"] == "pending":
        if state["proceedings"] or state["issues"]:
            raise ControllerError("case_records_require_classified_intake")
    else:
        if (not set(intake["evidence_refs"]) <= evidence_refs
                or any(_evidence_map(state)[ref]["kind"] != "conversation_record" for ref in intake["evidence_refs"])):
            raise ControllerError("intake_evidence_reference_invalid")
        if intake["urgency"] in {"urgent", "unknown"} and not intake["urgency_reason_ref"]:
            raise ControllerError("intake_urgency_reason_missing")
        try:
            valid_signals = set(issue_selection.signal_catalog(issue_selection.load_json(issue_selection.MATRIX_PATH)))
        except issue_selection.SelectionError as error:
            raise ControllerError("consultation_signal_catalog_unavailable") from error
        if not set(intake["legal_question_signal_ids"]) <= valid_signals:
            raise ControllerError("intake_signal_catalog_mismatch")
        if not state["proceedings"]:
            raise ControllerError("classified_intake_requires_proceeding")
    proceedings = {item["proceeding_ref"]: item for item in state["proceedings"]}
    if len(proceedings) != len(state["proceedings"]):
        raise ControllerError("duplicate_proceeding_reference")
    known_findings = {item["finding_ref"]: item for item in state["research_findings"] + state["findings"]}
    dependency_targets = {
        "issue": set(issue_refs),
        "proceeding": set(proceedings),
        "research": set(task_refs),
        "task": set(task_refs),
        "research-finding": set(research_finding_refs),
        "finding": set(finding_refs),
        "claim": set(claim_refs),
        "obligation": set(obligation_refs),
        "evidence": evidence_refs,
    }
    dependency_graph: dict[str, list[str]] = {}
    for collection, prefix, key in (
        (state["issues"], "issue", "issue_ref"),
        (state["research_tasks"], "research", "task_ref"),
        (state["research_findings"], "research-finding", "finding_ref"),
        (state["findings"], "finding", "finding_ref"),
        (state["strategy_dispositions"], "strategy", "issue_ref"),
        (state["claims"], "claim", "claim_ref"),
    ):
        for item in collection:
            dependency_graph[f"{prefix}:{item[key]}"] = item["depends_on"]

    def validate_dependencies(owner: str, refs: list[str]) -> None:
        for dependency in refs:
            prefix, separator, target = dependency.partition(":")
            if not separator:
                raise ControllerError("dependency_reference_must_be_typed:" + owner)
            if prefix in {"source", "fact", "authority", "external"}:
                continue
            if prefix not in dependency_targets or target not in dependency_targets[prefix]:
                raise ControllerError("dependency_reference_unknown:" + owner + ":" + dependency)

    for node, refs in dependency_graph.items():
        validate_dependencies(node, refs)
    dependency_visiting: set[str] = set()
    dependency_visited: set[str] = set()

    def visit_dependency(node: str) -> None:
        if node in dependency_visiting:
            raise ControllerError("consultation_dependency_cycle")
        if node in dependency_visited:
            return
        dependency_visiting.add(node)
        for ref in dependency_graph.get(node, []):
            if ref in dependency_graph:
                visit_dependency(ref)
        dependency_visiting.remove(node)
        dependency_visited.add(node)

    for node in dependency_graph:
        visit_dependency(node)
    for proceeding in state["proceedings"]:
        if proceeding["procedure_type"] not in route_validator.PROCEDURE_TYPES:
            raise ControllerError("proceeding_procedure_type_invalid")
        if (proceeding.get("administrative_outcome_classification") is not None
                and proceeding["administrative_outcome_classification"] not in issue_selection.ADMINISTRATIVE_OUTCOMES):
            raise ControllerError("proceeding_administrative_outcome_classification_invalid")
        if (proceeding.get("post_issuance_event_type") is not None
                and proceeding["post_issuance_event_type"] not in issue_selection.POST_ISSUANCE_EVENTS):
            raise ControllerError("proceeding_post_issuance_event_type_invalid")
        if not set(proceeding["evidence_refs"]) <= evidence_refs:
            raise ControllerError("proceeding_evidence_reference_invalid")
        if not set(proceeding["signal_ids"]) <= set(intake["legal_question_signal_ids"]):
            if proceeding["discovered_from_finding_ref"] is None:
                raise ControllerError("proceeding_signal_missing_from_intake")
        if proceeding["discovered_from_finding_ref"] is None:
            if intake["status"] != "classified" or not set(proceeding["evidence_refs"]) <= set(intake["evidence_refs"]):
                raise ControllerError("initial_proceeding_not_bound_to_intake")
        else:
            finding = known_findings.get(proceeding["discovered_from_finding_ref"])
            if finding is None or finding["status"] in {"stale", "unsupported"}:
                raise ControllerError("proceeding_discovery_finding_invalid")
    for item in state["evidence"]:
        if set(item["check_ids"]) != {binding["check_id"] for binding in item["check_bindings"]}:
            raise ControllerError("validator_check_binding_inventory_mismatch")
        if item["kind"] in EXECUTED_VALIDATOR_KINDS:
            if (item.get("status") not in {"passed", "failed", "unavailable"}
                    or not item.get("validator_id") or not item.get("subject_ref")
                    or not item.get("outcome") or not item.get("digest")
                    or (not item.get("artifact_digests") and item.get("status") != "unavailable")):
                raise ControllerError("validator_evidence_provenance_incomplete")
        elif item.get("validator_id") is not None or item.get("artifact_digests"):
            raise ControllerError("unexecuted_evidence_claims_validator_provenance")
    obligations = {item["obligation_ref"]: item for item in state["obligations"]}
    for gate_id, gate in state["gates"].items():
        if any(ref not in obligations for ref in gate["obligation_refs"]):
            raise ControllerError("gate_obligation_reference_invalid")
        if any(obligations[ref]["gate_id"] != gate_id for ref in gate["obligation_refs"]):
            raise ControllerError("gate_obligation_owner_mismatch")
        if not set(gate["evidence_refs"]) <= evidence_refs:
            raise ControllerError("gate_evidence_reference_invalid")
        if gate["status"] in TERMINAL_OBLIGATIONS:
            required_rows = [obligations[ref] for ref in gate["obligation_refs"] if obligations[ref]["required"]]
            carried_blocks = {
                item["obligation_ref"] for item in required_rows
                if gate_id == "research" and gate["status"] == "conditional"
                and item["obligation_ref"].startswith("research:")
                and item["status"] == "blocked" and item["reason_ref"] and item["evidence_refs"]
            }
            if any(item["status"] not in TERMINAL_OBLIGATIONS and item["obligation_ref"] not in carried_blocks
                   for item in required_rows):
                raise ControllerError("terminal_gate_has_open_required_obligation:" + gate_id)
            if gate["status"] in {"conditional", "not_applicable"} and (not gate["reason_ref"] or not gate["evidence_refs"]):
                raise ControllerError("conditional_gate_summary_incomplete:" + gate_id)
    for item in state["obligations"]:
        if not set(item["evidence_refs"]) <= evidence_refs:
            raise ControllerError("obligation_evidence_reference_invalid")
        if any(ref not in obligations for ref in item["depends_on"]):
            raise ControllerError("obligation_dependency_unknown")
    # Reject dependency cycles so no gate can be made to appear closed through a loop.
    graph = {item["obligation_ref"]: item["depends_on"] for item in state["obligations"]}
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(ref: str) -> None:
        if ref in visiting:
            raise ControllerError("obligation_dependency_cycle")
        if ref in visited:
            return
        visiting.add(ref)
        for dependency in graph[ref]:
            visit(dependency)
        visiting.remove(ref)
        visited.add(ref)
    for ref in graph:
        visit(ref)
    active_index = GATE_INDEX.get(state["active_gate"])
    if active_index is not None:
        for earlier in GATES[:active_index]:
            if state["gates"][earlier]["status"] not in TERMINAL_OBLIGATIONS:
                raise ControllerError("active_gate_skips_unresolved_predecessor:" + earlier)
    for issue in state["issues"]:
        proceeding = proceedings.get(issue["scope_ref"])
        if proceeding is None or proceeding["procedure_type"] != issue["procedure_type"]:
            raise ControllerError("issue_proceeding_classification_mismatch")
        if (not set(issue["signal_ids"]) <= set(proceeding["signal_ids"])
                and issue["discovered_from_finding_ref"] is None):
            raise ControllerError("issue_signal_missing_from_intake_or_discovery_link")
        if not set(issue["applicability_evidence_refs"]) <= evidence_refs:
            raise ControllerError("issue_applicability_evidence_reference_invalid")
        if issue["applicability"] == "not_applicable" and (
            not issue.get("applicability_reason_ref") or not issue["applicability_evidence_refs"]
        ):
            raise ControllerError("issue_not_applicable_missing_reason_or_evidence")
        if issue.get("discovered_from_finding_ref"):
            all_finding_refs = {item["finding_ref"] for item in state["research_findings"] + state["findings"]}
            if issue["discovered_from_finding_ref"] not in all_finding_refs:
                raise ControllerError("issue_discovery_finding_reference_invalid")
        proceeding = proceedings[issue["scope_ref"]]
        derived = _selector_requirement(
            proceeding["procedure_type"], issue["signal_ids"],
            administrative_outcome_classification=proceeding.get("administrative_outcome_classification"),
            post_issuance_event_type=proceeding.get("post_issuance_event_type"),
        )
        if issue["route_id"] not in derived["route_ids"]:
            raise ControllerError("issue_route_not_selected_by_signals")
        expected_checks = set(derived["check_ids"])
        recorded_checks = {item["check_id"] for item in issue["checks"]}
        if expected_checks != set(issue["c27_check_ids"]) or expected_checks != recorded_checks:
            raise ControllerError("c27_required_check_inventory_mismatch")
        check_obligations = []
        for check in issue["checks"]:
            if not set(check["evidence_refs"]) <= evidence_refs:
                raise ControllerError("check_evidence_reference_invalid")
            if check["assessment"] == "not_applicable" and (not check.get("reason_ref") or not check["evidence_refs"]):
                raise ControllerError("unselected_check_cannot_imply_not_applicable")
            obligation = obligations.get(f"c27:{issue['issue_ref']}:{check['check_id']}")
            if obligation is None:
                raise ControllerError("c27_check_obligation_missing")
            expected_status = {
                "not_checked": "pending", "assessed": "satisfied", "source_verified": "satisfied",
                "unavailable": "blocked", "not_applicable": "not_applicable", "stale": "stale",
            }[check["assessment"]]
            if (obligation["status"] != expected_status or obligation["reason_ref"] != check["reason_ref"]
                    or obligation["evidence_refs"] != check["evidence_refs"]):
                raise ControllerError("c27_check_obligation_state_mismatch")
            check_obligations.append(obligation)
        derived_issue, derived_c27_status, _, _ = _derive_issue_state(issue, check_obligations)
        if issue["status"] != derived_issue:
            raise ControllerError("c27_issue_status_not_derived_from_check_state")
        c27_obligation = obligations.get(f"c27:{issue['issue_ref']}")
        if c27_obligation is None or c27_obligation["status"] != derived_c27_status:
            raise ControllerError("c27_parent_obligation_state_mismatch")
        assessment_obligation = obligations.get(f"assessment:{issue['issue_ref']}")
        if assessment_obligation is None:
            raise ControllerError("assessment_issue_obligation_missing")
        all_issue_findings = [item for item in state["findings"] if issue["issue_ref"] in item["issue_refs"]]
        issue_findings = [item for item in all_issue_findings if item["status"] != "stale"]
        if issue["applicability"] == "not_applicable":
            expected_assessment = "not_applicable"
        elif issue["status"] == "stale" or (all_issue_findings and not issue_findings):
            expected_assessment = "stale"
        elif not issue_findings:
            expected_assessment = "pending"
        elif any(item["status"] in {"conditional", "unresolved"} for item in issue_findings):
            expected_assessment = "conditional"
        else:
            expected_assessment = "satisfied"
        if assessment_obligation["status"] != expected_assessment:
            raise ControllerError("assessment_issue_obligation_state_mismatch")
    task_ids = set(task_refs)
    validator_evidence = [item for item in state["evidence"] if item["kind"] == "research_gate"]
    observed_evidence = _evidence_map(state)
    attempt_refs: set[str] = set()
    for task in state["research_tasks"]:
        if not set(task["issue_refs"]) <= set(issue_refs):
            raise ControllerError("task_issue_reference_invalid")
        if task["max_attempts"] != RESEARCH_MODE_MAX_ATTEMPTS.get(task["mode"]):
            raise ControllerError("research_mode_retry_budget_mismatch")
        mode_evidence = observed_evidence.get(task["mode_reason_ref"])
        if (mode_evidence is None or mode_evidence["kind"] not in {"conversation_record", "other"}
                or mode_evidence["status"] != "observed" or task["mode_reason_ref"] not in task["evidence_refs"]):
            raise ControllerError("research_mode_reason_evidence_invalid")
        progress_hashes: set[str] = set()
        trailing_no_progress = 0
        for attempt in task["attempt_records"]:
            if attempt["attempt_ref"] in attempt_refs:
                raise ControllerError("duplicate_research_attempt_ref")
            attempt_refs.add(attempt["attempt_ref"])
            attempt_evidence = observed_evidence.get(attempt["evidence_ref"])
            if (attempt_evidence is None or attempt_evidence["kind"] not in {"source_review", "other"}
                    or attempt_evidence["status"] != "observed"
                    or attempt["evidence_ref"] not in task["evidence_refs"]):
                raise ControllerError("research_attempt_evidence_invalid")
            if attempt["result"] == "progress":
                if attempt["progress_sha256"] in progress_hashes:
                    raise ControllerError("research_attempt_repeats_prior_progress")
                progress_hashes.add(attempt["progress_sha256"])
                trailing_no_progress = 0
            elif attempt["result"] == "no_progress":
                if not attempt["reason_ref"]:
                    raise ControllerError("research_attempt_reason_missing")
                trailing_no_progress += 1
            else:
                if not attempt["reason_ref"]:
                    raise ControllerError("research_attempt_reason_missing")
                trailing_no_progress = 0
        if len(task["attempt_records"]) > task["max_attempts"]:
            raise ControllerError("research_attempt_budget_exceeded")
        if task["no_progress_streak"] != trailing_no_progress:
            raise ControllerError("research_no_progress_streak_mismatch")
        if (task["status"] == "complete"
                and (not task["attempt_records"] or task["attempt_records"][-1]["result"] != "progress")):
            raise ControllerError("complete_research_requires_recorded_progress")
        _validate_research_owner_role(task["owner_id"], task["role"])
        _validate_parent_source_pack_digest(task["owner_id"], task.get("source_pack_sha256"))
        owner_resolved = _validate_research_owner_assignment(
            state, task["issue_refs"], task["owner_id"], task["jurisdiction_ref"],
        )
        if task["status"] == "complete" and not owner_resolved:
            raise ControllerError("complete_research_owner_jurisdiction_unresolved")
        if not set(task["evidence_refs"] + task["counterevidence_refs"]) <= evidence_refs:
            raise ControllerError("task_evidence_reference_invalid")
        research_finding_map = {item["finding_ref"]: item for item in state["research_findings"]}
        if any(ref not in research_finding_map or research_finding_map[ref]["task_ref"] != task["task_ref"] for ref in task["finding_refs"]):
            raise ControllerError("task_research_finding_reference_invalid")
        expected_obligation_status = {
            "pending": "pending", "in_progress": "pending", "complete": "satisfied", "open": "conditional",
            "no_source_found": "conditional", "conflict_unresolved": "conditional",
            "blocked": "blocked", "not_applicable": "not_applicable", "stale": "stale",
        }[task["status"]]
        task_obligation = obligations.get(f"research:{task['task_ref']}")
        if task_obligation is None or task_obligation["status"] != expected_obligation_status:
            raise ControllerError("research_task_obligation_state_mismatch")
        if task["status"] == "complete" and not any(
            item["subject_ref"] == task["task_ref"] and item["status"] == "passed"
            and item["outcome"] == "research_complete" for item in validator_evidence
        ):
            raise ControllerError("complete_research_missing_validator_provenance")
    for item in state["research_findings"]:
        if item["task_ref"] not in task_ids or not set(item["issue_refs"]) <= set(issue_refs):
            raise ControllerError("research_finding_reference_invalid")
        if not set(item["evidence_refs"] + item["counterevidence_refs"]) <= evidence_refs:
            raise ControllerError("research_finding_evidence_reference_invalid")
        evidence = _evidence_map(state)
        if any(evidence[ref]["kind"] != "source_review" for ref in item["evidence_refs"]):
            raise ControllerError("research_finding_source_evidence_invalid")
        if any(evidence[ref]["kind"] not in {"source_review", "conversation_record"}
               for ref in item["counterevidence_refs"]):
            raise ControllerError("research_finding_counterevidence_invalid")
        task_validator = [entry for entry in validator_evidence if entry["subject_ref"] == item["task_ref"]]
        if not task_validator:
            raise ControllerError("research_finding_missing_executed_research_validator")
        if item["status"] == "supported" and not any(
            entry["status"] == "passed" and entry["outcome"] == "research_complete" for entry in task_validator
        ):
            raise ControllerError("supported_research_finding_missing_complete_validator")
        if item["status"] == "stale" and not any(entry["status"] == "passed" for entry in task_validator):
            raise ControllerError("stale_research_finding_missing_prior_validator")
        if item["status"] != "stale" and not any(entry["status"] in {"passed", "unavailable"} for entry in task_validator):
            raise ControllerError("research_finding_validator_not_acceptable")
    research_finding_map = {item["finding_ref"]: item for item in state["research_findings"]}
    task_map = {item["task_ref"]: item for item in state["research_tasks"]}
    for finding in state["findings"]:
        if not set(finding["issue_refs"]) <= set(issue_refs) or not set(finding["task_refs"]) <= task_ids:
            raise ControllerError("finding_reference_invalid")
        linked_research = [research_finding_map.get(ref) for ref in finding["research_finding_refs"]]
        if any(item is None for item in linked_research):
            raise ControllerError("finding_research_finding_reference_invalid")
        linked_tasks = {item["task_ref"] for item in linked_research}
        if linked_tasks != set(finding["task_refs"]):
            raise ControllerError("finding_task_research_finding_binding_invalid")
        if any(not set(item["issue_refs"]) <= set(finding["issue_refs"]) for item in linked_research):
            raise ControllerError("finding_research_finding_issue_mismatch")
        _check_synthetic_text({"statement": finding["statement"]})
        evidence = _evidence_map(state)
        for refs, kinds, code in (
            (finding["fact_refs"], {"conversation_record"}, "finding_fact_evidence_invalid"),
            (finding["source_refs"], {"source_review"}, "finding_source_evidence_invalid"),
            (finding["exception_refs"], {"source_review"}, "finding_exception_evidence_invalid"),
            (finding["condition_refs"], {"source_review", "conversation_record"}, "finding_condition_evidence_invalid"),
            (finding["counterevidence_refs"], {"source_review", "conversation_record"}, "finding_counterevidence_invalid"),
            (finding["uncertainty_refs"], {"source_review", "conversation_record", "other"}, "finding_uncertainty_evidence_invalid"),
        ):
            if any(ref not in evidence or evidence[ref]["kind"] not in kinds for ref in refs):
                raise ControllerError(code)
        if finding["status"] in {"supported", "conditional"} and (
            not finding["fact_refs"] or not finding["source_refs"] or not finding["counterevidence_refs"]
        ):
            raise ControllerError("reviewable_finding_missing_fact_source_or_counterevidence")
        if finding["status"] == "unsupported" and not (
            finding["fact_refs"] or finding["source_refs"] or finding["counterevidence_refs"]
        ):
            raise ControllerError("unsupported_finding_requires_review_evidence")
        if finding["status"] == "supported":
            if not linked_research or any(item["status"] != "supported" for item in linked_research):
                raise ControllerError("supported_finding_requires_supported_research")
            if any(task_map[ref]["status"] != "complete" for ref in finding["task_refs"]):
                raise ControllerError("supported_finding_requires_complete_research")
            source_evidence = {ref for item in linked_research for ref in item["evidence_refs"]}
            if not set(finding["source_refs"]) <= source_evidence:
                raise ControllerError("finding_source_not_bound_to_research_finding")
        elif finding["status"] == "conditional":
            if not linked_research or any(item["status"] not in {"supported", "conditional"} for item in linked_research):
                raise ControllerError("conditional_finding_requires_reviewable_research")
            if not finding["uncertainty_refs"] or not finding["assessment_reason_ref"]:
                raise ControllerError("conditional_finding_requires_uncertainty_and_reason")
        elif finding["status"] == "unresolved":
            if not finding["uncertainty_refs"] or not finding["assessment_reason_ref"]:
                raise ControllerError("unresolved_finding_requires_uncertainty_and_reason")
        elif finding["status"] == "unsupported" and not finding["assessment_reason_ref"]:
            raise ControllerError("unsupported_finding_requires_assessment_reason")
    finding_map = {item["finding_ref"]: item for item in state["findings"]}
    for disposition in state["strategy_dispositions"]:
        if disposition["issue_ref"] not in set(issue_refs):
            raise ControllerError("strategy_issue_reference_invalid")
        if not set(disposition["evidence_refs"]) <= evidence_refs:
            raise ControllerError("strategy_evidence_reference_invalid")
        if any(ref not in finding_map or disposition["issue_ref"] not in finding_map[ref]["issue_refs"]
               for ref in disposition["finding_refs"]):
            raise ControllerError("strategy_finding_reference_invalid")
        obligation = obligations.get(f"strategy:{disposition['issue_ref']}")
        if obligation is None:
            raise ControllerError("strategy_issue_obligation_missing")
        if disposition["validity"] == "stale":
            if disposition["status"] != "stale":
                raise ControllerError("stale_strategy_disposition_state_mismatch")
            continue
        status = disposition["status"]
        if status == "recommended":
            if (disposition["action_code"] == "none" or disposition["urgency"] == "none"
                    or not disposition["rationale_ref"] or not disposition["finding_refs"]
                    or any(finding_map[ref]["status"] != "supported" for ref in disposition["finding_refs"])):
                raise ControllerError("strategy_recommendation_state_invalid")
            valid_evidence = {
                ref for finding_ref in disposition["finding_refs"]
                for ref in (
                    finding_map[finding_ref]["fact_refs"] + finding_map[finding_ref]["source_refs"]
                    + finding_map[finding_ref]["exception_refs"] + finding_map[finding_ref]["condition_refs"]
                    + finding_map[finding_ref]["counterevidence_refs"] + finding_map[finding_ref]["uncertainty_refs"]
                )
            }
            if not set(disposition["evidence_refs"]) <= valid_evidence:
                raise ControllerError("strategy_evidence_not_linked_to_findings")
            expected_status = "satisfied"
        elif status == "conditional":
            if (disposition["action_code"] == "none" or disposition["urgency"] == "none"
                    or not disposition["rationale_ref"] or not disposition["qualification_ref"]
                    or not disposition["finding_refs"]
                    or any(finding_map[ref]["status"] not in {"supported", "conditional"}
                           for ref in disposition["finding_refs"])):
                raise ControllerError("conditional_strategy_state_invalid")
            expected_status = "conditional"
        elif status in {"no_action", "deferred"}:
            if (disposition["action_code"] != "none" or disposition["urgency"] != "none"
                    or not disposition["rationale_ref"] or not disposition["evidence_refs"]
                    or (status == "deferred" and not disposition["qualification_ref"])
                    or (status == "no_action" and disposition["qualification_ref"] is not None)):
                raise ControllerError("nonrecommendation_strategy_state_invalid")
            expected_status = "conditional" if status == "deferred" else "satisfied"
        else:
            raise ControllerError("strategy_disposition_status_invalid")
        if obligation["status"] != expected_status:
            raise ControllerError("strategy_issue_obligation_state_mismatch")
    for claim in state["claims"]:
        if not set(claim["issue_refs"]) <= set(issue_refs) or not set(claim["finding_refs"]) <= set(finding_refs):
            raise ControllerError("claim_reference_invalid")
        if not set(claim["evidence_refs"]) <= evidence_refs:
            raise ControllerError("claim_evidence_reference_invalid")
        _check_synthetic_text({"statement": claim["statement"]})
        if claim["treatment"] in {"qualified", "withheld"}:
            if not claim["qualification_ref"] or not claim["qualification_text"]:
                raise ControllerError("qualified_or_withheld_claim_requires_qualification")
            _check_synthetic_text({"statement": claim["qualification_text"]})
        elif claim["qualification_text"] is not None:
            raise ControllerError("established_claim_must_not_hide_qualification_text")
        if claim["validity"] == "current" and any(finding_map[ref]["status"] == "stale" for ref in claim["finding_refs"]):
            raise ControllerError("current_claim_links_stale_finding")
        if claim["validity"] == "current" and claim["treatment"] == "established" and (
            not claim["finding_refs"] or any(finding_map[ref]["status"] != "supported" for ref in claim["finding_refs"])
        ):
            raise ControllerError("established_claim_requires_supported_findings")
        if claim["treatment"] == "qualified":
            if not claim["finding_refs"] or not claim["qualification_ref"]:
                raise ControllerError("qualified_claim_requires_finding_and_qualification")
            if any(finding_map[ref]["status"] in {"unsupported", "stale"} for ref in claim["finding_refs"]):
                raise ControllerError("qualified_claim_requires_reviewable_findings")
        if claim["treatment"] == "withheld":
            if not claim["qualification_ref"] or not claim["evidence_refs"]:
                raise ControllerError("withheld_claim_requires_reason_and_evidence")
        if claim["treatment"] in {"established", "qualified"} and not claim["evidence_refs"]:
            raise ControllerError("released_claim_requires_evidence")
        if claim["validity"] == "current" and claim["treatment"] in {"established", "qualified"}:
            bound_evidence = {
                ref for finding_ref in claim["finding_refs"]
                for ref in (
                    finding_map[finding_ref]["fact_refs"] + finding_map[finding_ref]["source_refs"]
                    + finding_map[finding_ref]["exception_refs"] + finding_map[finding_ref]["condition_refs"]
                    + finding_map[finding_ref]["counterevidence_refs"] + finding_map[finding_ref]["uncertainty_refs"]
                )
            }
            if not set(claim["evidence_refs"]) <= bound_evidence:
                raise ControllerError("claim_evidence_not_bound_to_linked_findings")
        if claim["validity"] == "current" and claim["treatment"] == "established":
            required_tasks = {task_ref for ref in claim["finding_refs"] for task_ref in finding_map[ref]["task_refs"]}
            if any(task_map[ref]["status"] != "complete" for ref in required_tasks):
                raise ControllerError("established_claim_requires_complete_research_tasks")
        final_obligation = obligations.get(f"final_review:{claim['claim_ref']}")
        expected_claim_obligation = (
            "stale" if claim["validity"] == "stale"
            else "satisfied" if claim["treatment"] == "established"
            else "conditional"
        )
        if final_obligation is None or final_obligation["status"] != expected_claim_obligation:
            raise ControllerError("claim_final_review_obligation_state_mismatch")
    if state["gates"]["discovery"]["status"] in TERMINAL_OBLIGATIONS:
        _validate_discovery_route_coverage(state)
    if state["gates"]["strategy"]["status"] in TERMINAL_OBLIGATIONS:
        _validate_strategy_coverage(state)
    if state["gates"]["final_review"]["status"] in TERMINAL_OBLIGATIONS:
        _validate_final_review_coverage(state)


def atomic_write(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def render_controller_board(state: dict[str, Any]) -> str:
    """Render a diagnostic board from recorded controller state, never from intent."""
    validate_state(state)
    lines = [
        "# Consultation workflow status",
        "",
        f"**Mode:** {state['release']['mode'].title()}  ",
        f"**Release eligibility:** {state['release']['status'].replace('_', ' ')}  ",
        f"**Current step:** {state['active_gate'].replace('_', ' ').title()}",
        "",
        "| Review stage | Status | Open required items |",
        "| --- | --- | --- |",
    ]
    obligations = {item["obligation_ref"]: item for item in state["obligations"]}
    for gate_id in GATES:
        gate = state["gates"][gate_id]
        open_items = [obligations[ref]["obligation_ref"] for ref in gate["obligation_refs"]
                      if obligations[ref]["required"] and obligations[ref]["status"] not in TERMINAL_OBLIGATIONS]
        missing = ", ".join(f"`{ref}`" for ref in open_items) if open_items else "None recorded"
        status = gate["status"].replace("_", " ")
        lines.append(f"| {gate_id.replace('_', ' ').title()} | {status} | {missing} |")

    selected_checks = [check for issue in state["issues"] for check in issue["checks"]
                       if check["selection"] == "selected"]
    counts = {status: sum(check["assessment"] == status for check in selected_checks)
              for status in ("not_checked", "assessed", "source_verified", "unavailable", "not_applicable")}
    lines.extend([
        "",
        "## Issue and C27 review",
        "",
        f"Issues: {len(state['issues'])} total; "
        f"{sum(issue['materiality'] == 'material' for issue in state['issues'])} material; "
        f"{sum(issue['status'] == 'assessed' for issue in state['issues'])} assessed.",
        "",
        "| Selected checks | Count |",
        "| --- | ---: |",
        f"| Not assessed | {counts['not_checked']} |",
        f"| Model assessed | {counts['assessed']} |",
        f"| Source reviewed | {counts['source_verified']} |",
        f"| Unavailable | {counts['unavailable']} |",
        f"| Not applicable, with reason and evidence | {counts['not_applicable']} |",
        "",
        "## Research tasks",
        "",
    ])
    if state["research_tasks"]:
        lines.extend(["| Task | Source owner | Jurisdiction and role | Required? | Status | Validation run | Missing / limitation |",
                      "| --- | --- | --- | --- | --- | --- | --- |"])
        for task in state["research_tasks"]:
            obligation = obligations[f"research:{task['task_ref']}"]
            missing = obligation.get("reason_ref") or ("Research evidence not recorded" if task["status"] != "complete" else "None recorded")
            validation_runs = [item for item in state["evidence"]
                               if item["kind"] == "research_gate" and item["subject_ref"] == task["task_ref"]]
            validation = "; ".join(f"{item['status']} · {item['outcome']}" for item in validation_runs) or "Not executed"
            lines.append(
                f"| `{task['task_ref']}` | `{task['owner_id']}` | `{task['jurisdiction_ref']}` · {task['role'].replace('_', ' ')} | "
                f"{'Yes' if task['required'] else 'No'} | {task['status'].replace('_', ' ')} | {validation} | `{missing}` |"
            )
    else:
        lines.append("No research tasks recorded.")

    lines.extend(["", "## Findings and response dispositions", ""])
    if state["findings"]:
        lines.extend(["| Finding | Assessment | Statement |", "| --- | --- | --- |"])
        for finding in state["findings"]:
            lines.append(f"| `{finding['finding_ref']}` | {finding['status']} | {finding['statement']} |")
    else:
        lines.append("No legal findings recorded.")
    if state["claims"]:
        lines.extend(["", "| Claim | Treatment | Response statement / qualification |", "| --- | --- | --- |"])
        for claim in state["claims"]:
            detail = claim["statement"]
            if claim["qualification_text"]:
                detail += " — " + claim["qualification_text"]
            lines.append(f"| `{claim['claim_ref']}` | {claim['treatment']} | {detail} |")
    else:
        lines.append("No response claims recorded.")

    lines.extend(["", "## Recorded validator execution", "", "| Validator | Subject | Result | Evidence |", "| --- | --- | --- | --- |"])
    validator_labels = {
        "c27_receipt": "C27 receipt / route validation",
        "module_conformance": "C3 module conformance",
        "research_gate": "Research evidence validation",
        "source_preflight": "Issue source preflight",
    }
    recorded = [item for item in state["evidence"] if item["kind"] in EXECUTED_VALIDATOR_KINDS]
    if recorded:
        for item in recorded:
            lines.append(
                f"| {validator_labels[item['kind']]} | `{item['subject_ref']}` | "
                f"{item['status']} · {item['outcome']} | `{item['evidence_ref']}` |"
            )
    else:
        lines.append("| Any validator | — | Not executed; no result recorded | — |")

    open_items = state["release"].get("open_item_refs", [])
    lines.extend(["", "## Outstanding items", ""])
    if open_items:
        lines.extend(f"- `{item}`" for item in open_items)
    else:
        required_open = [item["obligation_ref"] for item in state["obligations"]
                         if item["required"] and item["status"] not in TERMINAL_OBLIGATIONS]
        if required_open:
            lines.extend(f"- `{item}`" for item in required_open)
        else:
            lines.append("No required open items are currently recorded.")
    lines.extend(["", "This synthetic controller report records workflow state; it does not establish legal correctness or enforce release in ChatGPT."])
    return "\n".join(lines)


def _event_artifact(base: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ControllerError("event_artifact_path_required")
    candidate = Path(value)
    if candidate.is_absolute() or any(part in {"..", ""} for part in candidate.parts):
        raise ControllerError("event_artifact_path_must_be_relative_and_contained")
    cursor = base
    for part in candidate.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ControllerError("event_artifact_symlink_not_allowed")
    resolved = (base / candidate).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ControllerError("event_artifact_path_escapes_event_directory")
    return resolved


def apply_event(state: dict[str, Any], event: dict[str, Any], event_dir: Path) -> Any:
    """Apply one allowlisted JSON state transition; no arbitrary code is executed."""
    validate_state(state)
    if event.get("fixture_kind") != "synthetic_abstract":
        raise ControllerError("event_must_declare_synthetic_abstract_fixture")
    _check_synthetic_text(event)
    action = event.get("action")
    arguments = event.get("arguments", {})
    if not isinstance(arguments, dict):
        raise ControllerError("event_arguments_must_be_object")
    methods = {
        "add_evidence": add_evidence,
        "add_obligation": add_obligation,
        "record_intake_classification": record_intake_classification,
        "add_proceeding": add_proceeding,
        "resolve_obligation": resolve_obligation,
        "add_issue": add_issue,
        "record_check": record_check,
        "add_research_task": add_research_task,
        "record_research_attempt": record_research_attempt,
        "set_research_status": set_research_status,
        "add_research_finding": add_research_finding,
        "add_finding": add_finding,
        "add_strategy_disposition": add_strategy_disposition,
        "add_claim": add_claim,
        "complete_gate": complete_gate,
        "invalidate": invalidate,
        "evaluate_release": evaluate_release,
    }
    if action == "record_research_validation":
        args = dict(arguments)
        args["plan_path"] = _event_artifact(event_dir, args.get("plan_path"))
        args["bundle_path"] = _event_artifact(event_dir, args.get("bundle_path"))
        return record_research_validation(state, **args)
    if action == "record_c27_receipt_validation":
        args = dict(arguments)
        args["receipt_path"] = _event_artifact(event_dir, args.get("receipt_path"))
        return record_c27_receipt_validation(state, **args)
    if action == "record_module_conformance_validation":
        args = dict(arguments)
        args["manifest_path"] = _event_artifact(event_dir, args.get("manifest_path"))
        args["export_path"] = _event_artifact(event_dir, args.get("export_path"))
        return record_module_conformance_validation(state, **args)
    if action == "record_source_preflight_validation":
        args = dict(arguments)
        for key in ("preflight_path", "plan_path", "bundle_path"):
            args[key] = _event_artifact(event_dir, args.get(key))
        return record_source_preflight_validation(state, **args)
    method = methods.get(action)
    if method is None:
        raise ControllerError("event_action_not_allowlisted")
    return method(state, **arguments)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create an empty synthetic controller state")
    init.add_argument("--state", type=Path, required=True)
    init.add_argument("--consultation-id", required=True)
    init.add_argument("--mode", choices=["full", "limited"], default="limited")
    apply = sub.add_parser("apply", help="apply one allowlisted synthetic state transition")
    apply.add_argument("--state", type=Path, required=True)
    apply.add_argument("--event", type=Path, required=True)
    validate = sub.add_parser("validate", help="validate an existing controller state")
    validate.add_argument("--state", type=Path, required=True)
    summary = sub.add_parser("summary", help="render a diagnostic board from recorded controller state")
    summary.add_argument("--state", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            if args.state.exists() or args.state.is_symlink():
                raise ControllerError("state_exists")
            state = new_state(args.consultation_id, args.mode)
            atomic_write(args.state, state)
            result = {"status": "initialized", "revision": state["revision"], "active_gate": state["active_gate"]}
        elif args.command == "apply":
            for path, label in ((args.state, "state"), (args.event, "event")):
                if path.is_symlink() or not path.is_file():
                    raise ControllerError(label + "_not_a_regular_file")
            state = json.loads(args.state.read_text(encoding="utf-8"))
            event = json.loads(args.event.read_text(encoding="utf-8"))
            transition_result = apply_event(state, event, args.event.resolve().parent)
            validate_state(state)
            atomic_write(args.state, state)
            result = {
                "status": "applied", "action": event.get("action"),
                "revision": state["revision"], "active_gate": state["active_gate"],
                "transition_result": transition_result,
            }
        else:
            if args.state.is_symlink() or not args.state.is_file():
                raise ControllerError("state_not_a_regular_file")
            state = json.loads(args.state.read_text(encoding="utf-8"))
            validate_state(state)
            if args.command == "summary":
                print(render_controller_board(state))
                return 0
            result = {"status": "valid", "revision": state["revision"], "active_gate": state["active_gate"], "release": state["release"]}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, TypeError, KeyError, json.JSONDecodeError, ControllerError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
