"""Build the versioned, privacy-minimised consultation dashboard view model."""
from __future__ import annotations

from contract_validate import validate_obj
from consultation_dashboard import (
    CLASSIFICATION_LABELS,
    OPERATION_LABELS,
    _gap_work,
    _humanize,
    _open_work,
    render_dashboard,
)


VIEW_MODEL_VERSION = "1.0.0"


def _text(value: object, fallback: str = "not recorded") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _tone(status: str) -> str:
    value = status.casefold().replace("_", " ")
    if any(word in value for word in ("invalid", "rejected", "failed", "error")):
        return "danger"
    if any(word in value for word in ("partial", "incomplete", "unknown", "unavailable", "not checked", "not verified", "not recorded", "not run", "open")):
        return "warning"
    if any(word in value for word in ("reviewed", "assessed", "completed", "conformant", "passed", "valid", "used")):
        return "success"
    return "neutral"


def _field(label: str, value: object) -> dict:
    return {"label": label, "value": _text(value)}


def _item(title: str, *, status: str | None = None, detail: str | None = None,
          missing: str | None = None, effect: str | None = None,
          fields: list[dict] | None = None) -> dict:
    status_text = _text(status) if status is not None else None
    return {
        "title": _text(title),
        "status": status_text,
        "tone": _tone(status_text) if status_text is not None else "neutral",
        "detail": detail,
        "missing": missing,
        "effect": effect,
        "fields": fields or [],
    }


def _section(section_id: str, title: str, items: list[dict]) -> dict:
    return {"id": section_id, "title": title, "items": items}


def _reference_summary(route: dict, refs: list[str]) -> str:
    evidence = {item["evidence_ref"]: item for item in route.get("evidence", [])}
    labels = {
        "conversation_record": "conversation record",
        "source_record": "source record",
        "module_conformance": "module check",
        "research_gate": "research check",
        "source_preflight": "source coverage check",
        "local_artifact": "local artifact",
    }
    counts: dict[str, int] = {}
    for ref in refs:
        kind = evidence.get(ref, {}).get("kind", "unresolved reference")
        label = labels.get(kind, kind)
        counts[label] = counts.get(label, 0) + 1
    if not counts:
        return "none recorded"
    return "; ".join(f"{name} ({count})" for name, count in sorted(counts.items()))


def _source_metric(metric: dict) -> dict:
    count = metric.get("count")
    return {
        "status": _text(metric.get("status"), "unknown"),
        "count": count if isinstance(count, int) and not isinstance(count, bool) else None,
        "sections_count": len(metric.get("sections", [])) if count is not None else None,
        "provenance": "model-reported",
    }


def _operation_progress(route: dict, route_gaps: list[str], required_operation_ids: tuple[str, ...]) -> dict:
    operations = {item["operation_id"]: item for item in route.get("operations", [])}
    for operation_id in required_operation_ids:
        operations.setdefault(operation_id, {
            "operation_id": operation_id, "applicability": "required",
            "status": "not_recorded", "reason_code": "not_attempted", "evidence_refs": [],
        })
    applicable = [item for item in operations.values()
                  if item["applicability"] in {"required", "triggered"}]

    def has_gap(operation_id: str) -> bool:
        return any(
            gap.startswith(f"operation:{operation_id}:")
            or gap == f"required_operation_missing:{operation_id}"
            or gap == f"required_operation_misclassified:{operation_id}"
            for gap in route_gaps
        )

    completed = sum(
        item["status"] == "completed" and bool(item.get("evidence_refs"))
        and not has_gap(item["operation_id"])
        for item in applicable
    )
    return {
        "completed": completed,
        "total": len(applicable),
        "scope": "declared required or triggered operations",
        "label": "Operations with acceptable completion evidence",
    }


def _c27_progress(route: dict) -> dict:
    checks = route.get("c27_checks", [])
    completed = sum(
        item["record"]["status"] in {"assessed", "not_applicable"}
        for item in checks
    )
    return {
        "completed": completed,
        "total": len(checks),
        "scope": "selected C27 check records",
        "label": "Selected checks assessed or justified as not applicable",
    }


def build_dashboard_view_model(
    route: dict,
    source_report: dict,
    route_gaps: list[str],
    required_operation_ids: tuple[str, ...] = (),
    validation_record: dict | None = None,
    validator_reports: dict | None = None,
) -> dict | None:
    """Create a deterministic display model from a validated route and reports.

    Counts are scoped to recorded route items. They never imply that omitted
    issues or conditional work were discovered.
    """
    dashboard = route.get("dashboard")
    if dashboard is None:
        return None

    validation = validation_record or {
        "result": "not run by standalone dashboard renderer",
        "validator": "consultation_route_gate.py",
        "validator_version": "unknown",
        "receipt_sha256": "not available",
        "outstanding_count": len(set(route_gaps)),
    }
    reports = validator_reports or {}
    request_kind = route["request_kind"]
    status = dashboard["assessment_status"]
    status_labels = {"reviewed": "Reviewed", "partial": "Partial", "not_verified": "Not verified"}
    status_label = status_labels[status]
    operations_progress = _operation_progress(route, route_gaps, required_operation_ids)
    c27_progress = _c27_progress(route)
    open_work = _open_work(route_gaps)
    issue_summaries = dashboard["issue_summaries"]
    source_report = source_report or {"response": {}, "conversation": {}}
    response_metric = _source_metric(source_report.get("response", {}))
    conversation_metric = _source_metric(source_report.get("conversation", {}))

    if request_kind == "no_case_assessment":
        minimal_view = {
            "schema_version": VIEW_MODEL_VERSION,
            "title": "FreeMovement — Consultation Review",
            "request_kind": request_kind,
            "assessment": {
                "status": "not_verified",
                "label": "Not verified",
                "tone": "warning",
                "coverage_claim": route["coverage_claim"],
                "summary": "No case assessment was performed.",
            },
            "validation": {
                "result": _text(validation.get("result")),
                "result_label": _humanize(_text(validation.get("result"))),
                "validator": _text(validation.get("validator")),
                "validator_label": "Consultation route validator",
                "validator_version": _text(validation.get("validator_version"), "unknown"),
                "receipt_sha256": _text(validation.get("receipt_sha256"), "not available"),
                "outstanding_count": validation.get("outstanding_count", len(set(route_gaps))),
                "host_release_enforcement": "unavailable",
            },
            "progress": {
                "operations": {"completed": 0, "total": 0,
                                "scope": "not applicable", "label": "No case operations"},
                "c27_checks": {"completed": 0, "total": 0,
                                "scope": "not applicable", "label": "No case-state checks"},
                "issues_declared": 0,
                "open_validation_items": len(set(route_gaps)),
                "source_response": {"status": "not applicable", "count": None,
                                    "sections_count": None, "provenance": "none"},
                "source_conversation": {"status": "not applicable", "count": None,
                                        "sections_count": None, "provenance": "none"},
            },
            "sections": [_section("invocation", "Invocation and validation", [
                _item("No case assessment", status="Not verified",
                      detail="No case assessment was performed.",
                      fields=[
                          _field("Invocation", _humanize(route.get("invocation", {}).get("state", "not recorded"))),
                          _field("Validation result", validation.get("result", "not recorded")),
                          _field("Outstanding validation items", validation.get("outstanding_count", len(set(route_gaps)))),
                          _field("Host release control", "Unavailable; this board cannot block chat output."),
                      ]),
            ])],
            "caveats": [
                "No case facts, source totals, issue records, or module checks are presented.",
                "This plugin has no host release hook; the tool cannot block an ordinary chat response.",
            ],
            "text_fallback": render_dashboard(
                route, source_report, route_gaps, required_operation_ids,
                validation_record=validation_record, validator_reports=validator_reports,
            ),
        }
        validate_obj("consultation-dashboard-view", minimal_view)
        return minimal_view

    scope_items = []
    for key, item in route.get("classification", {}).items():
        label = CLASSIFICATION_LABELS.get(key, _humanize(key).title())
        scope_items.append(_item(
            label, status=_humanize(item["state"]),
            fields=[_field("Evidence", _reference_summary(route, [item["evidence_ref"]]))],
        ))
    conditional = route.get("conditional_review", {})
    scope_items.append(_item(
        "Conditional workflow review", status=_humanize(conditional.get("status", "not recorded")),
        fields=[_field("Evidence", _reference_summary(route, [conditional["evidence_ref"]]
                                                         if conditional.get("evidence_ref") else []))],
    ))

    operation_records = {item["operation_id"]: item for item in route.get("operations", [])}
    for operation_id in required_operation_ids:
        operation_records.setdefault(operation_id, {
            "operation_id": operation_id, "applicability": "required", "status": "not_recorded",
            "reason_code": "not_attempted", "evidence_refs": [],
        })
    operation_items = []
    for operation_id, item in sorted(
        operation_records.items(), key=lambda pair: (pair[0] not in required_operation_ids, pair[0])
    ):
        has_gap = any(
            gap.startswith(f"operation:{operation_id}:")
            or gap == f"required_operation_missing:{operation_id}"
            or gap == f"required_operation_misclassified:{operation_id}"
            for gap in route_gaps
        )
        result = "completion not verified" if has_gap and item["status"] == "completed" else _humanize(item["status"])
        label = OPERATION_LABELS.get(operation_id, _humanize(operation_id).title())
        fields = [
            _field("Operation ID", operation_id),
            _field("Applicability", _humanize(item["applicability"])),
            _field("Evidence", _reference_summary(route, item.get("evidence_refs", []))),
        ]
        if item.get("reason_code"):
            fields.append(_field("Recorded reason", _humanize(item["reason_code"])))
        related_open = next((work for work in open_work if work["title"] == label), None)
        operation_items.append(_item(
            label, status=result,
            missing=related_open["missing"] if related_open else None,
            effect=related_open["effect"] if related_open else None,
            fields=fields,
        ))

    issue_by_scope: dict[str, str] = {}
    summaries_by_ref = {item["issue_ref"]: item for item in issue_summaries}
    for issue in route.get("issues", []):
        summary = summaries_by_ref.get(issue["issue_ref"])
        if summary:
            issue_by_scope.setdefault(issue["scope_ref"], summary["title"])
    c27_items = []
    for index, entry in enumerate(route.get("c27_checks", []), start=1):
        record = entry["record"]
        title = issue_by_scope.get(entry["scope_ref"], f"Scope {index}")
        related_gap = next((work for gap in route_gaps
                            if gap.startswith(f"c27:{entry['scope_ref']}:{record['check_id']}:")
                            for work in [_gap_work(gap)] if work is not None), None)
        c27_items.append(_item(
            f"{title} — {record['check_id']}",
            status=f"{_humanize(record['status'])} · {_humanize(record['method'])}",
            detail=record["reason"],
            missing=related_gap["missing"] if related_gap else None,
            effect=related_gap["effect"] if related_gap else None,
            fields=[
                _field("Evidence", _reference_summary(route, record["evidence_refs"])),
                _field("Sources", _reference_summary(route, record["source_refs"])),
            ] + ([_field("Scope exclusion", record["scope_exclusion"])]
                 if record.get("scope_exclusion") else []),
        ))
    if not c27_items:
        c27_items.append(_item("Case-state checks", status="No C27 checks recorded"))

    issue_items = []
    route_issues = {item["issue_ref"]: item for item in route.get("issues", [])}
    for index, summary in enumerate(issue_summaries, start=1):
        issue = route_issues.get(summary["issue_ref"], {})
        signals = ", ".join(_humanize(signal) for signal in issue.get("signal_ids", [])) or "signals not recorded"
        issue_items.append(_item(
            f"Issue {index}: {summary['title']}",
            status=_humanize(issue.get("disposition", "not recorded")),
            missing=summary["missing"], effect=summary["effect"],
            fields=[_field("Signals", signals)],
        ))
    for item in open_work:
        issue_items.append(_item(
            item["title"], status="Open", missing=item["missing"], effect=item["effect"],
        ))
    if not issue_items:
        issue_items.append(_item("Open work", status="No declared outstanding items"))

    validation_items = [
        _item("Route-receipt schema and declared references", status="Passed",
              detail="The board is returned only after structural validation."),
        _item("C27 record validation", status=f"{reports.get('c27_check_count', 0)} selected checks validated",
              detail="Shared C27 status and trace rules."),
        _item("Issue-to-C27 routing", status=(
            f"{reports.get('issue_record_count', 0)} declared issues checked"
            if reports.get("issue_records_declared") else "No issue records declared"
        )),
        _item("Source-ledger consistency", status=(
            "Passed; source-use counts remain model-reported"
            if reports.get("source_ledger_validated") else "No consultation ledger available"
        )),
        _item("Dashboard consistency", status=(
            "Passed" if reports.get("dashboard_consistency_validated") else "Not run"
        )),
    ]

    research_items = []
    research_reports = {item.get("research_ref"): item for item in reports.get("research", [])
                        if item.get("research_ref")}
    preflight_reports = {item.get("preflight_id"): item for item in reports.get("source_preflight", [])
                         if item.get("preflight_id")}
    for artifact in route.get("research_artifacts", []):
        report = research_reports.get(artifact["research_ref"], {})
        research_items.append(_item(
            "Research bundle", status=_humanize(report.get("status", "not validated")),
            fields=[
                _field("Mode", _humanize(report.get("mode"))),
                _field("Coverage", _humanize(report.get("coverage_status"))),
                _field("Complete", report.get("research_complete", "unknown")),
                _field("Validated files", f"plan {artifact['plan_path']}; bundle {artifact['bundle_path']}"),
                _field("Tasks / findings / evidence / claims",
                       f"{report.get('task_count', 'unknown')} / {report.get('finding_count', 'unknown')} / "
                       f"{report.get('evidence_count', 'unknown')} / {report.get('claim_count', 'unknown')}"),
            ],
            missing=report.get("reason"),
        ))
        if artifact.get("preflight_ref"):
            preflight = preflight_reports.get(artifact["preflight_ref"], {})
            research_items.append(_item(
                "Official-source coverage", status=_humanize(preflight.get("status", "not validated")),
                fields=[
                    _field("Validation", _humanize(preflight.get("validation_status"))),
                    _field("Accounted for review", preflight.get("source_coverage_accounted_for_review", "unknown")),
                    _field("Research gate", _humanize(preflight.get("research_gate_status"))),
                    _field("Outstanding", ", ".join(preflight.get("outstanding", [])) or "none recorded"),
                ],
                missing=preflight.get("reason"),
            ))
    if not research_items:
        research_items.append(_item("Research artifacts", status="No research artifact supplied"))
    for report in reports.get("module_pairs", []):
        research_items.append(_item(
            f"Module-pair validator: {report.get('module_id', 'module not identified')}",
            status=_humanize(report.get("status", "unknown")),
            fields=[
                _field("Jurisdiction", _humanize(report.get("jurisdiction"))),
                _field("Contract / profile", f"{report.get('contract_version', 'unknown')} / {report.get('profile_version', 'unknown')}"),
                _field("Supported roles", ", ".join(report.get("supported_roles", [])) or "none reported"),
                _field("Records / usable / full text / gaps",
                       f"{report.get('owned_record_count', 'unknown')} / {report.get('usable_source_count', 'unknown')} / "
                       f"{report.get('full_text_source_count', 'unknown')} / {report.get('known_gap_count', 'unknown')}"),
            ],
            missing=report.get("reason"),
        ))
    if not reports.get("module_pairs"):
        research_items.append(_item("C3 module-pair validator", status="No validator report produced"))

    source_items = []
    if request_kind == "no_case_assessment":
        source_items.append(_item("Source ledger", status="Not applicable; no case assessment"))
    else:
        for source in route.get("source_ledger", {}).get("sources", []):
            source_items.append(_item(
                source["title"], status=_humanize(source["currentness"]),
                fields=[
                    _field("Section / jurisdiction", f"{source['section']} / {source['jurisdiction']}"),
                    _field("Category / type", f"{_humanize(source['category'])} / {source.get('source_type') or 'not recorded'}"),
                    _field("Source identity", f"{source['source_id']} · logical record {source['logical_source_id']}"),
                    _field("Official source URL", source.get("official_url") or "not recorded"),
                    _field("This answer", f"{_humanize(source['response_use'])}; {_humanize(source['response_provenance'])}"),
                    _field("Earlier chat", f"{_humanize(source['conversation_use'])}; {_humanize(source['conversation_provenance'])}"),
                    _field("Edition / pinpoints", f"{source.get('version_or_edition') or 'not recorded'} / {', '.join(source['pinpoints']) or 'not recorded'}"),
                    _field("Library state", _humanize(source["library_state"])),
                ],
            ))
        if not source_items:
            source_items.append(_item("Source records", status="No source records supplied"))

    module_items = []
    for module in dashboard["module_use"]:
        current = {"used": "Used in this answer", "not_used": "Not used in this answer",
                   "not_applicable": "Not applicable"}[module["response_use"]]
        earlier = {"used_earlier": "Used earlier in this chat", "not_used": "Not used earlier",
                   "unknown": "Earlier-chat use unknown"}[module["conversation_use"]]
        module_items.append(_item(
            module.get("display_name", module["module_id"]),
            status=current,
            detail=module["reason"],
            fields=[
                _field("Module ID / role", f"{module['module_id']} / {module.get('role_label', _humanize(module['role']))}"),
                _field("Earlier in this chat", earlier),
                _field("Availability", _humanize(module["availability"])),
                _field("C3 conformance", _humanize(module["conformance"])),
            ],
        ))
    if not module_items:
        module_items.append(_item("Module use", status="No module-use record supplied"))

    issue_routing_items = []
    for index, issue in enumerate(route.get("issues", []), start=1):
        issue_routing_items.append(_item(
            f"Issue {index}", status=_humanize(issue["disposition"]),
            fields=[
                _field("Signals", ", ".join(_humanize(value) for value in issue["signal_ids"])),
                _field("Scope evidence", _reference_summary(route, [issue["evidence_ref"]])),
            ],
        ))
    if not issue_routing_items:
        issue_routing_items.append(_item("Issue routing", status="No issue records declared"))

    summary = "Validation is scoped to the declared route and selected evidence."

    validation_result = _text(validation.get("result"))
    view_model = {
        "schema_version": VIEW_MODEL_VERSION,
        "title": "FreeMovement — Consultation Review",
        "request_kind": request_kind,
        "assessment": {
            "status": status,
            "label": status_label,
            "tone": _tone(status_label),
            "coverage_claim": route["coverage_claim"],
            "summary": summary,
        },
        "validation": {
            "result": validation_result,
            "result_label": _humanize(validation_result),
            "validator": _text(validation.get("validator")),
            "validator_label": "Consultation route validator",
            "validator_version": _text(validation.get("validator_version"), "unknown"),
            "receipt_sha256": _text(validation.get("receipt_sha256"), "not available"),
            "outstanding_count": validation.get("outstanding_count", len(set(route_gaps))),
            "host_release_enforcement": "unavailable",
        },
        "progress": {
            "operations": operations_progress,
            "c27_checks": c27_progress,
            "issues_declared": len(route.get("issues", [])),
            "open_validation_items": len(set(route_gaps)),
            "source_response": response_metric,
            "source_conversation": conversation_metric,
        },
        "sections": [
            _section("scope", "Task scope", scope_items),
            _section("operations", "Work performed and engine checks", operation_items),
            _section("c27", "C27 case-state checks", c27_items),
            _section("open-work", "Material issues and open work", issue_items),
            _section("validators", "Deterministic validator results", validation_items),
            _section("research", "Research and source coverage validation", research_items),
            _section("sources", "Source ledger", source_items),
            _section("modules", "Module use in this answer and chat", module_items),
            _section("issue-routing", "Issue routing record", issue_routing_items),
        ],
        "caveats": [
            "Counts are scoped to declared receipt records and do not show omitted work.",
            "Model-reported facts, source reads and legal reasoning are not authenticated.",
            "This plugin has no host release hook; the tool cannot block an ordinary chat response.",
        ],
        "text_fallback": render_dashboard(
            route, source_report, route_gaps, required_operation_ids,
            validation_record=validation_record, validator_reports=validator_reports,
        ),
    }
    validate_obj("consultation-dashboard-view", view_model)
    return view_model


def render_dashboard_view_model(view_model: dict | None) -> str | None:
    """Return the accessible Markdown fallback from a validated display model."""
    if view_model is None:
        return None
    validate_obj("consultation-dashboard-view", view_model)
    return view_model["text_fallback"]
