---
name: eudirective-ac-turkiye
description: use when creating, inspecting or validating a turkiye applicant-country module for swedish eu family visa mission operations, local document acquisition and appointment channels under eudirective-core c3 contract 0.2.0. do not use for swedish legal judgments, all countries, individual legal advice or processing private case data; implicit invocation disabled.
---

# eudirective-ac-turkiye

## Version and Status
- Current version: `0.6.0`
- Last updated: `2026-10-14`
- Versioning rule: patch for factual/source clarifications, minor for contract coverage/workflow changes, major for incompatible contracts.

## Version Disclosure
In every visible report announce: `Skill: eudirective-ac-turkiye v0.6.0`.

## Workflow
1. Read `references/module-manifest.json` and `references/module-export.json`. Resolve scoped module notes from `turkiye/module-notes/source-notes/` in the plugin source library; these notes are not full authoritative texts.
2. Resolve module notes and Swedish source records from the bundled eudirective-source-library skill. Check current Swedish mission procedure and Turkish civil-record acquisition claims at the responsible official publishers; state the absence of a bundled Türkiye national-law pack. Do not imply that a compatibility note or installed bundle is live-updated.
3. Run `python scripts/verify_source_notes.py` before consuming module data; it checks the compatibility-note bytes in the source library.
4. Run core's `scripts/module_conformance.py` on the module manifest/export pair using the pinned C3 contract 0.2.0, protocol 0.3.0, model 0.2.0.
5. Confirm relevant country roles, source note scope and case-specific dates. Do not silently turn `candidate_interpretation` into direct statutory text or promote an attack-angle candidate to established violation.
6. Use current official publications for legal or operational claims, record the check date/version, and produce a source-gap/completeness statement. The bundled source corpus is externally maintained and mirrored into the plugin.
7. Refer to an independent human/legal review for exact procedural deadlines, disputed legislation, authority competence and case merits.

## Assumptions and Unknowns
- Module notes are NOT full authoritative text. Their hashes bind compatibility-note bytes only; current law must be checked against a current official publication. The bundled source corpus is externally maintained and versioned.
- This is C3 conformance plus narrowly enrolled, exact-content C10 fictional C6 fixtures (eight listed case contexts only); not a production-ready country source pack or a general C6 input license.
- C6 private input, arbitrary C7 enrolment, external transmission and decision authorisation remain prohibited. Exact C10 fixture enrolment is limited to the core policy-approved fictional case and module hashes.
- The core bundles 47 EU representations; complete current national-law texts are not bundled and require official re-verification.

## Maintenance boundary
Normal execution must not depend on `maintenance/`; read `maintenance/` only when modifying, repairing, auditing, porting, packaging or evaluating this skill. Do not read it during ordinary source verification.

## C10 semantic guard
Fee/reasons attack records which need unrepresented fact values are `unsupported_automation` rather than apparent positive legal findings. This is intentional until the frozen C3 contract is augmented.

## C12 rule extension

Publish the data-only, separately versioned `references/c12-rule-extension.json`; keep the frozen C3 `module-export.json` unchanged. The C12 evaluator must verify module identity, exported module SHA-256, source ownership, and the pilot trust enrolment. The extension contains review predicates only, not executable expressions or established violations. No private-case inference or legal-merits determination is permitted.

## C16 expanded rule sidecar

Use the v0.2.0 `references/c12-rule-extension.json` to inspect source-owned additional review topics. Its `activation` values select synthetic evidence topics, not substantive legal applicability, entitlement or violations. C3 module export and its v0.2.0 contract remain frozen; source notes are not authoritative consolidated text. Never use a C16 result as an approved merits finding.

## C17 source-owned Türkiye operational sidecar

Use `references/c17-remedy-catalog.json` only for Istanbul **Swedish mission contact-channel** review and Turkish civil-record authentication/acquisition. The consulate is a Swedish decision-making authority operating in Türkiye; the Turkish civil records authority does not decide Swedish visa appeals. Swedish appeal and JO remedies are owned by the Sweden module. Catalogue rules are developer-only C7-approved synthetic review triggers, not new Turkish statutory entitlements. The frozen C3 export remains unchanged. No real correspondence, recipient binding or private-data processing is allowed.

## C21 local sidecar-integrity hardening
Run `python scripts/test_sidecar_integrity.py` to check source/authority/rule ownership, canonical C12 export binding, and C17 non-send gates. This is a static local synthetic-data test, not confirmation of the current law, real remedies or competence in an individual case.
