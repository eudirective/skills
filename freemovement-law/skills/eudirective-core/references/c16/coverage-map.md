# C16: expanded legal-topic coverage — fictional reviewer use only

**Version:** 0.1.0 · **Date:** 2026-10-10 · **Scope:** Eight code-enrolled fictional C10 cases. Never a decision on an applicant's legal rights.

C16 uses the existing C12 structured source-bound fact ledger plus C13 passage-anchored raw-document review. The C12 `activation` field is a **topic-selection trigger**, not a conclusion that an untriggered legal rule is inapplicable to a real dispute. An `not_applicable` label for a non-activated C16 rule means only *not raised by that enrolled fixture's provable typed signal*. Contradictions, missing documents, and actual-law exceptions still require examination.

| Fixture | Core C16 question | Sweden C16 question | Türkiye C16 question | Evidence limits |
|---|---|---|---|---|
| L2: optional VFS payment | `eu:c16:visa-fee-v-provider-charge` | `se:c16:istanbul-service-fee` | `tr:c16:istanbul-vfs-choice` | A recorded service charge is not an unlawful consular visa fee; optional access must be assessed, not assumed. |
| L3: alternative relationship proof | `eu:c16:exclusive-proof-visa` | `se:c16:document-list-review` | — | A purported exclusive checklist is not automatically unlawful; authenticity and relevance matter. |
| L6: card before visa | `eu:c16:prior-card-entry-gate` | `se:c16:visa-card-route` | — | Entry visa and residence card are separate procedures; check Article 5(2) exemptions and Directive scope. |
| L7: JO route | — (EU Charter applicability not presumed) | `se:c16:jo-supervision-boundary` | — | JO criticism does not substitute for annulment or a timely legal appeal. |
| L8: electronically issued Turkish record | `eu:c16:electronic-proof-format` | `se:c16:electronic-format-review` | `tr:c16:electronic-population-extract` | Turkish domestic legal validity does not establish Swedish evidentiary acceptance. |

L1, L4, L5 remain enrolled unchanged: direct-consular access, Swedish visa appeal, and fact-specific *Deldwyn* disclosure. There are now 8/8 C10 scenarios with pinned C12 ledgers and C13 raw-document sets. The newly added C13 English extraction cues are **developer-authored synthetic fixtures**, not a multilingual semantic improvement or independent evaluation. For unfamiliar prose, use the host model's C15 review-only proposal flow, not a brittle token match or autonomous adjudication.

## Reader workflow

1. Identify whether a Directive 2004/38 entry-visa, residence-card, appellate, or supervisory matter actually arises. Confirm mobility, qualifying family status, territorial scope and relevant exceptions before any EU-law reasoning.
2. Check the SHA-bound C12 typed ledger *and* C13 exact passage quotations. Neither authenticates the source or proves a statement true. Treat denial of access, a refusal to consider alternative evidence and a date recorded by an email as claims pending source verification.
3. Retrieve primary EU text using C15 `retrieve`. Check article locality and relevant source identity. A bundled checksum proves identity of local bytes only. **Known source flaw:** the bundled 2004/38 consolidation appears to omit Article 2(2)(a); verify the definition of spouse independently against an official full text before relying on it.
4. Consult Sweden and Türkiye source notes as **review hints only**. These modules do not contain complete consolidated national legislation and are not empowered to state all applicable exceptions.
5. Distinguish reported problem, evidence-supported fact, legal question, candidate compliance issue, remedy, and possible novel issue. Do not treat `supported_for_review` as a finding of illegality.
6. Run `python scripts/test_c16_coverage.py`; verify the full C6/C7 regression suites after changing rules or trusted inputs. C15f independent legal-semantic evaluation has been **explicitly deferred**.

## Source ownership

- EU Article 5(2), Articles 9–10, 35 and 30–31, general principles, the Charter and EU guidance: **core**.
- Swedish administrative procedure, Utlänningslag, Istanbul EU-family application guidance, fees and JO competence: **member-state Sweden module**.
- Turkish electronic document origin and the Swedish mission/VFS operational interface in Türkiye: **applicant-country Türkiye module**.

**Enforcement:** all C16 extensions are typed JSON data with frozen C3 module-export digests; there are no country-to-country calls, legal decisions, live external writes or private-case inputs.

## C18 correction (2026-10-10)
The historical warning above applies to the archived v0.6.0 source. The C1 v0.6.1 test fixture contains Article 2(2)(a) from an official HTML passage check. The rest of the source pack and national-law coverage have not been independently verified; do not infer legal merits from the local repair.
