#!/usr/bin/env python3
"""Fail on compatibility-version drift between skill metadata and the C1/C7 binding."""
from pathlib import Path
import json
import unittest

from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]


class ResourceIndexTests(unittest.TestCase):
    def test_source_resource_index_compatibility_version_matches(self):
        index=(ROOT/'SKILL.md').read_text()
        manifest=json.loads((compatibility_root()/'core-source-pack-manifest-0.6.1.json').read_text())
        self.assertIn('The C1 manifest at `../eudirective-source-library/compatibility/core-source-pack/core-source-pack-0.6.1/core-source-pack-manifest-0.6.1.json` is a legacy compatibility contract',index)
        self.assertIn('compatibility manifests and provenance metadata only',index)
        self.assertNotIn('0.6.0 active manifests',index)
        self.assertNotIn('Normal v0.33.0 use',index)
        self.assertIn("'core_version': '0.36.0'",(ROOT/'scripts/verify_bundled_source_pack.py').read_text())
        self.assertNotIn('0.6.0 active) is evaluated', (ROOT/'references/c7-hardening.md').read_text())
        self.assertIn('0.6.1',json.dumps(manifest))


if __name__=='__main__':
    unittest.main(verbosity=2)
