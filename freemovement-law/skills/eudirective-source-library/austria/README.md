# Austria national source pack

**Review status (19 October 2026):** 73 of 74 retained source artifacts passed local-artifact acceptance; no captured sources remain pending review; one family-topic index is discovery-only. No official locator-only source remains uncaptured. A reviewed official reference can be used without a local capture; the counts below describe local artifacts. Legal topic coverage and country review remain incomplete.

This pack supports an issue-led review of EU free movement, privileged family-member visas, residence cards, administrative procedure, remedies, case law, oversight and local practice. Its source count is bounded; it is not an exhaustive inventory of Austrian law or practice.

- [Current source inventory](references/source-list.md)
- [Coverage model and completion gates](references/coverage-model.json)
- [Per-source acceptance register](references/source-acceptance.json)
- [Legal dependency and Directive article map](references/source-dependencies.json)
- [Case-law discovery plan](references/case-law-discovery.json)
- [Eleven selected case reviews](references/case-review-register.json)
- [NAG/FPG/BFA-VG procedural crosswalk](references/procedural-crosswalk.md)
- [Forms, submission routes and authority link audit](references/guidance-link-audit.json)
- [Nine-Land and 524-mission discovery queue](references/operational-discovery.json)
- [Capture ledger](references/capture-ledger.json)
- [Per-source retrieval/conversion rules](references/source-rules.json)
- [Nine legacy conversion replays](scripts/replay_legacy_conversions.py)
- [Operational discovery queue generator](scripts/operational_discovery.py)
- [Review gates and acceptance action](scripts/validate_review_gates.py)
- [Annex E/F visual and EU card-format assessment](references/card-format-assessment.json)

The pack has no local core folder. German EU sources are referenced through the shared core index.

The earlier description of Austria as complete overstated a bounded 37-record capture exercise. The workflow now separates source accepted, topic adequately covered and country review complete. The 73 accepted records do not imply the latter two. Accepted sources include FPG §§2(4)(11), 11, 11a, 11b, 15a, 15b, 66, 67 and 70; BFA-VG §§9–10; IFG §§1–20; the BMI EEA-family application form and explanation; six additional VwGH decisions; the C1 visa form; and the verified complaint routes.

All nine former broad-body conversions were replayed with source-specific extraction. The Vienna 2022 decision excludes the screen-reader-only duplicate while retaining the visible text. The BMEIA representation directory is structured as 196 country headings and 524 mission records, with the visible date “Stand 19. Oktober 2026.” Persistent HTML/PDF captures are hashed in the capture ledger. Interactive complaint-form session HTML is intentionally not stored because it contains transient ViewState and validation/session state; only official route metadata is retained.

NAG-DV §5's Austrian wording is preserved. Its reference to Regulation (EU) 2019/1157 has a separate editorial alert linking CJEU C-61/22 and successor Regulation (EU) 2025/1208. Annex E/F are accepted as residence-card specimens, not application forms. Visual review found blank front/reverse card models; the models do not demonstrate the current code in data field [10] or the functional MRZ/security properties, so compliance of current issued cards remains unresolved. See [card-format-assessment.json](references/card-format-assessment.json).

The official BMI form A and its accompanying explanation are now captured and accepted. The form includes separate checkboxes for a residence card and a permanent residence card. The mission queue has 524 entries; five official mission pages have leads and partial reviews, while 519 records have not been researched. All nine Länder now have at least a basic official authority or legal source lead. Six have partial procedure information and three remain lead-only; no Land task is complete. New leads include BH Linz-Land, three Salzburg district pages, a detailed Styrian e-government procedure, the BH Neunkirchen appointment page, a Kärnten 2025 social guide, Tirol's historical 2019 leaflet, and Vorarlberg's 2018 form. The Burgenland 2024 form surfaced in search was screened out as a citizenship application. Burgenland still has an official delegation ordinance with a stale NAG cross-reference that requires legal validation; Kärnten still lacks card-specific procedure. Neither queue is complete.

The 55-task RIS case-law plan covers VwGH, BVwG and all nine LVwG collections; no full discovery batch is recorded. Supplemental official RIS searching found several additional case leads, including VwGH Ra 2025/18/0038 and Ra 2025/22/0052–0054. They remain unaccepted until captured locally and semantically reviewed. The monthly GitHub Actions workflow file and schedule are present, but current run history and Actions enablement could not be verified because GitHub API connectivity failed on 19 October 2026. The workflow only checks known records and does not discover new cases, missions or Land procedures.

Use [coverage-register.md](references/coverage-register.md) for open gaps and [sustainability-assessment.md](references/sustainability-assessment.md) for rule-maintenance findings.
