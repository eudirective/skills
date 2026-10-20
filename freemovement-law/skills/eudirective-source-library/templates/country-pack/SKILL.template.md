---
name: <jurisdiction>-legal-source-system
description: Maintain <jurisdiction> national source candidates and reviewed documents for <defined scope>.
metadata:
  version: 0.1.0
  short-description: <Jurisdiction> national source pack
---

# <Jurisdiction> legal source system

Use this workflow only for the scope recorded in `references/source-list.md`. The machine-readable source inventory is `references/candidate-manifest.json`; per-source retrieval and conversion rules are in `references/source-rules.json`.

## Retrieval and conversion

- Official retrieval entry point: <publisher, catalogue, API, or documented manual route>
- Identity and version checks: <stable identifiers, currentness rules, and checks>
- Conversion rules: <format-specific extraction and validation>
- Failure handling and change detection: <timeouts, access blocks, drift, and review staging>
- Reuse terms and limits: <recorded permission or unresolved status>

## Review before use

Verify source authority, identity, language, current version, legal effect, completeness, extraction quality, scope, and reuse conditions. A successful retrieval or conversion does not establish legal correctness or trust.
