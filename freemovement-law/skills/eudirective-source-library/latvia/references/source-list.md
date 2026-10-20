# Latvia official-source discovery register

Skill: author-source-pack-rules v1.0.1

Research date: 18 October 2026  
State: EU Member State  
Comparison seed: Denmark EU free-movement residence regulation and guidance  
Scope: bounded discovery across official law/publication, free movement and immigration, forms, visa and consular routes, procedure/access, remedies, privacy/oversight, legal aid and courts. Prior country findings were carried forward as discovery leads and adapter lessons only.

**Discovery result:** 49 official-source and retrieval-route candidates; 0 accepted. **Capture result (19 October 2026):** 41 official HTML pages and 2 original PDFs converted to review-candidate Markdown, with the PDFs preserved byte-for-byte; 6 repository/discovery leads remain monitor-only. Every output remains unaccepted. The [candidate manifest](candidate-manifest.json) records each path and retrieval state; the [capture manifest](latvia-captures.json) records exact hashes, normalized change-detection digests, and replay inputs.

## Material 2026 status findings

- Latvia’s new EU/EEA/Swiss family and residence law (No. 369282) took effect on 10 July 2026. It expressly identifies EU, EEA and Swiss citizens, family members, mobile Latvian citizens, and UK Withdrawal Agreement beneficiaries. New Cabinet procedures are due by 1 December 2027; the transition clause keeps Regulation 675 for applications filed before commencement.
- The PMLP central EU/EEA/Swiss page was updated on 17 July 2026 and refers to the new law. Several linked checklist, filing and document pages pre-date it. The MFA EU-family page was updated on 17 June 2026 and still cites Cabinet Regulation 675. Treat that as a verified stale-guidance conflict, not as current procedure.
- A separate new Immigration Law was adopted 20 August 2026 and took effect 15 September 2026. Keep it distinct from free-movement law; reconcile PMLP third-country family guidance and forms against it.
- The new free-movement Act’s English record says the State Language Centre has not officially translated its text. Latvian-source conversion and translation boundaries need to remain explicit.

## Candidate register

### National Law Discovery

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-01 | [N-Lex Latvia country information](https://n-lex.europa.eu/n-lex/info/info-lv/index) | related_source | Official N-Lex country information page inspected; its description of Latvijas Vēstnesis and Likumi.lv was checked. | N-Lex identifies Latvijas Vēstnesis as the official Gazette and Likumi.lv as publisher-managed systematic legislation access. Discovery lead only; N-Lex is not the national source publisher and does not cover all requested classes. |

### Official Legislation Portal

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-02 | [Likumi.lv official legislation portal — about and version information](https://likumi.lv/about.php) | related_source | Official Likumi.lv about page inspected. | Publisher says current, historic and future wording, validity status, related documents and English translations are provided. Systematised text is informational; the official Gazette prevails in case of discrepancy. |

### Publisher Terms

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-03 | [Likumi.lv terms of service](https://likumi.lv/par-mums/portala-lietosanas-noteikumi) | related_source | Full official terms page fetched directly and converted in the capture pass; the earlier research-client open had timed out. | Section 6 says systematised acts are available for reuse under the public-information laws and applicable Cabinet-set fees, and the keeper organizes reuse. Links may be placed with attribution. This is a legal route, but does not itself confirm an unattended recurring monitor or its delivery method. See `candidates/lv-03.md`, lv-47 to lv-49, and the sustainability assessment. |

### Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-04 | [Law on Official Publications and Legal Information](https://likumi.lv/ta/en/en/id/249322) | related_source | Official Likumi.lv act page inspected in the bounded source review. | Act describes the official publisher role and the legal-publication framework for Latvijas Vēstnesis and systematised legal information. Use alongside the Gazette publication for legal force and the consolidated portal for version discovery. |

### Official Publication Integrity

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-05 | [Latvijas Vēstnesis official publication security information](https://www.vestnesis.lv/informacijas-drosiba) | related_source | Official publisher page directly fetched and converted. | Publisher states issue contents and each publication are also produced as PDF electronic documents, signed with the organisation electronic seal, with e-signature fallback. The capture preserves the page, but the linked file's signature/seal still needs cryptographic validation. |

### Free Movement Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-06 | [EU, EEA and Swiss citizens and family members entry/residence law (Likumi.lv consolidated record)](https://likumi.lv/ta/id/369282) | close_functional_match | Official current Likumi.lv act page inspected; scope, definitions, commencement and transition provisions checked. | Law 369282; adopted 11.06.2026, published 26.06.2026, effective 10.07.2026; page shows in force. Covers EU, EEA and Swiss citizens and family members, mobile Latvian citizens, and UK Withdrawal Agreement beneficiaries. Latvian-only substantive text; English page says State Language Centre has not officially translated it. Cabinet implementing rules are due by 01.12.2027. |

### Official Gazette Publication

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-07 | [Official Gazette publication OP 2026/119.1 — EU/EEA/Swiss residence law](https://www.vestnesis.lv/op/2026/119.1) | close_functional_match | Official Latvijas Vēstnesis publication page and linked PDF directly fetched; original PDF and page-wise Markdown are retained as unaccepted candidates. | Stable OP identifier 2026/119.1; issue 119, 26.06.2026. The linked PDF is the promulgated text; do not treat it alone as the current consolidated text after later amendments. Page-wise text extraction replays offline; cryptographic e-seal/signature verification remains open. |

### Historical Or Transitional Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-08 | [Cabinet Regulation No. 675 of 30 August 2011 — prior EU residence procedure](https://likumi.lv/ta/id/235499-kartiba-kada-savienibas-pilsoni-un-vinu-gimenes-locekli-iecelo-un-uzturas-latvijas-republika) | related_source | Official Likumi.lv record inspected through the new law transition link. | The 2026 law says applications submitted before its commencement are processed under Regulation 675. Do not use as the general post-10.07.2026 procedure without checking repeal and new rules; it remains a transition dependency for pending applications. |

### Third Country Immigration Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-09 | [Immigration Law (new 2026 Act)](https://likumi.lv/ta/id/370622-imigracijas-likums) | related_source | Official current Likumi.lv act page inspected; document passport and commencement metadata checked. | Law adopted 20.08.2026, published 01.09.2026, effective 15.09.2026; current record is in force. Separate third-country immigration route from the EU/EEA/Swiss free-movement law. The residence-law route must monitor both regimes and reconcile agency pages after this enactment. |

### Uk Withdrawal Agreement Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-10 | [UK Withdrawal Agreement implementation law](https://likumi.lv/ta/id/305836) | related_source | Official Likumi.lv act page reached through the new EU residence law transition link. | The new 2026 free-movement law expressly applies to UK nationals/family members covered by this Act. UK Withdrawal Agreement beneficiary route remains distinct from EU/EEA/Swiss nationality routes. |

### Administrative Procedure Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-11 | [Administrative Procedure Law](https://likumi.lv/ta/id/55567-administrativa-procesa-likums) | related_source | Official current Likumi.lv act page inspected; current amendment history checked. | Current record includes amendment adopted 28.05.2026, effective 01.06.2026. Covers procedure, evidence, access, review and administrative-court process. A high-value general procedure source; map provisions to each decision type and special migration rules. |

### Access To Information Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-12 | [Freedom of Information Law](https://likumi.lv/ta/en/en/id/50601) | related_source | Official English act page inspected. | Official English version selected from 01.05.2023; records access and reuse of public-sector information. General public-information access differs from an applicant’s access to their own administrative file. |

### Legal Aid Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-13 | [State-Provided Legal Aid Law](https://likumi.lv/ta/id/104831-valsts-nodrosinatas-juridiskas-palidzibas-likums) | related_source | Official current act page inspected; current text includes 2026 amendment history. | Amendments adopted 23.04.2026 have provisions effective 01.06.2026; links free legal aid eligibility and categories. Check applicability in each migration/court route; Immigration Law separately anticipates detention-extension legal aid provisions tied to future amendments. |

### Ombudsman Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-14 | [Ombudsman Law](https://likumi.lv/ta/id/133535-tiesibsarga-likums) | related_source | Official current act record inspected. | Law establishes national Ombudsman and individual submission/investigation powers; recent amendment effective 02.04.2025. General good-governance/human-rights oversight; not a substitute for statutory appeal deadlines. |

### Data Protection Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-15 | [Personal Data Processing Law](https://likumi.lv/ta/id/300099) | related_source | Official current act record inspected. | Current national data-protection law supporting GDPR implementation. Use with the DVI complaint procedure and GDPR; avoid personal case-data collection. |

### Law Enforcement Data Legislation

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-16 | [Personal data processing in criminal and administrative offence proceedings law](https://likumi.lv/ta/id/308278) | related_source | Official current act record inspected. | Separate Latvian act for processing by competent authorities for criminal and administrative offence purposes. Keep distinct from general GDPR and immigration/residence processing. |

### Court Publication Rules

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-17 | [Rules on publishing court information online and processing court decisions before release](https://likumi.lv/ta/id/187832) | related_source | Official current Likumi.lv result inspected; amendment dated 28.04.2026 identified. | Current rules direct court proceedings information to e-lieta and provide for public redaction; amended 28.04.2026. Court-publication regime changed in 2026; verify which decision classes are public and where before designing case-law monitoring. |

### Official Agency Guidance

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-18 | [PMLP: Entry of EU, EEA and Swiss citizens and family members](https://www.pmlp.gov.lv/en/entry-citizens-eu-eea-and-switzerland-and-their-family-members) | partial_functional_match | PMLP official page inspected; published/updated metadata and stated law references checked. | Updated 17.07.2026; after the new law took effect. It identifies current registration/permanent residence documents and non-EU family permits. Central guidance candidate. Reconcile its linked document requirements/forms against the new law and outstanding Cabinet rules. |
| lv-19 | [PMLP: Documents required for EU citizen and family residence document](https://www.pmlp.gov.lv/en/what-documents-must-be-filed) | partial_functional_match | Official PMLP page inspected; date and checklist content checked. | Updated 24.07.2025, before the new law took effect. Potentially stale operational checklist. Compare every item and route with the 2026 Act and new implementing rules before use. |
| lv-20 | [PMLP: Where can residence documents be filed?](https://www.pmlp.gov.lv/en/where-can-documents-be-filed) | partial_functional_match | Official PMLP page inspected; publication/update metadata and filing routes checked. | Updated 05.02.2025. Describes e-signature, post, in-person and some embassy/representative filing routes. Pre-2026 guidance; verify against the new act, Cabinet rules, actual e-address/form workflow and mission-specific intake. |
| lv-23 | [PMLP EU residence document types and explanation](https://www.pmlp.gov.lv/en/what-residence-documents-are-issued-union-citizens-and-their-family-members) | partial_functional_match | Official PMLP page identified in prior review; update metadata and old statutory references require recheck. | Page updated 24.07.2025; predates the new 2026 act. Operational detail may have been carried over; keep unverified/currentness-open until reconciled with the new law. |
| lv-24 | [PMLP information for UK Withdrawal Agreement beneficiaries](https://www.pmlp.gov.lv/en/information-brexit) | partial_functional_match | Official PMLP guidance page inspected in official search results. | Updated 24.07.2025; refers to WA residence rights and post-transition family procedures. Verify against the new law’s transition clause and the linked UK Act; distinguish protected beneficiaries from post-2020 entrants. |
| lv-25 | [PMLP: Declaration of place of residence](https://www.pmlp.gov.lv/en/declaration-residence-place) | related_source | Official PMLP page inspected; scope, channels and last-updated date checked. | Updated 03.06.2025; explains municipal/e-service/PMLP channels for persons with residence documents. Auxiliary operational obligation; validate law changes and Latvija.lv login/service route. |
| lv-27 | [PMLP: Identity number and declared residence for EU citizens](https://www.pmlp.gov.lv/en/article/how-obtain-personal-identity-number-and-declared-place-residence-latvia) | partial_functional_match | Official PMLP page inspected in official search results. | Published 31.01.2022; says an EU citizen planning to stay over 90 days should request registration. Older explanation needs comparison with current Act sections 19 and 24, including exemptions from registration. |

### Official Forms Index

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-21 | [PMLP: Residence-permit application and form index](https://www.pmlp.gov.lv/en/application-requiring-residence-permit) | partial_functional_match | Official PMLP forms index inspected in official search results. | Updated 22.09.2026; list includes forms for third-country residence and the EU citizen/family residence document application. Parent index is preferable to a pinned file URL. Capture attachment label/date/hash and verify applicable form after the 2026 law. |
| lv-38 | [Data State Inspectorate: complaint and request form examples](https://www.dvi.gov.lv/lv/iesniegumu-paraugi) | related_source | Official DVI forms page inspected in official search results. | Complaint/request forms updated 11.02.2026; page sets secure e-signature/e-address routes. Attachment rediscovery and version identity should be parent-index based. |

### Application Form Pdf

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-22 | [PMLP direct EU citizen/family residence application PDF](https://www.pmlp.gov.lv/en/media/100/download) | partial_functional_match | Official PDF endpoint fetched directly; original PDF and page-wise Markdown are retained as unaccepted candidates. The PDF has 182 interactive fields, which the Markdown does not recreate. | Search index dates the asset to over 10 years ago; its parent index was updated 22.09.2026. Treat as stale until the current parent index confirms the attachment. Text extraction replays offline; a stable media URL is not proof of current form identity. |

### Official Fees Guidance

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-26 | [PMLP: State fees for residence permits](https://www.pmlp.gov.lv/en/state-fees-issuance-residence-permit) | related_source | Official PMLP page identified through current official search results. | Dynamic fees and processing-speed options; exact applicable EU-family fees need current route-specific confirmation. Fees change independently of core legislation and can vary by document/processing time; monitor the date and table identity. |

### Official Ministry Guidance

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-28 | [MFA: Entry into Latvia by Union citizens and family members](https://www.mfa.gov.lv/en/entry-latvia-citizens-union-and-their-family-members) | partial_functional_match | Official MFA page inspected; date and cited legal instrument checked. | Updated 17.06.2026 and still cites Cabinet Regulation No. 675; new Act took effect 10.07.2026. Known stale conflict. Keep as a monitoring candidate and flag for correction; do not use its old citation as current procedure. |
| lv-29 | [MFA: Entry to Latvia information hub](https://www.mfa.gov.lv/en/entry-latvia) | related_source | Official MFA hub identified and updated metadata checked in prior official review. | Updated 20.05.2026. Discovery/index page for entry/visa information; pre-dates the EU-family law commencement, so check parent and child pages for current legal references. |
| lv-30 | [MFA: Documents required to apply for a visa](https://www.mfa.gov.lv/en/documents-required-apply-visa) | related_source | Official MFA page identified in official search results. | Updated 17.06.2026. General Schengen visa source; EU-family visa exceptions under the new Act need a separate comparison. |

### Official Visa Guidance

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-31 | [PMLP: Visa-exempt nationalities and stay period](https://www.pmlp.gov.lv/en/list-countries-citizens-which-do-not-need-visas) | related_source | Official PMLP page inspected in official search results. | Updated 16.03.2026; list reflects Regulation (EU) 2018/1806 and national/other categories. Nationality-based, change-sensitive table; distinguish visa exemption from residence rights. |

### Consular Directory

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-32 | [MFA: Latvia’s embassies and consulates directory](https://www.mfa.gov.lv/en/latvias-embassies-and-consulates) | related_source | Official MFA page inspected through official search result. | Updated 09.06.2026; lists Latvia missions by country. Parent directory is a discovery route; individual mission rules and outsourced appointment services can differ and change. |

### Consular Representation Directory

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-33 | [MFA: Other Schengen missions representing Latvia for visas](https://www.mfa.gov.lv/en/diplomatic-and-consular-missions-other-schengen-member-states-issuing-visas-enter-latvia) | related_source | Official MFA page inspected in official search results. | Current list includes representation arrangements; page content varies by mission/country. Monitor by parent index and record each representative mission separately; do not assume all countries have a Latvian mission. |

### Third Country Family Guidance

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-34 | [PMLP: Family unification under general immigration route](https://www.pmlp.gov.lv/en/family-unification) | related_source | Official PMLP page inspected in official search results. | Published 14.10.2020, updated 22.04.2022. Likely stale: references family-reunification requirements and old subsistence thresholds; check against the 2026 Immigration Law and current Cabinet regulations. |

### Border Authority Information

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-35 | [State Border Guard official site — entry and border information](https://www.rs.gov.lv/en) | related_source | Official State Border Guard domain and current operational notices found; exact dedicated refusal/appeal guide not identified. | Site publishes dated daily operational notices; individual notices are not a complete rules source. Bounded search found operational examples, not a dedicated appeal procedure. Search border refusal decisions and complaints separately before implementation. |

### Oversight Complaint Route

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-36 | [Ombudsman of Latvia contact and submission channel](https://www.tiesibsargs.lv/en/contacts/) | related_source | Official Ombudsman contacts page inspected. | Describes e-signed/e-address and paper submission routes; current contact details are exposed. National human-rights/good-administration oversight. Submission contains personal data; monitor only public instructions, not submissions. |

### Privacy Complaint Route

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-37 | [Data State Inspectorate: complaint about personal-data processing](https://www.dvi.gov.lv/en/services/complaint-concerning-processing-personal-data) | related_source | Official DVI service page inspected in official search results. | GDPR complaint process and response time information exposed. Current procedural steps and electronic intake terms need direct inspection; do not process case submissions. |

### Official Legal Aid Guidance

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-39 | [Court Administration: state-provided legal aid information](https://www.tiesas.lv/lv/valsts-nodrosinata-juridiska-palidziba) | related_source | Official Court Administration page inspected. | Page states eligibility, categories including certain administrative court proceedings, and application route. Current criteria depend on law and court decision; not every immigration matter qualifies. |

### Official Legal Aid Forms

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-40 | [Court Administration: legal-aid application forms](https://www.ta.gov.lv/lv/juridiskas-palidzibas-sanemsanas-pieprasijuma-veidlapas) | related_source | Official Court Administration forms page inspected; dates and special appendices checked. | Page updated 20.06.2026; forms updated 19.06.2026, with a special appendix for deportable foreigners/international cases. Good parent index for dynamic form downloads; confirm new legal aid amendments and attachment versions. |

### Court Procedure Guidance

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-41 | [Court Administration: administrative cases and appeal process](https://www.tiesas.lv/lv/administrativas-lietas) | related_source | Official Court Administration procedure page inspected. | Updated 11.02.2026; addresses administrative claim venue, procedure and fees. Useful general appeal guidance; reconcile special-law deadlines and current court fees before relying on it. |

### Court Decision Repository

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-42 | [E-lieta anonymised court decisions and proceedings information](https://www.elieta.lv) | related_source | Official Court Administration FAQ and current court-publication rules identify e-lieta as the public route; the live database was not directly inspected. | Current rules amended 28.04.2026; public anonymised decisions are identified in the official FAQ. Search access, recurring discoverability, stable IDs, redaction, coverage and automated access limits remain unverified. |

### Supreme Court Case Law

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-43 | [Supreme Court / Senate case-law archive](https://www.at.gov.lv/lv/tiesu-prakse/judikaturas-nolemumu-arhivs) | related_source | Official Supreme Court case-law site and search guidance inspected in official results. | Senate archive has selected precedential decisions; official guidance distinguishes decisions in E-lieta and non-public/archive holdings. Selective corpus, multiple archive/search paths and historical coverage mean it is not a complete national case-law feed. |

### Constitutional Court Case Law

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-44 | [Constitutional Court case-law database](https://www.satversmestiesa.lv/en/data-base-case-law) | related_source | Official Constitutional Court database page inspected. | Page updated 19.01.2026; downloadable Citavi database file is dated 11.12.2023 and text is in Latvian. Material maintenance risk: parent page current but database file date is old; database requires external Citavi software. Court judgments are also separately published. |

### Official Gazette Archive

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-45 | [Latvijas Vēstnesis daily issue archive and act publication pages](https://www.vestnesis.lv/) | related_source | Official Gazette archive inspected through the 2026/119.1 publication. | Archive browses issues from 1993 onward; each target publication exposes its own OP identifier and PDF link. A source-of-record retrieval path; stable OP identity and signature checks still need implementation and replay. |

### Legislation Change Discovery

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-46 | [Likumi.lv “newly published acts” RSS discovery surface](https://likumi.lv/) | related_source | Official page shows an RSS icon labelled “RSS Šodien publicēti tiesību akti”; the browser followed only the image asset, not the feed target. | Feed existence is suggested by official UI but feed URL, payload, coverage, retention and terms were not verified. Do not build a poller from the icon alone. Establish the actual feed target and compare its scope with Gazette issue search before use. |

## Search coverage and limits

Searches were made in Latvian and English against N-Lex, Likumi.lv, Latvijas Vēstnesis, PMLP, the Ministry of Foreign Affairs, the State Border Guard, the Ombudsman, the Data State Inspectorate, Court Administration, E-lieta, the Supreme Court and Constitutional Court. The class-by-class outcomes, native-language query strings and limits are in `candidate-manifest.json` under `search_coverage`.

No candidate or source class is declared absent. The search did not establish all mission practices, full regional/municipal rules, every appeal route, all court decisions, all family-document rules, or completeness of amendments and forms. Use official first-party pages and exact versions for any later rule.

## Retrieval route observations

- Likumi.lv exposes current, historic and future versions, legal status, related records and search. Its own about page says the content is informational and the official Gazette prevails in discrepancies.
- Latvijas Vēstnesis provides stable OP identifiers and publication-specific PDFs; the official publisher says PDFs carry an organisational electronic seal (or e-signature fallback). The direct capture preserved the OP 2026/119.1 PDF bytes and page-wise text; cryptographic signature validation remains unimplemented.
- Likumi.lv displays an RSS icon for newly published acts, but the research browser resolved only the icon image. The feed URL, scope and payload remain unverified. No official public API was found in the bounded search.
- Likumi.lv terms were fetched directly. They say systematised acts are available for reuse under the applicable public-information rules and fees and that the publisher organizes reuse. The official publisher separately requires written coordination, a stated purpose/product/service, and currently identifies grouped official notices as the supported public-interface route. A recurring legal-text monitor's availability, price and delivery format therefore require written confirmation.
- A repeat capture exposed volatile inline scripts, CSRF tokens and Drupal view IDs. The rule stores and hashes the exact raw response while ignoring only those identified values for comparison. All remaining HTML and link changes are still staged for review; exact PDF bytes are compared.
- The official Act remains Latvian-only on the English record. Agency pages and PDFs are mutable; discover them through parent indexes and validate title, language, visible dates, source identity and attachment version.

### Re-use law, publisher process and fees

| ID | Candidate | Relation | Verification | Route/version note |
|---|---|---|---|---|
| lv-47 | [Cabinet Regulation No. 536 — Official Publications Regulation](https://likumi.lv/ta/id/325308) | related_source | Official in-force regulation record fetched and converted. | Adopted 10.08.2021, effective 13.08.2021. Sets fees for re-use of official publications and Likumi.lv systematised acts: EUR 0.57 per document, EUR 21.34 per publication group/month, or EUR 128.06 for all groups/month. Confirm which fee and delivery scope applies to this library. |
| lv-48 | [Latvijas Vēstnesis re-use procedure](https://www.vestnesis.lv/atkalizmantosana) | related_source | Official publisher page fetched and converted. | Re-use must be coordinated in writing; the request must state purpose and product/service. The page says the current interface supports grouped official notices. It does not establish that the interface supplies a recurring feed of consolidated legal acts. |
| lv-49 | [Latvijas Vēstnesis services and re-use information](https://www.lv.lv/lv/pakalpojumi) | related_source | Official publisher service page fetched and converted. | Describes the re-use service, contact route, fee schedule and Regulation No. 536. Treat it and its linked tariff as parent routes for current service details; recheck fees before reuse. |

See [README.md](../README.md) and [sustainability-assessment.md](sustainability-assessment.md) for scope and proposed-route sustainability findings.
