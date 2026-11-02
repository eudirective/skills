# Finland source pack

**Status (2 November 2026):** Finland has 37 source records: 35 accepted official external references, six accepted dated local copies (four Finnish legal texts and two unofficial English language aids), two maintained locator notes, and five maintained Markdown summaries/transcriptions. Two official oversight routes remain under human review and two candidate records remain unresolved. No legal topic is accepted, and Finland is incomplete. The DVV foreigner-registration note summarizes current official forms linked from its guidance route; the guidance pages themselves returned 403 and are not claimed as fully reviewed. The DVV municipality-form transcription covers rendered instructions and fields but not client-side behavior. The Oikeus.fi summary covers the substantive page but is not a verbatim conversion.

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

The four Finnish local legal texts are the Aliens Act 301/2004, Administrative Procedure Act 434/2003, Data Protection Act 1050/2018 (Finlex edition dated 2026-05-22), and Police Personal Data Act 616/2019 (Finlex consolidation dated 2026-10-09). Act 616/2019's 61 section bodies match the pinned Legalize candidate; Act 875/2026 commencement by Government Decree remains unverified. The Data Protection Act capture includes current §§18a and 36a absent from the older candidate; its conversion replays from the retained official-page capture. Two additional local copies are unofficial English language aids, not current English law. Their hashes and cutoffs are recorded in the acceptance register. Verify later changes in Finlex.

The accepted external references include official Finlex statutory pages, guidance, source-discovery and retrieval pages, court information, and service locators. Three English Finlex translations are accepted only as unofficial language aids: the Aliens Act translation tracks amendments through 389/2023; the Administrative Procedure Act translation through 893/2015; and the Administrative Judicial Procedure Act translation through 639/2021. These are not current English legal texts. Verify legal wording against the official Finnish or Swedish version and check current agency instructions where fees, deadlines or service channels may change.

Unaccepted converted page and text artifacts are retained in the EU Source Update Monitor's indexed local-only archive. They do not establish topic coverage. Finlex replay outputs use the shared temporary workspace when `PUBLIC_DATA_TEMP_ROOT` is set; the current Data Protection Act capture is retained under `references/captures/` so its dated local text can be replayed offline. Other sync captures and regenerated review outputs remain in scratch.
