# P0 consultation hardening baseline

**Date:** 2026-10-23
**Repository:** `eudirective/skills`
**Baseline commit:** `ca76b49b00390c95006ded2f63cb0561cc4f6502`
**Working branch:** `codex/p0-hardening-v0-5-20261023`
**Worktree at baseline:** clean
**Published:** no

## Version and compatibility boundary

- Plugin package: `freemovement-law` 0.57.0.
- Core skill: `eudirective-core` 0.56.0.
- Consultation route receipt: schema 0.4.0 is the latest accepted version; 0.1.0–0.4.0 are readable.
- Issue source preflight: contract 0.3.0; older 0.1.0 and 0.2.0 are also accepted.
- Local release binding: schema 0.2.0.
- C2 element model: 0.2.0.
- Frozen C3 boundary: inter-skill contract 0.2.0, conformance profile 0.2.0, controller protocol 0.3.0, element model 0.2.0.

No `AGENTS.md` exists in this checkout or its `/tmp` ancestors. The plan's verified base was `ca76b49b00390c95006ded2f63cb0561cc4f6502`. Before the implementation branch was created, `main` advanced to `61fc9a49f1cb0bf3e0b1b6a40654252901319b66` in a source-library synchronization commit. The implementation branch used `61fc9a4` as its parent; the P0 change set did not modify source-library files. The fail-first regression run below was performed against the plan's exact `ca76b49` base. The worktree was clean before this baseline report was added.

## Baseline commands and observed results

Every command ran from `/tmp/skills-p0-hardening` with the source revision above. No applicant narrative or private case data was supplied to a synthetic-only script.

| Command | Exit | Result |
| --- | ---: | --- |
| `PYTHONDONTWRITEBYTECODE=1 python freemovement-law/skills/eudirective-core/scripts/test_consultation_issue_selection.py` | 0 | 18 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python freemovement-law/skills/eudirective-core/scripts/test_issue_source_preflight.py` | 0 | 5 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python freemovement-law/skills/eudirective-core/scripts/test_consultation_route_gate.py` | 0 | 23 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python freemovement-law/skills/eudirective-core/scripts/test_consultation_dashboard.py` | 0 | 47 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python freemovement-law/skills/eudirective-core/scripts/run_selftest.py` | 0 | 156 checks passed, including C2/C3 boundaries and the C5d no-violation inference guard. |
| `PYTHONDONTWRITEBYTECODE=1 python -m compileall -q freemovement-law/skills/eudirective-core/scripts` | 0 | Compilation passed. |
| `node freemovement-law/scripts/version_manifest.mjs --verify` | 0 | Plugin/core version parity passed. |

Baseline test coverage is green, but the tests do not prove the P0 invariants below. The defects are therefore reproduced through source inspection and new targeted regression cases, not through an existing failing test.

## Defects to pin with abstract regressions

1. **C27 issue attribution is proceeding-wide.** `check_declared_issues` builds `actual_by_scope` and lets each issue satisfy its required checks from any record in the same scope. The receipt has no unique assessment-occurrence reference or exact issue-to-occurrence list. Two issues sharing a scope can therefore borrow issue-specific check coverage.
2. **Conditional closure is under-specified.** A single `conditional_review.status=reviewed` does not identify which conditional predicates were considered or what evidence-backed closure permits a conditional answer to count as reviewed. Dashboard issue dispositions and open-work calculation need one strict rule.
3. **Source classes are receipt-selected.** Routing derives owners but not each owner's minimum required source classes. The gate checks only that the classes the receipt chose match its preflight, allowing a strict receipt to omit an owner-required class.
4. **Attack candidates can self-link.** The gate accepts `candidate_issue_linked` when the referenced issue exists, including the same issue, and does not require the linked issue's own assessment trace or check binding. Negative/unresolved outcomes have no required predicate/reason trace.
5. **Revision flags are caller-declared.** The 0.4.0 validator requires `revision_control` when `material_change=true`, but does not compare a prior and current abstract state. A caller can set `material_change=false` while changing abstract routing signals.
6. **Strict provenance and privacy are incomplete.** Legacy 0.4.0 permits absent discovery fields in some contexts; free-text and diagnostic values, symlinks/path escapes in some local reads, malformed UTF-8 and stderr content need stricter limits and explicit tests.
7. **Release tests do not cover the connected validators.** The route suite tests local receipt release and mutation, but its synthetic strict receipt has no real research-plan/evidence/preflight family exercising the full source-owner path.

## Fail-first regression plan

The new abstract cases will cover: two issues sharing a scope with issue-specific C27 references; an unresolved conditional predicate; an owner with a policy-required source class omitted; a self-linked and an unassessed linked attack candidate; a missing strict discovery/provenance record; changed abstract signals falsely labelled non-material; and the complete local validator/release path with actual research, preflight, route and dashboard validators.

All production routing and pathway review flags remain `pending_independent_review`. Test-only reviewed metadata may be used only in isolated copies. No test or implementation result is a legal-merits conclusion, source authentication, proof of source use, anonymity guarantee, or ChatGPT host veto.

## Fail-first regression run on the exact base

The new synthetic-only regression module was copied into a detached temporary worktree at the recorded base SHA and run before candidate behavior was completed:

| Command | Exit | Result |
| --- | ---: | --- |
| `PYTHONDONTWRITEBYTECODE=1 python freemovement-law/skills/eudirective-core/scripts/test_consultation_p0_regressions.py` | 1 | 11 regressions ran: 1 failed, 9 errored and 1 skipped. The existing 0.4 `check_declared_issues` path is invoked with two issues sharing one scope; it returns no C27-missing gap for the second issue after the scope-wide union is supplied. The strict issue-to-occurrence API is absent on base. The duplicate-occurrence expectation also fails against the old `(scope, check ID)` key, which does not encode per-issue occurrence identity. The remaining errors identify strict APIs absent from base. |

The temporary base worktree was created from `ca76b49b00390c95006ded2f63cb0561cc4f6502`; only the test module was copied into it. It contains no case narrative, dates, country pairing or identity data.
