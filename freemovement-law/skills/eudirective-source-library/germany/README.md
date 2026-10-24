# Germany source candidates

**Status (19 October 2026):** 47 candidates; 44 texts converted as unaccepted review candidates (18 statutory records from 17 official XML packages and 26 other official pages/PDFs); two discovery pages returned shells without stable text, and one BfJ URL returned 404. All 44 conversions pass offline replay; zero local copies are accepted. The inventory also covers authentic gazette discovery, visa and mission practice, regional residence services, procedure, courts, privacy and oversight, adoption/civil status, and legal aid.

**Link decisions (23 October 2026):** 12 official external references are accepted within stated scopes; 3 proposals remain in human review. The 44 local conversions remain unaccepted.

The 23 October verification initially could not run in this checkout because its ignored `temp/germany/raw/` folder was absent. The 17 hash-addressed raw XML ZIP snapshots were recovered from the parallel local `/tmp/public-data` checkout and copied here; all matched the source hashes in the manifest. Running `python3 sync_germany.py verify` then reproduced and verified all 18 statutory conversions at their recorded XML build dates. This confirms deterministic replay from the captured bytes, not later source currentness or acceptance of any local copy.

The law retrieval rule refreshes each statute's official Gesetze im Internet index, follows the XML ZIP link published there, validates the archive and statutory abbreviation, and stores the publisher norm ID, XML build date, exact URLs, and source hash. Three candidates are provision-specific excerpts from the complete official package. The generated Markdown preserves the statute's section and paragraph structure. The 18 conversions pass deterministic offline replay.

The publisher says German legal norms are free to use and reuse. Prefer the latest official Gesetze im Internet consolidation as the working text and record its publisher date, cutoff, and editorial notes. The electronic Bundesgesetzblatt is the authentic federal promulgation source; use it to resolve a specific discrepancy, known post-cutoff change, or commencement question, rather than reconstructing the whole amendment history. The AufenthG and VwVfG package metadata carries editorial-processing notes that remain targeted checks. None of these conversions has been accepted into the trusted legal corpus.

Run from this folder with `python3 sync_germany.py sync`, `python3 sync_germany.py convert`, and `python3 sync_germany.py verify`. Raw XML ZIP files and retrieval state are stored under the ignored repository `temp/germany/` path; accepted-source files are not changed by this rule.

The 29 non-law discovery records were also attempted through the bounded official-page capture workflow. Their results are in [the discovery-pass manifest](references/discovery-pass-2026-10-19.json) and [capture ledger](references/discovery-pass-2026-10-19-capture-results.json). This pass validates and replays the saved outputs but does not implement a durable updater for those source classes.

- [Candidate source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Retrieval manifest](references/gii-retrieval-manifest.json)
- [Sustainability assessment](references/sustainability-assessment.md)
