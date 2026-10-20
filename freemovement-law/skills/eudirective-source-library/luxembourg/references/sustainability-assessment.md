# Luxembourg source-rule sustainability assessment (2026-10-19)

## Scope and result

The 42-record register covers laws, official guidance, forms, visas and missions, procedure, remedies, case law, oversight, civil-status evidence, and legal aid. A bounded retrieval and conversion rule is now implemented for direct official pages and Legilux legal texts. It captured 38 records; 35 were converted to unaccepted review candidates, three public portal shells yielded no source body, and four direct candidate URLs returned HTTP 404. None is accepted into the trusted corpus.

Offline verification passes for all 35 conversions and the three retained PDF byte streams. The verifier checks exact source hashes and deterministic Markdown replay. Changed HTML captures are staged under `temp/luxembourg/pending/` so they do not replace earlier candidate artifacts without review.

## Implemented route

- **Legislation:** For nine official ELI candidate URLs, the sync rule requests the corresponding Casemates URL with `Accept: application/xml`, validates the final HTTPS host and LegalDocML media type, preserves exact XML bytes, and converts the LegalDocML body with article/section structure. The XML is reproducible and suitable for review capture. Casemates documents CC BY 4.0 for its identified dataset; this is not evidence of reuse permission for other publishers or all linked materials.
- **Official HTML:** Other candidates use ordinary allowlisted HTTPS GET with redirect-host checks, one-second spacing, a 25-second timeout and a 24 MiB cap. The converter extracts a primary page region and records the source URL, final URL, timestamp, media type and hashes. It does not interact with forms or authenticate.
- **PDFs:** Three official PDFs are retained byte-for-byte and converted with pinned `pypdf==6.21.1`; each page is marked in the Markdown. Hash-preserved capture and text-layer extraction do not verify electronic signatures or detect text that requires OCR.

The scripts are `sync_luxembourg.py` and the shared `sync_candidate_pages.py` helper. The per-country dependency is listed in `requirements.txt`.

## Source-specific findings

The nine LegalDocML texts include the Immigration Law, its original act, the 2008 formalities regulation, the 2024 amendment, procedure/access/data-protection laws and civil-status legislation. Legilux states that consolidated texts are documentary and have no legal force. A consolidation is therefore a readable current-text aid; the authentic Mémorial publication and amendment/rectification chain still need to be reconciled before legal reliance. A pinned ELI URL is not by itself a complete recurring version-discovery rule.

Twenty-three HTML candidate pages converted. Eighteen differed from earlier raw captures and are staged pending review. Some are mutable Guichet guidance and attachment pages; they need parent-index rediscovery, linked-form checks, language/date comparisons and publisher-specific reuse review. Three portal pages (N-Lex discovery, Casemates home and its ELI reference page) returned only shells, not source text. Four candidate pages returned 404: `lu-11`, `lu-19`, `lu-20` and `lu-42`; rediscover these from current parent pages rather than treating the error as proof that the procedure no longer exists.

The PDFs include a coordinated immigration regulation applicable from April 2023 and two nationality lists. The coordinated regulation predates the 2024 amendment/rectification and is only a comparison artifact. The visa lists have mutable attachment paths and no reliable version identity in their URLs; rediscover them from the current ministry parent page and compare them with current Schengen law.

## Sustainability judgment

- **Legilux/Casemates retrieval and replay:** **Sustainable with limits** for bounded capture of known ELI records (medium confidence). The official XML response is structured, host-validated, byte-hashed and replayable. Ongoing operation still needs ELI-prefix discovery, version/change detection, authentic Mémorial reconciliation, annex/rectification checks and a clarified reuse boundary for content outside the documented dataset.
- **Direct HTML capture:** **Fragile** for recurring use (medium-low confidence). Retrieval and replay work, but source pages change, candidate URLs can disappear, and page conversion does not discover changed parent links, language variants, forms or attachments. Use a parent-index refresh and explicit changed-output review.
- **PDF capture/conversion:** **Fragile** for recurring use (low confidence). Exact bytes and text extraction replay, but the ministry coordinated PDF is stale, visa attachment paths are mutable, signature authenticity is unchecked, and scans would need a separately reviewed OCR path.
- **Whole register:** **Not sustainable for unattended current-law monitoring**. A repeatable fetch is not proof of currentness, legal authority, completeness, or permission to republish. Keep all outputs as review candidates until those issues are resolved by source class.

## Actions before trust promotion

1. Reconcile current immigration consolidations against the authentic Mémorial acts, including the 2024 A262 amendment and A283 rectification; re-resolve each ELI to its newest version.
2. Implement a supported discovery/change query for ELI-prefix records and verify that it covers amendments, repeals, corrigenda and attachments.
3. Rediscover the four missing guidance records and the three portal-only surfaces from first-party parent pages; preserve failed URLs as audit evidence.
4. Check the current Guichet and ministry parent pages for linked forms and attachments, including the visa nationality lists, with language-specific dates and version IDs.
5. Confirm reuse conditions for Guichet, ministries, Justice/CNPD/Ombudsman pages and third-party-linked attachments; do not extend Casemates CC BY 4.0 beyond its documented dataset.
6. Review the 18 changed HTML candidates, ensure there is no boilerplate-only or incomplete extraction, and compare captured page dates with the publisher's visible dates.
7. For PDFs, validate signatures where present and add OCR only when the original is image-based; keep extracted text linked to the immutable original bytes.
8. Assess completeness and update cadence for the administrative-court archive and oversight decisions. Search-result absence is not evidence that no decision exists.
