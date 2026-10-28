#!/usr/bin/env python3
"""Generate a table of contents from a markdown file's headings.

Reads a markdown file, extracts H2 (and optionally H3) headings, and prints
a GitHub-compatible TOC to stdout. Anchors follow GitHub: lowercase, punctuation
stripped, each space a hyphen, -1/-2 suffixes for duplicate headings.

Includes H3s only if there are more than 10 H2 headings.
"""
from __future__ import annotations

import argparse
import sys

from _mdlib import collect_headings, parse_lines, unique_slugs


def extract_headings(content: str) -> list[tuple[int, str, str]]:
    """Extract (level, text, anchor) for each Markdown heading outside code.

    Anchors carry GitHub's -1, -2 suffixes, counted across every heading in
    the document (H1 and H4+ included), as GitHub numbers them.
    """
    headings = [h for h in collect_headings(parse_lines(content)) if not h.html]
    anchors = unique_slugs([h.text for h in headings])
    return [(h.level, h.text.strip(), anchor) for h, anchor in zip(headings, anchors)]


def generate_toc(headings: list[tuple[int, str, str]], include_h3: bool) -> list[str]:
    """Generate TOC lines from (level, text, anchor) headings."""
    lines: list[str] = []
    for level, text, anchor in headings:
        # Skip H1 (the title); include H2 and optionally H3
        if level == 2 or (level == 3 and include_h3):
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
    h2_count = sum(1 for level, _, _ in headings if level == 2)

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
