"""Fixtures for scripts/check-anti-ai.py rule-12 scoping and CLI help.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import subprocess
import sys
import unittest

from _load import REPO, load_script, script_path

SCRIPT = script_path("check-anti-ai.py")
ca = load_script("check-anti-ai.py")


def bold_lines(content: str) -> list[int]:
    return [f["line"] for f in ca.check_content(content) if f["rule"] == "bold-label-list"]


FEATURES = """# T

## Features

- **Fast** -- builds in 2s
- **Small** -- 4 kB gzipped
- **Typed**: ships .d.ts files
"""


class BoldLabelTests(unittest.TestCase):
    def test_feature_list_flagged(self):
        self.assertEqual(bold_lines(FEATURES), [5, 6, 7])

    def test_plain_labels_flagged_without_heading(self):
        self.assertEqual(len(bold_lines(FEATURES.replace("## Features\n", ""))), 3)

    def test_file_and_code_labels_exempt(self):
        content = """# T

## What's inside

- **train.py** -- trains the model
- **data/loader** -- batches images
- **`config.yaml`** -- hyperparameters
- **`--epochs`**: number of passes
"""
        self.assertEqual(bold_lines(content), [])

    def test_reference_headings_exempt(self):
        for heading in ["Project Structure", "Files", "Layout", "Configuration", "Options",
                        "CLI flags", "API", "Reference", "Languages", "Environment variables"]:
            content = FEATURES.replace("## Features", f"## {heading}")
            with self.subTest(heading=heading):
                self.assertEqual(bold_lines(content), [])

    def test_exemption_ends_at_next_heading(self):
        content = "# T\n\n## Configuration\n\n- **a**: b\n- **c**: d\n- **e**: f\n\n" + FEATURES[4:]
        self.assertEqual(len(bold_lines(content)), 3)

    def test_exemption_covers_subsections(self):
        content = "# T\n\n## Configuration\n\n### Advanced\n\n- **a**: b\n- **c**: d\n- **e**: f\n"
        self.assertEqual(bold_lines(content), [])

    def test_feature_heading_not_exempt(self):
        content = FEATURES.replace("## Features", "## Features and options")
        self.assertEqual(len(bold_lines(content)), 3)

    def test_tilde_fence_is_code(self):
        self.assertEqual(ca.check_content("# T\n\n~~~\nwe leverage it\n~~~\n"), [])

    def test_mixed_list_counts_plain_labels_only(self):
        content = FEATURES + "- **main.go** -- entry point\n"
        self.assertEqual(bold_lines(content), [5, 6, 7])

    def test_old_ganba_feature_list_still_flagged(self):
        try:
            old = subprocess.run(
                ["git", "show", "3c9f3e4~1:examples/ganba-mobile-app.md"],
                cwd=REPO, capture_output=True, text=True, check=True,
            ).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("git history for the old Ganba example is unavailable")
        self.assertEqual(len(bold_lines(old)), 11)


class CommentTests(unittest.TestCase):
    def test_comment_opener_in_inline_code_keeps_scanning(self):
        content = "# T\n\nEscapes `<!--` in output.\n\nWe leverage it.\n"
        self.assertIn("banned-word", [f["rule"] for f in ca.check_content(content)])


class CliTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=REPO,
                              capture_output=True, text=True, check=False)

    def test_help_text_matches_default(self):
        help_text = " ".join(self.run_script("--help").stdout.split())
        self.assertNotIn("all severities", help_text)
        self.assertIn("(default: P0)", help_text)

    def test_repo_files_clean(self):
        for path in ["README.md", "examples/ganba-mobile-app.md"]:
            with self.subTest(path=path):
                self.assertEqual(self.run_script("--file", path, "--severity", "P2").returncode, 0)


if __name__ == "__main__":
    unittest.main()
