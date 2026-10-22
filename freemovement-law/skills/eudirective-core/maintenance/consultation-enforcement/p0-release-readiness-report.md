# P0 consultation enforcement release-readiness report

**Date:** 2026-10-22
**Candidate versions:** `freemovement-law` 0.57.0 / `eudirective-core` 0.56.0
**Disposition:** Locally implemented and structurally tested; human review and any host integration remain outstanding. Not committed or published.

## Work completed

- Recorded the 0.56.1 / 0.55.1 baseline and mapped the existing C27, C3, research, source-preflight, attack-coverage and release components.
- Added consultation receipt schema 0.4.0 for controlled applicant-guidance and source-research artifacts, with mandatory issue records and a full dashboard.
- Derived per-issue C27 check, source-owner and attack-topic obligations from existing routing metadata; bound reviewed source work to issue/scope/owner/source-class preflight records.
- Added priority pathway bindings to existing signal IDs, C27 checks and C5d catalogue patterns, while keeping screen outcomes non-determinative.
- Added strict local `controlled-release`, allowing qualified partial output with open work and withholding unsupported comprehensive claims or changed artifacts.
- Added material-revision scope tracking. Affected scopes remain open until reassessment is declared and the current checks/obligations reconcile.
- Updated package and core versions and CI coverage. C2 and C3 interfaces were not modified.
- Added a deferred manual host test plan instead of attempting a live ChatGPT or deployment test.

## Readiness boundaries

The local implementation can validate declared receipt structure and exact bytes routed through its controlled process. It does not prove that the assistant discovered every issue, chose every legally relevant signal or source class, performed each model-led review, or reached a legally correct result. The package does not have a ChatGPT pre-output callback, so ordinary hosted replies can bypass the local runner.

Three reviews remain necessary before a strict comprehensive route can be treated as operationally ready:

1. **Legal semantics:** independently review issue signals, source-owner/source-class derivation, priority topic bindings, C27/C5d mapping, and false-positive/negative boundaries.
2. **Privacy:** review the generalized-artifact boundary, free-text receipt fields, temporary files, logging and any future host data flow. The validators are not a complete personal-data detector.
3. **Release assurance:** if a host integration is later built, run the deferred target-host tests for output withholding, exact-byte binding, races, alternate paths and bypasses. Local tests do not establish host enforcement.

Until the first review is complete, route/pathway metadata stays `pending_independent_review`, which causes strict comprehensive receipts to fail closed. Qualified partial outputs can still pass through the local runner with their open work shown.

## Verification

The regression counts and local package inspection are recorded in `p0-regression-report.md`. The dashboard visual check and host release-veto check are explicitly deferred; no applicant data or live ChatGPT session was used for validation.
