# Greece source candidates

Skill: author-source-pack-rules v1.0.1

Greece has a bounded discovery register of 56 official-source candidates across legal publication, free movement/residence, visa and mission practice, civil status, public access and procedure, courts, complaints, privacy, legal aid and selected local practice. The pack has 0 locally stored conversions accepted. On 19 October 2026, the shared bounded capture rule saved and converted 40 candidate texts; 16 requests failed, including 14 HTTP 403 responses and 2 TLS certificate errors. The captured conversions remain review artifacts, but official government links may be used manually within their displayed scope and cutoff.

The official Gazette route retrieved known issue PDFs and legal texts for this bounded pass. Prefer a current government-published consolidation; otherwise use the closest government-published edition and record its cutoff. A complete amendment-discovery mechanism or custom API is not needed for ordinary source use. The National Printing House search-site terms restrict copying/conversion, so use a human-reviewed official link where local copying is not clearly permitted; do not treat this as a reason to reconstruct the full law from Gazette issues. The codification portal was described as being in its final implementation stage in the recorded review.

- [Candidate source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Capture ledger](references/greece-capture-results.json)
- [Shared capture/replay rule](../sync_candidate_pages.py)
- [Sustainability assessment](references/sustainability-assessment.md)

Refresh with `python source-library/sync_candidate_pages.py greece sync`; replay captured hashes and conversions with `python source-library/sync_candidate_pages.py greece verify`. The shared rule does not validate currentness or publisher reuse permission.
