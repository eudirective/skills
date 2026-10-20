# Norway retrieval and conversion sustainability assessment (2026-10-19)

## Scope and result

The bounded register now has 54 official-source candidates, including laws, regulations, guidance, forms, decisions, oversight and discovery channels. A live capture pass saved source bytes for 32 candidates and converted 31 to review Markdown. Five changed outputs are staged under `temp/norway/pending/`. One additional response is a portal shell without a source body. No locally stored artifact has been accepted.

The Lovdata public-data rule is **sustainable with limits (medium confidence)** for selected current national laws, central regulations and Avdeling I promulgations. It uses the documented unauthenticated public-data API, checks package identity and size, preserves exact bytes and publisher version metadata, and replays offline. The rule does not cover local Avdeling II regulations or turn the captured archive index into complete Gazette text coverage. The non-legislative source lane remains partial because many UDI pages reject ordinary GETs and one portal returns only a shell.

## Lovdata access, terms and retrieval

Lovdata's [OpenAPI schema](https://api.lovdata.no/swagger/api.json) documents `GET /v1/publicData/list` and `GET /v1/publicData/get/{filename}` without an API key. Its separate `structuredRules` endpoints require an API key and are not used. The live API list returned all four public packages with exact byte sizes and `lastModified` values. The list and package downloads were fetched without credentials on 19 October 2026.

Lovdata's [service terms](https://lovdata.no/artikkel/brukervilkar_for_lovdatas_tjenester/1319) distinguish individual use of official texts from systematic extraction through its website and direct larger retrievals to the open API. Lovdata's [open API announcement](https://lovdata.no/artikkel/lovdata_tilrettelegger_for_bruk_tilpasset_var_ki-hverdag_gjor_api_av_oppdatert_regelverk_gratis_tilgjengelig_for_alle/5277) describes the current laws and central-regulations datasets as free under NLOD 2.0. The national [data-catalogue entry](https://data.norge.no/en/datasets/c0c6a87c-f597-3735-965f-650be23426a0/norsk-lovtidend-avdeling-i) independently describes open-licensed Avdeling I archives and the list/get route. The implemented rule stays within those packages and does not crawl Lovdata's record website.

The three downloaded package entries reported `lastModified: 2026-10-17T01:31:00Z`:

| Public package | Listed size | Archive content | Use in this pass |
|---|---:|---:|---|
| `gjeldende-lover.tar.bz2` | 5,804,120 bytes | 754 files | Selected current and future-effective law records |
| `gjeldende-sentrale-forskrifter.tar.bz2` | 21,339,520 bytes | 5,127 files | Immigration and public-access regulations |
| `lovtidend-avd1-2026.tar.bz2` | 1,514,940 bytes | 1,114 files | Gazette archive index for 2026 |

The public list also exposes `lovtidend-avd1-2001-2025.tar.bz2` (69,308,234 bytes); it was not downloaded because this bounded pass did not need that large historical package. The archive reader checks every member path and rejects absolute paths, parent traversal, links and non-regular selected members before reading text. It checks the listed package size, bzip2 signature, package SHA-256, and selected member byte/hash identity.

## Conversion and version handling

The selected Lovdata files are official XHTML. Conversion retains the publisher's `DokumentID`, legal title, department, commencement, last-amendment effective date, amendment links, chapter headings, article headings, full body text, and amendment notes. The table-of-contents `Innhold` block is omitted because the full body is preserved separately. The 2012 EØS Worker Mobility Act is current; the 1992 act is captured as a historical record only. Lovdata identifies the 2012 act as the replacement for the 1992 act and records its effective date and later amendment [on the current act record](https://lovdata.no/lov/2012-12-14-81).

Two administrative-procedure instruments need explicit commencement monitoring. The current 1967 Act remains in force until the 2025 replacement's commencement is set; the 2025 act currently states `Kongen bestemmer`. The 2026 Data Sharing and Data Management Act also states commencement is to be set by the King. Neither future-effective text should be presented as operative law before its commencement date.

The 2026 public-data list changed during the second sync, so the new list and changed candidate outputs for `no-01`, `no-03`, `no-09`, `no-10`, and `no-32` are staged for review. The other 26 conversions remain regular review candidates. All 31 converted outputs pass offline byte-for-byte replay against their captured sources. A changed page does not update an accepted source automatically.

## Candidate coverage and gaps

| Source class | Result | Sustainability limit |
|---|---|---|
| Lovdata API/package catalogue and current law | Live list/schema, three packages and selected legal texts captured; 0 local copies accepted | Stable IDs and package timestamps support refresh. Only selected records were extracted; a changed consolidated text still needs legal review. |
| Norsk Lovtidend Avdeling I | 2026 archive and 1,114-member index captured | The index is not a conversion of all promulgations. The 2001–2025 archive was not fetched. |
| Local/regional regulations | Candidate `no-05` has no matching package in the documented public API list | No Avdeling II/local package was found; do not infer central-package coverage. |
| EFTA texts and Norwegian guidance | EFTA pages and selected Police, UNE, Sivilombudet, court, Norway.no, legal-aid and privacy pages converted | Pages can be dynamic and public-content reuse terms are not established for every page. UNE decisions are a representative selection; court indexes do not cover all courts or unpublished decisions. |
| UDI, UDI Regelverk, forms and service flows | Current ordinary requests returned HTTP 403 for 20 candidates; self-service returned a network error | Search-indexed content is not a substitute for captured publisher bytes. Do not bypass access controls. Candidate-specific authenticated workflows are excluded. |
| eInnsyn and Statsforvalteren | eInnsyn shell captured without body; the obsolete apostille route returned 404 and the current regional service page was captured; regional legal-aid page converted | Search shell is discovery-only. Regional legal-aid and apostille service details must not be generalized nationwide. |

The 2012 act replacing the repealed 1992 EØS Worker Mobility Act is candidate `no-54`; see the official [Lovdata record](https://lovdata.no/lov/2012-12-14-81). Candidate `no-53` records the future-effective 2025 Public Administration Act. Norway's EEA implementation and Switzerland's separate EFTA route remain distinct from EU Member State rules.

## Reproduction and captured state

The per-source hashes, API list, package metadata, raw paths, output paths, status and review state are in [`norway-capture-results.json`](norway-capture-results.json). Candidate inventory and retrieval rules are in [`candidate-manifest.json`](candidate-manifest.json), and the 54-source table is in [`source-list.md`](source-list.md).

From the source-library work root:

```sh
python source-library/norway/sync_norway.py sync
python source-library/norway/sync_norway.py verify
```

`sync` refreshes the public API list and selected listed packages before checking all candidates. Source changes are staged under `temp/norway/pending/`; no output is trust-promoted. `verify` checks the recorded package/list/source hashes and replays all saved conversions offline.
