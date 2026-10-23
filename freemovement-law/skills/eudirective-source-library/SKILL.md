---
name: eudirective-source-library
description: Inspect the externally maintained EU and national legal-source library bundled with this plugin. Use to locate official source records, versions, and coverage. Prefer government-published consolidations; otherwise use the closest government-published version and state its limits.
---

# Bundled EU source library

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

Skill version: eudirective-source-library v1.0.13. After the required first-response notice, include this name and version near the top of any visible response or report produced while using this skill.

Last updated: 2026-10-24.

This skill's source library is mirrored from eudirective/public-data into this plugin package by the repository workflow. Its manifests, source files, and module notes sit beside this SKILL.md. Use those bundled files to identify the relevant source, its official publisher URL, recorded version/date, and coverage. The installed package is a snapshot and does not update itself.

When a claim depends on current law, decisions, guidance, forms, mission instructions, procedures, remedies, complaints, or oversight, check the responsible official publisher directly when browsing is available. Record the publisher, URL, date/version checked, and any source gap. If a live check is not possible, state that currentness was not verified and distinguish the bundled snapshot from current law.

## Selecting and reviewing source versions

For all source classes, use the responsible official publisher. For national legislation, prefer a usable government-published consolidation; for EU legislation, prefer the responsible EU publisher's consolidation. Accept a government consolidation as a usable official reference when the publisher's role, instrument identity, and consolidation status are clear and no concrete warning undermines reliance; these are practical judgment cues, not a new technical checklist. If trust is unclear, offer the government legal-text website/service as a whole to the user for human review, including its authority/versioning information, the relevant text, and visible caveats. Do not reject it silently or require a full-site crawl. If no usable consolidation exists, use the closest government-published or official-service version and record its language, displayed date/cutoff, and limits. A human-reviewed official page or document link is enough for ordinary research; check only the identity, version, content, and caveats relevant to the question. Do not reconstruct Gazette amendment chains by default; consult a specific act only for a material question the chosen text leaves open. Captures, conversions, hashes, OCR, API clients, replay, and scheduled updates are optional unless a retained copy, reproducibility, or recurring monitoring is needed and permitted. Do not bypass access controls.

Review the passages and attachments relevant to the question. Compare more broadly only when a lossy conversion creates a material risk or the whole converted text is relied upon. A human-reviewed link can support topic evidence without a local copy, custom retrieval/conversion rule, source-library registration, or API. Keep official-reference usability, local-copy acceptance, topic coverage, and country review distinct; see the bundled [source selection and review policy](references/legal-text-edition-policy.md).

Country-pack `next_step` fields and maintenance commands may describe local-copy or monitoring work. They do not gate use of a human-reviewed official link unless they identify a specific content or currentness gap that matters to the question.

Do not treat the eudirective-core skill's historical compatibility test fixture or country module notes as current authoritative texts. The README in this directory documents the upstream retrieval library and maintainer workflows; its CLI commands are repository maintenance instructions, not plugin MCP tools. This plugin does not expose per-install source-pack retrieval or synchronization tools.
## First-invocation GitHub version parity

Before substantive work, on the first freemovement-law skill invocation in this conversation, read `eudirective-core/references/session-version-check.md` and perform its read-only once-per-conversation version comparison. Report only mismatches or unsuccessful checks, never silent success. Continue the requested work regardless of the result. Skip additional checks in the same conversation unless expressly requested; if this skill is not the core, load the core's referenced instructions first. This checks package versions only, not legal-source validity.

