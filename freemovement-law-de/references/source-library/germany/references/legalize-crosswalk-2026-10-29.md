# Germany Legalize source crosswalk — 29 October 2026

## Scope and repository

Reviewed [legalize-dev/legalize-de](https://github.com/legalize-dev/legalize-de) at pinned main commit [`33f01eee9c28e457edd2189d54b4011b524fe3ed`](https://github.com/legalize-dev/legalize-de/tree/33f01eee9c28e457edd2189d54b4011b524fe3ed), dated 22 October 2026. The repository describes a corpus of consolidated federal law from Gesetze im Internet, excluding Land law. Its README says the displayed consolidations are not the authentic promulgated texts; the Federal Law Gazette remains authoritative for discrepancies and specific promulgation questions. It identifies official statutory texts as public domain under § 5 UrhG and separates the MIT-licensed pipeline.

This bounded crosswalk checks two principal federal records already registered in the Germany pack: the Freizügigkeitsgesetz/EU and the Aufenthaltsgesetz. It does not claim to inventory all 5,793 repository files or all 47 Germany source records.

## Candidate review

| Source-library record | Legalize-DE check | Disposition |
|---|---|---|
| `de-06` — Freizügigkeitsgesetz/EU | The pack holds the official Gesetze im Internet record and a dated local capture at publisher build `20260722220024`, checked 23 October 2026. The complete pinned Legalize-DE tree contains 5,793 entries and no path containing the law’s `FREIZ` abbreviation; the expected candidate was not found. | No Legalize candidate or retrieval method. Keep the official portal reference and dated copy; refer promulgation or version disputes to the Bundesgesetzblatt. |
| `de-08` — Aufenthaltsgesetz | [`de/AUFENTHG-2004.md`](https://github.com/legalize-dev/legalize-de/blob/33f01eee9c28e457edd2189d54b4011b524fe3ed/de/AUFENTHG-2004.md) points to the same Gesetze im Internet source. Legalize metadata says `last_updated: 2026-10-21` and `stand: zuletzt geändert durch Art. 13 G v. 22.7.2026 I Nr. 222`. The pack’s accepted official capture is frozen at publisher build `20260910215515`; its record preserves an unresolved amendment-processing note. | Candidate identified, but no retrieval method assigned. It was compared against the accepted official capture by section: all 201 section numbers were present in both; normalized word sequences matched in 192 sections. Nine sections differed: § 11, § 71 and § 44a include publisher amendment-history notes in the official capture; body text differs in §§ 54, 99, 16g, 60c, 60d and 81a. The candidate’s asserted later update date and these text differences require an exact-version check against the official publisher before any method or copy is accepted. |

## Attribution and conversion

The Legalize-DE file is an automated Gesetze-im-Internet reproduction, not an official text. Attribute the Bundesministerium der Justiz/Bundesamt für Justiz as publisher and Legalize-DE as the secondary candidate repository when discussing the candidate. The accepted local copy remains attributed to Gesetze im Internet and its recorded build date.

No Legalize text was copied and no conversion rule is needed. The existing official source captures remain dated and keep their publisher caveats. This crosswalk does not establish completeness of German federal law, Land law, legal topics, or the review of every Legalize candidate.
