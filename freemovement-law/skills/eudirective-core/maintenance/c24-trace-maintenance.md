# C24 trace/revision invariants (modifier-only)

The v0.37.0 read-only conversation lane aims to improve user-facing reasoning, **not** to admit private data into C6/C7/C17/C21 or convert an advisory answer into a controller-certified legal finding.

- Keep the actual source-driven narrative-to-predicate mapping in the reviewed *model-led conversation*. `scripts/c24_fact_rule_trace.py` takes strict abstract values from a reviewer. No script claims to parse or validate testimony. Its source list contains locally pinned EU/common-law review pointers only, not verified national remedies.
- Preserve `c23_scope_contrast` source verification and its exact scope predicates. If the C24 gate reuses it, do not re-implement its legal checklist rules; adding alternative regimes must be legally sourced and separately tested.
- Reject all free-text fields in C24; never include private/user documents, case identifiers, location/date particulars or host logs in automated trace fixtures. Even a minimal abstract vector is not guaranteed anonymous. Do not write real-case abstract vectors persistently by default.
- Revision comparison must show changed facts, mark affected conclusions stale and flag direct yes/no reversals for human reconciliation. Do not label a newer claim 'true' merely because it arrived later; use 'user correction' etc. The tool does not solve underlying credibility.
- Cases with national authority, formal appeal deadlines or returnee/Article 3(2) complexity require live source and additional legal review. `no direct three-feature scope` must not be promoted to `no rights`.
- Unit tests are contract/logic tests. Preserve a **separate, withheld, model-response** suite with both first-turn and 2-3-turn interaction cases. Record exact installed skill version plus profile differences. An empty capture never passes, and a quotation's presence does not prove its legal relevance. Expert substantive review is necessary for national law and correctness.
- Keep the OpenAI `agents/openai.yaml` profile as a separate platform overlay; explicit invocation is the safest default until actual skill responses have been assessed. Do not silently change installed user-managed profile settings.

No MCP, network write, incoming real-case file processing, telemetry or real-case retention layer is included in C24.
