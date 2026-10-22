# P0 consultation enforcement regression report

**Date:** 2026-10-23
**Base:** `ca76b49b00390c95006ded2f63cb0561cc4f6502`
**Candidate:** `freemovement-law` 0.58.0 / `eudirective-core` 0.57.0 / route receipt 0.5.0
**Data used:** fictional and abstract fixtures only; no applicant facts or private case data were sent to synthetic-only scripts.

## Candidate verification

The Python test scripts were run from `freemovement-law/skills/eudirective-core/scripts/`.

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_issue_selection.py` | Exit 0; 18 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_issue_source_preflight.py` | Exit 0; 5 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_route_gate.py` | Exit 0; 23 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_dashboard.py` | Exit 0; suite passed (47 tests). |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_p0_regressions.py` | Exit 0; 17 tests passed, including mismatched and all-only pathway predicates, linked C27 status, added/removed issue deltas, current-response removal evidence and merge targets. |
| `PYTHONDONTWRITEBYTECODE=1 python3 test_consultation_p0_integrated.py` | Exit 0; 11 unmocked integrated tests passed, including predicate mismatch/false-candidate rejection, both resolved conditional outcomes, and a resolved condition with a separate open C27 check. |
| `PYTHONDONTWRITEBYTECODE=1 python3 run_selftest.py > /tmp/skills-p0-hardening-selftest.json` | Exit 0; 156 checks passed, including C2/C3 and C5d guards. |
| `PYTHONPYCACHEPREFIX=/tmp/skills-p0-hardening-pycache python3 -m compileall -q freemovement-law/skills/eudirective-core/scripts` | Exit 0; Python compilation passed. The temporary cache was removed; no `__pycache__` remains in the plugin tree. |
| `node freemovement-law/scripts/version_manifest.mjs --verify` | Exit 0; plugin/skill/library version manifest parity passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 freemovement-law/skills/eudirective-core/scripts/c27_case_state.py checklist > /tmp/skills-p0-hardening-c27-checklist.json` | Exit 0; C27 registry checklist emitted successfully. |
| `git diff --check` | Exit 0; no whitespace errors. |

The integrated suite calls the real research, source-preflight, route, dashboard, and controlled-release validators. It verifies exact-byte release for a fully reconciled fictional receipt in a disposable test-only reviewed configuration and a qualified partial receipt; blocking for tampered research, stale source accounting, legacy 0.4.0 receipts, identifier-pattern matches, symlinked research paths, and invalid UTF-8 receipt/research artifacts; and absence of answer bytes and fixture/path leakage on blocked releases. Production review metadata remains pending.

The 0.5 attack-screen trace now repeats selector-derived trigger predicate IDs and must match them exactly; tri-state any/all logic binds the recorded outcome to those predicates. Linked candidates remain open if any required bound C27 assessment is not closed, with open status recorded against the linked issue. Abstract revision regressions cover additions, removals, current-response evidence, and merge-target validity. Dashboard counts distinguish conditionally closed answers from unresolved partial work when no separate issue-level check is open. A separate open required check keeps that issue in partial/open status while the conditional closure status and evidence remain visible. Integrated route/dashboard/release fixtures verify both outcomes against the gate.

## Fail-first result on the exact base

`test_consultation_p0_regressions.py`, copied into a detached worktree at the exact base SHA before candidate behavior was completed, ran 11 tests: 1 failed, 9 errored, and 1 skipped. The existing 0.4 path demonstrated that one issue in a shared scope could appear covered by another issue's C27 check. Strict issue-to-occurrence and other hardening APIs were absent. The complete baseline evidence is in `p0-hardening-baseline.md`.

## Limits and outstanding review

- Production source-class, route and attack-pathway metadata remains `pending_independent_review`; strict comprehensive release is intentionally blocked under production configuration.
- The local runner controls only output routed through that process. No ChatGPT pre-output hook or host release veto is implemented or verified.
- The privacy heuristic catches only a few obvious patterns. It is not a complete personal-data detector or anonymity guarantee. `controlled-release` itself creates no temporary files; its release path needs no temporary-file policy. Tests use disposable temporary directories only for fixtures.
- Model-declared source reads and assessments are not authenticated events. No test establishes legal correctness, source currency, or that the signal set covers every possible issue.
- The fresh-session version/dashboard/host-boundary checklist is written but not run. No live ChatGPT tests were performed or required in this maintenance session.
- CI workflow steps were updated but remote CI was not triggered from this local-only worktree.

No commit, push, PR, package build, install or publication occurred in this implementation worktree.
