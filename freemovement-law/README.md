# freemovement-law

This package provides the eudirective skills and an externally maintained EU
and national legal-source library, mirrored into the plugin package.

## Requirements

- Codex or ChatGPT Desktop with plugin and skill support.
- Network access when checking a source directly with its official publisher.

The source library is maintained in `eudirective/public-data` and mirrored into
`skills/eudirective-source-library/` by the repository's scheduled workflow.
Installed copies contain the corpus version present when they were packaged;
they do not synchronize source changes after installation. For a legal claim
that depends on currentness, check the responsible official publisher directly
and report the publication/version date checked.

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

## Personal installation

Copy this plugin folder to `~/.codex/plugins/freemovement-law` and add an entry
like this to `~/.agents/plugins/marketplace.json`:

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

The current source corpus, manifests, module notes, and source-maintenance material are
under `skills/eudirective-source-library/`. The historical C1 compatibility test fixture
is under `skills/eudirective-core/tests/fixtures/core-source-pack-0.6.1/`. The core
skill resolves the fixture there; core, Sweden, and Türkiye resolve current source and
module notes from the bundled source-library directory. The corpus is maintained upstream; source changes arrive through the
repository mirror and a refreshed plugin package.
