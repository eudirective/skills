# Finland Legalize source crosswalk — 29 October 2026

## Scope and repository

Reviewed [legalize-dev/legalize-fi](https://github.com/legalize-dev/legalize-fi) at pinned main commit [`e9c3d8b18c1d4dc3e5f4713b04bde214626edddc`](https://github.com/legalize-dev/legalize-fi/tree/e9c3d8b18c1d4dc3e5f4713b04bde214626edddc), dated 28 October 2026. Its README says the corpus is current Finnish consolidated legislation from the Finlex open-data API, in Finnish, converted from Akoma Ntoso XML to Markdown. It identifies the legislative-data license as CC BY 4.0 and the pipeline license as MIT. Finlex remains the official publisher.

This check is limited to the Aliens Act (301/2004), a principal national source already registered in the Finland pack. It does not inventory the 5,088-file Legalize-FI tree or every one of the pack’s 37 registered source records.

## Candidate and official-source verification

The pack records the Finnish Finlex current-text page for `Ulkomaalaislaki (301/2004)` at [Finlex](https://www.finlex.fi/fi/lainsaadanto/2004/301), with the ELI version recorded as 26 June 2026. The local conversion remains a review candidate, not an accepted text. A fresh browser attempt to load this very large official page exceeded the available response limit, so this crosswalk does not claim a new full-text or later-version check.

The Legalize-FI tree at the pinned commit contains 5,088 entries. The expected exact-identifier path `fi/2004-301.md` is absent, confirmed by both a recursive tree search and a direct GitHub path request. No Legalize candidate text was available to compare.

## Disposition

Keep Finlex as the official source and its existing recorded retrieval route. Do not add Legalize-FI as a retrieval method for the Aliens Act. No Legalize text was copied and no conversion rule is needed.

The crosswalk records a scoped candidate absence; it does not establish that Legalize-FI contains no other Finnish instruments relevant to the pack. Finland remains incomplete and no legal topic is accepted.
