# Bulgaria national-source candidates

Status updated 21 October 2026: the register has 36 records. The original 35-candidate capture run converted and replay-verified 24 texts; 11 remain blocked, errored, or unavailable. Two official Visa Ordinance references are now usable by link: the MFA consolidated edition through State Gazette issue 4/2025 and the targeted later changes in Decree №221/2025. No local copy is accepted.
Research date: 18 October 2026; retrieval run: 19 October 2026.  
Jurisdiction: Bulgaria (EU Member State).

This pack records official-source leads found by comparing the Denmark, Sweden, Czechia, Hungary, and Romania reviews. It is not a complete inventory or a legal equivalence assessment. See [`references/source-list.md`](references/source-list.md) for the dated search and candidate register, [`references/candidate-manifest.json`](references/candidate-manifest.json) for machine-readable records, and [`references/sustainability-assessment.md`](references/sustainability-assessment.md) for route constraints and missing runtime evidence.

## Main routes found

- Bulgaria has a distinct Act on the entry, residence, and departure of EU citizens and their family members. The Ministry of Interior (MVR) Migration Directorate's service page links the Act and applicant forms. Keep this source family distinct from the Foreigners Act, which governs broader third-country national matters.
- The MFA normative-documents index links a 42-page consolidated Visa Ordinance PDF whose heading lists amendments through State Gazette issue 4/2025 (14 January 2025). Use this as the closest current government-published consolidation within that cutoff, supplemented by the specific later changes in Decree №221/2025 §3. The MVR-linked PDF stops in 2019 and is historical only; PRIS records the amendment trail but attaches only the original 2011 files. No full amendment-chain reconstruction is required.
- The Ministry of Foreign Affairs (MFA) visa hub is a useful central procedural route, including an EU-family treatment section and an outbound link to the European Commission's prior-consultation list. The Commission download URL is versioned; rediscover it from the MFA page instead of treating the current file URL as permanent.
- The Administrative Procedure Code, Ombudsman, data-protection, discrimination, and court-search routes provide separate remedies and oversight leads. They do not form one complete appeal or lower-court search index.

## Capture and replay

The shared capture ledger is [`references/bulgaria-capture-results.json`](references/bulgaria-capture-results.json). The reusable route and offline integrity replay are [`../sync_candidate_pages.py`](../sync_candidate_pages.py). Run `python source-library/sync_candidate_pages.py bulgaria sync` to refresh the register and `python source-library/sync_candidate_pages.py bulgaria verify` to replay hashes and conversions. The original 19 October capture pass saved and converted 24 candidates. Four MFA links redirected to a third-party bot-validation host and were not followed; TLS errors, 404, and 500 responses were left unresolved.

## Review boundary

The 36-record register contains 0 accepted local copies. Two official Visa Ordinance references have passed a link-use review; the remaining records are still candidates. Some PDFs or linked form endpoints returned HTTP 403 or an error page during inspection; those outcomes are recorded rather than treated as proof that the source is unavailable to every client. No API, registration requirement, or bulk-use permission was identified in this bounded search. That is an unverified search result, not proof none exists.

The MVR EU-family notice page can expose applicant-specific notices and names. It is a procedural lead only: do not harvest, copy, or archive individual notices in the source library.
