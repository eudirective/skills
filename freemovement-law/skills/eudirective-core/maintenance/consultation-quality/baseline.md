# Consultation quality recovery baseline

- Baseline date: 2026-10-20
- Repository: `eudirective/skills`
- Branch: `codex/freemovement-consultation-quality`
- Baseline commit: `343a7464d5574d3c2957f1817dedcf70da6135ce`
- Working tree at branch creation: clean
- Installed versions at baseline: plugin `0.52.2`; core `0.51.1`

The plan's assumed commit and versions were stale. The branch was based on the then-current local `main` after it had been advanced to the live `main` commit available in the checkout. The core and plugin version manifest verified before edits.

## Public CI inventory

The public workflow is `.github/workflows/verify-freemovement-versions.yml`. Its version-manifest command passed (exit 0), and the C27 `checklist` command passed (exit 0). The workflow's other references do not exist in this public checkout:

- Python regression files: `test_c27_case_state.py`, `test_consultation_route_gate.py`, `test_issue_source_preflight.py`, `test_attack_angle_coverage.py`, `test_consultation_topic_review.py`, `test_consultation_assurance_cases.py`, `test_consultation_dashboard_format.py`, `test_evaluation_transcript_gate.py`, `test_c6_integration.py`, `test_c7_hardening.py`, and `test_c7_metadata_freshness.py`.
- The transcript-gate script and `evaluations/consultation-assurance-evaluations.json`.
- The C27 `initial.json` and `multi-proceeding.json` fixtures.
- Node tests `test_session_version_check.mjs` and `test_version_manifest.mjs`.

Each missing Python file or C27 fixture invocation failed locally with a file-not-found exit (2); the missing Node test invocations exited 1. The workflow therefore cannot pass as written in the public repository. The missing suite assets are present in the private `eudirective/internal` `fm-maintenance` checkout, which provides a manually triggered regression workflow and overlays those synthetic assets into a temporary copy of the selected public plugin. Hidden evaluation records remain private.

The GitHub API was unavailable during this baseline check, so no live Actions run was queried. A previously observed run `39438185723` failed on a missing public test path; that result was not re-fetched in this run.

## Private core regression baseline

Command:

```text
python3 plugins/fm-maintenance/scripts/run_regressions.py --plugin-root /tmp/skills-clean/freemovement-law --suite core
```

The private runner copied the public plugin to a temporary directory and overlaid the private regression assets there; it did not edit the public checkout. **26 of 33 scripts exited successfully.** Seven scripts failed:

- `test_version_manifest.mjs`: Node could not spawn its child process in this environment (`EPERM`).
- `test_c13_document_evidence.py`, `test_c16_coverage.py`, and `test_c17_applicant_drafts.py`: the optional `fitz`/PyMuPDF dependency is not installed.
- `test_c17_remedies.py`: the selected public package lacks Sweden module notes expected by the private fixture set.
- `test_c21_source_index.py`: a private assertion expects wording from an older core-source-pack compatibility contract.
- `test_issue_source_preflight.py`: two assertions expect the established `source_candidate_unaccepted` reason. The current validator emitted `candidate_source_not_accepted` for the same still-open candidate, so the tests exposed a reason-code compatibility regression. The candidate remained unaccepted and the required national source class remained open. The implementation will restore the expected reason code.

These are baseline failures, not candidate regressions. One source-accounting reason-code failure is being corrected; the remaining environment and contract-fixture failures are tracked separately. The local suite is useful evidence but does not replace the remote private workflow or legal-semantic review.

## Behavioral baseline

The private consultation-assurance ledger contains 36 records; all 36 are `not_executed`. No actual baseline model response, model version, independent grade, or behavioral metric was available. See `behavioral-baseline.md` and `input-completeness.md`. Implementation and deterministic tests must not be described as measured consultation improvement.

## Structural findings

- Ordinary consultations have a detailed model-led routing contract, C27 registry, route receipt gate, research validator, source preflight and dashboard instructions.
- The default output instructions require a technical dashboard before substantive guidance and enumerate many fields even for focused questions. This risks making the report dominate the legal answer.
- There is no explicit reusable issue record connecting a reported event to its proceeding, applicable checks, evidence/source owner, disposition and answer.
- There is no deterministic synthetic selector that checks issue signals against the C27 registry without ingesting real narratives.
- The declared route gate already validates C27 references, operation evidence, unresolved work and comprehensive-coverage claims, but it cannot compare declared issues and dispositions with signal-selected checks.
- The skill correctly states that it is model-led and that the host does not validate the route before answer release.
