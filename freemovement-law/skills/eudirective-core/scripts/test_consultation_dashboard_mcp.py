#!/usr/bin/env python3
"""Synthetic tests for the local dashboard MCP adapter and view contract."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from consultation_dashboard_mcp import (  # noqa: E402
    UI_PATH,
    UI_URI,
    _dispatch,
    _materialize_artifact_files,
    _render,
)
from contract_validate import validate_obj  # noqa: E402
from test_consultation_dashboard import make_route  # noqa: E402


class ConsultationDashboardMcpTests(unittest.TestCase):
    def test_view_model_schema_and_counts_are_deterministic(self):
        receipt = json.dumps(make_route(), sort_keys=True)
        first = _render({"receipt_json": receipt})["structuredContent"]
        second = _render({"receipt_json": receipt})["structuredContent"]
        validate_obj("consultation-dashboard-view", first)
        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "1.0.0")
        self.assertEqual(first["progress"]["operations"]["total"], 5)
        self.assertEqual(first["progress"]["c27_checks"]["total"], 1)
        self.assertIn("text_fallback", first)

    def test_unknown_source_tracking_stays_unknown_in_view_model(self):
        route = make_route(tracking="unavailable", coverage="partial", assessment_status="partial")
        model = _render({"receipt_json": json.dumps(route)})["structuredContent"]
        self.assertIsNone(model["progress"]["source_response"]["count"])
        self.assertEqual(model["progress"]["source_response"]["status"], "unknown")
        self.assertNotIn("%", json.dumps(model["progress"]))

    def test_partial_records_keep_missing_item_and_effect_in_structured_board(self):
        route = make_route(coverage="partial", assessment_status="partial")
        route["dashboard"]["issue_summaries"] = [{
            "issue_ref": "r_0000000000000004",
            "title": "Lodging stage",
            "missing": "Stamped receipt has not been classified.",
            "effect": "The processing clock cannot yet be confirmed.",
        }]
        route["issues"] = [{
            "issue_ref": "r_0000000000000004", "scope_ref": "r_0000000000000003",
            "signal_ids": ["formal_lodgement_confirmed"], "disposition": "fact_missing",
            "evidence_ref": "r_0000000000000001",
        }]
        model = _render({"receipt_json": json.dumps(route)})["structuredContent"]
        cards = [item for section in model["sections"] for item in section["items"]]
        issue = next(item for item in cards if item["title"] == "Issue 1: Lodging stage")
        self.assertEqual(issue["missing"], "Stamped receipt has not been classified.")
        self.assertEqual(issue["effect"], "The processing clock cannot yet be confirmed.")

    def test_partial_c27_check_shows_its_missing_item_and_effect_inline(self):
        route = make_route(coverage="partial", assessment_status="partial")
        route["c27_checks"][0]["record"]["status"] = "partial"
        model = _render({"receipt_json": json.dumps(route)})["structuredContent"]
        c27 = next(section for section in model["sections"] if section["id"] == "c27")
        self.assertIn("does not close", c27["items"][0]["missing"].casefold())
        self.assertTrue(c27["items"][0]["effect"])
        self.assertIn("Missing:", model["text_fallback"])

    def test_non_consultation_model_remains_minimal(self):
        route = make_route(request_kind="no_case_assessment", coverage="partial")
        model = _render({"receipt_json": json.dumps(route)})["structuredContent"]
        self.assertEqual(model["assessment"]["status"], "not_verified")
        self.assertEqual(len(model["sections"]), 1)
        self.assertEqual(model["sections"][0]["id"], "invocation")
        self.assertNotIn("Source ledger", json.dumps(model))

    def test_malformed_or_non_schema_receipt_returns_tool_error_without_echoing_input(self):
        private_value = "PERSONAL-INPUT-SHOULD-NOT-ECHO"
        result = _dispatch({
            "jsonrpc": "2.0", "id": 7, "method": "tools/call",
            "params": {"name": "render_consultation_dashboard", "arguments": {
                "receipt_json": json.dumps({"applicant_name": private_value}),
            }},
        })
        self.assertTrue(result["result"]["isError"])
        self.assertNotIn(private_value, json.dumps(result))

    def test_only_referenced_json_artifacts_are_materialized_in_temporary_tree(self):
        receipt = {"research_artifacts": [{
            "plan_path": "research/plan.json",
            "bundle_path": "research/bundle.json",
            "preflight_path": "research/preflight.json",
        }]}
        files = [
            {"relative_path": "research/plan.json", "json_content": '{"plan":[]}'},
            {"relative_path": "research/bundle.json", "json_content": '{"bundle":[]}'},
            {"relative_path": "research/preflight.json", "json_content": '{"coverage":[]}'},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _materialize_artifact_files(root, receipt, files)
            self.assertEqual(json.loads((root / "research/plan.json").read_text()), {"plan": []})
            self.assertEqual(json.loads((root / "research/bundle.json").read_text()), {"bundle": []})
            self.assertEqual(json.loads((root / "research/preflight.json").read_text()), {"coverage": []})
            with self.assertRaisesRegex(ValueError, "artifact_file_not_referenced"):
                _materialize_artifact_files(root, receipt, [{
                    "relative_path": "research/unlisted.json", "json_content": "{}",
                }])

    def test_referenced_path_traversal_is_rejected_without_writing_outside_tree(self):
        receipt = {"research_artifacts": [{
            "plan_path": "../outside.json", "bundle_path": "bundle.json",
        }]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "artifact_file_path_invalid"):
                _materialize_artifact_files(root, receipt, [{
                    "relative_path": "../outside.json", "json_content": "{}",
                }])
            self.assertEqual(list(root.iterdir()), [])

    def test_malformed_artifact_json_does_not_echo_supplied_contents(self):
        secretish = "PRIVATE-CONTENT-MUST-NOT-APPEAR"
        receipt = {"research_artifacts": [{
            "plan_path": "plan.json", "bundle_path": "bundle.json",
        }]}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(Exception) as caught:
                _materialize_artifact_files(Path(directory), receipt, [{
                    "relative_path": "plan.json", "json_content": secretish,
                }])
        self.assertNotIn(secretish, str(caught.exception))

    def test_mcp_advertises_tool_resource_and_read_only_safety(self):
        initialize = _dispatch({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertIn("tools", initialize["result"]["capabilities"])
        listed = _dispatch({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tool = listed["result"]["tools"][0]
        self.assertEqual(tool["name"], "render_consultation_dashboard")
        self.assertTrue(tool["annotations"]["readOnlyHint"])
        self.assertEqual(tool["_meta"]["ui"]["resourceUri"], UI_URI)
        resource = _dispatch({"jsonrpc": "2.0", "id": 3, "method": "resources/read",
                              "params": {"uri": UI_URI}})
        html = resource["result"]["contents"][0]
        self.assertEqual(html["mimeType"], "text/html;profile=mcp-app")
        self.assertTrue(UI_PATH.is_file())

    def test_ui_has_theme_accessibility_and_safe_dom_rendering(self):
        html = UI_PATH.read_text(encoding="utf-8")
        self.assertIn("prefers-color-scheme: dark", html)
        self.assertIn("forced-colors: active", html)
        self.assertIn("aria-live", html)
        self.assertIn("aria-label", html)
        self.assertIn("textContent", html)
        self.assertIn("ui/notifications/tool-result", html)
        self.assertNotIn("localStorage", html)
        self.assertNotIn("fetch(", html)

    def test_stdio_protocol_round_trip_returns_view_and_fallback(self):
        request_lines = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "render_consultation_dashboard",
                "arguments": {"receipt_json": json.dumps(make_route(), sort_keys=True)},
            }},
        ]
        process = subprocess.run(
            [sys.executable, str(HERE / "consultation_dashboard_mcp.py")],
            input="\n".join(json.dumps(item) for item in request_lines) + "\n",
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        responses = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([item["id"] for item in responses], [1, 2, 3])
        tool_result = responses[2]["result"]
        validate_obj("consultation-dashboard-view", tool_result["structuredContent"])
        self.assertIn("FreeMovement — Consultation Review", tool_result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
