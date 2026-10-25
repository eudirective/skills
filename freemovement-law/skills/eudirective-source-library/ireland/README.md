# Ireland national source pack

**Review date:** 24 October 2026

**State:** scoped official references accepted; selected local statutory texts accepted; topic and country completion remain open.

## What is in the pack

- The register contains 51 official source references, each accepted only for its recorded purpose and scope.
- Eleven reviewed eISB legal texts are stored under `documents/legislation/`. They are exact made/enacted versions, not a reconstructed current code.
- Current Law Reform Commission Revised Act links are separately recorded for the Immigration Act 2004, Freedom of Information Act 2014 and Data Protection Act 2018. Each is an administrative consolidation with its own stated cutoff and disclaimer.
- Fifteen other page conversions are retained as private research provenance in the EU Source Update Monitor archive; 25 references are link-only. No candidate, capture or retrieval-manifest copies remain in this pack.
- Topic coverage accepted: 0. Ireland review complete: no.

Use the [source list](references/source-list.md), [candidate/source register](references/candidate-manifest.json) and [source acceptance register](references/source-acceptance.json) together. A link or exact historic instrument does not by itself establish current law, topic coverage, or whole-country completion.

## Key limits

- Ireland’s EU, non-EU EEA, Swiss, UK Withdrawal Agreement and Irish-national family routes are distinct.
- S.I. No. 548/2015 is held as made, with its 2021 and 2025 amendments separately held. The files do not assert a consolidated current text.
- The static EUTR1 PDF and 2025 explanatory leaflet are dated. Current ISD instructions use the Customer Service Portal and permit applicants to request paper forms there.
- Current ISD guidance says an EU Treaty Rights decision can take up to six months. The gov.ie page updated 11 April 2025 says 12 months; that discrepancy remains recorded for human review.
- Current short-stay visa appeal instructions include the 1 June 2026 change and its EU Free Movement Directive exception.

## Captures and replay

The Monitor local-only archive contains the 26 original source responses, their 26 hash-verified conversions, and the retrieval manifest. This archive is private research provenance and is not part of the published source library. The archive index records exact hashes.

The optional helper is in `scripts/sync_ireland.py`. It reads the canonical register and writes raw downloads, the runtime retrieval manifest, and pending conversions only under the standard temporary workspace `/tmp/public-data/temp/ireland` (override with `EUDIRECTIVE_TEMP_ROOT`). It does not write candidate files or change source acceptance. Use an isolated environment with `scripts/requirements.txt` for PDF replay.

```sh
python3 -m pip install -r scripts/requirements.txt
python3 scripts/sync_ireland.py sync
python3 scripts/sync_ireland.py convert
python3 scripts/sync_ireland.py verify
```

A new pending conversion is still research material: archive it through Monitor `local_research_write` before review or acceptance. Replay proves byte integrity and reproducibility only; it does not establish legal currentness, reuse terms outside eISB, topic coverage, or country completion.
