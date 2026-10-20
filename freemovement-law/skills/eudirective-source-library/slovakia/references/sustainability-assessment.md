# Slovakia source-rule sustainability assessment

Research date: 2026-10-19. Scope: 40 official-source candidates across laws, guidance, forms, mission details, case-law discovery, oversight and legal aid. Fifteen Slov-Lex current legal texts, their binding PDFs, and eleven linked annex PDFs were captured. Sixteen other source pages were converted; eight MFA requests failed with HTTP 403. No source is accepted.

## Slov-Lex legal publication route

The Ministry of Justice identifies Slov-Lex as the electronic Collection of Laws, containing generally binding regulations from 1945 onward, including full texts. The official [dynamic archive index](https://www.slov-lex.sk/ezbierky/archiv-zbierky-zakonov) renders a JavaScript notice that links to the [static chronological register](https://static.slov-lex.sk/static/SK/ZZ/). Browser inspection of the static route showed an archive-year listing from 1918 through 2026. A direct exact-byte capture was attempted through the local workflow but failed at workspace DNS resolution; this is not evidence that either publisher route is unavailable. The static page remains uncaptured in the pack. The dynamic index describes an HTML archive with every version and annex and monthly change packages. Its July–August 2026 package was listed as two parts, 1,023 MB and 628 MB, so the incremental archive is useful for bulk reconciliation but too large for routine capture of this bounded candidate set.

The implemented rule resolves each law’s currently effective date from its official per-act history index, then retrieves the date-bound static print HTML, linked binding PDF, and linked annex PDFs. It uses ordinary HTTPS with TLS validation, a Slov-Lex host allowlist, a 24 MiB per-response cap, and a one-second pause between candidates. It checks the act number, effective date, PDF content type/signature, hashes exact response bytes, and deterministically converts the HTML to review text. Offline replay passed for all 15 legal candidates and their saved PDFs/annexes. The print HTML labels its text informational and says the PDF is legally binding; both are preserved. The history index, HTML, and PDF are all versioned in the capture ledger.

This is a promising, repeatable candidate rule with moderate change risk: it depends on official static path structure and history-index markup. It is safer than the earlier guess because every date is discovered from the source’s own history page, and the exact PDF link is parsed from the printed page rather than guessed. The official monthly archive provides a separate change-discovery route if individual URLs or page structure change. A changed HTML, PDF, or annex hash stages the converted result for review. Limits remain: the 24 MiB cap, at most 16 linked annex PDFs, no automatic retry, and a parser-quality review is still required against selected statutes and annexes.

No documented Slov-Lex API contract was located in the bounded search. An API is not required for this candidate set: official per-act history pages and static text/PDF routes are publicly retrievable, while monthly delta files provide a bulk fallback. This does not prove that no API exists.

Reuse permission remains unresolved. The Ministry’s [reuse page](https://www.justice.gov.sk/sluzby/opakovane-pouzitie-informacii/) describes individual Gazette issues in `.vp` format, approval and credentials, attribution, informational/non-binding labeling, and a no-content-change condition. It does not clearly establish whether those terms govern publicly accessible consolidated HTML/PDF. Public visibility is not treated as a general republication licence. Keep captures as unaccepted review material until the publisher clarifies automated retrieval, archival, conversion, and derivative-text conditions.

The Ministry announced Slov-Lex modernization in March 2026. A future platform change may alter history markup or routes. The rule fails closed if the history page, selected edition, metadata, host, response type, PDF signature, or candidate identity does not match.

## Guidance, forms and missions

The generic bounded capture converted 16 additional source pages. Eight MFA URLs/PDFs returned HTTP 403; no authentication or challenge bypass was attempted. Interior Ministry FAQs, visa guidance, forms, directory pages and mission pages have different update patterns. The March 2025 EU-citizen FAQ is dated operational guidance; its fixed folder path has no verified catalogue or feed. The [May 2026 relocation notice](https://www.minv.sk/?police=&sprava=opening-of-the-foreign-police-department-in-bratislava-at-a-new-address) shows office locations and booking categories can change. MFA mission requirements also vary by location, and local evidence lists, representation, appointments and forms need parent-page rediscovery.

The English MFA EU-family page is dated 2022 and cites Act 404/2012; the candidate inventory records it as a stale lead, not a current rule. Current law, central guidance and mission-specific instructions must be reconciled independently.

## Legal scope and procedure boundaries

Act 404/2011 generally includes EU, EEA and Swiss states in its member-state definition, but narrows the term to EU Member States in §§30 and 51–57. The record preserves that provision-specific distinction. Slovak return movement, EU citizens, EEA EFTA citizens, Swiss citizens, third-country family members and UK Withdrawal Agreement beneficiaries remain separate routes unless the law expressly groups them.

Administrative procedure, judicial review, complaints, petitions, Freedom of Information, Ombudsman, data protection and equal-treatment routes are separate sources. The Public Defender says its submissions do not suspend appeal or court deadlines. A complaint or Ombudsman submission cannot replace a decision-specific remedy. Legal-aid eligibility and court-search coverage need their own source checks.

## Courts, oversight and sensitive information

The Supreme Administrative Court, Supreme Court and Constitutional Court provide selected decision-search surfaces. Search-result completeness, date coverage and stable change feeds are not established. A no-result query cannot show there are no relevant decisions. Oversight and data-protection forms may contain personal information; monitor the procedural guidance, not private submissions.

## Next sustainability actions

1. Obtain written clarification from the Ministry or Slov-Lex on reuse terms for consolidated date-bound HTML/PDF, automated retrieval, local archival, conversion and derived text.
2. Review conversion quality against representative PDFs and annexes, including tables, footnotes, and version metadata; retain the original binding PDFs as the authority.
3. Monitor the official archive index and per-act history-page structure so a missing or changed monthly package, route, or markup is detected rather than silently treated as no change.
4. For MFA and Interior Ministry guidance, identify parent indexes and compare their child links, update dates, files and mission coverage. Keep appointments, local forms and office details volatile.
5. Define any case-law lane by named courts, date bounds, indexing limits and result caps; do not claim complete case-law coverage.

## Disposition

The Slov-Lex rule is implemented and offline replay-verified for 15 current legal candidates, with binding PDFs and linked annexes preserved. Its route is reasonably sustainable for bounded per-act monitoring, backed by official version histories and monthly bulk changes, subject to platform-change and size limits. Reuse permission and conversion quality still prevent acceptance. Other source classes remain partially retrievable: 16 converted pages, eight MFA access failures, and no complete mission or court inventory. No source is accepted.
