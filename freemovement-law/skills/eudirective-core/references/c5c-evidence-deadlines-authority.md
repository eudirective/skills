# C5c Evidence, Deadline and Authority/Route Candidate Stage

## Scope

C5c is a downstream candidate/review stage. It consumes the exact bound C5a and C5b chain plus an optional element bundle, typed C5c context, and conformant country-module pairs. It does not issue final legal conclusions, evidence-sufficiency findings, deadline applicability conclusions, or route recommendations.

## Evidence / freedom of proof

C5c distinguishes three things that must not be collapsed:

- an asserted proof restriction or closed-document requirement;
- the source/rule said to support that restriction;
- a possible freedom-of-proof/open-evidence principle.

`evidence.proof_restriction_status` remains an input claim. Even an `established` label does not make the restriction legally valid. A checklist, mission instruction, applicant-country operational source, Commission guidance or other non-binding material is not silently converted into a closed legal proof rule.

The bundled Jia authority (`eu:62005cj0001`) is used only for a **dependency-evidence freedom-of-proof candidate** when dependency context exists and the bound C5a output contains a usable Directive 2004/38 candidate. C5c does not generalize Jia into a universal rule covering every documentary demand. Exact wording and pinpoints require the official judgment because the bundled representation is an identity/version-verified source note.

## Deadline engine

A module `deadline_record` may be preserved as a deadline candidate without supporting an exact date. C5c context `0.2.0` adds explicit **per-deadline scoped bindings**. Legacy context `0.1.0` remains structurally accepted, but a deadline request without a scoped binding cannot produce an exact date.

Each exact-capable deadline request must name a `binding_ref`. The referenced binding contains the exact `deadline_ref`, an actual `rule_ref` (not the deadline-record ID), and a typed `trigger_event_ref`. The event reference must resolve to a separate `temporal_events` record carrying the event type, date, evidence reference, and provenance kind.

C5c verifies that the deadline and rule come from the same conformant module, that their source support overlaps, that the trigger-event reference resolves to an explicit temporal event record, and that the scoped trigger-event type matches the deadline record's declared trigger. Model inference or a bare user assertion cannot serve as exact trigger-date evidence. The general singleton elements `time.deadline_rule_ref`, `time.deadline_trigger_ref`, `time.event_id`, `time.event_type`, and `time.event_date` remain useful case/timeline evidence but are not treated as a multi-deadline binding mechanism.

Exact date arithmetic additionally requires:

- suspension state resolved to `none`;
- extension state resolved to `none`;
- a supported operator/calendar pair;
- an explicit machine-interpretable inclusion rule;
- a valid IANA timezone identifier in the deadline record.

For the current date-only operators, timezone validation is an identity sanity check; UTC-offset resolution does not alter the arithmetic. Invalid timezone identifiers fail closed.

Current exact operators are intentionally narrow:

- calendar-day addition with `trigger_date_excluded` or `trigger_date_included`;
- month addition only with `trigger_date_excluded`.

Business-day calculations remain candidate-only because the frozen contract does not yet bind a trusted holiday/business-day calendar identity. `source_defined`, unknown operators, opaque inclusion rules, missing amounts, inferred/asserted trigger dates, unresolved suspensions/extensions, missing scoped bindings, or invalid/missing timezone IDs block exact calculation without deleting the deadline candidate.

C5c preserves suspension conditions, extension conditions and `effect_on_other_remedies` as source-backed context. It does not interpret those clauses automatically.

## Authority and escalation routes

Country-module routes are accepted only from conformant modules requested by the case. C5c binds their authority, competence, powers, limits, source refs and legal-basis refs. The frozen module contract does not contain a normalized `authority_level`, so C5c does not infer institutional level from module family or country. Module-route output therefore carries `target_authority_level_validation=unknown_frozen_contract`; core-catalogue routes carry `matched` or `mismatched`. This prevents downstream stages from mistaking an unchecked target level for a successful match.

The bounded core route catalogue currently contains:

- SOLVIT;
- European Commission Member-State EU-law complaint route;
- European Ombudsman complaint route.

Each catalogue record is bound to a current/fixed verified core source and the source verification date. These are route candidates only. C5c preserves route competence and limits and does not rank or recommend them.

Important competence boundaries include:

- SOLVIT requires a structural cross-border context plus a usable EU free-movement regime candidate before promotion;
- the Commission complaint route targets possible Member-State EU-law breaches and is not represented as an individual appeal or guaranteed individual remedy;
- the European Ombudsman route concerns EU institutions/bodies, not Member-State authorities.

## Binding rules

C5c verifies:

- exact case digest;
- exact C5a regime-candidate digest;
- exact C5b digest and its C5a/source/element bindings;
- exact element-bundle digest where C5a/C5b are element-bound;
- exact C5c context digest;
- exact core source-pack digest;
- exact core route-catalog digest;
- exact country-module manifest/export digests.

Any module already bound by C5b must be replayed identically into C5c. A blocked upstream C5a/C5b chain cannot be upgraded into a C5c evidence/deadline/route candidate.

## Privacy boundary

Private case data remains disabled at the C5c engine boundary. C5c is for synthetic/public development until host-enforced private-data isolation and the wider C4 runtime gates are demonstrated.

## Non-goals

C5c does not determine:

- final evidence sufficiency;
- whether a document request is unlawful;
- whether a freedom-of-proof principle conclusively applies;
- whether a deadline legally applies to the case;
- whether a trigger condition is substantively satisfied;
- business-day calendars;
- route admissibility beyond encoded deterministic boundaries;
- which escalation route should be chosen;
- attack-angle support;
- strategy ranking.

Those are consumed only through later controlled stages: C5d attack-angle synthesis, the explicit C5e promotion/suggestion boundary, and future C5f ranking.
