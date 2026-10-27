# C12 — Synthetic country-owned rule resolution pilot

**Status:** v0.1.0 engine in `eudirective-core` v0.25.0, 10 October 2026. This is an inspectable research/development workflow, **not legal advice or an authenticated case file**.

## Modules and boundaries

- EU predicates: `references/legal-assessment/c12-eu-rules.json`; source IDs must belong to EU catalogue. No Swedish or Turkish legal conditions belong here.
- Swedish national predicates: resolve the `member_state` module registered for `SE` in `references/national-source-routing.json`; the module package and exact skill path are stated in that registry.
- Turkish application-context predicates: `eudirective-ac-turkiye/references/c12-rule-extension.json`. This module does not exercise Turkish authority over a Swedish visa decision.
- The extension binds `producer_module_id`, family, jurisdiction and exact canonical SHA-256 of the corresponding unchanged C3 `module-export.json`. Cross-owner source citations are rejected.
- To keep C7's approved-fiction-only intake, distribute exact extension snapshots under `references/fixtures/c12/` as **test enrollment copies**. The primary source-of-authoring is each country skill, not the core. Both source files must be byte-identical JSON objects at release.
- A synthetic ledger references in-package structured surrogate documents with pinned file hashes. `synthetic:*` is never proof of authenticity. Fact values must match actual document assertions and element `source_ref` where applicable; missing/mismatched references leave the fact unverified.

## C12 processing stages

1. Preflight in C6: read and schema-check C12 extensions and ledger; require C7 hash-allowlisted exact fixture content **before writing a workspace**.
2. Snapshot the fixture inputs, frozen C3 exports, source pack and case. Bind the C12 stage to the corresponding C5d, case, element, catalogue, ledger and extension hashes.
3. Evaluate typed `case:`, `element:`, `fact:` prerequisites. `one_of` uses strict scalar type + value matching; `date` enforces ISO calendar dates without inferring the applicable legal appeal period.
4. A legal issue can be `supported_for_review`, `contradicted`, `unresolved` or `not_applicable` **as a factual review predicate**. Every actual violation remains `not_determined`. Exception questions are presented for human/legal review and never silently treated as false.
5. All unmatched C5d issue candidates appear in `c12-legal-resolution.md` under **Novel / unprofiled issues** and in the complete C7 index. They are not automatically promoted to infringements.
6. `release` replays C12 with pinned inputs; `verify` rechecks stage JSON, Markdown and digest-bound receipts. No outbound actions, unrestricted intake or private cases.

## Exact fictional reproduction

From skill root (choose `N` in `1`, `4`, `5`):

```bash
python scripts/test_c12_rule_resolution.py
python scripts/test_c11_legal_assessment.py
```

To exercise the full C6 chain use `scripts/c6_integration.py prepare` with `--case references/fixtures/c10/LN/case.json`, `--elements .../LN/elements.json`, `--actors .../LN/actors.json`, `--module-pair references/fixtures/c10/sweden-module-manifest.json references/fixtures/c10/sweden-module-export.json`, `--c12-rule-extension references/fixtures/c12/sweden-rule-extension.json`, and `--c12-fact-ledger references/fixtures/c12/LN-fact-ledger.json`. L1/L4 also require the Türkiye C3 pair and `--c12-rule-extension references/fixtures/c12/turkiye-rule-extension.json`. Include `--c5c-context` only if LN provides it, `--run-id RUN-C10-LN`, `--time-of-check 2026-10-09T20:00:00Z`, and a new `--workdir` each run. Then use `release --workdir` and `verify --workdir`. The source default is 0.6.0 metadata, not a complete source byte pack.

## Scope and limitations

L1 tests consular channel and access, L4 records two event dates but does not compute an authoritative legal deadline, and L5 tests a narrow *Deldwyn* former-spouse information scenario with an explicit confidentiality-review field. The synthetic case documents are constructed typed surrogates, not scanned official correspondence, and their hashes do not prove factual truth. Some questions concerning balancing, source currentness, legal exceptions, and actual appeal periods remain for independently sourced review. All other five C10 scenarios remain earlier-stage limited hypotheses; no legal-merits pass is claimed.
