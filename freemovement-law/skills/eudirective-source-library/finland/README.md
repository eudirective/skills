# Finland source pack

**Status (21 October 2026):** 36 candidate records; eight current Finnish Finlex law-page references are accepted externally; 25 full-text/page conversions remain review candidates (23 converted and two changed versions staged for review); 0 local copies accepted. Eleven legal-text artifacts are captured: eight current Finnish acts and three unofficial English translations. Other candidates include guidance, forms, remedies, court/oversight sources and service discovery routes.

- [Candidate manifest](references/candidate-manifest.json)
- [Source catalog](references/source-catalog.json)
- [External source acceptance register](references/source-acceptance.json)
- [Sustainability assessment](references/sustainability-assessment.md)
- [Finlex capture manifest](references/finlex-retrieval-manifest.json)
- [Saved capture specification](references/finlex-captures.json)
- [Capture converter](convert_finlex_capture.py)
- [Current-page RSC capture manifest](references/finlex-rsc-retrieval-manifest.json)
- [Current-page RSC capture specification](references/finlex-rsc-captures.json)
- [Current-page RSC converter](convert_finlex_rsc_capture.py)

The eight accepted legal references are direct official Finnish Finlex current-law pages with their edition dates recorded in the [acceptance register](references/source-acceptance.json). Acceptance covers the external page reference only: no local copy or legal topic is accepted, and Finland remains incomplete. Ordinary research can use a human-reviewed official Finlex page and its displayed edition/cutoff; no API request, local capture, conversion, or replay is required for that use. The commands below are optional retained-copy maintenance. Install the pinned PDF converter only if rebuilding saved files. Use `python3 convert_finlex_capture.py sync-api` and `sync-pdfs` for the bounded API/PDF capture routes, `convert` to rebuild candidates, and `verify` to replay saved conversions. The API is incomplete for these records; resolve the known 808/2019 date conflict only if it affects the provisions in scope. Do not build a bulk download or custom API workflow just to cite a current official Finlex page.

Finlex’s no-registration Akoma Ntoso API is not complete for these candidate records. It returned XML for Acts 808/2019, 1050/2018 and 616/2019, while current consolidated-text requests for Acts 301/2004, 434/2003, 621/1999, 423/2003 and 257/2002 returned 404. The first two acts are captured from their official current-text pages through rendered main content. The other three are captured from the Finnish text sections embedded in their official current-page React Server Component stream; this page-specific fallback is fragile and fails closed on identity, ELI, heading-count and body-size changes. The API conversion for Act 808/2019 has a date conflict: its expression ELI says 5 July 2019, its consolidation date is 27 March 2026, and the same metadata lists amendment 213/2026 taking effect 14 April 2026. The official page reference is accepted, but the local conversion remains unaccepted for date-sensitive use until this metadata conflict is resolved. The three unofficial English translations are saved with publisher-recorded amendment cutoffs. All eleven legal-text conversions remain review candidates. Eight Finnish page references are accepted externally; this does not promote any local conversion. Use the latest Finlex-published edition and its cutoff; resolve the specific 808/2019 date conflict and any known material post-cutoff change. A full amendment-chain review is not required.

The [Aliens Act conversion](candidates/fi-aliens-act-301-2004-current.md) is a review candidate, not accepted. Its current Finlex ELI version is 26 June 2026. All source-specific XML, PDF and page conversions have offline hash/replay verification; the generic monitor pass separately records short page shells, blocked routes and changed captures.
