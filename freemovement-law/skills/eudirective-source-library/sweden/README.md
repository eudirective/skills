# Sweden national sources

This lane contains Swedish national legislation and Migration Court of Appeal decisions represented in `H:\Downloads\sweden\sweden legal pack.zip`. The Swedish-language EU representations are stored separately in this pack's [`core/`](core/) folder.

## Sources and update signals

- Swedish statutes and ordinances: stable SFS document IDs on the Riksdag open-data service (`https://data.riksdagen.se/dokument/sfs-YYYY-NNN.html`). The HTML contains the consolidated text and “Ändrad t.o.m. SFS …” marker. For each consolidated statute, the script also reads its linked Regeringskansliet amendment register, records the SFS change numbers, and reports newly listed amendments as candidates. The original SFS 2023:564 amendment is fetched from Svensk författningssamling's official PDF archive.
- Migrationsverket regulations: the official MIGRFS catalog lists in-force rules, archived rules, and RSS subscription. The script matches every pinned MIGRFS number against that catalog, detects new catalog entries, resolves each pinned item to its official PDF, converts PDF text to Markdown with the existing `pdfjs-dist` dependency, and stages changed content for review.
- Migration Court of Appeal: the official Sveriges Domstolar “Sök rättspraxis” API publishes full-text records and attachments. Its OpenAPI contract is at `https://rattspraxis.etjanst.domstol.se/openapi/puh-openapi.yaml`; stable publication IDs and direct record URLs are pinned in the manifest. The four identified case numbers and MIG references in the archive are tracked. Where an archive item is only a summary or a duplicate, it is recorded as such and is not treated as a second judicial source.

The archive also contains English EU acts and CJEU judgments; those belong to the existing EU core and are not duplicated here. The archived Markdown files themselves are not trusted source inputs for future refreshes.

## Use

For ordinary research, use the latest government-published Riksdag, Migrationsverket, or court source and note its displayed date/version and limits. A human-reviewed official link is enough; the sync, capture, conversion, and replay scripts below are optional tools for retaining copies or running a recurring monitor.

Optional retained-copy maintenance, from this directory:

```powershell
node sync.mjs --check
node sync.mjs --sync
node sync.mjs --verify
```

`--check` retrieves and validates official sources, retains each exact response under the project-root `temp/` tree, and updates observation metadata without changing accepted Markdown. `--sync` writes new converted Markdown directly under `documents/`; changed files are staged in project-root `temp/` until reviewed. `--verify` is offline: it replays conversion from each retained response, verifies the raw and Markdown hashes, and compares the replayed text with the accepted file. State and reports are under `temp/eudirective-source-library-0.6.0/sweden/work/`. `--discover` checks the official MIGRFS catalog, Migrationsverket's current legal-framework references, tracked SFS amendment registers, and newly published Migrationsöverdomstolen records since the previous check. It reports candidates and never adds them automatically. Review and add relevant items to `manifest.json` to extend the tracked scope.

After reviewing a staged update against its linked official source, accept it with `node sync.mjs --ack <source-id>` (for example, `sfs:2005:716`). Comparison is against the currently accepted Markdown, so a pending change continues to be reported until it is reviewed and accepted.

The official court API contract is versioned by the publisher. Case records are checked against court code, case number, and decision date before acceptance. If an API record does not match those pinned identifiers, the script stops rather than guessing at a request shape or using a third-party mirror.

Retrieved Markdown is an update candidate. It does not establish legal completeness or trust and must be checked against the official linked source before legal reliance.

## Agency guidance

Optional guidance-copy maintenance: the 12 official agency guidance records in `references/guidance-manifest.json` can be refreshed with `node sync-guidance.mjs sync` and replay-checked with `node sync-guidance.mjs verify`. Review changed text before promoting a retained copy. LIFOS originals remain under the project-root `temp/` tree; none of this is required to use the live official guidance page as a reference.
