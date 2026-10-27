# Consultation dashboard runtime assessment

## Decision

The full in-chat consultation board is an explicit audit and maintenance presentation. Ordinary applicant answers use concise prose and a short coverage note; material source or module changes may be reported briefly. The board remains native Markdown and does not require an MCP tool, hosted service, or custom UI. A skill can request that ChatGPT assemble it from the current conversation and recorded checks, but cannot force presentation or verify that every check ran. A local Codex shell can run the existing receipt gate and renderer when the exact plugin bundle and Python are available; this is a manual local path, not automatic ChatGPT integration.

## Layout supported by this package

The following layout applies only to an explicitly requested audit, maintenance review, dashboard, or detailed verification report. It is not required after each skill invocation or routine change in consultation variables.

The canonical board uses a clear case title and jurisdiction/proceeding subtitle, an overall status callout, three metrics (**Issues reviewed**, **Supported / conditionally closed**, **Partial / open**), an issue-disposition bar with exact counts and percentages when all dispositions are recorded and there are at most 20 issues, readable issue cards, a separate execution/verification section, then sources, module use, and provenance limits. Direct-supported and conditionally-closed counts are split in the distribution legend even though the top metric combines them. Above 20 issues the renderer gives exact counts and percentages without the bar; if dispositions are incomplete it gives unknown counts and explains why the bar is unavailable. A short three-column Markdown table is the only permitted table; it can fall back to stacked metric lines on narrow clients. Every partial or open issue names the missing information and its effect.

Native Markdown can provide headings, emphasis, blockquotes, lists, compact tables, and status icons. It cannot guarantee custom colors, CSS-styled cards, a separate graphical widget, or interactive progress controls. The layout should still be scannable without color or icons.

## Metric and evidence limits

Issue counts and status segments are derived only from material-issue rows and their recorded dispositions in the current response. The bar is a distribution of those labels, not a percentage of legal completeness and not evidence that all relevant issues were found. If tracking is incomplete or unavailable, show `unknown` or `not recorded`; do not substitute zero. The board must keep overall coverage separate from issue counts.

Operations and validators are displayed separately from legal issue conclusions. A model-led review is not a script execution. An execution is reported only when this conversation contains an observed result. Source retrieval and module use are model-reported unless the host supplies a trusted event record. `consultation_route_gate.py --dashboard-only` validates the existing receipt and writes the generated Markdown board without a JSON wrapper, allowing local Codex to include its output unchanged after the substantive answer. This local command must use a privacy-minimized receipt; do not put names, exact country/proceeding values, case numbers, exact dates or places, narratives, correspondence, or document contents in it. Ordinary ChatGPT does not invoke this local command automatically. The receipt stores only whether jurisdiction and proceeding classifications are recorded or unknown, not their values, so its preview uses a generic scope subtitle; the assistant's in-chat board can show the actual values already present in the conversation without copying them into the receipt.

## Enforcement boundary

A skill instruction cannot force ChatGPT to include the board, authenticate reported source reads, discover an omitted issue, or block answer release. The local route receipt and gate can validate declared structure and attached validator outputs, but cannot verify the truth of model-reported facts or legal conclusions. A non-bypassable release check would require host support that validates the receipt and binds the result to the answer; this package does not provide that host integration. Ordinary ChatGPT invocation, unchanged renderer-output pass-through, and consistency across thinking levels remain unverified.

## Implementation status

- In-chat native Markdown board layout: specified in the core skill, routing guidance, and examples.
- Issue metrics and status bar: one three-column contract, four recorded disposition groups, and explicit unknown/out-of-scope handling; not a legal-completeness score.
- Readable issue cards with missing-item/effect text: specified for the full board.
- Local Codex rendering: existing route gate exposes the rendered Markdown directly through `--dashboard-only`; it reuses the current receipt schema and renderer.
- Separate execution/verification ledger: specified; model-led assessments remain distinct from observed runs.
- Bundled-library matches, web-search discoveries, and module use: shown separately with overlap and unknown provenance handled explicitly.
- Custom graphical renderer, hosted service, MCP UI, and host-enforced release gate: not provided.
- Fresh-chat visual review: not performed. The historical test design is preserved at `consultation-dashboard-live-test-plan.md`, but is not a user task or maintenance prerequisite. Reopen only when a verified agent-controlled runtime is available or the requested scope changes.
