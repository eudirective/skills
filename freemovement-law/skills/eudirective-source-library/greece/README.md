# Greece source candidates

Skill: author-source-pack-rules v1.0.1

Greece has a bounded discovery register of 59 official-source candidates across legal publication, free movement/residence, visa and mission practice, civil status, public access and procedure, courts, complaints, privacy, legal aid and selected local practice. The original 56-candidate capture run on 19 October 2026 converted and replay-verified 40 texts; 16 requests failed (14 HTTP 403, 2 TLS errors). Three additional legal sources found during review are recorded as link-only candidates: the 2026 PD 106/2007 amendment, the 2025 return-procedure law and a 2020 transitional provision. Six official legal references have been reviewed for link use; 0 locally stored copies are accepted.

No public government consolidation of PD 106/2007 was found; the National Codification Portal still says it is in its final implementation stage, and the Migration Ministry legislation index does not list the later 2026 amendment. The original decree and targeted Laws 4071/2012, 4540/2018, 4686/2020, 5226/2025 and 5275/2026 are reviewed by link for their specific provisions. Law 5226/2025 Article 28 supplies the return-procedure and judicial-protection framework for EU-free-movement cases. Law 5275/2026 Article 53 changes the document duration for specified extended-family/partner routes to five years, effective 6 February 2026. Law 4686/2020 Article 43 concerns named legacy permit cases only. This bounded source method does not reconstruct every Gazette amendment. Use a human-reviewed official link where copying terms are unclear.

- [Candidate source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Source acceptance register](references/source-acceptance.json)
- [Capture ledger](references/greece-capture-results.json)
- [Shared capture/replay rule](../sync_candidate_pages.py)
- [Sustainability assessment](references/sustainability-assessment.md)

Refresh with `python source-library/sync_candidate_pages.py greece sync`; replay captured hashes and conversions with `python source-library/sync_candidate_pages.py greece verify`. The shared rule does not validate currentness or publisher reuse permission.
