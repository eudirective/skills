---
name: czechia-legal-source-system
description: Maintain Czech national source candidates for EU free movement, EU-family residence, visa procedure, civil-status evidence, and administrative remedies.
metadata:
  version: 0.4.1
  short-description: Czechia legal-source acquisition pack
---

# Czechia legal-source system

Pack version 0.4.1, updated 19 October 2026. The [source list](references/source-list.md) and [candidate manifest](references/candidate-manifest.json) contain 43 records: 17 current legal texts, 13 official guidance/index pages, and 13 monitor/discovery pages. All 43 were replay-verified against captured source bytes; none has been accepted. Candidates are filed under `candidates/<source-class>/`; retrieval bytes and run state are stored in the configured project temp tree.

## Scope

This pack covers Czech national legislation, official Czech guidance, forms, consular instructions, and official court/oversight discovery channels relevant to EU free movement, EU citizens and family members, entry and residence, consular process, family-status evidence, administrative procedure, access to information, data protection, and remedies. EU legislation and CJEU materials belong in the EU core. General third-country immigration, asylum, and unrelated Czech law are out of scope unless an intersection with an EU free-movement issue is recorded.

The principal legal language is Czech (`cs`). Official English administrative guidance is a separate representation and does not replace Czech legal texts. The inventory is a scoped research list, not a completeness claim.

## Retrieval rules and limits

- **Current legal text:** e-Sbírka is the official electronic Collection of Laws and International Treaties. For ordinary research, review its direct consolidated text and record the displayed version/effective date and “informative” label. The optional local-copy adapter uses its public page-data service to retrieve ordered XHTML fragments and validate identity/version metadata; the tested route required no account or key. It is separate from the documented registration-gated REST API.
- **Commands for retained legal copies:** run `python scripts/sync_esbirka_open_data.py sync` and optionally `verify` when refreshing or replaying local copies. The converter's hashes and fragment checks describe that artifact workflow; they are not required for direct official-reference use. The Node updater's former date-bound PDF route is obsolete for local statute capture.
- **Version and authority limits:** preserve e-Sbírka's informative-text caveat. Use the closest government-published edition and record its date. Check a specific promulgation only if a known discrepancy, later change, or commencement condition may materially affect the issue. A future-effective edition should be identified as such; no complete historical amendment-chain reconciliation is required for ordinary use.
- **Official guidance:** `scripts/sync-czechia.mjs --sync|--verify|--reconvert` maintains the configured official HTML guidance candidates under typed `candidates/` folders. Its H1 identity, encoding, primary-region, and hash checks do not establish that parent indexes or linked attachments are complete. The Node updater still contains the legacy date-bound PDF lane; use the Python adapter for statutes.
- **Forms and discovery pages:** the 13 monitor/discovery records have captured exact responses and converted text, but they do not form a sustainable full-text law feed. The MOI and MFA parent indexes are the rediscovery points for changing form URLs; the renewal-form URL was corrected from the official forms index. The MFA mission directory is paginated and local practice varies. Court and oversight search pages are discovery surfaces, not individual decisions or complete feeds. Only blank forms are in scope; do not collect completed applications or personal submissions.
- **Jurisdictional scope:** Czech MOI guidance describes similar procedures for Icelandic, Liechtenstein, Norwegian, and Swiss citizens. Switzerland is not an EU or EEA EFTA member. UK Withdrawal Agreement beneficiaries follow a distinct route.

## Review before acceptance

For an official reference, review the publisher, instrument identity, language, displayed date/version, relevant text, and visible caveats. For a retained local conversion, review extraction and reuse only to the extent needed for that artifact. Check enactment, commencement, or applicability records when a specific issue makes them material; do not require them as a blanket barrier to citing the government-published consolidation. Keep laws, guidance, forms, mission practice, and discovery repositories in distinct source classes.

No Czech source has been accepted into the trusted corpus.
