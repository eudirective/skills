# Consultation route receipt gate

`scripts/consultation_route_gate.py` is a portable structural check for hosts
that can call a local plugin script before releasing an answer. It returns a
non-zero result when a route labelled `comprehensive` still has declared work
open. The plugin does not invoke it automatically, so the script alone is not
a release barrier.

## Receipt boundary

The input uses `references/contracts/consultation-route-receipt.schema.json`.
It records classification states, workflow IDs, C27 check IDs/statuses, reason
codes, and generated opaque references (`r_` followed by 12–32 lowercase hex
characters). It also carries constrained relative paths and digests needed to
run local validators. Keep actual jurisdictions, proceeding facts, legal
questions, case narratives, identities, dates, and document contents in the
conversation, not in the receipt. The receipt can record that a classification
is `recorded`, `unknown`, or `not_applicable` without copying its value.

Research artifact paths in the receipt are relative to the receipt's directory
and must remain inside it. They must identify only generalized,
non-identifying source-research plans and bundles. Module manifest/export paths
are relative to the installed plugin package. The gate reads these artifacts
and emits a JSON summary; it does not write or transmit them. It does not scan
filenames or artifact contents for personal or identifying information, so the
privacy restriction is an operator requirement rather than an enforced check.

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

Run it locally with:

```bash
python scripts/consultation_route_gate.py route-receipt.json
```

An exit status of `3` rejects a `comprehensive` claim; `2` means the receipt or
an artifact is invalid. A valid partial route returns `0` and lists open work.

## Assurance limit

The gate checks only what the route receipt declares. It cannot determine
whether a conditional engine was omitted, whether a model-led review really
occurred, whether a relevant C27 check was omitted, whether a source supports a
proposition, or whether self-reported evidence exists or is authentic.
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
on invalid results, and bind the checked receipt to the exact answer it
releases. No such host integration is established by this plugin package.
