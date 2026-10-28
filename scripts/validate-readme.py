#!/usr/bin/env python3
"""Validate a generated README for correctness.

Checks:
- Relative links point to files that exist
- Badge URLs are syntactically valid
- No remaining placeholder text (TODO, TBD, PLACEHOLDER, lorem ipsum, ...)
- Line count within the type's range (above the maximum is an issue; below the
  minimum is only a note, since padding is worse than a short README)
- Title present (H1, or a banner image / <h1> at the top) and at most one H1
- First runnable step (shell block, store badge, download link, deploy button,
  hosted demo link) near the top; TOC lines before it are not counted
- In-page anchors (#slug) match a heading or explicit anchor
- No duplicate H2 headings
- At most 6 badges before the first H2
- No dead badge hosts or static shields that imitate live status
- No positional image references ("screenshot above")
- License text agrees with the LICENSE file in --dir
- No style= attributes on HTML tags (GitHub strips them)

Prints findings to stdout, then any notes. Exit 0 if all pass, 1 if issues
found; notes never change the exit code.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from urllib.parse import parse_qs, unquote, urlparse

from _mdlib import (
    BULLET_RE,
    MAX_HEADER_BADGES,
    MD_IMAGE_RE,
    MD_LINK_RE,
    Heading,
    Line,
    collect_headings,
    github_slug,
    iter_code_blocks,
    parse_lines,
    plain_heading_text,
    unique_slugs,
)


TYPE_SLUGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "type-slugs.json"
)


def load_type_slugs(path: str = TYPE_SLUGS_PATH) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


TYPE_SLUGS = load_type_slugs()
# Standard-mode line ranges by type slug, from data/type-slugs.json (which
# SKILL.md "Length Targets" mirrors). max None = no upper bound.
LENGTH_TARGETS: dict[str, tuple[int, int | None]] = {
    slug: tuple(entry["target_lines"]) for slug, entry in TYPE_SLUGS.items()
}
# Minimal is an absolute range whatever the type (SKILL.md Phase 3f).
MINIMAL_LENGTH = (30, 80)
# Early-stage projects override verbosity and type (SKILL.md Phase 3f).
EARLY_STAGE_LENGTH = (30, 60)
# Detailed stretches the upper bound; types with "detailed_max" get a fixed one.
DETAILED_MAX_STRETCH = 1.3
DETAILED_MAX_OVERRIDES = {
    slug: entry["detailed_max"] for slug, entry in TYPE_SLUGS.items() if "detailed_max" in entry
}
APPENDIX_HEADING_RE = re.compile(r"^appendix\b", re.IGNORECASE)

# Placeholder tokens. Uppercase-only tokens are matched case-sensitively so
# that ordinary prose ("leaves a placeholder", "a todo app") is not flagged.
PLACEHOLDER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bXXX\b"),
    # INSERT followed by a colon or an all-caps token ("INSERT LOGO"), but not
    # SQL ("INSERT INTO", "INSERT and UPDATE", "INSERT, UPDATE").
    re.compile(r"\bINSERT(?::|\s+(?!(?:INTO|AND|OR|OVERWRITE|IGNORE|ALL|FIRST|DELAYED|"
               r"LOW_PRIORITY|HIGH_PRIORITY|ON|UPDATE|DELETE|SELECT|UPSERT|MERGE|REPLACE|"
               r"RETURNING|VALUES|STATEMENTS?|QUERY|QUERIES)\b)[A-Z][A-Z_]+\b)"),
    re.compile(r"\bPLACEHOLDER\b"),
    re.compile(r"\bNEED TO ADD\b"),
    re.compile(r"\blink needed\b", re.IGNORECASE),
    re.compile(r"\blorem ipsum\b", re.IGNORECASE),
    re.compile(r"[\[<{]\s*(?:placeholder|insert|todo|tbd)\b[^\]>}]*[\]>}](?!\()", re.IGNORECASE),
    re.compile(r"\bYOUR[_\s].*?HERE\b"),
    re.compile(r"\byour-.*?-here\b", re.IGNORECASE),
    re.compile(r"\[(?:replace|fill in)\b", re.IGNORECASE),
]

# Run-first: how far down the first runnable step may sit
RUN_FIRST_MAX_LINE = {"minimal": 50, "standard": 80, "detailed": 80}
# Run-first exempt types (SKILL.md Phase 3b).
RUN_FIRST_SKIP_TYPES = {"educational", "dotfiles"}

SHELL_LANGS = {
    "bash", "sh", "shell", "zsh", "fish", "console", "terminal",
    "shell-session", "shellsession", "sh-session", "powershell", "pwsh",
    "ps", "ps1", "posh", "bat", "batch", "cmd",
}
COMMON_COMMANDS = {
    "apt", "apt-get", "brew", "bun", "bunx", "cargo", "cd", "choco", "composer",
    "conda", "curl", "deno", "docker", "docker-compose", "dotnet", "flutter",
    "gem", "git", "go", "gradle", "helm", "iwr", "java", "kubectl", "make",
    "mvn", "node", "npm", "npx", "pip", "pip3", "pipx", "pnpm", "poetry",
    "python", "python3", "rustup", "scoop", "snap", "sudo", "uv", "uvx",
    "wget", "winget", "yarn", "dnf", "pacman", "nix", "flatpak",
    # Firmware build and flash tools (hardware)
    "pio", "platformio", "arduino-cli", "idf.py", "west", "esptool", "esptool.py",
    "avrdude", "openocd", "picotool", "cmake",
}
# Store or download hosts that count as the run step wherever they appear
STORE_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:"
    r"apps\.apple\.com|itunes\.apple\.com|play\.google\.com|"
    r"apps\.microsoft\.com|get\.microsoft\.com|microsoft\.com/[^)\s\"']*store|"
    r"microsoftedge\.microsoft\.com/addons|"
    r"chrome\.google\.com/webstore|chromewebstore\.google\.com|"
    r"addons\.mozilla\.org|flathub\.org/apps|snapcraft\.io/"
    r")",
    re.IGNORECASE,
)
# GitHub releases only count in a table/list or when the link says download,
# so a version badge that links to /releases is not mistaken for a run step.
RELEASES_URL_RE = re.compile(r"https?://github\.com/[^/\s)]+/[^/\s)]+/releases", re.IGNORECASE)
DOWNLOAD_WORD_RE = re.compile(r"\b(?:download|get it|install)\b", re.IGNORECASE)
# One-click deploy buttons (Heroku, Vercel, Netlify, Render, Railway)
DEPLOY_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:"
    r"heroku\.com/deploy|dashboard\.heroku\.com/new|vercel\.com/(?:new/clone|import|button)|"
    r"app\.netlify\.com/start/deploy|render\.com/deploy|railway\.(?:app|com)/(?:new|template|deploy)"
    r")",
    re.IGNORECASE,
)
# A link to a hosted instance: its label (or badge alt text) is Demo, Live,
# Try it or Open app, or the line reads "Live demo: https://...".
HOSTED_LABEL_RE = re.compile(
    r"^\s*(?:(?:live|online|hosted)\s+)?demo\W*$|^\s*live(?:\s+(?:site|app|version|instance))?\s*$|"
    r"^\s*try\s+it\b|^\s*open\s+(?:the\s+)?app\b",
    re.IGNORECASE,
)
HOSTED_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*)?(?:(?:live|online|hosted)\s+demo|demo|live|try\s+it(?:\s+\w+)?|"
    r"open\s+(?:the\s+)?app)(?:\*\*)?\s*:(?:\*\*)?\s*<?https?://",
    re.IGNORECASE,
)
# A list or heading whose items are only in-page links, under a TOC label
TOC_LABEL_RE = re.compile(
    r"^\s*(?:\*\*|__)?(?:table\s+of\s+)?contents:?(?:\*\*|__)?\s*$"
    r"|^\s{0,3}#{1,6}\s+(?:table\s+of\s+)?contents\s*#*\s*$",
    re.IGNORECASE,
)
TOC_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[[^\]]*\]\(#[^)\s]*\)\s*$")
# Files that mean a hardware repo has firmware to build and flash
FIRMWARE_GLOBS = ["platformio.ini", "*.ino", "*/*.ino", "sdkconfig", "sdkconfig.defaults",
                  "west.yml", "CMakeLists.txt", "Makefile", "src/*.c", "src/*.cpp",
                  "firmware", "*/platformio.ini"]

BADGE_URL_RE = re.compile(
    r"shields\.io|badgen\.net|badge\.fury\.io|forthebadge\.com|badgesize\.io|"
    r"travis-ci\.(?:org|com)|codecov\.io|coveralls\.io|nodei\.co|david-dm\.org|"
    r"ci\.appveyor\.com/api/projects/status|/badge(?:s)?[/.]|badge\.svg",
    re.IGNORECASE,
)
DEAD_BADGE_HOSTS = [
    "travis-ci.org", "nodei.co", "ci.appveyor.com", "david-dm.org",
    "gemnasium.com", "requires.io", "inch-ci.org", "bettercodehub.com",
]
STATUS_LABELS = {
    "build", "builds", "ci", "coverage", "codecov", "tests", "test", "docs",
    "documentation", "maintained", "maintenance", "status", "pipeline", "checks",
}
STATUS_WORDS_RE = re.compile(r"\b(?:passing|passed|failing|failed|maintained)\b", re.IGNORECASE)

POSITIONAL_NOUNS = (
    r"(?:animation|screenshot|screen ?shot|image|gif|video|diagram|picture|"
    r"figure|screencast|recording|photo|illustration)s?"
)
POSITIONAL_RE = re.compile(
    rf"\b{POSITIONAL_NOUNS}\s+(?:above|below)\b"
    rf"|\b(?:above|below)\s+{POSITIONAL_NOUNS}\b"
    r"|\bpictured\s+(?:above|below)\b",
    re.IGNORECASE,
)

STYLE_ATTR_RE = re.compile(r"<[a-zA-Z][\w-]*\b[^>]*?\sstyle\s*=", re.DOTALL)

LICENSE_FILE_GLOBS = ["LICENSE*", "LICENCE*", "COPYING*", "license*", "licence*"]
# Order matters: the GPL variants share the "GENERAL PUBLIC LICENSE" phrase.
LICENSE_FILE_SIGNATURES: list[tuple[str, re.Pattern[str]]] = [
    ("AGPL", re.compile(r"GNU AFFERO GENERAL PUBLIC LICENSE", re.IGNORECASE)),
    ("LGPL", re.compile(r"GNU LESSER GENERAL PUBLIC LICENSE|GNU LIBRARY GENERAL PUBLIC", re.IGNORECASE)),
    ("GPL", re.compile(r"GNU GENERAL PUBLIC LICENSE", re.IGNORECASE)),
    ("Apache", re.compile(r"Apache License", re.IGNORECASE)),
    ("MPL", re.compile(r"Mozilla Public License", re.IGNORECASE)),
    ("MIT", re.compile(r"\bMIT License\b|Permission is hereby granted, free of charge", re.IGNORECASE)),
    ("ISC", re.compile(r"\bISC License\b|Permission to use, copy, modify, and/or distribute", re.IGNORECASE)),
    ("BSD", re.compile(r"\bBSD\b|Redistribution and use in source and binary forms", re.IGNORECASE)),
    ("Unlicense", re.compile(r"\bUnlicense\b|free and unencumbered software", re.IGNORECASE)),
]
LICENSE_NAME_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AGPL", re.compile(r"\bAGPL|\bAffero\b", re.IGNORECASE)),
    ("LGPL", re.compile(r"\bLGPL|\bLesser General Public", re.IGNORECASE)),
    ("GPL", re.compile(r"\bGPL|(?<!Lesser )(?<!Affero )\bGeneral Public License", re.IGNORECASE)),
    ("Apache", re.compile(r"\bApache\b", re.IGNORECASE)),
    ("MPL", re.compile(r"\bMPL\b|\bMozilla Public", re.IGNORECASE)),
    ("MIT", re.compile(r"\bMIT\b")),
    ("ISC", re.compile(r"\bISC\b")),
    ("BSD", re.compile(r"\bBSD\b")),
    ("Unlicense", re.compile(r"\bUnlicense\b", re.IGNORECASE)),
]
ALL_RIGHTS_RE = re.compile(r"\ball rights reserved\b", re.IGNORECASE)

HTML_IMG_RE = re.compile(r"<img\b[^>]*?\bsrc\s*=\s*[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
HTML_ALT_RE = re.compile(r"\balt\s*=\s*[\"']([^\"']*)[\"']", re.IGNORECASE)
HTML_HREF_RE = re.compile(r"<a\b[^>]*?\bhref\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
EXPLICIT_ANCHOR_RE = re.compile(r"<[a-zA-Z][^>]*?\b(?:name|id)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)


# --- Existing checks -------------------------------------------------------

def iter_link_targets(line: Line) -> list[str]:
    """Every link and image target on the line, Markdown or HTML."""
    targets = [m.group(2) for m in MD_LINK_RE.finditer(line.prose)]
    targets += [m.group(2) for m in MD_IMAGE_RE.finditer(line.prose)]
    targets += [m.group(1) for m in HTML_HREF_RE.finditer(line.prose)]
    targets += [m.group(1) for m in HTML_IMG_RE.finditer(line.prose)]
    return targets


def resolve_repo_path(base_dir: str, path: str) -> str:
    """A README path resolved against the project root. A leading "/" is
    repo-root relative on GitHub, not filesystem absolute."""
    return os.path.normpath(os.path.join(base_dir, path.lstrip("/")))


def is_expected(path: str, expected: list[str]) -> bool:
    """True when path is an --expect path or lies under an --expect directory."""
    return any(path == e or path.startswith(e.rstrip(os.sep) + os.sep) for e in expected)


def check_relative_links(lines: list[Line], base_dir: str, expect: list[str] | None = None) -> list[str]:
    """Check that relative link and image targets point to existing files.

    Paths in `expect` (relative to base_dir) count as existing: files the
    caller will write later, such as captures copied in at publish time.
    """
    expected = [resolve_repo_path(base_dir, p) for p in expect or []]
    findings: list[str] = []
    for line in lines:
        for target in iter_link_targets(line):
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue  # URLs, mailto:, and in-page anchors
            path = resolve_repo_path(base_dir, unquote(parsed.path))
            if not os.path.exists(path) and not is_expected(path, expected):
                findings.append(f"  L{line.lineno}: broken link {target} — file not found")
    return findings


def check_badge_urls(lines: list[Line]) -> list[str]:
    """Check that badge image URLs are syntactically valid."""
    findings: list[str] = []
    for line in lines:
        for m in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', line.prose):
            url = m.group(2)
            if "img.shields.io" not in url and "badge" not in url.lower():
                continue
            if " " in url:
                findings.append(f"  L{line.lineno}: badge URL contains spaces: {url[:80]}")
            if url.count("(") != url.count(")"):
                findings.append(f"  L{line.lineno}: badge URL has unbalanced parentheses: {url[:80]}")
            if not url.startswith("http"):
                findings.append(f"  L{line.lineno}: badge URL is not absolute: {url[:80]}")
            if "{" in url or "}" in url:
                findings.append(f"  L{line.lineno}: badge URL has unfilled template variable: {url[:80]}")
    return findings


def check_placeholders(lines: list[Line]) -> list[str]:
    """Placeholder text outside code and HTML comments."""
    findings: list[str] = []
    for line in lines:
        for pattern in PLACEHOLDER_PATTERNS:
            m = pattern.search(line.prose)
            if m:
                findings.append(
                    f"  L{line.lineno}: placeholder text found: {m.group()!r} in: {line.raw.strip()[:80]}"
                )
                break  # One finding per line is enough
    return findings


def length_target(
    project_type: str | None, verbosity: str | None, early_stage: bool = False
) -> tuple[int, int | None]:
    if early_stage:
        return EARLY_STAGE_LENGTH
    if verbosity == "minimal":
        return MINIMAL_LENGTH
    low, high = LENGTH_TARGETS[project_type]
    if verbosity == "detailed" and high is not None:
        high = DETAILED_MAX_OVERRIDES.get(project_type, int(high * DETAILED_MAX_STRETCH))
    return low, high


def appendix_line_count(lines: list[Line], headings: list[Heading]) -> int:
    """Lines inside `## Appendix: ...` sections that follow the License section."""
    license_seen = False
    count = 0
    h2s = [h for h in headings if h.level <= 2]
    for i, h in enumerate(h2s):
        if re.search(r"\blicen[cs]", h.text, re.IGNORECASE):
            license_seen = True
        elif license_seen and h.level == 2 and APPENDIX_HEADING_RE.match(h.text.strip()):
            end = h2s[i + 1].lineno if i + 1 < len(h2s) else len(lines) + 1
            count += end - h.lineno
    return count


def check_length(
    lines: list[Line], headings: list[Heading], project_type: str | None, verbosity: str | None,
    early_stage: bool = False,
) -> tuple[list[str], list[str]]:
    """(issues, notes) for the line count against the type's range.

    Above the maximum is an issue. Below the minimum is a note: SKILL.md
    forbids padding, so a short README is not a failure.
    """
    if not early_stage and project_type not in LENGTH_TARGETS:
        return [], []
    line_count = len(lines)
    note = ""
    if verbosity == "detailed" and not early_stage:
        appendix = appendix_line_count(lines, headings)
        if appendix:
            line_count -= appendix
            note = f" (excluding {appendix} appendix lines)"
    low, high = length_target(project_type, verbosity, early_stage)
    mode = "early-stage" if early_stage else f"{project_type}/{verbosity or 'standard'}"
    if high is not None and line_count > high:
        return [f"  Length: {line_count} lines{note} exceeds the target maximum of {high} for {mode}"], []
    if line_count < low:
        return [], [f"  Length: {line_count} lines{note} is below the target minimum of {low} "
                    f"for {mode} (not a failure; do not pad)"]
    return [], []


def has_banner_title(lines: list[Line]) -> bool:
    """True when the first content block is a banner image with alt text or an <h1>."""
    block: list[str] = []
    for line in lines:
        if line.in_code:
            break
        if not line.text.strip():
            if block:
                break
            continue
        block.append(line.text)
    joined = "\n".join(block)
    if re.search(r"<h1\b", joined, re.IGNORECASE):
        return True
    for img in HTML_IMG_RE.finditer(joined):
        alt = HTML_ALT_RE.search(img.group(0))
        if alt and alt.group(1).strip():
            return True
    return any(m.group(1).strip() for m in MD_IMAGE_RE.finditer(joined))


def check_structure(lines: list[Line], headings: list[Heading]) -> list[str]:
    """Exactly one H1, or a banner image / <h1> standing in as the title."""
    findings: list[str] = []
    h1s = [h for h in headings if h.level == 1]
    for h in h1s[1:]:
        findings.append(f"  L{h.lineno}: multiple H1 headings found (should have exactly one)")
    if not h1s and not has_banner_title(lines):
        findings.append("  Structure: no H1 heading or titled banner image found")
    return findings


# --- Run-first -------------------------------------------------------------

def is_shell_block(lang: str, body: list[str]) -> bool:
    if lang in SHELL_LANGS:
        return True
    if lang:
        return False
    first = next((b.strip() for b in body if b.strip() and not b.strip().startswith("#")), "")
    if first.startswith(("$ ", "> ", "PS> ", "PS ")):
        return True
    token = first.split(" ", 1)[0] if first else ""
    return token in COMMON_COMMANDS or token.startswith("./")


def find_first_runnable(lines: list[Line]) -> tuple[int, str] | None:
    """(line number, description) of the first runnable step, or None."""
    block = next(
        ((start, f"```{lang} block" if lang else "shell block")
         for start, lang, body in iter_code_blocks(lines) if is_shell_block(lang, body)),
        None,
    )
    link = next(
        (step for line in lines if not line.in_code and (step := link_step(line))),
        None,
    )
    return min((c for c in (block, link) if c), default=None)


def link_label(label: str) -> str:
    """Link text with nested badge images replaced by their alt text."""
    return MD_IMAGE_RE.sub(lambda m: m.group(1), label)


def link_step(line: Line) -> tuple[int, str] | None:
    """A store link, deploy button or hosted demo link anywhere, or a GitHub
    releases link in a table/list or saying download."""
    text = line.prose
    if STORE_URL_RE.search(text):
        return line.lineno, "store link"
    if DEPLOY_URL_RE.search(text):
        return line.lineno, "deploy button"
    if HOSTED_LINE_RE.match(text) or any(
        urlparse(m.group(2)).scheme in ("http", "https") and HOSTED_LABEL_RE.search(link_label(m.group(1)))
        for m in MD_LINK_RE.finditer(text)
    ):
        return line.lineno, "hosted demo link"
    if RELEASES_URL_RE.search(text) and (
        text.strip().startswith("|") or BULLET_RE.match(text) or DOWNLOAD_WORD_RE.search(text)
    ):
        return line.lineno, "download link"
    return None


def toc_line_count(lines: list[Line], before: int) -> int:
    """Lines taken by TOC blocks (label plus in-page link list) before line `before`.

    SKILL.md lets a TOC sit above the run section, so its lines do not count
    toward the run-first limit.
    """
    count = 0
    i = 0
    while i < len(lines) and lines[i].lineno < before:
        if lines[i].in_code or not TOC_LABEL_RE.match(lines[i].text):
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not lines[j].text.strip() and not lines[j].in_code:
            j += 1
        items = j
        while items < len(lines) and not lines[items].in_code and TOC_ITEM_RE.match(lines[items].text):
            items += 1
        if items > j:
            count += items - i
            i = items
        else:
            i += 1
    return count


def has_firmware(base_dir: str) -> bool:
    return any(glob.glob(os.path.join(base_dir, pattern)) for pattern in FIRMWARE_GLOBS)


def check_run_first(
    first: tuple[int, str] | None, project_type: str | None, verbosity: str | None,
    lines: list[Line] | None = None, base_dir: str = ".",
) -> tuple[list[str], list[str]]:
    """(issues, notes) for the position of the first runnable step."""
    if project_type in RUN_FIRST_SKIP_TYPES:
        return [], []
    limit = RUN_FIRST_MAX_LINE[verbosity or "standard"]
    if first is None:
        if project_type == "hardware" and not has_firmware(base_dir):
            return [], ["  Run-first: no runnable step found; fine for a board-only hardware repo "
                        "(no firmware found in --dir)"]
        return ["  Run-first: no runnable step found (shell block, store badge, download link, "
                "deploy button, or hosted demo link)"], []
    lineno, kind = first
    toc = toc_line_count(lines or [], lineno)
    if lineno - toc > limit:
        excluding = f" (L{lineno - toc} excluding {toc} TOC lines)" if toc else ""
        return [f"  L{lineno}: first runnable step ({kind}) is past line {limit}{excluding} "
                f"for {verbosity or 'standard'} verbosity"], []
    return [], []


# --- Anchors and headings --------------------------------------------------

def collect_anchors(lines: list[Line], headings: list[Heading]) -> set[str]:
    anchors = {"top", *unique_slugs([h.text for h in headings if not h.html])}
    # <hN> tags get no GitHub anchor; accept their slug anyway to avoid false alarms.
    anchors.update(github_slug(h.text) for h in headings if h.html)
    for line in lines:
        for m in EXPLICIT_ANCHOR_RE.finditer(line.text):
            anchors.add(m.group(1))
    return {a.lower() for a in anchors}


def check_anchors(lines: list[Line], headings: list[Heading]) -> list[str]:
    anchors = collect_anchors(lines, headings)
    findings: list[str] = []
    for line in lines:
        for ref in iter_link_targets(line):
            if not ref.startswith("#") or len(ref) == 1:
                continue
            slug = unquote(ref[1:]).lower()
            if slug not in anchors:
                findings.append(f"  L{line.lineno}: link to {ref} matches no heading or anchor")
    return findings


def normalise_heading(text: str) -> str:
    words = re.sub(r"[^\w\s]", " ", plain_heading_text(text).lower()).split()
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words)


def check_duplicate_h2(headings: list[Heading]) -> list[str]:
    findings: list[str] = []
    seen: dict[str, Heading] = {}
    for h in headings:
        if h.level != 2:
            continue
        key = " ".join(sorted(normalise_heading(h.text).split()))
        if not key:
            continue
        if key in seen:
            first = seen[key]
            findings.append(
                f"  L{h.lineno}: H2 {h.text.strip()!r} duplicates L{first.lineno} {first.text.strip()!r}"
            )
        else:
            seen[key] = h
    return findings


# --- Badges ----------------------------------------------------------------

def iter_images(line: Line) -> list[tuple[str, str]]:
    """(alt, url) for every markdown or HTML image on the line."""
    images = [(m.group(1), m.group(2)) for m in MD_IMAGE_RE.finditer(line.prose)]
    for m in HTML_IMG_RE.finditer(line.prose):
        alt = HTML_ALT_RE.search(m.group(0))
        images.append((alt.group(1) if alt else "", m.group(1)))
    return images


def check_header_badges(lines: list[Line], headings: list[Heading]) -> list[str]:
    first_h2 = next((h.lineno for h in headings if h.level == 2), None)
    badges: list[int] = []
    for line in lines:
        if first_h2 is not None and line.lineno >= first_h2:
            break
        badges.extend(line.lineno for _, url in iter_images(line) if BADGE_URL_RE.search(url))
    if len(badges) > MAX_HEADER_BADGES:
        return [f"  L{badges[0]}-L{badges[-1]}: {len(badges)} badges before the first H2 "
                f"(max {MAX_HEADER_BADGES})"]
    return []


def static_shield_text(url: str) -> tuple[str, str] | None:
    """(label, message) of a static shields.io badge, or None for dynamic badges."""
    parsed = urlparse(url)
    if not parsed.netloc.endswith("shields.io"):
        return None
    if parsed.path.startswith("/badge/"):
        content = re.sub(r"\.(?:svg|png|json)$", "", unquote(parsed.path[len("/badge/"):]))
        # A single dash separates fields; "--" is a literal dash. "_" is a space.
        parts = [p.replace("--", "-").replace("_", " ")
                 for p in re.split(r"(?<!-)-(?!-)", content)]
        if len(parts) >= 3:
            return parts[0], parts[1]
        return "", parts[0]
    if parsed.path.startswith("/static/"):
        query = parse_qs(parsed.query)
        return query.get("label", [""])[0], query.get("message", [""])[0]
    return None


def check_badge_hosts(lines: list[Line]) -> list[str]:
    findings: list[str] = []
    for line in lines:
        for _, url in iter_images(line):
            host = urlparse(url).netloc.lower()
            dead = next((d for d in DEAD_BADGE_HOSTS if host == d or host.endswith("." + d)), None)
            if dead:
                findings.append(f"  L{line.lineno}: badge from dead host {dead}: {url[:80]}")
                continue
            fields = static_shield_text(url)
            if fields is None:
                continue
            label, message = fields
            if label.strip().lower() in STATUS_LABELS or STATUS_WORDS_RE.search(f"{label} {message}"):
                findings.append(
                    f"  L{line.lineno}: static shield imitates live status "
                    f"({label + ': ' if label else ''}{message}): {url[:80]}"
                )
    return findings


# --- Prose checks ----------------------------------------------------------

def check_positional_refs(lines: list[Line]) -> list[str]:
    findings: list[str] = []
    for line in lines:
        # Ignore alt text and other attribute values; only rendered prose counts.
        prose = re.sub(r"<[^>]*>", " ", line.prose)
        prose = MD_IMAGE_RE.sub(" ", prose)
        m = POSITIONAL_RE.search(prose)
        if m:
            findings.append(f"  L{line.lineno}: positional image reference {m.group()!r}")
    return findings


def check_style_attrs(lines: list[Line]) -> list[str]:
    text = "\n".join(line.prose for line in lines)
    findings: list[str] = []
    lineno, last = 1, 0
    for m in STYLE_ATTR_RE.finditer(text):
        lineno += text.count("\n", last, m.start())
        last = m.start()
        tag = m.group(0).split()[0].lstrip("<")
        findings.append(f"  L{lineno}: style= attribute on <{tag}> is stripped by GitHub")
    return findings


# --- License ---------------------------------------------------------------

def read_license_files(base_dir: str) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for pattern in LICENSE_FILE_GLOBS:
        for path in sorted(glob.glob(os.path.join(base_dir, pattern))):
            real = os.path.realpath(path)
            if real in seen or not os.path.isfile(path):
                continue
            seen.add(real)
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    out.append((os.path.basename(path), f.read(4000)))
            except OSError:
                continue
    return out


def identify_license(text: str) -> str | None:
    head = text[:2000]
    for name, pattern in LICENSE_FILE_SIGNATURES:
        if pattern.search(head):
            return name
    return None


def license_section(lines: list[Line], headings: list[Heading]) -> list[Line]:
    for i, h in enumerate(headings):
        if not re.search(r"\blicen[cs]", h.text, re.IGNORECASE):
            continue
        end = next((n.lineno for n in headings[i + 1:] if n.level <= h.level), None)
        return [ln for ln in lines if ln.lineno > h.lineno and (end is None or ln.lineno < end)]
    return []


def check_license(lines: list[Line], headings: list[Heading], base_dir: str) -> list[str]:
    files = read_license_files(base_dir)
    families: dict[str, str] = {}
    for name, text in files:
        family = identify_license(text)
        if family:
            families[family] = name
    if not families:
        return []
    findings: list[str] = []
    file_label = ", ".join(f"{name} ({fam})" for fam, name in families.items())
    file_says_reserved = any(ALL_RIGHTS_RE.search(text) for _, text in files)

    for line in lines:
        if ALL_RIGHTS_RE.search(line.prose) and not file_says_reserved:
            findings.append(f"  L{line.lineno}: 'All rights reserved' contradicts {file_label}")

    section = license_section(lines, headings)
    named: dict[str, int] = {}
    for line in section:
        for fam, pattern in LICENSE_NAME_PATTERNS:
            if pattern.search(line.prose):
                named.setdefault(fam, line.lineno)
    if named and not set(named) & set(families):
        fam, lineno = min(named.items(), key=lambda kv: kv[1])
        findings.append(f"  L{lineno}: License section names {fam} but {file_label}")
    return findings


# --- Main ------------------------------------------------------------------

def run_checks(
    content: str, project_type: str | None, verbosity: str | None, base_dir: str,
    expect: list[str] | None = None, early_stage: bool = False,
) -> tuple[list[tuple[str, list[str]]], tuple[int, str] | None, list[str]]:
    """Return ([(group heading, issues)], first runnable step, notes)."""
    lines = parse_lines(content)
    headings = collect_headings(lines)
    first = find_first_runnable(lines)
    run_issues, run_notes = check_run_first(first, project_type, verbosity, lines, base_dir)
    length_issues, length_notes = check_length(lines, headings, project_type, verbosity, early_stage)
    groups = [
        ("Broken links", check_relative_links(lines, base_dir, expect)),
        ("Dead in-page anchors", check_anchors(lines, headings)),
        ("Badge URL issues", check_badge_urls(lines)),
        ("Header badge count", check_header_badges(lines, headings)),
        ("Dead or misleading badges", check_badge_hosts(lines)),
        ("Placeholder text", check_placeholders(lines)),
        ("Positional image references", check_positional_refs(lines)),
        ("HTML style attributes", check_style_attrs(lines)),
        ("License mismatch", check_license(lines, headings, base_dir)),
        ("Run-first", run_issues),
        ("Length issues", length_issues),
        ("Structure issues", check_structure(lines, headings)),
        ("Duplicate H2 headings", check_duplicate_h2(headings)),
    ]
    return [(name, findings) for name, findings in groups if findings], first, run_notes + length_notes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a generated README for correctness."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="README.md",
        help="README file to validate (default: README.md)",
    )
    parser.add_argument("--type", dest="project_type", default=None, choices=sorted(LENGTH_TARGETS),
                        metavar="SLUG",
                        help="Project type slug for length and run-first checks: "
                             + ", ".join(sorted(LENGTH_TARGETS)))
    parser.add_argument("--verbosity", default=None, choices=["minimal", "standard", "detailed"],
                        help="Verbosity level for length and run-first checks (default: standard)")
    parser.add_argument("--early-stage", action="store_true",
                        help=f"Early-stage project: length range {EARLY_STAGE_LENGTH[0]}-"
                             f"{EARLY_STAGE_LENGTH[1]} lines, overriding --type and --verbosity")
    parser.add_argument("--dir", default=".",
                        help="Project root: resolves relative links and locates the LICENSE file")
    parser.add_argument("--expect", action="append", default=[], metavar="PATH",
                        help="Path (relative to --dir) that will exist when the README is published; "
                             "links to it, or to files under it, are not reported broken. Repeatable.")
    args = parser.parse_args()

    try:
        with open(args.file, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    groups, first, notes = run_checks(content, args.project_type, args.verbosity, args.dir,
                                      args.expect, args.early_stage)
    line_count = len(content.splitlines())
    first_info = f"first runnable step: L{first[0]} ({first[1]})" if first else "no runnable step found"

    if not groups:
        print(f"All checks passed. ({line_count} lines; {first_info})")
    else:
        total = sum(len(findings) for _, findings in groups)
        print(f"Validation found {total} issue(s) ({line_count} lines; {first_info}):")
        print()
        for name, findings in groups:
            print(f"{name}:")
            for finding in findings:
                print(finding)
    if notes:
        print()
        print("Notes (do not affect the exit code):")
        for note in notes:
            print(note)
    sys.exit(1 if groups else 0)


if __name__ == "__main__":
    main()
