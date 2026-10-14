# Hungary source list

This source list reconciles the Hungarian national material in `hungary laws and OIF data.zip` with official publishers. The supplied ZIP has five relevance tiers. EU-law and CJEU entries are maintained by the shared EU packs, not copied here.

## Legislation

The fixed statutory registry is `manifest.json`. It covers free movement and applications (Act I of 2007; Decree 113/2007; OIF forms under Decree 9/2024), procedure and remedies, records management, public-data access, data protection, fees and address records, digital administration, immigration context, social security, civil status, private international law, and supporting legal context.

Primary publisher: [Nemzeti Jogszabálytár](https://njt.jog.gov.hu/). The pack uses NJT's official ELI URIs for acts and ministerial instruments and the official current consolidated pages for government decrees. Every retrieved instrument is checked against its Hungarian citation before conversion.

## OIF procedures, records, and public data

Official routes pinned in the manifest include OIF's EEA registration certificate and residence-card process, current forms catalogue, procedure fees, electronic administration, public-information procedure, data-protection regulation, information-transfer rules, organisational rules, current public-data/organisation/procurement catalogue pages, and archive-listed historic publications. Twelve OIF migration-statistics booklets (2013–14, 2014–16, and 2017–25), six historical contract registers (2020–23, September 2024, and June 2025), and the 2026 over-5-million-forint contract register are retrieved from official OIF pages as PDFs. The archive's `106-Ált-201/2026` statistical file corresponds to OIF's 2025 annual migration-statistics booklet, pinned as `oif-statistics-2025`. The archive's `106-TI-6332/2026` file is a contract disclosure, not a statistics report; it corresponds to the 2026 contract register pinned as `oif-contracts-2026`.

The archive also contains OIF's 2023 annual report on public-information requests under Infotv. § 30(3). Its official PDF is pinned as `oif-foi-annual-report-2023`. OIF's current transparency publication table, item X.5, now links its 2025 annual report under Infotv. § 71/D(4); that newer statutory report is pinned separately as `oif-foi-annual-report-2025`. These are the transparency-law statistical reports, distinct from the migration-statistics booklet and the contract disclosure. Their official filenames, direct URLs, catalogue pages, and archive mappings are recorded in `manifest.json`. The statistics, contract, procurement, public-data, and organisation catalogue pages are checked for new or changed editions. New yearly files are reported as discovery candidates and must be pinned before they enter the accepted corpus.

Primary publisher: [Országos Idegenrendészeti Főigazgatóság](https://oif.gov.hu/). OIF's public-data landing pages are dynamic catalogues; discovered file links are reported with their originating page and URL. The source ZIP's July 2026 dataset is a historical snapshot, not a live source.

## Data protection, FOI, and remedies

The source archive's NAIH procedure guidance is pinned from official NAIH pages, including data-subject rights, GDPR authority and investigation procedures, law-enforcement-data procedures, FOI requests, and FOI investigations. AJBH's official equal-treatment guidance URLs are identified, but AJBH currently presents a bot-detection challenge to scripted requests, so those four documents are registered as archive follow-up targets and excluded from the successful-conversion count. The local automated updater does not pretend those blocked records were retrieved. The official case-law channels are [Kúria decisions search](https://kuria-birosag.hu/hu/kuriai-dontesek-kereses) and the [national courts' decisions collection](https://eakta.birosag.hu/anonimizalt-hatarozatok). Individual domestic decisions require a verified official record before addition.

## Shared EU sources and non-authoritative archive files

- CELEX texts and CJEU cases from archive tiers 01–04 belong to the existing EU core and supported language mirrors; use those source IDs.
- The Hungarian domestic case-law research and regression-audit Markdown are researcher notes, not court decisions.
- User-uploaded diagrams, workbooks, conversion output, logs, and archive provenance files are not legal authority and are not converted into source documents.
- No Swedish or Danish national-language version is included in this Hungary lane.

## Retrieval boundary

All registered Hungarian Acts, Government decrees, and ministerial instruments now have pinned NJT routes and are checked against their citations before conversion. Annual NJT issue catalogues and official OIF/NAIH catalogues are crawled for candidate new records; discovery never silently accepts a new law, consolidated text, or publication. `manifest.json` maps supplied archive labels to the official OIF records even where the official filenames differ. The live report records the resolved source ID and catalogue matches. Remaining archive follow-up targets are limited to sources whose publisher blocks automated access. State advances only after a fully successful sync.
