# C21 — Purpose-bound privacy, minimisation and anonymisation preview (2026-10-10)

**Scope note:** This document governs only the synthetic **C21 executable privacy rehearsal**. It does not prohibit user-initiated, read-only discussion of a real immigration case under `references/c23-applicant-case-guidance.md`. The C23 chat mode is **not** locally anonymised by C21 and makes no host-confidentiality guarantees. Do not route real raw documents through the C21 preview engine.

**Status:** a deterministic, Python-only, offline *fictional-data preview* and safety rehearsal. **Not** an anonymity certification, real-applicant intake route, external transmission system, verified GDPR program or host security boundary. C21 deliberately does not activate the C4 private-data mode, C6/C7 private cases or C17 correspondence sending.

## What this implements

The C21 engine (`scripts/c21_privacy.py`) has two distinct deterministic controls:

1. **Minimisation:** a SHA-256-pinned, purpose-specific *positive field allowlist* determines what appears. Field classifications alone do not authorize retention; unknown fields disappear by default. Supported transforms are enumerated categories, full ISO dates reduced to year, and bounded free-text scrubbing. Publication previews omit exact dates, authorities, names, countries, procedural references and dossier/case IDs when those appear as separate structured fields; extra information embedded in narrative may still be missed.
2. **Anonymisation rehearsal:** explicit role-labeled strings, dropped direct/quasi/sensitive field values, and a fixed set of patterns are replaced with generic, nonpersistent labels. The engine does **not** issue stable person aliases, output original-input hashes or retain mapping tables in exported views. Exact contact patterns, commonly formatted dates, IBANs, IPv4s, labelled references, long quotations and declared names/places are handled; nonstandard formats and indirect/searchable facts require human assessment.

The `C17` adapter accepts only SHA-256-enrolled fictional plan JSON structures and **does not** reproduce C17 text, individual remedy names, source IDs, draft letters, recipient fields, case IDs, or source-input hashes. It emits only a coarse fictional review marker and whether at least one candidate route exists, marked *not externally releasable*. It validates that C17 is still review-only, without independently authenticating the underlying case.

## Offline usage (from core skill root)

```bash
python scripts/c21_privacy.py preview \
  --input references/fixtures/c21/fictional-private-looking.json \
  --profile public_story_preview \
  --output-dir /tmp/c21-public-preview
python scripts/c21_privacy.py verify \
  --input references/fixtures/c21/fictional-private-looking.json \
  --profile public_story_preview \
  --output-dir /tmp/c21-public-preview
python scripts/c21_privacy.py c17-preview \
  --plan references/fixtures/c21/fictional-c17-plan-L1.json \
  --output-dir /tmp/c21-c17-preview
python scripts/c21_privacy.py verify \
  --plan references/fixtures/c21/fictional-c17-plan-L1.json \
  --profile c17_feedback_preview \
  --output-dir /tmp/c21-c17-preview
python scripts/test_c21_privacy.py
```

Choose a **new** output directory per preview. The CLI fails rather than overwriting prior results. Result files are written with restrictive local Unix mode bits and contain no case reference or raw input digest; this does not guarantee file isolation across platforms or host-level erasure. `verify` replays the *original synthetic input* and checks the exact view and receipt against the pinned current policy. No network code or sending operation exists in this engine.

## Fields and purposes

The SHA-pinned policy lives in `references/privacy/c21-synthetic-purpose-policy.json`; a change requires editing both policy and script hash pin in a reviewed skill release. The separately SHA-pinned synthetic-fixture registry is `references/privacy/c21-enrolled-fixtures.json`; its pin must likewise be renewed deliberately whenever the enrolled developer fiction changes. This is release integrity, not protection against somebody who can modify the installed code.

- `internal_review_preview`: broad issue type, procedure stage, event year and scrubbed fictional narrative.
- `public_story_preview`: broad issue type plus scrubbed fictional narrative **for editorial evaluation**, not publication.
- `feedback_aggregate_preview`: broad, closed-vocabulary issue/outcome attributes only. A single preview is **not** an aggregate statistic and must never be transmitted as a case record.
- `c17_feedback_preview`: two exceptionally coarse category fields derived from an enrolled fictional C17 review plan. The adapter never promotes legal merits or sending permissions.

## Threat model and non-claims

**Identification versus discovery:** concealing names does not prevent a reader from *finding* the person using unusual procedural chronology, shared marriage histories, highly distinctive facts, specific consulates, exact quotations or other public records. The engine removes several obvious search handles and records linkability warnings, but performs **no search-based adversarial re-identification test**. No `eligible_for_publication` or `anonymised=true` conclusion is generated.

**Enrolled input, not mere declarations.** The public CLI accepts only the developer-created C21 fictional fixture and the exact enrolled C17 L1–L8 fictional review plans. Canonical JSON digests are enumerated in `references/privacy/c21-enrolled-fixtures.json`, whose bytes are pinned in `scripts/c21_privacy.py`. A new input or an edited C17 plan fails closed, even when it claims `data_class=synthetic`; enrolling another fixture requires a reviewed skill-code/registry update and renewed verification. Enrollment establishes local fixture identity only, **not** whether any story is actually fictional. The host might already have observed the text before local Python runs. In particular, do not upload private applicant records to this development skill on the theory that Python will protect them afterward.

**A hash is not a truth oracle.** A local administrator or the skill maintainer could alter a fixture and its pinned registry/code together; source hashes and code tests are integrity evidence, not host security, user consent, or proof that a named individual cannot be identified.

**Cannot replace legal/compliance judgment.** No DPIA, lawful-basis determination, data-subject rights process, international transfer analysis, data controller identification, storage/retention regime, deletion of host copies, processor agreements, consent or contract enforcement is supplied. Existing C4 approval/tombstone controls are separate and remain host-unverified. No real-law or applicant processing mode is activated.

**Attack surface:** free-text patterns can miss names, transliteration, structured metadata embedded in prose, office identifiers, biometric information, photographs and indirect identifiers. The output can retain searchable context; all outputs require editorial and external-data re-identification review before any possible public use. Statistical feedback requires additional aggregation, cohort-size, contribution limits and differencing protection; C21 does not claim to implement those mechanisms.

## Human and release gates

Before any future private-data activation, the project needs a verified host intake boundary, protected local storage, no-raw-to-model/connector guarantee, file/log/cache/backup retention/deletion rules, authenticated permission checks, approved destination channels, lawful purposes/notices, a threat-modelled re-identification evaluation and independent test evidence. These belong to a later host-integration milestone; **passing C21 synthetic tests is insufficient**.

Core owns the universal privacy engine. Sweden and Türkiye continue to own national legal facts and institutions; C21 adds no country law and changes no C3 contract or legal finding. All earlier C6/C7/C17 restrictions remain in force.

## C21 source-linked hardening (Core v0.34.0)

A rare/high-linkability tag on a field that is dropped by a `public_story_preview` no longer permits its free-text narrative to survive unchanged: the entire narrative is withheld from that preview, since it might contain a paraphrase of the dropped fact. A rare tag on the narrative itself remains a hard deny. This is **tag propagation only**, not inference of hidden identifiers or proof of anonymity; any missing/incorrect tag is still a potential miss.

`scripts/c21_cohort.py` provides a separate, fixed-set synthetic-only rehearsal. It accepts exactly the eight bundled, pinned fictional C17 plans (L1-L8), cannot be queried by arbitrary subgroups, reports only cross-case *remedy categories* occurring in at least three plans, and never emits individual plans or candidate counts. Other categories are suppressed without reporting their sizes. No external disclosure is authorized. These route categories must not be represented as measured unlawful conduct, compliance issues, complaint outcomes, independent re-identification resistance, or real-world statistics. Source-plan SHA pinning remains local developer identity/integrity evidence, not cryptographic evidence of an independent authority.

The new fixtures make all eight C17 source-plan replays executable from a fresh extracted skill ZIP. Production data isolation, host authentication, deletion/retention, separate protected audit lineage and genuinely independent legal/privacy grading remain out of scope.
