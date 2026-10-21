# Netherlands source-route sustainability assessment

**Assessment date:** 21 October 2026

**Skill:** `assess-source-rule-sustainability` v0.2.0

**State:** official source links reviewed; 59 external references accepted within scope, 3 exact routes not relied upon; no local copies or topics accepted; country review remains incomplete.

## Ordinary use

The most sustainable ordinary route is to use the official publisher page directly. Wetten.nl exposes Dutch legislation as consolidated records with a stable BWB identifier and a displayed effective interval. Use the current government consolidation and note its date where version precision matters. A dated working text is preferable to rebuilding an amendment chain from Gazette fragments. Human review of an official link is sufficient; a local copy is optional.

IND and NetherlandsWorldwide provide the relevant residence, family, visa, form, fee, appointment, and operational pages. Their content can change, so check the live page and linked form when using a deadline, document checklist, fee, or mission instruction. The review found page-specific limits that matter: IND's EU-family page was last updated 25 September 2026, while its residence-document model page was last updated 29 June 2026 and needs review against the EU card-format rules that took effect after that update.

## Link acceptance and local artifacts

The [source-acceptance register](source-acceptance.json) accepts 59 official links only for their listed page, instrument, service, or discovery scope. It offers whole official websites for human review where direct page access, currency, a broken route, or operational details need inspection. Three exact routes are not relied upon: an obsolete visa checklist, a NetherlandsWorldwide route that returned 404, and a Rechtspraak help page that returned 403 in the research client. These responses do not establish publisher downtime.

The previous eight-source conversion pass and the wider 52-source conversion pass remain unaccepted artifacts. Their captures and replay hashes are evidence about those past conversions only. The wider pass used broad `body` extraction for some dynamic pages; this is not accepted as semantic validation. No extraction, hashing, replay, machine API, or recurring update job is required to use the official links.

## Optional retained copies

If a future use case requires local copies or recurring monitoring, choose that work source by source. First check whether the publisher provides a usable download or export and whether retaining it is necessary. For a law, compare the relevant provisions against the official page; for a PDF specimen or form, inspect the actual attachment. Keep raw captures and conversion rules only when reproducibility is a real requirement. No blanket license or reuse permission is inferred from this assessment.

## Remaining sustainability and coverage work

- Confirm the current Dutch residence-card specimen and its status under Regulation (EU) 2025/1208. The IND model-2020 page predates the regulation's 3 August 2026 transition date.
- Map the remedies and decision deadlines for each EU-family decision type; the general IND objection/appeal page is not a decision-specific crosswalk.
- Review mission-specific appointment and outsourcing instructions and the Wet BRP, Besluit BRP, Regeling BRP, and municipal process for the relevant municipality.
- Establish how broadly Dutch immigration decisions are published in Rechtspraak and Raad van State search tools; neither search surface is treated as exhaustive.
- Determine the scope of publicly funded legal aid for EU-family immigration objections and appeals from the current Act and implementing criteria.

These open matters are recorded in the [issue-led coverage register](coverage-register.md). They do not make the official links unusable, but they prevent a country-complete finding.
