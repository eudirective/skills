# C5f — reviewer-bound ranking and conditional sequencing

C5f is **strictly downstream** of the C5d/C5e analysis handoff. It compares reviewed actions, not legal rights. The development-stage output is a priority-for-review artifact, not permission to execute actions or a determination that an authority violated law.

## Inputs and exact replay

1. A digest-bound `analysis-handoff` (C5d-to-C5e) artifact.
2. The exact `c5e-context` proposal set and the corresponding `c5e-suggestion-candidates` output.
3. A `c5f-context` v0.1.0 with **all** C5e candidate IDs assessed, baseline comparisons for direct compliance, cooperation, clarification, waiting and no-action, and optional pairwise relations/sequences.

C5f recomputes C5e from the handoff/context/catalogues, checks the exact result digest, and verifies the C5f review's pinned digests of **all three** preceding artifacts. Never rank a stale review merely because a suggestion ID is unchanged.

```bash
python scripts/suggestion_ranking.py analysis-handoff.json c5e-context.json \
  c5e-suggestion-candidates.json c5f-context.json --output c5f-ranking.json
```

See `references/contracts/c5f-context.schema.json` and `references/contracts/c5f-ranked-suggestions.schema.json` for the complete typed interfaces. The inter-skill producer contract remains frozen at `0.2.0`; these are internal core stages.

## Reviewer input, not invented verification

Every candidate needs a reviewer disposition and review of current assumptions, factual basis, contrary evidence, prerequisites and adverse consequences. Mark evidence as documented/reviewed, strategic inference or exploratory possibility. Exploratory-only suggestions do not become rankable. Bind rating references to already promoted attack angles/routes or their source refs. Reviewer identity is only `unverified_local`; a valid schema or local review label is not independent identity, legal or factual verification.

Assess: urgency, available remedy power, legal-support strength **as a reviewer estimate rather than a legal conclusion**, evidentiary value, reversibility, prerequisites, parallel-route compatibility, burden/cost and systemic value. Existing C5e declared reversibility/information/burden ratings cannot be silently contradicted by C5f. Unknown or contradictory ratings defer the option or return a question to analysis. A cited stratagem is never legal authority.

All five non-stratagem baselines must be marked represented, not applicable or unresolved. Existing direct-action/no-action candidates must be represented rather than hidden. An unresolved baseline prevents a unique preferred option. A rejected unsafe or contradicted candidate is excluded rather than silently discarded; an unresolved option remains pending. Do not force a stratagem advantage when a direct alternative, waiting or no action is preferable.

## Comparison and sequencing

Rank only fully reviewed eligible candidates by **Pareto-nondominated priority tiers** over ordinal reviewer factors. Do not manufacture a weighted probability of success or reduce legal hierarchy to a numeric score. A tier can contain multiple incomparable choices; give the reviewer their advantages/tradeoffs. A unique `preferred_suggestion_id` is allowed only when all comparisons and candidate review are complete and the top tier contains exactly one option. Its status remains `single_preferred_for_review` — never `approved_to_execute` or a legal finding.

Explicit relation records distinguish `conflict`, `compatible`, `precedes` and `response_before`. Reject contradictory/circular ordering. A sequence can be conditionally valid only if each adjacent transition is supported by a relation, no pair of steps conflicts, all steps are eligible, and a specific reassessment trigger is recorded. No unconditional chain execution is allowed; after an authority response or material fact/assumption change, return to analysis and regenerate the handoff/C5e/C5f bindings. An action may be useful alone and unsuitable in a chain.

## Direct and no-action alternatives

C5e context v0.2.0 additionally permits `candidate_kind=direct_action`, `baseline_kind` in `direct_compliance`, `direct_cooperation`, `request_clarification`, `waiting`, and **no stratagem** IDs; direct compliance still requires promoted support. The original context v0.1.0 remains accepted for previous stratagem-only tests. C5e engine/ruleset move to 0.2.0; output remains unranked. Direct actions without legal support are only neutral procedural choices for reviewer scrutiny and cannot claim a legal duty/remedy via C5f.

A `no_action` candidate must explicitly flag inaction and clear the deadline/waiver assessment before reaching C5f. Unknown disclosure duties or no-action deadline risk return to analysis. No action can be selected ahead of stratagems when other suggestions have been expressly rejected for known reasons and all remaining baselines are reviewed.

## Fail-closed limitations

- Do not use C5f to change C5a/C5b/C5c/C5d, the handoff, source status, fact truth, authority competence, deadline applicability or legal violations.
- Exact replay and hashes prove *input consistency*, not the legal truth of narrative reviewer assessments. Text-based claims require separate legal/factual review.
- Comparisons based on ordinal assessments are not probabilities or measured remedy effectiveness.
- The local reviewer is not a host-authenticated professional; output is for review only.
- Private-case data and write-capable automation are still disabled by upstream runtime limitations. No action is executed by this script.
