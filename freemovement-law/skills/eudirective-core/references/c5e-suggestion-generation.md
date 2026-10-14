# C5e suggestion generation and analysis handoff

C5e is strictly downstream of legal/procedural analysis. It may generate and structurally validate strategy candidates, but it must not create facts, decide legal applicability, establish a legal violation, alter source authority, change a deadline, determine competence, or rank a route.

## 1. C5d-to-C5e promotion barrier

Use `scripts/analysis_handoff.py` before C5e. A C5d label such as `candidate` or `supported` is never sufficient by itself.

The handoff requires:

- the exact case, C5c and C5d digests;
- the exact element-bundle digest;
- replay of every country module already bound by C5d/C5c;
- a digest-bound `analysis-review-record` with an explicit rationale and reviewed evidence references;
- core attack angles to be `supported`, `sufficient_for_review`, prerequisite-satisfied, exclusion-clear and complete-for-review before promotion;
- module attack angles to receive a complete value-level overlay for every declared prerequisite/disqualifier and provenance for prerequisite facts;
- routes to be candidate/matched and to have a validated target authority level. A module route left at `unknown_frozen_contract` is not promotion-grade.

The output keeps `legal_conclusion_status=not_determined`. Promotion means only “eligible input for strategy generation.”

The local reviewer identity remains `unverified_local` unless a deployment host provides a separately verified identity mechanism.

## 2. Two stratagem layers

C5e bundles two catalogues:

- `references/stratagems/original-stratagem-catalog.json` — abstract/classical reference only. English renderings vary and this catalogue is not operational authority.
- `references/stratagems/adapted-stratagem-catalog.json` — preferred operational layer, derived from the user-supplied `36_stratagems_generalized.md`.

The ordinal mapping is one-to-one. If the abstract and adapted layers differ operationally, the adapted layer governs.

## 3. Candidate workflow

1. Build `analysis-handoff.json` with `analysis_handoff.py`.
2. Read the objective and the eligible attack-angle/route references.
3. Use the adapted catalogue to generate zero or more candidate proposals. The original catalogue may widen the search space but may not override adapted constraints.
4. Put model-proposed candidates into a `c5e-context` artifact.
5. Run `scripts/suggestion_engine.py`.
6. Treat only output under `candidates` as structurally eligible for later C5f ranking. `analysis_returns`, `non_applicable`, and `blocked` remain separate.
7. Do not present any C5e candidate as a recommendation; `recommendation_status` remains `not_ranked` until C5f.

Example:

```bash
python scripts/analysis_handoff.py case.json c5c.json c5d.json review.json \
  --elements elements.json \
  --module-pair member-state-manifest.json member-state-export.json \
  --output analysis-handoff.json

python scripts/suggestion_engine.py analysis-handoff.json c5e-context.json \
  --output c5e-candidates.json
```

## 4. Operating constraints

Apply the 24-rule suggestion contract from the architecture white paper. In particular:

- stratagems generate possibilities; they do not prove advisability;
- start from the user's actual objective;
- do not force a pattern to apply;
- separate option generation from evaluation/ranking;
- distinguish required from voluntary disclosure;
- never treat concealment as permission to falsify;
- scrutinize incoming demands rather than presuming their validity;
- before inaction/delay, resolve deadline, waiver, review-right, evidence-loss and other prejudice risks;
- preserve options and favor evidence-producing moves where otherwise comparable;
- identify new factual/legal questions as `analysis_return` and send them back to analysis;
- allow an explicit no-action result;
- changing either stratagem catalogue must be incapable of changing C5a-C5d outputs or the analysis-handoff digest.

## 5. Deterministic limits

The C5e validator can verify bindings, support references, catalogue identity, declared falsification/disclosure/deadline-risk flags, and catalogue independence. It cannot infer from arbitrary prose whether a statement is actually truthful, legally required, proportionate, ethical, or strategically wise. Those semantics remain review work and C5f must not treat a schema pass as proof of advisability.

Private-data mode remains disabled under the current host-assurance boundary.

## v0.19.0 compatible direct-baseline extension

C5e context v0.2.0 permits `candidate_kind=direct_action` with `baseline_kind` chosen from `direct_compliance`, `direct_cooperation`, `request_clarification`, or `waiting`. These neutral procedural comparators have no required stratagem ID and are **not** assigned one artificially. Direct compliance requires support from the promoted analysis handoff. A waiting direct-action candidate must declare inaction and clear deadline/waiver risks. Older v0.1.0 proposal contexts are still accepted, but they cannot assert the new direct-action kind. All C5e outputs now use engine/ruleset `0.2.0` and remain unranked.

Any no-action proposal must explicitly mark `inaction_or_delay=true` and `deadline_waiver_review=clear`; missing clearance or an unknown affirmative disclosure duty returns to analysis. A no-action label cannot serve as a bypass around deadlines, appeal rights, evidence loss or disclosure obligations. See `references/c5f-ranking-sequencing.md` for baseline comparison and ranking-stage checks.
