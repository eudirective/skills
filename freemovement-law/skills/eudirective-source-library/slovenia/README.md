# Slovenia national-source candidates

Inventory dated 2026-10-18; capture state updated 2026-10-19. It contains 42 official-source candidates across national law and publication, EU/EEA/Swiss residence routes, visas and mission practice, administrative procedure and remedies, family-status evidence, privacy, oversight, legal aid and selected case-law discovery. The shared bounded capture saved 42 responses and converted 23; 19 pages were interactive or discovery shells. All 23 conversions replay offline; 0 sources are accepted.

- Candidate register and search evidence: [`references/source-list.md`](references/source-list.md)
- Machine-readable candidate metadata: [`references/candidate-manifest.json`](references/candidate-manifest.json)
- Capture ledger: [`references/slovenia-capture-results.json`](references/slovenia-capture-results.json)
- Shared capture/replay rule: [`../sync_candidate_pages.py`](../sync_candidate_pages.py)
- Proposed-route sustainability assessment: [`references/sustainability-assessment.md`](references/sustainability-assessment.md)
- Country sequence and prior findings: [`../references/eea-switzerland-country-expansion.md`](../references/eea-switzerland-country-expansion.md)

Comparison seed: Denmark's EU free-movement residence regulation and official guidance. The GOV.SI parent page expressly extends relevant EU-citizen Foreigners Act provisions to EEA nationals and their family members, while Switzerland is described under a separate EU–Swiss agreement route. These are documented scope differences, not an assertion of legal equivalence.

The PISRS developer API still requires Government Office for Legislation authorization; it was not used. The generic public-page pass saved 42 responses and converted 23, including public Official Gazette PDFs. This demonstrates specific routes, not a complete currentness or reuse rule; full-text terms and automated amendment discovery remain unresolved. OPSI's CC BY 4.0 dataset is limited to basic regulation metadata and does not grant full-text access or API authorization.

Refresh with `python source-library/sync_candidate_pages.py slovenia sync`; replay hashes/conversions with `python source-library/sync_candidate_pages.py slovenia verify`. The PISRS API remains gated; this capture used public candidate URLs only.
