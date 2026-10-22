# P0 consultation enforcement regression report

**Date:** 2026-10-22
**Candidate:** `freemovement-law` 0.57.0 / `eudirective-core` 0.56.0
**Data used:** synthetic and abstract fixtures only; no applicant dossier or private case data was supplied to a script.

## Results

| Check | Result |
| --- | --- |
| `test_consultation_issue_selection.py` | Passed, 18 tests. |
| `test_issue_source_preflight.py` | Passed, 5 tests. |
| `test_consultation_route_gate.py` | Passed, 23 tests. |
| `test_consultation_dashboard.py` | Passed, 47 tests. |
| `run_selftest.py` | Passed, 156 checks, including existing C2/C3 compatibility and C5d false-positive boundaries. |
| Attack-angle inventory generation | Passed: 366 records, including 6 priority review pathways. |
| C27 registry checklist smoke check | Passed. |
| Version manifest parity | Passed for plugin, skills and bundled source-library snapshot. |
| Diff whitespace validation | Passed. |

The new tests cover issue-derived C27/source-owner/attack-topic requirements; source-preflight issue/scope/owner binding; stale-scope reporting after a material change; exact answer-byte release for a qualified partial answer; rejection of unsupported comprehensive claims and legacy receipts on the strict path; and detection of an answer change between validation passes. The workflow now runs the source-preflight structural suite in CI.

## Local package inspection

A temporary candidate archive was built and inspected locally, then removed. The ZIP integrity check passed; all required plugin metadata, schema, runner and deferred live-test-plan files were present. The inspected archive had 2,564 files and no `/evaluations/` paths. No install, upload, commit or publication occurred.

## Limits and review items

- The local runner can control only output routed through that process. No ChatGPT host hook or hosted release veto was available or tested.
- The strict route and attack-pathway maps remain marked `pending_independent_review`; therefore strict comprehensive releases are deliberately blocked pending review.
- Source classes, declared issues and review outcomes remain model-declared. Structural validation does not establish legal sufficiency, source authenticity, reviewer identity, or that every issue was identified.
- No live ChatGPT visual or host-release test was performed. The deferred procedures are in `references/consultation-dashboard-live-test-plan.md` and `references/consultation-controlled-release-live-test-plan.md`.
- Passing deterministic tests is not an independent legal, privacy, or release-assurance review.
