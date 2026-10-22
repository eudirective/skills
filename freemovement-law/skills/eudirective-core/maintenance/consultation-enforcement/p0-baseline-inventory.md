# P0 consultation enforcement baseline

**Date:** 2026-10-22
**Repository:** `eudirective/skills`
**Baseline commit:** `9041b01336b216034bf0e2301284e98d1b37aee3`
**Working branch:** `codex/p0-consultation-enforcement-20261022`
**Published:** no

## Version and compatibility boundary

- Plugin package: `freemovement-law` 0.56.1.
- Core skill: `eudirective-core` 0.55.1.
- Consultation route receipt: schema 0.3.0 (the validator also accepts 0.1.0 and 0.2.0).
- Issue source preflight: contract 0.2.0 (also accepts 0.1.0).
- Local release binding: schema 0.2.0.
- C2 element model: 0.2.0.
- Frozen C3 boundary: inter-skill contract 0.2.0, conformance profile 0.2.0, controller protocol 0.3.0, element model 0.2.0.

P0 changes must not modify the C2 element interfaces or the C3 producer/consumer contracts. New consultation control data belongs in separately versioned consultation contracts.

## Existing components and dependencies

| Component | Existing responsibility | Inputs and dependencies | Current boundary |
| --- | --- | --- | --- |
| `consultation_issue_selection.py` | Select C27 check IDs from registered abstract signal IDs; validate routing matrix references and synthetic fixtures. | `consultation-issue-routing.json`, C27 `check-registry.json`. | Selector accepts only synthetic abstract fixtures; route gate calls its signal-ID API on declared issue records. It does not extract issues from applicant narratives. |
| `consultation_route_gate.py` | Validate receipts; reconcile C27 records; validate declared issue signal-to-check coverage; run module, research and attached source-preflight validators; produce a deterministic dashboard and validation record. | Receipt schema, C27 state registry, C3 module validator, `research_gate.py`, `issue_source_preflight.py`, dashboard renderer. | Structural validation of declared records. Issue records are optional, and it cannot discover omitted issues or verify model-declared work. |
| `issue_source_preflight.py` | Compose issue-level source accounting with the existing research-plan/evidence-bundle validator. | Preflight schema, research schemas and gate, pinned source pack and supported module records. | Checks declared source/task structure and references; does not establish source authenticity, current law, legal sufficiency, or reviewer identity. No dedicated committed regression test file or reusable preflight fixture was found at baseline. |
| `generate_attack_angle_coverage.py` | Build a deterministic inventory of available C27 prompts, core C5d patterns, topic pathways, adapted strategy heuristics, and country-module records. | C27 registry, attack-angle and stratagem catalogues, topic pathways, pinned source pack, Sweden/Türkiye module exports and sidecars. | Catalogue inventory, not a per-consultation attack-screen result. Baseline generated 366 coverage records: 7 deterministic, 305 model-led, 50 synthetic-only, 4 not implemented. |
| `consultation_release_gate.py` | Locally bind receipt bytes, exact answer bytes, and route-validation digest; revalidate on release and output the answer only on success. | Route gate, receipt schema, release-binding schema, exact dashboard preview. | Opt-in local control for calls routed through the script. Binding is not signed or authenticated and does not intercept ChatGPT output or prevent bypass. |
| `consultation-assurance-host-adr.md` | State the difference between local integrity checks and host-controlled release. | Platform capability review. | Correctly says skills-only ChatGPT has no verified pre-output veto; existing ADR metadata is stale (scope says plugin 0.50.0/core 0.49.0). |

The dedicated gate already reuses C27's registry and validator, the C3 module-conformance validator, and the existing research validator. P0 should extend this composition instead of adding parallel registries or validators.

## Baseline checks

All checks below were run locally on the baseline commit. No applicant narrative or private case data was supplied to a synthetic-only script.

| Check | Result |
| --- | --- |
| `test_consultation_issue_selection.py` | Passed, 15 tests. |
| `test_consultation_route_gate.py` | Passed, 16 tests. Includes release-binding and comprehensive-claim rejection cases. |
| `test_consultation_dashboard.py` | Passed, 47 tests. |
| `run_selftest.py` | Passed, 156 checks, including frozen C2/C3 and synthetic C5d invariants. |
| `generate_attack_angle_coverage.py` | Generated successfully; 366 records with the capability counts above. |
| Source-preflight regression suite | None found. The preflight validator is imported by the route gate, but no dedicated test exercises a valid and invalid preflight artifact pair. This is a baseline test-coverage gap. |

No failures were observed in the suites that exist. A successful baseline says nothing about omitted issue discovery, legal correctness, whether model-led reviews occurred, or hosted release enforcement.

## Gaps this initiative must address

1. **Declared issue coverage is optional.** The schema permits receipts without `issues`, and the route gate preserves that legacy behavior. A controlled release can therefore omit its issue inventory and avoid issue-to-C27 reconciliation.
2. **Routing metadata is only partly consumed.** Issue selection derives required C27 checks, but the matrix's source-owner requirements and its required attack-review topics are not reconciled into per-issue receipt records.
3. **Preflight is not issue-derived.** The gate validates a source preflight only when a research artifact supplies one. It does not currently require owner-specific source obligations generated from every declared material issue.
4. **Attack coverage is inventory-level.** Applicant guidance has a required `attack_angle_screen` operation, but its evidence is not bound to each issue's triggered review topics, including a recorded negative or unresolved result.
5. **The local release path is opt-in.** It can withhold an exact local answer routed through the script; it is not a signed approval, host integration, or veto over ordinary ChatGPT output.
6. **Privacy controls are partly procedural.** Documentation warns that free-text receipt fields may contain identifying details, but the receipt gate does not scan those fields for personal data.

## Test and privacy constraints

- Keep real applicant facts in the conversation; do not pass dossiers to synthetic-only engines or test scripts.
- Keep P0 regression data abstract and non-identifying.
- Do not interpret a structurally closed receipt as legally comprehensive or correct.
- Hosted ChatGPT enforcement remains unverified unless a host-supported release veto is independently integrated and tested.
- No commits or remote publication are authorized by the P0 plan.
