# Bulgaria national-source candidates

Status updated 19 October 2026: all 35 candidates were attempted with the shared bounded HTTPS capture rule; 24 source texts converted and replay-verified, 11 remained blocked, errored, or unavailable; 0 accepted.  
Research date: 18 October 2026; retrieval run: 19 October 2026.  
Jurisdiction: Bulgaria (EU Member State).

This pack records official-source leads found by comparing the Denmark, Sweden, Czechia, Hungary, and Romania reviews. It is not a complete inventory or a legal equivalence assessment. See [`references/source-list.md`](references/source-list.md) for the dated search and candidate register, [`references/candidate-manifest.json`](references/candidate-manifest.json) for machine-readable records, and [`references/sustainability-assessment.md`](references/sustainability-assessment.md) for route constraints and missing runtime evidence.

## Main routes found

- Bulgaria has a distinct Act on the entry, residence, and departure of EU citizens and their family members. The Ministry of Interior (MVR) Migration Directorate's service page links the Act and applicant forms. Keep this source family distinct from the Foreigners Act, which governs broader third-country national matters.
- The MVR legislation index links a Visa Ordinance PDF whose visible amendment history stops at April 2019. The Council of Ministers' legal information system records the underlying Ordinance №198 as amended by Decrees №3/2025 and №221/2025, and the State Gazette publishes those amendments. The MVR PDF is therefore not a sufficient current text. PRIS is a revision/index route, but its attachment remains the original 2011 file; no current consolidated payload was verified.
- The Ministry of Foreign Affairs (MFA) visa hub is a useful central procedural route, including an EU-family treatment section and an outbound link to the European Commission's prior-consultation list. The Commission download URL is versioned; rediscover it from the MFA page instead of treating the current file URL as permanent.
- The Administrative Procedure Code, Ombudsman, data-protection, discrimination, and court-search routes provide separate remedies and oversight leads. They do not form one complete appeal or lower-court search index.

## Capture and replay

The shared capture ledger is [`references/bulgaria-capture-results.json`](references/bulgaria-capture-results.json). The reusable route and offline integrity replay are [`../sync_candidate_pages.py`](../sync_candidate_pages.py). Run `python source-library/sync_candidate_pages.py bulgaria sync` to refresh the register and `python source-library/sync_candidate_pages.py bulgaria verify` to replay hashes and conversions. The current pass saved and converted 24 candidates. Four MFA links redirected to a third-party bot-validation host and were not followed; TLS errors, 404, and 500 responses were left unresolved.

## Review boundary

All records remain candidates. Some PDFs or linked form endpoints returned HTTP 403 or an error page during inspection; those outcomes are recorded rather than treated as proof that the source is unavailable to every client. No API, registration requirement, or bulk-use permission was identified in this bounded search. That is an unverified search result, not proof none exists.

The MVR EU-family notice page can expose applicant-specific notices and names. It is a procedural lead only: do not harvest, copy, or archive individual notices in the source library.
