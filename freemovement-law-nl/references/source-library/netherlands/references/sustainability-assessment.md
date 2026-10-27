# Netherlands source-route sustainability assessment

**Assessment date:** 25 October 2026

**Skill:** `assess-source-rule-sustainability` v0.2.0

**State:** 60 official external references accepted within scope, 3 exact routes not relied upon, 10 local texts accepted (6 statutory and 4 IND guidance pages), 0 topics accepted as adequate; country review remains incomplete.

## Ordinary use

The most sustainable ordinary route is to use the official publisher page directly. Wetten.nl exposes Dutch legislation as consolidated records with a stable BWB identifier and a displayed effective interval. Use the current government consolidation and note its date where version precision matters. A dated working text is preferable to rebuilding an amendment chain from Gazette fragments. Six local texts retain the publisher versions observed on 18 October 2026. Their Wetten.nl identifiers, canonical date versions, page modification metadata, raw-response hashes, and every article heading were checked against the archived official HTML. The publisher pages showed consolidated versions dated 1 August 2018 to 25 September 2026. Direct current-version checks on 25 October were rate-limited (HTTP 429), so these are accepted as last-observed versions, not certified as latest.

IND and NetherlandsWorldwide provide the relevant residence, family, visa, form, fee, appointment, and operational pages. Their content can change, so check the live page and linked form when using a deadline, document checklist, fee, or mission instruction. The review found page-specific limits that matter: IND's EU-family page was last updated 25 September 2026, while its residence-document model page was last updated 29 June 2026 and needs review against the EU card-format rules that took effect after that update.

## Link acceptance and local artifacts

The [source-acceptance register](source-acceptance.json) accepts 60 official links only for their listed page, instrument, publisher-policy, service, or discovery scope. It offers whole official websites for human review where direct page access, currency, a broken route, or operational details need inspection. Three exact routes are not relied upon: an obsolete visa checklist, a NetherlandsWorldwide route that returned 404, and a Rechtspraak help page that returned 403 in the research client. These responses do not establish publisher downtime.

The focused raw captures and converted candidates remain in the Monitor local-only archive as provenance. Six statutory texts were accepted under `documents/legislation/`, and four IND guidance pages under `documents/guidance/`. The archived nl-17 raw response and body show the 8 October 2026 update, matching the live page checked on 25 October. Its candidate header incorrectly annotated 17 June; this metadata discrepancy was corrected during review. Duplicate candidates and the inventory manifest remain provenance only.

## Optional retained copies

Auteurswet Article 11 provides the reuse basis for the six copied public-authority legal texts. For four IND pages, the [IND Proclaimer](https://ind.nl/en/proclaimer) checked on 25 October 2026 permits website content reuse if the source is named and warns that site information can be incomplete or out of date. The four local files identify and link their IND source. The registration-page copy covers the main HTML text only; its linked PDF forms are not copied. Government.nl separately states that CC0 1.0 applies to most text on its own website unless an item says otherwise; that policy does not extend to IND or other publishers. Link acceptance alone never establishes permission to copy. Forms and images need separate review. Raw captures remain provenance in the Monitor archive; no recurring retrieval rule has been accepted.

## Remaining sustainability and coverage work

- Confirm the current Dutch residence-card specimen and its status under Regulation (EU) 2025/1208. The IND model-2020 page predates the regulation's 3 August 2026 transition date.
- Map the remedies and decision deadlines for each EU-family decision type; the general IND objection/appeal page is not a decision-specific crosswalk.
- Review mission-specific appointment and outsourcing instructions and the Wet BRP, Besluit BRP, Regeling BRP, and municipal process for the relevant municipality.
- Establish how broadly Dutch immigration decisions are published in Rechtspraak and Raad van State search tools; neither search surface is treated as exhaustive.
- Determine the scope of publicly funded legal aid for EU-family immigration objections and appeals from the current Act and implementing criteria.

These open matters are recorded in the [issue-led coverage register](coverage-register.md). They do not make the official links unusable, but they prevent a country-complete finding.
