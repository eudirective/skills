# C4 deterministic trust, privacy, and lifecycle foundation

## Status

C4 local deterministic foundation was introduced in `eudirective-core` v0.12.1 and remains unchanged in v0.18.0 under trust profile `0.1.0` while preserving the C3 producer boundary: inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, and element model `0.2.0` remain unchanged.

This foundation does **not** assert that the host runtime provides protected storage, trusted approval identity, connector isolation, secure deletion, or a non-bypassable outbound channel. Private-data mode therefore remains disabled until those properties are independently demonstrated.

## Three data views

Use `scripts/trust_controls.py build-views` to construct three separate artifacts from structured protected data and an explicit privacy policy:

1. **protected view** — preserves the supplied structured fields inside the protected workspace;
2. **analysis view** — retains only fields marked necessary for analysis;
3. **outbound view** — applies the exact purpose/destination/action profile, field/classification transformations, residual-linkability scoring, and attempt budget.

Supported outbound transformations are deliberately bounded: `drop`, `redact`, `keep`, `presence_only`, `date_to_month`, `date_to_year`, `country_only`, and `count_only`. The policy is declarative; it cannot contain executable expressions.

Transform compatibility is deterministic, not string-slicing permissive. `date_to_month` and `date_to_year` require valid ISO temporal values; malformed/arbitrary strings are rejected. When `allow_direct_identifiers=false`, direct identifiers may only use `drop`, `redact`, `presence_only`, or structurally valid `country_only`; `keep`, date substring transforms, and `count_only` are rejected before any risk reduction is applied.

Deterministic minimisation is not proof of anonymity. Residual combinations may still identify a person when combined with external information. The outbound view therefore carries limitations and residual-risk flags and is rejected by the controller when `eligible=false`.

## Purpose and destination binding

An outbound view is bound to:

- case ID and exact case revision;
- policy ID and policy digest;
- purpose;
- destination kind and exact destination;
- action;
- maximum delivery attempts.

The case controller stores the outbound-view digest and a SHA-256 digest of the destination rather than the raw destination. Changing purpose, destination, action, view content, or bound revision requires a new outbound artifact and new approval.

## Approval boundary

`approval-record` binds an approval or retry decision to the exact outbound view, purpose, destination, action, and prepared revision. Controller state stores only approval IDs, approval digests, hashed approver references, assurance level, and validity window.

`identity_assurance=unverified_local` records that a local/human approval artifact exists but does not prove who approved it. `host_verified` is reserved for a runtime that can actually demonstrate trusted approval identity. Private-data outbound would require host-verified identity in addition to private-data host enforcement; private-data intake remains disabled in this release.

Revocation creates a persistent approval tombstone and increments the lifecycle epoch. A revoked approval cannot be reused.

## Delivery state and retry discipline

Controller delivery state is explicit:

`prepared -> authorized -> in_flight -> acknowledged | rejected | outcome_unknown`

A timeout or unknown result does not cause automatic resubmission. A second attempt requires a separate `retry` approval bound to the same outbound artifact. The outbound policy limits attempts to 1–3 and the controller enforces the budget.

The controller records only delivery state/attempt metadata. It does not itself perform network sends or external writes in v0.18.0.

## Dependency pins

Controller state pins:

- inter-skill contract `0.2.0`;
- controller protocol `0.3.0`;
- element model `0.2.0`;
- conformance profile `0.2.0`;
- trust profile `0.1.0`.

Validation and release receipts bind the digest of this dependency set. C4 therefore adds control behavior without silently widening the frozen C3 producer contract.

## Recovery and lifecycle

State writes remain atomic and every mutating operation is revision-guarded. `checkpoint` creates an integrity-bound snapshot containing the exact controller state, state digest, revision, lifecycle epoch, approval tombstones, and dependency-pin digest. `validate-checkpoint` accepts only a checkpoint matching the exact current state and lifecycle epoch.

There is intentionally no automatic restore command. Without a trusted external lifecycle anchor, restoring an older snapshot could resurrect revoked approvals or regress delivery state and cause duplicate side effects. Recovery remains conservative until the deployment environment can provide a stronger persistence/rollback boundary.

## Privacy-safe audit

Controller history stores bounded metadata such as IDs, digests, statuses, attempt numbers, purpose labels, and destination digests. It does not store raw case narratives, raw outbound destinations, or raw approver references. History is bounded to prevent unbounded accumulation.

## Remaining host-dependent controls

Do not claim any of the following from the local C4 tests alone:

- protected storage or connector isolation;
- trusted human identity;
- guaranteed secure deletion of files, caches, logs, or backups;
- non-bypassable output-channel enforcement;
- resistance to all re-identification attacks;
- GDPR compliance or legal sufficiency of a minimisation policy.

Keep private-data mode disabled until those runtime properties are separately evidenced.
