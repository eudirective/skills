# Poland national-source pack

This folder holds a 63-reference discovery and review pack for Poland's EU free-movement, immigration, procedure, remedy, privacy, consular and related source routes. Poland is an EU Member State. EU/EEA/Swiss, returning-Polish-national, UK Withdrawal Agreement, national-permit and asylum routes remain distinct.

- [Candidate source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Source-review manifest](references/source-review-manifest.json)
- [Official-link acceptance register](references/source-acceptance.json)
- [Issue-led coverage register](references/coverage-register.md)
- [Dependency register](references/dependency-register.json)
- [Sustainability assessment](references/sustainability-assessment.md)

## Current review state

The review accepts 54 current official links within their recorded scopes. Four older references are historical-only, and five exact routes are not relied upon; whole official sites or portals are offered for direct human review where an access failure or dynamic page prevents a precise currentness check. No local copy or topic is accepted, and Poland remains incomplete.

The official ELI links now include the current consolidated EU-citizen residence Act (Dz.U. 2026 poz. 1065), Electronic Delivery Act (Dz.U. 2026 poz. 3), SIS/VIS implementation Act (Dz.U. 2026 poz. 1061), Free Legal Aid Act (Dz.U. 2026 poz. 44), and companion form regulations for ordinary and permanent residence (Dz.U. 2021 poz. 1392 and 1391). The review also links the current Stamp Duty Act, Constitution, Ombudsman Act and KPA complaints regulation. Dated texts and later amendments are clearly scoped in the acceptance and dependency registers.

The current UDSC application and attachment index is accepted as a parent source for rediscovering forms; its attachments still need to be matched to the specific legal procedure. The MOS portal is offered for human review of the current EU-family card specimen, forms and collection procedures because the direct specimen route could not be opened in the research client. The 2021 “new forms” page and old-document deadline notice are historical references, not current form or deadline instructions.

One procedural conflict remains material: UDSC says personal ePUAP submissions after 1 January 2026 are ineffective for its general complaint route, while UODO's SIS-rights page still instructs applicants to use ePUAP. The applicable special-law exception, if any, must be checked before publishing a submission channel. This pack does not claim ePUAP or e-Doręczenia is universally effective for every procedure.

## Local-copy workflow

The earlier capture run covered 54 candidate URLs: 51 exact responses were saved and 50 conversions replay-verified as unaccepted local review material. Three requests failed (one HTTP 403 and two certificate-validation errors); e-Konsulat returned a dynamic shell without extractable text. Nine newer references were reviewed as links only and were not retrieved. These capture results are historical evidence about the optional local-copy route; they do not block official-link use or establish topic coverage.

Use `python source-library/poland/sync_poland.py sync [CANDIDATE_ID ...]` only when a local copy is wanted for a specific purpose such as reproducible retention or recurring change monitoring. The capture output remains a review candidate. Hashes and conversion replay establish file integrity, not legal sufficiency or semantic correctness. API registration, API reuse terms, pypdf and batch conversion are not prerequisites for using a trustworthy official link. No local files are automatically accepted.

## Remaining work

The issue-led coverage register identifies unresolved legal and practical crosswalks: core versus facilitated family categories, decision-specific administrative and judicial remedies, ePUAP exceptions, current Polish card specimens and transition rules, 16 voivodeship procedures, mission-specific appointment paths, and repeatable case-law discovery across the NSA and all voivodeship administrative courts. See the [coverage register](references/coverage-register.md) and [dependency register](references/dependency-register.json); do not describe the country review as complete.
