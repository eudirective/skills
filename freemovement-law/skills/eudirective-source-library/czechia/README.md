# Czechia national source pack

**Status (21 October 2026):** 43 records: 17 official e-Sbírka legal-text references are accepted within dated, narrow scopes based on the portal's current-version metadata and exact responses retrieved on 19 October; 0 local conversions are accepted. The 13 guidance/index pages and 13 forms, mission, court, and oversight discovery pages remain review candidates. The e-Sbírka texts retain the publisher's “informative” caveat, and their converted Markdown remains unaccepted. This does not make other official links unusable: a human-reviewed government page may be used within its displayed scope without capture or conversion. Prefer a government consolidation; otherwise use the closest government-published text with its cutoff. Do not require a full Gazette history by default. Raw bytes are in project temp, outside the library mirror.

- [Source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Source acceptance register](references/source-acceptance.json)
- [e-Sbírka current-text captures](references/esbirka-open-data-captures.json)
- [Monitor/discovery capture subset](references/monitor-pass-2026-10-19.json)
- [Monitor/discovery capture ledger](references/monitor-pass-2026-10-19-capture-results.json)
- [Sustainability assessment](references/sustainability-assessment.md)
- [Pack instructions](SKILL.md)

The optional local-copy adapter uses e-Sbírka's public, unauthenticated page-data service. For each stable act record, it resolves the publisher's current version, checks the act citation and effective-from date, captures ordered text-fragment pages, and converts XHTML to Markdown. It stores response hashes and replay data for retained copies; it does not use the separately documented registration-gated REST API. The 17 official e-Sbírka references are accepted only as the dated versions recorded in the acceptance register, retrieved 19 October 2026. Recheck the stable record for later use. Record the publisher's “informative” label and displayed effective date; consult a particular promulgation only for a known material discrepancy or commencement issue. The local conversions remain unaccepted.

To refresh retained legal copies, run `python scripts/sync_esbirka_open_data.py sync` (optionally with candidate IDs), then `verify` to replay saved conversions offline. These commands are not required to use official source links. The existing Node workflow handles retained guidance copies; its former date-bound PDF route is superseded for local statute capture. The 13 monitor/discovery records remain separate from legal texts.

The inventory covers Czech national law and official administrative, consular, court, and oversight materials relevant to EU free movement and family members. It is not an exhaustive account of Czech law. Official Czech guidance also describes similar free-movement rights for Icelandic, Liechtenstein, Norwegian, and Swiss citizens; Switzerland is not an EU or EEA EFTA member, and UK Withdrawal Agreement cases remain separate.
