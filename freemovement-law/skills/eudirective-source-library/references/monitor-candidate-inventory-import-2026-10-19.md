# Monitor candidate inventory import

Date: 2026-10-19

This import reconciles the public source library with the candidate dossiers shipped in `plugins/eu-source-update-monitor/source-runtime/eudirective-source-library-0.6.0/` at repository revision `e2196cc2f5f22b6f5a6108f0c05d98b0f698988e` in `eudirective/internal`. The inventories identify laws, official guidance, forms, decisions, oversight sources, and discovery channels. They are candidate records, not accepted texts. An entry is not treated as a retrieval authorization or proof of currency.

Where the public library already had a different country manifest, the imported full monitor register is stored separately so that existing records and converted review artifacts remain intact. Where no candidate manifest existed, the monitor register is added as `candidate-manifest.json`. Existing Finland and Estonia lowercase country slugs and local sustainability assessments are retained. Luxembourg and Malta have a register and source list but no README in the monitor bundle; this library marks those folders as candidate-only.

New country folders: iceland, ireland, latvia, liechtenstein, lithuania, luxembourg, malta, norway, poland, slovakia, slovenia, switzerland.

Supplemental monitor registers: italy, netherlands, portugal, spain.

Candidate manifest files added or copied: 10.

## Retrieval progress

The Spain register has 15 BOE legal texts converted to unaccepted review candidates under the BOE retrieval manifest. Finland has six legal-text conversions: browser-rendered current-text captures of the Aliens Act and Administrative Procedure Act, the 808/2019 Akoma Ntoso API response, and three unofficial English translation PDFs with publisher-recorded amendment cutoffs. The 808/2019 XML has unresolved expression/consolidation/effective-date metadata; the English translations are dated and unofficial. All six remain unaccepted. These changes do not mark any source accepted and do not complete the remaining candidate texts.
