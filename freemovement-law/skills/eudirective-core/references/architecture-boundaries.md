# Architecture boundaries

## Settled product split

Use three independently versioned families:

1. one EU/core skill;
2. one Member-State skill per relevant Member State;
3. one applicant-country skill per relevant applicant country.

The core is the only reasoning/orchestration owner. Country modules are versioned data/source providers plus their own maintenance utilities.

## Authority-first ownership

Classify by issuing authority, legal function, and scope before considering country variability.

- EU law, CJEU interpretation, reusable strategy, common completeness/control logic: core.
- National law, national institutional competence, national procedure: Member-State module.
- Local operational practice, mission/VAC channels, local document realities: applicant-country module.
- Individual case data: private case workspace only.

A document mentioning Sweden is not automatically Swedish-owned. A CJEU judgment about Sweden remains an EU/common authority. A mission-specific operational fact may live in an applicant-country module even if it concerns a Swedish mission.

## No hidden coupling

- Country modules do not call each other.
- The core may compose more than one Member-State module.
- Applicant-country context is optional only where no material claim depends on it.
- Missing modules remain visible through completeness.
- Unsupported national nuance must be marked unsupported and drive a core-contract change rather than being approximated or executed as arbitrary code.

## Negative boundary

Do not put these in a country module:

- generic legal hierarchy;
- generic Charter reasoning;
- generic attack-angle or strategy engine;
- generic privacy/minimisation logic;
- generic deadline calculator;
- generic feedback/publication logic.

## C3 frozen composition boundary

- Module requests bind family + jurisdiction + role; applicant-country requests also bind a destination-state profile.
- Keep residence, work, intended residence, deciding, representing, challenged-authority and document-issuing roles distinct.
- Member-State modules may export only the `national` normative layer; applicant-country modules may export only `local_operational`; EU/common hierarchy remains core-owned.
- Reusable record IDs are namespaced and cannot collide across registered modules.
- Semantic conflicts are preserved explicitly through gaps/completeness; registration order is never a conflict-resolution rule.
- All reusable module manifests declare `data_classification=reusable_non_case`; private applicant data remains outside distributable exports.

## C5a legal-engine boundary

C5a topology and applicability logic is core-owned because it is reusable across Member States. It may consume national/local module records only through the frozen contract. Its national-procedure output is a module-role hint, not synthesized national law. Topology/applicability candidates remain separate from downstream strategy suggestions and cannot be rewritten by the future stratagem layer.
