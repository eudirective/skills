from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parent.parent
LIBRARY_ROOT = PLUGIN_ROOT / "skills" / "eudirective-source-library"


def module_notes_root():
    notes = LIBRARY_ROOT / "sweden" / "module-notes" / "source-notes"
    if notes.is_dir():
        return notes
    raise FileNotFoundError("Sweden module notes are missing from the bundled eudirective source library.")
