# Czechia source-rule sustainability assessment

**Assessment date:** 25 October 2026
**Pack version assessed:** 0.4.5
**Register status:** 63 source records; 62 official external references accepted within recorded scopes; 41 accepted dated local copies; 2 incomplete captures represented by locator notes; 0 accepted topics; country review incomplete.
**Scope:** retrieval and replay rules, candidate promotion, and the repeatability limits of the one-time monitor/discovery capture.

## Summary

The e-Sbírka route uses its public page-data service to resolve a stable act record to a current publisher version and ordered text fragments. The adapter checks instrument identity, version metadata, page order, fragment identity, and deterministic conversion. The 17 dated legal copies remain accepted within their recorded scopes and the publisher's informative-text caveat.

The 43 prior candidate records are dispositioned: 41 local copies are accepted and stored under `documents/`; two incomplete captures have official-link locator notes there. Their pre-promotion conversions and the associated candidate/capture ledgers are indexed in the Monitor local research archive under origin `czechia-candidate-promotion-2026-10-25`. No candidate or capture-result files remain in the country pack.

The 62 raw response files from 19 October remain in the standard project temp tree and are indexed in the Monitor local research archive. Offline replay passed for all 17 e-Sbírka legal texts and all 13 official HTML guidance/index pages on 25 October 2026. This confirms the captured bytes reproduce the recorded conversions; it does not establish currentness after the recorded retrieval dates.

## Acceptance addendum — 25 October 2026

The 62 accepted official references retain their existing scope limits. Of 43 former candidates, 41 dated local copies are accepted: 17 e-Sbírka legal texts, 13 guidance pages, 6 forms with their native PDF files, and 5 discovery/index snapshots. Two incomplete captures are locator notes, not accepted source copies. Decree 429/2010 remains offered for whole-portal human review. No topic is accepted and the country review remains incomplete.

The 17 e-Sbírka references rely on the official page-data records retrieved on 19 October 2026, with identity, effective-from date, and `AKTUALNI` status recorded. The 13 official HTML guidance/index pages preserve their captured representations and have raw responses in the standard temp tree and Monitor archive. A separate 13-record Monitor batch covers six forms and seven mission/court/oversight captures; six PDFs remain as native files under `documents/forms/`, while the seven historical HTML response bodies are unavailable for replay.

## Rule assessment

| Lane | Evidence and controls | Sustainability limits | Verdict |
|---|---|---|---|
| e-Sbírka current legal text — 17 records | Public unauthenticated page-data route; recorded identity and version metadata; ordered page and fragment checks; response and conversion hashes. The prior record reports all 17 conversions replay-verified before promotion. | The page-data route is not the separately documented, versioned REST API. Offline replay passed for the 17 captured legal texts; the publisher labels consolidated texts informative, and a capture does not prove legal force or event-specific applicability. | **Fragile / medium confidence.** The route was demonstrated for these records. Capture fresh response bytes before relying on a new replay or freshness check. |
| Official guidance and index HTML — 13 records | Raw responses and the Monitor retrieval manifest are indexed; offline replay on 25 October 2026 passed 13/13, including accepted-document hash and conversion provenance checks. | Pinned URLs do not discover new pages. Main-region extraction and flattened tables need content review; linked attachments are not fetched. | **Fragile / medium confidence.** Suitable for refreshing known pages with review, not for claiming complete guidance or forms coverage. |
| One-time Monitor batch — 13 records | The Monitor archive contains prior conversions and response hashes. Six PDF originals are retained as native form files; the 7 HTML body responses are unavailable for replay. The incomplete NSS and UOOU records remain locator notes. | This was a bounded capture, not a maintained publisher-specific updater. Court searches, paginated mission directories, form links, and local mission practice need separate discovery rules. | **No sustainability verdict for an updater.** Recurrence and complete coverage are not implemented. |

## Open issues

- A new replay requires fresh official response bytes. Keep raw responses and changed conversions under the standard project temp tree, then archive them through Monitor before review; do not create a pack-level candidate or capture directory.
- The page-data route and schema may change. Keep the host allowlist, response-size limit, publisher identity checks, version checks, and explicit informative-text caveat.
- For retained text, check headings, tables, footnotes, and attachments where extraction creates a material risk or the whole conversion will be relied on.
- Build a parent-index resolver for volatile form links, and keep mission instructions scoped by jurisdiction and date.
- Review publisher reuse terms, source-language requirements, topical coverage, and whether discovered court/oversight materials are full primary decisions rather than directories or summaries.
- Coverage and dependency review remain partial. The selected court examples are not a repeatable case-law search.

## Verification record

- The Monitor local archive contains all 43 original Git candidate files, reclassified as 36 candidate-history records and 7 discovery records. Their indexed byte counts and SHA-256 values match the exact files in Git HEAD.
- Before the legacy paths were removed, all 43 candidate files and four pack reference manifests were checked against the synchronized GitHub `main` source-library snapshot at `86faf4787e44cfde38457da252ae355de7ff14b2`; Monitor archive reads and indexed byte counts/SHA-256 values matched all 47 files. The verified whole-library SHA-256 was `a569e3a3ff09a4f5722f9d0e21ea91c3c5738c15828bafba462d3b4f5a1b1a24`.
- All 62 raw response files were read back through `local_research_read`; each archived byte count and SHA-256 matches the corresponding file in the standard project temp tree.
- Current `documents/` hashes and source-register entries are checked separately from external-reference acceptance and topic coverage.
- Offline replay completed on 25 October 2026: all 17 e-Sbírka legal texts and all 13 official HTML guidance/index pages passed. Their 62 raw response files remain in project temp and are indexed in Monitor. The separate 13-record Monitor capture batch is not replayable from its seven missing historical HTML bodies; six native PDF originals are preserved in `documents/forms/`.
- Monitor runtime compatibility remains limited. The previous registered `check` action could not open its internal `candidate-manifest.json`; on 25 October the registered `verify` action returned ten `ENOENT` failures for obsolete `work/candidates/` paths, while no Czechia `inventory` or `accept` action is registered. These actions do not verify the promoted document set. Candidate promotion was reconciled against the local source registers and Monitor archive; this does not establish topic coverage or country completion.
