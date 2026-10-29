# Consultation receipt migration

Schema 0.1.0–0.8.0 receipts remain readable for historical replay. Do not relabel an old receipt as 0.8.0 by changing its schema version.

Use `scripts/migrate_consultation_receipt.py` only with a privacy-minimised receipt and a requested mode supplied by the responsible reviewer:

```bash
python scripts/migrate_consultation_receipt.py \
  --input receipt-0.7.json \
  --output receipt-0.8.json \
  --consultation-mode full
```

The migration does not infer the new consultation mode from the old dashboard mode or coverage claim. It removes the old nested dashboard mode, adds issue links only where the existing trigger/evidence record identifies a current issue, validates the 0.8.0 structure, and records the new `consultation_finalisation` operation as `not_checked` with `not_attempted`. It does not claim that the new finalisation was performed.

The migrator refuses missing or ambiguous trigger/limitation links. Resolve those links from the preserved conversation record before retrying; do not invent issue associations. Review the resulting board and run the route gate before using the migrated receipt. Structural migration does not verify the underlying analysis, evidence truth, legal accuracy, or host release behavior.

The receipt format is for abstract, privacy-minimised records. Never send a real applicant narrative, identity, exact date or place, correspondence, or document content to this script.

## Migration to 0.9.0

Use `--target-version 0.9.0` and supply an explicit `--consultation-mode`. For Limited, supply `--limitation-json` pointing to a privacy-minimised object containing `reason_code`, `missing`, `effect`, `issue_refs`, `evidence_refs`, and `review_ids`. Provide `--workflow-reviews-json` with explicit model-led review records and `--strategy-update-json` with an explicit strategy mode and disposition, including an objective or a no-action rationale where applicable. The migrator never invents these records or that explanation. A 0.7 receipt first passes through the existing 0.8 migration; finalisation remains unperformed. Migration validates structure and privacy only; run the route gate to reconcile model-led workflow reviews, execution records and evidence before controlled release. 0.8 receipts remain readable under their historical validation rules.
