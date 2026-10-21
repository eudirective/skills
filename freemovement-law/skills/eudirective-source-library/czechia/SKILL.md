---
name: czechia-legal-source-system
description: Maintain Czech national source candidates for EU free movement, EU-family residence, visa procedure, civil-status evidence, and administrative remedies.
metadata:
  version: 0.4.3
  short-description: Czechia legal-source acquisition pack
---

# Czechia legal-source system

Pack version 0.4.3, updated 21 October 2026. The [source list](references/source-list.md) and [candidate manifest](references/candidate-manifest.json) contain 63 records: 62 official external references accepted within recorded scope, one Decree 429/2010 reference pending whole-portal human review, zero accepted local copies, and zero adequately covered topics. The 62 link-only decisions cover the 17 dated e-Sbírka law texts, 26 earlier official pages, 15 Czech-language government pages and 4 individual decisions. See the [source acceptance register](references/source-acceptance.json), [coverage model](references/coverage-model.json), and [dependency register](references/source-dependencies.json). Candidates are filed under `candidates/<source-class>/`; retrieval bytes and run state are stored in the configured project temp tree.

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

The 17 e-Sbírka official source references may be used within the dated scopes in the acceptance register. This does not accept their local conversions, establish topical adequacy, or complete the country review. The 26 earlier non-law references, 15 added Czech-language pages, and 4 court decisions are link-accepted within their stated scopes; their local conversions remain unaccepted. Decree 429/2010 remains pending human review. Country review remains incomplete.
