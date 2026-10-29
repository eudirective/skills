# Latvia official-source discovery register

Skill: author-source-pack-rules v1.0.1

Research date: 18 October 2026  
State: EU Member State  
Comparison seed: Denmark EU free-movement residence regulation and guidance  
Scope: bounded discovery across official law/publication, free movement and immigration, forms, visa and consular routes, procedure/access, remedies, privacy/oversight, legal aid and courts. Prior country findings were carried forward as discovery leads and adapter lessons only.

**External-reference review (29 October 2026):** 48 of 52 official source records are accepted as links within stated scope and date limits; 4 remain pending and 0 stale or unverified records are not relied upon. **Local-copy review (24 October 2026):** 30 source text snapshots are accepted under `documents/` after exact-capture replay and per-record scope review. Thirteen other converted candidate texts and the old PMLP PDF are preserved in the Monitor’s local-only archive and are not accepted. The two PDFs remain byte-for-byte preserved: OP 2026/119.1 is stored under `documents/` with its text extraction, while the PMLP form is archived as unaccepted. Six discovery/repository records have no individual text. Issue-led review added the Declaration of Place of Residence Act, Law on the Register of Natural Persons, and Civil Status Act as external-only references. These decisions do not establish topic coverage or country completion. See the [source acceptance register](source-acceptance.json), [issue-led coverage register](coverage-register.md), and [dependency register](dependency-register.json). The [source manifest](candidate-manifest.json) records each source and link decision; the [capture manifest](latvia-captures.json) records local paths, hashes, and archived candidate dispositions.

## Material 2026 status findings

- Latvia’s new EU/EEA/Swiss family and residence law (No. 369282) took effect on 10 July 2026. It expressly identifies EU, EEA and Swiss citizens, family members, mobile Latvian citizens, and UK Withdrawal Agreement beneficiaries. New Cabinet procedures are due by 1 December 2027. The Act’s transitional text directs applications filed before commencement to Regulation 675, while the official Regulation 675 record itself displays an end-of-validity date of 2 December 2027. The scope of Regulation 675 for applications filed on or after 10 July 2026 remains unresolved; do not assume it is either fully current or wholly obsolete.
- The PMLP central EU/EEA/Swiss page was updated on 17 July 2026 and refers to the new law. Several linked checklist, filing and document pages pre-date it. The MFA EU-family page was updated on 17 June 2026 and still cites Cabinet Regulation 675. Treat that as a verified stale-guidance conflict, not as current procedure.
- A separate new Immigration Law was adopted 20 August 2026 and took effect 15 September 2026. Keep it distinct from free-movement law; some provisions start on 31 December 2027. Reconcile PMLP third-country family guidance and forms against the in-force provisions.
- The new free-movement Act’s English record says the State Language Centre has not officially translated its text. Latvian-source conversion and translation boundaries need to remain explicit.

## Source register

### National Law Discovery

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-01 | [N-Lex Latvia country information](https://n-lex.europa.eu/n-lex/info/info-lv/index) | related_source | Official N-Lex country information page inspected; its description of Latvijas Vēstnesis and Likumi.lv was checked. | N-Lex identifies Latvijas Vēstnesis as the official Gazette and Likumi.lv as publisher-managed systematic legislation access. Discovery lead only; N-Lex is not the national source publisher and does not cover all requested classes. |

### Official Legislation Portal

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-02 | [Likumi.lv official legislation portal — about and version information](https://likumi.lv/about.php) | related_source | Official Likumi.lv about page inspected. | Publisher says current, historic and future wording, validity status, related documents and English translations are provided. Systematised text is informational; the official Gazette prevails in case of discrepancy. |

### Publisher Terms

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-03 | [Likumi.lv terms of service](https://likumi.lv/par-mums/portala-lietosanas-noteikumi) | related_source | Full official terms page fetched directly and converted in the capture pass; the earlier research-client open had timed out. | Section 6 says systematised acts are available for reuse under the public-information laws and applicable Cabinet-set fees, and the keeper organizes reuse. Links may be placed with attribution. This is a legal route, but does not itself confirm an unattended recurring monitor or its delivery method. See the [accepted local text snapshot](../documents/guidance/lv-likumi-terms-of-service.md), lv-47 to lv-49, and the sustainability assessment. |

### Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-04 | [Law on Official Publications and Legal Information](https://likumi.lv/ta/en/en/id/249322) | related_source | Official Likumi.lv act page inspected in the bounded source review. | Act describes the official publisher role and the legal-publication framework for Latvijas Vēstnesis and systematised legal information. Use alongside the Gazette publication for legal force and the consolidated portal for version discovery. |

### Official Publication Integrity

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-05 | [Latvijas Vēstnesis official publication security information](https://www.vestnesis.lv/informacijas-drosiba) | related_source | Official publisher page directly fetched and converted. | Publisher states issue contents and each publication are also produced as PDF electronic documents, signed with the organisation electronic seal, with e-signature fallback. This describes the publisher's process; validate a specific file's seal only when authenticity of that exact PDF is material. |

### Free Movement Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-06 | [EU, EEA and Swiss citizens and family members entry/residence law (Likumi.lv consolidated record)](https://likumi.lv/ta/id/369282) | close_functional_match | Official current Likumi.lv act page inspected; scope, definitions, commencement and transition provisions checked. | Law 369282; adopted 11.06.2026, published 26.06.2026, effective 10.07.2026; page shows in force. Covers EU, EEA and Swiss citizens and family members, mobile Latvian citizens, and UK Withdrawal Agreement beneficiaries. Latvian-only substantive text; English page says State Language Centre has not officially translated it. Cabinet implementing rules are due by 01.12.2027. |

### Official Gazette Publication

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-07 | [Official Gazette publication OP 2026/119.1 — EU/EEA/Swiss residence law](https://www.vestnesis.lv/op/2026/119.1) | close_functional_match | Official Latvijas Vēstnesis publication page and linked PDF directly fetched; exact PDF bytes and page-wise text replay verified. | Stable OP identifier 2026/119.1; issue 119, 26.06.2026. The original PDF is stored with the [accepted text extraction](../documents/legislation/lv-gazette-op-2026-119-1.md). The promulgated text is not a substitute for checking the current consolidated text after later amendments. The PDF signature field was not cryptographically validated; check its seal only if authenticity of that exact file is material. |

### Historical Or Transitional Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-08 | [Cabinet Regulation No. 675 of 30 August 2011 — prior EU residence procedure](https://likumi.lv/ta/id/235499-kartiba-kada-savienibas-pilsoni-un-vinu-gimenes-locekli-iecelo-un-uzturas-latvijas-republika) | related_source | Official Likumi.lv record inspected through the new law transition link. | The 2026 Act directs pre-commencement applications to Regulation 675. The regulation’s official record separately says it remains in force until 02.12.2027. Its application to post-10.07.2026 filings is unresolved; do not treat the MFA page's old citation as resolving that issue. |

### Third Country Immigration Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-09 | [Immigration Law (new 2026 Act)](https://likumi.lv/ta/id/370622-imigracijas-likums) | related_source | Official current Likumi.lv act page inspected; document passport and commencement metadata checked. | Law adopted 20.08.2026, published 01.09.2026, effective 15.09.2026; record shows the current edition through 30.12.2027, with some provisions effective 31.12.2027. Separate this third-country route from EU/EEA/Swiss free movement. |

### Uk Withdrawal Agreement Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-10 | [UK Withdrawal Agreement implementation law](https://likumi.lv/ta/id/305836) | related_source | Official Likumi.lv act page reached through the new EU residence law transition link. | The new 2026 free-movement law expressly applies to UK nationals/family members covered by this Act. UK Withdrawal Agreement beneficiary route remains distinct from EU/EEA/Swiss nationality routes. |

### Administrative Procedure Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-11 | [Administrative Procedure Law](https://likumi.lv/ta/id/55567-administrativa-procesa-likums) | related_source | Official current Likumi.lv act page inspected; current amendment history checked. | Current record includes amendment adopted 28.05.2026, effective 01.06.2026. Covers procedure, evidence, access, review and administrative-court process. A high-value general procedure source; map provisions to each decision type and special migration rules. |

### Access To Information Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-12 | [Freedom of Information Law](https://likumi.lv/ta/en/en/id/50601) | related_source | Official English act page inspected. | Official English version selected from 01.05.2023; records access and reuse of public-sector information. General public-information access differs from an applicant’s access to their own administrative file. |

### Legal Aid Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-13 | [State-Provided Legal Aid Law](https://likumi.lv/ta/id/104831-valsts-nodrosinatas-juridiskas-palidzibas-likums) | related_source | Official current act page inspected; current text includes 2026 amendment history. | Amendments adopted 23.04.2026 have provisions effective 01.06.2026; links free legal aid eligibility and categories. Check applicability in each migration/court route; Immigration Law separately anticipates detention-extension legal aid provisions tied to future amendments. |

### Ombudsman Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-14 | [Ombudsman Law](https://likumi.lv/ta/id/133535-tiesibsarga-likums) | related_source | Official current act record inspected. | Law establishes national Ombudsman and individual submission/investigation powers; recent amendment effective 02.04.2025. General good-governance/human-rights oversight; not a substitute for statutory appeal deadlines. |

### Data Protection Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-15 | [Personal Data Processing Law](https://likumi.lv/ta/id/300099) | related_source | Official current act record inspected. | Current national data-protection law supporting GDPR implementation. Use with the DVI complaint procedure and GDPR; avoid personal case-data collection. |

### Law Enforcement Data Legislation

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-16 | [Personal data processing in criminal and administrative offence proceedings law](https://likumi.lv/ta/id/308278) | related_source | Official current act record inspected. | Separate Latvian act for processing by competent authorities for criminal and administrative offence purposes. Keep distinct from general GDPR and immigration/residence processing. |

### Court Publication Rules

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-17 | [Rules on publishing court information online and processing court decisions before release](https://likumi.lv/ta/id/187832) | related_source | Official current Likumi.lv result inspected; amendment dated 28.04.2026 identified. | Current rules direct court proceedings information to e-lieta and provide for public redaction; amended 28.04.2026. Court-publication regime changed in 2026; verify which decision classes are public and where before designing case-law monitoring. |

### Official Agency Guidance

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-18 | [PMLP: Entry of EU, EEA and Swiss citizens and family members](https://www.pmlp.gov.lv/en/entry-citizens-eu-eea-and-switzerland-and-their-family-members) | partial_functional_match | PMLP official page inspected; published/updated metadata and stated law references checked. | Updated 17.07.2026; after the new law took effect. It identifies current registration/permanent residence documents and non-EU family permits. Accepted local text snapshot of the current central overview. Reconcile linked document requirements/forms against the new law and outstanding Cabinet rules. |
| lv-19 | [PMLP: Documents required for EU citizen and family residence document](https://www.pmlp.gov.lv/en/what-documents-must-be-filed) | partial_functional_match | Main page and linked non-EU family-member list inspected 29.10.2026; date metadata and evidence categories checked. | Main page updated 24.07.2025; family-member page 19.06.2024; linked form 09.02.2026. See [maintained dated guidance](../documents/guidance/lv-19-pmlp-eu-family-documents.md). The detailed list predates the 10.07.2026 Act; post-commencement applicability is unresolved. |
| lv-20 | [PMLP: Where can residence documents be filed?](https://www.pmlp.gov.lv/en/where-can-documents-be-filed) | partial_functional_match | Official PMLP page inspected; publication/update metadata and filing routes checked. | Updated 05.02.2025. Describes e-signature, post, in-person and some embassy/representative filing routes. Pre-2026 guidance; verify against the new act, Cabinet rules, actual e-address/form workflow and mission-specific intake. |
| lv-23 | [PMLP EU residence document types and explanation](https://www.pmlp.gov.lv/en/what-residence-documents-are-issued-union-citizens-and-their-family-members) | related_source | Live English page and displayed dates checked 29.10.2026; maintained dated note at [lv-23](../documents/guidance/lv-23-pmlp-residence-document-types.md). | Published 23.01.2021; updated 24.07.2025. Accepted only as dated official guidance; its categories and conditions have not been reconciled against the Act effective 10.07.2026. |
| lv-24 | [PMLP information for UK Withdrawal Agreement beneficiaries](https://www.pmlp.gov.lv/en/information-brexit) | partial_functional_match | Official PMLP guidance page inspected in official search results. | Updated 24.07.2025; refers to WA residence rights and post-transition family procedures. Verify against the new law’s transition clause and the linked UK Act; distinguish protected beneficiaries from post-2020 entrants. |
| lv-25 | [PMLP: Declaration of place of residence](https://www.pmlp.gov.lv/en/declaration-residence-place) | related_source | Official PMLP page inspected; scope, channels and last-updated date checked. | Updated 03.06.2025; explains municipal/e-service/PMLP channels for persons with residence documents. Auxiliary operational obligation; validate law changes and Latvija.lv login/service route. |
| lv-27 | [PMLP: Identity number and declared residence for EU citizens](https://www.pmlp.gov.lv/en/article/how-obtain-personal-identity-number-and-declared-place-residence-latvia) | related_source | Live page and displayed date checked 29.10.2026; maintained dated note at [lv-27](../documents/guidance/lv-27-pmlp-personal-identity-number-and-residence.md). | Published 31.01.2022; no later update date displayed. Accepted as historical page content only. Do not rely on its 90-day registration statement; reconcile address/eID/citizenship links separately. |

### Official Forms Index

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-21 | [PMLP: Residence-permit application and form index](https://www.pmlp.gov.lv/en/application-requiring-residence-permit) | partial_functional_match | Official PMLP forms index inspected in official search results. | Updated 22.09.2026; list includes forms for third-country residence and the EU citizen/family residence document application. Parent index is preferable to a pinned file URL. Capture attachment label/date/hash and verify applicable form after the 2026 law. |
| lv-38 | [Data State Inspectorate: complaint and request form examples](https://www.dvi.gov.lv/lv/iesniegumu-paraugi) | related_source | Official DVI forms page inspected in official search results. | Complaint/request forms updated 11.02.2026; page sets secure e-signature/e-address routes. Attachment rediscovery and version identity should be parent-index based. |

### Application Form Pdf

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-22 | [PMLP EU citizen/family residence application form](https://www.pmlp.gov.lv/en/media/1666/download) ([current forms index](https://www.pmlp.gov.lv/en/application-requiring-residence-permit)) | partial_functional_match | Current PMLP index links an 8-page bilingual PDF updated 23.10.2026; full PDF reviewed 29.10.2026. Maintained paraphrased field map: [lv-22 form guide](../documents/forms/lv-22-pmlp-eu-family-residence-application-form.md). | Use the official PDF to apply; the Markdown is a field map, not the fillable form. Earlier /media/100 candidate was not linked from the current index and remains unaccepted. Check current law and PMLP instructions. |

### Official Fees Guidance

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-26 | [PMLP: State fees for residence permits](https://www.pmlp.gov.lv/en/state-fees-issuance-residence-permit) | related_source | Official PMLP page identified through current official search results. | Dynamic fees and processing-speed options; exact applicable EU-family fees need current route-specific confirmation. Fees change independently of core legislation and can vary by document/processing time; monitor the date and table identity. |

### Official Ministry Guidance

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-28 | [MFA: Entry into Latvia by Union citizens and family members](https://www.mfa.gov.lv/en/entry-latvia-citizens-union-and-their-family-members) | related_source | Live page checked 29.10.2026; maintained stale-guidance note at [lv-28](../documents/guidance/lv-28-mfa-eu-family-entry-stale-guidance.md). | Published 05.07.2021; updated 17.06.2026. Cites Regulation 675 after the new Act took effect 10.07.2026; accepted only as historical evidence of the MFA's guidance, not current procedure. |
| lv-29 | [MFA: Entry to Latvia information hub](https://www.mfa.gov.lv/en/entry-latvia) | related_source | Live hub and linked topic categories checked 29.10.2026; maintained index at [lv-29](../documents/guidance/lv-29-mfa-entry-hub.md). | Published 09.12.2024; updated 20.05.2026. Official navigation page only; child-page status is independent. EU-family link is covered by the lv-28 stale-guidance finding. |
| lv-30 | [MFA: Documents required to apply for a visa](https://www.mfa.gov.lv/en/documents-required-apply-visa) | related_source | Official MFA page identified in official search results. | Updated 17.06.2026. General Schengen visa source; EU-family visa exceptions under the new Act need a separate comparison. |

### Official Visa Guidance

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-31 | [PMLP: Visa-exempt nationalities and stay period](https://www.pmlp.gov.lv/en/list-countries-citizens-which-do-not-need-visas) | related_source | Official PMLP page inspected in official search results. | Updated 16.03.2026; list reflects Regulation (EU) 2018/1806 and national/other categories. Nationality-based, change-sensitive table; distinguish visa exemption from residence rights. |

### Consular Directory

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-32 | [MFA: Latvia’s embassies and consulates directory](https://www.mfa.gov.lv/en/latvias-embassies-and-consulates) | related_source | Official MFA page inspected through official search result. | Updated 09.06.2026; lists Latvia missions by country. Parent directory is a discovery route; individual mission rules and outsourced appointment services can differ and change. |

### Consular Representation Directory

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-33 | [MFA: Other Schengen missions representing Latvia for visas](https://www.mfa.gov.lv/en/diplomatic-and-consular-missions-other-schengen-member-states-issuing-visas-enter-latvia) | related_source | Official MFA page inspected in official search results. | Current list includes representation arrangements; page content varies by mission/country. Monitor by parent index and record each representative mission separately; do not assume all countries have a Latvian mission. |

### Third Country Family Guidance

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-34 | [PMLP: Family unification under general immigration route](https://www.pmlp.gov.lv/en/family-unification) | related_source | Live page and displayed dates checked 29.10.2026; maintained historical note at [lv-34](../documents/guidance/lv-34-pmlp-family-unification-stale-guidance.md). | Published 14.10.2020; updated 22.04.2022. Accepted as dated page content only; its criteria and EUR 500/EUR 150 amounts are not verified under the Immigration Law effective 15.09.2026. |

### Border Authority Information

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-35 | [State Border Guard official site — entry and border information](https://www.rs.gov.lv/en) | related_source | Homepage and five linked service pages reviewed 29.10.2026; maintained route map at [lv-35](../documents/guidance/lv-35-state-border-guard-entry-and-border-information.md). | Official authority/navigation reference only. Several linked pages cite superseded law or show historical content; no dedicated entry-refusal or appeal procedure was confirmed. |

### Oversight Complaint Route

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-36 | [Ombudsman of Latvia contact and submission channel](https://www.tiesibsargs.lv/en/contacts/) | related_source | Official Ombudsman contacts page inspected. | Describes e-signed/e-address and paper submission routes; current contact details are exposed. National human-rights/good-administration oversight. Submission contains personal data; monitor only public instructions, not submissions. |

### Privacy Complaint Route

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-37 | [Data State Inspectorate: complaint about personal-data processing](https://www.dvi.gov.lv/en/services/complaint-concerning-processing-personal-data) | related_source | Official DVI service page inspected in official search results. | GDPR complaint process and response time information exposed. Current procedural steps and electronic intake terms need direct inspection; do not process case submissions. |

### Official Legal Aid Guidance

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-39 | [Court Administration: state-provided legal aid information](https://www.tiesas.lv/lv/valsts-nodrosinata-juridiska-palidziba) | related_source | Official Court Administration page inspected. | Page states eligibility, categories including certain administrative court proceedings, and application route. Current criteria depend on law and court decision; not every immigration matter qualifies. |

### Official Legal Aid Forms

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-40 | [Court Administration: legal-aid application forms](https://www.ta.gov.lv/lv/juridiskas-palidzibas-sanemsanas-pieprasijuma-veidlapas) | related_source | Official Court Administration forms page inspected; dates and special appendices checked. | Page updated 20.06.2026; forms updated 19.06.2026, with a special appendix for deportable foreigners/international cases. Good parent index for dynamic form downloads; confirm new legal aid amendments and attachment versions. |

### Court Procedure Guidance

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-41 | [Court Administration: administrative cases and appeal process](https://www.tiesas.lv/lv/administrativas-lietas) | related_source | Official Court Administration procedure page inspected. | Updated 11.02.2026; addresses administrative claim venue, procedure and fees. Useful general appeal guidance; reconcile special-law deadlines and current court fees before relying on it. |

### Court Decision Repository

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-42 | [E-lieta anonymised court decisions and proceedings information](https://www.elieta.lv) | related_source | Official Court Administration FAQ and current court-publication rules identify e-lieta as the public route; the live database was not directly inspected. | Current rules amended 28.04.2026; public anonymised decisions are identified in the official FAQ. Search access, recurring discoverability, stable IDs, redaction, coverage and automated access limits remain unverified. |

### Supreme Court Case Law

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-43 | [Supreme Court / Senate case-law archive](https://www.at.gov.lv/lv/tiesu-prakse/judikaturas-nolemumu-arhivs) | related_source | Official Supreme Court case-law site and search guidance inspected in official results. | Senate archive has selected precedential decisions; official guidance distinguishes decisions in E-lieta and non-public/archive holdings. Selective corpus, multiple archive/search paths and historical coverage mean it is not a complete national case-law feed. |

### Constitutional Court Case Law

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-44 | [Constitutional Court case-law database](https://www.satversmestiesa.lv/en/data-base-case-law) | related_source | Official Constitutional Court database page inspected. | Page updated 19.01.2026; downloadable Citavi database file is dated 11.12.2023 and text is in Latvian. Material maintenance risk: parent page current but database file date is old; database requires external Citavi software. Court judgments are also separately published. |

### Official Gazette Archive

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-45 | [Latvijas Vēstnesis daily issue archive and act publication pages](https://www.vestnesis.lv/) | related_source | Official Gazette archive inspected through the 2026/119.1 publication. | Archive browses issues from 1993 onward; each target publication exposes its own OP identifier and PDF link. Accepted as an official source-of-record and discovery route; routine signature validation or replay is not required for use of current consolidated text links. |

### Legislation Change Discovery

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-46 | [Likumi.lv “newly published acts” RSS discovery surface](https://likumi.lv/) | related_source | Official page shows an RSS icon labelled “RSS Šodien publicēti tiesību akti”; the browser followed only the image asset, not the feed target. | Feed existence is suggested by official UI but feed URL, payload, coverage, retention and terms were not verified. Do not build a poller from the icon alone. Establish the actual feed target and compare its scope with Gazette issue search before use. |

## Search coverage and limits

Searches were made in Latvian and English against N-Lex, Likumi.lv, Latvijas Vēstnesis, PMLP, the Ministry of Foreign Affairs, the State Border Guard, the Ombudsman, the Data State Inspectorate, Court Administration, E-lieta, the Supreme Court and Constitutional Court. The class-by-class outcomes, native-language query strings and limits are in the source manifest under `search_coverage`.

No discovered source or source class is declared absent. The search did not establish all mission practices, full regional/municipal rules, every appeal route, all court decisions, all family-document rules, or completeness of amendments and forms. Use official first-party pages and exact versions for any later rule.

## Retrieval route observations

- Likumi.lv exposes current, historic and future versions, legal status, related records and search. Its own about page says the content is informational and the official Gazette prevails in discrepancies.
- Latvijas Vēstnesis provides stable OP identifiers and publication-specific PDFs; the official publisher says PDFs carry an organisational electronic seal (or e-signature fallback). The direct capture preserved the OP 2026/119.1 PDF bytes and page-wise text. A seal check is relevant only if a question depends on the authenticity of that specific PDF.
- Likumi.lv displays an RSS icon for newly published acts, but the research browser resolved only the icon image. The feed URL, scope and payload remain unverified. No official public API was found in the bounded search.
- Likumi.lv terms were fetched directly. They say systematised acts are available for reuse under the applicable public-information rules and fees and that the publisher organizes reuse. The official publisher separately requires written coordination, a stated purpose/product/service, and currently identifies grouped official notices as the supported public-interface route. A recurring legal-text monitor's availability, price and delivery format therefore require written confirmation.
- A repeat capture exposed volatile inline scripts, CSRF tokens and Drupal view IDs. The rule stores and hashes the exact raw response while ignoring only those identified values for comparison. All remaining HTML and link changes are still staged for review; exact PDF bytes are compared.
- The official Act remains Latvian-only on the English record. Agency pages and PDFs are mutable; discover them through parent indexes and validate title, language, visible dates, source identity and attachment version.

### Re-use law, publisher process and fees

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-47 | [Cabinet Regulation No. 536 — Official Publications Regulation](https://likumi.lv/ta/id/325308) | related_source | Official in-force regulation record fetched and converted. | Adopted 10.08.2021, effective 13.08.2021. Sets fees for re-use of official publications and Likumi.lv systematised acts: EUR 0.57 per document, EUR 21.34 per publication group/month, or EUR 128.06 for all groups/month. Confirm which fee and delivery scope applies to this library. |
| lv-48 | [Latvijas Vēstnesis re-use procedure](https://www.vestnesis.lv/atkalizmantosana) | related_source | Official publisher page fetched and converted. | Re-use must be coordinated in writing; the request must state purpose and product/service. The page says the current interface supports grouped official notices. It does not establish that the interface supplies a recurring feed of consolidated legal acts. |
| lv-49 | [Latvijas Vēstnesis services and re-use information](https://www.lv.lv/lv/pakalpojumi) | related_source | Official publisher service page fetched and converted. | Describes the re-use service, contact route, fee schedule and Regulation No. 536. Treat it and its linked tariff as parent routes for current service details; recheck fees before reuse. |

### Additional Primary Laws Identified Through Issue-Led Review

| ID | Source | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-50 | [Declaration of Place of Residence Act](https://likumi.lv/ta/id/64328) | related_source | Official consolidated Latvian act page inspected on 21 October 2026; publisher metadata shows it in force. | Covers address declaration and competent-authority rules. It does not establish EU/EEA residence eligibility; read with Act No. 369282 and the Register of Natural Persons Act. |
| lv-51 | [Law on the Register of Natural Persons](https://likumi.lv/ta/id/296185) | related_source | Official consolidated edition inspected; the selected edition is in force from 29 April 2026. | Section 4 includes foreigners holding or applying for listed EU registration/permanent-residence documents. The register law does not itself grant residence rights; read with the free-movement Act and data-protection rules. |
| lv-52 | [Civil Status Act](https://likumi.lv/ta/id/253442) | related_source | Official consolidated Latvian act page inspected on 21 October 2026; publisher metadata shows it in force. | Relevant to civil-status registration and foreign marital-status documents for marriage registration in Latvia. It does not resolve recognition of every foreign family document in residence procedures; section 4(3) points to the Administrative Procedure Law for refusal appeals. |

See [README.md](../README.md) and [sustainability-assessment.md](sustainability-assessment.md) for scope and proposed-route sustainability findings.


## Accepted local text copies (30)

These dated snapshots preserve the selected publisher text region. Their recorded limitations exclude page chrome, link targets, attached/interactive content, and later changes. Local acceptance does not establish legal currency or topic coverage.

| ID | Source | Document |
|---|---|---|
| `lv-02` | Likumi.lv official legislation portal — about and version information | [local copy](../documents/guidance/lv-likumi-about-and-version-information.md) |
| `lv-03` | Likumi.lv terms of service | [local copy](../documents/guidance/lv-likumi-terms-of-service.md) |
| `lv-04` | Law on Official Publications and Legal Information | [local copy](../documents/legislation/lv-law-official-publications-and-legal-information-en.md) |
| `lv-05` | Latvijas Vēstnesis official publication security information | [local copy](../documents/guidance/lv-vestnesis-publication-security.md) |
| `lv-06` | EU, EEA and Swiss citizens and family members entry/residence law (Likumi.lv consolidated record) | [local copy](../documents/legislation/lv-law-369282-eu-eea-swiss-family-residence.md) |
| `lv-07` | Official Gazette publication OP 2026/119.1 — EU/EEA/Swiss residence law | [local copy](../documents/legislation/lv-gazette-op-2026-119-1.md) |
| `lv-08` | Cabinet Regulation No. 675 of 30 August 2011 — prior EU residence procedure | [local copy](../documents/legislation/lv-cabinet-regulation-675-historical.md) |
| `lv-09` | Immigration Law (new 2026 Act) | [local copy](../documents/legislation/lv-immigration-law-2026.md) |
| `lv-10` | UK Withdrawal Agreement implementation law | [local copy](../documents/legislation/lv-uk-withdrawal-agreement-implementation-law.md) |
| `lv-11` | Administrative Procedure Law | [local copy](../documents/legislation/lv-administrative-procedure-law.md) |
| `lv-12` | Freedom of Information Law | [local copy](../documents/legislation/lv-freedom-of-information-law-en.md) |
| `lv-13` | State-Provided Legal Aid Law | [local copy](../documents/legislation/lv-state-provided-legal-aid-law.md) |
| `lv-14` | Ombudsman Law | [local copy](../documents/legislation/lv-ombudsman-law.md) |
| `lv-15` | Personal Data Processing Law | [local copy](../documents/legislation/lv-personal-data-processing-law.md) |
| `lv-16` | Personal data processing in criminal and administrative offence proceedings law | [local copy](../documents/legislation/lv-personal-data-processing-enforcement-law.md) |
| `lv-17` | Rules on publishing court information online and processing court decisions before release | [local copy](../documents/legislation/lv-court-publication-rules.md) |
| `lv-18` | PMLP: Entry of EU, EEA and Swiss citizens and family members | [local copy](../documents/guidance/lv-pmlp-eu-eea-swiss-overview.md) |
| `lv-21` | PMLP: Residence-permit application and form index | [local copy](../documents/guidance/lv-pmlp-residence-application-form-index.md) |
| `lv-25` | PMLP: Declaration of place of residence | [local copy](../documents/guidance/lv-pmlp-declaration-place-residence-snapshot.md) |
| `lv-26` | PMLP: State fees for residence permits | [local copy](../documents/guidance/lv-pmlp-residence-fees-snapshot-2026-10-19.md) |
| `lv-30` | MFA: Documents required to apply for a visa | [local copy](../documents/guidance/lv-mfa-ordinary-schengen-visa-document-list.md) |
| `lv-31` | PMLP: Visa-exempt nationalities and stay period | [local copy](../documents/guidance/lv-pmlp-visa-exemption-list-snapshot-2026-03-16.md) |
| `lv-36` | Ombudsman of Latvia contact and submission channel | [local copy](../documents/oversight/lv-ombudsman-contact-and-submission-route.md) |
| `lv-38` | Data State Inspectorate: complaint and request form examples | [local copy](../documents/forms/lv-dvi-complaint-and-request-form-index.md) |
| `lv-39` | Court Administration: state-provided legal aid information | [local copy](../documents/oversight/lv-court-administration-legal-aid-information.md) |
| `lv-40` | Court Administration: legal-aid application forms | [local copy](../documents/forms/lv-court-administration-legal-aid-forms-index.md) |
| `lv-41` | Court Administration: administrative cases and appeal process | [local copy](../documents/procedure/lv-court-administration-administrative-cases.md) |
| `lv-47` | Cabinet Regulation No. 536 — Official Publications Regulation (reuse fees) | [local copy](../documents/legislation/lv-cabinet-regulation-536-reuse-fees.md) |
| `lv-48` | Latvijas Vēstnesis official-publication reuse procedure | [local copy](../documents/guidance/lv-vestnesis-reuse-procedure.md) |
| `lv-49` | Latvijas Vēstnesis service directory — reuse and current fees | [local copy](../documents/guidance/lv-vestnesis-service-directory-reuse-fees.md) |
