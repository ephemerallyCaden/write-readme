"""Differential test: detect-project-type.sh against the per-check-grep version it replaced.

The single-scan rewrite must print the same type as the original script for
every tree. This builds fixture trees from fixtures/detect_project_type.json
and runs both scripts on each one. By default only the named cases run (a few
seconds). Set DETECT_DIFFERENTIAL=full to also run each snippet alone and the
seeded random mixes (about 275 trees, around 30 s):

    DETECT_DIFFERENTIAL=full python3 -m unittest test_detect_project_type_differential

REFERENCE is the last commit with the original script. The Unity and Unreal
signals added after it change output on purpose, so these fixtures contain
no engine files (test_detect_project_type.py covers those). Any other
intended detection change that these fixtures reach will fail this test:
move REFERENCE to that commit, or delete this test once the rewrite has
settled.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from _load import REPO
from test_detect_project_type import SCRIPT, run_detect, write_tree

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "detect_project_type.json")
REFERENCE = "20b43a2"
RANDOM_MIXES = 120
SEED = 1729
ROOT_NAMES = ["proj", "proj", "proj", "dotfiles", "awesome-list", "my-dotfiles-cli"]


def reference_script(dest_dir: str) -> str | None:
    """Write the original script to dest_dir; None if git or the commit is unavailable."""
    if not shutil.which("git"):
        return None
    result = subprocess.run(["git", "-C", REPO, "show", f"{REFERENCE}:scripts/detect-project-type.sh"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        return None
    path = os.path.join(dest_dir, "detect-project-type.reference.sh")
    with open(path, "w", encoding="utf-8") as f:
        f.write(result.stdout)
    return path


def body(spec) -> str:
    if isinstance(spec, dict):
        return spec["repeat"] * spec["times"]
    return spec


def build_cases(data: dict, full: bool) -> list[tuple[str, str, dict]]:
    """(case name, root dir name, {relative path: file body}) for every fixture tree."""
    snippets = data["snippets"]

    def merge(names):
        files = {}
        for n in names:
            files.update({rel: body(spec) for rel, spec in snippets[n].items()})
        return files

    cases = [(f"case:{n}", c.get("root", "proj"), merge(c["use"])) for n, c in data["cases"].items()]
    if not full:
        return cases
    cases += [(f"snippet:{n}", "proj", merge([n])) for n in snippets]
    rng = random.Random(SEED)
    names = sorted(snippets)
    for i in range(RANDOM_MIXES):
        picked = rng.sample(names, rng.randint(2, 4))
        cases.append((f"mix{i}:{'+'.join(picked)}", rng.choice(ROOT_NAMES), merge(picked)))
    return cases


def run(script: str, root: str) -> tuple[int, str]:
    result = run_detect(root, script)
    return result.returncode, result.stdout.strip()


@unittest.skipUnless(shutil.which("bash"), "bash not available")
class DetectProjectTypeDifferentialTests(unittest.TestCase):
    def test_matches_reference_script(self):
        full = os.environ.get("DETECT_DIFFERENTIAL") == "full"
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        reference = reference_script(tmp)
        if reference is None:
            self.skipTest(f"reference commit {REFERENCE} not available (no git history?)")
        with open(FIXTURES, encoding="utf-8") as f:
            cases = build_cases(json.load(f), full)

        def compare(item):
            i, (name, root_name, files) = item
            root = os.path.join(tmp, str(i), root_name)
            write_tree(root, files)
            return name, run(reference, root), run(SCRIPT, root)

        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool:
            results = list(pool.map(compare, enumerate(cases)))

        self.maxDiff = None
        mismatches = [f"{name}: reference {old}, new {new}" for name, old, new in results if old != new]
        self.assertEqual(mismatches, [], f"{len(mismatches)} of {len(results)} fixtures differ")
        if not full:
            return
        # The full set should reach every type the script can print.
        emitted = {old[1] for _, old, _ in results}
        self.assertEqual(emitted, {
            "dotfiles", "hardware", "game", "visual", "gen-ai", "bot", "browser-ext", "mobile", "desktop",
            "tui", "docs-site", "web-app", "api", "cli", "framework", "ml", "devops", "educational",
            "library", "other"})


if __name__ == "__main__":
    unittest.main()
