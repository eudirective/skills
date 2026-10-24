# Release and version policy

## Maintenance completion and handback policy

For new maintenance work, finish all work and applicable automated checks that can be run in the available environment. If a live plugin runtime is unavailable, record behavioral evaluation as `not_feasible_current_runtime`, keep behavior unverified, and do not create a user-run test, recurring follow-up, approval request, or release blocker solely because that runtime is unavailable. The private `fm-maintenance` package's `records/MAINTENANCE_STATUS.json` is the canonical record of accepted limitations and actionable blockers; historical plans and reports below remain evidence, not current task lists.

Before asking the user to intervene, classify the situation: complete agent-executable work; diagnose and retry recoverable failures; ask one focused question only for an indispensable user decision or authorization; record unavailable external capabilities without manufacturing a task; keep material defects and genuine safety blockers visible with an impact and resolution path; and label optional improvements as optional. Do not weaken legal, privacy, security, authorization, or justified release controls. Automated tests remain mandatory where applicable, and failures must be resolved or recorded as actionable blockers.

This policy applies to new work; entries below preserve the status and evidence recorded when each earlier change was made.


# Plugin v0.59.1 / core v0.58.1 module-note mirror and C6/C7 fixture repair

The C17 module-note consumers now follow the public-data `module-notes/{sweden,turkiye}` layout. The mirror workflow copies that tree into the bundled source library and stamps its separate Git tree fingerprint; the once-per-chat version check compares both the source-library and module-note trees. Sweden and Türkiye module guidance point to the same layout.

The C6 reviewer fixtures were refreshed against the current deterministic C5D and C5E output, then re-enrolled in the code-pinned C7 trust policy. The C7 maintenance regression now opts into the validator's narrow internal issue-code allowance when reading a generated issue index. No external or personal inputs were added.

The private fm-maintenance regression suite passed all 41 scripts after these changes. This is local deterministic testing, not live ChatGPT behavior testing or independent legal review. The live check remains documented in `references/consultation-dashboard-live-test-plan.md` and was not run.

Core advances from `0.58.0` to `0.58.1`; plugin advances from `0.59.0` to `0.59.1`. Sweden, Türkiye, and source-library skill versions advance by one patch.

# Plugin v0.59.0 / core v0.58.0 typed administrative outcomes and remedy routing

Receipt 0.6.0 now keeps procedure type, source-attributed administrative
outcome, and later post-issuance events distinct from generic stage. Routing
separates Visa Code Articles 18, 19 and 32, provider pre-screening, disputed
lodgement, and post-issuance events. Event-specific national remedy and
service-deadline checks are selected for cancellation, revocation, or
annulment; they are not inherited by expiry. The existing dashboard shows the
recorded outcome/event, whether its record is usable for routing, and which
routes are included or unresolved. The local controlled-release command
accepts receipts 0.5.0 and 0.6.0. This adds no ChatGPT host release hook.

The live behavior check for typed outcome cards is documented in
`references/consultation-dashboard-live-test-plan.md` and remains deferred.
Focused local regressions passed: 120 tests across the C27 case-state,
outcome-routing, route-gate, dashboard-format, and topic-review scripts.
PyMuPDF-dependent checks were not run because PyMuPDF is not installed in
this maintenance environment. The plugin package is not locally installed
as part of this maintenance.

Core advances from `0.57.2` to `0.58.0`; plugin advances from `0.58.2` to
`0.59.0`.

# Plugin v0.56.0 / core v0.55.0 source-origin dashboard accounting

The consultation board now reports distinct source records identified in the
current response and across the chat, matches to records in the plugin's
bundled source library, and sources explicitly identified through web search.
The receipt adds response and conversation discovery methods in schema v0.3.0.
Library membership and discovery are separate counts and can overlap. Older
receipts without discovery fields show search provenance as unknown rather than
assuming that an external official source came from search. All counts remain
model-reported; no host-authenticated retrieval or release gate was added.

The live ChatGPT display review is deferred. Use the source-accounting case in
`references/consultation-dashboard-live-test-plan.md` after the package is
installed. Local regression tests and live consultation tests were not run in
this maintenance session.

Core advances from `0.54.0` to `0.55.0`; plugin advances from `0.55.0` to
`0.56.0`.

# Plugin v0.55.0 / core v0.54.0 native Markdown consultation board

The full consultation dashboard is presented directly in the assistant's
ordinary Markdown response. Its display rules use readable status headings
and separated cards instead of wide tables, pipe-delimited rows, raw HTML, or
fenced code. Each operation and selected C27 check keeps its plain-language
status, evidence, and any missing item/effect. Module use is grouped by this
answer, earlier chat, and relevant modules not used. Execution claims remain
separate from model-led review. No MCP tool, custom UI, or hosted renderer was
added; the skill cannot authenticate its own reports or enforce answer
release. Core advances from `0.53.3` to `0.54.0`; plugin advances from
`0.54.3` to `0.55.0`.

Live ChatGPT display review is deferred by design. Follow
`references/consultation-dashboard-live-test-plan.md` after the package is
installed; do not require live consultation tests during maintenance sessions.

## Plugin v0.54.3 / core v0.53.3 full dashboard and receipt-validation binding

Compatible presentation and controller hardening. Replace the compact-by-
default dashboard with a full board after every explicit invocation and any
material continuation change. The board now lists every declared classification,
operation, C27 check, issue, validator result, source-ledger row, and module-use
entry, without truncation. The route gate emits it only after validating the
declared receipt and includes a validation record bound to the exact receipt
SHA-256. The local release binding now includes the validation-record digest in
addition to the receipt and answer digests. The receipt can mark
`invocation.material_change=true` to require a fresh board on a continuation.

The plugin still has no ChatGPT host release hook; hosted responses cannot be
made non-bypassable by skill instructions or these local scripts. The hosted
full-board acceptance plan remains unexecuted and is not a local maintenance
prerequisite. Core advances from `0.53.2` to `0.53.3`; plugin advances from
`0.54.2` to `0.54.3`.

## Plugin v0.54.2 / core v0.53.2 source taxonomy and provenance correction

The consultation dashboard now maps known mission directories and retrieval
documentation to reference categories, classifies canonical national-act,
case-law and Commission-notice records by type, and keeps unknown source types
out of legal-text totals as references/unclassified. Independently expected
category cases cover canonical library IDs, including prior misclassifications.
The portable local route gate rejects `runtime_recorded` source states: a
generic artifact hash does not prove a retrieval, and this package has no
host-authenticated source-read event contract. Counts remain model-reported or
unknown. The bundled source library is unchanged. Core advances from `0.53.1`
to `0.53.2`; plugin advances from `0.54.1` to `0.54.2`.

The plugin-level hosted invocation/rendering behavior remains unverified. Keep
the six-case live test plan for post-install review; do not require hosted tests
during local maintenance sessions.

## Plugin v0.54.1 / core v0.53.1 source-catalogue reconciliation repair

Compatible patch to consultation accounting. Owner-matched national manifests
now refine retrieval-index acceptance states, and the EU guidance manifest is
owned by EU core rather than a synthetic `References` jurisdiction. When
source type is absent from an established manifest, a deterministic title
fallback classifies recognized official guidance and procedures; unknown
titles remain references and are not counted as legal texts. The source
library itself is unchanged. Core advances from `0.53.0` to `0.53.1`; plugin
advances from `0.54.0` to `0.54.1`.

Require regression coverage for every existing source-manifest acceptance
state represented in the catalog, EU guidance ownership, and title-fallback
classification. Hosted ChatGPT checks remain documented in the dashboard live
test plan and are not part of the offline suite.

## Plugin v0.54.0 / core v0.53.0 invocation-aware consultation dashboard

The compatible core minor adds explicit-invocation dashboard requirements and
a source-use ledger resolved against the existing source retrieval index and
manifests. The compact board reports response and conversation counts, source
groups and pinpoints, outstanding issues, execution status, and relevant module
use now versus earlier in the chat. The receipt validator rejects duplicate
logical texts, unsupported library identities/categories, inconsistent issue
summaries and unverified C3 conformance claims. The local release wrapper binds
the rendered dashboard to the exact answer bytes, but the plugin does not
invoke it automatically and there is no host release gate. Core advances from
`0.52.0` to `0.53.0`; plugin advances from `0.53.0` to `0.54.0`.

Offline validation includes dashboard unit/receipt cases and existing route
gate tests. The hosted ChatGPT invocation/rendering checks are documented in
`references/consultation-dashboard-live-test-plan.md` and are not executed in
the local development session.

## Plugin v0.53.0 / core v0.52.0 issue-led routing and concise response default

This compatible core minor adds a deterministic selector from declared,
privacy-minimised issue signals to the existing C27 check registry and source
owners, plus a five-stage model-led consultation workflow and issue disposition
contract. The default answer now leads with the requested guidance and a short
coverage summary; the detailed issue/C27/operation/module board remains
available for a requested audit. The optional 0.1 route receipt can include
issue references and signal IDs; the existing gate checks required routed C27
checks and keeps source/fact gaps open while accepting older receipts without
the new field. Synthetic scripts remain restricted to abstract fixtures, and
the route gate is still not host-integrated. The enclosing plugin advances
from `0.52.2` to `0.53.0`.

Local verification against candidate source commit `f7ca9f9a66f43dfbc2ea9873bad72f45d3996c16` passed version-manifest verification, Python compilation, the C27 checklist, issue-selection tests (15/15), route-gate tests (16/16), evaluation-aggregator tests (8/8), and dashboard/consultation-coverage checks. The private all-suites regression runner passed 31/36 scripts. Its five local failures were: a nested Node process denied with `EPERM`; three PDF-related tests without locally installed PyMuPDF; and the C17 remedy test, which requires Sweden module notes absent from the selected package. These failures and their exact output are recorded in the private maintenance evidence. No remote CI run was made.

All 36 consultation-assurance records remain `not_executed`; there are no actual baseline or candidate model responses, independent grades, or behavioral metrics. Therefore this release is **implementation verified; consultation behavior not verified**. See `maintenance/consultation-quality/candidate-verification.md` for the requirement status and evidence boundaries.

## Plugin v0.51.3 / core v0.50.3 board-style execution summary

Substantive consultation dashboards now present work in grouped, separated
cards for review and screening, source retrieval, validators/scripts, and
module use. Each triggered operation shows a readable status, its result or
evidence, exact operation ID, and the reason/effect for any open work. The
format keeps model-led review, retrieval, validator execution, and module
consultation distinct. Core advances from `0.50.2` to `0.50.3`; plugin advances
from `0.51.2` to `0.51.3`. No local tests were run; live plugin rendering was
not verified.

## Plugin v0.51.2 / core v0.50.2 readable consultation dashboard

This compatible patch defines a compact Markdown dashboard with a visible
coverage/urgency summary, proceeding headings, separately labeled findings
and check IDs, explicit missing/effect lines, and compact operation and module
records. Compact statuses and methods use plain language; exact registry values
appear only in the expanded audit. Tables, pipe-delimited rows, and fenced
dashboard blocks are expressly excluded. C27 status/method semantics, relevant
check coverage, current-chat module tracking, and the host-enforcement
limitation remain unchanged. Core
advances from `0.50.1` to `0.50.2`; plugin advances from `0.51.1` to `0.51.2`.
No tests or evaluations were run for this change by instruction.

## Plugin v0.51.1 / core v0.50.1 GitHub update reminder

The first-invocation package-version check now gives users an actionable
reminder when installed plugin or skill versions differ from GitHub. It shows
the affected installed/GitHub values, says to check for an available update,
and explains that installation must be done through the user's existing
plugin source or manager. A source-library fingerprint mismatch alone is not
reported as proof that a plugin update is available. Failed checks say that
availability could not be confirmed. The check remains read-only and never
downloads or installs an update. Core advances from `0.50.0` to `0.50.1`;
plugin advances from `0.51.0` to `0.51.1`.

## Plugin v0.51.0 / core v0.50.0 compact consultation dashboard and evaluation evidence records

This compatible core minor makes the compact, readable status display the
default while retaining an expanded audit view. It keeps relevant C27 check
IDs and statuses visible, names missing items for every partial result, and
preserves module use in the current answer/current chat, urgency, source gaps,
the first-response disclaimer/licensing/version order, and the explicit
absence of host release enforcement. It also adds a fictional evaluation
record contract and local importer checker that distinguish not executed,
recorded/ungraded, independently graded, and blocked evidence. The checker
does not execute a model, authenticate transcripts or graders, or establish
behavioral performance. Core advances from `0.49.0` to `0.50.0`; plugin
advances from `0.50.0` to `0.51.0`. No real transcripts were captured and no
behavioral pass rate is claimed.

## v0.50.0 current-chat module-use dashboard

This compatible core minor adds a concise module-use section to each
substantive applicant dashboard. It distinguishes modules consulted or relied
on in the current answer, modules used earlier in this chat but not this
answer, and relevant modules not used with the reason and effect. The
section refreshes when C3-relevant jurisdiction roles, proceedings, material
routing facts, module availability/conformance, source consultation, or
execution state changes; otherwise it may give a concise no-change update
that keeps cumulative current-chat use clear. It applies existing C3 matching
semantics and separates module use from loading, conformance, and controller
execution. It does not retain status across chats or change synthetic-input
limits, validators, or host release enforcement. Core advances from `0.48.1`
to `0.49.0`; plugin advances from `0.49.1` to `0.50.0`. No tests or
evaluations were run for this change by instruction.

## v0.49.1 readable C27 dashboard and partial-status detail

This compatible patch presents the C27 dashboard as proceeding-grouped
Markdown bullets instead of wide tables or a fenced text template. Each item
leads with a plain-language issue and readable status/method, then preserves
the exact recorded scope/check IDs, status/method values, evidence/source
references and reason in a visible Record line. Engine, validator and source
retrieval operations have a separate readable execution account. Every
`partial` check or operation must name what is missing and how it limits the
assessment; the overall coverage statement names material outstanding work.
Existing disclaimer/version ordering, C27/C3/research semantics, synthetic
input boundaries and the explicit absence of host release validation remain
in force. Core advances from `0.48.0` to `0.48.1`; plugin advances from
`0.49.0` to `0.49.1`. No tests or evaluations were run for this change by
instruction.

## v0.49.0 C27 consultation status dashboard

This compatible core minor makes a standardized C27 status dashboard mandatory
before substantive applicant guidance. It displays only relevant selected
checks using their proceeding scope, recorded IDs, statuses, methods,
evidence/source references, and reasons or next steps; a separate ledger
reports execution status and evidence for required or triggered engine,
validator, and retrieval operations. It preserves C27's existing registry and
shared status/method validation, C3 and research validators, and the
synthetic-only input boundary.
The dashboard distinguishes self-reported model/source assessment from actual
tool execution. It is a skill-level presentation rule only: no host-validated
release gate is integrated, and the plugin does not guarantee that a dashboard
or any check is shown before answer release. Core advances from `0.47.1` to
`0.48.0`; plugin advances from `0.48.1` to `0.49.0`. No tests or evaluations
were run for this change by instruction.

## v0.48.1 personal-use licensing notice correction

This compatible patch removes licensing language from the default informational
disclaimer across the core, Sweden, Türkiye, and source-library skills. The
license/email reminder appears only when the prompt clearly indicates
non-personal use; clearly personal and ordinary or unspecified-use requests
explicitly omit it. One neutral clarification is permitted only when ambiguity
must be resolved to answer the request. The non-personal-use categories and
once-per-conversation disclaimer behavior are unchanged. The affected skill
versions advance to core `0.47.1`, Sweden `0.7.3`, Türkiye `0.6.3`, and
source-library `1.0.3`; the plugin advances from `0.48.0` to `0.48.1`.
README and plugin-catalog licensing terms remain general terms. No tests were
run for this change by instruction.

## v0.47.0 portable consultation route receipt gate

This compatible core minor adds a privacy-minimised route receipt contract and
local structural gate. It validates only the model-declared route, opaque
evidence-index references, local artifact digests, C3 module-pair conformance,
research-gate artifacts, and C27 check records using shared C27 validation
semantics. It cannot infer omitted conditional work, authenticate
self-reported evidence, match real-case geography to a module, or enforce
release; the host must call and enforce the gate. The enclosing plugin package
advances from `0.47.0` to `0.48.0`. No tests were run for this change by
instruction; static structure review does not establish runtime correctness.

## v0.46.0 ordinary-consultation routing addition

This compatible core minor adds a model-led routing layer for ordinary applicant consultations. It records task classification, execution planning, evidence/unavailability and coverage status; reuses C3 geography/role semantics, C27's atomic completeness registry and the existing `research_gate.py`; and requires an attack-angle screen for every substantive ordinary applicant consultation. It does not duplicate those contracts, run synthetic scripts on real case facts, change C3 `0.2.0` or controller protocol `0.3.0`, or provide host-enforced release validation. The enclosing plugin package advances from `0.46.1` to `0.47.0`. No live routing tests were run for this change.

## v0.45.0 evidence-gated research addition

This compatible core minor adds an opt-in, model-led source-research loop, `research-plan` and `research-evidence-bundle` schemas, and a local `research_gate.py` validator for cross-artifact integrity and claim/task coverage. It does not add a Python research controller, change legal-decision stages, or alter C3 contract `0.2.0`, controller protocol `0.3.0`, C6 run pins, C7 trust policy, or source-pack activation rules. The enclosing plugin package advances from `0.45.1` to `0.46.0`.

Keep the mode (`quick`/`case`/`deep`) independent from source ownership. Before any later runtime/controller integration, separately evaluate module routing, artifact privacy boundaries, task reopening, falsifier/counterevidence coverage, urgent provisional advice, and unresolved-source behavior. A schema pass is structural evidence only; it is not a semantic/legal accuracy or host-privacy pass.

- Patch: compatible bug fix, wording, tests or stricter validation that does not break documented valid inputs.
- Minor: compatible model/contract additions, new controller operations or new legal-engine modules.
- Major: breaking contract changes, changed skill-family ownership or widened trigger boundary that alters compatibility assumptions.

Before packaging: run the self-test, direct CLI smoke tests, quick_validate.py, lint_description.py and semantic review. Keep implicit invocation narrow until recorded real-prompt and integration evidence exists.

C3 is accepted at development contract `0.2.0`. Treat this as a frozen producer/consumer interface for MS0/applicant-country template work, but not as portfolio v1.0. Breaking changes before I3 require an explicit contract-version bump and migration evidence.

- C1 source-pack completion is a prerequisite for activating Member-State source work under the current program sequence. Do not use country-pack progress as evidence for core completeness.


## v0.6.0 source-text completion correction

C1 release readiness requires a verified usable representation for every required logical source. Byte-identical transport is not required. The release must state whether a representation is full bundled text or an identity/version-verified source note and preserve the quotation/pinpoint limitation.


For v0.8.x, a source may leave the C1 blocker list only when `source_text_gate.py` finds `bundled_text` with `authenticity_state=verified_official`. A provenance-free offline file is only a candidate. Offline promotion requires exact match to a digest already pinned in the trusted manifest; the digest must not be derived from the same untrusted import. Official fetches must remain on approved HTTPS hosts and use an explicit verification date.


## v0.10.0 pre-C3 hardening

Treat the direct-text/full-text distinction and the independent reverse source-support coverage baseline as compatibility-significant pre-C3 controls. Do not weaken either merely to make a producer export pass. C3 subsequently revised the provisional contract to 0.2.0 while preserving these guarantees.

## v0.11.0 C3 contract freeze

Freeze inter-skill contract `0.2.0`, conformance profile `0.2.0`, and controller protocol `0.3.0`. Preserve role-sensitive composition, typed geography/request consistency, applicant destination profiles, applicant destination-record/profile consistency, namespace ownership, global ID collision rejection, duplicate role-provider rejection, family-specific normative layers, explicit gap IDs, controlled-analysis reusable-record reference validation, reusable-non-case classification, and compatibility declarations. These controls are interface-significant and must not be weakened to accommodate a producer module.

## v0.12.0 C4 trust-control foundation

Keep the frozen C3 producer boundary at contract/profile `0.2.0` and controller protocol `0.3.0`; C4 introduces trust profile `0.1.0` as a compatible local control layer. Before release, require all C4 deterministic tests to pass, including private-data host gating, view minimisation, approval binding, no-blind-retry, revocation tombstones, dependency pins and current-state checkpoint validation. Do not advertise private-data, secure-deletion, trusted-identity or external-delivery guarantees until the deployment host independently demonstrates them.

## v0.12.1 C4 hardening gate

Require adversarial regressions showing that direct-identifier transform smuggling, malformed date strings, and invalid ISO temporal values fail closed before packaging. Keep trust profile `0.1.0` because this patch tightens implementation to the already-declared transform semantics rather than widening the contract.

## v0.13.0 C5a legal-engine gate

C5a is a compatible minor addition because it adds standalone candidate-producing engines and schemas without changing inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, or trust profile `0.1.0`. Before packaging, require regressions for role preservation, role-conflict blocking, private-data rejection, normalized EU-status gating, Directive/Visa/Schengen candidate coexistence, returnee/source-gap preservation, exact input binding, and source-hint/national ownership. Do not describe C5a as final legal applicability or controller-integrated analysis.


## v0.14.0 C5a adversarial repair gate

Treat 0.14.0 as a compatible minor hardening release: keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, and trust profile `0.1.0` unchanged. Before packaging, require regressions proving (1) unscoped family-member status fails closed rather than producing a false negative, (2) explicit applicant/relevant-Union-citizen actor scope can produce a family-member Directive review candidate, (3) `frontier_worker_context=false` cannot erase a structural residence/work difference, and (4) known jurisdiction aliases such as `SE` and `Sweden` canonicalize to one identity.


## v0.15.0 C5b release gate

Treat 0.15.0 as a compatible minor workflow/model addition. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, and trust profile `0.1.0` unchanged. Before packaging require deterministic regressions for unresolved lex-specialis overlap, Charter scope gating, source-backed principle requests, Article 41 boundary, non-binding soft-law handling, conformant case-relevant national rule binding, unknown/unrelated rule/module rejection, exact C5a chain binding, private-data rejection, and blocked-C5a non-upgrade.


## v0.16.0 C5c release gate

Treat 0.16.0 as a compatible minor workflow/model addition. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, C5b engine `0.1.0`, and trust profile `0.1.0` unchanged. Before packaging require deterministic regressions for dependency-scoped freedom-of-proof, proof-restriction source/rule binding, unknown restriction sources, exact calendar deadline arithmetic, suspension/extension blocking, business-day fail-closed behavior, inferred-date rejection, opaque inclusion rules, unknown deadline IDs, country-module authority competence preservation, core EU route competence boundaries, evidence-basis validation, exact upstream/private-data binding, replay of C5b-bound modules, and blocked-upstream non-upgrade.

## v0.16.1 C5c temporal-binding repair gate

Treat 0.16.1 as a compatible fail-closed repair. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, C5b engine `0.1.0`, and trust profile `0.1.0` unchanged. C5c engine/ruleset becomes `0.2.0`. Before packaging require regressions for unrelated trigger-event identity, true rule-reference semantics, two independently scoped exact deadlines, invalid timezone identity, legacy C5c context fail-closed behavior, and all prior C5c boundaries.

## v0.17.0 C5d release gate

Treat 0.17.0 as a compatible minor legal-engine addition. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, C5b engine `0.1.0`, C5c engine `0.2.0`, and trust profile `0.1.0` unchanged. Add C5d engine/ruleset `0.1.0` plus core attack-angle catalogue `0.1.0`.

Before packaging require deterministic regressions for: source-plus-signal gating; exact deadline plus independent adverse-state gating; proof-restriction non-upgrade; unknown-competence non-defect; unresolved lex-specialis non-attack; GDPR-presence non-attack; module-record candidate-only behavior; fact provenance before `supported`; proportionality concrete-signal gating; exact module replay; catalogue source integrity; blocked-upstream non-upgrade; private-data rejection; and all prior C1-C5c tests. Mock eval remains pipeline-only evidence.

## v0.18.0 C5e release gate

Treat 0.18.0 as a compatible minor downstream-suggestion addition. Keep inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, element model `0.2.0`, C5a engine `0.1.1`, C5b engine `0.1.0`, C5c engine `0.2.0`, C5d engine `0.1.0`, and trust profile `0.1.0` unchanged. Add analysis-handoff engine `0.1.0`, C5e suggestion engine/ruleset `0.1.0`, and original/adapted stratagem catalogues `0.1.0`.

Before packaging require regressions for explicit-review promotion, review-digest binding, module value semantics/provenance, unknown module-route target rejection, complete dual catalogues, candidate-not-recommendation state, unsupported attack-angle rejection, falsification rejection, disclosure/inaction return-to-analysis, non-mutating analysis return, explicit no-action, catalogue independence, private-data rejection, and all prior C1-C5d tests. Mock eval remains pipeline-only evidence.

## v0.19.0 C5f reviewer comparison gate

C5f adds version `0.1.0` review-context/output contracts with no C3 interface changes. Before accepting ranking, replay exact C5e candidates, verify all five direct/wait/no-action baselines and every candidate, preserve unknown/unsafe exclusions, and reject unsupported precedence, cycles and unconditional chains. `single_preferred_for_review` is not execution authorization.

## v0.20.0 C6 controlled synthetic release gate

This compatible minor addition does not alter C3 contract/profile `0.2.0`, controller protocol `0.3.0`, source pack `0.5.0`, element model `0.2.0`, or C5a–C5f engine versions. Add C6 driver/run manifest `0.1.0`, synthetic TR mock module and serialized CLI integration tests. Require existing 156 regressions plus C6 positive/review/negative tests, exact stage replay and script/policy hashes, controller-owned limited analysis validation/release, review-only separated strategy, changed-digest invalidation, and continued fail-closed private/full-release/outbound behavior. Do not claim reviewer authentication, independent legal accuracy, production host privacy or external delivery. After release, proceed to C7 independent hardening.

## v0.21.0 C7 fixed-fixture release gate

This minor, restrictive hardening release leaves C3 contract/profile 0.2.0, controller protocol 0.3.0, C1 pack version 0.5.0 and C5a–C5f legal/strategy engines unchanged. It revises only the C6 run-manifest contract to 0.2.0 (required source-trust record) and adds code-pinned metadata/source-representation declarations, allowlisted synthetic fixture content, complete companion issue indexes and a fail-closed release-attempt marker. A prior C6 v0.1.0 workdir requires a new run; silent migration or in-place rewriting is forbidden.

Before distributing: replay the evaluator's fabricated 64-zero source SHA; reject unapproved synthetic-labelled identifier-like text **before** a snapshot; enumerate all 31+ synthetic unresolved records without elision; mutate the issue companion after release and demand failed verification; inject interrupts at proposal, validation and release; run the full C1–C5f and C6 regressions plus C7 tests, schema/compile/link checks and fresh packaged-archive smoke verification. Compare source pack to a separately trusted identity, not a digest supplied by the pack itself.

The code-pinned policy is a local **release metadata** trust root, not a signed publisher attestation. Source representation bytes are not bundled. Existing C1 legal-source currentness is historical metadata until independently refreshed. Passing local tests does not permit real case intake, independent legal-conclusion claims, real reviewer identity, network delivery, publication or private-data host safety. External workflow evaluator/manual semantic review remains open after the local package passes.

## v0.21.1 C7.1 metadata and as-of repair

Compatible patch to the C6 synthetic-only integration boundary. It preserves source pack 0.5.0, C3 contracts 0.2.0, controller protocol 0.3.0, existing C5 engines and the code-pinned source/fixture policy. The prepared-run manifest advances to 0.2.1 and older C6 workspaces cannot silently migrate because the pinned code/schema and source-as-of field change.

Before releasing v0.21.1, run the exact independent 2026-10-09 probes: a fictional name/email in free-form `--run-id` or appended to `--time-of-check` must fail without creating a workspace; year 2099 must fail the pinned core metadata-age check; known fixed judgments must not be put on mutable operational-page age windows; direct controller initialization of a malformed date must fail; source-as-of mutation must block verification. Rerun C1-C7 deterministic suites, new metadata test, both structural validators, CLI release smoke from the final packaged ZIP, ZIP integrity and hash synchronization. All assertions of legal merits, publisher signatures, authenticated reviewer and host privacy remain explicitly unverified.

## v0.22.0 source-catalogue release (2026-10-09)

The active default moves to 0.6.0 metadata and bundled Deldwyn text while keeping 0.5.0 replay support. Full sibling v0.6.0 assembly and official-site revalidation remain separate release gates. Reuse the existing full C1–C7 tests and add Deldwyn-specific source-integrity and synthetic-controller regression. Do not label this source-pack complete without 47/47 byte matches.
