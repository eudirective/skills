# Country source-pack template

Use this layout for a national source pack. Keep shared EU-language material, reviewed national material, and unaccepted candidates in distinct locations. Store a shared EU-language corpus once and reference it from each country pack.

```text
<country>/
├── documents/                    # Reviewed, locally held national source text only
│   ├── legislation/
│   ├── guidance/
│   ├── forms/
│   ├── case_law/
│   ├── oversight/
│   └── procedure/
├── candidates/                   # Optional captured, unaccepted national source material
│   ├── legislation/
│   ├── guidance/
│   ├── forms/
│   ├── case_law/
│   ├── oversight/
│   ├── procedure/
│   └── discovery/                # Indexes, search pages, and textless portals
├── references/
│   ├── candidate-manifest.json   # Canonical machine-readable inventory
│   ├── source-rules.json         # Optional local-copy and monitoring rules
│   ├── source-list.md            # Human-readable view of that inventory
│   ├── capture-ledger.json       # Optional evidence for retained copies/updater
│   ├── shared-core.json          # References to shared EU-language files, when applicable
│   └── sustainability-assessment.md
├── captures/                    # Optional durable evidence needed for replay/audit
│   ├── raw/                      # Exact publisher responses; content-addressed where practical
│   └── derived/                  # OCR or other derived inputs with recorded provenance
├── scripts/                      # Source-specific sync/verify tools, when needed
├── README.md
└── SKILL.md                      # Only when an operational skill uses this pack
```

An EU-language corpus is optional. Keep one canonical local copy of each acquired representation in the shared library, organized by language, and reference it from country packs. `references/shared-core.json` lists source IDs through the library-level language index. Put official representations that are not held locally in `external_only_references`, with the official URL, a null local path, and an explicit external-only state; do not create an empty language folder or imply that a link is a stored copy. For example:

```text
source-library/core/de/           # Canonical German EU-language corpus, shared by Austria, Germany, and others
├── eu/
├── case_law/
│   ├── notes/
│   └── full_text/
└── guidance/
    ├── notes/
    └── handbooks/

<country>/references/shared-core.json  # Lists the language index and source IDs used by this country pack
```

## Placement rules

- The library-level `source-library/core/` contains the canonical EU corpus. English files directly under `core/eu/`, `core/case_law/`, and `core/guidance/` are shared with every country pack; do not duplicate them in country folders.
- Store a given official EU-language representation once under `source-library/core/<language-code>/`, even when several jurisdictions use that language. Each country pack records source IDs and canonical paths in `references/shared-core.json`; do not duplicate the files or use filesystem symlinks. For an external-only reference, include the official URL and mark the local path absent until the source bytes are acquired and reviewed.
- Do not create a country `core/` folder solely to point to shared material. Do not create empty `core/` folders, coverage-only README stubs, or placeholder folders for unavailable translations. Create a country-local `core/` only for actual EU-language files that are held there and are not part of the shared corpus.
- English is an official language in Ireland and Malta, and the shared English corpus already serves their English-language EU material; neither needs country-specific English files. Add Irish or Maltese representations only if the plugin needs them and actual official files are available. For other countries, add only language-specific EU representations that are actually held in the library. A country `core/` never contains that country's national legislation, guidance, or decisions.
- `documents/` is for national text the pack has reviewed and chosen to store locally. Use the source-type folders; do not mix sources by discovery pass or retrieval method. A local file is optional: a human-reviewed official URL can be used and can support topic evidence without a saved copy. Record link-only references in the manifest/source list; do not create placeholder files.
- `candidates/` is optional and contains retained, unaccepted captures or conversions. Organize it by source type. Put catalogues, search surfaces, and textless portals under `discovery/`. Do not create parallel `monitor-candidates/` trees. An uncaptured official lead remains a reference entry, not a failed or unusable source.
- `references/candidate-manifest.json` is the canonical inventory. The source list is its human-readable counterpart. `references/source-rules.json` records the retrieval and conversion rule assigned to each candidate. Keep retrieval evidence, legal-currentness review, scope, and sustainability findings distinct.
- Keep transient downloads, scratch conversion output, and pending updates in the repository's configured temporary workspace, not in a country `work/` folder. Retain exact source bytes or derived inputs under `captures/` only when a documented replay, audit, or legal-provenance need justifies durable storage; record their URLs, hashes, dates, and derivation steps. These are local-copy maintenance checks, not prerequisites for ordinary use of a reviewed official link or for topic evidence based on directly reviewed material. Do not create empty capture folders or commit disposable intermediates.
- `scripts/` is optional for inventory-only packs. Put any pack-specific scripts there rather than at the pack root.
- `SKILL.md` is optional. Add it only when a maintained operational workflow uses the pack; a candidate inventory alone is not a runnable skill.

## Template files

Copy and complete the adjacent `README.template.md`, `SKILL.template.md` (if applicable), and reference templates, including `source-rules.template.json` for candidate records. Add `shared-core.template.json` when the pack references shared local or external-only EU-language representations. Remove placeholders and unused empty folders before treating a pack as complete.
