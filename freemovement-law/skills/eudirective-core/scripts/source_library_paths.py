"""Resolve the externally maintained source library bundled with the plugin."""
from __future__ import annotations

from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parent.parent
LIBRARY_ROOT = PLUGIN_ROOT / "skills" / "eudirective-source-library"


def source_library_root() -> Path:
    if LIBRARY_ROOT.is_dir():
        return LIBRARY_ROOT
    raise FileNotFoundError("The bundled eudirective source library is missing.")


def compatibility_root() -> Path:
    root = source_library_root() / "compatibility" / "core-source-pack" / "core-source-pack-0.6.1"
    if (root / "core-source-pack-manifest-0.6.1.json").is_file():
        return root
    raise FileNotFoundError("The pinned core compatibility snapshot is missing from the bundled source library.")


def source_library_candidates() -> list[Path]:
    return [source_library_root()]


def compatibility_sources_root() -> Path:
    root = compatibility_root() / "sources"
    if not root.is_dir():
        raise FileNotFoundError("The pinned core source representations are missing from the source library.")
    return root


def module_notes_root(country: str) -> Path:
    if country not in {"sweden", "turkiye"}:
        raise ValueError("Unsupported country module.")
    root = source_library_root() / country / "module-notes" / "source-notes"
    if root.is_dir():
        return root
    raise FileNotFoundError(f"The {country} module notes are missing from the source library.")
