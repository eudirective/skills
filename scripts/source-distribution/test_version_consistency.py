"""Synthetic build and metadata consistency regressions."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build import choose_component_versions, fingerprint_inputs, update_plugin_version
from validate_versions import VersionValidationError, fingerprint, validate_distribution


CORE_NAME = "freemovement-law"
CORE_VERSION = "1.2.3"
CORE_SKILLS = {
    "eudirective-core": "0.9.1",
    "eudirective-source-library": "0.2.0",
    "eudirective-ac-turkiye": "0.3.0",
}
UPSTREAM = {"source-library": "a" * 40, "module-notes": "b" * 40}
COMPATIBILITY = {"contract": "1.0"}
CORE_PACK_VERSION = "0.8.0"


def json_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_package(root: Path, directory: str, name: str, component_id: str,
                 plugin_version: str, skill_versions: dict[str, str], core: bool) -> dict:
    package = root / directory
    json_write(package / "plugin.json", {"name": name, "version": plugin_version})
    json_write(package / ".codex-plugin/plugin.json", {"name": name, "version": plugin_version})
    if core:
        core_skill = package / "skills/eudirective-core/SKILL.md"
        core_skill.parent.mkdir(parents=True)
        core_skill.write_text(
            f"- Current version: `{skill_versions['eudirective-core']}`\n"
            f"- Plugin version: `{plugin_version}`\n"
            "Read the installed manifest and use its `skill_versions.eudirective-core` value.\n",
            encoding="utf-8",
        )
        source_skill = package / "skills/eudirective-source-library/SKILL.md"
        source_skill.parent.mkdir(parents=True)
        source_skill.write_text(f"**Skill version:** {skill_versions['eudirective-source-library']}\n", encoding="utf-8")
        tr_skill = package / "skills/eudirective-ac-turkiye/SKILL.md"
        tr_skill.parent.mkdir(parents=True)
        tr_skill.write_text(
            f"- Current version: `{skill_versions['eudirective-ac-turkiye']}`\n"
            "Read the manifest `skill_versions.eudirective-ac-turkiye`.\n", encoding="utf-8")
        json_write(package / "skills/eudirective-core/references/source-library/core-source-pack-manifest-0.8.0.json",
                   {"pack_name": "eudirective-core-source-pack", "pack_version": CORE_PACK_VERSION})
        json_write(package / "skills/eudirective-core/references/session-version-manifest.json", {
            "schema_version": 1,
            "plugin": {"name": name, "version": plugin_version},
            "skills": skill_versions,
            "library": {"core_pack_version": CORE_PACK_VERSION, "tree_sha": UPSTREAM["source-library"],
                        "module_notes_tree_sha": UPSTREAM["module-notes"], "repository": "eudirective/public-data",
                        "path": "source-library", "module_notes_path": "module-notes"},
        })
    else:
        skill = next(iter(skill_versions))
        skill_path = package / f"skills/{skill}/SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("Read the installed package component manifest.\n", encoding="utf-8")

    manifest_path = (package / "skills/eudirective-core/references/component-manifest.json" if core else
                     package / f"skills/{next(iter(skill_versions))}/references/component-manifest.json")
    compatibility = COMPATIBILITY
    input_files = {f"skill-template/{key}": "d" * 64 for key in skill_versions}
    input_files["synthetic-input"] = "e" * 64
    manifest = {
        "schema_version": "1.0.0", "component_id": component_id, "plugin_version": plugin_version,
        "skill_versions": skill_versions, "skill_fingerprints": {key: "d" * 64 for key in skill_versions},
        "source_contract_version": "1.0.0", "compatibility": compatibility,
        "upstream_trees": UPSTREAM, "upstream_revision": "test-upstream",
        "input_files": input_files, "input_fingerprint": fingerprint(input_files),
    }
    files = {p.relative_to(package).as_posix(): sha256(p) for p in sorted(package.rglob("*"))
             if p.is_file() and p != manifest_path}
    manifest["distributed_files"] = files
    manifest["distributed_fingerprint"] = fingerprint(files)
    json_write(manifest_path, manifest)
    return manifest


class VersionConsistencyTests(unittest.TestCase):
    def make_distribution(self, root: Path) -> tuple[Path, Path]:
        registry_path = root / "registry.json"
        registry = {
            "core_plugin": CORE_NAME,
            "additional_operational_modules": [{
                "plugin_name": CORE_NAME, "skill_directory": "skills/eudirective-ac-turkiye",
            }],
            "countries": [{
                "iso_country_code": "NL", "plugin_name": "fm-netherlands",
                "plugin_directory": "freemovement-law-nl", "skill_name": "eudirective-library-nl",
                "verification_profile": "national_source_review", "related_operational_modules": [],
                "core_compatibility_contract": COMPATIBILITY,
            }],
            "core_compatibility_contract": COMPATIBILITY,
        }
        json_write(registry_path, registry)
        core = make_package(root, CORE_NAME, CORE_NAME, "eu-core", CORE_VERSION, CORE_SKILLS, True)
        country = make_package(root, "freemovement-law-nl", "fm-netherlands", "NL", "0.4.1",
                               {"eudirective-library-nl": "0.2.2"}, False)
        components = []
        for name, directory, component_id, manifest, profile in (
            (CORE_NAME, CORE_NAME, "eu-core", core, "eu_core"),
            ("fm-netherlands", "freemovement-law-nl", "NL", country, "national_source_review"),
        ):
            components.append({
                "plugin_name": name, "package_directory": directory, "component_id": component_id,
                "plugin_version": manifest["plugin_version"], "skill_versions": manifest["skill_versions"],
                "source_contract_version": manifest["source_contract_version"],
                "input_fingerprint": manifest["input_fingerprint"],
                "distributed_fingerprint": manifest["distributed_fingerprint"],
                "compatibility": manifest["compatibility"], "verification_profile": profile,
            })
        json_write(root / "component-index.json", {
            "schema_version": "1.0.0", "source_repository": "eudirective/public-data",
            "upstream_revision": "test-upstream", "upstream_trees": UPSTREAM, "components": components,
        })
        return root, registry_path

    def refresh_component(self, root: Path, directory: str, skill: str | None = None) -> None:
        package = root / directory
        manifest_path = (package / "skills/eudirective-core/references/component-manifest.json" if skill is None else
                         package / f"skills/{skill}/references/component-manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["distributed_files"] = {
            p.relative_to(package).as_posix(): sha256(p) for p in sorted(package.rglob("*"))
            if p.is_file() and p != manifest_path
        }
        manifest["distributed_fingerprint"] = fingerprint(manifest["distributed_files"])
        json_write(manifest_path, manifest)
        index_path = root / "component-index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        row = next(item for item in index["components"] if item["package_directory"] == directory)
        row["distributed_fingerprint"] = manifest["distributed_fingerprint"]
        json_write(index_path, index)

    def test_complete_synthetic_core_and_country_inventory_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, registry = self.make_distribution(Path(temporary))
            self.assertEqual(validate_distribution(root, registry), {"components": 2, "countries": 1})

    def test_stale_self_disclosure_fails_even_when_hashes_are_refreshed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, registry = self.make_distribution(Path(temporary))
            skill = root / CORE_NAME / "skills/eudirective-core/SKILL.md"
            skill.write_text(skill.read_text() + "Skill: eudirective-core v9.9.9\n", encoding="utf-8")
            self.refresh_component(root, CORE_NAME)
            with self.assertRaisesRegex(VersionValidationError, "Stale self-disclosure"):
                validate_distribution(root, registry)

    def test_plugin_manifest_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, registry = self.make_distribution(Path(temporary))
            path = root / "freemovement-law-nl/plugin.json"
            json_write(path, {"name": "fm-netherlands", "version": "0.4.0"})
            with self.assertRaisesRegex(VersionValidationError, "Plugin version differs in plugin.json"):
                validate_distribution(root, registry)

    def test_core_session_version_manifest_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, registry = self.make_distribution(Path(temporary))
            path = root / CORE_NAME / "skills/eudirective-core/references/session-version-manifest.json"
            session = json.loads(path.read_text(encoding="utf-8"))
            session["plugin"]["version"] = "1.2.2"
            json_write(path, session)
            self.refresh_component(root, CORE_NAME)
            with self.assertRaisesRegex(VersionValidationError, "Session-version manifest plugin version"):
                validate_distribution(root, registry)

    def test_a_changed_component_input_cannot_keep_the_old_version(self):
        old_inputs = {"country": "same", "source": "old"}
        new_inputs = {"country": "same", "source": "new"}
        selected, selected_skills = choose_component_versions(
            {"plugin_version": "0.4.1", "input_fingerprint": fingerprint_inputs(old_inputs),
             "skill_versions": {"eudirective-library-nl": "0.2.2"},
             "skill_fingerprints": {"eudirective-library-nl": "e" * 64}},
            fingerprint_inputs(new_inputs), {"eudirective-library-nl": "e" * 64},
            "0.1.0", {"eudirective-library-nl": "0.1.0"})
        self.assertEqual(selected, "0.4.2")
        self.assertEqual(selected_skills["eudirective-library-nl"], "0.2.2")

    def test_core_version_update_stamps_the_session_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary)
            json_write(package / "plugin.json", {"name": CORE_NAME, "version": "1.0.0"})
            json_write(package / ".codex-plugin/plugin.json", {"name": CORE_NAME, "version": "1.0.0"})
            skill = package / "skills/eudirective-core/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("- Current version: `0.1.0`\n- Plugin version: `1.0.0`\n"
                             "Read installed manifest `skill_versions.eudirective-core`.\n", encoding="utf-8")
            session_path = package / "skills/eudirective-core/references/session-version-manifest.json"
            json_write(session_path, {"schema_version": 1, "plugin": {"name": CORE_NAME, "version": "1.0.0"},
                                      "skills": CORE_SKILLS, "library": {}})
            update_plugin_version(package, "1.0.1", {**CORE_SKILLS, "eudirective-core": "0.9.2"},
                                  UPSTREAM, CORE_PACK_VERSION)
            session = json.loads(session_path.read_text(encoding="utf-8"))
            self.assertEqual(session["plugin"]["version"], "1.0.1")
            self.assertEqual(session["skills"]["eudirective-core"], "0.9.2")


if __name__ == "__main__":
    unittest.main()
