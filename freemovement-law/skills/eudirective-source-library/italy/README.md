# Italy national source pack

**Status (19 October 2026):** the five prioritized candidates remain unaccepted; three Normattiva statutes have full-text candidate conversions and one older MAECI guidance capture remains currentness-unverified. The wider 42-record monitor inventory now has 34 exact responses and 33 replay-verified conversions; one discovery page returned no stable text, and eight requests failed. Zero sources are accepted, and this is not complete coverage.

- [Source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- Retrieved review candidates are under `candidates/`.
- [Expanded monitor source list](references/monitor-source-list-2026-10-18.md)
- [Expanded monitor candidate manifest](references/monitor-candidate-manifest-2026-10-18.json)
- [Expanded monitor capture ledger](references/monitor-candidate-manifest-2026-10-18-capture-results.json)

The pack records official national laws, operational guidance and procedural sources relevant to EU free movement, family members, civil status, adoption and remedies. EU law stays in the shared core. Three statutes were retrieved as 200 article-level responses through Normattiva's public current-text pages and converted into full-act review candidates. Their hashes and deterministic conversion replay are recorded in [the retrieval manifest](references/normattiva-retrieval-manifest.json); none is accepted. The article-loading route is an undocumented page interface and remains fragile. The expanded monitor pass used bounded ordinary HTTPS GETs and exact response hashes; outputs are stored separately under `monitor-candidates/`. It is a one-time review capture, not a recurring update rule. Some PDF conversions emitted font mapping warnings and require human text-quality review. The Ministry of Foreign Affairs pages redirect direct retrieval clients to a Radware challenge, although their current pages can be read through the standard web view. One earlier English FAQ capture is retained without currentness proof. France-Visas was captured from browser-rendered official text after direct HTTP download returned 403; its raw HTML capture remains outstanding. See the [sustainability assessment](references/sustainability-assessment.md). This pack and its 42-record monitor inventory are not completeness claims.
