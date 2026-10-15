---
name: eudirective-source-library
description: Inspect the externally maintained EU and national legal-source library bundled with this plugin. Use to locate source records, official publisher URLs, recorded versions/dates, and coverage. Current-law checks must use official publishers.
---

# Bundled EU source library

Skill version: eudirective-source-library v1.0.1. Include this name and version near the top of any visible response or report produced while using this skill.

This skill's source library is mirrored from eudirective/public-data into this plugin package by the repository workflow. Its manifests, source files, and module notes sit beside this SKILL.md. Use those bundled files to identify the relevant source, its official publisher URL, recorded version/date, and coverage. The installed package is a snapshot and does not update itself.

When a legal claim depends on current law, guidance, or case law, check the responsible official publisher directly when browsing is available. Record the publisher, URL, date/version checked, and any source gap. If a live check is not possible, state that currentness was not verified and distinguish the bundled snapshot from current law.

Do not treat the eudirective-core skill's historical compatibility test fixture or country module notes as current authoritative texts. The README in this directory documents the upstream retrieval library and maintainer workflows; its CLI commands are repository maintenance instructions, not plugin MCP tools. This plugin does not expose per-install source-pack retrieval or synchronization tools.
## First-invocation GitHub version parity

Before substantive work, on the first FreeMovement skill invocation in this conversation, read `eudirective-core/references/session-version-check.md` and perform its read-only once-per-conversation version comparison. Report only mismatches or unsuccessful checks, never silent success. Continue the requested work regardless of the result. Skip additional checks in the same conversation unless expressly requested; if this skill is not the core, load the core's referenced instructions first. This checks package versions only, not legal-source validity.

