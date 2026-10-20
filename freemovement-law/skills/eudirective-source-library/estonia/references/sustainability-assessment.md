Skill: assess-source-rule-sustainability v0.2.0

# Estonia source-route sustainability assessment

Status date: 19 October 2026

State: 42 candidates; 21 identified legal-text records converted, plus 12 current Estonian consolidations linked to English source leads; zero locally stored copies accepted. The 33 legal-text artifacts are unaccepted review candidates and pass offline replay.

## Assessment boundary

The 42 records in [source-catalog.json](source-catalog.json) cover official legislation and discovery portals, EU/EEA/Swiss residence, forms, visa and mission routes, general procedure, remedies, privacy, oversight, access to information, legal aid, and courts. Search outcomes and version doubts are recorded independently of source relationships and retrieval status. The count is a bounded research register, not a claim that Estonia's source universe is complete.

The current-law rule is implemented and exercised against Riigi Teataja's official APIs for 13 unique Acts. Exact-version XML covers two identified regulations and one future-effective Act edition; exact-version English HTML covers 16 identified translation editions. Other source groups remain discovery-only or monitor-only unless stated below.

## Strongest proposed route: Riigi Teataja

Riigi Teataja's official FAQ says published acts are available as XML, individually and in bulk. It documents a date-bound act search and recommends consolidated wording as the default. The FAQ records that on 1 June 2026 the act XML route changed to `https://www.riigiteataja.ee/public-api/api/v1/akt/{ID}/xml`; the old `/akt/{ID}.xml` route was discontinued. The search endpoint supports pagination, with a maximum page size of 500. The FAQ does not state an API-registration requirement.

The implementation queries the official law list for a requested effective date, follows each 500-result page, selects an exact Estonian title, retains the returned global ID and validity period, then retrieves that exact XML. It validates date, title, document type, and text identity; caps response size; restricts redirects to the official host; saves content-addressed raw bytes; and deterministically converts the hierarchy to Markdown. The 19 October 2026 run resolved 13 distinct current national acts, including IDs `130062026103` (Aliens Act) and `130062026048` (Citizen of the European Union Act). It also retrieved the two exact regulation IDs and the future EU-citizen-act edition from their candidate records. Sixteen English records were fetched from the publisher's `blob-html` route and their own metadata retained; many are expired editions. All 33 artifacts pass source-hash and conversion-replay checks.

**Current Estonian XML route: sustainable with limits (medium confidence).** Official documentation, dated discovery, exact version lookup, pagination, XML identity checks, and deterministic replay are demonstrated across 13 acts. It is now a repeatable update rule for the identified acts, not proof that the inventory contains every relevant instrument. Reuse conditions and rate limits need fuller confirmation. **Exact English HTML route: fragile (medium-low confidence).** The public publisher endpoint returned full article bodies and edition metadata for all 16 identified records, but its stability and terms are less clearly documented. Keep English editions version-specific and separate from current Estonian law. The JavaScript page shell itself is not used as an extraction fallback.

## Version selection is a critical dependency

The Citizen of the European Union Act illustrates why “latest published” cannot be used as “current”:

- The official Estonian consolidated wording published on 3 June 2026 is marked not yet in force until 31 October 2029.
- The newest English translation located reflects wording effective from 1 September 2025; a different English page is expressly marked in force only through 26 April 2025.
- An implementing regulation is shown in force from 1 January 2026, but that does not resolve the Act's own current Estonian wording.
- Other current-looking English links also surfaced with ended validity periods: the September 2026 Aliens Act wording ended on 30 September, the cited May 2026 administrative-court-code wording ended on 11 June, and the Public Information Act English result displayed wording ending 31 August 2025.
- The located State-funded Legal Aid Act wording ended on 5 July 2025, and the current replacement was not identified in this bounded search.

A future rule must query the publisher for the exact assessment date and preserve both currently operative and future-effective versions as distinct records. It must not infer currentness from a high publication date, a `consolide/current` path, or the latest search-engine result. English translations should be treated as language mirrors with their own publication and validity evidence; Estonian is the controlling text.

## Proposed route findings

| Source group | Maturity | Proposed route and evidence | Main unresolved sustainability issue |
|---|---|---|---|
| Current Estonian national acts | Converted local-copy candidates | Thirteen unique current acts resolved through exact-title date search and exact XML; all IDs and validity intervals checked and replayed offline | Local copies remain unaccepted pending proportionate review; the finite target-title list needs periodic expansion from publisher indexes; reuse terms matter for recurring or bulk copying |
| Exact Estonian editions and implementing regulations | Converted review candidates | Two regulation editions and one future-effective Act edition downloaded from exact official document IDs; XML identity and body checked | Exact records preserve their own version dates and must not be substituted for current wording |
| English legal editions | Converted review candidates | Sixteen exact official `blob-html` records preserve article body, publisher metadata, translation date, and in-force period | Several source URLs labeled as current leads resolve to expired English editions; endpoint stability and reuse terms need confirmation; Estonian is controlling |
| Ministry residence guidance and linked forms | Discovery-only | Re-fetch official parent pages and resolve links for notices, forms, and EU-residence instructions | Ministry terminology conflicts with the statutory “right of residence”; page/form dates and local-government differences need reconciliation |
| MFA visa and mission practice | Discovery-only | Re-discover visa instructions, representation lists, mission pages, appeal information, and linked forms from official MFA indexes | Dynamic mission/provider links and fees can change; no link-change detector or supported form extraction exists |
| Procedure, remedies, oversight, privacy, and access to information | Discovery-only | Date-resolve statutes and revisit official Ministry, Chancellor, and Data Protection Inspectorate guidance separately | Several English legal editions are stale or ambiguous; procedural deadlines and filing-language constraints need current first-party cross-checks |
| Administrative courts and decisions | Discovery-only | Use the current Code, administrative-court information pages, and official judgment portals as separate sources | Decision publication may be redacted or restricted; English summaries are selective; no complete corpus or bulk route was established |
| Online application services | Monitor-only candidate | Keep the MFA application portal as a route reference only | It accepts personal data and is not suitable for automated submission or case-data collection |

## Material guidance conflict

The Ministry of the Interior's population-register page correctly explains that EU citizens submit a residence notice to the relevant city or rural municipality and links to the Citizen of the European Union Act. It also describes temporary and permanent EU residence rights as “residence permits,” while the Act and implementing regulation use “right of residence.” This is a material terminology and accuracy conflict. The ministry page should remain a review lead until its wording is reconciled; do not convert its wording into an operative rule.

## Optional work for retained copies or recurring monitoring

The listed API, reuse, and conversion checks apply to a local-copy or recurring-monitor workflow. They do not gate a human-reviewed official Riigi Teataja page or use of its displayed version within scope.

1. Use the latest government-published Estonian consolidation for the relevant date and record its displayed validity. Keep future-effective editions and English translations distinct. Check named later changes only when they may affect the provisions in scope; do not reconstruct full amendment chains.
2. Confirm reuse terms, request limits, rate limits, maximum payload expectations, and any registration requirement from official publisher documentation.
3. Expand the exact-title set from official source indexes when new candidate laws are identified; keep the date-bound search and explicit document-type/publisher identity checks, and record future-effective versions separately.
4. Review relevant provisions in the current Administrative Procedure, Administrative Court Procedure, fees, public-information, data-protection, and legal-aid texts. Follow a specific later amendment or commencement condition only when it may affect the question; otherwise record the publisher's displayed version and limits.
5. Verify the residence-guidance terminology conflict with the Ministry and rediscover application forms from official parent indexes. Add link/date change tracking for MFA mission and provider routes.
6. Retrieve and assess procedure, remedies, privacy, oversight and court-decision sources through their own official channels; do not assume the Gazette law rule applies to them.
7. Add only public source pages and form definitions. Never automate submissions to the e-visa portal or ingest applicants' personal data.
8. Before acceptance, review scope and attribution against official sources and verify the dated retrieval and offline conversion record.

## Coverage limits

The broader 42-record capture produced 17 page conversions; source-specific Riigi Teataja APIs resolved the identified legal texts whose ordinary pages were only JavaScript shells. A remaining 403 route, textless discovery surfaces, PBGB residence guidance, a complete form catalogue, and a complete court-decision corpus remain unresolved. No bounded-search gap proves that no source exists. All legal and page conversions remain unaccepted; no completeness claim is made.

