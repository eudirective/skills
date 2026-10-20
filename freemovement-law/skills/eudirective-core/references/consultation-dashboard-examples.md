# Consultation dashboard layouts

Formatting examples only. Bracketed text is placeholder content, not a case
assessment, execution record, or evaluation result. Use ordinary Markdown
headings and bullets. Never use tables, pipe-delimited rows, or fenced code for
the dashboard.

## Compact view

On the first response, show the disclaimer, any applicable licensing note, and
the skill-version line in that order; put the dashboard after them and before
substantive guidance. On later replies, do not repeat the once-per-chat notices
unless the use context materially changes.

### Case status

**Coverage:** Partial — formal lodging and timing remain unresolved.

**Urgency:** Unknown; the information so far does not establish whether a
deadline or risk of losing evidence is active.

**Scope:** Visa application and a separate conduct complaint. Requested output:
source-grounded next steps.

#### Visa application

- **Formal lodging and receipt**
  - **Status:** Partly reviewed · model review.
  - **Finding:** Online tracking and a stamped submission are reported.
  - **Checks:** `lifecycle.lodgement_confirmed`; `lifecycle.receipt_evidence`.
  - **Missing / effect:** The receipt has not been inspected, so formal lodging
    and the clock-start date remain unresolved.
- **Processing time**
  - **Status:** Partly reviewed · source review.
  - **Finding:** Earlier source material on the EU timing rule was reviewed.
  - **Checks:** `timing.accelerated_processing`; `timing.clock_start`.
  - **Missing / effect:** The formal lodging date and any exceptional delay
    justification are unknown, so a processing breach cannot be assessed.

#### Separate conduct complaint

- **Staff conduct and non-response**
  - **Status:** Partly reviewed · model review.
  - **Finding:** The reported service grievance is considered separately from
    the visa decision.
  - **Checks:** `[exact registry IDs]`.
  - **Missing / effect:** The relevant correspondence has not been reviewed, so
    the response history and any available complaint route remain uncertain.

### Execution board

#### Review and screening

##### Applicant review

- **Status:** Performed · model-led review.
- **Applies to:** `[proceeding and question reviewed]`.
- **Workflow:** `[C23 guidance workflow; list C27 atomic checks above]`.
- **Result:** `[brief, user-readable summary of the review]`.
- **Evidence:** `[source references, or “conversation-only assessment”]`.

##### Attack-angle screen

- **Status:** Performed · model-led review.
- **Applies to:** `[material adverse interpretations and practical risks]`.
- **Workflow:** Model-led attack-angle screen.
- **Result:** `[brief result, kept separate from C27 stratagem checks]`.
- **Evidence:** Conversation-only assessment; no script output.

#### Source retrieval

##### Official-source retrieval

- **Status:** Performed.
- **Applies to:** `[jurisdictions, legal topics, or publishers relevant to the question]`.
- **Result:** `[plain-language summary of what retrieval established]`.
- **Evidence:** `[retrieved source references]`.
- **Operation:** `[exact operation ID]` · output `[reference]`.

##### National urgent-remedy procedure

- **Status:** Partly performed.
- **Applies to:** `[proceeding, jurisdiction, and procedural stage]`.
- **Result:** `[what the retrieved material established]`.
- **Evidence:** `[retrieved source references, or none]`.
- **Missing / effect:** `[name the missing country-specific source or step and
  what it prevents assessing]`.
- **Operation:** `[exact operation ID]` · output `[reference or none]`.

#### Validators and scripts

##### C27 deterministic case-state validator

- **Status:** Unavailable.
- **Applies to:** `[selected case-state checks]`.
- **Result:** No case-specific validator result is available.
- **Evidence:** None.
- **Reason / effect:** It does not accept a real applicant narrative, so it
  provides no case-specific validator result.
- **Operation:** `c27_deterministic_case_state_validator` · output `none`.

### Module use in this answer and current chat

#### [Member State] — deciding-law role

- **Use:** source content reviewed in this answer; not used earlier in this
  chat.
- **Availability:** Available.
- **C3 conformance:** `[result and reference, or “not checked”]`.

#### [Applicant country] — local-operations role

- **Use:** Relevant, but not used in this answer or earlier in this chat
  because `[reason]`.
- **Availability:** `[available / not installed]`.
- **C3 conformance:** `[result and reference, or “not checked”]`.
- **Effect:** `[specific local-operation question that remains open]`.

#### [Other Member State] — relevant national-law role

- **Use:** Source content reviewed earlier in this chat, but not relied on in
  this answer.
- **Availability:** `[available / not installed]`.
- **C3 conformance:** `[result and reference, or “not checked”]`.

**Overall coverage — partial.** Formal lodging, the timing trigger, and the
national complaint route remain open, so the deadline and remedy assessment is
limited.

**Assurance:** This is a model-led, self-reported status display. No
host-validated release gate is integrated, and the dashboard does not prevent
answer release.

## Expanded audit view

Use this when requested or when a compact display would hide material
complexity. Keep the same proceeding headings and plain-language labels, then
include each record's exact `scope_ref`, `check_id`, `status`, `method`,
evidence/source references, recorded reason, and `scope_exclusion` when
present. Preserve every partial item's **Missing / effect** line. Show the full
operation record, and distinguish module availability, C3 conformance, source
consultation in this answer, and use earlier in this chat. End with overall
coverage, the material gaps and their effects, and the host-enforcement
statement. Do not repeat unrelated background or expose private chain of
thought.
