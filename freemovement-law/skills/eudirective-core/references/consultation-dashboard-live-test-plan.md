# Consultation dashboard live test plan

**Status:** Not performed during maintenance. This is a deferred manual visual review in a fresh ChatGPT chat. Use fictional, non-sensitive facts only; no hosted service or MCP is part of the plan.

## Setup

1. Install or reload the plugin version containing the native-Markdown board instructions.
2. In a fresh chat, select freemovement-law through the normal interface and use fictional facts. Record the client, plugin version, date, and visible response.
3. Review the response at desktop width and a narrow/mobile width if available.

## Cases

### A. Substantive consultation with mixed issue statuses

Ask a fictional EU-family visa question involving an EU citizen moving to another Member State with a spouse. Include enough fictional details for several issues to be supported and at least one issue to remain partial because a receipt or written decision is missing.

**Check:** the substantive answer appears first. The dashboard begins with a case title, jurisdiction/proceeding subtitle, and plain-language overall status. The three compact metrics show only counts derived from the recorded issue rows. A short segmented bar has one segment per dispositioned issue (only when there are 20 or fewer); its legend gives exact counts and says that it is not a legal-completeness score. The layout remains readable on a narrow screen; if the metric table is cramped, stacked metric lines are acceptable.

### B. Issue cards and missing-item effects

Use the same case and inspect each material issue card.

**Check:** supported and partial/open issues are visually distinct. Each issue includes its supporting fact/source basis and selected C27 status/method. Each partial or open card names the exact missing fact, document, source or action and explains its effect. No issue-count summary is presented as overall completeness.

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
- Do the disclaimer and conditional licensing notice remain correctly placed?

Record pass, fail, or not observable for each item. Any successful observation is a sample of model behavior, not host enforcement or independent legal validation.
