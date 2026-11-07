# Belgium Legalize source crosswalk — 29 October 2026

## Scope and repository

Reviewed the public [legalize-dev/legalize-be repository](https://github.com/legalize-dev/legalize-be) at commit [`da37dfb18b17b06f8f8dc74c0d724cca22292bee`](https://github.com/legalize-dev/legalize-be/tree/da37dfb18b17b06f8f8dc74c0d724cca22292bee), dated 28 October 2026. Its README describes a Justel-derived corpus of consolidated primary federal and federated legislation. It explicitly excludes secondary instruments, including Royal and ministerial decrees. The repository license distinguishes its MIT-licensed pipeline from Belgian public-sector text, marked “CC0 par défaut / open data fédéral belge”; Legalize also says its reproductions are automated and unverified. Justel remains authoritative.

This bounded crosswalk checks the principal Immigration Law already registered by the Belgium pack and the scope of the corresponding implementing decree. It does not claim to inventory all files in the large Legalize-BE repository or every relevant Belgian instrument.

## Candidate review

| Source-library record | Legalize candidate and verification | Disposition |
|---|---|---|
| `be-law-1980-fr` | [`be/1980121550.md`](https://github.com/legalize-dev/legalize-be/blob/da37dfb18b17b06f8f8dc74c0d724cca22292bee/be/1980121550.md) has the matching NUMAC identifier, title, French Justel ELI and official-source attribution. Its frontmatter says `last_updated: 2025-09-01`, and the title note says the source was updated through 8 August 2025. The official [Justel record](https://www.ejustice.just.fgov.be/eli/loi/1980/12/15/1980121550/justel), checked 29 October 2026, displays an update through 24 June 2026, 136 archived versions and 331 implementing decrees. The existing pack copy was independently extracted from official Justel HTML, with the complete text retained and Articles 40bis, 40ter, 42 and 62 checked against the publisher on 24 October. | Identity confirmed; candidate is stale against the current official consolidation. Keep the official Justel source and existing official capture. Do not assign Legalize-BE as a current retrieval method and do not copy its text. No whole-body comparison to the older 2025 edition was needed for this currentness decision. |
| `be-law-1980-nl` | The Belgian pack contains the Dutch official Justel representation of the same NUMAC instrument. The reviewed Legalize file above is French; it does not establish a Dutch candidate or verify the Dutch text. | Retain the current official Dutch Justel source. No Dutch Legalize retrieval method is assigned. |
| `be-rd-1981-fr`, `be-rd-1981-nl` | The 8 October 1981 Royal Decree is secondary legislation. Legalize-BE’s published scope expressly excludes Royal Decrees. The pack’s French and Dutch official Justel records were separately checked on 19 October 2026; the displayed consolidation cutoff was 17 August 2026. | Legalize-BE is not a retrieval route for this instrument. Keep the dated official Justel records and their stated cutoff. |

## Attribution and limitations

For the reviewed candidate, cite Legalize-BE as an automated, dated Justel transcription and cite the Belgian Official Gazette/Justel record as the legal source. The Legalize candidate is not represented as official or verified. The existing local Immigration Law files were made from official Justel captures, not copied from Legalize.

No new source record or conversion rule is required: the checked candidate is stale, the official French and Dutch consolidations are already in the pack, and the secondary implementing decree is outside Legalize-BE’s stated corpus. This crosswalk does not establish complete Belgian legal coverage or complete mission, regional, community or procedural coverage.
