# C3 module conformance kit

Use this kit when building or checking a `core_source`, `member_state`, or `applicant_country` producer.

## Deterministic checks

Validate JSON shape first:

```bash
python scripts/contract_validate.py --schema module-manifest manifest.json
python scripts/contract_validate.py --schema module-export export.json
```

Then validate the pair semantically:

```bash
python scripts/module_conformance.py manifest.json export.json
```

The conformance validator checks the identity tuple, namespace ownership, supported roles, version compatibility, legal-layer boundaries, gap linkage, source-backed records, route-authority links, attack-angle element/authority/route references, applicant operational destination profiles, and representation-scope rules.

## Profiles

Machine-readable family policy:

`references/conformance/module-conformance-profile-0.2.0.json`

The profile freezes:

- contract `0.2.0`;
- controller protocol `0.3.0`;
- element model `0.2.0`;
- permitted roles and legal layers for each module family;
- composition rules for collisions, missing modules, and legal hierarchy.

## Fixtures

Positive fixtures:

- `references/fixtures/conformance/member-state-se-minimal-manifest.json`
- `references/fixtures/conformance/member-state-se-minimal-export.json`
- `references/fixtures/conformance/applicant-country-xx-minimal-manifest.json`
- `references/fixtures/conformance/applicant-country-xx-minimal-export.json`
- `references/fixtures/conformance/case-frontier-worker-topology.json`

Negative fixtures:

- `invalid-applicant-namespace-export.json`;
- `invalid-applicant-national-rule-export.json`;
- `invalid-incompatible-manifest.json`.

These are atomic interface/topology fixtures, not narrative golden cases and not legal-answer oracles.

## Composition invariants

- Required module absence blocks context freeze.
- Optional module absence remains an explicit scoped gap.
- Role matching is exact.
- Applicant-country destination profiles must match the requested destination state.
- Multiple Member-State modules are allowed simultaneously.
- Global reusable record-ID collisions are rejected.
- Duplicate producers for the same family + jurisdiction + role are rejected.
- Module requests must agree with typed case geography.
- Controlled analysis must resolve reusable deadline, route, and attack-angle references.
- Country modules cannot claim the EU/common normative layer.
- Applicant-country modules cannot claim the national normative layer.
- Semantic conflicts are preserved, not silently resolved by registration order.
