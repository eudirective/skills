"""Resolve core sources and country-owned module packages from the generated registry."""
from __future__ import annotations
import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parent.parent
LIBRARY_ROOT = SKILL_ROOT / "references" / "source-library"
ROUTING_PATH = SKILL_ROOT / "references" / "national-source-routing.json"

def source_library_root() -> Path:
    if LIBRARY_ROOT.is_dir():
        return LIBRARY_ROOT
    raise FileNotFoundError("The core EU source corpus is missing.")

def compatibility_root() -> Path:
    root = SKILL_ROOT / "tests" / "fixtures" / "core-source-pack-0.6.1"
    if (root / "core-source-pack-manifest-0.6.1.json").is_file():
        return root
    raise FileNotFoundError("The pinned core compatibility fixture is missing.")

def source_library_candidates() -> list[Path]:
    return [source_library_root()]

def compatibility_sources_root() -> Path:
    root = compatibility_root() / "sources"
    if not root.is_dir():
        raise FileNotFoundError("The pinned core source representations are missing.")
    return root

def routing_registry() -> dict:
    data = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("operational_modules"), list):
        raise ValueError("Generated operational module registry is malformed.")
    return data

def country_plugin_root(country: str) -> Path:
    data = routing_registry()
    row = next((item for item in data["countries"] if item["source_library_directory"] == country or item["iso_country_code"].lower() == country.lower()), None)
    if row is None:
        raise ValueError(f"Country is not registered: {country}")
    root = PLUGIN_ROOT.parent / row["plugin_name"]
    if root.is_dir():
        return root
    raise FileNotFoundError(f"Country plugin is not available beside the core package: {row['plugin_name']}")

def module_skill_root(module_id: str) -> Path:
    data = routing_registry()
    row = next((item for item in data["operational_modules"] if item["module_id"] == module_id), None)
    if row is None:
        raise ValueError(f"Operational module is not registered: {module_id}")
    package = PLUGIN_ROOT if row["plugin_name"] == data["core_plugin"] else PLUGIN_ROOT.parent / row["plugin_name"]
    root = package / row["skill_directory"]
    if not root.is_dir():
        raise FileNotFoundError(f"Registered module package is unavailable: {row['plugin_name']} / {row['skill_directory']}")
    return root

def module_record(module_id: str) -> dict:
    data = routing_registry()
    row = next((item for item in data["operational_modules"] if item["module_id"] == module_id), None)
    if row is None:
        raise ValueError(f"Operational module is not registered: {module_id}")
    return row

def module_record_for_root(module_root: Path) -> dict:
    root = module_root.resolve()
    for row in routing_registry()["operational_modules"]:
        package = PLUGIN_ROOT if row["plugin_name"] == routing_registry()["core_plugin"] else PLUGIN_ROOT.parent / row["plugin_name"]
        if (package / row["skill_directory"]).resolve() == root:
            return row
    raise ValueError(f"Module package is not registered: {module_root}")

def module_skill_for(jurisdiction: str, module_family: str) -> Path:
    matches = [row for row in routing_registry()["operational_modules"]
               if row["jurisdiction"] == jurisdiction.upper() and row["module_family"] == module_family]
    if len(matches) != 1:
        raise ValueError(f"Expected one registered {module_family} module for {jurisdiction}; found {len(matches)}")
    return module_skill_root(matches[0]["module_id"])

def operational_module_roots() -> list[Path]:
    rows = routing_registry()["operational_modules"]
    roots = [module_skill_root(row["module_id"]) for row in rows]
    return roots

def module_notes_root(country: str, module_id: str | None = None) -> Path:
    data = routing_registry()
    modules = data["operational_modules"]
    module = next((item for item in modules if item["module_id"] == module_id), None) if module_id else None
    if module_id and module is None:
        raise ValueError(f"Operational module is not registered for module notes: {module_id}")
    row = next((item for item in data["countries"]
                if item["source_library_directory"] == country or item["iso_country_code"].lower() == country.lower()), None)
    if not module and not row:
        matching_modules = [item for item in modules if item["notes_directory"] == country]
        if len(matching_modules) == 1:
            module = matching_modules[0]
    notes_directory = module["notes_directory"] if module else (row["source_library_directory"] if row else None)
    if notes_directory is None:
        raise ValueError(f"Country is not registered for module notes: {country}")
    owner = module.get("notes_plugin_name", module["plugin_name"]) if module else next(
        (item["plugin_name"] for item in data["module_notes_ownership"] if item["notes_directory"] == notes_directory),
        row["plugin_name"] if row else None,
    )
    if owner is None:
        raise ValueError(f"Module-note owner is not registered: {notes_directory}")
    package = PLUGIN_ROOT if owner == data["core_plugin"] else PLUGIN_ROOT.parent / owner
    library = package / "skills" / "eudirective-core" / "references" / "source-library" if owner == data["core_plugin"] else package / "references" / "source-library"
    root = library / "module-notes" / notes_directory
    if root.is_dir():
        return root
    raise FileNotFoundError(f"Registered module notes are not available: {notes_directory}")
