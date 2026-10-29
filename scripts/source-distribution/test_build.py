from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from build import accepted_paths


class AcceptedPathsTests(unittest.TestCase):
    def test_external_scope_acceptance_does_not_accept_candidate_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary) / "source-library"
            pack = source_root / "liechtenstein"
            pack.mkdir(parents=True)

            acceptance = {
                "records": {
                    "li-41": {
                        "status": "accepted_with_narrow_external_scope",
                        "local_copy_accepted": False,
                        "decision": "accepted_with_narrow_external_scope",
                        "legalize_candidate_snapshot": {
                            "repository": "legalize-dev/legalize-li",
                            "path": "li/LGBl-2020-465.md",
                            "status": "candidate_snapshot_method_only",
                        },
                    }
                }
            }

            self.assertEqual(accepted_paths(acceptance, source_root, pack), [])

    def test_explicitly_accepted_local_copy_is_still_distributed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary) / "source-library"
            pack = source_root / "liechtenstein"
            document = pack / "documents" / "accepted-act.md"
            document.parent.mkdir(parents=True)
            document.write_text("Synthetic accepted local text\n", encoding="utf-8")

            acceptance = {
                "records": {
                    "li-test": {
                        "local_copy_accepted": True,
                        "path": "documents/accepted-act.md",
                    }
                }
            }

            result = accepted_paths(acceptance, source_root, pack)
            self.assertEqual([item[0] for item in result], [document.resolve()])


if __name__ == "__main__":
    unittest.main()
