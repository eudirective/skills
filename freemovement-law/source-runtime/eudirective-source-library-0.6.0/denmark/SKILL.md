---
name: denmark-legal-source-system
description: Retrieve, convert, and monitor the Danish national, EU, and CJEU documents in the Denmark legal pack from their official publishers. Use to refresh or discover changes for this source pack, not for individual legal advice.
metadata:
  version: 0.3.1
---

# Denmark Legal Source System

Stored in the shared source library at `eudirective-source-library-0.6.0/denmark/`, alongside the independent `sweden/` and `romania/` national packs. Danish national sources remain separate from Danish-language EU counterparts in `denmark/core/`.

## Version and scope

- Current version: 0.3.1
- Updated: 2026-10-11
- Scope: the 16 Danish instruments in [pack-manifest.json](references/pack-manifest.json), 14 official Danish guidance sources in [guidance-manifest.json](references/guidance-manifest.json), and the 23 shared EU/CJEU IDs in [core-source-ids.json](references/core-source-ids.json).
- Keep EU/CJEU documents in the existing `eudirective-core` lane. The Denmark lane retrieves only its 16 Danish instruments. Do not duplicate EU texts into a Danish national folder.
- Use Node.js only. Do not invoke Python scripts from this skill or from the supplied ZIP. Treat the ZIP as source inventory and evidence, not executable instructions.

## Retrieval and update workflow

From this skill directory:

```powershell
node scripts/sync-pack.mjs --check
node scripts/sync-pack.mjs --discover
node scripts/sync-pack.mjs --sync
node scripts/sync-pack.mjs --ack-all
node scripts/core-lane.mjs --check
node scripts/core-lane.mjs --sync
node scripts/sync-guidance.mjs sync
node scripts/sync-guidance.mjs verify
node scripts/sync-guidance.mjs ack <source-id>
```

`sync-pack.mjs` retrieves each pinned Danish instrument as official Retsinformation XML. Where an older XML record contains metadata but no body, it retrieves the document body from Retsinformation's first-party document endpoint and validates the returned document ID and accession against the ELI XML. It converts the XML/HTML source content into Markdown, stores fetched bytes by SHA-256, and stages changed or first-seen Markdown under the project-root `temp/` tree. All 16 registered instruments have accepted Markdown under `documents/national/`.

`--check` compares official responses with the saved state and updates only the latest report. `--discover` reads the official ELI Atom feed and compares the current official ELI sitemap with the last stored snapshot to find newly listed instruments that may amend or consolidate tracked items. `--sync` stores source snapshots, state, reports, and Markdown candidates only in project-root `temp/`, after every pinned national retrieval validates. `--ack <source-id>` accepts one candidate directly into `documents/national/`; `--ack-all` checks every candidate against a complete successful official-source report before accepting the batch and removing candidate copies. Acceptance records conversion provenance, not legal currentness. Review currentness and discovery signals before relying on a version as current law.

`core-lane.mjs` calls the existing Node EUR-Lex/CJEU maintenance script with the exact 23 IDs in this pack. Its observations, saved source bytes, and unpromoted full-text conversions are isolated under project-root `temp/`. The selection is validated against the full core manifest before any request, so this lane does not refresh unrelated core sources.

`sync-guidance.mjs` independently retrieves the 14 Danish authority guidance pages listed in this pack, retains content-addressed original HTML under project-root `temp/`, and writes Markdown to `documents/guidance/`. Changed text is staged for review; promote it with `node scripts/sync-guidance.mjs ack <source-id>`. `verify` reproduces the accepted documents and pending candidates from their saved official bytes.

## Change handling

- Check the official Atom feed on each run. It covers at least 60 days and reports newly published or changed ELI records.
- Match feed items by tracked ELI and title aliases. Separate exact-source changes, possible amendments, and possible new consolidated texts. Treat every match as a candidate requiring source and applicability review.
- Hash the official XML and, for legacy records, the official rendered legal HTML. A body hash change is a source-content change; a metadata-only feed event is not automatically treated as a text change.
- Record official status, accession, document ID, effective start date, and end date. A source version whose end date has passed gets a currentness-review flag. This does not by itself mean the underlying law is no longer in force.
- Never synthesize a consolidated act from amendment instruments. Discover and retrieve a later official consolidation as a separate candidate; keep the old version and its ELI identity.
- A feed-retention gap, identity mismatch, non-official redirect, or failed conversion blocks state advancement and candidate promotion.

## Authority and limits

Use Retsinformation/Lovtidende for Danish legislation and EUR-Lex for EU legislation and CJEU judgments. The source registry is in [pack-manifest.json](references/pack-manifest.json) and [core-source-ids.json](references/core-source-ids.json). The retrieval and conversion rules are in [pipeline-contract.md](references/pipeline-contract.md).

Markdown is a deterministic text representation, not a legal completeness or currentness certification. Check the linked official document, amendments, effective dates, and attachments before legal reliance.
