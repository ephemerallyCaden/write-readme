#!/usr/bin/env python3
"""Scan a markdown file for AI-generated writing patterns.

Checks for banned words, chatbot artifacts, template phrases, and structural
anti-patterns from the design vision. Reports each finding with line number,
offending text, and severity (P0/P1/P2).

Exit code 0 if clean, 1 if findings.
"""
from __future__ import annotations

import argparse
import re
import sys


# Tier 1A banned words (P0 — must never appear)
BANNED_WORDS: list[str] = [
    "delve",
    "robust",
    "comprehensive",
    "leverage",
    "seamless",
    "cutting-edge",
    "cutting edge",
    "empower",
    "streamline",
    "harness",
    "elevate",
    "embark",
    "pivotal",
    "meticulous",
    "showcase",
    "beacon",
    "tapestry",
    "deep dive",
    "deep-dive",
    "unpack",
    "holistic",
    "actionable",
    "best practices",
    "utilize",
    "facilitate",
    "foster",
    "game-changer",
    "game changer",
    "paradigm",
    "realm",
    "testament to",
    "ever-evolving",
    "ever evolving",
]

# Chatbot artifacts (P1)
CHATBOT_ARTIFACTS: list[str] = [
    r"feel free to",
    r"i hope this helps",
    r"don'?t hesitate to",
    r"happy to help",
    r"as an ai",
    r"as a language model",
    r"i'?m here to",
    r"please note that",
    r"it'?s worth noting",
    r"it is worth noting",
    r"importantly",
    r"in conclusion",
    r"to summarize",
    r"in summary",
]

# Template/formulaic phrases (P1)
TEMPLATE_PHRASES: list[str] = [
    r"in the rapidly evolving",
    r"in today'?s (?:world|landscape|era|age)",
    r"in an era of",
    r"in the world of",
    r"serves as a",
    r"in order to",
    r"it goes without saying",
    r"at the end of the day",
    r"when it comes to",
    r"a wide (?:range|variety) of",
    r"plays a (?:crucial|vital|key|pivotal) role",
    r"whether you'?re a .+ or a",
    r"takes it to the next level",
    r"the possibilities are endless",
]

# Transition fluff (P2)
TRANSITION_FLUFF: list[str] = [
    r"^moreover\b",
    r"^furthermore\b",
    r"^additionally\b",
    r"^consequently\b",
    r"^nevertheless\b",
    r"^in addition\b",
]


def check_line(line: str, lineno: int) -> list[dict]:
    findings: list[dict] = []
    lower = line.lower()

    # P0: Banned words
    for word in BANNED_WORDS:
        pattern = r"\b" + re.escape(word) + r"\b"
        m = re.search(pattern, lower)
        if m:
            findings.append({
                "line": lineno,
                "severity": "P0",
                "rule": "banned-word",
                "text": m.group(),
                "context": line.strip(),
            })

    # P1: Chatbot artifacts
    for pattern in CHATBOT_ARTIFACTS:
        m = re.search(pattern, lower)
        if m:
            findings.append({
                "line": lineno,
                "severity": "P1",
                "rule": "chatbot-artifact",
                "text": m.group(),
                "context": line.strip(),
            })

    # P1: Template phrases
    for pattern in TEMPLATE_PHRASES:
        m = re.search(pattern, lower)
        if m:
            findings.append({
                "line": lineno,
                "severity": "P1",
                "rule": "template-phrase",
                "text": m.group(),
                "context": line.strip(),
            })

    # P1: "Let's" openers
    if re.match(r"^\s*let'?s\s", lower):
        findings.append({
            "line": lineno,
            "severity": "P1",
            "rule": "lets-opener",
            "text": line.strip().split()[0:2],
            "context": line.strip(),
        })

    # P1: Emoji in headings
    if re.match(r"^\s*#{1,6}\s", line):
        # Check for emoji (common Unicode ranges)
        emoji_pattern = (
            r"[\U0001F300-\U0001F9FF"
            r"\U00002702-\U000027B0"
            r"\U0000FE00-\U0000FE0F"
            r"\U0001FA00-\U0001FA6F"
            r"\U0001FA70-\U0001FAFF"
            r"\U00002600-\U000026FF"
            r"\U0000200D"
            r"\U00002764]"
        )
        if re.search(emoji_pattern, line):
            findings.append({
                "line": lineno,
                "severity": "P1",
                "rule": "emoji-in-heading",
                "text": line.strip(),
                "context": line.strip(),
            })

    # P2: Section preambles (heading followed by "This section explains/covers/describes...")
    if re.match(r"^\s*this\s+section\s+(explains?|covers?|describes?|provides?|contains?|outlines?)",
                lower):
        findings.append({
            "line": lineno,
            "severity": "P2",
            "rule": "section-preamble",
            "text": line.strip(),
            "context": line.strip(),
        })

    # P2: Transition fluff at start of line
    stripped = line.strip().lower()
    for pattern in TRANSITION_FLUFF:
        if re.match(pattern, stripped):
            findings.append({
                "line": lineno,
                "severity": "P2",
                "rule": "transition-fluff",
                "text": stripped.split()[0],
                "context": line.strip(),
            })
            break

    return findings


def check_content(content: str) -> list[dict]:
    all_findings: list[dict] = []
    in_code_block = False

    for lineno, line in enumerate(content.splitlines(), start=1):
        # Skip code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        all_findings.extend(check_line(line, lineno))

    # Deduplicate: same line + same rule
    seen: set[tuple[int, str]] = set()
    unique: list[dict] = []
    for f in all_findings:
        key = (f["line"], f["rule"], str(f["text"]))
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def format_finding(f: dict) -> str:
    return f"  L{f['line']:>4d}  [{f['severity']}] {f['rule']}: {f['text']!r}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan a markdown file for AI-generated writing patterns."
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Path to markdown file (reads stdin if omitted)",
    )
    parser.add_argument(
        "--severity",
        default="P0",
        choices=["P0", "P1", "P2"],
        help="Minimum severity to report (default: P0 = all severities)",
    )
    args = parser.parse_args()

    severity_order = {"P0": 0, "P1": 1, "P2": 2}
    min_severity = severity_order[args.severity]

    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(2)
    else:
        if sys.stdin.isatty():
            print("Reading from stdin (pipe a file or use --file)...", file=sys.stderr)
        content = sys.stdin.read()

    findings = check_content(content)

    # Filter by severity
    findings = [f for f in findings if severity_order[f["severity"]] <= min_severity + 2]
    # Actually: filter so we only show findings at min_severity or more severe
    # P0 is most severe. If --severity P1, show P0 and P1. If P2, show all.
    max_shown = severity_order[args.severity]
    findings = [f for f in findings if severity_order[f["severity"]] <= max_shown]

    if not findings:
        print("Clean: no anti-AI findings.")
        sys.exit(0)

    # Group by severity
    p0 = [f for f in findings if f["severity"] == "P0"]
    p1 = [f for f in findings if f["severity"] == "P1"]
    p2 = [f for f in findings if f["severity"] == "P2"]

    total = len(findings)
    print(f"Found {total} issue{'s' if total != 1 else ''}:")
    print()

    if p0:
        print(f"  P0 — Banned words ({len(p0)}):")
        for f in p0:
            print(format_finding(f))
        print()

    if p1:
        print(f"  P1 — Chatbot artifacts / template phrases ({len(p1)}):")
        for f in p1:
            print(format_finding(f))
        print()

    if p2:
        print(f"  P2 — Style issues ({len(p2)}):")
        for f in p2:
            print(format_finding(f))
        print()

    sys.exit(1)


if __name__ == "__main__":
    main()
