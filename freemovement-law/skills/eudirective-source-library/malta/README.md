# Malta source candidates

This 48-record register spans laws, guidance, forms, visas, procedures, courts, oversight, legal aid and civil-status evidence. Forty-seven sources were retrieved and converted to unaccepted review candidates; the Judiciary portal root returned 403. Twenty-one changed conversions are staged for review. Three initially broken Identità routes were replaced with current official parent-page links. All 47 conversions pass offline hash and replay verification; none is accepted.

Known legislation uses official ELI PDF representations, with original PDF bytes retained before text extraction. The previous visa Annex link was replaced with a versioned EUR-Lex consolidation. The visa-representation list remains uncertain because the official parent page links to a missing older file; a September 2025 replacement was captured without currentness proof. See the source list, capture results, candidate manifest and sustainability assessment in references/.

Run python sync_malta.py sync to refresh the inventory and python sync_malta.py verify for offline hash/replay checks. Install the pinned dependency in requirements.txt for PDF extraction and verification.
