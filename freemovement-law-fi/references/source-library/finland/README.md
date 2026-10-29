# Finland source pack

**Status (29 October 2026):** The inventory has 37 source records. Thirty-five official external references, four dated local copies, two maintained source locator notes, and five maintained Markdown records: a full rendered-form transcription for the live DVV form and summaries of DVV foreigner-registration form routes, Oikeus.fi administrative appeal guidance and Migri's EU/family landing and EU-registration pages are recorded: the local copies are two Finnish legal texts and two unofficial English language-aid translations. One obsolete or out-of-scope Migri route is dispositioned, and two oversight routes remain under human review. No legal topic is accepted, and Finland is incomplete. The separate DVV foreigner-registration note summarizes current official forms linked from the guidance route; the guidance pages themselves returned 403 and are not claimed as fully reviewed. The DVV municipality form transcription covers rendered instructions and field schema without preserving client-side behavior. The Oikeus.fi summary covers the complete substantive page but is not a verbatim conversion.

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


The Ministry for Foreign Affairs page “A visa to visit Finland” has an independently authored locator at `documents/guidance/fi-mfa-visa-guide.md`. The page itself remains an external reference: the Ministry identifies copyright ownership in published website text and images, and no page content is copied or stored in the library.

The two Finnish local legal texts are the Aliens Act 301/2004 and Administrative Procedure Act 434/2003. A third accepted local file is the unofficial English Aliens Act translation, completed 20 December 2023 through amendment 389/2023; use it only as a dated language aid, not current English law. Its full 188-page Finlex text and SHA-256 are recorded in the [acceptance register](references/source-acceptance.json). The English Administrative Procedure Act translation was completed 7 January 2019 through amendment 893/2015 and is also a language aid only, not current English law. The current Finnish copies are the legal-text sources. Verify later changes in Finlex.

The accepted external references include official Finlex statutory pages, guidance, source-discovery and retrieval pages, court information, and service locators. Three English Finlex translations are accepted only as unofficial language aids: the Aliens Act translation tracks amendments through 389/2023; the Administrative Procedure Act translation through 893/2015; and the Administrative Judicial Procedure Act translation through 639/2021. These are not current English legal texts. Verify legal wording against the official Finnish or Swedish version and check current agency instructions where fees, deadlines or service channels may change.

All unaccepted converted page and text artifacts are retained in the EU Source Update Monitor's indexed local-only archive. They do not establish topic coverage. The optional Finlex converters keep raw captures and regenerated review outputs in the shared temporary workspace when `PUBLIC_DATA_TEMP_ROOT` is set; they do not create pack-local candidate folders.
