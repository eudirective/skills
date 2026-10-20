# Liechtenstein source-rule sustainability assessment

Assessment date: 19 October 2026. Scope: the 40 candidates in [`source-list.md`](source-list.md) and [`candidate-manifest.json`](candidate-manifest.json). This reviews retrieval and conversion behavior, not legal currentness, legal advice, or coverage completeness.

## Implemented route and observed results

[`../sync_liechtenstein.py`](../sync_liechtenstein.py) performs ordinary allowlisted HTTPS GET requests with a 20-second timeout, a 24 MiB response cap, and a one-second delay. For Gesetze.li law records it first retrieves the stable LR/LGBl page, discovers the current-text iframe, then captures that exact frame and its version query. It preserves exact raw response hashes and produces Markdown from the legal body, official page content, or page-wise PDF text. PDF extraction uses pinned `pypdf==6.21.1`; `convert-pdfs` rebuilds it from preserved bytes and `verify` replays every conversion offline. A 19 October refresh saved and replay-verified 16 HTML and two PDF conversions; the two original PDFs remain byte-preserved; 16 requests received HTTP 403; four staging routes were skipped; one interactive form and one case-law application shell did not yield complete source texts. Accepted count is zero.

The change detector retains exact source hashes and ignores only observed transport variation: scripts, Drupal view IDs, CSRF and SiteImprove tokens, a Liechtenstein CSS cache timestamp, and the rotating Cloudflare email-protection fragment. Meaningful HTML changes are staged for review rather than accepted automatically. The observed email fragment change affected only a generated `href`; the same contact link retained its stable `mailto` path.

## Verdict

**Fragile for a bounded review-candidate capture; not sustainable yet for unattended source maintenance.** Confidence: medium for the observed retrieval behavior, low for ongoing reuse authorization and full source coverage. The accessible route is repeatable in this environment and offline replay is deterministic, but legal authenticity, recurring-use terms, blocked-route coverage, and several conversion forms remain unresolved.

| Rule dimension | Evidence | Remaining limitation |
|---|---|---|
| Identity | Gesetze.li law page IDs and the current iframe URL are recorded; candidate ID and both shell/frame hashes are retained. | Current consolidated text is not the authentic publication and may not establish the legally effective text. Verify LR/LGBl identity and effective dates against signed Gazette items. |
| Retrieval | HTTPS-only host allowlist, redirect checks, time/size limits, delay, explicit 403 and staging outcomes. No API registration or authentication was needed for accessible records. | Sixteen official requests returned 403 in this client. No retries, alternate challenge route, or bypass is attempted. Direct URL fetching does not rediscover all parent-page attachments or updates. |
| Payload | HTML identity and minimum body length are checked; current Gesetze.li text frame is separately captured. Exact source bytes and hashes are retained. Both PDFs are byte-preserved and text-extracted page by page. | PDF signature validation is absent. Interactive forms and the decisions JavaScript portal are not full source payloads. |
| Conversion | Deterministic HTML-to-Markdown and pinned PDF-to-Markdown extraction are replayed by `verify` from saved bytes. | German statute formatting, tables, footnotes, amendment annotations, attachments, layout, and page/section completeness need human comparison with the official source. |
| Change and review | Exact response hashes remain immutable; narrowly observed volatile fields are normalized only for change comparison. Substantive changes stage for review. | The script has one live refresh cycle; long-run version transitions and false-positive/false-negative behavior need more observations. |
| Reuse and publisher terms | Pages were retrieved through ordinary public GET without login or API registration. | The 2026 reuse framework, database conditions, signed Gazette rights, storage/transform rights, and recurring automated access have not been reconciled. A public download is not proof of bulk reuse permission. |
| Coverage | Accessible guidance, laws, oversight pages, court structure and legal-aid information are represented. | Gazette, EWR register, migration/visa pages and PDFs include 403 gaps; Swiss mission practice and selected decisions are inherently incomplete. Search coverage is bounded. |

## Sustainability risks

1. **Authenticity:** Gesetze.li's current consolidated text is a useful discovery and comparison source, while signed electronic LGBl PDF/A is the stated authentic publication from 2013 onward. The rule currently retrieves the consolidation but does not validate Gazette signatures or amendment chains.
2. **Reuse authorization:** The 2026 Information Reuse Act and EEA Open Data implementation need source-specific interpretation. No blanket permission for systematic copying, storage, transformation, or scheduled refresh has been established.
3. **Publisher blocks:** The LLV host returned HTTP 403 across multiple candidate routes. The failed requests are recorded; the rule does not emulate a browser challenge or use an unapproved route. Obtain a publisher-supported route or keep those sources manual.
4. **Text fidelity:** The current HTML and PDF extractors are deterministic but not legally validated against representative complex statutes. PDFs retain page boundaries, but tables, forms, links, annotations, layout, and attachments need separate review.
5. **Partial indexes:** The case-law portal is selected and exposes no individual decision through the captured shell. An empty search cannot be treated as proof that no relevant judgment exists.
6. **Jurisdiction boundaries:** PFZG, Liechtenstein's EEA-specific solution, the Swiss treaty route, third-country residence rules, and the EWR incorporation chain must remain distinct source identities.

## Required work before unattended use

- Reconcile current Information Reuse Act, Gazette publication rules, Gesetze.li terms, and dataset-specific permissions; document whether persistent automated retrieval and conversion are permitted.
- Reconcile a small set of PFZG/PFZV, AuG/ZAV, VEV, and LVG consolidated records to signed LGBl publications and effective dates. Validate PDF signatures and test page/section completeness.
- Ask the publisher for a supported route for LLV pages that return 403; otherwise document a periodic manual capture path.
+ Compare PDF page text and representative HTML conversions independently against the official sources; validate signatures where present and review tables, footnotes, forms and attachments. Keep e-services and the case-law search interface as discovery tools unless complete text records are individually identified.
- Run repeated refreshes across actual source changes before treating the comparison rules as stable. Continue to stage all changes for human review.

All current outputs remain unaccepted review candidates. The rule must not be presented as a complete or legally authoritative Liechtenstein source pack.
