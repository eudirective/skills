# Latvia source-rule sustainability assessment (2026-10-19)

Skill: `assess-source-rule-sustainability` v0.2.0

## Scope and result

This assessment covers the 49-record Latvian candidate register, including laws, official guidance, forms, visa/mission pages, remedies, privacy/oversight, legal aid, court-decision repositories, source discovery, and publisher reuse rules.

The ordinary HTTPS capture pass fetched 43 official source pages/files without API registration: 41 HTML pages and 2 PDFs were converted to review-candidate Markdown. Both original PDFs remain byte-for-byte preserved. Six records are discovery or repository surfaces without an individual source text. All 43 captures remain unaccepted. The converter replays all 43 outputs from captured responses and verifies both PDF hashes. No individual court decisions were identified by case number or downloaded.

**Overall verdict:** the current prototype is not cleared for an unattended source mirror. This does not block human-reviewed use of an official link. The publisher's written reuse conditions and fees matter if this library retains or repeatedly fetches content: Likumi.lv says systematised acts may be reused under public-information law and applicable fees, and Latvijas Vēstnesis requires coordination for recurring reuse. No scheduled monitor should be built until its specific route and terms are clear.

## Source and version evidence

- The new Latvian EU/EEA/Swiss residence Act, No. 369282, took effect on 10 July 2026. It is the core free-movement law in this register; Regulation 675 remains relevant to applications filed before that commencement. The separate new Immigration Law took effect on 15 September 2026.
- The central PMLP EU/EEA/Swiss page displays an update date of 17 July 2026 and refers to the new Act. Several linked checklists and document pages pre-date the Act. The MFA EU-family page was updated before commencement and still cites Regulation 675. These sources need substantive reconciliation rather than just URL monitoring.
- Likumi.lv stable act IDs and Gazette OP identifiers give usable source identities. Likumi.lv's own terms say its systematised texts are informational and the official publication prevails in a discrepancy. Reproducing an external legal act must also indicate the official-publication date and issue number.
- Cabinet Regulation No. 536 (effective 13 August 2021) sets reuse fees for official publication and Likumi.lv systematised acts. Its schedule lists EUR 0.57 per standard electronic document, EUR 21.34 per official-publication group per month, or EUR 128.06 for all groups per month. These are schedule amounts; the publisher must confirm which service and fee applies to the proposed recurring library.
- The official publisher's reuse page says the current public-interface service supports grouped official notices. The Vēstnesis publication-security page says PDFs carry the publisher's electronic seal or an e-signature fallback. The captured OP 2026/119.1 PDF's signature has not been validated cryptographically.

## Proposed-route assessment

| Route | Assessment | Evidence | Remaining condition |
|---|---|---|---|
| Likumi.lv systematised laws | Technically repeatable; reuse **conditional** | Captures include the current free-movement Act, Immigration Law, transition rules, procedure, access and oversight laws. Stable act IDs and in-force status are visible. Ordinary HTTPS worked without registration. | Written confirmation of automated/recurrent delivery, applicable fee, allowed storage/conversion, and a stable supported change-notice route. Preserve Gazette citation/version metadata because Likumi text is informational. |
| Latvijas Vēstnesis original publications | Direct capture and page-wise text extraction work; reuse **conditional** | Stable OP page and direct PDF links; exact 718,550-byte OP 2026/119.1 PDF preserved and extracted with pinned `pypdf==6.21.1`. Reuse page identifies written coordination and Regulation 536 fees. | Confirm legal-text PDF reuse scope and cost; quality-review the extracted text against the PDF and cryptographically verify the actual e-seal/signature. Retain OP identity and issue/date. |
| PMLP, MFA and other agency pages | Technically captured; ongoing maintenance **fragile** | Primary content from the official HTML pass includes agency guidance, filing routes, fees, visas, missions, complaint processes, legal aid, and forms. Visible content dates surfaced in the captured text. | Refresh through parent indexes and attachments; review old pages against both 2026 laws; distinguish CMS dates from legal verification. Confirm whether publisher reuse terms apply to each separate agency domain. |
| Forms and PDFs | Captured and text-extracted; **not ready for use** | The PMLP application PDF was fetched, preserved (192,258 bytes), and extracted page-by-page. Its 182 interactive fields are counted but not recreated in Markdown; the original PDF remains necessary for form entry. Parent form and legal-aid form indexes were converted. | The PMLP PDF is indexed as over ten years old. Confirm it is the attachment currently linked by the updated parent index and review the extracted text. |
| Case-law repositories | **Discovery only** | E-lieta, Supreme Court, Constitutional Court and Gazette archive routes are recorded. | No individual decision IDs or texts were part of the candidate list; search access, completeness, update cadence, anonymisation and reuse terms remain unverified. Selected precedent indexes must not be described as complete national coverage. |
| Likumi.lv RSS / change feed | **Unresolved** | The portal displays a “newly published acts” RSS icon. | Resolve and document its actual URL, scope, retention, stable IDs and terms; reconcile it against Gazette publication records. No public machine API was found in this bounded search. |

## Retrieval and change-detection rule

The prototype uses allowlisted HTTPS GETs, a 20-second timeout, a 16 MiB response cap, and a one-second delay. It stores exact raw response bytes under ignored `temp/latvia/raw/`, records each exact SHA-256, and converts the primary HTML content block into a review file. Direct responses were captured without registration, security challenges, or failed records in this pass.

Repeated HTML responses exposed volatile inline script tokens, Drupal `js-view-dom-id` hashes, and a rotating CSRF token. Those values are excluded from the HTML comparison digest only; exact original bytes and their hashes are retained. The comparison still includes the rest of the response, including content and links. A remaining change is staged under `temp/latvia/pending/` for review. PDFs use exact-byte comparison and deterministic page-text extraction. No source is automatically accepted. All 43 Markdown conversions replay from the saved raw captures and both preserved-PDF hashes verify.

This establishes a repeatable one-time retrieval/conversion path for captured pages, not a legally cleared or operational scheduled monitor. Terms/rate limits for non-Likumi publishers, RSS discovery, HTML layout changes, cryptographic signature validation, and PMLP attachment currentness remain open.

## Optional work for recurring local monitoring

The retrieval, publisher-fee, and change-feed conditions below apply to retaining or repeatedly fetching source material. They do not block a human-reviewed official source reference. For ordinary use, prefer the latest government-published consolidation and state its date/cutoff and informational status; use Gazette notices only for a specific material update.

1. **Confirm reuse in writing with the official publisher.** State that the requested service is a maintained, non-commercial legal-source library/monitor; ask whether recurrent retrieval and local conversion are allowed, which delivery mechanism is supported, which items/fees apply, and any rate/retention conditions. Do not schedule the current direct-GET prototype until this scope is clear.
2. **Resolve supported law-change discovery.** Ask for a documented bulk/current-text route or notification/feed for systematised acts. If using RSS, record its actual endpoint and payload and use notices to find a newer government-published edition or a known change. A complete RSS-to-Gazette reconciliation is not required when the current consolidated text can be checked directly.
3. **Current-text use.** Prefer the latest government-published consolidation and record its cutoff. Check a known future-effective provision, repeal, or material PMLP/MFA update only where it affects the review; the full Gazette amendment chain is not required.
4. **Review only the PDF content used.** The official files and replayable extraction are already preserved. Check relevant passages against the PDF when relying on converted text; cryptographic signature verification is needed only if the question turns on that Gazette file's seal or authenticity. Confirm the PMLP application's current parent-page attachment because its version is a real form-staleness issue.
5. **Identify individual decisions and define corpus scope.** Search official case databases for stable decision IDs relevant to entry/residence, appeals, delay, family definition and data protection. Preserve redaction and access conditions; do not infer completeness from a selected archive.
6. **Add publisher-specific rules only after permission and tests.** Keep each site's retrieval, payload, version, conversion, failure and change behavior independent. Preserve all capture outputs as candidates until source identity, legal scope, version and reuse conditions are reviewed.

No locally stored artifact is accepted. Mirror synchronization and integrity remain outside this assessment.
