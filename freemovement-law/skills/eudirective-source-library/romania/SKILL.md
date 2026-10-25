---
name: romanian-legal-source-system
description: Retrieve, convert, and monitor the Romanian national legal sources in this pack. Use when updating or checking Romanian legislation, Romanian court decisions, or Romanian authority guidance listed in its manifest.
metadata:
  short-description: Romanian legal source retrieval, conversion, and updates
---

# Romanian legal source system

Version 0.4.4, updated 2026-10-24. This national pack is stored at `eudirective-source-library-0.6.0/romania/`; all Romanian EU-language representations are stored centrally under `source-library/core/ro/` and routed through this pack’s shared-core record. The 23 expansion representations retain their reviewed representation-level acceptance. The 36 earlier files retain their previous status: 34 prior conversions had failed live rechecks, and two guidance retrieval candidates remain unpromoted. This storage consolidation does not change those states. Reviewed Romanian national legislation, court decisions, and authority material are stored under `romania/documents/`. It includes 14 case-law follow-up records with official versus secondary source quality recorded per entry. The guidance lane adds 10 official authority sources to this pack, with its own manifest, source bytes, Markdown, and replay verification.

Use this skill only for the Romanian source inventory in `references/source-list.md`. It covers Romanian national legislation, Romanian court decisions, Romanian authority guidance, and listed discovery repositories. Three follow-up case-law entries are secondary reproductions or a court-authored digest and are marked as such in the manifest and converted Markdown. EU legislation and CJEU judgments belong to the separate EU source system.

The manifest and retrieval pipeline are Node-only. The source list is the inventory authority; do not silently add unrelated sources. Read `references/manifest.json` for the compiled records and the latest run report under the project-root `temp/eudirective-source-library-0.6.0/romania/work/` tree.

For ordinary research, open the responsible official publisher page and use a clearly identified government-published consolidation or the closest government-published text. Record its language, visible date/cutoff, relevant content, and limitations in `references/source-acceptance.json`. A human-reviewed official link is usable without running the local update pipeline, saving bytes, converting, replaying hashes, or accepting a local copy. Check an individual later amendment only when it may materially affect the issue. If the publisher's identity, legal status, or relevant page cannot be established, offer the whole official website for human review in the acceptance register and continue independent work. Do not create placeholder files or add link-only references to the monitored manifest unless local copying or scheduled monitoring is actually needed.

## Optional local-copy maintenance

Use this workflow only when updating retained Romanian source copies or a recurring monitor is requested. It does not gate ordinary reference use or topic research.

1. Run `node scripts/build-manifest.mjs` after changing the included source list.
2. Run `node scripts/sync-romania.mjs --check` to retrieve and compare all records without writing source snapshots. Official publishers and the three explicitly labeled secondary case-law hosts are separately allowlisted.
3. Run `node scripts/sync-romania.mjs --discover` to refresh discovery findings without accepting changes.
4. Run `node scripts/sync-romania.mjs --sync` to save official HTML snapshots, state, search baselines, reports, and converted Markdown candidates under the project-root `temp/` tree.
5. Review changes, newly listed Portal Legislativ history records, and title-search hits in the latest report under `temp/eudirective-source-library-0.6.0/romania/work/`. A candidate is not an accepted legal source just because it appears in search results.
6. Accept a reviewed conversion with `node scripts/sync-romania.mjs --ack <source-id>`. To accept every conversion in the completed sync report after matching each candidate hash, run `node scripts/sync-romania.mjs --ack-all`. The manifest's `document_class` and `document_path` place accepted Markdown under `documents/<class>/`; the matching candidate copy is removed from `temp/`.

The converter extracts Portal Legislativ decisions and consolidated text from their legal-content containers, ÎCCJ judgments from the ID-validated `jurisprudence_details` record, printable forms from their document body, and guidance or secondary case-law sources from source-specific main-content containers. It records separate hashes for the fetched page, extracted source body, and Markdown so page chrome changes can be distinguished from text or converter changes. Markdown records content language and source quality; secondary reproductions are never labeled official.

Discovery checks each listed national act against Portal Legislativ's public title-search results and compares official document IDs with the saved baseline. Direct source history is monitored for newly linked forms. The court portal entry monitors the exact HTTP WSDL URL documented on its official programmatic-access page; this narrow transport exception applies only to that WSDL. The service describes case and hearing queries, not a comprehensive judgments feed. Review each candidate at its official record before updating accepted files. Result-page limits or official-host availability can limit discovery; the report must retain and show those failures rather than bypass them.

The inventory is non-exhaustive. Hashes and successful retrieval do not establish extraction fidelity or legal coverage. A link-only reference is limited to its displayed date/cutoff and recorded scope; check a later amendment only when material. Topic coverage and country completion are separately recorded in `references/coverage-register.md` and `references/sustainability-assessment.md`. The source-list's local-copy inventory date and limitations remain recorded in the manifest; link-only references in the source-list appendix are not compiled into monitored targets.

The main national inventory has 71 converted documents under `documents/` and eight monitor-only entries. The separate authority-guidance lane adds 10 documents under `documents/guidance/`, `documents/forms/`, and `documents/procedure/`. The 14 added case-law records comprise 11 official texts and three explicitly marked secondary sources. Raw page hashes may change without a legal-body change; compare `body_sha256` and `markdown_sha256` in the report before treating `official_page_changed` as a substantive update.

## Added guidance lane

For the optional guidance-copy lane, run `node scripts/sync-guidance.mjs sync` to check the 10 configured sources and `verify` to reproduce saved Markdown. Review and promote changed local copies only when maintaining that lane. Original PDF/HTML bytes, state, and reports are retained under project-root `temp/`.
