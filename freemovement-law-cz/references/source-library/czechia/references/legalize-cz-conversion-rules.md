# Czech official-text and Legalize-CZ conversion rules

**Reviewed:** 30 October 2026  
**Scope:** Direct official e-Sbírka retrieval for all accepted Czech text copies; the Legalize-CZ candidate-body rules are individually scoped below.

## Direct official e-Sbírka page-data retrieval

The accepted direct retrieval route is the unauthenticated public page-data service. It does not use the separately documented registration-gated REST API.

1. Request publisher metadata from `/sbr-externi/dokumenty-sbirky/{percent-encoded-stable-record-path}`.
2. Preserve the publisher's returned stable URL, resolved current `staleUrl`, citation, `typZneni`, `datumUcinnostiZneniOd`, `datumUcinnostiZneniDo`, and ELI.
3. Request every ordered page from `/sbr-externi/dokumenty-sbirky/{percent-encoded-resolved-staleUrl}/fragmenty?cisloStranky=N`, starting at 0 and ending at `pocetStranek - 1`. Confirm consistent page count and retain each complete JSON response. Do not treat metadata or a page link by itself as source text.
4. Convert all fragments with an `xhtml` value in publisher order. Preserve Czech wording, article and paragraph numbering, list enumerators, headings, notes, footnote markers and every visible text fragment. Add Markdown headings only from the fragment type; do not translate, paraphrase, reorder, silently correct, or omit text.
5. Keep official table fragments as XHTML so row/cell order and `rowspan`/`colspan` remain available. Strip only anchor wrappers and the `czechvoc-termin` vocabulary wrapper while retaining their visible text; retain other table structure and cell text. For non-table fragments, remove markup while preserving visible text and order. Group `PPC` footnotes under a separate heading while keeping their order.
6. Record the page count, total fragment count, text-bearing fragment count, publisher effective period, raw metadata/page hashes, response-set hash, converted-document hash, retrieval date and archived raw-response manifest.
7. Attribute the law to the Czech issuing authority and e-Sbírka. Treat stable and dated URLs as provenance/version locators; the retained text document is the source copy. Preserve e-Sbírka's informative-text caveat. A current consolidated version does not certify Gazette history, event-specific legal effect, or future currentness.

The 30 October 2026 capture added local copies of Acts 435/2004, 48/1997 and 117/1995. It retained 1,842, 1,891 and 679 text-bearing fragments respectively. The 48/1997 copy preserves all 14 official XHTML table fragments. Exact response bytes and per-response hashes are indexed in the Monitor local-only archive at `captures/czechia-official-source-capture-2026-10-30/Czechia/czechia/esbirka/retrieval-manifest.json`; the compressed response bundle is `captures/czechia-official-source-capture-2026-10-30/Czechia/czechia/esbirka/official-responses.tar.gz`.

## Verified Legalize-CZ candidate: Decree 429/2010

- **Instrument:** Vyhláška č. 429/2010 Sb.
- **Official publisher:** e-Sbírka, Czech Collection of Laws and International Treaties.
- **Official version:** effective 1 February 2020, incorporating Decree 67/2019: [official dated ELI](https://e-sbirka.gov.cz/eli/cz/sb/2010/429/2020-02-01).
- **Candidate:** [Legalize-CZ SB-2010-429.md](https://github.com/legalize-dev/legalize-cz/blob/f88290efc3062a7b4a56105193238c269816b613/cz/SB-2010-429.md), pinned at commit `f88290efc3062a7b4a56105193238c269816b613`, Git blob `9f86ae027ff3b12aacff28c59254853ccbd4a050`.
- **Accepted dated text copy:** [cz-decree-429-2010.md](../documents/legislation/cz-decree-429-2010.md).

Remove only the candidate YAML frontmatter and generated title heading when comparing legal text. Normalize Markdown headings, list markers and whitespace only. The complete candidate legal body matched §§ 1–3, the minister's signature and all 42 annex entries. The candidate omits the instrument number/date and the official enacting formula before § 1; supplement these from official e-Sbírka and record that supplementation. Preserve the official cutoff separately from the Legalize repository commit and any `last_updated` field. This acceptance is limited to the 2020-02-01 dated copy and does not establish later currentness or EU-family route applicability.

- Legalize candidate raw-file SHA-256: `2e2633898d0ba439a309a6bd15bbaaf5de878717b4dc42b5b76245f9bd847059`.
- Candidate legal-body SHA-256: `dac4654755df24bcb5342f8fe25f72e440cfccec646805d24f4405506dd2166c`.
- Extracted official legal-text SHA-256: `f6e8563f6f2baa21310aa1b84aa2cc98fc500607e79ccbbd99f7dc7ce34a5e8b`.
- Accepted local-copy SHA-256: `493f6eb0d8e78499467452f527d1aaed19c8a707a91853d41846e693f3525ccc`.

## Legalize-CZ candidates rejected after complete comparison

At pinned commit `f88290efc3062a7b4a56105193238c269816b613`, the complete candidate bodies for Acts 435/2004, 48/1997 and 117/1995 were compared with the official historical versions effective from 1 January 2026 named by their ELI links. Each has a substantive §1 mismatch and is not accepted as a current or exact historical local copy. Current official texts for all three were separately retrieved from e-Sbírka and retained under `documents/legislation/`. Legalize-CZ supplied no accepted text for those copies and is not established as the retrieval method.

The 17 same-code Legalize-CZ candidate files associated with existing official e-Sbírka copies establish identity overlap only. Their complete candidate bodies have not all been compared, so do not attribute the accepted text copies to Legalize-CZ or infer that their candidate files match.

## Evidence and attribution

Legalize-CZ's README identifies DILA/e-Sbírka as its source, says Markdown conversion can differ from the official text, and treats legislative content as public-sector work under Czech Copyright Act No. 121/2000 Coll. §3(a); MIT applies to pipeline software. For direct e-Sbírka copies, attribute text to the issuing authority/e-Sbírka. Identify Legalize-CZ only as a candidate transcription where it was used for a specifically verified comparison. Keep all source-copy dates, conversion limits and publisher caveats visible in the source acceptance register.
