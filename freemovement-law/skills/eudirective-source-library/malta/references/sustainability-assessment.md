# Malta source-rule sustainability assessment (2026-10-19)

## Scope and results

The 48-record inventory covers legislation and reuse, EU/EEA/Swiss free movement, third-country family routes, procedure and appeals, visas and missions, forms, data protection, oversight, legal aid, civil-status evidence and case-law discovery. The bounded capture pass retrieved and converted 47 records as unaccepted review candidates; the Judiciary portal root returned HTTP 403. Twenty-one responses differed from the earlier pass and revised Markdown remains staged under temp/malta/pending/. No source is accepted.

All 44 conversions pass offline verification: exact raw-source hashes, preserved PDF hashes and deterministic Markdown replay. Original PDFs are retained under temp/. PDF extraction used pinned pypdf 6.21.1; this does not validate signatures or OCR image-only pages.

## Implemented routes

- Legislation: known LEĠIŻLAZZJONI MALTA ELI records have official /pdf representations. Ordinary HTTPS GET returned actual application/pdf files for the identified laws and procedure instruments. The manifest preserves the ELI record URL separately from the PDF request URL. Current-version status and amendment relations still need a freshness check.
- Official HTML: Identità, Foreign Affairs, Legal Aid, Ombudsman and IDPC pages use the shared allowlisted HTTPS capture helper. It checks redirects, caps responses at 24 MiB, uses a 25-second timeout and one-second spacing. It converts page text but does not capture complete link graphs.
- PDFs: exact response bytes are preserved and extracted page by page with pypdf. The old Commission Annex route and a dated representation-agreement attachment were replaced with official versions described below.

## Source-specific findings

### Legislation and reuse

The normal Malta legislation ELI links returned HTML portal navigation rather than the legal text. Their official /pdf representations returned the actual PDFs. This source-specific retrieval adjustment captures legal content rather than portal chrome.

The three initial Identità 404s were resolved from current official parent pages: the EU-family parent links a July 2026 Form F.02, the third-country family FAQ now uses the non-eu-non-employment route, and the British Nationals section links the current Withdrawal Agreement FAQ. The dated 1 October 2026 edition of Chapter 12 is a point-in-time version. For other acts, verify which current version the /pdf route serves, in-force status, publication/effective dates, amendments, rectifications and consolidation dates. Chapter 546, amended in 2025 ([official text](https://legislation.mt/eli/cap/546/eng/pdf)), is relevant to reuse, but it does not establish that every portal document, database, image or attachment is reusable on identical terms. Record publisher and content-specific reuse conditions before bulk redistribution.

### Free movement and separate routes

Identità groups EU, EEA and Swiss nationals in some practical guidance, while the Free Movement Order defines its own legal scope. The candidate set did not establish a separate Swiss treaty implementation route. Keep EU, EEA EFTA, Swiss, mobile-Maltese-family and UK Withdrawal Agreement lanes distinct until each legal basis is verified. Third-country sponsor family reunification remains separate from EU-family residence.

### Visa sources and attachments

EUR-Lex reports 30 December 2025 as the current English consolidation of Regulation (EU) 2018/1806 ([consolidated record](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX%3A02018R1806-20251230); [base-act ELI](https://eur-lex.europa.eu/eli/reg/2018/1806/oj)). It includes the 2025 amendment and labels the consolidated text a documentary tool without legal effect. The earlier Commission-hosted 2024 Annex PDF returned HTTP 403, so the candidate now points to the versioned EUR-Lex PDF and retains the base-act ELI and current-version discovery URL. Refresh by checking the latest consolidated CELEX date and later Official Journal amendments or corrigenda.

The [Missions Malta visa FAQ](https://missions.foreign.gov.mt/visa-faqs/) still links to an Identità representation-agreement PDF under a 2025-04 path that now returns HTTP 404. A [September 2025 file](https://identita.gov.mt/wp-content/uploads/2025/09/VISA-Representation-Agreements.pdf) was found on Identità’s official host and preserved, but no parent-page link or newer edition was verified. Treat it as a review candidate, not a current mission map. Re-discover checklists and representation links from the current official parent pages.

### Procedure, oversight and courts

The earlier mt-13, mt-15 and mt-43 URLs returned 404. The current EU-family parent now links the [July 2026 Form F.02](https://identita.gov.mt/wp-content/uploads/2026/07/eu_nat_expats_FORM-F.02.pdf); the [third-country family FAQ](https://identita.gov.mt/frequently-asked-questions/expatriates/non-eu-non-employment/family-member/) and [British Nationals FAQ](https://identita.gov.mt/expatriates-unit-main-page/british-nationals/faqs/) were recaptured from their current routes. The Judiciary portal root, mt-44, still returned 403; this does not establish that court material is unavailable through every public channel.

The official [Judiciary FAQ](https://judiciary.mt/en/frequently-asked-questions/) says public online case records are restricted: people can search their own matters using eID, while other case files are obtained through the court registry and may involve fees. No public, complete judgments corpus or update feed was identified. Keep eCourts monitor-only; do not automate access to private files or infer a decision does not exist because it is not publicly searchable.

Privacy, Ombudsman and legal-aid pages were captured, but decision collection scope, appeal-specific legal-aid eligibility, versioning and completeness need separate verification.

## Sustainability judgment

- Known legislation ELI-to-PDF retrieval: sustainable with limits (medium confidence) for bounded known-record retrieval. Official ELI PDF routes are repeatable, and captures replay offline. Current-version and amendment checks and content-specific reuse review remain required.
- Official HTML guidance and forms: fragile (medium-low confidence). Captures replay, but 21 responses changed between passes; pinned child URLs can disappear, and page conversion does not discover parent-link, attachment or language changes.
- Visa attachments: fragile (low confidence). Both the old Annex PDF and the FAQ-linked representation list were blocked or missing. The replacements are dated; the parent-page link and latest-version signal remain unresolved.
- Court decisions: not currently sustainable as a public full-text feed (medium confidence). The direct portal request was blocked, and official guidance limits online case access; no public completeness/update feed was identified.
- Whole inventory: not ready for unattended current-law monitoring. Reproducible retrieval does not prove completeness, legal currentness or reuse permission.

## Actions before trust promotion

1. Refresh every legal ELI record for current status, version date, authentic Gazette publication, amendments, rectifications and annexes.
2. Confirm portal reuse notices and whether each law, page, PDF, image and database item is covered by the applicable Malta PSI Act or another licence.
3. Review the 21 changed HTML captures, compare visible dates and linked files, and preserve any new changes pending review.
4. Continue checking the three repaired Identità routes from their parent pages and preserve the old 404 URLs as audit evidence.
5. Resolve the dead representation-agreement link from a current Missions/Identità parent page; do not promote the September 2025 file without confirming it is still operative.
6. Refresh the EUR-Lex consolidation date and later Official Journal changes; preserve authentic amending acts alongside the documentary consolidation.
7. Keep eCourts limited to public metadata unless a public judgments feed, scope statement and reuse basis become available.
8. Verify legal-aid coverage for Immigration Appeals Board and judicial-review routes separately from general civil legal aid.
9. Rediscover mission directories, VFS/provider checklists and forms on each update and record each attachment’s version identity.
