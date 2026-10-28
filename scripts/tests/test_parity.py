"""Docs-vs-scripts parity: SKILL.md tables, data/type-slugs.json,
detect-project-type.sh, and the "(scripted)" claims vs check-anti-ai.py.

Run: python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import os
import re
import unittest

from _load import REPO, load_script, script_path

ca = load_script("check-anti-ai.py")
vr = load_script("validate-readme.py")

SKILL_MD = os.path.join(REPO, "SKILL.md")
DETECT = script_path("detect-project-type.sh")
# Files whose checklist bullets may carry "(scripted)"
SCRIPTED_DOCS = [SKILL_MD, os.path.join(REPO, "references", "anti-ai-rules.md")]


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def markdown_table(text: str, heading: str) -> list[list[str]]:
    """Body rows of the first table under `heading` (header and separator dropped)."""
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == heading)
    rows: list[list[str]] = []
    for ln in lines[start + 1:]:
        if ln.startswith("#"):
            break
        if ln.strip().startswith("|"):
            rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
        elif rows:
            break
    return rows[2:]


def parse_range(value: str) -> list[int | None]:
    m = re.fullmatch(r"(\d+)\s*(?:-\s*(\d+)|\+)", value)
    if not m:
        raise ValueError(f"unparseable range {value!r}")
    return [int(m.group(1)), int(m.group(2)) if m.group(2) else None]


class LengthTargetParityTests(unittest.TestCase):
    """SKILL.md "## Length Targets" == data/type-slugs.json (validate-readme.py's
    LENGTH_TARGETS are checked against the JSON in test_validate_readme.py)."""

    def test_skill_table_matches_type_slugs(self):
        """One row per type-slugs.json entry, labelled with its exact "name"."""
        slugs = vr.load_type_slugs()
        names = {entry["name"]: slug for slug, entry in slugs.items()}
        covered: dict[str, str] = {}
        problems: list[str] = []
        for label, value in (row[:2] for row in markdown_table(read(SKILL_MD), "## Length Targets")):
            slug = names.get(label)
            if slug is None:
                problems.append(f"row {label!r} is not a type-slugs.json name")
                continue
            if slug in covered:
                problems.append(f"{label!r} has more than one row")
            covered[slug] = label
            if parse_range(value) != slugs[slug]["target_lines"]:
                problems.append(f"{label!r} says {value}; type-slugs.json {slug} has "
                                f"{slugs[slug]['target_lines']}")
        problems += [f"{slugs[s]['name']!r} ({s}) has no row" for s in sorted(set(slugs) - set(covered))]
        self.assertEqual(problems, [])


class SlugSetParityTests(unittest.TestCase):
    def test_detect_outputs_match_type_slugs(self):
        outputs = set(re.findall(r'echo "([a-z-]+)"', read(DETECT)))
        self.assertEqual(outputs, set(vr.load_type_slugs()))

    def test_detect_usage_lists_every_slug(self):
        usage = read(DETECT).split("to stdout:", 1)[1].split("USAGE", 1)[0]
        listed = set(re.findall(r"[a-z][a-z-]*", usage))
        self.assertEqual(listed, set(vr.load_type_slugs()))

    def test_skill_slug_table_matches_type_slugs(self):
        rows = markdown_table(read(SKILL_MD), "### Canonical type slugs")
        self.assertEqual({slug: name for name, slug in rows},
                         {slug: e["name"] for slug, e in vr.load_type_slugs().items()})


# Each "(scripted)" bullet in SCRIPTED_DOCS must match at least one key
# phrase (case-insensitive regex). Each key maps to checker rules and a
# sample that must trigger every one of them.
SCRIPTED_RULES: list[tuple[str, list[tuple[str, str]]]] = [
    (r"banned (?:list|word)|tier 1[ab]", [("banned-word", "We leverage caches.")]),
    (r"chatbot artifact", [("chatbot-artifact", "Feel free to open an issue.")]),
    (r"template phrase", [("template-phrase", "It is a bold step towards better tools.")]),
    (r"let['’]s", [("lets-opener", "- Let’s get started.")]),
    (r"emoji", [("emoji-in-heading", "## ⭐ Features")]),
    (r"bold-label|rule 12", [
        ("bold-label-list", "- **Fast** - parses quickly\n- **Small** - 4 kB\n- **Typed** - ships types"),
        ("em-dash-in-list", "- Fast — parses quickly"),
    ]),
    (r"preamble", [("section-preamble", "This section covers setup.")]),
    (r"transition word", [("transition-fluff", "Moreover, it works.")]),
    (r"em dashes", [("em-dash-overuse", "A — b — c — d.")]),
]
SCRIPTED_BULLET_RE = re.compile(r"^\s*[-*]\s+(?:\[[ x]\]\s+)?(.*\(scripted\b.*)$", re.IGNORECASE)


def scripted_bullets() -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    for path in SCRIPTED_DOCS:
        for lineno, line in enumerate(read(path).splitlines(), start=1):
            m = SCRIPTED_BULLET_RE.match(line)
            if m:
                out.append((os.path.relpath(path, REPO), lineno, m.group(1)))
    return out


class ScriptedClaimTests(unittest.TestCase):
    def test_scripted_bullets_exist(self):
        # anti-ai-rules.md holds the "(scripted)" labels; SKILL.md is scanned
        # too in case any appear there. Guards against a vacuous pass.
        paths = [path for path, _, _ in scripted_bullets()]
        self.assertGreaterEqual(paths.count(os.path.join("references", "anti-ai-rules.md")), 9)

    def test_every_scripted_bullet_maps_to_a_rule(self):
        unmapped = [f"{path}:{lineno}: {text}" for path, lineno, text in scripted_bullets()
                    if not any(re.search(key, text, re.IGNORECASE) for key, _ in SCRIPTED_RULES)]
        self.assertEqual(unmapped, [], "add a SCRIPTED_RULES entry (and a checker rule) for these")

    def test_every_mapped_rule_fires(self):
        for key, rules in SCRIPTED_RULES:
            for rule, sample in rules:
                with self.subTest(key=key, rule=rule):
                    fired = {f["rule"] for f in ca.check_content(f"# T\n\n{sample}\n")}
                    self.assertIn(rule, fired)

    def test_quoted_examples_are_caught(self):
        """Quoted examples in phrase bullets ("Feel free to...", "serves as a") are flagged."""
        fill = {"[adjective]": "bold", "[noun]": "tools"}
        for path, lineno, text in scripted_bullets():
            rules = [rule for key, pairs in SCRIPTED_RULES if re.search(key, text, re.IGNORECASE)
                     for rule, _ in pairs if rule in ("chatbot-artifact", "template-phrase")]
            if not rules:
                continue
            for example in re.findall(r'"([^"]+)"', text):
                for token, word in fill.items():
                    example = example.replace(token, word)
                with self.subTest(at=f"{path}:{lineno}", example=example):
                    fired = {f["rule"] for f in ca.check_content(f"# T\n\n{example.rstrip('.')} x.\n")}
                    self.assertTrue(fired & set(rules), fired)

    def test_every_key_is_used(self):
        texts = [text for _, _, text in scripted_bullets()]
        unused = [key for key, _ in SCRIPTED_RULES
                  if not any(re.search(key, t, re.IGNORECASE) for t in texts)]
        self.assertEqual(unused, [])


if __name__ == "__main__":
    unittest.main()
