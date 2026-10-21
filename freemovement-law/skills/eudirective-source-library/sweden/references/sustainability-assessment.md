# Sweden source sustainability assessment

**Reviewed:** 21 October 2026  
**Status:** official links are usable within the dated scopes in [source-acceptance.json](source-acceptance.json); issue coverage, consular practice, broad case-law discovery, and country review remain incomplete.

## New source gap closed in the tracked inventory

The current Migrationsverket catalog lists [MIGRFS 2026:12](https://www.migrationsverket.se/download/18.15b2309e1a04e5ed2071d69/1790835688522/MIGRFS_2026_12.pdf), an official one-page rule published and effective from 1 October 2026. It specifies the housing-size and standard part of the ordinary family-immigration maintenance requirement and repeals MIGRFS 2022:8. The rule is now included in [`manifest.json`](../manifest.json), so the existing optional updater resolves it by its MIGRFS number through the official catalog rather than relying on the dated PDF path. It does not govern EU/EEA residence-card applications absent a separate legal basis.

## Source route assessment

- **Riksdag SFS pages:** official consolidated text links display the amendment cutoff and link to the Government's full text and amendment register. The Aliens Act page displayed SFS 2026:1752; the Aliens Ordinance page displayed SFS 2026:1746; the Administrative Procedure Act displayed SFS 2025:582. These dated pages are sufficient working references within the provisions checked. No Gazette reconstruction is required by default.
- **Migrationsverket MIGRFS:** the official catalog lists current and archived rules and links to the current PDFs; it also provides RSS. The optional script checks pinned MIGRFS identifiers against this catalog and reports untracked entries for review. The PDF route can change, so the catalog is the stable discovery page.
- **Courts:** four identified Migration Court of Appeal cases are tracked. Domstolsverket describes Sök rättspraxis as an appellate search service populated with new decisions from 4 March 2025; pre-2025 decisions are available across individual court websites to varying degrees, while case summaries date from 1981. Search and RSS support ongoing discovery, but the tracked cases and service do not establish broad migration-law coverage.
- **Operational guidance:** the reviewed Migrationsverket pages are trustworthy official references within their recorded route and check date. Their live pages do not consistently show a page revision date; recheck operational details and the case-specific decision before reliance.

## Route distinctions and dependencies

- Keep EEA family residence, the Swedish citizen's return route, the Swiss family permit route, ordinary family immigration linked to Swedish citizens, and the UK Withdrawal Agreement chapter separate.
- The return route depends on the free-movement conditions identified in CJEU O. and B. Migrationsverket summarizes the returning-Swedish condition as residence of at least three months; this assessment does not decide whether that operational summary resolves every fact pattern.
- MIGRFS 2026:12 depends on the statutory national-family housing requirement in Utlänningslagen 5 kap. 3 j § and its enabling provision in Utlänningsförordningen. Keep it outside the EU residence-card route unless a separate rule applies.
- Förvaltningslagen §12 gives a limited request-to-decide mechanism for an individual-initiated case undecided at first instance after six months. Special migration provisions may prevail; it is not a general appeal against delay.

## Still missing

- A route-by-route legal crosswalk for EU/EEA family, return cases, Swiss family, ordinary Swedish-family permits, and Withdrawal Agreement cases.
- Mission-specific visa instructions, forms, appointment and outsourcing routes, fees, and submission channels. The pack has one Istanbul mission page, so the whole [Sweden Abroad site](https://www.swedenabroad.se/en/) is offered for human review.
- A systematic search across relevant immigration decisions and courts, including pre-2025 court-site material; a topic-led review of the four pinned cases' holdings and procedural posture.
- A current review of Migrationsverket's forms, evidence checklists, fees, and route-specific instructions. The whole [Migrationsverket site](https://www.migrationsverket.se/en/) is offered for human review because the current pages are live, operational guidance and the site inventory is incomplete.
- Provision-level mapping of party access, language/translation, evidence, decision reasons, appeal routes, interim relief, privacy, JO/IMY oversight, and remedies.
- Evidence that GitHub Actions or another scheduled job is enabled and running successfully; this was not checked.

The pack now tracks the newly identified MIGRFS rule, but the source inventory is not a statement that all relevant Swedish texts or practices have been found. No local copy, topic, or country review is accepted here.
