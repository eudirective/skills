#!/usr/bin/env python3
"""Validate generated plugin, skill, component-manifest, and index versions."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SHA64 = re.compile(r"^[a-f0-9]{64}$")
SELF_LABEL = re.compile(r"\bSkill:\s*([A-Za-z0-9_-]+)\s+v(\d+\.\d+\.\d+)\b")
VERSION_FIELD = re.compile(r"(?:Current version|Skill version):\s*`?(\d+\.\d+\.\d+)`?")
PLUGIN_VERSION_FIELD = re.compile(r"Plugin version:\s*`?(\d+\.\d+\.\d+)`?")


class VersionValidationError(ValueError):
    pass


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VersionValidationError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VersionValidationError(f"Expected an object in {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(files: dict[str, str]) -> str:
    return hashlib.sha256(json_bytes(dict(sorted(files.items())))).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VersionValidationError(message)


def _component_manifest(package: Path, component_id: str) -> Path:
    if component_id == "eu-core":
        return package / "skills/eudirective-core/references/component-manifest.json"
    matches = sorted(package.glob("skills/*/references/component-manifest.json"))
    _require(len(matches) == 1, f"Expected one component manifest in {package}, found {len(matches)}")
    return matches[0]


def _validate_skill_disclosures(package: Path, manifest: dict[str, Any]) -> None:
    versions = manifest["skill_versions"]
    for path in sorted(package.glob("skills/**/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        skill_name = path.parent.name
        expected = versions.get(skill_name)
        if expected:
            for match in VERSION_FIELD.finditer(text):
                actual = match.group(1)
                _require(actual == expected,
                         f"Stale self-version in {path}: found {actual}, manifest declares {expected}")
        for match in PLUGIN_VERSION_FIELD.finditer(text):
            _require(match.group(1) == manifest["plugin_version"],
                     f"Stale plugin version in {path}: found {match.group(1)}, manifest declares {manifest['plugin_version']}")
        for match in SELF_LABEL.finditer(text):
            label_name, label_version = match.groups()
            if label_name in versions:
                _require(label_version == versions[label_name],
                         f"Stale self-disclosure in {path}: {label_name} says {label_version}, manifest declares {versions[label_name]}")
    for required_skill in ("eudirective-core", "eudirective-ac-turkiye", "eudirective-ms-sweden"):
        if required_skill in versions:
            candidates = list(package.glob(f"skills/**/{required_skill}/SKILL.md"))
            # Core and applicant-country skills are direct children; the Swedish module is a direct child
            # of the fm-sweden package. Their disclosure must be bound to installed package metadata.
            if not candidates and (package / f"skills/{required_skill}/SKILL.md").is_file():
                candidates = [package / f"skills/{required_skill}/SKILL.md"]
            if candidates:
                text = candidates[0].read_text(encoding="utf-8")
                _require(f"skill_versions.{required_skill}" in text,
                         f"{candidates[0]} must derive its visible skill version from the installed component manifest")


def validate_distribution(root: Path, registry_path: Path) -> dict[str, int]:
    root = root.resolve()
    registry = read_json(registry_path)
    index = read_json(root / "component-index.json")
    _require(index.get("schema_version") == "1.0.0", "Unsupported component-index schema")
    _require(index.get("source_repository") == "eudirective/public-data", "Unexpected component-index source repository")
    _require(isinstance(index.get("components"), list), "component-index components must be an array")
    core_name = registry.get("core_plugin")
    countries = registry.get("countries")
    _require(isinstance(core_name, str) and isinstance(countries, list), "Invalid country registry")

    expected: dict[str, tuple[str, str, str | None]] = {
        core_name: (core_name, "eu-core", None),
    }
    for country in countries:
        name = country["plugin_name"]
        expected[name] = (country["plugin_directory"], country["iso_country_code"], country["skill_name"])
    rows = index["components"]
    row_by_name = {row.get("plugin_name"): row for row in rows if isinstance(row, dict)}
    _require(len(row_by_name) == len(rows), "Component index contains missing or duplicate plugin names")
    _require(set(row_by_name) == set(expected),
             f"Component index registration mismatch: missing={sorted(set(expected)-set(row_by_name))}, extra={sorted(set(row_by_name)-set(expected))}")

    for name, (directory, component_id, primary_skill) in expected.items():
        package = root / directory
        _require(package.is_dir(), f"Missing package directory for {name}: {directory}")
        row = row_by_name[name]
        _require(row.get("package_directory") == directory, f"Wrong package directory in component index for {name}")
        _require(row.get("component_id") == component_id, f"Wrong component ID in component index for {name}")
        if primary_skill:
            _require(row.get("verification_profile") == next(c["verification_profile"] for c in countries if c["plugin_name"] == name),
                     f"Wrong verification profile in component index for {name}")

        manifest_path = _component_manifest(package, component_id)
        manifest = read_json(manifest_path)
        _require(manifest.get("schema_version") == "1.0.0", f"Unsupported manifest schema for {name}")
        _require(manifest.get("component_id") == component_id, f"Wrong manifest component ID for {name}")
        _require(manifest.get("plugin_version") == row.get("plugin_version"), f"Plugin version differs between manifest and index for {name}")
        _require(manifest.get("skill_versions") == row.get("skill_versions"), f"Skill versions differ between manifest and index for {name}")
        if name == core_name:
            expected_skills = {"eudirective-core", "eudirective-source-library"}
            expected_skills.update(
                module["skill_directory"].removeprefix("skills/").split("/")[0]
                for module in registry.get("additional_operational_modules", [])
                if module.get("plugin_name") == core_name
            )
        else:
            country = next(country for country in countries if country["plugin_name"] == name)
            expected_skills = {country["skill_name"]}
            expected_skills.update(
                module["skill_directory"].removeprefix("skills/").split("/")[0]
                for module in country.get("related_operational_modules", [])
                if module.get("plugin_name") == name
            )
        _require(set(manifest.get("skill_versions", {})) == expected_skills,
                 f"Manifest skill inventory differs from registered skills for {name}: expected={sorted(expected_skills)}")
        for field in ("source_contract_version", "input_fingerprint", "distributed_fingerprint", "compatibility"):
            _require(manifest.get(field) == row.get(field), f"{field} differs between manifest and index for {name}")
        _require(SEMVER.fullmatch(str(manifest.get("plugin_version", ""))) is not None,
                 f"Invalid plugin version for {name}")
        for skill, version in manifest.get("skill_versions", {}).items():
            _require(SEMVER.fullmatch(str(version)) is not None, f"Invalid skill version for {name}:{skill}")
        _require(manifest.get("upstream_trees") == index.get("upstream_trees"),
                 f"Upstream tree versions differ between manifest and index for {name}")
        _require(manifest.get("upstream_revision") == index.get("upstream_revision"),
                 f"Upstream revision differs between manifest and index for {name}")
        for field in ("input_fingerprint", "distributed_fingerprint"):
            _require(SHA64.fullmatch(str(manifest.get(field, ""))) is not None, f"Invalid {field} for {name}")
        input_files = manifest.get("input_files")
        skill_fingerprints = manifest.get("skill_fingerprints")
        _require(isinstance(input_files, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in input_files.items()),
                 f"Invalid input file inventory for {name}")
        _require(isinstance(skill_fingerprints, dict), f"Invalid skill fingerprint inventory for {name}")
        _require(manifest["input_fingerprint"] == fingerprint(input_files),
                 f"Input fingerprint does not match the recorded inputs for {name}")
        for skill, skill_hash in skill_fingerprints.items():
            _require(SHA64.fullmatch(str(skill_hash)) is not None and
                     input_files.get(f"skill-template/{skill}") == skill_hash,
                     f"Skill source fingerprint mismatch for {name}:{skill}")
        expected_compatibility = (registry.get("core_compatibility_contract") if name == core_name else
                                  next(c["core_compatibility_contract"] for c in countries if c["plugin_name"] == name))
        _require(manifest.get("compatibility") == expected_compatibility,
                 f"Component compatibility does not match the registry for {name}")

        metadata_path = package / "plugin.json"
        legacy_path = package / ".codex-plugin/plugin.json"
        metadata = read_json(metadata_path)
        legacy = read_json(legacy_path)
        for label, item in (("plugin.json", metadata), (".codex-plugin/plugin.json", legacy)):
            _require(item.get("name") == name, f"Plugin name differs in {label} for {name}")
            _require(item.get("version") == manifest["plugin_version"], f"Plugin version differs in {label} for {name}")

        files = {
            path.relative_to(package).as_posix(): sha256(path)
            for path in sorted(package.rglob("*"))
            if path.is_file() and path != manifest_path
        }
        _require(manifest.get("distributed_files") == files,
                 f"Distributed file hash mismatch for {name}; rerun the source distributor")
        _require(manifest["distributed_fingerprint"] == fingerprint(files),
                 f"Distributed fingerprint mismatch for {name}")
        _validate_skill_disclosures(package, manifest)

        if name == core_name:
            session = read_json(package / "skills/eudirective-core/references/session-version-manifest.json")
            _require(session.get("schema_version") == 1, "Unsupported session-version-manifest schema")
            _require(session.get("plugin", {}).get("name") == name, "Session-version manifest plugin identity mismatch")
            _require(session.get("plugin", {}).get("version") == manifest["plugin_version"],
                     "Session-version manifest plugin version differs from the component manifest")
            _require(session.get("skills") == manifest["skill_versions"],
                     "Session-version manifest skill versions differ from the component manifest")
            library = session.get("library", {})
            pack_manifests = []
            for pack_path in sorted((package / "skills/eudirective-core/references/source-library").glob("core-source-pack-manifest-*.json")):
                pack = read_json(pack_path)
                pack_version = str(pack.get("pack_version", ""))
                if pack.get("pack_name") == "eudirective-core-source-pack" and SEMVER.fullmatch(pack_version):
                    pack_manifests.append((tuple(map(int, pack_version.split("."))), pack_version))
            _require(bool(pack_manifests), "Core source-pack version manifest is missing")
            _require(library.get("core_pack_version") == max(pack_manifests)[1],
                     "Session-version manifest core source-pack version is stale")
            _require(library.get("repository") == "eudirective/public-data" and
                     library.get("path") == "source-library" and
                     library.get("module_notes_path") == "module-notes",
                     "Session-version manifest library identity is inconsistent")
            _require(library.get("tree_sha") == manifest["upstream_trees"].get("source-library"),
                     "Session-version manifest source-library tree differs from the component manifest")
            _require(library.get("module_notes_tree_sha") == manifest["upstream_trees"].get("module-notes"),
                     "Session-version manifest module-notes tree differs from the component manifest")
    return {"components": len(expected), "countries": len(countries)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Generated distribution root")
    parser.add_argument("--registry", type=Path, required=True, help="Source-distribution country registry")
    args = parser.parse_args()
    try:
        summary = validate_distribution(args.root, args.registry)
    except (VersionValidationError, KeyError, StopIteration, TypeError) as exc:
        print(f"version consistency failed: {exc}", file=sys.stderr)
        return 1
    print(f"Version consistency passed for {summary['components']} components ({summary['countries']} national plugins).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
