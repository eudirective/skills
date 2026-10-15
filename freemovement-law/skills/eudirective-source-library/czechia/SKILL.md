---
name: czechia-legal-source-system
description: Maintain the Czech national source candidates for EU free movement, EU-family residence, visa procedure, civil-status evidence and administrative remedies.
metadata:
  version: 0.2.0
  short-description: Czechia legal-source acquisition pack
---

# Czechia legal-source system

Version 0.2.0, created 2026-10-15. This Czech national pack is separate from the Czech-language EU mirror. Its inventory authority is [references/source-list.md](references/source-list.md); [candidate manifest](references/candidate-manifest.json) records the 31 candidates. Ten official guidance pages have source snapshots and unaccepted Markdown candidates. Seventeen legal text targets await e-Sbírka API access; four records are discovery-only.

## Scope

The pack is limited to Czech national legislation, official Czech guidance, official court and oversight discovery channels, and source evidence that bears on EU free movement, EU citizens and their family members, entry and residence, consular process, family-status evidence, administrative procedure, information access, data protection, and remedies. EU legislation and CJEU materials belong in the EU core and are not duplicated here. General third-country immigration, asylum, and unrelated Czech law are out of scope unless a demonstrated intersection with an EU free-movement issue is recorded.

The source language is Czech (`cs`). Official English guidance is included as a separate official-language representation where available; it does not replace the Czech legal text. The source list is a research inventory, not a finding that all applicable law has been identified.

## Authority and acquisition status

- e-Sbírka is the official electronic Collection of Laws and International Treaties. Its pages identify the displayed consolidated text as an informative text; retain the act's official promulgation and temporal-version metadata and do not treat a web-page hash as proof of a law amendment.
- e-Sbírka documents a REST API that requires an API access key. No key is bundled in this pack. Retrieval must use an authorized official interface or a documented official document endpoint; never put a key in source files or reports.
- The bundled local update monitor advertises a `czechia` pack with `check`, `sync`, `verify`, and `ack` actions. The separate hosted EU Directive Source Library connector does not currently advertise Czechia. `sync-czechia.mjs` retrieves only the allowlisted official guidance pages; it leaves legal text retrieval blocked until a registered e-Sbírka API key is available and records court/oversight directories as monitor-only.
- Before promotion, validate the official host, source identity, language, temporal version, any future effective date, and exact text. Keep official legal text, authority guidance, court decisions, and discovery-only repositories in separate source classes.

## Next implementation steps

1. Run `node scripts/sync-czechia.mjs --check` or `--sync` to refresh official guidance candidates; run `--verify` to replay saved conversions; use `--ack <source-id>` only after candidate review.
2. Obtain approved e-Sbírka REST API registration before adding the 17 statutory texts. Keep API keys in the runtime environment, never in manifests or source files.
3. Add the current and historical legal versions, source bytes, deterministic Markdown, and hashes after the authorized text endpoint and temporal metadata are verified.
4. Review candidate identity, source language, dates, enactment, entry into force, applicability, and future versions before acceptance.

No accepted Czech corpus documents are included in version 0.2.0.
