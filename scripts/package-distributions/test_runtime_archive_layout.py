#!/usr/bin/env python3
"""Verify plugin ZIP roots against the production extracted-package resolver."""
from __future__ import annotations

import importlib.util
from pathlib import Path, PurePosixPath
import tempfile
import unittest
import zipfile

from build import build_plugin_archives, discover_plugins


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def load_resolver(core_root: Path):
    resolver_path = core_root / "skills/eudirective-core/scripts/source_library_paths.py"
    spec = importlib.util.spec_from_file_location("extracted_source_library_paths", resolver_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load extracted resolver: {resolver_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeArchiveLayoutTests(unittest.TestCase):
    def test_extracted_core_resolves_registered_sweden_package_and_module(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fm-runtime-archives-") as temporary:
            root = Path(temporary)
            output = root / "distribution"
            built = build_plugin_archives(REPOSITORY_ROOT, output)
            plugins = {plugin.name: plugin for plugin in discover_plugins(REPOSITORY_ROOT)}
            by_name = {item.name: item for item in built}

            # Every national plugin ZIP must be rooted at the path registered
            # in its marketplace entry, while retaining the package identity.
            for plugin in plugins.values():
                if plugin.name == "freemovement-law":
                    continue
                archive_root = PurePosixPath(plugin.source_path).name
                with zipfile.ZipFile(by_name[plugin.name].path) as archive:
                    self.assertTrue(all(name == f"{archive_root}/" or name.startswith(f"{archive_root}/")
                                        for name in archive.namelist()), plugin.name)
                    self.assertIn(f"{archive_root}/plugin.json", archive.namelist())

            extracted = root / "extracted"
            extracted.mkdir()
            for name in ("freemovement-law", "fm-sweden"):
                with zipfile.ZipFile(by_name[name].path) as archive:
                    archive.extractall(extracted)

            resolver = load_resolver(extracted / "freemovement-law")
            sweden_root = resolver.country_plugin_root("SE")
            self.assertEqual(sweden_root, extracted / "freemovement-law-se")
            registry = resolver.routing_registry()
            sweden_plugin = next(row["plugin_name"] for row in registry["countries"]
                                 if row["iso_country_code"] == "SE")
            sweden_module = next(row for row in registry["operational_modules"]
                                 if row["plugin_name"] == sweden_plugin)
            module_root = resolver.module_skill_root(sweden_module["module_id"])
            self.assertTrue(module_root.is_dir())
            self.assertEqual(module_root, sweden_root / sweden_module["skill_directory"])

            legacy = root / "legacy-layout"
            legacy.mkdir()
            with zipfile.ZipFile(by_name["freemovement-law"].path) as archive:
                archive.extractall(legacy)
            with zipfile.ZipFile(by_name["fm-sweden"].path) as archive:
                with zipfile.ZipFile(legacy / "legacy-sweden.zip", "w") as renamed:
                    for info in archive.infolist():
                        suffix = info.filename.removeprefix("freemovement-law-se/")
                        name = f"fm-sweden/{suffix}"
                        renamed.writestr(name, archive.read(info.filename))
            with zipfile.ZipFile(legacy / "legacy-sweden.zip") as archive:
                archive.extractall(legacy)
            legacy_resolver = load_resolver(legacy / "freemovement-law")
            with self.assertRaises(FileNotFoundError):
                legacy_resolver.country_plugin_root("SE")


if __name__ == "__main__":
    unittest.main()
