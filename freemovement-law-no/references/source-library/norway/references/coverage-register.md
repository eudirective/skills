# Norway pathway coverage register

**Reviewed:** 31 October 2026

**Scope map:** owner-approved EEA national-source crosswalk v1.0.0, SHA-256 `8705c0b379adb10143c0a45349f0533c075b29420f4b2848422c3e18d4aa8544`

**Status:** initial issue map; six pathways incomplete; zero adequately covered topics; country review incomplete.

This register records evidence against the six core review pathways, not a complete inventory of Norwegian law. Source IDs point to the pack's acceptance and reference records. A locator note, official URL, candidate match, or dynamic guidance page is not retained legal text. No topic is accepted by the crosswalk approval or by this register.

## EEA-specific applicability boundary

For Norway, the approved crosswalk's E01 layer is conditional measure by measure: identify the EU act, the EEA Joint Committee Decision and adaptations, its entry into force for Norway, and the corresponding national implementation. The EØS Act notes identify a Norwegian incorporation framework; they do not make every EU act directly applicable Norwegian law. The retained no-54 worker-mobility text proposed in open PR #167 expressly incorporates specific EEA Annex V instruments as Norwegian law. It does not establish visa or residence-application coverage.

Official EFTA material identifies Directive 2004/38/EC as incorporated by JCD 158/2007 and in force in the EEA. The accompanying Joint Declaration limits the EEA basis, including the treatment of third-country family members. The Norway-specific statutory and procedural map remains open. GDPR is incorporated into the EEA Agreement by JCD 154/2018; its controller, processing-regime, national implementation, and immigration-system mapping remain open.

Norway's short-stay Visa Code route is a Schengen-association dependency, separate from EEA incorporation. The EFTA Convention's Swiss movement-of-persons route is another separate route. Do not merge either route with EEA-family rights or treat an ordinary Schengen checklist as an EU/EEA-family rule.

## Pathway register

| Pathway | Current evidence | Remaining work |
|---|---|---|
| P01 — Access blocked before formal lodging | Official-reference notes identify the Immigration Act (no-06), Immigration Regulations (no-07), EØS Act (no-08), EEA texts/JCD route (no-09), and UDI family guideline (no-11). UDI/mission workflow and remedy locators are in no-20, no-29, no-31, no-34, no-38 and no-51. These are not retained text copies. | Verify current provisions and identify the responsible authority, formal lodging event, refusal-to-lodge rule, mission/provider steps, exceptions, and decision-specific remedy. Keep EEA, Schengen and national immigration routes separate. |
| P02 — Digital-only or service-provider access requirement | UDI self-service, application-checklist and foreign-service routing references exist in no-29, no-31 and no-51. | No legal basis for mandatory digital access, delegation, accessibility, assisted filing, exception, or digital-failure remedy is mapped. |
| P03 — EU-family proof and ordinary Schengen checklist | The official EEA movement-of-persons layer and Norwegian immigration references are identified. UDI references cover EEA/EU residence and family routes (no-20 to no-23); no-27 is a Swiss-route selector. Exact checklist attachment no-30 remains pending. PR #167 proposes a retained text for the EØS Worker Mobility Act (no-54), but the file is not on `main` and concerns worker mobility, not a complete family residence or visa-document route. | Map the EEA JCD/adaptations and Norwegian implementing text by person category; compare the current Utlendingsloven and Utlendingsforskriften; verify the exact family checklist; separate the Schengen Visa Code from EEA-family facilitation and the EFTA/Swiss route. |
| P04 — Complaint, appeal, or review-path information | Official reference notes identify UDI appeal guidance (no-34), UNE EEA cases/practice (no-38/no-39), grand-board decisions (no-40), Sivilombudet routes (no-42/no-43), a Supreme Court decision/index (no-44/no-45), and legal aid (no-48). The current administrative-procedure source no-13 and future Public Administration Act no-53 are locator notes only. | Map notice, reasons, service, standing, responsible review body, deadline, suspensive effect, judicial review, urgent relief and legal aid by decision type. Recheck commencement before relying on no-53. |
| P05 — Appointment access and processing clock | UDI checklist/application/waiting-time locators no-29, no-30, no-31 and no-33, plus foreign-service routing no-51, identify operational leads. No-30 remains pending exact attachment/version verification. | Capture the actual route and distinguish appointment delay from a statutory processing clock; verify trigger, pauses/extensions, current mission channel and escalation remedy. |
| P06 — Personal-data access, minimisation, and separate preservation request | GDPR's shared EU text is present in `source-library/core/eu/eu_32016r0679_EN.md`; EEA JCD 154/2018 is identified. Norway reference notes cover the Personal Data Act (no-16), administrative-file access (no-35), personal-data access (no-36), privacy notice (no-37), public-journal services (no-46/no-47), and the Data Protection Authority (no-52). | Retain and compare the applicable Norwegian texts; identify controller, purpose, system, GDPR/national or law-enforcement regime, access and preservation routes, exceptions, deadlines, oversight and judicial remedy. Do not equate public-file access with personal-data access. |

## Source-text status

- `main` contains no accepted Norway legal-text copy at the baseline referenced by the existing source acceptance report.
- Open PR #167 proposes one official Lovdata text copy, LOV-2012-12-14-81. It is accepted on that branch only and remains unmerged. The file and its acceptance record are part of the proposal, not a claim about `main`.
- Other Norway entries cited above are official-reference or operational-reference notes. They do not substitute for the law, regulation, EEA measure, current checklist, or remedy text.

The machine-readable layer and dependency details are in [`coverage-model.json`](coverage-model.json) and [`source-dependencies.json`](source-dependencies.json).
