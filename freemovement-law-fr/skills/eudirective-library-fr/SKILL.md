---
name: eudirective-library-fr
description: Use when FreeMovement consultation requires France national sources. Read with eudirective-core; this skill provides source records and country-specific verification limits, not a separate legal-reasoning engine.
---

# France national source library

Use this skill with `eudirective-core` when France is a materially relevant jurisdiction.

- Determine the source's publisher, instrument or record identity, language, displayed version/date, scope, and limitations from the official publisher.
- Treat the bundled source records as a versioned snapshot. Check the official publisher for material current-law questions when available.
- Keep external-reference acceptance, local-copy acceptance, topic coverage, and country-review completion separate.
- Use local texts only where the source acceptance record explicitly accepts that exact representation; its hash confirms bytes, not legal meaning or currentness.
- If a source is absent, outdated, link-only, or outside its recorded scope, say what is missing and its effect, and continue with available official-source research.
- Country acceptance and index records are under `../../references/source-library/france/references/`.
- Compare this package's component manifest with the published component index using `scripts/session_version_check.mjs` when Node is available. If execution is unavailable, report package currentness as unknown; do not claim the package is current.


## Issue-to-source candidates

For a France EU-family visa refusal, ordinary short-stay refusal, or conditional interim-relief question, consult the package-root file `../../references/source-library/france/references/consultation-issue-source-index.json` to identify candidate sources. The index is a locator, not a finding that a source was consulted, applicable, binding, or current. Keep the ordinary F16146 short-stay RAPO route separate from a Directive 2004/38 EU-family refusal. The Nantes joined 2021 decisions are first-instance and fact-specific candidates, not automatically applicable precedent. For interim relief, describe the route only after current official-source review; preserve all ordinary appeal deadlines. In each response, record the state of each source: candidate identified, official link reviewed, official text opened, bundled accepted text actually read, or not consulted; include publisher, displayed date/version and pinpoint when available.
