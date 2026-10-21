# Consultation dashboard UI live test plan

**Status:** Not executed. The local MCP protocol, receipt validator, and view
model have automated checks. Do not run live consultation cases during local
maintenance sessions. This plan is for a fresh Codex Desktop/local-plugin
session after installing the updated package. A hosted ChatGPT session that
cannot start local stdio tools is expected to use the Markdown fallback; do
not add a remote service without separate maintainer approval because that
would create a new data-transfer boundary.

## Setup

1. Install or reload the local plugin package containing the dashboard changes.
2. Confirm Python 3.10+ and `requirements-runtime.txt` are available to the
   local stdio process. Confirm the plugin discovers
   `render_consultation_dashboard` and its `ui://` resource.
3. Start fresh chats for each case below. Use fictional, non-sensitive facts;
   do not upload applicant documents or real case details for this test.
4. When a case says to invoke FreeMovement, select the plugin through the
   host interface. Do not test invocation detection by merely typing its
   name into an ordinary prompt.
5. Save the visible response and note whether the plugin was explicitly
   selected, continued implicitly, or not selected. Do not send these notes to
   the plugin as if they were host telemetry.

## Cases

### A. Explicit legal consultation

Select FreeMovement and ask:

> For a fictional example, what EU free-movement rule generally applies when an EU citizen moves to another Member State with a spouse?

**Expected:** the answer leads with the requested explanation, then the model
calls `render_consultation_dashboard` with a privacy-minimised receipt. The host
shows one full `FreeMovement — Consultation Review` UI. It lists every
classification, operation, selected C27 check, issue, validator result, source
ledger row, and relevant module. Source counts are labelled model-reported;
this plugin has no host-authenticated source-read event. It states unknown
rather than zero when read tracking is unavailable and gives each open item
its missing detail and effect. It does not claim independently recorded
retrieval.

### B. Repeated explicit invocation in one chat

In the same chat, select FreeMovement again and ask a materially different
follow-up requiring source research.

**Expected:** the tool is called again and a new full dashboard is present.
“This response” is refreshed for
the new answer. The conversation total deduplicates the same logical law while
retaining all pinpoints. Earlier module use is separated from current-response
module use. The answer does not reuse only the prior dashboard.

### C. Implicit continuation

Continue in the chat with a short clarification question without selecting the
plugin again.

**Expected:** a dashboard is required if jurisdiction roles, proceeding/stage,
legal question, urgency, requested output, issue/check selection, sources,
module use, or execution materially changed. If it appears, its counts and use
states must still be accurate; it must not claim a new explicit invocation.

### D. Ordinary mention without invocation

In a fresh chat, do not select FreeMovement. Ask a general question that merely
mentions it, for example:

> I saw a tool called FreeMovement. What kinds of questions is it intended to answer?

**Expected:** no mandatory consultation dashboard is triggered solely by the
mention. Record whether the host activated a plugin for some other reason.

### E. Explicit dashboard request

Without a new explicit plugin selection, ask in an ongoing FreeMovement chat:

> Please show the consultation dashboard and list any remaining coverage gaps.

**Expected:** a dashboard appears with each partial item naming what is
missing and what it prevents assessing.

### F. Explicit non-consultation invocation

In a fresh chat, select FreeMovement and ask:

> Summarize what this plugin is for; do not assess a case.

**Expected:** the minimal dashboard says `Not verified · No case assessment was
performed.` It does not invent source counts, issues, or module checks.

### G. Tool unavailable or receipt rejected

Run in a host that does not expose the local stdio tool, or use a deliberately
invalid synthetic receipt in a development-only harness.

**Expected:** the host uses the Markdown fallback and says validation was
`not run/unavailable` when the tool could not be called. A rejected receipt
must not be described as validated; the error must not echo receipt contents.

## Review checklist

- Was the plugin visibly selected for explicit cases, and was selection
  distinguished from ordinary mention?
- Was `render_consultation_dashboard` called with only the privacy-minimised
  receipt, and did the MCP App render from its structured tool result?
- Did the component show readable status labels in addition to color, adapt to
  light/dark and forced-color modes, and expose progress-bar labels to screen
  readers?
- Did progress show exact recorded counts without an invented percentage or a
  claim that declared rows represent all applicable work?
- Did malformed input produce a safe error without echoing receipt text or
  making network requests?
- Did each explicit invocation receive a fresh board after the answer?
- Was the board readable in the target client, with no broken tables or
  duplicated one-cell table rendering?
- Were response and conversation totals separately labelled and deduplicated?
- Did every source listed in the ledger include its title and pinpoint, and
  agree with the cited/reviewed source in the answer?
- Were candidate/unaccepted, external, memory-cited, identified-not-read and
  currentness-unverified states represented accurately?
- Did module use distinguish this response from earlier chat use, and did it
  state a reason when a relevant module was not used or C3 conformance was not
  checked?
- Did partial items identify both the missing item and its effect?
- Did the board show every declared source, check, issue, operation, validator
  result, and relevant module without compact limits?
- Did it include the validation result and receipt fingerprint, or explicitly
  say validation was not run/unavailable?
- Did any response claim script execution or host enforcement without visible
  evidence?

Record pass, fail, or not observable for each item, with the plugin version,
client and date. A successful observation is still a behavioral sample, not a
non-bypassable release guarantee. A future host/controller must require the
tool call, validate the same receipt, and bind it to the exact answer before
release to provide that guarantee.
