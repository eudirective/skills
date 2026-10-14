# EU core C1 source availability and remaining gaps — C18 (2026-10-10)

**Physical sources:** 46 logical EU/common sources, 47 represented files. The active 0.6.1 manifest and C7 trust policy locally hash-check every representation. The 0.5.0/0.6.0 manifests remain archived for provenance, but are not accepted for new C6 synthetic cases. Historical original source digests have not been overwritten.

**Targeted source repair:** the Article 2(2)(a) spouse definition is now physically present in the active English consolidated Directive 2004/38 Markdown, matched in its Article 2 position against official EUR-Lex HTML on 10 October 2026. Compare exact old/new SHA-256/byte counts using `c18-directive-art2-restoration.json`. This check does **not** establish all of the Directive’s text or its legal interpretation.

**Still missing:** 21 source representations remain verified source identity/version notes rather than full primary text. Generate the entire gap list with `python scripts/c18_source_integrity.py --markdown-output <path>`; the resulting register distinguishes 21 notes from 26 locally bundled text representations. Source date fields do not constitute all-source 2026-10-10 revalidation. Independent complete-source comparisons, the 21 missing official full texts and C15f legal-semantic assessment remain pending.

**Release gates:** `python scripts/verify_bundled_source_pack.py`; `python scripts/c18_source_integrity.py`; `python scripts/test_c18_source_integrity.py`. Then C6/C7/C12/C16/C17 tests, standalone sibling-pack verification and post-extraction revalidation. Local hashes alone cannot certify current official law or real-world legal accuracy.
