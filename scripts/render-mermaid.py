#!/usr/bin/env python3
"""Render a Mermaid diagram to PNG using Playwright.

Creates an HTML page with the Mermaid JS CDN, renders the diagram in headless
Chromium, and captures a screenshot of the rendered SVG. Supports dark theme.
"""
from __future__ import annotations

import argparse
import html
import os
import sys


MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"


def build_mermaid_html(mermaid_source: str, dark: bool) -> str:
    """Build an HTML page that renders a Mermaid diagram."""
    bg_color = "#0d1117" if dark else "#ffffff"
    theme = "dark" if dark else "default"
    escaped = html.escape(mermaid_source)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    background: {bg_color};
    margin: 0;
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: flex-start;
  }}
  .mermaid {{
    max-width: 100%;
  }}
  .mermaid svg {{
    max-width: 100%;
    height: auto;
  }}
</style>
</head>
<body>
<pre class="mermaid">
{escaped}
</pre>
<script src="{MERMAID_CDN}"></script>
<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: '{theme}',
    securityLevel: 'loose',
    flowchart: {{ htmlLabels: true, curve: 'basis' }},
    themeVariables: {{
      darkMode: {'true' if dark else 'false'},
      background: '{bg_color}',
    }}
  }});
</script>
</body>
</html>"""


def render_mermaid(
    source: str,
    output: str,
    dark: bool,
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

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    page_html = build_mermaid_html(source, dark)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1200, "height": 800},
            device_scale_factor=2,
        )
        page.set_content(page_html)

        # Wait for Mermaid to render the SVG
        try:
            page.wait_for_selector(".mermaid svg", timeout=10000)
        except Exception:
            print(
                "Error: Mermaid failed to render the diagram. "
                "Check the syntax of your Mermaid source.",
                file=sys.stderr,
            )
            browser.close()
            sys.exit(1)

        # Extra time for rendering to complete
        page.wait_for_timeout(500)

        # Screenshot just the diagram element
        mermaid_el = page.locator(".mermaid")
        mermaid_el.screenshot(path=output)
        print(f"Mermaid diagram saved to {output}")
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a Mermaid diagram to PNG using Playwright."
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Mermaid source file (reads stdin if omitted)",
    )
    parser.add_argument(
        "--output", "-o",
        default="mermaid.png",
        help="Output PNG path (default: mermaid.png)",
    )
    parser.add_argument(
        "--dark",
        action="store_true",
        help="Use dark theme",
    )
    args = parser.parse_args()

    if args.input:
        try:
            with open(args.input, encoding="utf-8") as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("Reading Mermaid source from stdin...", file=sys.stderr)
        source = sys.stdin.read()

    source = source.strip()
    if not source:
        print("Error: empty Mermaid source", file=sys.stderr)
        sys.exit(1)

    render_mermaid(source=source, output=args.output, dark=args.dark)


if __name__ == "__main__":
    main()
