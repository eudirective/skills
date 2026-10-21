# Ireland source candidates

**Status (21 October 2026):** 51 candidate records; 29 official external links accepted within recorded scopes; 0 local copies accepted; 0 topics accepted; country review incomplete. Twenty-six saved conversions remain review-only. Twenty-one other candidate routes are verified but still need scope or currentness review; the listed Legal Aid Board PDF (ie-45) returned 404. Historical 403 responses describe the bounded downloader, not access for every user. See the [source-acceptance register](references/source-acceptance.json) for accepted links and human-review sites.

The optional eISB local-copy lane preserves source hashes and exact URLs, checks candidate-specific identity markers, caps responses at 32 MiB, and replays saved conversions offline. eISB’s Open Data PSI licence applies to eISB content only. Some captured legislation is an enacted/made instrument rather than a consolidated current text. For ordinary research, use a human-reviewed official eISB reference; prefer its latest government-published consolidation, or use the closest official text with its date and limits. Check a named amendment or commencement issue only when it may affect the provisions in scope; do not require a full chain review before using the link.

Install the pinned PDF converter with `python3 -m pip install -r requirements.txt`. From this folder, run `python3 sync_ireland.py sync`, `python3 sync_ireland.py convert`, then `python3 sync_ireland.py verify`. Source bytes are stored in the repository’s ignored `temp/ireland/raw/` capture area; the retrieval manifest records hashes and conversion status.

Some publisher hosts returned HTTP 403 in this retrieval environment, and the candidate Legal Aid Board PDF path returned 404. Current ISD guidance discovered through the official search index now says EUTR1/EUTR1A applications are handled online and paper forms are requested through the service portal; this makes the old static EUTR1 PDF a dated candidate rather than a current default. ISD/gov.ie guidance, registration, visa/mission, and several oversight pages remain unresolved in local retrieval.

- [Candidate source list](references/source-list.md)
- [Source acceptance register](references/source-acceptance.json)
- [Candidate manifest](references/candidate-manifest.json)
- [Retrieval manifest](references/ireland-retrieval-manifest.json)
- [Sustainability assessment](references/sustainability-assessment.md)

