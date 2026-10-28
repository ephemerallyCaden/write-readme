#!/usr/bin/env python3
"""Scan a markdown file for AI-generated writing patterns.

Checks for banned words, chatbot artifacts, template phrases, and structural
anti-patterns from references/anti-ai-rules.md (including bold-label feature
lists and em dash overuse). Only rendered prose is scanned: fenced code,
inline code and HTML comments are ignored. Reports each finding with line number, offending text, and
severity (P0/P1/P2).

Exit code 0 if clean, 1 if findings.
"""
from __future__ import annotations

import argparse
import re
import sys

from _mdlib import ATX_HEADING_RE, INLINE_CODE_RE, Line, parse_lines


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

# Extra forms the suffix rules below do not produce
EXTRA_FORMS: dict[str, list[str]] = {
    "utilize": [r"utilis(?:e|es|ed|ing)", r"utili[sz]ations?"],
    "holistic": [r"holistically"],
}


def banned_word_pattern(word: str) -> re.Pattern[str]:
    """Match a banned entry and its common inflections (lowercase input).

    Multi-word and hyphenated entries match exactly. Single words get
    stem + suffix forms: "leverage" -> leverages/leveraged/leveraging,
    "tapestry" -> tapestries, "harness" -> harnesses, "seamless" ->
    seamlessly. Suffixes are a closed list, so "elevator" does not match
    "elevate" and "realmente" does not match "realm".
    """
    if " " in word or "-" in word:
        body = re.escape(word)
    elif word.endswith("e"):
        body = re.escape(word[:-1]) + r"(?:e|es|ed|ing|ely)"
    elif word.endswith("y"):
        body = re.escape(word[:-1]) + r"(?:y|ies)"
    else:
        body = re.escape(word) + r"(?:s|es|ed|ing|ly|ness|ments?)?"
    alternatives = [body, *EXTRA_FORMS.get(word, [])]
    return re.compile(r"\b(?:" + "|".join(alternatives) + r")\b")


BANNED_WORD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (word, banned_word_pattern(word)) for word in BANNED_WORDS
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
    r"\bserves as (?:a|an|the)\b",
    r"in order to",
    r"it goes without saying",
    r"at the end of the day",
    r"when it comes to",
    r"a wide (?:range|variety) of",
    r"plays a (?:crucial|vital|key|pivotal) role",
    r"whether you'?re a .+ or a",
    r"takes it to the next level",
    r"the possibilities are endless",
    r"\bstep towards?\b",
]

# "Let's" opening a line, a list item, a heading or a quote. An apostrophe
# (straight or curly) is required: "Lets you ..." is ordinary README prose.
LETS_OPENER_RE = re.compile(
    r"^\s*(?:(?:[-*+]|\d+[.)]|#{1,6}|>)\s+)*(let['\u2019]s\b(?:\s+\S+)?)",
    re.IGNORECASE,
)

# Emoji ranges for headings. U+2B00-2BFF covers star/arrow emoji such as
# U+2B50; U+231A-23FA covers watch/hourglass/media-control emoji.
EMOJI_RE = re.compile(
    r"[\U0001F000-\U0001F2FF"
    r"\U0001F300-\U0001F9FF"
    r"\U0001FA00-\U0001FAFF"
    r"\U00002600-\U000027BF"
    r"\U00002B00-\U00002BFF"
    r"\U0000231A-\U0000231B"
    r"\U000023E9-\U000023FA"
    r"\U0000FE00-\U0000FE0F"
    r"\U0000200D]"
)

# Transition fluff (P2)
TRANSITION_FLUFF: list[str] = [
    r"^moreover\b",
    r"^furthermore\b",
    r"^additionally\b",
    r"^consequently\b",
    r"^nevertheless\b",
    r"^in addition\b",
]

EM_DASH = "\u2014"
# Prose em dashes allowed per README before flagging (P2)
MAX_PROSE_EM_DASHES = 2
# Bold-label list items allowed per list before flagging (P1)
MAX_BOLD_LABEL_ITEMS = 2

BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
# "**Name** -- desc", "**Name** — desc", "**Name** - desc", "**Name**: desc",
# "**Name:** desc". A single hyphen needs spaces around it ("**x**-ish" is not a label).
BOLD_LABEL_RE = re.compile(
    r"^\*\*([^*]+?)(?::\*\*|\*\*(?:\s*(?:--|\u2014|\u2013|:)|\s+-\s))\s*\S"
)
# Lists under these headings (and their subheadings) are reference lists, so
# rule 12 does not apply. A heading that also says "feature" is not exempt.
FEATURE_HEADING_RE = re.compile(r"\bfeatures?\b", re.IGNORECASE)
REFERENCE_HEADING_RE = re.compile(
    r"\b(?:structure|files?|layout|config|configuration|options?|flags?|api|"
    r"reference|languages?|environment)\b",
    re.IGNORECASE,
)


def is_reference_label(label: str) -> bool:
    """Inline code or a file/path token (`train.py`, src/app) names a thing, not a feature."""
    label = label.strip()
    if re.fullmatch(r"(`+).+\1", label):
        return True
    return not re.search(r"\s", label) and ("/" in label or bool(re.search(r"\.\w", label)))


def check_line(line: str, lineno: int, context: str | None = None) -> list[dict]:
    """Line-level rules. Pass rendered prose (Line.prose): HTML comments and
    inline code removed. `context` is the raw line shown in findings."""
    findings: list[dict] = []
    lower = line.lower()
    context = (line if context is None else context).strip()

    def add(severity: str, rule: str, text: str) -> None:
        findings.append({"line": lineno, "severity": severity, "rule": rule,
                         "text": text, "context": context})

    # P0: Banned words
    for _, pattern in BANNED_WORD_PATTERNS:
        m = pattern.search(lower)
        if m:
            add("P0", "banned-word", m.group())

    # P1: Chatbot artifacts and template phrases
    for rule, patterns in (("chatbot-artifact", CHATBOT_ARTIFACTS),
                           ("template-phrase", TEMPLATE_PHRASES)):
        for pattern in patterns:
            m = re.search(pattern, lower)
            if m:
                add("P1", rule, m.group())

    # P1: "Let's" openers
    m = LETS_OPENER_RE.match(line)
    if m:
        add("P1", "lets-opener", m.group(1))

    # P1: Emoji in headings
    if re.match(r"^\s*#{1,6}\s", line) and EMOJI_RE.search(line):
        add("P1", "emoji-in-heading", line.strip())

    # P2: Section preambles (heading followed by "This section explains/covers/describes...")
    if re.match(r"^\s*this\s+section\s+(explains?|covers?|describes?|provides?|contains?|outlines?)",
                lower):
        add("P2", "section-preamble", line.strip())

    # P2: Transition fluff at start of line
    stripped = line.strip().lower()
    for pattern in TRANSITION_FLUFF:
        if re.match(pattern, stripped):
            add("P2", "transition-fluff", stripped.split()[0])
            break

    return findings


def is_reference_heading(title: str) -> bool:
    return bool(REFERENCE_HEADING_RE.search(title)) and not FEATURE_HEADING_RE.search(title)


def check_structure(lines: list[Line]) -> list[dict]:
    """List and em dash checks over prose lines (HTML comments removed).

    Fenced code lines are skipped and leave list state untouched.

    Bold-label items are exempt from rule 12 when the label is inline code or
    a file/path token, or when the list sits in a reference section
    (Structure, Files, Configuration, Options, API, ...), subsections included.
    """
    findings: list[dict] = []
    bold_items: list[tuple[int, str, str]] = []
    prose_dashes: list[tuple[int, str]] = []
    in_list = False
    prev_blank = True
    # Level of the reference heading whose section we are in, if any
    reference_level: int | None = None

    def close_list() -> None:
        if len(bold_items) > MAX_BOLD_LABEL_ITEMS:
            for lineno, label, context in bold_items:
                findings.append({
                    "line": lineno,
                    "severity": "P1",
                    "rule": "bold-label-list",
                    "text": f"**{label}**",
                    "context": context,
                })
        bold_items.clear()

    for line in lines:
        if line.in_code:
            continue
        lineno, raw = line.lineno, line.text
        text = INLINE_CODE_RE.sub("CODE", raw)
        stripped = text.strip()
        if not stripped:
            prev_blank = True
            continue

        heading = ATX_HEADING_RE.match(text)
        if heading:
            level = len(heading.group(1))
            if reference_level is None or level <= reference_level:
                reference_level = level if is_reference_heading(heading.group(2)) else None

        bullet = BULLET_RE.match(raw)
        if bullet:
            in_list = True
            m = BOLD_LABEL_RE.match(bullet.group(1))
            if m and reference_level is None and not is_reference_label(m.group(1)):
                bold_items.append((lineno, m.group(1).strip(), raw.strip()))
        elif in_list and (text[:1].isspace()
                          or (not prev_blank and not stripped.startswith("#"))):
            pass  # indented or lazy continuation of the current item
        else:
            if in_list:
                close_list()
            in_list = False
        prev_blank = False

        if EM_DASH not in text:
            continue
        if in_list:
            findings.append({
                "line": lineno,
                "severity": "P1",
                "rule": "em-dash-in-list",
                "text": EM_DASH,
                "context": stripped,
            })
        else:
            prose_dashes.extend((lineno, stripped) for _ in range(text.count(EM_DASH)))

    close_list()

    if len(prose_dashes) > MAX_PROSE_EM_DASHES:
        total = len(prose_dashes)
        for lineno, context in prose_dashes:
            findings.append({
                "line": lineno,
                "severity": "P2",
                "rule": "em-dash-overuse",
                "text": f"{EM_DASH} ({total} in prose, max {MAX_PROSE_EM_DASHES})",
                "context": context,
            })

    return findings


def check_content(content: str) -> list[dict]:
    all_findings: list[dict] = []
    lines = parse_lines(content)
    for line in lines:
        if not line.in_code and line.prose.strip():
            all_findings.extend(check_line(line.prose, line.lineno, line.raw))
    all_findings.extend(check_structure(lines))
    all_findings.sort(key=lambda f: f["line"])

    # Deduplicate: same line + same rule
    seen: set[tuple[int, str]] = set()
    unique: list[dict] = []
    for f in all_findings:
        key = (f["line"], f["rule"], f["text"])
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
        help="Severity threshold: report this level and anything more severe. "
             "P0 = P0 only, P1 = P0+P1, P2 = all (default: P0)",
    )
    args = parser.parse_args()

    severity_order = {"P0": 0, "P1": 1, "P2": 2}

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

    # P0 is most severe. --severity P1 shows P0 and P1; P2 shows all.
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
