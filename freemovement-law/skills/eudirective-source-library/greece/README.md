# Greece source candidates

Skill: author-source-pack-rules v1.0.1

Greece has a bounded discovery register of 56 official-source candidates across legal publication, free movement/residence, visa and mission practice, civil status, public access and procedure, courts, complaints, privacy, legal aid and selected local practice. The candidates are not accepted sources. On 19 October 2026, the shared bounded capture rule saved and converted 40 candidate texts; 16 requests failed, including 14 HTTP 403 responses and 2 TLS certificate errors. The conversions replay offline; no source is accepted.

The official Gazette route retrieved known issue PDFs and legal texts for this bounded pass, and conversion replay succeeded. The machine API contract, complete amendment discovery method, and reuse terms remain unresolved. The National Printing House search-site terms contain a material copying/conversion restriction whose application to direct API PDFs and internal monitoring is unresolved. The codification portal is still described as being in its final implementation stage.

- [Candidate source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Capture ledger](references/greece-capture-results.json)
- [Shared capture/replay rule](../sync_candidate_pages.py)
- [Sustainability assessment](references/sustainability-assessment.md)

Refresh with `python source-library/sync_candidate_pages.py greece sync`; replay captured hashes and conversions with `python source-library/sync_candidate_pages.py greece verify`. The shared rule does not validate currentness or publisher reuse permission.
