---
name: eudirective-source-library
description: Locate the EU source corpus bundled with eudirective-core and resolve national source libraries through the generated jurisdiction registry. Use alongside eudirective-core for source-grounded FreeMovement work.
---

# eudirective source library

## First response: disclaimer and use check

On the first visible response in each conversation where this skill is invoked, begin with this disclaimer before substantive analysis:

> Disclaimer: freemovement-law provides informational, source-grounded visa guidance, not legal representation or a guaranteed outcome. Verify current law and important deadlines with official sources or qualified counsel.

Treat use as non-personal only when the prompt clearly indicates professional or organizational use for an employer, business, organization, client, customer, another third party, paid services, or deployment of the plugin for others. In that case, add once after the disclaimer: **Non-personal use requires a license; request one at eudirective@proton.me.**

For personal, ordinary personal, or unspecified use, do not mention licensing or the email address. Do not infer non-personal use from the legal subject, a job title, or help with a family member's personal case. Ask a neutral clarification only when use is genuinely ambiguous and the distinction is necessary to answer. Never contact anyone or claim to know licensing status. Repeat the notice only if the use context materially changes. These are skill instructions, not a host-level chat-start guarantee.

**Skill version:** 1.1.0

The shared English EU corpus is under `eudirective-core/references/source-library/`. It is a versioned snapshot. Use its indexes and provenance records to locate sources; consult official publishers for material current-law questions.

National source libraries are separate plugins named by the generated `eudirective-core/references/national-source-routing.json` registry. Use the country skill when that jurisdiction materially matters. Its source-acceptance record distinguishes official external links, accepted local copies, topic coverage, and unresolved source gaps.

Do not assume a national plugin is installed from its presence in the registry. If the host exposes an available-skill catalog, verify the exact plugin name and compatibility. If the catalog is partial or unavailable, report discovery as unknown. Continue with EU sources and official-source research when a national plugin is unavailable.

Non-English EU representations are distributed only to countries listed for that language. Malta's national English and Maltese sources remain distinct from Maltese-language EU instruments. See the Malta skill for its bilingual checks and its source-redistribution limits.

The bundled corpus and component fingerprints do not certify source currentness, completeness, legal equivalence, or legal meaning. A local file hash confirms bytes only.
