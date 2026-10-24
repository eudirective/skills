#!/usr/bin/env python3
"""C27: deterministic, non-sending abstract multi-proceeding state and coverage ledger.

Accepts strictly enumerated, opaque case metadata, NOT personal dossiers, raw
correspondence, names, passport numbers, addresses, or free-text narratives.
A caller's declaration that input is abstract does not certify anonymity.
This tool cannot extract facts from a story, authenticate records, establish
legal rules, track host conversations automatically, or execute legal engines.
Its model/source review entries are self-reported; no script-execution claim
is accepted. The CLI writes JSON to stdout only and never makes network calls.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "references/state-engine/check-registry.json"
SCHEMA = "c27-abstract-session/0.3.0"
LEGACY_SCHEMAS = frozenset(("c27-abstract-session/0.1.0",
                            "c27-abstract-session/0.2.0"))
OUTPUT_SCHEMA = "c27-case-state-report/0.4.0"
ID_PATTERN = re.compile(r"^[A-Z]{1,3}[1-9][0-9]{0,3}$")
REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:._/-]{0,100}$")

PROCEDURE_TYPES = frozenset((
    "eu_family_entry_visa", "ordinary_short_stay_visa", "national_long_stay_visa",
    "border_admission", "eu_family_residence_card", "national_residence_permit",
    "eu_citizen_registration", "permanent_residence", "family_status_recognition",
    "visa_appeal", "administrative_appeal", "judicial_review", "process_complaint",
    "conduct_complaint", "supervisory_complaint", "gdpr_access", "file_access",
    "evidence_preservation", "other_procedure"
))
REGIMES = frozenset((
    "directive_2004_38", "returnee_eu_rights", "visa_code", "national_family_law",
    "national_immigration_law", "schengen_borders", "gdpr", "national_procedure",
    "unknown", "disputed"
))
AUTHORITY_ROLES = frozenset((
    "consulate", "visa_application_centre", "border_authority", "migration_authority",
    "civil_registry", "ministry", "court", "data_controller", "supervisory_body",
    "eu_body", "other"
))
SOURCES = frozenset((
    "user_reported", "document_seen", "authority_record_seen",
    "reported_authority_oral", "model_inference"
))
STEPS = frozenset((
    "inquiry_sent", "appointment_requested", "appointment_confirmed",
    "form_prepared", "online_form_submitted", "appointment_attended",
    "lodgement_attempted", "lodgement_blocked", "lodgement_reported",
    "lodgement_disputed", "lodgement_confirmed", "receipt_issued",
    "examination_started", "supplement_requested", "interview_scheduled",
    "decision_taken", "decision_notified", "review_filed", "reopened",
    "closed", "withdrawn"
))
DOCUMENT_CATEGORIES = frozenset((
    "passport", "marriage_record", "birth_record", "divorce_record", "adoption_record",
    "residence_document", "travel_evidence", "employment_evidence",
    "means_evidence", "health_cover", "dependency_evidence", "translation",
    "application_form", "decision_notice", "visa_document", "appointment_record",
    "other_document"
))
DOC_ACTIONS = frozenset((
    "requested", "available", "shown", "submitted", "uploaded", "sent",
    "accepted", "rejected", "returned", "unavailable"
))
DISCLOSURE_TOPICS = frozenset((
    "eu_family_status", "relationship", "lawful_presence", "residence_status",
    "prior_mobility", "employment", "financial_means", "travel_plans",
    "previous_application", "legal_argument", "document_availability",
    "challenge_intent", "medical_context", "other_information"
))
CHANNELS = frozenset(("email", "post", "portal", "in_person", "oral", "provider", "other"))
DISC_ACTIONS = frozenset(("sent", "uploaded", "shown", "submitted", "communicated_orally"))
DISC_OBSERVATIONS = frozenset((
    "transport_delivered", "receipt_acknowledged", "content_acknowledged",
    "content_relied_on", "transmission_failed"
))
AUTHORITY_ISSUES = frozenset((
    "territorial_competence", "document_requirements", "lawful_presence",
    "family_status", "fraud_suspicion", "application_not_lodged",
    "procedure_timing", "refusal_reasons", "official_conduct",
    "other_authority_issue"
))
AUTHORITY_STANCES = frozenset((
    "expressly_invoked", "indicated_unconfirmed", "withdrawn",
    "clarified", "contested"
))
DEADLINE_TYPES = frozenset((
    "appointment_access", "visa_processing", "residence_card_processing",
    "appeal_filing", "administrative_response", "record_preservation",
    "data_access_response", "other_deadline"
))
CLOCK_STATUSES = frozenset((
    "candidate", "trigger_unconfirmed", "trigger_recorded",
    "reported_overdue", "fulfilled", "unknown"
))
RULE_STATUSES = frozenset(("not_checked", "publisher_checked", "contested"))
ISSUE_CATEGORIES = frozenset((
    "access", "lodgement", "document_demand", "delay", "staff_treatment",
    "physical_removal", "conduct", "records", "decision_reasons", "privacy",
    "representation", "other_issue"
))
RECEIPT_KINDS = frozenset(("application_lodgement", "appointment", "provider_check_in",
                           "payment", "document_return", "other", "unspecified"))
RECORD_KINDS = frozenset(("formal_lodgement", "inquiry", "file_opened",
                          "other", "unspecified"))
SCOPE_EXCLUSIONS = frozenset(("procedure_outside_scope", "actor_outside_scope",
                              "irrelevant_stage", "no_material_event",
                              "legally_excluded_with_basis",
                              "outcome_outside_scope"))
CORRECTION_REASONS = frozenset(("user_correction", "classification_revision",
                                 "later_document", "provenance_reassessment",
                                 "chronology_reassessment"))
EXCLUSION_REASONS = frozenset(("lawful_scope_exclusion", "wrong_procedure",
                                "disproved_report", "no_independent_grievance",
                                "duplicate_issue", "other_explained"))
ISSUE_DISPOSITIONS = frozenset((
    "unassessed", "complaint_candidate", "needs_fact",
    "preservation_only", "excluded_with_reason"
))
REVIEW_STATUSES = frozenset((
    "assessed", "partial", "not_checked", "not_applicable", "blocked", "unavailable"
))
REVIEW_METHODS = frozenset(("model_review", "source_review", "none"))
REVIEW_REASONS = frozenset((
    "scope_reviewed", "missing_fact", "missing_source", "missing_module",
    "not_attempted", "scope_excluded", "synthetic_only", "unsupported",
    "evidence_disputed", "pending_human_review", "other_unresolved"
))
VALID_TRIGGERS = frozenset((
    "always", "family", "appointment", "lodgement", "visa", "document", "interview",
    "decision", "review", "complaint", "disclosure", "authority", "strategy",
    "deadline", "issue", "residence", "border", "marriage", "country", "soft_law",
    "fraud", "stratagem", "legal_principle", "withdrawal",
    "outcome_article18", "outcome_article19", "outcome_article32",
    "post_issuance",
))
OUTCOME_TRIGGER_CLASSES = {
    "outcome_article18": "article18_not_competent",
    "outcome_article19": "article19_inadmissible",
    "outcome_article32": "article32_substantive_refusal",
}
ADMINISTRATIVE_OUTCOMES = frozenset((
    "article18_not_competent", "article19_inadmissible",
    "article32_substantive_refusal", "visa_issued",
    "withdrawn_or_not_pursued", "discontinued_or_transferred",
    "other", "undetermined"
))
POST_ISSUANCE_EVENTS = frozenset((
    "visa_cancelled", "visa_revoked", "visa_annulled", "visa_expired",
    "visa_extended", "visa_reissued", "other_post_issuance_event"
))
NEW_EVENT_KINDS = frozenset(("administrative_outcome", "post_issuance_event"))
ABSTRACT_EXPLANATION_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9 ,;:()'/_-]{1,199}$")
STEP_STAGE = {
    "inquiry_sent": "enquiry",
    "appointment_requested": "appointment_pending",
    "appointment_confirmed": "appointment_booked",
    "form_prepared": "preparation",
    "online_form_submitted": "online_submission_unverified",
    "appointment_attended": "appointment_attended",
    "lodgement_attempted": "lodgement_attempted",
    "lodgement_blocked": "lodgement_blocked",
    "lodgement_reported": "lodgement_reported",
    "lodgement_disputed": "lodgement_disputed",
    "lodgement_confirmed": "lodged",
    "receipt_issued": "lodged",
    "examination_started": "examination",
    "supplement_requested": "examination",
    "interview_scheduled": "interview_pending",
    "decision_taken": "decision_taken",
    "decision_notified": "notification_reported",
    "review_filed": "under_review",
    "reopened": "reopened",
    "closed": "closed",
    "withdrawn": "withdrawn"
}
STAGE_RANK = {
    "identified": 0, "enquiry": 1, "appointment_pending": 2,
    "appointment_booked": 3, "preparation": 3, "online_submission_unverified": 3,
    "appointment_attended": 4, "lodgement_attempted": 4,
    "lodgement_blocked": 4, "lodgement_reported": 4,
    "lodgement_disputed": 4, "lodged": 5, "examination": 6,
    "interview_pending": 6, "decision_taken": 7,
    "notification_reported": 8, "under_review": 9, "reopened": 6,
    "closed": 10, "withdrawn": 10
}
EVENT_FIELDS = {
    "proceeding_opened": (
        {"procedure_type", "claimed_regime", "authority_role"},
        {"parent_proceeding_id"}
    ),
    "procedural_step": (
        {"step"},
        {"receipt_kind", "issuer_role", "record_kind"}
    ),
    "document_event": (
        {"document_id", "document_category", "operation", "recipient_id"}, set()
    ),
    "disclosure": (
        {"disclosure_id", "topic", "operation", "channel", "recipient_id"},
        {"document_ids"}
    ),
    "disclosure_observation": ({"disclosure_id", "observation"}, set()),
    "authority_position": (
        {"issue", "stance"},
        {"related_disclosure_id", "related_event_id"}
    ),
    "authority_classification": ({"classified_as"}, set()),
    "administrative_outcome": (
        {"classification"},
        {"evidence_event_id", "explanation", "missing_evidence_explanation"}
    ),
    "post_issuance_event": (
        {"event_type", "evidence_event_id"}, {"explanation"}
    ),
    "deadline_event": (
        {"deadline_id", "deadline_type", "clock_status", "rule_status"},
        {"trigger_event_id"}
    ),
    "issue_event": (
        {"issue_id", "issue_category", "disposition"},
        {"from_event_id", "exclusion_reason"}
    )
}




class StateError(ValueError):
    pass


def require(test: bool, reason: str) -> None:
    if not test:
        raise StateError(reason)


def object_keys(obj, required, optional=(), label="object") -> None:
    require(isinstance(obj, dict), label + ":not_object")
    keys = set(obj)
    missing = set(required) - keys
    extra = keys - set(required) - set(optional)
    require(not missing, label + ":missing:" + ",".join(sorted(missing)))
    require(not extra, label + ":unexpected:" + ",".join(sorted(extra)))


def opaque_id(value, prefix: str, label: str) -> None:
    require(isinstance(value, str) and bool(ID_PATTERN.fullmatch(value))
            and value.startswith(prefix), label + ":invalid_opaque_id")


def value_in(value, allowed, label: str) -> None:
    require(isinstance(value, str) and value in allowed, label + ":unknown_value")


def validate_abstract_explanation(value, label: str) -> None:
    require(isinstance(value, str)
            and bool(ABSTRACT_EXPLANATION_PATTERN.fullmatch(value.strip())),
            label + ":invalid_abstract_explanation")
    require(not re.search(r"(?i)(https?://|www\.|[A-Z0-9._%+-]+@[A-Z0-9.-]+)", value)
            and not re.search(r"\d{7,}", value),
            label + ":identifier_or_contact_detail_not_allowed")


def validate_review_claim(status, method, reason, spec,
                          has_evidence, source_refs, scope_exclusion=None,
                          has_scope_exclusion=False):
    """Validate the shared C27 status/method/trace semantics.

    Case-state callers additionally validate event ownership and chronology;
    the consultation route receipt can validate only opaque references.
    """
    value_in(status, REVIEW_STATUSES, "review_status")
    value_in(method, REVIEW_METHODS, "review_method")
    value_in(reason, REVIEW_REASONS, "review_reason")
    if spec["capability"] != "model_guidance":
        require(status not in ("assessed", "partial"),
                "response:unavailable_capability_not_executed")
    if status in ("assessed", "partial"):
        require(method != "none", "response:assessed_without_method")
        require(reason != "not_attempted",
                "response:assessed_marked_unattempted")
        require(has_evidence or bool(source_refs),
                "response:assessed_without_trace")
    else:
        require(method == "none", "response:not_performed_has_method")
    if method == "source_review":
        require(bool(source_refs), "response:source_review_without_reference")
    if status == "not_applicable":
        require(has_evidence or bool(source_refs),
                "response:scope_exclusion_without_trace")
        require(reason == "scope_excluded",
                "response:not_applicable_without_scope_reason")
        require(has_scope_exclusion,
                "response:scope_exclusion")
        value_in(scope_exclusion, SCOPE_EXCLUSIONS,
                 "response:scope_exclusion")
        if scope_exclusion == "legally_excluded_with_basis":
            require(bool(source_refs),
                    "response:legal_exclusion_requires_source")
    else:
        require(not has_scope_exclusion,
                "response:scope_exclusion_for_other_status")


def validate_route_check_record(record, registry=None):
    """Check a privacy-minimised route check using C27's own rule vocabulary."""
    registry = registry or load_registry()
    object_keys(record, {"check_id", "status", "method", "reason",
                         "evidence_refs", "source_refs"},
                {"scope_exclusion"}, "route_check")
    specs = {item["check_id"]: item for item in registry["checks"]}
    check_id = record["check_id"]
    require(check_id in specs, "route_check:unknown_check:" + str(check_id))
    evidence_refs = record["evidence_refs"]
    source_refs = record["source_refs"]
    require(isinstance(evidence_refs, list) and len(evidence_refs) <= 30,
            "route_check:invalid_evidence_refs")
    require(isinstance(source_refs, list) and len(source_refs) <= 30,
            "route_check:invalid_source_refs")
    require(len(evidence_refs) == len(set(evidence_refs)),
            "route_check:duplicate_evidence_refs")
    require(len(source_refs) == len(set(source_refs)),
            "route_check:duplicate_source_refs")
    require(all(isinstance(ref, str) and bool(REF_PATTERN.fullmatch(ref))
                for ref in evidence_refs + source_refs),
            "route_check:unsafe_reference")
    validate_review_claim(
        record["status"], record["method"], record["reason"],
        specs[check_id], bool(evidence_refs), source_refs,
        record.get("scope_exclusion"), "scope_exclusion" in record)
    return True


def validate_event(e, nested=False) -> None:
    require(isinstance(e, dict), "event:not_object")
    kind = e.get("kind")
    is_correction = kind == "event_correction"
    require(is_correction or kind in EVENT_FIELDS, "event:invalid_kind")
    required, optional = (
        ({"target_event_id", "replacement"}, {"correction_reason"}) if is_correction
        else EVENT_FIELDS[kind]
    )
    object_keys(e, {"event_id", "proceeding_id", "kind", "source"} | required,
                optional | {"occurred_order"}, "event")
    opaque_id(e["event_id"], "E", "event_id")
    opaque_id(e["proceeding_id"], "P", "proceeding_id")
    value_in(e["source"], SOURCES, "event_source")
    if "occurred_order" in e:
        require(type(e["occurred_order"]) is int
                and 0 <= e["occurred_order"] <= 100000,
                "event:invalid_relative_occurrence_order")
    if is_correction:
        require(not nested, "correction:nested")
        opaque_id(e["target_event_id"], "E", "correction_target")
        if "correction_reason" in e:
            value_in(e["correction_reason"], CORRECTION_REASONS,
                     "correction:invalid_reason")
        require(e["source"] != "model_inference", "correction:inferred")
        validate_event(e["replacement"], nested=True)
        require(e["replacement"]["proceeding_id"] == e["proceeding_id"],
                "correction:proceeding_mismatch")
        return
    if kind == "proceeding_opened":
        value_in(e["procedure_type"], PROCEDURE_TYPES, "procedure_type")
        value_in(e["claimed_regime"], REGIMES, "claimed_regime")
        value_in(e["authority_role"], AUTHORITY_ROLES, "authority_role")
        if "parent_proceeding_id" in e:
            opaque_id(e["parent_proceeding_id"], "P", "parent_proceeding_id")
    elif kind == "procedural_step":
        value_in(e["step"], STEPS, "step")
        if "receipt_kind" in e:
            require(e["step"] == "receipt_issued", "receipt:wrong_step")
            value_in(e["receipt_kind"], RECEIPT_KINDS, "receipt_kind")
        if "issuer_role" in e:
            require(e["step"] == "receipt_issued", "receipt:issuer_wrong_step")
            value_in(e["issuer_role"], AUTHORITY_ROLES, "receipt_issuer")
        if "record_kind" in e:
            require(e["step"] == "lodgement_confirmed", "lodgement:record_wrong_step")
            value_in(e["record_kind"], RECORD_KINDS, "record_kind")
    elif kind == "document_event":
        opaque_id(e["document_id"], "D", "document_id")
        value_in(e["document_category"], DOCUMENT_CATEGORIES, "document_category")
        value_in(e["operation"], DOC_ACTIONS, "document_operation")
        opaque_id(e["recipient_id"], "A", "recipient_id")
    elif kind == "disclosure":
        opaque_id(e["disclosure_id"], "I", "disclosure_id")
        value_in(e["topic"], DISCLOSURE_TOPICS, "disclosure_topic")
        value_in(e["operation"], DISC_ACTIONS, "disclosure_operation")
        value_in(e["channel"], CHANNELS, "disclosure_channel")
        opaque_id(e["recipient_id"], "A", "recipient_id")
        if "document_ids" in e:
            require(isinstance(e["document_ids"], list)
                    and len(e["document_ids"]) <= 30
                    and len(set(map(str, e["document_ids"]))) == len(e["document_ids"]),
                    "disclosure:document_ids")
            for d in e["document_ids"]:
                opaque_id(d, "D", "document_id")
    elif kind == "disclosure_observation":
        opaque_id(e["disclosure_id"], "I", "disclosure_id")
        value_in(e["observation"], DISC_OBSERVATIONS, "disclosure_observation")
        require(e["source"] != "model_inference",
                "disclosure:observation_cannot_be_inferred")
        if e["observation"] in ("content_acknowledged", "content_relied_on"):
            require(e["source"] in ("document_seen", "authority_record_seen",
                                    "reported_authority_oral"),
                    "disclosure:acknowledgement_requires_authority_basis")
    elif kind == "authority_classification":
        value_in(e["classified_as"], PROCEDURE_TYPES | {"unknown", "disputed"},
                 "authority_classification")
        require(e["source"] != "model_inference",
                "authority:classification_requires_attribution")
    elif kind == "administrative_outcome":
        value_in(e["classification"], ADMINISTRATIVE_OUTCOMES,
                 "administrative_outcome")
        if "evidence_event_id" in e:
            opaque_id(e["evidence_event_id"], "E", "outcome_evidence_event")
        if "explanation" in e:
            validate_abstract_explanation(e["explanation"], "outcome_explanation")
        if "missing_evidence_explanation" in e:
            validate_abstract_explanation(
                e["missing_evidence_explanation"], "outcome_missing_evidence")
        classification = e["classification"]
        if classification in {
            "article18_not_competent", "article19_inadmissible",
            "article32_substantive_refusal", "visa_issued"
        }:
            require("evidence_event_id" in e,
                    "outcome:formal_result_requires_evidence_reference")
            require(e["source"] in ("document_seen", "authority_record_seen"),
                    "outcome:formal_result_requires_official_record_source")
        elif classification == "other":
            require("explanation" in e and "evidence_event_id" in e,
                    "outcome:other_requires_explanation_and_evidence")
            require(e["source"] in ("document_seen", "authority_record_seen"),
                    "outcome:other_requires_official_record_source")
        elif classification == "undetermined":
            require("missing_evidence_explanation" in e,
                    "outcome:undetermined_requires_missing_evidence_explanation")
        else:
            require(e["source"] != "model_inference",
                    "outcome:asserted_event_requires_attribution")
    elif kind == "post_issuance_event":
        value_in(e["event_type"], POST_ISSUANCE_EVENTS, "post_issuance_event")
        opaque_id(e["evidence_event_id"], "E", "post_issuance_evidence_event")
        require(e["source"] in ("document_seen", "authority_record_seen"),
                "post_issuance:requires_official_record_source")
        if e["event_type"] == "other_post_issuance_event":
            require("explanation" in e,
                    "post_issuance:other_requires_explanation")
        if "explanation" in e:
            validate_abstract_explanation(e["explanation"],
                                          "post_issuance_explanation")
    elif kind == "authority_position":
        value_in(e["issue"], AUTHORITY_ISSUES, "authority_issue")
        value_in(e["stance"], AUTHORITY_STANCES, "authority_stance")
        if e["stance"] == "expressly_invoked":
            require(e["source"] in ("document_seen", "authority_record_seen",
                                    "reported_authority_oral"),
                    "authority:express_position_requires_statement")
        if "related_disclosure_id" in e:
            opaque_id(e["related_disclosure_id"], "I", "related_disclosure_id")
        if "related_event_id" in e:
            opaque_id(e["related_event_id"], "E", "related_event_id")
    elif kind == "deadline_event":
        opaque_id(e["deadline_id"], "L", "deadline_id")
        value_in(e["deadline_type"], DEADLINE_TYPES, "deadline_type")
        value_in(e["clock_status"], CLOCK_STATUSES, "clock_status")
        value_in(e["rule_status"], RULE_STATUSES, "rule_status")
        if "trigger_event_id" in e:
            opaque_id(e["trigger_event_id"], "E", "trigger_event_id")
        if e["clock_status"] == "trigger_recorded":
            require("trigger_event_id" in e, "deadline:missing_trigger")
    elif kind == "issue_event":
        opaque_id(e["issue_id"], "G", "issue_id")
        value_in(e["issue_category"], ISSUE_CATEGORIES, "issue_category")
        value_in(e["disposition"], ISSUE_DISPOSITIONS, "issue_disposition")
        if "from_event_id" in e:
            opaque_id(e["from_event_id"], "E", "from_event_id")
        if "exclusion_reason" in e:
            value_in(e["exclusion_reason"], EXCLUSION_REASONS, "exclusion_reason")
            require(e["disposition"] == "excluded_with_reason",
                    "issue:exclusion_reason_for_nonexclusion")
        elif e["disposition"] == "excluded_with_reason":
            raise StateError("issue:missing_exclusion_reason")


def normalize_events(data):
    """Return active events in occurrence order; corrections supersede, never erase audit history."""
    raw = data["events"]
    require(isinstance(raw, list) and len(raw) <= 500, "events:invalid_count")
    if data.get("schema") != SCHEMA:
        for e in raw:
            has_new_event = isinstance(e, dict) and e.get("kind") in NEW_EVENT_KINDS
            if isinstance(e, dict) and e.get("kind") == "event_correction":
                replacement = e.get("replacement")
                has_new_event = (isinstance(replacement, dict)
                                 and replacement.get("kind") in NEW_EVENT_KINDS)
            require(not has_new_event,
                    "case:new_procedural_outcome_events_require_schema_0_3_0")
    active = []
    index = {}
    all_ids = {}
    superseded = set()
    opened = set()
    for pos, e in enumerate(raw):
        validate_event(e)
        eid = e["event_id"]
        require(eid not in all_ids, "events:duplicate_id:" + eid)
        all_ids[eid] = pos
        if e["kind"] == "event_correction":
            target = e["target_event_id"]
            require(target in index, "correction:missing_or_superseded_target")
            original = active[index[target]]
            replacement = e["replacement"]
            rid = replacement["event_id"]
            require(rid not in all_ids, "correction:replacement_id_not_fresh")
            require(original["proceeding_id"] == replacement["proceeding_id"]
                    and original["kind"] == replacement["kind"],
                    "correction:kind_or_proceeding_change_forbidden")
            if original["kind"] == "proceeding_opened" and (
                    replacement["procedure_type"] != original["procedure_type"]
                    or replacement["claimed_regime"] != original["claimed_regime"]):
                require(e.get("correction_reason") == "classification_revision",
                        "correction:classification_revision_required")
            all_ids[rid] = pos
            superseded.add(target)
            at = index.pop(target)
            active[at] = replacement
            index[rid] = at
            continue
        if e["kind"] == "proceeding_opened":
            require(e["proceeding_id"] not in opened,
                    "proceeding:duplicate_open:" + e["proceeding_id"])
            if "parent_proceeding_id" in e:
                require(e["parent_proceeding_id"] in opened,
                        "proceeding:parent_not_open")
            opened.add(e["proceeding_id"])
        else:
            require(e["proceeding_id"] in opened,
                    "proceeding:not_open:" + e["proceeding_id"])
        index[eid] = len(active)
        active.append(e)
    require(len(opened) <= 40, "proceeding:too_many")
    return active, all_ids, superseded


def load_registry(path=REGISTRY_PATH):
    reg = json.loads(Path(path).read_text(encoding="utf-8"))
    object_keys(reg, {"schema", "description", "families", "checks"},
                {"procedure_scopes"}, label="registry")
    require(reg["schema"] in ("freemovement-check-registry/0.1.0",
                               "freemovement-check-registry/0.2.0",
                               "freemovement-check-registry/0.3.0"),
            "registry:schema")
    procedure_scopes = {}
    for scope in reg.get("procedure_scopes", []):
        object_keys(scope, {"scope_id", "procedure_types"}, label="registry_procedure_scope")
        scope_id = scope["scope_id"]
        require(isinstance(scope_id, str) and bool(REF_PATTERN.fullmatch(scope_id)),
                "registry:invalid_procedure_scope_id")
        require(scope_id not in procedure_scopes,
                "registry:duplicate_procedure_scope")
        require(isinstance(scope["procedure_types"], list)
                and bool(scope["procedure_types"])
                and len(scope["procedure_types"]) == len(set(scope["procedure_types"]))
                and set(scope["procedure_types"]) <= PROCEDURE_TYPES,
                "registry:invalid_procedure_scope_types")
        procedure_scopes[scope_id] = set(scope["procedure_types"])
    if reg["schema"] == "freemovement-check-registry/0.3.0":
        require(bool(procedure_scopes), "registry:procedure_scopes_required")
    require(isinstance(reg["checks"], list) and len(reg["checks"]) >= 50,
            "registry:missing_checks")
    ids = set()
    families = {x["family_id"] for x in reg["families"]}
    for c in reg["checks"]:
        object_keys(c, {"check_id", "family", "label", "triggers_any",
                        "capability", "reference"},
                   {"priority", "catalog_entry_id", "procedure_scope_id"},
                        label="registry_check")
        require(c["family"] in families
                and c["check_id"].startswith(c["family"] + "."),
                "registry:unknown_family")
        require(c["check_id"] not in ids, "registry:duplicate_check")
        ids.add(c["check_id"])
        require(isinstance(c["triggers_any"], list) and c["triggers_any"]
                and set(c["triggers_any"]) <= VALID_TRIGGERS,
                "registry:invalid_triggers")
        require(c["capability"] in ("model_guidance", "synthetic_only",
                                    "not_implemented"), "registry:invalid_capability")
        if "priority" in c:
            value_in(c["priority"], {"urgent", "important", "normal", "low"},
                     "registry:invalid_priority")
        if "catalog_entry_id" in c:
            require(isinstance(c["catalog_entry_id"], str)
                    and bool(REF_PATTERN.fullmatch(c["catalog_entry_id"])),
                    "registry:invalid_catalog_entry")
        if "procedure_scope_id" in c:
            require(c["procedure_scope_id"] in procedure_scopes,
                    "registry:unknown_procedure_scope")
        require(isinstance(c["reference"], str)
                and c["reference"].startswith("references/"),
                "registry:invalid_reference")
    return reg


def summarize_administrative_outcome(records):
    """Summarize explicit outcome classifications without upgrading assertions.

    Generic decision/stage events never become a formal outcome here. Multiple
    incompatible source-attributed classifications remain unresolved.
    """
    evidence_ids = sorted({
        item["resolved_evidence_event_id"]
        for item in records if item.get("resolved_evidence_event_id")
    })
    event_ids = [item["event_id"] for item in records]
    if not records:
        return {
            "classification": "undetermined", "status": "undetermined",
            "source": "not_recorded", "event_ids": [],
            "evidence_event_ids": [], "explanation": None,
            "missing_evidence_explanation": (
                "No explicit administrative outcome is recorded; inspect decision, withdrawal, transfer, and lodging evidence."
            ),
            "assurance": "absence_of_record_is_not_proof_of_no_decision"
        }

    corrected_known = [
        item for item in records
        if item["classification"] != "undetermined"
        and item["evidence_reference_corrected"]
    ]
    known = [
        item for item in records
        if item["classification"] != "undetermined"
        and not item["evidence_reference_corrected"]
    ]
    if corrected_known:
        return {
            "classification": "undetermined", "status": "needs_reassessment",
            "source": "mixed_or_corrected", "event_ids": event_ids,
            "evidence_event_ids": evidence_ids, "explanation": None,
            "missing_evidence_explanation": (
                "The evidence linked to an outcome classification was corrected; reassess the classification against the replacement record."
            ),
            "assurance": "source_attributed_not_legal_validation"
        }
    if not known:
        last = records[-1]
        return {
            "classification": "undetermined", "status": "undetermined",
            "source": last["source"], "event_ids": event_ids,
            "evidence_event_ids": evidence_ids, "explanation": None,
            "missing_evidence_explanation": last.get(
                "missing_evidence_explanation") or (
                    "Only an undetermined classification is recorded; the missing evidence must be identified."
                ),
            "assurance": "source_attributed_not_legal_validation"
        }

    classes = {item["classification"] for item in known}
    other_explanations = {
        item.get("explanation") for item in known
        if item["classification"] == "other"
    }
    if len(classes) != 1 or len(other_explanations) > 1:
        return {
            "classification": "undetermined", "status": "conflicting",
            "source": "mixed", "event_ids": event_ids,
            "evidence_event_ids": evidence_ids, "explanation": None,
            "missing_evidence_explanation": (
                "Conflicting administrative outcome classifications are recorded; reconcile the proceeding and source documents."
            ),
            "assurance": "conflicting_source_attributed_classifications"
        }

    selected = known[-1]
    return {
        "classification": selected["classification"], "status": "classified",
        "source": selected["source"], "event_ids": event_ids,
        "evidence_event_ids": evidence_ids,
        "explanation": selected.get("explanation"),
        "missing_evidence_explanation": None,
        "assurance": "source_attributed_not_legal_validation"
    }


def build_proceedings(events, correction_aliases=None,
                      corrected_disclosures=None, corrected_documents=None):
    """Replay corrected effective records, retaining independent historical facts.

    Incoming order is when the model learned about an event, not proof of the
    date on which it occurred. Optional relative occurred_order is advisory;
    no calendar date, service, legal deadline, or factual authenticity is inferred.
    """
    ordered = {}
    global_documents = {}
    disclosures_seen = {}
    issue_owners = {}
    deadline_owners = {}
    event_lookup = {}
    event_objects = {}
    aliases = correction_aliases or {}
    unstable_disclosures = set(corrected_disclosures or ())
    unstable_documents = set(corrected_documents or ())

    def resolve_reference(ref, pid):
        """Resolve a corrected prior event, flagging that its legal effect needs review."""
        target = ref
        seen = set()
        corrected = False
        while target not in event_lookup and target in aliases:
            require(target not in seen, "dependency:correction_cycle")
            seen.add(target)
            target = aliases[target]
            corrected = True
        require(event_lookup.get(target) == pid,
                "dependency:event_missing_or_other_proceeding")
        return target, corrected

    def referenced_event(ref, pid):
        resolved, corrected = resolve_reference(ref, pid)
        return event_objects[resolved], resolved, corrected

    def official_notice(event, categories):
        return (
            event["kind"] == "document_event"
            and event["document_category"] in categories
            and event["operation"] in ("shown", "available")
            and event["source"] in ("document_seen", "authority_record_seen")
        )

    for position, e in enumerate(events):
        pid = e["proceeding_id"]
        kind = e["kind"]
        if kind == "proceeding_opened":
            require(pid not in ordered, "proceeding:replay_duplicate_open")
            if "parent_proceeding_id" in e:
                require(e["parent_proceeding_id"] in ordered,
                        "proceeding:parent_not_open")
            ordered[pid] = {
                "proceeding_id": pid, "type": e["procedure_type"],
                "claimed_regime": e["claimed_regime"],
                "authority_role": e["authority_role"],
                "parent_proceeding_id": e.get("parent_proceeding_id"),
                "authority_classifications": [],
                "stage": "identified", "stage_history": [], "steps": [],
                "lodgement": "not_established",
                "decision": "not_recorded", "notification": "not_recorded",
                "administrative_outcome_records": [],
                "post_issuance_events": [],
                "documents": {}, "disclosures": {}, "authority_positions": [],
                "deadlines": {}, "issues": {}, "event_ids": [], "timeline": [],
                "flags": [], "unresolved_dependencies": []
            }
        require(pid in ordered, "proceeding:active_order")
        p = ordered[pid]
        p["event_ids"].append(e["event_id"])
        p["timeline"].append({
            "event_id": e["event_id"],
            "kind": kind,
            "recorded_order": position,
            "occurred_order": e.get("occurred_order"),
            "source": e["source"]
        })
        if kind == "procedural_step":
            step = e["step"]
            p["steps"].append(step)
            next_stage = STEP_STAGE[step]
            event_status = "recorded"
            if e["source"] == "model_inference":
                p["flags"].append("inference_not_procedural_evidence")
                event_status = "unverified_inference"
            else:
                if step == "receipt_issued":
                    formal = (
                        e.get("receipt_kind") == "application_lodgement"
                        and e.get("issuer_role") in (
                            "consulate", "migration_authority", "border_authority")
                        and e["source"] in ("document_seen", "authority_record_seen")
                    )
                    if formal:
                        p["lodgement"] = "documented"
                    else:
                        p["flags"].append("receipt_does_not_establish_lodgement")
                        if p["lodgement"] == "not_established":
                            p["lodgement"] = (
                                "reported_not_documented"
                                if e.get("receipt_kind") == "application_lodgement"
                                and e.get("issuer_role") in (
                                    "consulate", "migration_authority",
                                    "border_authority")
                                else "receipt_purpose_unverified"
                            )
                        next_stage = "lodgement_reported"
                elif step == "lodgement_confirmed":
                    formal = (
                        e.get("record_kind") == "formal_lodgement"
                        and e["source"] in ("document_seen", "authority_record_seen")
                    )
                    if formal:
                        p["lodgement"] = "documented"
                    else:
                        if p["lodgement"] not in (
                            "documented", "documented_but_disputed"):
                            p["lodgement"] = "reported_not_documented"
                        next_stage = "lodgement_reported"
                        p["flags"].append("lodgement_confirmation_not_formally_documented")
                elif step == "lodgement_reported":
                    if p["lodgement"] not in ("documented", "documented_but_disputed"):
                        p["lodgement"] = "reported_not_documented"
                elif step in ("lodgement_attempted", "lodgement_blocked"):
                    if p["lodgement"] == "not_established":
                        p["lodgement"] = "attempted_unconfirmed"
                elif step == "lodgement_disputed":
                    p["lodgement"] = (
                        "documented_but_disputed"
                        if p["lodgement"] in ("documented", "documented_but_disputed")
                        else "disputed"
                    )
                    p["flags"].append("lodgement_requires_resolution")
                if step == "decision_taken":
                    p["decision"] = (
                        "document_seen" if e["source"] in (
                            "document_seen", "authority_record_seen")
                        else "reported"
                    )
                if step == "decision_notified":
                    p["notification"] = (
                        "record_seen_service_not_legally_verified"
                        if e["source"] in ("document_seen", "authority_record_seen")
                        else "reported_notification"
                    )
                    p["flags"].append("service_date_not_automatically_verified")
                if step == "online_form_submitted":
                    p["flags"].append("online_form_does_not_prove_lodgement")
                if step == "review_filed" and p["type"] not in (
                    "visa_appeal", "administrative_appeal", "judicial_review",
                    "process_complaint", "conduct_complaint", "supervisory_complaint"):
                    p["flags"].append("review_should_be_separate_proceeding")
                if (STAGE_RANK[next_stage] >= STAGE_RANK[p["stage"]]
                        or step == "reopened"):
                    p["stage"] = next_stage
            p["stage_history"].append({
                "event_id": e["event_id"], "step": step,
                "mapped_stage": next_stage, "source": e["source"],
                "record_status": event_status
            })
        elif kind == "authority_classification":
            p["authority_classifications"].append({
                "classified_as": e["classified_as"],
                "source": e["source"], "event_id": e["event_id"]
            })
        elif kind == "administrative_outcome":
            classification = e["classification"]
            evidence_id = e.get("evidence_event_id")
            evidence = None
            resolved_evidence_id = None
            evidence_corrected = False
            if evidence_id is not None:
                evidence, resolved_evidence_id, evidence_corrected = referenced_event(
                    evidence_id, pid)
            if classification in {
                "article18_not_competent", "article19_inadmissible",
                "article32_substantive_refusal"
            }:
                require(p["type"] == "ordinary_short_stay_visa",
                        "outcome:visa_code_article_requires_short_stay_visa_proceeding")
                if classification == "article18_not_competent":
                    require(p["authority_role"] == "consulate",
                            "outcome:article18_requires_consular_proceeding")
                if not evidence_corrected:
                    require(official_notice(evidence, {"decision_notice"}),
                            "outcome:visa_code_article_requires_decision_notice_evidence")
            elif classification == "visa_issued":
                require(p["type"] in (
                    "eu_family_entry_visa", "ordinary_short_stay_visa",
                    "national_long_stay_visa", "visa_appeal"),
                    "outcome:visa_issued_requires_visa_proceeding")
                if not evidence_corrected:
                    require(official_notice(evidence, {"decision_notice", "visa_document"}),
                            "outcome:visa_issued_requires_visa_or_decision_document")
            elif classification == "other":
                if not evidence_corrected:
                    require(official_notice(evidence, {"decision_notice"}),
                            "outcome:other_requires_decision_notice_evidence")
            if evidence_corrected:
                p["flags"].append("administrative_outcome_evidence_corrected_reassess")
                p["unresolved_dependencies"].append({
                    "event_id": e["event_id"], "reference": evidence_id,
                    "corrected_to": resolved_evidence_id,
                    "reason": "administrative_outcome_requires_reassessment"
                })
            p["administrative_outcome_records"].append({
                "event_id": e["event_id"], "classification": classification,
                "source": e["source"], "evidence_event_id": evidence_id,
                "resolved_evidence_event_id": resolved_evidence_id,
                "evidence_reference_corrected": evidence_corrected,
                "explanation": e.get("explanation"),
                "missing_evidence_explanation": e.get("missing_evidence_explanation"),
                "assurance": "source_attributed_not_legal_validation"
            })
        elif kind == "post_issuance_event":
            require(p["type"] in (
                "eu_family_entry_visa", "ordinary_short_stay_visa",
                "national_long_stay_visa", "visa_appeal"),
                "post_issuance:requires_visa_proceeding")
            evidence, resolved_evidence_id, evidence_corrected = referenced_event(
                e["evidence_event_id"], pid)
            if not evidence_corrected:
                require(official_notice(evidence, {"decision_notice", "visa_document"}),
                        "post_issuance:requires_visa_or_decision_document")
            if evidence_corrected:
                p["flags"].append("post_issuance_evidence_corrected_reassess")
            p["post_issuance_events"].append({
                "event_id": e["event_id"], "event_type": e["event_type"],
                "source": e["source"], "evidence_event_id": e["evidence_event_id"],
                "resolved_evidence_event_id": resolved_evidence_id,
                "evidence_reference_corrected": evidence_corrected,
                "explanation": e.get("explanation"),
                "assurance": "source_attributed_not_legal_validation"
            })
        elif kind == "document_event":
            did = e["document_id"]
            prior_category = global_documents.get(did)
            require(prior_category is None or prior_category == e["document_category"],
                    "document:category_changed_across_proceedings")
            global_documents[did] = e["document_category"]
            doc = p["documents"].setdefault(
                did, {"document_id": did, "category": e["document_category"],
                      "operations": []})
            doc["operations"].append({
                "action": e["operation"], "recipient_id": e["recipient_id"],
                "source": e["source"], "event_id": e["event_id"],
                "occurred_order": e.get("occurred_order")
            })
        elif kind == "disclosure":
            did = e["disclosure_id"]
            require(did not in disclosures_seen, "disclosure:duplicate_id")
            unresolved_docs = []
            for ref in e.get("document_ids", []):
                if ref in unstable_documents:
                    unresolved_docs.append(ref)
                elif ref not in p["documents"]:
                    raise StateError(
                        "disclosure:document_requires_proceeding_specific_operation")
            if unresolved_docs:
                p["flags"].append("document_disclosure_link_corrected")
                p["unresolved_dependencies"].append({
                    "event_id": e["event_id"],
                    "reason": "document_disclosure_link_requires_reassessment",
                    "document_ids": unresolved_docs
                })
            disclosures_seen[did] = pid
            p["disclosures"][did] = {
                "disclosure_id": did, "topic": e["topic"],
                "recipient_id": e["recipient_id"], "channel": e["channel"],
                "operation": e["operation"], "source": e["source"],
                "delivery_state": "sent_or_presented_unconfirmed",
                "transmission_delivered": False, "receipt_acknowledged": False,
                "content_acknowledged": False, "content_relied_on": False,
                "transmission_failed": False,
                "observations": [], "document_ids": e.get("document_ids", []),
                "unresolved_document_ids": unresolved_docs,
                "event_id": e["event_id"],
                "occurred_order": e.get("occurred_order")
            }
        elif kind == "disclosure_observation":
            did = e["disclosure_id"]
            if did in unstable_disclosures:
                p["flags"].append("disclosure_observation_refers_to_corrected_content")
                p["unresolved_dependencies"].append({
                    "event_id": e["event_id"], "disclosure_id": did,
                    "reason": "delivery_or_reliance_requires_content_reassessment"
                })
                event_lookup[e["event_id"]] = pid
                event_objects[e["event_id"]] = e
                continue
            require(disclosures_seen.get(did) == pid,
                    "disclosure:observation_wrong_ref")
            d = p["disclosures"][did]
            observation = e["observation"]
            field = {
                "transport_delivered": "transmission_delivered",
                "receipt_acknowledged": "receipt_acknowledged",
                "content_acknowledged": "content_acknowledged",
                "content_relied_on": "content_relied_on",
                "transmission_failed": "transmission_failed"
            }[observation]
            d[field] = True
            d["observations"].append({
                "observation": observation, "source": e["source"],
                "event_id": e["event_id"],
                "occurred_order": e.get("occurred_order")
            })
        elif kind == "authority_position":
            related_disclosure = e.get("related_disclosure_id")
            if related_disclosure:
                if related_disclosure in unstable_disclosures:
                    p["flags"].append("authority_linked_disclosure_corrected")
                    p["unresolved_dependencies"].append({
                        "event_id": e["event_id"],
                        "disclosure_id": related_disclosure,
                        "reason": "authority_reference_requires_disclosure_reassessment"
                    })
                else:
                    require(disclosures_seen.get(related_disclosure) == pid,
                            "authority:related_disclosure_missing_in_proceeding")
            related_event = e.get("related_event_id")
            resolved_related = None
            related_corrected = False
            if related_event:
                resolved_related, related_corrected = resolve_reference(
                    related_event, pid)
                if related_corrected:
                    p["flags"].append("authority_position_source_corrected")
                    p["unresolved_dependencies"].append({
                        "event_id": e["event_id"], "reference": related_event,
                        "corrected_to": resolved_related,
                        "reason": "authority_position_requires_reassessment"})
            p["authority_positions"].append({
                "issue": e["issue"], "stance": e["stance"],
                "attribution": e["source"], "event_id": e["event_id"],
                "related_disclosure_id": related_disclosure,
                "related_event_id": related_event,
                "resolved_event_id": resolved_related,
                "source_reference_corrected": related_corrected
            })
        elif kind == "deadline_event":
            did = e["deadline_id"]
            require(did not in deadline_owners or deadline_owners[did] == pid,
                    "deadline:cross_proceeding_id_reuse")
            deadline_owners[did] = pid
            trigger_resolved = None
            trigger_corrected = False
            if "trigger_event_id" in e:
                trigger_resolved, trigger_corrected = resolve_reference(
                    e["trigger_event_id"], pid)
                if trigger_corrected:
                    p["flags"].append("deadline_trigger_corrected")
                    p["unresolved_dependencies"].append({
                        "event_id": e["event_id"],
                        "reference": e["trigger_event_id"],
                        "corrected_to": trigger_resolved,
                        "reason": "deadline_trigger_requires_reassessment"})
            p["deadlines"][did] = {
                "deadline_id": did, "kind": e["deadline_type"],
                "clock_status": ("trigger_unconfirmed" if trigger_corrected
                                 else e["clock_status"]),
                "recorded_clock_status": e["clock_status"],
                "rule_status": e["rule_status"],
                "trigger_event_id": e.get("trigger_event_id"),
                "resolved_trigger_event_id": trigger_resolved,
                "trigger_reference_corrected": trigger_corrected,
                "assurance": "self_reported_metadata_not_legal_calculation"
            }
        elif kind == "issue_event":
            iid = e["issue_id"]
            require(iid not in issue_owners or issue_owners[iid] == pid,
                    "issue:cross_proceeding_id_reuse")
            issue_owners[iid] = pid
            issue_resolved = None
            issue_corrected = False
            if "from_event_id" in e:
                issue_resolved, issue_corrected = resolve_reference(
                    e["from_event_id"], pid)
                if issue_corrected:
                    p["flags"].append("issue_source_corrected")
                    p["unresolved_dependencies"].append({
                        "event_id": e["event_id"],
                        "reference": e["from_event_id"],
                        "corrected_to": issue_resolved,
                        "reason": "grievance_disposition_requires_reassessment"})
            prev = p["issues"].get(iid)
            require(prev is None or prev["category"] == e["issue_category"],
                    "issue:category_changed")
            p["issues"][iid] = {
                "issue_id": iid, "category": e["issue_category"],
                "disposition": ("needs_fact" if issue_corrected
                                else e["disposition"]),
                "recorded_disposition": e["disposition"],
                "exclusion_reason": e.get("exclusion_reason"),
                "source_event_id": e.get("from_event_id"),
                "resolved_source_event_id": issue_resolved,
                "source_reference_corrected": issue_corrected,
                "last_event_id": e["event_id"]
            }
        event_lookup[e["event_id"]] = pid
        event_objects[e["event_id"]] = e
    out = []
    for p in ordered.values():
        p["administrative_outcome"] = summarize_administrative_outcome(
            p["administrative_outcome_records"])
        for d in p["disclosures"].values():
            if d["transmission_failed"] and (
                d["transmission_delivered"] or d["receipt_acknowledged"]
                or d["content_acknowledged"] or d["content_relied_on"]
            ):
                d["delivery_state"] = "conflicting_observations"
                p["flags"].append("disclosure_transport_conflict")
            elif d["content_relied_on"]:
                d["delivery_state"] = "content_relied_on"
            elif d["content_acknowledged"]:
                d["delivery_state"] = "content_acknowledged"
            elif d["receipt_acknowledged"]:
                d["delivery_state"] = "receipt_acknowledged_not_content"
            elif d["transmission_delivered"]:
                d["delivery_state"] = "delivered_not_content_acknowledged"
            elif d["transmission_failed"]:
                d["delivery_state"] = "transmission_failed"
        for d in p["disclosures"].values():
            state_sources = {
                "conflicting_observations": {
                    "transport_delivered", "transmission_failed",
                    "receipt_acknowledged", "content_acknowledged",
                    "content_relied_on"},
                "content_relied_on": {"content_relied_on"},
                "content_acknowledged": {"content_acknowledged"},
                "receipt_acknowledged_not_content": {"receipt_acknowledged"},
                "delivered_not_content_acknowledged": {"transport_delivered"},
                "transmission_failed": {"transmission_failed"}
            }.get(d["delivery_state"], set())
            d["current_state_evidence_classes"] = sorted({
                obs["source"] for obs in d["observations"]
                if obs["observation"] in state_sources
            })
            d["authority_identity_authenticated"] = False
        if p["decision"] != "not_recorded" and p["notification"] == "not_recorded":
            p["flags"].append("decision_not_notification")
        if p["lodgement"] != "documented":
            p["flags"].append("formal_lodgement_not_unambiguously_documented")
        if any(x["delivery_state"] == "sent_or_presented_unconfirmed"
               for x in p["disclosures"].values()):
            p["flags"].append("disclosures_sent_no_receipt_evidence")
        # Relative chronology is separate from the order evidence was supplied.
        timeline = p["timeline"]
        order_values = [x["occurred_order"] for x in timeline
                        if x["occurred_order"] is not None]
        p["chronology_assurance"] = (
            "relative_order_partial" if len(order_values) < len(timeline)
            else "relative_order_supplied_unverified"
        )
        if any(x["occurred_order"] is not None and
               any(y["occurred_order"] is not None
                   and y["occurred_order"] > x["occurred_order"]
                   for y in timeline[:i])
               for i, x in enumerate(timeline)):
            p["flags"].append("later_disclosed_earlier_event")
        p["timeline_by_relative_occurrence"] = sorted(
            [x for x in timeline if x["occurred_order"] is not None],
            key=lambda x: (x["occurred_order"], x["recorded_order"]))
        p["documents"] = list(p["documents"].values())
        p["disclosures"] = list(p["disclosures"].values())
        p["deadlines"] = list(p["deadlines"].values())
        p["issues"] = list(p["issues"].values())
        p["flags"] = sorted(set(p["flags"]))
        out.append(p)
    return out


def feature_tags(p, requested_focus=()):
    """Conservative triage from entire history, not merely the final stage.

    These tags are *hints*, not decisions that an unselected legal check is
    inapplicable. A model may add explicit topic focus after reading the matter.
    """
    t = {"always", "country"} | set(requested_focus)
    typ = p["type"]
    steps = set(p["steps"])
    if "visa" in typ:
        t.add("visa")
    if typ in ("eu_family_entry_visa", "eu_family_residence_card",
               "family_status_recognition", "permanent_residence"):
        t.add("family")
    if "residence" in typ or typ == "eu_citizen_registration":
        t.add("residence")
    if typ == "border_admission":
        t.add("border")
    if typ == "family_status_recognition":
        t.add("marriage")
    if "complaint" in typ or typ in ("judicial_review", "administrative_appeal",
                                     "visa_appeal"):
        t.update(("complaint", "review", "strategy"))
    if p["disclosures"]:
        t.update(("disclosure", "strategy"))
    if p["documents"] or "supplement_requested" in steps:
        t.add("document")
    if p["authority_positions"] or p["authority_classifications"]:
        t.update(("authority", "soft_law", "strategy", "legal_principle"))
    if p["deadlines"]:
        t.add("deadline")
    if p["issues"]:
        t.update(("issue", "strategy"))
    if any(x["issue"] == "fraud_suspicion"
           for x in p["authority_positions"]):
        t.add("fraud")
    if steps.intersection({"inquiry_sent", "appointment_requested",
                           "appointment_confirmed", "appointment_attended"}):
        t.add("appointment")
    if steps.intersection({
        "lodgement_attempted", "lodgement_blocked", "lodgement_reported",
        "lodgement_disputed", "lodgement_confirmed", "receipt_issued",
        "online_form_submitted", "appointment_attended"
    }):
        t.add("lodgement")
    if "interview_scheduled" in steps:
        t.add("interview")
    if steps.intersection({"decision_taken", "decision_notified"}):
        t.add("decision")
    if p.get("administrative_outcome_records"):
        t.add("decision")
        if any(item["classification"] in {
            "article18_not_competent", "article19_inadmissible",
            "article32_substantive_refusal", "visa_issued"
        } for item in p["administrative_outcome_records"]):
            t.add("visa")
        for trigger, classification in OUTCOME_TRIGGER_CLASSES.items():
            if any(item["classification"] == classification
                   for item in p["administrative_outcome_records"]):
                t.add(trigger)
        if any(item["classification"] in {
            "withdrawn_or_not_pursued", "discontinued_or_transferred",
        } for item in p["administrative_outcome_records"]):
            t.add("withdrawal")
    if p.get("post_issuance_events"):
        t.update(("visa", "decision", "post_issuance"))
    if steps.intersection({"review_filed", "reopened"}):
        t.add("review")
    return t

def validate_responses(data, all_ids, superseded, proceedings, registry):
    """Validate *reported* checks against history, capability, and provenance.

    Historical response references to subsequently corrected events remain
    valid as-of that response. Corrections make the conclusion stale; they must
    not erase an earlier turn or imply the earlier record never existed.
    """
    review_records = []
    specs = {c["check_id"]: c for c in registry["checks"]}
    known_proceedings = {p["proceeding_id"] for p in proceedings}
    procedure_by_id = {p["proceeding_id"]: p["type"] for p in proceedings}
    scope_types = {
        item["scope_id"]: set(item["procedure_types"])
        for item in registry.get("procedure_scopes", [])
    }
    events = data["events"]
    event_proceeding = {}
    opened_at = {}
    superseded_at = {}
    outcome_events = []
    post_issuance_events = []
    for pos, e in enumerate(events):
        event_proceeding[e["event_id"]] = e["proceeding_id"]
        if e["kind"] == "event_correction":
            superseded_at[e["target_event_id"]] = pos
            child = e["replacement"]
            event_proceeding[child["event_id"]] = child["proceeding_id"]
            if child["kind"] == "administrative_outcome":
                outcome_events.append((pos, child))
            elif child["kind"] == "post_issuance_event":
                post_issuance_events.append((pos, child))
        elif e["kind"] == "proceeding_opened":
            opened_at[e["proceeding_id"]] = pos
        elif e["kind"] == "administrative_outcome":
            outcome_events.append((pos, e))
        elif e["kind"] == "post_issuance_event":
            post_issuance_events.append((pos, e))
    responses = data.get("responses", [])
    require(isinstance(responses, list) and len(responses) <= 100,
            "responses:invalid_count")
    used = set()
    previous_index = -1
    for response in responses:
        object_keys(response, {"response_id", "through_event_id", "checks"},
                    label="response")
        opaque_id(response["response_id"], "R", "response_id")
        require(response["response_id"] not in used, "responses:duplicate_id")
        used.add(response["response_id"])
        through = response["through_event_id"]
        require(through in all_ids, "response:through_event_missing")
        cursor = all_ids[through]
        require(cursor >= previous_index, "responses:nonmonotonic")
        previous_index = cursor
        checks = response["checks"]
        require(isinstance(checks, list) and len(checks) <= 800,
                "response:invalid_check_count")
        seen = set()
        for c in checks:
            object_keys(c, {"check_id", "proceeding_id", "status",
                            "method", "reason"},
                        {"evidence_event_ids", "source_refs", "scope_exclusion"},
                        "response_check")
            check_id = c["check_id"]
            require(check_id in specs,
                    "response:unknown_check:" + str(check_id))
            spec = specs[check_id]
            pid = c["proceeding_id"]
            require(pid in known_proceedings, "response:unknown_proceeding")
            require(opened_at.get(pid, cursor + 1) <= cursor,
                    "response:future_proceeding")
            key = (pid, check_id)
            require(key not in seen, "response:duplicate_check")
            seen.add(key)
            scope_id = spec.get("procedure_scope_id")
            procedure_out_of_scope = bool(
                scope_id and procedure_by_id[pid] not in scope_types[scope_id]
            )
            outcome_triggers = set(spec["triggers_any"]) & set(OUTCOME_TRIGGER_CLASSES)
            if outcome_triggers:
                current_outcomes = [
                    event for position, event in outcome_events
                    if event["proceeding_id"] == pid and position <= cursor
                    and superseded_at.get(event["event_id"], cursor + 1) > cursor
                ]
                outcome_classes = {event["classification"] for event in current_outcomes}
                matching_triggers = {
                    trigger for trigger, classification in OUTCOME_TRIGGER_CLASSES.items()
                    if trigger in outcome_triggers and classification in outcome_classes
                }
                if c["status"] in ("assessed", "partial") and not procedure_out_of_scope:
                    require(bool(matching_triggers),
                            "response:outcome_specific_check_without_matching_outcome")
                elif (c["status"] == "not_applicable" and not matching_triggers
                      and not procedure_out_of_scope):
                    expected_exclusion = (
                        "outcome_outside_scope" if outcome_classes
                        else "no_material_event"
                    )
                    require(c.get("scope_exclusion") == expected_exclusion,
                            "response:outcome_scope_exclusion_not_recorded")
            if procedure_out_of_scope:
                require(c["status"] == "not_applicable",
                        "response:procedure_scoped_check_assessed_outside_scope")
                require(c.get("scope_exclusion") == "procedure_outside_scope",
                        "response:procedure_scope_exclusion_not_recorded")
            if "post_issuance" in spec["triggers_any"]:
                current_post_events = [
                    event for position, event in post_issuance_events
                    if event["proceeding_id"] == pid and position <= cursor
                    and superseded_at.get(event["event_id"], cursor + 1) > cursor
                ]
                if c["status"] in ("assessed", "partial") and not procedure_out_of_scope:
                    require(bool(current_post_events),
                            "response:post_issuance_check_without_event")
                elif (c["status"] == "not_applicable" and not current_post_events
                      and not procedure_out_of_scope):
                    require(c.get("scope_exclusion") == "no_material_event",
                            "response:post_issuance_exclusion_not_recorded")
            refs = c.get("evidence_event_ids", [])
            require(isinstance(refs, list) and len(refs) <= 30,
                    "response:invalid_evidence_refs")
            for ref in refs:
                opaque_id(ref, "E", "response_evidence_event")
                require(ref in all_ids and all_ids[ref] <= cursor,
                        "response:future_or_missing_evidence")
                require(event_proceeding.get(ref) == pid,
                        "response:evidence_wrong_proceeding")
                require(superseded_at.get(ref, cursor + 1) > cursor,
                        "response:corrected_evidence_no_longer_current")
            sources = c.get("source_refs", [])
            require(isinstance(sources, list) and len(sources) <= 30,
                    "response:invalid_sources")
            for source in sources:
                require(isinstance(source, str)
                        and bool(REF_PATTERN.fullmatch(source)),
                        "response:unsafe_source_ref")
            validate_review_claim(
                c["status"], c["method"], c["reason"], spec,
                bool(refs), sources, c.get("scope_exclusion"),
                "scope_exclusion" in c)
            review_records.append({
                **c, "response_id": response["response_id"],
                "through_index": cursor,
                "method_assurance": "self_reported_not_proof_of_execution"
            })
    return review_records, responses

def make_coverage(proceedings, records, responses, registry, raw_events,
                  full, requested_focus=()):
    latest_response = responses[-1]["response_id"] if responses else None
    last_record = {(r["proceeding_id"], r["check_id"]): r for r in records}
    current_response = {
        (r["proceeding_id"], r["check_id"]): r for r in records
        if r["response_id"] == latest_response
    }
    scope_types = {
        item["scope_id"]: set(item["procedure_types"])
        for item in registry.get("procedure_scopes", [])
    }
    current = []
    for p in proceedings:
        pid = p["proceeding_id"]
        tags = feature_tags(p, requested_focus)
        for spec in registry["checks"]:
            cid = spec["check_id"]
            recorded = last_record.get((pid, cid))
            immediate = current_response.get((pid, cid))
            relevant = bool(tags.intersection(spec["triggers_any"]))
            scope_id = spec.get("procedure_scope_id")
            out_of_procedure_scope = bool(
                scope_id and p["type"] not in scope_types[scope_id]
            )
            if out_of_procedure_scope and recorded is None:
                if full or relevant:
                    current.append({
                        "proceeding_id": pid, "check_id": cid,
                        "family": spec["family"], "status": "not_applicable",
                        "capability": spec["capability"],
                        "priority": spec.get("priority", "normal"),
                        "method": "none", "from_response": None,
                        "method_assurance": "none",
                        "scope_exclusion": "procedure_outside_scope",
                        "procedure_scope_id": scope_id,
                        "procedure_type": p["type"],
                    })
                continue
            if not relevant and recorded is None:
                if full:
                    current.append({
                        "proceeding_id": pid, "check_id": cid,
                        "family": spec["family"],
                        "status": "not_indicated_not_excluded",
                        "capability": spec["capability"],
                        "priority": spec.get("priority", "normal")
                    })
                continue
            status = "not_checked"
            method = "none"
            from_response = None
            record = immediate or recorded
            if record:
                method = record["method"]
                from_response = record["response_id"]
                recorded_status = record["status"]
                newer_events = any(
                    i > record["through_index"] and
                    e["proceeding_id"] == pid
                    for i, e in enumerate(raw_events)
                )
                if recorded_status in ("assessed", "partial", "not_applicable"):
                    if newer_events:
                        status = "needs_recheck"
                    else:
                        status = (recorded_status if immediate
                                  else "previously_" + recorded_status)
                elif recorded_status == "unavailable":
                    status = "unavailable_for_live_advice"
                else:
                    status = recorded_status
            elif spec["capability"] in ("synthetic_only", "not_implemented"):
                status = "unavailable_for_live_advice"
            if not relevant and record is not None:
                status = "historical_" + status
            coverage_item = {
                "proceeding_id": pid, "check_id": cid,
                "family": spec["family"], "status": status,
                "capability": spec["capability"],
                "priority": spec.get("priority", "normal"),
                "method": method, "from_response": from_response,
                "method_assurance": (
                    "self_reported" if method != "none" else "none")
            }
            if record and record.get("scope_exclusion"):
                coverage_item["scope_exclusion"] = record["scope_exclusion"]
            if scope_id:
                coverage_item["procedure_scope_id"] = scope_id
            current.append(coverage_item)
    gap_statuses = {"not_checked", "needs_recheck",
                    "unavailable_for_live_advice", "blocked", "partial",
                    "previously_partial", "historical_needs_recheck"}
    material_gaps = [
        {k: c[k] for k in (
            "proceeding_id", "check_id", "status", "capability", "priority")}
        for c in current if c["status"] in gap_statuses
    ]
    priority_order = {"urgent": 0, "important": 1, "normal": 2, "low": 3}
    state_order = {"needs_recheck": 0, "blocked": 1,
                   "unavailable_for_live_advice": 2, "not_checked": 3,
                   "partial": 4}
    material_gaps.sort(
        key=lambda c: (
            priority_order.get(c["priority"], 3),
            state_order.get(c["status"], 9),
            c["proceeding_id"], c["check_id"]
        )
    )
    counts = dict(sorted(Counter(c["status"] for c in current).items()))
    response_counts = dict(sorted(Counter(
        r["status"] for r in records
        if r["response_id"] == latest_response
    ).items()))
    by_family = {}
    for c in current:
        family = c["family"]
        cell = by_family.setdefault(family, {
            "relevant": 0, "checked": 0, "outstanding": 0
        })
        if c["status"] != "not_indicated_not_excluded":
            cell["relevant"] += 1
        if c["status"] in (
            "assessed", "previously_assessed",
            "partial", "previously_partial"
        ):
            cell["checked"] += 1
        if c["status"] in gap_statuses:
            cell["outstanding"] += 1
    result = {
        "registry_checks": len(registry["checks"]),
        "latest_response_id": latest_response,
        "requested_focus": sorted(requested_focus),
        "this_response_recorded": response_counts,
        "session_coverage_states": counts,
        "by_family": by_family,
        "outstanding_total": len(material_gaps),
        "outstanding_sample": material_gaps[:30],
        "outstanding_sample_is_priority_sorted": True,
        "completeness_guaranteed": False,
        "assessment_record_assurance": "self_reported_and_schema_checked_only"
    }
    if full:
        result["checks"] = current
        result["outstanding_all"] = material_gaps
    return result

def evaluate(data, *, full=False, registry=None):
    object_keys(data, {"schema", "mode", "case_ref", "events"},
                {"responses", "requested_focus"}, "case")
    require(data["schema"] == SCHEMA or data["schema"] in LEGACY_SCHEMAS,
            "case:schema")
    value_in(data["mode"], {"fictional_fixture", "abstract_nonidentifying"},
             "case:mode")
    opaque_id(data["case_ref"], "C", "case_ref")
    registry = registry or load_registry()
    focus = data.get("requested_focus", [])
    require(isinstance(focus, list) and len(focus) <= 20
            and len(set(map(str, focus))) == len(focus)
            and set(focus) <= VALID_TRIGGERS - {"always"},
            "case:invalid_requested_focus")
    active, all_ids, superseded = normalize_events(data)
    correction_aliases = {
        e["target_event_id"]: e["replacement"]["event_id"]
        for e in data["events"] if e["kind"] == "event_correction"
    }
    recorded_sources = {}
    corrected_disclosures = set()
    corrected_documents = set()
    for event in data["events"]:
        if event["kind"] == "event_correction":
            original = recorded_sources.get(event["target_event_id"])
            replacement = event["replacement"]
            if original and original["kind"] == "disclosure":
                semantic_fields = (
                    "disclosure_id", "topic", "operation",
                    "channel", "recipient_id", "document_ids"
                )
                if any(original.get(k) != replacement.get(k)
                       for k in semantic_fields):
                    corrected_disclosures.add(original["disclosure_id"])
            if original and original["kind"] == "document_event":
                semantic_fields = (
                    "document_id", "document_category", "operation",
                    "recipient_id"
                )
                if any(original.get(k) != replacement.get(k)
                       for k in semantic_fields):
                    corrected_documents.add(original["document_id"])
            recorded_sources[replacement["event_id"]] = replacement
        else:
            recorded_sources[event["event_id"]] = event
    proceedings = build_proceedings(
        active, correction_aliases, corrected_disclosures, corrected_documents)
    records, responses = validate_responses(
        data, all_ids, superseded, proceedings, registry)
    coverage = make_coverage(
        proceedings, records, responses, registry, data["events"], full,
        requested_focus=focus)
    summarized = []
    for p in proceedings:
        out = dict(p)
        if not full:
            # No raw narratives exist, but default reports should still be compact.
            out.pop("event_ids", None)
        summarized.append(out)
    correction_log = [
        {"correction_event_id": e["event_id"],
         "supersedes": e["target_event_id"],
         "replacement_event_id": e["replacement"]["event_id"],
         "reason": e.get("correction_reason", "unspecified"),
         "recorded_revision": i + 1}
        for i, e in enumerate(data["events"])
        if e["kind"] == "event_correction"
    ]
    return {
        "schema": OUTPUT_SCHEMA, "mode": data["mode"],
        "correction_log": correction_log,
        "case_ref": data["case_ref"], "revision": len(data["events"]),
        "active_event_count": len(active),
        "corrections_applied": len(superseded),
        "proceedings": summarized, "coverage": coverage,
        "privacy_assurance": "not_an_anonymity_certification",
        "external_transmission": False,
        "legal_merits_verified": False,
        "host_session_automation_verified": False
    }


def compare(previous, current, *, registry=None):
    require(previous.get("case_ref") == current.get("case_ref"),
            "compare:case_ref_mismatch")
    left = previous.get("events")
    right = current.get("events")
    require(isinstance(left, list) and isinstance(right, list)
            and len(right) >= len(left) and right[:len(left)] == left,
            "compare:history_not_append_only")
    old_responses = previous.get("responses", [])
    new_responses = current.get("responses", [])
    require(isinstance(old_responses, list)
            and isinstance(new_responses, list)
            and new_responses[:len(old_responses)] == old_responses,
            "compare:response_history_not_append_only")
    p = evaluate(previous, registry=registry)
    c = evaluate(current, registry=registry)
    older = {x["proceeding_id"]: x for x in p["proceedings"]}
    changes = []
    for new in c["proceedings"]:
        old = older.get(new["proceeding_id"])
        if old is None:
            changes.append({"proceeding_id": new["proceeding_id"],
                            "kind": "new_proceeding"})
            continue
        for field in ("type", "claimed_regime", "stage", "lodgement",
                      "decision", "notification", "administrative_outcome",
                      "administrative_outcome_records", "post_issuance_events",
                      "documents", "disclosures",
                      "authority_positions", "deadlines", "issues"):
            if old[field] != new[field]:
                changes.append({"proceeding_id": new["proceeding_id"],
                                "field": field, "before": old[field],
                                "after": new[field]})
    return {"schema": "c27-state-diff/0.1.0",
            "previous_revision": p["revision"],
            "current_revision": c["revision"],
            "changes": changes,
            "current_coverage": c["coverage"],
            "legal_merits_verified": False}


def load_input(path):
    if path == "-":
        raw = sys.stdin.read(500001)
        require(len(raw) <= 500000, "input:too_large")
    else:
        require(Path(path).stat().st_size <= 500000, "input:too_large")
        raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inspect", "compare", "checklist"))
    parser.add_argument("--input", help="Abstract JSON path, or - for stdin")
    parser.add_argument("--previous", help="Previous append-only abstract JSON")
    parser.add_argument("--full", action="store_true",
                        help="Include every registry check and its status")
    args = parser.parse_args(argv)
    try:
        registry = load_registry()
        if args.command == "checklist":
            output = registry
        else:
            require(bool(args.input), "input:required")
            case = load_input(args.input)
            if args.command == "compare":
                require(bool(args.previous), "previous:required")
                output = compare(load_input(args.previous), case, registry=registry)
            else:
                output = evaluate(case, full=args.full, registry=registry)
        print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (StateError, OSError, json.JSONDecodeError, TypeError, KeyError) as e:
        print("C27_ERROR: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
