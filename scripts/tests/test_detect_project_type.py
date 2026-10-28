"""Fixtures for scripts/detect-project-type.sh.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest

from _load import REPO, script_path

SCRIPT = script_path("detect-project-type.sh")


def write_tree(root: str, files: dict[str, str]) -> str:
    """Create root with each {relative path: body} file in it; return root."""
    os.makedirs(root, exist_ok=True)
    for rel, body in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(body)
    return root


def run_detect(root: str, script: str = SCRIPT, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", script, "--dir", root], capture_output=True, text=True,
                          timeout=120, env=env)


@unittest.skipUnless(shutil.which("bash"), "bash not available")
class DetectProjectTypeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def make(self, name: str, files: dict[str, str]) -> str:
        return write_tree(os.path.join(self.tmp, name), files)

    def detect(self, root: str, script: str = SCRIPT, env: dict | None = None) -> str:
        result = run_detect(root, script, env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_many_pattern_hits_still_match(self):
        # has_pattern used to pipe grep into head under pipefail. Once grep's
        # output outgrew one write, it died of SIGPIPE and the check returned
        # false, so this fixture detected as "other". Long names make 300
        # files enough to reproduce it against the old script.
        files = {f"pkg/{'a' * 120}_{i}.py": "import argparse\n" for i in range(300)}
        self.assertEqual(self.detect(self.make("many", files)), "cli")

    def test_platformio_beats_helper_scripts(self):
        root = self.make("fw", {
            "platformio.ini": "[env:esp32]\nboard = esp32dev\n",
            "src/main.cpp": "void setup() {}\n",
            # Split so this file doesn't match the Visual Output grep itself.
            "tools/plot.py": "import argparse\n" + "import " + "matplotlib\n" + "import " + "pandas\n",
        })
        self.assertEqual(self.detect(root), "hardware")

    def test_arduino_sketch_is_hardware(self):
        self.assertEqual(self.detect(self.make("sk", {"Blink/Blink.ino": "void setup() {}\n"})), "hardware")

    def test_arduino_library_examples_are_not_hardware(self):
        root = self.make("lib", {"library.properties": "name=Foo\n",
                                 "examples/Demo/Demo.ino": "void setup() {}\n"})
        self.assertNotEqual(self.detect(root), "hardware")

    def test_rc_file_layout_is_dotfiles(self):
        root = self.make("conf", {".zshrc": "", ".tmux.conf": "", ".gitconfig": "",
                                  "install.py": "import argparse\n"})
        self.assertEqual(self.detect(root), "dotfiles")

    def test_dotfiles_name_without_manifest(self):
        self.assertEqual(self.detect(self.make("dotfiles", {"zshrc": ""})), "dotfiles")

    def test_dotfiles_name_with_manifest_is_not_dotfiles(self):
        root = self.make("dotfiles-cli", {"package.json": '{"name": "dotfiles-cli", "bin": {"d": "x.js"}}'})
        self.assertEqual(self.detect(root), "cli")

    # Dependency and environment directories are not project code (review #15).
    # Fixture strings are split so this file doesn't match the greps itself.
    LIB = {"package.json": '{"name": "lib", "main": "index.js"}', "index.js": "module.exports = 1;\n"}

    def test_node_modules_bot_dependency_ignored(self):
        root = self.make("lib-discord", {**self.LIB,
                                         "node_modules/dep/index.js": "const d = require('discord" + ".js');\n"})
        self.assertEqual(self.detect(root), "library")

    def test_node_modules_hex_string_ignored(self):
        root = self.make("lib-hex", {**self.LIB,
                                     "node_modules/dep/hash.js": 'import h from "./h"; const k = "a9d' + '3f0";\n'})
        self.assertEqual(self.detect(root), "library")

    def test_venv_argparse_ignored(self):
        root = self.make("pylib", {"pyproject.toml": '[project]\nname = "pylib"\n',
                                   "pylib/__init__.py": "VALUE = 1\n",
                                   ".venv/lib/python3.12/site-packages/tool/cli.py": "import argparse\n"})
        self.assertEqual(self.detect(root), "library")

    def test_other_excluded_dirs_ignored(self):
        for d in ["venv", "vendor", "dist", "build", "target", "__pycache__", ".git"]:
            with self.subTest(dir=d):
                root = self.make(f"ex-{d.strip('._')}", {**self.LIB, f"{d}/x/cli.py": "import argparse\n",
                                                         f"{d}/x/main.tf": 'resource "x" "y" {}\n'})
                self.assertEqual(self.detect(root), "library")

    def test_chart_yaml_alone_is_devops(self):
        # `A || B && C` used to parse as `(A || B) && C`, so Chart.yaml needed values.yaml.
        self.assertEqual(self.detect(self.make("chart", {"Chart.yaml": "name: c\n"})), "devops")

    def test_templates_need_values_yaml(self):
        self.assertEqual(self.detect(self.make("tv", {"templates/a.txt": "", "values.yaml": "a: 1\n"})),
                         "devops")
        self.assertEqual(self.detect(self.make("t", {"templates/a.txt": ""})), "other")

    def test_this_repo_is_cli(self):
        # Guards against test fixtures in this repo matching the detector's greps.
        self.assertEqual(self.detect(REPO), "cli")

    def test_tree_is_grepped_once(self):
        # Every has_pattern check used to grep the whole tree again (about 30
        # passes when nothing matched); now one recursive grep feeds them all.
        shim_dir = os.path.join(self.tmp, "shim")
        log = os.path.join(self.tmp, "grep.log")
        os.makedirs(shim_dir)
        shim = os.path.join(shim_dir, "grep")
        with open(shim, "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\nprintf "%s\\n" "$@" ---- >> "{log}"\nexec "{shutil.which("grep")}" "$@"\n')
        os.chmod(shim, 0o755)
        root = self.make("plain", {f"src/m{i}.py": "value = 1\n" for i in range(20)})
        env = {**os.environ, "PATH": shim_dir + os.pathsep + os.environ["PATH"]}
        self.assertEqual(self.detect(root, env=env), "other")
        with open(log, encoding="utf-8") as f:
            calls = f.read().split("----\n")
        recursive = [c for c in calls
                     if re.search(r"^(-[a-zA-Z]*[rR][a-zA-Z]*|--(dereference-)?recursive)$", c, re.M)]
        self.assertEqual(len(recursive), 1, f"{len(recursive)} recursive greps")

    def test_unlisted_regex_fails_loudly(self):
        # The one tree scan only covers regexes the script finds in its own
        # source, so a call written another way must stop the script rather
        # than silently never match.
        with open(SCRIPT, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("has_pattern 'console_scripts'", text)
        script = os.path.join(self.tmp, "detect.sh")
        with open(script, "w", encoding="utf-8") as f:
            f.write(text.replace("has_pattern 'console_scripts'", 'has_pattern "console_scripts"'))
        result = run_detect(self.make("plain", {"a.py": "value = 1\n"}), script)
        self.assertEqual(result.returncode, 1)
        self.assertIn("console_scripts", result.stderr)

    def test_home_assistant_config(self):
        root = self.make("ha", {"configuration.yaml": "homeassistant:\n  name: Home\n"})
        self.assertEqual(self.detect(root), "dotfiles")


if __name__ == "__main__":
    unittest.main()
