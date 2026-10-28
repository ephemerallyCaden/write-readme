"""Fixtures for scripts/detect-project-type.sh.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

from _load import script_path

SCRIPT = script_path("detect-project-type.sh")


@unittest.skipUnless(shutil.which("bash"), "bash not available")
class DetectProjectTypeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def make(self, name: str, files: dict[str, str]) -> str:
        root = os.path.join(self.tmp, name)
        for rel, body in files.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
        os.makedirs(root, exist_ok=True)
        return root

    def detect(self, root: str) -> str:
        result = subprocess.run(["bash", SCRIPT, "--dir", root], capture_output=True, text=True,
                                check=True, timeout=60)
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

    def test_home_assistant_config(self):
        root = self.make("ha", {"configuration.yaml": "homeassistant:\n  name: Home\n"})
        self.assertEqual(self.detect(root), "dotfiles")


if __name__ == "__main__":
    unittest.main()
