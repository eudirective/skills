# Retrieval routes for unregistered Finland sources

**Checked:** 23 October 2026  
**Scope:** The user-supplied Finland ZIP audit: 19 unregistered candidates, the separately identified Information Management Act and Migri EU-family guidance, and optional Finnish-language copies of three shared EU instruments.

**Inventory baseline:** EU Source Update Monitor reported GitHub `main` at `1d4a488fca1ae6c10c43911eb5074986a70e763e`; its Finland README still reports 36 candidate records, eight accepted external Finlex references and no accepted local copies. The current candidate manifest/catalog also contains three related Migri EU-family public-page candidates, each still marked discovery-only. The named staff instruction below is a distinct, unresolved source question.

This is a retrieval-route note, not source acceptance or topic review. No new candidate rows, source copies, or accepted references are added by this note. The catalog's 36-record count and its separate acceptance counts therefore remain unchanged. A link or a route through a publisher index does not prove that a particular version was downloaded, reviewed, or current for a legal question.

## Where to retrieve the sources

### Finnish legislation

Finlex exposes each listed law through its official current-law page. Use the Finnish page as the controlling text, inspect its displayed current-version ELI and date, and retain the page's links to the original Statute Book item and amendment history when needed. The page is a usable external reference without a local capture. If a local copy is later required, follow the Finland-specific Finlex manifests and converters; do not assume the Akoma Ntoso API covers these acts. The existing Finland README records API 404s for several consolidated texts and documents the more brittle page-stream fallback for only three other acts.

| Audit candidate | Official retrieval page | Retrieval notes |
| --- | --- | --- |
| Constitution, 731/1999 | <https://www.finlex.fi/fi/lainsaadanto/1999/731> | Current Finnish text page; select its consolidated text and record the displayed ELI/date. |
| Electronic Administrative Services Act, 13/2003 | <https://www.finlex.fi/fi/lainsaadanto/2003/13> | Current Finnish text page. |
| Immigration Administration Personal Data Act, 615/2020 | <https://www.finlex.fi/fi/lainsaadanto/2020/615> | Current Finnish text page. |
| Border Guard Personal Data Act, 639/2019 | <https://www.finlex.fi/fi/lainsaadanto/2019/639> | Current Finnish text page. |
| Public Officials' Language Skills Act, 424/2003 | <https://www.finlex.fi/fi/lainsaadanto/2003/424> | Current Finnish text page. |
| Police Act, 872/2011 | <https://www.finlex.fi/fi/lainsaadanto/2011/872> | Current Finnish text page. |
| Police Administration Act, 110/1992 | <https://www.finlex.fi/fi/lainsaadanto/1992/110> | Current Finnish text page. |
| Reception Act, 746/2011 | <https://www.finlex.fi/fi/lainsaadanto/2011/746> | Finlex showed consolidation ELI dated 9 June 2026 during this review. Recheck the displayed date at retrieval. |
| Openness Decree, 1030/1999 | <https://www.finlex.fi/fi/lainsaadanto/1999/1030> | Finlex provides a current-text page, but parts of the decree were repealed. Identify surviving provisions and their relationship to Act 906/2019 before relying on this as current authority. |
| Information Management Act, 906/2019 | <https://www.finlex.fi/fi/lainsaadanto/2019/906> | Additional gap named by the ZIP audit. Finlex showed consolidation ELI dated 16 June 2026 during this review. |

Finlex's official open-data documentation is at <https://www.finlex.fi/en/open-data>. The API may be checked for an individual act, but a returned XML file needs identity and consolidation-date checks; the official current-law page remains the fallback and is enough for an external reference. Do not rebuild missing consolidation text from Gazette amendments unless a specific provision-level need requires it.

The audit's ten “overlap” files do not need duplicate source records: six Finnish laws are already represented in the catalog (301/2004, 621/1999, 616/2019, 808/2019, 1050/2018 and 423/2003), with Act 621/1999 appearing twice in the ZIP; three EU instruments already exist in shared-core English. Existing links do not accept the ZIP's local copies. Reconcile any actual package files separately, deduplicate 621/1999, and keep its retained-copy review separate from external-reference acceptance.

### Supreme Administrative Court

| Candidate | Official retrieval page | Retrieval notes |
| --- | --- | --- |
| KHO:2024:32, 15 March 2024 | <https://www.kho.fi/paatokset/kho202432/> | Official full decision page. The official annual precedent archive is <https://www.kho.fi/kho-paatokset/ennakkopaatokset/arkisto/>. Retrieve the exact case page, preserve its case number and date, and treat it as one selected precedent rather than a complete case-law search. The page is Finnish; no official English full text was located in this review. |

### Migri application instructions and public guidance

Start from Migri's official [English guidelines index](https://migri.fi/en/guidelines-for-application-of-law) or [Finnish application-guidance index](https://migri.fi/soveltamisohjeet). The Finnish index currently lists the target documents below and links the file attachments. Migri says these application-of-law guidelines are published only in Finnish because they are prepared for the agency's internal use. The English index route returned HTTP 503 in the research viewer, but the official search index exposed the page and the Finnish index's current list. For each PDF, follow the index link, record the document title, publication/revision date, Migri document number, validity statement and attachment URL from the PDF itself, then hash the exact downloaded bytes. Do not infer those fields from the filename alone.

| ZIP candidate | Retrieval route located | Currentness and retrieval status |
| --- | --- | --- |
| Child's best interests (audit copy dated 2026) | Finnish index entry: **Ohje lapsen asian käsittelystä – Lapsen etu -ohje**. Retrieve the PDF from the official index above. | Official index entry found; the direct PDF URL and the copy's document number/date were not verified in this review. Inspect its first and final pages before registering a version. |
| Removal from Finland (audit copy dated 2025) | Finnish index entry: **Ohje ulkomaalaisen maasta poistamisesta – Maastapoistamisohje.pdf**. Retrieve the PDF from the official index. | Official index entry found; exact PDF version/date not checked. The library should keep the decision to remove, enforcement process, and public-facing customer pages distinct. |
| Profiling (2025) | [Official PDF](https://migri.fi/documents/5202425/150086203/Profilointi+asian+selvitt%C3%A4misess%C3%A4,+p%C3%A4%C3%A4t%C3%B6ksenteossa+ja+ulkomaalaisvalvonnassa+(pdf).pdf/d606968d-76cf-ebdf-fd5f-b58eddfe7bbe?t=1752218657816) | Migri search index identifies **Profilointi asian selvittämisessä, päätöksenteossa ja ulkomaalaisvalvonnassa**, published 11 July 2025, reference MIG-2521602. Download and verify the PDF's internal document number/date before capture. |
| Circumvention of entry rules, Aliens Act §§36a–f (2025) | [Official PDF](https://migri.fi/documents/5202425/150086203/Ohje+maahantulos%C3%A4%C3%A4nn%C3%B6sten+kiert%C3%A4misen+arvioinnista+%E2%80%93+36+a-f+-ohje.pdf/2da5e5d0-2ee8-2b14-c5c7-454abafc2c25?t=1781519396424) | Migri's index lists **MIGDno-2025-1509**, with the underlying order dated 18 July 2025 and effective from 1 September 2025. The index result itself was dated 15 June 2026. Preserve both the order date/effective date and the page's publication/update date. |
| Means of support (2025) | [Official PDF](https://migri.fi/documents/5202425/150086203/Ohje+toimeentulon+selvitt%C3%A4misest%C3%A4+ja+toimeentuloedellytyksen+soveltamisesta+lupa-+ja++kansalaisuusasioissa+-+Toimeentulo-ohje+(pdf).pdf/d6fba998-bda6-70de-1e1e-7152f0ae74f7?t=1750337714935) | Migri's index identifies **Toimeentulo-ohje**, dated 19 June 2025, reference MIG-251767. Its combined permit and citizenship scope must be kept distinct from applicant-facing, route-specific means guidance. |
| Family-based residence permits (ZIP copy dated 2021) | Current Finnish index entry: **Oleskelulupa perhesiteen perusteella (pdf)**. Retrieve the presently listed PDF from the official index. | Current index entry found; no exact direct PDF locator or current document date was verified. Keep the 2021 ZIP copy as historical until compared with the current listed file. Do not assume it covers EU free-movement residence-card routes. |

The 2025 circumvention instruction and profiling/means PDFs have direct official locators from Migri's own indexed results. The other three direct PDF locators should be recovered by following the official index or its “Files” search filter; an index listing alone is not a local copy.

For the ZIP's `automation.pdf`, the maintainable route is the current official HTML pages [Automation](https://migri.fi/en/automation), [Automated decision](https://migri.fi/en/automated-decision), and [Frequently asked questions: Automation](https://migri.fi/en/faq-automation). Formal case-type implementation decisions are separate PDFs linked from [Criteria for automated decisions](https://migri.fi/en/implementation-decisions). Capture each needed page or decision as its own source; do not treat a print-to-PDF copy of a public web page as the implementation decision. The older ZIP PDF remains historical until its originating URL and capture date are matched.

The exact title **Euroopan unionin kansalaisen, häneen rinnastettavan sekä hänen perheenjäsenensä maassa oleskelu** was not found as a distinct current Migri instruction. The current manifest/catalog already has three related but unaccepted public-page candidates: [I am an EU citizen or a family member](https://migri.fi/en/i-am-an-eu-citizen-or-a-family-member), [Residence card for a family member of an EU citizen](https://migri.fi/residence-card-for-family-members), and [Application for a family member of an EU citizen](https://migri.fi/en/application-for-family-member). They are marked discovery-only and do not establish availability of the distinct instruction cited by the 2025 circular. Search the Migri guidance index by exact Finnish title and document number; if the staff instruction is needed and not listed, request a copy from Migri through its official records channel.

### Police instruction

The ZIP's **POL-2019-71117, Police Communications** is described in the audit as an expired order. Exact-number searches on Finlex's authority-norm pages, Poliisi.fi and the Ministry of the Interior did not return an official copy or current successor during this review. The available routes are:

1. Search the Police Board's official norm/document register by exact identifier and Finnish title **Määräys poliisin viestinnästä**.
2. If no public file is listed, ask the National Police Board registry for the signed order, its effective/expiry dates, any extension, and any replacing order.
3. Register it as historical only after the retrieved copy's identity and dates are checked; discover the successor separately before using it for current practice.

No records request was sent. Exact-ID searches found no official locator for POL-2019-71117; this is not proof that the order is unavailable. The current POL-2025-163559 listing is accepted as a locator and date reference only, not as a formally verified successor.

### Visa-remedy notice

The ZIP filename **Rectification Request 2022 - FI.docx** did not resolve to an official public file. For current procedure use the Ministry for Foreign Affairs' official [A visa to visit Finland](https://um.fi/visa-to-visit-finland) page and the decision-specific appeal instructions. The MFA page currently describes the ordinary request-for-review route, a 30-day time limit, the stated fee, and the direct administrative-court route for EU free-movement family cases. The 2022 Word file is a historical notice only; do not use its former fee or route as current. If exact provenance is needed, search the originating Finnish mission page or request the dated notice from the MFA. No request was sent.

### Finnish-language EU instrument texts

The ZIP's Finnish texts for these shared instruments belong in the shared EU corpus, if acquired, rather than as duplicate national legislation files. EUR-Lex offers Finnish-language text by CELEX identifier:

| Instrument | Finnish-language EUR-Lex route | Retrieval caution |
| --- | --- | --- |
| Directive 2004/38/EC | <https://eur-lex.europa.eu/legal-content/FI/TXT/?uri=CELEX%3A32004L0038> | Preserve the official Finnish text and any separate corrigenda; an original instrument page is not a consolidated text. |
| Visa Code, Regulation 810/2009 | <https://eur-lex.europa.eu/legal-content/FI/TXT/?uri=CELEX%3A32009R0810> | The EUR-Lex English record showed a consolidated version dated 28 June 2024 and later 2026 provision-level suspensions. Resolve language/version and later-instrument dependencies before relying on a 2024 consolidation as current. |
| Schengen Borders Code, Regulation 2016/399 | <https://eur-lex.europa.eu/legal-content/FI/TXT/?uri=CELEX%3A32016R0399> | Select the latest available Finnish consolidated version and record its date, separate from the original Official Journal act. |

Use the shared language index to avoid duplicate EU texts. No Finnish national-language index was present in the checked checkout, so these would be new shared-corpus language files if accepted. Confirm that the Finnish representation matches the exact EUR-Lex version chosen before accepting it. The research viewer displayed a JavaScript verification interstitial on the direct EUR-Lex text URLs; use the official EUR-Lex browser interface if direct text retrieval is blocked. This is a viewer limitation, not a finding that EUR-Lex lacks the Finnish texts.

## Retrieval evidence and limits

- A live download test on 23 October 2026 retrieved ten Finlex current-law pages and the KHO decision page as raw HTML. The files are in the ignored scratch directory `temp/finland/raw/`; the table records their identity, Finlex current ELI date where available, byte count and SHA-256. These test captures are not accepted local copies or source-catalog records.

| Local raw file | Identity and Finlex current ELI date | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `fi-act-731-1999.html` | Constitution 731/1999; 2018-10-05 | 1,164,399 | `37ab717096abb2f7b2e6367467012a9ff0fb968be54a7d720ecf7b1548274085` |
| `fi-act-13-2003.html` | Electronic Administrative Services Act 13/2003; 2026-03-27 | 469,662 | `b3527cf4e684b495b4a99f14253f856605d8a9c9554cb6bfcf6bdcec1e602b0e` |
| `fi-act-615-2020.html` | Immigration Administration Personal Data Act 615/2020; 2026-07-09 | 715,652 | `066b3f3afb2a42097aa0aab16c1226a0b8878d54b6980d41c89f59c1598de729` |
| `fi-act-639-2019.html` | Border Guard Personal Data Act 639/2019; 2026-09-04 | 1,154,367 | `7efb37bd125d0492becce517ad26f54ae0f282f20781a8ff8a8d648cefd6f812` |
| `fi-act-424-2003.html` | Public Officials' Language Skills Act 424/2003; 2025-12-05 | 416,716 | `45fd06c5a75433cbaa82e6a39ff3b4eaf4ac9af6a8189c9a16b4e1cbb4446af4` |
| `fi-act-872-2011.html` | Police Act 872/2011; 2026-07-09 | 3,310,520 | `4e1933a5a9382392a7653b7c5fa1a15c7d0a0b85e1f44e2b615833a1be0afde2` |
| `fi-act-110-1992.html` | Police Administration Act 110/1992; 2026-05-22 | 957,545 | `3a95539ce47308c8afb9fef63cc83658e06c751c0fcf124bc6866e3eb2a840e4` |
| `fi-act-746-2011.html` | Reception Act 746/2011; 2026-06-09 | 1,181,016 | `fbd03683de2d775ab07cdb77675a16435fa09142166d104566d2a2fe23c73c9e` |
| `fi-decree-1030-1999.html` | Openness Decree 1030/1999; 2010-07-01 | 348,195 | `954dce580030a1f65c4aac5285d6878bb85338b51e065ab646791560052a715c` |
| `fi-act-906-2019.html` | Information Management Act 906/2019; 2026-06-16 | 1,068,424 | `892029c3720e7e9bc3a5843f627c9f0d62f5d44085f1e267a3138abe6f144ef6` |
| `fi-kho-2024-32.html` | KHO:2024:32; case number present in page title and body | 126,228 | `1329d8a0c62330225d640ad7d1856f6a47a121593a8f2b048e7916ab7487ee43` |

- All eleven successful test requests returned HTTP 200 and `text/html`. The Finlex AKN API GET for Act 731/1999 returned 404, while its current-law HTML page returned 200; the browser-page route is the tested fallback for that act.
- Migri's official guidance index and search results exposed the current instruction titles and direct PDF URLs for profiling, means of support, and the §§36a–f circumvention instruction. The child-interest, removal, and family-ties items were visible in the official index but their exact current PDF URLs and document metadata were not inspected.
- The direct official profiling PDF request returned HTTP 403 with a Cloudflare challenge. The Migri index also returned 403 in the shell and Chromium browser test. No Migri PDF raw was captured; the indexed titles and links remain retrieval leads, not retrieved source bytes.
- The KHO decision page was retrieved successfully; the official annual precedent archive remains a discovery route, not a captured source.
- The MFA current visa page request returned HTTP 403 in the shell test. Its official page remains a lead for current procedural reference, not the ZIP's 2022 DOCX.
- EUR-Lex page requests for all three Finnish-language EU instruments returned HTTP 202 with zero body bytes in the shell test; the research browser displayed its JavaScript verification page. No EUR-Lex raw was captured.
- The exact Migri EU-family guide title and the 2022 DOCX filename returned no matching official file locator in this bounded search. The four exact `POL-2019-71117` searches returned no qualifying official copy. These findings are not exhaustive portal reviews.
- The Source Update Monitor plugin lists no Finland source pack or Finland actions. Its mirror sync returned a verified snapshot at the baseline above, but mirror inventory and status calls still reported “not synchronized”; no Finland runtime checks or completion gates are claimed.

## Search record

Searches were run on 23 October 2026. Official-host queries used exact Finnish act numbers and titles on Finlex; the court number on `kho.fi`; Migri guideline titles and the official `soveltamisohjeet`/`guidelines-for-application-of-law` index; the exact Police order identifier on Finlex, Poliisi.fi and `intermin.fi`; the exact Word filename; CELEX identifiers on EUR-Lex; and the visa procedure on `um.fi`. Search results were screened for publisher, title/identifier, and whether the hit was a legal text, a guidance index, an attachment, or merely a related result. Official file links found above are lead locators pending the per-source identity/date checks in this note. No claim of exhaustive national-site discovery is made.

## Follow-up searches for failed retrievals

**Follow-up checked:** 23 October 2026. This addendum records official-site search results and retrieval routes discovered after the first download test. Search results and direct links remain leads unless the note expressly says a raw file was retrieved. The web search view did not expose total result counts; counts below refer to relevant exact locators surfaced, not the search engine's total results.

### Migri instruction PDFs

The official [Finnish application-guidance index](https://migri.fi/soveltamisohjeet) still lists **Ohje lapsen asian käsittelystä – Lapsen etu -ohje**, **Ohje ulkomaalaisen maasta poistamisesta – Maastapoistamisohje**, and **Oleskelulupa perhesiteen perusteella**. Follow-up searches scoped to Migri's document host and each exact title surfaced **zero new direct attachment locators**; the results were the index or public applicant-facing guidance and forms. The index itself returned HTTP 403 when opened in the research viewer, and earlier direct Migri requests also met a Cloudflare challenge. The exact PDF URLs and version metadata remain unverified. Use the official index in a normal user browser to follow its attachment links; do not treat related public guidance or forms as substitutes for these internal instructions.

For **Profilointi asian selvittämisessä, päätöksenteossa ja ulkomaalaisvalvonnassa** (MIG-2521602), the exact-title/identifier search surfaced the same official PDF URL already recorded above and **zero alternate official mirrors or file locators**. The direct PDF request remains blocked in the prior test; no raw was captured.

The distinct EU-family staff instruction **Euroopan unionin kansalaisen, häneen rinnastettavan sekä hänen perheenjäsenensä maassa oleskelu** also produced **zero exact-title official file locators** in this follow-up. The matching Migri index did not list it. Public EU-family pages remain different source material.

### Police communications order

The official [Police Board instructions and orders index](https://poliisi.fi/ohjeet-ja-maaraykset) now provides a strong current-source lead: **Poliisin viestintä**, order **POL-2025-163559**, dated 18 December 2025 and listed as valid 1 January 2026–31 December 2028. The official index's search result exposes the direct [PDF attachment](https://poliisi.fi/documents/25235045/138938434/Poliisin%20viestint%C3%A4.pdf/5024297c-bb52-c354-ddc2-f9e87c9c0cad?t=1767005435861). It is a current order on the same subject, but its status as the formal successor to the ZIP's expired **POL-2019-71117** is **not verified**: the PDF could not be opened in the research viewer to inspect its “amends/repeals” field. Exact-ID follow-up searches surfaced **zero official copy locators for POL-2019-71117**. Keep the old order's historical-copy question open. POL-2025-163559 is now recorded as an accepted official locator with the listed validity dates; its PDF text remains unreviewed because the research viewer returned 403, and formal succession from POL-2019-71117 remains unverified.

### Visa rectification notice

The exact **Rectification Request 2022 - FI.docx** search again surfaced **zero exact official DOCX locators**. It did surface a different official [Finland Abroad PDF, “Instructions for Rectification Request”](https://finlandabroad.fi/documents/2544010/0/oikaisuvaatimusohjeet%2Benglanniksi.pdf/14cf4ad2-98a9-ff87-5116-d1f4b4bd98fb?t=1556260324241). The PDF is in English and contains Embassy of Finland Bangkok contact details; it is a mission-specific comparator, not the requested Finnish 2022 DOCX and not a current general template. The current [MFA visa guidance](https://um.fi/visa-to-visit-finland) says rectification instructions are provided with the decision. Retain the exact ZIP file as historical/unlocated, and use the MFA's current page for current general procedure; do not substitute the Bangkok PDF.

### Finnish EUR-Lex text routes

The searches found official Finnish-language routes for the three shared EU texts, but a search result or rendered page is not a locally captured raw:

| Instrument | Official Finnish route found | What the search establishes / remaining check |
| --- | --- | --- |
| Directive 2004/38/EC | [EUR-Lex Finnish consolidated rendition, 16 June 2011](https://eur-lex.europa.eu/eli/dir/2004/38/2011-06-16/fin/pdf); the original Finnish CELEX page and Finnish corrigenda are also indexed. | Confirms an official FI rendition and a PDF route. The indexed consolidated rendition is dated 2011; inspect the EUR-Lex version/corrigenda record and later legal changes before treating it as current. |
| Visa Code, Regulation 810/2009 | [EUR-Lex Finnish original text](https://eur-lex.europa.eu/legal-content/FI/ALL/?uri=CELEX%3A32009R0810). | Confirms the official Finnish original text. EUR-Lex separately identifies the current consolidated version dated 28 June 2024, but this search did not verify a direct Finnish-language rendering of that consolidated version. Do not label the original text as the current consolidation; resolve the Finnish version and later 2026 provision-level changes. |
| Schengen Borders Code, Regulation 2016/399 | [EUR-Lex Finnish ELI page](https://eur-lex.europa.eu/eli/reg/2016/399/oj?locale=fi). | The official page displays Finnish text, lists FI among the HTML/PDF language choices, and identifies the current consolidated version as 12 October 2025. This is the clearest alternate route for the earlier blocked `/legal-content/FI/TXT/` URL. |

### Retrieval attempt and limits

The official-site searches surfaced the routes above, but this follow-up created **no new raw files**. A repeat local HTTP attempt could not resolve hostnames from the shell (`Temporary failure in name resolution`), so that attempt gives no new publisher response status. The previous observed Migri 403, EUR-Lex 202 with an empty body, and MFA 403 remain the only recorded direct-request outcomes for those sites. The Police order PDF also returned 403 in the research viewer. No bot challenge was bypassed, no external records request was sent, and none of these new links is recorded as a locally captured or accepted copy.

| Search scope and exact terms | Relevant official locators surfaced | Disposition |
| --- | ---: | --- |
| Migri document host: exact titles for “Lapsen etu -ohje”, “Maastapoistamisohje”, and “Oleskelulupa perhesiteen perusteella” | 0 new direct attachment URLs; 1 official index lists the targets | Locator recovery still open; normal-browser index route remains. |
| Migri document host: “MIG-2521602” / exact profiling title | 1 previously known official PDF URL; 0 alternate URLs | Same locator, retrieval blocked; no raw. |
| Poliisi.fi: exact “POL-2019-71117” and “Poliisin viestintä”; official orders index | 0 old-order URLs; 1 current order PDF, POL-2025-163559 | Current candidate found; succession relationship unverified. |
| Finlandabroad.fi / um.fi: exact “Rectification Request 2022 - FI.docx” and Finnish visa rectification terms | 0 exact DOCX URLs; 1 different mission-specific official PDF | Exact file remains unlocated; current MFA guidance and historical comparator identified. |
| EUR-Lex CELEX / ELI Finnish routes for 2004/38, 810/2009 and 2016/399 | 1 official FI route per instrument | Routes found, but no new raw downloads; current-version checks remain separate. |

The Source Update Monitor pack inventory was also checked during this follow-up: it has no Finland pack, so it cannot run Finland-specific source acceptance, retrieval, or completion checks.

## External-reference acceptance update

**Checked:** 23 October 2026. These entries resolve official link discovery only. They do not record downloaded raw files, accepted local copies, or topic coverage.

- **Police communications:** the Police Board index identifies order **POL-2025-163559**, document **ID-25841820**, dated 18 December 2025 and valid 1 January 2026–31 December 2028. The official linked PDF returned 403 in the research viewer. Its identity and dates are accepted as an external locator; its text and formal relationship to **POL-2019-71117** remain open. See the source-catalog and acceptance-register entries.
- **Directive 2004/38/EC:** EUR-Lex identifies the Finnish consolidated text dated **16 June 2011** as the current consolidation. The page lists corrigenda separately and states the consolidation is an informational aid without legal effect. The FI link is in [`shared-core-index-FI.json`](../../shared-core-index-FI.json).
- **Visa Code, Regulation 810/2009:** a Finnish consolidated text dated **11 June 2024** was located. EUR-Lex identifies **28 June 2024** as the latest overall consolidation, and the later Finnish rendition was not verified. Decisions (EU) 2026/1454 and 2026/1733 suspend specified provisions for nationals of Somalia and Guinea, respectively. Keep the language-version gap and country-specific dependencies open; do not present the 11 June Finnish text as the latest complete current text.
- **Schengen Borders Code, Regulation 2016/399:** EUR-Lex search results expose the Finnish consolidated text dated **12 October 2025**. The exact versioned official link is recorded in the Finnish shared-core index.

The three EU instruments are registered once as external-only Finnish shared-core references in [`shared-core-index-FI.json`](../../shared-core-index-FI.json), and Finland points to them from [`shared-core.json`](shared-core.json). No `core/fi/` files were created because no Finnish raw text was captured. The earlier search record's “no Finnish index present” statement describes the checkout before this update.
