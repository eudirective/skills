"""Read Austria's indexed raw captures from the monitor's local-only archive.

The repository keeps logical capture references in its ledgers, but never keeps
raw response bytes under the country pack. This resolver accepts those historic
references and verifies archive entries before returning their local path.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def archive_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if not codex_home:
        raise FileNotFoundError("CODEX_HOME is not set; Austria captures are available only in the monitor's local archive")
    root = Path(codex_home).expanduser() / "plugins" / "data" / "eu-source-update-monitor" / "local-research"
    if not (root / "index.json").is_file():
        raise FileNotFoundError(f"Monitor local research archive index not found: {root / 'index.json'}")
    return root.resolve()


def _entries() -> tuple[Path, list[dict]]:
    root = archive_root()
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    entries = [
        entry for entry in index.get("entries", [])
        if entry.get("classification") == "captures"
        and entry.get("jurisdiction") == "austria"
        and entry.get("origin") == "public-data"
        and entry.get("local_only") is True
    ]
    return root, entries


def _entry_for(value: str) -> tuple[Path, dict] | None:
    root, entries = _entries()
    reference = value.replace("\\", "/")

    if reference.startswith("captures/public-data/austria/"):
        matches = [entry for entry in entries if entry.get("archive_path") == reference]
    else:
        original = None
        if reference.startswith("source-library/austria/captures/"):
            original = reference.removeprefix("source-library/")
        elif reference.startswith("captures/"):
            original = "austria/" + reference
        elif reference.startswith("austria/captures/"):
            original = reference

        if original:
            matches = [entry for entry in entries if entry.get("original_path") == original]
        else:
            name = Path(reference).name
            matches = [entry for entry in entries if Path(entry.get("archive_path", "")).name == name]

    if len(matches) != 1:
        if not matches:
            return None
        raise ValueError(f"Capture reference is ambiguous in the monitor archive: {value}")
    return root, matches[0]


def resolve_capture(value: str | Path) -> Path | None:
    """Return a verified archive file for a known capture reference."""
    reference = str(value)
    path = Path(reference)
    if path.is_absolute():
        try:
            reference = path.resolve().relative_to(archive_root()).as_posix()
        except ValueError:
            return None

    found = _entry_for(reference)
    if not found:
        return None
    root, entry = found
    archived = (root / entry["archive_path"]).resolve()
    try:
        archived.relative_to(root)
    except ValueError as exc:
        raise ValueError("Archive index path escapes the monitor archive") from exc
    data = archived.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != entry.get("bytes") or digest != entry.get("sha256"):
        raise ValueError(f"Archived capture does not match its index: {entry['archive_path']}")
    return archived


def find_capture(pattern: str) -> Path:
    """Find one archived capture by filename glob and verify it against index."""
    from fnmatch import fnmatch

    root, entries = _entries()
    matches = [entry for entry in entries if fnmatch(Path(entry.get("archive_path", "")).name, pattern)]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one archived Austria capture matching {pattern!r}; found {len(matches)}")
    resolved = resolve_capture(matches[0]["archive_path"])
    if resolved is None:
        raise FileNotFoundError(matches[0]["archive_path"])
    return resolved


def archive_reference(value: str | Path) -> str:
    """Return the indexed archive-relative path for a capture file/reference."""
    reference = str(value)
    if Path(reference).is_absolute():
        root = archive_root()
        reference = Path(reference).resolve().relative_to(root).as_posix()
    found = _entry_for(reference)
    if not found:
        raise FileNotFoundError(f"Capture is not indexed in the monitor archive: {value}")
    return found[1]["archive_path"]
