# Consultation assurance and host capability

**Decision date:** 2026-10-22
**Scope:** `freemovement-law` 0.57.0 / `eudirective-core` 0.56.0
**Status:** local structural gates and the opt-in controlled-release runner are available; ChatGPT host release enforcement is not implemented or verified. Consultation routing and attack-pathway bindings remain pending independent review.

## Assurance claims

| Layer | What it can establish | What it cannot establish |
| --- | --- | --- |
| Skill instructions and ordinary ChatGPT answer | The assistant can be instructed to classify a request, select workflows, report evidence and disclose open work. | Instructions cannot prove that a review happened, discover every omitted issue, validate a dashboard, or prevent answer release. |
| Local route gate | A privacy-minimised receipt is structurally valid; its declared C27 checks, issue signals, attached research/preflight artifacts, module pairs and dashboard reconcile against the bundled contracts. | It cannot verify the truth of model-declared records, discover omitted issues, establish legal correctness/currentness, or authenticate a reviewer. |
| Local release binding | The exact receipt, validation result and answer bytes are unchanged between prepare and release. The local command emits the checked answer only when the binding still matches. | The binding is not signed, does not identify or authenticate an approver, and only controls invocations routed through this local command. Other output channels can bypass it. |
| ChatGPT host | No target-host integration is established. | No verified pre-output veto, authenticated tool-execution ledger, or binding to the exact answer shown to the user is available to this skills-only plugin. |

The local command is a controlled artifact workflow for generalized, non-identifying material. It is not a guarantee that a live ChatGPT answer passed through the workflow.

## Data boundary

- Keep real applicant narratives, identities, dates, case numbers and document contents in the conversation or an approved private case workspace. Never copy them into route receipts, research plans, bundles, fixtures, or synthetic-only engines.
- Route receipts use opaque references and constrained status values. Their free-text titles, reasons, source notes and dashboard explanations can still contain identifying details; the validator does not perform a full personal-data scan.
- Research plans and source-preflight artifacts may contain only generalized legal/source questions. They are not case files, module exports, or controller stages.
- Synthetic-only C27/C3/C5/C6/C7 tooling remains restricted to its enrolled fictional or abstract inputs. P0 does not expand those input permissions.
- A deterministic structural result is not legal advice, a legal finding, or proof that a source supports a proposition.

## Existing implementation

`consultation_route_gate.py` validates the declared route receipt and emits its full deterministic dashboard. It reuses the C27 registry and validator, C3 module-conformance validator, `research_gate.py`, and `issue_source_preflight.py`. The receipt records what the model says it classified or reviewed; the gate validates structure and supplied evidence references, not whether that work truly happened.

`consultation_release_gate.py prepare` validates a receipt and answer artifact and creates a local digest binding. `consultation_release_gate.py release` reruns validation and emits the exact answer bytes only when the receipt, answer and validation digest still match. The schema 0.4.0 `controlled-release` command performs the strict check and exact-byte emission in one local call; it is limited to generalized, non-identifying artifacts. A skills-only ChatGPT consultation does not invoke these commands automatically. Pending independent review of routing/pathway metadata blocks strict comprehensive releases, while a partial answer may be emitted with its open work displayed.

The C2 element model (`0.2.0`) and frozen C3 inter-skill contract (`0.2.0`), conformance profile (`0.2.0`), controller protocol (`0.3.0`) and element model (`0.2.0`) are outside the consultation receipt boundary and must remain unchanged.

## Deployment decision

Use the local controlled workflow only when a maintained host or operator explicitly routes the answer through it. Keep ordinary ChatGPT guidance model-led and describe its checks as model-reported. Do not describe ordinary ChatGPT output as release-gated.

A production host veto requires a supported host integration and a target-deployment test showing that the host withholds the exact answer when validation fails. Platform documentation review or a local script test is not that evidence. The manual ChatGPT dashboard display plan remains deferred at `references/consultation-dashboard-live-test-plan.md`; the future host release-veto test is specified at `references/consultation-controlled-release-live-test-plan.md` and has not been performed.

## Review required

Before describing a future strict consultation contract as operationally complete, a human reviewer must review its source-owner and source-class routing semantics, privacy boundary, and exact release assurance. Those are review judgments, not facts that the structural validators can certify.
