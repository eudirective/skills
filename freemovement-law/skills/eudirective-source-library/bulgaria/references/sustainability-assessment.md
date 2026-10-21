# Bulgaria source-rule sustainability assessment

Assessment date: 21 October 2026
Skill: `assess-source-rule-sustainability` v0.2.0  
Pack maturity: 36 records, 0 local copies accepted; two official Visa Ordinance references are usable by link. Shared bounded page retrieval and conversion are implemented, but no Bulgaria-specific validation or change-discovery adapter exists.

## Assessment boundary

The generic capture rule attempted the original 35 candidate URLs. Twenty-four exact responses were converted and replay-verified; eleven candidates were not converted because of four third-party bot-validation redirects, five TLS validation failures, one HTTP 500, and one HTTP 404. These are recorded runtime outcomes, not evidence that the sources are absent. A later link-use review found the MFA consolidated Visa Ordinance and a specific Gazette supplement; no local copy was accepted.

The generic rule provides reproducible byte capture, response hashing, bounded requests, host-restricted redirects, deterministic page/PDF conversion where supported, and offline replay. It does not, by itself, establish that a text is the latest applicable legal version, that linked annexes are complete, that a change feed is comprehensive, or that a source may be republished. The Bulgaria route therefore remains only partially sustainable.

## Proposed and observed routes

| Source cluster | Observed outcome | Sustainability assessment / next evidence |
|---|---|---|
| EU free-movement law and forms | The MVR service, current Bulgarian act PDF, forms, declaration, and instruction candidates were attempted. Non-ASCII URL encoding was fixed without changing TLS or redirect policy; these pages now convert where the official response is accessible. | **Fragile, medium-low confidence.** Re-resolve upload-ID PDFs from the MVR parent page, compare amendment metadata against the Gazette, and verify translated material against Bulgarian text.
| National visa rules | The MFA normative-documents index links a 42-page consolidated ordinance whose heading lists amendments through SG issue 4/2025; Decree №221/2025 §3 is the identified later supplement. PRIS version 10.0 confirms the amendment trail but attaches original 2011 files. | **Usable official references with a stated cutoff.** Use the MFA consolidated edition and add only Decree №221/2025 §3: Article 27(1) changed under §3(3), with the constitutional default commencement three days after promulgation (31 October 2025); the currency changes in Articles 16(3) and 17(1) took effect with euro adoption on 1 January 2026. Do not reconstruct the full amendment chain. Check the MFA index for a newer consolidated edition before date-sensitive use.
| MFA visa, forms, and missions | Four MFA pages redirected to `validate.perfdrive.com`, a third-party bot-validation host. The redirects were not followed and no challenge was bypassed. | **Unretrievable from this client.** Keep the MFA candidate routes and use the official European Commission prior-consultation list as corroborating evidence only; this does not replace national mission instructions.
| Administrative procedure, remedies, privacy, oversight, and legal aid | Public pages were captured where TLS validation succeeded. The Administrative Procedure Code, Ombudsman Act, personal-data law, data complaint, and legal-aid law had certificate errors; Access to Public Information Act URL returned 404. | **Fragile/incomplete.** Use official parent indexes and resolve canonical TLS-valid hostnames before retrying. Never disable certificate validation.
| Courts | Supreme Administrative Court search and administrative-court directory candidates were converted. | **Discovery only.** Court search completeness, lower-court coverage, indexing limits, and change feeds remain unverified.

## Cross-cutting risks

- Direct MVR PDF URLs carry upload IDs and filenames. Use the official parent service page as a discovery route and validate title, language, instrument number, version date and known material updates, and body.
- Four MFA redirects pointed to a third-party validation service. Do not treat a bot challenge as a source URL or bypass target; access is unresolved until an official accessible route is documented.
- Five TLS certificate failures prevent a trustworthy capture. Resolve the official hostname or certificate chain through publisher documentation; do not weaken TLS.
- The earlier Visa Ordinance gap is materially improved: the government-published MFA consolidation covers amendments through January 2025, and Decree №221/2025 provides a targeted later update. The MVR-linked edition ending in 2019 is historical only. The MFA page is a maintained discovery path, while its direct PDF upload URL may change.
- Bulgarian controlling texts should be used for legal monitoring. The English translation has a known older amendment date.
- The bounded search did not locate a documented API, registration requirement, or bulk-use permission. This is not proof they do not exist. Access and reuse terms require publisher verification.
- MVR notice pages can expose applicant names or case details. Do not harvest or retain individual notices.

## Next sustainability actions

1. Use the reviewed MFA consolidated Visa Ordinance within its January 2025 cutoff, supplemented by the specific Decree №221/2025 changes. Rediscover the PDF from the MFA normative-documents index when needed; no full historical reconstruction is required.
2. Rediscover MVR forms and acts through the stable service index, detect replacement upload IDs, and validate PDF identity before conversion.
3. Ask the publishers of the TLS-failing legislation, ombudsman, data-protection, and legal-aid endpoints to identify their current canonical TLS-valid hostnames.
4. Reassess MFA source access from a supported official route or browser-visible page without bypassing its third-party challenge.
5. Review the passages and attachments actually used. Broader page checks are needed only where PDF extraction shows a material risk.
6. Define court coverage, date bounds, result limits, and indexing caveats before treating search as a monitoring source.

## Conclusion

The shared retrieval and replay rule is implemented, and 24 Bulgarian candidate texts pass offline verification. Link review has resolved the principal Visa Ordinance version-selection issue for ordinary reference use: the MFA consolidated edition plus the targeted Decree №221/2025 changes is now the working government source, with cutoffs and commencement recorded. Eleven original candidates remain unconverted; no local copies are accepted; MFA bot-validation redirects, five TLS failures, reuse permission for retained derivatives, and broader topic coverage remain open.
