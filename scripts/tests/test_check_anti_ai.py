"""Fixtures for scripts/check-anti-ai.py: line rules, rule-12 scoping and CLI help.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import subprocess
import sys
import unittest

from _load import REPO, load_script, script_path

SCRIPT = script_path("check-anti-ai.py")
ca = load_script("check-anti-ai.py")


def findings(content: str, rule: str | None = None) -> list[tuple[str, str]]:
    return [(f["rule"], f["text"]) for f in ca.check_content(content)
            if rule is None or f["rule"] == rule]


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

    def test_single_hyphen_labels_flagged(self):
        content = "# T\n\n- **Fast** - parses in 2s\n- **Small** - 4 kB\n- **Typed** - ships .d.ts\n"
        self.assertEqual(bold_lines(content), [3, 4, 5])

    def test_hyphenated_bold_word_is_not_a_label(self):
        content = "# T\n\n- **Fast**-ish parsing\n- **Small**-ish output\n- **Typed**-ish API\n"
        self.assertEqual(bold_lines(content), [])

    def test_mixed_list_counts_plain_labels_only(self):
        content = FEATURES + "- **main.go** -- entry point\n"
        self.assertEqual(bold_lines(content), [5, 6, 7])

    def test_period_and_colon_inside_bold_flagged(self):
        """The TinySim run's shape: "**Label.** text" on every item."""
        content = ("# T\n\n## Features\n\n"
                   "- **Evolving brains.** Each agent has a NEAT network that grows over generations.\n"
                   "- **Heritable traits.** Size, speed and vision pass to offspring.\n"
                   "- **Speciation.** Agents split into named species by genome distance.\n"
                   "- **Predation:** agents can attack and eat each other.\n")
        self.assertEqual(bold_lines(content), [5, 6, 7, 8])

    def test_period_labels_exempt_in_reference_lists(self):
        content = ("# T\n\n## Configuration\n\n- **Seed.** World seed.\n"
                   "- **Size.** World size.\n- **Food.** Food limit.\n")
        self.assertEqual(bold_lines(content), [])
        paths = "# T\n\n- **train.py.** Trains.\n- **data/loader.** Batches.\n- **`cfg`.** Settings.\n"
        self.assertEqual(bold_lines(paths), [])

    def test_single_bold_lead_and_inline_keywords_pass(self):
        content = ("# T\n\n- **Note.** Back up your saves first.\n- Pick a **seed** to repeat a run.\n"
                   "- Press **Play** to start.\n- Use **Tab** for analytics.\n")
        self.assertEqual(bold_lines(content), [])
        two = "# T\n\n- **Fast.** Parses in 2s.\n- **Small.** 4 kB.\n- Typed: ships .d.ts.\n"
        self.assertEqual(bold_lines(two), [])

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


class ProseOnlyTests(unittest.TestCase):
    """check_content scans rendered prose: inline code and HTML comments are skipped."""

    def test_inline_code_identifier_ignored(self):
        self.assertEqual(findings("# T\n\nInstall with `npm i comprehensive-lib`.\n"), [])

    def test_html_comment_ignored(self):
        content = ("# T\n\n<!-- screenshot:dash | description=Showcase the robust dashboard -->\n"
                   "<!--\nLet's leverage this\n-->\n")
        self.assertEqual(findings(content), [])

    def test_prose_next_to_code_still_flagged(self):
        content = "# T\n\nRun `npm i comprehensive-lib` for a robust setup. <!-- seamless -->\n"
        self.assertEqual(findings(content), [("banned-word", "robust")])

    def test_context_is_the_raw_line(self):
        f = ca.check_content("# T\n\nA robust `x` tool.\n")[0]
        self.assertEqual(f["context"], "A robust `x` tool.")


class BannedWordInflectionTests(unittest.TestCase):
    def test_review_sentence(self):
        content = ("# T\n\nIt leverages caches, Empowers teams, Streamlined setup, Showcases output, "
                   "Utilizes threads and syncs Seamlessly.\n")
        self.assertEqual(sorted(t for _, t in findings(content, "banned-word")),
                         ["empowers", "leverages", "seamlessly", "showcases", "streamlined", "utilizes"])

    def test_more_inflections(self):
        for text in ["delved", "delving", "harnessing", "harnesses", "elevating", "embarked",
                     "tapestries", "fostering", "realms", "paradigms", "utilising", "utilization",
                     "holistically", "robustness", "comprehensively", "unpacked", "facilitates",
                     "empowerment", "pivotally", "meticulously", "beacons"]:
            with self.subTest(text=text):
                self.assertEqual(len(findings(f"# T\n\nWe saw {text} here.\n", "banned-word")), 1)

    def test_unrelated_words_not_matched(self):
        for text in ["elevator", "elevation", "realmente", "unpacker", "fosterage",
                     "showcasement", "robusta", "delver", "levers"]:
            with self.subTest(text=text):
                self.assertEqual(findings(f"# T\n\nWe saw {text} here.\n", "banned-word"), [])

    def test_multi_word_entries_exact(self):
        self.assertEqual(findings("# T\n\nA deep dive into best practices.\n", "banned-word"),
                         [("banned-word", "deep dive"), ("banned-word", "best practices")])
        self.assertEqual(findings("# T\n\nDeep dives and best practice notes.\n", "banned-word"), [])


class PhraseTests(unittest.TestCase):
    def test_template_phrases(self):
        for text, hit in [("This is a bold step towards better tools.", "step towards"),
                          ("A first step toward sanity.", "step toward"),
                          ("It serves as the base layer.", "serves as the"),
                          ("It serves as an adapter.", "serves as an"),
                          ("It serves as a cache.", "serves as a")]:
            with self.subTest(text=text):
                self.assertEqual(findings(f"# T\n\n{text}\n", "template-phrase"),
                                 [("template-phrase", hit)])

    def test_serves_without_article_passes(self):
        self.assertEqual(findings("# T\n\nIt serves assets as static files.\n"), [])

    def test_lets_openers(self):
        for text, hit in [("Let's get started.", "Let's get"),
                          ("Let\u2019s get started.", "Let\u2019s get"),
                          ("- Let's begin", "Let's begin"),
                          ("1. Let's begin", "Let's begin"),
                          ("## Let's build", "Let's build"),
                          ("> Let's go", "Let's go")]:
            with self.subTest(text=text):
                self.assertEqual(findings(f"# T\n\n{text}\n", "lets-opener"), [("lets-opener", hit)])

    def test_lets_without_apostrophe_passes(self):
        self.assertEqual(findings("# T\n\n- Lets you stream logs.\n"), [])

    def test_emoji_in_heading(self):
        for heading in ["## \u2b50 Features", "## \U0001f680 Quick start", "## \u2705 Done",
                        "## \u23f1 Benchmarks", "## \U0001f195 New"]:
            with self.subTest(heading=heading):
                self.assertEqual(len(findings(f"# T\n\n{heading}\n", "emoji-in-heading")), 1)
        self.assertEqual(findings("# T\n\n## Migrating 1.x \u2192 2.x\n"), [])
        self.assertEqual(findings("# T\n\n## The `\u2b50` flag\n"), [])


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
