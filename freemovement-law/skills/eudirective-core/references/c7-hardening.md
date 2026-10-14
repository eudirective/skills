> **Historical-note warning (restoration on 2026-10-10):** Statements below saying that 46 representation bytes are missing describe the superseded C8/C7 distribution. The v0.27.1 core and standalone v0.6.0 pack now contain all 47 locally verified representations. See the final restoration update and `references/source-pack/source-gap-register.md` for remaining content/currentness limits.

# C7 hardening — fixed-fixture integration boundary (v0.1.1)

C7 hardens the C6 synthetic-only integration path in `eudirective-core` v0.22.0. This is **local technical assurance**, not a production legal-analysis release. The C3 contract 0.2.0 and controller protocol 0.3.0 remain unchanged; C6 prepared-run index rises to 0.2.1 because its source-trust record is required.

## Source-trust boundary

`scripts/c7_trust_gate.py` checks a code-pinned SHA-256 of `references/trust/c7-trust-policy.json`, then checks the exact canonical digest of EU/common source-pack legacy manifest 0.5.0 (46 metadata hashes) or exact reviewed 0.6.0 manifest (47 metadata hashes) against that detached policy. A caller cannot mark an altered manifest `current` by supplying a different hash; malformed, stale-relabelled, added/removed-source or 64-zero-digest variants fail **before** the C6 case workspace is created. `verify` repeats this gate before exact stage replay. Changing the accepted C1 pack requires an explicit reviewed trust-policy/code-root release, not silently rewriting the source-pack JSON.

**Important assurance limit:** only the **new Deldwyn full-text Markdown bytes are included** in the v0.22.0 skill ZIP. The v0.6.0 gate verifies the new Deldwyn text against its code-pinned SHA-256 and the previous 46 representation declarations by metadata only; it does **not** establish the bytes of those 46 records, independent authenticity of retrieval, substantive legal correctness or live currentness. The optional `require_source_pack(pack, source_root)` Python function checks each provided sibling representation file byte-for-byte against its pinned digest; absent sibling bytes are never claimed checked. A bundled code-root plus trust policy is not an external signature, and cannot withstand an attacker allowed to replace both trusted code and policy. Distribution/host integrity must be established separately.

## Synthetic input provenance

For `scripts/c6_integration.py prepare`, exact-content allowlists (SHA-256 of canonical JSON) restrict the case, scoped elements, actor/context bundles and all country-module manifests/exports to specific **fictional bundled test fixtures**. For `release`, the three external review artifacts are similarly pinned; no review is generated automatically. Caller-supplied `privacy_classification=synthetic` is insufficient. `prepare` preflights and rejects non-enrolled inputs before creating a case workspace; `verify` independently rechecks the snapshots and frozen trust policy.

This guards the **C6 integration entrypoint**, not every general-purpose script or host connector. The fixture policy may be updated only through a reviewed skill release and is not a generic registration API. No real/private case, uncontrolled synthetic-looking text, arbitrary reviewer statement or external send is authorized. Run IDs, paths and alternate host output paths are not proof of private-data isolation. Preserve `private-data mode disabled` even when the local tests pass.

## C7.1 caller-controlled metadata and dated freshness

The C6 `prepare` CLI additionally enforces `c7_trust_gate.require_synthetic_run_metadata` **before creating any workspace**. The only accepted opaque labels are `RUN-C6-TEST`, `RUN-C6-1`, and `RUN-C7-DEMO`. No free-form run identifier can reach the controller or published issue index. The clock must be canonical UTC ISO 8601 with seconds (`YYYY-MM-DDTHH:MM:SSZ`); appended prose, impossible dates, missing zones and offsets are rejected. The generic controller independently parses its initialization time as a defensive backstop, but the C7 fixture gate applies specifically to C6. Path arguments select filesystem locations only and must not be misrepresented as a universal host privacy barrier.

The selected pinned core source pack (0.5.0 and 0.6.0 archival, or 0.6.1 active) is evaluated **as of the supplied synthetic run timestamp**. Every source must have a verified date not later than that date. `fixed_verified` judgments/other fixed instruments are checked for chronology/identity, **not** invalidated by arbitrary mutable-age thresholds. For the 11 mutable-current sources, the maximum locally permitted age of their recorded verification is **30 days** for consolidated legislation, **14 days** for Commission notices/handbooks/other guidance, and **7 days** for operational Commission/Ombudsman guidance pages. Unknown type/state combinations fail closed. A future year-2099 run therefore cannot retain the `live_current` success label by recycling an October 2026 verification date. The gate rejects it before case creation; an expired source pack requires a reviewed independent refresh and trust-root update, not a caller-supplied freshness string.

The `source_as_of` record is part of prepared-run manifest contract **0.2.1** and is checked anew during `release` and `verify`, against the controller's immutable prepared timestamp. These windows are **development-test conservatism**: they do not prove that official legislation/guidance remained unchanged for 7/14/30 days. Country modules lack equivalent verified-as-of dates in frozen contract 0.2.0; their categorical freshness remains unverified beyond fixture assertions. `source_freshness` support is limited to pinned metadata, not independent official-currentness assurance.

## Complete issue index and bound release

C7 does not shorten `unresolved[:12]`, `limitations[:10]` or missing controller reference IDs in the released presentation. It generates:

- `issue-index.json`: full stage-derived unresolved and limitation values plus unregistered candidate reference IDs; each item has source-stage SHA-256, JSON pointer and value SHA-256.
- `issue-index.md`: deterministic, untruncated human-readable version of the same index.
- `controlled-analysis.md`: bounded summary and **explicit companion filenames, per-category counts and the issue-index JSON digest**. Users must receive the companion files whenever presenting the controlled-analysis report as complete.

The C6 release receipt binds both issue-index JSON and rendered Markdown. `verify` independently recomputes the full index from the frozen, replayed stages; a removed, added or changed issue value or companion text blocks verification. No C5 issue becomes a legal conclusion because it appears in the index.

## Interrupted release handling

`release-attempt.json` is written **before** controller proposal, validation or release side effects. Failure leaves an incomplete, non-retryable work directory. No C7 success receipt is issued until every output is bound and `verify_release` passes. Starting a fresh workspace is the only supported recovery; do **not** overwrite/replay a partly released directory or trust controller `stage=released` on its own. Fault-injection tests cover interruption before proposal, validation and release.

## Verification commands and evidence

```bash
python scripts/run_selftest.py
python scripts/test_c6_integration.py
python scripts/test_c7_hardening.py --trace-output /tmp/c7-deterministic-traces.json
python scripts/test_c7_metadata_freshness.py --trace-output /tmp/c7-metadata-traces.json
python scripts/c6_integration.py prepare --workdir /tmp/c7-demo --run-id RUN-C7-DEMO \
  --time-of-check 2026-10-09T09:00:00Z \
  --case references/fixtures/c5a/case-frontier.json \
  --elements references/fixtures/c5d/elements-signals.json \
  --actors references/fixtures/c5a/actors-family-member.json \
  --c5c-context references/fixtures/c5c/context-ready.json \
  --module-pair references/fixtures/member-state-se-manifest.json references/fixtures/c5c/member-state-se-c5c-export.json \
  --module-pair references/fixtures/member-state-de-manifest.json references/fixtures/member-state-de-export.json \
  --module-pair references/fixtures/c6/applicant-country-tr-manifest.json references/fixtures/c6/applicant-country-tr-export.json
python scripts/c6_integration.py release --workdir /tmp/c7-demo
python scripts/c6_integration.py verify --workdir /tmp/c7-demo
```

These are deterministic test/replay results, not an outside legal expert's review or authenticated host isolation. Record and separately adjudicate sampled adverse legal evidence/contrary authorities before attempting applicant-facing use. Keep implicit invocation narrow.

## C8 source-catalogue transition

The default v0.22.0 C6 source pack is v0.6.0, which adds Deldwyn (C-477/24) as an identity-fixed CJEU judgment. The fixed-identity count is **35**, not 34, and the Markdown text is checked at C6 intake and verification. Historical 0.5.0 remains accepted solely for existing deterministic fixture replay. Complete local validation requires all 47 representation bytes, and this skill does not contain the 46 historical files. The legacy 0.5.0 source pack must be independently supplied, validated, and merged using the separate Deldwyn delta applicator; see `c8-deldwyn-integration.md`.


## 2026-10-10 source-pack restoration (v0.27.1)

The historical C8/C7 text above describes the **earlier** metadata-only v0.22.0–v0.27.0 state. The original 0.5.0 archive was subsequently recovered via the authorized Project Library copy and SHA-256-verified against every 0.5.0 representation. The verified Deldwyn delta was then applied. The v0.27.1 core now includes all 47 declared representation bytes, and C7 requires each bundled file to match its pinned size and SHA-256. This updates the physical distribution assurance only; source freshness and legal correctness remain unreviewed. The standalone sibling pack 0.6.0 is also complete.
