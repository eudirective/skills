# Ordinary-consultation routing

## Scope and assurance

Use this routing layer before substantive ordinary consultations, including real applicant questions handled through the C23 read-only lane. It assigns review workflows and source owners; it does not make legal findings by itself.

Classification, workflow selection, and the user-facing board remain model-led. Ordinary ChatGPT renders the board directly in its Markdown response; the plugin does not provide an automatic renderer call or host release gate. In a local Codex host with shell access, `consultation_route_gate.py --dashboard-only` can validate a privacy-minimized receipt and emit the existing renderer output for unchanged inclusion. Do not write conversation text or case-specific narratives, identities, case numbers, exact dates/places, or document contents to a receipt or temporary file. If the input cannot be minimized safely, render the board directly in the conversation. C3, C27, the research gate, and issue-source preflight remain the authoritative existing contracts for their respective purposes. Skill instructions cannot force a board to appear or block the host from releasing a response.

## 1. Classify the request

Before substantive analysis, record a concise working classification. Use `unknown` when the conversation does not establish a value; do not infer it. Use `not_applicable` only with a short reason.

- **Jurisdictions by role:** EU/common; residence, work, intended-residence, deciding, representing, challenged-authority and document-issuing Member State roles; applicant-country mission/application context and destination state; any other national-law jurisdiction. Keep roles distinct even when they identify the same country. Follow C3's typed-geography contract.
- **Proceedings:** list each separate visa, residence, border, appeal, conduct complaint, administrative complaint, file-access or data-access proceeding that is implicated. Preserve the person's claimed category separately from the authority's classification.
- **Issues and questions:** identify material events and neutral legal questions, separating EU/common law, national law or procedure, local operations, evidence, deadlines, authority competence, remedies and factual disputes where relevant. Use `references/consultation-issue-model.md`.
- **Procedural stage:** for each proceeding, distinguish inquiry, appointment, attempted submission, formal lodging, decision, notification, appeal, complaint, access request and closure. Keep disputed or unsupported stage claims open under C27.
- **Urgency:** identify a known deadline or evidence-loss risk and its basis. Otherwise use `urgency unknown` or `no urgent risk identified` only when supported. Give an appropriately qualified urgent step without waiting for non-urgent research.
- **Requested output:** identify whether the person asks for an explanation, issue assessment, source check, deadline/remedy route, evidence plan, draft, comparison or another concrete deliverable.

For an applicant matter, use C27's `references/state-engine/check-registry.json` to select relevant atomic checks. Do not duplicate its check catalogue or run all 308 checks by default. A check's absence from the selected set does not establish legal inapplicability.

## 2. Build an execution plan

Use `references/consultation-issue-routing.json` to map declared issue signals to C27 checks and review owners. It is routing metadata, not a second legal-rule or check registry. For routes with a procedure scope, classify the proceeding first. If its type is missing or unresolved, record the scope gap and select only the framework-resolution checks. A `visa_appeal` stays a separate linked proceeding; review the underlying application in its own scope. Keep required, conditionally triggered and not-selected work distinct in the working record. For selected operations, record the trigger, expected evidence, source/engine owner and whether they can run in the ordinary consultation lane.

Keep a formal outcome separate from a lifecycle stage. Article 18 competence, Article 19 inadmissibility and Article 32 substantive refusal are separate Visa Code routes. Select the Article 32 refusal and appeal-information check only for an ordinary short-stay Visa Code application with a source-attributed Article 32 outcome. A declared Article 19 inadmissibility or pre-lodgement/access obstruction must not select that check. If the type or official outcome record is missing, record the unresolved status and leave the specialized route open. See `references/consultation-outcomes-and-remedies.md`.

For a C27 `other` outcome, put its brief explanation in plain language on the issue card, indicate that the official evidence reference is recorded, and leave the route for manual review until the event is identified. For `undetermined`, say what evidence is missing or conflicting and how that prevents classification; keep outcome-specific routes unresolved. Distinguish these states from an outcome that was not recorded and from a claimed outcome whose official record has not been checked. Do not promote any of these states to a formal Visa Code outcome.

When a country module is selected, run C3's existing pair-level module-conformance check against its manifest/export with `scripts/module_conformance.py` when available. It checks module identity, contract/profile, supported roles and declared destination profiles; it does not match case geography to a module request. Use `case_controller.py` for typed-geography-to-module matching only through an approved input boundary. Never send a real applicant record to a synthetic case controller. If no approved case-level check is available, record it as unavailable; do not add a second deterministic geography ruleset.

### Required for substantive applicant guidance

- C23 read-only guidance and C27 proceeding/completeness reconciliation.
- A model-led attack-angle screen, separate from C27's adapted-stratagem checks. Consider only factually indicated candidates in the core catalogue and relevant, C3-conformant country-module records. This is screening, not a finding of illegality, misconduct, motive or remedy entitlement. Never claim the C5d script ran on a real case.
- The answer requested and a concise, accurate account of material coverage and limitations.

For 0.8.0 and 0.9.0 applicant-guidance and source-research receipts, record the required `consultation_finalisation` operation after the core has reconciled the current board, strategy review, and route evidence. National modules and research validators provide scoped evidence; they do not replace this core-owned final receipt check. Its evidence remains model-declared unless a trusted runtime supplies an execution record.

### Conditional analysis and research

| Trigger | Workflow to route to |
| --- | --- |
| Movement, family relationship, destination or cross-border topology affects the governing regime | C5a topology/applicability review; EU/common source owner and relevant Member-State roles |
| Competing rules, hierarchy, Charter scope or legal principles affect an issue | C5b hierarchy/principles review; keep each source owner attached to its rule |
| Evidence restrictions, exact deadlines, authority powers or remedy routes matter | C5c evidence/deadline/authority-route review; route national questions to the correct Member-State owner |
| New facts or corrected records may change an earlier answer | C24 fact-rule revision and affected C27 checks |
| A material procedural-friction candidate is source-supported, the user asks for prevention/planning/strategy, or a foreseeable decision could materially affect rights | C25 prospective-prevention branch in `references/consultation-preventive-strategy.md`; compare feasible options and give a proportionate first step or justified no-action choice, with conditional reassessment. No adverse event or C5d predicate is required. |
| A refusal, disputed authority position, separate grievance, disclosure history or evidence-preservation need is present | C25 grievance and evidence-acquisition review; distinguish actual from hypothetical authority grounds |
| A required step is available only through an online process, or a person reports digital access barriers | Review the documented access requirement and its effect; do not infer that an online-only process is unlawful without the applicable legal and factual analysis |
| A material question depends on current, multiple, disputed or incomplete sources | `references/research-control.md`; create owner-specific tasks and validate plans/bundles with `scripts/research_gate.py` |
| A material source gap affects issue-level or overall coverage | Use `references/contracts/issue-source-preflight.schema.json` and bind the record to existing research artifacts; see `references/issue-source-preflight.md` |
| Local application, mission, VAC or document-acquisition operations matter | Türkiye applicant-country owner only when the C3 role/destination matches; otherwise identify the responsible owner or leave the source gap open |
| Swedish law, administrative procedure, appeals or Swedish authority powers matter | Sweden Member-State owner for the applicable C3 role |
| Another national-law question is material | Use the registered national pack when available; otherwise review the responsible government's official source and record it as an `unregistered:<CC>` `official_reference` |

Use the source library to locate bundled records and publisher details. For current-law questions, prefer the responsible government's latest usable consolidation; otherwise use the closest official version and state its cutoff and limits. A human-reviewed official link may be used without library registration or a local copy. A bundled snapshot is not a live source check.

The C5a-C5d scripts and C6/C7/C17/C21 tools retain their documented input limits. For real consultations, do applicable reasoning model-led in the conversation; do not represent it as scripted execution. C5e/C5f synthetic suggestion and ranking workflows are not ordinary real-case engines. Route concrete next steps through C23/C25 and verify source support.

## 3. Check execution and preserve evidence gaps

For each selected C27 check, preserve C27's exact fields: `check_id`, `status`, `method`, `reason`, `evidence_refs`, and `source_refs`, plus `scope_exclusion` when applicable. Use only C27's statuses `assessed`, `partial`, `not_checked`, `blocked`, `not_applicable`, and `unavailable`, and methods `model_review`, `source_review`, and `none`. An assessed/partial record needs its corresponding method and a traceable evidence or source reference; a not-applicable record needs its scope reason and trace.

For every partial check or operation, name the missing fact, document, source, review, retrieval or execution step and explain how it limits the assessment. If the exact missing item is unknown, say so. An unavailable required operation remains open for completeness even when its reason is recorded.

For every required or triggered engine, validator or retrieval operation, record its own operation ID, applicability, execution status, output/evidence reference, and reason or next step. Cite output only when that operation actually ran. Do not mark an operation complete because its skill, engine or catalogue was merely read or named. Keep model-led consideration, reviewed source text, deterministic validator output and synthetic script execution distinct.

Reuse the C27 registry for check IDs/status, C3 for module semantics, `research_gate.py` for research-artifact validation, and `issue_source_preflight.py` for source accounting. These validators do not establish source authenticity, legal entailment, semantic correctness or host enforcement.

## 4. Gate completeness claims

Do not call an assessment **comprehensive** while any required check, triggered workflow or material research task remains unperformed, partial, stale, blocked, conflicting or unavailable. Say `partial`, `preliminary` or another accurate scope label, name material outstanding items and explain their effects. Assess completeness against relevant selected checks, not the entire registry; use supportable C27-compatible not-applicable decisions.

Use `comprehensive` only when every required and triggered check has acceptable evidence or a reasoned C27-compatible not-applicable status, and research coverage meets its existing validator and review rules. This label still does not establish a legal outcome, expert review, source authenticity or guaranteed result.

Receipt 0.8.0 and 0.9.0 make the top-level consultation mode (`full` or `limited`) independent of the coverage claim and assessment status. Full means the complete review flow appropriate to the requested scope was performed; Limited means the response was narrowed or a material review step could not be completed. Either mode may carry partial or comprehensive declared coverage, with every open item and effect shown. The receipt requires a board and strategy screen for each substantive applicant-guidance or source-research response, and reuses the typed scope, C27 occurrence, source-owner and research checks described above. Triggered and unknown strategy reviews link to current issue records and their evidence; any strategy limitation links to open issues and evidence. When intervention is warranted, record the objective, a case-specific first step, purpose, reassessment event and alternatives. A no-action recommendation records its rationale. Generic explanations are rejected. Receipts 0.1.0–0.7.0 remain readable for replay, and local controlled release accepts versions 0.5.0–0.9.0. These checks reconcile declared records; they do not establish that the model found every issue, selected every relevant signal, authenticated a source, or made legally correct choices. A local runner may append the canonical board once if it is wholly absent, but refuses to rewrite a malformed or conflicting board. This does not provide a ChatGPT host hook.

Existing production routing, source-class and pathway metadata retain their recorded `pending_independent_review` status. The local checker does not alter that production review state. The strict comprehensive path continues to respect its scoped production gate; qualified limited output remains available where the existing release configuration permits it. A local controller is not invoked by ordinary ChatGPT and does not veto hosted responses.

When a strict receipt records `invocation.material_change=true`, list affected opaque scopes in `revision_control.affected_scope_refs` and list a scope in `reassessed_scope_refs` only after its issue checks and linked obligations have been reviewed again for the current response. Their evidence entries must say `record_scope=current_response`; otherwise the changed scope stays open. This is an explicit workflow record, not an authenticated proof of reassessment.

## 5. User-facing answer and diagnostic dashboard

### Every substantive consultation

Answer the user's request directly and concisely, then show a fresh native-Markdown board in the same response. For every material turn, update it when jurisdictions, proceedings/stage, issue facts, source review, modules or execution state change. Show its top-level **Full** or **Limited** consultation mode separately from declared coverage and assessment status. Full means the complete review flow appropriate to the requested scope was performed; Limited means the response was narrowed or a material review step could not be completed. A Full review can still show partial coverage and outstanding items. A Limited review can show comprehensive coverage of a narrow question. Neither mode establishes legal completeness or proves that the model found every issue.

Keep the underlying issue, C27, research, source, module, strategy and execution records distinct. Screen the five strategy trigger categories on every substantive guidance answer. When a material jurisdiction, proceeding/stage, source, module, or execution variable changes, briefly identify what informed the answer and any materially relevant source/module not used. Skill presence and instructions read do not prove that national source text was consulted. Do not report an operation as executed without an observed result. A concise answer does not permit a comprehensive claim while required work remains open.

### Board content and mode

Use the **freemovement-law — Consultation Review** board for every substantive legal consultation. A mere mention of the plugin and unrelated development work do not trigger a case board. Use `references/consultation-dashboard-examples.md` for native-Markdown layout.

The board shows its output mode; recorded classifications; conditional-workflow review; required, triggered, and not-triggered operations, including missing required operations; every selected C27 check with exact ID/status/method/reason/evidence/source trace and any `scope_exclusion`; every issue disposition/signal and its missing-item/effect summary; every validator result and unavailable reason; all source-ledger rows; relevant module use now or earlier, availability, C3 conformance and reason; and the five strategy trigger reviews. Keep model-led assessment separate from source review and deterministic validator execution. Show plain-language status before technical identifiers. A selected check remains a prompt until assessed. Each partial or unavailable item names what is missing and how it limits the assessment; the overall label does not replace individual statuses.

Derive metrics only from recorded issue dispositions. Unknown or incomplete data remains unknown/not recorded, not zero. Counts and percentages describe only recorded outcomes, not legal completeness or proof that every issue was found. For every source, distinguish whether it matches the bundled library and how it was identified for this response and earlier in the chat; use `plugin_library`, `web_search`, `user_provided`, `prior_conversation`, `model_knowledge`, `other`, or `unknown`. Bundled matches and search discoveries may overlap. Count source records, not raw search hits, and never claim an unread source was consulted. These values are model-reported unless a trusted host event is available.

A local Codex shell may run `consultation_route_gate.py --dashboard-only` or the opt-in local controlled-release command only with the exact bundle, available Python, and a privacy-minimized receipt. Use only schema-enumerated abstract identifiers, procedure types and states, opaque evidence references, and generic missing/effect text. Never put names, countries, dates, case numbers, proceeding facts, narratives, correspondence, or document contents into a receipt or temporary file. The gate checks declared structure only; it cannot find omitted issues, validate law, authenticate source reading, or force answer release. Ordinary ChatGPT does not invoke this command automatically. See `references/consultation-route-gate.md` and `references/consultation-dashboard-runtime-assessment.md` for its limits.

## 6. Conversation record

Keep a concise issue-to-answer record for the current conversation. Record jurisdictions by role, proceedings/stages, material issues, selected signals/checks, dispositions, source owners, operations, module use and open work. Do not persist a case file, repeat sensitive facts unnecessarily, or reveal private chain-of-thought. This record is not a host-validated release receipt.

For 0.9.0, Limited consultation mode requires a specific `consultation_limitation`: reason, missing review, effect, relevant issue/evidence links, and identifiers of any unperformed required workflow reviews. Full mode requires the declared mandatory model-led workflow reviews to be performed with acceptable evidence; deterministic execution is recorded separately and may be unavailable; open factual or legal findings alone do not prevent Full mode. Strategy mode is independent: assess all five trigger categories, address unknown facts and conditional alternatives, and use Limited only where an essential strategy assessment cannot be performed. Preserve the distinct 0.8 replay rules.

For a completed 0.9 source or research workflow review, record `source_outcome: reviewed` with a referenced source or local artifact, or `source_outcome: no_source_available` with a specific explanation and evidence of the attempted review. An unavailable source remains a coverage gap. Record deterministic validator outcomes separately.
