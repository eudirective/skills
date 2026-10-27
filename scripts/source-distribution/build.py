#!/usr/bin/env python3
"""Build deterministic core and national plugin distributions from public-data."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "1.0.0"
AUTHOR = {"name": "eudirective", "email": "eudirective@proton.me"}
ACCEPTED_COPY_STATUS = re.compile(r"^(accepted($|_)|accepted\b|passed$)", re.I)
PATH_FIELDS = {"path", "local_path", "local_copy_path", "document_path", "artifact_path", "local_file_path", "local_document_path"}
HASH_FIELDS = ("sha256", "local_sha256", "local_copy_sha256", "artifact_sha256", "document_sha256", "local_file_sha256", "local_document_sha256", "final_document_sha256")
SKIP_DIRS = {".git", "__pycache__", "node_modules", "captures", "candidates", "candidate-archive", "archive", "archives", "tmp", "temp", "build", "dist"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_source_path(root: Path, raw: str, pack: Path) -> Path:
    p = PurePosixPath(raw.replace("\\", "/"))
    if p.is_absolute() or any(part in {"", "."} for part in p.parts):
        raise ValueError(f"Unsafe source path: {raw}")
    candidates = []
    if p.parts[0] == "source-library":
        candidates.append(root.parent.joinpath(*p.parts))
    else:
        candidates.extend((pack.joinpath(*p.parts), pack / "references" / Path(*p.parts)))
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_relative_to(root.resolve()) and resolved.is_file():
            return resolved
    raise FileNotFoundError(f"Accepted path does not resolve inside source root: {raw}")


def accepted_hash(obj: dict[str, Any]) -> str | None:
    for key in HASH_FIELDS:
        value = obj.get(key)
        if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value):
            return value.lower()
    return None


def accepted_paths(acceptance: Any, root: Path, pack: Path) -> list[tuple[Path, str | None, str]]:
    """Collect only paths nested in explicit local-copy acceptance decisions."""
    found: dict[str, tuple[Path, str | None, str]] = {}

    local_fields = {
        "accepted_derived_texts", "accepted_local_copies", "accepted_local_copy_reviews",
        "accepted_local_copy", "local_copy", "local_copy_decision", "local_copy_decisions", "local_copy_reviews",
    }

    def walk(obj: Any, accepted_context: bool = False, source_id: str = "", field_context: str = "") -> None:
        if isinstance(obj, dict):
            this_id = str(obj.get("source_id") or obj.get("id") or source_id)
            local_status = str(obj.get("local_copy_status") or "")
            record_status = str(obj.get("status") or "")
            explicit_status = bool(ACCEPTED_COPY_STATUS.search(local_status) or ACCEPTED_COPY_STATUS.search(record_status) or obj.get("local_copy_accepted") is True)
            explicit_local = field_context in local_fields
            context = accepted_context or explicit_local or explicit_status
            for key, value in obj.items():
                if key in PATH_FIELDS and isinstance(value, str):
                    local_marked = context
                    if local_marked and not any(part in {"candidates", "candidate-archive", "archives", "captures"} for part in PurePosixPath(value).parts):
                        try:
                            source = safe_source_path(root, value, pack)
                        except (ValueError, FileNotFoundError):
                            raise
                        expected = accepted_hash(obj)
                        sid = this_id or str(obj.get("source_id", ""))
                        found[source.as_posix()] = (source, expected, sid)
                child_context = context or key in local_fields
                walk(value, child_context, this_id, key if isinstance(value, (dict, list)) else "")
        elif isinstance(obj, list):
            for value in obj:
                walk(value, accepted_context, source_id, field_context)

    walk(acceptance)
    return [found[key] for key in sorted(found)]


def document_source_id(path: Path) -> str | None:
    if path.suffix.lower() not in {".md", ".txt"}:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")[:10000]
    patterns = (
        r"(?im)^\s*-?\s*Source ID\s*:\s*`?([^`\s]+)",
        r"(?im)^\s*source_id\s*:\s*['\"]?([^'\"\s]+)",
        r"(?im)^\s*id\s*:\s*['\"]?([^'\"\s]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).rstrip("`\"'")
    return None


def add_id_selected_documents(country: dict[str, Any], acceptance: dict[str, Any], pack: Path, root: Path, found: list[tuple[Path, str | None, str]]) -> list[tuple[Path, str | None, str]]:
    code = country["iso_country_code"]
    ids: set[str] = set()
    if code == "AT":
        records = acceptance.get("records", {})
        if isinstance(records, dict):
            ids = {str(source_id) for source_id, row in records.items() if isinstance(row, dict) and row.get("status") == "accepted"}
    elif code == "NL":
        ids = {str(value) for value in acceptance.get("local_copy_source_ids", [])}
    if not ids:
        return found
    existing = {path for path, _, _ in found}
    for path in sorted((pack / "documents").rglob("*")):
        if not path.is_file() or path in existing:
            continue
        source_id = document_source_id(path) or path.stem
        if source_id in ids:
            found.append((path.resolve(), None, source_id))
            existing.add(path.resolve())
    matched = {source_id for path, _, source_id in found if path.is_relative_to(pack.resolve())}
    missing = ids - matched
    if missing:
        raise ValueError(f"{code} accepted source IDs lack matching local files: {sorted(missing)}")
    return sorted(found, key=lambda item: item[0].as_posix())


def copy_exact(src: Path, dst: Path, writes: dict[str, str], expected_hash: str | None = None) -> None:
    actual = sha256(src)
    if expected_hash and actual != expected_hash:
        raise ValueError(f"Accepted source hash mismatch for {src}: expected {expected_hash}, got {actual}")
    key = dst.as_posix()
    if key in writes and writes[key] != actual:
        raise ValueError(f"Output path collision with differing bytes: {key}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copyfile(src, dst)
    elif sha256(dst) != actual:
        raise ValueError(f"Output path collision with existing bytes: {key}")
    writes[key] = actual


def load_language_index(root: Path, rel: str) -> tuple[Path, dict[str, Any]]:
    path = root / rel
    index = load_json(path)
    if not isinstance(index, dict) or not isinstance(index.get("entries"), list):
        raise ValueError(f"Malformed language index: {rel}")
    return path, index


def indexed_representations(root: Path, index: dict[str, Any]) -> list[tuple[Path, str]]:
    output = []
    seen = set()
    for row in index["entries"]:
        if row.get("storage_state") != "local_representation_present":
            continue
        rel = row.get("canonical_path")
        expected = row.get("local_file_sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            raise ValueError(f"Local source lacks path/hash in {index.get('language')} index")
        source = (root / rel).resolve()
        if not source.is_relative_to(root.resolve()) or not source.is_file():
            raise FileNotFoundError(f"Indexed local representation missing or unsafe: {rel}")
        if sha256(source) != expected:
            raise ValueError(f"Local source differs from indexed hash: {rel}")
        if rel in seen:
            raise ValueError(f"Duplicate indexed local representation: {rel}")
        seen.add(rel)
        output.append((source, expected))
    return sorted(output, key=lambda item: item[0].as_posix())


def write_json(path: Path, value: Any, writes: dict[str, str]) -> None:
    data = json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"Generated file collision: {path}")
    path.write_bytes(data)
    writes[path.as_posix()] = hashlib.sha256(data).hexdigest()


def registry_countries(registry: dict[str, Any]) -> list[dict[str, Any]]:
    countries = registry.get("countries")
    if not isinstance(countries, list) or len(countries) != 31:
        raise ValueError("Country registry must contain exactly 31 countries")
    codes = [c.get("iso_country_code") for c in countries]
    plugins = [c.get("plugin_name") for c in countries]
    directories = [c.get("plugin_directory") for c in countries]
    skills = [c.get("skill_name") for c in countries]
    if len(set(codes)) != 31 or len(set(plugins)) != 31 or len(set(directories)) != 31 or len(set(skills)) != 31:
        raise ValueError("Country, plugin, package-directory, and skill identities must be unique")
    for country in countries:
        slug = re.sub(r"[^a-z0-9]+", "-", country.get("country_name", "").casefold()).strip("-")
        if country.get("plugin_name") != f"fm-{slug}":
            raise ValueError(f"Plugin identity does not match country name: {country.get('iso_country_code')}")
        directory = country.get("plugin_directory")
        if not isinstance(directory, str) or Path(directory).is_absolute() or ".." in Path(directory).parts:
            raise ValueError(f"Unsafe country package directory: {directory}")
        if directory != f"freemovement-law-{country['iso_country_code'].lower()}":
            raise ValueError(f"Country package directory changed unexpectedly: {country['iso_country_code']}")
    module_ids: list[str] = []
    for country in countries:
        modules = country.get("related_operational_modules", [])
        if not isinstance(modules, list):
            raise ValueError(f"Operational modules must be a list for {country['iso_country_code']}")
        for module in modules:
            required = {"module_id", "module_family", "plugin_name", "skill_name", "skill_directory", "skill_version"}
            if not isinstance(module, dict) or not required <= module.keys():
                raise ValueError(f"Malformed operational module for {country['iso_country_code']}")
            if not all(isinstance(module[key], str) and module[key] for key in required):
                raise ValueError(f"Operational module fields must be non-empty strings for {country['iso_country_code']}")
            if Path(module["skill_directory"]).is_absolute() or ".." in Path(module["skill_directory"]).parts:
                raise ValueError(f"Unsafe operational module path for {country['iso_country_code']}")
            if module.get("template_directory") and (Path(module["template_directory"]).is_absolute() or ".." in Path(module["template_directory"]).parts):
                raise ValueError(f"Unsafe operational module template path for {country['iso_country_code']}")
            if module["plugin_name"] == country["plugin_name"] and not module.get("template_directory"):
                raise ValueError(f"Country-owned operational module lacks a template directory: {module['module_id']}")
            module_ids.append(module["module_id"])
    if len(module_ids) != len(set(module_ids)):
        raise ValueError("Operational module identities must be unique")
    return sorted(countries, key=lambda x: x["iso_country_code"])


def registry_operational_modules(registry: dict[str, Any], countries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten country-owned and core-owned module records for generic discovery."""
    modules: list[dict[str, Any]] = []
    for country in countries:
        for source in country.get("related_operational_modules", []):
            module = dict(source)
            module.setdefault("jurisdiction", country["iso_country_code"])
            module.setdefault("notes_directory", country["upstream_source_directory"])
            module.setdefault("notes_plugin_name", country["plugin_name"])
            module["package_directory"] = country["plugin_directory"]
            modules.append(module)
    extras = registry.get("additional_operational_modules", [])
    if not isinstance(extras, list):
        raise ValueError("additional_operational_modules must be a list")
    for source in extras:
        if not isinstance(source, dict):
            raise ValueError("Malformed additional operational module")
        module = dict(source)
        module.setdefault("package_directory", ".")
        modules.append(module)
    required = {"module_id", "module_family", "jurisdiction", "plugin_name", "skill_directory", "skill_version", "notes_directory"}
    known_plugin_names = {registry["core_plugin"], *(country["plugin_name"] for country in countries)}
    ids = []
    for module in modules:
        if not required <= module.keys() or not all(isinstance(module[key], str) and module[key] for key in required):
            raise ValueError("Operational module record lacks required identity, package, or notes fields")
        module.setdefault("notes_plugin_name", module["plugin_name"])
        if module["plugin_name"] not in known_plugin_names or module["notes_plugin_name"] not in known_plugin_names:
            raise ValueError(f"Operational module package is not registered: {module['module_id']}")
        for key in ("skill_directory", "package_directory", "notes_directory"):
            raw = module[key]
            if Path(raw).is_absolute() or ".." in Path(raw).parts:
                raise ValueError(f"Unsafe operational module {key}: {raw}")
        if module.get("template_directory") and (Path(module["template_directory"]).is_absolute() or ".." in Path(module["template_directory"]).parts):
            raise ValueError(f"Unsafe operational module template path: {module['template_directory']}")
        ids.append(module["module_id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Operational module identities must be unique")
    return modules


MALTA_LANGUAGE_COVERAGE = {"both_verified", "english_only", "maltese_only", "neither_verified"}
MALTA_EDITION_ALIGNMENT = {"matched", "mismatch", "not_verified"}
MALTA_COMPARISON_STATUS = {"no_material_difference_identified", "material_difference_flagged", "not_checked"}
MALTA_PRECEDENCE_STATUS = {"maltese_default", "specific_statutory_exception", "not_applicable", "unverified"}
MALTA_STORAGE_STATUS = {"local_accepted", "official_link_only", "unaccepted_candidate", "unavailable"}


def validate_malta_pair_register(pairs: dict[str, Any], source_list_text: str) -> None:
    """Validate declared Malta pair metadata without asserting legal meaning."""
    if not isinstance(pairs, dict) or pairs.get("schema_version") != SCHEMA or pairs.get("jurisdiction") != "MT":
        raise ValueError("Malformed Malta language-pair register")
    instruments = pairs.get("instruments")
    if not isinstance(instruments, list) or not instruments:
        raise ValueError("Malta language-pair register has no instrument records")
    instrument_ids: set[str] = set()
    source_ids: set[str] = set()
    for row in instruments:
        if not isinstance(row, dict):
            raise ValueError("Malformed Malta instrument record")
        instrument_id = row.get("instrument_id")
        if not isinstance(instrument_id, str) or not instrument_id or instrument_id in instrument_ids:
            raise ValueError("Malta instrument IDs must be present and unique")
        instrument_ids.add(instrument_id)
        source_id = row.get("source_id")
        if source_id is not None:
            if not isinstance(source_id, str) or source_id in source_ids:
                raise ValueError("Malta source IDs must be unique when present")
            source_ids.add(source_id)

        urls = row.get("official_urls")
        availability = row.get("language_availability")
        if not isinstance(urls, dict) or not isinstance(availability, dict):
            raise ValueError(f"Malta language evidence is missing for {instrument_id}")
        verified = {
            "en": availability.get("english_text_language_verified") is True,
            "mt": availability.get("maltese_text_language_verified") is True,
        }
        for language, is_verified in verified.items():
            url = urls.get(language)
            if is_verified and (not isinstance(url, str) or not url.startswith("https://")):
                raise ValueError(f"Verified {language} text lacks an official URL for {instrument_id}")
        expected_coverage = (
            "both_verified" if verified["en"] and verified["mt"] else
            "english_only" if verified["en"] else
            "maltese_only" if verified["mt"] else
            "neither_verified"
        )
        if availability.get("language_coverage") != expected_coverage:
            raise ValueError(f"Language coverage contradicts text-language evidence for {instrument_id}")
        if expected_coverage == "both_verified":
            language_evidence = row.get("language_verification_evidence")
            if not isinstance(language_evidence, dict):
                raise ValueError(f"Both verified languages need returned-document evidence for {instrument_id}")
            for language in ("en", "mt"):
                evidence = language_evidence.get(language)
                if not isinstance(evidence, dict):
                    raise ValueError(f"Missing returned-document evidence for {language} in {instrument_id}")
                document_url = evidence.get("document_url")
                observed_language = evidence.get("observed_text_language")
                checked_on = evidence.get("checked_on")
                if (
                    not isinstance(document_url, str)
                    or not document_url.startswith("https://legislation.mt/")
                    or observed_language != language
                    or not isinstance(checked_on, str)
                    or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked_on)
                ):
                    raise ValueError(f"Invalid returned-document language evidence for {language} in {instrument_id}")

        pair_status = row.get("pairing_status")
        editions = row.get("editions")
        if not isinstance(pair_status, dict) or not isinstance(editions, dict):
            raise ValueError(f"Malta edition-pair evidence is missing for {instrument_id}")
        alignment = pair_status.get("edition_alignment")
        if alignment not in MALTA_EDITION_ALIGNMENT:
            raise ValueError(f"Invalid edition-alignment status for {instrument_id}")
        en_date = (editions.get("en") or {}).get("publisher_date")
        mt_date = (editions.get("mt") or {}).get("publisher_date")
        if alignment == "matched" and (not en_date or not mt_date or en_date != mt_date):
            raise ValueError(f"Matched editions require equal recorded dates for {instrument_id}")
        if alignment == "mismatch" and (not en_date or not mt_date or en_date == mt_date):
            raise ValueError(f"Mismatched editions require differing recorded dates for {instrument_id}")

        comparison = pair_status.get("substantive_comparison")
        if comparison not in MALTA_COMPARISON_STATUS:
            raise ValueError(f"Invalid substantive-comparison status for {instrument_id}")
        if comparison == "no_material_difference_identified" and not row.get("comparison_evidence"):
            raise ValueError(f"A no-difference assessment needs recorded review evidence for {instrument_id}")
        precedence = row.get("precedence_rule")
        storage = row.get("local_copy_status")
        if precedence not in MALTA_PRECEDENCE_STATUS or storage not in MALTA_STORAGE_STATUS:
            raise ValueError(f"Invalid precedence or storage status for {instrument_id}")
        paths = row.get("local_representation_paths") or {}
        if storage == "local_accepted" or any(paths.get(language) for language in ("en", "mt")):
            raise ValueError("The current Malta source policy does not accept local national-law copies")

        mirror = row.get("verification_status") or {}
        for field, expected in (
            ("language_coverage", expected_coverage),
            ("edition_alignment", alignment),
            ("substantive_comparison", comparison),
            ("precedence_rule", precedence),
            ("storage_status", storage),
        ):
            if mirror.get(field) != expected:
                raise ValueError(f"Verification status contradicts {field} for {instrument_id}")

        # Preserve each English URL already accepted as a source record. The
        # extra constitution/court-law controls have no source_id in that list.
        english_url = urls.get("en")
        if source_id and (not isinstance(english_url, str) or english_url not in source_list_text):
            raise ValueError(f"Accepted English source reference is missing for {source_id}")


def fingerprint_inputs(inputs: dict[str, str]) -> str:
    """Fingerprint a component's own sorted inputs, not the entire upstream repository."""
    return hashlib.sha256(json_bytes(dict(sorted(inputs.items())))).hexdigest()


def bump_patch(version: str) -> str:
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid semantic version in prior manifest: {version}")
    return f"{int(parts[0])}.{int(parts[1])}.{int(parts[2]) + 1}"


def choose_component_versions(
    old: dict[str, Any] | None,
    input_fingerprint: str,
    skill_fingerprints: dict[str, str],
    initial_plugin: str,
    initial_skills: dict[str, str],
) -> tuple[str, dict[str, str]]:
    """Select versions from only this component's inputs and skills."""
    if old is None:
        return initial_plugin, dict(initial_skills)
    if not isinstance(old, dict):
        raise ValueError("Prior component manifest must be an object")
    if not isinstance(old.get("input_fingerprint"), str):
        raise ValueError("Prior component manifest lacks its input fingerprint")
    old_plugin = str(old.get("plugin_version", ""))
    if not re.fullmatch(r"\d+\.\d+\.\d+", old_plugin):
        raise ValueError(f"Invalid semantic version in prior manifest: {old_plugin}")
    plugin_version = old_plugin if old.get("input_fingerprint") == input_fingerprint else bump_patch(old_plugin)
    old_skills = old.get("skill_versions", {})
    old_fingerprints = old.get("skill_fingerprints", {})
    if not isinstance(old_skills, dict) or not isinstance(old_fingerprints, dict):
        raise ValueError("Prior component skill version metadata is malformed")
    versions: dict[str, str] = {}
    for skill_name, fingerprint in skill_fingerprints.items():
        old_version = old_skills.get(skill_name)
        if old_version and old_fingerprints.get(skill_name) == fingerprint:
            versions[skill_name] = old_version
        elif old_version:
            versions[skill_name] = bump_patch(str(old_version))
        else:
            versions[skill_name] = initial_skills.get(skill_name, "0.1.0")
    return plugin_version, versions


def build_source_manifest(
    component: str,
    version: str,
    skill_versions: dict[str, str],
    skill_fingerprints: dict[str, str],
    upstream_revision: str,
    upstream_trees: dict[str, str],
    inputs: dict[str, str],
    outputs: dict[str, str],
    compatibility: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "component_id": component,
        "plugin_version": version,
        "skill_versions": dict(sorted(skill_versions.items())),
        "skill_fingerprints": dict(sorted(skill_fingerprints.items())),
        "source_contract_version": "1.0.0",
        "compatibility": compatibility,
        "upstream_revision": upstream_revision,
        "upstream_trees": dict(sorted(upstream_trees.items())),
        "input_fingerprint": fingerprint_inputs(inputs),
        "distributed_fingerprint": hashlib.sha256(json_bytes(dict(sorted(outputs.items())))).hexdigest(),
        "input_files": dict(sorted(inputs.items())),
        "distributed_files": dict(sorted(outputs.items())),
    }


def file_hashes(root: Path, exclude: set[str] | None = None) -> dict[str, str]:
    excluded = exclude or set()
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).as_posix() not in excluded
    }


def update_plugin_version(plugin_dir: Path, version: str, core_skill_version: str, source_skill_version: str) -> None:
    for rel in ("plugin.json", ".codex-plugin/plugin.json"):
        path = plugin_dir / rel
        if not path.is_file():
            raise FileNotFoundError(f"Core plugin template is missing {rel}")
        data = load_json(path)
        data["version"] = version
        data["author"] = AUTHOR
        if rel == ".codex-plugin/plugin.json" and isinstance(data.get("interface"), dict):
            data["interface"]["developerName"] = AUTHOR["name"]
            data["interface"]["displayName"] = "freemovement-law"
        path.write_bytes(json_bytes(data))
    core_skill = plugin_dir / "skills/eudirective-core/SKILL.md"
    if not core_skill.is_file():
        raise FileNotFoundError("Core template is missing eudirective-core/SKILL.md")
    text = core_skill.read_text(encoding="utf-8")
    quote = chr(96)
    text = re.sub(r"(?m)^- Current version: .*?$", f"- Current version: {quote}{core_skill_version}{quote}", text, count=1)
    text = re.sub(r"(?m)^- Plugin version: .*?$", f"- Plugin version: {quote}{version}{quote}", text, count=1)
    text = re.sub(
        r"(?m)^(For each visible answer or report produced with this skill, identify near the top: \*\*Skill: eudirective-core v)\d+\.\d+\.\d+(\*\*.*)$",
        rf"\g<1>{core_skill_version}\g<2>", text, count=1,
    )
    core_skill.write_text(text, encoding="utf-8", newline="\n")


def prune_monolithic_source_skill(plugin_dir: Path) -> None:
    source_skill = plugin_dir / "skills/eudirective-source-library"
    if not source_skill.is_dir():
        raise FileNotFoundError("Core template lacks the source-library skill to migrate")
    keep_files = {"SKILL.md", "README.md", "references/legal-text-edition-policy.md"}
    for path in sorted(source_skill.rglob("*"), reverse=True):
        if path.is_file():
            if path.relative_to(source_skill).as_posix() not in keep_files:
                path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    for name in ("SKILL.md",):
        if not (source_skill / name).is_file():
            raise FileNotFoundError(f"Core source skill missing {name}")


def first_response_notice() -> str:
    return """## First response: disclaimer and use check

On the first visible response in each conversation where this skill is invoked, begin with this disclaimer before substantive analysis:

> Disclaimer: freemovement-law provides informational, source-grounded visa guidance, not legal representation or a guaranteed outcome. Verify current law and important deadlines with official sources or qualified counsel.

Treat use as non-personal only when the prompt clearly indicates professional or organizational use for an employer, business, organization, client, customer, another third party, paid services, or deployment of the plugin for others. In that case, add once after the disclaimer: **Non-personal use requires a license; request one at eudirective@proton.me.**

For personal, ordinary personal, or unspecified use, do not mention licensing or the email address. Do not infer non-personal use from the legal subject, a job title, or help with a family member's personal case. Ask a neutral clarification only when use is genuinely ambiguous and the distinction is necessary to answer. Never contact anyone or claim to know licensing status. Repeat the notice only if the use context materially changes. These are skill instructions, not a host-level chat-start guarantee."""


def write_core_source_skill(plugin_dir: Path, version: str) -> None:
    source_skill = plugin_dir / "skills/eudirective-source-library"
    text = f'''---
name: eudirective-source-library
description: Locate the EU source corpus bundled with eudirective-core and resolve national source libraries through the generated jurisdiction registry. Use alongside eudirective-core for source-grounded FreeMovement work.
---

# eudirective source library

{first_response_notice()}

**Skill version:** {version}

The shared English EU corpus is under `eudirective-core/references/source-library/`. It is a versioned snapshot. Use its indexes and provenance records to locate sources; consult official publishers for material current-law questions.

National source libraries are separate plugins named by the generated `eudirective-core/references/national-source-routing.json` registry. Use the country skill when that jurisdiction materially matters. Its source-acceptance record distinguishes official external links, accepted local copies, topic coverage, and unresolved source gaps.

Do not assume a national plugin is installed from its presence in the registry. If the host exposes an available-skill catalog, verify the exact plugin name and compatibility. If the catalog is partial or unavailable, report discovery as unknown. Continue with EU sources and official-source research when a national plugin is unavailable.

Non-English EU representations are distributed only to countries listed for that language. Malta's national English and Maltese sources remain distinct from Maltese-language EU instruments. See the Malta skill for its bilingual checks and its source-redistribution limits.

The bundled corpus and component fingerprints do not certify source currentness, completeness, legal equivalence, or legal meaning. A local file hash confirms bytes only.
'''
    (source_skill / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
    (source_skill / "README.md").write_text(
        "# EU and national source libraries\n\nThe English EU corpus is bundled in `eudirective-core`. National source packs are independently distributed country plugins listed in the core routing registry. See the skill instructions for source-selection and version limits.\n",
        encoding="utf-8",
        newline="\n",
    )


def country_skill(country: dict[str, Any], maltese: bool = False) -> str:
    name = country["country_name"]
    code = country["iso_country_code"]
    if maltese:
        return f'''---\nname: {country['skill_name']}\ndescription: Use when FreeMovement consultation requires Malta national sources. Apply the Malta bilingual verification profile for material Maltese national law.\n---\n\n# Malta national source library\n\nUse this skill alongside `eudirective-core`; it supplies Malta-owned sources and language checks, not a separate legal-reasoning engine.\n\n- Determine whether a source is Maltese national law, a judgment, official guidance, or an EU instrument before applying language rules.\n- For national statutes, seek the official English and Maltese versions under the same ELI identity. Preserve both official representations and align their editions before comparing relevant provisions.\n- Apply Maltese statutory-text precedence only where Article 74 of the Constitution governs, after checking for a specific statutory exception. Do not apply that rule automatically to judgments, proceedings, or EU law.\n- Identify the language actually used in judicial records and check the applicable court-language provisions separately.\n- If a counterpart, edition, exception, or comparison is unverified, name the exact gap and its effect while continuing useful research.\n- Follow `references/source-library/malta/references/source-acceptance.json` for accepted official links and local-copy restrictions. No national-law local copies are currently accepted; do not treat an EU Maltese-language source as Malta national law.\n- See `references/source-library/malta/references/language-pairs.json` and `references/malta-bilingual-verification.md` for the instrument register and detailed workflow.\n- Check this package's component version with `scripts/session_version_check.mjs` when the host can execute Node; otherwise disclose that package currentness is unknown.\n'''
    return f'''---\nname: {country['skill_name']}\ndescription: Use when FreeMovement consultation requires {name} national sources. Read with eudirective-core; this skill provides source records and country-specific verification limits, not a separate legal-reasoning engine.\n---\n\n# {name} national source library\n\nUse this skill with `eudirective-core` when {name} is a materially relevant jurisdiction.\n\n- Determine the source's publisher, instrument or record identity, language, displayed version/date, scope, and limitations from the official publisher.\n- Treat the bundled source records as a versioned snapshot. Check the official publisher for material current-law questions when available.\n- Keep external-reference acceptance, local-copy acceptance, topic coverage, and country-review completion separate.\n- Use local texts only where the source acceptance record explicitly accepts that exact representation; its hash confirms bytes, not legal meaning or currentness.\n- If a source is absent, outdated, link-only, or outside its recorded scope, say what is missing and its effect, and continue with available official-source research.\n- Country acceptance and index records are under `references/source-library/{country['upstream_source_directory']}/references/`.\n- Compare this package's component manifest with the published component index using `scripts/session_version_check.mjs` when Node is available. If execution is unavailable, report package currentness as unknown; do not claim the package is current.\n'''


def classify_inventory(root: Path, registry: dict[str, Any], accepted: set[str], language_paths: set[str], english_paths: set[str]) -> list[dict[str, Any]]:
    country_dirs = {c["upstream_source_directory"] for c in registry["countries"]}
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        parts = PurePosixPath(rel).parts
        if any(part in SKIP_DIRS for part in parts):
            category, action = "maintenance_or_candidate_material", "excluded_by_path_policy"
        elif rel in english_paths:
            category, action = "core_english_eu_text", "distributed_to_core"
        elif rel in language_paths:
            category, action = "shared_non_english_eu_text", "distributed_to_registered_countries"
        elif parts[0] in country_dirs:
            if len(parts) > 1 and parts[1] == "references":
                category, action = "national_source_metadata", "distributed_to_country_plugin"
            elif len(parts) > 1 and parts[1] == "documents":
                if rel in accepted:
                    if "attachments" in parts:
                        category, action = "accepted_national_source_attachment", "distributed_to_country_plugin"
                    else:
                        category, action = "accepted_national_source_text", "distributed_to_country_plugin"
                elif path.name.lower() == "readme.md":
                    category, action = "national_source_metadata", "distributed_to_country_plugin"
                else:
                    category, action = "unaccepted_or_unreviewed_national_text", "excluded_not_accepted"
            elif path.name in {"README.md", "SKILL.md"}:
                category, action = "national_source_metadata", "distributed_to_country_plugin"
            elif parts[-1].endswith((".py", ".mjs", ".js", ".sh", ".lock", ".txt")):
                category, action = "maintenance_material", "excluded_from_runtime_plugin"
            else:
                category, action = "country_pack_auxiliary_metadata", "excluded_by_runtime_distribution_policy"
        elif rel.startswith("core/"):
            category, action = "unindexed_core_language_or_source", "excluded_not_indexed"
        elif path.name.startswith(("shared-core-index-", "national-language-index-", "national-language-state-")) or path.name in {"retrieval-index.json", "core-source-pack-manifest-0.7.0.json", "core-source-pack-manifest-0.8.0.json"}:
            category, action = "source_index_or_manifest", "distributed_as_required_by_registry"
        elif parts[0] in {"references", "visa-code-handbook-i-2020"}:
            category, action = "shared_source_metadata", "distributed_only_when_referenced"
        elif path.name == "README.md":
            category, action = "source_library_readme", "distributed_to_core"
        elif path.name.endswith((".py", ".mjs", ".js", ".sh", ".lock", ".txt")) or parts[0] in {"scripts", "runtime-storage.mjs"}:
            category, action = "maintenance_material", "excluded_from_runtime_plugin"
        elif path.name.endswith((".json", ".md")):
            category, action = "shared_source_metadata", "inventory_recorded_not_copied_by_default"
        else:
            raise ValueError(f"Unclassified source input: {rel}")
        rows.append({"source_path": rel, "classification": category, "distribution_action": action, "sha256": sha256(path), "bytes": path.stat().st_size})
    return rows


def build(
    source_root: Path,
    module_notes_root: Path,
    registry_path: Path,
    output_root: Path,
    upstream_revision: str,
    plugin_root: Path,
    previous_root: Path | None = None,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    module_notes_root = module_notes_root.resolve()
    registry_path = registry_path.resolve()
    output_root = output_root.resolve()
    plugin_root = plugin_root.resolve()
    previous_root = previous_root.resolve() if previous_root else plugin_root.parent
    if not source_root.is_dir() or not module_notes_root.is_dir() or not plugin_root.is_dir():
        raise FileNotFoundError("Source library, module-notes, or core plugin template is missing")
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"Output root must be empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    registry = load_json(registry_path)
    countries = registry_countries(registry)
    operational_modules = registry_operational_modules(registry, countries)
    malta_record = next((c for c in countries if c["iso_country_code"] == "MT"), None)
    if not malta_record or malta_record.get("verification_profile") != "malta_bilingual":
        raise ValueError("Malta must declare verification_profile=malta_bilingual")

    generator_hash = sha256(Path(__file__).resolve())
    registry_hash = sha256(registry_path)
    en_index_path, en_index = load_language_index(source_root, "shared-core-index-EN.json")
    english = indexed_representations(source_root, en_index)
    if len(english) != int(en_index.get("logical_source_count", -1)):
        raise ValueError("English core local representation count differs from its index")

    language_paths: set[str] = set()
    language_indexes: dict[str, tuple[Path, dict[str, Any]]] = {}
    for country in countries:
        for item in country.get("eu_language_representation_inputs", []):
            rel = item.get("shared_core_index")
            if not rel:
                continue
            idx_path, idx = load_language_index(source_root, rel)
            language_indexes[rel] = (idx_path, idx)
            for source, _ in indexed_representations(source_root, idx):
                language_paths.add(source.relative_to(source_root).as_posix())

    accepted_by_country: dict[str, list[tuple[Path, str | None, str]]] = {}
    accepted_paths_all: set[str] = set()
    for country in countries:
        pack = source_root / country["upstream_source_directory"]
        expected_pack = country.get("national_source_inputs", {}).get("pack_root")
        if expected_pack != f"source-library/{country['upstream_source_directory']}":
            raise ValueError(f"Registry pack root mismatch for {country['iso_country_code']}: {expected_pack}")
        acceptance_rel = country["national_source_inputs"]["acceptance_record"]
        if not acceptance_rel.startswith("references/"):
            raise ValueError(f"Acceptance record must be under references/: {acceptance_rel}")
        acceptance_file = pack / "references" / acceptance_rel.split("references/", 1)[-1]
        if not acceptance_file.is_file():
            raise FileNotFoundError(f"Missing acceptance record for {country['iso_country_code']}: {acceptance_file}")
        acceptance = load_json(acceptance_file)
        docs = accepted_paths(acceptance, source_root, pack)
        docs = add_id_selected_documents(country, acceptance, pack, source_root, docs)
        accepted_by_country[country["upstream_source_directory"]] = docs
        accepted_paths_all.update(p.relative_to(source_root).as_posix() for p, _, _ in docs)

    inventory = classify_inventory(source_root, registry, accepted_paths_all, language_paths,
                                   {p.relative_to(source_root).as_posix() for p, _ in english})
    for row in inventory:
        if not row.get("classification") or not row.get("distribution_action"):
            raise ValueError(f"Unclassified source input: {row.get('source_path')}")
    if len({row["source_path"] for row in inventory}) != len(inventory):
        raise ValueError("Source inventory contains duplicate paths")

    component_manifests: dict[str, dict[str, Any]] = {}
    migration_rows: list[dict[str, Any]] = []

    def choose_versions(package_name: str, package_directory: str, manifest_rel: str, input_fingerprint: str,
                        skill_fingerprints: dict[str, str], initial_plugin: str,
                        initial_skills: dict[str, str]) -> tuple[str, dict[str, str]]:
        old_path = previous_root / package_directory / manifest_rel
        old = load_json(old_path) if old_path.is_file() else None
        return choose_component_versions(
            old, input_fingerprint, skill_fingerprints, initial_plugin, initial_skills
        )

    source_repo = source_root.parent.resolve()
    if module_notes_root.parent.resolve() != source_repo or source_root.name != "source-library":
        raise ValueError("Source library and module notes must come from one public-data checkout")
    try:
        source_tree_sha = subprocess.run(
            ["git", "-C", str(source_repo), "rev-parse", f"{upstream_revision}:source-library"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        module_notes_tree_sha = subprocess.run(
            ["git", "-C", str(source_repo), "rev-parse", f"{upstream_revision}:module-notes"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("Could not resolve exact upstream tree fingerprints") from exc
    if not re.fullmatch(r"[0-9a-f]{40}", source_tree_sha) or not re.fullmatch(r"[0-9a-f]{40}", module_notes_tree_sha):
        raise ValueError("Invalid upstream tree fingerprint")

    notes_plugin_by_directory = {c["upstream_source_directory"]: c["plugin_name"] for c in countries}
    for module in operational_modules:
        directory = module["notes_directory"]
        plugin_name = module.get("notes_plugin_name", module["plugin_name"])
        prior = notes_plugin_by_directory.get(directory)
        if prior and prior != plugin_name:
            raise ValueError(f"Conflicting module-note ownership for {directory}: {prior} / {plugin_name}")
        notes_plugin_by_directory[directory] = plugin_name
    package_directory_by_plugin = {registry["core_plugin"]: "."}
    package_directory_by_plugin.update({country["plugin_name"]: country["plugin_directory"] for country in countries})
    for module in operational_modules:
        package_name = module["plugin_name"]
        package_directory = "." if package_name == registry["core_plugin"] else module["package_directory"]
        previous_directory = package_directory_by_plugin.get(package_name)
        if previous_directory is not None and previous_directory != package_directory:
            raise ValueError(f"Package-directory mapping conflict for {package_name}")
        package_directory_by_plugin[package_name] = package_directory
    module_notes_by_plugin: dict[str, list[Path]] = {name: [] for name in package_directory_by_plugin}
    for note in sorted(module_notes_root.rglob("*")):
        if not note.is_file() or any(part in SKIP_DIRS for part in note.relative_to(module_notes_root).parts):
            continue
        relative = note.relative_to(module_notes_root)
        owner = relative.parts[0] if relative.parts else ""
        if relative == Path("README.md"):
            continue
        if owner not in notes_plugin_by_directory:
            raise ValueError(f"Module note has no registered package owner: {relative.as_posix()}")
        package_owner = notes_plugin_by_directory[owner]
        module_notes_by_plugin[package_owner].append(note)

    def core_ignore(directory: str, names: list[str]) -> set[str]:
        rel = Path(directory).resolve().relative_to(plugin_root)
        ignored = {name for name in names if name in {".git", "__pycache__", "node_modules", "dist", "build"}}
        source_rel = Path("skills/eudirective-source-library")
        if rel == source_rel:
            ignored.update(name for name in names if name not in {"SKILL.md", "README.md", "references"})
        elif rel == source_rel / "references":
            ignored.update(name for name in names if name != "legal-text-edition-policy.md")
        core_refs = Path("skills/eudirective-core/references")
        if rel == core_refs:
            ignored.update(name for name in names if name in {"source-library", "component-manifest.json", "national-source-routing.json"})
        elif rel == Path("skills/eudirective-core/scripts"):
            ignored.update(name for name in names if name == "source_library_paths.py")
        elif rel == Path("skills/eudirective-ac-turkiye/scripts"):
            ignored.update(name for name in names if name == "source_library_paths.py")
        return ignored

    core = output_root / registry["core_plugin"]
    shutil.copytree(plugin_root, core, ignore=core_ignore)
    prune_monolithic_source_skill(core)
    write_core_source_skill(core, "1.1.0")
    core_data = core / "skills/eudirective-core/references/source-library"
    core_data.mkdir(parents=True, exist_ok=True)
    core_input_files: dict[str, str] = {
        "registry/country-registry.json": registry_hash,
        "distributor/build.py": generator_hash,
    }
    module_notes_readme_text = (
        "# Module notes bundled with eudirective-core\n\n"
        "This directory contains source identity and scope notes for operational modules that the package registry assigns to the core package. "
        "Notes owned by a country module are shipped with that country package under its source-library references. "
        "Consult the generated national source routing registry to identify each module's package and note location.\n\n"
        "These notes are not authoritative source texts and do not establish current law. Verify material legal and procedural claims against current official publications.\n"
    )
    target = core_data / "module-notes/README.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(module_notes_readme_text, encoding="utf-8", newline="\n")
    module_notes_readme_sha = hashlib.sha256(module_notes_readme_text.encode("utf-8")).hexdigest()
    core_input_files["generated/module-notes/README.md"] = module_notes_readme_sha
    migration_rows.append({
        "source_path": "generated-by-distributor:module-notes/README.md",
        "target_path": f"{registry['core_plugin']}/skills/eudirective-core/references/source-library/module-notes/README.md",
        "classification": "generated_core_module_note_ownership_readme", "sha256": module_notes_readme_sha,
    })
    for note in module_notes_by_plugin[registry["core_plugin"]]:
        relative = note.relative_to(module_notes_root)
        target = core_data / "module-notes" / relative
        copy_exact(note, target, {})
        inputs_key = f"module-notes/{relative.as_posix()}"
        core_input_files[inputs_key] = sha256(note)
        migration_rows.append({
            "source_path": inputs_key,
            "target_path": f"{registry['core_plugin']}/skills/eudirective-core/references/source-library/{inputs_key}",
            "classification": "core_owned_operational_module_note",
            "sha256": sha256(note),
        })
    eea_note_candidates = (
        plugin_root / "skills/eudirective-core/references/eea-switzerland-country-expansion.md",
        plugin_root / "skills/eudirective-source-library/references/eea-switzerland-country-expansion.md",
        previous_root / registry["core_plugin"] / "skills/eudirective-core/references/eea-switzerland-country-expansion.md",
    )
    eea_note_source = next((path for path in eea_note_candidates if path.is_file()), None)
    if eea_note_source is None:
        raise FileNotFoundError("The EEA/Switzerland core-scope note is required during migration")
    eea_note_target = core / "skills/eudirective-core/references/eea-switzerland-country-expansion.md"
    copy_exact(eea_note_source, eea_note_target, {})
    core_input_files["core-template/eea-switzerland-country-expansion.md"] = sha256(eea_note_source)
    core_static = file_hashes(plugin_root, {
        "skills/eudirective-source-library/SKILL.md",
        "skills/eudirective-source-library/README.md",
    })
    generated_exact = {
        "skills/eudirective-core/references/national-source-routing.json",
        "skills/eudirective-core/references/component-manifest.json",
        "skills/eudirective-core/scripts/source_library_paths.py",
        "skills/eudirective-ac-turkiye/scripts/source_library_paths.py",
    }
    core_static = {
        rel: digest for rel, digest in core_static.items()
        if rel not in generated_exact and not rel.startswith("skills/eudirective-core/references/source-library/")
    }
    for versioned_rel in ("plugin.json", ".codex-plugin/plugin.json"):
        if versioned_rel in core_static:
            normalized = load_json(plugin_root / versioned_rel)
            normalized["version"] = "<version>"
            core_static[versioned_rel] = hashlib.sha256(json_bytes(normalized)).hexdigest()
    for skill_rel in [rel for rel in core_static if rel.endswith("/SKILL.md")]:
        skill_text = (plugin_root / skill_rel).read_text(encoding="utf-8")
        normalized_skill = chr(10).join(
            line for line in skill_text.splitlines()
            if not line.startswith(("- Current version:", "- Plugin version:"))
        ) + chr(10)
        normalized_skill = re.sub(
            r"(?m)(Skill: eudirective-core v)\d+\.\d+\.\d+",
            r"\g<1><version>", normalized_skill,
        )
        core_static[skill_rel] = hashlib.sha256(normalized_skill.encode("utf-8")).hexdigest()
    for rel, digest in core_static.items():
        if rel.startswith("skills/eudirective-source-library/") and rel != "skills/eudirective-source-library/references/legal-text-edition-policy.md":
            continue
        core_input_files[f"core-template/{rel}"] = digest

    for source, expected in english:
        rel = source.relative_to(source_root)
        dest = core_data / rel
        copy_exact(source, dest, {}, expected)
        core_input_files[f"source-library/{rel.as_posix()}"] = expected
        migration_rows.append({
            "source_path": f"source-library/{rel.as_posix()}",
            "target_path": f"{registry['core_plugin']}/skills/eudirective-core/references/source-library/{rel.as_posix()}",
            "classification": "core_english_eu_text", "sha256": expected,
        })
    core_inputs = [en_index_path, source_root / "retrieval-index.json",
                   source_root / "core-source-pack-manifest-0.7.0.json",
                   source_root / "core-source-pack-manifest-0.8.0.json",
                   source_root / "references/guidance-manifest.json"]
    source_readme = source_root / "README.md"
    if source_readme.is_file():
        core_inputs.append(source_readme)
    for source in core_inputs:
        if not source.is_file():
            continue
        rel = source.relative_to(source_root)
        dest = core_data / rel if rel.name != "README.md" else core_data / "upstream-library-readme.md"
        copy_exact(source, dest, {})
        core_input_files[f"source-library/{rel.as_posix()}"] = sha256(source)
        inventory_row = next((row for row in inventory if row["source_path"] == rel.as_posix()), None)
        migration_rows.append({
            "source_path": rel.as_posix(),
            "target_path": dest.relative_to(output_root).as_posix(),
            "classification": inventory_row["classification"] if inventory_row else "core_source_metadata",
            "sha256": sha256(source),
        })
    routing = {
        "schema_version": SCHEMA,
        "core_plugin": registry["core_plugin"],
        "core_compatibility_contract": registry.get("core_compatibility_contract", {}),
        "countries": [{
            "iso_country_code": c["iso_country_code"],
            "country_name": c["country_name"],
            "jurisdiction_class": c["jurisdiction_class"],
            "plugin_name": c["plugin_name"],
            "package_directory": c["plugin_directory"],
            "skill_name": c["skill_name"],
            "source_library_directory": c["upstream_source_directory"],
            "official_languages": c.get("official_languages", []),
            "verification_profile": c.get("verification_profile", "national_source_review"),
            "core_compatibility_contract": c.get("core_compatibility_contract", {}),
            "related_operational_modules": [{
                "module_id": module["module_id"],
                "module_family": module["module_family"],
                "plugin_name": module["plugin_name"],
                "package_directory": module["package_directory"],
                "skill_name": module["skill_name"],
                "skill_directory": module["skill_directory"],
                "skill_version": module["skill_version"],
                "jurisdiction": module.get("jurisdiction", c["iso_country_code"]),
                "notes_directory": module.get("notes_directory", c["upstream_source_directory"]),
                "notes_plugin_name": module.get("notes_plugin_name", c["plugin_name"]),
                "manifest_path": (Path(module["skill_directory"]) / "references/module-manifest.json").as_posix(),
                "export_path": (Path(module["skill_directory"]) / "references/module-export.json").as_posix(),
            } for module in c.get("related_operational_modules", [])],
        } for c in countries],
        "operational_modules": [{
            "module_id": module["module_id"],
            "module_family": module["module_family"],
            "jurisdiction": module["jurisdiction"],
            "plugin_name": module["plugin_name"],
            "package_directory": module["package_directory"],
            "skill_name": module.get("skill_name", Path(module["skill_directory"]).name),
            "skill_directory": module["skill_directory"],
            "skill_version": module["skill_version"],
            "notes_directory": module["notes_directory"],
            "notes_plugin_name": module.get("notes_plugin_name", module["plugin_name"]),
            "manifest_path": (Path(module["skill_directory"]) / "references/module-manifest.json").as_posix(),
            "export_path": (Path(module["skill_directory"]) / "references/module-export.json").as_posix(),
            "destination_state_profiles_available": module.get("destination_state_profiles_available", []),
        } for module in operational_modules],
        "module_notes_ownership": [{
            "notes_directory": directory,
            "plugin_name": plugin_name,
            "package_directory": package_directory_by_plugin[plugin_name],
            "ownership_basis": (
                "core_owned_operational_module_no_country_package"
                if plugin_name == registry["core_plugin"] and directory not in {c["upstream_source_directory"] for c in countries}
                else "registered_country_package"
            ),
        } for directory, plugin_name in sorted(notes_plugin_by_directory.items())],
    }
    write_json(core / "skills/eudirective-core/references/national-source-routing.json", routing, {})
    core_input_files["registry/national-source-routing.json"] = sha256(core / "skills/eudirective-core/references/national-source-routing.json")

    paths_py = '''"""Resolve core sources and country-owned module packages from the generated registry."""
from __future__ import annotations
import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parent.parent
LIBRARY_ROOT = SKILL_ROOT / "references" / "source-library"
ROUTING_PATH = SKILL_ROOT / "references" / "national-source-routing.json"

def source_library_root() -> Path:
    if LIBRARY_ROOT.is_dir():
        return LIBRARY_ROOT
    raise FileNotFoundError("The core EU source corpus is missing.")

def compatibility_root() -> Path:
    root = SKILL_ROOT / "tests" / "fixtures" / "core-source-pack-0.6.1"
    if (root / "core-source-pack-manifest-0.6.1.json").is_file():
        return root
    raise FileNotFoundError("The pinned core compatibility fixture is missing.")

def source_library_candidates() -> list[Path]:
    return [source_library_root()]

def compatibility_sources_root() -> Path:
    root = compatibility_root() / "sources"
    if not root.is_dir():
        raise FileNotFoundError("The pinned core source representations are missing.")
    return root

def routing_registry() -> dict:
    data = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("operational_modules"), list):
        raise ValueError("Generated operational module registry is malformed.")
    return data

def _package_directory_for_plugin(data: dict, plugin_name: str) -> str:
    if plugin_name == data["core_plugin"]:
        return "."
    matches = [item for item in data["countries"] if item["plugin_name"] == plugin_name]
    if len(matches) != 1:
        raise ValueError(f"Plugin identity is not registered exactly once: {plugin_name}")
    directory = matches[0].get("package_directory")
    if not isinstance(directory, str) or Path(directory).is_absolute() or ".." in Path(directory).parts:
        raise ValueError(f"Registered package directory is unsafe: {plugin_name}")
    return directory

def _package_root(data: dict, plugin_name: str, package_directory: str) -> Path:
    expected = _package_directory_for_plugin(data, plugin_name)
    if package_directory != expected:
        raise ValueError(f"Registered package directory mismatch for {plugin_name}")
    return PLUGIN_ROOT if plugin_name == data["core_plugin"] else PLUGIN_ROOT.parent / package_directory

def country_plugin_root(country: str) -> Path:
    data = routing_registry()
    row = next((item for item in data["countries"] if item["source_library_directory"] == country or item["iso_country_code"].lower() == country.lower()), None)
    if row is None:
        raise ValueError(f"Country is not registered: {country}")
    root = PLUGIN_ROOT.parent / row["package_directory"]
    if root.is_dir():
        return root
    raise FileNotFoundError(f"Country plugin is not available beside the core package: {row['plugin_name']}")

def module_skill_root(module_id: str) -> Path:
    data = routing_registry()
    row = next((item for item in data["operational_modules"] if item["module_id"] == module_id), None)
    if row is None:
        raise ValueError(f"Operational module is not registered: {module_id}")
    package = _package_root(data, row["plugin_name"], row["package_directory"])
    root = package / row["skill_directory"]
    if not root.is_dir():
        raise FileNotFoundError(f"Registered module package is unavailable: {row['plugin_name']} / {row['skill_directory']}")
    return root

def module_record(module_id: str) -> dict:
    data = routing_registry()
    row = next((item for item in data["operational_modules"] if item["module_id"] == module_id), None)
    if row is None:
        raise ValueError(f"Operational module is not registered: {module_id}")
    return row

def module_record_for_root(module_root: Path) -> dict:
    root = module_root.resolve()
    data = routing_registry()
    for row in data["operational_modules"]:
        package = _package_root(data, row["plugin_name"], row["package_directory"])
        if (package / row["skill_directory"]).resolve() == root:
            return row
    raise ValueError(f"Module package is not registered: {module_root}")

def module_skill_for(jurisdiction: str, module_family: str) -> Path:
    matches = [row for row in routing_registry()["operational_modules"]
               if row["jurisdiction"] == jurisdiction.upper() and row["module_family"] == module_family]
    if len(matches) != 1:
        raise ValueError(f"Expected one registered {module_family} module for {jurisdiction}; found {len(matches)}")
    return module_skill_root(matches[0]["module_id"])

def operational_module_roots() -> list[Path]:
    rows = routing_registry()["operational_modules"]
    roots = [module_skill_root(row["module_id"]) for row in rows]
    return roots

def module_notes_root(country: str, module_id: str | None = None) -> Path:
    data = routing_registry()
    modules = data["operational_modules"]
    module = next((item for item in modules if item["module_id"] == module_id), None) if module_id else None
    if module_id and module is None:
        raise ValueError(f"Operational module is not registered for module notes: {module_id}")
    row = next((item for item in data["countries"]
                if item["source_library_directory"] == country or item["iso_country_code"].lower() == country.lower()), None)
    if not module and not row:
        matching_modules = [item for item in modules if item["notes_directory"] == country]
        if len(matching_modules) == 1:
            module = matching_modules[0]
    notes_directory = module["notes_directory"] if module else (row["source_library_directory"] if row else None)
    if notes_directory is None:
        raise ValueError(f"Country is not registered for module notes: {country}")
    owner = module.get("notes_plugin_name", module["plugin_name"]) if module else next(
        (item["plugin_name"] for item in data["module_notes_ownership"] if item["notes_directory"] == notes_directory),
        row["plugin_name"] if row else None,
    )
    if owner is None:
        raise ValueError(f"Module-note owner is not registered: {notes_directory}")
    package_directory = _package_directory_for_plugin(data, owner)
    package = PLUGIN_ROOT if owner == data["core_plugin"] else PLUGIN_ROOT.parent / package_directory
    library = package / "skills" / "eudirective-core" / "references" / "source-library" if owner == data["core_plugin"] else package / "references" / "source-library"
    root = library / "module-notes" / notes_directory
    if root.is_dir():
        return root
    raise FileNotFoundError(f"Registered module notes are not available: {notes_directory}")
'''
    (core / "skills/eudirective-core/scripts/source_library_paths.py").write_text(paths_py, encoding="utf-8", newline="\n")
    for module in operational_modules:
        if module["plugin_name"] != registry["core_plugin"]:
            continue
        helper = core / module["skill_directory"] / "scripts/source_library_paths.py"
        if helper.is_file():
            text = helper.read_text(encoding="utf-8")
            text = text.replace(
                'PLUGIN_ROOT / "skills" / "eudirective-source-library"',
                'PLUGIN_ROOT / "skills" / "eudirective-core" / "references" / "source-library"',
            )
            helper.write_text(text, encoding="utf-8", newline="\n")

    core_skill = core / "skills/eudirective-core/SKILL.md"
    text = core_skill.read_text(encoding="utf-8")
    text = text.replace(
        "Use the freemovement-law eudirective-source-library skill to locate the bundled, externally maintained source library.",
        "Use the eudirective-source-library skill to locate the core-owned EU corpus and generated national source routing registry.",
    )
    routing_section = (
        "\n## National plugin discovery\n\n"
        "Use the generated references/national-source-routing.json after C3 classifies a materially relevant national jurisdiction and role. "
        "Check the host's available-skill catalog for the exact registered plugin and compatibility contract; a registry entry proves identity, not installation. "
        "Record available_compatible, available_outdated, available_incompatible, unavailable, discovery_unknown, or not_required only when supported by the available catalog and package manifests. "
        "If discovery is unavailable or partial, report discovery_unknown, continue with EU law and responsible official-source research, and state the exact national-source limitation. "
        "For Malta, separately report plugin availability, language representation availability, edition alignment, and whether the relevant provisions were compared. "
        "Do not block an ordinary consultation solely because a country plugin is absent.\n"
    )
    if "## National plugin discovery" not in text:
        text = text.replace("## Conditional legal and research workflows", routing_section + "\n## Conditional legal and research workflows", 1)
    core_skill.write_text(text, encoding="utf-8", newline="\n")

    for rel in ("plugin.json", ".codex-plugin/plugin.json"):
        meta_path = core / rel
        meta = load_json(meta_path)
        meta["version"] = "0.60.0"
        if rel == "plugin.json":
            meta["author"] = AUTHOR
        else:
            meta["author"] = AUTHOR
            meta["interface"]["developerName"] = AUTHOR["name"]
            meta["interface"]["displayName"] = "freemovement-law"
        meta_path.write_bytes(json_bytes(meta))
    update_plugin_version(core, "0.60.0", "0.59.0", "1.1.0")

    for country in countries:
        code = country["iso_country_code"]
        name = country["plugin_name"]
        package_directory = country["plugin_directory"]
        plugin_dir = output_root / package_directory
        skill_rel = country["skill_directory"].removeprefix("skills/")
        skill_file = plugin_dir / "skills" / skill_rel / "SKILL.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        is_malta = code == "MT"
        skill_content = country_skill(country, is_malta)
        skill_file.write_text(skill_content, encoding="utf-8", newline="\n")
        if is_malta:
            verification = plugin_dir / "skills" / skill_rel / "references/malta-bilingual-verification.md"
            verification.parent.mkdir(parents=True, exist_ok=True)
            verification.write_text(
                "# Malta bilingual verification\n\n"
                "Use the language-pair register at references/source-library/malta/references/language-pairs.json and the source-acceptance record together. "
                "A language-pair entry records discovery and version metadata; it does not certify legal equivalence.\n\n"
                "1. Identify the source as Maltese legislation, subsidiary legislation, judgment, guidance, or EU law.\n"
                "2. For national statutes, locate the official English and Maltese representation under the same ELI identity. Confirm the returned text itself is in the claimed language; a URL suffix, selector or portal label alone is not enough.\n"
                "3. Compare publication dates, point-in-time editions, amendments, commencement and instrument identifiers before comparing wording.\n"
                "4. Align the actual provisions, definitions and numbering; do not infer matching content from matching article numbers.\n"
                "5. When material, compare obligations, negations, exceptions, conditions, deadlines, powers, remedies and legal effects in both texts.\n"
                "6. Apply Constitution Article 74's Maltese-text precedence only to national laws and after checking for a specific statutory exception. Do not apply it automatically to EU instruments or judgments. For court-language issues, check Constitution Article 5, Code of Organization and Civil Procedure Chapter 12 Article 21, Chapter 189 and the actual language of the judicial record.\n"
                "7. Report which official versions were consulted, edition alignment, comparison status, any material difference, applicable language rule, and the exact unresolved gap.\n\n"
                "Keep the official English reference even when Maltese prevails in a statutory conflict. Do not describe an unofficial or machine-generated English rendering as an official version. The source pack currently accepts official links only and no local national-law copies; do not package restricted statutory text. Keep Maltese-language EU texts separate from Malta national law.\n",
                encoding="utf-8", newline="\n",
            )
        (plugin_dir / "README.md").write_text(
            f"# {country['country_name']} FreeMovement source library\n\n"
            f"Install this plugin alongside freemovement-law when {country['country_name']} national sources are relevant. "
            "The package preserves source acceptance and coverage limits; official-source links remain primary for current-law checks.\n",
            encoding="utf-8", newline="\n",
        )
        meta = {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": name, "version": "0.1.0",
            "description": f"{country['country_name']} national source library for FreeMovement consultations.",
            "author": AUTHOR,
            "keywords": ["eu-free-movement", "national-source-library", code.lower()],
        }
        write_json(plugin_dir / "plugin.json", meta, {})
        write_json(plugin_dir / ".codex-plugin/plugin.json", {
            "name": name, "version": "0.1.0", "skills": "./skills", "author": AUTHOR,
            "description": f"{country['country_name']} national source library for FreeMovement consultations.",
        }, {})

        checker_source = plugin_root / "skills/eudirective-core/scripts/session_version_check.mjs"
        if not checker_source.is_file():
            raise FileNotFoundError("Core component version checker is required for each country plugin")
        checker_target = plugin_dir / "skills" / skill_rel / "scripts/session_version_check.mjs"
        copy_exact(checker_source, checker_target, {})
        inputs = {
            "registry/country-record.json": hashlib.sha256(json_bytes(country)).hexdigest(),
            "distributor/build.py": generator_hash,
            "core-tool/session_version_check.mjs": sha256(checker_source),
        }
        module_fingerprints: dict[str, str] = {}
        for module in operational_modules:
            if module["plugin_name"] != name:
                continue
            template_rel = module.get("template_directory")
            if not template_rel:
                raise ValueError(f"Country-owned module lacks a source template: {module['module_id']}")
            template = plugin_root.parents[0] / template_rel
            if not template.is_dir():
                raise FileNotFoundError(f"Operational module template is missing: {template}")
            module_skill_rel = module["skill_directory"].removeprefix("skills/")
            module_skill_root = plugin_dir / "skills" / module_skill_rel
            module_skill_root.mkdir(parents=True, exist_ok=True)
            for source in sorted(template.rglob("*")):
                if not source.is_file() or any(part in SKIP_DIRS for part in source.relative_to(template).parts):
                    continue
                relative = source.relative_to(template)
                target = module_skill_root / relative
                content = source.read_bytes()
                if relative.as_posix() == "SKILL.md":
                    skill_text = content.decode("utf-8")
                    skill_text, count = re.subn(
                        r"(?m)^- Skill version: `\d+\.\d+\.\d+`$",
                        f"- Skill version: `{module['skill_version']}`", skill_text, count=1,
                    )
                    if count != 1:
                        raise ValueError(f"Operational module skill version line is missing: {module['skill_name']}")
                    normalized, normalized_count = re.subn(
                        r"(?m)^- Skill version: `\d+\.\d+\.\d+`$",
                        "- Skill version: `<version>`", skill_text, count=1,
                    )
                    if normalized_count != 1:
                        raise ValueError(f"Could not normalize operational module skill fingerprint: {module['skill_name']}")
                    module_fingerprints[module["skill_name"]] = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(skill_text, encoding="utf-8", newline="\n")
                    inputs[f"operational-module/{module['skill_name']}/{relative.as_posix()}"] = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                    module_sha = sha256(source)
                else:
                    copy_exact(source, target, {})
                    inputs[f"operational-module/{module['skill_name']}/{relative.as_posix()}"] = sha256(source)
                    module_sha = sha256(source)
                migration_rows.append({
                    "source_path": f"{template_rel}/{relative.as_posix()}",
                    "target_path": f"{package_directory}/{module['skill_directory']}/{relative.as_posix()}",
                    "classification": "country_owned_operational_module",
                    "sha256": module_sha,
                })
            if module["skill_name"] not in module_fingerprints:
                raise ValueError(f"Operational module template lacks SKILL.md: {module['skill_name']}")
            country_skill_dir = country["skill_directory"].removeprefix("skills/")
            module_manifest_path = previous_root / package_directory / f"skills/{country_skill_dir}/references/component-manifest.json"
            previous_manifest = load_json(module_manifest_path) if module_manifest_path.is_file() else None
            if previous_manifest and module["skill_name"] not in previous_manifest.get("skill_versions", {}):
                old_core_manifest_path = previous_root / registry["core_plugin"] / "skills/eudirective-core/references/component-manifest.json"
                if old_core_manifest_path.is_file():
                    previous_manifest = load_json(old_core_manifest_path)
            if previous_manifest:
                previous_version = previous_manifest.get("skill_versions", {}).get(module["skill_name"])
                previous_fingerprint = previous_manifest.get("skill_fingerprints", {}).get(module["skill_name"])
                if previous_version and previous_fingerprint != module_fingerprints[module["skill_name"]] and previous_version == module["skill_version"]:
                    raise ValueError(f"Operational module changed without a skill version update: {module['skill_name']}")
        for note in module_notes_by_plugin[name]:
            rel_note = note.relative_to(module_notes_root)
            target_note = Path("references/source-library/module-notes") / rel_note
            copy_exact(note, plugin_dir / target_note, {})
            source_path = f"module-notes/{rel_note.as_posix()}"
            inputs[source_path] = sha256(note)
            migration_rows.append({
                "source_path": source_path,
                "target_path": f"{package_directory}/{target_note.as_posix()}",
                "classification": "operational_module_note", "sha256": sha256(note),
            })
        pack = source_root / country["upstream_source_directory"]
        accepted = accepted_by_country[country["upstream_source_directory"]]
        source_targets: set[str] = set()
        for source in sorted(pack.rglob("*")):
            if not source.is_file():
                continue
            rel_parts = source.relative_to(pack).parts
            if any(part in SKIP_DIRS for part in rel_parts):
                continue
            if rel_parts[0] == "references":
                target_rel = Path("references/source-library") / country["upstream_source_directory"] / Path(*rel_parts)
                copy_exact(source, plugin_dir / target_rel, {})
                source_rel = source.relative_to(source_root).as_posix()
                inputs[f"source-library/{source_rel}"] = sha256(source)
                source_targets.add(source_rel)
                migration_rows.append({
                    "source_path": source_rel, "target_path": f"{package_directory}/{target_rel.as_posix()}",
                    "classification": "national_source_metadata", "sha256": sha256(source),
                })
            elif rel_parts[0] == "documents":
                source_rel = source.relative_to(source_root).as_posix()
                if source_rel not in accepted_paths_all:
                    if source.name == "README.md":
                        target_rel = Path("references/source-library") / country["upstream_source_directory"] / Path(*rel_parts)
                        copy_exact(source, plugin_dir / target_rel, {})
                        inputs[f"source-library/{source_rel}"] = sha256(source)
                        source_targets.add(source_rel)
                    continue
                expected = next((h for p, h, _ in accepted if p.resolve() == source.resolve()), None)
                target_rel = Path("references/source-library") / country["upstream_source_directory"] / Path(*rel_parts)
                copy_exact(source, plugin_dir / target_rel, {}, expected)
                inputs[f"source-library/{source_rel}"] = sha256(source)
                source_targets.add(source_rel)
                classification = "accepted_national_source_attachment" if "attachments" in rel_parts else "accepted_national_source_text"
                migration_rows.append({
                    "source_path": source_rel, "target_path": f"{package_directory}/{target_rel.as_posix()}",
                    "classification": classification, "sha256": sha256(source),
                })
            elif source.name in {"README.md", "SKILL.md"}:
                target_rel = Path("references/source-library") / country["upstream_source_directory"] / source.name
                copy_exact(source, plugin_dir / target_rel, {})
                source_rel = source.relative_to(source_root).as_posix()
                inputs[f"source-library/{source_rel}"] = sha256(source)
                source_targets.add(source_rel)

        acceptance_path = pack / "references" / country["national_source_inputs"]["acceptance_record"].split("references/", 1)[-1]
        acceptance_target = plugin_dir / "references/source-library" / country["upstream_source_directory"] / country["national_source_inputs"]["acceptance_record"]
        if not acceptance_target.is_file() or sha256(acceptance_path) != sha256(acceptance_target):
            raise ValueError(f"Acceptance record missing or changed in generated package: {name}")

        for lang_input in country.get("eu_language_representation_inputs", []):
            rel = lang_input.get("shared_core_index")
            if not rel:
                continue
            idx_path, idx = language_indexes[rel]
            idx_dest_rel = Path("references/source-library") / rel
            copy_exact(idx_path, plugin_dir / idx_dest_rel, {})
            inputs[f"source-library/{rel}"] = sha256(idx_path)
            for source, expected in indexed_representations(source_root, idx):
                rel_source = source.relative_to(source_root)
                target_rel = Path("references/source-library") / rel_source
                copy_exact(source, plugin_dir / target_rel, {}, expected)
                inputs[f"source-library/{rel_source.as_posix()}"] = expected
                source_targets.add(rel_source.as_posix())
                migration_rows.append({
                    "source_path": f"source-library/{rel_source.as_posix()}",
                    "target_path": f"{package_directory}/{target_rel.as_posix()}",
                    "classification": "shared_non_english_eu_text", "sha256": expected,
                })
            national_idx = lang_input.get("national_language_index")
            if national_idx and (source_root / national_idx).is_file():
                national_path = source_root / national_idx
                dest = plugin_dir / "references/source-library" / national_idx
                copy_exact(national_path, dest, {})
                inputs[f"source-library/{national_idx}"] = sha256(national_path)
            state_idx = f"national-language-state-{lang_input['language_code']}.json"
            if (source_root / state_idx).is_file():
                state_path = source_root / state_idx
                dest = plugin_dir / "references/source-library" / state_idx
                copy_exact(state_path, dest, {})
                inputs[f"source-library/{state_idx}"] = sha256(state_path)

        if is_malta:
            pair_register = pack / "references/language-pairs.json"
            if not pair_register.is_file():
                raise FileNotFoundError("Malta bilingual source-pair register is required")
            pairs = load_json(pair_register)
            source_list = pack / "references/source-list.md"
            if not source_list.is_file():
                raise FileNotFoundError("Malta official source list is required to preserve English references")
            validate_malta_pair_register(pairs, source_list.read_text(encoding="utf-8"))
            inputs["source-library/malta/references/language-pairs.json"] = sha256(pair_register)

        for row in inventory:
            rel = row["source_path"]
            if row["distribution_action"] == "distributed_to_country_plugin" and PurePosixPath(rel).parts[0] == country["upstream_source_directory"] and rel not in source_targets:
                raise ValueError(f"Inventory marks a source for distribution but package omitted it: {name}:{rel}")

        skill_name = "eudirective-library-" + code.lower()
        skill_fingerprint = hashlib.sha256(
            skill_content.replace("Skill version: 0.1.0", "Skill version: <version>").encode("utf-8")
        ).hexdigest()
        skill_fingerprints = {skill_name: skill_fingerprint}
        skill_fingerprints.update(module_fingerprints)
        inputs[f"skill-template/{skill_name}"] = skill_fingerprint
        inputs.update({f"skill-template/{key}": value for key, value in module_fingerprints.items()})
        input_fingerprint = fingerprint_inputs(inputs)
        manifest_rel = f"skills/{skill_rel}/references/component-manifest.json"
        plugin_version, skill_versions = choose_versions(
            name, country["plugin_directory"], manifest_rel, input_fingerprint, skill_fingerprints, "0.1.0",
            {skill_name: "0.1.0", **{module["skill_name"]: module["skill_version"] for module in operational_modules if module["plugin_name"] == name}},
        )
        for module in operational_modules:
            if module["plugin_name"] == name:
                skill_versions[module["skill_name"]] = module["skill_version"]
        skill_file.write_text(
            skill_content.replace("Skill version: 0.1.0", f"Skill version: {skill_versions[skill_name]}"),
            encoding="utf-8", newline="\n",
        )
        for rel in ("plugin.json", ".codex-plugin/plugin.json"):
            meta_path = plugin_dir / rel
            meta = load_json(meta_path)
            meta["version"] = plugin_version
            meta_path.write_bytes(json_bytes(meta))
        outputs = file_hashes(plugin_dir, {manifest_rel})
        manifest = build_source_manifest(
            code, plugin_version, skill_versions, skill_fingerprints,
            upstream_revision, {"source-library": source_tree_sha, "module-notes": module_notes_tree_sha},
            inputs, outputs, country.get("core_compatibility_contract", {}),
        )
        write_json(plugin_dir / manifest_rel, manifest, {})
        component_manifests[name] = manifest

    def without_skill_version(text: str, prefixes: tuple[str, ...]) -> str:
        return chr(10).join(line for line in text.splitlines() if not line.startswith(prefixes)) + chr(10)

    core_skill_fingerprints = {
        "eudirective-core": hashlib.sha256(re.sub(
            r"(?m)(Skill: eudirective-core v)\d+\.\d+\.\d+",
            r"\g<1><version>",
            without_skill_version(core_skill.read_text(encoding="utf-8"), ("- Current version:", "- Plugin version:")),
        ).encode("utf-8")).hexdigest(),
        "eudirective-source-library": hashlib.sha256(without_skill_version(
            (core / "skills/eudirective-source-library/SKILL.md").read_text(encoding="utf-8"),
            ("**Skill version:**",),
        ).encode("utf-8")).hexdigest(),
    }
    module_skill_paths = {
        "eudirective-ac-turkiye": core / "skills/eudirective-ac-turkiye/SKILL.md",
    }
    for skill_name, skill_path in module_skill_paths.items():
        core_skill_fingerprints[skill_name] = hashlib.sha256(without_skill_version(
            skill_path.read_text(encoding="utf-8"), ("- Current version:",)
        ).encode("utf-8")).hexdigest()
    core_input_files.update({f"skill-template/{key}": value for key, value in core_skill_fingerprints.items()})
    core_input_fingerprint = fingerprint_inputs(core_input_files)
    core_manifest_rel = "skills/eudirective-core/references/component-manifest.json"
    initial_core_skill_versions: dict[str, str] = {}
    initial_skill_paths = {
        "eudirective-core": core / "skills/eudirective-core/SKILL.md",
        "eudirective-source-library": core / "skills/eudirective-source-library/SKILL.md",
        **module_skill_paths,
    }
    for skill_name, skill_path in initial_skill_paths.items():
        content = skill_path.read_text(encoding="utf-8")
        match = re.search(r"(?m)^- Current version: `(\d+\.\d+\.\d+)`", content)
        if not match:
            match = re.search(r"(?m)^\*\*Skill version:\*\* (\d+\.\d+\.\d+)", content)
        if not match:
            raise ValueError(f"Skill version missing from core component: {skill_name}")
        initial_core_skill_versions[skill_name] = match.group(1)
    core_plugin_version, core_skill_versions = choose_versions(
        registry["core_plugin"], registry["core_plugin"], core_manifest_rel, core_input_fingerprint, core_skill_fingerprints,
        "0.60.0", initial_core_skill_versions,
    )
    write_core_source_skill(core, core_skill_versions["eudirective-source-library"])
    update_plugin_version(core, core_plugin_version, core_skill_versions["eudirective-core"],
                          core_skill_versions["eudirective-source-library"])
    for skill_name, skill_path in module_skill_paths.items():
        content = skill_path.read_text(encoding="utf-8")
        content, count = re.subn(
            r"(?m)^- Current version: .*?$",
            f"- Current version: `{core_skill_versions[skill_name]}`", content, count=1,
        )
        if count != 1:
            raise ValueError(f"Could not stamp module skill version: {skill_name}")
        skill_path.write_text(content, encoding="utf-8", newline="\n")
    core_outputs = file_hashes(core, {core_manifest_rel})
    core_manifest = build_source_manifest(
        "eu-core", core_plugin_version, core_skill_versions, core_skill_fingerprints,
        upstream_revision, {"source-library": source_tree_sha, "module-notes": module_notes_tree_sha},
        core_input_files, core_outputs, registry.get("core_compatibility_contract", {}),
    )
    write_json(core / core_manifest_rel, core_manifest, {})
    component_manifests[registry["core_plugin"]] = core_manifest

    for package_name, manifest in component_manifests.items():
        country = next((item for item in countries if item["plugin_name"] == package_name), None)
        package_directory = registry["core_plugin"] if country is None else country["plugin_directory"]
        package_root = output_root / package_directory
        manifest_rel = "skills/eudirective-core/references/component-manifest.json" if country is None else next(
            f"skills/{item['skill_directory'].removeprefix('skills/')}/references/component-manifest.json"
            for item in countries if item["plugin_name"] == package_name
        )
        actual_outputs = file_hashes(package_root, {manifest_rel})
        if actual_outputs != manifest["distributed_files"]:
            raise ValueError(f"Distributed-file manifest does not match package bytes: {package_name}")

    distributable_actions = {
        "distributed_to_core", "distributed_to_country_plugin",
        "distributed_to_registered_countries", "distributed_as_required_by_registry",
    }
    package_roots = [output_root / registry["core_plugin"]] + [output_root / c["plugin_directory"] for c in countries]
    output_index: dict[tuple[str, str], list[Path]] = {}
    for package_root in package_roots:
        if not package_root.is_dir():
            continue
        for candidate in package_root.rglob("*"):
            if candidate.is_file():
                output_index.setdefault((candidate.name, sha256(candidate)), []).append(candidate)
    migration_keys = {(row["source_path"], row["target_path"]) for row in migration_rows}
    for source_row in inventory:
        if source_row["distribution_action"] not in distributable_actions:
            continue
        source_rel = source_row["source_path"]
        source_name = Path(source_rel).name
        aliases = {source_name}
        if source_rel == "README.md":
            aliases.add("upstream-library-readme.md")
        targets = [candidate for alias in aliases for candidate in output_index.get((alias, source_row["sha256"]), [])]
        for target in targets:
            target_rel = target.relative_to(output_root).as_posix()
            key = (source_rel, target_rel)
            if key not in migration_keys:
                migration_rows.append({
                    "source_path": source_rel, "target_path": target_rel,
                    "classification": source_row["classification"], "sha256": source_row["sha256"],
                })
                migration_keys.add(key)
        if not targets:
            raise ValueError(f"Inventory requires distribution but no package target exists: {source_rel}")

    for row in migration_rows:
        target = output_root / row["target_path"]
        source = source_root / row["source_path"]
        if not target.is_file() or sha256(target) != row["sha256"]:
            raise ValueError(f"Migration target missing or hash-mismatched: {row['target_path']}")
        if source.is_file() and sha256(source) != row["sha256"]:
            raise ValueError(f"Migration source hash changed: {row['source_path']}")
    migration_rows = list({(row["source_path"], row["target_path"]): row for row in migration_rows}.values())

    component_index = {"schema_version": SCHEMA, "source_repository": "eudirective/public-data", "upstream_revision": upstream_revision, "upstream_trees": {"source-library": source_tree_sha, "module-notes": module_notes_tree_sha}, "components": []}
    for name, manifest in sorted(component_manifests.items()):
        country = next((c for c in countries if c["plugin_name"] == name), None)
        component_index["components"].append({
            "component_id": manifest["component_id"],
            "plugin_name": name,
            "package_directory": registry["core_plugin"] if country is None else country["plugin_directory"],
            "plugin_version": manifest["plugin_version"],
            "skill_versions": manifest["skill_versions"],
            "source_contract_version": manifest["source_contract_version"],
            "input_fingerprint": manifest["input_fingerprint"],
            "distributed_fingerprint": manifest["distributed_fingerprint"],
            "compatibility": manifest["compatibility"],
            "verification_profile": "eu_core" if country is None else country.get("verification_profile", "national_source_review"),
        })
    write_json(output_root / "component-index.json", component_index, {})
    write_json(output_root / "source-inventory.json", inventory, {})
    write_json(output_root / "migration-map.json", sorted(migration_rows, key=lambda x: (x["source_path"], x["target_path"])), {})

    marketplace_path = plugin_root.parent / ".agents/plugins/marketplace.json"
    marketplace = load_json(marketplace_path)
    generated_names = {
        registry["core_plugin"],
        *(country["plugin_name"] for country in countries),
        *(f"freemovement-law-{country['iso_country_code'].lower()}" for country in countries),
    }
    generated_paths = {f"./{country['plugin_directory']}" for country in countries}
    def entry_source_path(entry: dict[str, Any]) -> str | None:
        source = entry.get("source")
        if isinstance(source, dict):
            return source.get("path")
        return source if isinstance(source, str) else None
    plugins = [
        entry for entry in marketplace.get("plugins", [])
        if entry.get("name") not in generated_names and entry_source_path(entry) not in generated_paths
    ]
    plugins.append({
        "name": registry["core_plugin"],
        "source": {"source": "local", "path": f"./{registry['core_plugin']}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    })
    plugins.extend({
        "name": country["plugin_name"],
        "source": {"source": "local", "path": f"./{country['plugin_directory']}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    } for country in countries)
    marketplace["plugins"] = plugins
    write_json(output_root / "marketplace.json", marketplace, {})

    old_tree = core / "skills/eudirective-source-library"
    forbidden_country_dirs = {c["upstream_source_directory"] for c in countries}
    if any((old_tree / country).exists() for country in forbidden_country_dirs):
        raise ValueError("Monolithic national source data remains in the core package")
    fixture = core / "skills/eudirective-core/tests/fixtures/core-source-pack-0.6.1/core-source-pack-manifest-0.6.1.json"
    if not fixture.is_file():
        raise ValueError("Historical C1/C18 compatibility fixture was removed")
    if (core / "skills/eudirective-ms-sweden").exists():
        raise ValueError("Sweden operational module leaked into the shared core package")
    sweden = next(country for country in countries if country["iso_country_code"] == "SE")
    if not (output_root / sweden["plugin_directory"] / "skills/eudirective-ms-sweden/SKILL.md").is_file():
        raise ValueError("Sweden operational module is missing from its country package")
    if not (core / "skills/eudirective-ac-turkiye/SKILL.md").is_file():
        raise ValueError("The existing Türkiye applicant-country module was removed")

    return {
        "country_count": len(countries),
        "english_core_sources": len(english),
        "components": len(component_manifests),
        "inventory_rows": len(inventory),
        "accepted_local_texts": sum(1 for docs in accepted_by_country.values() for path, _, _ in docs if "attachments" not in path.parts),
        "accepted_local_attachments": sum(1 for docs in accepted_by_country.values() for path, _, _ in docs if "attachments" in path.parts),
        "output_root": str(output_root),
        "component_index": str(output_root / "component-index.json"),
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--module-notes-root", required=True, type=Path)
    parser.add_argument("--registry", type=Path, default=Path(__file__).with_name("country-registry.json"))
    parser.add_argument("--upstream-revision", required=True)
    parser.add_argument("--plugin-root", required=True, type=Path)
    parser.add_argument("--previous-root", type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40,64}", args.upstream_revision):
        parser.error("--upstream-revision must be a full lowercase git object ID")
    try:
        result = build(args.source_root, args.module_notes_root, args.registry, args.output_root, args.upstream_revision, args.plugin_root, args.previous_root)
    except Exception as exc:
        print(f"distribution failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
