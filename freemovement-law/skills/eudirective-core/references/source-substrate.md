# Current note — C18 supersedes historical source claims

As of 2026-10-10, the active C1 manifest is **v0.6.1**, not v0.6.0. The Directive 2004/38 Article 2(2)(a) omission is repaired in the active physical source and new C7 trust pin; 21 identity-only notes remain. The following chronology records prior releases and may contain obsolete earlier-state language. See `c18-source-integrity.md` and the C18 source gap register for current scope.

> **Historical-note warning (restoration on 2026-10-10):** Statements below saying that 46 representation bytes are missing describe the superseded C8/C7 distribution. The v0.27.1 core and standalone v0.6.0 pack now contain all 47 locally verified representations. See the final restoration update and `references/source-pack/source-gap-register.md` for remaining content/currentness limits.

# Source substrate and ownership staging

## Current C1 state

`eudirective-core` v0.18.0 is exact-tested against sibling source pack 0.5.0. C5a/C5b/C5c/C5d candidate/review outputs; C5e handoff binds the exact C5d/C5c state also bind the exact source-pack manifest digest; this does not turn source-hint presence into legal entailment. The registry contains 45 logical EU/common sources in 46 representations. C1 is **complete under the verified-representation standard**.

## Completion rule

C1 does not require byte-identical official files. A source is incorporated when it has at least one verified usable representation:

- `bundled_text` + `verified_official`; or
- `verified_source_note` + `verified_identity_version`.

For a verified source note, the official source identity and the relevant fixed/current/consolidated version must be checked. The representation hash protects the stored project copy against corruption; it does not prove byte identity with the official publication.

When no usable consolidation exists, a verified source note may use the closest government-published version. Record its displayed date or cutoff and limits; do not block ordinary source use or C1 on reconstructing the full Gazette amendment chain. Check a specific later act only when a known, material currentness or legal-effect question affects the scope. Full-text capture and conversion remain optional unless exact wording, a pinpoint, or a retained full copy is needed.

Run:

```bash
python scripts/source_text_gate.py <source-pack-dir>
```

Exit 0 means C1 source-representation complete. Exit 3 means one or more required sources still lack a verified usable representation.

## Exact-text boundary

A verified source note may support source discovery, element modelling, applicability routing, and a reviewed or candidate interpretation within its recorded proposition scope. It does **not** support a rule labelled `direct_text`, an exact quotation, paragraph number, or fine-grained holding. `direct_text` requires an explicit `text_source_ref` resolving to `authoritative_bundled_text` + `verified_official`. Note-backed interpretations must carry an explicit `support_scope`.

## Optional fuller-text acquisition

`scripts/source_text_ingest.py` remains available to add fuller official snapshots. Offline candidate staging remains non-authoritative unless a trusted digest is already pinned. Fuller text is an enhancement, not a C1 prerequisite once identity/version verification is complete.

## Adapter semantics

The core-source adapter distinguishes `authoritative_bundled_text`, `verified_source_note`, `curated_reference_note` and `unverified_candidate`. The first two are usable source representations; the latter two are not.

## Authority-first classification

EU law, CJEU interpretation and EU/common guidance belong to core. National and local material remain outside this pack. Do not inspect Member-State packs during C1/C2 core work.

## C2 gate

C1 is complete. C2 source-informed element modelling may proceed.

## C8 0.6.0 Deldwyn activation (2026-10-09)

The current core catalogue supports 46 sources/47 representations and includes full Markdown Deldwyn C-477/24. The historical 0.5.0 manifest and its trust policy remain for replay. The new source entry and Markdown are pinned by C7; other representation bytes are not supplied and no full 0.6.0 sibling pack was assembled. See `c8-deldwyn-integration.md` for scope and legal review requirements.


## 2026-10-10 source-pack restoration (v0.27.1)

The historical C8/C7 text above describes the **earlier** metadata-only v0.22.0–v0.27.0 state. The original 0.5.0 archive was subsequently recovered via the authorized Project Library copy and SHA-256-verified against every 0.5.0 representation. The verified Deldwyn delta was then applied. The v0.27.1 core now includes all 47 declared representation bytes, and C7 requires each bundled file to match its pinned size and SHA-256. This updates the physical distribution assurance only; source freshness and legal correctness remain unreviewed. The standalone sibling pack 0.6.0 is also complete.
