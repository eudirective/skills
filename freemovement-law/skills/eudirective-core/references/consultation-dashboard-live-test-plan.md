# Hosted consultation dashboard test plan

**Status:** Not executed. This is a manual acceptance plan for ChatGPT after
the updated plugin is installed. Offline tests cannot verify host invocation
signals, visible plugin selection, UI rendering, or whether model instructions
are followed in a hosted chat.

## Setup

1. Install the released plugin version that contains the dashboard changes.
2. Start fresh chats for each case below. Use fictional, non-sensitive facts;
   do not upload applicant documents or real case details for this test.
3. When a case says to invoke FreeMovement, select the plugin through the
   ChatGPT interface. Do not test invocation detection by merely typing its
   name into an ordinary prompt.
4. Save the visible response and note whether the plugin was explicitly
   selected, continued implicitly, or not selected. Do not send these notes to
   the plugin as if they were host telemetry.

## Cases

### A. Explicit legal consultation

Select FreeMovement and ask:

> For a fictional example, what EU free-movement rule generally applies when an EU citizen moves to another Member State with a spouse?

**Expected:** the answer leads with the requested explanation, then includes
one compact `FreeMovement — Consultation Review` dashboard. It identifies its
source-count basis (model-reported or runtime-recorded), lists the texts and
pinpoints it actually consulted, states an unknown rather than zero when read
tracking is unavailable, and gives a plain-language coverage status.

### B. Repeated explicit invocation in one chat

In the same chat, select FreeMovement again and ask a materially different
follow-up requiring source research.

**Expected:** a new dashboard is present. “This response” is refreshed for the
new answer. The conversation total deduplicates the same logical law while
retaining all pinpoints. Earlier module use is separated from current-response
module use. The answer does not reuse only the prior dashboard.

### C. Implicit continuation

Continue in the chat with a short clarification question without selecting the
plugin again.

**Expected:** a repeated dashboard is optional if the assessment and source or
module use did not materially change. If a dashboard appears, its counts and
use states must still be accurate; it must not claim a new explicit
invocation.

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

## Review checklist

- Was the plugin visibly selected for explicit cases, and was selection
  distinguished from ordinary mention?
- Did each explicit invocation receive a fresh board after the answer?
- Was the board readable in the ChatGPT client, with no broken tables or
  duplicated one-cell table rendering?
- Were response and conversation totals separately labelled and deduplicated?
- Did every source listed as consulted include its title and pinpoint, and
  agree with the cited/reviewed source in the answer?
- Were candidate/unaccepted, external, memory-cited, identified-not-read and
  currentness-unverified states represented accurately?
- Did module use distinguish this response from earlier chat use, and did it
  state a reason when a relevant module was not used or C3 conformance was not
  checked?
- Did partial items identify both the missing item and its effect?
- Did any response claim script execution or host enforcement without visible
  evidence?

Record pass, fail, or not observable for each item, with the plugin version,
client and date. A successful hosted observation is still a behavioral sample,
not a non-bypassable release guarantee. A future host/controller must consume
and validate the same receipt before release to provide that guarantee.
