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
               base_dir: str = ".") -> dict[str, list[str]]:
    groups, _ = vr.run_checks(content, project_type, verbosity, base_dir)
    return dict(groups)


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
                     "Lorem ipsum dolor", "INSERT LOGO", "[placeholder]", "<placeholder>",
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
    def length(self, n: int, project_type: str, verbosity: str | None, tail: str = "") -> list[str]:
        content = "# T\n" + "x\n" * (n - 1 - tail.count("\n")) + tail
        return groups_for(content, project_type, verbosity).get("Length issues", [])

    def test_standard_uses_table_range(self):
        self.assertEqual(self.length(150, "mobile", "standard"), [])
        self.assertEqual(self.length(150, "mobile", None), [])
        self.assertIn("minimum of 150", self.length(149, "mobile", "standard")[0])
        self.assertIn("maximum of 500", self.length(501, "cli", "standard")[0])

    def test_minimal_is_absolute(self):
        self.assertEqual(self.length(30, "ml", "minimal"), [])
        self.assertIn("maximum of 80", self.length(81, "ml", "minimal")[0])
        self.assertIn("minimum of 30", self.length(29, "cli", "minimal")[0])

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


class RepoFileTests(unittest.TestCase):
    """End-to-end runs on the repo's own README and the Ganba example."""

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=REPO,
                              capture_output=True, text=True, check=False)

    def test_repo_readme(self):
        out = self.run_script("README.md", "--type", "other", "--dir", ".").stdout
        self.assertNotIn("Placeholder text", out)
        self.assertNotIn("Structure issues", out)
        self.assertIn("first runnable step: L19", out)

    def test_ganba_example(self):
        out = self.run_script("examples/ganba-mobile-app.md", "--type", "mobile", "--dir", "examples").stdout
        groups = [ln for ln in out.splitlines()[1:] if ln.endswith(":") and not ln.startswith(" ")]
        self.assertEqual(groups, ["Length issues:"])


if __name__ == "__main__":
    unittest.main()
