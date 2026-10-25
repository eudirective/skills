---
name: <jurisdiction>-legal-source-system
description: Maintain the <jurisdiction> source inventory and reviewed national documents for <defined scope>.
metadata:
  version: 0.1.0
  short-description: <Jurisdiction> national source pack
---

# <Jurisdiction> legal source system

Use this workflow only for the scope recorded in `references/source-list.md`. The machine-readable source inventory is `references/candidate-manifest.json`; optional local-copy or monitoring rules are in `references/source-rules.json`. Keep unaccepted research files and captures in the Monitor's indexed local-only archive, not in a country-pack folder.

## Retrieval and conversion

- Official source route: <direct government page or, only when needed, a catalogue/API>
- Identity and version: record publisher, title or stable ID, language, displayed date/cutoff, scope, and visible caveats
- Conversion: describe only a conversion actually used for a retained local copy; a human-reviewed link needs no capture or converter
- Change review: note when the source was checked; add a change signal/updater only when recurring monitoring is needed
- Reuse: assess permission for copying, automated retrieval, or republication when those actions are planned; linking/reference use is separate

## Review before use

Record the official publisher and URL, language, displayed version/date/cutoff, relevant legal effect, scope, and any publisher caveat. Prefer the latest government-published consolidation; when none is usable, use the closest government-published text and state its limits. Accept a government consolidation as a usable official reference when the publisher, instrument, and consolidation status are clear and no concrete warning undermines reliance. If trust is unclear, offer the full government legal-text website/service, including its authority and versioning information and the relevant text, to the user for human review. Do not turn uncertainty into a default full-site crawl or Gazette-chain reconstruction. Consult amendment or Gazette fragments only for a specific material gap, such as a known later change or commencement issue. Do not require a complete amendment-chain reconstruction by default. For ordinary source use and topic evidence, a human-reviewed official link is enough; capture, hash, conversion, OCR, replay, and updater checks apply only to retained local artifacts or a justified recurring-monitoring workflow. A successful retrieval or conversion does not establish topic or country completeness.
