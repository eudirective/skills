# Consultation answer contract

Use this contract to connect the user's questions and material events to the answer. It supplements C23, C24, C25, C27, the C3 module contracts, and the existing research validators; it does not replace them.

## Disposition for every material issue

Give each issue one clear disposition:

- **Answered and supported:** state the answer and its controlling source/facts.
- **Answered conditionally:** state the answer and the specific unresolved predicate that could change it.
- **Source missing:** identify the exact source or source review still needed and which conclusion it limits. Preserve conclusions supported by other source owners.
- **Fact missing:** ask only for the fact that could change the result; state what can already be concluded without it.
- **Out of scope:** give the reason and, where useful, the proper source owner or route.

Do not use a generic `partial` label in place of the issue's disposition. Distinguish an open legal/factual question from an operation that was not run. For every partly reviewed item, say what is missing and how that gap limits the assessment.

## Preventive response to material friction

When a source-supported prospective friction point has a feasible preventive response, include it near the related procedure step. Concisely state the foreseeable risk, why it matters under the applicable EU safeguard, the recommended initial action and its purpose, and what authority response or later event would justify reassessment or escalation. Compare proportionate alternatives, including cooperation, targeted clarification, waiting/no extra action, and escalation only where its route and value are supported. Do not require an adverse event before offering useful prevention, and do not turn a normal procedure answer into a litigation manual.

For a substantive procedure question, make that prevention easy to act on: use a short **“How to avoid this problem”** step when it would materially help, naming the risk, the EU-rights significance, the first step and its purpose, and the trigger for reassessment. For Czech 14/45-day guidance, flag that 45 days resembles ordinary Visa Code Article 23(2) as a legal-basis question, not proof of misclassification. Explain that a decision should be made as soon as lawfully possible; any one-day illustration is not a statutory deadline.

## Authority position and remedies

Describe an authority's actual position only when the record supports it. Keep oral reports, written decisions, stated reasons, disclosed facts, and independent inference separate. Do not attribute a hypothetical defence to an authority or decision. A missing written decision may limit the verified grounds without preventing analysis of the conduct actually reported.

Keep separate proceedings and clocks distinct, including attempted submission versus formal lodging, visa refusal versus access obstruction, administrative or conduct complaints, SOLVIT, and access requests. Do not imply that a complaint suspends a formal appeal period. A weakness in one claim does not close an independent grievance.

## User-facing presentation

After any required first-response notices and skill-version line, lead with the requested substantive answer. Use short headings or bullets for the legal assessment and practical next steps. For a substantive EU-family visa procedure answer, include material source-supported friction warnings near the relevant procedural step; do not defer them to technical diagnostics. End the substantive answer with a concise coverage note that names material open issues and their effects. When jurisdiction roles, proceeding/stage, facts, source consultation, module availability/conformance, or execution materially changes, briefly state which relevant modules/sources informed the answer and which relevant module/source was not used, explaining any material limit.

Every substantive legal consultation ends with a fresh consultation board in the same answer. Use receipt schema 0.10.0 for a privacy-minimised structured receipt and record a top-level **Full** or **Limited** consultation mode. Full means the complete review flow appropriate to the requested scope was performed; Limited means the response was narrowed or a material review step could not be completed. Mode is separate from `coverage_claim` and the board's assessment status: a Full review can report partial coverage, and a Limited review can have comprehensive coverage for its narrow scope. Name every missing fact, source, module check, operation, or review and explain its effect. Greetings, unrelated development requests, and direct plugin mentions without a case assessment do not need a case board. Follow `references/consultation-routing.md` for the board layout.

The board contains the strategy trigger screen and its disposition. If a strategy trigger is present, give a case-specific first step, purpose, reassessment event and proportionate alternatives. If no trigger is present, say why no separate preventive step is indicated. If the assessment is limited, name the missing item and effect; do not use generic limitations or hide a triggered action behind them. Show every selected C27 ID, source/evidence trace, operation ID, exact status, module-conformance result, source-ledger row and validation result required by the board layout. Do not claim comprehensiveness while any required or triggered work remains open. A complete-looking record is not proof of legal accuracy or host enforcement.


For a source ledger, separate (a) candidate matched in the bundled source library, (b) candidate discovered by search, (c) official link reviewed, (d) official text actually opened, (e) bundled accepted text actually read, and (f) not consulted. A source appearing in a manifest or issue index is only a candidate; it is not evidence it was used, opened, current, binding, or applicable in this consultation. Identify publisher, document or instrument title, article/section or pinpoint, and displayed edition/date for material legal propositions. Keep HTTPS syntax checks separate from reachability: a URL that was not opened, is blocked, times out, or is JS-only is not a verified working link and should be described as not verified, not dead. When available, record a bounded official-link check with date and any redirect evidence; do not require networking for offline deterministic checks.


For every in-scope adverse decision/outcome issue, make the interim-protection screen visible even when no C27 interim check is selected: record `not_applicable` and why when no potentially irreversible, time-sensitive harm is reported, or `unknown` and the exact missing urgency assessment. Mark it triggered only where the refusal route is applicable and the reported harm warrants screening. A deadline alone does not satisfy that predicate.
