# Consultation issue model

This is an in-conversation model for organising material questions in a consultation. It keeps legal issues, facts, proceedings, evidence, and answer status connected without turning the conversation into a persisted case file. The deterministic selector in this package accepts only abstract signal IDs; it does not accept this model's case facts or a user narrative.

## Issue record

Create one issue record for each materially distinct question or event. Use a stable, conversation-local issue ID and link it to exactly one proceeding as its primary scope.

| Field | Required content |
|---|---|
| Issue ID and proceeding | A short stable issue ID; the proceeding ID it belongs to; links to other issues only when they are genuinely related. |
| Reported event or question | A neutral description of what the user says happened or asks. Attribute reported facts to the user; distinguish supplied records from the account. |
| Requested outcome | The practical result sought for this issue, such as acceptance of an application, a decision, correction, review, complaint response, or preservation of evidence. |
| Jurisdiction and legal regime | Separate the relevant states by role (for example, nationality, intended residence, application location, deciding authority, or challenged authority). Record the candidate legal regime and any competing regime. |
| Known and unresolved facts | Keep facts supported by the user's account or shown records separate from unresolved predicates. Record only facts that can change the rule, procedure, deadline, or next action. |
| Authority position | Record what the authority actually said or decided, by whom and through which channel, with the available provenance. Distinguish a formal written ground, reported oral statement, inference, and no known position. |
| Administrative outcome | Record the source-attributed formal outcome separately from procedural stage. Keep competence, inadmissibility, substantive refusal, withdrawal/transfer, issuance and post-issuance events distinct. A decision stage or oral report alone does not establish a formal outcome. |
| Applicable C27 checks | List the existing check IDs selected for this issue and the reason each applies. Selection is a plan, not evidence that a check was completed. Do not create or copy a second check registry. |
| Source owner and supporting evidence | Name the owner of the legal source: EU/common core, the relevant Member-State module, the applicant-country operational module, or another identified authority. Link the source proposition and the fact evidence separately. State when a needed source or record has not been checked or supplied. |
| Exceptions and counterarguments | Record plausible exceptions, competing characterisations, contrary authority, and the facts that would make them material. Do not treat a possible defence as an authority's actual ground. |
| Independent complaint or remedy track | Link any conduct, access, data-protection, supervisory, appeal, or other remedy issue as its own issue with its own authority, deadline, requested relief, and disposition. |
| Review status and gap | Use a clear status such as open, conditionally assessed, supported, or not applicable. For every gap, say exactly what is missing and why it matters. |
| Answer disposition | Record whether the issue is answered and supported, answered conditionally, awaiting a specific fact, limited by a missing source, outside scope, or still open. |

## Proceeding and lifecycle boundaries

Maintain a separate proceeding record for every application, refusal, challenge, complaint, residence process, or information request. Each record has its own authority, legal basis, procedural stage, event history, evidence, disclosures, clocks, and decisions. A linked complaint may refer to the application event without becoming part of the visa decision. A later application does not inherit the documents, notices, or disclosures of an earlier application unless the evidence establishes that they were shared.

Distinguish, where relevant:

- enquiry and appointment request;
- prepared or online form;
- attendance and attempt to submit;
- receipt, formal lodging, or a disputed account of lodging;
- examination, supplementary request, and decision;
- notification or service of the decision;
- appeal, reconsideration, complaint, or supervisory process.

In particular, refusal to receive or lodge an application is not the same event as a formal visa refusal after examination. Visa Code Article 18 competence, Article 19 inadmissibility and Article 32 substantive refusal are separate outcome routes for an ordinary short-stay visa application. Keep the access-obstruction issue and any later visa decision in separate records, even if they concern the same application. A visa appeal is a linked, separate proceeding; record the underlying application separately. See `references/consultation-outcomes-and-remedies.md`.

## Submitted original documents not returned

Treat a report that submitted originals remain unreturned as a separate custody and safe-return issue, even if the visa refusal challenge is weak or the originals are not necessary to prove another claim. Record a submission inventory, the actual custodian (consulate, service provider, another body, or unknown), the stated retention reason and current status, any request for accounting and safe return, submission/receipt and handoff evidence, and a concrete follow-up trigger. Do not assume the documents remain withheld, that retention is unlawful, or which body is responsible without evidence. A request for a copy or translation alone does not trigger this issue. GDPR access or processing questions are separate; they do not recover physical originals, and physical custody alone does not automatically trigger a GDPR claim.

## Independent conclusions and missing documents

Assess each legal question on its own available facts and sources. A missing document may leave a fact unproved or an evidentiary step unresolved; it does not automatically prevent a legal conclusion that can already be reached from the applicable rule and known facts. State the remaining evidentiary limitation precisely and continue with independently answerable issues.

Likewise, uncertainty in one proceeding does not close a separate grievance. For example, a disputed lodging date may limit a processing-clock conclusion while leaving a reported appointment-access event independently reviewable.

## Use and privacy limits

Keep this as a concise working structure in the conversation. Do not feed real applicant narratives, identities, dates, documents, or free text into the synthetic selector or other synthetic-only scripts. Use the source owner appropriate to the legal question; a country mention alone does not transfer EU-law ownership to a national module. Do not report a selected C27 check as assessed, a source as current, or an engine as executed without the corresponding work and evidence.
