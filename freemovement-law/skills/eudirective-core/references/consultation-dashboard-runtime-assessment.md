# Consultation dashboard runtime assessment

**Checked:** 2026-10-21

**Scope:** `freemovement-law` package in this repository. This is an integration
assessment, not evidence that a candidate has been installed into a ChatGPT
client.

## Capability matrix

| Runtime surface | Executable integration | Visual dashboard | Status in this package | Release enforcement |
| --- | --- | --- | --- | --- |
| ChatGPT Desktop, local plugin installation | OpenAI documents root `mcp.json` with a local stdio server. The package config points to the bundled Python renderer. | OpenAI documents MCP App UI resources returned by tools. This package advertises its `ui://` resource and returns structured data plus Markdown. | Implemented and protocol-tested with synthetic receipts. Clean installation, plugin discovery, model invocation, and visible rendering in ChatGPT Desktop have not been tested. | No ChatGPT release hook is configured or established. The model can omit the tool. |
| ChatGPT web or other hosted-only session | A local stdio process is a desktop-only execution path, not an endpoint this hosted surface can start. A hosted adapter would require an HTTPS MCP endpoint. | The local MCP App cannot render here. Skill instructions request a plain-text fallback, but if the local tool is unavailable that fallback is model-produced and not validated by the deterministic renderer. | No remote server or new data-transfer boundary was added. Hosted execution remains blocked pending an approved design. | Unavailable. |
| Codex Desktop/local plugin | Portable plugin packages can include MCP servers. | The same MCP App resource is offered by the server. | The local package is configured, but invocation and rendering in the installed Codex plugin have not been tested. | No release hook is configured. |

OpenAI’s current plugin documentation says local stdio MCP packages are
desktop-only and run in local threads. It also specifies `text/html;profile=mcp-app`
as the MCP Apps resource MIME type. These sources establish that the selected
protocol shape is supported; they do not establish that this package has been
installed, discovered, invoked, or visually rendered in a target client.

## Package entrypoints and flow

1. Root `mcp.json` starts `skills/eudirective-core/scripts/consultation_dashboard_mcp.py`.
2. The server accepts a privacy-minimised route receipt and only explicitly
   referenced generalized research JSON. It materializes them under a fresh
   temporary directory, reuses the existing route/research validators, and
   returns a validated, versioned view model with a Markdown fallback.
3. The MCP tool metadata references the bundled `ui://` HTML resource. The UI
   reads structured tool output and displays status cards, accessible progress
   indicators, open items, caveats, and validation provenance.
4. The existing local `consultation_release_gate.py` can bind an answer to a
   receipt and validation record when a separate controller invokes it. The
   plugin MCP server does not invoke that gate and cannot block an ordinary
   ChatGPT response.
5. `.agents/plugins/marketplace.json` points to the local `freemovement-law`
   folder for installation from this repository. The GitHub workflow verifies
   the source package; it does not install or publish a plugin into a ChatGPT
   account. The current maintenance session did not expose the candidate tool.

The dashboard path does not run the synthetic-only C27 engine on applicant
narratives. C27 rows remain declarations checked against the existing
registry; their displayed status is not proof that the engine executed. The
MCP process makes no network calls and logs no request content. The input
schema and instructions reduce what should be passed, but the server does not
perform personal-data detection on free-text receipt fields or research JSON.
Keep personal facts out of those fields and use only generalized, non-identifying
research artifacts.

## Evidence status

| Claim | Evidence | Finding |
| --- | --- | --- |
| The package declares a supported local plugin entrypoint | Root `mcp.json`, plugin manifests, OpenAI package and desktop-only plugin docs | Supported package shape; target-client discovery remains unverified |
| The repository installs or publishes the candidate to ChatGPT | `.agents/plugins/marketplace.json` and `.github/workflows/verify-freemovement-versions.yml` | Marketplace entry is local-source configuration; CI does not publish or install the plugin |
| The server protocol path works | `test_consultation_dashboard_mcp.py` synthetic stdio round-trip and resource/tool tests | Passed locally; not an installed-host test |
| The candidate tool is installed in this maintenance session | Current tool registry lookup for `render_consultation_dashboard` | Not exposed; this session cannot provide installed-candidate invocation evidence |
| View model and renderer are deterministic and validated | Versioned JSON schema, shared route gate, deterministic-output and malformed-input tests | Passed locally |
| The UI structure includes accessibility and fallback behavior | Static accessibility assertions and source inspection | Passed statically; no target-client visual observation |
| A missing tool or invalid receipt is reported honestly | Skill instructions, Markdown fallback plan, error tests | Implemented and locally tested |
| The host will always invoke or display the dashboard | No host-side evidence | Not established |
| The host will prevent release without a valid dashboard | No host-side evidence | Not established |
| The GitHub verification workflow covers the adapter | `.github/workflows/verify-freemovement-versions.yml` | Updated to run the MCP adapter tests; remote CI has not run for these commits |

## Required live verification

Do not run a live consultation during routine maintenance. Use the separate
[dashboard UI live-test plan](consultation-dashboard-live-test-plan.md) in a
fresh, locally installed desktop-plugin session with fictional, non-sensitive
facts. Record plugin version, client, and date. Until those observations exist,
describe this as a locally implemented and protocol-tested candidate, not a
verified installed-host feature.

## Open platform constraint

OpenAI documents local MCP submissions as desktop-only and states that public
local-MCP submissions require an approved partner organization. The documented
lifecycle hooks apply to manually installed Codex Desktop plugins; they do not
establish a ChatGPT answer-release hook. This package can be tested as a local
plugin where the client permits it, but neither hosted UI behavior nor public
local-MCP distribution eligibility follows from repository files alone. If
hosted visual rendering is required, the remaining option is to separately
authorize and design a remote HTTPS service with its data-transfer, privacy,
and hosting implications. If that boundary is not approved, hosted use remains
plain-text and unvalidated when the local tool is unavailable.

## Official platform references

- [Plugin package structure and bundled MCP servers](https://developers.openai.com/plugins/build/plugins)
- [Desktop-only plugins and local stdio MCP](https://developers.openai.com/plugins/deploy/desktop-only)
- [MCP App UI resources](https://developers.openai.com/plugins/build/chatgpt-ui)
- [Connect and test a complete plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt)
