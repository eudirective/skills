# Czechia national source pack

**Status (19 October 2026):** 43 candidate records: 17 current legal texts, 13 official guidance/index pages, and 13 forms, mission, court, and oversight discovery pages have been captured and converted as review candidates. All 43 were replay-verified against their captured source bytes; 0 sources are accepted. Raw source bytes are kept in project temp and are not part of the library mirror. Captures do not establish legal completeness, current applicability, or trust.

- [Source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [e-Sbírka current-text captures](references/esbirka-open-data-captures.json)
- [Monitor/discovery capture subset](references/monitor-pass-2026-10-19.json)
- [Monitor/discovery capture ledger](references/monitor-pass-2026-10-19-capture-results.json)
- [Sustainability assessment](references/sustainability-assessment.md)
- [Pack instructions](SKILL.md)

The legal-text adapter uses e-Sbírka's public, unauthenticated page-data service. For each stable act record, it resolves the publisher's current version, checks the act citation and effective-from date, captures every ordered text-fragment page, and converts the XHTML fragments to deterministic Markdown. Exact metadata and page JSON responses are hash-pinned in the configured project temp tree; the capture ledger retains stable pack-relative `work/raw/` paths. Unaccepted Markdown candidates are organized under `candidates/legislation/`. This does not use the separately documented registration-gated REST API. The publisher describes consolidated text as informative, so version and promulgation review is still required before legal reliance.

Run `python scripts/sync_esbirka_open_data.py sync` to retrieve all 17 identified legal texts, or add candidate IDs for a focused refresh. Run `python scripts/sync_esbirka_open_data.py verify` to replay saved conversions offline. The existing Node workflow handles guidance; its former date-bound PDF route is superseded for statute retrieval by this adapter. The 13 monitor/discovery captures use the shared bounded capture ledger and remain distinct from current legal texts.

The inventory covers Czech national law and official administrative, consular, court, and oversight materials relevant to EU free movement and family members. It is not an exhaustive account of Czech law. Official Czech guidance also describes similar free-movement rights for Icelandic, Liechtenstein, Norwegian, and Swiss citizens; Switzerland is not an EU or EEA EFTA member, and UK Withdrawal Agreement cases remain separate.
