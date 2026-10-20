# Netherlands source candidates

**Status (19 October 2026):** all eight scoped source-list candidates have unaccepted review-candidate conversions; zero accepted. The wider 52-record monitor inventory has now been captured separately: 50 exact responses, 49 conversions replay-verified, one textless discovery shell, and two retrieval failures. These additional candidate pages do not establish full national coverage or become accepted sources.

The six Wetten.nl sources were retrieved from their official stable BWB identifiers and converted from the publisher's current HTML. Their pages record the consultation date, exact current version URL, and effective interval. The two IND guidance pages were extracted from their official `main` elements. The saved source hashes and conversion outputs are recorded in the retrieval manifest; all eight pass offline replay verification.

The Wetten.nl HTML route is **fragile** for sustainability purposes: the current-version redirect and version markers worked, but the endpoint is not a documented machine API in this implementation, the page structure can change, and reuse terms were not confirmed. IND pages can also change without a dependable version identifier. All output remains unaccepted pending source-scope review and stronger route/terms verification.

Run from this folder with `python3 sync_netherlands.py sync` and `python3 sync_netherlands.py verify`. Raw HTML captures are stored under the ignored repository `temp/netherlands/raw/` path.

- [Source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Retrieval manifest](references/official-page-retrieval-manifest.json)
- [Sustainability assessment](references/sustainability-assessment.md)
- [Expanded monitor source list](references/monitor-source-list-2026-10-18.md)
- [Expanded monitor candidate manifest](references/monitor-candidate-manifest-2026-10-18.json)
- [Expanded monitor capture ledger](references/monitor-candidate-manifest-2026-10-18-capture-results.json)
