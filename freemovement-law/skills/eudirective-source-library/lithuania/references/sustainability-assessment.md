# Lithuania source-rule sustainability assessment

Assessment date: 19 October 2026. Scope: the 44 candidates in [`source-list.md`](source-list.md) and [`candidate-manifest.json`](candidate-manifest.json). This assesses the retrieval and conversion route, not legal advice, source completeness, or acceptance.

## Implemented route and observed results

[`../sync_lithuania.py`](../sync_lithuania.py) tries the official e-TAR record by ordinary HTTPS GET. When that page returns HTTP 403, it queries the Seimas Chancellery's official TAR dataset API at `get.data.gov.lt`, using the exact `dokumento_id` and `suvestines_id`, and saves both the metadata response and full Lithuanian `tekstas_lt` record. Reads required no account or API registration in the observed run. API validity dates, record IDs, source links, raw JSON hashes, and converted Markdown hashes are stored. Public HTML candidates are converted from their main body. Offline `verify` checks the raw bytes, API identity/version, conversion hash, and deterministic conversion replay.

The 19 October run converted 13 TAR API records and two HTML pages; it also saved the LITEKO public-search shell as a discovery surface without treating it as a decision. Twenty-eight candidates yielded HTTP 403 or no matching version row. The 44-entry inventory has 15 converted texts, one captured discovery surface, 28 retrieval failures, and zero accepted sources.

The dataset API exposes useful structure, but its current-version records are not a reliable current-law feed in the observed data. Examples:

- For the Aliens Act, e-TAR candidate evidence identifies a 1 July 2026 to 31 October 2026 consolidation; the API lists a 1 January 2026 version with no end date.
- For two residence-card procedures, the API's latest version ended on 30 June 2019, while the inventory records current official text pages inspected on 18 October 2026.
- The Public Administration Law API version begins 1 January 2024 with no end date, while e-TAR candidate evidence identifies a 1 October 2026 to 31 December 2026 edition.
- The administrative proceedings, Ombudsmen, data-protection, and legal-aid texts show API dates that predate the current versions recorded in the candidate inventory.
- The newly identified Seimas Chancellor Order 400-ĮVK-229 has no row in the dataset API under the candidate's record identifier.

All 13 API texts are saved for comparison only. The manifest and Markdown identify them as currentness-unverified or not-current according to the dataset fields; none should be treated as the operative version until reconciled with e-TAR.

## Verdict

**The API rule is sustainable for retrieving and replaying dataset snapshots, but unsustainable as a standalone current-law rule.** Confidence: high for the observed version mismatches, medium for repeatable API retrieval, and low for the complete legal and reuse position. The public interface is documented, the dataset identifies a CC BY 4.0 licence, and sampled GET requests worked without registration. Those strengths do not overcome stale or missing consolidation metadata. Guidance and form retrieval remains **undetermined** because direct requests from this client returned 403; the court search remains an incomplete interactive discovery channel.

| Dimension | Evidence | Remaining limitation |
|---|---|---|
| Source identity | The API returns `dokumento_id`, `suvestines_id`, `nuoroda`, and validity dates; the converter checks exact act and version identifiers. | API results are not consistently reconciled with the e-TAR page or legal amendment chronology. |
| Retrieval | Official API reads succeeded with ordinary GET; the API documentation describes filtering, pagination and change queries. | The refresh has one observation cycle. API model documentation labels consolidated-text fields as in development. e-TAR and multiple guidance hosts returned 403 in this client. |
| Version selection | The script enumerates version metadata and selects the latest interval that contains the retrieval date, or labels the latest prior version if no active interval exists. | An API-marked open-ended version can be older than the e-TAR current consolidation. Thus the dataset's own validity interval is insufficient as a currentness assertion. |
| Payload and conversion | API JSON carries full Lithuanian text in `tekstas_lt`; raw records and converted text are hash-pinned, and offline replay passes. | The API may omit newer consolidated texts, amendments or annexes. PDF and attachment extraction is not implemented; no direct e-TAR sample was readable in this environment. |
| Failure and review state | HTTP 403, missing API versions, and interactive search surfaces remain explicit. All outputs are review candidates. | Parent-index rediscovery and alternative publisher-supported delivery are not established. Do not retry or bypass access controls automatically. |
| Reuse | The official dataset record identifies CC BY 4.0 for that dataset. | Do not extend that licence to direct e-TAR pages, government guidance, third-party mission pages, forms, or court material. Persistent storage and transformation terms for these sources need separate review. |
| Coverage | Candidate types include laws, guidance, forms, visa practice, procedure, courts, privacy, oversight and legal aid. | Most non-API pages were blocked from this client; LITEKO is selective and not a complete decisions corpus. Candidate coverage is not complete national coverage. |

## Requirements before monitor use

1. Ask the data publisher whether the TAR dataset's consolidated-text model is current for all relevant acts, what causes the observed date gaps, and whether the model's “develop/in preparation” status is resolved.
2. Cross-check each API version against the live e-TAR page and Gazette/amendment chronology. Fail closed when an API date conflicts with e-TAR or when the dataset exposes no current edition.
3. Obtain an official, supported route for e-TAR and the government pages that returned 403. Keep manual access as the stated route if the publisher provides no automated option; do not simulate a browser or bypass a block.
4. Confirm reuse terms separately for the dataset, e-TAR, government guidance and forms, and court decision content. The dataset licence does not cover other publishers by implication.
5. Add tests for late amendments, future-effective editions, missing end dates, overlapping intervals, missing consolidated versions, annex-bearing records, pagination, and deterministic replay before any source is promoted.
6. Keep LITEKO search as a bounded discovery channel, not a completeness claim or change feed. Do not capture submitted applicant data.

All current outputs remain unaccepted review candidates. The API is a useful source snapshot, not proof that a retrieved text is the current law.
