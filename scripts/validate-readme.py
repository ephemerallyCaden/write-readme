#!/usr/bin/env python3
"""Validate a generated README for correctness.

Checks:
- Relative links point to files that exist
- Badge URLs are syntactically valid
- No remaining placeholder text (TODO, INSERT, PLACEHOLDER)
- Line count within expected range for the project type and verbosity

Prints findings to stdout. Exit 0 if all pass, 1 if issues found.
"""
from __future__ import annotations

import argparse
import os
import re
import sys


# Length targets by type from the design vision
LENGTH_TARGETS: dict[str, tuple[int, int]] = {
    "web-app": (100, 300),
    "cli": (200, 1200),
    "library": (50, 400),
    "framework": (100, 300),
    "game": (100, 400),
    "visual": (150, 500),
    "gen-ai": (150, 500),
    "ml": (200, 800),
    "desktop": (100, 350),
    "devops": (80, 300),
    "educational": (500, 5000),
    "browser-ext": (80, 400),
    "api": (100, 350),
    "mobile": (150, 350),
    "docs-site": (60, 200),
    "bot": (140, 400),
    "tui": (200, 1200),
    "other": (80, 300),
}

# Verbosity multipliers for length targets
VERBOSITY_MULTIPLIERS: dict[str, tuple[float, float]] = {
    "minimal": (0.3, 0.5),
    "standard": (0.8, 1.0),
    "detailed": (1.0, 1.3),
}

PLACEHOLDER_PATTERNS: list[str] = [
    r"\bTODO\b",
    r"\bINSERT\b",
    r"\bPLACEHOLDER\b",
    r"\bXXX\b",
    r"\bFIXME\b",
    r"\bYOUR[_\s].*?HERE\b",
    r"\byour-.*?-here\b",
    r"\[replace\b",
    r"\[fill in\b",
]


def check_relative_links(content: str, base_dir: str) -> list[str]:
    """Check that relative links point to existing files."""
    findings: list[str] = []
    in_code_block = False

    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Match [text](path) links — skip URLs and anchors
        for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', line):
            link_text = m.group(1)
            path = m.group(2)

            # Skip URLs, anchors, mailto, images from shields.io
            if path.startswith(("http://", "https://", "#", "mailto:")):
                continue
            # Skip image badges that look like shield URLs
            if "img.shields.io" in path:
                continue

            # Strip fragment and query
            clean = path.split("#")[0].split("?")[0]
            if not clean:
                continue

            full_path = os.path.join(base_dir, clean)
            if not os.path.exists(full_path):
                findings.append(
                    f"  L{lineno}: broken link [{link_text}]({path}) — file not found"
                )

    return findings


def check_badge_urls(content: str) -> list[str]:
    """Check that badge image URLs are syntactically valid."""
    findings: list[str] = []
    in_code_block = False

    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Match badge images: ![alt](url)
        for m in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', line):
            alt = m.group(1)
            url = m.group(2)

            if "img.shields.io" in url or "badge" in url.lower():
                # Check for common URL issues
                if " " in url:
                    findings.append(
                        f"  L{lineno}: badge URL contains spaces: {url[:80]}"
                    )
                if url.count("(") != url.count(")"):
                    findings.append(
                        f"  L{lineno}: badge URL has unbalanced parentheses: {url[:80]}"
                    )
                if not url.startswith("http"):
                    findings.append(
                        f"  L{lineno}: badge URL is not absolute: {url[:80]}"
                    )
                # Check for unfilled template vars
                if "{" in url or "}" in url:
                    findings.append(
                        f"  L{lineno}: badge URL has unfilled template variable: {url[:80]}"
                    )

    return findings


def check_placeholders(content: str) -> list[str]:
    """Check for remaining placeholder text."""
    findings: list[str] = []
    in_code_block = False

    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Skip HTML comments (screenshot placeholders are fine)
        if stripped.startswith("<!--"):
            continue

        for pattern in PLACEHOLDER_PATTERNS:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                findings.append(
                    f"  L{lineno}: placeholder text found: {m.group()!r} in: {stripped[:80]}"
                )
                break  # One finding per line is enough

    return findings


def check_length(
    content: str, project_type: str | None, verbosity: str | None
) -> list[str]:
    """Check line count against expected range."""
    findings: list[str] = []
    line_count = len(content.splitlines())

    if not project_type or project_type not in LENGTH_TARGETS:
        return findings

    base_min, base_max = LENGTH_TARGETS[project_type]

    if verbosity and verbosity in VERBOSITY_MULTIPLIERS:
        mult_min, mult_max = VERBOSITY_MULTIPLIERS[verbosity]
        target_min = int(base_min * mult_min)
        target_max = int(base_max * mult_max)
    else:
        target_min = base_min
        target_max = base_max

    if line_count < target_min:
        findings.append(
            f"  Length: {line_count} lines is below the target minimum "
            f"of {target_min} for {project_type}/{verbosity or 'standard'}"
        )
    elif line_count > target_max:
        findings.append(
            f"  Length: {line_count} lines exceeds the target maximum "
            f"of {target_max} for {project_type}/{verbosity or 'standard'}"
        )

    return findings


def check_structure(content: str) -> list[str]:
    """Check basic markdown structure."""
    findings: list[str] = []
    h1_count = 0
    in_code_block = False

    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if re.match(r'^#\s+', stripped):
            h1_count += 1
            if h1_count > 1:
                findings.append(f"  L{lineno}: multiple H1 headings found (should have exactly one)")

    if h1_count == 0:
        findings.append("  Structure: no H1 heading found")

    return findings


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
    parser.add_argument("--type", dest="project_type", default=None, help="Project type slug for length check")
    parser.add_argument("--verbosity", default=None, choices=["minimal", "standard", "detailed"],
                        help="Verbosity level for length check")
    parser.add_argument("--dir", default=".", help="Base directory for resolving relative links")
    args = parser.parse_args()

    try:
        with open(args.file, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    all_findings: list[str] = []

    # Run all checks
    link_findings = check_relative_links(content, args.dir)
    if link_findings:
        all_findings.append("Broken links:")
        all_findings.extend(link_findings)

    badge_findings = check_badge_urls(content)
    if badge_findings:
        all_findings.append("Badge URL issues:")
        all_findings.extend(badge_findings)

    placeholder_findings = check_placeholders(content)
    if placeholder_findings:
        all_findings.append("Placeholder text:")
        all_findings.extend(placeholder_findings)

    length_findings = check_length(content, args.project_type, args.verbosity)
    if length_findings:
        all_findings.append("Length issues:")
        all_findings.extend(length_findings)

    structure_findings = check_structure(content)
    if structure_findings:
        all_findings.append("Structure issues:")
        all_findings.extend(structure_findings)

    if not all_findings:
        line_count = len(content.splitlines())
        print(f"All checks passed. ({line_count} lines)")
        sys.exit(0)

    print(f"Validation found {len(link_findings) + len(badge_findings) + len(placeholder_findings) + len(length_findings) + len(structure_findings)} issue(s):")
    print()
    for line in all_findings:
        print(line)
    sys.exit(1)


if __name__ == "__main__":
    main()
