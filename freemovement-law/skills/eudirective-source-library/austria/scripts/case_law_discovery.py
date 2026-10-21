#!/usr/bin/env python3
"""Plan, validate, and record complete official RIS discovery batches."""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

PACK = Path(__file__).resolve().parents[1]
TEMPLATE = PACK / "references" / "case-law-discovery.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def expected_tasks(template: dict) -> dict[str, dict]:
    return {row["task_id"]: row for row in template.get("planned_search_tasks", [])}


def make_plan(start: str | None, end: str | None) -> dict:
    template = load(TEMPLATE)
    today = date.today()
    completed = [
        row.get("batch_end")
        for row in template.get("runs", [])
        if row.get("status") == "complete" and row.get("batch_end")
    ]
    start_day = date.fromisoformat(start) if start else (
        date.fromisoformat(max(completed)) + timedelta(days=1) if completed else today.replace(day=1)
    )
    end_day = date.fromisoformat(end) if end else today
    if start_day > end_day:
        raise ValueError("from date must not be after through date")
    tasks = []
    for row in template["planned_search_tasks"]:
        task = dict(row)
        task.update({
            "date_window": {"from": start_day.isoformat(), "through": end_day.isoformat()},
            "status": "not_run",
            "searched_at": None,
            "result_count": None,
            "screened_results": [],
        })
        tasks.append(task)
    return {
        "jurisdiction": "AT",
        "batch_id": f"RIS-{start_day.isoformat()}-{end_day.isoformat()}",
        "batch_start": start_day.isoformat(),
        "batch_end": end_day.isoformat(),
        "status": "planned_not_run",
        "task_count": len(tasks),
        "execution_method": "Open each official RIS search form and enter the listed query, court filter and date window. This command does not access RIS or call an API. Record every result and screening decision before validating.",
        "tasks": tasks,
    }


def validate_batch(batch: dict, template: dict) -> list[str]:
    expected = expected_tasks(template)
    tasks = batch.get("tasks", [])
    ids = [row.get("task_id") for row in tasks]
    errors: list[str] = []
    if batch.get("jurisdiction") != "AT":
        errors.append("batch jurisdiction must be AT")
    if not valid_date(batch.get("batch_start")) or not valid_date(batch.get("batch_end")):
        errors.append("batch must record valid ISO start and end dates")
    elif batch["batch_start"] > batch["batch_end"]:
        errors.append("batch start date must not be after batch end date")
    if set(ids) != set(expected) or len(ids) != len(expected):
        errors.append("batch must contain each of the 55 court/query tasks exactly once")

    for task in tasks:
        task_id = task.get("task_id")
        if task_id not in expected:
            continue
        planned = expected[task_id]
        if task.get("court_collection") != planned.get("court_collection"):
            errors.append(f"{task_id}: court collection does not match the plan")
        if task.get("query") != planned.get("query"):
            errors.append(f"{task_id}: exact planned query is missing or changed")
        if task.get("status") != "searched" or not valid_date(task.get("searched_at")):
            errors.append(f"{task_id}: missing searched status/date")
        window = task.get("date_window")
        if not isinstance(window, dict) or not valid_date(window.get("from")) or not valid_date(window.get("through")):
            errors.append(f"{task_id}: exact date window is missing")
        elif window["from"] != batch.get("batch_start") or window["through"] != batch.get("batch_end"):
            errors.append(f"{task_id}: task date window does not match batch dates")

        count = task.get("result_count")
        if not isinstance(count, int) or count < 0:
            errors.append(f"{task_id}: result_count must be a non-negative integer, including zero-result searches")
        hits = task.get("screened_results")
        if not isinstance(hits, list):
            errors.append(f"{task_id}: screened_results must be a list")
            continue
        if isinstance(count, int) and len(hits) != count:
            errors.append(f"{task_id}: every result must have a screening record")
        for hit in hits:
            for field in ("official_record_url", "screening_decision", "reason"):
                if not hit.get(field):
                    errors.append(f"{task_id}: each hit needs {field}")
            url = hit.get("official_record_url", "")
            if url:
                parsed = urlparse(url)
                if parsed.scheme != "https" or parsed.hostname not in {"ris.bka.gv.at", "www.ris.bka.gv.at"}:
                    errors.append(f"{task_id}: screened result must link to an official RIS record URL")
            if hit.get("screening_decision") not in {"include", "exclude"}:
                errors.append(f"{task_id}: screening_decision must be include or exclude")
            if hit.get("screening_decision") == "include":
                for field in ("case_number", "decision_date", "holding", "outcome", "procedural_posture", "applicability_and_limits"):
                    if not hit.get(field):
                        errors.append(f"{task_id}: included hit missing {field}")
                if not valid_date(hit.get("decision_date")):
                    errors.append(f"{task_id}: included hit decision_date must be ISO YYYY-MM-DD")
    return errors


def plan(args: argparse.Namespace) -> int:
    batch = make_plan(args.from_date, args.through_date)
    print(json.dumps(batch, ensure_ascii=False, indent=2))
    return 0


def validate(args: argparse.Namespace) -> int:
    batch = load(args.batch)
    errors = validate_batch(batch, load(TEMPLATE))
    print(json.dumps({"batch_id": batch.get("batch_id"), "task_count": len(batch.get("tasks", [])), "complete": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 2 if errors else 0


def record(args: argparse.Namespace) -> int:
    batch = load(args.batch)
    template = load(TEMPLATE)
    errors = validate_batch(batch, template)
    existing_ids = {row.get("batch_id") for row in template.get("runs", [])}
    if batch.get("batch_id") in existing_ids:
        errors.append(f"batch_id {batch.get('batch_id')} is already recorded")
    if errors:
        print(json.dumps({"recorded": False, "batch_id": batch.get("batch_id"), "errors": errors}, ensure_ascii=False, indent=2))
        return 2
    recorded = dict(batch)
    recorded.update({"status": "complete", "completed_on": date.today().isoformat()})
    template.setdefault("runs", []).append(recorded)
    template["updated"] = date.today().isoformat()
    template["status"] = "full_court_search_recorded"
    save(TEMPLATE, template)
    print(json.dumps({"recorded": True, "batch_id": recorded.get("batch_id"), "task_count": len(recorded.get("tasks", []))}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("--from-date")
    plan_parser.add_argument("--through-date")
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("batch", type=Path)
    record_parser = commands.add_parser("record")
    record_parser.add_argument("batch", type=Path)
    args = parser.parse_args()
    if args.action == "plan":
        return plan(args)
    if args.action == "validate":
        return validate(args)
    return record(args)


if __name__ == "__main__":
    raise SystemExit(main())
