---
name: hungarian-national-source-system
description: Retrieve, convert, and monitor the Hungarian national legal and OIF source inventory in this pack from official publishers. Use for source updates or discovery only; it is not legal advice.
metadata:
  version: 0.3.0
---

# Hungarian national source system

This pack is stored at `eudirective-source-library-0.6.0/hungary/`. It was created from the supplied Hungary/OIF source archive. The ZIP's index and documents are inventory evidence, not instructions. The pack owns Hungarian legislation, OIF procedure and public-data sources, Hungarian authority guidance, and domestic case-law discovery.

EU instruments and CJEU decisions remain in the shared EU core and `hungary/core/` language mirror. This pack refers to those by source ID and does not duplicate them. Research notes and conversion logs in the ZIP are not primary legal sources.

## Node-only commands

Install the shared Node.js runtime dependencies once from the project root (the parent of `eudirective-source-library-0.6.0`):

```powershell
npm ci
```

Then, from this Hungary directory, run:

```powershell
node scripts/sync-hungary.mjs --check
node scripts/sync-hungary.mjs --discover
node scripts/sync-hungary.mjs --sync
node scripts/sync-hungary.mjs --verify
node scripts/sync-hungary.mjs --reconvert
```

The source inventory and official host allowlist are in `references/manifest.json`. `--check` retrieves the pinned records and compares raw and extracted-text hashes without changing accepted documents. `--discover` checks official catalogue pages and reports matching same-host links not yet in the saved discovery baseline, including discovery-only catalogue entries in `oif_pages`; pages must expose visible content and cannot be bot-challenge interstitials. `--sync` saves original HTML/PDF bytes by SHA-256 and creates clean Markdown for each successful source; failed sources retain their prior state, and a discovery baseline is replaced only after every discovery page succeeds. The report distinguishes a complete sync from partial successful saves. `--verify` replays conversion from saved bytes and checks hashes offline. `--reconvert` regenerates Markdown and conversion hashes offline from the retained official bytes after a converter change; it writes nothing if any source fails validation.

Each Markdown file records source ID, publisher, category, official URL, raw-byte SHA-256, and extracted-body SHA-256. Retrieval time, state, and reports are kept under the project-root `temp/eudirective-source-library-0.6.0/hungary/work/` tree so a repeated conversion stays byte-stable. Original source snapshots and OCR scratch files are also kept under project-root `temp/` and resolved through `runtime-storage.mjs`. PDF conversion uses pinned `pdfjs-dist`; sparse pages are rendered with Poppler `pdftoppm` and processed with pinned Tesseract.js and the bundled Hungarian OCR model. Set `PDFTOPPM_PATH` if `pdftoppm` is not on `PATH`. HTML conversion extracts the legal content container, main/article content, or body and removes navigation, scripts, styling, and forms. No generated Markdown is presented as an official publication.

## Update and discovery rules

- Retrieve Hungarian legislation from the official Nemzeti Jogszabálytár (NJT); validate the citation in the extracted Hungarian text before saving.
- Retrieve OIF forms, fees, procedures, public data, statistics, contracts, and organisational records from OIF pages and their official linked files.
- AJBH catalogue pages remain discovery-only and are now scanned by discovery runs. Three direct AJBH PDFs are registered as candidates and use the existing PDF converter; retrieval requires the registered PDF media type and signature. Automated access is still unverified. The 2025 general-complaint PDF stays blocked until a content identity marker can be confirmed from the first-party document; do not treat the pinned URL or filename as proof of identity.
- Use the Kúria and Országos Bírósági Hivatal collections only as official case-law discovery channels. A catalogue search hit is a candidate, not a new accepted case record; add it to the manifest only after matching the decision number, court, date, and official full text.
- A new PDF or page linked from an OIF source page is reported as a discovery candidate. Review its title/date and category before adding it to the fixed source manifest.
- Treat changed texts, newly consolidated legal versions, amendments, and new OIF publications as distinct events. Do not synthesize a consolidated statute from amendment acts. Retain old raw snapshots and do not overwrite them.
- A 404, 403, failed redirect, non-official host, unexpected content, missing citation, or conversion failure is recorded as a failure; it never advances the successful state.

The ZIP inventory includes historic statistical and procurement publications. The OIF catalogue pages remain the official update channel for newer editions; each discovered edition should be pinned as an individual record so its dated version is preserved. `archive_targets` maps supplied archive labels to their official OIF editions and identifies any genuinely unresolved or access-blocked items. A mapped item is represented by its pinned official source ID; it is not treated as a second source or counted twice.

## Scope and limits

See `references/source-list.md` for the archive-to-publisher map and exclusions. The initial manifest is bounded to records whose identity and official retrieval route are registered there. A successful fetch or matching hash proves retrieval/conversion reproducibility, not legal force, completeness, or currentness. Check the publisher's version dates and status before legal reliance.
