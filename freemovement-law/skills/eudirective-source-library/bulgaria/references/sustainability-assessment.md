# Bulgaria source-rule sustainability assessment

Assessment date: 19 October 2026  
Skill: `assess-source-rule-sustainability` v0.2.0  
Pack maturity: 35 candidates, 0 accepted; shared bounded page retrieval and conversion are implemented, but no Bulgaria-specific validation or change-discovery adapter exists.

## Assessment boundary

The generic capture rule attempted all 35 candidate URLs. Twenty-four exact responses were converted and replay-verified; eleven candidates were not converted because of four third-party bot-validation redirects, five TLS validation failures, one HTTP 500, and one HTTP 404. These are current runtime outcomes, not evidence that the sources themselves are absent. No source was accepted.

The generic rule provides reproducible byte capture, response hashing, bounded requests, host-restricted redirects, deterministic page/PDF conversion where supported, and offline replay. It does not, by itself, establish that a text is the latest applicable legal version, that linked annexes are complete, that a change feed is comprehensive, or that a source may be republished. The Bulgaria route therefore remains only partially sustainable.

## Proposed and observed routes

| Source cluster | Observed outcome | Sustainability assessment / next evidence |
|---|---|---|
| EU free-movement law and forms | The MVR service, current Bulgarian act PDF, forms, declaration, and instruction candidates were attempted. Non-ASCII URL encoding was fixed without changing TLS or redirect policy; these pages now convert where the official response is accessible. | **Fragile, medium-low confidence.** Re-resolve upload-ID PDFs from the MVR parent page, compare amendment metadata against the Gazette, and verify translated material against Bulgarian text.
| National visa rules | PRIS and Gazette candidates were captured where accessible; the PRIS Ordinance attachment returned HTTP 500. The MVR-linked PDF remains an older edition whose amendments stop at 2019, while 2025 amendment records were identified in the inventory. | **Unsustainable as a current consolidated text.** No current full consolidation or validated reconstruction was established. Preserve each promulgated amendment separately until the publisher provides a current consolidation or a legally reviewed reconstruction rule.
| MFA visa, forms, and missions | Four MFA pages redirected to `validate.perfdrive.com`, a third-party bot-validation host. The redirects were not followed and no challenge was bypassed. | **Unretrievable from this client.** Keep the MFA candidate routes and use the official European Commission prior-consultation list as corroborating evidence only; this does not replace national mission instructions.
| Administrative procedure, remedies, privacy, oversight, and legal aid | Public pages were captured where TLS validation succeeded. The Administrative Procedure Code, Ombudsman Act, personal-data law, data complaint, and legal-aid law had certificate errors; Access to Public Information Act URL returned 404. | **Fragile/incomplete.** Use official parent indexes and resolve canonical TLS-valid hostnames before retrying. Never disable certificate validation.
| Courts | Supreme Administrative Court search and administrative-court directory candidates were converted. | **Discovery only.** Court search completeness, lower-court coverage, indexing limits, and change feeds remain unverified.

## Cross-cutting risks

- Direct MVR PDF URLs carry upload IDs and filenames. Use the official parent service page as a discovery route and validate title, language, instrument number, version/amendment history, and body.
- Four MFA redirects pointed to a third-party validation service. Do not treat a bot challenge as a source URL or bypass target; access is unresolved until an official accessible route is documented.
- Five TLS certificate failures prevent a trustworthy capture. Resolve the official hostname or certificate chain through publisher documentation; do not weaken TLS.
- The Visa Ordinance remains the clearest currentness gap: one official route appears stale and another current candidate failed with HTTP 500. The 2025 amending decrees were captured as separate records, but not reconciled into a current consolidated text.
- Bulgarian controlling texts should be used for legal monitoring. The English translation has a known older amendment date.
- The bounded search did not locate a documented API, registration requirement, or bulk-use permission. This is not proof they do not exist. Access and reuse terms require publisher verification.
- MVR notice pages can expose applicant names or case details. Do not harvest or retain individual notices.

## Next sustainability actions

1. Establish a documented current-version route for the Visa Ordinance, including amendments after October 2025 and a deterministic reconciliation method if no publisher consolidation exists.
2. Rediscover MVR forms and acts through the stable service index, detect replacement upload IDs, and validate PDF identity before conversion.
3. Ask the publishers of the TLS-failing legislation, ombudsman, data-protection, and legal-aid endpoints to identify their current canonical TLS-valid hostnames.
4. Reassess MFA source access from a supported official route or browser-visible page without bypassing its third-party challenge.
5. Review 24 converted outputs against source pages and PDFs, including page structure, footnotes, and attachments; store version evidence and checksums.
6. Define court coverage, date bounds, result limits, and indexing caveats before treating search as a monitoring source.

## Conclusion

The shared retrieval and replay rule is implemented, and 24 Bulgarian candidate texts pass offline verification. This is useful progress, but it does not resolve legal version selection, the current Visa Ordinance text, MFA bot-validation redirects, five TLS failures, or reuse permission. Eleven candidates remain unconverted, and all 35 remain unaccepted.
