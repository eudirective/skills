# C22a - Portable execution contract (2026-10-10)

**Implemented for local, enrolled fictional material only. No ChatGPT plugin, MCP server, or private-case intake is part of this release.** The existing EU and country skills remain separately installable. Country-specific law stays in the country modules.

## Portable core and transport boundary

`SKILL.md`, `scripts/`, `references/` and their schemas remain the independent standalone execution base. `scripts/c22_portable_api.py` is an optional, dependency-light facade over EXISTING C18/C21 scripts. A future desktop/plugin adapter may call `invoke_request(request, output_dir=trusted_output_dir)`; it must not copy legal rules or invent new backends. Standalone installations need only Python and the dependencies already required by the bundled scripts. When no Python tool exists, do not fabricate results; report execution unavailable.

`references/contracts/c22-transport-request.schema.json` defines the adapter request payload. Its allowed properties are `interface_version`, `operation`, and optional **enrolled fictional** `fixture` and `profile` selectors. It contains no case text, personal data, source-update paths, URLs, shell commands, arbitrary input files, webhook destinations, or user-selected case subsets. A trusted host supplies `output_dir` out of band; use a private newly created workspace, never allow an LLM to choose a filesystem path.

## Current operations

| Operation | Input | Existing implementation | Assertion scope |
| --- | --- | --- | --- |
| `capabilities` | none | facade | Reports admitted operations and flags only |
| `source_audit` | none | `c18_source_integrity.py` | Local pin/byte integrity only; 21 full-text gaps persist |
| `privacy_preview` | `c21-demo`, allowed story profile | `c21_privacy.py` | Enrolled fictional input, never public disclosure |
| `privacy_verify` | matching selector, prior output dir | `c21_privacy.py` | Local replay and receipt equality, not anonymity |
| `c17_feedback_preview` | enrolled L1-L8 token | `c21_privacy.py` | Single case categorical, non-send review |
| `c17_feedback_verify` | matching token, prior output dir | `c21_privacy.py` | Local replay only |
| `cohort_preview` | none; all 8 pinned cases | `c21_cohort.py` | Suppressed synthetic category counts, non-send |
| `cohort_verify` | none; prior output dir | `c21_cohort.py` | Local fixed-cohort replay only |

These operations do **not** expose arbitrary C6 controller execution, C17 remedy drafting, network retrieval, file ingestion or country-data mutation. Those remain separate, existing workflows; any future adapter exposure requires an explicit scope change and new safety tests.

## Standalone commands

Run from an extracted `eudirective-core/` skill root:

```bash
python scripts/c22_portable_api.py capabilities
python scripts/c22_portable_api.py source_audit
python scripts/c22_portable_api.py privacy_preview --fixture c21-demo --profile public_story_preview --output-dir /absolute/new-workspace
python scripts/c22_portable_api.py privacy_verify --fixture c21-demo --profile public_story_preview --output-dir /absolute/new-workspace
```

For C17 feedback use `c17_feedback_preview --fixture L1 ...` followed by `c17_feedback_verify --fixture L1 ...`. For the fixed cohort use `cohort_preview --output-dir ...` and `cohort_verify --output-dir ...`. All responses are one JSON object on stdout, with `interface_version`, `operation`, `status`, and two false safety booleans; a blocked request returns exit code 2. CLI success never means legal or privacy validation.

A future adapter can use the same bounded call:

```python
from c22_portable_api import invoke_request
result = invoke_request({
    'interface_version': '0.1.0',
    'operation': 'privacy_preview',
    'fixture': 'c21-demo',
    'profile': 'public_story_preview',
}, output_dir=trusted_fresh_workspace)
```

There is deliberately no MCP-specific import, discovery or runtime dependency in the standalone skill.

## Adapter obligations for future C22b/C22c

- Keep the transport adapter outside the core execution path; do not silently replace `SKILL.md`, rename country modules or duplicate the policy/source files.
- Forbid tool calls containing real applicant documents or free-form case text. Preserve enrolled-fixture and non-send restrictions on **both** CLI and adapter paths.
- Do not claim local-before-model processing merely because a local executable exists. Establish verifiable host boundaries before enabling private inputs.
- Use a host-selected isolated output workspace and constrain filesystem access, working directory, logs, secrets, network, concurrent calls and lifecycle. Host sandboxing is **not** supplied by this facade.
- Treat results as human-review-only; never infer an approved legal conclusion, anonymous output, publication approval, or external delivery.
- Run the same pinned fixtures through both interfaces and compare structured output and receipts byte-for-byte. Direct callable and CLI equivalence in C22a is a precursor, **not** MCP/plugin runtime verification.
- Generate standalone and plugin archives from one versioned skill tree, with the plugin embedding the exact same core bytes plus a separately versioned adapter. Audit SHA-256 hashes after extraction.

## Known limits

The `source_audit` retains 21 identity-only legal notes. Authentication of legal texts, C15f independent legal-semantic review, privacy assurance, actual applicant intake, external feedback, deletion proof and live desktop-plugin compatibility remain unverified. The facade cannot remove the known risks of identifiers in prompts already sent to a model.
