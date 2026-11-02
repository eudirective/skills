# Norway legal-source references

This is a bounded source-reference review, not a complete Norway legal pack. Norway is an EEA EFTA State, not an EU Member State. Keep Norwegian implementation, EEA incorporation and distinct EFTA/Swiss routes separate.

Reviewed 31 October 2026: **52 official external references accepted within recorded scope; 1 exact attachment pending; 1 Avdeling II retrieval/coverage gap; 1 local current-law text copy accepted (no-54); 0 topics accepted; country review incomplete.** The 54 former candidate IDs each have a final source-reference or disposition note under [documents/references](documents/references/). The [source list](references/source-list.md) is the index; [source acceptance](references/source-acceptance.json) records status and evidence.

## Priority official references

- [Immigration Act (no-06)](documents/references/no-06-utlendingsloven-lov-2008-05-15-35.md)
- [Immigration Regulations (no-07)](documents/references/no-07-utlendingsforskriften-for-2009-10-15-1286.md)
- [EEA Act (no-08)](documents/references/no-08-e-s-loven-lov-1992-11-27-109.md)
- [UDI 2010-025 EEA-family guideline (no-11)](documents/references/no-11-udi-2010-025-family-immigration-with-an-eea-citizen.md)
- [UDI EU/EEA residence guidance (no-20)](documents/references/no-20-udi-eea-eu-residence-guidance-hub.md)
- [UNE EEA case route (no-38)](documents/references/no-38-une-eea-cases.md)
- [Supreme Court HR-2022-2329-A (no-44)](documents/references/no-44-supreme-court-family-immigration-ruling-hr-2022-2329-a.md)
- [Legal Aid Act (no-48)](documents/references/no-48-legal-aid-act-lov-1980-06-13-35.md)
- [Current EØS Worker Mobility Act (no-54)](documents/legislation/no-54-e-s-worker-mobility-act-lov-2012-12-14-81.md) — retained Nynorsk text; locator and review note at [no-54](documents/references/no-54-current-e-s-worker-mobility-act-lov-2012-12-14-81.md)

Except for the retained current legal text for no-54, the listed records are source locators and do not establish topic coverage. The exact UDI visa checklist PDF (no-30) is pending verification of its current parent route and revision. The Avdeling II/local-regulation lead (no-05) remains an open retrieval gap; no missing law is inferred from the lack of a publicData package.

The previous candidates and manifests are preserved in the EU Source Update Monitor local archive. Old converted bodies were not promoted as source text. Fifteen prior conversion outputs failed offline replay; sixteen replayed byte-for-byte, which does not establish legal sufficiency or reuse permission. Lovdata's terms were rechecked on 31 October: individual formal laws/central regulations have a copying route under NLOD 2.0 with attribution, but bulk copying/systematic extraction is restricted. The no-54 current-law page is now retained as one text copy under the individual-law NLOD 2.0 route; this does not authorize mass or systematic page extraction. The Legalize-no candidate was not copied because its comparison found 17 empty article bodies, boundary and footnote differences, and list-layout defects. No other local text copy is accepted.

No Norway-specific Source Monitor action is registered. The legacy updater has been disabled because it wrote candidate files and manifests into the pack. No Norway-specific replacement action is registered. National topic coverage, cross-reference dependencies, continuing case-law/mission discovery and operational evidence remain open.

## Topic coverage and dependencies (31 October 2026)

The [coverage register](references/coverage-register.md) and [machine-readable coverage model](references/coverage-model.json) apply the owner-approved EEA scope map v1.0.0 to the six core review pathways. The [dependency register](references/source-dependencies.json) keeps EEA incorporation/adaptations, Norwegian implementation, the Schengen visa route, and the separate EFTA/Swiss route distinct. All six pathways remain incomplete; zero topics are accepted and country review is incomplete.

These registers distinguish retained text from official-reference notes. An official URL or source locator is metadata, not a retained legal source. The no-54 text shown in the current PR branch is proposed in open PR #167 and is not present on `main` until that PR is merged.


## Legalize-no crosswalk (29 October 2026)

The following Legalize files were matched to official records already listed in this pack:

| Existing source | Legalize candidate file | Crosswalk disposition |
|---|---|---|
| no-06 Utlendingsloven, LOV-2008-05-15-35 | [`no/LOV-2008-05-15-35.md`](https://github.com/legalize-dev/legalize-no/blob/729ce30333de9d6f9f1e5faf537999cf42bc2a2f/no/LOV-2008-05-15-35.md) | Identity confirmed. Candidate metadata names amendment LOV-2025-06-20-96; official Lovdata material also exposes later 2026 changes to the Act. Do not treat this file as the current consolidated text without an exact-version comparison. |
| no-08 EØS-loven, LOV-1992-11-27-109 | [`no/LOV-1992-11-27-109.md`](https://github.com/legalize-dev/legalize-no/blob/729ce30333de9d6f9f1e5faf537999cf42bc2a2f/no/LOV-1992-11-27-109.md) | Identity confirmed. The Legalize file is a candidate snapshot; its `last_updated` field is the original 1994 date, not proof of present version status. |
| no-54 EØS-arbeidstakarlova, LOV-2012-12-14-81 | [`no/LOV-2012-12-14-81.md`](https://github.com/legalize-dev/legalize-no/blob/729ce30333de9d6f9f1e5faf537999cf42bc2a2f/no/LOV-2012-12-14-81.md) | Identity confirmed as an EEA worker-mobility statute. Keep the EEA incorporation and the official current source record as the controlling version evidence. |

Legalize-no's README states that its input is Lovdata's current-laws public-data package; central regulations are not included in that package, amendment history is not represented by the free-data extract, and images are omitted. Therefore the Legalize route does **not** fill the existing no-07 Utlendingsforskriften gap or no-05 Avdeling II/regional-regulation gap. It must not be described as a regulations retrieval method.

**Use and attribution:** For an individual candidate, cite Lovdata's official law record and attribute the reused data to Stiftelsen Lovdata under NLOD 2.0, with the Legalize-no repository and pinned revision as the intermediary. Do not bulk-copy or systematically extract the dataset; Lovdata's terms distinguish single-law reuse from bulk extraction. The repo's MIT license covers pipeline code, not a separate content grant.

**Conversion rules:** preserve Bokmål, formal identifiers, chapters/sections, lists, notes and footnotes; record the exact Legalize commit and source record; compare complete body and key EEA provisions against the same official Lovdata version; distinguish original publication date from amendment/effective dates; mark omitted images and attachments; never promote based on repository date or hash alone. No Legalize file is accepted as a retained source text in this review.
