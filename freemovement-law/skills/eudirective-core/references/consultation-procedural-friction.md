# Proactive procedural-friction review

Use this reference for a substantive question about how an EU-family entry or short-stay visa procedure works. The review begins before any application, delay, refusal, blocked appointment, charge, or complaint exists. Its purpose is to compare the relevant national instructions with applicable EU rights, including when the user asks only for practical steps.

This is model-led legal issue review. Reuse C3, C5a–C5c, C23, the existing C27 registry, and the existing research validators. Do not add an independent legal-reasoning engine or run synthetic-only checks on applicant narratives. The route selects a review; it does not prove law, facts, execution, an attack angle, or infringement.

## 1. Route and baseline questions

For a general EU-family visa procedure, select `eu_family_visa_procedure_enquiry` from `consultation-issue-routing.json`. It does not require an adverse event. Classify, using C3, the applicant, EU citizen, destination state, application country, competent authority, family category, proceeding and stage, urgency, and requested output. Unknowns remain unknown; do not infer that the Directive applies merely because the citizen is European or the user says “family member.”

Consider the following, at a depth proportionate to the request:

1. Directive or derived-rights scope and the applicable family category.
2. Visa-exempt nationality, qualifying Article 10 or 20 residence card, and relevant national exemptions before application instructions.
3. Member State responsible and territorially competent consulate or mission.
4. Enquiry, appointment, direct access, lodging, and external-provider arrangements.
5. Visa-fee exemption and any separate optional provider charge.
6. Proof of identity, family status and category conditions; alternative evidence; translation, legalisation or authenticity questions; and ordinary Schengen checklist boundaries.
7. Published national processing periods, legally binding deadlines, the EU accelerated-processing rule, applicable exceptions, and the event that starts a clock.
8. Refusal grounds, remedies and deadlines when requested or materially relevant; keep formal refusal separate from access obstruction.
9. Border-entry safeguards, including the Article 5(4) reasonable-opportunity rule where applicable.
10. Material friction between the cited national procedure and the applicable EU standard.

Apply scope and family category before treating national instructions as decisive. Distinguish Article 2(2) family members; Article 3(2) extended-family beneficiaries; returning Union citizens; other derived-rights cases; and purely national extensions. Article 3(2) requires entry facilitation under national law and an individual examination; it does not itself give every extended relative an automatic right of entry. A national category does not establish the Directive category without legal comparison.

## 2. Source-grounded comparison

For each materially relevant national rule or practice:

1. Identify the source, publisher, type (binding national law, procedural rule, official guidance, mission/provider instruction, court decision), displayed version/date, and exact section or provision.
2. Identify the EU benchmark and classify it as binding legislation, CJEU interpretation, or non-binding official guidance.
3. Check that both sources apply to the same person/category, cross-border topology, authority, procedural stage, type of proceeding, and relevant date.
4. Compare the actual requirements, evidence, deadlines, discretion, access route, fees or remedies.
5. Check exceptions, counterarguments and source limits. A textual difference or inconvenience alone does not establish incompatibility.
6. Classify the result using section 3. If a material source is unavailable or not current enough, record that gap instead of inventing a warning.
7. Put any supported, relevant warning in the ordinary answer near the step it affects. Do not bury substantive legal friction in an audit board.

Check visa exemptions before describing how to apply. Article 5(2) of Directive 2004/38 requires a qualifying visa to be issued free of charge as soon as possible under an accelerated procedure. The Commission Visa Code Handbook I (2024), Part III, is official but non-binding operational guidance. It explains that qualifying Article 10 and Article 20 residence cards have visa-exempting effect; direct consular lodging should be genuinely and effectively available free of charge; processing beyond 15 days should be exceptional and duly justified; and delays beyond four weeks are not reasonable. Do not describe the Commission's 15-day/four-week guidance as a statutory deadline.

For documents, separate evidence establishing the beneficiary category from ordinary Visa Code purpose, accommodation, funds and intention-to-leave documents. Check alternative proof, authority competence, translation, and authentication separately. Do not describe a national checklist as exhaustive unless the applicable law and category support that conclusion. For outsourcing, distinguish the visa fee from optional services and check for a genuine, effective direct route. For timing, distinguish enquiry, appointment, attempted lodging, confirmed lodging, processing, and appeal periods.

## 3. Friction classifications

Use exactly one model-led disposition for each assessed material candidate:

- `potential_legal_conflict` — an identified national law or formal instruction appears difficult to reconcile with an applicable binding EU obligation.
- `potentially_restrictive_practice` — a published administrative procedure or checklist may narrow an entitlement or impose a restriction beyond what the applicable EU regime permits.
- `practical_access_barrier` — an identified arrangement may impede effective exercise of rights, although it is not inherently unlawful on the evidence available.
- `difference_explained_no_friction` — the difference is supported by a relevant category distinction, exception, or other adequate explanation.
- `insufficient_evidence_to_assess` — a consequential source, scope, category, practice, date, or exception is missing.
- `not_applicable` — the issue does not apply to the established procedure or category.

Do not call every inconvenience a legal conflict. Do not display unsupported speculation or every imaginable issue. If no material friction is identified after an adequate review, no warning is necessary.

## 4. Applicant-facing warning

A concise warning should state:

1. **Issue:** the specific national rule or published practice.
2. **EU standard:** the applicable right or safeguard and its legal force.
3. **Why it matters:** the source-grounded point of possible tension.
4. **Qualification:** category limits, exceptions, evidence gaps and interpretive uncertainty.
5. **Practical effect:** what the applicant should know, preserve, ask, or verify.

Use plain language. Distinguish the authority's published instruction from the EU obligation. A warning may be appropriate before the applicant experiences the procedure. It is not an allegation that the authority acted against this applicant.

## 5. Czech processing example

For a general Czech EU-family visa timing question, when the relevant route and source applicability are established or expressly presented as assumptions, include a warning substantially equivalent to:

> **Potential procedural conflict — processing time**
>
> The Czech Ministry of Foreign Affairs publishes a normal processing period of 14 days and says it may be extended to 45 days in well-founded instances. Directive 2004/38 requires qualifying entry visas to be issued as soon as possible through an accelerated procedure. The European Commission's non-binding guidance says processing beyond 15 days should be exceptional and duly justified, and delays beyond four weeks are not reasonable.
>
> The published Czech extension therefore raises a potential compatibility question. It is not automatically unlawful in every case: the applicable family category, actual processing stages, extension reason, and individual circumstances matter.

Do not call the 14-day period a statutory deadline unless its national legal basis has been verified. Do not treat Commission guidance as a binding absolute deadline. Include the issue even if no application has yet been lodged or no delay has occurred.

When this potential friction is material and a proportionate step is feasible, do not leave the warning alone: apply C25's prospective-prevention method in `references/consultation-preventive-strategy.md`. For the Czech example, consider a cooperative request to confirm the correct EU-family category and appropriate mission route before lodging, then targeted clarification if the 45-day period is later invoked. This is conditional guidance, not a finding that a Czech authority has misclassified an applicant; check the responsible mission's current instructions before giving mission-specific channels or escalation routes.

The Czech country reference is `freemovement-law-cz/skills/eudirective-library-cz/references/eu-family-short-stay-visa.md`. It records Czech Act 326/1999 §§15a, 20 and 180e, the central MFA page, accepted-source limits, and the still-partial national coverage. Use the exact installed Czech module and its `source-library/czechia/references/source-acceptance.json`; absence of the module or a source read remains reportable.

## 6. Rule-level review versus attack-angle or infringement findings

Keep these states separate:

1. A neutral procedure route was selected.
2. A source-backed national/EU comparison identified a possible friction point.
3. A topic-specific adverse predicate for C5d was assessed.
4. An applicant reported conduct or an authority action.
5. An infringement conclusion was legally and factually established.

A neutral route must not create an adverse factual predicate. A possible friction warning may be appropriate before any event; it does not automatically create a C5d candidate. An actual attack-angle or infringement conclusion requires its own applicable predicate, evidence and legal analysis. Do not claim that an authority has applied a published rule to the applicant unless the record supports it.

## 7. Source-use status and output mode

Keep these provenance states distinct for each materially relevant national module/source:

- the plugin was detected or available;
- skill instructions were read;
- a source record was located;
- the relevant source text or official guidance was actually consulted;
- the publisher was independently checked for currentness.

Module presence or skill invocation is not source consultation. An accepted local representation is a dated source artifact, not proof of current law. Record the exact missing source and its effect. Do not state that a script, validator, or deterministic engine ran without an observed result.

Ordinary answers use the direct answer, practical procedure, applicable safeguards, material friction warning, qualifications, next steps, and a concise source/coverage note where needed. Do not routinely show C27 identifiers, validator names, manifests, operation ledgers, provenance counts, or the full dashboard. The full diagnostic board remains available for an explicit audit, maintenance review, dashboard request, or detailed verification report.
