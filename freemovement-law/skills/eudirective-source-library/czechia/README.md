# Czechia national source pack

**Status:** 31 candidate records: 10 official guidance pages have been retrieved and converted to review candidates; 17 legal texts are blocked pending e-Sbírka API registration; four entries are discovery-only. No source has been accepted.

The inventory contains 31 candidate source records and one separate e-Sbírka infrastructure reference.

The pack is scoped to Czech national law and official administrative, consular, court, and oversight materials that intersect with EU free movement and EU citizens' family members. EU law and CJEU judgments remain in the EU core.

- [Source list](references/source-list.md): reviewable official source targets and taxonomy tags.
- [Candidate manifest](references/candidate-manifest.json): machine-readable IDs and current acquisition state.
- [Pack instructions](SKILL.md): status boundaries and required retrieval work.

The principal legislation publisher is [e-Sbírka](https://e-sbirka.gov.cz/), the Czech official electronic Collection of Laws and International Treaties. The official e-Sbírka REST interface requires an issued API access key. The local monitor now has a `czechia` pack action for official guidance retrieval, conversion, replay verification, and reviewed acknowledgement. The separate hosted connector still has no Czechia pack ID.

Run `node scripts/sync-czechia.mjs --check|--sync|--verify|--ack <source-id>` from this directory. `--sync` saves original HTML and review Markdown under `work/`; `--verify` replays conversions offline. The local MCP action uses the same script from the plugin bundle.

This initial inventory is not exhaustive. It prioritizes free-movement residence, EU-family visa and residence procedures, civil-status evidence, administrative procedure, litigation, complaints, access to information, and data protection. Discovery repositories are monitor-only targets, not evidence that any individual judgment has been collected.
