# Spain national source pack

**Status (19 October 2026):** 49 unique candidate records across the original national inventory and the 46-record monitor register; 15 BOE law texts and 30 broad monitor pages converted as review candidates; 0 accepted sources. The two inventories overlap on four records. Candidate records include laws, guidance, forms, publisher documentation, oversight and court-search sources; a register entry is not necessarily a full text. The converted candidate files are not admitted to the trusted source corpus, which is why the accepted Spanish-law library remains empty.

- [Original source list](references/source-list.md)
- [Original candidate manifest](references/candidate-manifest.json)
- [Expanded monitor source list](references/monitor-source-list-2026-10-18.md)
- [Expanded monitor candidate manifest](references/monitor-candidate-manifest-2026-10-18.json)
- [Expanded monitor capture ledger](references/monitor-candidate-manifest-2026-10-18-capture-results.json)
- [BOE retrieval manifest](references/boe-retrieval-manifest.json)
- [BOE retrieval and conversion rule](sync_boe.py)

The BOE rule uses its official no-registration open-data API by BOE identifier. It retains raw API XML under project-root `temp/spain/boe/`, checks publisher identity and metadata, converts the latest returned version in each text block, records source and conversion hashes, and supports offline replay. The BOE consolidations are informational review candidates, not authentic legal publications. BOE reuse terms and attribution are reproduced in each converted text. Run `python sync_boe.py sync` to refresh, `python sync_boe.py rebuild` to reconvert retained raw XML without network access, or `python sync_boe.py verify` to check hashes and replay conversion.

The wider monitor pass saved exact responses for 34 of 46 records: 30 converted, four dynamic pages had no stable text body, and 12 failed (mostly publisher 403 responses). All 30 conversions pass offline replay verification. They are stored under `monitor-candidates/`; the separate BOE texts are under `candidates/`. The previous saved Hoja 62 page conversion contains navigation noise and is flagged for rework. No Spain source has been accepted; identity, scope, current-version, extraction quality, reuse terms and coverage review remain necessary.
