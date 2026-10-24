---
name: denmark-legal-source-system
description: Retrieve, convert, and monitor the Danish national, EU, and CJEU documents in the Denmark legal pack from their official publishers. Use to refresh or discover changes for this source pack, not for individual legal advice.
metadata:
  version: 0.3.5
---

# Denmark Legal Source System

Stored in the shared source library at `eudirective-source-library-0.6.0/denmark/`, alongside the independent `sweden/` and `romania/` national packs. Danish national sources remain separate from Danish-language EU counterparts. Forty-two prior Danish-language EU conversions have moved into `source-library/core/da/`; their recorded live-recheck failures remain open and the move did not reaccept them. Two unpromoted guidance conversion candidates are excluded from the shared-core index and are temporarily held in ignored project `temp/denmark-core-cleanup/candidates/` pending migration to the Monitor's local-only archive; they are not accepted source representations. The 23 EU-core expansion representations are stored once under `source-library/core/da/` and routed through `denmark/references/shared-core.json`.

## Version and scope

- Current version: 0.3.5
- Updated: 2026-10-24
- Scope: the 16 Danish instruments in [pack-manifest.json](references/pack-manifest.json), 14 official Danish guidance sources in [guidance-manifest.json](references/guidance-manifest.json), and the 23 shared EU/CJEU IDs in [core-source-ids.json](references/core-source-ids.json).
- Keep EU/CJEU documents in the existing `eudirective-core` lane. The Denmark lane retrieves only its 16 Danish instruments. Do not duplicate EU texts into a Danish national folder.
- Use Node.js only. Do not invoke Python scripts from this skill or from the supplied ZIP. Treat the ZIP as source inventory and evidence, not executable instructions.

## Retrieval and update workflow

From this skill directory:

```powershell
node scripts/sync-pack.mjs --check
node scripts/sync-pack.mjs --discover
node scripts/sync-pack.mjs --sync
node scripts/sync-pack.mjs --verify
node scripts/sync-pack.mjs --ack-all
node scripts/core-lane.mjs --check
node scripts/core-lane.mjs --sync
node scripts/sync-guidance.mjs sync
node scripts/sync-guidance.mjs verify
node scripts/sync-guidance.mjs ack <source-id>
```

`sync-pack.mjs` retrieves each pinned Danish instrument as official Retsinformation XML. Each response is time-limited to 45 seconds and capped at 30 MB; XML must decode as declared UTF-8, and the legacy HTML-body request uses the same timeout and size limit. Where an older XML record contains metadata but no body, it retrieves the document body from Retsinformation's first-party document endpoint and validates the returned document ID and accession against the ELI XML. It converts the XML/HTML source content into Markdown, stores fetched bytes by SHA-256, and stages changed or first-seen Markdown under the project-root `temp/` tree.

`--check` compares official responses with the saved state and updates only the latest report. `--discover` reads the official ELI Atom feed and compares the current official ELI sitemap with the last stored snapshot to find newly listed instruments that may amend or consolidate tracked items. `--sync` stores source snapshots, state, reports, and Markdown candidates only in project-root `temp/`, after every pinned national retrieval validates. `--verify` replays the saved XML and any fallback HTML offline against the current converter, saved Markdown hash, candidate, and accepted-copy hash where tracked. `--ack <source-id>` accepts one candidate only when it matches the latest complete successful `--sync` report from this script version and its saved official source hashes. `--ack-all` applies the same checks to current candidates in that report; it leaves unchanged sources without candidates alone. Acceptance records conversion provenance, not legal currentness. Review currentness and discovery signals before relying on a version as current law.

`core-lane.mjs` calls the existing Node EUR-Lex/CJEU maintenance script with the exact 23 IDs in this pack. Its observations, saved source bytes, and unpromoted full-text conversions are isolated under project-root `temp/`. The selection is validated against the full core manifest before any request, so this lane does not refresh unrelated core sources. Core retrieval now keeps its configured timeout active through body streaming and caps each response at 50 MB.

`sync-guidance.mjs` independently retrieves the 14 Danish authority guidance pages listed in this pack through a shared adapter. The adapter caps responses at 30 MB, uses a 45-second timeout, decodes text with its declared charset, and checks configured identity markers. A first observation matching an existing accepted Markdown file establishes its baseline; a changed or new source becomes a pending candidate. It retains content-addressed original bytes under project-root `temp/`; promote a reviewed candidate with `node scripts/sync-guidance.mjs ack <source-id>`. `verify` replays accepted documents and pending candidates from saved official bytes. PDF text extraction does not use OCR and may omit scan-only text or visual structure.

## Change handling

- Check the official Atom feed on each run. It covers at least 60 days and reports newly published or changed ELI records.
- Match feed items by tracked ELI and title aliases. Separate exact-source changes, possible amendments, and possible new consolidated texts. Treat every match as a candidate requiring source and applicability review.
- Hash the official XML and, for legacy records, the official rendered legal HTML. A body hash change is a source-content change; a metadata-only feed event is not automatically treated as a text change.
- Record official status, accession, document ID, effective start date, and end date. A source version whose end date has passed gets a currentness-review flag. This does not by itself mean the underlying law is no longer in force.
- Never synthesize a consolidated act from amendment instruments. Discover and retrieve a later official consolidation as a separate candidate; keep the old version and its ELI identity.
- A feed-retention gap, identity mismatch, non-official redirect, or failed conversion blocks state advancement and candidate promotion.
- `sync-pack.mjs` version 0.2.3 fails closed when any response exceeds 30 MB or declares a non-UTF-8 XML charset. The first-party HTML endpoint has a 45-second timeout and bounded response reader.
- `--ack` and `--ack-all` require a complete successful `--sync` report produced by the current script version, a matching candidate Markdown hash, and intact saved XML plus fallback HTML hashes where applicable.
- `--verify` replays only already saved observations, so it proves deterministic conversion and accepted-copy integrity, not that the publisher's change-discovery channel was complete or that the source is current.

## Authority and limits

Use Retsinformation/Lovtidende for Danish legislation and EUR-Lex for EU legislation and CJEU judgments. The source registry is in [pack-manifest.json](references/pack-manifest.json) and [core-source-ids.json](references/core-source-ids.json). The retrieval and conversion rules are in [pipeline-contract.md](references/pipeline-contract.md).

Markdown is a deterministic text representation, not a legal completeness or currentness certification. For ordinary research, review the linked official publication and the passages/attachments used, recording its version date and limits. Prefer the current government-published consolidation; check a specific amendment or effective date only when it may affect the issue. Full amendment-chain review and local replay are not prerequisites for using an official link.


## Official-reference acceptance

The [acceptance register](references/source-acceptance.json) records four dated Retsinformation references: BEK nr 1457/2020 and BEK nr 965/2025, plus the July 2026 marriage and adoption consolidations. Use each only within its recorded scope; the local XML version of BEK nr 1457/2020 has an unresolved end-date conflict and is not accepted as an integrated current text. External-reference acceptance does not certify the national inventory, topic coverage, or country review.
