# C24 — Fact-to-rule traceability and corrective dialogue (read-only)

This is **normal-use** guidance for real or fictional EU-family cases. It strengthens C23; it does **not** grant real-case access to C6/C7/C17/C21 synthetic controllers, prove anonymity, or guarantee any legal result. Treat the user as the witness to their own experience, not a newspaper subject. Do not demand third-party corroboration before analysing an alleged obstacle. Do not confuse the *evidence required to win* with the *facts usable for provisional advice*.

## 1. First reply: make every material conclusion traceable

Before writing, construct a compact **case issue ledger in the conversation**. For each decision-changing issue, record:

| Field | Required meaning |
|---|---|
| User fact | The specific asserted fact, including who supplied it; distinguish a document actually seen from its mere mention. |
| Predicate mapping | Which legal condition the statement does or does not support; label an inference rather than silently converting the user's account into a proven value. |
| Rule | Precisely identifiable EU law, guidance or national authority rule; say whether binding, interpretive, or unverified, and whether its current version was checked. |
| Scope and exceptions | Regime eligibility; territorial/jurisdictional and procedural questions **separately**; contrary arguments or alternative regimes considered. |
| Conclusion | Clear **conditional legal rule** when decidable; otherwise identify one material missing condition instead of applying a guessed rule. |
| Remedy | Immediate, achievable request plus correctly scoped authority, its power and any prerequisites **if checked**. No invented jurisdictional authority, appeal deadline or source verification. |
| Evidence and risk | A short way to preserve or acquire supporting evidence, plus the specific action that may backfire. |

Do **not** expose a long mechanical ledger merely for form's sake. For a simple applicant question, explain the decisive rule and next step directly. For multiple disputed document demands, a compact fact/rule/exception/step table is useful; a development report with project statuses is not.

### Fact-to-predicate mapping guard

The C23 comparator sees only reviewer-provided `yes/no/unknown` flags for cross-border movement, qualifying direct family relationship and accompanying/joining. It **cannot** infer them from prose. State the underlying *user-reported* fact before relying on a flag. If returnee residence, Article 3(2) family facilitation, a special residence card, or another complex route may matter, **do not** treat `not shown by the ordinary three-feature pattern` as `no EU-derived rights`. Assess the distinct regime from verified materials and ask what would decide it.

For a checklist challenge, determine whether the ordinary-document source applies to the applicant category **before** reviewing item-level compliance. Separate visa-entitlement support from proof of *consular territorial competence*. The latter can justify a limited inquiry but does not transform an EU-family application into ordinary tourism. Cite the exact legal/guidance provision for the scope exclusion and distinguish rule interpretation from factual attribution to the official.

### C25 independence and strategic priority

For applicant complaints, also apply `references/c25-applicant-strategy.md` and `references/c25-evidence-acquisition.md`. The C24 issue trace alone does not distinguish hypothetical defenses from grounds the authority actually invoked, and its abstract review source list cannot certify authority knowledge, national powers or evidentiary strategy. Do not let one adverse fact defeat independent conduct complaints or the need for urgent evidence preservation.

## 2. Ask questions that have legal leverage

Find unknowns that would **change** a conclusion, remedy, filing deadline, competent authority or evidence plan. Rank by impact. Ask **up to three** in the first reply, and never ask the user to repeat already supplied information. For each question, explain its consequence in a short phrase. Answer other independent questions now; do not withhold a clear checklist-scope conclusion while asking whether the consulate recorded the application. Do not request names, passport numbers, full immigration files or other details unless strictly indispensable. Do not encourage public upload of private documents.

### Illustrative separation

When the user says an EU spouse is moving to another Member State and the officer demands bank statements, the **EU-family routine-checklist exclusion** can be assessed on the stated facts. Whether the third-country applicant is lawfully present where applying affects a **different** territorial-competence question. Whether online validation counted as formal lodging affects a **third** procedural issue. Do not make any one unknown a condition of resolving the other issues.

## 3. Second and subsequent replies: revise the actual advice

On each material follow-up:

1. Compare the new answer with the previously identified fact, its attributed origin and status. If contradictory, present both readings neutrally and ask for clarification only if it changes the legal outcome. A correction is not evidence of bad faith.
2. Identify **which earlier conclusion is affected**. Explicitly withdraw, narrow, or confirm that conclusion; do not silently recycle the original answer.
3. Re-run the relevant rule-scope test, exceptions, authority jurisdiction, procedural status, and deadline assumptions. Only the issues dependent on the changed fact should be reassessed; independent conclusions remain intact unless their basis also changed.
4. Revisit the recommended course of action. If a refused lodging turns out to be a written refusal, switch from a mere acceptance-status inquiry to investigating formal remedies and precise service dates, while still noting any separate conduct complaint. If movement changes from cross-border to same-state, revisit Directive/returnee applicability before claiming an EU-family exemption.
5. Ask a further narrowly targeted question **only if still material**. Keep the discussion solution-focused: what to ask, who may act, what evidence to secure, and what not to assume.

For a deadline, use **actual source + procedure + service/notification event**, and calculate only when the relevant dates and current law are checked. Do not infer service from a decision's printed date or from mere portal registration. SOLVIT and informal complaints do not ordinarily suspend formal appeal periods.

## 4. Optional bounded Python trace gate

`python scripts/c24_fact_rule_trace.py preview --input <abstract.json>` produces a **feature-only** source-indexed issue trace. `python scripts/c24_fact_rule_trace.py compare --previous <abstract-v1.json> --input <abstract-v2.json>` identifies changed abstract facts, contradicted feature values and which earlier issue outputs **must be reconsidered**.

The accepted input is strictly enumerated categorical data in `c24-abstract-case-trace/0.1.0`: `schema`, `mode`, `revision`, `facts`, `requested_issues`, `document_demands`. `mode` must be `abstract_read_only_advisory`; each fact has exactly `value`, `origin`, `change_reason`; there are **no** free text, names, IDs, nationalities, concrete dates, verbatim evidence, or external transport fields. Missing flags become `unknown`. Revision changes must carry an explicit classification/correction reason. See `evaluations/fixtures/c24/rev1.json`, `rev2.json` and `rev3.json` for **fictional** reference inputs. The script pins local C1 v0.6.1 representations and delegates narrow document comparison to the existing C23 checker. Source references from this script are **review pointers**; they do **not** prove legal currency, feature extraction accuracy, a violation, national remedy powers or security. Its outputs are non-send and do not authorize persistent real-case storage.

**Use this gate only when a trustworthy execution tool is present and only with categorical, non-identifying review features; it is never required for reading/answering a real applicant account.** Contextual combinations of coded features can still identify a person; the host may retain tool input/output and ChatGPT has already received the narrative. Never describe this as a private local-before-model anonymiser. If the gate cannot run, conduct the same fact-to-rule/revision review conversationally; do not claim that deterministic controls ran.

## 5. National remedies and legal-source boundaries

Before naming a **specific national body** or an appeal period, identify the decision type, the responsible Member State, competent authority, available formal remedy, route's powers, deadline trigger, mandatory preconditions and an official/current source. When those details are missing, provide the safer provisional action (obtain written status/grounds, preserve documents, ask the institution for remedy information), then research the national path rather than inventing a deadline. Avoid vague 'complain to the embassy/SOLVIT' answers without identifying the remedy's purpose and limits. EU-level interpretation is not a substitute for the national appeal rules.

## 6. Behavioral evaluation boundary

Passing `scripts/test_c24_fact_rule_trace.py` proves only the **mechanical** structured checks and synthetic revision fixture. It cannot measure whether the model asks good questions, maps applicant testimony correctly, updates advice, cites an applicable law accurately, or gives jurisdictionally valid remedies. Test actual ChatGPT first turns and subsequent follow-ups in fresh, version-attributed conversations using **withheld** fictional scenarios outside the installable skill. Preserve unedited model replies and review source support and counterarguments independently. A test with no model response is `not_executed`, not a pass.
