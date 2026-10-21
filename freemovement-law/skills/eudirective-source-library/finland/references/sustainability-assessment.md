Skill: assess-source-rule-sustainability v0.2.0

# Finland source-route sustainability assessment

Status date: 19 October 2026
State: 36 candidates, 25 unaccepted review-candidate conversions (23 converted and two changed versions staged), zero locally stored copies accepted; eleven legal texts are captured (eight Finnish acts and three unofficial English translations), while wider source coverage and version review remain incomplete.

## External reference acceptance — 21 October 2026

Eight current Finnish Finlex consolidated-law page references are accepted in [source-acceptance.json](source-acceptance.json). Finlex identifies itself as owned by the Ministry of Justice and maintained by the Legal Register Centre. This decision accepts those dated official page links only; it does not accept any local conversion or certify legal-topic coverage. The Openness Act record uses the 28 November 2025 current ELI date, and the Police Personal Data Act record uses the 9 October 2026 Finnish consolidation. For 808/2019, the official page reference is accepted while the retained XML conversion stays unaccepted for date-sensitive use because its expression metadata conflicts with the consolidation and effective-date metadata. The other 28 inventory records remain candidates or are routed to official sites for human review.

## Assessment boundary

The current register at [source-catalog.json](source-catalog.json) identifies official leads for national law and legal discovery; free-movement and family guidance; population registration; visas and consular routes; procedure, language and file access; appeals, courts and case law; privacy, oversight and legal aid. It is a bounded search record, not a claim that Finland's source universe is complete. Eleven legal text records have local conversions; none has been accepted as a retained copy.

The initial discovery assessment below predates the live checks and conversion documented in “Live route and conversion update.” Its untested-route statements are historical. The current operational verdict at the end of this file applies to the API and page-fallback evidence collected on 19 October 2026. No whole-pack retrieval rule is implemented, and No locally stored artifact has been accepted.

## Strongest proposed route: Finlex open data

Finlex publishes official documentation for a REST API and downloadable data packages. The API returns Akoma Ntoso XML and, for some datasets, JSON listings. The official quick guide says API access does not require identification or registration; TLS 1.2 or later and a `User-Agent` header are required. Listing endpoints use `page` and `limit` pagination, and the service can return HTTP 429 when request volume is restricted. Documents can refer by relative HATEOAS links to attachments, images, or PDFs that contain the body text. API data is updated with a small delay after publication, while downloadable packages are updated daily. The guide gives an example of a consolidated current statute and links to the OpenAPI description.

This is strong design evidence for a possible national-law acquisition route. It supports a constrained design that begins with a date-specific official law record, retrieves its exact Akoma Ntoso representation, validates jurisdiction, instrument type, number, language, and validity metadata, and follows only publisher-relative attachment links required to obtain the body. A bounded page loop and deliberate handling of 429 responses would be required. The API and the daily package route have different update timing and should not be blended without recording which is authoritative for a given check.

The local live check did not reach the API: workspace DNS resolution for `opendata.finlex.fi` failed. This is an environment limitation, not evidence of publisher failure. The quick guide and OpenAPI description were inspected, but there is no captured API response, fixture, conversion, deterministic replay, or verified output. The available documentation does not settle every operational question about terms, practical rate limits, maximum response sizes, charset behavior, error payloads, or how all current consolidated versions expose commencement and end-of-validity metadata.

**Proposed-route assessment:** technically promising and documented, but untested. It is not an implemented rule and is not rated.

## Version selection and language are critical dependencies

The Aliens Act shows why a translation's presence cannot stand in for current legal text:

- Finlex's official current Finnish Aliens Act record exposed an ELI consolidation date of 26 June 2026, but opening the page exceeded the research client's 4 MiB response limit. The title and current-law record were identified, but exact current provision content was not independently inspected in this run.
- Finlex's official English translation page states that the translation was completed on 20 December 2023 and tracks amendments only through 389/2023. It is not a current English rendering of later changes.
- The English Administrative Procedure Act page states a completion date of 7 January 2019 and an amendment cutoff of 893/2015.
- The English Act on Judicial Procedure in Administrative Matters translation was completed on 19 January 2024 and tracks amendments through 639/2021.
- Finnish and Swedish consolidated texts, unofficial translations, original enactments, and amendment instruments must remain distinct records. A high version date or an `updated` URL alone does not establish which wording was in force on a requested date.

For ordinary use, cite the latest government-published Finlex text that is usable for the question and record its date, language, and cutoff. Do not require an API response or a local capture. Treat an unofficial English translation within its publisher-stated cutoff; use Finnish where translation currency is uncertain. The known 808/2019 date conflict needs follow-up only if it affects the provisions in scope.

## Proposed route findings

| Source group | Maturity | Proposed route and evidence | Main unresolved sustainability issue |
|---|---|---|---|
| Finlex national statutes | Discovery-only | Official OpenAPI-described route; Akoma Ntoso XML; documented consolidated-act example; no registration | No live retrieval, exact-response validation, amendment/date query proof, schema fixture, converter, or offline replay |
| Finlex downloadable packages | Discovery-only alternative | Official UI package route, updated daily and organized around Akoma Ntoso | Package completeness, version semantics, repeatable selection, file sizes, and update detection were not checked |
| Migri residence and family guidance | Discovery-only | Official residence-registration, EU/family, fees and processing-time pages | Direct inspection of the key registration page returned 403 from the research client; guidance freshness and dynamic links need a supported live check. This does not establish a Migri outage |
| DVV registration and forms | Discovery-only / monitor-only | Official population-register guidance and municipality-of-residence form | These procedures are distinct from Migri residence-right decisions; online forms contain personal data and must not be automated or retained |
| MFA visa and mission routes | Discovery-only | Official MFA visa page and FAQ link onward to missions and the Finland Visa service | Mission representation, local providers, fees, appointments and country instructions are dynamic; page-link rediscovery is required |
| Procedure, remedies and public access | Discovery-only | Finlex statutes plus Oikeus.fi and official court guidance | Older English translations, decision-specific filing instructions, exceptions, and date-specific legal text need provision-level review |
| Administrative courts and KHO case law | Discovery-only | Official court administration and Supreme Administrative Court pages | Court venue depends on the matter; precedent publication is selective and English summaries are not comprehensive |
| Privacy, oversight and legal aid | Discovery-only | Data Protection Ombudsman, Parliamentary Ombudsman, Chancellor of Justice, and National Legal Services Authority | Complaint competences differ; some routes and language access are unverified; legal-aid e-services are described as Finnish/Swedish-only |

## Publisher and route distinctions

Finlex is a free legal-information database maintained by the Legal Register Centre, but its own portal says its materials come from multiple authorities and courts and that the Ministry of Justice and Legal Register Centre are not responsible for content other than their own. A future rule must identify the issuing authority and document, not treat the portal brand as sufficient proof of the source's legal authority.

N-Lex is useful for finding Finland's national legal database profile. It does not cover every source class and is not a substitute for Migri, MFA, courts, DVV, or oversight bodies. EU-law database discovery also does not by itself establish the applicable EEA or Swiss legal route.

Migri's right-of-residence registration, DVV's population-register/municipality process, and the MFA's Schengen visa process are separate routes. They should remain separate records and checks. Application and registration services may collect sensitive personal information; only public guidance and public form definitions belong in automated monitoring.

## Optional work for recurring local monitoring

These engineering checks apply only if automated retrieval or retained copies are needed. A human-reviewed official Finlex page with its edition date, language, and limits is enough for ordinary research. Use the closest government-published version; a complete amendment-chain audit is not required.

- Use the latest native Finlex consolidation for the relevant date. Keep unofficial English translations' own cutoffs visible. Resolve the known 808/2019 date conflict only if it affects the provisions in scope.
- If using the API or PDF route repeatedly, confirm that route's identity and applicable reuse conditions; validate only the payload and conversion the monitor will retain. A bulk package comparison, fixture matrix, and replay verifier are not prerequisites for citing Finlex.
- Review specific Migri, MFA, court, and oversight pages directly for the operational issue in scope. Parent-index rediscovery is useful only when maintaining a recurring link monitor; do not automate forms or personal services.

## Coverage limits

Remaining limits include version-date reconciliation for the 808/2019 Finlex Akoma Ntoso XML; five current consolidated-text API requests returned 404; the two rendered-page and three RSC page fallbacks depend on dynamic page structures; some Migri pages returned 403; Chancellor of Justice and Data Protection Ombudsman complaint routes remain unverified; and no complete court-decision corpus has been proven. These are named search limits, not evidence that the publishers or sources are unavailable. All eleven legal-text conversions remain review candidates, not accepted sources.


## Live route and conversion update — 19 October 2026

A direct, low-volume check against the official Finlex API revised the earlier environment-blocked finding. The API is reachable without registration when called over HTTPS with a `User-Agent`, but route coverage is not uniform: the current Aliens Act (301/2004) and Administrative Procedure Act (434/2003) API requests returned HTTP 404, while the current Act on Judicial Procedure in Administrative Matters (808/2019) returned an Akoma Ntoso XML document. The attempted English-translation route for the Aliens Act returned 404. These are record-specific API results, not evidence that the acts or translations are absent from Finlex.

The official Aliens Act page was captured at `https://www.finlex.fi/fi/lainsaadanto/2004/301`. It identified current ELI version `http://data.finlex.fi/eli/sd/2004/301/ajantasa/2026-06-26/fin`. The publisher page response was 6.3 MB and its rendered `main` content was captured separately; the converter removes the page navigation/table of contents, keeps the statutory text and source ELI, and produces a review-candidate Markdown file. Raw HTML, rendered text and Markdown hashes are recorded under project-root `temp/` and `finlex-retrieval-manifest.json`. The rule is **fragile, medium confidence**: current text identity and offline conversion replay are retained, but retrieval depends on a dynamic publisher page and browser rendering for records the API does not serve. This is a fallback for the identified record, not a complete national acquisition rule.

Finlex states that its open data is available under CC BY 4.0, subject to its personal-data restrictions. The official download page listed the updated-legislation archive at 4.1 GB, the Statute Book at 12.3 GB and translations at 151 MB, all last updated 17 October 2026. That bulk route is too large to use as the routine fallback for individual statutes; it may be useful for a separately scoped bulk mirror after its record-selection and freshness behavior are reviewed.

The eight Finnish statutory copies and three identified English translations remain **unaccepted local copies**. The Aliens Act capture confirms that § 3(2) includes EU Member State, Icelandic, Liechtenstein, Norwegian and Swiss nationals in the statutory definition of “Union citizen and equivalent person”; this is a source-content observation, not a legal completeness finding. The Administrative Procedure Act page identifies ELI version 27 June 2025 and includes an amendment effective date of 1 January 2026. The 808/2019 Akoma Ntoso conversion preserves 15 chapters and 127 sections, but its expression ELI date is 5 July 2019, its consolidation date is 27 March 2026, and its metadata lists amendment 213/2026 effective 14 April 2026. Keep this as a dated Finlex-published snapshot; do not label the affected provision current until the latest official Finlex text or that specific amendment resolves the date conflict. No full amendment-chain comparison is required. Two additional API XML records match Acts 1050/2018 and 616/2019; their API consolidation dates are 22 May 2026 and 9 October 2026. Three further current Finnish texts (621/1999, 423/2003 and 257/2002) were extracted from official page RSC streams after their direct consolidated-API routes returned 404; their displayed ELI dates are 28 November 2025, 19 December 2024 and 22 May 2026. The three English PDFs were rediscovered from official translation-history pages; their publisher-recorded cutoffs are 389/2023, 893/2015, and 639/2021. Finlex labels them unofficial and says only Finnish and Swedish are legally binding. Guidance, forms, court/oversight sources and all personal-data service candidates still need their own source review.

The translation-PDF adapter captures the official parent page, verifies the act title, completion date and amendment cutoff, rediscovers the English PDF link, then checks its media type, PDF signature, page count and source identity markers. It stores page and PDF responses by hash and converts offline with pinned pypdf 6.10.0. All three PDFs had extractable text on every page and pass replay verification. A changed translation cutoff or page count fails closed for manual review.

The expanded capture pass corrected a generic-conversion quality issue: the monitor helper had marked eleven law pages as converted even though it produced only short portal shells. Those broad-pass records are now classified as discovery surfaces with no legal text. The separate source-specific lanes retain eight current Finnish acts: three publisher-page conversions, three Akoma Ntoso API conversions and two earlier page captures. All eight were replay-verified offline. For Acts 621/1999, 423/2003 and 257/2002, the [RSC capture manifest](finlex-rsc-retrieval-manifest.json) records the exact page hash, displayed ELI, paragraph and heading counts, and converted output; its parser requires a Finnish Akoma Ntoso section, exact act identity, a current ELI, the enacting formula and minimum body/section thresholds. This is a validated fallback for these three records, not a sustainable API replacement: the publisher's Next.js component stream is undocumented and may change.

## Current operational verdict

| Route | Current verdict | Evidence and limit |
|---|---|---|
| Finlex Akoma Ntoso API | **Fragile for this candidate set; medium confidence** | No registration; the official guide asks for HTTPS/TLS 1.2+, a `User-Agent`, and describes API XML plus a daily package alternative. Three identity-matching current-text XML records convert offline (808/2019, 1050/2018, 616/2019); five current-consolidation requests returned 404 (301/2004, 434/2003, 621/1999, 423/2003, 257/2002). The 808/2019 version metadata conflict remains unresolved. Do not infer complete current-law coverage from the documented design. |
| Finlex rendered-page current-text fallbacks | **Fragile; medium confidence** | Two current law pages use rendered `main` text, and three use a page-specific Finnish RSC extractor. ELI identity, statutory markers, section counts, full-body thresholds, raw hashes and deterministic offline replay are recorded. These dynamic page routes require manual review when the publisher changes the page structure; they are fallbacks for the identified records, not a whole-library updater. |
| Finlex unofficial English translation PDFs | **Sustainable with limits; medium confidence** | The rule reopens each publisher translation-history page, validates title/completion/cutoff, rediscovers its English PDF link, validates PDF type/signature and act identity, stores hash-named page/PDF responses, and replays conversion offline. A new cutoff or page structure stops for manual record review; the translations remain unofficial and stale after their recorded cutoffs. |
| Finlex daily bulk packages | **Not adopted** | Official package totals are multi-gigabyte and update daily; no sustainable per-record selection/update procedure has been proven. |

The earlier discovery assessment remains useful for search coverage and the other source classes. No local content is accepted by a successful request, conversion, current ELI date, or metadata status. External-reference acceptance is recorded separately in `source-acceptance.json`.
