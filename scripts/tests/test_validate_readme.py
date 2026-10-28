"""Fixtures for scripts/validate-readme.py.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

from _load import REPO, load_script, script_path

SCRIPT = script_path("validate-readme.py")
vr = load_script("validate-readme.py")

MIT_TEXT = "MIT License\n\nCopyright (c) 2024 Someone\n\nPermission is hereby granted, free of charge, ...\n"
APACHE_TEXT = "                                 Apache License\n                           Version 2.0, January 2004\n"


def groups_for(content: str, project_type: str | None = None, verbosity: str | None = None,
               base_dir: str = ".", **kwargs) -> dict[str, list[str]]:
    groups, _, _ = vr.run_checks(content, project_type, verbosity, base_dir, **kwargs)
    return dict(groups)


def notes_for(content: str, project_type: str | None = None, verbosity: str | None = None,
              base_dir: str = ".", **kwargs) -> list[str]:
    return vr.run_checks(content, project_type, verbosity, base_dir, **kwargs)[2]


def padding(n: int) -> str:
    return "".join(f"Line {i} of prose.\n\n" for i in range(n // 2))


class RelativeLinkTests(unittest.TestCase):
    def test_missing_targets_flagged(self):
        content = ('# T\n\n[![L](https://img.shields.io/badge/a-b-c)](NOPE.md)\n'
                   '![x](docs/missing.png)\n<img src="gone.png" alt="g">\n<a href="nope/">n</a>\n')
        findings = groups_for(content, base_dir=REPO)["Broken links"]
        self.assertEqual([f.split(":")[0].strip() for f in findings], ["L3", "L4", "L5", "L6"])

    def test_existing_and_external_pass(self):
        content = ('# T\n\n[l](LICENSE) [s](scripts/) [a](#t) [m](mailto:a@b.c)\n'
                   '<img src="assets/banner.png" alt="b"> [u](https://x.dev/none.md)\n')
        self.assertNotIn("Broken links", groups_for(content, base_dir=REPO))

    def test_leading_slash_is_repo_root(self):
        content = "# T\n\n[l](/LICENSE) ![b](/assets/banner.png) [x](/docs/missing.md)\n"
        findings = groups_for(content, base_dir=REPO)["Broken links"]
        self.assertEqual(len(findings), 1)
        self.assertIn("/docs/missing.md", findings[0])

    def test_expect_paths_count_as_existing(self):
        content = ("# T\n\n[a](ARCHITECTURE.md) ![s](assets/screenshots/main.png) "
                   "![t](/assets/screenshots/sub/x.gif) [n](NOTES.md)\n")
        findings = groups_for(content, base_dir=REPO,
                              expect=["ARCHITECTURE.md", "assets/screenshots/"])["Broken links"]
        self.assertEqual(len(findings), 1)
        self.assertIn("NOTES.md", findings[0])

    def test_expect_is_not_a_prefix_match(self):
        content = "# T\n\n[a](ARCHITECTURE.md.bak) ![s](assets/screenshots-old/a.png)\n"
        findings = groups_for(content, base_dir=REPO,
                              expect=["ARCHITECTURE.md", "assets/screenshots"])["Broken links"]
        self.assertEqual(len(findings), 2)


class RunFirstTests(unittest.TestCase):
    def first(self, content: str):
        return vr.find_first_runnable(vr.parse_lines(content))

    def test_bash_block_line_reported(self):
        self.assertEqual(self.first("# T\n\nIntro.\n\n```bash\nnpm i x\n```\n"), (5, "```bash block"))

    def test_untagged_block_with_command(self):
        self.assertEqual(self.first("# T\n\n```\npip install x\n```\n")[0], 3)
        self.assertEqual(self.first("# T\n\n```\n$ x --help\n```\n")[0], 3)

    def test_untagged_non_command_block_ignored(self):
        self.assertIsNone(self.first("# T\n\n```\n/readme minimal\n```\n"))
        self.assertIsNone(self.first("# T\n\n```python\nimport x\n```\n"))

    def test_store_badge_counts(self):
        content = "# T\n\n[![Get it](b.png)](https://play.google.com/store/apps/details?id=x)\n"
        self.assertEqual(self.first(content), (3, "store link"))

    def test_releases_in_table_counts_but_version_badge_does_not(self):
        table = "# T\n\n| OS | Download |\n|---|---|\n| macOS | [dmg](https://github.com/o/r/releases/latest) |\n"
        self.assertEqual(self.first(table)[0], 5)
        badge = "# T\n\n[![v](https://img.shields.io/github/v/release/o/r)](https://github.com/o/r/releases)\n"
        self.assertIsNone(self.first(badge))

    def test_deploy_buttons_count(self):
        for url in ["https://heroku.com/deploy?template=https://github.com/o/r",
                    "https://vercel.com/new/clone?repository-url=https://github.com/o/r",
                    "https://app.netlify.com/start/deploy?repository=https://github.com/o/r",
                    "https://render.com/deploy?repo=https://github.com/o/r",
                    "https://railway.app/new/template/abc"]:
            with self.subTest(url=url):
                content = f"# T\n\n[![Deploy](https://example.com/button.svg)]({url})\n"
                self.assertEqual(self.first(content), (3, "deploy button"))

    def test_hosted_demo_links_count(self):
        for line in ["[Live demo](https://app.example.com)", "[Demo](https://app.example.com)",
                     "[Try it online](https://app.example.com)", "[Open app](https://app.example.com)",
                     "[![Demo](https://img.shields.io/badge/demo-online-blue)](https://app.example.com)",
                     "Live demo: https://app.example.com", "- **Try it:** <https://app.example.com>",
                     "[**Demo**](https://app.example.com)", "1. Demo: https://app.example.com"]:
            with self.subTest(line=line):
                self.assertEqual(self.first(f"# T\n\n{line}\n"), (3, "hosted demo link"))

    def test_other_links_are_not_hosted_demos(self):
        for line in ["[Demo video](https://youtube.com/watch?v=x)", "[Docs](https://docs.example.com)",
                     "[Demo](docs/demo.md)", "[Live reload](https://example.com/live-reload)",
                     "The demo lives at the bottom of the page."]:
            with self.subTest(line=line):
                self.assertIsNone(self.first(f"# T\n\n{line}\n"))

    def test_firmware_commands_count(self):
        self.assertEqual(self.first("# T\n\n```\npio run -t upload\n```\n")[0], 3)
        self.assertEqual(self.first("# T\n\n```\narduino-cli upload -p /dev/ttyUSB0\n```\n")[0], 3)

    def test_board_only_hardware_is_a_note(self):
        content = "# T\n\nA KiCad board. Order it from any fab.\n"
        with tempfile.TemporaryDirectory() as board:
            open(os.path.join(board, "board.kicad_pcb"), "w").close()
            self.assertNotIn("Run-first", groups_for(content, "hardware", base_dir=board))
            self.assertIn("board-only", notes_for(content, "hardware", base_dir=board)[0])
        with tempfile.TemporaryDirectory() as fw:
            open(os.path.join(fw, "platformio.ini"), "w").close()
            self.assertIn("Run-first", groups_for(content, "hardware", base_dir=fw))

    def test_toc_lines_not_counted(self):
        toc = "**Contents**\n\n" + "".join(f"- [S{i}](#s{i})\n" for i in range(30))
        content = "# T\n\n" + padding(60) + toc + "\n```bash\nmake\n```\n" + \
            "".join(f"## S{i}\n" for i in range(30))
        self.assertNotIn("Run-first", groups_for(content, "cli", "standard"))
        without = content.replace("**Contents**", "Sections")
        self.assertIn("Run-first", groups_for(without, "cli", "standard"))
        legacy = content.replace("**Contents**", "## Table of Contents")
        self.assertNotIn("Run-first", groups_for(legacy, "cli", "standard"))

    def test_generate_toc_output_is_recognised(self):
        headings = "".join(f"## S{i}\n" for i in range(30))
        toc = subprocess.run([sys.executable, script_path("generate-toc.py")], input="# T\n\n" + headings,
                             capture_output=True, text=True, check=True).stdout
        lines = vr.parse_lines("# T\n\n" + toc + "\n```bash\nmake\n```\n")
        self.assertEqual(vr.toc_line_count(lines, len(lines)), 32)

    def test_late_step_warns_standard(self):
        content = "# T\n\n" + padding(90) + "```bash\nmake\n```\n"
        self.assertIn("Run-first", groups_for(content, "cli", "standard"))

    def test_minimal_threshold_is_50(self):
        content = "# T\n\n" + padding(56) + "```bash\nmake\n```\n"
        self.assertIn("Run-first", groups_for(content, "cli", "minimal"))
        self.assertNotIn("Run-first", groups_for(content, "cli", "standard"))

    def test_missing_step_warns_except_educational(self):
        content = "# T\n\nNo commands here.\n"
        self.assertIn("Run-first", groups_for(content, "cli"))
        self.assertNotIn("Run-first", groups_for(content, "educational"))
        self.assertNotIn("Run-first", groups_for(content, "dotfiles"))
        with tempfile.TemporaryDirectory() as fw:
            open(os.path.join(fw, "Blink.ino"), "w").close()
            self.assertIn("Run-first", groups_for(content, "hardware", base_dir=fw))


class AnchorTests(unittest.TestCase):
    def test_slug_rules(self):
        self.assertEqual(vr.github_slug("Getting Started!"), "getting-started")
        self.assertEqual(vr.github_slug("`config.yaml` options"), "configyaml-options")
        self.assertEqual(vr.github_slug("snake_case & more"), "snake_case--more")
        self.assertEqual(vr.github_slug("[Link](x) here"), "link-here")

    def test_valid_anchors_pass(self):
        content = (
            "# T\n\n[a](#usage) [b](#usage-1) [c](#custom) <a href=\"#faq\">f</a> [top](#top)\n\n"
            "## Usage\n\n## Usage\n\n<a name=\"custom\"></a>\n\n## FAQ\n"
        )
        self.assertNotIn("Dead in-page anchors", groups_for(content))

    def test_dead_anchor_flagged(self):
        content = "# T\n\nSee [install](#instalation).\n\n## Installation\n"
        findings = groups_for(content)["Dead in-page anchors"]
        self.assertEqual(len(findings), 1)
        self.assertIn("L3", findings[0])

    def test_comment_opener_in_inline_code_is_not_a_comment(self):
        content = "# T\n\nEscapes `<!--` in output.\n\n## Options\n\n[o](#options) [x](#missing)\n"
        findings = groups_for(content)["Dead in-page anchors"]
        self.assertEqual(len(findings), 1)
        self.assertIn("#missing", findings[0])

    def test_anchor_in_code_ignored(self):
        content = "# T\n\n`[x](#nope)`\n\n```md\n[y](#nope)\n```\n"
        self.assertNotIn("Dead in-page anchors", groups_for(content))


class DuplicateH2Tests(unittest.TestCase):
    def test_duplicate_flagged(self):
        content = "# T\n\n## Installation\n\ntext\n\n## installation:\n"
        self.assertIn("L7", groups_for(content)["Duplicate H2 headings"][0])

    def test_distinct_pass(self):
        content = "# T\n\n## Install\n\n## Usage\n\n### Install\n"
        self.assertNotIn("Duplicate H2 headings", groups_for(content))


class BadgeTests(unittest.TestCase):
    def badge(self, label: str) -> str:
        return f"![{label}](https://img.shields.io/badge/{label}-1.0-blue)\n"

    def test_header_badge_cap(self):
        seven = "# T\n\n" + "".join(self.badge(f"b{i}") for i in range(7)) + "\n## Install\n"
        six = "# T\n\n" + "".join(self.badge(f"b{i}") for i in range(6)) + "\n## Install\n"
        self.assertIn("Header badge count", groups_for(seven))
        self.assertNotIn("Header badge count", groups_for(six))

    def test_badges_after_first_h2_not_counted(self):
        content = "# T\n\n## Status\n\n" + "".join(self.badge(f"b{i}") for i in range(8))
        self.assertNotIn("Header badge count", groups_for(content))

    def test_banner_image_not_a_badge(self):
        content = '<p align="center"><img src="assets/banner.png" alt="x"></p>\n\n' + \
            "".join(self.badge(f"b{i}") for i in range(6)) + "\n## Install\n"
        self.assertNotIn("Header badge count", groups_for(content))

    def test_dead_hosts(self):
        content = (
            "# T\n\n![b](https://travis-ci.org/o/r.svg?branch=main)\n"
            "![d](https://david-dm.org/o/r.svg)\n![n](https://nodei.co/npm/x.png)\n"
            "![a](https://ci.appveyor.com/api/projects/status/abc)\n"
            "![ok](https://badge.fury.io/js/x.svg)\n"
        )
        findings = groups_for(content)["Dead or misleading badges"]
        self.assertEqual([f.split(":")[0].strip() for f in findings], ["L3", "L4", "L5", "L6"])

    def test_static_status_shields(self):
        bad = [
            "https://img.shields.io/badge/build-passing-brightgreen",
            "https://img.shields.io/badge/coverage-95%25-green",
            "https://img.shields.io/badge/Maintained%3F-yes-green.svg",
            "https://img.shields.io/badge/maintained-yes-green",
            "https://img.shields.io/badge/docs-available-blue",
            "https://img.shields.io/badge/tests-failing-red",
            "https://img.shields.io/static/v1?label=build&message=passing&color=green",
        ]
        for url in bad:
            with self.subTest(url=url):
                self.assertIn("Dead or misleading badges", groups_for(f"# T\n\n![x]({url})\n"))

    def test_dynamic_and_plain_static_shields_pass(self):
        ok = [
            "https://img.shields.io/github/actions/workflow/status/o/r/ci.yml",
            "https://img.shields.io/codecov/c/github/o/r",
            "https://img.shields.io/badge/Flutter-3.12+-02569B?logo=flutter",
            "https://img.shields.io/badge/version-0.1.0--alpha.1-orange",
            "https://img.shields.io/badge/build_tool-gradle-blue",
        ]
        for url in ok:
            with self.subTest(url=url):
                self.assertNotIn("Dead or misleading badges", groups_for(f"# T\n\n![x]({url})\n"))


class PlaceholderTests(unittest.TestCase):
    def test_flagged(self):
        for text in ["TODO: write this", "Docs TBD.", "NEED TO ADD screenshots", "(link needed)",
                     "Lorem ipsum dolor", "INSERT LOGO", "INSERT: project tagline",
                     "INSERT SCREENSHOT HERE", "[placeholder]", "<placeholder>",
                     "PLACEHOLDER", "Set YOUR_KEY_HERE"]:
            with self.subTest(text=text):
                self.assertIn("Placeholder text", groups_for(f"# T\n\n{text}\n"))

    def test_prose_and_hidden_pass(self):
        for text in [
            "It leaves a placeholder that says exactly what to capture.",
            "Build a todo app in ten minutes.",
            "Tasks you need to add go in tasks.yml.",
            "<!-- TODO: screenshot of the dashboard -->",
            "<!--\nTODO: multi-line\ncomment\n-->",
            "Run `TODO=1 make`.",
            "```\n# TODO in code\n```",
            "[Todo list](todo.md) example",
            "Tracks every INSERT and UPDATE.",
            "Logs INSERT, UPDATE and DELETE statements.",
            "Batches INSERT INTO rows.",
            "INSERT statements are queued.",
            "Needs the INSERT PRIVILEGE and an INSERT TRIGGER.",
            "Press INSERT KEY to toggle INSERT MODE.",
        ]:
            with self.subTest(text=text):
                self.assertNotIn("Placeholder text", groups_for(f"# T\n\n{text}\n"))


class PositionalTests(unittest.TestCase):
    def test_flagged(self):
        for text in ["The animation above shows it.", "See the screenshot below.",
                     "As the image above shows", "The GIF below loops.", "the above screenshot", "Pictured above: the editor."]:
            with self.subTest(text=text):
                self.assertIn("Positional image references", groups_for(f"# T\n\n{text}\n"))

    def test_pass(self):
        for text in ["Images are stored above the fold limit? no", "See the commands below.", "Output as shown below:",
                     '<img src="a.png" alt="screenshot below the header">',
                     "```\nimage above\n```"]:
            with self.subTest(text=text):
                self.assertNotIn("Positional image references", groups_for(f"# T\n\n{text}\n"))


class LicenseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write_license(self, text: str, name: str = "LICENSE") -> None:
        with open(os.path.join(self.tmp.name, name), "w", encoding="utf-8") as f:
            f.write(text)

    def test_all_rights_reserved_with_mit(self):
        self.write_license(MIT_TEXT)
        content = "# T\n\n## License\n\nAll rights reserved.\n"
        self.assertIn("L5", groups_for(content, base_dir=self.tmp.name)["License mismatch"][0])

    def test_different_licence_named(self):
        self.write_license(APACHE_TEXT)
        content = "# T\n\n## License\n\nReleased under the [MIT](LICENSE) license.\n"
        self.assertIn("names MIT", groups_for(content, base_dir=self.tmp.name)["License mismatch"][0])

    def test_matching_licence_passes(self):
        self.write_license(MIT_TEXT)
        content = "# T\n\n## License\n\nMIT\n\nApache is mentioned elsewhere.\n\n## Other\n\nGPL tools.\n"
        self.assertNotIn("License mismatch", groups_for(content, base_dir=self.tmp.name))

    def test_dual_licence_passes(self):
        self.write_license(MIT_TEXT, "LICENSE-MIT")
        self.write_license(APACHE_TEXT, "LICENSE-APACHE")
        content = "# T\n\n## License\n\nMIT or Apache-2.0, at your option.\n"
        self.assertNotIn("License mismatch", groups_for(content, base_dir=self.tmp.name))

    def test_bsd_file_with_reserved_line_passes(self):
        self.write_license("Copyright (c) 2020, X\nAll rights reserved.\n\n"
                           "Redistribution and use in source and binary forms ...\n")
        content = "# T\n\n## License\n\nBSD-3-Clause. Copyright (c) 2020 X. All rights reserved.\n"
        self.assertNotIn("License mismatch", groups_for(content, base_dir=self.tmp.name))

    def test_no_license_file_skips(self):
        content = "# T\n\n## License\n\nAll rights reserved.\n"
        self.assertNotIn("License mismatch", groups_for(content, base_dir=self.tmp.name))


class StyleAttrTests(unittest.TestCase):
    def test_flagged(self):
        content = '# T\n\n<img src="a.png" style="filter: invert(1)">\n<p\n  style="color:red">x</p>\n'
        findings = groups_for(content)["HTML style attributes"]
        self.assertEqual([f.split(":")[0].strip() for f in findings], ["L3", "L4"])

    def test_query_param_and_code_pass(self):
        content = ('# T\n\n<img src="https://img.shields.io/badge/a-b-c?style=flat">\n\n'
                   '`<div style="x">`\n\n```html\n<div style="x"></div>\n```\n')
        self.assertNotIn("HTML style attributes", groups_for(content))


class TitleTests(unittest.TestCase):
    def test_banner_image_counts_as_title(self):
        content = '<p align="center">\n  <img src="banner.png" alt="write-readme" width="800">\n</p>\n\n## Install\n'
        self.assertNotIn("Structure issues", groups_for(content))

    def test_html_h1_counts(self):
        self.assertNotIn("Structure issues", groups_for('<h1 align="center">Name</h1>\n\ntext\n'))

    def test_untitled_flagged(self):
        self.assertIn("Structure issues", groups_for("Just text.\n\n## Install\n"))
        self.assertIn("Structure issues", groups_for('<img src="banner.png" alt="">\n\n## Install\n'))

    def test_multiple_h1_flagged(self):
        self.assertIn("Structure issues", groups_for("# A\n\n# B\n"))


class LengthTests(unittest.TestCase):
    def content(self, n: int, tail: str = "") -> str:
        return "# T\n" + "x\n" * (n - 1 - tail.count("\n")) + tail

    def length(self, n: int, project_type: str | None, verbosity: str | None, tail: str = "",
               **kwargs) -> list[str]:
        return groups_for(self.content(n, tail), project_type, verbosity, **kwargs).get("Length issues", [])

    def short(self, n: int, project_type: str | None, verbosity: str | None, **kwargs) -> list[str]:
        """Length notes (below-minimum) for an n-line README."""
        return [note for note in notes_for(self.content(n), project_type, verbosity, **kwargs)
                if note.strip().startswith("Length")]

    def test_standard_uses_table_range(self):
        self.assertEqual(self.length(150, "mobile", "standard"), [])
        self.assertEqual(self.length(150, "mobile", None), [])
        self.assertEqual(self.short(150, "mobile", "standard"), [])
        self.assertIn("minimum of 150", self.short(149, "mobile", "standard")[0])
        self.assertIn("maximum of 500", self.length(501, "cli", "standard")[0])

    def test_below_minimum_is_a_note_not_an_issue(self):
        self.assertEqual(self.length(10, "mobile", "standard"), [])
        self.assertIn("do not pad", self.short(10, "mobile", "standard")[0])

    def test_dotfiles_and_hardware_are_length_checked(self):
        self.assertEqual(self.length(30, "dotfiles", "standard"), [])
        self.assertIn("minimum of 30", self.short(29, "dotfiles", "standard")[0])
        self.assertIn("maximum of 200", self.length(201, "dotfiles", "standard")[0])
        self.assertEqual(self.length(100, "hardware", "standard"), [])
        self.assertIn("minimum of 100", self.short(99, "hardware", "standard")[0])
        self.assertIn("maximum of 400", self.length(401, "hardware", "standard")[0])
        self.assertIn("maximum of 520", self.length(521, "hardware", "detailed")[0])

    def test_minimal_is_absolute(self):
        self.assertEqual(self.length(30, "ml", "minimal"), [])
        self.assertIn("maximum of 80", self.length(81, "ml", "minimal")[0])
        self.assertIn("minimum of 30", self.short(29, "cli", "minimal")[0])

    def test_early_stage_wins_over_verbosity_and_type(self):
        for verbosity in [None, "minimal", "standard", "detailed"]:
            with self.subTest(verbosity=verbosity):
                self.assertEqual(self.length(60, "ml", verbosity, early_stage=True), [])
                self.assertIn("maximum of 60 for early-stage",
                              self.length(61, "ml", verbosity, early_stage=True)[0])
                self.assertIn("minimum of 30", self.short(29, "ml", verbosity, early_stage=True)[0])
        self.assertIn("maximum of 60", self.length(61, None, None, early_stage=True)[0])

    def test_detailed_stretch_and_cli_override(self):
        self.assertEqual(self.length(390, "web-app", "detailed"), [])
        self.assertIn("maximum of 390", self.length(391, "web-app", "detailed")[0])
        self.assertEqual(self.length(1200, "tui", "detailed"), [])
        self.assertIn("maximum of 1200", self.length(1201, "cli", "detailed")[0])

    def test_educational_has_no_max(self):
        self.assertEqual(self.length(9000, "educational", "standard"), [])

    def test_appendix_after_license_excluded_in_detailed(self):
        appendix = "## License\n\nMIT\n\n## Appendix: Flags\n" + "f\n" * 100
        self.assertEqual(self.length(450, "web-app", "detailed", appendix), [])
        self.assertTrue(self.length(450, "web-app", "standard", appendix))
        early = "## Appendix: Flags\n" + "f\n" * 100 + "## License\n\nMIT\n"
        self.assertTrue(self.length(450, "web-app", "detailed", early))

    def test_targets_come_from_type_slugs_json(self):
        data = vr.load_type_slugs()
        self.assertEqual(vr.LENGTH_TARGETS, {k: tuple(v["target_lines"]) for k, v in data.items()})
        self.assertEqual(vr.DETAILED_MAX_OVERRIDES, {"cli": 1200, "tui": 1200})


class RepoFileTests(unittest.TestCase):
    """End-to-end runs on the repo's own README and the Ganba example."""

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=REPO,
                              capture_output=True, text=True, check=False)

    def test_repo_readme(self):
        with open(os.path.join(REPO, "README.md"), encoding="utf-8") as f:
            install_line = next(i for i, ln in enumerate(f, start=1) if ln.startswith("```bash"))
        for project_type in ["cli", "other"]:
            with self.subTest(project_type=project_type):
                result = self.run_script("README.md", "--type", project_type, "--dir", ".")
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertTrue(result.stdout.startswith("All checks passed."))
                self.assertIn(f"first runnable step: L{install_line} (```bash block)", result.stdout)

    def test_ganba_example(self):
        result = self.run_script("examples/ganba-mobile-app.md", "--type", "mobile", "--dir", "examples")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Notes (do not affect the exit code):", result.stdout)
        self.assertIn("below the target minimum of 150 for mobile/standard", result.stdout)

    def test_unknown_type_rejected(self):
        result = self.run_script("README.md", "--type", "nonsense")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice: 'nonsense'", result.stderr)

    def test_early_stage_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "README.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# T\n\n```bash\nmake\n```\n" + "x\n" * 70)
            result = self.run_script(path, "--type", "ml", "--verbosity", "detailed",
                                     "--early-stage", "--dir", tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("exceeds the target maximum of 60 for early-stage", result.stdout)

    def test_expect_flag_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "README.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# T\n\n```bash\nmake\n```\n\n[a](ARCHITECTURE.md) ![s](assets/s/a.png)\n")
            self.assertEqual(self.run_script(path, "--dir", tmp).returncode, 1)
            ok = self.run_script(path, "--dir", tmp, "--expect", "ARCHITECTURE.md", "--expect", "assets/s")
        self.assertEqual(ok.returncode, 0, ok.stdout)


if __name__ == "__main__":
    unittest.main()
