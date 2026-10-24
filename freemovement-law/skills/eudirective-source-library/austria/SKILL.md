---
name: austria-legal-source-system
description: Maintain and review Austria's national legal-source pack, issue-led coverage, legal dependencies, semantic acceptance gates and new-source discovery. Use for source work and completeness review, not individual legal advice.
metadata:
  version: 0.6.0
  short-description: Austria national source pack
---

# Austria legal source system

Use this workflow for the bounded source pack in references/source-list.md. The canonical inventory is references/candidate-manifest.json; per-source acquisition rules are in references/source-rules.json.

## Current state

As of 19 October 2026, 73 of 74 records passed per-source acceptance. No captured records remain pending review; one family-topic index is discovery-only; there are no uncaptured official locator-only records. The country review remains incomplete. Source accepted, topic adequately covered and country review complete are distinct results. A fixed inventory can execute successfully while remaining legally insufficient.

## Mandatory review gates

1. **Coverage gate:** Map each relevant issue to primary legislation, implementing rules, procedure, and remedies or operational practice. Use the required topic list and Directive article map in the coverage/dependency registers. Each layer needs evidence from an accepted local artifact or a human-reviewed official reference, or a reasoned not-applicable entry; missing topics or layers block country completion.
2. **Issue-led discovery:** For each topic, ask what is needed to challenge refusal, delay, an added-document demand, visa denial, loss of residence, removal, or an authority's failure to act. Search primary law, implementing rules, court decisions, official guidance, forms and authority procedures. A preselected source list is not evidence of sufficiency.
3. **Dependency gate:** Record material references to other legal instruments and check amendments, validity judgments, successor instruments and procedural dependencies. Keep editorial notes separate from quoted national wording. Every material dependency needs a status and evidence.
4. **Proportionate source review:** A human-reviewed official page or link can be used directly after checking publisher, identity, language, displayed version/date, relevant content and caveats. Extraction, replay and semantic-comparison checks apply to a retained local copy or to extracted passages relied on beyond the material directly reviewed. Hashes establish byte identity only; they do not establish legal currentness or completeness.
5. **Three completion levels:** Report accepted local artifact, usable official reference, topic adequately covered and country review complete separately. A covered layer needs at least one source whose relevant content has been reviewed, whether directly at the official publisher or in an accepted local artifact; a resolved dependency needs evidence. Source acceptance alone never closes a topic.
6. **Continuing discovery:** Exact-record monitoring checks only registered sources. Run separate case-law, mission and Land discovery queues, record exact queries, scope, date, numeric results and dispositions, and require evidence for every terminal task. A plan or status label alone is not completion.

## Retrieval and conversion

- Use the Austria monitor for registered official locators. Its `capture` action handles locator-only RIS statutes with serial public HTTPS requests, current consolidated pages and the `div.contentBlock` selector. Do not use undocumented RIS endpoints, OGD/API, authentication or challenge bypass.
- Raw and derived captures are kept only in the EU Source Update Monitor local-only archive and indexed there by exact bytes and SHA-256. The pack ledger keeps source URLs, retrieval metadata and archive-relative references; do not create pack-local captures or pending-updates folders. Interactive pages with transient ViewState/session state use metadata-only records; never store those tokens or submit forms.
- RIS laws and decisions use record-aware `div.contentBlock` extraction. Exclude screen-reader-only duplicate spans. If visible text is marked aria-hidden, retain the visible text.
- Official guidance pages use publisher-specific main regions. Keep page-shell/navigation text out of converted legal or guidance content.
- Preserve native PDFs where layout or fields matter. Annex E/F are statutory residence-card specimens, not application forms. Visually review both card faces and compare them with the current EU card-format requirements. Accept the Austrian statutory specimens as source artifacts only when identity and visual-source checks pass; record issued-card format compliance separately when the blank models cannot demonstrate encoded data or security features.
- N-Lex is a discovery path only. Verify legal text at RIS or the relevant EU publisher.

## Case-law discovery

Use `scripts/case_law_discovery.py plan` to generate the 55-task matrix, `validate` to review a completed batch, and `record` to append only a valid batch. The wrapper exposes `validate-case-law-batch` and `record-case-law-batch` for files under `references/case-law-batches/`. Search each official RIS form manually: VwGH, BVwG and all nine LVwG collections. Record the exact query, date range, court filter, numeric result count, every official RIS result and the reason for inclusion or exclusion. Eleven reviewed decisions are indexed, but no full search batch is complete. Supplemental web-search leads do not count as a completed RIS batch. RIS collections are selected and update timing differs by court.

## Mission and regional discovery

Use `scripts/operational_discovery.py init` to build or reconcile the manual queue, `plan` to inspect it, and `validate` to check evidence. The queue covers all nine Länder and each of the 524 representation records in the BMEIA directory. It does not search the web. For every mission, review visa instructions, family-member routes, appointment channels, forms/checklists, outsourcing/representation, decision authority and applicant-residence scope. For every Land, review the competent authority, territorial jurisdiction, current form, evidence checklist, appointment and submission route. Each resolved field must have a value, official URL or accepted source ID and a checked date. A no-source result needs exact queries, scope, date, numeric result count and screened results. Five mission pages have leads and partial review. All nine Länder have official authority or legal-source leads; six have partial procedure information and three are lead-only. No regional task is complete.

## Current Austria focus

- FPG §§2(4)(11), 11, 11a, 11b, 15a, 15b, 66, 67 and 70; BFA-VG §§9–10; and IFG §§1–20 are captured and accepted.
- BMI form A and its 2026 supporting-document explanation identify the current national residence-card application form.
- Keep NAG §54(7)'s express exclusion route separate from §55(3)'s continued-right/BFA route. See references/procedural-crosswalk.md.
- Preserve NAG-DV §5 wording and track its Regulation 2019/1157 invalidity/successor relationship separately.
- The BMEIA directory is a mission locator, not a substitute for each mission's instructions.
- Review all eleven selected case holdings, outcomes, postures, applicability and limits, then complete cross-court discovery.

## Acceptance and reporting

Run the Austria `review` action to report local-artifact, dependency, coverage, case-law-discovery and operational-discovery states. `capture` and `accept` maintain locally stored copies; their checks do not gate ordinary use of a human-reviewed official reference. `discover` creates the manual RIS search plan; `validate-case-law-batch` checks all 55 planned search tasks and their recorded dispositions; `record-case-law-batch` records a completed batch. `discover-operations` creates the nine-Land/524-mission work queue. Discovery actions do not run broad searches. A monitor run may stage changes but never accepts a local artifact or declares a country complete. Read references/coverage-register.md before reporting status.
