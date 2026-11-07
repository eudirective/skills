# Austria Legalize conversion rules

## `legalize-at-ris-consolidated-v1`

Applies only to the verified full consolidated Informationsfreiheitsgesetz (IFG), RIS Gesetzesnummer 20012537, Legalize file `at/AT-20012537.md`.

1. Resolve the current RIS consolidation page and confirm the statute number, title, in-force status, displayed consolidation date, and amendment list.
2. Retrieve the Legalize file from a pinned commit. Record repository, file path, commit, Git blob SHA, and snapshot metadata.
3. Remove the Legalize YAML frontmatter and generated top-level heading from the body; record provenance and attribution in the local document header.
4. Remove only the standalone repeated display label consisting of “Abkürzung” followed by “IFG”. Do not remove or rewrite legal text, substantive headings, preamble, paragraph numbering, references, notes, punctuation, or amendment language. No translation or editorial normalization is allowed.
5. Compare every section body against the current official RIS section pages or accepted official RIS captures. For this IFG snapshot, §§ 1–20 matched 20/20 after this label removal and Markdown/whitespace normalization only.
6. Record RIS as the authoritative publisher and attribute the source data to RIS/Bundeskanzleramt under CC BY 4.0. The Legalize pipeline’s MIT license is separate from the legal text/data license.
7. If any section, amendment, statute identity, or current-version check differs, do not refresh or promote the local copy until the discrepancy is resolved. Recheck against RIS on every Legalize snapshot update.

This is a single-source rule. It does not authorize conversion or acceptance of other Austrian Legalize statutes without separate identity, current-version, complete-text, and official-body comparisons.

## `legalize-at-ris-section-v1`

Applies only to the following verified sections: AVG §§ 17 and 73 (`at-avg-17`, `at-avg-73`) and VwGVG §§ 7–8 (`at-vwgvg-7`, `at-vwgvg-8`). The verified source files are `legalize-dev/legalize-at/at/AT-10005768.md` (blob `3f91809405497da9e0789aa93c9a47e888d07920`) and `legalize-dev/legalize-at/at/AT-20008255.md` (blob `5c77501f66968e9fb47139e004654b725787b0e9`) at commit `30b7ded29545baa1079dc2ab8b2eef9193df3f59`.

1. Treat Legalize only as the retrieval copy. Resolve the statute and requested section from the official RIS current-section record; Legalize metadata is not authoritative for legal status or version.
2. Extract only the specifically requested section. These four section bodies matched both the accepted RIS captures dated 19 October 2026 and the current official RIS text checked on 29 October 2026. Full-act equivalence was not checked.
3. Where a file repeats a section, select a body only when its full operative text matches the official section; stop if candidate copies disagree or the requested section is ambiguous.
4. Compare section numbering, headings, every paragraph, embedded lists, notes and punctuation. Formatting-only whitespace/Markdown normalization is permitted for comparison, not as a license to rewrite the stored text.
5. Recheck against RIS on each candidate update. Never use this rule to retrieve or accept any other section or full statute.

The AVG candidate has an inconsistent `last_updated` stamp alongside 2026 amendment metadata. The VwGVG candidate incorrectly labels the act repealed despite the current RIS consolidation. These fields must not be carried forward as legal-version evidence.
