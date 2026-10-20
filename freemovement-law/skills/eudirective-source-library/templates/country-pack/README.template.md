# <Jurisdiction> national source pack

**Status (<YYYY-MM-DD>):** <inventory and retrieval state>; <accepted source count> accepted sources.

This pack covers <defined legal and administrative scope>. It does not claim exhaustive national-law coverage.

- EU-language core (optional; remove if this pack has no localized core files): [core/README.md](core/README.md)
- National source inventory: [candidate manifest](references/candidate-manifest.json)
- Optional local-copy and monitoring rules: [source rules](references/source-rules.json)
- Human-readable source list: [source list](references/source-list.md)
- Optional local-copy or updater evidence: [capture ledger](references/capture-ledger.json) <!-- remove when not used -->
- Shared EU-language material, when applicable: [shared core references](references/shared-core.json)
- Sustainability review: [assessment](references/sustainability-assessment.md)
- Pack instructions: [SKILL.md](SKILL.md) <!-- remove if no operational skill exists -->

The accepted-source count describes locally held artifacts only. It does not count or disqualify human-reviewed official references. For ordinary research, an official source link reviewed by a person may be enough and may support topic evidence; a stored capture or automated updater is a separate choice. Record publisher, language, version/cutoff when shown, scope, reviewed passage, and material limitations. A source need not have a custom retrieval or conversion rule to be used as a reference.
Across legislation, decisions, guidance, forms, and procedures, prefer the latest usable government-published version. For legal text, accept a government-published consolidation as a usable official reference when the publisher, instrument, and consolidation status are clear and no concrete warning undermines reliance. If trust is unclear, offer the official legal-text website/service as a whole to the user for human review, with its authority/versioning information and relevant text. Do not require Gazette-by-Gazette reconstruction or a full-site crawl by default. If no usable consolidation is available, use the closest government-published version and state its date, status, language, and limits; use individual Gazette acts only to resolve a material gap. See the [source edition and review policy](../../references/legal-text-edition-policy.md).
When an EU-language corpus is shared across jurisdictions, reference each source ID and either its canonical repository path or its official publisher URL if no local copy is held. Do not copy shared files or use filesystem symlinks, and do not describe an external link as a stored source.
