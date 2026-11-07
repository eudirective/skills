# Legalize-to-Italy conversion rules

**Status:** drafted for future use; no candidate has passed full official text verification.

## Source gate

1. Resolve the candidate's exact act identifier and `source` URL at a pinned Legalize commit.
2. Compare every article, inserted article, annex, note and table against the official Normattiva version for the same as-of date. Match the complete inventory and all text before promotion.
3. Treat differences in words, punctuation, accents, numbering, citations or notes as content differences until individually resolved. A matching title, source URN, update date or article count alone is insufficient.
4. Record the official version/date, the Legalize commit and path, and both source identifiers. Legalize is a retrieval route; Normattiva remains the publisher.

## Formatting and preservation

- Preserve the full Italian text, section order, article numbering, inserted articles, annexes, notes, cross-references and links.
- Keep the Legalize YAML metadata in provenance or map each field into the local document header without losing the original identifier, source URN, publication date, update date, rank and act number.
- Do not translate, paraphrase, repair, or normalize legal text while wrapping it in the Italy source-copy format. Log any formatting-only change and retain a copy/hash of the retrieved candidate.
- Do not globally replace apostrophes with accented characters. For example, the D.P.R. 184/2006 candidate has `modalita'` where the official text has `modalità`. If accent restoration is proposed, use an explicit, reviewed token map and compare the complete result with Normattiva.
- Add per-article official URLs and hashes only when they can be obtained and verified. If not, retain a whole-document hash and keep the copy pending rather than imply article-level review.

## Promotion record

Only after the full comparison passes, add the converted text to `documents/legislation/`, record Legalize as a retrieval method for that source, cite Normattiva as the publisher, add the conversion-rule version and exact change log, and update local-copy counts. A failed or incomplete comparison remains a discovery candidate and does not change accepted-source counts.
