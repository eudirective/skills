# Austria source-rule sustainability assessment

Assessment date: 19 October 2026. Scope: 74 source records, 12 retrieval/conversion rules, legal dependencies, topic coverage, operational discovery and source acceptance.

## Current state

Seventy-three records pass source identity, version/applicability, extraction, attachment and classification checks plus semantic review. The two native NAG-DV specimens passed source acceptance after visual review; conformity of current issued cards remains an open legal dependency because the blank models do not demonstrate data-field [10], MRZ or security properties. One family index is discovery-only. No official locator-only source remains uncaptured. Austria's country review is incomplete.

The workflow now distinguishes source accepted, topic adequately covered and country review complete. A fixed source inventory can finish all its actions while remaining legally insufficient. Coverage is enforced at the topic/layer level; cross-references are mapped separately; extracted text receives semantic review in addition to byte hashes.

## Rule sustainability and remaining gaps

| Area | Current rule | Assessment |
|---|---|---|
| RIS current legislation | Current-section URLs and statute identifiers; serial capture, saved raw bytes, specific content selector, replay and legal-anchor review. | Sustainable for the bounded list. Selector/identity failures stop acceptance. Source wording is preserved; editorial dependencies stay separate. |
| RIS decisions | Exact official record, court/date/case number, full `div.contentBlock` replay, operative-part checks and a per-case holding/outcome/posture/applicability/limits record. | Sustainable for known decisions. Eleven reviewed decisions remain a selected set, not a case-law survey. |
| Case-law discovery | Fifty-five repeatable manual searches across VwGH, BVwG and all nine LVwG collections. | Repeatable but manual. No full query batch is recorded; fixed-record monitoring cannot discover new decisions. |
| Official forms and routes | Native PDFs retained and extracted; route records follow official parent links. Transient ViewState/session HTML is excluded. | Sustainable with limits. A PDF remains the visual authority; interactive submission behavior is not replayed or automated. BMI form links must be re-resolved from the official index. |
| Mission and Land practice | Queue generator reconciles nine Länder and 524 BMEIA representation records into manual research tasks. | Discovery is repeatable; research is incomplete. Five mission pages are partly reviewed; all nine Länder have official authority or legal-source leads; six have partial procedure information and three are lead-only. |
| Legal dependencies | Material cross-references, validity judgments and successor instruments are recorded independently from source text. Directive article map has explicit mapped/partial/unresolved states. | Stronger than URL-only monitoring. Article-level map is incomplete, so the dependency gate stays open. NAG-DV §5 preserves its original Austrian wording and carries a separate C-61/22/2025-1208 alert. |
| Semantic acceptance | Five required source checks plus human review and source-region replay. Only fully passing items can be accepted. | Prevents hash-only acceptance. The two native annex visuals passed source acceptance; current issued-card conformity remains separately unresolved. Route metadata acceptance is explicitly bounded and contains no session state. |
| Scheduled monitoring | Monthly GitHub Actions workflow for fixed manifest records only. | Workflow file and schedule are present, but current run history and Actions enablement could not be checked because GitHub API access failed on 19 October 2026. No successful execution is verified. |
| Capture reproducibility | Persistent source HTML/PDF bytes, hashes, resolved URLs, media types, and timestamps are registered in a 74-row capture ledger. | Deterministic replay is available for persistent captures. Interactive route HTML is not retained because it contains ephemeral state; its exact official route and reviewed initial capabilities are stored instead. |

## Completion gate

Do not describe Austria as complete until every required topic has primary-law, implementing-rule, procedure and remedy/operational evidence from accepted local artifacts or separately reviewed official references (or an evidenced not-applicable status); the Directive article map and material source dependencies are resolved; case-law discovery and operational tasks have evidence-backed dispositions; and all nine Land tasks plus the applicable BMEIA mission tasks have been reviewed. Pending or unaccepted local copies do not block use of reviewed links or country completion where the relied-on content was checked directly. See [coverage-register.md](coverage-register.md), [source-acceptance.json](source-acceptance.json), [source-dependencies.json](source-dependencies.json), and [operational-discovery.json](operational-discovery.json).
