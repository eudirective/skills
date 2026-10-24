# Austria coverage and source-research register

Checked 19 October 2026. The earlier Austria “complete” label described a bounded 37-record capture exercise, not a conclusion about legal sufficiency. The workflow now separates source acceptance, topic coverage and country review.

## Current source status

| State | Count | Meaning |
|---|---:|---|
| Accepted local artifact | 73 | Passed source-specific identity, version, extraction, attachment and classification gates plus semantic review. Official references remain usable when separately reviewed, even without a stored copy. |
| Captured, pending review | 0 | All captured sources passed their per-source checks. |
| Discovery-only | 1 | Family topic index used to locate substantive pages. |
| Located, not captured | 0 | All current manifest locators now have a retained, reviewed capture or bounded metadata-only route record. |
| Topic coverage complete | 0 topics | Accepted source status does not establish coverage. |
| Country review complete | No | Directive mapping, procedures, broader discovery, mission operations and Land practice remain open. |

## Completed corrections and source additions

- **FPG visa provisions:** §§2(4)(11), 11, 11a, 11b, 15a and 15b are accepted. The privileged third-country family-member definition, visa entitlement, priority handling and visa-free entry rules are present. FPG §§66, 67 and 70 and BFA-VG §§9–10 are accepted for removal/procedure analysis.
- **NAG-DV §5 dependency:** Austrian statutory text remains unchanged. The dependency register links CJEU C-61/22, Regulation (EU) 2019/1157 and successor Regulation (EU) 2025/1208. The statutory specimens are visually reviewed and accepted as source artifacts; a separate dependency row records the unresolved conformity of current issued cards with the successor EU format.
- **Vienna 2022 extraction:** Replayed from the visible RIS decision region. The screen-reader-only expansion is excluded; visible text is preserved. Case identity and operative part were checked.
- **Other legacy conversions:** All nine former broad-body conversions were replayed with validated source-specific regions or a structured directory parser. Navigation and page-shell contamination is excluded from the converted content.
- **IFG:** §§1–20 are captured and accepted, including the procedure, exceptions and remedies. Implementing instruments and actual request channels still need a separate review.
- **Forms and submission routes:** BMI form A and its English explanation, the official C1 Schengen form, the Volksanwaltschaft PDF, and the DSB/Volksanwaltschaft interactive routes have records. The two interactive pages are metadata-only because their raw HTML contains ephemeral form-session state; no session values are retained and neither form was submitted.
- **BMEIA directory:** The date discrepancy is resolved to the visible “Stand 19. Oktober 2026.” The 196 country headings and 524 representation records are retained structurally.
- **Court reviews:** Eleven selected VwGH, BVwG and LVwG decisions now have reviewed holdings, outcomes, procedural posture, applicability and limits. This is an index of selected cases, not a full survey.

## Mandatory coverage and dependency gates

The coverage model requires primary law, implementing rules, procedure, and remedy/operational-practice evidence for every required topic. The dependency register includes a preliminary map for 36 relevant Directive 2004/38 articles. It explicitly marks unresolved and partial articles; country completion stays blocked until those rows are source-checked or reasoned not applicable. A covered layer can cite an accepted local artifact or a separately recorded human-reviewed official reference; the latter does not change the local-artifact count. The inventory keeps a route or retrieval disposition per source, but a local conversion rule is not required for ordinary link use.

The NAG §54(7)/§55(3) crosswalk is in [procedural-crosswalk.md](procedural-crosswalk.md). Section 54(7) is the express abuse/fraud exclusion route and is excepted from the §55(3) referral process. Section 55(3) addresses a right that does not or no longer exists on specified grounds and requires prompt BFA involvement, notice to the person, and suspension of the VwGVG §8 delay period during the termination procedure. The distinct route and its case-law application still need broader validation.

## Case-law discovery

[case-law-discovery.json](case-law-discovery.json) defines 55 manual query tasks across VwGH, BVwG and all nine LVwG collections. The plan has not been run as a complete discovery batch. The six formerly uncaptured VwGH leads are now captured and reviewed, including Ra 2023/22/0090–0091. That 2026 decision rejected revisions as inadmissible; it is not a new merits holding on NAG §§54(7) or 55(3).

A repeatable plan is not a completed search. Record query, filters, dates, numeric result counts, screened records and inclusion/exclusion reasons for every batch. The completion gate now checks that each of the 55 tasks appears exactly once in a recorded batch and that every included decision has a holding, outcome, posture and applicability limits. A supplemental official-source search on 19 October 2026 found Ra 2025/18/0038 and Ra 2025/22/0052–0054, plus leads for Ra 2025/17/0049, LVwG-AV-1203/001-2025 and VGW-151/080/1941/2025. The VwGH Ra 2025/18/0038 PDF and Ra 2025/22/0052 HTML were opened; the LVwG Wien 1941/2025 page contains duplicated parallel text, so review the official decision directly before relying on it. Replay is needed only for a retained conversion. Other RIS excerpts could not be fully opened. These are recorded as leads in [case-law-discovery.json](case-law-discovery.json), not as a completed batch or accepted case index. The search service did not expose result counts. RIS court collections are selected and published at different times.

## Mission and Land practice still open

[operational-discovery.json](operational-discovery.json) contains a task for each Land and each of the 524 records in the BMEIA directory. Current progress:

- Five mission pages have leads and partial review: Nicosia, Pretoria, Addis Ababa, Jakarta and London. Their official pages show that appointment, checklists, outsourcing and applicant-residence limits can vary by mission. The other 519 representation tasks have not been researched.
- All nine Länder have an official authority or legal-source lead. Six have partial procedure information (Niederösterreich, Oberösterreich, Salzburg, Steiermark, Tirol and Wien); three are lead-only (Burgenland, Kärnten and Vorarlberg). Burgenland’s delegation ordinance carries an old NAG cross-reference that needs legal validation; Kärnten’s directory does not provide card-specific instructions. No Land task is complete.
- New official local leads include BH Linz-Land; Salzburg BH Zell am See, Hallein and Salzburg-Umgebung; and a more detailed Styrian e-government procedure. The federal oesterreich.gv.at card procedure gives the shared baseline for filing, timing, authority and documents, but does not replace each Land's local forms, appointment rules and jurisdiction. A directly reviewed official page can support the fields it covers; no raw capture is required for that reference use.
- Additional searches found the current BH Neunkirchen appointment/contact page (useful for contact and residence-law hours, but not a card checklist), Kärnten's 2025 social guide (mentions the card only as status evidence), Tirol's 2019 EEA leaflet (historical), and Vorarlberg's NAG form marked 10/2018 (historical but includes the card checkbox). Burgenland's 2024 PDF result was opened and screened out because it is a citizenship application form. Search result counts were not exposed; these records are leads or screened results, not completed Land reviews. The exact queries and dispositions are recorded in [operational-discovery.json](operational-discovery.json).
- No Land-level source lead is treated as a complete accepted practice record. Current authority, territorial jurisdiction, family-specific documents, form, appointment and submission route remain required fields.

## Reproducibility and source monitoring

Raw HTML/PDF responses are retained in the EU Source Update Monitor local-only archive, with archive-relative paths and SHA-256 values in [capture-ledger.json](capture-ledger.json). Interactive session HTML was excluded to avoid retaining transient form state; route identity and bounded first-screen details are preserved instead. The nine legacy conversions can be replayed from the indexed local archive.

The repository GitHub Actions workflow was retired on 24 October 2026 because it published raw captures and pending candidates in the country pack. Use the registered EU Source Update Monitor Austria check/capture actions. No successful run or schedule is asserted here.
