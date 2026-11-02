#!/usr/bin/env python3
"""Tests for main-branch Discord announcement content and webhook requests."""
from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from discord_announcement import (
    DiscordAnnouncementError,
    payload_for,
    post_webhook,
    release_metadata,
    should_announce,
    webhook_url_with_wait,
)


CHANGELOG = """# FreeMovement package changelog

## [1.2.0] - 2026-11-02

**Packages:** `freemovement-law` 1.2.0

- Added a clearer consultation summary.

## [1.1.0] - 2026-10-01

**Packages:** `freemovement-law` 1.1.0

- Added an older feature.
"""
PLUGIN_METADATA = {"name": "freemovement-law", "version": "1.2.0"}


class DiscordAnnouncementTests(unittest.TestCase):
    def test_message_contains_latest_version_and_changelog(self) -> None:
        entry, version, content = release_metadata(CHANGELOG, PLUGIN_METADATA)
        self.assertIn("[1.2.0]", entry)
        self.assertEqual(version, "1.2.0")
        self.assertIn("FreeMovement v1.2.0", content)
        self.assertIn("clearer consultation summary", content)
        self.assertNotIn("older feature", content)
        self.assertIn("/blob/main/CHANGELOG.md", content)

    def test_rejects_version_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "must match"):
            release_metadata(CHANGELOG, {"version": "1.3.0"})

    def test_skips_unchanged_latest_entry_but_announces_new_or_changed_entry(self) -> None:
        self.assertFalse(should_announce(CHANGELOG, CHANGELOG))
        self.assertTrue(should_announce(CHANGELOG, None))
        previous = CHANGELOG.replace("clearer consultation summary", "older summary")
        self.assertTrue(should_announce(CHANGELOG, previous))
        older_only_edit = CHANGELOG.replace("older feature", "reworded history")
        self.assertFalse(should_announce(CHANGELOG, older_only_edit))

    def test_discord_content_limit_is_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "2000 characters"):
            payload_for("x" * 2001)

    def test_payload_disables_mentions(self) -> None:
        self.assertEqual(
            payload_for("@everyone FreeMovement update"),
            {"content": "@everyone FreeMovement update", "allowed_mentions": {"parse": []}},
        )

    def test_webhook_url_gets_confirmation_parameter(self) -> None:
        self.assertEqual(
            webhook_url_with_wait("https://discord.com/api/webhooks/123/token?thread_id=5"),
            "https://discord.com/api/webhooks/123/token?thread_id=5&wait=true",
        )

    def test_post_sends_json_and_does_not_need_a_bot_token(self) -> None:
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = None
        with patch("discord_announcement.urlopen", return_value=response) as urlopen_mock:
            post_webhook(
                "https://discord.com/api/webhooks/123/token",
                payload_for("FreeMovement v1.2.0"),
            )
        request = urlopen_mock.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(request.full_url, "https://discord.com/api/webhooks/123/token?wait=true")
        self.assertEqual(json.loads(request.data), payload_for("FreeMovement v1.2.0"))


if __name__ == "__main__":
    unittest.main()
