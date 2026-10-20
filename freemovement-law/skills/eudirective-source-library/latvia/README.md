# Latvia source discovery

This directory contains the Latvian official-source candidate register, captured review texts, and a retrieval/conversion prototype. It is not an accepted or active legal-source pack.

- Candidate manifest: [references/candidate-manifest.json](references/candidate-manifest.json)
- Human-readable register: [references/source-list.md](references/source-list.md)
- Proposed-route sustainability review: [references/sustainability-assessment.md](references/sustainability-assessment.md)

Latvia is an EU Member State. EU, EEA EFTA, Swiss, and UK Withdrawal Agreement routes are recorded distinctly. The new Latvian EU/EEA/Swiss residence law took effect on 10 July 2026; a separate new Immigration Law took effect on 15 September 2026. The MFA EU-family page still cites the former Cabinet Regulation 675, while PMLP’s central page was updated after the new Act. Older forms/checklists need reconciliation against the new law and forthcoming Cabinet rules.

As of 19 October 2026, the 49-record register has 43 direct official-source captures: 41 HTML pages and 2 PDFs converted to unaccepted review-candidate Markdown. Both original PDFs remain preserved byte-for-byte. Six records are discovery or case-law database routes without an individual text. Offline verification replays all 43 conversions and verifies each original PDF hash.

The direct pass covered legislation, agency guidance, forms, visa and mission pages, administrative procedure, privacy and oversight, legal aid, and complaint routes. It did not download individual court decisions: the three court entries identify repositories/search surfaces, not specific decision records. The Gazette PDF and PMLP form PDF are preserved and extracted page-by-page with pinned `pypdf==6.21.1`; the Gazette signature is not cryptographically validated and Markdown does not recreate the form's 182 interactive fields. The PDF links and parent indexes need currentness review before relying on either file.

Run `python3 sync_latvia.py convert-pdfs` to rebuild PDF candidate Markdown from preserved bytes, `python3 sync_latvia.py reconvert` to replay every saved HTML and PDF conversion, and `python3 sync_latvia.py verify` to check source/output hashes and deterministic conversion. PDF tooling is pinned in [`requirements.txt`](requirements.txt). These commands do not retrieve sources.

The ordinary HTTPS route worked without API registration or publisher security challenges. The publisher's official terms allow reuse under Latvia's public-information rules and applicable fees, and say the publisher organizes reuse. Latvijas Vēstnesis requires written coordination stating the purpose and product/service; its current public service supports grouped official notices. Confirm in writing that a recurring legal-text library is covered and what fee or delivery route applies before running a scheduled mirror. The bounded refresh uses a one-second delay, stores exact source bytes/hashes, ignores only observed volatile script/CSRF/view tokens for change comparison, and stages any other response change for review. See the [retrieval capture manifest](references/latvia-captures.json) and [sustainability assessment](references/sustainability-assessment.md).
