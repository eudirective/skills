# Consultation dashboard

Show a full board after every explicit invocation and whenever a material
routing, source, module, or execution variable changes. The full board is the
default; there is no compact version or request-only expanded audit. This
example shows the headings and readable form. A real board includes every row
present in its receipt, with no row limits.

## Full consultation review

## FreeMovement — Consultation Review

**Partial** · Requested coverage: partial

### Invocation and validation

- Invocation: explicit; basis: visible plugin selection.
- Validation result: **valid partial route**.
- Validator: `consultation_route_gate.py` v0.2.0.
- Receipt fingerprint: `<SHA-256 fingerprint>`.
- Outstanding validation items: 3.
- The structural validator checks declared records. It does not authenticate
  model-reported facts, source reads, legal reasoning, or omitted issues.
- ChatGPT host release control: unavailable in this plugin. The local
  controller can bind a receipt and answer only when a host calls it.

### At a glance

- Assessment: partial; requested coverage: partial.
- Legal texts this response: 2 (model-reported).
- Conversation total: 4 (model-reported).
- Source-library sections this response: 2.
- Declared material issues: 1; outstanding checks and operations: 3.

### Task scope

- **Jurisdiction roles:** recorded · conversation record.
- **Proceedings and stages:** recorded · conversation record.
- **Legal questions:** recorded · conversation record.
- **Urgency:** recorded · conversation record.
- **Requested output:** recorded · conversation record.
- **Conditional workflow review:** reviewed · conversation record.

### Work performed and engine checks

4/5 required or triggered operations have completion records with acceptable evidence.

- **Route classification** (`route_classification`) — Required; completed. Evidence: conversation record.
- **Applicant guidance** (`c23_guidance`) — Required; completed. Evidence: conversation record and official source records.
- **C27 case-state checks** (`c27_reconciliation`) — Required; partial. Missing: receipt classification not inspected.
- **Alternative-risk screening** (`attack_angle_screen`) — Required; completed. Evidence: conversation record.
- **Country-to-case match** (`c3_case_geography_match`) — Triggered; unavailable. Reason: restricted to synthetic inputs. Effect: real-case module fit remains unverified.
- **Research-plan validation** (`research_gate`) — Not triggered; not applicable. Reason: no material research task identified.

The actual board lists every required, triggered, and not-triggered operation,
including any required operation missing from the receipt.

### C27 case-state checks

- **Visa application — `lifecycle.lodgement_confirmed`**
  - Status and method: partial · model review. Reason: online tracking was reported; receipt classification was not inspected.
  - Evidence: conversation record; sources: none recorded.

Every selected C27 check appears with its exact ID, status, method, reason,
evidence/source trace, and any `scope_exclusion`.

### Material issues and open work

- **Formal lodging and processing time:** disposition: answered conditionally.
  Missing: the receipt was not inspected. Effect: the formal processing-clock
  start remains unverified.
- **Country-to-case match:** the real-case geography check is unsupported by
  the synthetic-only controller. Effect: the selected country's module fit
  remains unverified.

List every declared material issue and every validator gap. For every partial
or unavailable item, state what is missing and how it limits the assessment.

### Research and source coverage validation

- Research plan and bundle: not supplied; no research result is claimed.
- Module-pair validation: no module pair was submitted to C3.
- Source-preflight validation: not run; explain the missing task if required.

### Source ledger

- **Directive 2004/38/EC** — EU core · EU · EU law.
  - Identity: source `eu:32004l0038`; logical record `eu:32004l0038`; source library.
  - This answer: consulted; provenance model-declared. Earlier chat: consulted; provenance model-declared.
  - Edition: consolidated edition; pinpoints: Articles 2, 3 and 5.
  - Currentness: unknown; library status: registered record.
- **Official national procedure** — Spain · ES · procedure.
  - Identity: external official source; edition not recorded.
  - This answer: consulted; provenance model-declared. Earlier chat: identified, not read.
  - Pinpoint: section 8. Currentness: unknown; library status: not applicable.

Show every ledger entry, including unread, memory-cited, and not-referenced
sources. Use `unknown` when tracking is unavailable; never substitute zero.

### Module use in this answer and chat

- **eudirective-core** — Consultation routing and EU/common legal analysis.
  - This answer: used; earlier in chat: used earlier; available; C3 not applicable.
  - Reason: core guidance used for this response.
- **eudirective-ms-spain** — Spanish procedure.
  - This answer: used; earlier in chat: not used earlier; available; C3 not checked.
  - Reason: country-specific procedure reviewed; pair validation not run.
- **eudirective-ac-turkiye** — Applicant-country documents.
  - This answer: not used; earlier in chat: not used earlier; available; C3 not applicable.
  - Reason: no Türkiye-side document issue was identified.

List every relevant module record, and explain when unavailable or unvalidated
module information limits coverage.

### What this board can verify

- It shows each source, selected C27 check, declared issue, module record, and
  required or triggered operation present in the receipt.
- Local validators check declared structure and selected artifacts. They do
  not prove model-reported work or detect omitted issues and triggers.
- A local controller can bind the exact answer and receipt when called by a
  host. This plugin does not control ChatGPT's host release path.

## Non-consultation invocation

For a direct explicit invocation that does not request case assessment, use a
minimal board:

## FreeMovement — Consultation Review

**Not verified** · No case assessment was performed.

Invocation: explicit. Receipt validation: show the actual result, or state
`not run/unavailable`. Do not invent source totals, issues, or module checks.
