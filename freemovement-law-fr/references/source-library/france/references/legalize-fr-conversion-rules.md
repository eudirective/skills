# France Legalize France retrieval and conversion rules

**Reviewed:** 2026-10-30  
**Use:** bounded primary-law extracts for the France source library. These rules do not authorize treating an entire Legalize France code file as current or as an official source.

## Authority and source status

DILA/Légifrance is the publisher and legal authority. A Légifrance URL is retained as a locator and provenance record; it is not the source document by itself. The library accepts a source only when a retained local file contains the verified French legal text or a verified native official record.

Legalize France is a third-party retrieval and Markdown conversion route. Pin the exact repository commit and file path. Record its `LEGITEXT` ID, `last_updated` value, file size and SHA-256. Treat `last_updated` as the repository snapshot date, not as proof of the law's version or currentness. The reviewed files at commit `e38417fd7b982b2df02fbe01f2960127a7bf9031` report `last_updated: 2026-04-03`.

Attribute statutory text to DILA/Légifrance under Licence Ouverte / Open Licence 2.0. Attribute the Markdown transformation to Legalize France at the pinned commit when its text is used. The Legalize repository's MIT licence applies to its software, not to statutory text.

## Retrieval and selection

1. Retrieve the exact pinned Markdown file and verify its code identifier, title, language, repository path, snapshot date, bytes and SHA-256.
2. Select a bounded, issue-relevant provision scope. Do not convert a full code solely because a file exists in the repository.
3. Locate each article by its exact article number and surrounding section. If the file contains duplicate article headings or historical text, compare each candidate occurrence with the official current version and keep only the version whose status and wording match. Never choose an occurrence based only on its position in the Markdown file.
4. Record the official Légifrance display cutoff and each relevant article's effective date separately from the Legalize snapshot date.

## Verification gate

For every retained article, compare the complete article body, paragraph order, numbered and lettered lists, cross-references, amendment notes, effective dates and abrogation state with the corresponding official Légifrance current article or DILA LEGI XML. Confirm both scope anchors and the ending article. A spot-check cannot verify a whole code. If one article is missing, stale, duplicated, truncated or mismatched, do not accept the candidate as a complete current code; accept only individually verified provisions and obtain the missing or corrected text from DILA/Légifrance.

## Conversion rules

- Preserve the code title, hierarchy, article number, French wording, paragraph and list order, punctuation, cross-reference numbers and legal notes.
- Remove Markdown link syntax only when retaining its visible label verbatim; preserve article identifiers and link-text wording. Do not translate, summarize, normalize spelling, repair citations or silently drop content.
- Select one verified current article instance. Exclude duplicate historical text and explicitly label repealed provisions; do not merge their wording into the current copy.
- For DILA XML, extract `BLOC_TEXTUEL/CONTENU` in publisher order. Preserve paragraph/list structure. Retain `NOTA/CONTENU` as a separate official version note and use `VERSIONS` plus `DATE_DEBUT`/`DATE_FIN` to establish the active version. Keep source XML, raw archive SHA-256, extracted XML SHA-256, conversion description and derived-text SHA-256 in the local-only capture archive.
- Place accepted French text under `documents/legislation/`. Include the official locator only as provenance/navigation metadata, state that the retained file is the source document, record license/attribution, and state the exact scope and limits.

## Findings applied on 2026-10-30

- **Code du travail:** Legalize Article L5221-5 omitted the DILA applicability note limiting the provision's application through 2026-12-31. The file also contained two Article L5221-8 entries; only the one matching the current Légifrance section was retained. Current Article L5221-5 was taken from the official DILA 2026-10-29 LEGI delta.
- **Code de la sécurité sociale:** Legalize omitted current Article L160-1-1, created by Law No. 2025-1403 and in force from 2025-12-31. Articles L160-1 and L160-2 to L160-7 were retained only after comparison with the current Légifrance section. Article L160-1-1 was taken from the official DILA 2026-01-02 LEGI delta.
- **Code de l’éducation:** retained Articles L131-1 and L131-1-1 matched the current Légifrance text.
- **Code de la santé publique:** Article L1110-3 matched the current Légifrance text. The adjacent Legalize Article L1110-3-1 was stale: the current text includes amendments effective 2026-07-01, so that article and the full-code snapshot were not accepted.
- **Code de procédure civile:** Article 1166 matched the current Légifrance text.

The five accepted local documents are bounded provision copies. The five Legalize files are not accepted as complete current codes. Other files in the Legalize directory remain subject to issue-led relevance review; directory presence alone neither creates a coverage gap nor proves legal equivalence.
