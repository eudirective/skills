#!/usr/bin/env python3
"""Tests for changelog validation and rolling GitHub release-note generation."""
from __future__ import annotations

import unittest

from release_notes import ChangelogError, latest_entry, render_release_notes, validate_changelog


SAMPLE_CHANGELOG = """# FreeMovement package changelog

## [1.2.0] - 2026-11-02

**Packages:** `freemovement-law` 1.2.0

- Added a clearer consultation summary.

## [1.1.0] - 2026-10-01

**Packages:** `freemovement-law` 1.1.0

- Added an older feature.
"""
REVISION = "a" * 40


class ReleaseNotesTests(unittest.TestCase):
    def test_selects_only_the_latest_release_section(self) -> None:
        entry = latest_entry(SAMPLE_CHANGELOG)
        self.assertIn("[1.2.0]", entry)
        self.assertIn("clearer consultation summary", entry)
        self.assertNotIn("older feature", entry)
        self.assertEqual(len(validate_changelog(SAMPLE_CHANGELOG)), 2)

    def test_release_notes_include_exact_revision_and_distribution_links(self) -> None:
        notes = render_release_notes(SAMPLE_CHANGELOG, REVISION)
        self.assertIn(f"at [{REVISION}](https://github.com/eudirective/skills/commit/{REVISION})", notes)
        self.assertIn("https://github.com/eudirective/skills/blob/main/CHANGELOG.md", notes)
        self.assertIn("https://github.com/eudirective/skills/releases/download/freemovement-latest/packages.json", notes)
        self.assertIn("https://github.com/eudirective/skills/releases/download/freemovement-latest/SHA256SUMS", notes)

    def test_rejects_missing_versioned_entry(self) -> None:
        with self.assertRaisesRegex(ChangelogError, "no versioned release entries"):
            latest_entry("# FreeMovement package changelog\n")

    def test_rejects_malformed_heading(self) -> None:
        with self.assertRaisesRegex(ChangelogError, "must use"):
            latest_entry("## Latest\n\n**Packages:** package 1.0.0\n\n- Change.\n")

    def test_rejects_missing_package_version(self) -> None:
        changelog = "## [1.2.0] - 2026-11-02\n\n**Packages:** freemovement-law\n\n- Change.\n"
        with self.assertRaisesRegex(ChangelogError, "semantic version"):
            latest_entry(changelog)

    def test_rejects_entry_without_user_facing_summary(self) -> None:
        changelog = "## [1.2.0] - 2026-11-02\n\n**Packages:** freemovement-law 1.2.0\n"
        with self.assertRaisesRegex(ChangelogError, "at least one user-facing change"):
            latest_entry(changelog)

    def test_rejects_malformed_historical_entry(self) -> None:
        changelog = SAMPLE_CHANGELOG.replace(
            "**Packages:** `freemovement-law` 1.1.0",
            "**Packages:** `freemovement-law`",
        )
        with self.assertRaisesRegex(ChangelogError, "semantic version"):
            validate_changelog(changelog)

    def test_rejects_versions_out_of_order(self) -> None:
        changelog = SAMPLE_CHANGELOG.replace(
            "## [1.1.0] - 2026-10-01", "## [1.3.0] - 2026-10-01"
        )
        with self.assertRaisesRegex(ChangelogError, "strictly descending"):
            validate_changelog(changelog)

    def test_rejects_invalid_source_revision(self) -> None:
        with self.assertRaisesRegex(ChangelogError, "source revision"):
            render_release_notes(SAMPLE_CHANGELOG, "not-a-hash")


if __name__ == "__main__":
    unittest.main()
