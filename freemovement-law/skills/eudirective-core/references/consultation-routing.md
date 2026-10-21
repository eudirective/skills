# Ordinary-consultation routing

## Scope and assurance

Use this routing layer before substantive ordinary consultations, including real applicant questions handled through the C23 read-only lane. It assigns review workflows and source owners; it does not make legal findings by itself.

Classification, workflow selection, and the user-facing board remain model-led. Render the board directly in ChatGPT's ordinary Markdown response; no tool or hosted service is needed. The optional local route gate is a structural maintenance check, not an automatic ChatGPT runtime. Keep real applicant facts in the conversation. Do not pass narratives, identities, case numbers, precise dates, or dossier contents to synthetic scripts. C3, C27, the research gate, and issue-source preflight remain the authoritative existing contracts for their respective purposes. Skill instructions cannot force a board to appear or block the host from releasing a response.

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

### Full dashboard trigger

Show the full **FreeMovement — Consultation Review** dashboard after every explicit invocation, every user request for a dashboard/coverage report/execution audit, and every reply where a material routing variable changes. Refresh it when jurisdiction roles, proceeding or stage, legal question, urgency, requested output, issue/check selection, sources, module use, or execution changes. In an ordinary ChatGPT response, refresh the board directly; if a maintainer is separately creating a route receipt for the optional local gate, record `invocation.material_change=true`. Do not make the full board opt-in, and do not cap or omit recorded rows for compactness. A mere mention of FreeMovement is not an invocation. Use `explicit`, `implicit` or `unknown` as the recorded state. The available plugin metadata does not establish a reliable host invocation event; when neither a host signal nor visible plugin-selection marker is available, record `unknown` and do not claim the trigger was detected. A direct explicit invocation unrelated to legal consultation receives a minimal board stating that no case assessment was performed.

For applicant guidance and source research, record source use in the structured ledger defined by `references/contracts/consultation-route-receipt.schema.json`. Resolve bundled source IDs against the existing retrieval index and manifests; do not create a duplicate source registry. For each source, record separately whether it matched a source record in the plugin's bundled library and how it was identified in the current response and earlier conversation. Use `plugin_library`, `web_search`, `user_provided`, `prior_conversation`, `model_knowledge`, `other`, or `unknown`; never infer `web_search` from an external official URL. Count distinct source records identified and canonical legal texts consulted separately. Show plugin-library matches and web-search discoveries as separate counts; these dimensions can overlap when a search returns a source also bundled in the plugin, so do not add them as if mutually exclusive. Counts cover the source records listed in the board, not every raw search-result hit. Include identified-but-not-read records in the identified total but not in the consulted total. Show every source title, consulted pinpoint, candidate/unaccepted state, source-note status, external official source, version/edition, currentness, discovery method, and response-versus-chat use. If source-use or discovery tracking is unavailable, show `unknown`, never zero. The 0.3.0 receipt records response and conversation discovery methods; older receipts without these fields must render the search total as unknown when their method cannot be established. Counts are model-reported, not proof of retrieval. This package has no host-authenticated source-read event contract: mark consultations as model-reported, and do not use `runtime_recorded` unless a future host provides and validates its own attested event. The local gate rejects runtime-recorded source states because a generic file and digest do not establish that a retrieval occurred. The core module must appear for applicant guidance and source research; every declared module-pair check must reconcile to its module-use entry. Do not collapse C27 or research statuses into the overall label. See `references/consultation-dashboard-examples.md` for the complete board layout.

### Default response and full board contents

Answer the user's substantive request first. Add a brief scope or urgency note only when it helps. End with a concise coverage summary naming material open issues and their effect, then add the dashboard whenever the trigger above applies. Do not expose private chain-of-thought.

The full board must show every recorded classification state; conditional-workflow review; required, triggered, and not-triggered operations, including missing required operations; every selected C27 check with exact ID/status/method/reason/evidence/source trace and any `scope_exclusion`; every issue disposition/signal and its missing-item/effect summary; every validator result and unavailable reason; all source-ledger rows without truncation; and every relevant module's current response use, earlier-chat use, availability, C3 conformance and reason. Keep model-led assessment separate from source review and deterministic validator execution. Show opaque receipt references only when needed to link records, and explain them in plain language. Each partial or unavailable item must name what is missing and how it limits the assessment. The overall label does not replace individual check or validator statuses.

### Native Markdown board and validation boundary

Render the board in native Markdown using readable section headings and separated status cards. Do not use a wide table, pipe-delimited rows, raw HTML, or a fenced code block for the board. Put a plain-language status before any exact check or operation ID. Keep each operation and C27 check visible with its evidence, status, method, and any missing item/effect. If the model cannot tell whether an item ran, say `unknown` or `not recorded`; do not imply that a validator ran merely because it is described in a skill or present in the package. Source and module use are model-reported unless a trusted host event is actually available. The route-receipt schema and local gate can support offline structural maintenance, but ordinary ChatGPT responses do not invoke them automatically or receive a validated view model. See `references/consultation-route-gate.md` for their limited role.

## 6. Conversation record

Keep a concise issue-to-answer record for the current conversation. Record jurisdictions by role, proceedings/stages, material issues, selected signals/checks, dispositions, source owners, operations, module use and open work. Do not persist a case file, repeat sensitive facts unnecessarily, or reveal private chain-of-thought. This record is not a host-validated release receipt.
