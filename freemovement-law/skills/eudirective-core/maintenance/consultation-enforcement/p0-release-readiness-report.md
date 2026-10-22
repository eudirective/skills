# P0 consultation enforcement release-readiness report

**Date:** 2026-10-23
**Candidate:** `freemovement-law` 0.58.0 / `eudirective-core` 0.57.0
**Base:** `ca76b49b00390c95006ded2f63cb0561cc4f6502`
**Disposition:** local implementation and synthetic verification complete; independent legal/privacy review remains pending. Not committed, pushed, or published.

## Implemented

- Added strict consultation receipt schema 0.5.0 while preserving 0.1.0–0.4.0 for historical reading. Strict controlled release requires 0.5.0.
- Bound each C27 assessment occurrence to an exact issue or explicit shared proceeding set; duplicate `(scope, check, issue)` occurrences are rejected.
- Derived required and conditional source classes from versioned route/signal policy, with explicit source-owner exclusions and evidence-backed exclusion records. A potential Member-State owner alone does not force national law for an EU-only route.
- Required attack-screen predicate traces are bound to selector-derived route/pathway trigger predicates. Exact predicate sets and tri-state any/all outcomes are checked; unrelated signals cannot close or satisfy a screen. Safe issue links are required, and self-linked candidates cannot satisfy the screen.
- Compared abstract previous/current signal states (`present`, `absent`, `unknown`) and kept changed or unavailable scopes open until current-response reassessment is declared. Regressions cover added/removed issues, current-response removal evidence, and valid/invalid merge targets.
- Linked candidate closure considers every required C27 check bound to the linked issue, including non-closed statuses, and records issue-specific open-check details.
- Dashboard issue counts separate conditionally closed answers from partial/open issues when no other issue-level check remains open. A separate open C27 check keeps the issue partial while the conditional closure status/evidence remains visible; integrated release tests check both paths against the route gate.
- Tightened strict provenance, dashboard reconciliation, path/symlink checks, and a limited scan for obvious identifiers in selected free-text fields.
- Added unmocked integration tests that run the real research, preflight, route, dashboard and controlled-release validators, including exact-byte release and adversarial fail-closed cases.
- Updated CI steps and synchronized package metadata to `freemovement-law` 0.58.0 / `eudirective-core` 0.57.0.
- Prepared an independent route/pathway review packet and a copyable fresh-session test plan. Neither review nor live ChatGPT testing is represented as complete.

## Verification evidence

The exact local commands and results are in `p0-regression-report.md`. All listed local checks passed. Fail-first results on the exact base are in `p0-hardening-baseline.md`. CI configuration was updated but remote CI was not triggered from this local worktree.

## Release gates still open

1. **Independent legal/privacy review:** the route, source-class and attack-pathway mappings in production metadata remain `pending_independent_review`. The review packet is ready for a human reviewer; no approval has been fabricated.
2. **Host integration:** the skill cannot force local validators to run or intercept ordinary ChatGPT output. No supported pre-output release hook has been implemented or tested. The local controlled-release command governs only its own output.
3. **Privacy assurance:** selected text patterns and path controls reduce common leakage risks but do not provide general personal-data detection or an anonymity guarantee.

The C2 element model and frozen C3 contracts/validators were preserved. No source-library rewrite, new outbound flow, live ChatGPT test, commit, push, PR, package build, install, or publication occurred.
