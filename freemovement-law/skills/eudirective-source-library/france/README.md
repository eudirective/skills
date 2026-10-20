# France source candidates

**Status updated 2026-10-19:** 47 candidates; 17 official catalog, guidance, and discovery pages converted and replay-verified; 30 local retrieval attempts failed or timed out; no law text is retained as a local copy. These counts do not mean official links are unusable. Human-review accessible government pages directly, recording their version/cutoff and limits; a local capture or DILA archive extraction is optional unless a retained conversion or recurring updater is needed. Legifrance direct retrieval returned 403 in this client. The DILA LEGI archive is a possible bulk route, not a prerequisite for ordinary source use.

- [Candidate manifest](references/candidate-manifest.json)
- [Source list](references/source-list.md)
- [Capture ledger](references/france-capture-results.json)
- [Shared capture/replay rule](../sync_candidate_pages.py)
- [Sustainability assessment](references/sustainability-assessment.md)

The register reconciles the earlier seven-candidate France pack and adds national legal-source discovery and DILA bulk-data routes, residence and visa guidance, procedure and remedies, courts, public access, privacy, oversight, and legal aid. The local manifest distinguishes candidate records and retained artifacts; it does not prevent direct use of an official source link after human review.

The official DILA LEGI public dataset is the strongest no-registration route for full legal texts. Its page states an Open Licence and provides HTTPS bulk access; the directory exposes a 1.1 GB baseline plus dated deltas through 2026-10-17. No baseline/delta replay, targeted extraction, date-specific law identity check, XML conversion, or offline replay has been implemented. The 17 captured pages are catalogue/guidance/discovery text, not statute text. The separate Légifrance API requires PISTE registration, accepted terms, application credentials, and quota management.

France-Visas and ANEF are dynamic services. Monitor only their public pages, links, and form definitions; never automate applications or collect case data. The CESEDA EU-family section must remain linked to the Conseil d'État's partial annulment in decision no. 450285 of 24 February 2022.

Refresh bounded candidate pages with `python source-library/sync_candidate_pages.py france sync`; replay saved conversions with `python source-library/sync_candidate_pages.py france verify`. This does not retrieve the bulk LEGI archive or produce current statutory text.
