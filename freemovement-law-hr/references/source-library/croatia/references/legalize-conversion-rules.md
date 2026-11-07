# Croatia Legalize-HR conversion and comparison rules

**Review date:** 29 October 2026
**Candidate repository:** [norislav/legalize-hr](https://github.com/norislav/legalize-hr)
**Comparison authority:** Narodne novine official ELI/HTML/PDF records

These rules apply when considering a Legalize-HR file as a candidate transcription for a Croatia source-library record. The candidate repository is secondary and early-stage. It may be regenerated, so never refer to an unpinned branch as the source of a reviewed comparison.

## Intake and identity

1. Pin the Legalize commit, exact candidate path and Git blob SHA. Record the retrieval date separately.
2. Resolve the candidate identifier and source ELI to the corresponding Narodne novine publication. Confirm title, year, issue, item number, document type and date against the official publisher.
3. Check the current MUP legislation index or the responsible authority’s official index for later amendments and the relevant version chain. Do not use a candidate timestamp or Git commit date as legal-currentness evidence.
4. Keep each amending act separate unless the official publisher provides a dated consolidation. A matching amendment file does not prove the base instrument’s current consolidated text.

## Body conversion and comparison

1. Exclude YAML frontmatter only from the body-to-body comparison. Keep its identifier and official ELI as identity metadata.
2. Preserve Croatian diacritics, punctuation, paragraph numbering, heading hierarchy, article structure, tables, forms, annexes, signatures and footnotes.
3. Normalize only Markdown presentation, Unicode normalization, equivalent hyphen/space code points and whitespace for comparison. Do not join or split words, infer missing characters, reorder columns, rebuild tables, substitute annex text or remove repeated legal text to force a match.
4. Compare the complete candidate body with the complete official text for the same Gazette edition. Record the exact candidate and official blob/content hashes and the first substantive difference.
5. Treat a missing body, metadata-only file, unreviewed image, omitted form or incomplete PDF extraction as a gap. Do not infer body equivalence from matching title or ELI.
6. Inspect image-based forms and attachments against official page images. If they are omitted or not visually reviewed, mark the candidate incomplete for any use that depends on them.

### Official HTML table rendering

For NN 37/23, the official HTML presents three tariff tables as pipe-delimited text. Render each as a Markdown table by adding a separator row after its header; preserve every source cell and row order. Verify all three tables and all 11 data rows against the official page. Do not use a candidate that flattens cells or merges rows as a source text.

## Acceptance, attribution and rights

- Narodne novine remains the legal source. The pinned Legalize file is only a candidate transcription or discovery route.
- Accept a candidate transcription only after full identity, version, body, table, attachment and reuse checks pass. A crosswalk match alone does not accept a new local copy.
- If a candidate is later retained, attribute the individual Narodne novine act and identify Legalize-HR, the exact commit and file as the intermediary. Keep official publication date, consolidation date and Legalize snapshot date separate.
- Legalize-HR’s MIT license notice is not assumed to grant rights over upstream Croatian law or to authorize bulk reuse. Follow the pack’s existing, source-specific reuse policy; do not copy from the repository as a corpus.
- Do not silently correct extraction defects. Preserve the official-source capture or document any conversion as a separate, reproducible transformation with explicit provenance.

## Croatia review outcome

The 30 October 2026 review found 32 exact normalized body pairs and ten body differences among 42 comparable full bodies. All 46 crosswalk records now have accepted local official text. Three candidate files are metadata-only and one expected Legalize file is absent. The candidate remains a discovery/transcription route; source acceptance requires the locally retained official text.
