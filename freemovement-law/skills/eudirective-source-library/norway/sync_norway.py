#!/usr/bin/env python3
"""Disabled legacy Norway updater.

This helper previously wrote candidate Markdown and capture manifests into the
country pack. Norway's candidate artifacts now belong in the EU Source Update
Monitor local-only archive. No Norway-specific Monitor pack action is
registered, so this helper cannot safely sync or replay the archived data.
"""

import sys

MESSAGE = (
    "Norway sync_norway.py is disabled. It wrote candidates and manifests into "
    "the country pack, which is no longer the accepted workflow. No Norway "
    "Source Monitor action is registered. Use the manual complete-national-"
    "source-pack workflow and save candidate, discovery, raw and derived "
    "captures with the Monitor local-research archive before review."
)


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"sync", "verify"}:
        raise SystemExit("usage: sync_norway.py sync|verify")
    raise SystemExit(MESSAGE)


if __name__ == "__main__":
    main()
