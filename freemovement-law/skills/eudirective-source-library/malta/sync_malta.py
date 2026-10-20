#!/usr/bin/env python3
"""Malta inventory sync wrapper; ELI PDF retrieval URLs are in the manifest."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync_candidate_pages as generic

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"sync", "verify"}:
        raise SystemExit("usage: sync_malta.py sync|verify")
    if sys.argv[1] == "sync":
        generic.sync("malta")
    else:
        generic.verify("malta")

if __name__ == "__main__":
    main()
