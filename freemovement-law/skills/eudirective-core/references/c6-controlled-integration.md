# C6 controlled synthetic integration (v0.2.1; C7.1 hardening)

**Current C18 source-gate override (2026-10-10):** New controlled synthetic cases must use the trusted active C1 0.6.1 manifest and an as-of timestamp no earlier than the targeted 2026-10-10 source verification. C6 now checks local source representation hashes through C7; this is not full official-source verification, legal-merits adjudication, or confirmation that 21 identity-only source notes contain the legal texts. The C7-era 0.5.0 rule described below is retained only as a historical note; it no longer authorizes new cases. See `references/c18-source-integrity.md`.

**Current v0.21.1 override:** before using any older examples in this document, read `references/c7-hardening.md`. The C6 prepared-run index is now 0.2.1 and accepts only code-pinned approved fictional fixture JSON and the pinned source 0.5.0 metadata release. An explicit full `issue-index.json` + `issue-index.md` companion is mandatory for reported completeness. The default runtime does not inspect EU source text bytes; never claim independent official-source authenticity/currentness verification. Interrupted releases are non-retryable in the old workspace.

C6 connects the existing C3/0.2.0 country-module boundary, original controller protocol 0.3.0, C5a–C5d candidate chain, explicit C5e handoff and C5f review to a **limited** controller-validated legal-analysis projection. It is an integration/development workflow, not verified legal advice. It does not enable real/private cases or outbound actions.

## Inputs and controller ownership

`scripts/c6_integration.py prepare` accepts a code-pinned fictional `case-input`, an `element-instance-bundle`, optional actor/C5b/C5c context, a C1 EU/common source-pack manifest and one or more `<manifest> <export>` country pairs. The C1 pack is adapted through `core_source_adapter.py`; the controller, not the integration script's unchecked claims, owns case intake, module registration, freeze, requirements, revision-checked proposal, validation and release. Both country families are data-only. Role-sensitive matching, destination profiles, freshness and duplicate-ID controls use the existing frozen C3 controller. C6 neither adds national rules nor modifies the contract.

`prepare` rejects any run ID other than the three code-enrolled synthetic fixture labels and any time other than canonical UTC second-resolution ISO 8601; source verification dates are aged against this time before workspace creation. The source-as-of record is replay-bound in the C6 0.2.1 manifest. Pinned metadata age is not live re-verification.

`prepare` snapshots structured inputs into a **new** work directory, validates contracts, builds exactly C5a topology/regimes → C5b → C5c → C5d, and stores all outputs in `stages/`. A typed `c6-run-manifest.json` pins case/run identity, prepared controller revision/state digest, source/element/country inputs, C5 stage output digests and hashes of relevant scripts/contracts/catalogues. `verify` checks each snapshot digest and exact deterministic stage replay. This prevents unchanged-looking, locally edited outputs from silently preserving their old release. A new input, changed policy/engine, or source correction must start a **new run**; do not patch a released work directory.

## Example synthetic workflow

Run from the unpacked skill root:

```bash
python scripts/c6_integration.py prepare \
  --workdir /tmp/c6-demo --run-id RUN-C6-1 \
  --time-of-check 2026-10-10T11:00:00Z \
  --case references/fixtures/c5a/case-frontier.json \
  --elements references/fixtures/c5d/elements-signals.json \
  --actors references/fixtures/c5a/actors-family-member.json \
  --c5c-context references/fixtures/c5c/context-ready.json \
  --module-pair references/fixtures/member-state-se-manifest.json references/fixtures/c5c/member-state-se-c5c-export.json \
  --module-pair references/fixtures/member-state-de-manifest.json references/fixtures/member-state-de-export.json \
  --module-pair references/fixtures/c6/applicant-country-tr-manifest.json references/fixtures/c6/applicant-country-tr-export.json
python scripts/c6_integration.py release --workdir /tmp/c6-demo
python scripts/c6_integration.py verify --workdir /tmp/c6-demo
```

The synthetic case deliberately retains distinct Sweden/residence, Germany/work and Türkiye/application roles; it does **not** establish the legal merits of any real case. A missing required country role blocks `prepare`; an absent optional module is explicitly scoped in completeness. A required module with insufficient freshness remains blocked for full release and may appear only in a properly qualified limited output.

## Explicit reviewer path

For an independently supplied, structurally valid, case/digest-matched review record and the C5e/C5f context snapshots:

```bash
python scripts/c6_integration.py release --workdir /tmp/c6-reviewed \
  --review /path/to/c5d-review.json \
  --c5e-context /path/to/c5e-context.json \
  --c5f-context /path/to/c5f-context.json
python scripts/c6_integration.py verify --workdir /tmp/c6-reviewed
```

Provide **all three**, or none. C6 does not author an affirmative reviewer decision, and calls the actual `analysis_handoff`, `suggestion_engine`, and `suggestion_ranking` implementations. The C5e gate requires promoted evidence and the C5f gate covers all candidate options and five neutral baselines, including direct compliance, cooperation, clarification, waiting and no action. A reviewer identity string is **not authenticated locally**. Altering the exact review/context/proposal/baseline digests invalidates its review-only output. C5f labels, including `single_preferred_for_review`, never authorize action or change legal conclusions.

## Output semantics and limitations

- `analysis.json` is a schema-checked **controlled projection**. C5d hypotheses are `cannot_assess` rather than established violations; mechanically computed dates are marked candidate-only. No suggestion is inserted into the controlled analysis. The meritorious-law requirement stays `not_checked`, so the controller can issue only a **limited** release.
- `controlled-analysis.md` is rendered *only by* `case_controller.render_markdown` from the exact validated analysis, not by appending unvalidated model prose. `validation-receipt.json`, `release-receipt.json` and `state.json` retain the original controller's authoritative transitions.
- `strategy-review-only.md` is a **separate** deterministic view: review-needed when C5e/C5f reviewer input is absent; otherwise it displays the reviewed candidates, five baseline comparisons, tradeoffs, deferred and excluded alternatives and conditional sequences, and explicitly denies execution authorization. `c6-release-receipt.json` binds the exact analysis, controller release digest, strategy bytes and reviewer snapshots.
- `c6-run-manifest.json` and each receipt are **content integrity evidence**, not signatures or evidence of actual reviewer identity, source correctness, host privacy, legal correctness, or independent semantic/legal review.
- C1 notes of verified document identity/version are not verifiable exact quotations. Unknown national-law conditions, unresolved lex-specialis, scope questions and missing facts remain limitations. Recorded source freshness must also satisfy the code-pinned **as-of** window at the synthetic run timestamp; it cannot be carried forward indefinitely, and passing the age window is not a live verification of law.
- Private or public real-person intake, host-enforced secure deletion, external network delivery and action execution are disabled in this C6 driver. Use only fictional/synthetic case data.

## Verification and adversarial requirements

Run `python scripts/run_selftest.py` for the 156 legacy C1–C5f checks, `python scripts/test_c6_integration.py` for C6 CLI integration, and `python scripts/test_c7_hardening.py` for C7 adversarial source/input/report/fault tests, and `python scripts/test_c7_metadata_freshness.py` for the 2099 timestamp, metadata-injection and source-age tests. Verify both suites *after* any executable changes. C6 tests check multi-role composition, exact controller stages, limited/full gating, reviewed and unreviewed strategy, immutable analysis independence, stale review/hash/markdown/controller tampering, optional/required modules, staleness, wrong destination profiles, incompatibility and disabled private mode. The existing C5 suites separately test falsification, disclosure, inaction/deadline waiver, module review prerequisites and cycle/conflict controls; deterministic pass ≠ legal-semantic certification.

The next milestone, **C7**, is independent, cross-environment hardening and real-prompt/host enforcement review, not a claim that C6 is a production legal-assistance service.
