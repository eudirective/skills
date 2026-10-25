# eudirective-core simplification report

## Source and candidate

- Repository: `eudirective/skills`
- Baseline commit: `ff28f54a8e0dc2d951106e22600ba027230f51aa`
- Baseline plugin/core versions: `freemovement-law 0.59.3` / `eudirective-core 0.58.3`
- Baseline core file: 563 lines, 81,544 characters, 81,662 UTF-8 bytes; SHA-256 `182042c8bc0558514406365c0afafb605bb30d8a91928709dcb85e828b766ad7`
- Candidate versions: `freemovement-law 0.59.4` / `eudirective-core 0.58.4`
- Candidate core file: 137 lines, 26,788 characters, 26,811 UTF-8 bytes; SHA-256 `b24efb8f6a26022e1926236dc7fcd78843c36e993a7b148e312adb626dce3a78`
- Size reduction: 67.2% by UTF-8 bytes (67.1% by characters), within the requested 60–75% range.
- The exact candidate plugin fingerprint is recorded in the private fm-maintenance regression artifact.

## Preservation record

`core-simplification-requirement-map.json` maps every original section and activation description to its category, activation condition, disposition, and current destination. Its 51 entries cover all 563 source lines without gaps or overlaps. The private structural regression checks that map coverage and all public destinations remain valid.

The normal-use entry point retains the skill's purpose and activation limits; the exact first-response disclaimer and licensing distinction; one-time package-version checking and visible version disclosure; applicant consultation routing; C23/C24/C25 activation; C27 reconciliation; the mandatory full consultation dashboard, its triggers, metrics, provenance, module and execution rows, and missing-item effects; source-owner/currentness rules; evidence-gated research; legal reasoning and completeness limits; jurisdiction/module boundaries; synthetic-only execution boundaries; and maintenance/evaluation separation.

The full dashboard remains mandatory after each explicit invocation. The ordinary consultation path still requires issue discovery before C27 check selection, keeps Visa Code Articles 18, 19 and 32 routes separate, and uses a separate model-led attack-angle screen. The refactor changes neither C27 IDs nor route triggers, dashboard data/schema definitions, C3 contracts, country ownership, or engine semantics.

## Consolidation and relocation

- Removed repeated consultation, privacy, source-integrity, dashboard, capability, and legal-correctness caveats from the entry point after consolidating them into the applicable operational rule.
- Replaced the exhaustive script/resource inventory with a conditional dispatch table that names the existing authoritative references. It states that links do not automatically load references and identifies when each reference must be read.
- Moved stage commands, schemas, fixture restrictions, and detailed C1–C22 procedures to the existing source, element, contract, controller, C5–C8, C10–C17, C21, and C22 references and modifier-only maintenance records. Real applicant facts remain outside synthetic scripts.
- Consolidated C26 follow-up and authority-ground attribution duties with the existing C25 applicant-strategy and evidence-acquisition references.
- Preserved the removed v0.58.3 purpose/status, implementation-boundary, risk, and assumptions sections as an explicitly historical snapshot in `maintenance/design-rationale.md`. They are labeled as claims recorded at the baseline commit, not current implementation status.
- Removed the duplicate resource inventory rather than copying it elsewhere. The resources and their paths remain in the package and are reachable from the dispatch table or the requirement map.
- No legal-rule, source-library, country-module, JSON contract/schema, or release-enforcement semantics were changed. The change is an entry-point and documentation organization refactor; detailed workflow instructions now load only when the corresponding issue or maintenance task is active.

## Reference loading and runtime implications

The plugin does not automatically load linked references. The new entry point distinguishes references required for every substantive applicant matter from those activated by a specific legal issue, synthetic workflow, or package-maintenance request. Optional references are not treated as read merely because they are linked. Modifier-only `maintenance/` material remains excluded from normal legal consultations.

The local dashboard receipt remains optional to the current local Codex environment, privacy-minimized, and structural only. The skill still cannot authenticate retrieval, validate legal reasoning, isolate host data, guarantee graphical rendering, or enforce answer release. No live installed-plugin/model behavior was tested, and no manual test plan, user assignment, or recurring blocker was created.

## Verification

Baseline evidence from the exact baseline commit: the private `fm-maintenance 0.6.2` full runner passed 42/42 scripts. The candidate full runner used the exact local candidate directory and recorded its content fingerprint.

Commands run against the candidate:

1. `/tmp/fm-maintenance-venv/bin/python plugins/fm-maintenance/scripts/run_regressions.py --plugin-root /home/player/src/eudirective-skills/freemovement-law --suite core --json-report /tmp/fm-core-simplification-core-20261025.json` — **41/41 passed**.
2. `/tmp/fm-maintenance-venv/bin/python plugins/fm-maintenance/scripts/run_regressions.py --plugin-root /home/player/src/eudirective-skills/freemovement-law --suite all --json-report /tmp/fm-core-simplification-all-20261025.json` — **43/43 passed**, 0 failed, 0 unavailable (41 core, 1 Sweden, 1 Türkiye).
3. `/tmp/fm-maintenance-venv/bin/python -m unittest discover -s plugins/fm-maintenance/scripts -p 'test_*.py' -v` — **20/20 passed**.
4. `node freemovement-law/scripts/version_manifest.mjs --verify` — **passed**.
5. Structural migration-map/reference check — **51 entries, all 563 original lines covered, public destinations and referenced files resolved**.

The private maintenance package is now `fm-maintenance 0.6.3`; it contains the persistent core-simplification regression in the existing regression payload. The package's test report and logs remain local in `/tmp` and are execution evidence only. No GitHub Actions, network tests, live model tests, install, or release were used.

## Scope checks and remaining limits

The version manifest retains the existing public-data source-library and module-note fingerprints, source-library pack version, and country skill versions. No files under `sources/` or country-module contents were changed. The full automated suite passing demonstrates only the mechanical checks it ran; legal correctness, natural-language issue discovery, dashboard rendering in ChatGPT, and live model behavior remain unverified as before.
