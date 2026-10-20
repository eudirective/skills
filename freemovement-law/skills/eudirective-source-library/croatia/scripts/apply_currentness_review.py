#!/usr/bin/env python3
"""Record MUP version-index evidence without treating it as a consolidation or capture mandate."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "source-library/croatia"
REF = PACK / "references"


def read(name: str) -> dict:
    return json.loads((REF / name).read_text(encoding="utf-8"))


def write(name: str, value: dict) -> None:
    (REF / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    review = read("currentness-review.json")
    acceptance = read("source-acceptance.json")
    manifest = read("candidate-manifest.json")
    known = {row["id"] for row in manifest.get("documents", [])}
    missing: list[str] = []
    applied: list[str] = []
    stale_conflict_ids = {x["id"] for x in review.get("conflicts", [])}

    for chain in review.get("chains", []):
        if chain.get("status") != "current_index_chain_verified_not_consolidated":
            continue
        for source_id in chain.get("source_ids", []):
            if source_id not in known or source_id not in acceptance.get("records", {}):
                missing.append(source_id)
                continue
            evidence = (
                f"{chain['evidence']} Official publisher index checked {review['reviewed_on']} at "
                f"{review['authority']['index_url']} ({review['authority']['retrieval_reference']}). "
                "This records the latest listed version and known amendment references only; it is not a consolidated text, a mandate to capture every act, or a legal-topic-completeness review."
            )
            if chain["id"] in {"hr-foreigners-act-chain", "hr-third-country-procedure-regulation-chain"}:
                conflict = next((x for x in review.get("conflicts", []) if x["id"] in stale_conflict_ids), None)
                if conflict:
                    evidence += (
                        f" A separate older MUP page omits the latest amendment for this chain; it is recorded as stale in "
                        f"currentness-review.json and does not override the current Propisi index."
                    )
            acceptance["records"][source_id].setdefault("checks", {})["current_legal_version"] = {
                "status": "pass",
                "chain_id": chain["id"],
                "review_date": review["reviewed_on"],
                "evidence_url": review["authority"]["index_url"],
                "evidence": evidence,
            }
            applied.append(source_id)

    mup_index_id = "hr-mup-propis-index"
    if mup_index_id in acceptance.get("records", {}):
        acceptance["records"][mup_index_id].setdefault("checks", {})["current_legal_version"] = {
            "status": "pass",
            "review_date": review["reviewed_on"],
            "evidence_url": review["authority"]["index_url"],
            "evidence": (
                "Live official MUP Propisi index inspected on 2026-10-19; the current page lists the EEA, Foreigners Act, "
                "third-country residence, and third-country procedure chains. A separate older MUP page is stale for two chains."
            ),
        }
        applied.append(mup_index_id)

    if missing:
        raise SystemExit("Missing manifest/acceptance records: " + ", ".join(sorted(set(missing))))

    acceptance["currentness_review_file"] = "references/currentness-review.json"
    write("source-acceptance.json", acceptance)
    print(f"Currentness evidence applied: {len(set(applied))} source records; {len(set(missing))} missing.")
    print("The version-index statuses do not imply consolidation or topic coverage; individual Gazette acts are follow-up only when material to the issue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
