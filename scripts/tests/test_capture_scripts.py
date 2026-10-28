"""Hardening of the capture scripts: capture-terminal.py runs argv lists with no
shell, generate-tape.py quotes what it writes into a tape, and render-mermaid.py
loads a pinned Mermaid build with an SRI hash.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import base64
import contextlib
import glob
import io
import os
import re
import sys
import tempfile
import unittest

from _load import REPO, SCRIPTS, load_script

ct = load_script("capture-terminal.py")
gt = load_script("generate-tape.py")
rm = load_script("render-mermaid.py")


class CaptureTerminalParseTests(unittest.TestCase):
    def test_splits_like_a_shell(self):
        self.assertEqual(ct.parse_command("mytool --help"), ["mytool", "--help"])
        self.assertEqual(
            ct.parse_command("mytool run \"a b\" 'c d' e\\ f"),
            ["mytool", "run", "a b", "c d", "e f"],
        )

    def test_quoted_metacharacters_are_literal(self):
        self.assertEqual(ct.parse_command('grep "a|b;c>d" f.txt'), ["grep", "a|b;c>d", "f.txt"])
        self.assertEqual(ct.parse_command("echo '$(id) `id` $HOME'"), ["echo", "$(id) `id` $HOME"])
        self.assertEqual(ct.parse_command("x \\| y"), ["x", "|", "y"])

    def test_rejects_shell_syntax(self):
        for command in [
            "ls | wc -l",
            "a && b",
            "a || b",
            "a; b",
            "a & b",
            "mytool > out.txt",
            "mytool < in.txt",
            "mytool 2>&1",
            "echo `id`",
            "echo $(id)",
            'echo "$(id)"',
            'echo "`id`"',
            "echo $HOME",
            "echo ${HOME}",
            "ls *.py",
            "(cd x)",
            "a\nb",
        ]:
            with self.subTest(command=command), self.assertRaises(ct.CommandError):
                ct.parse_command(command)

    def test_rejects_empty_and_unbalanced(self):
        for command in ["", "   ", "echo 'unclosed"]:
            with self.subTest(command=command), self.assertRaises(ct.CommandError):
                ct.parse_command(command)

    def test_cli_rejects_metacharacters_before_running(self):
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(io.StringIO()):
            ct.main(["--command", "rm -rf x; echo hi", "-o", os.devnull])
        self.assertEqual(cm.exception.code, 2)

    def test_cli_needs_exactly_one_command_form(self):
        for argv in [["-o", os.devnull], ["-c", "a", "-o", os.devnull, "--", "b"]]:
            with self.subTest(argv=argv), self.assertRaises(SystemExit), \
                    contextlib.redirect_stderr(io.StringIO()):
                ct.main(argv)


class CaptureTerminalRunTests(unittest.TestCase):
    def test_runs_in_dir_without_stdin(self):
        with tempfile.TemporaryDirectory() as d:
            code = "import os, sys; print(os.getcwd()); print(repr(sys.stdin.read()))"
            out = ct.run_command([sys.executable, "-c", code], cwd=d)
        cwd, stdin = out.splitlines()
        self.assertEqual(os.path.realpath(cwd), os.path.realpath(d))
        self.assertEqual(stdin, "''")

    def test_no_shell_interprets_arguments(self):
        out = ct.run_command([sys.executable, "-c", "import sys; print(sys.argv[1])", "$(id); `id`"], cwd=".")
        self.assertEqual(out.strip(), "$(id); `id`")

    def test_timeout(self):
        with self.assertRaisesRegex(ct.CommandError, "timed out after 0.5s"):
            ct.run_command([sys.executable, "-c", "import time; time.sleep(10)"], cwd=".", timeout=0.5)

    def test_missing_program(self):
        with self.assertRaisesRegex(ct.CommandError, "could not run"):
            ct.run_command(["write-readme-no-such-program"], cwd=".")


class GenerateTapeQuotingTests(unittest.TestCase):
    def test_picks_a_delimiter_the_value_lacks(self):
        self.assertEqual(gt.vhs_string("mytool --help"), '"mytool --help"')
        self.assertEqual(gt.vhs_string('mytool "x"'), "'mytool \"x\"'")
        self.assertEqual(gt.vhs_string("echo \"a\" 'b'"), "`echo \"a\" 'b'`")

    def test_rejects_unquotable_values(self):
        for value in ["a\nHide", "a\rb", "\"'`"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                gt.vhs_string(value)

    def test_command_cannot_add_tape_directives(self):
        tape = gt.generate_tape_content('x" Enter Type "rm -rf ~', "out.gif", "Dracula", 900, 500)
        type_lines = [ln for ln in tape.splitlines() if ln.startswith("Type ")]
        self.assertEqual(type_lines, ["Type 'x\" Enter Type \"rm -rf ~'"])
        with self.assertRaises(ValueError):
            gt.generate_tape_content("ok\nOutput /etc/x.gif", "out.gif", "Dracula", 900, 500)


class MermaidPinTests(unittest.TestCase):
    def test_script_is_pinned_with_sri(self):
        src, integrity = rm.MERMAID_SCRIPT["src"], rm.MERMAID_SCRIPT["integrity"]
        self.assertRegex(src, r"^https://cdn\.jsdelivr\.net/npm/mermaid@\d+\.\d+\.\d+/dist/mermaid\.min\.js$")
        self.assertNotIn("latest", src)
        algo, _, digest = integrity.partition("-")
        self.assertEqual(algo, "sha384")
        self.assertEqual(len(base64.b64decode(digest, validate=True)), 48)

    def test_page_loads_it_with_integrity(self):
        page = rm.build_mermaid_html("flowchart LR\n  a --> b", dark=True)
        tag = re.search(r"<script src=[^>]*>", page).group(0)
        self.assertIn(f'src="{rm.MERMAID_SCRIPT["src"]}"', tag)
        self.assertIn(f'integrity="{rm.MERMAID_SCRIPT["integrity"]}"', tag)
        self.assertIn('crossorigin="anonymous"', tag)


class NoShellNoUnpinnedCdnTests(unittest.TestCase):
    """Repo-wide guards for the two audit findings."""

    def files(self) -> list[str]:
        found = glob.glob(os.path.join(SCRIPTS, "*.py")) + glob.glob(os.path.join(SCRIPTS, "*.sh"))
        found += glob.glob(os.path.join(REPO, "skills", "**", "*.md"), recursive=True)
        return found

    def test_no_shell_true(self):
        for path in self.files():
            with self.subTest(path=os.path.relpath(path, REPO)), open(path, encoding="utf-8") as f:
                self.assertNotIn("shell=True", f.read())

    def test_no_unpinned_jsdelivr(self):
        unpinned = re.compile(r"cdn\.jsdelivr\.net/npm/(@[\w.-]+/)?[\w.-]+(?!@)(?=[/`'\")\s]|$)")
        for path in self.files():
            with self.subTest(path=os.path.relpath(path, REPO)), open(path, encoding="utf-8") as f:
                self.assertIsNone(unpinned.search(f.read()))

    def test_remote_scripts_carry_integrity(self):
        for path in glob.glob(os.path.join(SCRIPTS, "*.py")):
            with self.subTest(path=os.path.relpath(path, REPO)), open(path, encoding="utf-8") as f:
                for tag in re.findall(r"<script\b[^>]*\bsrc=[^>]*>", f.read()):
                    self.assertIn("integrity=", tag)
                    self.assertIn('crossorigin="anonymous"', tag)


if __name__ == "__main__":
    unittest.main()
