# Ireland source candidates

**Status (19 October 2026):** 51 candidate records; 26 saved as unaccepted review-candidate text conversions; 0 accepted. The 26 include eISB legislation and amendment records, source-reuse documentation, guidance, oversight, privacy, courts, and service material. The other 25 retrievals returned HTTP 403 (24 records) or 404 (one Legal Aid Board PDF) in the bounded downloader. Their content remains pending; these responses are not treated as evidence that the official pages are unavailable to people using other access routes.

The eISB lane now has a repeatable per-record downloader and converter. It preserves source hashes and exact URLs, checks candidate-specific identity markers, caps each response at 32 MiB, allowlists candidate publisher hosts, and replays saved conversions offline. eISB’s official Open Data PSI licence incorporates CC BY 4.0; that reuse permission applies to eISB content only. Captured legislation is unaccepted and may be an enacted/made instrument rather than a consolidated current text. Compare amendment and commencement records before relying on it.

Install the pinned PDF converter with `python3 -m pip install -r requirements.txt`. From this folder, run `python3 sync_ireland.py sync`, `python3 sync_ireland.py convert`, then `python3 sync_ireland.py verify`. Source bytes are stored in the repository’s ignored `temp/ireland/raw/` capture area; the retrieval manifest records hashes and conversion status.

Some publisher hosts returned HTTP 403 in this retrieval environment, and the candidate Legal Aid Board PDF path returned 404. Current ISD guidance discovered through the official search index now says EUTR1/EUTR1A applications are handled online and paper forms are requested through the service portal; this makes the old static EUTR1 PDF a dated candidate rather than a current default. ISD/gov.ie guidance, registration, visa/mission, and several oversight pages remain unresolved in local retrieval.

- [Candidate source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Retrieval manifest](references/ireland-retrieval-manifest.json)
- [Sustainability assessment](references/sustainability-assessment.md)

