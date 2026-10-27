# freemovement-law

This repository distributes the freemovement-law EU core and 31 separately
installable country source plugins. Install the core for EU-level work and add
only the national plugins relevant to your consultations.

## Requirements

- Codex or ChatGPT Desktop with plugin and skill support.
- Network access when checking a source directly with its official publisher.

## Use and licensing

This plugin is intended for personal use. Non-personal use includes explicit professional or organizational use for an employer, business, organization, client, customer, or other third party; paid services; or deploying the plugin for others. Non-personal use requires a license. Request one at eudirective@proton.me.

The canonical source records are maintained in `eudirective/public-data`.
The repository workflow builds the EU core and country packages from a pinned
upstream revision and publishes a component index. Installed packages contain
their recorded snapshot; they do not synchronize source changes after
installation. For a legal claim
that depends on currentness, check the responsible official publisher directly
and report the publication/version date checked.
For ordinary research, a human-reviewed official link is enough within its
reviewed scope. Government consolidations are preferred; if unavailable, use
the closest government-published version and state its limits. Captures,
conversions, APIs, hashes, replay, and scheduled updates are optional unless
keeping or monitoring local copies is actually needed.

## Evidence-gated legal research

For material current, multi-source, disputed or incomplete questions within an
EU free-movement or EU-family-visa issue, the core uses one research loop with
`quick`, `case` and `deep` depth profiles. Connected EU law, Swedish
law/procedure, Türkiye operations, and relevant national source packs keep
separate source owners and coverage criteria. Modes change research depth, not
evidence standards. Optional research plans and evidence bundles contain only
generalized, non-identifying source questions; they do not enter synthetic case
controllers or determine legal merits. A local gate checks artifact references
and coverage labels, not source authenticity or legal conclusions.

## Ordinary consultation routing

Before substantive applicant guidance, the core records jurisdictions and
roles, proceedings and stages, legal questions, urgency, requested output,
selected workflows, source owners, and execution/coverage status. It reuses
C3's role and jurisdiction contract, C27's atomic completeness registry, and
the existing research validator. A model-led attack-angle screen is required
for every substantive ordinary applicant consultation. A portable receipt
schema and local structural gate are included at
`skills/eudirective-core/references/consultation-route-gate.md`. They validate
only the model-declared plan, indexed references and artifacts accepted by
existing validators; they cannot identify omitted conditionals or authenticate
self-reported evidence, and they do not scan artifact names or contents for
personal data. The plugin does not invoke the gate or enforce its result before
release. Non-bypassable enforcement requires host integration that validates
the receipt and binds it to the answer being released.

## Consultation dashboard

The full dashboard is written in the assistant's ordinary Markdown response.
It starts with the case scope, overall status, a compact issue summary and
status distribution, then shows readable issue cards and a separate
execution/verification section. Sources and modules appear with their
provenance and current-versus-earlier-chat use. Source accounting separates
matches to records in the bundled plugin library from sources identified
through web search; these counts can overlap, and missing discovery provenance
is shown as unknown. This is a native Markdown layout, not a custom graphical
widget, and it does not require an MCP tool or hosted service. Source and module
use remain model-reported, and the skill cannot force the board to appear or
block an answer from release. See
`skills/eudirective-core/references/consultation-dashboard-examples.md` for the
display format and `skills/eudirective-core/references/consultation-dashboard-live-test-plan.md`
for a deferred manual review plan.

## Personal installation

Copy the EU core folder to `~/.codex/plugins/freemovement-law`. When a
national jurisdiction is relevant, also copy that country's `freemovement-law-xx`
folder and add each installed package to `~/.agents/plugins/marketplace.json`:

```json
{
  "name": "eudirective-local",
  "plugins": [
    {
      "name": "freemovement-law",
      "source": {
        "source": "local",
        "path": "./.codex/plugins/freemovement-law"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

Restart the desktop app and install the plugin from that personal marketplace.

## Bundled source library

The shared English EU corpus and operational module notes are bundled at
`skills/eudirective-core/references/source-library/`. Country source records and
permitted local texts are bundled only in their matching country packages. The
historical C1 compatibility fixture remains under
`skills/eudirective-core/tests/fixtures/core-source-pack-0.6.1/`. The runtime
version check compares the installed core manifest with the published component
index and separately reports when the public-data repository has advanced.
