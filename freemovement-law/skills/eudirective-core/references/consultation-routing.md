# Ordinary-consultation routing

## Scope and assurance

Use this routing layer before substantive ordinary consultations, including real applicant questions handled through the C23 read-only lane. It assigns the applicable workflows and source owners; it does not make legal findings by itself.

This is a skill-level, model-led control. Record the route, plan, execution status and coverage in the conversation. A skill instruction cannot ensure that the model follows the route or prevent an answer from being released. Non-bypassable enforcement requires a controller or host to validate the route record and its evidence before release. No such host enforcement is established by this reference.

Keep real applicant facts in the conversation. Do not pass narratives, identities, case numbers, precise dates or dossier contents to synthetic scripts. Apply C3's existing family, jurisdiction, role and destination matching semantics from `references/inter-skill-contract.md` and `references/controller-protocol.md`; do not create a second geography-to-module ruleset. The C3 case controller and C6 pipeline remain within their documented synthetic-input boundaries. If a deterministic case-level C3 check cannot be run in the ordinary lane without using restricted input, record that check as unavailable and state the consequence. Static module conformance may use the existing C3 validator against module files.

## 1. Classify the request

For a substantive consultation, record the following before choosing workflows. Use `unknown` when the conversation does not establish a value; do not infer it. Use `not_applicable` only with a short reason.

- **Jurisdictions by role:** EU/common; residence, work, intended-residence, deciding, representing, challenged-authority and document-issuing Member State roles; applicant-country application or mission context and its destination state; any other national-law jurisdiction. Keep roles distinct even when they have the same country. Follow C3's typed-geography contract.
- **Proceedings:** list each separate visa, residence, border, appeal, conduct complaint, administrative complaint, file-access and data-access proceeding that is implicated. Preserve the applicant's claimed category separately from the authority's classification.
- **Legal questions:** state each material issue as a neutral question, separating EU/common law, national law or procedure, local operations, evidence, deadlines, authority competence, remedies and factual disputes as applicable.
- **Procedural stage:** for each proceeding, distinguish inquiry, appointment, attempted submission, formal lodging, decision, notification, appeal, complaint, access request and closure. Keep disputed or unsupported stage claims open under C27.
- **Urgency:** identify known deadline or evidence-loss risk and its basis; otherwise say `no urgent risk identified` or `urgency unknown`. Give a useful, appropriately qualified urgent step without waiting for non-urgent research.
- **Requested output:** identify whether the person asks for an explanation, issue assessment, source check, deadline/remedy route, evidence plan, draft, comparison or another concrete deliverable.

For an applicant matter, read C27 and use its atomic `check-registry.json` to select relevant checks. Do not duplicate its check catalogue or run all 301 checks by default. A check's absence from the relevant set does not establish legal inapplicability.

## 2. Build an execution plan

Separate **required**, **conditional**, and **not selected** work. For every selected operation, state its trigger, source/engine owner, expected evidence and whether it can run in the ordinary consultation lane.

When a country module is selected, run C3's existing pair-level module-conformance check against its manifest/export with `scripts/module_conformance.py`. This checks module identity, contract/profile, supported roles and declared destination profiles; it does not match the consultation's case geography to a module request. Use `case_controller.py` for typed-geography-to-module-request matching only through an approved input boundary. Never send a real applicant record to a synthetic case controller; when no approved case-level check is available, record it as unavailable and do not substitute a second deterministic routing implementation.

### Required for substantive applicant guidance

- **C23 read-only guidance** and **C27 multi-proceeding/completeness reconciliation**. Read the relevant references and keep each proceeding and stage distinct.
- **A model-led attack-angle screen** for every substantive ordinary applicant consultation, including when the user has not alleged an adverse act. Consider only factually indicated candidates in the core catalogue and relevant, C3-conformant country-module records; record that no angle was indicated only after screening the available facts and source scope. This is a review screen, not a finding of illegality, misconduct, motive or remedy entitlement. Do not claim that the C5d script ran on a real case. Keep this screen distinct from C27's adapted-stratagem checks; select those registry checks separately when indicated.
- The requested output and the compact execution/coverage record required below.

### Conditional analysis and research

Select only workflows triggered by the classification:

| Trigger | Workflow to route to |
| --- | --- |
| Facts about EU-citizen movement, family relationship, destination or cross-border topology affect the governing regime | C5a topology/applicability review; EU/common source owner and relevant Member-State roles |
| Competing rules, hierarchy, Charter scope or legal principles affect an issue | C5b hierarchy/principles review; each source owner remains attached to its own rule |
| Evidence restrictions, exact deadlines, authority powers or remedy routes matter | C5c evidence/deadline/authority-route review; route each national issue to the correct Member-State owner |
| New facts or corrected records may change an earlier answer | C24 fact-rule revision and affected C27 checks |
| A refusal, disputed authority position, separate grievance, disclosure history or evidence-preservation need is present | C25 grievance and evidence-acquisition review; distinguish invoked from hypothetical authority grounds |
| A material legal/procedural question depends on current, multiple, disputed or incomplete sources | `references/research-control.md`; create owner-specific tasks at the appropriate depth and validate any plan/bundle with the existing `scripts/research_gate.py` |
| Material source gaps affect issue-level or overall coverage | Add an owner-specific record in `references/contracts/issue-source-preflight.schema.json` and bind it to the existing plan/bundle. A human-reviewed official link may satisfy its source class within its declared scope without library registration or a local copy; keep missing, stale, unreviewed, secondary-only, or out-of-scope sources visible. See `references/issue-source-preflight.md`. |
| The issue depends on local application, mission, VAC or document-acquisition operations | Türkiye applicant-country source owner only when that role/destination matches; otherwise identify the responsible owner or leave the source gap open |
| The issue depends on Swedish law, Swedish administrative procedure, appeals or Swedish authority powers | Sweden Member-State source owner for the applicable C3 role |
| Another national-law question is material | Use the exact registered national pack when available; otherwise review the responsible government's official page and record it under `unregistered:<CC>` as an `official_reference`. Library registration and a local copy are not prerequisites for research; see research control. |

Use `eudirective-source-library` to locate bundled source records and publisher details. For current-law questions, prefer the latest responsible-government consolidation; if no usable consolidation exists, use the closest government-published text and state its cutoff and limits. A human-reviewed official link is enough for research without local registration, capture or hash. The source-library snapshot is not a live source check.

The C5a-C5d scripts and C6/C7/C17/C21 controller tools retain their documented input limits. For real consultations, perform the applicable reasoning and attack-angle screen model-led in the conversation; do not represent that as scripted execution. C5e/C5f synthetic suggestion and ranking workflows are not ordinary real-case consultation engines. Route a request for concrete next steps through C23/C25 and verify source support instead.

## 3. Check execution and preserve evidence gaps

For every selected C27 check, record the shared C27 fields and preserve their exact values: `check_id`, `status`, `method`, `reason`, `evidence_refs`, and `source_refs` (plus `scope_exclusion` when applicable). Use only C27's statuses `assessed`, `partial`, `not_checked`, `blocked`, `not_applicable`, and `unavailable`, and methods `model_review`, `source_review`, and `none`. An assessed or partial row needs the corresponding method and a traceable evidence or source reference; a not-applicable row needs its specific scope reason and trace. Do not relabel these statuses as engine execution results.

For every C27 check or operation recorded as `partial`, explicitly identify what is missing, such as a fact, document, current source, review, retrieval, or execution step, and explain how that gap limits the assessment. A bare label such as “unresolved” or “incomplete” is not enough. If the available record does not identify the exact missing item, say that the missing item is unknown and do not imply that the partial item is fully assessed. The overall coverage summary must name material outstanding checks or operations and their effect.

For each required or triggered engine, validator, or research-retrieval operation, record its own operation ID, applicability, execution status, output/evidence reference, and reason or next step. Use the route operation vocabulary: `completed`, `partial`, `not_checked`, `blocked`, `unavailable`, or `not_applicable`. Cite actual output or retrieval evidence only when the operation ran. If it did not run, state why and what remains unresolved. An unavailable required operation remains open for completeness purposes even when its reason is recorded.

Do not mark an operation complete because its skill, engine or catalogue was merely read or named. Keep model-led consideration, reviewed source text, deterministic validator output and synthetic script execution as separate evidence types. Use the C27 registry for check IDs/status semantics and `research_gate.py` for research artifact structure and coverage; do not create a parallel completeness registry or research validator. These validators do not establish source authenticity, legal entailment, semantic correctness or host enforcement.

## 4. Gate completeness claims

Do not call an assessment **comprehensive** while any required check, triggered conditional workflow or material research task remains unperformed, partial, stale, blocked, conflicting or unavailable. Use `partial`, `preliminary` or another accurate scope label, name the outstanding items and explain their effect. Do not treat the full C27 registry as a universal checklist: comprehensiveness is measured against the checks selected as relevant for this classified matter, with supportable non-applicability decisions.

Only label coverage `comprehensive` when every required and triggered check has acceptable evidence or a reasoned C27-compatible not-applicable status, and any research coverage is complete under its existing validator and review rules. Comprehensive coverage still does not establish a legal outcome, expert review, source authenticity or guaranteed result.

## Mandatory C27 status dashboard

Before substantive guidance in every substantive applicant consultation,
present a readable dashboard grouped by proceeding. On the first response,
preserve the existing notice/version order: required disclaimer first, any
applicable licensing note next, skill-version line after the notices, then the
dashboard. On later substantive replies, put the dashboard before guidance
while preserving the once-per-conversation disclaimer and skill-version rules.

### Compact view by default; expanded audit when useful

Use the compact view by default, especially for focused questions. Use the
expanded audit when requested, when several proceedings or open checks make a
short display misleading, or when the user asks for a route/evidence audit.
Keep all relevant checks, operations, module use, material gaps, and urgency in
either view; do not list all 301 checks by default. Do not repeat unchanged
background when a concise current-chat update is enough.

Use ordinary Markdown headings and bullets. Never render this dashboard as a
Markdown table, pipe-delimited rows, empty cells, or a fenced text block. Keep
one concise issue per bullet and separate the status, finding, check IDs, and
missing/effect into short labeled lines. Put the readable issue before the
technical IDs. Avoid long prose bullets and do not place multiple unrelated
issues in one row.

At the top, give a short coverage line with the overall label and the main
open issue, followed by one brief urgency line. Name any known deadline or
evidence-loss risk and the immediate qualified action, or say `urgency unknown`
/ `no urgent risk identified` when supported. Do not infer that no risk exists
just because a date or notice is missing. A short scope/request line may
identify the proceedings, jurisdictions by role, and requested output without
repeating sensitive facts.

### C27 checks, grouped by proceeding

Use a short heading for each implicated proceeding, with a privacy-minimised
label where helpful. Use “Matter-wide checks” for checks not tied to one
proceeding. Under each heading, give one compact issue item per relevant
selected, required, or triggered C27 check. Group IDs only when their proceeding
scope, status, method, and readable finding are the same. Keep separate items
when any of those differ; do not merge the same check ID across distinct
proceedings.

In the compact view, present each item in this order:

- plain-language issue heading
- **Status:** readable status and method only
- **Finding:** one short sentence on what the review established or did not
  establish
- **Checks:** every exact registry check ID for that item, on its own line
- **Missing / effect:** for every partly reviewed item, name the missing fact,
  document, source, review, or step and what it prevents assessing

Use readable labels such as “Reviewed,” “Partly reviewed,” “Not checked,”
“Blocked,” “Unavailable,” or “Not applicable,” with a plain-language reason
for open or out-of-scope items. Describe the method as “model review,” “source
review,” or “no method recorded.” Do not show machine-readable status or method
values in the compact view, including in parentheses. Keep exact values for the
expanded audit only.

For reviewed items, keep the finding and any material evidence/source
reference concise. For partly reviewed items, explicitly name what is missing
and how that gap limits the assessment; “unresolved” or “incomplete” alone is
insufficient. For every other open item, give its reason or next step and its
effect. For an item outside scope, preserve the reason in plain language in the
compact view. In the expanded audit, add each full record: exact `scope_ref`,
`check_id`, `status`, `method`, `scope_exclusion` when present,
`evidence_refs`, `source_refs`, and recorded `reason`. Do not omit a relevant
open item to make the display shorter.

### Execution board: review, retrieval, and tools

After C27 checks, show required or triggered work in an **Execution board**
with separate groups such as **Review and screening**, **Source retrieval**,
and **Validators and scripts**. Give every required or triggered engine,
validator, and retrieval operation its own visually separated card. Start the
card with a plain-language name and readable status: “Performed,” “Partly
performed,” “Not run,” “Blocked,” “Unavailable,” or “Not applicable.” Put its
applicability, result/output or evidence, exact `operation_id`, and any open
reason/effect on short, separately labeled lines. Give each card an **Applies
to**, **Status**, **Result**, **Evidence**, and **Operation** field as
applicable; use **Missing / effect** or **Reason / effect** for open work.
Do not combine different operations, jurisdictions, or execution states into
one paragraph or bullet.

In the compact view, retain the exact `operation_id` and any output/evidence
reference, but express applicability and result in plain language. Explain the
reason and effect for every open operation. For a partly performed operation,
name the missing step/evidence and its effect; if unknown, say so. An
unavailable required operation remains open for completeness even when its
reason is recorded. If no operation was selected, say so plainly. In the
expanded audit, include exact `operation_id`, `applicability`, operation
`status`, output/evidence reference, and recorded reason.

Use headings and short field lines to create a board-like display. Do not use
tables, pipe rows, or code fences. A model-led review may appear as a review
card with its status, method, workflow, result, and evidence; do not invent an
`operation_id` for model reasoning or imply that an engine or validator ran.
Show the required model-led attack-angle screen as its own review card, apart
from C27 stratagem checks and script execution. Keep module use in its own
group after the execution cards; module availability, source consultation, and
C3 conformance are not execution results.

Do not infer execution from model-led consideration, source content being
reviewed, a skill being read, or model reasoning. Keep these separate from
deterministic validator output and synthetic script execution. When C27/C6/C21
scripts cannot accept a real applicant narrative, do not run them; state that
boundary and its effect if the operation is required. Never claim output
without actual execution or retrieval.

### Module use in this answer and current chat

Include only modules relevant under C3's existing family, jurisdiction, role,
and destination rules. For each relevant module, report its C3 role and
separately distinguish:

- whether its source content was reviewed or relied on in this answer
- whether it was used earlier in this chat, and whether the current answer
  relies on that earlier review
- availability
- C3 conformance and its evidence, or that conformance was not checked

Use one short card per relevant module under **Module use in this answer and
current chat**, with the module name and C3 role followed by separate lines for
use in this answer/current chat, availability, and conformance. Say “consulted”
only when source content was actually reviewed. A module that is available but
whose source was not consulted is not “used.” If relevant but unused, state why
and the effect on the assessment. Do not infer case-level geographic matching
from pair-level conformance or infer module use from a skill being named,
loaded, or available. Separate module source consultation from C3 validator/controller execution: reading or relying on module content does not mean its conformance validator or case controller ran. Record any such execution only in the **Execution board**. If no module is relevant, state the brief C3-based reason.

Refresh this section when a C3-relevant variable changes, including
jurisdiction roles, proceeding/stage, material routing facts, module
availability/conformance, source consultation, or execution. Track use only
within the current conversation. If nothing changed, a concise no-change update
is acceptable only when it still makes cumulative current-chat use clear.

### Overall coverage and assurance

End with one short **Overall coverage** statement using `comprehensive`,
`partial`, or `preliminary` as appropriate. Name all material outstanding
checks or operations and explain their effect. Do not call the assessment
comprehensive while required checks, triggered conditional work, or material
research remain unperformed, partial, stale, blocked, conflicting, or
unavailable. Comprehensiveness is measured against checks selected as relevant
for this matter, not the full registry; supportable C27-compatible
`not_applicable` decisions may close a check.

Always end the dashboard with this assurance statement: **This is a model-led,
self-reported status display. No host-validated release gate is integrated,
and the dashboard does not prevent answer release.** A host/controller must
separately validate the route and bind its result to the exact answer before
release for non-bypassable enforcement; this plugin has no such integration.

The following short-form pattern shows the required Markdown structure; replace
all placeholders with the actual recorded values:

#### [Proceeding]

- **[Plain-language issue]**
  - **Status:** [Readable status] · [readable method].
  - **Finding:** [Short result in ordinary language.]
  - **Checks:** `[exact.check_id]`; `[exact.check_id]`.
  - **Missing / effect:** [Specific missing item] prevents [specific part of
    the assessment].

- **[Plain-language operation] — Not run.** [Reason and effect.] Operation
  `[operation_id]`; output/evidence `[reference or none]`.

**Overall coverage — partial.** [Name material open work and its effect.]

**Assurance:** This is a model-led, self-reported status display. No
host-validated release gate is integrated, and the dashboard does not prevent
answer release.

## Conversation record

Keep the dashboard with a user-readable route summary. Put jurisdictions by
role, implicated proceedings and stages, material questions, urgency, and
requested output in the opening scope lines. Show required/triggered workflows,
research tasks, review, retrieval, tools, and module status in the grouped
board described above; do not compress them into a single “Execution and
coverage” paragraph. Report the attack-angle screen as a model-led review,
separately from C27 stratagem checks and any scripted execution. Do not repeat
sensitive facts or expose private chain-of-thought. This is a conversation aid,
not a persisted case file or a host-validated release receipt.

## Optional local receipt check

Where a host can run local package scripts, it may serialize a privacy-minimised
receipt using `contracts/consultation-route-receipt.schema.json` and call
`scripts/consultation_route_gate.py`. The receipt contains classification states,
workflow/check identifiers, and generated opaque references only. Keep actual
case facts in the conversation. The gate resolves references against the
receipt's evidence index, runs the existing C3 module-pair and research
validators, and checks C27 records through C27's shared validation logic. The
receipt also includes constrained relative artifact paths and digests for the
validator inputs; do not put case facts in those artifacts. Attached issue-source
preflight gaps are included in the route coverage result. Self-reported
conversation/source records are not authenticated, omitted
conditionals cannot be discovered by the gate, and the host must call the gate
and enforce its result before release. See `references/consultation-route-gate.md`.
