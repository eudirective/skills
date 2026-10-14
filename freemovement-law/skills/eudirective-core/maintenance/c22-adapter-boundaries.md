# C22 adapter migration rules (modifier-only)

This file is for maintaining or packaging the skill, not normal execution.

## Frozen boundaries

1. Core v0.35.0 adds only a transport-neutral interface to the already-bundled C18/C21 synthetic engines. Do not promote unknown source notes into authoritative texts or move Swedish/Turkiye law into core.
2. The executable API must accept *only* fixed operation and enrolled fixture selectors; it must not accept arbitrary paths for input, free-text applicant data, user-selected C17 subsets, command strings, URLs, credentials or outbound destinations.
3. A caller may supply an output directory through the trusted execution host; never expose it as a model-controlled request field. The current facade checks absoluteness, parent, symlinks, prior existence and whether the path is inside the skill tree; host-level path isolation remains a separate task.
4. Direct Python and CLI execution share `invoke`/`invoke_request`. A future MCP adapter must be a thin wrapper of `invoke_request` with identical error/redaction and no separate legal/privacy code. No plugin dependency enters core `SKILL.md` or scripts.
5. Never convert mechanical hashes, schema checks, replay or small-cell suppression into legal validation, provenance authentication, anonymity or GDPR guarantees.
6. Versions of schema and facade travel together. Changing operations, trust assumptions or approved input categories requires a version bump, new negative tests, post-extraction comparison and renewed privacy/legal review.

## C22a evidence scope

The tests check: all eight enrolled C17 feedback selectors; current pinned C21 demo profiles; local C18 pack integrity; cohort; rejected freeform input, subprocess failure, symlink/output path abuse; no overwrite; and CLI/direct structured response equivalence. They do NOT exercise desktop-plugin installation, MCP protocol transport, local host isolation, network constraints enforced by an OS sandbox, or processing real applicant documents.

## Next adapter stage

Create an optional MCP wrapper in an adapter-only distribution, not inside the core skill root; import the same `invoke_request` function, bind output paths by host policy, never allow the model to provide file paths, and run post-extraction cross-mode tests. Confirm currently supported plugin manifest/runtime behavior independently before claiming installation compatibility.
