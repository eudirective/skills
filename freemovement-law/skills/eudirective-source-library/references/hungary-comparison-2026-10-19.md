# Hungary pack comparison

Status date: 19 October 2026; Hungary count/source update: 21 October 2026

Reference pack: [`source-library/hungary/`](../hungary/README.md)

## Pack shape

Hungary provides the most complete implementation pattern among the country packs reviewed here. Its pack has a README and use instructions, a manifest and source list, a sustainability assessment, a publisher-aware sync/discovery workflow, content-addressed raw snapshots under the project-root `temp/` directory, conversion outputs, offline replay verification, and explicit review-state gates. The runner separates checking, discovery, syncing, verification, and offline reconversion. Its HTML and PDF adapters also use different extraction and identity checks.

The new country dossiers provide dated candidate manifests and source lists, but most do not yet have implemented acquisition, conversion, change-detection, and replay rules. A manifest entry or working URL alone is therefore not equivalent to a Hungary active source record.

## What can be reused

- Keep source inventory, acquisition state, converted output, and acceptance state separate.
- Pin the official source identifier and expected title/citation, not only a URL or filename.
- Preserve raw response bytes by hash, record retrieval metadata, and support deterministic offline conversion replay.
- Keep catalogue discovery distinct from retrieval of registered texts; new discovery hits remain candidates until reviewed.
- Fail closed on wrong content types, redirects outside publisher hosts, missing identity markers, partial bodies, and converter errors.
- Make publisher-specific rules independently selectable, paced, and reportable so a blocked source does not trigger unrelated requests.

## What should not be copied as a retrieval rule

The [Hungary sustainability assessment](../hungary/references/sustainability-assessment.md) rates automated NJT retrieval/storage **unsustainable under the recorded terms**. Use NJT's government-published consolidated page as a human-reviewed source reference, record its displayed version date, and do not copy or poll the protected portal database. A specific Gazette amendment is supplemental only when it resolves a material post-cutoff or commencement issue; a manual Gazette-by-Gazette workflow is not required.

The same assessment rates the OIF lane **fragile** because source-specific identity checks are missing for some pages, PDF text quality is not reviewed, and a run can make many requests without timeouts, backoff, or per-source host restrictions. NAIH/AJBH access terms and some court coverage also remain unresolved. These findings mean the Hungary pack is a useful structural comparator, not a sustainability approval for its existing automation.

## Inventory count reconciliation

The 21 October review reconciles the former count difference. The manifest lists 59 legal entries (58 historical NJT records plus link-only Act I/2010) and 47 OIF/NAIH/AJBH entries. Three AJBH PDFs and three catalogue pages are excluded from retrieval, leaving 41 online updater records. The 99 saved state rows represent 58 historical NJT review captures plus those 41 online records. This is a count reconciliation only; no local copy or topic is accepted. See the updated [Hungary README](../hungary/README.md), [source-acceptance register](../hungary/references/source-acceptance.json), and [coverage register](../hungary/references/coverage-register.json).

## Comparison outcome for this expansion

The 27 imported country inventories contain 1,203 candidate entries in the reconciled 19 October ledger. They span law, guidance, forms, decisions and oversight sources, as well as discovery services; this is not a 1,203-text download list. Candidate records without a sustainable, verified retrieval route remain explicitly pending or discovery-only. Spain's BOE lane and Finland's partial Finlex lane currently produce unaccepted review candidates with retained source hashes and offline conversion checks. Finland also demonstrates that a successful API request is insufficient when its own version metadata conflicts; the 808/2019 conversion remains unaccepted until that conflict is resolved.

Country work should follow the Hungary pack's provenance, identity, state, and replay structure while rating and implementing each publisher lane on its own terms. Do not adopt NJT automated acquisition without explicit publisher permission.


## Live GitHub comparison — 19 October 2026

The public [`main` branch](https://github.com/eudirective/public-data/commit/d69d33bdb08f69e784d8a9d383d779024c38be6d) resolves to commit `d69d33bdb08f69e784d8a9d383d779024c38be6d`, which is also the local checkout `HEAD`. A recursive comparison of the live Hungary tree and the local `HEAD` found the same 168 files with identical Git blob hashes, no missing or extra paths, and no truncated API response. This supersedes the earlier six-file spot check and confirms the complete comparator tree is current at the audit commit.

The Swiss implementation now combines a Fedlex RDF-to-file-store rule with bounded direct-page capture: 27 responses were saved from 28 configured records and 26 review conversions were produced. HTML outputs and Fedlex metadata pass offline replay/integrity verification; one SEM PDF conversion came from the connected Acrobat service and is hash-checked but not locally replayable. Switzerland still has only `sync` and `verify`, with discovery, general current-version resolution and repeatable PDF conversion outstanding. Hungary's NJT acquisition restrictions remain; its former state-count discrepancy is reconciled by separating link-only AJBH records from the online updater set.
