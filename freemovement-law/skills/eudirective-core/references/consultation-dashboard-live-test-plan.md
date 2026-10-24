# Historical consultation dashboard live-test plan

**Current status:** This is a preserved historical test design, not an active maintenance task or an assignment to the user. Do not ask the user to run it, copy prompts, or collect responses. Reopen behavioral evaluation only if a verified agent-controlled runtime can invoke the exact target build and capture its responses, or the user explicitly requests a changed evaluation scope. Otherwise record `not_feasible_current_runtime` and keep behavior unverified in the private fm-maintenance status record.


**Status:** ChatGPT live checks remain deferred and are not required to finish maintenance. The locally installed v0.58.2 package is the baseline; candidate v0.59.1 is not installed in this environment. The prior manual installed-bundle check covered v0.58.2 only. A fresh session with each exact build remains necessary for client-level behavior checks. Use fictional, non-sensitive facts in any future chat review; do not place those facts or conversation text in a renderer receipt or temporary file. No hosted service or MCP is part of the plan.

## Target builds

| Arm | Plugin / core | Source identity |
|---|---|---|
| Baseline | `0.58.2` / `0.57.2` | `eudirective/skills` commit `d5db832670c43aac2c69f53c29b9f2511f28de79` |
| Candidate | `0.59.1` / `0.58.1` | `eudirective/skills` commit `c84547a37f08e1c273fbe04e04c8f73a1990be93` (local candidate source; not published) |

Before a live comparison, load each exact build separately and confirm the visible plugin/core versions. Do not treat the currently installed baseline as the candidate. If either build identity cannot be confirmed, leave the live run unexecuted.

## Setup

1. For each arm, start a fresh Codex session with that exact `freemovement-law` build. Confirm the selected plugin and core versions before capturing evidence. The currently installed v0.58.2 baseline is not evidence about candidate v0.59.1.
2. In a fresh chat, select freemovement-law through the normal interface and use fictional facts. Record the client, plugin version, date, and visible response.
3. Review the response at desktop width and a narrow/mobile width if available.

The local Codex path uses the selected build's bundle and shell manually. With a synthetic receipt, run `python3 scripts/consultation_route_gate.py <receipt.json> --dashboard-only`; compare stdout byte-for-byte with `dashboard_preview` from the JSON mode. The prior check covered v0.58.2. Repeat against v0.59.1 before recording candidate local-runtime evidence. This proves local command integration and deterministic Markdown generation only. It does not prove that ChatGPT calls the renderer, includes its output unchanged, or enforces release.

## Cases

### A. Substantive consultation with mixed issue statuses

Ask a fictional EU-family visa question involving an EU citizen moving to another Member State with a spouse. Include enough fictional details for several issues to be supported and at least one issue to remain partial because a receipt or written decision is missing.

**Check:** the substantive answer appears first. The dashboard begins with a case title, jurisdiction/proceeding subtitle, and plain-language overall status. The three metrics are `Issues reviewed`, `Supported / conditionally closed`, and `Partial / open`; the latter two combine exactly as specified, while the status distribution separates supported, conditionally closed, partial/open, and out-of-scope. A short segmented bar has one segment per recorded issue only when dispositions are complete and there are 20 or fewer. Above 20, all counts and percentages remain visible without the bar; incomplete dispositions display unknown counts and explain why the bar is unavailable. Percentages describe recorded outcomes, not legal completeness. The layout remains readable on a narrow screen; if the metric table is cramped, stacked metric lines are acceptable.

### B. Issue cards and missing-item effects

Use the same case and inspect each material issue card.

**Check:** supported and partial/open issues are visually distinct. A supported primary answer with an unresolved mandatory screen is labelled as a supported answer with an unresolved required screen, and the card explains that the issue remains partial/open. A C27 check with an exact issue-level receipt link appears inside that issue's card; shared, legacy, or otherwise unlinked checks appear once in the generic scope list. A scope-level gap for a C27 ID shared across issues must not be attributed to an issue lacking its own open-check record. Repeated evidence/source references are not repeated. Each partial or open card names the exact missing fact, document, source or action and explains its effect. No issue-count summary is presented as overall completeness.

### C. Execution and verification

Include a triggered check that was reviewed in the conversation and a deterministic engine that was not run because the input is synthetic-only.

**Check:** execution/verification is a separate section. Model-led review is not presented as script execution. Every required or triggered operation has a status and evidence/result or a clear reason and effect for being unavailable/not run. Not-triggered items have a reasoned not-applicable label.

### D. Sources and modules

Use one relevant source record from the plugin library and one official source found through web search; when practical, use a search result that also matches a bundled record. Include a module used in the current reply, one used earlier, and a relevant module not used.

**Check:** counts distinguish all source records, bundled-library matches, and web-search discoveries. Counts can overlap, identified-but-not-read items are not called consulted, and unknown discovery is not counted as zero. Module use is grouped as used now, used earlier, or relevant but not used, with a reason for a consequential omission.

### E. Material follow-up

In the same chat, change a material fact such as the intended residence state, proceeding, or procedural stage.

**Check:** the board refreshes its title/scope, issue counts, C27 checks, source totals, and module rows where affected. It does not reuse a stale summary.

### F. No case assessment and ordinary mention

Select freemovement-law and ask for a plugin summary without asking for a case review; separately mention “freemovement-law” without selecting the plugin.

**Check:** the selected non-consultation case receives a minimal board without invented issue/source/module counts. A mere mention does not trigger an applicant-consultation board.

### G. First-response notices

Start a fresh chat with a clearly personal-use question, then another prompt that explicitly indicates professional use for a third party.

**Check:** the disclaimer appears at the beginning of the first response in both chats. The licensing note appears only for clear non-personal use. The dashboard layout change does not displace or remove either notice.

### H. Local Codex output path

From a local shell using each selected bundle, use a synthetic receipt with at least one supported issue, one partial issue with a missing/effect summary, and a C27 check sharing its scope. Run that bundle's route gate in JSON mode and `--dashboard-only` mode.

**Check:** both modes validate the same receipt; `--dashboard-only` stdout matches the JSON mode's `dashboard_preview` exactly for each build. The receipt contains opaque refs, a schema-enumerated procedure type, and generic text only. Confirm the CLI is manual local-shell execution and that the board does not include country names or applicant-specific proceeding facts from the conversation.

### I. Administrative outcomes and post-issuance routing

Use ordinary fictional chat prompts through the installed candidate in separate fresh chats; do not prepare or copy prompts from evaluation JSON, and do not enter these facts into synthetic-only scripts.

1. Describe an ordinary short-stay application with a fictional written inadmissibility notice under Article 19. Ask what was decided and what should be checked next.
2. In a separate fictional scenario, describe an ordinary short-stay application with a written substantive refusal under Article 32.
3. Describe an attempted application where an appointment or lodgement was blocked, with no formal written decision.
4. Describe an issued visa later recorded as revoked, then compare with a separate expired-visa scenario.
5. Describe an official procedural outcome that does not fit the named Article 18, Article 19, Article 32, issuance, withdrawal, or transfer categories. Include a short non-identifying explanation and a reference to the official record.
6. Describe an attempted application where no formal outcome can be established because the written decision has not been seen; separately use a scenario with conflicting records.

**Check:** each issue card names the proceeding type and records whether the outcome/event can be used for routing. Article 19 selects its own route and leaves the Article 32 route unactivated; the Article 32 route appears only with a matching official outcome record in the correct proceeding. A blocked lodgement without a formal decision stays on the access/lodgement route and says the formal outcome is missing. A revocation shows a separate event and requires national remedy/service-deadline checks to be researched; expiry does not inherit those cancellation/revocation checks. Missing, disputed or unverified records are named as outstanding work. This manual display check remains deferred and is not a maintenance-session prerequisite.

For case 5, the consultation board should show **Other**, state that its C27 explanation and evidence reference need review, and avoid promoting it into an Article 19 or Article 32 route. For case 6, it should show **Undetermined**, state what evidence is missing or conflicting, and keep the specific outcome routes unresolved. In both cases, any issue recorded as supported while its outcome route remains open must appear in the partial/open metric, and overall coverage must remain partial. A missing or disputed classification must not be presented as a formal decision.

### J. First-use GitHub reminder for module-note changes

Use an installed `freemovement-law` snapshot whose plugin and skill versions, core-pack version, and source-library tree match the published manifest, but whose recorded `module_notes_tree_sha` is older than the live `module-notes` tree in `eudirective/public-data`.

**Check:** on the first invocation, the assistant reports the exact installed and GitHub module-note fingerprints, reminds the user to check for an available update, explains that the bundled notes differ, and does not claim that the fingerprint alone proves a plugin release is available. The check is read-only and does not install anything; a later invocation in the same chat does not repeat it. No live mismatch test was run during this maintenance session.

## Review checklist

- Is the case title and jurisdiction/proceeding context easy to spot?
- Is overall coverage status distinct from issue counts and execution status?
- Are counts based only on recorded issue rows, and are missing counts shown as unknown rather than zero?
- Does the segmented bar represent issue dispositions only, with an exact legend and no completeness claim?
- Are issue cards readable without technical IDs dominating the line?
- Does every partial/open item name what is missing and how that limits the answer?
- Are model-led review, source review, and actual script/tool runs distinct?
- Are all relevant source records and module-use states present, including plugin-library matches and web-search discoveries?
- Does the board remain readable on desktop and narrow/mobile widths?
- Does the three-column metric contract match the renderer and example, including conditional closures and out-of-scope counts?
- Does local Codex output match the validated renderer preview while ChatGPT automatic invocation remains unclaimed?
- Do the disclaimer and conditional licensing notice remain correctly placed?

Record pass, fail, or not observable for each item. Any successful observation is a sample of model behavior, not host enforcement or independent legal validation.
