# P0 consultation enforcement regression report

**Skill:** fm-maintenance v0.3.0
**Date:** 2026-10-23
**Base:** `824a29ed7aa41db35575ebc5f801544a991f9a95` (`main` before this follow-up)
**Candidate:** `freemovement-law` 0.58.1 / `eudirective-core` 0.57.1 / route receipt 0.5.0
**Data used:** fictional and abstract fixtures only; no applicant facts or private case data were sent to synthetic-only scripts.

## Candidate verification

The Python test scripts were run from `freemovement-law/skills/eudirective-core/scripts/`.

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_issue_selection.py` | Exit 0; 21 tests passed, including exact route/label/trigger matching, unmatched pathway preservation, and duplicate-match rejection. |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_issue_source_preflight.py` | Exit 0; 5 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_route_gate.py` | Exit 0; 24 tests passed, including present neutral route triggers paired with adverse predicates absent or unknown. |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_dashboard.py` | Exit 0; suite passed (47 tests). |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_p0_regressions.py` | Exit 0; 17 tests passed, including mismatched and all-only pathway predicates, linked C27 status, added/removed issue deltas, current-response removal evidence and merge targets. |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_p0_integrated.py` | Exit 0; 12 unmocked integrated tests passed, including a complete synthetic test-only release, unmapped-predicate fail-closed behavior, qualified partial release, resolved conditional outcomes remaining open when attack mapping is missing, and a separate open C27 check. |
| `PYTHONDONTWRITEBYTECODE=1 python3 run_selftest.py` | Exit 0; 156 checks passed, including C2/C3 and C5d guards. |
| `PYTHONPYCACHEPREFIX=/tmp/skills-p0-hardening-pycache-20261023 python3 -m compileall -q freemovement-law/skills/eudirective-core/scripts` | Exit 0; Python compilation passed. The temporary cache was removed. |
| `node freemovement-law/scripts/version_manifest.mjs --verify` | Exit 0; plugin/skill/library version manifest parity passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 freemovement-law/skills/eudirective-core/scripts/c27_case_state.py checklist` | Exit 0; C27 registry checklist emitted 301 checks. |
| `git diff --check` | Exit 0; no whitespace errors. |

The integrated suite calls the real research, source-preflight, route, dashboard, and controlled-release validators. It verifies exact-byte release of a complete synthetic test-only receipt and qualified partial output, plus blocking for tampered research, legacy 0.4.0 receipts, identifier-pattern matches, symlinked research paths, and invalid UTF-8 receipt/research artifacts. In the disposable success fixture only, synthetic pathway metadata and test-only review flags exercise a structurally closed path; this does not change production files or constitute independent legal/privacy review. Production generic route topics remain unmapped and unresolved; a neutral route trigger cannot create a candidate, and the missing mapping is named in the dashboard. No production comprehensive release is claimed. Production review metadata remains pending.

The 0.5 attack-screen trace separates selector-derived route triggers from adverse predicates. Trigger states must agree with the issue's declared signals; a mapped topic's predicate IDs are selector-bound and its tri-state values govern negative, unresolved, or candidate outcomes. A pathway supplies a generic topic's mapping only when route ID, exact topic label and trigger signal sets match; duplicate bindings are rejected. Unmatched generic topics remain `predicate_unmapped` and cannot close. Linked candidates remain open if any required bound C27 assessment is not closed, with open status recorded against the linked issue. Abstract revision regressions cover additions, removals, current-response evidence, and merge targets. Dashboard counts distinguish conditionally closed answers from unresolved partial work and count unresolved attack screens as partial/open. Integrated route/dashboard/release fixtures verify these outcomes against the gate.

## Fail-first result on the exact base

`test_consultation_p0_regressions.py`, copied into a detached worktree at the exact base SHA before candidate behavior was completed, ran 11 tests: 1 failed, 9 errored, and 1 skipped. The existing 0.4 path demonstrated that one issue in a shared scope could appear covered by another issue's C27 check. Strict issue-to-occurrence and other hardening APIs were absent. The complete baseline evidence is in `p0-hardening-baseline.md`.

## Limits and outstanding review

- Production source-class, route and attack-pathway metadata remains `pending_independent_review`; strict comprehensive release is intentionally blocked under production configuration.
- The local runner controls only output routed through that process. No ChatGPT pre-output hook or host release veto is implemented or verified.
- The privacy heuristic catches only a few obvious patterns. It is not a complete personal-data detector or anonymity guarantee. `controlled-release` itself creates no temporary files; its release path needs no temporary-file policy. Tests use disposable temporary directories only for fixtures.
- Model-declared source reads and assessments are not authenticated events. No test establishes legal correctness, source currency, or that the signal set covers every possible issue.
- The fresh-session version/dashboard/host-boundary checklist is written but not run. No live ChatGPT tests were performed or required in this maintenance session.
- The private `fm-maintenance` aggregate runner reported 35/39 staged scripts successful. Its bundled payload overlays the target checkout, and the four failures came from its nested Node process (`EPERM`), missing Sweden module notes in the staged payload, and two staged dashboard/route scripts. The candidate's current route, dashboard, issue-selection, integrated-release, preflight, P0 and self-test suites were run directly and passed. The aggregate runner result is not represented as a passing candidate run.
- Remote CI was not triggered from this local worktree.

This report does not claim independent legal/privacy approval, remote CI success, a ChatGPT host release veto, or a live ChatGPT test. The deferred manual display/release plan remains the operational check for a fresh installed version.
