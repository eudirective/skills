# Ordinary-consultation routing

## Scope and assurance

Use this routing layer before substantive ordinary consultations, including real applicant questions handled through the C23 read-only lane. It assigns review workflows and source owners; it does not make legal findings by itself.

This is a skill-level, model-led control. Keep real applicant facts in the conversation. Do not pass narratives, identities, case numbers, precise dates, or dossier contents to synthetic scripts. C3, C27, the research gate, and issue-source preflight remain the authoritative existing contracts for their respective purposes. This skill cannot ensure that a model follows the route or prevent an answer from being released; no host-enforced gate is established here.

## 1. Classify the request

Before substantive analysis, record a concise working classification. Use `unknown` when the conversation does not establish a value; do not infer it. Use `not_applicable` only with a short reason.

- **Jurisdictions by role:** EU/common; residence, work, intended-residence, deciding, representing, challenged-authority and document-issuing Member State roles; applicant-country mission/application context and destination state; any other national-law jurisdiction. Keep roles distinct even when they identify the same country. Follow C3's typed-geography contract.
- **Proceedings:** list each separate visa, residence, border, appeal, conduct complaint, administrative complaint, file-access or data-access proceeding that is implicated. Preserve the person's claimed category separately from the authority's classification.
- **Issues and questions:** identify material events and neutral legal questions, separating EU/common law, national law or procedure, local operations, evidence, deadlines, authority competence, remedies and factual disputes where relevant. Use `references/consultation-issue-model.md`.
- **Procedural stage:** for each proceeding, distinguish inquiry, appointment, attempted submission, formal lodging, decision, notification, appeal, complaint, access request and closure. Keep disputed or unsupported stage claims open under C27.
- **Urgency:** identify a known deadline or evidence-loss risk and its basis. Otherwise use `urgency unknown` or `no urgent risk identified` only when supported. Give an appropriately qualified urgent step without waiting for non-urgent research.
- **Requested output:** identify whether the person asks for an explanation, issue assessment, source check, deadline/remedy route, evidence plan, draft, comparison or another concrete deliverable.

For an applicant matter, use C27's `references/state-engine/check-registry.json` to select relevant atomic checks. Do not duplicate its check catalogue or run all 301 checks by default. A check's absence from the selected set does not establish legal inapplicability.

## 2. Build an execution plan

Use `references/consultation-issue-routing.json` to map declared issue signals to C27 checks and review owners. It is routing metadata, not a second legal-rule or check registry. Keep required, conditionally triggered and not-selected work distinct in the working record. For selected operations, record the trigger, expected evidence, source/engine owner and whether they can run in the ordinary consultation lane.

When a country module is selected, run C3's existing pair-level module-conformance check against its manifest/export with `scripts/module_conformance.py` when available. It checks module identity, contract/profile, supported roles and declared destination profiles; it does not match case geography to a module request. Use `case_controller.py` for typed-geography-to-module matching only through an approved input boundary. Never send a real applicant record to a synthetic case controller. If no approved case-level check is available, record it as unavailable; do not add a second deterministic geography ruleset.

### Required for substantive applicant guidance

- C23 read-only guidance and C27 proceeding/completeness reconciliation.
- A model-led attack-angle screen, separate from C27's adapted-stratagem checks. Consider only factually indicated candidates in the core catalogue and relevant, C3-conformant country-module records. This is screening, not a finding of illegality, misconduct, motive or remedy entitlement. Never claim the C5d script ran on a real case.
- The answer requested and a concise, accurate account of material coverage and limitations.

### Conditional analysis and research

| Trigger | Workflow to route to |
| --- | --- |
| Movement, family relationship, destination or cross-border topology affects the governing regime | C5a topology/applicability review; EU/common source owner and relevant Member-State roles |
| Competing rules, hierarchy, Charter scope or legal principles affect an issue | C5b hierarchy/principles review; keep each source owner attached to its rule |
| Evidence restrictions, exact deadlines, authority powers or remedy routes matter | C5c evidence/deadline/authority-route review; route national questions to the correct Member-State owner |
| New facts or corrected records may change an earlier answer | C24 fact-rule revision and affected C27 checks |
| A refusal, disputed authority position, separate grievance, disclosure history or evidence-preservation need is present | C25 grievance and evidence-acquisition review; distinguish actual from hypothetical authority grounds |
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

## 5. User-facing answer and dashboard

On the first response, preserve the existing order: required disclaimer, applicable licensing note, skill-version line, then the answer. On later replies, do not repeat once-per-conversation notices unless the use context materially changes.

### Compact dashboard trigger

Show the compact **FreeMovement — Consultation Review** dashboard after the substantive answer when a host signal or visible plugin-selection marker establishes an explicit invocation. Refresh it on every new explicit invocation, including repeated invocations in the same conversation. Also show it whenever the user asks for a dashboard, coverage report or execution audit. A continuation without a new explicit invocation may omit it unless the assessment materially changes or the dashboard improves transparency.

Use `explicit`, `implicit` or `unknown` as the recorded invocation state. A mere mention of FreeMovement is not an invocation. The available plugin metadata does not establish a reliable host invocation event; absent a host signal, the strongest supported instruction-level cue is a visible plugin-selection marker. When neither is available, record `unknown` and do not claim the trigger was reliably detected. A direct explicit invocation unrelated to legal consultation receives a minimal dashboard stating that no case assessment was performed.

For applicant guidance and source research, record source use in the structured ledger defined by `references/contracts/consultation-route-receipt.schema.json`. Resolve bundled source IDs against the existing retrieval index and manifests; do not create a duplicate source registry. Count distinct canonical legal texts consulted in the response and, when supported by a reliable ledger, across the conversation. A source found in an index, cited from memory, or identified but not read is not a consultation. Keep each consulted pinpoint, candidate/unaccepted state, source-note status, external official source, and currentness state visible. If source-use tracking is unavailable, show `unknown`, never zero. Label model-reported counts separately from runtime-recorded events. Group bundled sources by library section and category; show external official texts separately. Bars compare only the displayed groups and never imply library coverage.

The compact dashboard follows the legal answer and contains an overall status, response/conversation source metrics, library sections consulted, outstanding material issues and checks, source groups with underlying titles and pinpoints, and relevant module use for this response and earlier in the chat. Every partial assessment must name all recorded material issues and open checks, say what is missing, and explain what remains unassessed. The core module must appear for applicant guidance and source research; every declared module-pair check must reconcile to its module-use entry. The receipt cannot infer omitted relevant modules from case facts, which remain in the conversation. Do not collapse C27 or research statuses into the overall label. For layout and a Markdown fallback see `references/consultation-dashboard-examples.md`.

### Default response

Answer the user's substantive request first. Add a brief scope or urgency note only when it helps. End with a concise coverage summary naming material open issues and their effect, then add the dashboard only when its trigger above applies. When jurisdiction roles, proceeding or stage, material facts, source consultation, module availability/conformance or execution changes, state which relevant modules informed this answer, which were used earlier in this chat, and which relevant modules were not used; give a short reason when absence limits coverage. If these variables and module-use states have not changed, do not repeat the full module record. Do not expose private chain-of-thought.

Avoid listing every completed check, operation, reference and status in the compact dashboard. Keep all partial and unresolved work visible in plain language: say exactly what is missing and what cannot yet be assessed. The expanded audit below retains the detailed ledger.

### Expanded audit, when requested or needed

Group the record by proceeding, with a short plain-language issue heading. For each issue, provide:

- **Disposition:** answered and supported, answered conditionally, source missing, fact missing, or out of scope.
- **C27:** readable status and method; exact check ID; finding; material evidence/source references; reason; `scope_exclusion` where present.
- **Missing / effect:** specific missing item and the part of the assessment it limits.

Then show an **Execution board**, with separate entries for review/screening, source retrieval and validators/scripts. Each actual operation gets its own status, applicability, result/evidence, exact `operation_id`, and reason/effect for open work. Model-led review has no invented operation ID and is not presented as script execution. Keep attack-angle screening separate from C27 stratagem checks. Include the source-use ledger with canonical titles and every consulted pinpoint; distinguish response reads from conversation history, identified-not-read sources, memory citations and external sources.

Finish with **Module use in this answer and current chat**. Include only relevant modules under C3's role/family/destination semantics. For each, separate source consultation in this answer, use earlier in this chat, availability, and C3 conformance/evidence. A module being installed or named does not mean it was used. Refresh this record when role, proceeding, stage, material facts, source consultation, availability, conformance or execution changes; otherwise a concise no-change note is enough.

End the expanded audit with the accurate coverage label, material open items and their effect. Do not imply that the dashboard enforces release. A skill-only route is self-reported; non-bypassable enforcement requires a host/controller to validate and bind evidence before release.

## 6. Conversation record

Keep a concise issue-to-answer record for the current conversation. Record jurisdictions by role, proceedings/stages, material issues, selected signals/checks, dispositions, source owners, operations, module use and open work. Do not persist a case file, repeat sensitive facts unnecessarily, or reveal private chain-of-thought. This record is not a host-validated release receipt.

## Optional local receipt check

Where a host can run local package scripts, it may serialize a privacy-minimised receipt using `references/contracts/consultation-route-receipt.schema.json` and call `scripts/consultation_route_gate.py`. The receipt contains classification states, workflow/check identifiers and generated opaque references only. Keep actual case facts in the conversation. An optional `issues` array can bind each opaque issue/scope reference to registered signal IDs, a disposition and a conversation-record reference; when present, the gate reports required routed C27 checks missing from that scope. Existing receipts without `issues` remain valid. The gate resolves references against the evidence index, runs existing C3 module-pair and research validators, checks C27 records through C27's shared validation, and incorporates source-preflight gaps. Self-reported conversation/source records are not authenticated, omitted issues or conditionals cannot be discovered unless declared, and the host must call the gate and enforce its result before release. See `references/consultation-route-gate.md`.
