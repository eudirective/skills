from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parent.parent


def module_notes_root():
    for library in (
        PLUGIN_ROOT / "data" / "eudirective-source-library-0.6.0",
        PLUGIN_ROOT / "source-runtime" / "eudirective-source-library-0.6.0",
        PLUGIN_ROOT.parent.parent.parent / "eudirective-source-library-0.6.0",
    ):
        notes = library / "sweden" / "module-notes" / "source-notes"
        if notes.is_dir():
            return notes
    raise FileNotFoundError("Sweden module notes are missing from the eudirective source library.")
