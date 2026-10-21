# Consultation dashboard live test plan

**Status:** Not performed during maintenance. The board uses ordinary Markdown in a ChatGPT response. This plan is for a later manual visual review in a fresh chat; it does not require a hosted service, MCP tool, or real applicant data.

## Setup

1. Install or reload the plugin version containing the Markdown instructions.
2. Start fresh chats and use fictional, non-sensitive facts. Do not upload applicant records.
3. Select FreeMovement through the normal ChatGPT interface for the explicit-invocation cases. Record the client, plugin version, date, and visible response.

## Cases

### A. Substantive consultation

Ask a fictional EU-family visa question involving an EU citizen moving to another Member State with a spouse.

**Check:** the answer comes first, followed by a readable board. The board uses headings and separated status cards rather than a wide table or code block. It distinguishes model review from actual script/tool execution and states missing items and their effects.

### B. Material follow-up

In the same chat, change a material fact such as the intended residence state or the procedural stage.

**Check:** the board refreshes to show the changed scope, newly relevant modules/checks, and any module use earlier in the chat. It does not reuse a stale board.

### C. Partial or unavailable operation

Use a fictional case where an important receipt, decision notice, or national procedure is missing.

**Check:** each partial or unavailable row names what is missing and how that limits the assessment. A validator or engine is not called “run” merely because its instructions or registry were read.

### D. Non-consultation request

Select FreeMovement and ask for a summary of the plugin, explicitly saying not to assess a case.

**Check:** the response uses the minimal board and does not invent sources, issues, module use, or execution.

### E. Ordinary mention without selection

In a fresh chat, ask what a tool named FreeMovement is for without selecting it.

**Check:** a mere mention does not trigger an applicant-consultation dashboard.

### F. Plugin library and web-search source counts

Use a fictional consultation with one relevant source in the plugin library and one official source found through web search. If practical, include a web-search result that also matches a bundled source record.

**Check:** the board separately shows the number of identified source records, matches to records in the plugin's bundled library, and web-search discoveries for this answer and the conversation. It marks the counts as model-reported, says discovery and library membership can overlap, and does not treat an external URL as proof of web search. An unrecorded discovery method appears as unknown rather than zero. Identified-but-not-read sources count as identified but not as consulted.

## Review checklist

- Are the headings and status cards easy to scan in the target ChatGPT client?
- Are status words readable without relying on color or emoji?
- Are modules clearly grouped as used now, used earlier, or not used?
- Does each partial, unavailable, or not-run item name the missing input and its effect?
- Are model-led review, actual source consultation, and script execution accurately distinguished?
- Are bundled-library matches separated from web-search discoveries, with overlap and unknown provenance handled accurately?
- Is the substantive answer still easy to find before the board?

Record pass, fail, or not observable for each item. A successful observation is a sample of model behavior; it does not make the skill instruction non-bypassable.
