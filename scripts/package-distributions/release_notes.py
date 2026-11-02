#!/usr/bin/env python3
"""Build user-facing GitHub release notes from the latest changelog entry."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re


REPOSITORY_URL = "https://github.com/eudirective/skills"
HEADING = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})$")
PACKAGE_LINE = re.compile(r"^\*\*Packages:\*\*\s+.+$")
SEMVER = re.compile(r"\b\d+\.\d+\.\d+\b")
REVISION = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")


class ChangelogError(ValueError):
    """The changelog does not contain a valid latest release entry."""


def validate_changelog(changelog: str) -> list[str]:
    """Validate every release entry and return the sections newest first."""
    lines = changelog.splitlines()
    headings = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if not headings:
        raise ChangelogError("CHANGELOG.md has no versioned release entries")

    sections: list[str] = []
    previous_version: tuple[int, int, int] | None = None
    previous_date: date | None = None
    for position, start in enumerate(headings):
        match = HEADING.fullmatch(lines[start])
        if match is None:
            raise ChangelogError("changelog entries must use '## [x.y.z] - YYYY-MM-DD'")
        version = tuple(int(part) for part in match.group(1).split("."))
        try:
            entry_date = date.fromisoformat(match.group(2))
        except ValueError as exc:
            raise ChangelogError("changelog entry has an invalid date") from exc

        if previous_version is not None and version >= previous_version:
            raise ChangelogError("changelog versions must be in strictly descending order")
        if previous_date is not None and entry_date > previous_date:
            raise ChangelogError("changelog dates must be in descending order")

        end = headings[position + 1] if position + 1 < len(headings) else len(lines)
        section_lines = lines[start:end]
        package_lines = [
            line.strip() for line in section_lines[1:]
            if PACKAGE_LINE.fullmatch(line.strip())
        ]
        if not package_lines:
            raise ChangelogError("each changelog entry must identify affected package versions")
        if not any(SEMVER.search(line) for line in package_lines):
            raise ChangelogError("changelog package lines must include a semantic version")
        if not any(line.strip().startswith("- ") for line in section_lines[1:]):
            raise ChangelogError("each changelog entry must contain at least one user-facing change")

        sections.append("\n".join(section_lines).strip())
        previous_version = version
        previous_date = entry_date
    return sections


def latest_entry(changelog: str) -> str:
    """Return the newest well-formed release section from changelog Markdown."""
    return validate_changelog(changelog)[0]


def render_release_notes(changelog: str, revision: str) -> str:
    """Render the latest user-facing entry with exact snapshot and asset links."""
    if REVISION.fullmatch(revision) is None:
        raise ChangelogError("source revision must be a 40- or 64-character lowercase Git hash")
    entry = latest_entry(changelog)
    commit_url = f"{REPOSITORY_URL}/commit/{revision}"
    notes = [
        entry,
        "---",
        f"This rolling package snapshot was generated from `main` at [{revision}]({commit_url}).",
        f"See the [full changelog]({REPOSITORY_URL}/blob/main/CHANGELOG.md), "
        f"[packages.json]({REPOSITORY_URL}/releases/download/freemovement-latest/packages.json), "
        f"and [SHA256SUMS]({REPOSITORY_URL}/releases/download/freemovement-latest/SHA256SUMS).",
    ]
    return "\n\n".join(notes) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        changelog = args.changelog.read_text(encoding="utf-8")
        notes = render_release_notes(changelog, args.revision)
        args.output.write_text(notes, encoding="utf-8")
    except (OSError, ChangelogError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
