# Czechia source-rule sustainability assessment

**Assessment date:** 21 October 2026 (detailed retrieval-route review conducted 19 October)
**Pack version assessed:** initial retrieval design 0.4.0; current pack 0.4.3
**Manifest:** 63 records; 62 accepted official external references within stated scope; 1 Decree 429/2010 link pending whole-portal human review; 0 local copies and 0 topics accepted
**Scope:** active legal and guidance acquisition rules, plus the repeatability limits of the one-time monitor/discovery capture.

## Summary

The pack now has replayable conversions for 17 current e-Sbírka legal texts, 13 official guidance/index pages, and 13 monitor/discovery pages. The legal route was repaired after the registration-gated REST API proved infeasible: the capture uses e-Sbírka's public page-data service, which the official web application itself uses, without an account or API key. This route resolved all 17 records and supplied effective-version metadata plus ordered text fragments. It is technically demonstrated but not yet a guaranteed publisher interface.

No local copy has been accepted. This does not block use of a reviewed official source link within its displayed scope. For retained conversions, review the relevant content and use broader comparison only when the conversion is lossy or the whole converted text will be relied on. The initial 43-record inventory was not a completeness claim. The current 63-record register also does not establish complete legal coverage.

## Acceptance addendum — 21 October 2026

The 17 e-Sbírka legal-source references are accepted for external use within dated scopes. The official portal identified each retrieved record as `AKTUALNI`, with instrument identity, effective-from date, and ordered text fragments; the exact response and metadata hashes are in the capture ledger. The source references can be used as the government-published working texts for those recorded versions, preserving e-Sbírka's informative-text caveat. For later use, recheck the stable official record. This does not accept any derived Markdown conversion, prove legal applicability to a particular past event, or complete topic/country coverage.

The research browser opened the e-Sbírka record pages on 21 October but returned no rendered text. The acceptance therefore relies on the official page-data responses retrieved on 19 October, not a claim of a 21 October refresh. These reviewed and accepted source references mean no whole-portal review is needed to establish whether e-Sbírka is an official text publisher; individual currentness still follows the dated scope above.

## Rule assessment

| Lane | Evidence and controls | Sustainability limits | Verdict |
|---|---|---|---|
| e-Sbírka current legal text — 17 records | Public unauthenticated page-data route resolves the stable act record to `typZneni=AKTUALNI`, a current-version URL, effective-from date, and publisher citation. The adapter captures metadata and every ordered JSON fragment page, validates identity/version/page/fragment consistency, hashes exact responses, converts XHTML fragments deterministically, and replays offline. All 17 captured texts passed replay. | The page-data route and JSON schema are not the separately documented, versioned REST API. Frontend changes may alter endpoint or fragment fields. The captured page labels consolidated text informative; a capture does not prove force, completeness, or event-specific applicability. | **Fragile / medium confidence.** Repeatable for identified records today, with strong identity and replay checks; add a live change monitor for repeatable freshness checks; consult promulgations only where a specific legal question requires them. |
| Official guidance/index HTML — 13 records | Exact official responses and deterministic candidate conversions are retained in `work/raw/` and `work/candidates/`; offline verification passed for all 13. The rule checks configured H1 identity, encoding, payload and extraction region; hashes prevent unnoticed candidate drift. | Pinned URLs do not discover new pages. Main-region extraction and flattened tables need content review. Linked attachments are not fetched by the HTML rule; form links need rediscovery through official parent indexes. | **Fragile / medium confidence.** Suitable for refreshing known pages with review, not for claiming complete guidance or forms coverage. |
| Monitor/discovery pages — 13 records | Exact responses and converted candidates are in the 19 October capture ledger. The bounded generic capture passed offline replay for all 13. The stale renewal form URL was repaired from the official MOI forms index. | This is a one-time capture, not a maintained publisher-specific updater. Court searches, paginated mission directories, form links, and local mission practice need different discovery and coverage rules. A successful page capture does not make them legal texts or complete feeds. | **No sustainability verdict for an updater.** The capture is reproducible from saved bytes; recurrence and coverage are not implemented. |

## Open issues

- The old Node law lane still attempts the date-bound PDF route. The public page-data adapter is an optional local-copy/monitoring route; connect it to a product updater only if recurring automated updates are wanted. Direct human review of official e-Sbírka pages does not depend on this integration.
- Use the publisher's latest current consolidated text and record its effective-from date. Preserve a future-effective version separately when one is specifically relevant; consult Gazette promulgations only for a known discrepancy or commencement question, not as a prerequisite for each current text.
- If retaining or relying on converted text, check relevant headings, tables, footnotes, and passages against e-Sbírka. Full visual comparison is needed only where extraction creates a material risk or the whole conversion is relied on.
- Build a parent-index resolver for volatile form links, and keep mission instructions scoped by jurisdiction and date.
- Review publisher reuse terms, source-language requirements, topical coverage, and whether any discovered court/oversight material is the full primary decision rather than a directory or summary.

## Verification record

- `python sync_esbirka_open_data.py verify`: 17/17 legal conversions replayed; 0 failures.
- `node scripts/sync-czechia.mjs --verify`: 13/13 guidance conversions replayed; 0 failures.
- `python source-library/sync_candidate_pages.py czechia verify monitor-pass-2026-10-19.json candidates`: 13/13 monitor/discovery conversions replayed; 0 failures.
- These checks verify stored bytes and deterministic conversion only. They neither refresh the sources nor accept or promote any candidate.


## External-reference review update (21 October 2026)

The link-only source-reference gate is now applied to the records already reviewed. There are 63 candidate records: 62 official external references accepted within stated publisher, language, date/status and scope limits, one Decree 429/2010 record offered for whole e-Sbírka portal review, zero accepted local copies, and zero topics adequately covered. The 26 earlier official pages and 19 added Czech-language pages/decisions are links only; retained conversions remain unaccepted.

The MZe-hosted Act 326 page is a supplemental government working text; e-Sbírka remains the temporal anchor. Four selected court decisions add useful evidence but do not constitute repeatable case-law discovery. The visa refusal page states a general 15-day reconsideration period, whose application to EU-family applicants remains unresolved. Decree 429/2010 has official identity metadata but its current consolidation, cutoff and route applicability need a human reviewer. See `source-acceptance.json`, `coverage-model.json`, `source-dependencies.json`, and `human-review-offers.md`.

The 14 topic map remains partial. Most source dependencies have not had a full cross-reference scan; the register marks that work explicitly. The four Czech-language EUR-Lex records are official external-only leads, but direct pages returned a JS/robot check and their text was not validated. No challenge was bypassed.
