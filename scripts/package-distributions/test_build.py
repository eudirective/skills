#!/usr/bin/env python3
"""Unit tests for registered plugin archive discovery and packaging."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from build import (
    PackageBuildError,
    SOURCE_LICENCE_FILES,
    build_distributions,
    build_plugin_archives,
    discover_plugins,
    verify_distribution,
)


class PluginArchiveBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="package-distributions-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.output = Path(self.temp.name) / "out"
        self.write_marketplace([
            {"name": "freemovement-law", "path": "freemovement-law", "version": "1.2.3"},
            {"name": "fm-test", "path": "country-plugin", "version": "0.1.4"},
        ])

    def write_marketplace(self, plugins: list[dict[str, str]]) -> None:
        entries = []
        (self.root / "LICENCE.md").write_text("Synthetic EPIL\n", encoding="utf-8")
        for plugin in plugins:
            plugin_root = self.root / plugin["path"]
            skills = plugin_root / "skills" / f"{plugin['name']}-skill"
            skills.mkdir(parents=True, exist_ok=True)
            (plugin_root / ".codex-plugin").mkdir(parents=True, exist_ok=True)
            metadata = {"name": plugin["name"], "version": plugin["version"]}
            (plugin_root / "plugin.json").write_text(json.dumps(metadata), encoding="utf-8")
            codex_metadata = {**metadata, "skills": "./skills"}
            (plugin_root / ".codex-plugin" / "plugin.json").write_text(
                json.dumps(codex_metadata), encoding="utf-8"
            )
            (plugin_root / "README.md").write_text(f"{plugin['name']} package\n", encoding="utf-8")
            (skills / "SKILL.md").write_text(f"# {plugin['name']}\n", encoding="utf-8")
            (plugin_root / "references").mkdir(exist_ok=True)
            (plugin_root / "references" / "source.json").write_text('{"complete":true}\n', encoding="utf-8")
            source_library = plugin_root / "references" / "source-library"
            source_library.mkdir(parents=True, exist_ok=True)
            (source_library / "source.md").write_text(f"source for {plugin['name']}\n", encoding="utf-8")
            (plugin_root / "LICENCE.md").write_bytes((self.root / "LICENCE.md").read_bytes())
            (plugin_root / "SOURCE-LIBRARY-NOTICE.md").write_text("Source revision test-revision\n", encoding="utf-8")
            for name in SOURCE_LICENCE_FILES:
                destination = source_library / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(f"Test {name}\n", encoding="utf-8")
            entries.append({
                "name": plugin["name"],
                "source": {"source": "local", "path": f"./{plugin['path']}"},
            })
        (self.root / "marketplace.json").write_text(
            json.dumps({"name": "test", "plugins": entries}, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.root / "component-index.json").write_text(json.dumps({
            "components": [
                {"plugin_name": item["name"], "plugin_version": item["version"],
                 "package_directory": item["path"]}
                for item in plugins
            ],
            "upstream_revision": "test-revision",
        }), encoding="utf-8")
        (self.root / "source-inventory.json").write_text(json.dumps([{
            "source_path": "source.md", "classification": "accepted_national_source_text",
            "distribution_action": "distributed_to_country_plugin", "bytes": 1, "sha256": "0" * 64,
        }]), encoding="utf-8")
        (self.root / "migration-map.json").write_text("[]\n", encoding="utf-8")

    def test_discovers_all_marketplace_entries_and_validates_mirrored_metadata(self) -> None:
        plugins = discover_plugins(self.root)
        self.assertEqual([(item.name, item.version) for item in plugins], [
            ("fm-test", "0.1.4"),
            ("freemovement-law", "1.2.3"),
        ])

    def test_builds_complete_archives_and_checks_zip_integrity(self) -> None:
        archives = build_plugin_archives(self.root, self.output)
        self.assertEqual([item.path.name for item in archives], [
            "fm-test-0.1.4.zip",
            "freemovement-law-1.2.3.zip",
        ])
        for result in archives:
            registered_path = next(
                row["source"]["path"][2:]
                for row in json.loads((self.root / "marketplace.json").read_text())["plugins"]
                if row["name"] == result.name
            )
            archive_root = Path(registered_path).name
            plugin_root = self.root / next(
                row["source"]["path"][2:]
                for row in json.loads((self.root / "marketplace.json").read_text())["plugins"]
                if row["name"] == result.name
            )
            expected_entries = {f"{archive_root}/"}
            expected_entries.update(
                f"{archive_root}/{path.relative_to(plugin_root).as_posix()}{'/' if path.is_dir() else ''}"
                for path in plugin_root.rglob("*")
            )
            with zipfile.ZipFile(result.path) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), expected_entries)
                self.assertIn(f"{archive_root}/plugin.json", archive.namelist())
                self.assertIn(f"{archive_root}/.codex-plugin/plugin.json", archive.namelist())
                self.assertIn(f"{archive_root}/skills/{result.name}-skill/SKILL.md", archive.namelist())
                self.assertIn(f"{archive_root}/LICENCE.md", archive.namelist())
                self.assertIn(f"{archive_root}/SOURCE-LIBRARY-NOTICE.md", archive.namelist())
                for name in SOURCE_LICENCE_FILES:
                    self.assertIn(f"{archive_root}/references/source-library/{name}", archive.namelist())
            self.assertEqual(result.sha256, hashlib.sha256(result.path.read_bytes()).hexdigest())

    def test_rejects_missing_licence(self) -> None:
        (self.root / "country-plugin" / "LICENCE.md").unlink()
        with self.assertRaisesRegex(PackageBuildError, "EPIL licence missing"):
            build_plugin_archives(self.root, self.output)

    def test_rejects_changed_source_licence(self) -> None:
        country = self.root / "country-plugin" / "references" / "source-library"
        (country / "LICENSING.md").write_text("Unexpected change\n", encoding="utf-8")
        with self.assertRaisesRegex(PackageBuildError, "Source Library licence differs"):
            build_distributions(self.root, self.output)

    def test_extracted_plugins_resolve_country_modules_and_notes(self) -> None:
        repo = Path(self.temp.name) / "resolver-repo"
        repo.mkdir()
        (repo / "LICENCE.md").write_text("Synthetic EPIL\n", encoding="utf-8")
        core_path = "core-package"
        country_path = "freemovement-law-se"
        core = repo / core_path
        country = repo / country_path

        def write_plugin(root: Path, name: str, version: str) -> None:
            root.mkdir(parents=True, exist_ok=True)
            metadata = {"name": name, "version": version}
            (root / "plugin.json").write_text(json.dumps(metadata), encoding="utf-8")
            codex = root / ".codex-plugin"
            codex.mkdir()
            (codex / "plugin.json").write_text(
                json.dumps({**metadata, "skills": "./skills"}), encoding="utf-8"
            )
            (root / "skills").mkdir(exist_ok=True)
            (root / "LICENCE.md").write_bytes((repo / "LICENCE.md").read_bytes())
            (root / "SOURCE-LIBRARY-NOTICE.md").write_text("Source revision test-revision\n", encoding="utf-8")
            source_library = root / "references" / "source-library"
            source_library.mkdir(parents=True, exist_ok=True)
            for name in SOURCE_LICENCE_FILES:
                destination = source_library / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(f"Test {name}\n", encoding="utf-8")

        write_plugin(core, "freemovement-law", "1.0.0")
        write_plugin(country, "fm-sweden", "0.2.0")

        core_skill = core / "skills" / "eudirective-core"
        core_skill.mkdir()
        (core_skill / "SKILL.md").write_text("# Core\n", encoding="utf-8")
        resolver_source = Path(__file__).parents[2] / "freemovement-law" / "skills" / "eudirective-core" / "scripts" / "source_library_paths.py"
        resolver_target = core_skill / "scripts" / "source_library_paths.py"
        resolver_target.parent.mkdir()
        resolver_target.write_bytes(resolver_source.read_bytes())

        module_skill = country / "skills" / "eudirective-library-se"
        module_skill.mkdir(parents=True)
        (module_skill / "SKILL.md").write_text("# Sweden module\n", encoding="utf-8")
        notes = country / "references" / "source-library" / "module-notes" / "sweden"
        notes.mkdir(parents=True)
        (notes / "README.md").write_text("Synthetic module notes\n", encoding="utf-8")

        routing = {
            "core_plugin": "freemovement-law",
            "countries": [{
                "plugin_name": "fm-sweden",
                "package_directory": country_path,
                "source_library_directory": "sweden",
                "iso_country_code": "SE",
            }],
            "operational_modules": [{
                "module_id": "sweden-country",
                "plugin_name": "fm-sweden",
                "package_directory": country_path,
                "skill_directory": "skills/eudirective-library-se",
                "jurisdiction": "SE",
                "module_family": "country",
                "notes_directory": "sweden",
                "notes_plugin_name": "fm-sweden",
            }],
            "module_notes_ownership": [{
                "notes_directory": "sweden", "plugin_name": "fm-sweden",
            }],
        }
        references = core_skill / "references"
        references.mkdir()
        (references / "national-source-routing.json").write_text(
            json.dumps(routing), encoding="utf-8"
        )
        (repo / "marketplace.json").write_text(json.dumps({"plugins": [
            {"name": "freemovement-law", "source": {"source": "local", "path": f"./{core_path}"}},
            {"name": "fm-sweden", "source": {"source": "local", "path": f"./{country_path}"}},
        ]}), encoding="utf-8")

        archives = build_plugin_archives(repo, self.output / "resolver-build")
        install = Path(self.temp.name) / "installed"
        install.mkdir()
        for archive in archives:
            with zipfile.ZipFile(archive.path) as bundle:
                bundle.extractall(install)

        extracted_resolver = install / core_path / "skills" / "eudirective-core" / "scripts" / "source_library_paths.py"
        spec = importlib.util.spec_from_file_location("extracted_source_library_paths", extracted_resolver)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        resolver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(resolver)

        self.assertEqual(resolver.country_plugin_root("SE"), install / country_path)
        self.assertEqual(
            resolver.module_skill_for("SE", "country"),
            install / country_path / "skills" / "eudirective-library-se",
        )
        self.assertEqual(
            resolver.module_notes_root("SE", "sweden-country"),
            install / country_path / "references" / "source-library" / "module-notes" / "sweden",
        )

    def test_build_is_reproducible_and_replaces_only_managed_plugin_archives(self) -> None:
        first = build_plugin_archives(self.root, self.output)
        first_bytes = {item.path.name: item.path.read_bytes() for item in first}
        stale = self.output / "plugins" / "removed-plugin-9.9.9.zip"
        stale.write_bytes(b"stale")
        second = build_plugin_archives(self.root, self.output)
        self.assertEqual(first_bytes, {item.path.name: item.path.read_bytes() for item in second})
        self.assertFalse(stale.exists())
        self.assertTrue((self.output / "plugins" / ".distribution-output.json").is_file())

    def test_does_not_modify_marketplace_or_plugin_sources(self) -> None:
        before = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob("*") if path.is_file()
        }
        build_plugin_archives(self.root, self.output)
        after = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)

    def test_rejects_duplicate_plugin_names(self) -> None:
        self.write_marketplace([
            {"name": "fm-test", "path": "first", "version": "0.1.0"},
            {"name": "fm-test", "path": "second", "version": "0.1.0"},
        ])
        with self.assertRaisesRegex(PackageBuildError, "duplicate marketplace plugin name"):
            discover_plugins(self.root)

    def test_rejects_duplicate_plugin_directories(self) -> None:
        self.write_marketplace([
            {"name": "fm-one", "path": "same", "version": "0.1.0"},
            {"name": "fm-two", "path": "same", "version": "0.1.0"},
        ])
        with self.assertRaisesRegex(PackageBuildError, "same plugin directory"):
            discover_plugins(self.root)

    def test_rejects_path_traversal_before_reading_external_directory(self) -> None:
        self.write_marketplace([
            {"name": "fm-escape", "path": "../outside", "version": "0.1.0"},
        ])
        with self.assertRaisesRegex(PackageBuildError, "safe relative path"):
            discover_plugins(self.root)

    def test_rejects_plugin_metadata_identity_or_version_mismatch(self) -> None:
        plugin_json = self.root / "freemovement-law" / "plugin.json"
        metadata = json.loads(plugin_json.read_text())
        metadata["version"] = "9.9.9"
        plugin_json.write_text(json.dumps(metadata), encoding="utf-8")
        with self.assertRaisesRegex(PackageBuildError, "metadata versions disagree"):
            discover_plugins(self.root)

    def test_rejects_symlinked_plugin_content(self) -> None:
        plugin_root = self.root / "freemovement-law"
        outside = Path(self.temp.name) / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        (plugin_root / "linked.txt").symlink_to(outside)
        with self.assertRaisesRegex(PackageBuildError, "symbolic link"):
            build_plugin_archives(self.root, self.output)

    def test_refuses_to_replace_unmanaged_output_directory(self) -> None:
        managed = self.output / "plugins"
        managed.mkdir(parents=True)
        user_file = managed / "keep.txt"
        user_file.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(PackageBuildError, "unrecognized contents"):
            build_plugin_archives(self.root, self.output)
        self.assertEqual(user_file.read_text(encoding="utf-8"), "keep")

    def test_rejects_symlinked_output_path(self) -> None:
        target = Path(self.temp.name) / "existing-output"
        target.mkdir()
        sentinel = target / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        self.output.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(PackageBuildError, "symlinked output"):
            build_plugin_archives(self.root, self.output)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_rejects_output_inside_repository(self) -> None:
        with self.assertRaisesRegex(PackageBuildError, "outside the repository tree"):
            build_distributions(self.root, self.root / "dist")

    def test_builds_aggregates_catalog_and_checksums_then_verifies_them(self) -> None:
        archives = build_distributions(self.root, self.output)
        self.assertEqual(len(archives), 4)
        self.assertTrue((self.output / "packages.json").is_file())
        self.assertTrue((self.output / "SHA256SUMS").is_file())
        catalog = json.loads((self.output / "packages.json").read_text(encoding="utf-8"))
        self.assertEqual({item["id"] for item in catalog["packages"]}, {
            "freemovement-law", "fm-test", "all-skills", "source-library",
        })
        self.assertEqual(verify_distribution(self.root, self.output), 4)
        with zipfile.ZipFile(self.output / "freemovement-all-skills.zip") as archive:
            names = set(archive.namelist())
            self.assertIn("skills/fm-test-skill/SKILL.md", names)
            self.assertIn("skills/freemovement-law-skill/SKILL.md", names)
            manifest = json.loads(archive.read("DISTRIBUTION.json"))
            self.assertEqual(manifest["skill_count"], 2)
            self.assertIn("LICENCE.md", names)
            self.assertIn("SOURCE-LIBRARY-NOTICE.md", names)
            for name in SOURCE_LICENCE_FILES:
                self.assertIn(f"source-licenses/{name}", names)
        with zipfile.ZipFile(self.output / "freemovement-source-library.zip") as archive:
            self.assertIn("source-libraries/fm-test/source.md", archive.namelist())
            self.assertIn("provenance/component-index.json", archive.namelist())
            self.assertIn("SOURCE-LIBRARY-NOTICE.md", archive.namelist())
            for name in SOURCE_LICENCE_FILES:
                self.assertIn(name, archive.namelist())

    def test_full_distribution_is_reproducible_and_does_not_modify_sources(self) -> None:
        before = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob("*") if path.is_file()
        }
        first = build_distributions(self.root, self.output)
        first_bytes = {item.path.name: item.path.read_bytes() for item in first}
        repeat_output = Path(self.temp.name) / "repeat"
        second = build_distributions(self.root, repeat_output)
        self.assertEqual(first_bytes, {item.path.name: item.path.read_bytes() for item in second})
        after = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)

    def test_rejects_skill_slug_collisions(self) -> None:
        plugins = discover_plugins(self.root)
        skill = self.root / "country-plugin" / "skills" / "freemovement-law-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("# duplicate\n", encoding="utf-8")
        with self.assertRaisesRegex(PackageBuildError, "skill name collision"):
            build_distributions(self.root, self.output)

    def test_rejects_stale_source_inventory_mapping(self) -> None:
        migration = [{
            "source_path": "upstream/source.md",
            "classification": "accepted_national_source_text",
            "target_path": "country-plugin/references/source-library/source.md",
            "sha256": "0" * 64,
        }]
        (self.root / "migration-map.json").write_text(json.dumps(migration), encoding="utf-8")
        with self.assertRaisesRegex(PackageBuildError, "migration-map target hash mismatch"):
            build_distributions(self.root, self.output)

    def test_rejects_disagreeing_marketplace_copies(self) -> None:
        (self.root / ".agents" / "plugins").mkdir(parents=True)
        (self.root / ".agents" / "plugins" / "marketplace.json").write_text(
            '{"plugins": []}\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(PackageBuildError, "marketplace manifest copies disagree"):
            discover_plugins(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
