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

The recorded NJT terms prohibit automated bulk retrieval and storage of the curated portal database. Use current NJT consolidated pages as human-reviewed official references, note their displayed version date, and consult a Gazette item only for a specific material change or commencement question. Do not use a Gazette-by-Gazette workflow as a substitute for the NJT text.

The online commands below operate on OIF and other permitted non-NJT sources. They exclude NJT legislation and its catalogue from network retrieval. `--verify` and `--reconvert` may process previously saved bytes offline.

Then, from this Hungary directory, run:

```powershell
node scripts/sync-hungary.mjs --check
node scripts/sync-hungary.mjs --discover
node scripts/sync-hungary.mjs --sync
node scripts/sync-hungary.mjs --verify
node scripts/sync-hungary.mjs --reconvert
```

The source inventory and official host allowlist are in `references/manifest.json`. `--check` retrieves permitted OIF sources and compares raw and extracted-text hashes without changing accepted documents. `--discover` checks OIF catalogue pages and reports matching same-host links not yet in the saved discovery baseline; pages must expose visible content and cannot be bot-challenge interstitials. `--sync` saves permitted OIF HTML/PDF bytes and creates clean Markdown for each successful source. Failed sources retain prior state, and a discovery baseline is replaced only after every discovery page succeeds. The report distinguishes complete and partial runs and lists the 58 NJT law records as manual references. `--verify` replays existing saved bytes offline. `--reconvert` regenerates Markdown offline from retained bytes after a converter change.

Each Markdown file records source ID, publisher, category, official URL, raw-byte SHA-256, and extracted-body SHA-256. Retrieval time, state, and reports are kept under the project-root `temp/eudirective-source-library-0.6.0/hungary/work/` tree so a repeated conversion stays byte-stable. Original source snapshots and OCR scratch files are also kept under project-root `temp/` and resolved through `runtime-storage.mjs`. PDF conversion uses pinned `pdfjs-dist`; sparse pages are rendered with Poppler `pdftoppm` and processed with pinned Tesseract.js and the bundled Hungarian OCR model. Set `PDFTOPPM_PATH` if `pdftoppm` is not on `PATH`. HTML conversion extracts the legal content container, main/article content, or body and removes navigation, scripts, styling, and forms. No generated Markdown is presented as an official publication.

## Update and discovery rules

- Use the current government-published NJT consolidation as a human-reviewed source reference; record its displayed date and publisher label. Do not fetch, store, or poll NJT law records through this updater. Check a Gazette item only for a specific material post-cutoff change, commencement, or discrepancy.
- Retrieve OIF forms, fees, procedures, public data, statistics, contracts, and organisational records from OIF pages and their official linked files.
- AJBH catalogue pages remain discovery-only and are now scanned by discovery runs. Three direct AJBH PDFs are registered as candidates and use the existing PDF converter; retrieval requires the registered PDF media type and signature. Automated access is still unverified. The 2025 general-complaint PDF stays blocked until a content identity marker can be confirmed from the first-party document; do not treat the pinned URL or filename as proof of identity.
- Use the Kúria and Országos Bírósági Hivatal collections only as official case-law discovery channels. A catalogue search hit is a candidate, not a new accepted case record; add it to the manifest only after matching the decision number, court, date, and official full text.
- A new PDF or page linked from an OIF source page is reported as a discovery candidate. Review its title/date and category before adding it to the fixed source manifest.
- Treat changed texts, newly consolidated legal versions, amendments, and new OIF publications as distinct events. Do not synthesize a consolidated statute from amendment acts. Retain old raw snapshots and do not overwrite them.
- A 404, 403, failed redirect, non-official host, unexpected content, missing citation, or conversion failure is recorded as a failure; it never advances the successful state.

The ZIP inventory includes historic statistical and procurement publications. The OIF catalogue pages remain the official update channel for newer editions; each discovered edition should be pinned as an individual record so its dated version is preserved. `archive_targets` maps supplied archive labels to their official OIF editions and identifies any genuinely unresolved or access-blocked items. A mapped item is represented by its pinned official source ID; it is not treated as a second source or counted twice.

## Scope and limits

See `references/source-list.md` for the archive-to-publisher map and exclusions. The initial manifest is a bounded inventory. A successful fetch or matching hash proves retrieval/conversion reproducibility, not completeness or currentness. For ordinary research, a human-reviewed NJT official reference is enough; record its displayed version date/status and use the closest government-published text. The updater and replay checks apply only to retained local copies or recurring monitoring.
