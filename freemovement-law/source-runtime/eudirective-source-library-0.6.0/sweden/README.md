# Sweden national sources

This lane contains Swedish national legislation and Migration Court of Appeal decisions represented in `H:\Downloads\sweden\sweden legal pack.zip`. The Swedish-language EU representations are stored separately in this pack's [`core/`](core/) folder.

## Sources and update signals

- Swedish statutes and ordinances: stable SFS document IDs on the Riksdag open-data service (`https://data.riksdagen.se/dokument/sfs-YYYY-NNN.html`). The HTML contains the consolidated text and “Ändrad t.o.m. SFS …” marker. For each consolidated statute, the script also reads its linked Regeringskansliet amendment register, records the SFS change numbers, and reports newly listed amendments as candidates. The original SFS 2023:564 amendment is fetched from Svensk författningssamling's official PDF archive.
- Migrationsverket regulations: the official MIGRFS catalog lists in-force rules, archived rules, and RSS subscription. The script matches every pinned MIGRFS number against that catalog, detects new catalog entries, resolves each pinned item to its official PDF, converts PDF text to Markdown with the existing `pdfjs-dist` dependency, and stages changed content for review.
- Migration Court of Appeal: the official Sveriges Domstolar “Sök rättspraxis” API publishes full-text records and attachments. Its OpenAPI contract is at `https://rattspraxis.etjanst.domstol.se/openapi/puh-openapi.yaml`; stable publication IDs and direct record URLs are pinned in the manifest. The four identified case numbers and MIG references in the archive are tracked. Where an archive item is only a summary or a duplicate, it is recorded as such and is not treated as a second judicial source.

The archive also contains English EU acts and CJEU judgments; those belong to the existing EU core and are not duplicated here. The archived Markdown files themselves are not trusted source inputs for future refreshes.

## Use

From this directory run:

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

The 12 official agency guidance records in `references/guidance-manifest.json` are refreshed independently with `node sync-guidance.mjs sync` and replay-checked with `node sync-guidance.mjs verify`. Changed text is staged for review and promoted with `node sync-guidance.mjs ack <source-id>`. Content-addressed original PDF and HTML responses are stored physically under the project-root `temp/`; converted text is in `documents/guidance/`. This includes the current LIFOS RS/030/2021 version 5 and RS/008/2022 version 6 PDFs. Their landing pages and PDF attachments are both saved. LIFOS TLS verification uses the official ISRG Root YR certificate pinned in `references/certs/isrg-root-yr.pem`, sourced from [Let's Encrypt](https://letsencrypt.org/certs/gen-y/root-yr.pem), fingerprint SHA-256 `E5:7B:7E:6F:15:0C:41:91:02:E8:D5:C0:55:72:9F:F9:67:B9:D1:A8:29:BF:00:CE:C8:9C:A6:04:EB:F4:A8:6F`.
