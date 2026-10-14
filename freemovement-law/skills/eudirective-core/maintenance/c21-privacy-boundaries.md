# C21 modifier-only release boundary and unresolved implementation risks

This file is for maintainers modifying the skill, not for normal use.

## Invariants

- Keep `data_class=private` and `data_class=public` blocked even when a user marks a fixture synthetic by mistake. A self-declared synthetic flag is never proof of fiction; host policy remains essential.
- Preserve `external_disclosure_authorized=false`, `human_review_required=true`, `private_data_enabled=false` in all C21 output contracts, **including** the C17-derived preview.
- Keep purpose profiles allowlisted and SHA-pinned, and keep enrolled synthetic source fixtures/fictional C17 plans under a second independently code-pinned SHA registry; changes to the registry alone must fail. Any new fixture requires deliberate modifier review and re-running C21 plus post-extraction tests. A digest/`synthetic` label cannot prove the content was invented.
- A policy-only rewrite must fail. Never let a caller request arbitrary `keep` transformations or raise linkability thresholds.
- Never persist reversible name/person mappings, original-case identifiers, raw-source digests or stable cross-case pseudonyms in an output receipt.
- Keep input and source code strictly Python-handled and offline in this preview lane. An LLM/connector/browser may not process raw actual applicant materials under these constraints.
- Treat pattern catches as known-format redactions, not general detection of identifying information. An unknown name or distinctive story may pass the recognizers and remain in an *unreleasable* preview.
- All national law remains in the Member-State/applicant-country modules; avoid introducing national privacy law in core.

## Future external-use verification requirements

1. Demonstrate host-enforced raw data isolation before any private actual intake or human/model review.
2. Define controller identity, processing purposes, legal basis, retention, security, rights/contact process, transfers/processor agreements, audit/deletion arrangements; prepare reviewed privacy notice and terms for the actual service. A user uninstall is **not** proof that server copies were erased or consent rescinded at every controller.
3. Model output recipients, categories of data, necessity and consent/other lawful basis separately. Block each external route until a verified non-bypassable output gate exists. C4 local controller cannot enforce host network permissions.
4. Add cross-case and *external public-search* re-identification red-team tests, including rare fact mosaics, background knowledge, quote search, bilingual entities, and differencing or unique statistic linkage. No universal anonymity promise even then.
5. Build aggregate-only telemetry with cohort-size/small-cell suppression, stable bounded issue taxonomy, contribution limits and differencing defence. The current feedback preview is a **single input** and must not be sent.
6. Test failure atomicity, encrypted/restorable protected state where necessary, limited logging, media/PDF metadata, OCR redaction, backups, adversarial prompts and user revocation semantics. Never treat platform tool availability as a security boundary without direct evidence.
7. Conduct a DPIA and legal review where applicable; GDPR compliance cannot be determined by pattern rules and JSON Schemas.

## Known edge cases

- Even an enrolled, self-declared synthetic fixture may actually contain personal data; the registry identifies reviewed local fixtures, not human reality.
- Narrative content can reveal a person without any direct string that matches a recognizer.
- Policy hash pin binds the local bundled bytes, not producer identity or trusted execution. An editor can alter both the code and pin.
- The optional C17 plan adapter performs a structural check and coarse projection; it does not reproduce C7 source-trust or C6 replay proofs independently. C6/C7/C17 remain responsible for those guarantees.
- Unix file modes are only a local defence; host storage, external attachments, cloud caching and Windows ACLs are outside C21 verification.

## Testing

Run `python scripts/test_c21_privacy.py`, then C6/C7/C16/C17/C18/core self-tests after changes. Run tests from a fresh extracted release too. Passing tests are **mechanical only**, not independent privacy or legal expert validation.


## C21 synthetic hardening invariant (Core 0.34.0)

For public-story rehearsals, a dropped field's high-linkability tag must suppress retained narrative even when the narrative itself carries no risk tag. Neither category-only story previews nor synthetic eight-case aggregated remedy counts are externally releasable. The fixed cohort is all L1-L8 together; permitting arbitrary subsets, overlapping cohort releases, per-case labels, or rows would invalidate the suppression argument. Maintain all eight enrolled plan fixtures and preserve the C7/C17 gate against modified inputs. Treat independent reviewer-authenticated lineage as a future protected-channel requirement, not as established by these fixtures.
