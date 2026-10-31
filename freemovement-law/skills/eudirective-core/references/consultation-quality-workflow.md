# Consultation quality workflow

This is a model-led review sequence for ordinary freemovement-law consultations. Its stages improve issue coverage and answer traceability; they are not independent agents, deterministic execution, legal certification, or a host release gate. Keep real applicant facts in the conversation and outside synthetic-only scripts.

## A. Discover issues before selecting checks

Read the user's request again and identify each material question, reported event, proceeding, procedural stage, requested outcome, jurisdiction by role, urgency, and potential independent grievance. Use `references/consultation-issue-model.md` to keep them distinct. Do not start from a dashboard or the check registry alone.

## B. Expand and route coverage

Map each issue to one or more neutral signals in `references/consultation-issue-routing.json`. For general EU-family entry or short-stay visa procedure questions, select `eu_family_visa_procedure_enquiry` even when there is no adverse event. Select only checks the signal requires or conditionally triggers from `references/state-engine/check-registry.json`. Apply negative conditions and typed procedure scope. Keep Visa Code Article 18 competence, Article 19 inadmissibility, Article 32 substantive refusal, and blocked access/lodgement on distinct paths. Do not select Article 32 refusal/remedy checks for inadmissibility or pre-lodgement obstruction. Separate proceedings and C3 jurisdiction roles. A route signal triggers review; it does not prove an adverse condition. Independently compare the full procedural history and reported issues against C27 triggers. A selected check is a review prompt, not evidence that the check was assessed.

For an explicit request to prevent or plan around an EU-family procedure risk, also select `preventive_strategy_requested`. It reaches the existing general procedure route, not a second general visa route. After source comparison, assess the route's C25 conditional workflow; the selector exposes it as awaiting model condition assessment and does not decide that a legal or factual risk is present.

## C. Compare national procedure with EU safeguards

For a substantive EU-family visa procedure consultation, read `references/consultation-procedural-friction.md` and apply its workflow whether or not a dispute exists. Check category and scope, exemption, competent authority, access, fee/provider arrangements, documentary proof, processing periods, and border safeguards, at a depth proportionate to the request. Identify the official national rule or practice, the applicable EU benchmark, the match in category/stage/authority, exceptions, and the practical effect. Separate a potential rule-level conflict or practical barrier from an adverse event, C5d attack-angle candidate, or infringement finding. The Czech 14/45-day example is required when its route and source applicability are established or expressly assumed.

## D. Assess law, facts, sources and evidence

For each issue, identify the responsible legal/source owner and the relevant rule, scope, conditions, exceptions, counterauthority, and evidence. Distinguish reported facts, inspected documents, official source text actually consulted, bundled snapshots, model interpretation, and unverified procedure. A country skill or source record alone does not prove that its underlying text was read. Use current official sources when the answer depends on current law. Reuse existing source research and preflight validators. Do not make a missing document a reason to withhold a legal conclusion that can already be assessed.

For every material issue, choose an answer disposition from `references/consultation-answer-contract.md`. Record its finding, support, limits, and any targeted missing fact or source. A selected check is not an assessed check; record only work actually performed.

## E. Preventive strategy and conditional action review

After the source and EU-law comparison, use `references/consultation-preventive-strategy.md` when a material friction candidate is source-supported, the user expressly requests prevention/planning/strategy, or a foreseeable decision could materially affect rights. This is a conditional C25 model-led stage, available before an application or adverse event; do not require or invent a grievance, refusal, delay, or C5d predicate.

For each material risk, identify the applicant's practical objective, the specific foreseeable decision/barrier, and whether a proportionate step before it could reduce risk. Compare feasible direct cooperation, targeted clarification, a concise legal-category statement, waiting/no extra action, and verified supervisory or formal routes where genuinely relevant. Separate legal entitlement, strategic benefit, feasibility, and evidentiary value. Recommend a suitable first step or explain why no extra action is preferable. State what response or event should trigger reassessment or conditional escalation. Keep recommendations truthful, cooperative where effective, source-grounded, and no more burdensome or confrontational than necessary.

Reuse C5e/C5f comparison and sequencing principles conversationally through C25. Do not run their synthetic-only scripts on applicant facts, create a C5d finding to unlock this stage, or claim a deterministic strategy engine ran.

## F. Review omissions and contradictions

Compare the draft against the original questions and issue list. Check for unanswered questions, merged proceedings, unsupported factual or legal conclusions, missed independent grievances or remedies, mismatched source owners, contradiction between advice and evidence, hypothetical authority arguments presented as actual grounds, and unsupported claims that an engine or validator ran. Give an urgent, appropriately qualified step without waiting for non-urgent research.

## G. Deliver the answer and coverage note

Follow `references/consultation-answer-contract.md`: answer the request directly, include any material and source-supported procedural-friction warning near the relevant step, then append the required Full or Limited board. When a material jurisdiction, proceeding/stage, source, module, or execution variable changes, refresh the board and report relevant module/source use and material gaps. Every limited item names what is missing and its effect. See `references/consultation-routing.md` for contents and limits.

**Final response check:** Inspect the actual answer before ending. For every substantive consultation, the last section must be a fresh `## freemovement-law — Consultation Review` board, even if the user never requested a dashboard. A generic `## Consultation review` table, isolated `Consultation mode` sentence, or intention to add the board later does not count. Replace a shortcut with the complete board; do not append a duplicate. Put any follow-up questions above the board, and report unperformed checks honestly.

These are stages of one model-led review. Do not describe them as independent reviews or claim that a stage executed a Python engine.
