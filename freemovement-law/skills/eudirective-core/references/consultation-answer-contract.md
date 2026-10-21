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

## Authority position and remedies

Describe an authority's actual position only when the record supports it. Keep oral reports, written decisions, stated reasons, disclosed facts, and independent inference separate. Do not attribute a hypothetical defence to an authority or decision. A missing written decision may limit the verified grounds without preventing analysis of the conduct actually reported.

Keep separate proceedings and clocks distinct, including attempted submission versus formal lodging, visa refusal versus access obstruction, administrative or conduct complaints, SOLVIT, and access requests. Do not imply that a complaint suspends a formal appeal period. A weakness in one claim does not close an independent grievance.

## User-facing presentation

After any required first-response notices and skill-version line, lead with the requested substantive answer. Add a brief scope or urgency line only when it helps. Use short headings or bullets for the legal assessment and practical next steps. End with a concise coverage note that names material open issues and their effects. When jurisdiction roles, proceeding/stage, material facts, source consultation, module availability/conformance or execution changes, say which relevant modules informed this answer, which were used earlier in this chat, and which relevant modules were not used; briefly explain any absence that limits coverage. If those variables and module-use states have not changed, do not repeat the full record. Add the compact consultation dashboard after the answer when there is a new explicit plugin invocation, an explicit dashboard/audit request, or a material change that makes an optional continuation dashboard useful. Apply the invocation and source-accounting rules in `references/consultation-routing.md`.

Keep detailed C27 IDs, source/evidence references, operation IDs, exact status values, module conformance and the full route ledger for an expanded audit or when a specific item is necessary to explain an important limitation. Do not claim comprehensiveness while any required or triggered work remains open. A complete-looking record is not proof of legal accuracy or host enforcement.
