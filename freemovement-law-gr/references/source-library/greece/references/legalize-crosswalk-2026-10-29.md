# Greece Legalize source crosswalk — 29 October 2026

## Scope and repository

Reviewed [legalize-dev/legalize-gr](https://github.com/legalize-dev/legalize-gr) at pinned main commit [36cb88a](https://github.com/legalize-dev/legalize-gr/commit/36cb88a374cd2413cf8b128b7561d1b2bd0129cd), dated 26 October 2026. The repository says it extracts FEK A instruments published from 2000 onward from official National Printing House PDFs. Its README says each Gazette instrument is preserved “as enacted”; amendments are tracked separately and are not consolidated into earlier files. The repository warns that automated Markdown extraction may contain defects and is not a verified legal text. It describes the official statutory texts as public domain; the separate pipeline code is MIT.

This is a bounded review of the pack’s principal Directive 2004/38 instrument, source `gr-05`, Presidential Decree 106/2007. It is not a review of every file in Legalize-GR.

## Candidate checked

Legalize file: [gr/FEK-A-135-2007.md](https://github.com/legalize-dev/legalize-gr/blob/36cb88a374cd2413cf8b128b7561d1b2bd0129cd/gr/FEK-A-135-2007.md), Git blob `21c2a51ae3b95078d8452f17923215ce519e3c64`. Its metadata identifies FEK A 135/2007 and points to the National Printing House PDF. The candidate body identifies Presidential Decree 106 and the same subject as the official pack record. Its publication-date metadata says 22 June 2007, while the Gazette issue itself is dated 21 June 2007.

The official pack record links directly to [National Printing House PDF, Presidential Decree 106/2007](https://api.et.gr/apiLAW/2/2007/106/pdf). Its reviewed text extract, [gr-05 selected provisions](../documents/legislation/gr-05-pd-106-2007-reviewed-provisions.md), identifies the same official PDF and records the source-response and source-text hashes. Comparing Legalize’s extracted text with that official-source-based extract found exact normalized wording for Articles 15 and 16, but differences in Articles 11–14, 17 and 24. The candidate therefore is not a verified verbatim copy even within the reviewed provisions.

## Decision

Do not add Legalize-GR as an accepted source or retrieval method for `gr-05`, and do not copy its Markdown into the accepted corpus. The exact instrument and upstream PDF are identified, but conversion fidelity fails the available article-level comparison. The Legalize file is also explicitly “as enacted,” not a consolidated current version; its amendment metadata does not incorporate those amendments into the body.

Continue using the National Printing House official PDF as the accepted source route. The existing selected-provision extract remains limited to the articles and findings documented in the source list; it does not establish current consolidated wording. No conversion rule is added from this unverified candidate. The official source list already attributes the publisher and the Legalize review result is linked here for auditability.
