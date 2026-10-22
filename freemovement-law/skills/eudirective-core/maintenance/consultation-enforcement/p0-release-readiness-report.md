# P0 consultation enforcement release-readiness report

**Skill:** fm-maintenance v0.3.0
**Date:** 2026-10-23
**Candidate:** `freemovement-law` 0.58.1 / `eudirective-core` 0.57.1
**Base:** `824a29ed7aa41db35575ebc5f801544a991f9a95`
**Disposition:** implementation and local synthetic checks are complete. Independent legal/privacy review and the host-level release veto remain outstanding; production strict comprehensive release is not enabled.

## Implemented

- Added strict consultation receipt schema 0.5.0 while preserving 0.1.0–0.4.0 for historical reading. Strict controlled release requires 0.5.0.
- Bound each C27 assessment occurrence to an exact issue or explicit shared proceeding set; duplicate `(scope, check, issue)` occurrences are rejected.
- Derived required and conditional source classes from versioned route/signal policy, with explicit source-owner exclusions and evidence-backed exclusion records. A potential Member-State owner alone does not force national law for an EU-only route.
- Required attack-screen traces separate neutral route triggers from topic-specific adverse predicates. Existing pathways bind an adverse predicate to their declared `adverse_signal`; a pathway maps a generic topic only when route ID, exact topic label and trigger sets match. Absent or unknown adverse states cannot create a candidate. Unmapped generic route topics stay unresolved, are named in the dashboard, and block production comprehensive claims. Safe issue links are required, and self-linked candidates cannot satisfy the screen.
- Compared abstract previous/current signal states (`present`, `absent`, `unknown`) and kept changed or unavailable scopes open until current-response reassessment is declared. Regressions cover added/removed issues, current-response removal evidence, and valid/invalid merge targets.
- Linked candidate closure considers every required C27 check bound to the linked issue, including non-closed statuses, and records issue-specific open-check details.
- Dashboard issue counts put unresolved mandatory attack screens in the partial/open bucket, including issues whose primary disposition says supported. A separate open C27 check keeps the issue partial while the conditional closure status/evidence remains visible; integrated release tests reconcile these paths against the route gate.
- Tightened strict provenance, dashboard reconciliation, path/symlink checks, and a limited scan for obvious identifiers in selected free-text fields.
- Added unmocked integration tests that run the real research, preflight, route, dashboard and controlled-release validators. A complete synthetic path uses test-only reviewed metadata in a disposable copy to exercise exact-byte success; this neither changes production review flags nor certifies legal semantics. Qualified partial release and adversarial fail-closed cases are also covered. Production comprehensive release remains blocked while generic attack predicates and independent review remain outstanding.
- Updated CI steps and synchronized package metadata to `freemovement-law` 0.58.1 / `eudirective-core` 0.57.1.
- Prepared an independent route/pathway review packet and a copyable fresh-session test plan. Neither review nor live ChatGPT testing is represented as complete.

## Verification evidence

The exact local commands and results are in `p0-regression-report.md`. All listed local checks passed. Fail-first results on the exact base are in `p0-hardening-baseline.md`. CI configuration was updated but remote CI was not triggered from this local worktree.

## Release gates still open

1. **Independent legal/privacy review:** the route, source-class and attack-pathway mappings in production metadata remain `pending_independent_review`. The review packet is ready for a human reviewer; no approval has been fabricated.
2. **Host integration:** the skill cannot force local validators to run or intercept ordinary ChatGPT output. No supported pre-output release hook has been implemented or tested. The local controlled-release command governs only its own output.
3. **Privacy assurance:** selected text patterns and path controls reduce common leakage risks but do not provide general personal-data detection or an anonymity guarantee.

The C2 element model and frozen C3 contracts/validators were preserved. No source-library rewrite, new outbound flow, or live ChatGPT test was performed. Remote CI, human legal/privacy signoff and a ChatGPT host-level release veto are separate pending checks.
