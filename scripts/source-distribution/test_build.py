from __future__ import annotations

import tempfile
import json
import unittest
from pathlib import Path

from build import SOURCE_LICENCE_FILES, accepted_paths, build_marketplace, classify_inventory


class AcceptedPathsTests(unittest.TestCase):
    def test_external_scope_acceptance_does_not_accept_candidate_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary) / "source-library"
            pack = source_root / "liechtenstein"
            pack.mkdir(parents=True)

            acceptance = {
                "records": {
                    "li-41": {
                        "status": "accepted_with_narrow_external_scope",
                        "local_copy_accepted": False,
                        "decision": "accepted_with_narrow_external_scope",
                        "legalize_candidate_snapshot": {
                            "repository": "legalize-dev/legalize-li",
                            "path": "li/LGBl-2020-465.md",
                            "status": "candidate_snapshot_method_only",
                        },
                    }
                }
            }

            self.assertEqual(accepted_paths(acceptance, source_root, pack), [])

    def test_explicitly_accepted_local_copy_is_still_distributed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary) / "source-library"
            pack = source_root / "liechtenstein"
            document = pack / "documents" / "accepted-act.md"
            document.parent.mkdir(parents=True)
            document.write_text("Synthetic accepted local text\n", encoding="utf-8")

            acceptance = {
                "records": {
                    "li-test": {
                        "local_copy_accepted": True,
                        "path": "documents/accepted-act.md",
                    }
                }
            }

            result = accepted_paths(acceptance, source_root, pack)
            self.assertEqual([item[0] for item in result], [document.resolve()])


class SourceLicenceInventoryTests(unittest.TestCase):
    def test_canonical_licence_files_are_marked_for_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary) / "source-library"
            for rel in SOURCE_LICENCE_FILES:
                destination = source_root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(f"Synthetic {rel}\n", encoding="utf-8")
            rows = classify_inventory(source_root, {"countries": []}, set(), set(), set())
            by_path = {row["source_path"]: row for row in rows}
            self.assertEqual(set(by_path), set(SOURCE_LICENCE_FILES))
            self.assertTrue(all(
                row["classification"] == "canonical_source_licensing" and
                row["distribution_action"] == "distributed_to_core_and_country_plugins"
                for row in rows
            ))


class MarketplaceGenerationTests(unittest.TestCase):
    def test_adds_current_countries_removes_retired_countries_and_keeps_custom_entries(self) -> None:
        existing = {"name": "FreeMovement", "plugins": [
            {"name": "freemovement-law", "source": {"source": "local", "path": "./freemovement-law"}},
            {"name": "freemovement-law-be", "source": {"source": "local", "path": "./freemovement-law-be"}},
            {"name": "freemovement-law-xx", "source": {"source": "local", "path": "./freemovement-law-xx"}},
            {"name": "custom-tool", "source": {"source": "local", "path": "./custom-tool"}},
        ]}
        registry = {"core_plugin": "freemovement-law"}
        countries = [
            {"iso_country_code": "BE", "plugin_name": "freemovement-law-be", "plugin_directory": "freemovement-law-be"},
            {"iso_country_code": "SE", "plugin_name": "freemovement-law-se", "plugin_directory": "freemovement-law-se"},
        ]
        generated = build_marketplace(existing, registry, countries)
        entries = {entry["name"]: entry for entry in generated["plugins"]}
        self.assertEqual(set(entries), {"freemovement-law", "freemovement-law-be", "freemovement-law-se", "custom-tool"})
        self.assertEqual(entries["freemovement-law-se"]["source"]["path"], "./freemovement-law-se")
        self.assertEqual(entries["custom-tool"], existing["plugins"][-1])
        self.assertEqual(existing["plugins"][2]["name"], "freemovement-law-xx")

    def test_one_generated_artifact_can_be_applied_to_both_marketplace_paths(self) -> None:
        generated = build_marketplace({"plugins": [{"name": "custom-tool"}]},
                                      {"core_plugin": "freemovement-law"}, [])
        encoded = json.dumps(generated, ensure_ascii=False, indent=2) + "\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nested = root / ".agents/plugins/marketplace.json"
            nested.parent.mkdir(parents=True)
            (root / "marketplace.json").write_text(encoded, encoding="utf-8")
            nested.write_text(encoded, encoding="utf-8")
            self.assertEqual((root / "marketplace.json").read_bytes(), nested.read_bytes())
            nested.write_text(encoded + " ", encoding="utf-8")
            self.assertNotEqual((root / "marketplace.json").read_bytes(), nested.read_bytes())


if __name__ == "__main__":
    unittest.main()
