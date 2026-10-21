# France source candidates

**Status updated 2026-10-21:** 48 candidates; 17 official catalogue, guidance, and discovery pages converted and replay-verified; 30 local retrieval attempts failed or timed out; no law text is retained as a local copy. The two parts of CESEDA Book II are now recorded as usable official references: the legislative section displayed a version in force as of 24 August 2026, and the regulatory section as of 9 September 2026. These are link-use reviews, not accepted local copies; check the page's displayed version again for date-sensitive work. Legifrance direct retrieval returned 403 in this client. The DILA LEGI archive is an optional route for retaining or monitoring copies, not a prerequisite for ordinary source use.

- [Candidate manifest](references/candidate-manifest.json)
- [Source acceptance and official-reference reviews](references/source-acceptance.json)
- [Source list](references/source-list.md)
- [Capture ledger](references/france-capture-results.json)
- [Shared capture/replay rule](../sync_candidate_pages.py)
- [Sustainability assessment](references/sustainability-assessment.md)

The register reconciles the earlier seven-candidate France pack and adds national legal-source discovery and DILA bulk-data routes, residence and visa guidance, procedure and remedies, courts, public access, privacy, oversight, and legal aid. The local manifest distinguishes candidate records and retained artifacts; it does not prevent direct use of an official source link after human review.

The official consolidated Légifrance sections are sufficient for ordinary legal-reference use. The DILA LEGI bulk dataset and Légifrance API are optional acquisition routes only if a retained copy or recurring monitor is later needed; no bulk replay, API registration, credentials, or local conversion is required for the reviewed links. The 17 local conversions are catalogue, guidance, and discovery pages, not statute copies.

France-Visas and ANEF are dynamic services. Monitor only their public pages, links, and form definitions; never automate applications or collect case data. The CESEDA EU-family section must remain linked to the Conseil d'État's partial annulment in decision no. 450285 of 24 February 2022.

Refresh bounded candidate pages with `python source-library/sync_candidate_pages.py france sync`; replay saved conversions with `python source-library/sync_candidate_pages.py france verify`. This does not retrieve the bulk LEGI archive or produce current statutory text.
