#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "references" / "contracts"
MAX_BYTES = 2_000_000
MAX_DEPTH = 24
FORBIDDEN_KEYS = {"command", "callback", "python", "shell", "eval", "exec", "import", "executable", "code"}

class ContractError(Exception):
    pass

def reject_constant(value):
    raise ContractError(f"non-finite numeric constant is not allowed: {value}")

def no_duplicates(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ContractError(f"duplicate JSON key: {k}")
        out[k] = v
    return out

def load_json(path: Path, *, allow_internal_issue_code=False):
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise ContractError(f"input exceeds {MAX_BYTES} bytes")
    try:
        obj = json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicates, parse_constant=reject_constant)
    except UnicodeDecodeError as e:
        raise ContractError(f"input is not UTF-8: {e}")
    except json.JSONDecodeError as e:
        raise ContractError(f"invalid JSON: {e}")
    inspect_value(obj, allow_internal_issue_code=allow_internal_issue_code)
    return obj

def inspect_value(value, depth=0, *, allow_internal_issue_code=False, path=()):
    if depth > MAX_DEPTH:
        raise ContractError(f"JSON nesting exceeds {MAX_DEPTH}")
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                # Only typed, locally created stage issue records may carry a
                # non-executable 'code' string. Never enable for outside input.
                if not (allow_internal_issue_code and key == 'code' and
                        ((len(path) == 2 and path[0] == 'unresolved' and isinstance(path[1], int)) or
                         (len(path) == 3 and path[0] == 'issues' and isinstance(path[1], int) and path[2] == 'value')) and
                        isinstance(child, str) and re.fullmatch(r'[A-Za-z0-9_:-]{1,160}', child)):
                    raise ContractError(f"forbidden executable-style key: {key}")
            inspect_value(child, depth + 1, allow_internal_issue_code=allow_internal_issue_code,
                          path=path + (key,))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            inspect_value(child, depth + 1, allow_internal_issue_code=allow_internal_issue_code,
                          path=path + (i,))
    elif isinstance(value, float) and not math.isfinite(value):
        raise ContractError("non-finite numbers are not allowed")

def schema_names():
    return sorted(p.name[:-12] for p in SCHEMA_DIR.glob("*.schema.json"))

def load_schema(name):
    p = SCHEMA_DIR / f"{name}.schema.json"
    if not p.is_file():
        raise ContractError(f"unknown schema {name}; choose one of: {', '.join(schema_names())}")
    return json.loads(p.read_text(encoding="utf-8"))

def validate_obj(name, obj):
    schema = load_schema(name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(obj), key=lambda e: list(e.absolute_path))
    if errors:
        rendered = []
        for err in errors[:25]:
            where = "/".join(str(x) for x in err.absolute_path) or "$"
            rendered.append(f"{where}: {err.message}")
        extra = "" if len(errors) <= 25 else f" (+{len(errors)-25} more)"
        raise ContractError("schema validation failed: " + "; ".join(rendered) + extra)
    return True

def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def digest_obj(obj):
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()

def main():
    ap = argparse.ArgumentParser(description="Validate eudirective-core JSON contracts")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--schema")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.list:
        print("\n".join(schema_names()))
        return 0
    if not args.path or not args.schema:
        ap.error("--schema and path are required unless --list is used")
    try:
        obj = load_json(Path(args.path))
        validate_obj(args.schema, obj)
        print(json.dumps({"status":"valid","schema":args.schema,"sha256":digest_obj(obj)}, sort_keys=True))
        return 0
    except (ContractError, OSError) as e:
        print(json.dumps({"status":"invalid","error":str(e)}, sort_keys=True), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
