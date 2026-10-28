"""The license and Code of Conduct texts that Phase 6 copies into a project.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import hashlib
import os
import unittest

from _load import REPO, load_script

vr = load_script("validate-readme.py")

LICENSES = os.path.join(REPO, "references", "licenses")
CONDUCT = os.path.join(REPO, "references", "community", "CODE_OF_CONDUCT-2.1.md")
# SHA-256 of contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md,
# byte for byte (it starts with a blank line).
CONDUCT_SHA256 = "977d781349351fd7c1f076e4c7dc7de2a05b40e12c773542c3815dd4ce7f37ba"

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


class ConductTextTests(unittest.TestCase):
    def setUp(self):
        with open(CONDUCT, "rb") as f:
            self.data = f.read()

    def test_canonical_text_is_unmodified(self):
        self.assertEqual(hashlib.sha256(self.data).hexdigest(), CONDUCT_SHA256)

    def test_contact_placeholder_appears_once(self):
        text = self.data.decode("utf-8")
        self.assertEqual(text.count(vr.CONDUCT_PLACEHOLDER), 1)
        self.assertIn(f"enforcement at {vr.CONDUCT_PLACEHOLDER}.", text)


if __name__ == "__main__":
    unittest.main()
