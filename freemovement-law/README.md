# freemovement-law

This package provides the eudirective skills and the externally maintained,
versioned EU and national legal-source bundle.

## Requirements

- Codex or ChatGPT Desktop with plugin and skill support.
- Network access when checking a source directly with its official publisher.

The source corpus is bundled with each plugin release. Its maintainers update the
upstream source pack and publish refreshed plugin bundles. The plugin does not
launch a per-install MCP server or synchronize sources separately for each
install. Treat the bundled corpus as a release snapshot; check the named official
publisher for live currentness when a legal answer depends on it.

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

## Bundled source corpus

The versioned corpus is under `source-runtime/eudirective-source-library-0.6.0/`.
Source-pack maintenance and refresh happen upstream and arrive with a new package
release. To verify a legal proposition for current use, consult the official
publisher and report the publication/version date checked.

## Maintainer rebuild

From the project checkout, rebuild the bundled source corpus after updating the
upstream source library or retrieval scripts:

```powershell
node .agents/plugins/freemovement-law/scripts/build-source-runtime.mjs
```
