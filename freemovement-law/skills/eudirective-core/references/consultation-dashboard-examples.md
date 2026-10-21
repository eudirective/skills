# Consultation dashboard

Show the full board after every explicit FreeMovement invocation, whenever the user asks for it, and whenever a material routing, source, module, or execution variable changes. Use the response's native Markdown. Do not use wide tables, pipe-delimited rows, raw HTML, or fenced code blocks for the board; they make the status display hard to scan in chat.

Use the section headings below as visual groups. Each operation and selected C27 check gets its own short status card: a plain-language label first, the registered ID second, then the evidence, missing item, and effect. Keep every relevant row. Do not shrink the execution section into a single compact table.

Status text is authoritative. A small icon may help scanning, but it never replaces the status word: `✅ Reviewed`, `🟡 Partial`, `⚪ Not checked`, `⛔ Unavailable`, or `➖ Not applicable`. Keep the answer itself first; the board follows it.

## Full consultation review

## FreeMovement — Consultation Review

> 🟡 **PARTIAL** — The advice addresses the main question. The receipt was not inspected, so the formal lodging date remains unresolved.

### At a glance

- **Jurisdictions:** EU law; Spain as the intended residence state; Türkiye as the application context.
- **Proceedings:** family-member visa application; prospective residence-card procedure.
- **Urgency:** no verified deadline; appointment delay may affect timing.
- **Requested output:** explain the applicable route and practical next steps.
- **Coverage:** partial. Receipt classification and the authority's written position remain unknown.

### Work and execution

#### ✅ Reviewed — Applicant guidance

**Method:** model-led review of the reported facts against the cited official sources.

**Evidence:** conversation record and the official source entries below.

#### 🟡 Partial — Case-state review

**Checks:** `lifecycle.lodgement_confirmed`, `lifecycle.receipt_evidence`.

**Evidence:** the applicant reported a stamped submission and online tracking.

**Missing:** the receipt itself was not inspected.

**Effect:** formal lodging and the processing-clock start are unverified.

#### ⚪ Not run — Deterministic C27 case validator

**Reason:** its case scripts accept synthetic inputs; real applicant facts were not sent to them.

**Effect:** this is a model-led C27 review, not a recorded Python-engine result.

#### ⛔ Unavailable — C3 case-to-module match

**Reason:** no approved real-case geography check is available in this consultation.

**Effect:** the selected country-module fit remains unverified.

#### ➖ Not applicable — Research-artifact validator

**Reason:** no structured research plan or evidence bundle was created.

### C27 case checks

#### 🟡 Partial — Visa application: formal lodging

`lifecycle.lodgement_confirmed` · model review

**Evidence:** online tracking was reported.

**Missing:** the submission receipt and its classification.

**Effect:** the formal application date and processing-clock start remain uncertain.

#### 🟡 Partial — Visa application: receipt evidence

`lifecycle.receipt_evidence` · model review

**Evidence:** a stamped submission was reported.

**Missing:** a copy of the stamp or receipt was not reviewed.

**Effect:** the report is recorded but not independently checked.

### Other material issues

#### 🟡 Partial — Authority's stated grounds

**Evidence:** adverse comments were reported orally.

**Missing:** no written decision or verified statement of grounds was provided.

**Effect:** the authority's actual legal and factual position remains uncertain.

### Sources

#### Directive 2004/38/EC — EU law

- **This answer:** consulted; Articles 2, 3 and 5.
- **Earlier in this chat:** consulted.
- **Edition/currentness:** bundled consolidated edition; live currentness not checked.

#### Spanish official procedure

- **This answer:** consulted; section 8.
- **Earlier in this chat:** identified but not read.
- **Edition/currentness:** edition not recorded; currentness not verified.

### Modules

**Used in this answer**

- **eudirective-core** — EU/common-law analysis and consultation routing.
- **eudirective-ms-spain** — Spanish residence procedure. C3 pair validation was not run.

**Used earlier in this chat, not in this answer**

- **eudirective-ac-turkiye** — Türkiye-side document guidance was used earlier; no Türkiye document issue was reviewed in this answer.

**Relevant but not used**

- List each relevant module, its availability, and why it was not used. If the reason affects coverage, state the effect.

### Coverage and execution limits

- The statuses above describe model-led review unless a named tool or script is explicitly recorded as run with an observed result.
- No deterministic C27 case script, C3 case-geography controller, or research-artifact validator ran on this consultation.
- Source reading and module use are model-reported. A skill-level dashboard does not independently authenticate them or prevent an answer from being released without the board.
- Every partial, unavailable, or not-run item names what is missing and how it limits the assessment. Use `unknown` when the missing detail itself is not known.

## Minimal board when no case was assessed

## FreeMovement — Consultation Review

> ⚪ **NOT VERIFIED** — No case assessment was performed.

- **Invocation:** explicit, if visibly established; otherwise `unknown`.
- **Applicant guidance, C27 checks, sources, and country modules:** not assessed.
- Do not invent issue counts, source totals, module use, or execution results.
