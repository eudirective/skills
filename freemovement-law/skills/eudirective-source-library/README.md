# EU source retrieval library

The reusable national-pack layout is documented in [the country-pack template](templates/country-pack/LAYOUT.md). The latest structural inventory is in [the folder audit](references/library-folder-audit-2026-10-19.md). The shared English EU corpus serves every pack; country-level `core/` folders are kept only when they contain actual official EU-language files. Ireland and Malta use that shared corpus for English instead of duplicating English files.

### Source edition and review policy

Use the responsible official publisher for every source class. Prefer a usable government-published consolidation for national laws and the responsible EU publisher's consolidation for EU laws; if none is available, use the closest usable official version and record its date/cutoff, language, and limits. Do not reconstruct Gazette amendment chains by default. A human-reviewed official link is sufficient for ordinary research; capture, conversion, hashes, and automated updates are optional unless a retained copy or recurring monitoring is needed. See the [source selection and review policy](references/legal-text-edition-policy.md). Accepted counts describe local artifacts only, not usable references or topic coverage.

This local library is a derived retrieval workspace. Its expanded core inventory is `core-source-pack-manifest-0.7.0.json` (69 logical records / 70 total representations); [`shared-core-index-EN.json`](shared-core-index-EN.json) maps the 69 English representations to their local files and current retrieval-index hashes. The English index records 46 differences from baseline manifest hashes rather than treating them as unchanged; those local files remain unaccepted artifacts, while their official links can still be reviewed directly. The historical skill bundle remains at 0.6.0 and the protected project `sources/` mirror is unchanged.

This library stores legal source corpora and their retrieval and maintenance support for the plugin skills. Module-scoped research summaries are kept separately in [`../module-notes/`](../module-notes/README.md); they are not authoritative legal texts or hash-pinned source snapshots. The historical C1 compatibility fixture is kept separately in the `eudirective/skills` repository at `freemovement-law/skills/eudirective-core/tests/fixtures/core-source-pack-0.6.1/`; it is used only for synthetic replay, not as current legal content. Current retrieval results belong in each installation's persistent plugin `data/` directory.

The 0.6.0 baseline contains 46 logical records / 47 representations. The 0.7.0 library manifest adds 18 CJEU judgments and five EU regulations; CJEU full texts remain under `sources/case_law/full_text/`, Commission/Ombudsman operational notes under `sources/guidance/notes/`, and EU legal material under `sources/eu/`.

### How the inventory counts work

Counts in this overview use different units and should not be compared as if they were all converted files. An EU **logical record** is a source instrument or case; a **representation** is one language/file for that record. A national pack's **monitored target** is a manifest entry checked by its updater; some targets are discovery-only or monitor-only and do not produce Markdown. A **converted document** is a saved Markdown output. Guidance records are counted in their separate guidance lane. Specifically, Hungary has 58 NJT law references that are human-reviewed only, alongside its separate OIF/NAIH/AJBH maintenance sources; Romania has 79 monitored targets, of which 71 produce Markdown and eight are monitor-only. Language-mirror totals count representations, not additional logical EU instruments.

Transient working files, reports, update state, pending conversions, and atomic-write staging files are stored under the project-root `temp/` directory. Its subfolders mirror the source-pack paths; `runtime-storage.mjs` maps those paths to the shared temp tree. A country pack may retain documented source bytes and derived replay inputs under its own `captures/raw/` and `captures/derived/` folders when reproducibility or audit evidence requires durable artifacts. Accepted Markdown and source manifests remain in their corpus packs.

## EU case law and legislation additions

The 11 October 2026 gap review is maintained by [`sync-core-expansion.mjs`](sync-core-expansion.mjs). It retrieves only the 23 unique English sources from the official EUR-Lex host, follows EUR-Lex's current-consolidation link for consolidated regulations, saves content-addressed raw HTML in project-root `temp/`, converts the official document body to Markdown directly under `core/`, and records source and Markdown SHA-256 hashes. `node sync-core-expansion.mjs sync` checks for content changes, changed consolidation identities, and new CELEX references linked from these records; changed conversions are staged under project-root `temp/` for review. `node sync-core-expansion.mjs verify` checks each saved raw and Markdown hash and replays conversion byte-for-byte without network access.

The candidate list named C-225/19 and C-226/19 separately, but EUR-Lex publishes their joined judgment under CELEX 62019CJ0225. One full-text representation covers both case numbers. The 23 additions comprise 18 judgment records and five regulations. All are retrieved and converted; the new library records are not trust-promoted into the separately pinned 0.6.0 skill bundle. Each addition has a locally stored, identity- and language-validated counterpart in HU, SV, DA and RO. HU and DA each passed all 23 live checks; SV and RO each passed 19 live checks, with four prior official conversions retained after the latest live responses failed validation. All 92 language files pass offline replay verification.

The English EU core files are under `core/`, grouped as `core/eu/`, `core/case_law/notes/`, `core/case_law/full_text/`, `core/guidance/notes/`, and `core/guidance/handbooks/`. The Visa Code Handbook is guidance. The Swedish representation of Commission Recommendation 2013/461/EU is under `sweden/core/eu/`, retrieved from the official Publications Office XHTML by `node sync-swedish-recommendation.mjs sync|verify`; the prior invalid English clone was removed. The source index maps the 47 representations to their actual library files. Retrieved Markdown remains a conversion candidate; the original trust hashes in the core manifest were not silently changed.

The previously saved official-language inventory contains 39 Hungarian, 42 Swedish, 44 Danish, and 36 Romanian counterparts among the original 46 English core items. With the 23 additions, the library now contains 62 HU, 65 SV, 67 DA, and 59 RO counterparts across the 69 logical English sources. The four retained SV additions remain locally stored and pass offline verification; their latest live recheck did not validate. The per-language indexes record retrieval status and update checks.

Hungarian, Swedish, Danish and Romanian counterparts that pass language validation are mirrored directly under `hungary/core/`, `sweden/core/`, `denmark/core/` and `romania/core/` using the same source-type subfolders and language suffixes. For the 23 additions, run `node sync-core-expansion-languages.mjs sync --language <LANG>` with `HU`, `SV`, `DA` or `RO`, or run `node sync-core-expansion-languages.mjs sync --all`; run `node sync-core-expansion-languages.mjs verify` to check raw/Markdown hashes and replay conversions offline. Each `national-language-index-<LANG>.json` records the latest check and each `national-language-state-<LANG>.json` stores that language's accepted content hash per source. Changed text is staged under project-root `temp/` for review. A localized page shell that returns another language does not count as a translation. These are derived candidates outside the trusted source manifest; CJEU translations identify the language of the case and are not substitutes for that authentic-language version.

`retrieval-index.json` records official source URLs, manifest and library paths, source representation kinds, observed byte/conversion hashes, and retrieval status. Run `node organize-core.mjs` here to place English EU core files in their type-specific folders and update the library paths without changing file contents or trust metadata. The base maintainer can scan EN or SV independently; HU, SV, DA and RO each have separate official-language retrieval and update state. Run `node ../eudirective-core-work/eudirective-core/scripts/national-language-maintenance.mjs --language HU|SV|DA|RO --library .` to refresh the selected language. A successful conversion, host match, or hash does not establish legal completeness, trust, or exact pinpoints. Review the official linked source before legal reliance.

Swedish national laws, Migrationsverket regulations, and Migration Court of Appeal sources from the Swedish legal pack are maintained separately under [`sweden/`](sweden/README.md). Run `node sweden/sync.mjs --check` to retrieve and hash-pin official response snapshots without changing accepted Markdown, `node sweden/sync.mjs --sync` to refresh accepted files and stage detected text changes, or `node sweden/sync.mjs --verify` to replay all conversions offline from retained official bytes. This lane is distinct from `sweden/core/`, which holds Swedish-language EU materials.

The superseded Visa Code Handbook I (C(2020) 395) language-reference pack is under [`visa-code-handbook-i-2020/`](visa-code-handbook-i-2020/manifest.json). The [official Commission document register](https://ec.europa.eu/transparency/documents-register/detail?ref=C(2020)395&lang=en) publishes its annex in 23 languages. All 23 official PDFs and converted Markdown files are saved locally and replay-verified; the Markdown files are together in `accepted/`, with language codes in their filenames. The register has no Irish (`GA`) annex for this decision. From the core skill directory run `node scripts/visa-handbook-language-reference.mjs inventory|sync|verify`. `sync` checks the register's language IDs and the official visa-document catalogue for later editions. This 2020 edition is a language reference; the 2024 Handbook I remains current.

The 42 added official-guidance records are stored in their owning target folders: 14 in [`denmark/documents/guidance/`](denmark/SKILL.md), 12 in [`sweden/documents/guidance/`](sweden/README.md), 10 across Romania's [`documents/guidance/`](romania/documents/README.md), `documents/forms/`, and `documents/procedure/`, and 6 in `core/guidance/official/`. The Danish, Swedish, and Romanian national packs are sibling country folders, each with its own inventory and update lane. Romania's 79 monitored national targets include 71 converted documents now under `romania/documents/` and eight monitor-only entries; the separate guidance lane adds 10 documents. Its 14 categorized case-law follow-up records include three reproductions/digests labeled secondary. The Romanian EU-language mirror remains under `romania/core/`, in the corresponding `eu/`, `case_law/`, and `guidance/` subfolders. Raw source bytes, state, reports, and pending conversions are kept under project-root `temp/`; reviewed accepted Markdown is written directly to its manifest-recorded target folder. `verify` replays accepted files and pending candidates offline. From this directory run `node sync-guidance.mjs sync|verify|ack SOURCE_ID` for the EU guidance lane; country packs expose the same commands through their wrappers. The active 46-record EU legal manifest is unchanged.

## Czech national source pack

The candidate inventory for Czech national sources is under [`czechia/`](czechia/README.md). It contains 43 records: 17 legal texts, 13 official guidance/index pages, and 13 monitor/discovery pages. All 43 local conversions replay against captured bytes; 0 local copies are accepted. That storage status does not prevent human-reviewed use of official links within their displayed scope. The page-data service is an optional local-copy route; the API-key-gated REST route is not used. See the Czechia assessment for version and coverage limits.


## Online acquisition candidates

The [2026-10-15 online acquisition candidate register](references/online-acquisition-candidates-2026-10-15.md) records 83 additional official-source candidates compared with current EU and national inventories. It is a discovery register; its candidates are not retrieved or accepted legal texts.


### National acquisition expansion

The [2026-10-16 candidate extension for Portugal, Spain, France, the Netherlands, Belgium and Italy](references/national-acquisition-candidates-2026-10-16.md) applies the current acquisition taxonomy to six additional countries. It contains 39 source candidates.

The six-country register contains 39 scoped source leads. Retrieval includes 39 Belgian, 15 Spanish BOE law and 30 broader Spanish monitor conversions; 49 Dutch monitor pages and eight scoped law/guidance pages; 19 replay-verified Portuguese monitor pages (plus 27 shells and 14 errors) and six scoped DRE pages that returned an application shell; and 33 Italian monitor pages in addition to three Normattiva statute copies. These are local-copy candidates. France yielded 17 guidance/catalogue conversions but no local statute text; bulk DILA extraction is optional for retaining or monitoring copies, while human-reviewed official law links remain usable. A raw France-Visas capture is not required to use the official page as a reference. See [Portugal](portugal/README.md), [Spain](spain/README.md), [France](france/README.md), [the Netherlands](netherlands/README.md), [Belgium](belgium/README.md), and [Italy](italy/README.md).

The Spain register now includes the 46-record monitor dossier alongside the earlier seven-record national inventory (four records overlap). The official BOE open-data route has retrieved and converted 15 identified legal texts into unaccepted review candidates. A separate ordinary-HTTPS monitor pass saved 34 exact responses and converted 30 mixed candidate pages; four discovery pages had no stable text body, and 12 routes failed. The BOE API returns consolidated text by stable identifier; raw XML is retained under project-root `temp/`, with hashes and offline conversion replay documented in [`spain/`](spain/README.md). No Spanish local copy is accepted into the trusted library yet. This does not disqualify a human-reviewed official BOE link as a source within its displayed scope; candidate captures are not trusted local artifacts.



## Estonia source candidates

The [Estonia candidate inventory](estonia/references/candidate-manifest.json) contains 42 candidates across legislation, residence, guidance and forms, visas and missions, administrative procedure, remedies, privacy, oversight, and courts. Twenty-one identified legal-text records have full-text conversions, including 13 unique current Estonian acts, exact editions of two regulations and one future Act wording, and 16 dated English editions. Twelve English source leads also have a linked current Estonian text. All 33 legal-text artifacts remain unaccepted and pass offline hash and conversion replay; 17 additional official pages were converted. Wider source coverage remains pending. See the [Estonia README](estonia/README.md), [sustainability assessment](estonia/references/sustainability-assessment.md), and [31-jurisdiction expansion ledger](references/eea-switzerland-country-expansion.md).

## Finland source pack

The [Finland source catalog](finland/references/source-catalog.json) contains 36 candidates across statutes, guidance, forms, visas, procedure, appeals, courts, privacy, oversight and legal aid. Eleven legal texts are saved as unaccepted review candidates: eight current Finnish statutes and three unofficial English translations with recorded amendment cutoffs. Finlex's no-registration Akoma Ntoso API returned XML for Acts 808/2019, 1050/2018 and 616/2019, but HTTP 404 for the current consolidated-text requests checked for five other acts. The Aliens Act and Administrative Procedure Act use official current-text pages; the Openness, Language and Legal Aid Acts use a page-specific extractor for the Finnish text embedded in Finlex's React Server Component stream. That fallback is fragile and stops when identity, ELI, heading or body checks change. The 808/2019 XML has a specific conflict between its consolidation date and a listed amendment effective date; that provision-level version limit remains unresolved. A full amendment-chain review is not required. All 11 legal conversions pass offline hash and replay verification. See the [Finland README](finland/README.md), [sustainability assessment](finland/references/sustainability-assessment.md) and [31-jurisdiction expansion ledger](references/eea-switzerland-country-expansion.md).

## Austria national-source candidates

The [Austria register](austria/references/candidate-manifest.json) contains 74 official source records. As of 19 October 2026, 73 retained records pass the local-artifact acceptance checks and one family-topic index is discovery-only; this local count does not establish topic or country completion. The review still has open legal and operational coverage work, including broad court-search completion and mission/Land procedures. See the [Austria README](austria/README.md) and [sustainability assessment](austria/references/sustainability-assessment.md).

## Germany federal-law candidates

The [Germany inventory](germany/references/candidate-manifest.json) contains 47 candidates. Eighteen statutory records from 17 official Gesetze im Internet XML packages and 26 additional official pages/PDFs are converted as unaccepted review candidates; two discovery pages returned shells and one BfJ URL returned 404. All 44 conversions replay offline. Use the official consolidated texts as the legal-text source; resolve the specific AufenthG amendment the publisher flags as not fully processed, rather than requiring issue-by-issue Bundesgesetzblatt reconstruction. See the [Germany README](germany/README.md) and [sustainability assessment](germany/references/sustainability-assessment.md).

## Italy national-source candidates

The [Italy scoped inventory](italy/references/candidate-manifest.json) contains five prioritized sources, alongside a wider 42-record monitor inventory. Three current Normattiva statutes are captured through 200 article responses and converted as unaccepted full-act candidates; their per-article source hashes and offline conversion replay are recorded. The broader monitor pass added 33 replay-verified page conversions, including PDF conversions that need visual text-quality review. The official URN links are stable, but the article-loading interface is undocumented and rated fragile. Direct automated retrieval of the two MAECI guidance pages redirects to a Radware challenge; one older English capture remains without currentness proof. See the [Italy README](italy/README.md) and [sustainability assessment](italy/references/sustainability-assessment.md).

## Latvia national-source candidates

The [Latvia register](latvia/references/candidate-manifest.json) contains 49 candidates. The direct capture pass converted 41 official HTML pages and two PDFs to unaccepted Markdown; six discovery or case-law repository routes remain monitor-only. The PDF extractions are replayable. Current identity of the PMLP form, individual decisions, publisher arrangements for recurring capture, and update coverage remain open. A Gazette signature check is needed only if relying on that file's seal. See the [Latvia README](latvia/README.md) and [sustainability assessment](latvia/references/sustainability-assessment.md).


## Lithuania national-source candidates

The [Lithuania register](lithuania/references/candidate-manifest.json) contains 44 candidates across laws, guidance, forms, visas and missions, procedure, remedies, courts, privacy, oversight and legal aid. Thirteen records were converted from the official TAR API and two official pages were converted; one court-search surface was captured, while 28 routes returned HTTP 403 or had no matching API version. Some API version fields conflict with current e-TAR evidence; use those dated snapshots with the recorded limit and resolve only a conflict material to the provisions in scope. See the [README](lithuania/README.md) and [sustainability assessment](lithuania/references/sustainability-assessment.md).

## Liechtenstein national-source candidates

The [Liechtenstein register](liechtenstein/references/candidate-manifest.json) contains 40 candidates across laws, guidance, forms, court and oversight material. Sixteen official HTML pages were converted as unaccepted review candidates, two PDFs were preserved without text extraction, and 16 requests returned HTTP 403; staging, interactive-form and case-law-app limitations are recorded separately. Offline replay passes for all 16 conversions and both PDF hashes. No locally stored artifact has been accepted, and reuse conditions and legal-authenticity checks remain unresolved. See the [README](liechtenstein/README.md) and [sustainability assessment](liechtenstein/references/sustainability-assessment.md).

## Malta national-source candidates

The Malta register contains 48 candidates. Forty-seven were retrieved and converted to unaccepted review candidates; only the Judiciary portal root returned 403. Three stale Identità URLs were resolved through current parent pages. All conversions replay offline. Known legislation now uses the official ELI PDF route; the old visa Annex link was replaced with a versioned EUR-Lex consolidation. Mission attachment currentness and reuse terms remain unresolved. See the Malta README and sustainability assessment.

## Norway national-source candidates

The [Norway register](norway/references/candidate-manifest.json) contains 54 sources. Lovdata’s documented no-auth publicData list/get route is implemented for current laws, central regulations, and the current-year national Gazette archive. Thirty-two candidates have source bytes and 31 have converted Markdown; five changed outputs are staged for review, all saved conversions replay offline, and 0 are accepted. Local Avdeling II coverage is unavailable from the listed packages; 20 UDI/Regjeringen routes returned 403 in this environment. See the [README](norway/README.md) and [sustainability assessment](norway/references/sustainability-assessment.md).

## Luxembourg national-source candidates

The [Luxembourg register](luxembourg/references/candidate-manifest.json) contains 42 candidates. Thirty-eight were retrieved and 35 were converted from official LegalDocML, HTML and PDF sources; three portal shells had no source text, and four routes returned 404. Offline replay passes for all conversions. The Casemates XML route is sustainable with limits for known ELI records; direct HTML and PDF monitoring remain fragile. No locally stored artifact has been accepted. See the [README](luxembourg/README.md) and [sustainability assessment](luxembourg/references/sustainability-assessment.md).

## Switzerland federal-law candidates

The [Switzerland register](switzerland/references/candidate-manifest.json) contains 44 candidates. Twenty-eight Fedlex and direct-page routes were configured: 27 exact responses were saved, 26 were converted into unaccepted review candidates, one Fedlex discovery page was only a JavaScript shell, and one configured court-search page failed TLS verification. HTML conversions replay offline; one SEM PDF was converted through Adobe Acrobat and has hash-integrity checks but no local replay. No locally stored artifact is accepted. Current legal versions and the 16 unconfigured candidates still need resolution; see the [README](switzerland/README.md) and [sustainability assessment](switzerland/references/sustainability-assessment.md).

## Iceland source candidates

The [Iceland register](iceland/references/candidate-manifest.json) has 28 candidates. The shared bounded page capture saved 21 responses and converted 20 local review copies; offline replay passes. Six Althingi requests returned 403, one court publication-rules URL returned 404, and one Ombudsman page had no extractable text. The official Althingi archive index lists edition 158a; the unresolved SGML route affects local capture, while the dated official index can be reviewed as a source reference. See the [README](iceland/README.md) and [sustainability assessment](iceland/references/sustainability-assessment.md).





## Cyprus candidate pack

The [Cyprus register](cyprus/references/candidate-manifest.json) contains 90 records. Ten local artifacts have narrow acceptance, including two complete Protocol No. 10 text representations; 12 bounded passages are accepted, but no topic or country review is complete. Direct current-text review of government-published Law 7(I)/2007 and Cap.105 remains open because the recorded OLC routes are inaccessible; local retention is optional. A full Gazette-by-Gazette reconstruction is not required; use the closest government-published text and check only material post-cutoff or commencement issues. See the [README](cyprus/README.md), [completion report](cyprus/references/completion-status-report.md), and [sustainability assessment](cyprus/references/sustainability-assessment.md).

## Croatia candidate pack

The [Croatia register](croatia/references/candidate-manifest.json) tracks 75 records: 17 accepted sources, 30 converted review candidates, 25 located uncaptured leads, one no-text discovery surface and two excluded stale-source leads. The 41/40 capture count describes the original seed batch; two MVEP pages were captured separately. Use the closest government-published version and record its date and limits; do not assemble every Gazette fragment. Topic and country completion remain open. See the [README](croatia/README.md) and [sustainability assessment](croatia/references/sustainability-assessment.md).

## Bulgaria candidate pack

The [Bulgaria register](bulgaria/references/candidate-manifest.json) has 35 candidates. The shared bounded capture converted and replay-verified 24 texts; 11 requests remain unresolved: four MFA links redirected to a third-party bot-validation host, five failed TLS validation, one returned HTTP 500, and one returned 404. Use the MVR Visa Ordinance text through April 2019 as the closest located government version, record that cutoff, and consult the identified 2025 decrees only where relevant; no full amendment reconstruction is required. See the [README](bulgaria/README.md) and [sustainability assessment](bulgaria/references/sustainability-assessment.md).


## Greece candidate pack

The [Greece register](greece/references/candidate-manifest.json) has 56 candidates. Forty texts converted and replayed offline; 16 requests failed (14 HTTP 403 and two TLS errors). No locally stored artifact is accepted. The Gazette route works for known items. Publisher copying/conversion terms remain unresolved; use the closest government-published legal version and record its cutoff without requiring a full amendment inventory. See the [README](greece/README.md) and [sustainability assessment](greece/references/sustainability-assessment.md).


## Slovenia candidate pack

The [Slovenia register](slovenia/references/candidate-manifest.json) has 42 candidates. All 42 responses were saved; 23 converted and replayed offline, while 19 were shells or dynamic discovery pages. Use PISRS consolidated law pages as the government-published working versions and note their displayed editions and informational labels; Gazette reconstruction is not required. The developer API remains authorization-gated, and automated copying terms remain separate. See the [README](slovenia/README.md) and [sustainability assessment](slovenia/references/sustainability-assessment.md).

## Slovakia candidate pack

The [Slovakia register](slovakia/references/candidate-manifest.json) has 40 candidates. Fifteen date-bound Slov-Lex laws were captured with their binding PDFs and eleven linked annex PDFs; 16 additional guidance, directory, court, or oversight pages were converted. All 31 candidate-text conversions passed offline replay. Eight MFA retrievals returned HTTP 403. The dynamic archive page links to a static year register visible in browser research, but its exact-byte local capture is pending after a workspace DNS failure. No locally stored artifact is accepted; consolidated-text reuse terms remain unresolved. See the [README](slovakia/README.md) and [sustainability assessment](slovakia/references/sustainability-assessment.md).

## Poland candidate pack

The [Poland register](poland/references/candidate-manifest.json) now contains 54 candidates. The official ELI API and listed public publisher pages yielded 51 saved responses and 50 replay-verified conversions; seven PDFs used pinned pypdf 6.21.1. ELI current-act search found newer consolidated texts DU/2026/1065 and DU/2026/44, retained alongside earlier editions. Three requests failed, and the e-Konsulat portal had no extractable text body. No locally stored artifact is accepted. See the [README](poland/README.md), [source list](poland/references/source-list.md), and [sustainability assessment](poland/references/sustainability-assessment.md).

## 31-jurisdiction candidate inventory

The [EEA and Switzerland expansion ledger](references/eea-switzerland-country-expansion.md) now reconciles all 31 jurisdiction folders: 27 dated candidate inventories plus established Denmark, Hungary, Romania, and Sweden packs. It records 1,203 candidate entries across the current inventories; entries are not all full texts and are not accepted. Review, lawful retrieval, and conversion status remains explicit per source.

The [Hungary pack comparison](references/hungary-comparison-2026-10-19.md) documents which parts of its source and update approach transfer to the expansion. NJT consolidated texts remain human-reviewed government references; the updater excludes NJT retrieval and catalogue polling under the recorded portal terms. Gazette amendments are targeted supplements, not a routine reconstruction workflow.
