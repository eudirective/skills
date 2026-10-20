---
name: austria-legal-source-system
description: Maintain the Austrian national source candidates and shared German EU-language references in this pack. Use for source discovery, capture, conversion review, or update checks; not for individual legal advice.
metadata:
  version: 0.1.0
  short-description: Austria national source pack
---

# Austria legal source system

Use this workflow only for the bounded inventory in [references/source-list.md](references/source-list.md). The machine-readable inventory is [references/candidate-manifest.json](references/candidate-manifest.json), and the per-source maintenance contract is [references/source-rules.json](references/source-rules.json).

## Current state

All 37 declared records have a capture: 35 text candidates and two native Annex E/F PDFs. No source has been accepted. The inventory does not establish exhaustive coverage. Austria has no local `core/`; German-language EU material is referenced through `references/shared-core.json` and the library-level German index.

## Retrieval and conversion

- The scheduled network monitor is `python3 source-library/austria/sync_austria_sources.py`. It checks only the fixed manifest monthly; use it manually when useful. Do not present it as broad Austrian discovery or as an acceptance workflow.
- Retrieve one official record at a time from the URL or current landing page in the manifest. Use the N-Lex Austria entry only to discover or repair links to RIS and EUR-Lex; do not treat N-Lex as the Austrian text publisher. Do not use RIS OGD/API, authentication, parallel requests, undocumented exports, or challenge bypass. The current approach uses the normal public web pages, so it requires no API registration.
- Confirm the host, source identity, current version/date and attachment links before recording a capture. If the publisher redirects off an allowlisted official host or identity markers do not match, record a failed observation and leave the prior candidate unchanged.
- Keep exact raw bytes and their SHA-256 in the configured project `temp/` workspace. Update `references/capture-ledger.json` with the requested and resolved URLs, media type, timestamp, hashes, candidate path, and any failure.
- For RIS law pages, use the current `div.contentBlock` rule in `scripts/convert_ris_capture.py`; exclude accessibility-only `sr-only` content. Use the offline `convert` action only for records explicitly marked `pending_conversion`; use `verify` to check available local captures and candidate hashes. Nine existing page candidates use legacy body conversions; see the audit before replaying them.
- For guidance and directory pages, review the rendered main content and linked forms manually. No common stable main-content selector has been verified across their publishers. Treat directories and indexes as discovery sources, not legal texts.
- For Annex E/F, resolve the currently linked PDF from the RIS annex page, verify its expected annex and `Dokumentnummer`, and retain the native PDF. Do not replace its visual/form content with text extraction.
- Before reporting pack completeness, consult [the coverage register](references/coverage-register.md). It separates the 37-record capture inventory from open mission, case-law, state-practice, IFG, conversion, and scheduled-maintenance work.
- Record any source change as a review candidate. Do not automatically overwrite accepted material or treat a hash change as a legal change.
- The network monitor stages changed exact response bytes and converted candidates in `pending-updates/`. Review those files and update the candidate manifest and capture ledger together; do not auto-promote them. Broad case-law, mission, and Land-level discovery remain outside the fixed monitor scope.

For OGD requirements if that route is ever reconsidered, read the current [RIS OGD FAQ](https://ris.bka.gv.at/RisInfo/OGD-FAQ.pdf) first. The existing workflow intentionally does not use the API.

## Shared German material

Use `source-library/shared-core-index-DE.json` and stable source IDs. Do not copy or symlink EU material into Austria. Keep `canonical_path` null while an entry is external-only. Before relying on a particular German representation, confirm that the official publisher actually provides that translation; a constructed EUR-Lex language URL does not prove availability.

## Review and limits

Before relying on any candidate, check publisher authority, identity, language, current version, legal effect, complete attachments, extraction quality, scope, and reuse terms. See [the sustainability assessment](references/sustainability-assessment.md) and [coverage register](references/coverage-register.md) for known limitations.
