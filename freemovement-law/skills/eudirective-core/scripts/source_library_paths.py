"""Resolve packaged source-library data and the pinned compatibility snapshot."""
from __future__ import annotations

from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parent.parent


def source_library_root() -> Path:
    candidates = [
        PLUGIN_ROOT / "data" / "eudirective-source-library-0.6.0",
        PLUGIN_ROOT / "source-runtime" / "eudirective-source-library-0.6.0",
        PLUGIN_ROOT.parent.parent.parent / "eudirective-source-library-0.6.0",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("The eudirective source library is not present in this plugin installation.")


def compatibility_root() -> Path:
    for library in source_library_candidates():
        root = library / "compatibility" / "core-source-pack" / "core-source-pack-0.6.1"
        if (root / "core-source-pack-manifest-0.6.1.json").is_file():
            return root
    raise FileNotFoundError("The pinned core compatibility snapshot is missing from the source library.")


def source_library_candidates() -> list[Path]:
    return [
        PLUGIN_ROOT / "data" / "eudirective-source-library-0.6.0",
        PLUGIN_ROOT / "source-runtime" / "eudirective-source-library-0.6.0",
        PLUGIN_ROOT.parent.parent.parent / "eudirective-source-library-0.6.0",
    ]


def compatibility_sources_root() -> Path:
    root = compatibility_root() / "sources"
    if not root.is_dir():
        raise FileNotFoundError("The pinned core source representations are missing from the source library.")
    return root


def module_notes_root(country: str) -> Path:
    if country not in {"sweden", "turkiye"}:
        raise ValueError("Unsupported country module.")
    for library in source_library_candidates():
        root = library / country / "module-notes" / "source-notes"
        if root.is_dir():
            return root
    raise FileNotFoundError(f"The {country} module notes are missing from the source library.")
