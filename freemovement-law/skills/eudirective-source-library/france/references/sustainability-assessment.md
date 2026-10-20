Skill: assess-source-rule-sustainability v0.2.0

# France source-route sustainability assessment

Status date: 18 October 2026  
State: discovery-only candidates; 47 candidates, zero locally stored copies accepted, and no France retrieval or conversion rule implemented.

## Assessment boundary

The inventory in [candidate-manifest.json](candidate-manifest.json) contains the seven previously recorded French candidates plus 40 additional official-source leads across national law, EU/EEA/Swiss residence and family routes, civil status, visas, procedure, remedies, courts, privacy, public access, oversight, and legal aid. The count describes this bounded register, not France's complete source universe. No candidate has been accepted, and no acquired legal source text has been converted in the France runtime.

There is no implemented France rule to rate. This report assigns **no sustainability verdict**. It evaluates proposed routes and names evidence that is still missing.

## Strongest proposed legal-text route: DILA LEGI open data

The official data.gouv.fr LEGI dataset says DILA provides the consolidated national legislation and regulation corpus over public HTTPS and FTPS, under the Open Licence. The official directory was reachable over HTTPS during this review. It showed a 2025-07-13 global LEGI Freemium package and dated daily delta archives through 2026-10-17. The dataset metadata was updated on 2026-10-16. This is a feasible no-account discovery lead and avoids the PISTE account and credential dependency of the Légifrance API.

The LEGI bulk corpus includes current and historical/repealed versions, and its API FAQ instructs bulk users to retrieve a baseline and apply archives in chronological order. That complexity is relevant only if we choose to run a recurring bulk-monitoring or reproducible-copy workflow. For ordinary research, a human-reviewed Légifrance government-published consolidated text is sufficient; record its displayed version and publisher caveat, and consult a specific Journal officiel item only for a material publication/effect question. No baseline/delta adapter is required to use an official link.

The official dataset describes the limits of its coverage: it includes 73 current official codes, laws, ordinances, decrees, and selected orders; it is exhaustive for laws and decrees from 1945, but selected orders and circulars published mainly in ministry bulletins require separate publisher discovery. The official Légifrance open-data description warns that consolidated wording is not the legally authentic/opposable source; the official Journal officiel remains the validation route where publication and legal effect matter. LEGI is therefore a promising retrieval route for legislation, not a complete source universe or a legal-currentness determination.

## PISTE API alternative

Légifrance documents a stable API, free after registration. Its official FAQ describes OAuth2 client-credentials authentication, separate sandbox and production applications, production subscription to the API, acceptance of PISTE and Légifrance API terms, quotas, and credentials that must remain secret. The official API conditions provide no minimum availability guarantee. Registration is technically feasible but requires an accountable credential owner, renewal and rotation process, quota monitoring, and operational recovery. The public DILA bulk route appears less fragile for scheduled source acquisition, subject to the baseline/delta complexity above. Neither route has been consumed from the plugin runtime.

## Other proposed routes and maintenance limits

| Source group | Maturity | Proposed route evidence | Main unresolved sustainability issue |
|---|---|---|---|
| CESEDA and other national legislation | Discovery-only | Official Légifrance records plus DILA LEGI XML bulk route; article and code identifiers identified | Date-specific version query, amendment/supersession identity, DTD versioning, ordered delta replay, record completeness, and deterministic conversion are untested. CESEDA L. 233-1/L. 233-2 require a linked judicial annulment check. |
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

The official Conseil d'État decision no. 450285, issued 24 February 2022, says CESEDA Articles L. 233-1 and L. 233-2 were annulled in part as they excluded the right of residence beyond three months for a specified dependent child of an EU citizen studying or training in France. A future date-aware rule must preserve the linked decision and verify how the official consolidated text reflects the ruling. Do not monitor those article pages as isolated, unqualified statements.

## Source use and optional monitoring

For ordinary research, use the relevant government-published Légifrance text, Conseil d'État decision, France-Visas or Service Public page, and record its date/version and limits. A direct human-reviewed official link is sufficient; no DILA baseline, delta replay, XML fixtures, API credentials, page capture, or scheduled link monitor is required. Use the closest government-published version when a consolidation is unavailable, and check the cited Conseil d'État annulment where it affects the provision in question.

If a recurring local monitor is later needed, choose a documented permitted route for the specific source, then add only the identity, version, conversion, failure, and change checks that route needs. Keep forms and portals read-only; do not submit or retain personal information. Do not bypass access controls.

## Coverage limits

The register identified official candidates in all requested source classes, but direct source references, current Service Public page revisions, current ANEF-system privacy documentation, ministry circulars, mission-specific instructions, regional practice, and comprehensive lower-court coverage still need review. “No candidate found” was not concluded for any class. No local statutory copy has been accepted and no France adapter is implemented; neither condition prevents human-reviewed use of an official link. Current-law and completeness claims remain outside this bounded inventory.
