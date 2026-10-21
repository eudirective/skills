Skill: assess-source-rule-sustainability v0.2.0
Skill: author-source-pack-rules v1.0.1

# Poland source-route sustainability assessment (updated 2026-10-21)

## Scope and maturity

The 54-candidate register has a working bounded capture rule. Fifty-one exact responses were saved and 50 converted to unaccepted local review candidates. Nine official ELI legal-record links are accepted for scoped human use; 0 local copies and 0 topics are accepted, and 45 other records remain under review. All saved outputs pass offline source-hash and conversion replay, including seven PDFs converted with pinned pypdf 6.21.1. Three candidate requests failed (one HTTP 403 and two certificate-validation failures); one dynamic e-Konsulat page had no extractable source text. The ELI/API lane is promising for known records but only partially sustainable: API-specific reuse terms and automated current-version discovery remain relevant to copying and recurring retrieval, not ordinary link use. Provision-specific later amendments and broader coverage remain open.

## Promising legal discovery route

The official ELI API documentation describes stable ELI URI patterns, publisher/year lists, record metadata (`changeDate`, legal status, and text availability), a changed-acts endpoint, and PDF plus some HTML text formats. The capture rule now fetches ELI metadata, checks the publisher/year/position against the candidate ELI ID, selects an advertised text format, preserves exact bytes, converts the text, and replays the conversion offline. Nine original and two newly discovered current ELI texts were captured; ELI metadata said HTML was unavailable for seven and PDF was used. The documentation still does not establish registration requirements, service limits or API-specific bulk-reuse rights. ISAP's attribution terms do not establish those terms for ELI/API payloads.

ELI metadata identifies a legal publication record but does not by itself decide whether that expression is the current consolidated text. The official current-act search (`inForce=1`) found newer texts for the EU-citizen residence Act, DU/2026/1065, and the Free Legal Aid Act, DU/2026/44. Their ELI pages and seven related official legal-record pages were reviewed on 2026-10-21 and accepted as usable links within the scopes recorded in [the source acceptance register](source-acceptance.json). The earlier records DU/2025/1164 and DU/2024/1534 are still preserved as historical candidates; their exact-record metadata returned `wygaśnięcie aktu`. The Foreigners Act consolidated at DU/2025/1079 was returned as `obowiązujący`. Continue to distinguish promulgation, consolidated text, amendments, staged commencement and effective dates; the 2025 residence-law amendment still needs article-level timing reconciliation.

## Operational guidance and route boundaries

MSWiA's entry/residence and registration pages are useful first-party guidance. They describe in-person EU-citizen registration through a competent voivode, while the MOS FAQ describes electronic applications from 27 April 2026 for temporary, permanent and EU long-term residence permits. Those are different legal processes. A general MOS keyword or page title must not route EU free-movement registration into the national residence-permit workflow. Guidance updates, page dates, attachment URLs, forms and the responsible voivode need parent-page rediscovery.

The UDSC old-document notice states that old-pattern documents expired after 3 August 2026 while the underlying right does not end solely because a document expires. Its title now refers to a past deadline, so an update rule must retain its publication/update date and avoid treating the announcement as a current deadline. The UDSC new-forms index is a more sustainable discovery root than fixed ZIP/PDF URLs, but attachment identity, new form versions, and correspondence with the 2021 regulation remain unverified. The UDSC complaints page now explicitly lists e-Doręczenia and states that individual ePUAP submissions after 1 January 2026 are ineffective. By contrast, the UODO SIS procedure page still directs individuals to a Police ePUAP inbox and says an ePUAP account is required. That conflict needs a statute-specific check before a current submission route is published; do not silently reuse either page as a universal rule.

Country-specific consular guidance, mission directories, visa instructions and civil-status examples can change independently. The Kazakhstan and Germany mission pages are examples only, not a nationwide route. E-Doręczenia became the basic electronic-delivery channel from 1 January 2026 subject to special rules; legacy ePUAP instructions in older authority pages require current verification.

## Coverage and authority limits

- EU, EEA EFTA and Swiss routes must stay distinct even when Polish operational guidance groups them. Returning Polish nationals after cross-border free movement, extended relatives, third-country family members and UK Withdrawal Agreement cases are separate branches.
- Public case-file inspection, individual registry access and SIS rights are procedural sources, not public bulk data. Personal and case-specific records are outside this discovery pack.
- The NSA Central Database is a search surface, not a complete official judgment corpus. The NSA describes the database as informational/educational; completeness and zero-result meaning are not established.
- RPO interventions and complaint materials are selected oversight publications. They support topic discovery but do not establish legal rules, prevalence, or exhaustive monitoring.
- This first pass does not inventory all voivodeship-local pages or every consular mission, language variant, published case, or form. The search coverage statements are bounded and cannot prove the absence of additional sources.

## Sustainability findings for proposed routes

**ELI/Sejm legal-data route: usable for direct official links; recurring capture remains optional and needs separate review.** The reviewed ELI pages identify official records and displayed legal-status/version metadata; nine links are usable within the scopes recorded in the acceptance register. The API and exact-byte capture workflow is available for retained copies, but API reuse terms and change polling matter only if those copies or recurring retrieval are wanted. For normal research, open the government-published consolidated text and check a specific later change only when it could affect the issue.

**Gov.pl/MOS/authority guidance: feasible only with parent discovery and route-specific identity checks.** Pages and attachments are mutable; navigation, publication/update metadata and form titles need capture. Use separate source identities for legal guidance, form indexes, downloadable files and interactive application services. The MOS permit workflow must not be merged with EU-citizen registration.

**Missions and civil-status material: manual or directory-assisted candidates until rediscovery is demonstrated.** Mission responsibilities, represented territories, appointments and document checklists vary. Keep location-specific examples scoped and preserve their parent directory relationship.

**Courts and oversight: selected search lanes only.** Define dates, case filters, publication gaps and what a no-result means. Do not advertise comprehensive case-law or oversight coverage.

## Next repair priorities

1. Resolve the exact ELI API reuse terms, any registration requirements, service limits and retention conditions; record the answer before broad monitoring.
2. Automate bounded current-act search and changed-record checkpoints; compare ELI metadata, stable ELI pages and Dziennik Ustaw, and retain prior editions as history rather than silently overwriting them.
3. Reconcile the 2025 EU-citizen amendment with the 2026 consolidated text at article and commencement level; check the current status and amendments for each remaining legal instrument.
4. Continue validation of language, exact source identity, ELI title/status, PDF signature and converter fidelity; pin pypdf and keep HTML/PDF replay checks. Recheck two TLS-failing pages only through ordinary certificate-validated HTTPS.
5. Add parent-page rediscovery for MSWiA/UDSC/MOS forms, MSZ visa and mission pages, and e-Doręczenia guidance. The direct captures document current pages but do not yet detect replaced attachments. Resolve the UDSC-versus-UODO SIS submission conflict under the applicable statute and special rules.
6. Keep EU registration, EU-family documents, EEA EFTA/Swiss routes, national permits, UK Withdrawal Agreement cases and asylum-only aid separate.
7. Limit case-law and RPO lanes to selected, dated records unless completeness is verifiable. The NSA and court candidate pages capture search surfaces, not a complete corpus or a set of specifically selected case decisions.

## Capture evidence — 19 October 2026

The 52 initial candidates plus two current consolidated texts discovered from the official ELI `inForce=1` search produced 51 saved source responses and 50 conversions. All 50 outputs replayed offline; ELI metadata identity/status checks also passed for 11 legal-text records. Seven PDFs were converted by pypdf 6.21.1. `pl-04` returned HTTP 403; `pl-20` and `pl-26` failed certificate validation; `pl-39` returned a public dynamic application shell without extractable body text. Those outcomes remain explicit, with no authentication or TLS bypass. ELI reports the 2026 residence and free-legal-aid consolidated announcements as `obowiązujący`; the previous 2025/2024 announcements report `wygaśnięcie aktu`. All downloaded and converted text remains a review candidate; link acceptance is tracked separately from local-copy acceptance.

## Result

Poland now has a bounded ELI/text capture and replay lane plus review captures for its identified official guidance, forms, visa/missions, procedure, remedies, privacy, oversight, and case-search candidates. The ELI lane is promising for known ELI identifiers but only partially sustainable until reuse conditions and automated current-version/change discovery are resolved. Direct page captures need parent-page rediscovery; three requests remain certificate/403 blocked and one portal is a textless shell. Nine official ELI links are usable within their recorded scopes, while no local copy or topic is accepted and the pack does not claim complete national-source coverage. Forty-five other records remain under review. See the [source acceptance register](source-acceptance.json).
