# Legalize-li conversion rule — Liechtenstein

**Rule ID:** `legalize-li-ewr-regv-gazette-v1`  
**Reviewed:** 2026-10-29  
**Applies only to:** `legalize-dev/legalize-li/li/LGBl-2020-465.md` at commit `1b19742b74b852c50b50bde418b8045db774b2ba` (blob `db8d62161d531a1972419154df4667c867b19f58`).  
**Official authority:** [Liechtenstein State Law Gazette PDF, LGBl 2020.465](https://www.gesetze.li/konso/pdf/2020465000?version=1); [official Lilex record](https://www.gesetze.li/konso/2020465000).

## Conversion and validation

1. Retain the official title, LGBl/LR identifiers, enactment/publication dates, German wording, preamble, article sequence, commencement provision, signature, and footnote.
2. Treat the candidate front matter and generated H1 as repository metadata/presentation, not part of the enactment. Keep publication date (18 December 2020), enactment date (15 December 2020), and displayed version date (Fassung 01.02.2021) as distinct fields.
3. Convert the body to Markdown headings and paragraphs. Normalize only PDF line wrapping, line-break hyphenation, and the footnote marker/link presentation. Do not translate, paraphrase, silently correct, or change spelling or punctuation.
4. Compare the complete preamble and every provision, signature, and footnote against the official Gazette PDF. Acceptance requires all legal wording and anchors to match. A mismatch or missing page/attachment blocks acceptance.
5. Do not infer that the 2021 Gazette version is the later current consolidated text. Check the official current record and version history before any future refresh or currentness claim.
6. Attribute the legal text to Liechtenstein Government Legal Services/Lilex and identify Legalize-li, the pinned commit, and blob as retrieval/conversion provenance. The candidate repository's MIT code license is not the source-text reuse basis. Reuse is limited to official statutory text under the recorded Liechtenstein URG basis; it does not extend to Lilex interface/design, unrelated materials, or systematic database reuse.

The verified local copy is [li-41 EWR-RegV](../documents/legislation/li-41-ewr-register-regulation.md). The crosswalk records the full-body comparison and its limits.
