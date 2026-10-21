# Consultation route receipt gate

`scripts/consultation_route_gate.py` is the shared structural check for a
privacy-minimised route receipt. The local `render_consultation_dashboard` MCP
tool calls it before returning a versioned view model and full Markdown
fallback. For an explicit invocation it returns a validation record bound to
the receipt SHA-256 and rejects a `comprehensive` label when declared work
remains open. The local tool can render an MCP App UI in a compatible host; it
does not intercept the host's final answer or make the tool call mandatory.

## Receipt boundary

The input uses `references/contracts/consultation-route-receipt.schema.json`
(0.2.0 adds invocation, source-use and dashboard records; existing 0.1.0
receipts retain their legacy validation). A 0.2.0 explicit invocation,
dashboard request, or `material_change=true` requires a dashboard. It records
classification states, workflow IDs, C27 check IDs/statuses, reason codes, and
generated opaque references (`r_` followed by 12–32 lowercase hex characters).
It also carries constrained relative paths and digests needed to run local
validators. Keep actual jurisdictions, proceeding facts, legal questions,
case narratives, identities, dates, and document contents in the conversation,
not in the receipt. The receipt can record that a classification is
`recorded`, `unknown`, or `not_applicable` without copying its value.

Free-text receipt fields such as issue titles, missing/effect explanations,
operation reasons and source-read notes can accidentally contain personal or
identifying details. Generalize them and keep case facts in the conversation.
The validator does not detect or remove personal data from those fields.

Research artifact paths in the receipt are relative to the receipt's directory
and must remain inside it. They must identify only generalized,
non-identifying source-research plans and bundles. Module manifest/export paths
are relative to the installed plugin package. The gate reads these artifacts
and emits a JSON summary; it does not write or transmit them. It does not scan
filenames, artifact contents or free-text receipt fields for personal or
identifying information, so the privacy restriction is an operator requirement
rather than an enforced check.

## Checks performed

- Requires explicit records for the applicant-guidance entry workflows: route
  classification, C23 guidance, C27 reconciliation, attack-angle screening,
  and requested output. Source-research routes also require the existing
  research gate and requested output.
- Validates each selected C27 check against the current atomic registry and
  applies C27's shared status, method, reason, and trace rules through
  `c27_case_state.py`; it does not substitute the unrelated generic C5
  `completeness-record` contract.
- Resolves every referenced opaque evidence ID against the receipt's evidence
  index. Local artifacts are SHA-256 checked; module-conformance and research
  evidence entries must match successful output from the existing validators.
  Core operation records must cite the expected evidence kinds. Conversation
  and source-record entries remain model-declared references.
- Runs C3's existing pair-level `module_conformance.py` validator on each
  referenced module manifest/export. This does not match the consultation's
  actual geography to that module.
- Runs the existing `research_gate.py` validator on each referenced plan and
  evidence bundle.
- Runs `issue_source_preflight.py` for any preflight attached to a research
  artifact. Source-research routes require a preflight operation; its source
  gaps are carried into the route's outstanding-work list.
- Blocks the `comprehensive` label when any declared required or triggered
  operation, selected C27 check, required research task, or module check remains
  incomplete. It also requires the model to declare that it reviewed
  conditional workflows.
- Optionally reconciles declared issue records to the existing issue-signal
  routing matrix and C27 registry. Each issue record uses opaque issue/scope
  references, registered signal IDs, a disposition, and a conversation-record
  reference. The gate reports required routed checks missing from that scope.
  `source_missing` and `fact_missing` dispositions remain open for a
  comprehensive claim. This is additive: older 0.1 receipts without `issues`
  retain their prior validation behavior.
- For 0.2.0, resolves bundled source identity, section, category, and acceptance
  metadata from the existing retrieval index/manifests; calculates response
  and conversation totals from the unique logical-source ledger; checks read
  versus unread/memory states, pinpoints, currentness labels and evidence
  references; checks that dashboard issue summaries match unresolved declared
  issue dispositions; and checks module-use record uniqueness and any claimed
  C3 conformance against validator output, including the exact manifest
  `module_id` and canonical supported `role`. Optional `display_name` and
  `role_label` fields provide readable dashboard labels without changing the
  validated identity. `unavailable` tracking displays an
  unknown count, not zero. These are structural checks of self-reported
  consultation/module use, not proof that a source was read or a module used.
- The local gate rejects `runtime_recorded` source states. This package has no
  host-authenticated retrieval event contract, and hashing an arbitrary local
  artifact does not prove that a legal text was opened. A future host
  integration must validate its own trusted event before claiming independent
  source-read provenance.
- Returns a full deterministic Markdown dashboard and a validation record only
  after route, source, C27, module, research, preflight, and dashboard checks
  finish. The board includes every declared source, check, issue, module, and
  operation; no compact rendering limit applies. If receipt validation fails,
  no successful dashboard result is emitted.
- `scripts/consultation_dashboard_view.py` builds the versioned
  `consultation-dashboard-view` 1.0.0 from the validated receipt, source
  metrics, validator reports, and receipt-bound validation record. Operation
  and C27 progress counts are scoped to declared required/triggered operations
  and selected C27 rows. Unknown source tracking remains null; no percentage
  is generated for unknown or zero denominators.
- `scripts/consultation_dashboard_mcp.py` exposes the read-only
  `render_consultation_dashboard` tool over local stdio and the bundled
  `ui://freemovement-law/consultation-dashboard/v1.html` MCP App. It keeps
  receipt and explicitly referenced generalized research JSON in temporary
  local memory, makes no network calls, and logs no input content. The UI uses
  semantic status labels as well as color, responds to
  light/dark and forced-color modes, and provides the Markdown fallback as tool
  text. It requires Python 3.10+ and the package in `requirements-runtime.txt`.
- For an explicit local answer binding, `consultation_release_gate.py` requires
  the exact full dashboard and its validation record at the end of the answer.
  It binds the receipt bytes, answer bytes, and validation-record digest, then
  rechecks those exact bytes before release. This is a local controller path,
  not a host release gate.

Run it locally with:

```bash
python scripts/consultation_route_gate.py route-receipt.json
```

The normal plugin path is to let the host start the local MCP server from
`mcp.json` and call `render_consultation_dashboard`. Install the documented
Python dependency before enabling that stdio server. The local script command
above remains useful for development and does not display the MCP App UI.

An exit status of `3` rejects a `comprehensive` claim; `2` means the receipt or
an artifact is invalid. A valid partial route returns `0`, lists every open
work item, and includes its full board and validation record.

## Assurance limit

The gate checks only what the route receipt declares. It cannot determine
whether a conditional engine was omitted, whether a model-led review really
occurred, whether a relevant C27 check was omitted, whether a source supports a
proposition, or whether self-reported evidence exists or is authentic.
When the optional `issues` array is present, the gate validates signal IDs and
required check selection for each declared issue/scope. It cannot determine
whether the model omitted an issue, chose an incomplete signal set, or attached
an accurate disposition.

Resolving an ID means only that the receipt
declares it in the evidence index; only local artifact digests and outputs of
the invoked structural validators receive a deterministic check. A
`structurally_closed_declared_plan` result is not a legal-completeness finding.
Source-preflight account status is also not proof of legal sufficiency. It
checks declared source IDs against the pinned core pack or supported
Sweden/Türkiye module exports, ties evidence and claim trace to the exact
owner-specific task, and preserves unsupported or unregistered national
source work as open. Currentness and reviewer identity are not authenticated
by this gate.

For ordinary applicant consultations, do not pass real facts to
`case_controller.py`. If a country module is selected, this gate checks only
its reusable manifest/export pair. The case-geography-to-module match remains
unavailable in the ordinary lane; the receipt must record that restriction,
which leaves the comprehensive claim blocked where that match is required.

Genuine release enforcement requires the host to call this gate, fail closed
on invalid results, require the rendered board, and bind the checked receipt
to the exact answer it releases. The MCP tool is a callable plugin component,
not a host release hook; omission of the call or board is still possible.
