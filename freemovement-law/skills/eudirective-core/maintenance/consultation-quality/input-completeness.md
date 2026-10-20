# Behavioral evaluation input-completeness ledger

| Required input | Status | Consequence |
| --- | --- | --- |
| Private consultation-assurance inventory | Available: 36 records, all `not_executed` | Scenario inventory exists, but it supplies no response evidence. |
| Baseline plugin version and repository commit | Available: plugin `0.52.2`, core `0.51.1`, baseline commit `343a7464d5574d3c2957f1817dedcf70da6135ce` | A target can be identified for a later run. |
| Supported runtime that invokes the installed target plugin in a fresh conversation | Unavailable in this session | Baseline and candidate transcripts cannot be captured here. |
| Exact model/version and execution configuration | Unavailable until runtime execution | Results cannot be compared reproducibly. |
| Independent human or separately run evaluation-model grading | Unavailable | No quality metrics or critical-error count can be reported. |
| Held-out fictional cases unavailable during implementation | Not prepared or executed | Generalization is unverified. |

Do not fill missing inputs with authored sample outputs, deterministic script results, or reconstructed transcripts. Keep behavioral status `not_executed` until the missing runtime and grading evidence are supplied.
