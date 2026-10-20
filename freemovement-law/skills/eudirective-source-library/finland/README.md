# Finland source pack

**Status (19 October 2026):** 36 candidate records; 25 full-text/page conversions are tracked as review candidates (23 converted and two changed versions staged for review); 0 accepted. Eleven legal-text artifacts are captured: eight current Finnish acts and three unofficial English translations. Other candidates include guidance, forms, remedies, court/oversight sources and service discovery routes.

- [Candidate manifest](references/candidate-manifest.json)
- [Source catalog](references/source-catalog.json)
- [Sustainability assessment](references/sustainability-assessment.md)
- [Finlex capture manifest](references/finlex-retrieval-manifest.json)
- [Saved capture specification](references/finlex-captures.json)
- [Capture converter](convert_finlex_capture.py)
- [Current-page RSC capture manifest](references/finlex-rsc-retrieval-manifest.json)
- [Current-page RSC capture specification](references/finlex-rsc-captures.json)
- [Current-page RSC converter](convert_finlex_rsc_capture.py)

Install the pinned PDF converter with `python3 -m pip install -r requirements.txt`. Run `python3 convert_finlex_capture.py sync-api` and `python3 convert_finlex_capture.py sync-pdfs` for bounded Finlex checks; the PDF sync reopens each official translation-history page, validates its title, completion date and amendment cutoff, rediscovers the English PDF link, and checks the PDF identity. Then run `python3 convert_finlex_capture.py convert` to rebuild candidates and `python3 convert_finlex_capture.py verify` to check retained source hashes and replay conversions offline. The two current-text law-page captures remain browser-rendered fallbacks and must be refreshed separately; the script does not automate those fragile page routes.

Finlex’s no-registration Akoma Ntoso API is not complete for these candidate records. It returned XML for Acts 808/2019, 1050/2018 and 616/2019, while current consolidated-text requests for Acts 301/2004, 434/2003, 621/1999, 423/2003 and 257/2002 returned 404. The first two acts are captured from their official current-text pages through rendered main content. The other three are captured from the Finnish text sections embedded in their official current-page React Server Component stream; this page-specific fallback is fragile and fails closed on identity, ELI, heading-count and body-size changes. The API conversion for Act 808/2019 has a date conflict: its expression ELI says 5 July 2019, its consolidation date is 27 March 2026, and the same metadata lists amendment 213/2026 taking effect 14 April 2026. The three unofficial English translations are saved with publisher-recorded amendment cutoffs. All eleven legal-text conversions remain review candidates pending version and amendment review.

The [Aliens Act conversion](candidates/fi-aliens-act-301-2004-current.md) is a review candidate, not accepted. Its current Finlex ELI version is 26 June 2026. All source-specific XML, PDF and page conversions have offline hash/replay verification; the generic monitor pass separately records short page shells, blocked routes and changed captures.
