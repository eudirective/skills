# Slovakia national-source candidates

Discovery register dated 2026-10-18; capture state updated 2026-10-19. It contains 40 official-source candidates across free-movement and family-residence law, visas and missions, administrative procedure and remedies, privacy, oversight, legal aid, and court-search routes. Fifteen Slov-Lex legal candidates now have date-bound current-version text and binding PDFs captured, with eleven linked annex PDFs. Across the register, 31 source texts were converted and replay-verified; eight MFA requests returned HTTP 403, and the archive-index page was inspected but not captured as text. No locally stored artifact is accepted.

- Candidate register and native-language search log: [`references/source-list.md`](references/source-list.md)
- Machine-readable candidate metadata: [`references/candidate-manifest.json`](references/candidate-manifest.json)
- Static archive-index capture attempt: [`references/archive-index-pass-2026-10-19-capture-results.json`](references/archive-index-pass-2026-10-19-capture-results.json)
- Generic first-pass capture ledger: [`references/slovakia-capture-results.json`](references/slovakia-capture-results.json)
- Slov-Lex legal-text/PDF capture ledger: [`references/slovlex-captures.json`](references/slovlex-captures.json)
- Slov-Lex capture and offline replay rule: [`sync_slovakia.py`](sync_slovakia.py)
- Generic capture and offline replay for the other source classes: [`../sync_candidate_pages.py`](../sync_candidate_pages.py)
- Sustainability assessment: [`references/sustainability-assessment.md`](references/sustainability-assessment.md)
- Country sequence: [`../references/eea-switzerland-country-expansion.md`](../references/eea-switzerland-country-expansion.md)

Use `python source-library/slovakia/sync_slovakia.py sync` to refresh Slov-Lex acts; it resolves each act’s currently effective date from the official history index, fetches the date-bound printed HTML, binding PDF, and linked annex PDFs, and stages changed outputs for review. Use the matching `verify` command for offline hash and conversion replay. The dynamic archive index links to a public static chronological registry at `https://static.slov-lex.sk/static/SK/ZZ/`; it displays years 1918–2026 but still needs an exact-byte capture. The local capture attempt was blocked by temporary workspace DNS resolution failure; do not classify this as a Slov-Lex outage. The shared page capture handles other Slovak source classes; do not bypass HTTP errors or alter TLS verification.

Comparison seed: Denmark's EU free-movement residence regulation, with Sweden, Finland, Czechia, Hungary, and Romania findings carried forward only as discovery leads. Act 404/2011 is a broad immigration statute and only a partial functional match. Its definition of “member state” generally includes EU states, EEA states, and Switzerland, but narrows to EU Member States for §§30 and 51–57. No legal equivalence or complete inventory is claimed.
