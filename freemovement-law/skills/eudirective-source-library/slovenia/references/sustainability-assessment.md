# Slovenia proposed-route sustainability assessment

Research date: 2026-10-19 update. The 42-candidate pack now has 42 exact responses, 23 replay-verified text conversions, 19 shell/discovery responses, and 0 accepted sources. The shared generic retrieval rule is exercised, but no source-specific currentness adapter or amendment-completeness rule exists. This remains a route assessment, not a legal-currentness certification.

## PISRS and official legal publication

PISRS is the official national legal-information portal and offers public search and record pages. Its developer instructions explicitly require authorization from the Government Office for Legislation to use the API. That permission gate is a real dependency; public browser access, a guessed endpoint, or a request to register does not establish an authorized automated route. Do not call the API or seek to circumvent its access control.

There is a practical no-API discovery path, but it remains manual and limited: use PISRS and GOV.SI as human-operated indexes, follow a record to its official publication, and inspect a specific Official Gazette issue PDF where available. One official issue PDF (`u20260026.pdf`) was opened without registration. This confirms that one issue route is reachable; it does not prove the URL pattern works for all issues, that repeated automated retrieval is permitted, or that PDF-to-text conversion will be reliable. The publisher's 2026 transition under ZOUL also means pre- and post-1 March 2026 publication/archive paths need separate treatment.

OPSI lists a CC BY 4.0 dataset for basic information on Slovenian regulations and links to PISRS. The licence applies to this metadata dataset, not to full legal text. The catalogue says bulk download is not enabled. Its linked resource is declared as API but its quality checker detected HTML, flags the mismatch, and shows 5 October 2024 as the check date. It does not supply API-PISRS authorization or establish reuse rights for PISRS texts. The general public-information/reuse rules likewise do not, by themselves, resolve the specific API approval gate or terms for a particular full-text source.

PISRS consolidated texts are informational aids. For a sustainable acquisition rule, the publisher's legally authoritative issue must anchor version identity. The rule would need to retain act identifier, Gazette issue, publication and commencement dates, relevant future/effective dates, language, and source route; detect amendments and repeals; and reconcile any PISRS consolidated text against the full amendment chain. ZTuj-2's PISRS record currently surfaced NPB 20 through UPB15/Official Gazette 46/2025, but this bounded search is not proof that no later act affects the law.

## GOV.SI guidance, forms, privacy and missions

The central Entry and Residence page is a strong discovery parent: it links the EU, EEA and Swiss sections, service pages, visa process, forms, privacy notices, VIS/SIS rights, and mission directory. It is a dynamic HTML page with page-level edit metadata and mutable attachments. A future rule should rediscover its linked services and files from the parent on each check, compare exact file identity and dates, and flag broken, replaced or removed links. It should not pin opaque PDF/DOCX links as the only way to find a current form.

Mission instructions, application channels, appointment access, fees, checklists and representation arrangements vary by location. The Copenhagen Embassy page is one dated sample; it cannot represent the national mission network. A sustainable mission lane needs a current official directory, a defined set or explicit selection rule for posts, and per-post update evidence. The present discovery does not attempt a complete mission search.

The English Schengen privacy notice was available as an official PDF and identifies MZEZ, VIS and external service provider processing. It is an opaque attachment, so the parent page must remain the rediscovery route. Public procedural guidance can be monitored; individual visa files, privacy requests and submitted personal data must not be collected.

## Legal and geographic scope

GOV.SI expressly says that Foreigners Act provisions used for EU citizens also apply to EEA member-state citizens and their family members. The same central page and service inventory present Swiss nationals separately, and the Swiss service explicitly cites the EU–Swiss Agreement on Free Movement of Persons. Keep those as distinct legal routes. A shared GOV.SI page or form directory is not evidence that all detailed rules, family definitions, or remedies are the same.

The EU-family service for non-EU relatives groups EU citizens and Slovenian citizens on one page. Its two legal bases may differ, so the source record must retain that distinction. The directly linked permanent-family service timed out in the research client; the central page exposes a five-year general threshold, but detailed conditions and form links remain unverified. Family-status evidence, recognition, translation and authentication were only partially searched.

## Procedure, remedies, privacy, legal aid and courts

ZUP-I has a direct official Gazette issue PDF and PISRS reports that the consolidated ZUP text begins use on 7 February 2026. Keep the amendment, publication, application date and consolidated record separate. GOV.SI procedure guidance is explanatory, and special immigration provisions may govern particular steps. Ombudsman, Information Commissioner, equality-body, administrative appeal and judicial review channels have different mandates; none should be treated as a substitute for a decision-specific remedy.

The PISRS advanced search offers selected Supreme Court, higher-court, labour/social-court and Administrative Court collections. The official court portal lists a case-law RSS feed, but the target endpoint, retention, inclusion criteria and coverage were not established. Do not claim complete national case-law coverage from either surface. eUprava says foreign nationals may qualify for legal aid under statutory conditions; its legal-aid pages were last changed in August 2025 and warn that they have not yet been renewed and will redirect to the old eUprava site. The FAQ describes eligibility by residence/status and reciprocity or treaty conditions. Reconcile that guidance with current ZBPP and the live service; the page migration is a concrete change-detection risk.

## Implementation prerequisites

1. Keep PISRS API use blocked unless the required authorization is granted. Do not build an adapter against the gated API or use a workaround that evades it.
2. Obtain publisher clarification on the terms for automated retrieval, archival, conversion and derived text from public PISRS/Official Gazette full-text records. Keep this separate from the CC BY 4.0 metadata dataset.
3. Document and verify the Official Gazette issue-PDF URL contract across representative issues before treating the one observed PDF as a reusable route. Confirm publisher terms, redirects, status, content type, PDF signature and act identity.
4. Capture representative issue PDFs only through an authorized route; create offline positive/negative fixtures for current, amended, repealed, annex-bearing and transition-period issues before any conversion implementation.
5. Reconcile PISRS informational consolidations against authoritative issue publications and amendment/commencement chains, particularly for ZTuj-2 and ZUP.
6. Use GOV.SI topic/service pages as rediscovery parents for forms, privacy notices and mission links. Define how to cover missions and detect changed links, fees, appointments and representation.
7. Bound any case-law lane by named collections, courts, date filters and publication limitations. Confirm the RSS target and its update contract before automated monitoring.
8. Recheck the permanent-family service after the research-client timeout, reconcile foreigner legal-aid guidance with current ZBPP and the migrated service, and verify family-status evidence procedures from competent official sources.

## Disposition

The feasible no-API route used in this pass is public-page retrieval and inspection of specific official Gazette issue PDFs, with no call to the gated developer API. It avoids the API authorization dependency for these exact candidate URLs, and 23 conversions replayed offline. It is still not a sustainable automated currentness/amendment rule and does not establish broad full-text reuse permission. OPSI metadata may help locate acts after its schema and freshness are confirmed. All 42 records remain review candidates; 19 still have no stable extractable body. The generic route is reproducible for saved responses, but currentness and full-text reuse remain unresolved. No source is accepted and no API-gated adapter is ready.
