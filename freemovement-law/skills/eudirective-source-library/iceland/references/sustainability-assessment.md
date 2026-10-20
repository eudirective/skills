Skill: assess-source-rule-sustainability v0.2.0

# Iceland source-route sustainability assessment

Status date: 19 October 2026  
State: 28 candidates; 21 source responses saved, 20 conversions replay-verified, zero local copies accepted. A shared bounded capture/replay helper was exercised; no Iceland-specific archive importer is implemented.

## Assessment boundary

The [candidate manifest](candidate-manifest.json) and [source list](source-list.md) cover Icelandic EEA/EFTA free movement and family residence, entry and visas, publication and legislation, registration, administrative procedure and remedies, appeal decisions, public access, privacy, courts, and oversight. Iceland is an EEA EFTA State rather than an EU Member State; Switzerland is not an EEA Contracting Party. A shared bounded capture/replay pass saved 21 source responses and converted 20 candidate pages. Six Althingi requests returned 403, one court rules route returned 404, and one Ombudsman response had no extractable body. The results remain unaccepted.

The generic page-capture lane is **fragile** for the Iceland inventory: it converted 20 direct pages, but the core Althingi legislation could not be fetched and no source-specific archive/update rule exists. The Althingi route therefore remains **undetermined**; its archive bytes, latest edition link, SGML schema, and deterministic law-level extraction have not been verified.

## Strongest proposed route: Althingi law editions plus Gazette amendments

Althingi publishes dated Lagasafn editions in PDF and SGML ZIP formats. Its official archive page says the ZIP can be unpacked and read offline, including import into other systems or integration with other websites. Althingi's current indexed page reports edition 158a, Icelandic laws as of 1 October 2026, and says the SGML ZIP can be unpacked for offline import. One page snapshot exposed an older 157c link, while later open requests to the archive page and ordinary HTTPS requests for both 157c and 158a SGML ZIPs returned 403. No raw archive bytes were obtained. The official archive warns that laws passed after an edition date are not included; the current edition/file link must be reconciled before capture.

The publisher describes a low-maintenance route in principle: check the issue index, retrieve the corresponding dated SGML archive, preserve issue/date and hashes, and compare selected Acts. In this run the index and linked archive could not be downloaded by the ordinary client, so the route is promising by publisher description but **not demonstrated live**. The dated bundle is not a real-time amendment stream. Pair it with Stjórnartíðindi A-deild, whose electronic publication is legally effective, and preserve Gazette issue identity, publication date, and commencement date. The SGML schema, package completeness, per-Act identity, and deterministic conversion remain unverified.

The current Foreign Nationals Act route resolves to edition 158a and lists amendment citations and differing effective dates, including parts of Act 48/2026 effective on 1 December 2026. A future monitor must retain the consolidated issue and the authentic amending publication, and must not flatten future-effective text into an “already in force” status.

## Regulation consolidation risk

Use the official collection's linked Regulation 540/2017 PDF as the closest government-published text, recording that it states an in-force date of 19 June 2025 and document date of 10 April 2026. The collection separately lists amendments 669/2026, 724/2026, and 725/2026, so currentness after those listed items is unresolved. Do not compare every B-deild issue or require source-owner confirmation of the endpoint as a general gate; check whether a newer government consolidation resolves these three named updates, or keep their effect explicitly open.

## Proposed-route review

| Source group | Maturity | Proposed route evidence | Main unresolved sustainability issue |
|---|---|---|---|
| National legislation | Promising, discovery-only | Dated Althingi SGML ZIP and current Act pages; public publisher instructions permit import into other systems | No schema replay, content identity, edition-change monitor, amendment gap handling, or deterministic conversion has been implemented. The ZIP excludes later-passed laws. |
| Authentic legislation and regulations | Promising, discovery-only | Stjórnartíðindi A/B/C divisions; official rules make electronic publication legally effective | Gazette result discovery, completeness, stable search/query behavior, corrections, and reliable individual-record identity remain untested. |
| Consolidated immigration regulation | Working version with a known cutoff issue | Reglugerðasafn regulation record and linked PDF | The linked PDF predates listed 2026 amendments. Retain it as the closest government-published text with that date; resolve only the named 2026 changes that affect provisions in scope. A full chain audit is not required. |
| EEA/EFTA legal basis | Strong discovery route | Official EFTA EEA-Lex factsheet for Directive 2004/38/EC/JCD 158/2007 plus Icelandic Act 2/1993 and Foreign Nationals Act Chapter XI | No legal-equivalence assessment; applicable Icelandic rules and amendments need human review. |
| Immigration guidance and forms | Fragile for fully automated retrieval | Ísland.is central service pages, forms index, and agency-owned guidance | Pages and links may change without notice; no revision dates or feed were found; exact Icelandic counterpart was not located for the family guidance. Fees, forms, evidence standards, and processing data are volatile. |
| EEA/EFTA and Nordic registration | Not sustainable without source-owner reconciliation | Registers Iceland and Directorate guidance pages | One page states both three-month and six-month triggers; the entry page states six months. Nordic nationals have a separate channel. Do not encode the trigger until reconciled with the Act and source owner. |
| Visas and missions | Fragile | MFA C-visa country/mission list and separate D-visa instructions | Mission partners and submission locations change. Family-member visa exemption and local mission processing were not fully checked. No applicant data may enter the monitor. |
| Immigration appeal decisions | Partial, privacy-limited | KNU explains the publication route; Government portal provides individual decision pages | Published decisions are delayed until communication to the appellant, redacted, and not shown to be exhaustive. No stable feed or completeness proof found. |
| Courts and case law | Incomplete | Official Courts Administration portal and publication rules | No complete, stable, nationwide searchable corpus was verified; decisions may be anonymised or removed under publication rules. |
| Privacy, access, and oversight | Moderate for public guidance | Current legal pages, Data Protection Authority instructions, Parliamentary Ombudsman English page | Complaint forms contain personal data and must never be submitted by an automated monitor. Authority competence and current procedure should be linked to the responsible institution. |

## Sustainability and scope caveats

Ísland.is is a central public information and service portal. Its terms explain that pages may be maintained by the responsible public body and that information and links may change without notice. This supports parent-page discovery and human review; it does not by itself establish permission for frequent automated harvesting or guarantee stable endpoints.

The public-facing country label “EEA/EFTA” includes Switzerland in some Icelandic service pages, while the EEA Agreement does not include Switzerland. Icelandic law uses separate EEA and EFTA definitions; national arrangements and any Swiss route must be established from their own official instruments. Nordic registration and the Icelandic citizen return route also need separate records. Do not copy a Danish or Swedish route into Iceland based only on a shared topic.

KNU states that decisions with substantive outcomes are published after the final result has been communicated to the appellant, with personal and sensitive information removed. Court rules also require anonymisation in categories of decisions and may allow further redaction. This makes legal-case coverage selective and sensitive to privacy-driven deletion or redaction changes.

## Capture results and repair priorities

1. Reconcile the official edition index: the current search/index reports 158a (1 October 2026), while an opened index snapshot exposed 157c. Resolve the live page and exact SGML file URL through the publisher, then retry only ordinary TLS-validated requests; do not work around 403 responses. Capture archive bytes, issue/date, and publisher identity once accessible.
2. Use the latest Althingi consolidated edition as the working text. Record its cutoff and check only a known post-cutoff act or commencement date that affects the review; retain publication and effective dates separately.
3. Keep the government-linked Regulation 540/2017 PDF as a dated working text and identify the listed 2026 amendments as targeted possible gaps. Check their specific effect only for provisions in scope; do not reconstruct the full B-deild chain.
4. Ask Registers Iceland and the Directorate of Immigration to reconcile the three-month/six-month registration discrepancy and the inclusion of Swiss nationals under the EEA/EFTA public label.
5. Record Icelandic law and guidance as distinct from English public-service translations; identify a first-party Icelandic guidance counterpart or keep the translation as a user-facing lead only.
6. Inspect the Ministry's visa lists and current mission handoffs by country. Keep C-visas, post-approval D-visas, EEA/EFTA family cards, and ordinary national residence permits distinct.
7. Decide whether a manually refreshed KNU decision register provides enough value. If so, retain each decision ID and date, preserve redaction state, and report publication coverage as selective.
8. Search Supreme Court, Landsréttur, and district-court sources separately before describing court-law coverage. Respect privacy/redaction rules and never infer completeness from a single portal search.
9. Keep forms, visa applications, complaints, and personal case submissions outside automated retrieval and storage.

## Capture record — 19 October 2026

Twenty candidates converted and passed offline replay. The seven failures are `is-01` to `is-04`, `is-22`, and `is-24` (HTTP 403 from Althingi) plus `is-26` (404); `is-23` returned a page without extractable text. Six failures are 403s; the 21st saved response was the textless Ombudsman page. The official web search indexed the current Althingi issue and the archive download page, but direct capture of the index and SGML ZIP did not work.

## Coverage limits

Official discovery found the core legislation, EEA incorporation record, family-card route, supporting-document requirements, registration, C-visa channel, appeal authority and decisions, public-access law, privacy regulator, Ombudsman, and court publication rules. Native-language service-page discovery was incomplete; visa exemptions and mission practice were not fully researched; regional and local practice, every case-law repository, and source-use terms for third-party mission partners were not covered. No Iceland-specific source updater or SGML conversion rule is implemented. The generic page-capture result is fragile, while the Althingi archive route remains undetermined.
