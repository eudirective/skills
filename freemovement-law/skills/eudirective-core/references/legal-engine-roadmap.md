# Legal-engine roadmap

Implement reusable legal engines from the element model, interaction rules, real source records and hardened contracts. Preserve the split-skill boundary and keep legal analysis separate from the downstream suggestion layer.

## C5 staged sequence

### C5a — topology/routing and legal-regime applicability — implemented and repaired in v0.14.0

- `scripts/topology_engine.py` preserves nationality/residence/work/host/intended residence/application/deciding/representing/document-issuing/challenged-authority roles without collapse, canonicalizes known jurisdiction aliases, and never lets a frontier-context flag erase structural residence/work divergence.
- `scripts/regime_applicability.py` emits bound review candidates for Directive 2004/38, Visa Code, Schengen and national procedure, with optional applicant/relevant-Union-citizen actor scope for family-member cases.
- returnee/Article 21 context is preserved as a separate review candidate with an explicit primary-source gap rather than a fabricated final regime conclusion.
- Directive/Visa Code coexistence emits a hierarchy/lex-specialis review flag for C5b.
- candidate output is digest-bound to case, topology, element bundle, optional actor context and source-pack manifest.

Read `references/c5a-topology-applicability.md` before changing these engines.

### C5b — hierarchy and principles — implemented in v0.15.0

- `scripts/hierarchy_principles.py` consumes the exact C5a chain and emits hierarchy, Charter-scope, source-use and legal-principle review candidates only.
- Directive/Visa Code coexistence remains an unresolved lex-specialis relationship; source legal status does not mechanically pick a winner.
- Charter promotion requires explicit scoped EU-law scope; missing scope blocks and explicit negative scope remains negative.
- `references/principles/principle-catalog.json` binds reusable principles to bundled EU/common sources and special boundaries such as direct Charter Article 41 reliance.
- non-binding guidance/soft law cannot be recoded as binding law; recommendations may retain Grimaldi review relevance.
- EU/national hierarchy questions bind actual conformant, case-relevant Member-State rule records and identify candidate primacy/disapplication/consistent-interpretation/equivalence/effectiveness paths without resolving the conflict.
- principle requests require an existing C5a regime/source basis and cannot upgrade a blocked C5a chain.

Read `references/c5b-hierarchy-principles.md` before changing these engines.

### C5c — evidence, deadlines and authority — implemented in v0.16.0; temporal binding repaired in v0.16.1

- `scripts/evidence_deadline_authority.py` consumes the exact C5a/C5b chain and emits evidence/freedom-of-proof, deadline and authority/route candidates only.
- Jia-based freedom-of-proof handling is limited to dependency evidence and is not generalized into a universal proof rule.
- proof-restriction claims must bind a source; supporting module rules are surfaced where present, but source existence does not establish legal validity.
- exact deadline arithmetic requires rule/trigger/date/timezone/suspension/extension/operator/inclusion prerequisites; business-day and source-defined calculations remain non-exact without stronger deterministic contracts.
- authority/route candidates bind conformant case-relevant country modules and a bounded EU/common route catalogue; competence, powers and limits are preserved without route ranking.
- blocked upstream C5a/C5b state cannot be upgraded by C5c.

Read `references/c5c-evidence-deadlines-authority.md` before changing this engine.

### C5d — attack-angle synthesis — implemented in v0.17.0

- `scripts/attack_angle_synthesis.py` consumes the exact bound C5a/C5b/C5c chain, the same element bundle, source pack, bounded core attack-angle catalogue and every country module already bound by C5c.
- core attack patterns require both a concrete factual/procedural signal and the required upstream source/legal basis; source presence alone never creates an angle.
- `supported` means supported for review by the encoded trigger plus source/fact provenance, while every angle keeps `legal_violation_status=not_determined`.
- exact deadlines require an independently adverse `procedure.deadline_state`; the engine does not compare dates to wall-clock time.
- proof restrictions stay review candidates, unknown authority competence is not treated as a defect, unresolved lex-specialis overlap is not a contradiction angle, and GDPR/data-minimisation allegations are not generated from personal-data/GDPR relevance alone.
- conformant module `attack_angle_records` remain candidate/review inputs because contract `0.2.0` names prerequisite/disqualifier element IDs but does not encode their expected values.
- C5d does not rank remedies, choose routes, apply stratagems or mutate C5a-C5c analysis.

Read `references/c5d-attack-angle-synthesis.md` before changing this engine.

### C5e — stratagem suggestion layer — implemented in v0.18.0

- `scripts/analysis_handoff.py` creates the explicit C5d-to-C5e promotion barrier. C5d `candidate`/`supported` labels never promote themselves.
- the handoff binds the exact case/C5c/C5d/element/module chain plus an explicit review-record digest and keeps `legal_conclusion_status=not_determined`;
- core attack angles must be promotion-grade (`supported`, sufficient-for-review, prerequisite-satisfied, exclusion-clear and complete-for-review) plus explicitly reviewed;
- module attack angles require a complete value-level overlay for every declared prerequisite/disqualifier plus prerequisite fact provenance, fixing the value-agnostic contract-0.2.0 gap without changing the frozen producer contract;
- module routes with `target_authority_level_validation=unknown_frozen_contract` remain non-promotable;
- the user-supplied `36_stratagems_generalized.md` is compiled into the preferred adapted operational catalogue, while a separate original/classical catalogue remains abstract/reference-only;
- `scripts/suggestion_engine.py` validates model-proposed candidate actions against the handoff and catalogues, blocks invented support, falsification-dependent tactics and disclosure-duty conflicts, returns unresolved disclosure or inaction/deadline-waiver questions to analysis, and permits non-applicable/no-action outputs;
- every C5e output remains `recommendation_status=not_ranked`; C5f owns sequencing/ranking and surfaced recommendation status;
- catalogue mutation must not alter C5a-C5d analysis or the analysis-handoff digest.

Read `references/c5e-suggestion-generation.md` before changing this stage.

### C5f — reviewer-bound suggestion ranking and conditional sequencing — implemented in v0.19.0

- `scripts/suggestion_ranking.py` pins the exact handoff, C5e proposal set, C5e output and reviewer assessments, then replays C5e rather than trusting candidate labels.
- C5e now allows neutral direct-action baselines (no forced stratagem), and no-action requires explicit deadline/waiver clearance.
- Every candidate and each of direct compliance, cooperation, clarification, waiting and no-action is dispositioned before any preference.
- Compare urgency, remedy power, **reviewed** legal support, evidentiary value, reversibility, prerequisites, route compatibility, burden/cost and systemic value without converting them into legal truth or arbitrary weighted probabilities.
- Prefer Pareto priority tiers and show tradeoffs. Exclude known unsafe/contradicted options; defer missing/unknown/changed facts and unresolved alternatives.
- Conflicts, precedence cycles and unreviewed combinations cannot produce unconditional chains. Every allowed sequence requires reassessment after a material response.
- Output statuses are `single_preferred_for_review`, `alternatives_for_review`, `insufficient_for_ranking` or `no_safe_option_for_review`; legal conclusion remains `not_determined`. Never execute actions automatically.

Read `references/c5f-ranking-sequencing.md` before changing or relying on C5f.

## Rules for implementation

- Consume national/local records through the contract; do not import country-specific reasoning into core code.
- Define required inputs in terms of catalogued elements and source-backed records.
- Keep facts, assertions, calculations, legal interpretations, contrary evidence and unresolved gaps distinct.
- Bind material outputs to source/fact dependencies.
- A schema or invariant pass validates structure, not legal support.
- Where an EU/common evaluator needs a country-specific condition, keep the evaluator in core and the authoritative national fact/rule in the Member-State module.
- Unsupported nuance becomes an explicit unsupported/blocked state or a model/contract change request, never arbitrary Python in a module export.
- Add atomic fixtures for new structural interactions and counterconditions. Do not require a canonical whole-case answer.
- Use generated combinations to find representational or coupling failures, then perform source-backed legal review for substantive conclusions.
- Do not convert C5a `candidate` into `applicable`; later semantic review must own that transition.
- Do not infer returnee status from geography alone or frontier-worker legal status from different work/residence states alone. Treat residence/work divergence as structural even when a contextual frontier-worker flag says otherwise; surface the contradiction for review.
- In family-member cases, bind applicant and relevant Union-citizen actors explicitly; never assign a singleton person-status value to one of them by guesswork.
- Canonicalize known jurisdiction aliases before equality checks and preserve unknown labels rather than inventing identity.
- Source hints are discovery/provenance aids, not entailment proof.

## Attack-angle catalogue coverage and remaining model gaps

- appointment/lodgement/access impediments are implemented; digital-only legality still needs a more explicit requirement/alternative-channel factual predicate;
- complaint/review-path review is implemented when paired with a source-backed C5b principle candidate;
- exact deadline/timeliness review is implemented only with an independently adverse timeliness state;
- dependency-scoped freedom-of-proof and source-bound proof-restriction review are implemented;
- broader excessive/irrelevant-document analysis still needs issue-specific necessity/relevance predicates;
- principle-backed procedural fairness/good-administration synthesis remains limited to currently modeled complaint/proportionality signals;
- explicit source-backed authority-competence review is implemented; unknown competence is not a defect;
- missing reasons/review-information synthesis still needs a dedicated factual predicate and source-specific duty model;
- timing synthesis is implemented for exact deadlines plus adverse state; consultation-specific duties remain future work;
- data-minimisation/privacy auto-synthesis is intentionally deferred until authority-processing purpose/necessity/excess facts are modeled;
- unresolved hierarchy/lex-specialis is explicitly not treated as contradiction; a dedicated contradiction comparator remains future work;
- escalation-failure synthesis remains future work; C5c/C5d preserve route competence/power limits without ranking.

Data corruption, stale sources, unsupported operators or missing sources route to maintenance/completeness, not automatically to a legal violation.
