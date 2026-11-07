# Estonia Legalize source crosswalk — 29 October 2026

## Scope and repository

Reviewed [legalize-dev/legalize-ee](https://github.com/legalize-dev/legalize-ee) at pinned main commit [`5d9503824059b635f570a02682a3986b8de143dd`](https://github.com/legalize-dev/legalize-ee/tree/5d9503824059b635f570a02682a3986b8de143dd), dated 23 June 2026. The repository README identifies Riigi Teataja as its official source, says it stores consolidated laws and regulations by official global ID, and describes the legislative texts as public domain. The repository’s stated source route is Riigi Teataja XML; its pipeline license is separate.

This crosswalk checks the national instrument most directly tied to EU citizens’ residence rights. It is not a file-by-file inventory of all 1,597 Legalize-EE files or all 53 Estonia source-catalog records.

## Verified current-version gap

The Estonia pack already holds the official current consolidation of the Citizen of the European Union Act, Riigi Teataja record `130062026048`, selected by the official date-filtered search for 19 October 2026. The accepted source catalog records its effective period as 1 October 2026 through 31 December 2027 and records exact-source XML replay evidence. The [official record](https://www.riigiteataja.ee/akt/130062026048) is the authority.

At the pinned Legalize-EE commit, both expected global-ID paths returned GitHub 404:

- `ee/130062026048.md` — the current October 2026 edition.
- `ee/103062026006.md` — the earlier published edition also held by the pack.

The candidate absence is verified for those exact paths and that pinned commit. The repository head predates the current October edition, so it cannot supply the current version. No Legalize-EE candidate body was available to compare.

## Disposition

Keep Riigi Teataja XML as the retrieval method for the current and dated official editions already recorded in the pack. Do not add Legalize-EE as a retrieval method for the current Citizen Act. No Legalize text was copied, and no conversion rule is needed for this direct official XML route.

The existing Estonia records cite Riigi Teataja as the source publisher. This crosswalk identifies Legalize-EE only as a checked secondary repository. It does not establish complete Estonian law coverage, operational procedure, or legal-topic completeness.
