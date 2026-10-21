# Consultation dashboard

Use this as the visual pattern for a full consultation board. It is ordinary Markdown: status icons and structure help scanning, but do not imply custom colors, CSS, interactivity, or host verification. Keep the answer itself first. Avoid wide tables and code-like dumps; the small three-column metric row below is the only table in the board.

## Full consultation review

# EU-family visa and residence review

*Application in Türkiye · intended residence in Spain · EU citizen moving with a spouse*

> 🟠 **PARTIAL REVIEW** — The EU route and residence-card entry rule were assessed. Formal visa lodging, authority classification, and the processing-clock start remain unresolved.

### At a glance

| **Issues reviewed** | **Supported** | **Partial / open** |
| :---: | :---: | :---: |
| **6** | **3** | **3** |

**Assessment coverage · 6 / 6 recorded issues reviewed**

🟩🟩🟩🟨🟨🟨

🟩 Supported: **3 (50%)** · 🟨 Partial/open: **3 (50%)** · ⚪ Out of scope: **0 (0%)**

*Each square represents one issue with a recorded disposition. Percentages describe only the distribution of these recorded outcomes, not legal completeness or proof that every relevant issue was found. Counts are model-reported.*

### Review scope

- **Jurisdictions:** EU law; Spain as intended residence; Türkiye as the application context.
- **Proceedings:** family-member visa application; prospective Spanish residence-card procedure; separate service grievance.
- **Stage:** visa appointment/submission; formal lodging not established; residence-card application prospective.
- **Urgency:** no verified filing deadline; appointment delay may affect timing.
- **Requested:** explain the route, identify unresolved points, and give practical next steps.

### Assessment by issue

#### 🟩 Supported — EU-family visa route

**Finding:** the reported relationship and cross-border plan engage the EU-family route for the question assessed.

**Evidence and source basis:** reported marriage and joint travel; Directive 2004/38/EC and official EU guidance.

**C27 checks:** `eu_scope.directive_scope` — assessed by source review; `eu_scope.accompany_or_join` — assessed by source review.

#### 🟨 Partial — Formal visa lodging

**Finding:** a stamped submission and online tracking were reported, but formal lodging is not established from the available record.

**Evidence:** applicant's account of the stamp and tracking page.

**C27 checks:** `lifecycle.lodgement_confirmed` — partial, model review; `lifecycle.receipt_evidence` — partial, model review.

**Missing:** the receipt or submission record and its exact classification were not inspected.

**Effect:** the formal application date and processing-clock start remain uncertain.

#### 🟨 Partial — Authority's application classification

**Finding:** the fee exemption may indicate EU-family handling, but does not establish the authority's internal case classification.

**Evidence:** reported fee treatment.

**C27 check:** `case_intake.authority_classification` — partial, model review.

**Missing:** a written classification, case-system record, or other confirmation from the authority.

**Effect:** advice about the applicable procedure and any challenge should remain qualified.

#### 🟨 Partial — Processing time and clock start

**Finding:** the EU acceleration requirement was reviewed; the individual processing clock and any exceptional justification remain open.

**Evidence and source basis:** reported appointment/submission timeline; Directive 2004/38/EC and official EU guidance.

**C27 checks:** `timing.accelerated_processing` — partial, source review; `timing.clock_start` — partial, model review.

**Missing:** proof of formal lodging and the authority's explanation for the delay.

**Effect:** the applicable start date and whether the delay is justified cannot yet be determined.

#### 🟩 Supported — Residence-card entry rule

**Finding:** the entry-visa question for the prospective residence-card application was assessed separately from the visa application.

**Evidence and source basis:** stated plan to reside in Spain; Spanish Article 8 procedure and applicable EU-law guidance.

**C27 check:** `eu_scope.residence_card_entry_exemption` — assessed by source review.

#### 🟩 Supported — Separate service grievance

**Finding:** the reported staff treatment and access problem can be recorded as a separate service-grievance track, independently of the visa merits.

**Evidence:** reported appointment delay and difficulty accessing the service.

**C27 check:** `conduct.staff_treatment` — assessed by model review.

**Scope:** this identifies a separate issue; it does not establish misconduct or resolve the available remedy or deadline.

### Execution and verification

#### ✅ Model-led applicant guidance

**Status:** performed in this response.

**Method:** facts and legal questions reviewed in the conversation against the identified official sources. No real applicant facts were sent to synthetic-only scripts.

#### ✅ Source review

**Status:** official EU and Spanish materials were reviewed for the issues above.

**Limit:** the source accounting below is model-reported; it is not an authenticated retrieval log.

#### ⚪ Deterministic C27 case-state validator — not run

**Reason:** its case scripts are restricted to synthetic inputs; real applicant facts were not submitted.

**Effect:** the check statuses above describe model-led review, not results from the Python case-state engine.

#### ⚪ C3 case-to-module match — not run

**Reason:** no approved real-case geography check was available in this consultation.

**Effect:** the selected module's fit to this particular case was not validated by the controller.

#### ⚪ Research-artifact validator — not run

**Reason:** no structured research plan and evidence bundle were created.

**Effect:** no validator-backed research-coverage result is available.

### Sources and modules

**Source accounting — this response:** 2 distinct records; **1** matched to the plugin's bundled library; **1** identified through web search.

**Across this chat:** 2 distinct records; **1** bundled-library match; **1** web-search discovery.

Counts can overlap: a web search can find a source also present in the bundle. Counts cover the source records listed here, not every search-result hit. Identified-but-not-read records count as identified, not consulted. If discovery tracking is missing, show `unknown`, not zero.

#### Directive 2004/38/EC — EU law

- **Bundle match:** yes; identified from `plugin_library` in this response and earlier in this chat.
- **Use:** consulted for Articles 2, 3 and 5 in this response and earlier in this chat.
- **Edition:** bundled edition; live currentness was not checked.

#### Spanish official procedure

- **Bundle match:** no; identified through `web_search` in this response and carried from `prior_conversation` earlier in this chat.
- **Use:** consulted for the residence-card procedure in this response; identified but not read earlier.
- **Edition:** edition not recorded; currentness not verified.

#### Modules

**Used in this response:**

- **eudirective-core** — EU/common-law analysis and routing.
- **eudirective-ms-spain** — Spanish residence procedure; source review only, with no C3 pair validation.

**Used earlier in this chat:**

- **eudirective-ac-turkiye** — Türkiye-side document guidance was used earlier; it was not needed for the issues reviewed in this response.

**Relevant but not used:** name each relevant module, whether it was available, and why it was not used. Explain any effect on coverage.

### Limits and provenance

- The issue summary counts the dispositions recorded above; it does not measure overall legal completeness.
- Source review, issue assessment, and module use are model-reported. Say a script or tool ran only when this chat contains its observed result.
- No deterministic C27 validator, C3 case-level controller, or research-artifact validator ran in this example.
- This plugin emits ordinary Markdown. It does not provide custom colors, a separate UI widget, a host-validated source-read record, or a release gate.
- Every partial or unrun item names what is missing and how it affects the assessment. Use `unknown` when the missing detail itself is unknown.

## Minimal board when no case was assessed

## freemovement-law — Consultation Review

> ⚪ **NOT ASSESSED** — No case assessment was performed.

- **Invocation:** explicit only when established by a host signal or visible plugin-selection marker; otherwise `unknown`.
- **Applicant guidance, issues, C27 checks, sources, and country modules:** not assessed or not recorded.
- Do not invent zero counts, issue statuses, source totals, module use, or execution results.
