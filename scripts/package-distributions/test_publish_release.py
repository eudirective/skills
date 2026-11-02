#!/usr/bin/env python3
"""Deterministic tests for interruption-safe immutable release publication."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from publish_release import GhClient, PublishError, ReleasePublisher


REVISION = "a" * 40
OLD_REVISION = "b" * 40
CHANGELOG = "## [1.2.0] - 2026-11-02\n\n**Packages:** core 1.2.0\n\n- Safer releases.\n"


class GhClientTests(unittest.TestCase):
    def test_api_commands_use_repository_in_endpoint_without_repo_flag(self):
        client = GhClient("eudirective/skills")
        with patch("publish_release.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = b"{}"
            run.return_value.stderr = b""
            client.api_json("repos/eudirective/skills/commits/main")
            client.delete_asset(42)
            client.download_asset(43)

        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0], ["gh", "api", "repos/eudirective/skills/commits/main"])
        self.assertEqual(commands[1], ["gh", "api", "--method", "DELETE",
                                       "repos/eudirective/skills/releases/assets/42"])
        self.assertEqual(commands[2], ["gh", "api", "repos/eudirective/skills/releases/assets/43",
                                       "-H", "Accept: application/octet-stream"])

    def test_missing_tag_ref_is_reported_as_absent(self):
        client = GhClient("eudirective/skills")
        with patch.object(client, "api_json", side_effect=PublishError("HTTP 404")):
            self.assertIsNone(client.resolve_tag("freemovement-" + "a" * 40))

    def test_lightweight_tag_ref_resolves_to_commit(self):
        client = GhClient("eudirective/skills")
        with patch.object(client, "api_json", return_value={"object": {"sha": "a" * 40, "type": "commit"}}):
            self.assertEqual(client.resolve_tag("freemovement-" + "a" * 40), "a" * 40)

    def test_annotated_tag_ref_resolves_to_commit(self):
        client = GhClient("eudirective/skills")
        with patch.object(client, "api_json", side_effect=[
            {"object": {"sha": "b" * 40, "type": "tag"}},
            {"object": {"sha": "a" * 40, "type": "commit"}},
        ]) as api_json:
            self.assertEqual(client.resolve_tag("freemovement-" + "a" * 40), "a" * 40)
        self.assertEqual(api_json.call_count, 2)


def make_distribution(root: Path, revision: str = REVISION) -> dict[str, bytes]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "fm-core.zip").write_bytes(b"plugin archive bytes")
    catalog = {
        "schema_version": 1,
        "repository": "eudirective/skills",
        "source_revision": revision,
        "packages": [{"id": "freemovement-law", "type": "plugin", "name": "freemovement-law",
                      "version": "1.2.0", "path": "plugins/fm-core.zip"}],
    }
    (root / "packages.json").write_text(json.dumps(catalog, sort_keys=True) + "\n", encoding="utf-8")
    assets = {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}
    sums = {
        "plugins/fm-core.zip": hashlib.sha256(assets["fm-core.zip"]).hexdigest(),
        "packages.json": hashlib.sha256(assets["packages.json"]).hexdigest(),
    }
    (root / "SHA256SUMS").write_text("".join(f"{sums[name]}  {name}\n" for name in sorted(sums)), encoding="utf-8")
    return {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}


class FakeGitHub:
    def __init__(self):
        self.tags = {"freemovement-latest": OLD_REVISION}
        self.releases = {"freemovement-latest": {
            "id": 2, "draft": False, "assets": [{"id": 3, "name": "old.zip", "data": b"old"}],
            "body": "old pointer",
        }}
        self.main = REVISION
        self.upload_failure = False
        self.latest_failure = False
        self.advance_main_after_pointer = False
        self.next_id = 10
        self.deleted_assets = []
        self.published = []

    def resolve_tag(self, tag):
        return self.tags.get(tag)

    def get_release(self, tag):
        return self.releases.get(tag)

    def create_draft(self, tag, revision, notes_path):
        self.releases[tag] = {"id": self.next_id, "draft": True, "target_commitish": revision, "assets": []}
        self.next_id += 1

    def delete_asset(self, asset_id):
        self.deleted_assets.append(asset_id)
        for release in self.releases.values():
            release["assets"] = [asset for asset in release["assets"] if asset["id"] != asset_id]

    def upload(self, tag, paths):
        release = self.releases[tag]
        for path in paths:
            release["assets"].append({"id": self.next_id, "name": path.name, "data": path.read_bytes()})
            self.next_id += 1
            if self.upload_failure:
                raise PublishError("simulated upload interruption")

    def assets(self, release_id):
        return next(value["assets"] for value in self.releases.values() if value["id"] == release_id)

    def download_asset(self, asset_id):
        for release in self.releases.values():
            for asset in release["assets"]:
                if asset["id"] == asset_id:
                    return asset["data"]
        raise PublishError("missing asset")

    def publish(self, tag):
        self.releases[tag]["draft"] = False
        self.tags[tag] = self.releases[tag]["target_commitish"]
        self.published.append(tag)

    def branch_sha(self, branch):
        return self.main

    def create_latest(self, revision, notes_path):
        self.tags["freemovement-latest"] = revision
        self.releases["freemovement-latest"] = {"id": self.next_id, "draft": False, "assets": [],
                                                 "body": notes_path.read_text(encoding="utf-8")}
        self.next_id += 1

    def update_latest_notes(self, notes_path):
        if self.latest_failure:
            raise PublishError("simulated pointer update failure")
        self.releases["freemovement-latest"]["body"] = notes_path.read_text(encoding="utf-8")
        if self.advance_main_after_pointer:
            self.main = OLD_REVISION


class PublishReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fm-publish-test-")
        self.addCleanup(self.temp.cleanup)
        self.distribution = Path(self.temp.name) / "dist"
        self.assets = make_distribution(self.distribution)
        self.client = FakeGitHub()

    def publisher(self, client=None):
        return ReleasePublisher(client or self.client, "eudirective/skills", REVISION,
                                self.distribution, CHANGELOG)

    def test_draft_is_verified_published_then_latest_notes_pointer_is_updated(self):
        state = self.publisher().publish()
        self.assertEqual(state.status, "promoted")
        self.assertEqual(self.client.tags["freemovement-" + REVISION], REVISION)
        release = self.client.releases["freemovement-" + REVISION]
        self.assertFalse(release["draft"])
        self.assertEqual({item["name"] for item in release["assets"]}, set(self.assets))
        self.assertEqual(self.client.tags["freemovement-latest"], OLD_REVISION)
        self.assertIn("freemovement-" + REVISION, self.client.releases["freemovement-latest"]["body"])
        self.assertEqual(state.latest_asset_retirement, "retired")
        self.assertEqual(self.client.releases["freemovement-latest"]["assets"], [])

    def test_new_draft_is_bound_to_revision_before_github_creates_its_tag(self):
        self.assertNotIn("freemovement-" + REVISION, self.client.tags)
        state = self.publisher().publish()
        self.assertEqual(state.status, "promoted")
        self.assertEqual(self.client.tags["freemovement-" + REVISION], REVISION)

    def test_half_upload_failure_keeps_draft_and_does_not_change_latest(self):
        self.client.upload_failure = True
        with self.assertRaisesRegex(PublishError, "upload interruption"):
            self.publisher().publish()
        self.assertTrue(self.client.releases["freemovement-" + REVISION]["draft"])
        self.assertNotIn("freemovement-" + REVISION, self.client.published)
        self.assertEqual(self.client.tags["freemovement-latest"], OLD_REVISION)

    def test_retry_resets_incomplete_draft_assets_and_finishes(self):
        draft = {"id": 4, "draft": True, "target_commitish": REVISION,
                 "assets": [{"id": 5, "name": "stale.zip", "data": b"stale"}]}
        self.client.tags["freemovement-" + REVISION] = REVISION
        self.client.releases["freemovement-" + REVISION] = draft
        state = self.publisher().publish()
        self.assertEqual(state.status, "promoted")
        self.assertEqual(self.client.deleted_assets, [5, 3])
        self.assertEqual({item["name"] for item in draft["assets"]}, set(self.assets))

    def test_published_release_mismatch_is_never_modified_or_promoted(self):
        release = {"id": 4, "draft": False, "assets": [{"id": 5, "name": "extra.zip", "data": b"extra"}]}
        self.client.tags["freemovement-" + REVISION] = REVISION
        self.client.releases["freemovement-" + REVISION] = release
        with self.assertRaisesRegex(PublishError, "inventory differs"):
            self.publisher().publish()
        self.assertEqual(release["assets"][0]["name"], "extra.zip")
        self.assertEqual(self.client.tags["freemovement-latest"], OLD_REVISION)

    def test_same_count_unexpected_zip_cannot_replace_required_archive(self):
        assets = [{"id": i + 10, "name": name, "data": data}
                  for i, (name, data) in enumerate(self.assets.items())]
        assets = [dict(item, name="unexpected.zip") if item["name"] == "fm-core.zip" else item
                  for item in assets]
        self.client.tags["freemovement-" + REVISION] = REVISION
        self.client.releases["freemovement-" + REVISION] = {"id": 4, "draft": False, "assets": assets}
        with self.assertRaisesRegex(PublishError, "inventory differs"):
            self.publisher().publish()
        self.assertEqual(self.client.tags["freemovement-latest"], OLD_REVISION)

    def test_corrupt_remote_asset_bytes_block_published_release_reuse(self):
        assets = [{"id": i + 10, "name": name, "data": data}
                  for i, (name, data) in enumerate(self.assets.items())]
        assets[0] = dict(assets[0], data=b"corrupt")
        self.client.tags["freemovement-" + REVISION] = REVISION
        self.client.releases["freemovement-" + REVISION] = {"id": 4, "draft": False, "assets": assets}
        with self.assertRaisesRegex(PublishError, "differs from the verified local build"):
            self.publisher().publish()
        self.assertEqual(self.client.tags["freemovement-latest"], OLD_REVISION)

    def test_corrupt_local_checksums_block_before_release_mutation(self):
        (self.distribution / "SHA256SUMS").write_text("0" * 64 + "  packages.json\n", encoding="utf-8")
        with self.assertRaisesRegex(PublishError, "SHA256SUMS does not exactly match"):
            self.publisher().publish()
        self.assertNotIn("freemovement-" + REVISION, self.client.releases)
        self.assertEqual(self.client.tags["freemovement-latest"], OLD_REVISION)

    def test_wrong_revision_tag_is_rejected(self):
        self.client.tags["freemovement-" + REVISION] = OLD_REVISION
        with self.assertRaisesRegex(PublishError, "revision tag resolves"):
            self.publisher().publish()

    def test_main_advance_after_release_prevents_latest_promotion(self):
        self.client.main = OLD_REVISION
        state = self.publisher().publish()
        self.assertEqual(state.status, "published_verified_main_advanced")
        self.assertEqual(self.client.tags["freemovement-latest"], OLD_REVISION)

    def test_main_advance_during_pointer_update_is_reported_after_safe_update(self):
        self.client.advance_main_after_pointer = True
        state = self.publisher().publish()
        self.assertEqual(state.status, "latest_pointer_updated_main_advanced")
        self.assertIn("freemovement-" + REVISION, self.client.releases["freemovement-latest"]["body"])

    def test_latest_update_failure_keeps_verified_revision_release(self):
        self.client.latest_failure = True
        with self.assertRaisesRegex(PublishError, "pointer update failure"):
            self.publisher().publish()
        self.assertFalse(self.client.releases["freemovement-" + REVISION]["draft"])
        self.assertEqual(self.client.tags["freemovement-latest"], OLD_REVISION)

    def test_immutable_latest_release_notes_can_point_to_revision_without_asset_edits(self):
        self.client.releases["freemovement-latest"]["immutable"] = True
        state = self.publisher().publish()
        self.assertEqual(state.status, "promoted")
        self.assertEqual(state.latest_asset_retirement, "retained_immutable")
        self.assertEqual(self.client.releases["freemovement-latest"]["assets"][0]["name"], "old.zip")
        self.assertIn("freemovement-" + REVISION, self.client.releases["freemovement-latest"]["body"])

    def test_existing_exact_published_release_is_idempotently_reused(self):
        self.client.tags["freemovement-" + REVISION] = REVISION
        self.client.releases["freemovement-" + REVISION] = {
            "id": 4, "draft": False,
            "assets": [{"id": i + 5, "name": name, "data": data}
                       for i, (name, data) in enumerate(self.assets.items())],
        }
        state = self.publisher().publish()
        self.assertEqual(state.status, "promoted")
        self.assertEqual(self.client.published, [])
        self.assertEqual(self.client.deleted_assets, [3])


if __name__ == "__main__":
    unittest.main()
