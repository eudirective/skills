# Belgium Justel HTML to retained-text rule v1.0.0

**Applies to:** individual Belgian Official Gazette / Justel consolidated legal-text records whose body is exposed in `div#list-title-3.box.plain-text`.

**Demonstrated record:** Law of 19 July 1991 on population registers, identity cards, foreigner cards, and residence documents, French record NUMAC `1991000380`.

## Source and replay

- Official record: `https://www.ejustice.just.fgov.be/eli/loi/1991/07/19/1991000380/justel`.
- Retrieved: 2026-10-31; response size 118,137 bytes; raw HTML SHA-256 `656a46afcd4ecc4edec858bd3424e72094438c82f93322590fe4a982b57ba141`.
- Official page states its consolidated text is updated through 2026-08-05. The captured current page incorporates Law of 19 July 2026 provisions effective 2026-09-28.
- Replayer: [`justel-plain-text-to-utf8.py`](justel-plain-text-to-utf8.py), SHA-256 `f30e4b268c7dcdfc66dabcb1af32d40cc93d2852c59718c5da708f2397f3ce2e`.
- Command: `python3 justel-plain-text-to-utf8.py <official-response.html> <extracted-body.txt>`; input decoding defaults to ISO-8859-1 and can be overridden with `--encoding`.
- Output for the demonstration record: 68,702 UTF-8 bytes; SHA-256 `6f6e9a813c21916c6d5aee8ed2c86bafb1a8044789c6da43bd97aa6f59cc1e0b`.

## Deterministic conversion

1. Select only the official page's `div#list-title-3.box.plain-text` content. Exclude page navigation, the separate table of contents, scripts, and external-link lists.
2. Decode the publisher response using its ISO-8859-1 encoding and decode HTML character references.
3. Convert `<br>` and paragraph boundaries to line breaks. Keep visible text from anchors; discard anchor destinations and presentation-only attributes.
4. Mark visible superscript note numbers as `[n]`. Remove the page's leading `Texte` UI label.
5. Replace non-breaking spaces with ordinary spaces; collapse display whitespace within each line; trim line-edge whitespace and repeated blank lines. Preserve paragraph order, article and chapter order, words, punctuation, cross-references, amendment notes, and visible note text.
6. Save the extracted body as UTF-8 with LF endings. Add the source-specific identity, version, retrieval, rights, and scope metadata above the body in the retained Markdown document.

This is a text extraction, not a translation or legal editing step. Do not use the Legalize Markdown as the current legal wording when it differs from Justel. Retain the publisher's article sequence and amendment text as displayed.

## Verification and limits

- Replaying this rule on the retained official response produced the same 68,702-byte extracted body and SHA-256 above. The current body contains 17 article headings, including Articles 9 and 10; the official sequence places Article 6sexies before Articles 7 and 8.
- A normalized article-body comparison with Legalize BE commit `da37dfb18b17b06f8f8dc74c0d724cca22292bee`, file `be/1991000380.md` (66,277 bytes; SHA-256 `6e23ed20d7bc9db6f4cda738962c20877e3e8e93e4e712e4220126e29ae9d308`), found 13 of 17 article bodies exact after presentation, whitespace, and citation-link normalization. Articles 2, 6, 6bis, and 6sexies differ materially: Article 2 includes the 2024 amendment; Articles 6, 6bis, and 6sexies include Law of 19 July 2026 amendments. The archive candidate's stated 2024-08-30 cutoff predates these changes, and it places Articles 6sexies after Chapters II and III.
- The stored text is the current French Justel consolidation displayed through 2026-08-05, captured on 2026-10-31. Justel's consolidated text is an information copy; the promulgated Belgian Official Gazette text remains authentic. The 27 archived versions, 92 execution instruments, and Dutch-language representation are separate records and are not included.
- The rule establishes faithful extraction of this publisher page only. It does not establish legal topic coverage, acceptance of an entire product pathway, or bulk/database reuse rights.
