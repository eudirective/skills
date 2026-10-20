Skill: assess-source-rule-sustainability v0.2.0

# Italy source-route sustainability assessment

Status date: 19 October 2026

State: the 42-record monitor inventory has 34 exact responses and 33 replay-verified page conversions; one dynamic page was textless and eight retrieval/conversion attempts failed. Five prioritized sources are in the scoped source list. Three current statutes are separately captured and converted as unaccepted full-act candidates; one earlier English guidance capture has unverified currentness; zero sources are accepted.

## Assessment boundary

This assessment rates the sustainable retrieval rules and sources in the five-record [scoped manifest](candidate-manifest.json). The broader 42-record [monitor inventory](monitor-candidate-manifest-2026-10-18.json) spans legislation, official guidance, forms, visa and mission practice, administrative procedure, remedies, courts, oversight and other discovery channels. Its 19 October capture pass is a bounded one-time review capture, not a recurring update rule. It is not fully reconciled to the scoped register and is not a coverage-completeness claim.

## Normattiva current-text route

Normattiva's official URN guide says its URNs are persistent and that a linked act can be shown as originally published, current at consultation, current on a specific date, or multivigent ([URN guidance](https://www.normattiva.it/staticPage/utilita)). It also describes an XML representation standard. The separate Open Data portal offers bulk collections, but its documented collection workflow asks for an email address, a confirmation link, and a later time-limited download link ([Open Data download procedure](https://dati.normattiva.it/Come-scaricare-i-dati)). This implementation uses the public current-text pages rather than that email-confirmed bulk workflow.

For each of the three scoped statutes, the implementation fetches the stable URN page, checks the act title, reads the publisher ELI version date where available, and extracts the article URLs published in the page's `showArticle` links. The page explicitly labels its article content as dynamically loaded by AJAX. The updater keeps the ordinary session cookie, requests each article on the allowlisted Normattiva host using the landing page as Referer and the XHR header, and waits 0.25 seconds between article requests. It validates that each returned fragment contains the expected article number, stores content-addressed raw responses, converts the first official text container to Markdown, and records per-response hashes plus an aggregate source-bundle hash. The 19 October 2026 retrieval contains 28 article responses for Legislative Decree 30/2007, 80 for Law 218/1995, and 92 for Law 184/1983. Two landing pages report ELI version date 19 October 2026; the third has no ELI version date, so its currentness relies on the official current-text selector and retrieval date. All three full outputs pass offline source-hash and deterministic conversion replay.

**Assessment: fragile (medium-low confidence).** Stable, documented URNs and the publisher's persistent identifiers support reliable act discovery. The conversion depends on article links and an undocumented AJAX endpoint embedded in HTML, not a documented bulk interface. A site redesign, session-policy change, or missing article link can break the rule. The public page currently supports retrieval without account registration, but reuse terms, request limits, and automated redistribution rights have not been independently confirmed. The route is suitable for controlled review captures; it is not ready for unattended production or automatic trust promotion.

## MAECI guidance and visa pages

The two MAECI source pages are available in the standard web view, including the current Italian foreign-judgment page ([MAECI guidance](https://www.esteri.it/it/servizi-opportunita/italiani-all-estero/stato-civile/riconoscimento-di-sentenze-straniere/)) and the visa FAQ in English and Italian ([English](https://www.esteri.it/en/ministero/sportello_info/domandefrequenti/sezione_visti_entrare_in_italia/), [Italian](https://www.esteri.it/it/ministero/sportello_info/domandefrequenti/sezione_visti_entrare_in_italia/)). Ordinary direct HTTP retrieval from this workspace returns a Radware Bot Manager challenge page instead of the publisher content. The web view confirms the page content, but it does not provide this updater a raw response it can hash and replay. No challenge bypass is used.

The English visa FAQ has an earlier 15 October 2026 review capture, but its raw HTML was not retained locally and the page does not expose a dependable version date. It stays currentness-unverified. The foreign-judgment guidance has no converted capture. MAECI's transparency register also lists the recognition procedure and refers to Law 218/1995, but its direct HTTP route is challenged in the same way. The current web-view content is useful for legal cross-checking, not as a reusable local conversion rule.

**Assessment: unsustainable for direct automated capture with the current client (high confidence).** The pages are official and useful, but the automated route does not return source text, stable version evidence, or replayable bytes. Keep these entries as monitor leads until a supported publisher export, accessible official parent feed, or other first-party public text route is established. A regional embassy page may add local instructions, but it is not a scope-equivalent replacement for central guidance.

## Findings by source group

| Source group | Maturity | Evidence | Remaining sustainability issue |
|---|---|---|---|
| Legislative Decree 30/2007 | Converted review candidate | Stable Normattiva URN; title and ELI version date checked; 28 linked article responses saved; bundle hash and deterministic replay pass | Undocumented XHR article endpoint, reuse terms and request limits unresolved; legal review and primary-publication reconciliation remain open |
| Law 218/1995 | Converted review candidate | Stable current-text URN; title and ELI version date checked; 80 article responses saved; bundle hash and replay pass | Same route fragility; verify amendments, effective-date treatment, and interaction with applicable EU instruments before acceptance |
| Law 184/1983 | Converted review candidate | Current-text URN resolves; 92 article responses saved; bundle hash and replay pass | Landing page lacks ELI version-date metadata; validate operative-version evidence and distinguish domestic adoption from international adoption/recognition rules |
| MAECI recognition guidance | Discovery / blocked direct retrieval | Current official page can be inspected through the standard web view; direct HTTP response is a security challenge | No raw capture or reproducible conversion; do not bypass the challenge; seek a documented first-party export or officially linked equivalent |
| MAECI entry and visa FAQ | Prior review capture, currentness unverified | English review text retained from 15 October 2026; current Italian and English pages are visible in web view | No raw source for replay, no dependable change date, direct requests challenged; reconcile its operational visa guidance against the statute and consular instructions |
| Other monitor leads | Review-candidate capture | The wider register has 33 replay-verified page conversions; one shell and eight failed routes are recorded | Not individually normalized to the scoped source list or assigned sustainable source-specific rules |

## Repair priorities before acceptance

1. Obtain written confirmation of Normattiva reuse terms, request limits, and whether repeated article-page requests are supported; prefer a documented XML/AKN export if available without the email-confirmed collection process.
2. Retain the current URN selector and publisher version evidence for each capture. For date-specific legal work, use and verify Normattiva's documented specific-date selection instead of treating a later consultation as historical truth.
3. Reconcile the 200 article responses with the complete article inventory and the official promulgation/amendment history; inspect annexes, notes, abrogations, and future-effective provisions before accepting any statute.
4. Add a human review step for a changed source-bundle hash. The updater stages changed text under `temp/italy/pending/` and does not replace the prior candidate; it never auto-accepts.
5. Ask MAECI for a supported public retrieval or export route, or identify an official first-party mirror whose scope is equivalent. Do not bypass its automated security challenge.
6. Retain the 15 October English FAQ as a historical review artifact only until a raw capture and current-version check are available; keep Italian and English versions as distinct language records.
7. Reconcile all 42 monitor leads, including procedural rules, forms, mission instructions, remedies, court decisions, and oversight, before making a national coverage claim.

## Coverage limits

This is a bounded register, not a complete Italian legal-source catalogue. The three statute captures and wider monitor conversions are unaccepted. Direct MAECI retrieval is not sustainable with the current client, and the monitor pass has unresolved failures and PDF text-quality warnings. A stable URL, successful HTML response, article count, or conversion hash does not establish legal completeness, authoritative status, or trust.
