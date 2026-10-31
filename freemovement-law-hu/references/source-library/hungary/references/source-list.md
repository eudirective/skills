# Hungary source list

This source list reconciles the Hungarian national material in `hungary laws and OIF data.zip` with official publishers. The supplied ZIP has five relevance tiers. EU-law and CJEU entries are maintained by the shared EU packs, not copied here.

## Legislation

The statutory registry in `manifest.json` lists 59 legal records. Fifty-eight existing NJT records retain historical local review files but are manual-only; Act I of 2010 on civil registration is recorded as link-only and is not an updater target. The inventory covers free movement and applications, procedure and remedies, records management, public-data access, data protection, fees and address records, digital administration, immigration context, social security, civil status, private international law, and supporting legal context.

Primary publisher: [Nemzeti Jogszabálytár](https://njt.jog.gov.hu/). Use its official current consolidated pages as human-reviewed source references and record the displayed version. Under the recorded portal terms, the updater does not fetch, store, or poll NJT law content.

### Current official law references reviewed by link

- [Act I of 2007 on free movement and residence](https://njt.jog.gov.hu/jogszabaly/2007-1-00-00) — NJT consolidation displayed 1 October 2026.
- [Government Decree 113/2007 implementing Act I of 2007](https://njt.jog.gov.hu/jogszabaly/2007-113-20-22) — NJT consolidation displayed 7 October 2026.
- [Act I of 2010 on civil-registration procedure](https://njt.jog.gov.hu/jogszabaly/2010-1-00-00) — NJT consolidation displayed 1 October 2026; link-only source.
- [Act CL of 2016 on general administrative procedure](https://njt.jog.gov.hu/jogszabaly/2016-150-00-00) — NJT consolidation displayed 1 October 2026; record ID corrected to `hu-act-2016-150`.
- [Act I of 2017 on administrative court procedure](https://njt.jog.gov.hu/jogszabaly/2017-1-00-00) — NJT consolidation displayed 1 October 2026.

The NJT user manual identifies the official operator and says the public service publishes the queried day's effective law in consolidated form. These are official link references only: no local copies are accepted, and statutory-link acceptance does not establish topic coverage.

## OIF procedures, records, and public data

Official routes pinned in the manifest include OIF's EEA registration certificate and residence-card process, current forms catalogue, procedure fees, electronic administration, public-information procedure, data-protection regulation, information-transfer rules, organisational rules, current public-data/organisation/procurement catalogue pages, and archive-listed historic publications. Twelve OIF migration-statistics booklets (2013–14, 2014–16, and 2017–25), six historical contract registers (2020–23, September 2024, and June 2025), and the 2026 over-5-million-forint contract register are retrieved from official OIF pages as PDFs. The archive's `106-Ált-201/2026` statistical file corresponds to OIF's 2025 annual migration-statistics booklet, pinned as `oif-statistics-2025`. The archive's `106-TI-6332/2026` file is a contract disclosure, not a statistics report; it corresponds to the 2026 contract register pinned as `oif-contracts-2026`.

The archive also contains OIF's 2023 annual report on public-information requests under Infotv. § 30(3). Its official PDF is pinned as `oif-foi-annual-report-2023`. OIF's current transparency publication table, item X.5, now links its 2025 annual report under Infotv. § 71/D(4); that newer statutory report is pinned separately as `oif-foi-annual-report-2025`. These are the transparency-law statistical reports, distinct from the migration-statistics booklet and the contract disclosure. Their official filenames, direct URLs, catalogue pages, and archive mappings are recorded in `manifest.json`. The statistics, contract, procurement, public-data, and organisation catalogue pages are checked for new or changed editions. New yearly files are reported as discovery candidates and must be pinned before they enter the accepted corpus.

Primary publisher: [Országos Idegenrendészeti Főigazgatóság](https://oif.gov.hu/). OIF's public-data landing pages are dynamic catalogues; discovered file links are reported with their originating page and URL. The source ZIP's July 2026 dataset is a historical snapshot, not a live source.

## Data protection, FOI, and remedies

The source archive's NAIH procedure guidance is pinned from official NAIH pages, including data-subject rights, GDPR authority and investigation procedures, law-enforcement-data procedures, FOI requests, and FOI investigations. AJBH catalogue pages remain discovery-only and are scanned during discovery runs. Three direct AJBH documents are accepted as official link references: the [2024 equal-treatment booklet](https://www.ajbh.hu/documents/10180/160450/T%C3%A1j%C3%A9koztat%C3%B3%2Bf%C3%BCzet_2024.pdf/37e09aa0-bc59-c2ac-ba81-767b67bfb8d7?t=1711035444903&version=1.0), the [2025 public-interest and whistleblowing guide](https://www.ajbh.hu/documents/10180/160450/T%C3%A1j%C3%A9koztat%C3%B3%2Bf%C3%BCzet_2025.pdf/3e2af0a4-9b3c-ee2e-73cd-3777c857c2af?t=1747998995496&version=1.0), and the equal-treatment directorate disclosure. They are link-only, not retrieval candidates; the currentness of their procedures and channels is offered for whole-site human review. The 2025 guide is not an individual complaint or appeal form. The official case-law channels are [Kúria decisions search](https://kuria-birosag.hu/hu/kuriai-dontesek-kereses) and the [national courts' decisions collection](https://eakta.birosag.hu/anonimizalt-hatarozatok). Individual domestic decisions require a verified official record before addition.

## Shared EU sources and non-authoritative archive files

- CELEX texts and CJEU cases from archive tiers 01–04 belong to the existing EU core and supported language mirrors; use those source IDs.
- The Hungarian domestic case-law research and regression-audit Markdown are researcher notes, not court decisions.
- User-uploaded diagrams, workbooks, conversion output, logs, and archive provenance files are not legal authority and are not converted into source documents.
- No Swedish or Danish national-language version is included in this Hungary lane.

## Retrieval boundary

The manifest keeps 58 existing Hungarian Acts, decrees, and ministerial instruments as manual NJT references and includes Act I of 2010 as link-only. The online updater excludes NJT law records, NJT catalogues, and the three accepted AJBH link-only documents. It maintains 41 non-link-only OIF/NAIH/AJBH records; newly found links remain separate candidates until reviewed. The saved state contains 99 records, matching the 58 historical NJT review captures plus 41 online sources. `manifest.json` maps supplied archive labels to official OIF records even where filenames differ.

<!-- source-identity-inventory:start -->
## Source identity crosswalk

Canonical rows: **9**; provisional unique IDs: **9**; unresolved entries: **0**. This crosswalk preserves catalogue IDs, links external-reference and local-artifact representations to a source identity, and keeps acceptance status separate.

| Existing entry ID | Canonical source identity | Resolution | Representations | Catalogued statuses | Status record IDs |
|---|---|---|---|---|---|
| `ajbh-equal-treatment-directorate` | `hu:url:99937eeb61dc1d88cde5` | resolved | official_reference/hu/undated | accepted_external_reference | — |
| `ajbh-equal-treatment-request-procedure-2024` | `hu:url:aec7e13cc428212cf563` | resolved | official_reference/hu/2024 edition | accepted_external_reference | — |
| `ajbh-public-interest-whistleblowing-guide-2025` | `hu:url:d27a8faf4680aeb15390` | resolved | official_reference/hu/2025 edition | accepted_external_reference | — |
| `hu-act-2007-1` | `hu:url:53b9cf4bd18d970ee581` | resolved | local_artifact/hu/2007 (`documents/laws/free-movement-core/hu-act-2007-1.md`)<br>official_reference/hu/2026 | accepted_external_reference, pending | — |
| `hu-act-2010-1` | `hu:url:6b74c17906955984f831` | resolved | official_reference/hu/2026 | accepted_external_reference | — |
| `hu-act-2016-150` | `hu:url:6546886af7b5e3f99d18` | resolved | local_artifact/hu/2016 (`documents/laws/administrative-procedure/hu-act-2016-150.md`)<br>official_reference/hu/2026 | accepted_external_reference, pending | — |
| `hu-act-2017-1` | `hu:url:66d29db04361039d24b1` | resolved | local_artifact/hu/2017 (`documents/laws/administrative-court-procedure/hu-act-2017-1.md`)<br>official_reference/hu/2026 | accepted_external_reference, pending | — |
| `hu-act-2023-25` | `hu:url:d2fd3841960b10d6d32f` | resolved | local_artifact/hu/2023-25 (`documents/laws/complaints/hu-act-2023-25.md`)<br>official_reference/hu/2026 | accepted_external_reference, pending | — |
| `hu-gov-2007-113` | `hu:url:676251842e0b540668b9` | resolved | local_artifact/hu/2007 (`documents/laws/free-movement-core/hu-gov-2007-113.md`)<br>official_reference/hu/2026 | accepted_external_reference, pending | — |
<!-- source-identity-inventory:end -->
