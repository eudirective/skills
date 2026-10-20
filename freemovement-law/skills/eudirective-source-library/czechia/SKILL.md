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

- **Current legal text:** e-Sbírka is the official electronic Collection of Laws and International Treaties. The legal adapter uses its public page-data service at `/sbr-externi/dokumenty-sbirky/{encoded-stable-act-url}` to resolve the current version and retrieve ordered XHTML fragments. It validates the act citation, `typZneni=AKTUALNI`, effective-from date, current-version path, fragment identity, page count, and duplicate fragment identifiers. Exact metadata/page JSON is saved and hash-pinned; Markdown conversion is deterministic and replayable. The tested route required no account or key. It is separate from e-Sbírka's documented REST API, which requires registration and an issued key.
- **Commands for legal texts:** from this pack, run `python scripts/sync_esbirka_open_data.py sync` (optionally followed by candidate IDs) and `python scripts/sync_esbirka_open_data.py verify`. The converter writes only unaccepted review candidates under `candidates/legislation/`. Exact raw responses are stored under project temp and referenced by the capture ledger's pack-relative `work/raw/` paths. The Node updater's former date-bound PDF route is obsolete for legal-text capture; its law results must not be used as evidence when the page-data adapter has not run.
- **Version and authority limits:** e-Sbírka labels its consolidated text informative. A successful page-data capture establishes the publisher response and recorded version metadata, not legal force, completeness, or applicability. Reconcile the captured current version with official promulgation and any future-effective wording before accepting or relying on it. The National Open Data Catalog's e-Sbírka datasets are a separate research route; its publisher warns that identifiers and structures can change through 15 January 2027, so this pack does not depend on it for recurring production retrieval.
- **Official guidance:** `scripts/sync-czechia.mjs --sync|--verify|--reconvert` maintains the configured official HTML guidance candidates under typed `candidates/` folders. Its H1 identity, encoding, primary-region, and hash checks do not establish that parent indexes or linked attachments are complete. The Node updater still contains the legacy date-bound PDF lane; use the Python adapter for statutes.
- **Forms and discovery pages:** the 13 monitor/discovery records have captured exact responses and converted text, but they do not form a sustainable full-text law feed. The MOI and MFA parent indexes are the rediscovery points for changing form URLs; the renewal-form URL was corrected from the official forms index. The MFA mission directory is paginated and local practice varies. Court and oversight search pages are discovery surfaces, not individual decisions or complete feeds. Only blank forms are in scope; do not collect completed applications or personal submissions.
- **Jurisdictional scope:** Czech MOI guidance describes similar procedures for Icelandic, Liechtenstein, Norwegian, and Swiss citizens. Switzerland is not an EU or EEA EFTA member. UK Withdrawal Agreement beneficiaries follow a distinct route.

## Review before acceptance

For each candidate, verify the official host, instrument identity and type, Czech or official-language text, temporal version, enactment, entry into force, applicability, future versions, extraction quality, and reuse conditions. Keep laws, guidance, forms, mission practice, and discovery repositories in distinct source classes. A hash or successful conversion is not a trust decision.

No Czech source has been accepted into the trusted corpus.
