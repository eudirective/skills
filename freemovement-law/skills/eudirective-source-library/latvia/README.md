# Latvia official-source review

This directory contains the Latvian official-source register, scoped external-link decisions, captured review texts, and a retrieval/conversion prototype. Official links can be used within their recorded scope; no local copy or topic is accepted and the country review is incomplete.

- Candidate manifest: [references/candidate-manifest.json](references/candidate-manifest.json)
- Source acceptance: [references/source-acceptance.json](references/source-acceptance.json)
- Issue-led coverage: [references/coverage-register.md](references/coverage-register.md)
- Legal dependencies: [references/dependency-register.json](references/dependency-register.json)
- Human-readable register: [references/source-list.md](references/source-list.md)
- Proposed-route sustainability review: [references/sustainability-assessment.md](references/sustainability-assessment.md)

Latvia is an EU Member State. The 52-record inventory distinguishes EU/EEA/Swiss free movement, UK Withdrawal Agreement beneficiaries, and third-country immigration. Forty-one official links are accepted within narrow recorded scopes; seven are pending and four stale or unverified records are not relied upon. Three additional primary laws cover address registration, population-register records, and civil-status documentation. The current free-movement Act took effect on 10 July 2026. Its transitional text, the displayed validity of Cabinet Regulation 675 through 2 December 2027, and the new rule-making deadline leave Regulation 675’s application to post-commencement filings unresolved. The MFA page still describes Regulation 675 as the governing route; the current PMLP overview points to the new Act. See the acceptance, coverage, and dependency registers before relying on operational instructions.

The 52-record register has 43 direct official-source captures: 41 HTML pages and 2 PDFs converted to review-candidate Markdown. Those local copies remain unaccepted; both original PDFs are preserved byte-for-byte. Six records are discovery or case-law database routes without an individual text. The external-link acceptance decision is a separate lane and does not change the capture status.

The source review covers legislation, agency guidance, forms, visa and mission pages, administrative procedure, privacy and oversight, legal aid, and complaint routes. It did not identify individual court decisions: the court entries identify repositories/search surfaces, not specific decisions. A signature check is not a routine gate for a government-published consolidation; verify it only if a conclusion depends on that Gazette file's seal. Confirm that the PMLP form is linked from its current parent page before using it.

Run `python3 sync_latvia.py convert-pdfs` to rebuild PDF candidate Markdown from preserved bytes, `python3 sync_latvia.py reconvert` to replay every saved HTML and PDF conversion, and `python3 sync_latvia.py verify` to check source/output hashes and deterministic conversion. PDF tooling is pinned in [`requirements.txt`](requirements.txt). These commands do not retrieve sources.

The ordinary HTTPS route worked without API registration or publisher security challenges. The publisher's reuse terms and fees concern retained or recurring copies; they do not block ordinary links to the official consolidated texts. No scheduled mirror is proposed here. See the [retrieval capture manifest](references/latvia-captures.json) and [sustainability assessment](references/sustainability-assessment.md) for the separate optional capture and reuse assessment.
