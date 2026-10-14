# Denmark pack retrieval contract

## Source scope

The national lane is fixed to 16 official Retsinformation ELI records in `pack-manifest.json`. The four Danish targets that were listed but absent or unverified in the supplied Markdown pack remain included. Their absence from the ZIP is not treated as a source deletion.

The shared EU/CJEU lane is fixed to the 23 IDs in `core-source-ids.json`. It uses `eudirective-core/scripts/source-maintenance.mjs` with a validated source-ID filter and stores observations and unpromoted conversions in project-root `temp/`. Never run its unfiltered scan as part of a Danish pack refresh.

## Danish retrieval

For each pinned `https://www.retsinformation.dk/eli/lta/YYYY/NUMBER`:

1. Fetch `/xml` from the official host. Save exact response bytes content-addressed and record URL, final URL, media type, retrieval time, HTTP validators, and SHA-256.
2. Validate `Year`, `Number`, `DocumentId`, `AccessionNumber`, and `DocumentTitle` against the manifest. Reject redirects away from Retsinformation and any identity mismatch.
3. Convert the structured `DokumentIndhold` in document order. Preserve headings, chapters, paragraph labels, numbered lists, and text. Ignore `Meta` and page-interface elements. Do not infer coverage of image-only, layout-only, or other non-text matter.
4. Some older ELI XML records contain only metadata. For those records, use the first-party Retsinformation document endpoint `POST /api/document/eli/lta/YYYY/NUMBER` with JSON `{ "isRawHtml": true }`. Require exactly one record and verify its document ID, accession, and title against the ELI XML metadata. Extract only the `INDHOLD` legal-text container; do not include its table of contents or site chrome. Store the extracted official HTML content-addressed and hash it.
5. If neither representation contains the legal body, fail closed and report the exact source. Do not use a third-party transcription or silently fall back to a search-result rendering.
6. Render stable UTF-8 Markdown with the ELI, citation, source IDs, source hashes, version status/date fields, converter version, and a clear coverage statement. Keep retrieval timestamps in the machine-readable report/state, not in Markdown, so identical official bytes and converter versions yield identical Markdown bytes.

The legacy body endpoint is part of Retsinformation's official website application and is not the published harvest API. Treat its route/schema as a dependency: verify status, response type, and identity on every use, fail closed on a changed shape, and review it against the public ELI technical documentation when the site changes.

## Change discovery and new consolidations

Use the official [ELI Atom feed](https://www.retsinformation.dk/eli/eli-update-feed.atom). It includes ELI identifiers, titles, change dates, publication media, and change reasons, with at least 60 days of history. Parse and retain `NewDocument`, `DocumentContentChanged`, `DocumentMetadataChanged`, `DocumentMetadataChangedAndDocumentContentChanged`, and `RemovedDocument` as distinct signals.

- `DocumentContentChanged` or a changed XML/HTML hash creates a content candidate.
- `DocumentMetadataChanged` is recorded but is not by itself a body change.
- A new Lovtidende A record whose title exactly matches an alias and whose ELI is newer than the pinned version is a possible new consolidation.
- A new Lovtidende A act or order whose title names a tracked law is a possible amendment or commencement instrument. Keep it as a candidate; a person must confirm scope, commencement, and territorial application.
- Proposals and parliamentary records are not treated as enacted law. Greenland/Faroe records remain candidates only when the source title and territorial scope merit review.
- For records with an end date earlier than the check date, flag the exact version for currentness review. Do not infer that the underlying law ceased to apply.

The Atom feed retains at least 60 days. If the previous successful feed check is more than 55 days old, mark a reconciliation gap and do not advance the feed checkpoint. Compare the official [ELI sitemap](https://www.retsinformation.dk/eli/sitemap.xml) against the last successfully stored sitemap snapshot. For newly listed Lovtidende A records, retrieve official XML metadata and emit possible title matches as review candidates. This can detect newly listed instruments; it cannot reconstruct every change event that may have appeared and disappeared during the missed interval. Keep the gap open until an operator completes a separate historical reconciliation. Do not claim complete change coverage based only on the current sitemap.

The official harvest API has a limited 10-day date lookback and a restricted daily retrieval window; this implementation does not currently perform harvest API replay. Its limits are documented at the [Retsinformation harvest API](https://api.retsinformation.dk/index.html). If a future version adds replay, it must retrieve every missing day, obey the published interval, store every response, and validate coverage before closing a gap.

The public documentation is [ELI channels](https://www.retsinformation.dk/eli/technicaldocumentation/eli-channels), [ELI URI and format specification](https://www.retsinformation.dk/eli/technicaldocumentation), and the [Retsinformation harvest API](https://api.retsinformation.dk/index.html). Recheck these primary sources before changing retrieval logic.

## State and promotion

- The project-root `temp/` tree holds immutable official XML, HTML fallback bodies, Atom and sitemap snapshots, state, reports, and update candidates.
- `documents/national/` holds accepted Markdown for the registered Danish instruments.
- A failed request, unexpected response shape, ELI identity mismatch, or conversion error does not advance state and does not stage a partial national pack.
- `--ack <source-id>` promotes one reviewed candidate directly to `documents/national/` and records its Markdown hash. It does not certify currentness or legal completeness.
- A new amendment or later consolidated ELI must be added to a reviewed manifest change before it becomes a pinned tracked source. Never replace historical source bytes or a previous version in place.

## Run commands

```powershell
node scripts/sync-pack.mjs --check
node scripts/sync-pack.mjs --discover
node scripts/sync-pack.mjs --sync
node scripts/sync-pack.mjs --ack aliens-act-2025-1183
node scripts/core-lane.mjs --check
node scripts/core-lane.mjs --sync
```

The `--sync` commands perform official network retrieval and stage conversion candidates. They do not certify those candidates as a legally current source pack.
