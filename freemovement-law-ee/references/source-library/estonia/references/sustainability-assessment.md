Skill: assess-source-rule-sustainability v0.2.0

# Estonia source-route sustainability assessment

Status date: 25 October 2026

State: 53 source records: 32 accepted local legal-text editions, 18 official operational/court links accepted only as external references, and three discovery-only routes. Thirty-three saved legal-text acquisitions produced 32 distinct local documents after one duplicate Aliens Act acquisition was consolidated. Fifteen local editions fall within publisher validity on 25 October 2026. Zero topics are accepted; the country review remains incomplete.

## Assessment boundary

The 53 records in [source-catalog.json](source-catalog.json) cover official legislation, discovery routes, EU/EEA/Swiss residence, forms, visa and mission routes, general procedure, remedies, privacy, oversight, access to information, legal aid, and courts. Thirty-two records have accepted local texts; 18 operational/court pages are external-only references; three portal routes remain discovery-only. Three statutory link decisions overlap accepted local texts and are counted separately in source-acceptance. Search outcomes and version doubts remain separate from source acceptance and country coverage. This is a bounded research register, not a claim that Estonia's source universe is complete.

The current-law rule was exercised against Riigi Teataja's official APIs for 13 unique Acts. Exact-version XML covers two identified regulations and one future-effective Act edition; exact-version English HTML covers 16 identified translation editions. The official English Administrative Procedure Act edition remains in force through 31 December 2026; the other 15 translations are historical on the review date. Seventeen unaccepted monitoring snapshots are retained in the Monitor's local-only archive. Other source groups remain open.

## Strongest proposed route: Riigi Teataja

Riigi Teataja's official FAQ says published acts are available as XML, individually and in bulk. It documents a date-bound act search and recommends consolidated wording as the default. The FAQ records that on 1 June 2026 the act XML route changed to `https://www.riigiteataja.ee/public-api/api/v1/akt/{ID}/xml`; the old `/akt/{ID}.xml` route was discontinued. The search endpoint supports pagination, with a maximum page size of 500. The FAQ does not state an API-registration requirement.

The implementation queries the official law list for a requested effective date, follows each 500-result page, selects an exact Estonian title, retains the returned global ID and validity period, then retrieves that exact XML. It validates date, title, document type, and text identity; caps response size; restricts redirects to the official host; saves content-addressed raw bytes; and deterministically converts the hierarchy to Markdown. The 19 October 2026 run resolved 13 distinct current national Acts, including IDs `130062026103` (Aliens Act) and `130062026048` (Citizen of the European Union Act). It also retrieved two exact regulation IDs and the future Citizen Act edition. Sixteen English records were fetched from the publisher's `blob-html` route with their own metadata retained. The 33 acquired legal-text artifacts pass offline source-hash and conversion replay; the 32 accepted documents' legal bodies match those replays. Raw responses and the retrieval ledger are preserved in the Monitor local-only archive and in the standard temporary archive. Seventeen page observations are also archived locally: 16 correspond to official operational references, and one is the N-Lex discovery route. Two accepted official routes have no saved page snapshot.

**Current Estonian XML route: sustainable with limits (medium confidence).** Official documentation, dated discovery, exact version lookup, pagination, XML identity checks, and deterministic replay are demonstrated across 13 Acts. The accepted local text is a reviewed representation of the captured official response, not proof that the inventory contains every relevant instrument. Reuse conditions and rate limits need fuller confirmation. **Exact English HTML route: fragile (medium-low confidence).** The public publisher endpoint returned full article bodies and edition metadata for all 16 identified records, but its stability and terms are less clearly documented. Keep English editions version-specific and separate from controlling Estonian wording. The JavaScript page shell itself is not used as an extraction fallback.

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
| Current Estonian national acts and regulation | Accepted dated local texts | Thirteen Act consolidations plus the residence-procedure regulation were validated against exact official IDs, published status, full-text type, validity and article anchors; the complete bodies replay offline | The finite title set needs periodic expansion from publisher indexes; later versions require a fresh dated check; reuse terms matter for recurring or bulk copying |
| Exact future and historical Estonian editions | Accepted as version-specific local texts | The future Citizen Act edition and expired residence-data regulation preserve their exact publisher IDs and stated validity | Do not substitute these editions for current wording |
| English legal editions | Accepted version-specific translations | Sixteen exact official `blob-html` records preserve article bodies, publisher metadata, translation date, and in-force period | Fifteen editions are historical on the review date; endpoint stability and reuse terms need confirmation; Estonian is controlling |
| Ministry residence guidance and linked forms | External reference only | Use the accepted official page links within the source acceptance register's narrow scope; refresh forms and child links before reliance | Ministry terminology conflicts with the statutory “right of residence”; page/form dates and local-government differences need reconciliation |
| MFA visa and mission practice | External reference only | Use official MFA links as dated operational references; refresh instructions, representation lists, mission pages, appeal information, and linked forms before reliance | Dynamic mission/provider links and fees can change; no link-change detector or supported form extraction exists |
| Procedure, remedies, oversight, privacy, and access to information | External reference only | Use the accepted official links for the limited page scopes; date-resolve statutes and recheck official guidance separately | Several English legal editions are stale or ambiguous; procedural deadlines and filing-language constraints need current first-party cross-checks |
| Administrative courts and decisions | External reference only | Use court information and decision-search links as discovery routes; review each individual decision before relying on its holding | Decision publication may be redacted or restricted; English summaries are selective; no complete corpus or bulk route was established |
| Online application services | External reference only | Keep the public MFA application portal link as a route reference only | It accepts personal data and is not suitable for automated submission or case-data collection |

## Material guidance conflict

The Ministry of the Interior's population-register page explains that EU citizens submit a residence notice to the relevant city or rural municipality and links to the Citizen of the European Union Act. It also describes temporary and permanent EU residence rights as “residence permits,” while the Act and implementing regulation use “right of residence.” This is a material terminology and accuracy conflict. Human review remains open before operative use; do not convert the disputed wording into an operative rule. The Tallinn service reference is also held for human review before operative use because the direct page returned HTTP 403 in the research viewer and the current parent index was not established. Its link remains external-only and local to Tallinn.

## Optional work for retained copies or recurring monitoring

The listed API, reuse, and conversion checks apply to a local-copy or recurring-monitor workflow. They do not gate a human-reviewed official Riigi Teataja page or use of its displayed version within scope.

1. Use the latest government-published Estonian consolidation for the relevant date and record its displayed validity. Keep future-effective editions and English translations distinct. Check named later changes only when they may affect the provisions in scope; do not reconstruct full amendment chains.
2. Confirm reuse terms, request limits, rate limits, maximum payload expectations, and any registration requirement from official publisher documentation.
3. Expand the exact-title set from official source indexes when new relevant laws are identified; keep the date-bound search and explicit document-type/publisher identity checks, and record future-effective versions separately.
4. Review relevant provisions in the current Administrative Procedure, Administrative Court Procedure, fees, public-information, data-protection, and legal-aid texts. Follow a specific later amendment or commencement condition only when it may affect the question; otherwise record the publisher's displayed version and limits.
5. Verify the residence-guidance terminology conflict with the Ministry and rediscover application forms from official parent indexes. Add link/date change tracking for MFA mission and provider routes.
6. Retrieve and assess procedure, remedies, privacy, oversight and court-decision sources through their own official channels; do not assume the Gazette law rule applies to them.
7. Add only public source pages and form definitions. Never automate submissions to the e-visa portal or ingest applicants' personal data.
8. For a later text update, use the Monitor's local-only capture archive, review scope and attribution against the official source, and replay the accepted body through `sync_estonia_legal_texts.py verify` before replacing any document.

## Coverage limits

The bounded 53-record catalog includes 32 accepted local legal texts, 18 official operational/court links accepted only as external references, and three discovery-only routes. A remaining 403 page response, textless publisher surfaces, PBGB residence guidance, a complete form catalog, and a complete court-decision corpus remain unresolved. Seventeen page observations remain in the Monitor local-only archive; they are research evidence, not accepted local copies. The Tallinn page and court-decision search route were accepted from bounded official-domain/portal evidence without a saved page snapshot. No bounded-search gap proves that no source exists, and no completeness claim is made.


## Official-reference review addendum — 21 October 2026

Three official Riigi Teataja links remain accepted for direct reference within their displayed dates and scopes: the Aliens Act (record 130062026103, valid 1 October–31 December 2026), the Citizen of the European Union Act (record 130062026048, valid 1 October 2026–31 December 2027), and the VSS (record 130062026110, valid 1 October–31 December 2026). Each XML record was retrieved again on 21 October; the two current Act responses and VSS response match the 19 October raw hashes. Their local texts are now separately accepted, with independent artifact hashes and scope records. See [source-acceptance.json](source-acceptance.json).

The current Citizen Act record must be kept separate from record 103062026006, a published full-text edition whose validity begins on 31 October 2029. The VSS link is needed alongside the Citizen Act: § 1(1¹) of the Citizen Act expressly applies VSS departure and entry-ban provisions to EU citizens and family members subject to stated exceptions. VSS § 1(2) applies the Administrative Procedure Act to its administrative procedure, but excludes entry-ban procedure; the current procedural-law sources and remedies still need a separate review.

The Riigi Teataja [FAQ](https://www.riigiteataja.ee/kkk) documents the current-text link form `?leiaKehtiv` and the XML API introduced on 1 June 2026. Use exact-version URLs as the dated evidence and the publisher’s dynamic link form for a link intended to open the version currently in force. The page renderer exposed a JavaScript-only shell to the research viewer, so the exact official XML API responses and the official FAQ search result were used for this review.

The EU-citizen residence-procedure regulation uncertainty is resolved by the saved official XML: record `125042025013` reports `dokumentStaatus=avaldatud`, document type `määrus`, full-text type `terviktekst`, and validity beginning 1 January 2026. The accepted local edition remains date-bound and does not expand topic coverage.

The inventory retains 53 source records across legislation, guidance, forms, visas and missions, procedure and remedies, privacy, oversight, legal aid, and courts. Thirty-two local legal texts and 18 external-only operational/court references are accepted within recorded scopes; three statutory external-link decisions overlap these local texts; three routes remain discovery-only. Seventeen research observations remain in the Monitor local-only archive. No topic or country review is accepted. In particular, the Administrative Procedure Act dependency, administrative remedies, current legal-aid wording, mission procedures, forms, competent-authority practice, and case-law discovery remain open.
