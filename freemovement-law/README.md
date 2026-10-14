# freemovement-law

This package provides the eudirective skills and a local MCP bridge to the
registered EU and national legal-source packs.

## Requirements

- Codex or ChatGPT Desktop with local plugin marketplace support.
- Node.js 20 or later with npm on `PATH`.
- Network access to npm for first-use dependency setup and to the registered
  official publishers for retrieval and updates.

The retrieval bridge uses only the source registries bundled in this package.
It does not require the developer's project folder or a user-specific path.

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
On the first source action, the bridge initializes the bundled scripts and
registries, then installs the exact locked Node dependencies if they are
missing.

## Where retrieved files go

Each installation has a persistent `data/` directory inside its plugin
installation folder. In the desktop version cache, `data/` sits beside the
versioned plugin folder so updates keep the same source packs and change
history. The EU and national packs, converted Markdown, raw snapshots, and
update state are stored there. No source files are downloaded into the user's
project folder.

The plugin uses local stdio tools, so source retrieval is available only in a
compatible desktop host that can run local Node processes. A workspace-hosted
plugin installation on web or mobile cannot access a user's local filesystem.

## Maintainer rebuild

From the project checkout, rebuild the packaged retrieval runtime after
changing source registries or retrieval scripts:

```powershell
node .agents/plugins/freemovement-law/scripts/build-source-runtime.mjs
```
