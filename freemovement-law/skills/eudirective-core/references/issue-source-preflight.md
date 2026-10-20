# Issue-level source preflight

`references/contracts/issue-source-preflight.schema.json` adds source accounting for each neutral material issue. It composes the existing research plan/evidence-bundle contract and `scripts/research_gate.py`; it does not create a second research validator or accepted-source registry.

## What the record binds

Each issue record includes a neutral issue ID, shared matter-issue reference, exact research task and owner, source classes required for review, source record IDs and evidence IDs, source date/currentness declaration, scope and exception review, counterauthority status, review provenance, claim IDs, and an explicit open/accounted disposition. Several owner-specific issue records can share one `matter_issue_ref`, so EU-common and national questions remain separate while visibly concerning the same material issue.

The validator checks that:

- the existing research plan/bundle passes `research_gate.py` and the issue's owner exactly matches its research task;
- registered EU sources resolve to the pinned core-source-pack manifest and local source-byte gate;
- registered Swedish or Türkiye module sources resolve to the exact C3-conformant manifest/export digests and source record;
- a national candidate reference in the form `CAND-<CC>-<library-id>` found in a bundled country `candidate-manifest.json` is bound to that country and exact source ID; the manifest is pinned for named packs, each local representation is checked against its corresponding manifest digest, and the supplied digest must match the inventory or local bytes, while the candidate still remains unaccepted and cannot satisfy a required source class;
- national candidates absent from the bundled inventory may still be recorded as open external candidates, but cannot satisfy a required source class;
- source and counterevidence IDs resolve to the same owner-specific research task and are linked through the declared research claim/finding chain;
- missing source classes, stale or unknown currentness, unreviewed scope/exceptions, open counterauthority, and unfinished tasks remain visible; and
- `accounted_for_review` is rejected when any of those structural gaps remain.

## Limits

`reviewed_current`, `source_review`, and `human_review` are declared provenance. The script does not authenticate a reviewer or establish a live official-publisher check, law's current effect, legal applicability, source entailment, counterauthority completeness, or nationwide coverage. A locally intact source pack proves only that its local bytes match its manifest. The bundled national candidate inventories are not one accepted-source registry: at this checkout, 27 country candidate manifests use 18 different top-level shapes and each reports zero accepted sources. The validator can bind known candidates to those inventories and keep them open, but it does not validate registered national accepted-source records. A national source outside the registered core pack and the two bound module exports remains open unless its owner supplies a supported, validated pack. A candidate, including `unregistered:<CC>`, cannot be promoted by a preflight entry.

Keep preflight and research artifacts generalized and non-identifying. Do not put applicant names, exact case facts, dates, case numbers, or document contents in these files. The scripts perform structural and path checks, not a complete privacy scan.

## Command

```bash
python scripts/issue_source_preflight.py \
  --preflight issue-source-preflight.json \
  --plan research-plan.json \
  --bundle research-evidence-bundle.json
```

Exit `0` means the artifact is structurally valid; output may still show `valid_open_work`. Exit `3` rejects an `accounted_for_review` claim with open items. Exit `2` means the contract, task/owner binding, source record, evidence trace, or underlying research validation is invalid. Even an `accounted_for_review` result is not a legal-completeness finding.

For consultation-route receipts, include `preflight_ref` and `preflight_path` on the related `research_artifact`, include evidence of kind `source_preflight` bound to that opaque reference, and record the `source_preflight` operation. Source-research routes require this operation. The route gate incorporates every open preflight item into its own coverage decision.
