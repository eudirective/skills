# Poland candidate pack

This directory stages 54 official-source candidates found from the Danish EU free-movement residence seed and earlier jurisdiction findings. Poland is an EU Member State. Its EU/EEA/Swiss, returning-Polish-national, UK Withdrawal Agreement, national-permit and asylum routes remain distinct.

- [Candidate source list](references/source-list.md)
- [Candidate manifest](references/candidate-manifest.json)
- [Proposed-route sustainability assessment](references/sustainability-assessment.md)

The pack now has a bounded capture rule for the Polish ELI API and official candidate pages. Of 54 candidates, 51 exact responses were saved and 50 converted as unaccepted review material; 0 sources are accepted. Seven PDFs were extracted with pinned pypdf 6.21.1 and pass offline replay. Three public requests failed (one 403 and two certificate-verification errors), and the e-Konsulat portal returned a dynamic shell without source text. Official ELI current-act searches surfaced newer current consolidated texts for the EU-citizen residence Act (DU/2026/1065) and the Free Legal Aid Act (DU/2026/44); prior editions remain as historical candidates. API-specific reuse terms, automatic change discovery, article-level commencement and broader source coverage remain open. EU-citizen registration stays separate from national residence-permit filings; the UDSC/ePUAP versus UODO SIS submission conflict also remains for legal review.

Install the pinned local PDF extractor with `python -m pip install -r source-library/poland/requirements.txt`. Run `python source-library/poland/sync_poland.py sync` to refresh all configured candidate URLs, or pass candidate IDs to refresh selected records; run `python source-library/poland/sync_poland.py verify` for offline hash and conversion replay. Changed source bytes are staged for review. No source is automatically accepted.
