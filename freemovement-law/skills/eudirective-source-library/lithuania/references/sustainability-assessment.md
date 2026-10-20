# Lithuania source-rule sustainability assessment

Assessment date: 19 October 2026. Scope: the 44 candidates in [`source-list.md`](source-list.md) and [`candidate-manifest.json`](candidate-manifest.json). This assesses the retrieval and conversion route, not legal advice, source completeness, or acceptance.

## Implemented route and observed results

[`../sync_lithuania.py`](../sync_lithuania.py) tries the official e-TAR record by ordinary HTTPS GET. When that page returns HTTP 403, it queries the Seimas Chancellery's official TAR dataset API at `get.data.gov.lt`, using the exact `dokumento_id` and `suvestines_id`, and saves both the metadata response and full Lithuanian `tekstas_lt` record. Reads required no account or API registration in the observed run. API validity dates, record IDs, source links, raw JSON hashes, and converted Markdown hashes are stored. Public HTML candidates are converted from their main body. Offline `verify` checks the raw bytes, API identity/version, conversion hash, and deterministic conversion replay.

The 19 October run converted 13 TAR API records and two HTML pages; it also saved the LITEKO public-search shell as a discovery surface without treating it as a decision. Twenty-eight candidates yielded HTTP 403 or no matching version row. The 44-entry inventory has 15 converted texts, one captured discovery surface, 28 retrieval failures, and zero locally stored copies accepted.

The dataset API exposes useful structure, but its current-version records are not a reliable current-law feed in the observed data. Examples:

- For the Aliens Act, e-TAR candidate evidence identifies a 1 July 2026 to 31 October 2026 consolidation; the API lists a 1 January 2026 version with no end date.
- For two residence-card procedures, the API's latest version ended on 30 June 2019, while the inventory records current official text pages inspected on 18 October 2026.
- The Public Administration Law API version begins 1 January 2024 with no end date, while e-TAR candidate evidence identifies a 1 October 2026 to 31 December 2026 edition.
- The administrative proceedings, Ombudsmen, data-protection, and legal-aid texts show API dates that predate the current versions recorded in the candidate inventory.
- The newly identified Seimas Chancellor Order 400-ĮVK-229 has no row in the dataset API under the candidate's record identifier.

All 13 API texts are official state-published snapshots, but the dataset marks some as currentness-unverified or not current. Preserve those labels and dates: use such records as dated working texts/version leads, not as proof of current wording. Prefer the latest available e-TAR or dataset version for a current-law question, and resolve a specific status conflict only when it affects the provisions in scope. A full reconciliation of every API record with e-TAR is not a prerequisite for ordinary source use.

## Verdict

**Use the responsible official publisher's human-reviewed page for ordinary source use. The TAR API is an optional snapshot route, not a dependable current-version selector where its dates conflict with e-TAR.** Confidence is high for the observed version mismatches and medium for repeatable API retrieval. A direct source reference remains usable within its reviewed date and scope without an API query, local copy, hash, or conversion. Guidance and form retrieval remains **undetermined** in this client because direct requests returned 403; this does not prevent human review at the official site when available. The court search remains a selective discovery channel.

| Dimension | Evidence | Remaining limitation |
|---|---|---|
| Source identity | The API returns `dokumento_id`, `suvestines_id`, `nuoroda`, and validity dates; the converter checks exact act and version identifiers. | API results are not consistently reconciled with the e-TAR page or legal amendment chronology. |
| Retrieval | Official API reads succeeded with ordinary GET; the API documentation describes filtering, pagination and change queries. | The refresh has one observation cycle. API model documentation labels consolidated-text fields as in development. e-TAR and multiple guidance hosts returned 403 in this client. |
| Version selection | The script enumerates version metadata and selects the latest interval that contains the retrieval date, or labels the latest prior version if no active interval exists. | An API-marked open-ended version can be older than the e-TAR current consolidation. Thus the dataset's own validity interval is insufficient as a currentness assertion. |
| Payload and conversion | API JSON carries full Lithuanian text in `tekstas_lt`; raw records and converted text are hash-pinned, and offline replay passes. | The API may omit newer consolidated texts, amendments or annexes. PDF and attachment extraction is not implemented; no direct e-TAR sample was readable in this environment. |
| Failure and review state | HTTP 403, missing API versions, and interactive search surfaces remain explicit. All outputs are review candidates. | Parent-index rediscovery and alternative publisher-supported delivery are not established. Do not retry or bypass access controls automatically. |
| Reuse | The official dataset record identifies CC BY 4.0 for that dataset. | Do not extend that licence to direct e-TAR pages, government guidance, third-party mission pages, forms, or court material. Persistent storage and transformation terms for these sources need separate review. |
| Coverage | Candidate types include laws, guidance, forms, visa practice, procedure, courts, privacy, oversight and legal aid. | Most non-API pages were blocked from this client; LITEKO is selective and not a complete decisions corpus. Candidate coverage is not complete national coverage. |

## Optional work for a recurring local monitor

The items below apply only if a recurring updater or retained-copy workflow is wanted. They do not gate citation of a human-reviewed official page, source-reference usability, or topic research.

- Prefer the latest government-published text and its displayed date/cutoff. Resolve only a known API/e-TAR conflict that affects the provisions in scope; do not reconcile every act against Gazette history.
- Check reuse conditions for whichever publisher and content the updater would retain. The dataset's CC BY 4.0 notice does not extend to e-TAR, agency guidance, forms, or court content.
- Keep HTTP 403 responses as access limitations; use a publisher-supported route or manual official page review, and do not bypass access controls.
- If converting or retaining text, validate the relevant legal passages and any material attachments. Broad pagination, change-feed, and replay checks are needed only when the selected recurring workflow relies on them.
- Keep LITEKO search as selective discovery, not a completeness claim. Do not capture submitted applicant data.

All current outputs remain unaccepted review candidates. The API is a useful source snapshot, not proof that a retrieved text is the current law.
