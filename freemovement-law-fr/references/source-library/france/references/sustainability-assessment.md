Skill: assess-source-rule-sustainability v0.2.0

# France source-route sustainability assessment

Status date: 21 October 2026
State: 48 source records; two CESEDA consolidated sections are usable official references, 17 other pages have replay-verified local review copies, no local copy is accepted, and legal-topic coverage remains incomplete.

## Assessment boundary

The inventory in [candidate-manifest.json](candidate-manifest.json) contains 48 source records across national law, EU/EEA/Swiss residence and family routes, civil status, visas, procedure, remedies, courts, privacy, public access, oversight, and legal aid. The count describes this bounded register, not France's complete source universe. Two government-published consolidated CESEDA Book II sections have passed a link-use review; no local statutory copy has been accepted or converted.

Direct link use for the two CESEDA sections requires no retrieval or conversion rule. This report does not assign a sustainability verdict to optional retained-copy or recurring-monitor routes.

## Usable official legal references

The official Légifrance current sections for CESEDA Book II are recorded in [source-acceptance.json](source-acceptance.json): the legislative part (Articles L. 200-1 to L. 286-2) and regulatory part (Articles R. 210-1 to R. 286-2). When checked on 21 October 2026, the page headers displayed versions in force as of 24 August 2026 and 9 September 2026, respectively. The code sections identify EU citizens and family members, and the legislative part expressly addresses qualifying EEA EFTA and Swiss nationals. The regulatory part includes the entry/visa and residence-card rules.

Read Articles L. 233-1 and L. 233-2 with the linked Conseil d'État decision nos. 450285/450288 of 24 February 2022; Légifrance flags the partial annulment in the code section. Before date-sensitive reliance, check the displayed version again. These references do not complete French topic coverage or replace separate procedural, consular, court, and oversight sources.

## Optional retained-copy route: DILA LEGI open data

The official data.gouv.fr LEGI dataset describes a no-account bulk route for retaining legal-text copies. It is unnecessary for ordinary use of the two reviewed Légifrance sections. The bulk route is relevant only if the project later needs local copies or recurring monitoring.

No baseline, delta replay, XML conversion, API credential, or automated extractor is required to use an official Légifrance link. Consult a specific Journal officiel item only for a material publication, commencement, correction, or legal-effect question left open by the consolidated text.

If later required for local retention, assess the dataset route for the particular text needed. It is not a prerequisite to use the government-published consolidated sections already reviewed.

API registration is also unnecessary for ordinary link use. Do not make a PISTE account or API client a prerequisite for this country pack.

## Other proposed routes and maintenance limits

| Source group | Maturity | Proposed route evidence | Main unresolved sustainability issue |
|---|---|---|---|
| CESEDA and other national legislation | Two CESEDA Book II sections are usable official references; other code leads remain discovery candidates | Légifrance current sections for legislative and regulatory Book II, with displayed version cutoffs recorded in the acceptance register | Check the displayed version at use; keep the partial annulment of L. 233-1/L. 233-2 linked. Other legal topics and local-copy acceptance remain open. |
| France-Visas pages and fees | Discovery-only or monitor-only | Official parent portal and a directly rendered EU-family page; dynamic guidance, wizard, country instructions, and fees are separate | Prior direct HTTP capture of the EU-family page returned 403. The research browser can render it, but that does not prove plugin-runtime retrieval or conversion. Link movement, redirects, page branches, dates, and volatile PDFs need parent-index discovery. |
| Service Public guidance | Discovery-only | Stable page IDs F2651, F19315, F39, F16146, F16162 and F18074 identified on official domain | Pages contain interactive branches and internal links; F19315 visibly dates from 2024-02-02. Capture page dates and branching content; reconcile guidance to current law and avoid treating an unchanged page as current legal text. |
| ANEF and application forms | Monitor-only | Ministry ANEF overview, Service Public task record, and official form definition | Application services and forms involve authentication or personal data. Monitor public route/form metadata only; never automate submissions or collect applicant case data. |
| Procedure and visa remedies | Discovery-only | CRPA/CJA code and provision leads plus separate short-stay RAPO and long-stay CRRV guidance | General rules and distinct special routes can be confused. Current deadlines, exceptions, jurisdiction, language, and notice effects need statute-level review and versioned identity. |
| Civil status/adoption | Discovery-only | Existing Code civil and Code de l'action sociale et des familles leads | Raw text, current consolidation, connected provisions, competent authorities, and full document workflows were not inspected. These topics are relevant but are not EU-family residence rules themselves. |
| Courts and case law | Discovery-only | Conseil d'État open-data XML documentation, ArianeWeb, TA Nantes court page, Légifrance | Publication coverage differs by source and court. Lower-court publication is selective; no complete corpus, pagination scheme, converter, or cross-database deduplication rule was proven. |
| CADA, CNIL, Défenseur des droits | Discovery-only | Official authority portals and public-information/complaint guidance | Complaints and case-access processes are distinct from merits appeals and may request personal data. CNIL's AGDREF system note is several years old and may not describe current processing architecture. |
| Legal aid | Discovery-only | Service Public guidance and the 1991 legal aid act record | Current act, nationality/residence criteria, income limits, and forms must be reconciled. No current-law response or version history was captured. |

## Functional and currentness caveats

France's CESEDA is a broad immigration code that contains EU-citizen and family provisions; it is a partial functional match to the Danish EU-residence seed, not an equivalent dedicated regulation. Keep French-citizen family routes separate from EU/EEA/Swiss free-movement routes. France-Visas identifies mainland and overseas territorial differences. EU law remains in the shared source core; France candidates must represent national provisions and administrative routes without duplicating EU instruments.

The official Conseil d'État decision no. 450285, issued 24 February 2022, says CESEDA Articles L. 233-1 and L. 233-2 were annulled in part as they excluded the right of residence beyond three months for a specified dependent child of an EU citizen studying or training in France. The current official code section displays this legal note, and the decision remains linked in the candidate register. Do not use the affected articles without that context.

## Source use and optional monitoring

For ordinary research, use the relevant government-published Légifrance text, Conseil d'État decision, France-Visas or Service Public page, and record its date/version and limits. A direct human-reviewed official link is sufficient; local capture, DILA bulk processing, API credentials, and a scheduled link monitor are optional. Use the closest government-published version when a consolidation is unavailable, and check the cited Conseil d'État annulment where it affects the provision in question.

If a recurring local monitor is later needed, choose a documented permitted route for the specific source, then add only the identity, version, conversion, failure, and change checks that route needs. Keep forms and portals read-only; do not submit or retain personal information. Do not bypass access controls.

## Coverage limits

The register identified official candidates in all requested source classes, but many direct references still need review. Current Service Public page revisions, current ANEF-system privacy documentation, ministry circulars, mission-specific instructions, regional practice, administrative remedies, and lower-court coverage remain open. “No candidate found” was not concluded for any class. The two usable CESEDA links do not establish statutory topic coverage or country completion.
