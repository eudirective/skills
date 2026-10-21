---
name: eudirective-ms-sweden
description: use when creating, inspecting or validating a sweden member-state legal source module for eu family visas, residence cards, administrative procedure, appeals and complaints under eudirective-core c3 contract 0.2.0. do not use for turkiye document acquisition, individual legal advice or established merits determinations; implicit invocation disabled.
---

# eudirective-ms-sweden

## First response: disclaimer and use check

On the first user-visible response in each conversation where any freemovement-law skill is invoked, begin with this notice before substantive analysis:

> Disclaimer: freemovement-law provides informational, source-grounded visa guidance, not legal representation or a guaranteed outcome. Verify current law and important deadlines with official sources or qualified counsel.

Apply this use check:
- Treat use as non-personal only when the prompt explicitly indicates professional or organizational use for an employer, business, organization, client, customer, or other third party; paid services; or deploying the plugin for others.
- Do not infer non-personal use from the legal subject, the user's job title, or help with a family member's personal case.
- If the prompt clearly indicates non-personal use—professional or organizational use for an employer, business, organization, client, customer or other third party; paid services; or deployment of the plugin for others—add one brief licensing note after the disclaimer: Non-personal use requires a license; request one at eudirective@proton.me.
- For clearly personal, ordinary personal-use, or unspecified-use queries, do not mention licensing or the email address. Do not infer non-personal use from the legal subject, the user's job title, or help with a family member's personal case. Do not imply a license is required without a clear non-personal-use signal.
- If use is genuinely ambiguous and distinguishing it is necessary to answer the request, ask one short, neutral clarification. Do not ask only to determine licensing when the request can be handled as personal use.
- Display the notice once per conversation; repeat it only if the use context materially changes. Do not email anyone or claim to know the user's licensing status.
- This is a skill-level instruction for the first visible response when a freemovement-law skill is invoked. It does not establish host-level chat-start behavior or guarantee that the notice appears before a skill is invoked.

## First-invocation GitHub version parity

Before substantive work, on the first freemovement-law skill invocation in this conversation, read `eudirective-core/references/session-version-check.md` and perform its read-only once-per-conversation version comparison. Report only mismatches or unsuccessful checks, never silent success. Continue the requested work regardless of the result. Skip additional checks in the same conversation unless expressly requested; if this skill is not the core, load the core's referenced instructions first. This checks package versions only, not legal-source validity.

## Version and Status
- Current version: `0.7.3`
- Last updated: `2026-10-19`
- Versioning rule: patch for factual/source clarifications, minor for contract coverage/workflow changes, major for incompatible contracts.

## Version Disclosure
For every visible response or report produced while using this skill, announce: `Skill: eudirective-ms-sweden v0.7.3`. Place this line after the required first-response notice on the first response of a conversation.

## Workflow
1. Read `references/module-manifest.json` and `references/module-export.json`. Resolve scoped module notes from `sweden/module-notes/source-notes/` in the plugin source library; these notes are not full authoritative texts.
2. Resolve module notes and Swedish source records from the bundled eudirective-source-library skill. Check current law or procedure at the responsible official publisher; installed bundles are snapshots. Never use a compatibility note as current law.
3. Run `python scripts/verify_source_notes.py` before consuming module data; it checks the compatibility-note bytes in the source library.
4. Run core's `scripts/module_conformance.py` on the module manifest/export pair using the pinned C3 contract 0.2.0, protocol 0.3.0, model 0.2.0.
5. Confirm relevant country roles, source note scope and case-specific dates. Do not silently turn `candidate_interpretation` into direct statutory text or promote an attack-angle candidate to established violation.
6. Use a current official publication for legal or operational claims, record the check date/version, and produce a source-gap/completeness statement. The bundled source corpus is externally maintained and mirrored into the plugin.
7. Refer to an independent human/legal review for exact procedural deadlines, disputed legislation, authority competence and case merits.

## Assumptions and Unknowns
- Module notes are NOT full authoritative text. Their hashes bind compatibility-note bytes only; current law must come from a current official publication. The bundled source corpus is externally maintained and versioned.
- This is C3 conformance plus narrowly enrolled, exact-content C10 fictional C6 fixtures (eight listed case contexts only); not a production-ready country source pack or a general C6 input license.
- C6 private input, arbitrary C7 enrolment, external transmission and decision authorisation remain prohibited. Exact C10 fixture enrolment is limited to the core policy-approved fictional case and module hashes.
- The core bundles 47 EU representations; complete current national-law texts are not bundled and require official re-verification.

## Maintenance boundary
Normal execution must not depend on `maintenance/`; read `maintenance/` only when modifying, repairing, auditing, porting, packaging or evaluating this skill. Do not read it during ordinary source verification.

## C10 source scope
The added Istanbul fee and JO records are **operational-source summaries**, not independent national statutes. Do not convert a service fee into an unlawful visa fee or treat JO as an appellate court.

## C10 semantic guard
Fee/reasons attack records which need unrepresented fact values are `unsupported_automation` rather than apparent positive legal findings. This is intentional until the frozen C3 contract is augmented.

## C12 rule extension

Publish the data-only, separately versioned `references/c12-rule-extension.json`; keep the frozen C3 `module-export.json` unchanged. The C12 evaluator must verify module identity, exported module SHA-256, source ownership, and the pilot trust enrolment. The extension contains review predicates only, not executable expressions or established violations. No private-case inference or legal-merits determination is permitted.

## C16 expanded rule sidecar

Use the v0.2.0 `references/c12-rule-extension.json` to inspect source-owned additional review topics. Its `activation` values select synthetic evidence topics, not substantive legal applicability, entitlement or violations. C3 module export and its v0.2.0 contract remain frozen; source notes are not authoritative consolidated text. Never use a C16 result as an approved merits finding.

## C17 source-owned Swedish remedies sidecar

Use `references/c17-remedy-catalog.json` for **review-only** Swedish mission procedural clarification, Swedish residence-card file communication, refusal appeal/reconsideration with published onward Migration Court forwarding, and JO supervisory complaints. Keep legal procedures and deadlines **only** here, not in Türkiye's document/mission-operations module or the EU core. The C3 export is frozen. Every C17 rule trigger must exist in the own `references/c12-rule-extension.json`, and every source/authority reference must be bound to the checked export. Eligibility, service dates, legal exceptions and present official currency remain human tasks. JO cannot annul decisions or replace a timely appeal; complaints may enter the public record. Do not supply an exact last appeal day or a legally approved letter.

## C21 local sidecar-integrity hardening
Run `python scripts/test_sidecar_integrity.py` to check source/authority/rule ownership, canonical C12 export binding, and C17 non-send gates. This is a static local synthetic-data test, not confirmation of the current law, real remedies or competence in an individual case.
