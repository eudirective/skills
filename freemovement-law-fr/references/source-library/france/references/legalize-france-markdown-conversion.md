# Legalize France Markdown conversion and acceptance rules

**Document type:** project-authored retrieval and conversion procedure, not a legal source.
**Jurisdiction:** France.
**Reviewed:** 2026-10-31.

## Scope

Apply this procedure when using a pinned Legalize France Markdown archive to retrieve bounded French statutory text for the source library. The Legalize repository is a retrieval method; DILA/Légifrance remains the official publisher and authority. Its MIT software licence does not license statutory wording.

## Retrieval and version control

1. Record the Legalize France repository commit and exact file path. Do not use a moving branch as provenance.
2. Resolve the code by its official Légifrance code identifier, then resolve the exact section and article scope on the official publisher site.
3. Record the displayed official version cutoff, per-article commencement or amendment note where applicable, and the date checked. Treat the official page as a locator and current-version check, not as a substitute for retaining text where a source copy is required.
4. Keep the pinned Legalize snapshot and dated official-text comparison evidence in the Monitor's indexed local-only archive. Record their archive-relative paths and SHA-256 values in the acceptance entry. A URL is provenance/version metadata; it does not replace the retained text.

## Text selection and conversion

1. Select only the declared article or section identifiers. Preserve each article's full heading, paragraphs, numbered points, cross-references, punctuation, accents, and official version notes.
2. Compare the full selected text article by article with the current official consolidated text. Check the article identifiers and the body boundaries, not only hashes or headings.
3. If the Legalize snapshot is stale, incomplete, duplicated, or marks an article repealed incorrectly, do not copy that wording as current. Use the official current text or its DILA LEGI delta, record the reason, and retain only current text. Mark repealed articles as excluded when needed to explain a gap.
4. Markdown conversion may change structural presentation only: use headings for article labels and Markdown list syntax for equivalent enumerations. Do not paraphrase, normalize legal terms, remove qualifiers, renumber points, or silently merge distinct provisions.
5. Add a metadata header that clearly separates publisher, code identifier, retained scope, version/cutoff, official provenance locator, retrieval source/commit, reuse/attribution, and limits from the official statutory body.

## Acceptance and maintenance

Accept a retained copy only after all of these are recorded: official publisher and source identity; complete declared scope; text and legal-anchor comparison; attachment review or a reasoned not-applicable note; legal classification as official statutory text; reuse/attribution; and explicit limits. DILA LEGI text is attributed under Licence Ouverte / Open Licence 2.0. Recheck the official locator before date-sensitive use and replace a copy only through a new review branch, preserving the superseded copy under the repository's source-note archive process.

## Applied extracts

- [Code du travail, Articles L5221-5 to L5221-9 and L5221-11](../documents/legislation/fr-code-travail-articles-l5221-5-to-l5221-11.md)
- [Code de la sécurité sociale, Articles L160-1, L160-1-1 and L160-2 to L160-7](../documents/legislation/fr-code-securite-sociale-beneficiaries-l160-1-to-l160-7.md)
- [Code de l’éducation, Articles L131-1 and L131-1-1](../documents/legislation/fr-code-education-articles-l131-1-and-l131-1-1.md)
- [Code de la santé publique, Article L1110-3](../documents/legislation/fr-code-sante-publique-article-l1110-3.md)
- [Code de procédure civile, Article 1166](../documents/legislation/fr-code-procedure-civile-article-1166-adoption.md)
- [Code de justice administrative, Article R. 312-18](../documents/legislation/fr-cja-r312-18-visa-jurisdiction.md)
- [Code de justice administrative, Article R. 421-1](../documents/legislation/fr-cja-r421-1-deadline.md)
- [Code des relations entre le public et l’administration, Article L. 411-1](../documents/legislation/fr-crpa-l411-1-appeals.md)
