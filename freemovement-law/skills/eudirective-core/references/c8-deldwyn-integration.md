> **Historical-note warning (restoration on 2026-10-10):** Statements below saying that 46 representation bytes are missing describe the superseded C8/C7 distribution. The v0.27.1 core and standalone v0.6.0 pack now contain all 47 locally verified representations. See the final restoration update and `references/source-pack/source-gap-register.md` for remaining content/currentness limits.

# C8 — Deldwyn source activation and scope controls

**Skill:** `eudirective-core` v0.22.0 · **Catalogue:** C1 EU/common v0.6.0 · **Date:** 2026-10-09

## 1. Activated source

Source `eu:62024cj0477`, *Deldwyn*, C-477/24, ECLI:EU:C:2026:182, was decided on 12 March 2026. The 0.6.1 compatibility copy is maintained outside the skill under the source library's compatibility area and is used only for synthetic replay and its pinned digest check. Retrieve and verify the current representation from the registered EU source-library pack before relying on it. The old C1 0.6.x catalogues remain compatibility metadata, not the current inventory.

The judgment Markdown originated from the user's PDF, whose case identity was cross-checked with EUR-Lex in the prior conversion. No independent public-server binary comparison of the supplied PDF is claimed.

## 2. Source trust (mechanical)

The updated code-pinned trust policy accepts exactly 0.5.0 and 0.6.0 manifest metadata. For 0.6.0, it independently reads and checks the bundled Deldwyn Markdown SHA-256 during C6 intake and release replay. Freshness gates are date-aware: the 2026-10-09 source verification cannot justify a run dated earlier. Source adapter exports the new source through the frozen C3 contract, while source-support mappings refer only to existing model targets.

**A full standalone 0.6.0 sibling source pack is not distributed by this skill.** The original 46 representation files from 0.5.0 were identified in a Library archive but the runtime could not materialize their bytes. They have **not** been re-created. If an original verified 0.5.0 directory becomes available, use the previously published delta's `apply_delta.py` to assemble 0.6.0 and run `python scripts/verify_complete_source_pack.py <dir>`; this will reject any missing or mismatching representation file.

## 3. Legal scope: human-review predicates, not executable automatic determinations

- **Worker retention** — Paragraphs 24–42 and operative ruling 1: Directive 2004/38 Article 7(3)(b) requires a **single continuous period of more than one year** for the specified retention provision; scattered shorter periods cannot simply be aggregated to meet it. The alternative Article 7(3)(c) may be relevant in appropriate circumstances.
- **Unemployment evidence** — Paragraphs 43–52 and ruling 2: unemployment-allowance receipt alone is **not** adequate proof of duly recorded involuntary unemployment. The statutory conditions and actual checks behind the grant can affect whether it is evidence; do not conflate evidence and a binding employment-status decision.
- **Good administration** — Paragraphs 54–59: Directive 2004/38 does **not** supply a general documentary-cooperation duty. Charter Article 41 addresses Union institutions rather than imposing a directly invoked Article 41 right against national authorities. EU-law general principles, rights of defence and Article 47 may nevertheless govern national implementation of EU law.
- **Decisive inaccessible evidence** — Paragraphs 60–70 and operative ruling 3: in the specified residence-card case, pre-decision communication of decisive file material (redacted or disclosed in substance if necessary) can be required when the applicant lacks access to former-spouse information on which refusal relies and the former spouse does not cooperate. Balance confidentiality and effective defence. Do **not** automatically generalise this holding to every family visa, every third-party file or every request.

The *Deldwyn* source/support map is a retrieval aid, **not** a proposition-entailment database. C5a–C5d legal candidates remain `not_determined`; no new automatic violation, recommendation or substantive legal-mechanism rule has been added.

## 4. Verification and outstanding gates

Run `python scripts/test_source_v06_activation.py`; its tests confirm fixed metadata, mandatory new Markdown bytes, conservative as-of handling, additive C2/C3 indexing, and synthetic C6 prepare–release–verify. Run the prior C1–C7 suites separately and check the actual distributable archive after extraction. For substantive adequacy, assess `evaluations/c8-deldwyn-review-cases.json` with primary-source manual grading.

**Open:** full 0.5.0 sibling source archive byte materialization, official-server recheck, independent legal-merits grading, installed-host privacy and real country modules.


## 2026-10-10 source-pack restoration (v0.27.1)

The historical C8/C7 text above describes the **earlier** metadata-only v0.22.0–v0.27.0 state. The original 0.5.0 archive was subsequently recovered via the authorized Project Library copy and SHA-256-verified against every 0.5.0 representation. The verified Deldwyn delta was then applied. The v0.27.1 core now includes all 47 declared representation bytes, and C7 requires each bundled file to match its pinned size and SHA-256. This updates the physical distribution assurance only; source freshness and legal correctness remain unreviewed. The standalone sibling pack 0.6.0 is also complete.
