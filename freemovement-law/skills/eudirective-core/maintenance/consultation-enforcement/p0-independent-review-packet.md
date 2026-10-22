# P0 consultation routing: independent legal and privacy review packet

**Prepared:** 2026-10-23
**Candidate:** `freemovement-law` 0.58.0 / `eudirective-core` 0.57.0; strict consultation receipt 0.5.0
**Review state:** `pending_independent_review`
**Reviewer / date / decision:** not completed

## Purpose and boundary

This packet makes the routing and source-class rules inspectable for an independent legal/privacy reviewer. It is not an approval record and does not clear production review flags. The test-only reviewed configuration used by the synthetic integration test exists only in a disposable temporary copy. No real applicant facts were used. Structural checks do not establish legal correctness, source authentication, or complete issue identification. C5d/C11 candidate material is not a legal violation finding.

## Adverse-predicate mapping decision

The strict receipt distinguishes the neutral signal that selects a route from the topic-specific condition that could support a potential-issue candidate. Existing priority pathways declare an `adverse_signal`; their screening state is recorded separately. Most general route review prompts do not yet have a mapped adverse condition. They must remain `unresolved` with reason `predicate_unmapped`, appear as missing in the dashboard, and prevent a comprehensive claim. The reviewer should either supply a justified, narrowly scoped condition for each prompt or confirm that it should remain unresolved. Do not treat the route trigger alone as evidence of an adverse condition.

## Route-by-route review register

For each route, review whether its trigger signals are sufficiently narrow, the C27 checks identify necessary fact/rule/procedure questions, the owner/class mapping is justified, cited source records are suitable and currentness-limited, and negative cases prevent over-routing. Route and source-class metadata remain pending review.

### `directive_personal_and_territorial_applicability`

- **Trigger:** any_signal: directive_scope_question
- **Mandatory C27 checks:** eu_scope.directive_scope; case_intake.actor_roles; case_intake.relationship_basis; case_intake.geographic_roles
- **Conditional C27 checks:**
  - movement_or_cross_border_context -> eu_scope.movement_exercised
  - returnee_context -> eu_scope.returnee_derived_rights; country.national_extension
  - family_relationship_question -> country.status_recognition
- **Owner/source-class policy:**
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (directive_scope_question; family_relationship_question; movement_or_cross_border_context): case_law — case_law_context_triggered
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (movement_or_cross_border_context; returnee_context): national_binding_law — national_law_scope_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** eu:32004l0038; references/c23-applicant-case-guidance.md; references/c5a-topology-applicability.md
- **Attack-screen review topics:** competing legal regime; territorial or personal-scope exception; contrary authority or fact that changes the claimed topology
- **Negative applicability:** A generic visa enquiry, provider fee, or complaint alone does not activate this route.
- **Related separate issues:** pre_lodgement_obstruction_and_appointment_access; processing_delay_or_clock_trigger; remedy_or_supervisory_track
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `eu_citizen_accompanying_or_joining`

- **Trigger:** any_signal: accompanying_or_joining_question
- **Mandatory C27 checks:** eu_scope.directive_scope; eu_scope.movement_exercised; eu_scope.accompany_or_join; case_intake.relationship_basis; case_intake.geographic_roles
- **Conditional C27 checks:**
  - returnee_context -> eu_scope.returnee_derived_rights; country.national_extension
  - family_relationship_question -> eu_scope.family_recognition; documents.family_status_records
- **Owner/source-class policy:**
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (accompanying_or_joining_question; family_relationship_question): case_law — case_law_context_triggered
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (returnee_context): national_binding_law — national_law_scope_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** eu:32004l0038; references/c23-applicant-case-guidance.md; references/c5a-topology-applicability.md
- **Attack-screen review topics:** different travel dates or travel sequence; whether movement is qualifying; family status and any recognised exception
- **Negative applicability:** A family member's travel question without a claimed Union-citizen movement link does not by itself establish Directive coverage.
- **Related separate issues:** directive_personal_and_territorial_applicability; ordinary_document_list_or_eu_family_requirements
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `prior_refusal_and_legal_status_change`

- **Trigger:** any_signal: prior_refusal_or_status_change
- **Mandatory C27 checks:** case_intake.proceedings_identified; lifecycle.decision_taken; lifecycle.decision_notified; authority.actual_ground; authority.position_provenance; eu_scope.directive_scope
- **Conditional C27 checks:**
  - prior_refusal_predates_claimed_status -> case_intake.applicant_prior_actions; authority.ground_change; lifecycle.procedural_reopening
  - formal_refusal_issued -> remedies.formal_appeal; timing.service_date; timing.appeal_limit
- **Owner/source-class policy:**
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (formal_refusal_issued; prior_refusal_or_status_change): case_law — case_law_context_triggered
    - Conditional (formal_refusal_issued; prior_refusal_or_status_change): contrary_authority — adverse_or_remedy_issue_triggered
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (formal_refusal_issued; prior_refusal_or_status_change): national_binding_law — national_law_scope_triggered
    - Conditional (formal_refusal_issued; prior_refusal_or_status_change): case_law — national_decision_or_remedy_triggered
    - Conditional (formal_refusal_issued): contrary_authority — adverse_or_remedy_issue_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** references/c23-applicant-case-guidance.md; references/c24-fact-rule-revision.md; references/c5c-evidence-deadlines-authority.md
- **Attack-screen review topics:** which legal status existed at each event; whether the prior decision is being treated as a current ground without support; whether service or a later decision creates a separate deadline
- **Negative applicability:** An application, appointment, or complaint alone does not establish a prior refusal or a later status change.
- **Related separate issues:** remedy_or_supervisory_track; processing_delay_or_clock_trigger
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `member_state_versus_eu_swiss_framework`

- **Trigger:** any_signal: swiss_free_movement_framework_question
- **Mandatory C27 checks:** eu_scope.directive_scope; eu_scope.movement_exercised; country.multiple_jurisdictions; sources.binding_classification; sources.official_publisher; sources.source_currentness
- **Conditional C27 checks:**
  - family_relationship_question -> country.status_recognition; proof.national_evidence_rules
  - formal_refusal_issued -> authority.actual_ground; authority.position_provenance; remedies.formal_appeal
- **Owner/source-class policy:**
  - **eu_swiss_framework**
    - Required: eu_binding_law
    - Conditional (family_relationship_question; swiss_free_movement_framework_question): case_law — treaty_interpretation_triggered
    - Conditional (swiss_free_movement_framework_question): official_guidance — treaty_guidance_relevant
    - Explicit exclusions: national_binding_law — national_implementation_requires_member_state_owner; procedural_rule — national_procedure_requires_member_state_owner
  - **member_state_law**
    - Conditional (formal_refusal_issued; swiss_free_movement_framework_question): national_binding_law — national_law_scope_triggered
    - Conditional (formal_refusal_issued): case_law — national_decision_or_remedy_triggered
    - Conditional (formal_refusal_issued): contrary_authority — adverse_or_remedy_issue_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** Official EU–Swiss Agreement on the Free Movement of Persons text at EUR-Lex or Fedlex; ../eudirective-source-library/switzerland/README.md; ../eudirective-source-library/references/eea-switzerland-country-expansion.md
- **Attack-screen review topics:** Directive versus bilateral-agreement legal basis; personal and material scope of the agreement; Swiss domestic implementation and available remedy
- **Negative applicability:** Do not select this route solely because a Swiss location or a generic European free-movement question is mentioned.
- **Related separate issues:** prior_refusal_and_legal_status_change; remedy_or_supervisory_track
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `pre_lodgement_obstruction_and_appointment_access`

- **Trigger:** any_signal: pre_lodgement_access_obstruction
- **Mandatory C27 checks:** lifecycle.enquiry_state; lifecycle.appointment_request; lifecycle.lodgement_attempted; lifecycle.lodgement_confirmed; access.appointment_wait; access.refusal_to_lodge; timing.pre_lodgement_delay
- **Conditional C27 checks:**
  - appointment_delay -> access.direct_access; timing.urgent_preservation
  - physical_exclusion_or_staff_treatment; staff_conduct -> conduct.staff_treatment; conduct.physical_exclusion; conduct.complaint_channel; conduct.independent_outcomes; remedies.conduct_supervision
- **Owner/source-class policy:**
  - **applicant_country_operations**
    - Required: official_guidance
    - Conditional (appointment_delay; pre_lodgement_access_obstruction): procedural_rule — application_channel_or_timing_triggered
    - Explicit exclusions: case_law — legal_interpretation_belongs_to_legal_source_owner; contrary_authority — legal_interpretation_belongs_to_legal_source_owner; eu_binding_law — eu_common_law_belongs_to_core_owner; national_binding_law — national_law_belongs_to_member_state_owner
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (appointment_delay; pre_lodgement_access_obstruction): official_guidance — operational_guidance_relevant
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (appointment_delay; pre_lodgement_access_obstruction): national_binding_law — national_law_scope_triggered
    - Conditional (appointment_delay; pre_lodgement_access_obstruction): procedural_rule — national_procedure_triggered
    - Conditional (pre_lodgement_access_obstruction): official_guidance — national_guidance_relevant
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** references/c23-applicant-case-guidance.md; references/c5c-evidence-deadlines-authority.md; references/architecture-boundaries.md
- **Attack-screen review topics:** appointment access versus a decision on the merits; evidence of attempted submission and any receipt; the exact legal basis for direct access or use of a service provider
- **Negative applicability:** Do not label a pre-lodgement access event a formal visa refusal without a formal decision.
- **Related separate issues:** external_service_provider_and_fees; processing_delay_or_clock_trigger; remedy_or_supervisory_track; personal_data_protection; ephemeral_evidence_preservation
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `external_service_provider_and_fees`

- **Trigger:** any_signal: external_service_provider_used
- **Mandatory C27 checks:** access.service_provider_accountability; access.direct_access; authority.staff_responsibility
- **Conditional C27 checks:**
  - provider_fee_disputed -> access.outsourcing_fees; access.fee_waiver
- **Owner/source-class policy:**
  - **applicant_country_operations**
    - Required: official_guidance
    - Conditional (external_service_provider_used): procedural_rule — application_channel_or_timing_triggered
    - Explicit exclusions: case_law — legal_interpretation_belongs_to_legal_source_owner; contrary_authority — legal_interpretation_belongs_to_legal_source_owner; eu_binding_law — eu_common_law_belongs_to_core_owner; national_binding_law — national_law_belongs_to_member_state_owner
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (external_service_provider_used): official_guidance — operational_guidance_relevant
    - Conditional (provider_fee_disputed): contrary_authority — adverse_or_remedy_issue_triggered
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (external_service_provider_used; provider_fee_disputed): national_binding_law — national_law_scope_triggered
    - Conditional (external_service_provider_used): procedural_rule — national_procedure_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** eu:32009r0810; eu:visa-code-handbook-i-2024; references/c23-applicant-case-guidance.md; references/architecture-boundaries.md
- **Attack-screen review topics:** visa fee versus optional provider service fee; the Member State's responsibility for outsourced processing; direct access rule, if any, under the exact applicable arrangement
- **Negative applicability:** signal_id: provider_fee_not_disputed; opposes_signal_id: provider_fee_disputed; excluded_check_ids: access.outsourcing_fees; access.fee_waiver; reason: When no provider-fee dispute is declared, do not select fee-specific checks merely because a provider is used.
- **Related separate issues:** pre_lodgement_obstruction_and_appointment_access; ordinary_document_list_or_eu_family_requirements; remedy_or_supervisory_track
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `digital_only_channel_and_accessibility`

- **Trigger:** any_signal: digital_only_access_requirement
- **Mandatory C27 checks:** access.digital_only; access.direct_access; access.appointment_wait; documents.ordinary_checklist_scope; authority.competence
- **Conditional C27 checks:**
  - None registered.
- **Owner/source-class policy:**
  - **applicant_country_operations**
    - Required: official_guidance
    - Conditional (digital_only_access_requirement): procedural_rule — application_channel_or_timing_triggered
    - Explicit exclusions: case_law — legal_interpretation_belongs_to_legal_source_owner; contrary_authority — legal_interpretation_belongs_to_legal_source_owner; eu_binding_law — eu_common_law_belongs_to_core_owner; national_binding_law — national_law_belongs_to_member_state_owner
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (digital_only_access_requirement): official_guidance — operational_guidance_relevant
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (digital_only_access_requirement): national_binding_law — national_law_scope_triggered
    - Conditional (digital_only_access_requirement): procedural_rule — national_procedure_triggered
    - Conditional (digital_only_access_requirement): official_guidance — national_guidance_relevant
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** eu:32009r0810; references/consultation-topic-review-pathways.json; references/architecture-boundaries.md
- **Attack-screen review topics:** whether the digital channel is mandatory for this procedure and date; the mission or service provider's role and any effective alternative; accessibility or practical barriers that change the route
- **Negative applicability:** Do not infer a digital-only requirement from the mere existence or use of an online portal.
- **Related separate issues:** external_service_provider_and_fees; pre_lodgement_obstruction_and_appointment_access; processing_delay_or_clock_trigger
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `ordinary_document_list_or_eu_family_requirements`

- **Trigger:** any_signal: ordinary_document_list_or_eu_family_document_question
- **Mandatory C27 checks:** documents.requested_item; documents.requested_legal_basis; documents.ordinary_checklist_scope; documents.mandatory_vs_optional; documents.alternative_proof
- **Conditional C27 checks:**
  - document_demand -> documents.provider_document_rules; documents.legalisation_apostille; documents.translations
  - missing_document -> documents.missing_document; documents.proof_completeness; proof.proof_freedom
- **Owner/source-class policy:**
  - **applicant_country_operations**
    - Required: official_guidance
    - Conditional (ordinary_document_list_or_eu_family_document_question): procedural_rule — application_channel_or_timing_triggered
    - Explicit exclusions: case_law — legal_interpretation_belongs_to_legal_source_owner; contrary_authority — legal_interpretation_belongs_to_legal_source_owner; eu_binding_law — eu_common_law_belongs_to_core_owner; national_binding_law — national_law_belongs_to_member_state_owner
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (ordinary_document_list_or_eu_family_document_question): official_guidance — operational_guidance_relevant
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (document_demand; missing_document; ordinary_document_list_or_eu_family_document_question): national_binding_law — national_law_scope_triggered
    - Conditional (ordinary_document_list_or_eu_family_document_question): procedural_rule — national_procedure_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** eu:32004l0038; eu:32009r0810; eu:visa-code-handbook-i-2024; references/c23-applicant-case-guidance.md
- **Attack-screen review topics:** ordinary checklist applicability to the applicant category; the item's actual purpose and legal basis; alternative proof, proportionality, and any specific exception
- **Negative applicability:** Do not activate this route for an unrelated ordinary visitor checklist unless an EU-family or free-movement issue is also declared.
- **Related separate issues:** eu_citizen_accompanying_or_joining; external_service_provider_and_fees; pre_lodgement_obstruction_and_appointment_access
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `processing_delay_or_clock_trigger`

- **Trigger:** any_signal: processing_delay_or_deadline_question
- **Mandatory C27 checks:** timing.clock_start; timing.lodgement_trigger; timing.applicable_rule; timing.accelerated_processing; timing.pre_lodgement_delay
- **Conditional C27 checks:**
  - formal_lodgement_confirmed -> lifecycle.lodgement_confirmed; lifecycle.receipt_evidence; timing.exceptions_and_extension; timing.suspension
  - appeal_deadline_risk -> timing.service_date; timing.appeal_limit; remedies.formal_appeal
- **Owner/source-class policy:**
  - **applicant_country_operations**
    - Required: official_guidance
    - Conditional (processing_delay_or_deadline_question): procedural_rule — application_channel_or_timing_triggered
    - Explicit exclusions: case_law — legal_interpretation_belongs_to_legal_source_owner; contrary_authority — legal_interpretation_belongs_to_legal_source_owner; eu_binding_law — eu_common_law_belongs_to_core_owner; national_binding_law — national_law_belongs_to_member_state_owner
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (processing_delay_or_deadline_question): official_guidance — operational_guidance_relevant
    - Conditional (appeal_deadline_risk): contrary_authority — adverse_or_remedy_issue_triggered
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (appeal_deadline_risk; processing_delay_or_deadline_question): national_binding_law — national_law_scope_triggered
    - Conditional (appeal_deadline_risk; processing_delay_or_deadline_question): procedural_rule — national_procedure_triggered
    - Conditional (appeal_deadline_risk): case_law — national_decision_or_remedy_triggered
    - Conditional (processing_delay_or_deadline_question): official_guidance — national_guidance_relevant
    - Conditional (appeal_deadline_risk): contrary_authority — adverse_or_remedy_issue_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** eu:32004l0038; eu:32009r0810; references/c5c-evidence-deadlines-authority.md; references/c23-applicant-case-guidance.md
- **Attack-screen review topics:** enquiry, appointment, and formal lodging as different clock events; legal basis and any exception or extension; parallel appeal deadline that a complaint does not suspend
- **Negative applicability:** A complaint or appointment question alone does not activate this route unless a processing delay, clock, or deadline issue is declared.
- **Related separate issues:** pre_lodgement_obstruction_and_appointment_access; prior_refusal_and_legal_status_change; remedy_or_supervisory_track
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `remedy_or_supervisory_track`

- **Trigger:** any_signal: remedy_or_solvit_or_supervisory_complaint
- **Mandatory C27 checks:** case_intake.linked_proceedings; lifecycle.challenge_stage; remedies.remedy_compatibility; remedies.competent_authority; authority.supervisory_path
- **Conditional C27 checks:**
  - formal_refusal_issued; appeal_deadline_risk -> remedies.formal_appeal; timing.service_date; timing.appeal_limit
  - solvit_involved -> remedies.solvit; remedies.remedy_compatibility
  - staff_conduct -> conduct.complaint_channel; remedies.conduct_supervision; conduct.independent_outcomes
- **Owner/source-class policy:**
  - **eu_common_core**
    - Required: eu_binding_law
    - Conditional (formal_refusal_issued): case_law — case_law_context_triggered
    - Conditional (appeal_deadline_risk; formal_refusal_issued; remedy_or_solvit_or_supervisory_complaint): contrary_authority — adverse_or_remedy_issue_triggered
    - Explicit exclusions: national_binding_law — national_law_belongs_to_member_state_owner; procedural_rule — national_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (appeal_deadline_risk; formal_refusal_issued; remedy_or_solvit_or_supervisory_complaint): national_binding_law — national_law_scope_triggered
    - Conditional (appeal_deadline_risk; remedy_or_solvit_or_supervisory_complaint): procedural_rule — national_procedure_triggered
    - Conditional (appeal_deadline_risk; formal_refusal_issued; remedy_or_solvit_or_supervisory_complaint): case_law — national_decision_or_remedy_triggered
    - Conditional (remedy_or_solvit_or_supervisory_complaint): official_guidance — national_guidance_relevant
    - Conditional (appeal_deadline_risk; formal_refusal_issued; remedy_or_solvit_or_supervisory_complaint): contrary_authority — adverse_or_remedy_issue_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** references/c23-applicant-case-guidance.md; references/c25-applicant-strategy.md; references/c5c-evidence-deadlines-authority.md
- **Attack-screen review topics:** formal decision versus administrative grievance; competent body and exact power to grant the requested relief; parallel routes and preserved deadlines
- **Negative applicability:** A complaint label alone does not create a statutory visa appeal or prove that a formal decision exists.
- **Related separate issues:** pre_lodgement_obstruction_and_appointment_access; personal_data_protection; ephemeral_evidence_preservation; prior_refusal_and_legal_status_change
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `personal_data_protection`

- **Trigger:** any_signal: personal_data_processing_question
- **Mandatory C27 checks:** gdpr.lawful_basis; gdpr.purpose_limitation; gdpr.data_minimisation; gdpr.controller_identity
- **Conditional C27 checks:**
  - ephemeral_evidence_at_risk -> gdpr.preservation_request; gdpr.retention_obligations; timing.urgent_preservation
- **Owner/source-class policy:**
  - **eu_data_protection**
    - Required: eu_binding_law
    - Conditional (personal_data_processing_question): procedural_rule — supervisory_or_procedure_triggered
    - Conditional (personal_data_processing_question): case_law — data_protection_interpretation_triggered
    - Explicit exclusions: national_binding_law — national_supervisory_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (ephemeral_evidence_at_risk; personal_data_processing_question): national_binding_law — national_law_scope_triggered
    - Conditional (ephemeral_evidence_at_risk; personal_data_processing_question): procedural_rule — national_procedure_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** Official GDPR text and current competent supervisory-authority procedure; references/c21-privacy-and-anonymisation.md; references/c25-evidence-acquisition.md
- **Attack-screen review topics:** whether the issue is actually about personal data; purpose, necessity, and the precise controller; national supervisory competence and any scope exception
- **Negative applicability:** Do not select GDPR checks solely because a visa application, complaint, or non-personal evidence-preservation request exists.
- **Related separate issues:** pre_lodgement_obstruction_and_appointment_access; remedy_or_supervisory_track
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

### `ephemeral_evidence_preservation`

- **Trigger:** any_signal: ephemeral_evidence_at_risk
- **Mandatory C27 checks:** timing.urgent_preservation; proof.unexamined_records; strategy.preservation_first
- **Conditional C27 checks:**
  - evidence_record_contains_personal_data -> gdpr.cctv; gdpr.preservation_request; gdpr.retention_obligations; gdpr.controller_identity
  - physical_exclusion_or_staff_treatment; staff_conduct -> conduct.evidence_loss; conduct.independent_outcomes; remedies.conduct_supervision
- **Owner/source-class policy:**
  - **eu_data_protection**
    - Required: eu_binding_law
    - Explicit exclusions: national_binding_law — national_supervisory_procedure_belongs_to_member_state_owner
  - **member_state_law**
    - Conditional (ephemeral_evidence_at_risk): national_binding_law — national_law_scope_triggered
    - Conditional (ephemeral_evidence_at_risk): procedural_rule — national_procedure_triggered
    - Explicit exclusions: eu_binding_law — eu_common_law_belongs_to_core_owner
- **Source references:** references/c5c-evidence-deadlines-authority.md; references/c25-evidence-acquisition.md
- **Attack-screen review topics:** specific record and likely deletion or overwrite time; competent holder and proportionate preservation request; whether the record contains personal data, which would add a separate GDPR question
- **Negative applicability:** Do not select an urgent preservation route from a generic complaint or records request without evidence at risk of loss.
- **Related separate issues:** personal_data_protection; pre_lodgement_obstruction_and_appointment_access; remedy_or_supervisory_track
- **Reviewer decision:** pending; confirm trigger coverage, owner/class applicability, source scope/currentness, exceptions, and false-positive boundary.

## Six priority pathway review register

Each pathway is a candidate-review screen. A triggered screen may identify an issue for separate assessment; it does not establish a breach, grievance, or legal outcome. Confirm each signal-to-route binding, applicable C27 family, relevant owner/source class, and counterexample before approving the pathway.

### `pre_lodgement_obstruction` — Possible obstruction before formal lodging

- **Signal and route binding:**
  - pre_lodgement_obstruction_and_appointment_access (pre_lodgement_access_obstruction)
- **C27 families:** lifecycle; access; authority
- **Coverage binding:** core:attack:procedural-access-review
- **Adverse signal screened:** A person attempted to submit an application or required form, and an identified authority or service channel prevented acceptance before a formal decision or receipt was created.
- **Sources and provisions to verify:**
  - eu:32004l0038 [binding_eu_law] — Article 5(2); Articles 30-31 where applicable (official_EUR-Lex_text_checked_2026-10-20; confirm applicable version and national implementation for case date)
  - eu:32009r0810 [binding_eu_law] — Articles 9, 19 and 43; Article 17(5): a Member State may maintain direct lodging at its consulate; verify the actual State route (official_consolidation_2024-06-28_checked_2026-10-20; amendment and case-date check required)
  - commission:visa-code-handbook-I-2024 [official_nonbinding_operational_guidance] — Part II, sections 2.2.1-2.2.2; Part III for EU-family safeguards (Commission C(2024) 4319 final checked 2026-10-20; nonbinding guidance; verify later replacement)
- **Counterarguments and exceptions:**
  - A request to use an appointment, provide a complete form, attend biometrics, or approach a competent mission is not automatically a refusal to lodge.
  - A service provider may perform limited intake tasks under an applicable arrangement; examination and decision remain with the consulate under the Visa Code.
  - The authority, procedure, urgency, representation arrangement, and any usable alternative channel may change the analysis.
  - Visa Code Article 17(5) permits a Member State to maintain a direct-lodging possibility; do not turn that wording into a universal direct-lodging entitlement. Article 43(6) permits specified provider intake/logistics, while Article 43(4) reserves examination and decisions to the consulate.
- **Records to seek:**
  - Dated lodging attempt and exact form/version
  - Written instructions or refusal, including sender and authority role
  - Portal status, receipt, appointment record, and subsequent correspondence
  - Available alternative channel and any access or accessibility barrier
  - Current deciding/representing Member State instructions showing whether direct consular lodging is maintained, provider tasks, appointment channel, and any refusal or alternative offered
- **Competence and limits:** The national competent authority and urgent judicial route are not resolved by this shared EU review record. Do not describe a pre-lodgement access problem as a formal refusal without evidence. Article 17(5) does not establish a universal direct-channel obligation; check the current Member-State arrangement and any separate Directive-based facilitation requirement.
- **Reviewer decision:** pending; confirm screen predicate, source classes, exceptions, negative cases, and whether any candidate must remain unresolved.

### `digital_only_access` — Digital-only or service-provider access requirement

- **Signal and route binding:**
  - digital_only_channel_and_accessibility (digital_only_access_requirement)
- **C27 families:** access; documents; authority
- **Coverage binding:** core:attack:procedural-access-review
- **Adverse signal screened:** A digital platform, VAC, or intermediary is said to be the only way to request or lodge, and the person reports being unable to use it or reach an effective alternative.
- **Sources and provisions to verify:**
  - eu:32009r0810 [binding_eu_law] — Articles 9(2)-(3), 10(1), 11, 43(4),(6), 44 and 45 (official_consolidation_2024-06-28_checked_2026-10-20; amendment and case-date check required)
  - candidate:eu:32023r2667 [binding_amending_eu_law] — Article 7: EU VAP start requires a separate Commission decision; Member States may notify a transition opt-out of up to seven years (Official Journal text checked 2026-10-20; not in pinned core pack; check start decision and Member-State notice at case date)
  - commission:visa-code-handbook-I-2024 [official_nonbinding_operational_guidance] — Part II, section 2.2.1: urgent appointment/direct access; section 2.2.2: appointment timing (Commission C(2024) 4319 final checked 2026-10-20; nonbinding guidance; verify later replacement)
- **Counterarguments and exceptions:**
  - Visa Code Article 10(1) permits electronic lodgement where available, while personal appearance may be required for fingerprint collection; assess the actual route and exceptions.
  - Regulation (EU) 2023/2667 Article 7 makes EU VAP operation dependent on a Commission start-date decision and permits Member-State transition opt-outs; do not infer a live or exclusive EU-wide platform from the regulation alone.
  - External service providers may perform specified intake tasks, but examination and the visa decision remain with the consulate under Article 43(4); a service-provider logistics requirement does not itself establish unlawful access.
- **Records to seek:**
  - Exact platform message and date
  - Published instructions and version
  - Alternative or assisted channel and response
  - Any representation arrangement, accessibility need, or failed upload record
- **Competence and limits:** No general illegality inference follows from a digital process. Competence, commencement, alternatives, and national accessibility remedies require separate checking.
- **Reviewer decision:** pending; confirm screen predicate, source classes, exceptions, negative cases, and whether any candidate must remain unresolved.

### `eu_family_documentary_proof` — EU-family proof and ordinary Schengen checklist

- **Signal and route binding:**
  - ordinary_document_list_or_eu_family_requirements (ordinary_document_list_or_eu_family_document_question)
- **C27 families:** eu_scope; proof; documents
- **Coverage binding:** core:attack:proof-restriction-review
- **Adverse signal screened:** An authority is reported to reject or refuse to consider relevant evidence of EU-citizen identity, family relationship, dependency, or accompanying/joining because it is not on a stated list.
- **Sources and provisions to verify:**
  - eu:32004l0038 [binding_eu_law] — Articles 2, 3 and 5(2) (official_EUR-Lex_text_checked_2026-10-20; confirm applicable version and national implementation for case date)
  - eu:32009r0810 [binding_eu_law] — Article 14(3) (Annex II is non-exhaustive), Article 21 (official_consolidation_2024-06-28_checked_2026-10-20; amendment and case-date check required)
  - candidate:eu:52023xc01392 [official_nonbinding_guidance] — Section 2.2.4: relevant alternative evidence may not be refused solely because it is not the preferred document type (Official Journal guidance checked 2026-10-20; nonbinding; not in pinned core pack)
  - commission:visa-code-handbook-I-2024 [official_nonbinding_operational_guidance] — Part III: assess the Visa Code together with the specific Directive/Withdrawal Agreement rules for eligible family members (Commission C(2024) 4319 final checked 2026-10-20; nonbinding guidance; verify later replacement)
  - candidate:eu:32016r1191 [binding_eu_law] — Article 2(1)(e) (marriage documents); Article 2(3)(a)-(b) (third-country documents and Member-State-certified copies of them excluded); Article 2(4) (legal effects excluded); Article 4 (exemption from legalisation and similar formality); Article 5(1)-(2) (cross-border certified-copy requirements); Article 6(1)(a)-(b) (translation and multilingual standard-form conditions) (Official Journal text checked 2026-10-20; not in pinned core pack; applies only to covered public documents issued by one Member State for presentation in another; verify amendments, document scope, translation rules and case-date national treatment)
- **Counterarguments and exceptions:**
  - A checklist can be illustrative or request evidence relevant to the actual eligibility condition.
  - Alternative evidence can be considered and still found insufficient for a stated, evidence-based reason.
  - The Directive's scope and relationship with the Visa Code must be established before importing its family-member facilitation rules.
  - For a covered public document establishing marriage, Regulation (EU) 2016/1191 can exempt the document from legalisation or an apostille when presented in another Member State; it does not require recognition of the legal effects of its contents or establish every family-member eligibility condition.
  - For a covered document, Article 5 limits demands for both an original and certified copy and requires acceptance of a certified copy made in another Member State when certified copies are permitted; Article 6(1) limits translation demands in the stated language or sufficient multilingual-form conditions. Check the exact form, accepted languages and receiving-state procedure.
- **Records to seek:**
  - Exact checklist and any statement that it is exhaustive
  - Identity/family evidence actually presented
  - Authority response and reason for rejecting any alternative
  - Facts establishing the EU citizen's movement and the applicant's claimed category
  - Issuing authority and Member State, receiving authority and Member State, document purpose and form
  - Any translation, multilingual standard form, certified-copy, authenticity, or separate legal-effect objection
  - If relevant, whether the authority permits a certified copy, the issuing state of that copy, the document language, any accepted-language list, and whether a multilingual standard form contains enough information
- **Competence and limits:** The pathway flags a proof issue for review. It does not establish family status, documentary sufficiency, or an unlawful closed list. Commission guidance is nonbinding. Regulation (EU) 2016/1191 is limited to covered Member-State public documents and formalities; it excludes third-country public documents and does not determine recognition of legal effects. A document falling outside it may still be governed by another treaty or national rule, so do not assume an apostille is always required.
- **Reviewer decision:** pending; confirm screen predicate, source classes, exceptions, negative cases, and whether any candidate must remain unresolved.

### `complaint_and_review_path` — Complaint, appeal, or review-path information

- **Signal and route binding:**
  - remedy_or_supervisory_track (remedy_or_solvit_or_supervisory_complaint)
- **C27 families:** authority; conduct; remedies
- **Coverage binding:** core:attack:complaint-path-review
- **Adverse signal screened:** A formal decision or independently actionable procedural act is known, but the authority's review information or the actual route is reported missing, inaccessible, or contradictory.
- **Sources and provisions to verify:**
  - eu:32009r0810 [binding_eu_law] — Article 32(2)-(3), Annex VI; Article 38(5): Member States must provide a complaint procedure for staff conduct/application process and make its information public (official_consolidation_2024-06-28_checked_2026-10-20; amendment and case-date check required)
  - eu:32004l0038 [binding_eu_law] — Articles 30-31, where applicable (official_EUR-Lex_text_checked_2026-10-20; national remedy remains unverified)
  - eu:12012p [primary_eu_law] — Article 47, only within the Charter's Article 51 scope (Official Journal text checked 2026-10-20; applicability depends on implementation of EU law)
  - commission:visa-code-handbook-I-2024 [official_nonbinding_operational_guidance] — Part II, section 11.2; Part III family-member appeal information (Commission C(2024) 4319 final checked 2026-10-20; points to national appeal law; nonbinding)
- **Counterarguments and exceptions:**
  - A complaint route can exist elsewhere in the legal system even if a web page omits it.
  - An informal complaint, supervisory route, SOLVIT, and judicial appeal are distinct and may not suspend one another's deadlines.
  - A procedural step may not be a separately reviewable decision at the current stage.
  - Visa Code Article 38(5) requires a procedure for complaints about staff conduct or the application process and public information about that procedure. A missing website link therefore does not alone prove the procedure is unavailable; this complaint process is distinct from the appeal right for a visa refusal under Article 32(3).
- **Records to seek:**
  - Decision and service date
  - Appeal instructions and envelope/portal timestamp
  - Current official national procedure and competent court/authority
  - Any separate service complaint and whether it affects a deadline
  - Official national complaint procedure, authoritative decision instructions, alternate official publication of the route, and whether the complaint affects any appeal deadline
- **Competence and limits:** The shared record cannot identify a national court, filing method, deadline, or interim remedy without a current Member-State source pack and case-stage facts. Article 38(5) requires a complaint procedure and public information, but it does not itself identify a country-specific filing body, deadline, judicial remedy, or suspensive effect.
- **Reviewer decision:** pending; confirm screen predicate, source classes, exceptions, negative cases, and whether any candidate must remain unresolved.

### `appointment_and_processing_time` — Appointment access and processing clock

- **Signal and route binding:**
  - pre_lodgement_obstruction_and_appointment_access (pre_lodgement_access_obstruction; appointment_delay)
  - processing_delay_or_clock_trigger (processing_delay_or_deadline_question)
- **C27 families:** access; lifecycle; timing
- **Coverage binding:** core:attack:procedural-access-review;core:attack:deadline-timeliness-review
- **Adverse signal screened:** A dated appointment or processing delay is reported, with a potentially applicable statutory or accelerated time rule.
- **Sources and provisions to verify:**
  - eu:32009r0810 [binding_eu_law] — Articles 9(2)-(3), 19 and 23 (official_consolidation_2024-06-28_checked_2026-10-20; appointment and processing clocks differ; amendment check required)
  - eu:32004l0038 [binding_eu_law] — Article 5(2) (official_EUR-Lex_text_checked_2026-10-20; qualifying-family-member and urgency conditions matter)
  - commission:visa-code-handbook-I-2024 [official_nonbinding_operational_guidance] — Part II, section 2.2.2: appointment generally within two weeks; Part III, section 4.4: EU-family processing beyond 15 days exceptional and duly justified, delays beyond four weeks described as not reasonable (Commission C(2024) 4319 final checked 2026-10-20; nonbinding guidance, not a freestanding statutory deadline; verify later replacement)
- **Counterarguments and exceptions:**
  - Appointment waiting time is not automatically the same clock as processing after lodging.
  - Urgency, appointment availability, completeness, representation, and justified extensions may matter.
  - A missed service target does not by itself establish an individual remedy or damages claim.
- **Records to seek:**
  - Appointment request and response dates
  - Formal lodging receipt and any later completeness notice
  - Applicable current rule, start event, pauses, extensions, and decision service date
  - Urgency evidence and any alternative appointment offered
- **Competence and limits:** The core pattern is a review hypothesis only; it does not calculate a national urgent remedy or infer lateness from today's date.
- **Reviewer decision:** pending; confirm screen predicate, source classes, exceptions, negative cases, and whether any candidate must remain unresolved.

### `data_access_minimisation_and_preservation` — Personal-data access, minimisation, and separate preservation request

- **Signal and route binding:**
  - personal_data_protection (personal_data_processing_question)
  - ephemeral_evidence_preservation (ephemeral_evidence_at_risk; evidence_record_contains_personal_data)
- **C27 families:** privacy; conduct; authority
- **Coverage binding:** not_implemented_in_C5d_deterministic_predicates
- **Adverse signal screened:** A specific personal-data request or a narrowly identified record-preservation concern is reported, with a named or potentially identifiable controller/processor and purpose.
- **Sources and provisions to verify:**
  - eu:32016r0679 [binding_eu_law] — Articles 5, 12, 15, 17(3)(e), 18(1)(c), 23 (Official Journal text checked 2026-10-20; controller, processing purpose, special regimes and any restriction law require verification)
  - candidate:eu:32008r0767 [specialized_binding_eu_data_law] — Articles 38-40: VIS rights, assistance and remedies (official_consolidation_2023-12-27 checked 2026-10-20; not in pinned core pack; verify amendments and regime applicability)
  - cjeu:62021cj0487 [cjeu_interpretation_of_binding_eu_law] — Case C-487/21, paragraphs 39-44: context can require document extracts or entire documents for an intelligible copy, subject to others' rights; no general full-file entitlement (Official CJEU judgment checked 2026-10-20; apply only to the GDPR access issue and relevant facts)
- **Counterarguments and exceptions:**
  - Article 15 concerns personal data and prescribed information. Under C-487/21, document extracts or entire documents may be needed where essential for intelligibility, subject to others' rights; this is not a general full-file entitlement.
  - Article 18(1)(c) restriction is available only where the controller no longer needs the data but the data subject needs them for legal claims; Article 17(3)(e) can limit erasure where processing is needed for legal claims.
  - Article 23 restrictions require a legislative measure meeting its conditions; do not infer a restriction without identifying that measure.
  - VIS access, correction and remedies have specialized provisions; a practical preservation request is distinct from an automatic retention duty or judicial preservation order.
- **Records to seek:**
  - Targeted request, response, identity verification, and delivery evidence
  - Controller/processor identity and processing purpose
  - Specific data categories, systems, recipients, and date range
  - Separate preservation request, records at risk, and any national procedural basis
- **Competence and limits:** No automatic deletion, retention, full-file access, or preservation conclusion. National access-to-file rules and specialized visa-data procedures remain separate source tasks.
- **Reviewer decision:** pending; confirm screen predicate, source classes, exceptions, negative cases, and whether any candidate must remain unresolved.

## Cross-cutting legal and privacy questions

- **Signal completeness:** Are route triggers and conditional signal predicates sufficient to avoid omission without turning every generic visa, provider, or complaint question into a legal assessment?
- **Source-class policy:** Are minimum and conditional classes mapped to the correct owner? In particular, does an EU-only route avoid forcing national binding law, while national remedy and local procedure classes activate only on the stated predicates?
- **Attack-angle limits:** Are candidate/negative outcomes framed as screening only, with adequate predicate traces and counterexamples? No C5d/C11 item may be described as a legal violation based on structural screening.
- **Privacy:** Do receipt fields and the abstract revision manifest avoid narrative facts? The strict scanner catches only a few identifier patterns and is not an anonymity guarantee. Are opaque references and evidence pointers necessary and proportionate?
- **Provenance:** Are model-declared source reads and review methods clearly distinguished from authenticated host/tool events? Does the dashboard avoid implying that the local gate ran in ChatGPT?
- **Completeness:** Do unresolved issue, source, C27, attack, revision, and national-remedy items stay open? Are conditional answers distinguished from comprehensive coverage?
- **Freshness and source limits:** Do policy references identify source records without treating versioned bundles or candidate sources as current or authoritative proof?

## Review record (to be completed independently)

| Reviewer | Date | Routes/topics reviewed | Findings and required changes | Decision |
| --- | --- | --- | --- | --- |
| pending | pending | pending | pending | pending_independent_review |

No approval is inferred from implementation, passing tests, or preparation of this packet. Production metadata must remain `pending_independent_review` until an independent reviewer records a decision through the project’s approved review process.
