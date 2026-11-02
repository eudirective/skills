#!/usr/bin/env python3
"""Post a changed FreeMovement changelog entry to a Discord webhook."""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from release_notes import ChangelogError, HEADING, latest_entry


REPOSITORY_URL = "https://github.com/eudirective/skills"
MAX_CONTENT_LENGTH = 2000
GIT_REVISION = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")


class DiscordAnnouncementError(ValueError):
    """The Discord announcement cannot be safely generated or sent."""


def release_metadata(changelog: str, plugin_metadata: dict[str, object]) -> tuple[str, str, str]:
    """Return the validated latest entry, version and Discord message text."""
    entry = latest_entry(changelog)
    heading = entry.splitlines()[0]
    match = HEADING.fullmatch(heading)
    if match is None:
        raise ChangelogError("latest changelog entry has an invalid version heading")
    version, release_date = match.groups()
    if plugin_metadata.get("version") != version:
        raise ChangelogError(
            "latest changelog version must match freemovement-law/plugin.json"
        )

    details = "\n".join(entry.splitlines()[1:]).strip()
    content = (
        f"**FreeMovement v{version} — {release_date}**\n\n"
        f"{details}\n\n"
        f"[Full changelog]({REPOSITORY_URL}/blob/main/CHANGELOG.md)"
    )
    if len(content) > MAX_CONTENT_LENGTH:
        raise DiscordAnnouncementError(
            f"Discord announcement is {len(content)} characters; "
            f"keep it within {MAX_CONTENT_LENGTH} characters"
        )
    return entry, version, content


def should_announce(changelog: str, previous_changelog: str | None) -> bool:
    """Announce only when the newest entry differs from the previous main commit."""
    current_entry = latest_entry(changelog)
    if previous_changelog is None:
        return True
    try:
        return current_entry != latest_entry(previous_changelog)
    except ChangelogError:
        return True


def webhook_url_with_wait(webhook_url: str) -> str:
    """Request Discord's confirmation response while preserving existing query fields."""
    parts = urlsplit(webhook_url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if key != "wait"]
    query.append(("wait", "true"))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def payload_for(content: str) -> dict[str, object]:
    """Build a webhook payload with mentions disabled."""
    if not content or len(content) > MAX_CONTENT_LENGTH:
        raise DiscordAnnouncementError(
            f"Discord message content must be between 1 and {MAX_CONTENT_LENGTH} characters"
        )
    return {"content": content, "allowed_mentions": {"parse": []}}


def _previous_changelog(before_sha: str, path: Path) -> str | None:
    if not GIT_REVISION.fullmatch(before_sha):
        return None
    result = subprocess.run(
        ["git", "show", f"{before_sha}:{path.as_posix()}"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout if result.returncode == 0 else None


def post_webhook(webhook_url: str, payload: dict[str, object]) -> None:
    """Send JSON to Discord without printing the secret webhook URL."""
    if not webhook_url:
        raise DiscordAnnouncementError("DISCORD_WEBHOOK_URL is not configured")
    request = Request(
        webhook_url_with_wait(webhook_url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            if not 200 <= response.status < 300:
                raise DiscordAnnouncementError(
                    f"Discord webhook returned HTTP {response.status}"
                )
    except HTTPError as exc:
        raise DiscordAnnouncementError(
            _discord_http_error(exc, webhook_url)
        ) from None
    except URLError:
        raise DiscordAnnouncementError("Could not reach the Discord webhook") from None


def _discord_http_error(exc: HTTPError, webhook_url: str) -> str:
    """Return Discord's useful error fields without exposing webhook credentials."""
    detail = f"Discord webhook returned HTTP {exc.code}"
    try:
        response = json.loads(exc.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return detail
    if not isinstance(response, dict):
        return detail

    message = response.get("message")
    code = response.get("code")
    if not isinstance(message, str):
        return detail

    # Error messages are normally fixed Discord text. Redact URL credentials in
    # case an intermediary echoes request details back in its response.
    parts = urlsplit(webhook_url)
    secrets = [webhook_url, parts.path.rsplit("/", 1)[-1]]
    for secret in secrets:
        if secret:
            message = message.replace(secret, "[redacted]")
    message = " ".join(message.split())[:240]
    if isinstance(code, int) and not isinstance(code, bool):
        return f"{detail} (Discord error {code}: {message})"
    return f"{detail} ({message})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument(
        "--plugin-manifest", type=Path, default=Path("freemovement-law/plugin.json")
    )
    args = parser.parse_args()

    try:
        changelog = args.changelog.read_text(encoding="utf-8")
        plugin_metadata = json.loads(args.plugin_manifest.read_text(encoding="utf-8"))
        entry, version, content = release_metadata(changelog, plugin_metadata)
        previous = _previous_changelog(os.environ.get("BEFORE_SHA", ""), args.changelog)
        force_announcement = os.environ.get("FORCE_ANNOUNCEMENT", "").lower() == "true"
        if not force_announcement and not should_announce(changelog, previous):
            print("Latest changelog entry is unchanged; skipping Discord announcement.")
            return 0
        payload = payload_for(content)
        post_webhook(os.environ.get("DISCORD_WEBHOOK_URL", ""), payload)
    except (OSError, json.JSONDecodeError, ChangelogError, DiscordAnnouncementError) as exc:
        parser.error(str(exc))
    print(f"Published FreeMovement v{version} changelog to Discord.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
