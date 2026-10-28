"""Shared Markdown line model for the README checker scripts.

Imported by validate-readme.py and check-anti-ai.py. Running either script as
`python3 scripts/<name>.py` puts this directory on sys.path, so a plain
`import _mdlib` works without packaging.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})\s*([^\s`{]*)")
ATX_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
HTML_HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1\s*>", re.IGNORECASE | re.DOTALL)
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?[^)]*\)")
MD_LINK_RE = re.compile(r"(?<!!)\[((?:[^\[\]]|!\[[^\]]*\]\([^)]*\))*)\]\(\s*<?([^)\s>]+)>?[^)]*\)")
# _emphasis_ / __strong__ delimiters; intraword underscores (snake_case) stay
UNDERSCORE_EMPHASIS_RE = re.compile(r"(?<![^\W_])(_{1,3})(?=\S)(.+?)(?<=\S)\1(?![^\W_])")

# Header badges allowed before the first H2 (SKILL.md: 0-6). Shared by
# generate-badges.py and validate-readme.py.
MAX_HEADER_BADGES = 6


@dataclass
class Heading:
    lineno: int
    level: int
    text: str
    html: bool = False   # an <hN> tag; GitHub gives these no automatic anchor


@dataclass
class Line:
    """One Markdown line, pre-split into the views the checks need."""

    lineno: int
    raw: str
    in_code: bool       # inside a fenced code block (fence lines included)
    text: str           # HTML comments removed; "" for code lines
    prose: str          # text with inline code spans blanked
    fence_lang: str | None = None   # info-string language, set on opening fences only
    fence_close: bool = False       # True on closing fence lines


def find_comment_start(text: str) -> int:
    """Index of the first "<!--" outside inline code spans, or -1."""
    pos = text.find("<!--")
    if pos == -1:
        return -1
    spans = [m.span() for m in INLINE_CODE_RE.finditer(text)]
    while pos != -1 and any(a <= pos < b for a, b in spans):
        pos = text.find("<!--", pos + 1)
    return pos


def strip_html_comments(lines: list[str]) -> list[str]:
    """Blank out <!-- ... --> spans (which may cross lines), keeping line count."""
    out: list[str] = []
    in_comment = False
    for line in lines:
        kept = ""
        rest = line
        while rest:
            if in_comment:
                end = rest.find("-->")
                if end == -1:
                    break
                rest = rest[end + 3:]
                in_comment = False
            else:
                start = find_comment_start(rest)
                if start == -1:
                    kept += rest
                    break
                kept += rest[:start]
                rest = rest[start + 4:]
                in_comment = True
        out.append(kept)
    return out


def blank_inline_code(text: str) -> str:
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)


def parse_lines(content: str) -> list[Line]:
    """Split content into Lines, tracking ``` / ~~~ fences and HTML comments."""
    raw_lines = content.splitlines()
    out: list[Line] = []
    fence: str | None = None
    # Openers are detected on comment-stripped text so a fence inside a
    # comment does not toggle code state.
    for lineno, (raw, uncommented) in enumerate(
        zip(raw_lines, strip_html_comments(raw_lines)), start=1
    ):
        if fence is None:
            m = FENCE_RE.match(uncommented)
            if m:
                fence = m.group(1)
                out.append(Line(lineno, raw, True, "", "", fence_lang=m.group(2).lower()))
            else:
                out.append(Line(lineno, raw, False, uncommented, blank_inline_code(uncommented)))
            continue
        m = FENCE_RE.match(raw)
        closes = bool(m) and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
            and not raw.strip()[len(m.group(1)):].strip()
        if closes:
            fence = None
        out.append(Line(lineno, raw, True, "", "", fence_close=closes))
    return out


def iter_code_blocks(lines: list[Line]) -> list[tuple[int, str, list[str]]]:
    """(opening line number, info-string language, body lines) per fenced block."""
    blocks: list[tuple[int, str, list[str]]] = []
    for line in lines:
        if line.fence_lang is not None:
            blocks.append((line.lineno, line.fence_lang, []))
        elif line.in_code and not line.fence_close:
            blocks[-1][2].append(line.raw)
    return blocks


def front_matter_end(lines: list[Line]) -> int:
    """Index of the first line after a leading YAML front matter block (0 if none)."""
    if not lines or lines[0].raw.strip() != "---":
        return 0
    for i, line in enumerate(lines[1:], start=1):
        if line.raw.strip() in ("---", "..."):
            return i + 1
    return 0


def collect_headings(lines: list[Line]) -> list[Heading]:
    """ATX, setext and <hN> headings outside code, in document order."""
    headings: list[Heading] = []
    prev: Line | None = None
    for line in lines[front_matter_end(lines):]:
        if line.in_code:
            prev = None
            continue
        m = ATX_HEADING_RE.match(line.text)
        if m:
            headings.append(Heading(line.lineno, len(m.group(1)), m.group(2)))
        elif prev is not None and re.match(r"^\s{0,3}(=+|-+)\s*$", line.text):
            p = prev.text.strip()
            if p and not BULLET_RE.match(prev.text) and not p.startswith(("|", "<", "#", ">")):
                level = 1 if line.text.strip()[0] == "=" else 2
                headings.append(Heading(prev.lineno, level, p))
        for hm in HTML_HEADING_RE.finditer(line.text):
            headings.append(Heading(line.lineno, int(hm.group(1)), hm.group(2), html=True))
        prev = line
    headings.sort(key=lambda h: h.lineno)
    return headings


def _strip_markup(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    while True:
        stripped = UNDERSCORE_EMPHASIS_RE.sub(lambda m: m.group(2), text)
        if stripped == text:
            break
        text = stripped
    return text.replace("*", "").replace("~", "")


def plain_heading_text(text: str) -> str:
    """The rendered text GitHub slugs a heading from (code span content kept verbatim)."""
    text = MD_IMAGE_RE.sub(lambda m: m.group(1), text)
    text = MD_LINK_RE.sub(lambda m: m.group(1), text)
    parts: list[str] = []
    pos = 0
    for m in INLINE_CODE_RE.finditer(text):
        parts += [_strip_markup(text[pos:m.start()]), m.group(2)]
        pos = m.end()
    parts.append(_strip_markup(text[pos:]))
    return "".join(parts)


def github_slug(text: str) -> str:
    """GitHub's heading anchor: lowercase, drop punctuation except - and _,
    each space becomes a hyphen (repeated hyphens are kept)."""
    text = plain_heading_text(text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def unique_slugs(texts: list[str]) -> list[str]:
    """Slugs for headings in document order, with GitHub's -1, -2 duplicate suffixes."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for text in texts:
        base = slug = github_slug(text)
        while slug in seen:
            seen[base] += 1
            slug = f"{base}-{seen[base]}"
        seen[slug] = 0
        out.append(slug)
    return out
