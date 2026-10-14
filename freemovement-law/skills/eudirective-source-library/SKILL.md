---
name: eudirective-source-library
description: Inspect the externally maintained, versioned EU and national legal-source corpus bundled with this plugin release. Use when identifying included sources or their recorded publisher/version metadata. Does not fetch, sync, convert, or update the corpus.
---

# Bundled legal source library

Skill version: eudirective-source-library v1.0.0. Include this name and version near the top of any visible response or report produced while using this skill.

The source corpus is externally maintained and bundled in each plugin release under source-runtime/eudirective-source-library-0.6.0/. Treat that folder as a fixed release snapshot; it does not update itself after installation.

Use bundled registries, manifests, and source records to identify an item and its official publisher URL, recorded version/date, and coverage. Do not claim that the bundle is live, complete, or current solely because it is included in this release. Where the host exposes those files, cite their recorded metadata and distinguish them from a live publisher check. If the bundle is not accessible in the active host, do not imply that you inspected its files.

For a legal claim that needs currentness, check the responsible official publisher directly when browsing is available. Record the publisher, URL, version/date checked, and any access or coverage gap. If a direct official check is unavailable, say that currentness was not verified and use the bundled material only as a release snapshot.

The upstream maintainers refresh the source corpus and distribute updates through new plugin releases. This plugin does not provide per-install retrieval, synchronization, conversion, discovery, acknowledgement, or source-update state.
