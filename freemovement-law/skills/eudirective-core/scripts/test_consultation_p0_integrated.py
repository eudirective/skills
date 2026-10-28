#!/usr/bin/env python3
"""Unmocked local controlled-release tests using fictional fixture records.

The reviewed routing metadata is created only in a disposable copied tree. The
production metadata remains pending independent review. Fictional
``official_reference`` entries exercise structural acceptance only and do not
represent real or authenticated law.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
PLUGIN = CORE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import consultation_issue_selection as selector
import consultation_route_gate as route_gate


STAMP = "2026-10-20T12:00:00Z"
ISSUE_REF = "r_0000000000000101"
SCOPE_REF = "r_0000000000000102"
CONVERSATION_REF = "r_0000000000000103"
PREFLIGHT_REF = "r_0000000000000104"
RESEARCH_REF = "r_0000000000000105"
RESEARCH_ID = "RCH-P0-INTEGRATED"
TASK_ID = "RQT-P0-INTEGRATED"
CLAIM_ID = "RCL-P0-INTEGRATED"
OWNER = {
    "family": "core_source",
    "owner_id": "eu_common_core",
    "jurisdiction": "EU",
    "role": "common_eu",
    "source_pack_sha256": "a" * 64,
}


def digest_obj(value: dict) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def official_reference(ref: str, source_type: str, legal_status: str, title: str) -> dict:
    return {
        "record_kind": "official_reference",
        "owner": copy.deepcopy(OWNER),
        "reference_id": ref,
        "authority": "Synthetic test authority; not a real publisher",
        "publisher_basis": "Fictional metadata used only to exercise structural validators",
        "source_type": source_type,
        "legal_status": legal_status,
        "title": title,
        "url": f"https://example.invalid/{ref.casefold()}",
        "language": "en",
        "reviewed_at": STAMP,
        "scope_note": "Fictional fixture record; no proposition of law is asserted.",
        "limitations": ["Not a real or authenticated source."],
        "activation_status": "reference_only_not_registered",
    }


def make_research_records():
    class_sources = [
        ("REF-P0-EU-LAW", "directive", "binding_secondary_law", "Synthetic EU-law fixture"),
        ("REF-P0-EU-CASE", "judgment", "case_law", "Synthetic case-law fixture"),
    ]
    evidence_ids = ["REV-P0-EU-LAW", "REV-P0-EU-CASE"]
    finding_ids = ["RFN-P0-EU-LAW", "RFN-P0-EU-CASE"]
    sources = [official_reference(*item) for item in class_sources]
    plan = {
        "contract_version": "0.1.0",
        "research_id": RESEARCH_ID,
        "created_at": STAMP,
        "purpose": "synthetic_issue_followup",
        "mode": "case",
        "question": "Validate a fictional EU-scope research fixture.",
        "synthetic_binding": {
            "run_id": "RUN-C10-L1",
            "issue_index_sha256": "b" * 64,
            "issue_id": "ISS-SYNTHETIC-P0-01",
        },
        "tasks": [{
            "task_id": TASK_ID,
            "task_kind": "eu_common_law",
            "question": "Exercise structural EU source-class mapping using fictional records.",
            "owner": copy.deepcopy(OWNER),
            "acceptance_criteria": ["Both required fixture classes are linked to findings."],
        }],
    }
    evidence = []
    findings = []
    preflight_sources = []
    for index, ((ref, _source_type, _legal_status, _title), evidence_id, finding_id, source) in enumerate(
        zip(class_sources, evidence_ids, finding_ids, sources), start=1
    ):
        evidence.append({
            "evidence_id": evidence_id,
            "task_id": TASK_ID,
            "relation": "supports",
            "directness": "direct",
            "source": source,
            "pinpoint": f"Synthetic fixture marker {index}",
            "accessed_at": STAMP,
            "limitations": ["Fictional fixture; no legal conclusion."],
        })
        findings.append({
            "finding_id": finding_id,
            "task_id": TASK_ID,
            "statement": f"Fictional source record {index} is structurally linked.",
            "disposition": "supported_for_review",
            "evidence_ids": [evidence_id],
            "counterevidence_ids": [],
            "falsifier_review": {
                "question": "Would a conflicting fixture alter this structural mapping?",
                "result": "survives_review",
                "note": "Structural fixture only; no law is asserted.",
            },
            "limitations": ["Does not establish authenticity, current law, or legal applicability."],
        })
        source_class = "eu_binding_law" if index == 1 else "case_law"
        preflight_sources.append({
            "source_ref": ref,
            "record_kind": "official_reference",
            "source_class": source_class,
            "acceptance_state": "reference_usable",
            "currentness": "reviewed_current",
            "source_date": None,
            "evidence_ids": [evidence_id],
            "scope_note": "Synthetic fixture record; no real law represented.",
            "exceptions_note": "Fixture limitations explicitly retained.",
        })
    bundle = {
        "contract_version": "0.1.0",
        "research_id": RESEARCH_ID,
        "plan_sha256": digest_obj(plan),
        "mode": "case",
        "reviewed_at": STAMP,
        "coverage_status": "complete",
        "tasks": [{
            "task_id": TASK_ID,
            "status": "complete",
            "search_log": [{
                "query": "fictional P0 fixture query",
                "channel": "synthetic test fixture",
                "searched_at": STAMP,
                "result_summary": "Fictional fixture records only; no source search performed.",
            }],
            "finding_ids": finding_ids,
            "evidence_ids": evidence_ids,
            "limitations": ["No external research or legal assessment is represented."],
        }],
        "findings": findings,
        "evidence": evidence,
        "claims": [{
            "claim_id": CLAIM_ID,
            "statement": "The fictional fixture is internally linked for structural testing.",
            "disposition": "supported_for_review",
            "finding_ids": finding_ids,
            "counterevidence_ids": [],
            "falsifier_review": {
                "question": "Would a conflicting fixture alter this structural test?",
                "result": "survives_review",
                "note": "Synthetic contract behavior only.",
            },
            "limitations": ["Not a legal claim or source verification."],
        }],
        "legal_merits_status": "not_determined",
        "downstream_status": "research_only",
    }
    preflight = {
        "contract_version": "0.3.0",
        "preflight_id": PREFLIGHT_REF,
        "research_id": RESEARCH_ID,
        "coverage_claim": "accounted_for_review",
        "issues": [{
            "issue_id": "ISS-P0-INTEGRATED",
            "consultation_issue_ref": ISSUE_REF,
            "consultation_scope_ref": SCOPE_REF,
            "matter_issue_ref": "ISS-MAT-P0-INTEGRATED",
            "task_id": TASK_ID,
            "claim_ids": [CLAIM_ID],
            "question": "Fictional EU-scope source-class fixture.",
            "owner": copy.deepcopy(OWNER),
            "required_source_classes": ["case_law", "eu_binding_law"],
            "sources": preflight_sources,
            "scope_review": "reviewed",
            "exceptions_review": "reviewed",
            "counterauthority_review": "searched_none_reported",
            "counterauthority_evidence_ids": [],
            "review_provenance": "source_review",
            "reviewed_at": STAMP,
            "gap_disposition": "accounted_for_review",
            "gap_reason": "All synthetic fixture requirements are structurally accounted for.",
        }],
    }
    return plan, bundle, preflight


def make_receipt(*, partial=False, conditional_status=None, c27_status="assessed",
                 selector_module=None, attack_outcome=None):
    selector_impl = selector_module or selector
    requirements = selector_impl.select_issue_requirements(["directive_scope_question"])
    check_ids = requirements["check_ids"]
    assessments = []
    assessment_refs = []
    for index, check_id in enumerate(check_ids, start=1):
        assessment_ref = f"r_{0x200 + index:016x}"
        assessment_refs.append(assessment_ref)
        assessments.append({
            "scope_ref": SCOPE_REF,
            "assessment_ref": assessment_ref,
            "binding_kind": "issue_specific",
            "bound_issue_refs": [ISSUE_REF],
            "record": {
                "check_id": check_id,
                "status": c27_status,
                "method": "model_review",
                "reason": "scope_reviewed",
                "evidence_refs": [CONVERSATION_REF],
                "source_refs": [],
            },
        })
    research_ref = RESEARCH_REF
    research_evidence = "r_0000000000000106"
    preflight_evidence = "r_0000000000000107"
    operation_ids = [
        "route_classification", "c23_guidance", "c27_reconciliation",
        "attack_angle_screen", "requested_output", "research_gate", "source_preflight",
    ]
    operations = [{
        "operation_id": operation_id,
        "applicability": "required",
        "status": "completed",
        "evidence_refs": [
            research_evidence if operation_id == "research_gate" else
            preflight_evidence if operation_id == "source_preflight" else CONVERSATION_REF
        ],
    } for operation_id in operation_ids]
    attack_reviews = []
    for topic in requirements["attack_angle_topics"]:
        trigger_ids = sorted(set(topic["trigger_any_signal_ids"]) | set(topic["trigger_all_signal_ids"]))
        adverse_ids = topic["adverse_predicate_ids"]
        mapped = bool(adverse_ids)
        outcome = attack_outcome or "unresolved"
        if outcome == "no_signal_identified" and not mapped:
            raise ValueError("test-only closed path requires mapped attack predicates")
        reason_code = (
            "no_adverse_signal" if outcome == "no_signal_identified" else
            "evidence_missing" if mapped else "predicate_unmapped"
        )
        attack_reviews.append({
            **topic,
            "outcome": outcome,
            "evidence_ref": CONVERSATION_REF,
            "screening": {
                "reason_code": reason_code,
                "predicate_states": [{
                    "signal_id": signal_id,
                    "state": "present" if signal_id in {"directive_scope_question"} else "absent",
                    "evidence_ref": CONVERSATION_REF,
                } for signal_id in trigger_ids],
                "adverse_predicate_states": [{
                    "predicate_id": predicate_id,
                    "state": "absent" if outcome == "no_signal_identified" else "unknown",
                    "evidence_ref": CONVERSATION_REF,
                } for predicate_id in adverse_ids],
            },
        })
    conditional_closed = conditional_status in {"evidence_resolved", "qualified_condition"}
    conditional_answer = partial or conditional_status is not None
    attack_closed = all(item["outcome"] != "unresolved" for item in attack_reviews)
    closed = not partial and (conditional_status is None or conditional_closed) and attack_closed
    issue = {
        "issue_ref": ISSUE_REF,
        "scope_ref": SCOPE_REF,
        "signal_ids": ["directive_scope_question"],
        "disposition": "answered_conditionally" if conditional_answer else "answered_supported",
        "evidence_ref": CONVERSATION_REF,
        "c27_assessment_refs": assessment_refs,
        "conditional_closure": {
            "status": (conditional_status or "predicate_open") if conditional_answer else "not_conditional",
            "evidence_refs": [] if not conditional_answer else [CONVERSATION_REF],
        },
        "source_owner_exclusions": [{
            "owner_id": owner_id,
            "reason_code": "no_source_class_predicate_triggered",
            "evidence_ref": CONVERSATION_REF,
        } for owner_id in requirements["source_owner_exclusions"]],
        "source_obligations": [{
            "owner_id": owner_id,
            "required_source_classes": value["required_classes"],
            "policy_excluded_source_classes": value["excluded_classes"],
            "status": "reviewed",
            "evidence_ref": preflight_evidence,
            "preflight_ref": PREFLIGHT_REF,
        } for owner_id, value in requirements["source_class_requirements"].items()
            if value["required_classes"]],
        "attack_angle_reviews": attack_reviews,
    }
    abstract_state = {
        "manifest_version": "0.1.0",
        "issues": [{
            "issue_ref": ISSUE_REF,
            "scope_ref": SCOPE_REF,
            "signal_states": [{"signal_id": "directive_scope_question", "state": "present"}],
        }],
    }
    issue_summary = [] if closed else [{
        "issue_ref": ISSUE_REF,
        "title": "Synthetic scope predicate",
        "missing": "Topic-specific adverse predicate mappings or evidence remain unresolved in this partial fixture.",
        "effect": "The output must remain qualified and must not claim comprehensive coverage.",
    }]
    return {
        "schema_version": "0.5.0",
        "route_ref": "r_0000000000000108",
        "request_kind": "applicant_guidance",
        "invocation": {
            "state": "explicit", "basis": "visible_plugin_marker",
            "dashboard_requested": True, "material_change": False,
        },
        "revision_control": {
            "change_detection_status": "compared",
            "current_abstract_state": abstract_state,
            "previous_abstract_state": copy.deepcopy(abstract_state),
            "added_issue_refs": [], "removed_issue_refs": [], "changed_issue_refs": [],
            "affected_scope_refs": [], "reassessed_scope_refs": [], "removed_issue_reviews": [],
        },
        "source_ledger": {
            "response_tracking": "model_declared",
            "conversation_tracking": "model_declared",
            "sources": [],
        },
        "classification": {
            key: {"state": "recorded", "evidence_ref": CONVERSATION_REF}
            for key in (
                "jurisdictions_by_role", "proceedings_and_stages", "legal_questions",
                "urgency", "requested_output",
            )
        },
        "conditional_review": {"status": "reviewed", "evidence_ref": CONVERSATION_REF},
        "operations": operations,
        "c27_checks": assessments,
        "issues": [issue],
        "evidence": [
            {"evidence_ref": CONVERSATION_REF, "kind": "conversation_record", "record_scope": "current_response"},
            {"evidence_ref": research_evidence, "kind": "research_gate", "subject_ref": RESEARCH_REF},
            {"evidence_ref": preflight_evidence, "kind": "source_preflight", "subject_ref": PREFLIGHT_REF},
        ],
        "research_artifacts": [{
            "research_ref": RESEARCH_REF,
            "plan_path": "plan.json", "bundle_path": "bundle.json",
            "preflight_ref": PREFLIGHT_REF, "preflight_path": "preflight.json",
        }],
        "module_pairs": [],
        "coverage_claim": "comprehensive" if closed else "partial",
        "dashboard": {
            "assessment_status": "reviewed" if closed else "partial",
            "issue_summaries": issue_summary,
            "module_use": [{
                "module_id": "eudirective-core",
                "role": "consultation routing and EU/common legal analysis",
                "availability": "available", "response_use": "used",
                "conversation_use": "used_earlier", "conformance": "not_applicable",
                "reason": "The core consultation workflow is represented in this fictional test fixture.",
            }],
        },
    }


class IntegratedControlledReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fm-p0-integrated-")
        self.root = Path(self.temp.name)
        self.plugin = self.root / "freemovement-law"
        self.core = self.plugin / "skills" / "eudirective-core"
        self.run_dir = self.root / "run"
        self.run_dir.mkdir()
        shutil.copytree(HERE, self.core / "scripts", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(CORE / "references", self.core / "references")
        shutil.copytree(
            CORE / "tests" / "fixtures" / "core-source-pack-0.6.1",
            self.core / "tests" / "fixtures" / "core-source-pack-0.6.1",
        )
        # Materialize only static route-reference paths in this disposable
        # tree. These synthetic placeholders are not treated as source records.
        routing = json.loads((self.core / "references" / "consultation-issue-routing.json").read_text(encoding="utf-8"))
        for owner in routing["source_owners"].values():
            for relative in owner.get("core_references", []):
                candidate = self.core / relative
                if not candidate.exists():
                    candidate.parent.mkdir(parents=True, exist_ok=True)
                    candidate.write_text("Synthetic test-only path placeholder; not a source record.\n", encoding="utf-8")
        self._reviewed_test_copy("consultation-issue-routing.json", "routing_review_status")
        self._reviewed_test_copy("consultation-source-class-policy.json", "review_status")
        self._reviewed_test_copy("attack-angles/consultation-topic-review-pathways.json", "consultation_binding_review_status")
        self.script_dir = self.core / "scripts"
        self.receipt_path = self.run_dir / "receipt.json"
        self.answer_path = self.run_dir / "answer.md"
        self.plan_path = self.run_dir / "plan.json"
        self.bundle_path = self.run_dir / "bundle.json"
        self.preflight_path = self.run_dir / "preflight.json"

    def tearDown(self):
        self.temp.cleanup()

    def _reviewed_test_copy(self, relative: str, field: str):
        path = self.core / "references" / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(CORE / "references" / relative, path)
        value = json.loads(path.read_text(encoding="utf-8"))
        value[field] = "reviewed"
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def write_fixture(self, *, partial=False, conditional_status=None, c27_status="assessed",
                      selector_module=None, attack_outcome=None):
        plan, bundle, preflight = make_research_records()
        receipt = make_receipt(
            partial=partial, conditional_status=conditional_status, c27_status=c27_status,
            selector_module=selector_module, attack_outcome=attack_outcome,
        )
        for path, value in (
            (self.plan_path, plan), (self.bundle_path, bundle),
            (self.preflight_path, preflight), (self.receipt_path, receipt),
        ):
            path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return receipt

    def install_test_only_pathway_mappings(self):
        """Add synthetic mappings only inside this test's disposable plugin copy."""
        route_id = "directive_personal_and_territorial_applicability"
        matrix_path = self.core / "references" / "consultation-issue-routing.json"
        pathways_path = self.core / "references" / "attack-angles" / "consultation-topic-review-pathways.json"
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        pathways = json.loads(pathways_path.read_text(encoding="utf-8"))
        route = next(item for item in matrix["routes"] if item["route_id"] == route_id)
        topics = route["potential_attack_angle_review"]["review_topics"]
        for index, topic in enumerate(topics, start=1):
            pathways["topics"].append({
                "topic_id": f"synthetic_p0_closed_path_{index}",
                "label": topic,
                "coverage": "not_implemented_in_C5d_deterministic_predicates",
                "c27_families": ["eu_scope"],
                "consultation_bindings": [{
                    "route_id": route_id,
                    "when_any_signal": ["directive_scope_question"],
                }],
                "adverse_signal": (
                    "Synthetic test-only screen predicate; it is not a legal rule or finding."
                ),
            })
        pathways_path.write_text(json.dumps(pathways, indent=2) + "\n", encoding="utf-8")

        # Load the selector from the staged copy so fixture selection and the
        # subprocess validators use the same isolated test-only metadata.
        copied_selector = self.script_dir / "consultation_issue_selection.py"
        spec = importlib.util.spec_from_file_location(
            "consultation_issue_selection_test_copy", copied_selector
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("test_copy_selector_unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_script(self, name: str, *args: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(self.script_dir / name), *map(str, args)],
            cwd=self.plugin, env=env, capture_output=True, check=False,
        )

    def run_release(self):
        return self.run_script(
            "consultation_release_gate.py", "controlled-release",
            "--receipt", str(self.receipt_path), "--answer", str(self.answer_path),
        )

    def prepare_answer(self, body: str):
        route = self.run_script("consultation_route_gate.py", str(self.receipt_path))
        self.assertEqual(route.returncode, 0, route.stderr.decode())
        report = json.loads(route.stdout)
        self.assertIn(report["status"], {"structurally_closed_declared_plan", "valid_partial_route"})
        self.answer_path.write_bytes((body.rstrip() + "\n\n" + report["dashboard_preview"]).encode("utf-8"))
        return report

    def test_checked_path_stays_partial_when_attack_predicates_are_unmapped(self):
        self.write_fixture()
        research = self.run_script(
            "research_gate.py", "--plan", str(self.plan_path), "--bundle", str(self.bundle_path),
            "--require-complete",
        )
        self.assertEqual(research.returncode, 0, research.stderr.decode())
        self.assertEqual(json.loads(research.stdout)["status"], "valid")

        preflight = self.run_script(
            "issue_source_preflight.py", "--preflight", str(self.preflight_path),
            "--plan", str(self.plan_path), "--bundle", str(self.bundle_path),
        )
        self.assertEqual(preflight.returncode, 0, preflight.stderr.decode())
        self.assertEqual(json.loads(preflight.stdout)["status"], "accounted_for_review")

        report = self.prepare_answer("Synthetic integrated answer; no legal proposition asserted.")
        self.assertEqual(report["status"], "valid_partial_route")
        self.assertEqual(report["research_reports"][0]["status"], "valid")
        self.assertEqual(report["source_preflight_reports"][0]["status"], "accounted_for_review")
        self.assertTrue(any("attack_angle_predicate_unmapped" in item for item in report["outstanding"]))
        self.assertIn("no topic-specific adverse predicate is mapped", report["dashboard_preview"])
        self.assertIn("**PARTIAL**", report["dashboard_preview"])
        self.assertIn("Supported: **0 (0%)**", report["dashboard_preview"])
        self.assertIn("Partial/open: **1 (100%)**", report["dashboard_preview"])

        released = self.run_release()
        self.assertEqual(released.returncode, 0, released.stderr.decode())
        self.assertEqual(released.stdout, self.answer_path.read_bytes())

    def test_test_only_reviewed_metadata_releases_complete_synthetic_path(self):
        test_selector = self.install_test_only_pathway_mappings()
        receipt = self.write_fixture(
            selector_module=test_selector,
            attack_outcome="no_signal_identified",
        )
        self.assertEqual(receipt["coverage_claim"], "comprehensive")
        self.assertTrue(all(
            item["outcome"] == "no_signal_identified"
            for item in receipt["issues"][0]["attack_angle_reviews"]
        ))

        report = self.prepare_answer("Synthetic closed-path fixture; no legal proposition asserted.")
        self.assertEqual(report["status"], "structurally_closed_declared_plan")
        self.assertEqual(report["outstanding"], [])
        self.assertEqual(report["research_reports"][0]["status"], "valid")
        self.assertEqual(report["source_preflight_reports"][0]["status"], "accounted_for_review")
        self.assertIn("**REVIEWED**", report["dashboard_preview"])

        released = self.run_release()
        self.assertEqual(released.returncode, 0, released.stderr.decode())
        self.assertEqual(released.stdout, self.answer_path.read_bytes())

    def test_qualified_partial_path_releases_exact_bytes_with_open_predicate(self):
        self.write_fixture(partial=True)
        report = self.prepare_answer("Synthetic answer, qualified because one predicate remains open.")
        self.assertEqual(report["status"], "valid_partial_route")
        self.assertTrue(any("conditional_predicate_open" in item for item in report["outstanding"]))
        self.assertIn("**PARTIAL**", report["dashboard_preview"])
        released = self.run_release()
        self.assertEqual(released.returncode, 0, released.stderr.decode())
        self.assertEqual(released.stdout, self.answer_path.read_bytes())

    def test_resolved_conditional_does_not_close_unmapped_attack_screen(self):
        for closure_status, label in (
            ("evidence_resolved", "Evidence resolved"),
            ("qualified_condition", "Qualified condition"),
        ):
            with self.subTest(closure_status=closure_status):
                self.write_fixture(conditional_status=closure_status)
                report = self.prepare_answer("Synthetic answer with a recorded conditional closure.")
                self.assertEqual(report["status"], "valid_partial_route")
                self.assertIn("Conditionally closed: **0 (0%)**", report["dashboard_preview"])
                self.assertIn("Partial/open: **1 (100%)**", report["dashboard_preview"])
                self.assertIn(f"Conditional closure: **{label}**", report["dashboard_preview"])
                self.assertIn("Conditional closure:", report["dashboard_preview"])
                self.assertIn(
                    "Closure evidence: same evidence/source record already listed above in this scope.",
                    report["dashboard_preview"],
                )
                self.assertIn("no topic-specific adverse predicate is mapped", report["dashboard_preview"])
                released = self.run_release()
                self.assertEqual(released.returncode, 0, released.stderr.decode())
                self.assertEqual(released.stdout, self.answer_path.read_bytes())

    def test_resolved_condition_does_not_hide_separate_open_c27_review(self):
        receipt = self.write_fixture(
            conditional_status="evidence_resolved", c27_status="partial"
        )
        receipt["coverage_claim"] = "partial"
        receipt["dashboard"]["assessment_status"] = "partial"
        self.receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        report = self.prepare_answer("Synthetic answer; predicate resolved but a required C27 review remains open.")
        self.assertEqual(report["status"], "valid_partial_route")
        self.assertIn("Conditionally closed: **0 (0%)**", report["dashboard_preview"])
        self.assertIn("Partial/open: **1 (100%)**", report["dashboard_preview"])
        self.assertIn(
            "**🟠 Conditional answer · required screen unresolved — Synthetic scope predicate**",
            report["dashboard_preview"],
        )
        self.assertIn(
            "Primary assessment: conditional; the issue remains partial/open until its required attack-angle screen is resolved.",
            report["dashboard_preview"],
        )
        self.assertIn("Conditional closure: **Evidence resolved**", report["dashboard_preview"])
        self.assertIn(
            "**C27 check linked to this issue:** 🟠 `case_intake.actor_roles` · partial · model review.",
            report["dashboard_preview"],
        )
        self.assertIn("c27_check_open", " ".join(report["outstanding"]))

    def test_neutral_route_signal_cannot_create_an_unmapped_attack_candidate(self):
        receipt = self.write_fixture()
        topic = receipt["issues"][0]["attack_angle_reviews"][0]
        topic["screening"]["predicate_states"] = [{
            "signal_id": "formal_refusal_issued", "state": "absent",
            "evidence_ref": CONVERSATION_REF,
        }]
        self.receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        rejected = self.run_script("consultation_route_gate.py", str(self.receipt_path))
        self.assertEqual(rejected.returncode, 2)
        self.assertIn(b"issue_attack_screen_predicate_binding_mismatch", rejected.stderr)

        receipt = self.write_fixture()
        topic = receipt["issues"][0]["attack_angle_reviews"][0]
        topic["outcome"] = "candidate_same_issue"
        topic["screening"]["reason_code"] = "candidate_assessed"
        self.receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        rejected = self.run_script("consultation_route_gate.py", str(self.receipt_path))
        self.assertEqual(rejected.returncode, 2)
        self.assertIn(b"issue_attack_unmapped_predicate_must_remain_unresolved", rejected.stderr)

    def test_tampered_research_and_stale_preflight_block_answer_bytes(self):
        self.write_fixture()
        self.prepare_answer("Synthetic partial answer pending attack predicate mapping.")
        plan = json.loads(self.plan_path.read_text(encoding="utf-8"))
        plan["question"] = "Changed after bundle creation."
        self.plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        blocked = self.run_release()
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(blocked.stdout, b"")
        self.assertIn(b"evidence_research_report_unverified", blocked.stderr)

        self.write_fixture()
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        receipt["dashboard"]["assessment_status"] = "partial"
        self.receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        preflight = json.loads(self.preflight_path.read_text(encoding="utf-8"))
        preflight["coverage_claim"] = "partial"
        preflight["issues"][0]["sources"][0]["currentness"] = "stale"
        preflight["issues"][0]["gap_disposition"] = "open"
        preflight["issues"][0]["gap_reason"] = "The fictional source has stale currentness in this adversarial fixture."
        self.preflight_path.write_text(json.dumps(preflight, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        report = self.prepare_answer("Synthetic partial answer; stale source status is disclosed.")
        self.assertEqual(report["status"], "valid_partial_route")
        self.assertTrue(any("source_preflight" in item for item in report["outstanding"]))
        self.assertIn("**PARTIAL**", report["dashboard_preview"])
        released = self.run_release()
        self.assertEqual(released.returncode, 0, released.stderr.decode())
        self.assertEqual(released.stdout, self.answer_path.read_bytes())

    def test_legacy_receipt_is_not_accepted_for_strict_controlled_release(self):
        receipt = self.write_fixture(partial=True)
        receipt["schema_version"] = "0.4.0"
        receipt.pop("revision_control", None)
        self.receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.prepare_answer("Legacy receipt fixture.")
        blocked = self.run_release()
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(blocked.stdout, b"")
        self.assertIn(b"controlled_release_requires_receipt_0_5_or_later", blocked.stderr)

    def assert_no_fixture_or_path_leak(self, result, *markers: bytes):
        combined = result.stdout + result.stderr
        self.assertNotIn(str(self.root).encode(), combined)
        for marker in markers:
            self.assertNotIn(marker, combined)

    def test_symlinked_research_artifact_is_rejected_without_path_leak(self):
        self.write_fixture()
        external = self.root / "external-plan.json"
        external.write_text("SYNTHETIC_EXTERNAL_TARGET_MARKER", encoding="utf-8")
        self.plan_path.unlink()
        self.plan_path.symlink_to(external)
        with self.assertRaisesRegex(route_gate.RouteGateError, "research_plan:symlink_not_allowed"):
            route_gate.safe_relative_file(self.run_dir, "plan.json", "research_plan")

        route = self.run_script("consultation_route_gate.py", str(self.receipt_path))
        self.assertEqual(route.returncode, 2, route.stderr.decode() + route.stdout.decode())
        self.assertIn(b"evidence_research_report_unverified", route.stderr)
        self.assert_no_fixture_or_path_leak(route, b"SYNTHETIC_EXTERNAL_TARGET_MARKER")

        blocked = self.run_release()
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(blocked.stdout, b"")
        self.assert_no_fixture_or_path_leak(blocked, b"SYNTHETIC_EXTERNAL_TARGET_MARKER")

    def test_invalid_utf8_receipt_is_rejected_without_content_or_path_leak(self):
        self.write_fixture()
        marker = b"SYNTHETIC_RECEIPT_CONTENT_MARKER"
        self.receipt_path.write_bytes(marker + b"\xff")
        blocked = self.run_release()
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(blocked.stdout, b"")
        self.assertIn(b"receipt_json_invalid", blocked.stderr)
        self.assert_no_fixture_or_path_leak(blocked, marker)

    def test_invalid_utf8_research_artifact_is_rejected_without_content_or_path_leak(self):
        self.write_fixture()
        marker = b"SYNTHETIC_RESEARCH_CONTENT_MARKER"
        self.plan_path.write_bytes(marker + b"\xff")

        research = self.run_script(
            "research_gate.py", "--plan", str(self.plan_path), "--bundle", str(self.bundle_path),
        )
        self.assertEqual(research.returncode, 2)
        self.assertIn(b"input is not UTF-8", research.stderr)
        self.assert_no_fixture_or_path_leak(research, marker)

        blocked = self.run_release()
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(blocked.stdout, b"")
        self.assert_no_fixture_or_path_leak(blocked, marker)

    def test_privacy_pattern_rejects_free_text_without_content_or_path_leak(self):
        receipt = self.write_fixture(partial=True)
        marker = "privacy fixture contact: test-subject@example.invalid"
        receipt["dashboard"]["issue_summaries"][0]["missing"] = marker
        self.receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        blocked = self.run_release()
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(blocked.stdout, b"")
        self.assertIn(b"privacy_minimisation_failed", blocked.stderr)
        self.assert_no_fixture_or_path_leak(blocked, marker.encode("utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
