#!/usr/bin/env python3
"""Capture terminal output as a styled PNG screenshot.

Runs a command, captures stdout with ANSI colors, converts to styled HTML
using Dracula theme colors, wraps in terminal window chrome, and uses
Playwright to render and screenshot the result.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys


# Dracula theme ANSI color map
DRACULA_COLORS: dict[int, str] = {
    30: "#44475a",  # black
    31: "#ff5555",  # red
    32: "#50fa7b",  # green
    33: "#f1fa8c",  # yellow
    34: "#bd93f9",  # purple/blue
    35: "#ff79c6",  # magenta/pink
    36: "#8be9fd",  # cyan
    37: "#f8f8f2",  # white
    90: "#6272a4",  # bright black
    91: "#ff6e6e",  # bright red
    92: "#69ff94",  # bright green
    93: "#ffffa5",  # bright yellow
    94: "#d6acff",  # bright blue
    95: "#ff92df",  # bright magenta
    96: "#a4ffff",  # bright cyan
    97: "#ffffff",  # bright white
}

DRACULA_BG = "#282a36"
DRACULA_FG = "#f8f8f2"
DRACULA_COMMENT = "#6272a4"


def ansi_to_html(text: str) -> str:
    """Convert ANSI escape sequences to HTML spans with Dracula colors."""
    escaped = html.escape(text)

    def replace_ansi(m: re.Match) -> str:
        codes = m.group(1).split(";")
        styles: list[str] = []
        for code_str in codes:
            try:
                code = int(code_str)
            except ValueError:
                continue
            if code == 0:
                return "</span>"
            elif code == 1:
                styles.append("font-weight:bold")
            elif code == 2:
                styles.append("opacity:0.7")
            elif code == 3:
                styles.append("font-style:italic")
            elif code == 4:
                styles.append("text-decoration:underline")
            elif code in DRACULA_COLORS:
                styles.append(f"color:{DRACULA_COLORS[code]}")
            elif 40 <= code <= 47:
                fg_code = code - 10
                if fg_code in DRACULA_COLORS:
                    styles.append(f"background-color:{DRACULA_COLORS[fg_code]}")

        if styles:
            return f'<span style="{";".join(styles)}">'
        return ""

    result = re.sub(r'\033\[([0-9;]*)m', replace_ansi, escaped)
    # Clean up any remaining escape sequences
    result = re.sub(r'\033\[[0-9;]*[A-Za-z]', '', result)
    return result


def build_terminal_html(content_html: str, title: str = "Terminal") -> str:
    """Wrap content in a terminal-styled HTML page with window chrome."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: transparent;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  }}
  .terminal {{
    background: {DRACULA_BG};
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    max-width: 900px;
  }}
  .titlebar {{
    background: #21222c;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
  }}
  .dot-red {{ background: #ff5555; }}
  .dot-yellow {{ background: #f1fa8c; }}
  .dot-green {{ background: #50fa7b; }}
  .title-text {{
    color: {DRACULA_COMMENT};
    font-size: 13px;
    margin-left: 8px;
  }}
  .content {{
    padding: 16px 20px;
    color: {DRACULA_FG};
    font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', 'Cascadia Code',
                 'Menlo', 'Monaco', 'Consolas', monospace;
    font-size: 14px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-x: auto;
  }}
</style>
</head>
<body>
<div class="terminal">
  <div class="titlebar">
    <span class="dot dot-red"></span>
    <span class="dot dot-yellow"></span>
    <span class="dot dot-green"></span>
    <span class="title-text">{html.escape(title)}</span>
  </div>
  <div class="content">{content_html}</div>
</div>
</body>
</html>"""


def capture_terminal(
    command: str,
    output: str,
    title: str | None = None,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Error: playwright is not installed. Install with:\n"
            "  pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    # Run the command and capture output
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    # Force color output for common tools
    env["FORCE_COLOR"] = "1"
    env["CLICOLOR_FORCE"] = "1"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        cmd_output = result.stdout
        if result.stderr and not result.stdout:
            cmd_output = result.stderr
        elif result.stderr:
            cmd_output = result.stdout + "\n" + result.stderr
    except subprocess.TimeoutExpired:
        print(f"Error: command timed out after 30s: {command}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        sys.exit(1)

    if not cmd_output.strip():
        print("Warning: command produced no output", file=sys.stderr)
        cmd_output = f"$ {command}\n(no output)"

    # Prepend the command prompt
    display = f"$ {command}\n{cmd_output.rstrip()}"
    content_html = ansi_to_html(display)
    term_title = title or command.split()[0] if command else "Terminal"
    full_html = build_terminal_html(content_html, title=term_title)

    # Render with Playwright
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 960, "height": 600},
            device_scale_factor=2,
        )
        page.set_content(full_html)
        page.wait_for_timeout(500)

        terminal = page.locator(".terminal")
        terminal.screenshot(path=output)
        print(f"Terminal screenshot saved to {output}")
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture terminal command output as a styled PNG screenshot."
    )
    parser.add_argument("--command", "-c", required=True, help="Command to run and capture")
    parser.add_argument("--output", "-o", default="terminal.png", help="Output PNG path (default: terminal.png)")
    parser.add_argument("--title", default=None, help="Window title (default: command name)")
    args = parser.parse_args()

    capture_terminal(
        command=args.command,
        output=args.output,
        title=args.title,
    )


if __name__ == "__main__":
    main()
