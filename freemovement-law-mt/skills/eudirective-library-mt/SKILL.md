---
name: eudirective-library-mt
description: Use when FreeMovement consultation requires Malta national sources. Apply the Malta bilingual verification profile for material Maltese national law.
---

# Malta national source library

Use this skill alongside `eudirective-core`; it supplies Malta-owned sources and language checks, not a separate legal-reasoning engine.

- Determine whether a source is Maltese national law, a judgment, official guidance, or an EU instrument before applying language rules.
- For national statutes, seek the official English and Maltese versions under the same ELI identity. Preserve both official representations and align their editions before comparing relevant provisions.
- Apply Maltese statutory-text precedence only where Article 74 of the Constitution governs, after checking for a specific statutory exception. Do not apply that rule automatically to judgments, proceedings, or EU law.
- Identify the language actually used in judicial records and check the applicable court-language provisions separately.
- If a counterpart, edition, exception, or comparison is unverified, name the exact gap and its effect while continuing useful research.
- Follow `references/source-library/malta/references/source-acceptance.json` for accepted official links and local-copy restrictions. No national-law local copies are currently accepted; do not treat an EU Maltese-language source as Malta national law.
- See `references/source-library/malta/references/language-pairs.json` and `references/malta-bilingual-verification.md` for the instrument register and detailed workflow.
- Check this package's component version with `scripts/session_version_check.mjs` when the host can execute Node; otherwise disclose that package currentness is unknown.
