# Consultation quality workflow

This is a model-led review sequence for ordinary FreeMovement consultations. Its stages improve issue coverage and answer traceability; they are not independent agents, deterministic execution, legal certification, or a host release gate. Keep real applicant facts in the conversation and outside synthetic-only scripts.

## A. Discover issues before selecting checks

Read the user's request again and identify each material question, reported event, proceeding, procedural stage, requested outcome, and potential independent grievance. Use `references/consultation-issue-model.md` to keep them distinct. Do not start from a dashboard or from the check registry alone.

## B. Expand and route coverage

Map each issue to one or more neutral signals in `references/consultation-issue-routing.json`. Select only checks those signals require or conditionally trigger from `references/state-engine/check-registry.json`. Apply the route's negative conditions. Separate proceedings and keep C3 jurisdiction roles distinct. This routing metadata describes review coverage; it is not a second legal-rule or check registry.

## C. Assess law, facts and evidence

For each issue, identify the responsible legal/source owner and the relevant rule, scope, conditions, exceptions, counterauthority, and evidence. Distinguish user-reported facts, inspected documents, reviewed official source text, bundled snapshots, model interpretation, and unverified procedure. Use current official sources when the answer depends on current law. Reuse the existing source research and preflight validators. Do not make a missing document a reason to withhold a legal conclusion that can already be assessed.

For every material issue, choose an answer disposition from `references/consultation-answer-contract.md`. Record its finding, support, limits, and any targeted missing fact or source. A selected check is not an assessed check; record only work actually performed.

## D. Review omissions and contradictions

Compare the draft against the original questions and issue list. Check for unanswered questions, merged proceedings, unsupported factual or legal conclusions, missed independent grievances or remedies, mismatched source owners, contradiction between advice and evidence, hypothetical authority arguments presented as actual grounds, and unsupported claims that an engine or validator ran. Give an urgent, appropriately qualified step without waiting for non-urgent research.

## E. Deliver the answer and coverage summary

Follow `references/consultation-answer-contract.md`: answer the user's substantive request first, then give a concise coverage summary naming material open issues and their effect. Include relevant module use when C3 variables change. Add the compact consultation dashboard when explicit invocation or an explicit dashboard/audit request requires it; implicit continuation may omit it unless material state changes. Keep that board concise and readable rather than exposing a large technical ledger. When the user requests a route or evidence audit, provide the expanded issue, C27, operation, source, and module records described in `references/consultation-routing.md`.

These are stages of one model-led review. Do not describe them as independent reviews or claim that a stage executed a Python engine.
