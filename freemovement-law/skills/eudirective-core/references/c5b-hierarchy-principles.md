# C5b hierarchy, Charter scope and general-principle candidates

## Status

C5b engine/ruleset version `0.1.0` is implemented in `eudirective-core` v0.15.0 without changing the frozen C3 producer boundary: inter-skill contract `0.2.0`, conformance profile `0.2.0`, controller protocol `0.3.0`, and element model `0.2.0` remain unchanged.

C5b consumes an exact C5a legal-regime candidate artifact, the same bound element bundle, the bundled EU/common source pack, an optional typed C5b context, and optional conformant Member-State module pairs for national-rule conflict questions. It emits review candidates only. `final_hierarchy_resolution` is always `not_determined`.

## Engine

Use:

```bash
python scripts/hierarchy_principles.py case.json regimes.json \
  --elements elements.json \
  --context c5b-context.json \
  --module-pair member-state-manifest.json member-state-export.json \
  --output c5b.json
```

The `--module-pair` option is repeatable. A bound Member-State module must both conform to C3 and match a Member-State module request in the case by jurisdiction and supported role. C5b rejects unrelated national modules and unknown national rule IDs.

## Lex-specialis handling

When C5a contains simultaneous Directive 2004/38 and Visa Code candidates, C5b records an unresolved `directive_visa_code_lex_specialis` relationship. It classifies both instruments as binding secondary EU law but does not infer priority from source class alone. Issue-specific legal interpretation remains required.

## EU/national hierarchy questions

Typed `eu_vs_national` questions must reference:

- at least one EU/common source from the bundled core source pack; and
- at least one `national` rule from a conformant, case-relevant Member-State module export.

C5b may identify primacy, disapplication, consistent interpretation, equivalence and effectiveness as candidate principles. It does not establish that a conflict exists, choose a conforming interpretation, or order disapplication. Non-binding EU guidance/recommendations cannot ground a primacy/disapplication conflict path.

## Charter scope

C5b reads the scoped `legal_regime.eu_law_scope_established` element from the exact element bundle already bound by C5a:

- `true` permits a Charter-scope review candidate;
- `false` preserves a `not_indicated` state for Charter scope;
- missing scope blocks Charter promotion rather than inferring scope from EU-regime candidacy.

The Charter-scope candidate is supported by the Charter and the bundled Article 51 scope authority. It is not a finding that any particular Charter right applies or has been infringed.

## General principles

`references/principles/principle-catalog.json` is the bounded C5b catalogue. Each principle has explicit source references, an EU-law-scope requirement, and any special boundary metadata. Current candidates include direct effect, primacy, disapplication, consistent interpretation, equivalence, effectiveness, proportionality, legal certainty, legitimate expectations, Grimaldi/soft-law treatment, rights of defence, good administration, effective judicial protection, and direct Article 41 reliance.

A principle request must bind at least one existing C5a regime candidate or EU/common source through `basis_refs`. Unknown bases are rejected. Candidate generation cannot upgrade a blocked C5a chain.

Direct Article 41 reliance against a Member-State authority or national court is blocked by the explicit addressee boundary. General rights-of-defence/good-administration principles remain separate candidate paths and must be requested separately where relevant.

## Source-use boundary

C5b classifies source binding force from the verified source-pack metadata. It preserves these classes without numeric ranking:

- primary law;
- binding secondary law;
- binding judicial interpretation;
- non-binding official guidance;
- non-binding soft law;
- unknown.

Non-binding materials may be considered for interpretive support but cannot be recoded as binding rules. Commission recommendations/soft law can carry a Grimaldi review reference without becoming binding.

## Binding and privacy rules

C5b verifies the exact C5a case, element-bundle and source-pack bindings. Principle catalogue and optional C5b context digests are also recorded in output. Member-State module manifests/exports are hash-bound when used. Private case data remains disabled at the C5b engine boundary.

## Limits

C5b does not determine final legal applicability, final hierarchy, lex-specialis priority, direct effect, actual conflict, disapplication, proportionality, effectiveness, Charter infringement, national-law correctness, or applicant-facing legal advice. These remain candidate/review states until later controlled analysis and semantic legal review.
