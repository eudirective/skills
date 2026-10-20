# Estonia source candidates

**Status (19 October 2026):** 42 candidates; 21 identified legal-text records have full-text conversions, plus 12 linked current Estonian consolidations for English source leads; all remain unaccepted. This includes 13 unique current national acts, two exact Estonian regulation editions, one future-effective EU-citizen-act edition, and 16 exact English editions. The broader register covers residence guidance and forms, visas and missions, procedure and remedies, privacy, oversight, legal aid, and courts; 17 additional official pages also have review-candidate conversions. It remains a bounded inventory, not a complete account of Estonian sources.

The current-text rule queries the official law list for an effective date, follows all result pages, selects exact Estonian titles, then downloads the returned global IDs through the Gazette's XML API. On 19 October 2026 this resolved 13 unique acts, including the Aliens Act and Citizen of the European Union Act. Exact candidate editions use their published document IDs. English records use the publisher's `blob-html` API and retain the edition's own in-force dates and translation date; they are not treated as current merely because their source URL is a `current` alias. All 33 saved text artifacts pass source-hash and deterministic offline replay checks. None is accepted into the trusted corpus.

The official FAQ documents the dated law search and the XML endpoint introduced on 1 June 2026; the prior `.xml` route was discontinued. The API calls require no account or registration in the demonstrated public route. Reuse terms and rate limits still need a fuller official review. English-version retrieval works through an observed publisher API route, but its long-term stability is less well documented than current Estonian XML retrieval. Guidance, forms, visa and mission information, administrative procedure, remedies, oversight, and legal aid still need their own source-specific sustainability review.

Run `python3 sync_estonia_legal_texts.py sync` to refresh current acts and exact editions, then `python3 sync_estonia_legal_texts.py verify` to replay every saved XML and English HTML conversion offline. The narrower two-act workflow remains available through `python3 convert_riigiteataja.py sync`, `convert`, and `verify`. Captured original bytes are stored under the ignored repository `temp/estonia/raw/`; the manifests retain source URLs, IDs, dates, versions, and hashes.

- [Candidate manifest](references/candidate-manifest.json)
- [Source catalog](references/source-catalog.json)
- [Retrieval manifest](references/riigiteataja-retrieval-manifest.json)
- [Sustainability assessment](references/sustainability-assessment.md)
