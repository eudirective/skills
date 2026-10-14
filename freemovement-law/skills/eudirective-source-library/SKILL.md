---
name: eudirective-source-library
description: Retrieve, verify, convert, and refresh the project's registered EU and national legal source packs through local source-library tools. Use when the user asks to update, check, convert, or inspect this corpus.
---

# Local legal source library

Skill version: eudirective-source-library v0.3.0. Include this name and version near the top of any visible response or report produced while using this skill.

Use `list_source_packs` first to identify the registered pack and its supported actions. Use `run_source_pack_action` only with a listed `pack_id` and supported action. The bridge accepts no arbitrary URL, command, file path, or manifest input; each operation is tied to bundled official-source scripts and pack manifests.

On first source action, the bridge copies the bundled retrieval runtime into the installation's stable `data/` directory and installs the pinned Node dependencies from the included lockfile if they are missing. This requires Node.js 20 or later, npm, and network access for dependency setup and official-source retrieval. Retrieved Markdown, raw snapshots, and update state are stored under that installation's `data/` directory, never in the user project or plugin package code.

## Retrieval and updates

- Use `check` or `sync` to retrieve from registered official publishers. A `sync` may write a pending candidate or pack-specific state; inspect the returned report before acknowledging it.
- Use `verify` for the pack's local hash and conversion replay checks.
- Use `discover` only for packs that advertise that action; it checks for new records through that pack's official discovery endpoint.
- Use `convert` only for `eu-core`, after a successful check, and report conversion counts and errors.
- Use `ack` only when the user explicitly approves accepting the identified pending source candidate. Acknowledgement takes a registered `source_id` and does not accept an entire pack by default.
- Use the handbook `inventory` action to inspect the 2020 multilingual Visa Code handbook register. Do not merge its older wording into current law.
- On a clean installation, run the English `eu-core` check and conversion before retrieving EU national-language mirrors; those mirrors use the local English core inventory.

## Scope and reporting

This integration runs locally in a compatible desktop host and is self-contained: it does not require the installer to have this development project or a fixed user path. Each plugin installation has its own data directory and update state. It covers only the pack IDs returned by `list_source_packs`: EU core, its registered additions and language mirrors, EU guidance, the Swedish recommendation representation, Denmark, Sweden, Hungary, Romania, country guidance, and the 2020 handbook language reference. Do not crawl unrelated sources or add packs through these tools.

This is the canonical retrieval and update interface for source content. Other eudirective skills must use these tools to check or retrieve current official text. Bundled compatibility snapshots and country module notes are retained only where deterministic synthetic integrity checks need stable bytes; they are not the current corpus and do not replace retrieved material in the installation's `data/` directory. Country module notes are scoped summaries, never full authoritative legal text.

Report the pack ID, action, result, source IDs when returned, official-source errors, and pending review state. Distinguish a failed publisher request from a missing local file or a conversion/hash failure. Do not claim a pack is fully current merely because an operation exited successfully; use its report counts and a verify action where available.
