# Estonia source candidates

**Status (19 October 2026):** 42 candidates; 21 identified legal-text records have full-text conversions, plus 12 linked Estonian consolidations for English source leads; the local conversions remain unaccepted. This includes 13 unique Estonian acts, two exact regulation editions, one future-effective EU-citizen-act edition, and 16 exact English editions. The broader register covers residence guidance and forms, visas and missions, procedure and remedies, privacy, oversight, legal aid, and courts; 17 additional official pages also have review-candidate conversions. It remains a bounded inventory, not a complete account of Estonian sources.

The optional local-copy workflow queries the official law list for an effective date, follows result pages, selects Estonian titles, then retrieves the returned global IDs through the Gazette XML API. On 19 October 2026 this resolved 13 unique acts, including the Aliens Act and Citizen of the European Union Act. English records retain their own in-force and translation dates; they are not current merely because a URL contains `current`. All 33 saved text artifacts pass source-hash and deterministic offline replay checks. None of the local conversions is accepted into the trusted corpus. For ordinary research, a human-reviewed direct Riigi Teataja text is enough; record its displayed validity and check named later changes only when they affect the provisions in scope.

The official FAQ documents the dated law search and the XML endpoint introduced on 1 June 2026; the prior `.xml` route was discontinued. The API calls required no account or registration in the observed route. API reuse terms and rate limits matter only if retaining copies or automating retrieval. English-version retrieval works through an observed publisher API route, but its long-term stability is less documented than current Estonian XML retrieval. For ordinary research, use the reviewed official page and displayed validity; do not build an API workflow just to cite it.

Optional retained-copy workflow: run `python3 sync_estonia_legal_texts.py sync` to refresh the configured acts and editions, then `verify` to replay saved XML and English HTML conversions offline. The narrower two-act workflow remains available through `python3 convert_riigiteataja.py sync`, `convert`, and `verify`. These checks apply to the saved artifact; human-reviewed official links remain usable without them.

- [Candidate manifest](references/candidate-manifest.json)
- [Source catalog](references/source-catalog.json)
- [Retrieval manifest](references/riigiteataja-retrieval-manifest.json)
- [Sustainability assessment](references/sustainability-assessment.md)
