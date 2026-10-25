# Finland source pack

**Status (24 October 2026):** The inventory has 37 source records. Thirty-four official external references and two dated Finnish local copies are accepted. One obsolete or out-of-scope Migri route is dispositioned, and two oversight routes remain under human review. No legal topic is accepted, and Finland is incomplete.

- [Candidate manifest](references/candidate-manifest.json)
- [Source catalog](references/source-catalog.json)
- [External source acceptance register](references/source-acceptance.json)
- [Shared EU-language references](references/shared-core.json)
- [Sustainability assessment](references/sustainability-assessment.md)
- [Finlex capture manifest](references/finlex-retrieval-manifest.json)
- [Saved capture specification](references/finlex-captures.json)
- [Capture converter](convert_finlex_capture.py)
- [Current-page RSC capture manifest](references/finlex-rsc-retrieval-manifest.json)
- [Current-page RSC capture specification](references/finlex-rsc-captures.json)
- [Current-page RSC converter](convert_finlex_rsc_capture.py)

The two accepted local texts are the Finnish Aliens Act 301/2004 and Administrative Procedure Act 434/2003. Their Finlex editions and copy hashes are recorded in the [acceptance register](references/source-acceptance.json). The captured source and conversion replay hashes were checked, but the texts were not compared clause by clause with the publisher pages. These are dated copies; use Finlex for later changes.

The accepted external references include official Finlex statutory pages, guidance, source-discovery and retrieval pages, court information, and service locators. Three English Finlex translations are accepted only as unofficial language aids: the Aliens Act translation tracks amendments through 389/2023; the Administrative Procedure Act translation through 893/2015; and the Administrative Judicial Procedure Act translation through 639/2021. These are not current English legal texts. Verify legal wording against the official Finnish or Swedish version and check current agency instructions where fees, deadlines or service channels may change.

All unaccepted converted page and text artifacts are retained in the EU Source Update Monitor's indexed local-only archive. They do not establish topic coverage. The optional Finlex converters keep raw captures and regenerated review outputs in the shared temporary workspace when `PUBLIC_DATA_TEMP_ROOT` is set; they do not create pack-local candidate folders.
