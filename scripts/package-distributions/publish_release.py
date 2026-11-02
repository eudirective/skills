#!/usr/bin/env python3
"""Publish a verified, revision-specific FreeMovement distribution release."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from release_notes import render_latest_pointer_notes, render_revision_release_notes


REVISION_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
ASSET_NAMES = {"packages.json", "SHA256SUMS"}


class PublishError(RuntimeError):
    """Raised when local or remote release evidence is incomplete or inconsistent."""


class GhClient:
    """Small gh CLI adapter; all network operations stay in GitHub Actions."""

    def __init__(self, repository: str):
        self.repository = repository

    def _run(self, *args: str, binary: bool = False) -> bytes | str:
        command = ["gh", *args]
        result = subprocess.run(command, check=False, capture_output=True)
        if result.returncode:
            error = result.stderr.decode("utf-8", errors="replace").strip()
            raise PublishError(f"GitHub CLI failed ({' '.join(command)}): {error}")
        return result.stdout if binary else result.stdout.decode("utf-8")

    def api_json(self, endpoint: str) -> object:
        raw = self._run("api", endpoint)
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise PublishError(f"GitHub returned invalid JSON for {endpoint}") from exc

    def resolve_tag(self, tag: str) -> str | None:
        try:
            reference = self.api_json(f"repos/{self.repository}/git/ref/tags/{tag}")
        except PublishError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise
        if not isinstance(reference, dict) or not isinstance(reference.get("object"), dict):
            raise PublishError(f"GitHub returned a malformed tag reference for {tag}")
        target = reference["object"]
        sha, object_type = target.get("sha"), target.get("type")
        if not isinstance(sha, str):
            raise PublishError(f"GitHub did not resolve tag {tag} to an object")
        if object_type == "commit":
            return sha
        if object_type != "tag":
            raise PublishError(f"Tag {tag} points to {object_type}, not a commit")
        annotated = self.api_json(f"repos/{self.repository}/git/tags/{sha}")
        if (not isinstance(annotated, dict) or not isinstance(annotated.get("object"), dict)
                or annotated["object"].get("type") != "commit"
                or not isinstance(annotated["object"].get("sha"), str)):
            raise PublishError(f"GitHub did not resolve annotated tag {tag} to a commit")
        return annotated["object"]["sha"]

    def get_release(self, tag: str) -> dict | None:
        try:
            release = self.api_json(f"repos/{self.repository}/releases/tags/{tag}")
        except PublishError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise
        if not isinstance(release, dict) or not isinstance(release.get("id"), int):
            raise PublishError(f"GitHub returned a malformed release record for {tag}")
        return release

    def create_draft(self, tag: str, revision: str, notes_path: Path) -> None:
        self._run("release", "create", tag, "--repo", self.repository,
                  "--draft", "--target", revision, "--title", f"FreeMovement distributions {revision}",
                  "--notes-file", str(notes_path))

    def delete_asset(self, asset_id: int) -> None:
        self._run("api", "--method", "DELETE",
                  f"repos/{self.repository}/releases/assets/{asset_id}")

    def upload(self, tag: str, paths: list[Path]) -> None:
        self._run("release", "upload", tag, *(str(path) for path in paths), "--repo", self.repository)

    def assets(self, release_id: int) -> list[dict]:
        result = self.api_json(f"repos/{self.repository}/releases/{release_id}/assets?per_page=100")
        if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
            raise PublishError("GitHub returned a malformed release asset list")
        return result

    def download_asset(self, asset_id: int) -> bytes:
        raw = self._run("api", f"repos/{self.repository}/releases/assets/{asset_id}",
                        "-H", "Accept: application/octet-stream", binary=True)
        return raw

    def publish(self, tag: str) -> None:
        self._run("release", "edit", tag, "--repo", self.repository, "--draft=false")

    def branch_sha(self, branch: str) -> str:
        result = self.api_json(f"repos/{self.repository}/commits/{branch}")
        if not isinstance(result, dict) or not isinstance(result.get("sha"), str):
            raise PublishError(f"GitHub did not resolve branch {branch}")
        return result["sha"]

    def create_latest(self, revision: str, notes_path: Path) -> None:
        self._run("release", "create", "freemovement-latest", "--repo", self.repository,
                  "--target", revision, "--title", "FreeMovement latest verified distribution",
                  "--notes-file", str(notes_path), "--prerelease")

    def update_latest_notes(self, notes_path: Path) -> None:
        # Deliberately omit --target: the legacy tag never moves.
        self._run("release", "edit", "freemovement-latest", "--repo", self.repository,
                  "--title", "FreeMovement latest verified distribution", "--notes-file", str(notes_path))


@dataclass
class PublishState:
    status: str = "started"
    revision: str = ""
    release_tag: str = ""
    latest_tag_sha_before: str | None = None
    latest_tag_sha_after: str | None = None
    latest_asset_retirement: str = "not_attempted"
    warnings: list[str] | None = None
    error: str | None = None


class ReleasePublisher:
    def __init__(self, client, repository: str, revision: str, distribution_dir: Path,
                 changelog: str, state: PublishState | None = None):
        if not REVISION_RE.fullmatch(revision):
            raise PublishError("revision must be a full lowercase Git SHA")
        self.client = client
        self.repository = repository
        self.revision = revision
        self.tag = f"freemovement-{revision}"
        self.distribution_dir = distribution_dir.resolve(strict=True)
        self.changelog = changelog
        self.state = state or PublishState()
        self.state.revision = revision
        self.state.release_tag = self.tag

    def _local_assets(self) -> dict[str, bytes]:
        files = [path for path in self.distribution_dir.iterdir() if path.is_file() and not path.is_symlink()]
        assets = {path.name: path.read_bytes() for path in files if path.name.endswith(".zip") or path.name in ASSET_NAMES}
        if len(assets) != len([path for path in files if path.name.endswith(".zip") or path.name in ASSET_NAMES]):
            raise PublishError("duplicate local distribution asset name")
        if set(assets) != ASSET_NAMES | {name for name in assets if name.endswith(".zip")}:
            raise PublishError("distribution must contain packages.json, SHA256SUMS and ZIP archives")
        if not any(name.endswith(".zip") for name in assets):
            raise PublishError("distribution contains no plugin ZIP archives")
        try:
            catalog = json.loads(assets["packages.json"])
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise PublishError("packages.json is invalid") from exc
        if catalog.get("source_revision") != self.revision:
            raise PublishError("packages.json source_revision does not match the release SHA")
        package_records = catalog.get("packages")
        if not isinstance(package_records, list):
            raise PublishError("packages.json has no package list")
        zip_records = [item for item in package_records if isinstance(item, dict)
                       and isinstance(item.get("path"), str) and item["path"].endswith(".zip")]
        catalog_zips = {Path(item["path"]).name for item in zip_records}
        zip_names = {name for name in assets if name.endswith(".zip")}
        if catalog_zips != zip_names:
            raise PublishError("ZIP asset set does not match packages.json")
        expected_hashes = {item["path"]: hashlib.sha256(assets[Path(item["path"]).name]).hexdigest()
                           for item in zip_records}
        expected_hashes["packages.json"] = hashlib.sha256(assets["packages.json"]).hexdigest()
        sums = {}
        for line in assets["SHA256SUMS"].decode("utf-8").splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
            if not match or match.group(2) in sums:
                raise PublishError("SHA256SUMS contains a malformed or duplicate entry")
            sums[match.group(2)] = match.group(1)
        if sums != expected_hashes:
            raise PublishError("SHA256SUMS does not exactly match the distribution assets")
        return assets

    def _verify_remote(self, release: dict, expected: dict[str, bytes]) -> None:
        actual = self.client.assets(release["id"])
        names = [asset.get("name") for asset in actual]
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise PublishError("remote release asset inventory differs from the verified local build")
        by_name = {asset["name"]: asset for asset in actual}
        for name, content in expected.items():
            remote = self.client.download_asset(by_name[name]["id"])
            if remote != content:
                raise PublishError(f"remote release asset differs from the verified local build: {name}")

    def _ensure_revision_release(self, expected: dict[str, bytes], notes_path: Path) -> None:
        target = self.client.resolve_tag(self.tag)
        if target is not None and target != self.revision:
            raise PublishError(f"revision tag resolves to {target}, expected {self.revision}")
        release = self.client.get_release(self.tag)
        if release is not None:
            if target is None or target != self.revision:
                if (not release.get("draft", False)
                        or release.get("target_commitish") != self.revision):
                    raise PublishError("existing release has no matching immutable revision target")
            if not release.get("draft", False):
                self.state.status = "published_existing"
                self._verify_remote(release, expected)
                self.state.status = "published_verified"
                return
        else:
            self.client.create_draft(self.tag, self.revision, notes_path)
            release = self.client.get_release(self.tag)
            if (release is None or not release.get("draft", False)
                    or release.get("target_commitish") != self.revision):
                raise PublishError("GitHub did not create a draft for the requested revision")
            self.state.status = "draft_created"

        for asset in self.client.assets(release["id"]):
            asset_id = asset.get("id")
            if not isinstance(asset_id, int):
                raise PublishError("draft contains a malformed asset record")
            self.client.delete_asset(asset_id)
        paths = [self.distribution_dir / name for name in sorted(expected)]
        self.client.upload(self.tag, paths)
        self.state.status = "draft_assets_uploaded"
        self._verify_remote(release, expected)
        self.state.status = "draft_assets_verified"
        self.client.publish(self.tag)
        published = self.client.get_release(self.tag)
        if published is None or published.get("draft", True):
            raise PublishError("revision release was not published after successful draft verification")
        if self.client.resolve_tag(self.tag) != self.revision:
            raise PublishError("published revision tag no longer points to the requested commit")
        self._verify_remote(published, expected)
        self.state.status = "published_verified"

    def _promote_latest_pointer(self, notes_path: Path) -> None:
        self.state.latest_tag_sha_before = self.client.resolve_tag("freemovement-latest")
        if self.client.branch_sha("main") != self.revision:
            self.state.status = "published_verified_main_advanced"
            return
        latest = self.client.get_release("freemovement-latest")
        expected_pointer = f"freemovement-{self.revision}"
        if latest is None:
            self.client.create_latest(self.revision, notes_path)
        else:
            self.client.update_latest_notes(notes_path)
        self.state.status = "latest_pointer_updated"
        latest = self.client.get_release("freemovement-latest")
        body = latest.get("body", "") if latest else ""
        if expected_pointer not in body or "/releases/download/freemovement-latest/" in body:
            raise PublishError("latest release notes do not point to the verified revision assets")
        self.state.latest_tag_sha_after = self.client.resolve_tag("freemovement-latest")
        if self.state.latest_tag_sha_before is not None and self.state.latest_tag_sha_after != self.state.latest_tag_sha_before:
            raise PublishError("latest release tag moved while updating pointer notes")
        if latest and latest.get("immutable") is True:
            self.state.latest_asset_retirement = "retained_immutable"
        elif latest:
            try:
                for asset in self.client.assets(latest["id"]):
                    self.client.delete_asset(asset["id"])
                self.state.latest_asset_retirement = "retired"
            except Exception as exc:
                self.state.latest_asset_retirement = "partial_or_unavailable"
                self.state.warnings = [f"legacy latest assets could not all be retired: {exc}"]
        else:
            self.state.latest_asset_retirement = "unverified"
        if self.client.branch_sha("main") != self.revision:
            self.state.status = "latest_pointer_updated_main_advanced"
            return
        self.state.status = "promoted"

    def publish(self) -> PublishState:
        expected = self._local_assets()
        self.state.status = "locally_verified"
        with tempfile.TemporaryDirectory(prefix="freemovement-release-") as temporary:
            notes = Path(temporary) / "revision-notes.md"
            notes.write_text(render_revision_release_notes(self.changelog, self.revision), encoding="utf-8")
            self._ensure_revision_release(expected, notes)
            if self.state.status == "published_verified":
                pointer_notes = Path(temporary) / "latest-notes.md"
                pointer_notes.write_text(render_latest_pointer_notes(self.revision), encoding="utf-8")
                self._promote_latest_pointer(pointer_notes)
        return self.state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="eudirective/skills")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--distribution-dir", type=Path, required=True)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--state-output", type=Path)
    args = parser.parse_args()
    state = PublishState(revision=args.revision, release_tag=f"freemovement-{args.revision}")
    try:
        changelog = args.changelog.read_text(encoding="utf-8")
        state = ReleasePublisher(GhClient(args.repo), args.repo, args.revision,
                                 args.distribution_dir, changelog, state).publish()
        code = 0
    except Exception as exc:
        state.error = str(exc)
        print(f"release publication failed: {exc}", file=sys.stderr)
        code = 1
    encoded = json.dumps(state.__dict__, sort_keys=True)
    if args.state_output:
        args.state_output.parent.mkdir(parents=True, exist_ok=True)
        args.state_output.write_text(encoded + "\n", encoding="utf-8")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"status={state.status}\n")
            stream.write(f"state_json={encoded}\n")
    print(encoded)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
