# Luxembourg source candidates

This 42-record inventory spans legislation, guidance, forms, visas and missions, procedure, remedies, case law, oversight, civil status and legal aid. The capture pass retrieved 38 records and converted 35 to unaccepted Markdown review candidates. Three portal shells yielded no text; four candidate URLs returned 404. All 35 conversions and all three preserved PDF originals pass offline hash/replay verification. No locally stored artifact is accepted.

Legislation uses the official Casemates LegalDocML endpoint through ELI content negotiation. Direct official pages use an allowlisted HTTPS capture helper. Three retained PDFs have byte-preserving captures and text extraction with pinned `pypdf`; changed local conversions are staged for review. These replay details govern retained copies. For ordinary research, a human-reviewed official source link is sufficient; check that source's displayed version and caveats, using the government-published consolidation or closest available government text.

Run `python sync_luxembourg.py sync` to refresh captures, `python sync_luxembourg.py verify` to check hashes and replay conversions offline, or `python sync_luxembourg.py convert-pdfs` to convert already captured PDFs without a network request. Install the pinned dependency from this directory's `requirements.txt` before PDF conversion/replay.
