#!/usr/bin/env python3
"""Generate a table of contents from a markdown file's headings.

Reads a markdown file, extracts H2 (and optionally H3) headings, and prints
a GitHub-compatible TOC to stdout. Uses GitHub anchor format: lowercase,
hyphens, stripped special chars.

Includes H3s only if there are more than 10 H2 headings.
"""
from __future__ import annotations

import argparse
import re
import sys


def heading_to_anchor(text: str) -> str:
    """Convert heading text to GitHub-compatible anchor."""
    # Strip inline code, bold, italic, links
    text = re.sub(r'`[^`]+`', lambda m: m.group()[1:-1], text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', text)

    anchor = text.lower()
    # Keep only word chars, hyphens, spaces
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    # Replace spaces with hyphens
    anchor = re.sub(r'\s+', '-', anchor.strip())
    # Collapse multiple hyphens
    anchor = re.sub(r'-+', '-', anchor)
    return anchor


def extract_headings(content: str) -> list[tuple[int, str]]:
    """Extract heading level and text from markdown content.

    Returns list of (level, text) tuples. Skips headings inside code blocks.
    """
    headings: list[tuple[int, str]] = []
    in_code_block = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        m = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headings.append((level, text))

    return headings


def generate_toc(headings: list[tuple[int, str]], include_h3: bool) -> list[str]:
    """Generate TOC lines from headings."""
    # Track anchors for deduplication
    anchor_counts: dict[str, int] = {}
    lines: list[str] = []

    for level, text in headings:
        # Skip H1 — it is the title
        if level == 1:
            continue
        # Only include H2 and optionally H3
        if level == 2 or (level == 3 and include_h3):
            anchor = heading_to_anchor(text)

            # Handle duplicate anchors (GitHub appends -1, -2, etc.)
            if anchor in anchor_counts:
                anchor_counts[anchor] += 1
                anchor = f"{anchor}-{anchor_counts[anchor]}"
            else:
                anchor_counts[anchor] = 0

            indent = "  " * (level - 2)
            lines.append(f"{indent}- [{text}](#{anchor})")

    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a table of contents from markdown headings."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Markdown file to process (reads stdin if omitted)",
    )
    parser.add_argument(
        "--h3",
        action="store_true",
        default=False,
        help="Force include H3 headings (auto-enabled if >10 H2s)",
    )
    parser.add_argument(
        "--no-h3",
        action="store_true",
        default=False,
        help="Force exclude H3 headings even if >10 H2s",
    )
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("Reading from stdin (pipe a file or pass a filename)...", file=sys.stderr)
        content = sys.stdin.read()

    headings = extract_headings(content)
    h2_count = sum(1 for level, _ in headings if level == 2)

    if args.no_h3:
        include_h3 = False
    elif args.h3:
        include_h3 = True
    else:
        include_h3 = h2_count > 10

    toc_lines = generate_toc(headings, include_h3)

    if not toc_lines:
        print("<!-- No H2 headings found — TOC not generated -->", file=sys.stderr)
        sys.exit(0)

    print("## Table of Contents")
    print()
    for line in toc_lines:
        print(line)


if __name__ == "__main__":
    main()
