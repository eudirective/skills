# Consultation quality candidate verification

## Current candidate verification — 2026-10-21

**Status:** Full dashboard and local structural/controller checks verified;
hosted consultation behavior not verified.
**Candidate code commit:** pending commit.
**Base:** `bf2fff23c31d70645327b7f20435e4647b617601` (`origin/main`)
**Branch:** `codex/full-dashboard-validation-20261021`
**Plugin/core:** `0.54.3` / `0.53.3`

The default compact renderer and its limits are removed. The full board lists
every recorded classification, operation, C27 check, issue, validator result,
source-ledger row, and module-use record. The route gate produces the board
after validation and binds a validation record to the exact receipt digest;
the local answer controller binds that record together with the exact receipt
and answer bytes. A material continuation change can require a refreshed board.
No ChatGPT host release hook is available, so hosted output is not
non-bypassably controlled.

Checks run against this candidate:

- Dashboard receipt/render and local release-binding tests: 47/47 passed.
- Route-gate tests: 16/16 passed.
- Issue-selection tests: 15/15 passed.
- Python compilation passed for the changed dashboard and route/release gates.
- Version-manifest verification and JSON parsing: passed.
- C27 registry checklist: 301 checks loaded; `git diff --check`: passed.
- Source-library manifests and source texts were not edited.
- Hosted ChatGPT tests were not run; the updated live test plan remains the
  post-install acceptance procedure. No claim of host-enforced release gating
  is made.

Remote CI/PR results are not yet available for this candidate.

## Previous candidate record — superseded

**Status:** Implementation verified; consultation behavior not verified.
**Candidate code commit:** `f7ca9f9a66f43dfbc2ea9873bad72f45d3996c16` on `codex/freemovement-consultation-quality`.
**Base:** `343a7464d5574d3c2957f1817dedcf70da6135ce`.
**Date:** 2026-10-21 (documentation follow-up; code candidate unchanged).

## Story status

| Story | Status | Evidence and remaining boundary |
|---|---|---|
| US-001 baseline reconciliation | Completed locally | Baseline commit, versions, CI inventory and failures are recorded in `baseline.md`. The current public workflow runs tracked public structural checks; regression prompts and scripts remain private. |
| US-002 behavioral baseline | Not executed | The private ledger has 36 `not_executed` records and no transcripts or grades. |
| US-003–005 issue model, routing, selector | Implemented and structurally checked | Issue model and source-referenced signal matrix reuse C27 IDs. The selector accepts synthetic/abstract IDs only; its 15 tests pass. This does not test model issue extraction. |
| US-006–009 consultation workflow, source accounting, answer contract and presentation | Implemented; behavior unverified | The five model-led stages, per-issue dispositions, concise default answer, and full default dashboard are documented. Dashboard/coverage fixtures pass; no live output was reviewed. |
| US-010 route receipt gate | Implemented and structurally checked | Legacy receipt compatibility, missing routed checks/gaps, receipt fingerprinting, and local answer binding are tested. The gate checks declared data and is not called by the ChatGPT host. |
| US-011 adversarial scenarios | Available in private maintenance suite | The synthetic suite checks 24 cross-suite cases and 12 topic challenges with positive/negative contrasts and required/forbidden claims. These are regression cases, not held-out cases; no model response was evaluated. |
| US-012 actual-response aggregation | Implemented and structurally checked | The private aggregator's 8 tests pass. It preserves independent claim disagreements and reports metrics unavailable when responses/grades are absent. |
| US-013 fresh-context behavior comparison | Deferred; plan prepared | No supported runner for fresh target-plugin conversations or independent grading was available. There are no baseline/candidate scores. A concrete run plan is stored in private `fm-maintenance`; the live run is a separate follow-up, not a prerequisite for ending this implementation session. |
| US-014 integration and release preparation | Partial | Manifest, compilation, C27 checklist and targeted tests pass. The private all-suites run is 31/36 locally. No remote CI or pull request was run; the commits were left local as requested. |

## Executed checks

- `node freemovement-law/scripts/version_manifest.mjs --verify` — passed.
- `python3 -m compileall -q freemovement-law/skills/eudirective-core/scripts` — passed.
- `python3 freemovement-law/skills/eudirective-core/scripts/c27_case_state.py checklist` — passed.
- `python3 freemovement-law/skills/eudirective-core/scripts/test_consultation_issue_selection.py` — 15/15 passed.
- `python3 freemovement-law/skills/eudirective-core/scripts/test_consultation_route_gate.py` — 16/16 passed.
- Private evaluation aggregator tests — 8/8 passed.
- `git diff --check` — passed for the local changes in both repositories.
- Private consultation-assurance case checks — 5/5 passed; dashboard format checks — 6/6 passed. C23/C24/C25/C27 and both country sidecar suites passed in the all-suites run.
- Private all-suites regression runner — 31/36 scripts exited successfully. Five local failures:
  - nested Node version-manifest test: `spawnSync /usr/bin/node EPERM` (direct version verification passed);
  - C13 document evidence, C16 coverage, and C17 applicant drafts: local PyMuPDF (`fitz`) dependency unavailable;
  - C17 remedies: required Sweden module notes are absent from the selected plugin package.
- The local runner output and aggregator status report are in the private repository under `plugins/fm-maintenance/records/FM-ASSURANCE-2026-10-20/evidence/`, named `candidate-all-regressions-f7ca9f9-2026-10-20.log` and `candidate-assurance-status-f7ca9f9-2026-10-20.json`.

## Behavioral and release limits

The current private ledger contains 36 records, all `not_executed`; model metadata, transcript evidence, independent grades, precision/recall, critical-error counts and before/after comparisons are unavailable. No held-out evaluation was executed. The private live-test plan records exact baseline/candidate builds, the 36-case run, fresh-chat controls, blind grading, evidence capture, and release thresholds. The plan closes the implementation-session deliverable only; it does not establish measured improvement. Do not describe deterministic routing or structural test results as measured advice improvement.

The plugin still has no host-validated pre-output release gate. The optional receipt checker cannot discover omitted issues or authenticate model-declared analysis. The Sweden source-package gap and any other national-source limitations remain scoped gaps; no country-source package was changed or promoted.

The tested implementation commit and current documentation-only follow-up remain on local branches. No PR, push, merge or remote CI run was performed.
