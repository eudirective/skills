# C18 — Active source identity, targeted correction and persistent gaps

The **active** EU/common source pack is `references/source-pack/core-source-pack-manifest-0.6.1.json`. It contains 46 logical sources represented by 47 local files. Run `scripts/verify_bundled_source_pack.py` for exact local bytes and `scripts/c18_source_integrity.py` for a source-by-source content-extent register. Both gates are deterministic and perform no network access. The C6 synthetic intake refuses older source manifests.

## Document restoration

The restored English consolidated Directive 2004/38/EC source formerly omitted Article 2(2)(a). The new locally pinned text contains the small definition `(a) the spouse;`, placed directly after point 2 (family-member definition) and before point (b). The official reference checked was EUR-Lex consolidated `02004L0038-20110616` (version 16 June 2011), with an additional check against the original official instrument. `references/source-pack/c18-directive-art2-restoration.json` records the exact original and corrected file hashes and lengths, dates, a limited check scope, and official URLs.

The unchanged v0.6.0 manifest records the **old** file digest. Historical declarations and the trust policy remain archived for provenance; the replaced active file is *not* misrepresented as satisfying v0.6.0. The 0.6.1 manifest, representation digest and separate code-root-pinned C7 policy digest are updated. The other 45 source records were not changed.

## What the source-level register proves

1. A 47/47 hash and byte-count match demonstrates that all *declared local files* are present and unchanged relative to the active policy.
2. The targeted Article 2(2)(a) clause matches the manually inspected official HTML excerpt. The check does **not** certify the entire consolidated Directive, PDF bytes, or future amendments.
3. **21 files remain curated identity/version notes, not complete official judicial decisions or operational guidance pages.** These gaps are emitted by source ID into the machine-readable register and Markdown report. Neither the 26 other text files' actual full-text completeness nor their current operative status has been independently reverified in C18.
4. A manifest `verification_date` is a pinned date associated with an earlier source check, **not** independent evidence of a fresh online check. The one corrected Directive record has a new targeted check date of 2026-10-10; other source dates are not changed.
5. Neither local hashes nor passage presence establish legal correctness, factual applicability, C15f expert assessment, or safe real-person processing. Review-only synthetic restrictions stay in force.

## Release and audit

For each new core bundle: validate the active source schema; run both deterministic source gates; run `test_c18_source_integrity.py`, C6/C7/C12/C16/C17 regressions; package and extract the ZIP; rerun the same checks against the extracted package. If a source representation is modified, **never** edit the manifest or C7 pin merely to make validation pass. Require provenance of actual official text and scope an explicit new version.

A future source acquisition increment should replace or augment the 21 identity notes with complete official material where permitted and independently confirm the rest of the texts and their current status, with separate evidence for legal-semantic validation.
