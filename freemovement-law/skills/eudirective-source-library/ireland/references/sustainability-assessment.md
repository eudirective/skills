Skill: assess-source-rule-sustainability v0.2.0

## Retrieval implementation update (2026-10-19)

The initial review below describes the 18 October discovery-only state. It is superseded for acquisition status by this update; its legal-currentness and coverage cautions remain applicable.

### Retrieved and converted material

The bounded [retrieval manifest](ireland-retrieval-manifest.json) records 51 candidate URLs. Twenty-six first-party payloads were saved and converted to unaccepted review candidates, with 0 accepted. The set includes 11 legislative texts (including S.I. 548/2015, its 2021 and 2025 amending instruments, the 1977 and 1997 EEA instruments, the Swiss Confederation Act, the Withdrawal Agreement Regulations, the 2025 fee instrument, the Immigration Act, the FOI Act, and the Data Protection Act), the SI 548 amendment index, eISB retrieval/reuse material, public guidance, privacy and oversight sources, court procedure, and service content. Twenty-five candidate retrievals did not produce a conversion: 24 returned HTTP 403 and one Legal Aid Board PDF returned HTTP 404 in this runtime. This is an observed access result for this retrieval client, not a claim that each page is unavailable through every user-facing route.

The converter retains raw responses under ignored `temp/ireland/raw/`, records SHA-256 and exact final URLs, enforces a 32 MiB per-response cap and candidate-host allowlist, checks payload format and record identity, labels every output as unaccepted, and can replay conversions offline. The PDF converter is pinned to pypdf 6.10.0. All 26 saved outputs pass hash and deterministic replay verification. The per-record candidate manifest and human source list now reflect conversion status.

### Updated sustainability verdicts

| Lane | Retrieval sustainability | Legal-currentness and coverage limits |
|---|---|---|
| eISB ELI legislative records | **Sustainable with limits** (medium confidence). Stable record paths and HTML/PDF representations were live for the captured records; the publisher’s Open Data PSI licence incorporates CC BY 4.0; captured records have host, payload, identity, size, hash, and replay checks. | A `made` or `enacted` representation is not a consolidated current text. The SI amendment index plus 2021/2025 instruments must be reconciled provision by provision. No source is accepted. |
| eISB annual/amendment discovery | **Fragile** (medium confidence). Official indexes and the SI 548 amendment table were captured, but the rule does not yet crawl all annual indexes or detect every new amendment. | The ISD legislative index was not retrievable in this run and its previously recorded omission of SI 398/2025 remains a discoverability warning. |
| ISD, gov.ie, FOI and Ombudsman page lanes | **Undetermined** (low confidence). Many fixed official URLs returned HTTP 403; no reusable body extraction, parent-link update check, or continuous change detector is evidenced for those records. | Official search results expose current-page changes, including revised EUTR application steps, but are not retained source payloads. Do not treat search snippets as converted evidence. |
| Static PDF guidance and forms | **Fragile** (low confidence). A few official PDFs convert, but several link paths could not be rediscovered because parent pages were inaccessible; one Legal Aid Board PDF path returned 404. | The 2023 EUTR1 PDF is no longer the default route described by current ISD guidance. The 2021 short-stay checklist and older Ombudsman fact sheet need a current parent-page check. |

### Current-route discrepancies

Current official ISD search content says EUTR1/EUTR1A applications are submitted through the ISD Customer Portal and paper forms are requested through the portal. It describes the old paper EUTR3 as superseded after 15 October 2026. The candidate EUTR1 PDF dated 2023 therefore remains a versioned historic/form candidate, not the current default. The same guidance still lists SI 548/2015 and SI 445/2021 but not SI 398/2025, although the eISB amendment table records the 2025 instrument. The downloaded SI 398/2025 is now available for direct comparison; its legal effect and the current consolidated SI 548 text have not been resolved here.

The eISB reuse licence does not extend to ISD, gov.ie, the courts, the Ombudsman, the Data Protection Commission, or the Legal Aid Board. Each non-eISB lane needs its own terms and accessible, repeatable acquisition route before it can receive a positive sustainability rating.

No source is accepted. The source inventory remains bounded and does not claim full coverage of national, regional, mission, or judicial sources.

# Ireland proposed-route sustainability assessment (2026-10-18)

## Scope and evidence

Reviewed the discovery-only candidate register and source list; N-Lex Ireland; official eISB legislation, amendment tables, annual SI index, ELI format documentation and Open Data PSI licence; Immigration Service Delivery legislation, EU Treaty Rights, entry, family, visa and registration guidance; gov.ie notices; DFA mission directory; FOI review pages; Ombudsman scope guidance; Data Protection Commission sources; Legal Aid Board sources; family-status and civil-registration guidance; and Courts.ie procedure and judgment discovery. No source bytes were saved to the workspace or converted. No Ireland adapter, active source manifest, conversion replay, change detector or live runtime rule exists.

The candidate manifest contains 51 records: 0 accepted and 0 retrieved/converted. These counts define the current review scope; they do not prove source-universe completeness.

## Summary

No implemented Irish source rule exists, so there is **no rule sustainability verdict** to assign. The eISB route has the strongest documented proposed-route evidence: stable ELI identifiers, named representations, amendment tables, annual indexes, and an explicit Open Data PSI licence. It remains a discovery and acquisition design lead until live retrieval, payload identity, amendment resolution, deterministic conversion and change detection are implemented and reviewed.

The clearest currentness warning is that eISB's SI 548/2015 amendment table says Regulation 24 was substituted by SI 398/2025, while ISD's immigration legislation index, last updated 6 February 2026, lists SI 548/2015, SI 445/2021 and SI 728/2020 but omits SI 398/2025. ISD's EU Treaty Rights page was updated on 10 September 2026 but still summarizes the 2015/2021 instruments. The direct eISB text endpoint for SI 398/2025 returned 403 in this research client, so the instrument’s operative wording and effect have not been inspected. A second cross-publisher discrepancy remains: gov.ie gives a 12-month EUTR processing estimate (last updated 11 April 2025), while the current ISD page says up to six months. These are update and reconciliation issues, not proof of the legal effect of the 2025 amendment.

## Proposed-route findings

| Source group | Maturity | Evidence and missing work | Assessment |
|---|---|---|---|
| eISB legislation and amendment discovery | Discovery only; promising | eISB documents ELI paths and available representations: Acts have HTML/print/PDF/XML and SIs have HTML/print/PDF. Its Open Data page states reuse is under the Oireachtas Open Data PSI licence incorporating CC BY 4.0. The SI annual index and SI 548 amendment table identify SI 398/2025. Direct live requests, response headers/redirects, SI 398 text, newest edition behavior, complete amendment chains, size limits and HTML/PDF/XML conversion fixtures were not verified. | Strongest proposed route; no acquisition rule or rule verdict. It is a documented publisher URI/file scheme, not a confirmed API. No API registration step was found in reviewed documentation. |
| SI 548/2015 current text and EU/EEA/Swiss legal split | Discovery only; unresolved current consolidation | SI 548 identifies itself as giving effect to Directive 2004/38/EC. Regulation 3(2) separately refers EEA citizens who are not Union citizens to the 1977 and 1997 instruments. The 2001 Act gives effect to listed EC–Swiss agreements. SI 728/2020 is the separate UK Withdrawal Agreement route. | Do not use a single umbrella EEA/Swiss label as proof of one legal source. Resolve each instrument's current status and territorial/personal scope, and inspect SI 398/2025 before source acceptance. |
| ISD guidance, forms and application portal | Discovery only; plausible but fragile as a pinned-URL strategy | Official pages expose update dates, form links, eligibility, EUTR4 review, and current portal instructions. The EUTR guidance has a dynamic Customer Service Portal route; EUTR1's saved PDF candidate dates from 2023 while the combined explanatory leaflet is from 2025. ISD and gov.ie processing times conflict. | A page-and-link discovery rule may be viable after testing stable identifiers, visible dates, metadata, parent-page rediscovery and body extraction. Do not automate portal submissions or capture personal case data. |
| Visa rules, office directory and mission instructions | Discovery only; manual/dynamic route | Official national pages identify Article 10 residence-card visa treatment, visa appeal exceptions effective 1 June 2026, AVATS instructions and visa-office coverage. DFA mission pages and local instructions vary. The 2021 short-stay family checklist is old. | Maintain directories and verify mission-specific sources; a fixed list of URLs would be fragile. Do not interact with AVATS or store applicant identifiers. |
| Registration and fee guidance | Discovery only; volatile | ISD records first registration, online appointments and fee guidance; SI 421/2025 is a separate fee-law candidate. Rolling appointment availability and service instructions can change independently from legislation. | Separate public, dated guidance monitoring from any booking/account workflow; reconcile legal fee and exemption conditions before use. |
| Procedure, remedies, oversight and privacy | Discovery only; heterogeneous sources | FOI and DPC pages expose review procedures; Ombudsman material expressly excludes decisions about asylum, citizenship, family reunification, residence and visas. Complaint workflows may collect private information. | Only public explanatory rules/pages are candidates. Keep each authority's jurisdiction distinct and exclude submissions, case files and personal data. |
| Family-status evidence and civil registration | Discovery only; partial | DFA authentication guidance identifies treatment of Irish public documents and references EU public-document exemptions; gov.ie marriage guidance lists evidence and foreign-divorce review. Comprehensive foreign-status recognition, adoption procedure and local registration practice remain open. | Useful supporting-document leads; no general foreign-document or civil-status rule established. |
| Courts and legal aid | Discovery only; incomplete coverage evidence | Courts Service has a searchable judgment surface; Order 84 and HC140 (2026) show current judicial-review and immigration-list procedure. The Legal Aid Board describes limited civil, protection and appropriate immigration/deportation services. Searchability and service descriptions do not establish comprehensive case coverage or eligibility for EUTR cases. | Candidate discovery only; identify corpus limits, public formats and legal-aid eligibility boundaries before any monitoring rule. |

## Repair priorities

1. **Inspect SI 398/2025 and reconcile the governing instrument.** Obtain the official text through an available eISB route, compare it with the amendment table and SI 548, record commencement and affected provisions, and locate a reviewed current text. Do not infer content from the instrument title or the amendment table alone.
2. **Specify repeatable eISB update discovery.** Enumerate annual SI indexes and amendments to selected ELI records, preserving exact record identifiers and amendment references. Determine whether eISB exposes reliable update timestamps or whether index snapshots/hashes are needed to detect new records and edits.
3. **Prototype only after the lawful route is confirmed.** Confirm actual response status, redirects, media type, payload identity and permitted retention; capture authorized bytes and hashes; separately replay conversion for SI HTML/PDF and Act XML; ensure outputs preserve sections, tables and amendment metadata.
4. **Reconcile official guidance and the legislative route.** Track ISD's parent index, EUTR page and form links; flag missing/new laws and conflicting processing details against gov.ie. Capture visible page dates and treat the portal's application steps as dynamic.
5. **Complete family-status and foreign-document route review.** Reconcile civil-registration guidance, DFA authentication, EU public-document exceptions and source-specific document rules; identify official adoption and foreign-status recognition routes where relevant.
6. **Build mission and remedy discovery from official parent directories.** Track current visa-office assignments, DFA mission paths, Courts.ie rule/practice-direction indexes and oversight scope pages. Document jurisdiction and corpus limits.
7. **Enforce privacy boundaries.** Do not submit AVATS, book appointments, authenticate to personal portals, collect application numbers, or store complaint and case materials as source content.

## Separate coverage limits

This is a proposed-route review, not a current-law opinion or complete Ireland source inventory. It does not rate mirror synchronization. It does not assign a verdict to a rule because no Ireland rule is implemented. It covers only the candidates and bounded searches recorded in the manifest; mission-level instructions, native-language completeness, full court-case coverage, current consolidated statutory text and all local authority practice remain open.

