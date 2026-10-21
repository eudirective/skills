# Consultation dashboard examples

The board follows the legal answer and coverage note. These are illustrative
formatting examples, not case assessments or execution records. Keep the
default board compact; use `references/consultation-routing.md` for the expanded
audit and full source/use ledger.

## Compact dashboard

Use this Markdown fallback when the client has no richer presentation
capability. Render each line from the structured receipt; do not guess values.

## FreeMovement — Consultation Review

**Partial**

- **This response:** 3 legal texts · model-reported
- **Conversation total:** 5 legal texts · model-reported
- **Library sections:** 2 · **Outstanding issues and checks:** 2

**Execution** · 5/5 required or triggered operations recorded complete.

**Legal texts read**

- **EU core · legislation · 1** `▰▰▰▰▰▰▰▰▰▰▰▰`
  - Directive 2004/38/EC — Articles 2, 3 and 5 (currentness not verified)
- **Spain · official guidance · 2** `▰▰▰▰▰▰▰▰▰▰▰▰`
  - [Official source title] — section 8
  - [Official source title] — application procedure

**Still missing — material issues**

- Receipt not inspected; formal lodging and the processing-clock start remain unverified.
- Current national urgent-remedy procedure not checked; the available time-sensitive route remains uncertain.

**Relevant modules**

- `eudirective-core` — used this response; used earlier in this chat; available; C3 not applicable.
- `eudirective-ms-spain` — used this response; not used earlier in this chat; available; C3 not checked.
- `eudirective-ac-turkiye` — not used this response or earlier; available; not applicable to the stated role.

*Source counts and module-use states are model-reported. This plugin has no host-authenticated source-read event; the local validator cannot prove that a source was opened.*

The source bars compare the source groups displayed for this response; they do
not represent the proportion of a library reviewed. A candidate or unaccepted
source remains counted if it was actually consulted, with its acceptance state
shown beside the source. An external official text is shown in its own group,
not as a bundled-library section. Keep all pinpoints in the expanded audit if
the compact line must be shortened.

The compact renderer shows at most 10 source groups, 12 source titles/pinpoints,
3 highest-priority missing issues/checks, and 10 module-use rows. It reports
how many records were omitted and retains the full source ledger and all
missing/effect details for the expanded audit. Order gaps by urgency and
materiality before rendering.

For a C3-validated module pair, the receipt's `module_id` and `role` must use
the exact manifest ID and canonical supported-role token. Optional
`display_name` and `role_label` fields keep those validated values while
showing familiar plugin and role names in the dashboard.

When source-use tracking is unavailable, show `unknown` instead of a zero and
state that any listed sources are only the incomplete recorded subset. A
source identified but not read or cited from memory is not included in the
consulted count; show these separately if material. A direct explicit
invocation unrelated to legal consultation uses only:

## FreeMovement — Consultation Review

**Not verified** · No case assessment was performed.

## Expanded audit

When requested, include one issue record per proceeding with its disposition,
exact C27 IDs/status/method/evidence, missing evidence and effect. Follow this
with a separate execution board for model-led review, retrieval, engines and
validators. Name each operation ID and report `not checked`, `unavailable`,
`partial`, or `blocked` when appropriate. Include every source title and
consulted pinpoint; separate this response from earlier conversation use,
identified-not-read items, memory citations and external official sources.
Finish with module use and C3 conformance evidence. Never present source-pack
availability, a read instruction, or a module name as proof that it was used.

**Assurance:** source reads and module use in this package are model-reported.
The local validator checks declared records and selected validator outputs; it
rejects `runtime_recorded` source states because no host-authenticated read
event is available. The plugin does not call the validator automatically and
no host-enforced release gate is established.
