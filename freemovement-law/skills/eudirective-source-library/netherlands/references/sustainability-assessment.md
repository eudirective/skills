Skill: assess-source-rule-sustainability v0.2.0

# Netherlands source-route sustainability assessment

Status date: 19 October 2026

State: eight scoped source-list candidates and 49 pages from the broader 52-record monitor register are converted as unaccepted review candidates; 50 exact monitor responses were saved, one page was textless, two requests failed, and zero sources are accepted.

## Assessment boundary

The scoped source list contains six Wetten.nl statutory instruments and two IND guidance pages. All eight have official-page captures, extracted Markdown, source hashes and deterministic offline replay records. The separate monitor pass has 50 exact responses and 49 replay-verified conversions. Neither set establishes completeness for Dutch national or local sources.

## Wetten.nl current-text route

For each legislation record, the implementation requests the official stable BWB identifier without pinning an old effective-date query. The publisher redirects to the version current at retrieval. The page supplies the BWB identity, consultation date, effective interval and, where present, future or undated amendment notices. The extractor is limited to the `regeling` document container and retains the returned URL and original HTML hash. Six legal texts were retrieved on 18 October 2026; their publisher effective versions ranged from 25 September 2026 to 1 July 2026, and each was in force on the recorded assessment date.

**Assessment: fragile (medium-low confidence).** The current-version path and effective-date markers were live-checked successfully, but this implementation extracts structured HTML rather than using the publisher's XML export, whose interactive flow was documented in the official page but not established as an unattended endpoint. A page redesign could break extraction; the source's reuse terms were not independently confirmed for this automated copy workflow. The result is suitable as a review capture, not a rule to accept without a supported export route and source-use review.

## IND guidance route

Two official IND pages were retrieved from their public URLs and extracted from the `main` element. The EU-family verification page displays an update date of 25 September 2026. The objection/appeal page has no comparable stable version identifier in the capture. These pages may change as the application service or administrative process changes.

**Assessment: fragile (low confidence).** Direct pages are usable for review but lack a validated parent-index rediscovery rule and reliable change metadata. A future monitor should rediscover them from official IND topic indexes, record page dates and linked forms, and detect material text or destination changes.

## Findings and limits

| Source group | Maturity | Evidence | Remaining issue |
|---|---|---|---|
| Wetten.nl consolidated laws and regulation | Converted review candidates | Six stable BWB records resolve to current pages; identity, effective interval, raw hash and deterministic replay are recorded | HTML scraping is unsupported by a demonstrated unattended export route; usage terms and historic-version policy need confirmation; no authentic publication-chain reconciliation |
| IND residence and appeal guidance | Converted review candidates | Two official pages extracted; one displays a 25 September 2026 update date | Parent-page rediscovery and dependable change/version metadata are absent; verify linked forms and exact procedural scope |
| Wider 52-record monitor inventory | Review-candidate capture | 50 exact responses; 49 page conversions replay-verified; one textless discovery shell; two retrieval failures | Records are not reconciled into the eight-record scoped list; no source-specific version, reuse, or completeness rule established |

## Next steps before acceptance

1. Identify and validate a documented Wetten.nl XML export route that can be followed without a form or interactive session, then compare its output with the HTML capture.
2. Confirm source-use terms from the publisher's current documentation.
3. Reconcile consolidated texts with official promulgation and commencement records where version precision matters.
4. Add historical-version retrieval for dated legal questions and preserve future/undated amendment notices separately.
5. Rediscover IND guidance from official parent indexes and record outbound form changes; do not submit user or case data.
6. Reconcile the monitor conversions into the scoped register and resolve the one shell and two failed routes before making a national coverage claim.

No source is accepted. A successful response, stable identifier or replay hash does not establish legal completeness or trust.
