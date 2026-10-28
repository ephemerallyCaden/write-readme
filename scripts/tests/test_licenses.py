"""The license texts in references/licenses/ that Phase 6 copies into a project.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import hashlib
import os
import unittest

from _load import REPO, load_script

vr = load_script("validate-readme.py")

LICENSES = os.path.join(REPO, "references", "licenses")

# SHA-256 of the canonical texts: gnu.org/licenses/gpl-3.0.txt and
# apache.org/licenses/LICENSE-2.0.txt. MIT has no single canonical file;
# ours is choosealicense.com's, word-identical to SPDX apart from placeholders.
SHA256 = {
    "GPL-3.0.txt": "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
    "Apache-2.0.txt": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
}


def read(name: str) -> str:
    with open(os.path.join(LICENSES, name), encoding="utf-8") as f:
        return f.read()


class LicenseTextTests(unittest.TestCase):
    def test_canonical_texts_are_unmodified(self):
        for name, digest in SHA256.items():
            with self.subTest(name=name):
                data = read(name).encode("utf-8")
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest)

    def test_mit_keeps_its_placeholders(self):
        self.assertIn("Copyright (c) [year] [fullname]", read("MIT.txt"))

    def test_validate_readme_identifies_each_text(self):
        expected = {"MIT.txt": "MIT", "Apache-2.0.txt": "Apache", "GPL-3.0.txt": "GPL"}
        for name, family in expected.items():
            with self.subTest(name=name):
                self.assertEqual(vr.identify_license(read(name)), family)


if __name__ == "__main__":
    unittest.main()
