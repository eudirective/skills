# C13 — Passage-anchored documentary statement assessment

**Core:** 0.27.0 · **Stage:** `c13` v0.2.0 · **Status:** synthetic, review-only, not applicant-facing.

## What this stage does

1. C7 preflight authenticates the *local test fixture identity* of `--c13-evidence-set` before the C6 workspace is created. A fixture digest is not a real-world document authenticity check.
2. The in-package registry pins each fictional raw-format file by SHA-256. Enrolled document refs may only resolve to their exact case fixture. File bytes cannot be replaced, symlinked, path-traversed or silently loaded from a private user directory.
3. Offline extract plaintext from UTF-8 text, MIME text/plain or HTML body, safe visible HTML text, or PyMuPDF textual PDF pages. Ignore email attachments, remote links, script/style content and PDF image-only content. PDFs without extractable text return `text_not_extractable_ocr_required`; no OCR guesses.
4. Apply separately code-pinned, bounded, English-language phrase recognisers. Record *exact quote*, `[start:end]` Unicode character offsets relative to an identified extracted page/body, segment hash, source raw-byte hash and cue ID. Do not treat matching a regex as general semantic understanding.
5. Reconcile observed documentary **statements** with the structured C12 fact values; distinguish corroborating **statements**, contrary statement values, missing textual support and internal contradiction. Mark every observation `not_authenticated`, every fact truth `not_determined`.
6. Allow C13 to **suppress** a C12 review-candidate promotion when its required documentary cues are missing or contradictory. No C13 path may upgrade an unsupported candidate or create a legal violation.
7. Replay stage and Markdown report from pinned inputs in C6 `verify` and check receipt hashes. Index all unresolved C13 issues with the C7 full issue index.

## Trust and interpretative boundaries

- A raw SHA-256 proves local byte integrity relative to the enrolled test registry, **not origin, integrity before enrollment, authorship, truth, or legal sufficiency**.
- MIME headers are untrusted metadata; `From` and `Date` alone do not establish sender identity, actual service or date of receipt.
- The extracted character offsets refer to *rendered text* from the identified page/body; they are not PDF byte coordinates or the original HTML byte offset. The immutable source hash and per-segment hash permit reproduction.
- Patterns are intentionally narrow. Example: “the application was rejected” may not match “your visa application has been refused.” Missing a match creates a review gap, not an assertion that nothing happened.
- A generated fact that has no specific byte-supported passage may not be marked as document-corroborated. A document stating “we hold the file” still does not prove the sender is the competent authority.
- Real-case ingestion, scanned PDF/OCR, multilingual interpretation, authority-level legal proof, complex service rules, independent source-freshness checks and applicant-facing release remain out of scope.
- Existing C3 export schema and country-module source ownership remain unchanged. C13's recognisers represent generic documentary phrasing, not Swedish/Turkish legal rules.

## Reproduce

```bash
python scripts/test_c13_document_evidence.py > c13-evaluation.json
python scripts/c6_integration.py prepare --case references/fixtures/c10/L1/case.json \
  --elements references/fixtures/c10/L1/elements.json \
  --actors references/fixtures/c10/L1/actors.json \
  --module-pair references/fixtures/c10/sweden-module-manifest.json references/fixtures/c10/sweden-module-export.json \
  --module-pair references/fixtures/c10/turkiye-module-manifest.json references/fixtures/c10/turkiye-module-export.json \
  --c12-rule-extension references/fixtures/c12/sweden-rule-extension.json \
  --c12-rule-extension references/fixtures/c12/turkiye-rule-extension.json \
  --c12-fact-ledger references/fixtures/c12/L1-fact-ledger.json \
  --c13-evidence-set references/fixtures/c13/L1-evidence-set.json \
  --run-id RUN-C10-L1 --time-of-check 2026-10-09T20:00:00Z --workdir /tmp/c13-L1
python scripts/c6_integration.py release --workdir /tmp/c13-L1
python scripts/c6_integration.py verify --workdir /tmp/c13-L1
```

## Evaluation meaning

The 36-item `evaluations/c13-heldout-lexical-benchmark.json` is an inspectable manually labelled *wording* challenge with 12 examples each for L1/L4/L5. It is not independent lawyer grading, a test of authenticity, source authority correctness, or general NLP recall. Its false negatives must be counted, not optimized away by reporting only known successful fixtures. Twelve additional hypothetical legal case variants in `evaluations/c13-ungraded-legal-merits-cases.json` require external legal adjudication before any legal-correctness score can be reported.

## C14 compatibility extension

The C13 stage now also contains review-only `c14_interpretation_candidates` and `c14_review_targets`, with pinned grammar/topic hashes. Neither can upgrade C12 facts or create findings. See `references/c14-interpretation-and-review.md`.
