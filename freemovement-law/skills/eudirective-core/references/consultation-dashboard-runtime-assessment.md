# Consultation dashboard runtime assessment

## Decision

The requested in-chat display is a visually organized consultation board in the assistant's ordinary Markdown response. It does not require an MCP tool, hosted service, or custom UI. A plugin skill can specify this layout and ask ChatGPT to assemble it from the current conversation and recorded checks.

## Layout supported by this package

The core instructions and example prescribe a clear case title and jurisdiction/proceeding subtitle, an overall status callout, a compact three-metric row, an issue-disposition bar with exact counts, readable issue cards, a separate execution/verification section, then sources, module use, and provenance limits. A short three-column Markdown table is the only permitted table; it can fall back to stacked metric lines on narrow clients. Every partial or open issue names the missing information and its effect.

Native Markdown can provide headings, emphasis, blockquotes, lists, compact tables, and status icons. It cannot guarantee custom colors, CSS-styled cards, a separate graphical widget, or interactive progress controls. The layout should still be scannable without color or icons.

## Metric and evidence limits

Issue counts and status segments are derived only from material-issue rows and their recorded dispositions in the current response. The bar is a distribution of those labels, not a percentage of legal completeness and not evidence that all relevant issues were found. If tracking is incomplete or unavailable, show `unknown` or `not recorded`; do not substitute zero. The board must keep overall coverage separate from issue counts.

Operations and validators are displayed separately from legal issue conclusions. A model-led review is not a script execution. An execution is reported only when this conversation contains an observed result. Source retrieval and module use are model-reported unless the host supplies a trusted event record. An optional local renderer can produce a Markdown preview from a structured receipt, but ordinary ChatGPT responses do not run it automatically. The receipt stores only whether jurisdiction and proceeding classifications are recorded or unknown, not their values, so its preview uses a generic scope subtitle; the assistant's in-chat board can show the actual values already present in the conversation without copying them into the receipt.

## Enforcement boundary

A skill instruction cannot force ChatGPT to include the board, authenticate reported source reads, discover an omitted issue, or block answer release. The local route receipt and gate can validate declared structure and attached validator outputs. A non-bypassable release check would require host support that validates the receipt and binds the result to the answer; this package does not provide that host integration.

## Implementation status

- In-chat native Markdown board layout: specified in the core skill, routing guidance, and examples.
- Issue metrics and status bar: limited to recorded dispositions; not a legal-completeness score.
- Readable issue cards with missing-item/effect text: specified for the full board.
- Separate execution/verification ledger: specified; model-led assessments remain distinct from observed runs.
- Bundled-library matches, web-search discoveries, and module use: shown separately with overlap and unknown provenance handled explicitly.
- Custom graphical renderer, hosted service, MCP UI, and host-enforced release gate: not provided.
- Fresh-chat visual review: deferred to `consultation-dashboard-live-test-plan.md`; no live session test is required during maintenance.
