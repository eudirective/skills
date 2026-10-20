# C10 scenario and source-noted module pilot

This developmental corpus binds eight fixed fictional case inputs and exactly the matching Sweden and Türkiye module manifests/exports. All entries are code-pinned via the detached JSON policy hash.

Use `scripts/c6_integration.py prepare` with the pinned 0.6.0 EU source catalogue, a case/element/actor triple in `references/fixtures/c10/LN` and the exact enrolled Sweden and (if appropriate) Türkiye module pair. Never use arbitrary personal details. 

**Quality boundary:** C3 modules contain source-identity notes, not full statutory text. Country attack-angle records are candidate-only and can appear for irrelevant facts where their prerequisite IDs are present; semantic reviewers must flag such false positives. EU source pack 0.6.0 is still metadata-pinned for all legacy representations except the bundled Deldwyn judgment. An unavailable legacy standalone pack is not silently reconstructed. C6 full release and outbound/private-data mode remain disabled.

## C10 internal typed `code` handling

`contract_validate.load_json` rejects executable-style `code` keys on all external inputs. Only the bounded `unresolved[index].code` fields of locally produced, exact-replayed stages and their digest-bound issue-index companions may contain a short token `code` after `allow_internal_issue_code=True` is selected internally. Never enable that exception on user/country input.

## Measured limits

The eight C10 fictional scenarios verify pipeline and report behavior, not correct legal merits. In particular, missing appeal-event binding, precise Article 5/10 differentiation, foreign-document evidentiary treatment and Deldwyn pinpoint application are review gaps. An independently certified national source corpus is absent. No full or private release.
