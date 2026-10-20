# Cyprus source-rule sustainability assessment

Assessment date: 19 October 2026  
Pack state: 44 candidates; 5 source texts converted and replay-verified; 6 shell pages; 31 HTTP 403 responses; 2 HTTP 404 responses; 0 accepted.

## Assessment boundary

The shared bounded HTTPS capture rule is implemented and replayable. It does not establish a complete Cyprus legal corpus, current consolidated versions, or authority to reuse the content. The low retrieval rate is a client-access limitation and must not be interpreted as proof that official pages or laws are unavailable. Search-index text is not treated as a full capture.

## Official publication routes

The Government Printing Office’s main and archive pages respond with interactive shells. The official Gov.cy service says that users can search Gazette issues and annexes. Most direct Gazette, Ministry of Interior/Migration, MFA, Ombudsman, Information Commissioner, and Data Protection Authority routes returned HTTP 403. The rule did not try alternate headers, cookies, browser challenges, or other bypasses.

A reliable alternate exists for one historical source: the official [Government Gazette issue PDF](https://www.mof.gov.cy/mof/gpo/gazette.nsf/All/5ECD762847398688C2258728003A22A7/%24file/A.4110%209.2.2007%20P.%20I%20Meros%20I.pdf?OpenElement=) for original Law 7(I)/2007 was retrieved as a 2.5 MB PDF, converted, and replay-verified. It is the original promulgated law, not current consolidated wording. Its amendments remain separate texts and need a verified chain.

The official Office of the Law Commissioner’s index is discoverable through Gov.cy search results and advertises an English consolidation of the free-movement law covering 2007–2023. The index returned 403 and its previously indexed direct PDF URL returned 404 in this capture environment. The Law Commissioner’s access-to-information consolidation route also returned 404. Do not treat either missing download as proof the text no longer exists; rediscover the current official file URL from the publisher index once accessible.

Official search indexing also reveals current Gov.cy pages for residence cards, MEU1/MEU2 forms and related family guidance. Direct page retrieval and web-page opening returned 403 in this environment. Those search results help identify the authoritative routes but do not provide replayable exact response bytes. Keep those records pending rather than substituting snippets.

## Conversion and candidate evidence

Adding source-declared HTML encoding support enabled deterministic conversion of three legacy CyLaw pages declared as Windows-1253, plus an N-Lex candidate and a Supreme Court page; the changed N-Lex output is staged for review. The CyLaw records are discovery candidates and their publisher status must be distinguished from official Government Gazette publications. The one captured official law is the 2007 Gazette PDF. No text is accepted.

The shared rule provides bounded downloads, official-host checks, TLS validation, exact response hashes, deterministic conversions, and offline replay. Its result is **fragile / low confidence** for Cyprus coverage because 31 routes still return 403, the core official portal pages are interactive, and source-specific legal identity/currentness validation is incomplete.

## Sustainability actions

1. Ask the Government Printing Office and Gov.cy/Migration Department for a stable public access route or machine-readable export for Gazette issues, current MEU guidance and forms. Do not infer an API or add automated access based on a search result.
2. Reacquire the Law Commissioner index and its current 2007–2023 consolidated PDF from a valid official link; confirm the file version and identify every post-2023 amendment.
3. Preserve original Gazette editions separately from consolidated text. Validate instrument number, issue date, amendments, language, and annexes before calling a text current.
4. Keep retrieval on ordinary TLS-validated HTTPS. Do not bypass 403 responses or treat search-engine snippets as source bytes.
5. For Ministry/MFA forms and guidance, establish parent-page link rediscovery and verify the linked file identity/version.
6. Define judicial coverage by court, index, date range, publication limits and stable change signals; interactive case search alone is not a complete corpus.
7. Review reuse rights before storing derived text for distribution; no general permission was established by this pass.

## Conclusion

One official historical Gazette law is now captured and replay-verified, and four other candidate pages convert. The current official legal consolidation and most government guidance remain inaccessible through this capture client. The rule is operational but not sustainable for complete Cyprus coverage until the Government Printing Office and ministry routes provide stable retrievable documents and currentness can be validated. All candidates remain unaccepted.
