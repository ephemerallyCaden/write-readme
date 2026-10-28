#!/usr/bin/env python3
"""Capture terminal output as a styled PNG screenshot.

Runs a command without a shell, captures stdout with ANSI colors, converts to
styled HTML using Dracula theme colors, wraps in terminal window chrome, and
uses Playwright to render and screenshot the result.

The command is an argument list: either everything after `--`, or a
`--command` string split with shlex. Shell syntax (pipes, redirects, `;`,
`&&`, backticks, `$(...)`, variables, globs) is rejected rather than handed to
a shell.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shlex
import subprocess
import sys

DEFAULT_TIMEOUT = 30.0

# Characters a shell treats as syntax when they appear outside quotes.
_UNQUOTED_SYNTAX = {
    "|": "a pipe",
    "&": "'&' or '&&'",
    ";": "';'",
    "<": "a redirect",
    ">": "a redirect",
    "(": "a subshell",
    ")": "a subshell",
    "*": "a glob",
    "?": "a glob",
    "\n": "a newline",
}


class CommandError(ValueError):
    """The command can't be run as a plain argument list."""


def find_shell_syntax(command: str) -> str | None:
    """Describe the first shell construct in `command`, or None if there is none.

    Single quotes make everything literal. Double quotes keep `|`, `;`, `>`
    and the like literal, but a shell still expands backticks and `$` inside
    them, so those are reported wherever they appear outside single quotes.
    """
    quote = None
    i = 0
    while i < len(command):
        c = command[i]
        if quote == "'":
            if c == "'":
                quote = None
        elif c == "\\":
            i += 1  # the next character is escaped
        elif c == "`":
            return "backticks (command substitution)"
        elif c == "$" and (m := re.match(r"\$([({A-Za-z_])", command[i:])):
            return "'$(' (command substitution)" if m.group(1) == "(" else "a '$' variable or expansion"
        elif quote == '"':
            if c == '"':
                quote = None
        elif c in "'\"":
            quote = c
        elif c in _UNQUOTED_SYNTAX:
            return _UNQUOTED_SYNTAX[c]
        i += 1
    return None


def parse_command(command: str) -> list[str]:
    """Split a command string into argv, refusing anything that needs a shell."""
    found = find_shell_syntax(command)
    if found:
        raise CommandError(
            f"the command uses {found}, which needs a shell; capture-terminal.py runs "
            "commands without one. Capture a single command, or pass its arguments "
            "after '--'."
        )
    try:
        argv = shlex.split(command)
    except ValueError as e:
        raise CommandError(f"could not parse the command: {e}") from e
    if not argv:
        raise CommandError("the command is empty")
    return argv


def run_command(argv: list[str], cwd: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Run argv in cwd with no shell and no stdin; return stdout and stderr."""
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    # Force color output for common tools
    env["FORCE_COLOR"] = "1"
    env["CLICOLOR_FORCE"] = "1"
    shown = shlex.join(argv)
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as e:
        raise CommandError(f"command timed out after {timeout:g}s: {shown}") from e
    except OSError as e:
        raise CommandError(f"could not run {shown}: {e}") from e
    if result.stderr and result.stdout:
        return result.stdout + "\n" + result.stderr
    return result.stdout or result.stderr


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
    argv: list[str],
    output: str,
    title: str | None = None,
    cwd: str = ".",
    timeout: float = DEFAULT_TIMEOUT,
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

    try:
        cmd_output = run_command(argv, cwd=cwd, timeout=timeout)
    except CommandError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not cmd_output.strip():
        print("Warning: command produced no output", file=sys.stderr)
        cmd_output = "(no output)"

    # Prepend the command prompt
    display = f"$ {shlex.join(argv)}\n{cmd_output.rstrip()}"
    content_html = ansi_to_html(display)
    full_html = build_terminal_html(content_html, title=title or os.path.basename(argv[0]))

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


def main(args_list: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Capture terminal command output as a styled PNG screenshot.",
        epilog="Example: capture-terminal.py --dir . -o help.png -- mytool --help",
    )
    parser.add_argument(
        "--command", "-c", default=None,
        help="Command string, split like a shell would but run without one; "
             "pipes, redirects, ';', '&&', backticks and '$(' are rejected",
    )
    parser.add_argument("--output", "-o", default="terminal.png", help="Output PNG path (default: terminal.png)")
    parser.add_argument("--title", default=None, help="Window title (default: command name)")
    parser.add_argument("--dir", default=".", help="Directory to run the command in, the project root (default: .)")
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT,
        help=f"Seconds before the command is stopped (default: {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument("argv", nargs="*", help="The command and its arguments, after '--'")
    args = parser.parse_args(args_list)

    if bool(args.command) == bool(args.argv):
        parser.error("give the command either with --command or after '--', not both")
    if not os.path.isdir(args.dir):
        parser.error(f"--dir is not a directory: {args.dir}")
    if args.argv:
        argv = args.argv
    else:
        try:
            argv = parse_command(args.command)
        except CommandError as e:
            parser.error(str(e))

    capture_terminal(
        argv=argv,
        output=args.output,
        title=args.title,
        cwd=args.dir,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
