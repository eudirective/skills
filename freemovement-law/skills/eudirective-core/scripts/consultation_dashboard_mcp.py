#!/usr/bin/env python3
"""Local, read-only MCP adapter for validated consultation dashboard rendering.

The server accepts only a privacy-minimised route receipt. It does not access
the network, persist inputs, or log request contents. It cannot intercept or
block the host's final response.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from consultation_route_gate import validate_route
from contract_validate import load_json

ROOT = Path(__file__).resolve().parents[1]
UI_URI = "ui://freemovement-law/consultation-dashboard/v1.html"
UI_PATH = ROOT / "ui" / "consultation-dashboard-v1.html"
MAX_RECEIPT_BYTES = 2_000_000
MAX_ARTIFACT_BYTES = 1_000_000
MAX_ARTIFACT_TOTAL_BYTES = 2_000_000


def _write(message: dict) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":"), ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _tool_definition() -> dict:
    output_schema = json.loads(
        (ROOT / "references" / "contracts" / "consultation-dashboard-view.schema.json")
        .read_text(encoding="utf-8")
    )
    return {
        "name": "render_consultation_dashboard",
        "title": "Validate and render consultation dashboard",
        "description": (
            "Use after substantive FreeMovement guidance when the skill requires a dashboard. "
            "Pass the privacy-minimised consultation route receipt JSON and, when referenced, only generalized "
            "non-identifying research plan/bundle JSON files. Never pass an applicant narrative, identity, "
            "case number, document text, or unredacted private evidence. The local read-only tool "
            "validates the declared receipt and returns an accessible visual board plus a Markdown fallback. "
            "It does not authenticate model-reported work or block the final chat response."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["receipt_json"],
            "properties": {
                "receipt_json": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": MAX_RECEIPT_BYTES,
                    "description": "JSON for consultation-route-receipt schema 0.2.0; no narrative or personal data.",
                },
                "artifact_files": {
                    "type": "array",
                    "maxItems": 60,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["relative_path", "json_content"],
                        "properties": {
                            "relative_path": {"type": "string", "maxLength": 300},
                            "json_content": {"type": "string", "maxLength": MAX_ARTIFACT_BYTES},
                        },
                    },
                    "description": "Optional generalized research files referenced by receipt paths; no case facts or personal data.",
                },
            },
        },
        "outputSchema": output_schema,
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        },
        "_meta": {
            "ui": {
                "resourceUri": UI_URI,
                "prefersBorder": True,
                "csp": {},
            }
        },
    }


def _materialize_artifact_files(base: Path, receipt: dict, artifact_files: list[dict] | None) -> None:
    files = artifact_files or []
    if not isinstance(files, list) or len(files) > 60:
        raise ValueError("artifact_files_invalid")
    referenced: set[str] = set()
    for artifact in receipt.get("research_artifacts", []):
        referenced.add(artifact["plan_path"])
        referenced.add(artifact["bundle_path"])
        if artifact.get("preflight_path"):
            referenced.add(artifact["preflight_path"])
    seen: set[str] = set()
    total_bytes = 0
    root = base.resolve()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("artifact_file_invalid")
        relative_path = item.get("relative_path")
        content = item.get("json_content")
        if not isinstance(relative_path, str) or relative_path not in referenced:
            raise ValueError("artifact_file_not_referenced")
        if relative_path in seen:
            raise ValueError("artifact_file_duplicate")
        seen.add(relative_path)
        candidate = Path(relative_path)
        if (candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts
                or "\\" in relative_path or candidate.suffix.casefold() != ".json"):
            raise ValueError("artifact_file_path_invalid")
        resolved = (root / candidate).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as error:
            raise ValueError("artifact_file_path_invalid") from error
        if not isinstance(content, str):
            raise ValueError("artifact_file_content_invalid")
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_ARTIFACT_BYTES:
            raise ValueError("artifact_file_too_large")
        total_bytes += len(encoded)
        if total_bytes > MAX_ARTIFACT_TOTAL_BYTES:
            raise ValueError("artifact_files_too_large")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_bytes(encoded)
        # Apply the same strict JSON parser before the existing research gate.
        load_json(resolved)


def _render(arguments: dict) -> dict:
    raw = arguments.get("receipt_json")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("receipt_json_required")
    encoded = raw.encode("utf-8")
    if len(encoded) > MAX_RECEIPT_BYTES:
        raise ValueError("receipt_json_too_large")
    with tempfile.TemporaryDirectory(prefix="freemovement-dashboard-") as temp_dir:
        receipt_path = Path(temp_dir) / "route-receipt.json"
        receipt_path.write_bytes(encoded)
        # Reuse the shared strict JSON loader before the path-based route gate.
        # Writing canonical JSON also eliminates ambiguous duplicate keys.
        receipt = load_json(receipt_path)
        _materialize_artifact_files(Path(temp_dir), receipt, arguments.get("artifact_files"))
        receipt_path.write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            encoding="utf-8",
        )
        result = validate_route(receipt_path)
    view_model = result.get("dashboard_view_model")
    if not result.get("dashboard_required") or not isinstance(view_model, dict):
        raise ValueError("dashboard_not_required_or_not_produced")
    return {
        "structuredContent": view_model,
        "content": [{"type": "text", "text": view_model.get("text_fallback") or "Dashboard rendered."}],
        "isError": False,
    }


def _resource_read(uri: str) -> dict:
    if uri != UI_URI:
        raise ValueError("resource_not_found")
    return {
        "contents": [{
            "uri": UI_URI,
            "mimeType": "text/html;profile=mcp-app",
            "text": UI_PATH.read_text(encoding="utf-8"),
            "_meta": {"ui": {"prefersBorder": True, "csp": {}}},
        }]
    }


def _dispatch(request: dict) -> dict | None:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}
    if method in {"initialize", "ping", "tools/list", "tools/call", "resources/list", "resources/read"} and request_id is None:
        return None
    if not isinstance(params, dict):
        if request_id is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32602, "message": "invalid_params"}}
    if method == "notifications/initialized" or method == "notifications/cancelled":
        return None
    if method == "ping":
        result = {}
    elif method == "initialize":
        result = {
            "protocolVersion": params.get("protocolVersion", "2025-11-25"),
            "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}},
            "serverInfo": {"name": "freemovement-dashboard", "version": "1.0.0"},
            "instructions": (
                "Call render_consultation_dashboard with only a privacy-minimised receipt. "
                "The tool is read-only and local; it cannot gate ordinary host output."
            ),
        }
    elif method == "tools/list":
        result = {"tools": [_tool_definition()]}
    elif method == "resources/list":
        result = {"resources": [{
            "uri": UI_URI,
            "name": "FreeMovement consultation dashboard",
            "mimeType": "text/html;profile=mcp-app",
            "description": "Accessible status cards, declared-work progress, and open items.",
        }]}
    elif method == "resources/read":
        try:
            result = _resource_read(params.get("uri", ""))
        except (OSError, ValueError) as error:
            result = None
            rpc_error = {"code": -32002, "message": str(error)}
            return {"jsonrpc": "2.0", "id": request_id, "error": rpc_error}
    elif method == "tools/call":
        if params.get("name") != "render_consultation_dashboard":
            return {"jsonrpc": "2.0", "id": request_id,
                    "error": {"code": -32602, "message": "tool_not_found"}}
        try:
            result = _render(params.get("arguments") or {})
        except Exception as error:  # Return a safe tool error; never log receipt content.
            return {"jsonrpc": "2.0", "id": request_id, "result": {
                "content": [{"type": "text", "text": f"Dashboard not rendered: {error}"}],
                "isError": True,
            }}
    else:
        if request_id is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32601, "message": "method_not_found"}}

    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> int:
    for raw_line in sys.stdin.buffer:
        try:
            request = json.loads(raw_line.decode("utf-8"))
            response = _dispatch(request)
            if response is not None:
                _write(response)
        except (UnicodeDecodeError, json.JSONDecodeError):
            _write({"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700, "message": "parse_error"}})
        except Exception:
            _write({"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32603, "message": "internal_error"}})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
