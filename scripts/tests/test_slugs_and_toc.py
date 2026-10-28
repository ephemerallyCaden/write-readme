"""GitHub slugs (_mdlib), generate-toc.py anchors, and the shared badge cap.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import subprocess
import sys
import unittest

from _load import REPO, load_script, script_path

import _mdlib

toc = load_script("generate-toc.py")
badges = load_script("generate-badges.py")
vr = load_script("validate-readme.py")


def toc_for(content: str, include_h3: bool = False) -> list[str]:
    return toc.generate_toc(toc.extract_headings(content), include_h3)


class SlugTests(unittest.TestCase):
    def test_punctuation_keeps_repeated_hyphens(self):
        self.assertEqual(_mdlib.github_slug("Build & Test"), "build--test")
        self.assertEqual(_mdlib.github_slug("Q&A -- notes"), "qa----notes")

    def test_emphasis_and_underscores(self):
        cases = {
            "**Bold** heading": "bold-heading",
            "_private_ fields": "private-fields",
            "__init__ hooks": "init-hooks",
            "snake_case names": "snake_case-names",
            "`__all__` export": "__all__-export",
            "*Em* and ~~strike~~": "em-and-strike",
        }
        for text, slug in cases.items():
            with self.subTest(text=text):
                self.assertEqual(_mdlib.github_slug(text), slug)

    def test_duplicates_numbered_across_all_levels(self):
        self.assertEqual(_mdlib.unique_slugs(["Usage", "Usage", "Usage-1", "Usage"]),
                         ["usage", "usage-1", "usage-1-1", "usage-2"])


class TocTests(unittest.TestCase):
    def test_build_and_test(self):
        self.assertEqual(toc_for("# T\n\n## Build & Test\n"), ["- [Build & Test](#build--test)"])

    def test_duplicate_headings_count_excluded_levels(self):
        content = "# Usage\n\n## Usage\n\n#### Usage\n\n## Usage\n"
        self.assertEqual(toc_for(content), ["- [Usage](#usage-1)", "- [Usage](#usage-3)"])

    def test_h3_nested_and_emphasis(self):
        content = "# T\n\n## _private_ API\n\n### `__init__` args\n"
        self.assertEqual(toc_for(content, include_h3=True),
                         ["- [_private_ API](#private-api)", "  - [`__init__` args](#__init__-args)"])

    def test_tilde_fenced_heading_ignored(self):
        self.assertEqual(toc_for("# T\n\n~~~\n## Not a heading\n~~~\n\n## Real\n"), ["- [Real](#real)"])

    def test_front_matter_is_not_a_heading(self):
        content = "---\nname: x\ndescription: y\n---\n\n# T\n\nIntro\n---\n\n## Real\n"
        self.assertEqual(toc_for(content), ["- [Intro](#intro)", "- [Real](#real)"])

    def test_cli_output_is_bold_label_not_heading(self):
        result = subprocess.run([sys.executable, script_path("generate-toc.py")],
                                input="# T\n\n## Install\n\n### From source\n\n## Usage\n",
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, "**Contents**\n\n- [Install](#install)\n- [Usage](#usage)\n")
        self.assertEqual(_mdlib.collect_headings(_mdlib.parse_lines(result.stdout)), [])

    def test_cli_h3_option(self):
        result = subprocess.run([sys.executable, script_path("generate-toc.py"), "--h3"],
                                input="# T\n\n## Install\n\n### From source\n",
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.splitlines()[2:],
                         ["- [Install](#install)", "  - [From source](#from-source)"])

    def test_generated_toc_passes_anchor_check(self):
        body = "## Build & Test\n\n## Usage\n\n### Usage\n\n## Usage\n\n## __init__ and snake_case\n"
        result = subprocess.run([sys.executable, script_path("generate-toc.py"), "--h3"],
                                input="# T\n\n" + body, capture_output=True, text=True, check=True)
        readme = "# T\n\n" + result.stdout + "\n" + body
        groups, _, _ = vr.run_checks(readme, None, None, REPO)
        self.assertNotIn("Dead in-page anchors", dict(groups))


class BadgeCapTests(unittest.TestCase):
    def test_shared_constant(self):
        self.assertIs(vr.MAX_HEADER_BADGES, _mdlib.MAX_HEADER_BADGES)
        many = badges.generate_badges(owner="o", repo="r", ecosystem="npm", package="p",
                                      license_name="MIT", ci_workflow="ci.yml")
        self.assertLessEqual(len(many), _mdlib.MAX_HEADER_BADGES)


if __name__ == "__main__":
    unittest.main()
