# C11a/b — Value-sensitive legal assessment in the synthetic C6 chain

**Version:** 0.1.0 (core release v0.24.0, 2026-10-10). **Scope:** exact, C7-approved fictional fixtures only. The C3 country-module contract remains 0.2.0, and C2 elements remain 0.2.0. Neither source-note integrity nor successful mechanical replay establishes a legal result.

## Execution and inputs

1. Complete C5a/C5b/C5c/C5d analysis with exact case/element/source/module hashes.
2. Reuse **only** code-root-pinned `references/legal-assessment/c11-rule-profiles.json`. Validate predicate field names against the closed C2 element catalogue and a small case-field allowlist; do not evaluate expressions or parse narrative facts.
3. Compute the C11 stage via `scripts/legal_assessment.py`, bound to the case, elements, C5d, source pack, country-module manifest/export digests, and profile digest.
4. Include `stages/c11.json` in the C6 run manifest; keep the controlled projection `cannot_assess` even when an angle has all explicitly modelled predicate values. Report C11 predicate output in `c11-legal-assessment.json` and `c11-legal-assessment.md`.
5. Preserve every C11 unresolved field and limitation in the complete C7 issue index. Verify exact stage replay and both C11 report hashes in release verification.
6. Do not send a C5d angle to the controlled candidate view or a reviewer-approved C5e handoff unless its C11 predicate record is `supported_for_review`. Other source-backed candidate angles remain in the lossless issue index and C11 output.

## Result semantics

- `supported_for_review`: all encoded structured prerequisites match, and the upstream candidate is not blocked. **Not** evidence of a legal violation; questions about contrary evidence and exceptions remain open.
- `contradicted`: a recorded structured value contradicts the profile's expected signal. This contradicts the *review predicate*, not the wider legal issue or the applicant's legal position.
- `unresolved`: material facts, precise evidence, source module or review predicates are missing, or C5d's upstream record is blocked. In particular, narrative claims about appeal receipt or Deldwyn third-party evidence do not substitute for typed case-bound data.
- `not_applicable`: the profile is outside the case's procedure type. This makes **no** general finding about the case or the law.

The `legal_violation_status` and the final `conclusion` are always `not_determined`. New source citations are **pinpoint review hints**, not quotations; core metadata is not the absent 0.5.0 archive, and national module sources are notes rather than full enacted text.

## Specific legal distinctions and known gaps

- Article 5(2) entry visas versus Article 10 residence cards: procedure typing is a starting point, not entitlement or proof that one document is demanded as a prerequisite for the other.
- Swedish consular direct channels versus VFS: a reported refusal can support review; choosing VFS voluntarily does not indicate denial or illegal charging. No fee allegation without fee-demand data.
- Deldwyn C-477/24 paragraphs 53-70: a former spouse's decisive information, prior request, inability to obtain it, authority reliance and confidentiality/redaction balancing require **separate typed facts**; `evidence.status=disputed` alone is insufficient. Charter Article 41 is directed to EU institutions; Member-State good-administration obligations must be evaluated via general principles and the appropriate law.
- Swedish visa appeals: published three-week guidance is not a case-bound expiry date without proven notice/receipt and actual filing event. Never derive precise deadline from a narrative sentence.
- Swedish JO supervision and Turkish e-Devlet records: supervisor is not appeal authority, Turkish domestic validity does not dictate Swedish evidentiary sufficiency.

## Reproducible checks

Run from the core skill root:

```bash
python scripts/test_c11_legal_assessment.py
python scripts/run_selftest.py
python scripts/test_c7_metadata_freshness.py
```

For exact end-to-end checks use the existing `scripts/c6_integration.py prepare`, `release`, `verify` command sequence with only code-enrolled fiction and the authorized C10 SE/Türkiye module fixture exports. The generated `c11-legal-assessment.{json,md}` and complete C7 issue-index companions must survive tamper/replay checks.

## What this does not establish

No independent legal merits validation or completeness, no full EU source-pack v0.6.0, no full current Swedish statute reproduction, no authenticated case reviewer, no safe host/private-case input, no external complaint or visa action. The fixed profile is a bounded prototype; expand it only through reviewed sources, case facts and new regression counterexamples, not country-specific hardcoding in the reusable core.
