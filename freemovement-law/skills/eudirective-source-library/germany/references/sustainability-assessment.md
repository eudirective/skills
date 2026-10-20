Skill: assess-source-rule-sustainability v0.2.0

# Germany source-route sustainability assessment

Status date: 19 October 2026
State: 47 candidates; 44 texts converted as unaccepted review candidates (18 statutory records from 17 XML packages, plus 26 official pages/PDFs); two discovery pages had no stable text body and one BfJ URL returned 404; zero local copies accepted. The federal-law lane has a repeatable source-specific retrieval and conversion rule; the wider page pass is a one-time bounded capture.

## Assessment boundary

The [candidate manifest](candidate-manifest.json) covers federal legal-publication channels; residence/visa/mission sources; civil status/adoption; procedure/remedies; courts; privacy/oversight; public access and legal aid. Hesse and Bremen are regional samples only. Eighteen statutory records now have XML-derived review-candidate conversions. The other 29 records were attempted in the 19 October page-capture pass: 26 converted, two had no stable text body, and one current URL returned 404. This search is bounded and does not exhaust 16 Länder, municipalities, missions or courts.

The federal-law XML lane is implemented and exercised for all identified `national_legislation` records. This report rates that bounded lane separately from the still-unimplemented BGBl event monitor and the other source groups.

## Strongest proposed route: authentic publication plus consolidated text

The official federal gazette is the electronic Bundesgesetzblatt at `recht.bund.de`. The Federal Ministry of Justice says it has been the sole federal promulgation organ since 1 January 2023. Its official service documents stable ELI-style issue paths, rule-text and annex PDFs, ZIP issue packages, response-code checks and RSS feeds. This is a plausible no-registration route for discovering and preserving authentic federal promulgation events.

`Gesetze im Internet` provides continuously consolidated federal statutes and regulations, with HTML, PDF and XML ZIP/EPUB formats. Its official guidance states that the German legal norms are free to use and reuse and that an XML table of contents is available. The implemented rule re-fetches each candidate law's official index, follows its XML ZIP link, validates the package and act abbreviation, retains the publisher norm ID and XML build date, and converts the legal structure. Eighteen records across 17 law packages were saved; section-specific candidates are limited to their identified provisions. All outputs remain unaccepted.

**Federal consolidated-law lane: sustainable with limits (medium confidence).** The official route, reuse terms, index-to-package link, XML structure, identity checks and deterministic offline replay are demonstrated. Gesetze im Internet is the government-published working text, although the BGBl remains the authentic promulgation record. Record the consolidation date and the publisher's editorial notes; consult a specific BGBl act only for a known post-cutoff change, commencement issue, or conflict relevant to the review. A full Gazette-history reconciliation is not required. The BGBl ELI/RSS route may help locate such targeted updates; exhaustive issue coverage, seal verification, and correction recovery are separate monitoring enhancements, not prerequisites for using the consolidation.

## Currentness risks

Use the current consolidated text from the official Gesetze im Internet service as the legal-text source; do not compare every Bundesgesetzblatt issue by default. The FreizügG/EU text records amendment by 16 July 2026, BGBl. 2026 I No. 213. The AufenthG record flags a specific amendment dated 22 July 2026 as textually evidenced but not fully processed. That stated exception remains material: use a later consolidated edition if available or keep only the affected provisions unresolved. Preserve the edition date and the publisher's caveat.

The publication chain has two different payload types: authentic BGBl PDFs/ZIPs and separately maintained consolidated HTML/XML. PDF is durable and authentic but requires seal validation and careful deterministic extraction. XML may be easier to convert but needs schema and version checks. RSS is a discovery signal, not an authoritative text or archive by itself.

## Other proposed routes and limits

| Source group | Maturity | Proposed route evidence | Main unresolved sustainability issue |
|---|---|---|---|
| Federal consolidated-law XML lane | Converted review candidates | Official law index -> its XML ZIP link; 18 records across 17 packages; identity checks and replay pass | Not the authentic promulgated text; no signed BGBl issue reconciliation or historic-version retrieval; AufenthG and VwVfG XML carry editorial processing caveats. |
| Wider official-page capture | 26 converted review candidates; two shells and one 404 | Bounded, allowlisted capture and offline replay across the other 29 inventory entries | No source-specific recurring updater, parent-index link resolver, nationwide/mission completeness guarantee, or currentness reconciliation. |
| Authentic federal gazette monitor | Discovery-only | BGBl ELI paths, issue PDFs/ZIPs and RSS | Feed details and correction handling remain unimplemented. Use the consolidated law text as the working version; consult the Gazette for a specific material update or when authentic promulgation matters. |
| EU movement and immigration statutes | Converted local-copy candidates | FreizügG/EU, AufenthG, AufenthV and related federal provisions retrieved through the XML route | Distinguish EU, EEA, Swiss, UK-transition and German-citizen routes. The AufenthG and VwVfG copies carry the specific currentness caveats recorded above; these do not block use of unaffected provisions from the government consolidation. |
| Visas and mission practice | Discovery-only | AA guidance, Visa Handbook, Consular Services Portal, mission directory, AABGebV | Portal coverage and local instructions change by mission; fees change; stable PDF URLs may mask new content. Public metadata only; no personal application data. |
| Administrative procedure/remedies | Discovery-only | VwVfG § 2, VwGO, IFG, AA procedure notice | Federal missions are excluded from direct VwVfG application. Remonstration ended 1 July 2025. Remedies and deadlines remain notice-specific. |
| Residence service practice | Discovery-only | Bundesportal region selector plus Hesse/Bremen samples | Land/local records vary. Hesse is dated 2020; Bremen full page needs review. Nationwide coverage is absent. |
| Civil status/adoption | Discovery-only | PStG/PStV, EGBGB, FamFG, AdWirkG, AdVermiG, AdÜbAG and BfJ | Most statutes are carried candidates awaiting text/version inspection. Federal and Land responsibilities differ. |
| Courts/case law | Discovery-only | BVerwG decision search/ECLI and VG Berlin guidance | Publication is selective; one court’s material is not nationwide or complete lower-court coverage. |
| Privacy/information access | Discovery-only | BfDI contact finder, IFG guidance and annual report | Federal vs Land authority depends on controller. Annual reports are historical, not current complaint instructions. |
| Legal aid | Discovery-only | Justiz-Services Prozesskostenhilfe and Beratungshilfe | Forms may collect sensitive financial details. Monitor public information only; do not submit or retain case data. |

## Scope and procedure caveats

FreizügG/EU is a partial functional match to the Danish EU-residence seed, not an equivalent instrument. German-citizen family routes under AufenthG are distinct. Swiss nationals rely on a separate EU–Switzerland route; EEA and UK Withdrawal Agreement provisions need separate scope. No relationship label is a legal-equivalence conclusion.

Visa processing involves the Federal Foreign Office and missions; residence documentation involves Länder and local immigration authorities. Bundesportal content varies by region. BfDI competence also depends on the responsible controller. Do not treat a federal source as complete local practice.

The AA states that voluntary visa remonstration was abolished worldwide on 1 July 2025 while judicial review remains available. Use refusal notices and applicable law for the remedy and deadline; Berlin court material is local guidance only.

## Repair priorities before accepting a rule or claiming wider coverage

1. Use the government-published Gesetze im Internet consolidation and record its displayed build date and editorial notes. Check a specific Bundesgesetzblatt item only for a known material discrepancy, commencement question, or when authentic promulgation itself matters; do not reconstruct the full issue history.
2. The publisher flags a specific editorial lag on the AufenthG and VwVfG. Keep the dated consolidation as the working text and leave only provisions affected by that known lag unresolved until a later consolidation or targeted update resolves them.
3. Establish ELI/RSS completeness and recovery behavior, including duplicate events, issue gaps, corrections, republished issues and timeouts. Validate digital seals before extracting text.
4. Add historic-version retrieval and effective-date resolution for the laws where past wording may matter.
5. Retrieve AA, mission, Bundesportal, BfDI, BfJ and court candidates through constrained parent links; record visible dates and redirects. Never automate visa or legal-aid submissions.
6. Expand residence, court, privacy/oversight and legal-aid discovery across all Länder before claiming nationwide service coverage. Keep EU, EEA, Swiss and German-citizen family routes distinct.
7. Recheck the 2025 remonstration change against current AA guidance before writing procedural adapters.

## Coverage limits

The search found official leads in each requested broad class. All 47 candidate routes were attempted; 44 conversions are stored as review candidates, two responses were shells, and one listed URL returned 404. The 18 law conversions are stored as review candidates; raw XML ZIPs and retrieval state are under the ignored project `temp/germany/` path. BGBl feeds and seals were not exercised. Mission-specific rules, all 16 Länder, local authorities, comprehensive lower-court case law, full adoption/civil-status workflows, and current legal-aid forms remain open. No absence claim or source acceptance is made.
