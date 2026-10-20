# Issue-level source preflight

`references/contracts/issue-source-preflight.schema.json` adds source accounting for each neutral material issue. It composes the existing research plan/evidence-bundle contract and `scripts/research_gate.py`; it does not create a second research validator or accepted-source registry.

## What the record binds

Each issue record includes a neutral issue ID, shared matter-issue reference, exact research task and owner, source classes required for review, source references and evidence IDs, source date/currentness declaration, scope and exception review, counterauthority status, review provenance, claim IDs, and an explicit open/accounted disposition. A human-reviewed official source link from any relevant source owner may be recorded as `official_reference` without source-library registration or a saved-content hash. Several owner-specific issue records can share one `matter_issue_ref`, so EU-common and national questions remain separate while visibly concerning the same material issue.

The validator checks that:

- the existing research plan/bundle passes `research_gate.py` and the issue's owner exactly matches its research task;
- registered EU sources resolve to the pinned core-source-pack manifest and local source-byte gate;
- registered Swedish or Türkiye module sources resolve to the exact C3-conformant manifest/export digests and source record;
- a national candidate reference in the form `CAND-<CC>-<library-id>` found in a bundled country `candidate-manifest.json` is bound to that country and exact source ID and remains unaccepted; it does not satisfy a required source class merely by appearing in the inventory;
- a human-reviewed official reference uses `official_reference`, records publisher identity, URL, language, review date, displayed version/cutoff, scope, and limitations, and may satisfy a required source class within that declared scope without a local copy, library registration, or content hash; official status and reviewer identity remain declared evidence, not authenticated facts;
- prefer a usable government-published consolidation for legislation; when none is usable, the closest government-published version can support the issue if its cutoff and limits are recorded. Gazette fragments are targeted follow-ups for material questions, not a default reconstruction task;
- an official reference can be used for research without being added to the bundled library, regardless of whether its owner is EU/common, a supported module, or a national source; a secondary, inaccessible, or unreviewed lead remains open;
- source and counterevidence IDs resolve to the same owner-specific research task and are linked through the declared research claim/finding chain;
- missing source classes, stale or unknown currentness, unreviewed scope/exceptions, open counterauthority, and unfinished tasks remain visible; and
- `accounted_for_review` is rejected when any of those structural gaps remain.

## Limits

Currentness and review states are declared, not authenticated. A `reviewed_within_cutoff` reference supports only the stated period; it does not claim current law beyond the cutoff. The script does not authenticate a reviewer or official publisher, establish legal applicability or entailment, prove counterauthority completeness, or certify nationwide coverage. A locally intact source pack proves only that its local bytes match its manifest. A research reference does not add or activate a source in the library; that is a separate maintenance decision.

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
