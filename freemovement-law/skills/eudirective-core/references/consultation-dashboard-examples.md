# Consultation response examples

Formatting examples only. Bracketed text is placeholder content, not a case assessment, execution record, legal finding, or evaluation result. Keep the default answer concise and use ordinary Markdown.

## Concise default response

After the required first-response notice(s) and skill-version line, lead with the requested answer. Use a short scope or urgency line only if it helps.

### Assessment

[Answer the user's question directly. Separate what the law/source establishes from any disputed or unverified fact.]

### Practical next step

[Give one or two proportionate steps, with any urgent deadline caveat.]

### Coverage

[Partial — name the missing fact, document, source or check and what it prevents assessing.]

**Modules:** [When a jurisdiction, proceeding/stage, material fact, source review, module availability/conformance or execution changes, name the relevant modules used for this answer, those used earlier in this chat, and relevant ones not used. Give the reason/effect only when an absence limits the answer.]

For a narrow answer with no material open issue, the coverage note can be one sentence. Do not add a technical board just to display statuses that did not change.

## Expanded audit, when requested

Keep one issue record per proceeding and distinguish issue assessment from execution evidence.

### Visa application

- **Formal lodging and receipt**
  - **Disposition:** Answered conditionally.
  - **C27:** Partly reviewed · model review. `lifecycle.lodgement_confirmed`; `lifecycle.receipt_evidence`.
  - **Finding:** The user's account indicates a submission attempt.
  - **Missing / effect:** The receipt has not been inspected, so formal lodging and the date that starts the processing clock remain unverified.

### Execution board

#### Review and screening

- **Applicant issue review — Performed.**
  - **Applies to:** [proceeding and question].
  - **Result:** [brief account of the model-led review].
  - **Evidence:** Conversation record; no script output.

- **Attack-angle screen — Performed.**
  - **Applies to:** [factually indicated risks].
  - **Result:** [brief result, separate from C27 checks].
  - **Evidence:** Model-led review; no script output.

#### Source retrieval

- **Official-source check — Partly performed.**
  - **Applies to:** [legal issue and responsible source owner].
  - **Result:** [what reviewed source text establishes].
  - **Evidence:** [actual source reference].
  - **Missing / effect:** [name an unchecked national source or retrieval step and its effect].
  - **Operation:** `[exact_operation_id]` · output `[actual reference or none]`.

#### Validators and scripts

- **C27 deterministic case-state validator — Unavailable.**
  - **Applies to:** [selected case-state checks].
  - **Reason / effect:** It does not accept real applicant narratives, so no case-specific script result is available.
  - **Operation:** `c27_deterministic_case_state_validator` · output `none`.

### Module use in this answer and current chat

- **[Member State] — deciding-law role**
  - **Use:** Source content reviewed for this answer; not used earlier in this chat.
  - **Availability:** Available.
  - **C3 conformance:** [result and evidence, or “not checked”].

- **[Applicant country] — local-operations role**
  - **Use:** Relevant, but not consulted in this answer or earlier in this chat.
  - **Availability:** [available / not installed].
  - **C3 conformance:** [result and evidence, or “not checked”].
  - **Effect:** [local question that remains open].

**Coverage — partial.** [Name each material open check or operation and how it limits the answer.]

**Assurance:** This is a model-led, self-reported audit. The plugin has no host-validated answer-release gate.
