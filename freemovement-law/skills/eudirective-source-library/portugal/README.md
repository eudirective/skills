# Portugal national source pack

**Status (19 October 2026):** the scoped inventory has 7 candidates; one AIMA guidance candidate is converted, while six Diário da República law-page requests returned the same 2,346-byte OutSystems JavaScript shell with no legal text. The expanded monitor inventory has 60 candidates across laws, guidance, forms, services, oversight and court discovery; 46 exact responses were saved, 19 pages converted and replay-verified, 27 were discovery shells without a stable text body, and 14 retrievals failed. Zero sources are accepted; neither inventory is a completeness claim.

- [Source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Expanded monitor source list](references/monitor-source-list-2026-10-18.md)
- [Expanded monitor candidate manifest](references/monitor-candidate-manifest-2026-10-18.json)
- [Expanded monitor capture ledger](references/monitor-candidate-manifest-2026-10-18-capture-results.json)
- [Scoped retrieval attempt](references/retrieval-pass-2026-10-19-capture-results.json)
- Retrieved review candidates are under `candidates/`.

The pack records official national laws, operational guidance and procedural sources relevant to EU free movement, family members, civil status, adoption and remedies. EU law stays in the shared core. Direct HTTP retrieval from the official Diário da República URLs currently exposes the same JavaScript application shell rather than legal text; browser-rendered display is not yet a reproducible pack rule. The expanded monitor capture is a bounded ordinary HTTPS GET pass with exact source hashes and a separate output namespace; it is not an unattended sustainable update rule. Each candidate still needs source identity, current-version, language, extraction quality, reuse-terms and scope review. France-Visas was captured from browser-rendered official text after direct HTTP download returned 403; its raw HTML capture remains outstanding.
