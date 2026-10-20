# Norway source candidates

This pack contains 54 candidate sources found from the Danish EU free-movement residence seed and the wider source taxonomy. Norway is an EEA EFTA State, not an EU Member State. Keep Norwegian implementation, EEA incorporation and EFTA/Swiss routes distinct.

## Capture state (19 October 2026)

- 32 candidates have source bytes saved; 31 have converted Markdown.
- Five changed-source conversions are staged in `../../temp/norway/pending/` for review.
- One eInnsyn response is a JavaScript shell with no extractable source body.
- Twenty-one routes failed with HTTP 403 or a network error; local Avdeling II regulations have no package in the documented public API list.
- No source is accepted.

The live Lovdata API list reported the current-law, central-regulation and 2026 Avdeling I packages last modified on 17 October 2026. The capture keeps the exact list, package sizes, modification times, archive hashes, and selected member hashes in [the capture results](references/norway-capture-results.json). The archive-backed set includes the Immigration Act and Regulations, EEA Act, Public Administration Act, Public Information Act and Regulation, Personal Data Act, Legal Aid Act, and current worker-mobility legislation. It also retains the repealed 1992 worker-mobility text as historical context and the not-yet-effective 2025 Public Administration Act as a commencement watch.

## Retrieval and conversion rule

Run `python source-library/norway/sync_norway.py sync` from the source-library work root to refresh the no-auth Lovdata public-data list and required current packages, then recheck all candidate routes. The rule uses the documented `publicData/list` and `publicData/get/{filename}` endpoints, validates listed byte sizes, bzip2 data, safe archive members, stable Lovdata IDs and publisher version metadata, and stages changed outputs for review. It does not scrape Lovdata record pages systematically or use API-key-only `structuredRules` routes.

Run `python source-library/norway/sync_norway.py verify` to check package/list/source hashes and replay each conversion offline. The converter preserves publisher metadata, chapter and section headings, article text and amendment notes from official Lovdata XHTML. Other official pages use the shared bounded HTML/JSON/PDF converter.

## Coverage limits

The current public package set does not expose Avdeling II/local regulations. The Avdeling I archive candidate is an index of 1,114 records, not conversion of every Gazette item. UDI and UDI Regelverk direct GETs returned 403 in this environment; the public UDI candidate records remain unresolved even where current pages are visible in search indexes. eInnsyn returned only a script shell. Statsforvalteren's legal-aid and apostille guidance were captured from current regional pages; the obsolete apostille URL returned 404 and was replaced with the captured current service route. UNE's practice database is a representative selection and the court candidates are selected publication channels, not comprehensive decision corpora.

Use the [source list](references/source-list.md), [manifest](references/candidate-manifest.json), and [sustainability assessment](references/sustainability-assessment.md) for per-candidate state. Captures remain unaccepted review candidates.
