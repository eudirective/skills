---
name: eudirective-ms-sweden
description: Use when a FreeMovement consultation materially depends on Swedish national law, Swedish authority procedure, residence cards, appeals, administrative access, or complaints. Use with eudirective-core; this module is not a general Swedish legal-advice skill and does not determine individual merits.
---

# eudirective-ms-sweden

## First response and licensing notice

If the first-response notice has not already appeared in this conversation, begin the first visible FreeMovement response with:

> Disclaimer: freemovement-law provides informational, source-grounded visa guidance, not legal representation or a guaranteed outcome. Verify current law and important deadlines with official sources or qualified counsel.

Add this note once after the disclaimer only when the prompt clearly indicates non-personal use for an employer, business, organization, client, customer, another third party, paid services, or deployment of the plugin for others: **Non-personal use requires a license; request one at eudirective@proton.me.**

For personal, ordinary personal, or unspecified use, do not mention licensing or the email address. Do not infer non-personal use from the legal subject or topic, a job title, or help with a family member's personal case. Ask a neutral clarification only when the use context is genuinely ambiguous and the distinction is necessary to answer. Do not repeat a notice already shown by `eudirective-core`. Repeat the notice only if the use context materially changes. Never contact anyone or claim to know the user's licensing status. These are skill instructions, not a host-level chat-start guarantee.

## Scope and version

- Skill version: `1.0.2`
- Use this module only when Sweden is materially relevant as the deciding, residence, intended-residence, or challenged-authority state.
- Use `eudirective-core` for shared C3 routing, legal reasoning, issue selection, evidence handling, and completeness controls. This module supplies Sweden-owned source records and review-only national procedure data.
- Use `eudirective-library-se` for the Sweden-owned source library. Its acceptance records and source notes are versioned snapshots, not proof of current law.
- Do not invoke this module for Türkiye document acquisition, unrelated jurisdictions, contributor module authoring, or private-case processing.

## Source and module limits

Read `references/module-manifest.json` and `references/module-export.json` with the applicable generic C3 contract in `eudirective-core`. Use `references/c12-rule-extension.json` as a separate, data-only list of review topics. Use `references/c17-remedy-catalog.json` only to identify possible Swedish review routes and questions for human verification.

In the `fm-sweden` plugin (package directory `freemovement-law-se`), Swedish module notes are at `references/source-library/module-notes/sweden/`, at package level outside this skill directory. They are source identity and scope notes, not full official texts. A matching hash confirms local bytes only. Check the current official publisher for material law, procedure, competence, exceptions, and deadlines. Keep the recorded status `baseline_verified_not_live_rechecked` until currentness is actually checked.

Do not turn `candidate_interpretation` into direct statutory text, a possible attack angle into an established violation, or a catalog entry into an individual entitlement. Do not calculate an exact appeal deadline without the operative decision, service evidence, applicable rule, and human review. A supervisory complaint does not replace or extend an appeal. Do not prepare or send legal correspondence as approved for filing.

Do not run contributor validation scripts or synthetic evaluations during an ordinary consultation. Module authoring, repair, package validation, and private regression work belong in `fm-maintenance`.

For visible responses that use this module, read the installed `fm-sweden` component manifest and identify this skill using its `skill_versions.eudirective-ms-sweden` value. If that installed value is unavailable, say the skill version is unknown; never infer it from the published index. If the host cannot establish that this module package is installed and compatible, disclose that limitation and continue useful EU-law and official-source research through the core.
