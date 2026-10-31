#!/usr/bin/env python3
"""Build and verify deterministic FreeMovement distribution archives."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
import zipfile


MARKETPLACE_FILES = (".agents/plugins/marketplace.json", "marketplace.json")
PLUGIN_OUTPUT_DIR = "plugins"
PLUGIN_MARKER = ".distribution-output.json"
PLUGIN_MARKER_CONTENT = {"kind": "plugin-archives", "format_version": 1}
DIST_MARKER = ".distribution-output.json"
DIST_MARKER_CONTENT = {"kind": "freemovement-distribution", "format_version": 1}
PACKAGES_FILE = "packages.json"
CHECKSUMS_FILE = "SHA256SUMS"
REPOSITORY = "eudirective/skills"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
PLUGIN_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


class PackageBuildError(ValueError):
    """Raised when marketplace metadata or package contents are unsafe/invalid."""


@dataclass(frozen=True)
class Plugin:
    name: str
    version: str
    source_path: str
    root: Path


@dataclass(frozen=True)
class PluginArchive:
    name: str
    version: str
    path: Path
    file_count: int
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class BuiltArchive:
    package_id: str
    package_type: str
    name: str
    version: str
    path: Path
    file_count: int
    size_bytes: int
    sha256: str


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PackageBuildError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise PackageBuildError(f"{label} is missing or is not a regular file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, PackageBuildError) as exc:
        raise PackageBuildError(f"could not read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PackageBuildError(f"{label} must contain a JSON object: {path}")
    return value


def _relative_path(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PackageBuildError(f"{label} must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise PackageBuildError(f"{label} is not a safe relative path: {value!r}")
    return path


def _resolve_contained(base: Path, value: object, label: str) -> Path:
    relative = _relative_path(value, label)
    candidate = base
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise PackageBuildError(f"{label} must not traverse a symbolic link: {value!r}")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise PackageBuildError(f"{label} does not resolve: {value!r}") from exc
    if resolved == base or base not in resolved.parents:
        raise PackageBuildError(f"{label} escapes or names its containing directory: {value!r}")
    return resolved


def _validate_plugin(
    root: Path,
    marketplace_name: object,
    source_path: object,
    resolved_root: Path | None = None,
) -> Plugin:
    if not isinstance(marketplace_name, str) or not PLUGIN_NAME_RE.fullmatch(marketplace_name):
        raise PackageBuildError(f"invalid marketplace plugin name: {marketplace_name!r}")
    plugin_root = resolved_root or _resolve_contained(root, source_path, f"source path for {marketplace_name}")
    if plugin_root.is_symlink() or not plugin_root.is_dir():
        raise PackageBuildError(f"plugin source is not a real directory: {source_path!r}")

    primary = _read_json_object(plugin_root / "plugin.json", "plugin.json")
    codex = _read_json_object(plugin_root / ".codex-plugin" / "plugin.json", ".codex-plugin/plugin.json")
    if primary.get("name") != marketplace_name or codex.get("name") != marketplace_name:
        raise PackageBuildError(f"plugin identity does not match marketplace entry {marketplace_name!r}")
    version = primary.get("version")
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        raise PackageBuildError(f"plugin {marketplace_name!r} has an invalid semantic version")
    if codex.get("version") != version:
        raise PackageBuildError(f"plugin {marketplace_name!r} metadata versions disagree")

    skills_value = codex.get("skills")
    if skills_value is not None:
        skills_root = _resolve_contained(plugin_root, skills_value, f"skills path for {marketplace_name}")
        if not skills_root.is_dir() or not any(
            item.is_file() and not item.is_symlink() and item.name == "SKILL.md"
            for item in skills_root.rglob("SKILL.md")
        ):
            raise PackageBuildError(f"plugin {marketplace_name!r} has no regular SKILL.md entrypoint")

    return Plugin(
        name=marketplace_name,
        version=version,
        source_path=str(source_path),
        root=plugin_root,
    )


def discover_plugins(repository_root: Path) -> list[Plugin]:
    """Read and validate the marketplace's complete local plugin registry."""
    root = repository_root.expanduser().resolve(strict=True)
    manifest_paths = [root / name for name in MARKETPLACE_FILES if (root / name).exists()]
    if not manifest_paths:
        raise PackageBuildError(f"marketplace manifest not found; expected one of {MARKETPLACE_FILES!r}")
    manifests = [_read_json_object(path, str(path.relative_to(root))) for path in manifest_paths]
    if any(item != manifests[0] for item in manifests[1:]):
        raise PackageBuildError("marketplace manifest copies disagree")
    manifest = manifests[0]
    entries = manifest.get("plugins")
    if not isinstance(entries, list) or not entries:
        raise PackageBuildError("marketplace.json must register at least one plugin")

    plugins: list[Plugin] = []
    pending: list[tuple[str, object, Path]] = []
    folded_names: set[str] = set()
    roots: set[Path] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise PackageBuildError(f"marketplace plugin entry {index} must be an object")
        source = entry.get("source")
        if not isinstance(source, dict) or source.get("source") != "local":
            raise PackageBuildError(f"marketplace plugin entry {index} must use a local source")
        name = entry.get("name")
        if not isinstance(name, str) or not PLUGIN_NAME_RE.fullmatch(name):
            raise PackageBuildError(f"invalid marketplace plugin name: {name!r}")
        if name.casefold() in folded_names:
            raise PackageBuildError(f"duplicate marketplace plugin name: {name}")
        source_root = _resolve_contained(root, source.get("path"), f"source path for {name}")
        if not source_root.is_dir():
            raise PackageBuildError(f"plugin source is not a directory: {source.get('path')!r}")
        if source_root in roots:
            raise PackageBuildError(f"multiple marketplace entries use the same plugin directory: {source_root}")
        for other in roots:
            if source_root in other.parents or other in source_root.parents:
                raise PackageBuildError("marketplace plugin source directories may not overlap")
        pending.append((name, source.get("path"), source_root))
        folded_names.add(name.casefold())
        roots.add(source_root)
    for name, source_path, source_root in pending:
        plugins.append(_validate_plugin(root, name, source_path, source_root))
    return sorted(plugins, key=lambda plugin: plugin.name.casefold())


def _plugin_entries(plugin: Plugin) -> list[tuple[str, Path, bool]]:
    """Return deterministic archive names, paths, and directory flags."""
    entries: list[tuple[str, Path, bool]] = [(f"{plugin.name}/", plugin.root, True)]
    seen: set[str] = {f"{plugin.name}/".casefold()}
    for current, directory_names, file_names in os.walk(plugin.root, topdown=True, followlinks=False):
        current_path = Path(current)
        directory_names.sort(key=str.casefold)
        file_names.sort(key=str.casefold)
        kept_directories: list[str] = []
        for name in directory_names:
            if name == ".git":
                continue
            source = current_path / name
            if source.is_symlink() or not source.is_dir():
                raise PackageBuildError(f"plugin tree contains a non-regular directory: {source}")
            kept_directories.append(name)
            archive_name = f"{plugin.name}/{source.relative_to(plugin.root).as_posix()}/"
            folded = archive_name.casefold()
            if folded in seen:
                raise PackageBuildError(f"case-insensitive duplicate ZIP path: {archive_name}")
            seen.add(folded)
            entries.append((archive_name, source, True))
        directory_names[:] = kept_directories

        for name in file_names:
            if name == ".git":
                continue
            source = current_path / name
            if source.is_symlink():
                raise PackageBuildError(f"plugin tree contains a symbolic link: {source}")
            try:
                mode = source.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise PackageBuildError(f"could not inspect plugin file: {source}") from exc
            if not stat.S_ISREG(mode):
                raise PackageBuildError(f"plugin tree contains a non-regular file: {source}")
            archive_name = f"{plugin.name}/{source.relative_to(plugin.root).as_posix()}"
            folded = archive_name.casefold()
            if folded in seen:
                raise PackageBuildError(f"case-insensitive duplicate ZIP path: {archive_name}")
            seen.add(folded)
            entries.append((archive_name, source, False))
    return sorted(entries, key=lambda item: item[0].casefold())


def _zip_info(name: str, mode: int, is_directory: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    file_type = stat.S_IFDIR if is_directory else stat.S_IFREG
    permissions = (mode & 0o777) or (0o755 if is_directory else 0o644)
    info.external_attr = (file_type | permissions) << 16
    if is_directory:
        info.external_attr |= 0x10
    return info


def _write_plugin_archive(plugin: Plugin, destination: Path) -> int:
    entries = _plugin_entries(plugin)
    with zipfile.ZipFile(destination, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.comment = b""
        for archive_name, source, is_directory in entries:
            mode = stat.S_IMODE(source.stat().st_mode)
            info = _zip_info(archive_name, mode, is_directory)
            if is_directory:
                archive.writestr(info, b"")
                continue
            before = source.stat(follow_symlinks=False)
            data = source.read_bytes()
            after = source.stat(follow_symlinks=False)
            if before.st_size != len(data) or before.st_mtime_ns != after.st_mtime_ns or before.st_ino != after.st_ino:
                raise PackageBuildError(f"plugin source changed while being packaged: {source}")
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return sum(not is_directory for _, _, is_directory in entries)


def _validate_existing_output(path: Path, marker_name: str, marker_content: dict[str, object]) -> None:
    if path.is_symlink():
        raise PackageBuildError(f"refusing to replace a symlinked output directory: {path}")
    if not path.exists():
        return
    if not path.is_dir():
        raise PackageBuildError(f"plugin archive output path is not a directory: {path}")
    marker_path = path / marker_name
    if marker_path.is_symlink() or not marker_path.is_file():
        raise PackageBuildError(f"unrecognized contents at managed plugin archive path: {path}")
    marker = _read_json_object(marker_path, "plugin archive output marker")
    if marker != marker_content:
        raise PackageBuildError(f"unrecognized contents at managed plugin archive path: {path}")


def build_plugin_archives(repository_root: Path, output_dir: Path) -> list[PluginArchive]:
    """Build all registered plugins and atomically replace output_dir/plugins."""
    root = repository_root.expanduser().resolve(strict=True)
    plugins = discover_plugins(root)
    requested_output = output_dir.expanduser()
    if requested_output.is_symlink():
        raise PackageBuildError(f"refusing to write through a symlinked output directory: {requested_output}")
    output = requested_output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise PackageBuildError("plugin archive output must be outside the repository tree")
    for plugin in plugins:
        if output == plugin.root or plugin.root in output.parents:
            raise PackageBuildError("output directory must not be inside a plugin source directory")

    output.mkdir(parents=True, exist_ok=True)
    managed_output = output / PLUGIN_OUTPUT_DIR
    _validate_existing_output(managed_output, PLUGIN_MARKER, PLUGIN_MARKER_CONTENT)
    staging = Path(tempfile.mkdtemp(prefix=".plugin-zips-staging-", dir=output))
    backup = output / f".plugin-zips-backup-{uuid.uuid4().hex}"
    results: list[PluginArchive] = []
    try:
        for plugin in plugins:
            filename = f"{plugin.name}-{plugin.version}.zip"
            archive_path = staging / filename
            file_count = _write_plugin_archive(plugin, archive_path)
            data = archive_path.read_bytes()
            results.append(PluginArchive(
                name=plugin.name,
                version=plugin.version,
                path=managed_output / filename,
                file_count=file_count,
                size_bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
            ))
        (staging / PLUGIN_MARKER).write_text(
            json.dumps(PLUGIN_MARKER_CONTENT, sort_keys=True) + "\n", encoding="utf-8"
        )

        if managed_output.exists():
            os.replace(managed_output, backup)
        try:
            os.replace(staging, managed_output)
        except OSError:
            if backup.exists():
                os.replace(backup, managed_output)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    return results


def _tree_entries(source_root: Path, prefix: str, skip_git: bool = False) -> list[tuple[str, Path, bool]]:
    """Return safe, deterministic ZIP entries for a complete directory tree."""
    if source_root.is_symlink() or not source_root.is_dir():
        raise PackageBuildError(f"archive source is not a regular directory: {source_root}")
    root_entry = prefix.rstrip("/") + "/"
    entries: list[tuple[str, Path, bool]] = [(root_entry, source_root, True)]
    seen = {root_entry.casefold()}
    for current, directory_names, file_names in os.walk(source_root, topdown=True, followlinks=False):
        current_path = Path(current)
        directory_names.sort(key=str.casefold)
        file_names.sort(key=str.casefold)
        kept_directories: list[str] = []
        for name in directory_names:
            if skip_git and name == ".git":
                continue
            source = current_path / name
            if source.is_symlink() or not source.is_dir():
                raise PackageBuildError(f"source tree contains a non-regular directory: {source}")
            kept_directories.append(name)
            archive_name = f"{prefix.rstrip('/')}/{source.relative_to(source_root).as_posix()}/"
            if archive_name.casefold() in seen:
                raise PackageBuildError(f"case-insensitive duplicate ZIP path: {archive_name}")
            seen.add(archive_name.casefold())
            entries.append((archive_name, source, True))
        directory_names[:] = kept_directories
        for name in file_names:
            if skip_git and name == ".git":
                continue
            source = current_path / name
            if source.is_symlink():
                raise PackageBuildError(f"source tree contains a symbolic link: {source}")
            try:
                mode = source.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise PackageBuildError(f"could not inspect source file: {source}") from exc
            if not stat.S_ISREG(mode):
                raise PackageBuildError(f"source tree contains a non-regular file: {source}")
            archive_name = f"{prefix.rstrip('/')}/{source.relative_to(source_root).as_posix()}"
            if archive_name.casefold() in seen:
                raise PackageBuildError(f"case-insensitive duplicate ZIP path: {archive_name}")
            seen.add(archive_name.casefold())
            entries.append((archive_name, source, False))
    return sorted(entries, key=lambda item: item[0].casefold())


def _write_entries(destination: Path, entries: list[tuple[str, Path, bool]]) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.comment = b""
        for archive_name, source, is_directory in entries:
            mode = stat.S_IMODE(source.stat().st_mode)
            info = _zip_info(archive_name, mode, is_directory)
            if is_directory:
                archive.writestr(info, b"")
                continue
            before = source.stat(follow_symlinks=False)
            data = source.read_bytes()
            after = source.stat(follow_symlinks=False)
            if before.st_size != len(data) or before.st_mtime_ns != after.st_mtime_ns or before.st_ino != after.st_ino:
                raise PackageBuildError(f"archive source changed while being packaged: {source}")
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return sum(not is_directory for _, _, is_directory in entries)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _built_archive(package_id: str, package_type: str, name: str, version: str,
                   path: Path, root: Path, file_count: int) -> BuiltArchive:
    return BuiltArchive(package_id, package_type, name, version, path, file_count,
                        path.stat().st_size, _file_sha256(path))


def discover_skills(plugins: list[Plugin]) -> list[tuple[Plugin, Path]]:
    """Find every skill directory and reject case-insensitive slug collisions."""
    discovered: list[tuple[Plugin, Path]] = []
    owners: dict[str, tuple[str, Path]] = {}
    for plugin in plugins:
        codex_metadata = _read_json_object(plugin.root / ".codex-plugin" / "plugin.json", ".codex-plugin/plugin.json")
        skills_value = codex_metadata.get("skills")
        if skills_value is None:
            continue
        skills_root = _resolve_contained(plugin.root, skills_value, f"skills path for {plugin.name}")
        if not skills_root.is_dir():
            raise PackageBuildError(f"skills path for {plugin.name} is not a directory")
        for marker in sorted(skills_root.rglob("SKILL.md"), key=lambda path: path.as_posix().casefold()):
            if marker.is_symlink() or not marker.is_file():
                raise PackageBuildError(f"skill entrypoint is not a regular file: {marker}")
            skill_root = marker.parent
            slug = skill_root.name
            previous = owners.get(slug.casefold())
            if previous:
                raise PackageBuildError(
                    f"skill name collision {slug!r}: {previous[0]} ({previous[1]}) and {plugin.name} ({skill_root})"
                )
            owners[slug.casefold()] = (plugin.name, skill_root)
            discovered.append((plugin, skill_root))
    if not discovered:
        raise PackageBuildError("no skill folders with SKILL.md entrypoints were discovered")
    return sorted(discovered, key=lambda item: item[1].name.casefold())


def build_all_skills_archive(repository_root: Path, output_path: Path) -> BuiltArchive:
    """Package each complete skill folder under a unique skills/<slug> path."""
    root = repository_root.expanduser().resolve(strict=True)
    plugins = discover_plugins(root)
    skills = discover_skills(plugins)
    entries: list[tuple[str, Path, bool]] = []
    skill_records: list[dict[str, object]] = []
    for plugin, skill_root in skills:
        tree = _tree_entries(skill_root, f"skills/{skill_root.name}", skip_git=True)
        entries.extend(tree)
        count = sum(not is_directory for _, _, is_directory in tree)
        skill_records.append({
            "skill": skill_root.name,
            "plugin": plugin.name,
            "plugin_version": plugin.version,
            "source_path": skill_root.relative_to(plugin.root).as_posix(),
            "file_count": count,
        })
    core = next((plugin for plugin in plugins if plugin.name == "freemovement-law"), None)
    if core is None:
        raise PackageBuildError("marketplace does not register freemovement-law")
    manifest = {
        "format_version": 1,
        "kind": "aggregate-skills",
        "skill_count": len(skill_records),
        "skills": skill_records,
        "note": "Complete skill directories are included. Plugin-level resources outside those directories are not bundled.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".skills-manifest-", dir=output_path.parent) as temp_dir:
        manifest_file = Path(temp_dir) / "DISTRIBUTION.json"
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        entries.append(("DISTRIBUTION.json", manifest_file, False))
        archive_file_count = _write_entries(output_path, sorted(entries, key=lambda item: item[0].casefold()))
    return _built_archive("all-skills", "aggregate", "freemovement-all-skills", core.version,
                          output_path, output_path.parent, archive_file_count)


def _source_library_root(plugin: Plugin) -> Path:
    roots = [path for path in plugin.root.rglob("source-library") if path.is_dir()]
    if len(roots) != 1:
        raise PackageBuildError(
            f"plugin {plugin.name} must contain exactly one source-library directory; found {len(roots)}"
        )
    if roots[0].is_symlink():
        raise PackageBuildError(f"source-library root is a symbolic link: {roots[0]}")
    return roots[0]


def _validate_source_provenance(repository_root: Path, plugins: list[Plugin]) -> dict[str, object]:
    """Check generated inventory records against the package snapshot before distribution."""
    component_index = _read_json_object(repository_root / "component-index.json", "component-index.json")
    components = component_index.get("components")
    if not isinstance(components, list):
        raise PackageBuildError("component-index.json must contain a components array")
    component_by_name: dict[str, dict[str, object]] = {}
    for component in components:
        if not isinstance(component, dict) or not isinstance(component.get("plugin_name"), str):
            raise PackageBuildError("component-index.json contains an invalid component record")
        name = component["plugin_name"]
        if name in component_by_name:
            raise PackageBuildError(f"component-index.json contains duplicate plugin {name}")
        component_by_name[name] = component
    expected = {plugin.name: plugin for plugin in plugins}
    if set(component_by_name) != set(expected):
        raise PackageBuildError("component-index.json plugin inventory does not match marketplace.json")
    for name, plugin in expected.items():
        component = component_by_name[name]
        if component.get("plugin_version") != plugin.version or component.get("package_directory") != Path(plugin.source_path).as_posix().removeprefix("./"):
            raise PackageBuildError(f"component-index.json metadata is stale for {name}")

    inventory_path = repository_root / "source-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if not isinstance(inventory, list):
        raise PackageBuildError("source-inventory.json must contain an array")
    inventory_paths: set[str] = set()
    for item in inventory:
        if not isinstance(item, dict) or not isinstance(item.get("source_path"), str):
            raise PackageBuildError("source-inventory.json contains an invalid record")
        source_path = item["source_path"]
        _relative_path(source_path, "source inventory path")
        if source_path in inventory_paths:
            raise PackageBuildError(f"source-inventory.json contains duplicate source path: {source_path}")
        inventory_paths.add(source_path)
        if not isinstance(item.get("classification"), str) or not isinstance(item.get("distribution_action"), str):
            raise PackageBuildError(f"source-inventory.json lacks classification/action for {source_path}")
        if (not isinstance(item.get("bytes"), int) or item["bytes"] < 0
                or not isinstance(item.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])):
            raise PackageBuildError(f"source-inventory.json lacks valid size/hash data for {source_path}")

    migration_path = repository_root / "migration-map.json"
    migration = json.loads(migration_path.read_text(encoding="utf-8"))
    if not isinstance(migration, list):
        raise PackageBuildError("migration-map.json must contain an array")
    target_paths: dict[str, str] = {}
    for item in migration:
        if not isinstance(item, dict) or not isinstance(item.get("target_path"), str):
            raise PackageBuildError("migration-map.json contains an invalid record")
        if not isinstance(item.get("source_path"), str) or not isinstance(item.get("classification"), str):
            raise PackageBuildError("migration-map.json contains an incomplete provenance record")
        _relative_path(item["source_path"], "migration source path")
        target = item["target_path"]
        relative = _relative_path(target, "migration target path")
        existing_hash = target_paths.get(relative.as_posix())
        if existing_hash is not None and existing_hash != item.get("sha256"):
            raise PackageBuildError(f"migration-map.json contains conflicting target hashes: {target}")
        if existing_hash is not None:
            continue
        declared_hash = item.get("sha256")
        if not isinstance(declared_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", declared_hash):
            raise PackageBuildError(f"migration-map has an invalid content hash: {target}")
        target_paths[relative.as_posix()] = declared_hash
        try:
            target_file = _resolve_contained(repository_root, target, "migration target path")
        except PackageBuildError as exc:
            raise PackageBuildError(f"migration-map target is missing or unsafe: {target}") from exc
        if not target_file.is_file():
            raise PackageBuildError(f"migration-map target is missing or not a regular file: {target}")
        if _file_sha256(target_file) != declared_hash:
            raise PackageBuildError(f"migration-map target hash mismatch: {target}")
    return component_index


def build_source_library_archive(repository_root: Path, output_path: Path) -> BuiltArchive:
    """Consolidate the exact source-library trees from every marketplace plugin."""
    root = repository_root.expanduser().resolve(strict=True)
    plugins = discover_plugins(root)
    component_index = _validate_source_provenance(root, plugins)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[str, Path, bool]] = []
    libraries: list[dict[str, object]] = []
    for plugin in plugins:
        library_root = _source_library_root(plugin)
        tree = _tree_entries(library_root, f"source-libraries/{plugin.name}", skip_git=True)
        entries.extend(tree)
        files = [path for _, path, is_directory in tree if not is_directory]
        libraries.append({
            "plugin": plugin.name,
            "plugin_version": plugin.version,
            "plugin_directory": plugin.source_path,
            "source_library_path": library_root.relative_to(plugin.root).as_posix(),
            "file_count": len(files),
            "files": [
                {"path": path.relative_to(library_root).as_posix(), "bytes": path.stat().st_size,
                 "sha256": _file_sha256(path)}
                for path in sorted(files, key=lambda item: item.relative_to(library_root).as_posix().casefold())
            ],
        })

    provenance_names = ("component-index.json", "source-inventory.json", "migration-map.json")
    provenance_records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix=".source-provenance-", dir=output_path.parent) as temp_dir:
        temporary_root = Path(temp_dir)
        for filename in provenance_names:
            source = root / filename
            if source.is_symlink() or not source.is_file():
                raise PackageBuildError(f"required source provenance file is missing: {filename}")
            staged = temporary_root / filename
            shutil.copyfile(source, staged)
            entries.append((f"provenance/{filename}", staged, False))
            provenance_records.append({"path": f"provenance/{filename}", "bytes": staged.stat().st_size,
                                       "sha256": _file_sha256(staged)})
        manifest = {
            "format_version": 1,
            "kind": "consolidated-source-library",
            "source_repository": REPOSITORY,
            "upstream_revision": component_index.get("upstream_revision"),
            "libraries": libraries,
            "provenance_files": provenance_records,
            "note": "Hashes establish byte identity; they do not certify legal completeness or currentness.",
        }
        staged_manifest = temporary_root / "DISTRIBUTION.json"
        staged_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        entries.append(("DISTRIBUTION.json", staged_manifest, False))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        archive_file_count = _write_entries(output_path, sorted(entries, key=lambda item: item[0].casefold()))
    return _built_archive("source-library", "aggregate", "freemovement-source-library", "snapshot",
                          output_path, output_path.parent, archive_file_count)


def _git_revision(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(repository_root), "rev-parse", "HEAD"],
                                check=True, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    revision = result.stdout.strip()
    return revision if re.fullmatch(r"[0-9a-f]{40,64}", revision) else None


def _catalog_entry(archive: BuiltArchive, output_root: Path) -> dict[str, object]:
    return {
        "id": archive.package_id,
        "type": archive.package_type,
        "name": archive.name,
        "version": archive.version,
        "path": archive.path.relative_to(output_root).as_posix(),
        "file_count": archive.file_count,
        "size_bytes": archive.size_bytes,
        "sha256": archive.sha256,
    }


def _write_catalog(output_root: Path, archives: list[BuiltArchive], source_revision: str | None) -> None:
    catalog = {
        "schema_version": 1,
        "repository": REPOSITORY,
        "source_revision": source_revision,
        "packages": [_catalog_entry(item, output_root) for item in sorted(archives, key=lambda x: x.path.name.casefold())],
    }
    packages_path = output_root / "packages.json"
    packages_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksummed = sorted([item.path for item in archives] + [packages_path],
                         key=lambda path: path.relative_to(output_root).as_posix())
    (output_root / "SHA256SUMS").write_text(
        "".join(f"{_file_sha256(path)}  {path.relative_to(output_root).as_posix()}\n" for path in checksummed),
        encoding="utf-8",
    )


def build_distributions(repository_root: Path, output_dir: Path) -> list[BuiltArchive]:
    """Build plugins, both aggregates, package catalog, and checksums atomically."""
    root = repository_root.expanduser().resolve(strict=True)
    plugins = discover_plugins(root)
    requested_output = output_dir.expanduser()
    if requested_output.is_symlink():
        raise PackageBuildError(f"refusing to replace a symlinked output directory: {requested_output}")
    output = requested_output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise PackageBuildError("distribution output must be outside the repository tree")
    if any(output == plugin.root or plugin.root in output.parents for plugin in plugins):
        raise PackageBuildError("distribution output must not be inside a plugin source directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    _validate_existing_output(output, DIST_MARKER, DIST_MARKER_CONTENT)
    staging = Path(tempfile.mkdtemp(prefix=".distribution-staging-", dir=output.parent))
    backup = output.parent / f".distribution-backup-{uuid.uuid4().hex}"
    try:
        plugin_archives = build_plugin_archives(root, staging)
        archives: list[BuiltArchive] = []
        for item in plugin_archives:
            flat_path = staging / item.path.name
            os.replace(item.path, flat_path)
            archives.append(_built_archive(item.name, "plugin", item.name, item.version,
                                           flat_path, staging, item.file_count))
        shutil.rmtree(staging / PLUGIN_OUTPUT_DIR)
        archives.append(build_all_skills_archive(root, staging / "freemovement-all-skills.zip"))
        archives.append(build_source_library_archive(root, staging / "freemovement-source-library.zip"))
        _write_catalog(staging, archives, _git_revision(root))
        (staging / DIST_MARKER).write_text(json.dumps(DIST_MARKER_CONTENT, sort_keys=True) + "\n", encoding="utf-8")
        if output.exists():
            os.replace(output, backup)
        try:
            os.replace(staging, output)
        except OSError:
            if backup.exists():
                os.replace(backup, output)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return [
            BuiltArchive(item.package_id, item.package_type, item.name, item.version,
                         output / item.path.relative_to(staging), item.file_count, item.size_bytes, item.sha256)
            for item in archives
        ]
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise


def verify_distribution(repository_root: Path, distribution_dir: Path) -> int:
    """Verify all ZIP CRCs, package hashes, catalog entries, and manifest coverage."""
    root = repository_root.expanduser().resolve(strict=True)
    output = distribution_dir.expanduser().resolve(strict=True)
    marker = _read_json_object(output / DIST_MARKER, "distribution marker")
    if marker != DIST_MARKER_CONTENT:
        raise PackageBuildError("unrecognized distribution output directory")
    catalog = _read_json_object(output / PACKAGES_FILE, PACKAGES_FILE)
    records = catalog.get("packages")
    if catalog.get("schema_version") != 1 or not isinstance(records, list) or not records:
        raise PackageBuildError("packages.json is unsupported or empty")
    expected_checksums: dict[str, str] = {}
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise PackageBuildError("packages.json entries must be objects")
        package_id = record.get("id")
        relative = _relative_path(record.get("path"), "package path")
        if relative.as_posix() in seen_paths:
            raise PackageBuildError(f"duplicate archive path in packages.json: {relative}")
        seen_paths.add(relative.as_posix())
        if not isinstance(package_id, str) or package_id in seen_ids:
            raise PackageBuildError(f"invalid or duplicate package id: {package_id!r}")
        seen_ids.add(package_id)
        path = output.joinpath(*relative.parts)
        if path.is_symlink() or not path.is_file() or output not in path.resolve().parents:
            raise PackageBuildError(f"catalog archive is missing or escapes the output directory: {relative}")
        if record.get("sha256") != _file_sha256(path) or record.get("size_bytes") != path.stat().st_size:
            raise PackageBuildError(f"catalog hash or size mismatch: {relative}")
        try:
            with zipfile.ZipFile(path) as archive:
                bad_member = archive.testzip()
                if bad_member is not None:
                    raise PackageBuildError(f"corrupt ZIP member in {relative}: {bad_member}")
                names = archive.namelist()
                if len(names) != len({name.casefold() for name in names}):
                    raise PackageBuildError(f"duplicate ZIP member in {relative}")
                for name in names:
                    member_path = PurePosixPath(name.rstrip("/"))
                    if member_path.is_absolute() or any(part in {"", ".", ".."} for part in member_path.parts):
                        raise PackageBuildError(f"unsafe ZIP member path in {relative}: {name!r}")
                actual_file_count = sum(not item.is_dir() for item in archive.infolist())
                if actual_file_count != record.get("file_count"):
                    raise PackageBuildError(f"catalog file count mismatch: {relative}")
        except zipfile.BadZipFile as exc:
            raise PackageBuildError(f"invalid ZIP archive: {relative}") from exc
        if not isinstance(record.get("file_count"), int) or record["file_count"] < 1:
            raise PackageBuildError(f"invalid file count for {relative}")
        expected_checksums[relative.as_posix()] = record["sha256"]
    expected_checksums[PACKAGES_FILE] = _file_sha256(output / PACKAGES_FILE)
    sums_path = output / CHECKSUMS_FILE
    if sums_path.is_symlink() or not sums_path.is_file():
        raise PackageBuildError("SHA256SUMS is missing or is not a regular file")
    actual_checksums: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match or match.group(2) in actual_checksums:
            raise PackageBuildError(f"invalid SHA256SUMS line: {line!r}")
        actual_checksums[match.group(2)] = match.group(1)
    if actual_checksums != expected_checksums:
        raise PackageBuildError("SHA256SUMS does not exactly cover all archives and packages.json")

    plugins = discover_plugins(root)
    plugin_records = {item["id"]: item for item in records if item.get("type") == "plugin"}
    if set(plugin_records) != {plugin.name for plugin in plugins}:
        raise PackageBuildError("plugin archive catalog does not match the marketplace manifest")
    for plugin in plugins:
        record = plugin_records[plugin.name]
        if record.get("name") != plugin.name or record.get("version") != plugin.version:
            raise PackageBuildError(f"plugin archive catalog identity/version mismatch: {plugin.name}")
        expected_entries = _plugin_entries(plugin)
        expected = {name for name, _, _ in expected_entries}
        archive_path = output / record["path"]
        with zipfile.ZipFile(archive_path) as archive:
            if set(archive.namelist()) != expected:
                raise PackageBuildError(f"plugin archive contents do not match source tree: {plugin.name}")
            for name, source, is_directory in expected_entries:
                if not is_directory and archive.read(name) != source.read_bytes():
                    raise PackageBuildError(f"plugin archive file differs from source: {plugin.name}/{name}")
            for metadata_path in (f"{plugin.name}/plugin.json", f"{plugin.name}/.codex-plugin/plugin.json"):
                try:
                    metadata = json.loads(archive.read(metadata_path))
                except (KeyError, UnicodeError, json.JSONDecodeError) as exc:
                    raise PackageBuildError(f"invalid plugin metadata inside archive: {metadata_path}") from exc
                if metadata.get("name") != plugin.name or metadata.get("version") != plugin.version:
                    raise PackageBuildError(f"plugin archive metadata mismatch: {metadata_path}")
    skill_record = next((item for item in records if item.get("id") == "all-skills"), None)
    source_record = next((item for item in records if item.get("id") == "source-library"), None)
    if skill_record is None or source_record is None:
        raise PackageBuildError("aggregate skill or source-library archive is missing")
    skill_roots = discover_skills(plugins)
    with zipfile.ZipFile(output / skill_record["path"]) as archive:
        try:
            skill_manifest = json.loads(archive.read("DISTRIBUTION.json"))
        except (KeyError, UnicodeError, json.JSONDecodeError) as exc:
            raise PackageBuildError("aggregate skills archive is missing a valid DISTRIBUTION.json") from exc
        expected_skills = {skill_root.name: (plugin, skill_root) for plugin, skill_root in skill_roots}
        manifest_skills = skill_manifest.get("skills")
        actual_skills = {
            item.get("skill"): item for item in manifest_skills if isinstance(item, dict)
        } if isinstance(manifest_skills, list) else {}
        if (len(actual_skills) != len(manifest_skills or [])
                or set(actual_skills) != set(expected_skills)
                or skill_manifest.get("skill_count") != len(expected_skills)):
            raise PackageBuildError("aggregate skills archive does not cover all registered skills")
        for slug, (plugin, skill_root) in expected_skills.items():
            item = actual_skills[slug]
            expected_skill_file_count = sum(
                not is_directory for _, _, is_directory in _tree_entries(skill_root, f"skills/{slug}", skip_git=True)
            )
            if (item.get("plugin") != plugin.name or item.get("plugin_version") != plugin.version
                    or item.get("source_path") != skill_root.relative_to(plugin.root).as_posix()
                    or item.get("file_count") != expected_skill_file_count):
                raise PackageBuildError(f"aggregate skill provenance mismatch: {slug}")
        expected_entries = {"DISTRIBUTION.json"}
        skill_sources: list[tuple[str, Path, bool]] = []
        for _, skill_root in skill_roots:
            tree = _tree_entries(skill_root, f"skills/{skill_root.name}", skip_git=True)
            skill_sources.extend(tree)
            expected_entries.update(name for name, _, _ in tree)
        if set(archive.namelist()) != expected_entries:
            raise PackageBuildError("aggregate skills archive contains missing or unexpected files")
        for name, source, is_directory in skill_sources:
            if not is_directory and archive.read(name) != source.read_bytes():
                raise PackageBuildError(f"aggregate skill file differs from source: {name}")
    with zipfile.ZipFile(output / source_record["path"]) as archive:
        try:
            source_manifest = json.loads(archive.read("DISTRIBUTION.json"))
        except (KeyError, UnicodeError, json.JSONDecodeError) as exc:
            raise PackageBuildError("source-library archive is missing a valid DISTRIBUTION.json") from exc
        expected_libraries = {plugin.name: plugin for plugin in plugins}
        library_records = source_manifest.get("libraries")
        actual_libraries = {
            item.get("plugin"): item for item in library_records if isinstance(item, dict)
        } if isinstance(library_records, list) else {}
        if len(actual_libraries) != len(library_records or []) or set(actual_libraries) != set(expected_libraries):
            raise PackageBuildError("consolidated source archive does not cover all plugin source libraries")
        expected_entries = {"DISTRIBUTION.json"}
        source_files: list[tuple[str, Path, bool]] = []
        for plugin in plugins:
            library_root = _source_library_root(plugin)
            tree = _tree_entries(library_root, f"source-libraries/{plugin.name}", skip_git=True)
            source_files.extend(tree)
            expected_entries.update(name for name, _, _ in tree)
        for filename in ("component-index.json", "source-inventory.json", "migration-map.json"):
            archived = archive.read(f"provenance/{filename}")
            if archived != (root / filename).read_bytes():
                raise PackageBuildError(f"source archive provenance differs from repository: {filename}")
            expected_entries.add(f"provenance/{filename}")
        if set(archive.namelist()) != expected_entries:
            raise PackageBuildError("consolidated source archive contains missing or unexpected files")
        for name, source, is_directory in source_files:
            if not is_directory and archive.read(name) != source.read_bytes():
                raise PackageBuildError(f"source-library archive file differs from source: {name}")
        for plugin_name, plugin in expected_libraries.items():
            record = actual_libraries[plugin_name]
            library_root = _source_library_root(plugin)
            tree_files = [source for _, source, is_directory in _tree_entries(
                library_root, f"source-libraries/{plugin_name}", skip_git=True
            ) if not is_directory]
            expected_file_records = [
                {"path": source.relative_to(library_root).as_posix(), "bytes": source.stat().st_size,
                 "sha256": _file_sha256(source)}
                for source in sorted(tree_files, key=lambda item: item.relative_to(library_root).as_posix().casefold())
            ]
            if (record.get("plugin_version") != plugin.version
                    or record.get("plugin_directory") != plugin.source_path
                    or record.get("source_library_path") != library_root.relative_to(plugin.root).as_posix()
                    or record.get("file_count") != len(tree_files)
                    or record.get("files") != expected_file_records):
                raise PackageBuildError(f"source-library provenance mismatch: {plugin_name}")
        _validate_source_provenance(root, plugins)
    return len(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plugins_parser = subparsers.add_parser("plugins", help="build one complete ZIP for each marketplace plugin")
    plugins_parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root containing the marketplace manifest")
    plugins_parser.add_argument("--output-dir", type=Path, required=True, help="generated distribution directory")
    all_parser = subparsers.add_parser("all", help="build plugin and aggregate distribution archives")
    all_parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root containing the marketplace manifest")
    all_parser.add_argument("--output-dir", type=Path, required=True, help="managed generated distribution directory")
    verify_parser = subparsers.add_parser("verify", help="verify a generated distribution")
    verify_parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root containing sources and manifests")
    verify_parser.add_argument("--distribution-dir", type=Path, required=True, help="generated distribution directory")
    args = parser.parse_args(argv)

    try:
        if args.command == "plugins":
            archives = build_plugin_archives(args.root, args.output_dir)
            total_files = sum(archive.file_count for archive in archives)
            print(f"Built {len(archives)} plugin archives ({total_files} files) in {args.output_dir / PLUGIN_OUTPUT_DIR}")
            for archive in archives:
                print(f"{archive.name} {archive.version}: {archive.path.name} ({archive.size_bytes} bytes, sha256 {archive.sha256})")
            return 0
        if args.command == "all":
            archives = build_distributions(args.root, args.output_dir)
            print(f"Built {len(archives)} archives in {args.output_dir}")
            print(f"Wrote {args.output_dir / PACKAGES_FILE} and {args.output_dir / CHECKSUMS_FILE}")
            return 0
        verified = verify_distribution(args.root, args.distribution_dir)
        print(f"Verified {verified} archives, ZIP integrity, package catalog, and checksums")
        return 0
    except (PackageBuildError, OSError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
