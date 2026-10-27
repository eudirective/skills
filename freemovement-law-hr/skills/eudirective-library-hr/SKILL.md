---
name: eudirective-library-hr
description: Use when FreeMovement consultation requires Croatia national sources. Read with eudirective-core; this skill provides source records and country-specific verification limits, not a separate legal-reasoning engine.
---

# Croatia national source library

Use this skill with `eudirective-core` when Croatia is a materially relevant jurisdiction.

- Determine the source's publisher, instrument or record identity, language, displayed version/date, scope, and limitations from the official publisher.
- Treat the bundled source records as a versioned snapshot. Check the official publisher for material current-law questions when available.
- Keep external-reference acceptance, local-copy acceptance, topic coverage, and country-review completion separate.
- Use local texts only where the source acceptance record explicitly accepts that exact representation; its hash confirms bytes, not legal meaning or currentness.
- If a source is absent, outdated, link-only, or outside its recorded scope, say what is missing and its effect, and continue with available official-source research.
- Country acceptance and index records are under `references/source-library/croatia/references/`.
- Compare this package's component manifest with the published component index using `scripts/session_version_check.mjs` when Node is available. If execution is unavailable, report package currentness as unknown; do not claim the package is current.
