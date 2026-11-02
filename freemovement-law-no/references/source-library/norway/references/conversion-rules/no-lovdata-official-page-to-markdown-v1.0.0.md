# Lovdata official current-law page to retained text — rule v1.0.0

**Applies to:** one individually identified current formal law captured from its official Lovdata record page. It does not authorize whole-site or systematic page extraction.

**Demonstrated record:** Norway's EØS-arbeidstakarlova, LOV-2012-12-14-81, rendered in Nynorsk.

## Official source and reuse basis

- Official current record: `https://lovdata.no/lov/2012-12-14-81` (page's document URL: `https://lovdata.no/dokument/NL/lov/2012-12-14-81`).
- Retrieved: 2026-10-31; UTF-8 response: 131,405 bytes; SHA-256 `51530d4b9f44df1350f9a057be32374fac0db2441cc2504e7494c0ccb3d78d6b`.
- Official record identifies LOV-2012-12-14-81 and says it was last changed by LOV-2025-04-10-8. The official amendment record reports that amendment in force from 2025-04-10. The page also records a correction dated 2022-05-05.
- Lovdata's terms, last changed 2025-10-31, permit copying, using and sharing an individual current formal law when Lovdata is attributed and NLOD 2.0 is followed. The same terms prohibit mass downloads and systematic extraction from the web service; larger downloads are routed to Lovdata's open APIs. The API dataset is not the retained source for this record.
- Attribution in the retained file: “Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Lovdata”. NLOD 2.0 permits copying, modification and distribution subject to attribution, link to the licence and source where practical, and clearly identifying changes. This is one current formal law, not bulk republication of the page service.

## Deterministic conversion

- Page adapter: [`convert_lovdata_official_page_to_markdown.py`](convert_lovdata_official_page_to_markdown.py), version 1.0.0, SHA-256 `3db2703aab1c295cdbe3f5714ceab1c217fd5d41f656c3d7af7e6477019cb1ca`.
- Shared renderer: [`convert_lovdata_html_to_markdown.py`](convert_lovdata_html_to_markdown.py), version 0.4.0, SHA-256 `02089c623200666729969edf08ce09e12289c0050d747de337e2754c32bd7b41`.
- The adapter first verifies the exact response SHA-256 and extracts only the single `#documentBody`. It uses the publisher's displayed title, legal identifier, last-change identifier, correction note and language metadata. It drops the page navigation and share controls, maps the publisher's `PARAGRAF_n` and `ARTIKKEL_n` containers to retained legal-section containers, and preserves ordered headings, lists, visible words, punctuation, notes, footnote markers, legal anchors and cross-reference text. It does not translate or paraphrase.
- The adapter proves the normalized visible text of the selected official page body equals the adapted body before rendering. The shared renderer additionally checks exact visible-body equivalence, ordered element identifiers, duplicate/missing identifiers, per-section bodies and footnote reference/note pairing. A review copy's frontmatter acceptance field is changed from `unaccepted_local_review_copy` to `accepted_local_copy` only after source, rights and conversion review; the legal text is not changed by this final status stamp.
- Derived adapter input: 75,475 bytes; SHA-256 `832bbe848fb63f0429bccd22f2c30792cb6280f8b1783a8659c5e7ff9c37edaa`.
- Converter output before the acceptance-status stamp: 78,324 bytes; SHA-256 `6c3ad9045cfba8e273a909b12f14f0e13ccf45f50cd17468fc579276a5753951`.
- Retained source file after the acceptance-status stamp: 78,315 bytes; SHA-256 `beb10b9e5347908daf32f6981b0a5d39bd71b283c0ebc1acb84241fc998754c6`.

## Verification and limits

- Two independent replays of the captured page produced the same derived-input and converter-output hashes. Validation passed with 46 ordered legal sections, zero body mismatches, zero unmatched footnote references, zero missing/unexpected/duplicate source identifiers, and exact normalized visible-body preservation.
- The separately captured Lovdata NLOD 2.0 current-laws API package member contains the same 46 sections but omits visible list labels in Articles 3, 13, 15, 19, 22 and 30 that appear on the official record page. The API conversion is therefore not used for the retained copy. The page-derived copy preserves these enumerators.
- Legalize-no commit `729ce30333de9d6f9f1e5faf537999cf42bc2a2f`, file `no/LOV-2012-12-14-81.md`, was checked as a discovery candidate. A current-page comparison aligned 46 of 46 headings in order, but 17 Legalize article bodies are empty; its §1 amendment note and §4 boundary differ, Articles 22/30 have damaged list layout, and Article 42 omits the displayed EEA footnotes. The Legalize file is not the retained source text and was not copied into the source library.
- This representation is the single official current-law page's displayed text, not a statement that every EEA instrument referenced by §1 is reproduced in this law record. No topic is accepted and Norway's national pack remains incomplete. Recheck the official page and amendment metadata before time-sensitive use.
