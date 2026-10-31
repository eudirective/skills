# Consultation parent controller

This contract coordinates intake, issue discovery, research, C24 assessment, C25 strategy, final review and reporting. It reuses the existing C3 role and module contracts, C27 issue selector and completeness registry, and `research_gate.py`. It does not copy their check definitions or claim that a syntactically valid record proves legal correctness.

## Two execution profiles

### Portable ChatGPT consultation

Ordinary applicant guidance remains model-led and read-only in chat. Follow `consultation-quality-workflow.md`, the applicable C23/C24/C25/C27 references, and `research-control.md`. Record only work actually performed in the answer and board. Do not claim that the Python controller, C27 engine, or research validator ran unless an observed result exists. The skill instructions cannot intercept or block a ChatGPT response.

### Tool-controlled synthetic workflow

Use `scripts/consultation_controller.py` only with fictional or sufficiently abstract, non-identifying records. It validates structured state transitions and can invoke the existing route selector, research validator, source preflight, C3 module-pair validator, and C27 receipt validator. It does not consume applicant narratives, documents, or correspondence; retrieve legal sources; determine legal meaning; or provide host-level release enforcement. The controller's privacy screen catches some obvious identifiers but is not an anonymisation or data-loss-prevention system. Do not send real case histories to it.

The local commands are:

- `python scripts/consultation_controller.py init --state <state.json> --consultation-id <synthetic-id> [--mode limited|full]`
- `python scripts/consultation_controller.py apply --state <state.json> --event <synthetic-event.json>`
- `python scripts/consultation_controller.py validate --state <state.json>`
- `python scripts/consultation_controller.py summary --state <state.json>`

An event is one allowlisted controller transition. Validator inputs must be separate files referenced by the event and must satisfy the relevant existing contract. The private `fm-maintenance` suite contains regression tests; those tests and evaluation records are not distributed in the applicant-facing plugin.

## State and progression

The state schema is `contracts/consultation-controller-state.schema.json`. It separates selection, assessment, source evidence, validator execution, C24 finding status, C25 strategy disposition, claim treatment and release eligibility.

| Stage | Required record | Progress condition |
| --- | --- | --- |
| Intake | Actor roles, jurisdiction by role, proceedings, procedural stage, signals, objective and urgency | Material facts are identified or recorded as unresolved |
| Discovery | Issues linked to proceedings and routes; C27 checks derived from the registered selector | Every route selected by the recorded proceeding signals has an issue record; selected checks remain distinct from assessed checks |
| Research | One owner, jurisdiction, mode, mode rationale and acceptance criteria per task; observed attempt evidence; evidence and counterevidence; nested plan and bundle where used | A task can be complete only with recorded progress, a passing `research_gate.py` result and an owner/jurisdiction consistent with the existing routing and country-module registries; the child plan must match the parent mode |
| Assessment | C24 finding linked to relevant facts, source reviews, research findings, exceptions, counterevidence and uncertainty | Unsupported material findings cannot support an established claim; supported claims require completed linked research |
| Strategy | C25 disposition for each applicable material issue, including recommendation, conditional recommendation, no action or deferral | A recommendation links to a supported or conditional finding and states its urgency, rationale and any qualification |
| Final review | Claims linked to material issues, findings and evidence; explicit established, qualified or withheld treatment | No current established claim may rely on unsupported, stale or incomplete work; every material issue receives a disposition |
| Reporting | Full or Limited mode, recorded gate statuses, open obligations and evidence-backed board | The board describes observed state and names material missing work; it does not infer completion from intent |

New research findings can add issues or proceedings and reopen discovery. A changed dependency marks only its downstream records stale and reopens the earliest affected stage. A stale record remains in history but cannot support a current established claim.

Full and Limited are separate release modes, not execution metrics. Limited release can preserve supported advice while required work remains open only when affected claims are qualified or withheld. It must not imply that unresolved questions were assessed or legally decided.

## Ownership and module use

The selected route's `source_owner_ids` come from `consultation-issue-routing.json`; country and operational modules come from `national-source-routing.json`. A research task may not choose an owner absent from every linked issue's selected routes. A registered national source-library owner uses the exact country plugin ID, `national_source` role, jurisdiction and `source_pack_sha256`; the parent binds these to the child plan while routing through the existing `member_state_law` owner. Child evidence records package provenance and caller-declared `source_access.channel` / `source_access.status` separately from text inspection; neither status is authenticated. A manifest-listed source can therefore be present in the registered pack while inaccessible through the runtime, with a separately reviewed official-publisher `official_reference` recorded as fallback. An `unregistered:<CC>` owner is allowed only when the country registry has no national source pack for that code; supporting or contradicting evidence must then be a reviewed `official_reference`. `member_state_law` still maps to the proceeding jurisdiction; `applicant_country_operations` still maps to the application-location country and a registered applicant-country operational module. Local package identity is not proof of runtime exposure or source inspection. If the responsible jurisdiction or module is unavailable, keep the task unresolved or blocked. Do not treat a module's presence, a route assignment, or a successful C3 check as proof that its law or sources were consulted.

The synthetic controller records the selected `quick`, `case` or `deep` mode and an observed reason for that choice. Its attempt ceilings are one, two and three respectively. Each attempt links to observed source-review or other evidence and is classified as progress, no progress or blocked. Progress must carry a new content digest; duplicate progress is rejected. Two consecutive no-progress attempts, an explicit block, or an exhausted attempt ceiling blocks the task. A blocked task cannot be reopened through a status edit. These limits govern controller state only; they do not replace the mode-specific research and acceptance criteria in `research-control.md`.

A blocked required research task stays visibly blocked with its reason and evidence. The parent may advance the research gate as `conditional` to preserve work on independent questions. This does not close or satisfy the blocked task: full release remains unavailable, and limited release requires an explicit qualified or withheld disposition for every affected material issue. A dependent task cannot proceed while its dependency is blocked.

EU/common legal workflow remains in this core. National legal sources and law remain in the matching country plugin. Mission and applicant-country operational procedure remains with its registered operational module. C3 compatibility validation records a structural result only; current official-source review and legal assessment remain separate.

## Evidence, claims and limitations

The controller records identifiers and evidence references; it does not authenticate the person or authority behind a record. `source_review` means a review was recorded, not that the publisher, currency, interpretation or legal proposition was independently verified by the script. A passing nested research validator verifies structure and coverage, not source authenticity, legal entailment or the truth of the finding.

Only a result emitted by the named validator counts as execution evidence for that operation. A selected check, pending task, skill availability, generated plan, or state transition is not evidence that a source was retrieved or reviewed. Missing or inaccessible work must be recorded with its status, reason and effect. The controller is a local synthetic workflow aid, not an ordinary ChatGPT runtime hook or a non-bypassable answer-release gate.
