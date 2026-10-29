# Consultation route receipt gate

`scripts/consultation_route_gate.py` is a portable structural check for a
runtime or host that can call a local plugin script before rendering or
releasing an answer. For a 0.9.0 substantive consultation it returns a
deterministic Full or Limited board preview and a validation record bound to
the receipt SHA-256. Board mode is independent of the declared coverage claim
and assessment status. It
returns a non-zero result when a route labelled `comprehensive` still has
declared work open. The skills-only plugin has no ChatGPT host hook, so the
script is not automatically invoked in hosted ChatGPT and cannot itself block
ordinary ChatGPT output.

## Receipt boundary

The input uses `references/contracts/consultation-route-receipt.schema.json`
(0.2.0 adds invocation, source-use and dashboard records; 0.3.0 adds response
and conversation source-discovery methods; 0.4.0 adds issue records and a
dashboard; strict 0.5.0 adds per-issue C27 assessment bindings, policy-derived
source classes, attack-screen predicate traces, abstract revision comparison,
and strict provenance requirements; strict 0.6.0 adds typed proceeding scopes
and source-attributed outcome/post-issuance routing; strict 0.7.0 requires
Full/Limited output mode and a case-specific strategy trigger screen; strict
0.8.0 separates Full/Limited consultation mode from coverage and binds strategy
triggers and limitations to current issue and evidence records. Receipts 0.1.0–0.4.0
remain readable for historical replay but are not accepted by the strict
controlled-release path. That command accepts 0.5.0–0.9.0. Version 0.8.0
requires a fresh board for each substantive applicant-guidance or source-research
response. It records classification states, workflow
IDs, C27 check IDs/statuses, reason codes, and generated opaque references
(`r_` followed by 12–32 lowercase hex characters). It also carries constrained
relative paths and digests needed to run local validators. Keep actual
jurisdictions, proceeding facts, legal questions, case narratives, identities,
dates, and document contents in the conversation, not in the receipt. The
receipt can record that a classification is `recorded`, `unknown`, or
`not_applicable` without copying its value.

Use `references/consultation-receipt-migration.md` to migrate a 0.7.0 receipt.
The migrator requires an explicit new consultation mode, refuses ambiguous
issue/evidence links, and leaves the new core-finalisation operation open as
`not_checked`.

Free-text receipt fields such as missing/effect explanations, operation
reasons and source-read notes can accidentally contain personal or identifying
details. The strict 0.5.0 gate rejects a small set of obvious patterns (email
addresses, long numeric identifiers, exact dates and travel-document-like
identifiers) in selected text fields. This is a limited screening heuristic:
it can miss identifying content and can flag harmless text. Generalize fields
and keep case facts in the conversation; the check does not guarantee
anonymity.

Research artifact paths in the receipt are relative to the receipt's directory
and must remain inside it. Absolute paths, path traversal and symlinked
components are rejected. They must identify only generalized,
non-identifying source-research plans and bundles. Module manifest/export paths
are relative to the installed plugin package. The gate reads these artifacts
and emits a JSON summary; it does not write or transmit them. It does not scan
filenames or full artifact contents for arbitrary personal information, so the
privacy restriction remains an operator requirement beyond the limited strict
text-field heuristic.

## Checks performed

- Requires explicit records for the applicant-guidance entry workflows: route
  classification, C23 guidance, C27 reconciliation, attack-angle screening,
  and requested output. Source-research routes also require the existing
  research gate and requested output. In 0.8.0 and 0.9.0 both in-scope request kinds
  require a core `consultation_finalisation` record; this receipt operation is
  model-declared unless a trusted runtime supplies observed execution evidence.
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
- For strict 0.5.0–0.9.0, every C27 occurrence has an opaque assessment reference and
  is bound either to exactly one issue or to an explicitly shared proceeding
  set. Duplicate `(scope, check, issue)` occurrences are rejected even when
  they use different assessment references. Issue-specific checks cannot be
  borrowed from a separate issue in the same proceeding.
- For strict 0.5.0–0.9.0, derives required C27 check IDs, source-owner IDs,
  source-class requirements, exclusions and attack-review topics from each
  declared issue's route/signal predicates using the existing routing matrix
  and the versioned `consultation-source-class-policy.json`. Conditional
  classes are required only when their declared route/signal predicates apply;
  an EU-only route does not force national binding law merely because a
  Member-State owner is possible. Exclusions require an explicit reason and
  evidence reference. Every derived obligation must have a receipt record.
  Owner-specific source tasks bind to the same opaque issue and scope in a
  validated 0.3.0 source preflight. Missing or open source work, unresolved
  attack topics, unlinked candidate issues, or missing routed checks block
  `comprehensive` and remain visible in the dashboard.
- Every strict 0.5.0–0.9.0 attack-topic record repeats selector-derived route
  triggers and records their states separately from adverse predicates. A
  route trigger selects review; it does not prove the adverse condition. For
  a mapped pathway, `adverse_predicate_states` must bind to the pathway's
  declared `adverse_signal`; only a `present` state can support a candidate.
  For generic topics without a topic-specific adverse-predicate mapping, the
  only accepted result is `unresolved` with reason `predicate_unmapped`. Such
  topics stay open, appear as missing in the dashboard, and block a
  `comprehensive` claim. In particular, a neutral route signal marked present
  cannot create a candidate. A linked candidate remains open if any required
  C27 assessment bound to its target issue is missing or has a non-closed
  status; the target issue's open check status is recorded separately.
  A maintained pathway can supply the mapping for a generic topic only when
  its consultation binding has the same route ID, exact topic label, and exact
  route-trigger signal sets. That pathway enriches the existing route-topic
  record; duplicate mappings are rejected. A different label or trigger set
  leaves the generic topic unresolved and the pathway as a separate review.
  This matching is structural and does not clear independent-review status.
- Dashboard outcome counts distinguish `evidence_resolved` and
  `qualified_condition` conditional answers from partial/open issues. Their
  closure status and evidence references appear on the issue card, and the
  dashboard's unresolved-issue list is reconciled against the route gate.
  A separate open issue-level check keeps the issue partial even when its
  conditional predicate is resolved.
- The current routing matrix and topic-pathway bindings are explicitly marked
  `pending_independent_review`. The strict gate therefore reports outstanding
  review items and blocks a `comprehensive` claim until a human reviewer has
  reviewed those mappings and their false-positive boundaries. A successful
  structural test does not clear that review status.
- For a 0.5.0 receipt, compares a privacy-minimised abstract state manifest
  containing opaque issue/scope references and registered signal IDs with
  categorical `present`, `absent`, or `unknown` states. The caller-declared
  `material_change` flag cannot suppress a detected state change. Changed,
  added or removed scopes must be reconciled against affected and reassessed
  references; affected C27, source and attack evidence must be current-response
  evidence. Missing state comparison remains open. This does not infer changes
  from real conversation narratives.
- For legacy 0.4.0 receipts with `invocation.material_change=true`,
  `revision_control.affected_scope_refs` identifies prior scope states as
  invalidated. Each affected scope must appear in `reassessed_scope_refs` after
  its current issue checks and linked obligations have been reviewed again.
  The affected issue, source-obligation, attack-review and C27 evidence must
  also be marked `record_scope=current_response`. An affected scope not listed
  as reassessed or lacking current-response evidence is reported as open and
  blocks a comprehensive claim. These remain declared review records, not
  proof that the model actually repeated the work.
- `candidate_issue_linked` records a possible issue for separate review; it is
  not a finding of illegality. `no_signal_identified` records only that no
  candidate was identified from the declared signals. The gate does not verify
  that the signal set or required source classes are legally complete.
- For 0.2.0 and later, resolves bundled source identity, section, category, and acceptance
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
- For 0.3.0, requires a discovery method for each source's current-response and
  conversation records. The dashboard separately counts matches to the
  bundled plugin library and sources marked as found through web search. The
  counts can overlap, and search provenance remains model-reported. Older
  receipts without discovery fields display unknown search totals when that
  provenance cannot be established.
- The local gate rejects `runtime_recorded` source states. This package has no
  host-authenticated retrieval event contract, and hashing an arbitrary local
  artifact does not prove that a legal text was opened. A future host
  integration must validate its own trusted event before claiming independent
  source-read provenance.
- Returns the deterministic Markdown board and a validation record only
  after route, source, C27, module, research, preflight, and dashboard checks
  finish. The board includes every declared source, check, issue, module, and
  operation; no compact rendering limit applies. If receipt validation fails,
  no successful dashboard result is emitted.
- For an explicit local answer binding, `consultation_release_gate.py` requires
  the exact validated board and its validation record at the end of the answer.
  It binds the receipt bytes, answer bytes, and validation-record digest, then
  rechecks those exact bytes before release. This is a local controller path,
  not a host release gate.
- `consultation_release_gate.py controlled-release` is an opt-in local path
  for 0.5.0–0.9.0 applicant-guidance or source-research artifacts. For 0.8.0 and 0.9.0
  it requires the top-level consultation mode and issue-linked strategy in the
  validated board. If the board is wholly
  absent, it may append the canonical preview once in memory; if a board is
  present but malformed or conflicting, release is blocked. It rechecks the
  receipt and answer bytes immediately before output. A limited answer can
  pass with missing items and effects shown; an unsupported comprehensive
  claim is withheld. The older `prepare`/`release` commands remain
  compatibility helpers.

Run it locally with:

```bash
python scripts/consultation_route_gate.py route-receipt.json
```

For a strict one-call local release, place the answer in `answer.md` and run:

```bash
python scripts/consultation_release_gate.py controlled-release \
  --receipt route-receipt.json --answer answer.md
```

An exit status of `3` rejects a `comprehensive` claim; `2` means the receipt or
an artifact is invalid. The controlled command uses exit `2` and writes no
answer to stdout when release is blocked. A valid partial route returns `0`,
lists every open work item, and includes its Limited board and validation record.

## Assurance limit

The gate checks only what the route receipt declares. It cannot determine
whether a conditional engine was omitted, whether a model-led review really
occurred, whether a relevant C27 check was omitted, whether a source supports a
proposition, or whether self-reported evidence exists or is authentic.
When the optional `issues` array is present, the gate validates signal IDs and
required check selection for each declared issue/scope. It cannot determine
whether the model omitted an issue, chose an incomplete signal set, or attached
an accurate disposition.

For 0.5.0–0.9.0 it derives declared source-owner and source-class coverage from the
versioned policy and checks every topic named by the existing routing matrix.
This does not prove that the policy or declared signal set includes every
legally relevant source class or issue. The attack screen remains
model-declared.

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

The local controlled command controls only its own output and can be bypassed
through other channels. Genuine host release enforcement requires a supported
host integration that calls the gate, fails closed, and binds the checked
receipt to the exact answer it releases. No such host integration is
established by this plugin package.

Version 0.9.0 requires a specific reason, missing work, effect and relevant references for Limited consultation mode. A Full claim requires applicable required and triggered model-led workflow reviews to be completed with acceptable recorded evidence. Deterministic operations have their own execution statuses and may be unavailable. An unknown strategy trigger can be addressed in a Full conditional strategy; the legacy 0.8.0 replay rules are preserved. These checks concern declared evidence and cannot verify that ordinary ChatGPT executed the work.
